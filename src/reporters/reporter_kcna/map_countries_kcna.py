#!/usr/bin/env python

"""Query MongoDB for map countries data; export in csv."""

import datetime
import logging
import os
import re
import sys

from pymongo import MongoClient

DB_HOST = 'localhost'
DB_PORT = 27017
DB_NAME = 'NKODP'
COLLECTION_NAME = 'KCNA'

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

def main():
    logger = _get_logger()
    logger.info("{} started at {}.".format(os.path.basename(__file__),TIME_START))
    logger.debug("SCRIPT_ROOT {}".format(SCRIPT_ROOT))
    logger.debug("PROJECT_ROOT {}".format(PROJECT_ROOT))
    logger.debug("LOG_FILE_PATH {}".format(LOG_FILE_PATH))
    logger.debug("OUTPUT_ROOT {}".format(OUTPUT_ROOT))

    # connect to db
    client = MongoClient(DB_HOST, DB_PORT)
    db = client[DB_NAME]
    coll = db[COLLECTION_NAME]

    # query for data
    pipeline = [
        { "$match":   { "$text":      { "$search": "mongolia" } } },
        { "$sort":    { "textScore":  { "$meta": "textScore"  } } },
        { "$project": {"_id": 0,
                        "published":  "$data.metadata.date_published",
                        "modified":   "$data.metadata.html_modified",
                        "title":      "$data.metadata.title",
                        "location":   "$data.metadata.location",
                        "textScore":  { "$meta": "textScore" },
                        "searchterm": { "$literal": "mongolia" },
                        "textbody":   "$data.text",
        }}
    ]
    cursor = coll.aggregate(pipeline, cursor={})

    # write output data
    if( not os.path.exists(OUTPUT_ROOT) ):
        os.makedirs(OUTPUT_ROOT)

    output_path = os.path.join(OUTPUT_ROOT, 'map_countries_kcna_'+TIME_START+'.csv')

    with open(output_path, 'w') as f:
        firstline = True
        for doc in cursor:
            if firstline:
                for key in doc:
                    print("{},".format(key)),
                    f.write("{},".format(key))
                firstline = False
                print
                f.write("\n")

            for key in doc:
                print("{},".format(doc[key])),
                f.write("{},".format(doc[key])),
            print
            f.write("\n")

    TIME_END = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("{} finished at {}.".format(os.path.basename(__file__),TIME_END))

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)