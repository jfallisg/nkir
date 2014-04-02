#!/usr/bin/env python

"""Queues HTML articles (to be processed in to JSON) based on Git commit logs after any mirroring of the KCNA website - part of the NKIR project."""

import datetime
import logging
import os
import re
import shutil
import sys

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_REGEX = re.search("^(.*/nkir).*$", SCRIPT_ROOT)
PROJECT_ROOT = PROJECT_ROOT_REGEX.group(1)
TIME_START = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_NAME = PROJECT_ROOT + '/var/logs/queuer_kcna_' + TIME_START + '.log'
QUEUER_INBOX_ROOT = PROJECT_ROOT + '/data/collector_kcna/inbox_queuer'
QUEUEUR_INBOX_ARCHIVE = QUEUER_INBOX_ROOT + "/" + "archive"
JSON_INBOX_ROOT = PROJECT_ROOT + '/data/collector_kcna/inbox_json'
MIRROR_ROOT = PROJECT_ROOT + '/data/collector_kcna/mirror/www.kcna.co.jp'

def _get_logger():
    # init the root logger (which logs to persistent local logfile)
    logging.basicConfig(filename=LOG_FILE_NAME,
                        format='%(asctime)s: %(levelname)-8s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)
    
    # configure console logger
    _console_logger = logging.StreamHandler()
    _console_logger.setLevel(logging.INFO)
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
    QUEUER_INBOX_ROOT_contents = os.listdir(QUEUER_INBOX_ROOT)
    git_log_filenames = filter(lambda x:re.search(r'.log', x), QUEUER_INBOX_ROOT_contents)

    processed_articles = 0

    for git_log_filename in git_log_filenames:
        git_log_path = QUEUER_INBOX_ROOT + "/" + git_log_filename
        logger.debug("git_log_path {}".format(git_log_path))

        git_logs_articles = []

        regex = re.compile(
            r"""^
            (?:M|A)\t+
            (?P<article>item/.*/\d\d\d\d\d\d\d\d-\d\dee.html)
            $""", re.VERBOSE)
        with open(git_log_path) as f:
            for line in f:
                match = regex.match(line)
                if match:
                    git_logs_articles.append(match.group("article"))

        # copy relevant HTML files to our JSON_INBOX_ROOT
        total_articles = 0
        queued_articles = 0
        for article in git_logs_articles:
            total_articles += 1
            
            article_path = MIRROR_ROOT + "/" + article

            if( not os.path.exists(JSON_INBOX_ROOT) ):
                os.makedirs(JSON_INBOX_ROOT)

            try:
                shutil.copy2(article_path, JSON_INBOX_ROOT)
            except IOError as e:
                logger.warning("I/O error: {} when attempting copy from [{}] to [{}]".format(e.strerror, article_path, JSON_INBOX_ROOT))
            else:
                logger.debug("Copied {} to JSON_INBOX.".format(article))
                queued_articles += 1

        # archive git log file if we queued/copied everything ok
        if( total_articles == queued_articles ):
            processed_articles += total_articles

            if( not os.path.exists(QUEUEUR_INBOX_ARCHIVE) ):
                os.makedirs(QUEUEUR_INBOX_ARCHIVE)

            git_log_archive_path = QUEUEUR_INBOX_ARCHIVE + "/" + git_log_filename

            try:
                shutil.move(git_log_path, git_log_archive_path)
            except IOError as e:
                logger.warning("I/O error: {} when attempting move [{}] to [{}]".format(e.strerror, git_log_path, git_log_archive_path))
            else:
                logger.debug("Moved {} to QUEUER_INBOX's archive.".format(git_log_filename))

    logger.info("Processed {} HTML articles out of {} git log files.".format(processed_articles, len(git_log_filenames)))
    TIME_END = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("{} finished at {}.".format(os.path.basename(__file__),TIME_END))

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)