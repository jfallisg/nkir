#!/usr/bin/env python

"""Queues HTML articles (to be processed in to JSON) based on Git commit logs after any mirroring of the KCNA website - part of the NKIR project."""

import datetime
import logging
import os
import re
import shutil
import sys

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_REGEX = re.search("^(.*)/src/.*$", SCRIPT_ROOT)
PROJECT_ROOT = PROJECT_ROOT_REGEX.group(1)
TIME_START = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_NAME = os.path.join(PROJECT_ROOT,'var/logs/queuer_kcna_' + TIME_START + '.log')
QUEUER_INBOX_ROOT = os.path.join(PROJECT_ROOT,'data/collector_kcna/inbox_queuer')
QUEUEUR_INBOX_ARCHIVE = os.path.join(QUEUER_INBOX_ROOT,"archive")
JSON_INBOX_ROOT = os.path.join(PROJECT_ROOT,'data/collector_kcna/inbox_json')
MIRROR_ROOT = os.path.join(PROJECT_ROOT,'data/collector_kcna/mirror/www.kcna.co.jp')

# article filepaths contained in the git log have the following naming conventions:
#   item/1997/9701/news1/01.htm
#   item/1998/9806/news06/10.htm
#   item/2000/200001/news01/01.htm
#   item/2008/200810/news01/20081001-01ee.html
REGEX_GITLOG = re.compile(
    r"""^
    (?:M|A)\t+
    (?P<filepath>item/
    (?P<year>\d\d\d\d)/
    (?P<yearsmall>(?:9\d|20\d\d))
    (?P<month>\d\d)/news
    (?P<newsmonth>(?:\d|\d\d))/
    (?P<file>(?:\d\d.htm|\d\d\d\d\d\d\d\d-\d\dee.html)))
    $""", re.VERBOSE).match

# new-style (post 2008/10/01) KCNA article file naming convention
#   all articles for a given day are in their own .html file
REGEX_FILENAME_NEW = re.compile(
    r"""^
    (\d\d\d\d\d\d\d\d-\d\d)ee.html
    $""", re.VERBOSE).match

# old-style (pre 2008/10/01) KCNA article file naming convention.
#   all articles for a given day are in a single .htm file
REGEX_FILENAME_OLD = re.compile(
    r"""^
    (\d\d).htm
    $""", re.VERBOSE).match

def _get_filename_path_pre(regex_gitlog_match):
    return regex_gitlog_match.group("filepath")

# want to copy standardized named article files with full date in them
#   will use convention that <yyyymmdd>-00ee.html is filename for multi-article html files (old KCNA convention)
def _get_filename_post(regex_gitlog_match):
    logger = logging.getLogger('')
    filename = regex_gitlog_match.group("file")
    logger.debug("queuer_kcna::_get_filename_post filname [{}]".format(filename))
    if REGEX_FILENAME_NEW(filename):
        return filename
    elif REGEX_FILENAME_OLD(filename):
        filename = regex_gitlog_match.group("year")
        filename += regex_gitlog_match.group("month")
        filename += os.path.splitext(regex_gitlog_match.group("file"))[0]
        filename += "-00ee.html"
        return filename
    else:
        logger.warning("queuer_kcna::_get_filename_post unrecognized article filename [{}].".format(filename))
        return None

# filters list of articles using supplied regex, returning tuple of (pre-copy-path, post-copy-filename)
def _filter_log_lines(list, filter):
    return [ ( _get_filename_path_pre(m), _get_filename_post(m) ) for line in list for m in (filter(line),) if m ]

# boilerplate logger singleton declaration
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
        git_log_path = os.path.join(QUEUER_INBOX_ROOT, git_log_filename)
        logger.debug("git_log_path {}".format(git_log_path))

        git_logs_articles = []

        with open(git_log_path) as f:
            git_logs_articles = _filter_log_lines(f, REGEX_GITLOG)

        # copy relevant HTML files to our JSON_INBOX_ROOT
        total_articles = 0
        queued_articles = 0
        for filename_path_pre, filename_post in git_logs_articles:
            total_articles += 1

            article_path = MIRROR_ROOT + "/" + filename_path_pre

            if( not os.path.exists(JSON_INBOX_ROOT) ):
                os.makedirs(JSON_INBOX_ROOT)

            article_target_path = os.path.join(JSON_INBOX_ROOT, filename_post)

            try:
                shutil.copy2(article_path, article_target_path)
            except IOError as e:
                logger.warning("I/O error: {} when attempting copy from [{}] to [{}]".format(e.strerror, article_path, article_target_path))
            else:
                logger.info("Copied {} to JSON_INBOX. ({} articles copied.)".format(filename_path_pre, queued_articles))
                queued_articles += 1

        # archive git log file if we queued/copied everything ok
        if( total_articles == queued_articles ):
            processed_articles += total_articles

            if( not os.path.exists(QUEUEUR_INBOX_ARCHIVE) ):
                os.makedirs(QUEUEUR_INBOX_ARCHIVE)

            git_log_archive_path = os.path.join(QUEUEUR_INBOX_ARCHIVE, git_log_filename)

            try:
                shutil.move(git_log_path, git_log_archive_path)
            except IOError as e:
                logger.warning("I/O error: {} when attempting move [{}] to [{}]".format(e.strerror, git_log_path, git_log_archive_path))
            else:
                logger.info("Moved {} to QUEUER_INBOX's archive.".format(git_log_filename))

    logger.info("Processed {} HTML articles out of {} git log files.".format(processed_articles, len(git_log_filenames)))
    TIME_END = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("{} finished at {}.".format(os.path.basename(__file__),TIME_END))

    return(0)

if(__name__ == '__main__'):
    main()
    sys.exit(0)
