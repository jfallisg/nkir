#!/usr/bin/env python

import datetime
import logging
import os
import re
import sys

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_REGEX = re.search("^(.*/nkir).*$", SCRIPT_ROOT)
PROJECT_ROOT = PROJECT_ROOT_REGEX.group(1)
TIME_START = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_NAME = PROJECT_ROOT + '/var/logs/queuer_kcna_' + TIME_START + '.log'
QUEUER_INBOX_ROOT = PROJECT_ROOT + '/data/collector_kcna/inbox_queuer'
JSON_INBOX_ROOT = PROJECT_ROOT + '/data/collector_kcna/inbox_json'
MIRROR_ROOT = PROJECT_ROOT + '/data/collector_kcna/mirror/www.kcna.co.jp'

def _get_logger():
    """
    Configures logging to both file and console.
    <http://docs.python.org/2/howto/logging-cookbook.html>
    
    """
    
    # init the root logger (which logs to persistent local logfile)
    logging.basicConfig(filename=LOG_FILE_NAME,
                        format='%(asctime)s: %(levelname)-8s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)
    
    # configure console logger
    _console_logger = logging.StreamHandler()
    _console_logger.setLevel(logging.DEBUG)
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
    logger.debug("LOG_FILE_NAME {}".format(LOG_FILE_NAME))
    logger.debug("QUEUER_INBOX_ROOT {}".format(QUEUER_INBOX_ROOT))
    logger.debug("MIRROR_ROOT {}".format(MIRROR_ROOT))

    # Look inside QUEUER_INBOX_ROOT for queueud Git logs
    for git_log in os.listdir(QUEUER_INBOX_ROOT):
        print git_log


    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)