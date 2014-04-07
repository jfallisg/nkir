#!/usr/bin/env python

"""Scrapes HTML articles from http://www.kcna.co.jp/ for relevant text, outputting as JSON for database import."""

import datetime
import logging
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
    _console_logger.setLevel(logging.DEBUG)	#DEV: Can modify tthis level
    _formatter = logging.Formatter('%(levelname)-8s %(message)s')
    _console_logger.setFormatter(_formatter)
    
    # add the console logger to root (file) logging handler
    _root_logger = logging.getLogger('')
    _root_logger.addHandler(_console_logger)
    return _root_logger

def _html_to_json(html_file_path):
	success = 1

	soup = BeautifulSoup(open(html_file_path,'r').read())
	print(soup.prettify())

	return success

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
    html_filenames = filter(lambda x:re.search(r'.html', x), inbox_json_root_contents)

    for html_filename in html_filenames:
    	html_file_path = os.path.join(INBOX_JSON_ROOT,html_filename)
    	print html_file_path
    	#count, 
    	json_processer_return = _html_to_json(html_file_path)
    	#check return
    		#increment if successful
    		#archive the html file

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)