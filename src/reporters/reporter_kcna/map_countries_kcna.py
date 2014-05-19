#!/usr/bin/env python

"""Query MongoDB for map countries data; export in csv."""

import datetime
import logging
import os
import re
import sys

from pymongo import MongoClient

# TODOs
# Refactor common functionality (logging, setup, teardown, etc) to library
# Singleton of MongoDB connection instead of new connection each country

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_REGEX = re.search("^(.*/nkir).*$", SCRIPT_ROOT)
PROJECT_ROOT = PROJECT_ROOT_REGEX.group(1)
TIME_START = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, 'var/logs/map_countries_kcna_'+TIME_START+'.log')
OUTPUT_ROOT = os.path.join(PROJECT_ROOT, 'data/reporter_kcna/output_map_countries_kcna')

# instantiate a logging object singleton for use throughout script
def _get_logger():
    # init the root logger (which logs to persistent local logfile)
    logging.basicConfig(filename=LOG_FILE_PATH,
                        format='%(asctime)s: %(levelname)-8s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)

    # configure console logger
    _console_logger = logging.StreamHandler()
    _console_logger.setLevel(logging.DEBUG) #DEV: Can modify tthis level
    _formatter = logging.Formatter('%(levelname)-8s %(message)s')
    _console_logger.setFormatter(_formatter)

    # add the console logger to root (file) logging handler
    _root_logger = logging.getLogger('')
    _root_logger.addHandler(_console_logger)
    return _root_logger

# _get_countries returns a dict of lists with each entry looking like:
#  {ISO 3166-1 alpha-3 code : [ISO 3166 Country Name, Alias1, Alias2],
#   next country alpha-3    : [ISO 3166 Country name, Alias1],
#   etc
#  }
def _get_countries():
    _country_map = {}

    _COUNTRIES_FILE_PATH = os.path.join(PROJECT_ROOT, 'var/datasets/countries.txt')

    logger = logging.getLogger('')

    # make sure we have the list of countries file
    if os.path.isfile(_COUNTRIES_FILE_PATH):
        with open(_COUNTRIES_FILE_PATH, 'r') as f:
            for line in f:
                # parse line which looks like:
                # "NLD|Netherlands;Holland\n"
                _country_code, _country_text = line.split("|")
                _country_map[_country_code] = []
                _alias_list = _country_text.rstrip("\n").split(";")
                for _alias in _alias_list:
                    _country_map[_country_code].append(_alias)
            logger.info("Retrieved list of countries.")
    else:
        logger.error("Countries list file {} wasn't available; exiting.".format(_COUNTRIES_FILE_PATH))
        # can't run if we don't have a list of countries, so exit program
        sys.exit(1)

    return _country_map

# _get_articles returns a list of articles (with each article being a
#  PyMongo document from the aggregate function on a MongoDB collection
#  in Python dict form).
def _get_articles(country_code, alias_list):
    _articles = []

    # constants
    _DB_HOST = 'localhost'
    _DB_PORT = 27017
    _DB_NAME = 'NKODP'
    _COLLECTION_NAME = 'KCNA'

    logger = logging.getLogger('')

    logger.info("Looking for country \"{}\".".format(alias_list[0]))

    # NOTE:
    # We want to return all relevant docs for a given country, no matter
    #  which alias is used to find that article, but without duplicating
    #  articles.
    # Ideally this would entail a text search that OR's all the aliases for a
    #  given country.
    # BUT, MongoDB currently has a text search limitation where if one of
    #  search terms is a phrase in double quotes, like "\"North Korea\"",
    #  this phrase will be ANDed with the rest of your search terms.
    # So you can't run a search like:  "United States" || "US" || "USA"
    #  as MongoDB will instead search: "United States" && ("US" || "USA")
    # As a result, we run seperate queries for each alias and append our
    #  found docs by url to a temp dict before returning our final _articles
    #  list for the given country parameter.
    _temp_article_dict = {}
    for alias in alias_list:
        # connect to MongoDB
        _client = MongoClient(_DB_HOST, _DB_PORT)
        _db = _client[_DB_NAME]
        _coll = _db[_COLLECTION_NAME]

        # query for data
        _PIPELINE = [
            { "$match":   { "$text":      { "$search": '"{}"'.format(alias) } } },
            { "$sort":    { "textScore":  { "$meta": "textScore"  } } },
            { "$project": {"_id": 0,
                            "published":  "$data.metadata.date_published",
                            "modified":   "$data.metadata.html_modified",
                            "title":      "$data.metadata.title",
                            "location":   "$data.metadata.location",
                            "url":        "$data.metadata.article_url",
                            "textScore":  { "$meta": "textScore" },
                            "country":    { "$literal": '"{}"'.format(country_code) },
                            "searchterm": { "$literal": '"{}"'.format(alias) },
                            "textbody":   "$data.text",
            }}
        ]

        logger.info("Querying MongoDB for mentions of \"{}\"...".format(alias))

        # execute query
        _cursor = _coll.aggregate(_PIPELINE, cursor={})

        # push return to _temp_article_dict with KEY on url.
        # duplicate articles as we loop through aliases won't appear
        for _doc in _cursor:
            _temp_article_dict[_doc["url"]] = _doc

    # build return list of article/doc dictionaries
    for _url in _temp_article_dict:
        _articles.append(_temp_article_dict[_url])

    # throw message if queried list is empty
    if len(_articles) == 0:
        logger.info("No results found for \"{}\".".format(alias_list[0]))
    else:
        logger.info("{} results found.".format(len(_articles)))

    return _articles

# _get_output_line returns an output csv string for each article dictionary
def _get_output_line(article):

    _country_REGEX = re.search("^\"(.*)\"$", article["country"])
    _country = _country_REGEX.group(1)

    _date_published_REGEX = re.search("^(\d\d\d\d-\d\d-\d\d).*$", article["published"])
    _date_published = _date_published_REGEX.group(1)

    _output_line = ",".join([   _country,
                                _date_published,
                                "\"{}\"".format(article["title"]),
                                article["url"],
                            ])
    return _output_line

# _output_csv prints out output csv file
def _output_csv(data, header):
    if( not os.path.exists(OUTPUT_ROOT) ):
        os.makedirs(OUTPUT_ROOT)

    _output_path = os.path.join(OUTPUT_ROOT, 'map_countries_kcna_'+TIME_START+'.csv')

    with open(_output_path, 'w') as f:
        f.write(header)
        for line in sorted(data):
            f.write(line)
            f.write("\n")

    return(0)

def main():
    logger = _get_logger()
    logger.info("{} started at {}.".format(os.path.basename(__file__),TIME_START))
    logger.debug("SCRIPT_ROOT {}".format(SCRIPT_ROOT))
    logger.debug("PROJECT_ROOT {}".format(PROJECT_ROOT))
    logger.debug("LOG_FILE_PATH {}".format(LOG_FILE_PATH))
    logger.debug("OUTPUT_ROOT {}".format(OUTPUT_ROOT))

    # seed data's header csv string line
    header = "country,date,title,url\n"
    data = []

    countries = _get_countries()

    for country_code, alias_list in sorted(countries.iteritems()):
        articles = _get_articles(country_code, alias_list)

        for article in articles:
            output_line = _get_output_line(article)
            data.append(output_line)
            logger.debug("{}".format(output_line))

    _output_csv(data, header)

    TIME_END = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("{} finished at {}.".format(os.path.basename(__file__),TIME_END))

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)
