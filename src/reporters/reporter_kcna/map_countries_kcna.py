#!/usr/bin/env python

"""Query MongoDB for map countries data; export in csv."""

import datetime
import logging
import os
import re
import sys

from pymongo import MongoClient

# TODOs
# BUG in url column of output
# Names of many countries are weird, need a synanyms directory!
# Refactor common functionality (logging, setup, teardown, etc) to library
# Singleton of MongoDB connection instead of new connection each country

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_REGEX = re.search("^(.*/nkir).*$", SCRIPT_ROOT)
PROJECT_ROOT = PROJECT_ROOT_REGEX.group(1)
TIME_START = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, 'var/logs/map_countries_kcna_'+TIME_START+'.log')
OUTPUT_ROOT = os.path.join(PROJECT_ROOT, 'data/reporter_kcna/output_map_countries_kcna')

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

def _get_countries():

    # constants
    _COUNTRIES_FILE_PATH = os.path.join(PROJECT_ROOT, 'var/datasets/countries.txt')

    logger = logging.getLogger('')

    _countries = []

    # make sure we have the list of countries file
    if os.path.isfile(_COUNTRIES_FILE_PATH):
        with open(_COUNTRIES_FILE_PATH, 'r') as f:
            for line in f:
                # parse line which looks like:
                # "BE|Belgium\n"
                _countries.append(line.split("|")[1].rstrip('\n'))
            logger.info("Retrieved list of countries.")
    else:
        logger.error("Countries list file {} wasn't available; exiting.".format(_COUNTRIES_FILE_PATH))
        # can't run if we don't have a list of countries, so exit program
        sys.exit(1)

    return _countries

def _get_articles(country):

    # constants
    _DB_HOST = 'localhost'
    _DB_PORT = 27017
    _DB_NAME = 'NKODP'
    _COLLECTION_NAME = 'KCNA'

    logger = logging.getLogger('')

    _articles = []

    # connect to MongoDB
    _client = MongoClient(_DB_HOST, _DB_PORT)
    _db = _client[_DB_NAME]
    _coll = _db[_COLLECTION_NAME]

    # query for data
    _PIPELINE = [
        { "$match":   { "$text":      { "$search": '"{}"'.format(country) } } },
        { "$sort":    { "textScore":  { "$meta": "textScore"  } } },
        { "$project": {"_id": 0,
                        "published":  "$data.metadata.date_published",
                        "modified":   "$data.metadata.html_modified",
                        "title":      "$data.metadata.title",
                        "location":   "$data.metadata.location",
                        "url":        "$data.metadata.article_url",
                        "textScore":  { "$meta": "textScore" },
                        "searchterm": { "$literal": '"{}"'.format(country) },
                        "textbody":   "$data.text",
        }}
    ]

    logger.info("Querying MongoDB for mentions of \"{}\"...".format(country))

    # execute query
    _cursor = _coll.aggregate(_PIPELINE, cursor={})

    # build return list or dicts
    for _doc in _cursor:
        _articles.append(_doc)

    # throw message if queried list is empty
    if len(_articles) == 0:
        logger.info("No results found for \"{}\".".format(country))
    else:
        logger.info("{} results found.".format(len(_articles)))

    return _articles

def _get_output_line(article):
    
    _output_line = ",".join([   article["searchterm"],
                                article["published"],
                                article["title"],
                                article["url"],
                            ])

    return _output_line

def _output_csv(data):

    logger = logging.getLogger('')

    if( not os.path.exists(OUTPUT_ROOT) ):
        os.makedirs(OUTPUT_ROOT)

    _output_path = os.path.join(OUTPUT_ROOT, 'map_countries_kcna_'+TIME_START+'.csv')

    with open(_output_path, 'w') as f:
        for line in data:
            f.write(line)
            f.write("\n")

    return 1

def main():
    logger = _get_logger()
    logger.info("{} started at {}.".format(os.path.basename(__file__),TIME_START))
    logger.debug("SCRIPT_ROOT {}".format(SCRIPT_ROOT))
    logger.debug("PROJECT_ROOT {}".format(PROJECT_ROOT))
    logger.debug("LOG_FILE_PATH {}".format(LOG_FILE_PATH))
    logger.debug("OUTPUT_ROOT {}".format(OUTPUT_ROOT))

    data = ["country," +
            "published," +
            "title,"+
            "url,"]

    countries = _get_countries()

    for country in countries:
        articles = _get_articles(country)
    
        for article in articles:
            output_line = _get_output_line(article)
            data.append(output_line)
            logger.debug("{}".format(output_line))
    
    _output_csv(data)

    TIME_END = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("{} finished at {}.".format(os.path.basename(__file__),TIME_END))

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)