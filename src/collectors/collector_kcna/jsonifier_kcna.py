#!/usr/bin/env python

"""Scrapes HTML articles from http://www.kcna.co.jp/ for relevant text, outputting as JSON for database import."""

# TODOs:
# Clean up code
    # pythonic
    # comments
    # variable, function names
    # import just what's needed
    # better logging functions
# Throw exceptions, handle more edge cases
# Check for spanish language articles and not process them
# Multiple rules defined by year, with function to choose the correct rule
# Process real data
# Confirm you can run just the HTML->JSON function on it's own from cmd ln
# fix definitions of our payload to be defined as DATA rather than code
# deploy to server with automation
# refactor to a single definition of all rules self contained, possibly
#   with inheritance from an abstract base class

import datetime
import logging
import json
import os
import re
import shutil
import sys

from bs4 import BeautifulSoup

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_REGEX = re.search("^(.*/nkir).*$", SCRIPT_ROOT)
PROJECT_ROOT = PROJECT_ROOT_REGEX.group(1)
TIME_START = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, 'var/logs/jsonifier_kcna_'+TIME_START+'.log')
INBOX_JSON_ROOT = os.path.join(PROJECT_ROOT, 'data/collector_kcna/inbox_json')
INBOX_JSON_ARCHIVE = os.path.join(INBOX_JSON_ROOT, 'archive')
INBOX_DB_ROOT = os.path.join(PROJECT_ROOT,'data/collector_kcna/inbox_db')

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

def _pp_date(date):
    date = date.replace('Juche','').replace('.','').strip()
    dt = datetime.datetime.strptime(date,"%B %d %Y")
    return dt.__str__()

def _pp_article(data):
    article = data['text']
    
    # slice up first paragraph
    fp = article[0]
    regex = re.search("^(.*),.*\((.*)\) -- (.*)$",fp)
    (data['metadata']['location'],
     data['metadata']['news_service'],
     article[0]) = regex.groups()
    
    # chop off copyright line of article
    article.pop()
    data['text'] = article
    return data

def _get_link_url(html_filename):
    KCNA_URL_ROOT = 'http://www.kcna.co.jp'

    reg = re.search("^(\d\d\d\d)(\d\d)(\d\d).*$", html_filename)
    (year, month, day) = reg.groups()
    
    URL_FORMAT = [KCNA_URL_ROOT,
                  'item',
                  year,
                  year+month,
                  'news'+day,
                  html_filename]

    link_url = "/".join(URL_FORMAT)
    return link_url

def html_to_json(html_file_path):
    logger = logging.getLogger('')
    logger.debug("Processing: {}".format(html_file_path))    

    # initialize for every article
    payload = {
        'app': 'jsonifier_kcna.py',
        'data_type': 'text',
        'data_source': 'kcna_article',
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'version': 1,
    }

    # parse HTML
    soup = BeautifulSoup(open(html_file_path,'r').read())

    html_text = soup.get_text()
    re_parse = re.compile(ur"^.*>> (.* \d\d\d\d) Juche ([0-9]+)(.*)$",
                   re.DOTALL | re.UNICODE)
    parsed = re_parse.search(html_text)
    try:
        (date, juche_year, article) = parsed.groups()
    except AttributeError as e:
        logger.warning("I/O error: {} when attempting regex search on [{}].".format(e, html_file_path))
        return False

    article_text = []
    for line in article.splitlines():
        line = line.strip()
        if line:
            article_text.append(line)

    # process metadata
    data = {}
    data['metadata'] = {}

    data['metadata']['date_published'] = _pp_date(date)

    data['metadata']['juche_year'] = int(juche_year)

    html_filename = os.path.basename(html_file_path)
    data['metadata']['article_url'] = _get_link_url(html_filename)

    datetime_modified = datetime.datetime.fromtimestamp(os.path.getmtime(html_file_path))
    data['metadata']['html_modified'] = datetime_modified.__str__()

    data['metadata']['title'] = article_text.pop(0)

    # process article's text data
    data['text'] = []
    for para_text in article_text:
        data['text'].append(para_text)

    _pp_article(data)
    payload['data'] = data

    # write output JSON
    new_filename = os.path.splitext(os.path.basename(html_file_path))[0] + '.json'
    new_filepath = os.path.join(INBOX_DB_ROOT, new_filename)

    if( not os.path.exists(INBOX_DB_ROOT) ):
        os.makedirs(INBOX_DB_ROOT)

    with open(new_filepath, 'w') as outfile:
        json.dump(payload, outfile, sort_keys=True)

    return True

def main():
    logger = _get_logger()
    logger.info("{} started at {}.".format(os.path.basename(__file__),TIME_START))
    logger.debug("SCRIPT_ROOT {}".format(SCRIPT_ROOT))
    logger.debug("PROJECT_ROOT {}".format(PROJECT_ROOT))
    logger.debug("LOG_FILE_PATH {}".format(LOG_FILE_PATH))
    logger.debug("INBOX_JSON_ROOT {}".format(INBOX_JSON_ROOT))
    logger.debug("INBOX_DB_ROOT {}".format(INBOX_DB_ROOT))

     # Look inside INBOX_JSON_ROOT for queueud HTML files
    inbox_json_root_contents = os.listdir(INBOX_JSON_ROOT)
    html_filenames = filter(lambda x:re.search(r'.htm', x), inbox_json_root_contents)

    total_articles = 0
    processed_articles = 0
    for html_filename in html_filenames:
        total_articles += 1
        html_file_path = os.path.join(INBOX_JSON_ROOT,html_filename)
        json_processer_return = html_to_json(html_file_path)

        # archive html file if we processed ok
        if json_processer_return:
            processed_articles += 1
            logger.info("Successfully processed {} in to JSON.".format(html_filename))
            if( not os.path.exists(INBOX_JSON_ARCHIVE) ):
                os.makedirs(INBOX_JSON_ARCHIVE)
            
            html_file_archive_path = os.path.join(INBOX_JSON_ARCHIVE,html_filename)
            try:
                shutil.move(html_file_path, html_file_archive_path)
            except IOError as e:
                logger.warning("I/O error: {} when attempting move [{}] to [{}]".format(e.strerror, html_file_path, html_file_archive_path))
            else:
                logger.debug("Moved {} to JSONIFIER_INBOX's archive.".format(html_file_path))
        else:
            logger.warning("html_to_json error: {} was not successfully processed from HTML -> JSON.".format(html_file_path))

    logger.info("Processed {} HTML articles out of {} from HTML to JSON.".format(processed_articles, total_articles))
    TIME_END = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("{} finished at {}.".format(os.path.basename(__file__),TIME_END))

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)