#!/usr/bin/env python

"""Insert JSON documents queued in INBOX_JSON_ROOT into MongoDB."""

import datetime
import logging
import json
import os
import re
import shutil
import sys

from pymongo import MongoClient

DB_HOST = 'localhost'
DB_PORT = 28017
DB_NAME = 'NKODP'
COLLECTION_NAME = 'KCNA'

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_REGEX = re.search("^(.*)/src/.*$", SCRIPT_ROOT)
PROJECT_ROOT = PROJECT_ROOT_REGEX.group(1)
TIME_START = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, 'var/logs/dbimporter_kcna_'+TIME_START+'.log')
INBOX_DB_ROOT = os.path.join(PROJECT_ROOT, 'data/collector_kcna/inbox_db')
INBOX_DB_ARCHIVE = os.path.join(INBOX_DB_ROOT, 'archive')

def _get_logger():
    # init the root logger (which logs to persistent local logfile)
    logging.basicConfig(filename=LOG_FILE_PATH,
                        format='%(asctime)s: %(levelname)-8s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)

    # configure console logger
    _console_logger = logging.StreamHandler()
    _console_logger.setLevel(logging.INFO) #DEV: Can modify tthis level
    _formatter = logging.Formatter('%(levelname)-8s %(message)s')
    _console_logger.setFormatter(_formatter)

    # add the console logger to root (file) logging handler
    _root_logger = logging.getLogger('')
    _root_logger.addHandler(_console_logger)
    return _root_logger

def main():
    logger = _get_logger()
    logger.info("{} started at {}.".format(os.path.basename(__file__),TIME_START))
    logger.debug("SCRIPT_ROOT {}".format(SCRIPT_ROOT))
    logger.debug("PROJECT_ROOT {}".format(PROJECT_ROOT))
    logger.debug("LOG_FILE_PATH {}".format(LOG_FILE_PATH))
    logger.debug("INBOX_DB_ROOT {}".format(INBOX_DB_ROOT))
    logger.debug("INBOX_DB_ARCHIVE {}".format(INBOX_DB_ARCHIVE))

    # connect to db
    client = MongoClient(DB_HOST, DB_PORT)
    db = client[DB_NAME]
    coll = db[COLLECTION_NAME]

    # build a todolist of JSON documents to insert in to DB
    inbox_db_root_contents = os.listdir(INBOX_DB_ROOT)
    json_filenames = filter(lambda x:re.search(r'.json', x), inbox_db_root_contents)

    # insert json documents one by one
    total_articles = 0
    processed_articles = 0
    for json_filename in json_filenames:
        total_articles += 1
        json_file_path = os.path.join(INBOX_DB_ROOT,json_filename)
        logger.debug("JSON_FILE_PATH {}".format(json_file_path))

        # open JSON document, insert to MongoDB
        json_file_id = ''
        with open(json_file_path) as json_file:
            try:
                json_data = json.load(json_file)
            except ValueError as e:
                logger.warning("ValueError: {} when attempting to json.load [{}].".format(e, json_file_path))
            else:
                json_file_id = coll.insert(json_data)
                json_file.close()

        if json_file_id:
            processed_articles +=1
            logger.info("Successfully inserted {} in to {}, with fileid {}.".format(json_filename,DB_NAME,json_file_id))
            if( not os.path.exists(INBOX_DB_ARCHIVE) ):
                os.makedirs(INBOX_DB_ARCHIVE)

            json_file_archive_path = os.path.join(INBOX_DB_ARCHIVE,json_filename)
            try:
                shutil.move(json_file_path, json_file_archive_path)
            except IOError as e:
                logger.warning("I/O error: {} when attempting move [{}] to [{}]".format(e.strerror, json_file_path, json_file_archive_path))
            else:
                logger.debug("Moved {} to DBIMPORTER_INBOX's archive.".format(json_file_path))
        else:
            logger.warning("MongoDB insertion error: {} was not successfully inserted.".format(json_file_path))

    logger.info("Inserted {} json articles out of {} into MongoDB.".format(processed_articles, total_articles))

    # Ensure that text search index exists now, so that it can process text index in the background
    coll.ensure_index([
        ('data.text', 'text'),
        ('data.metadata.title', 'text'),
        ('data.metadata.location', 'text'),
        ('data.metadata.news_service', 'text')],
        weights={'data.text': 5, 'data.metadata.title': 10, 'data.metadata.location': 10, 'data.metadata.news_service': 1})
    logger.info("completed ensuring MongoDB text index updated.")

    TIME_END = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("{} finished at {}.".format(os.path.basename(__file__),TIME_END))

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)
