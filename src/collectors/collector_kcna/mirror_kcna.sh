#!/bin/bash
# 
# `mirror_kcna.sh`
# 
# A wrapper for `wget` to allow optional configuration of local mirroring of
# http://www.kcna.co.jp.
# 
# INPUTS
#	- command line arguments
#	- KCNA news websites, sourced either from:
#		- http://www.kcna.co.jp
#		- http://localhost
# 
# OUTPUTS
# 	- Local mirrored copy of KCNA news website
#	- log with downloads strings that can be input to `kcna_queuer.py`
# 
# REQUIREMENTS
#	- wget
#	- git
#	- nginx if doing development to run mirror from http://localhost
# 
# http://github.com/jfallisg
# Spring, 2014
#############################################################################

script_timestamp=$(date +"%Y%m%d_%H%M%S")
script_root=$(pwd)
[[ $script_root =~ (^.*nkir).*$ ]]
project_root=${BASH_REMATCH[1]}

############
# CONSTANTS & WGET OPTIONS
######
wget=/usr/local/bin/wget	# if on Mac OS, wget installed via Homebrew
# wget=/ur/bin/wget			# uncomment/override above if on Linux

mirrorpath=$project_root/data/collector_kcna/mirror
logpath=$project_root/var/logs
queue_inbox_path=$project_root/data/collector_kcna/inbox_queuer
test_mirror_path=$project_root/test/mirror_kcna/www.kcna.co.jp

DIR_PREFIX="--directory-prefix=${mirrorpath}/www.kcna.co.jp"
ROBOTS_OFF="--execute robots=off"
#depth=""					# see variable declarations
DEPTH_DAILY="--level=3"
DEPTH_FULL=""
OVERRIDE_HOST_DIR="--no-host-directories"
SIMPLE_LOGGING="--no-verbose"
#console_logging=""			# see variable declarations
CONSOLE_LOGGING_VERBOSE="--output-file=/dev/stdout"
CONSOLE_LOGGING_NON_VERBOSE="--output-file=${logpath}/wget_${script_timestamp}.log"
RECURSIVE="--recursive"
#html_only=""				# see variable declarations
HTML_ONLY_DAILY="--reject mp3,gif"
HTML_ONLY_FULL=""
TIMESTAMPING="--timestamping"
WAIT_DELAY_DEV=""
WAIT_DELAY_PROD="--wait=0.001 --random-wait"
#url=""						# see variable declarations
URL_DEV="http://localhost/index-e.htm"
URL_PROD="http://www.kcna.co.jp/index-e.htm"
#log_file=""				# see variable declarations
LOG_FILE_VERBOSE="| tee ${logpath}/wget_${script_timestamp}.log"
LOG_FILE_NON_VERBOSE=""

# Currently unused wget options
#BACKUPS="--backups=99"
# USER_AGENT="--user-agent=\"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0\""
#wait_delay=""
############

############
# VARIABLES
######
mode_dev=0		# 0 == production mode
mode_verbose=0	# 0 == quiet mode
mode_mirror=""

depth=""
console_logging=""
html_only=""
wait_delay=""
url=""
log_file=""
############

#############################################################################

############
# GETOPTS
# consulted (http://wiki.bash-hackers.org/howto/getopts_tutorial)
######
function print_usage {
	echo "USAGE:" >&2
	echo " ./mirror_kcna.sh [-dv] daily|full" >&2
	echo "OPTIONAL FLAGS:" >&2
	echo " -d for \"development\", mirror from dev server http://localhost instead of production server http://www.kcna.co.jp" >&2
	echo " -v for \"verbose\", will log to console as well as to default ./<file>.log file" >&2
	echo "REQUIRED ARG:" >&2
	echo " daily | full" >&2
	echo "  specify \"daily\" to update mirror with the latest articles." >&2
	echo "  specify \"full\" to do a full site recursive mirror." >&2
	echo "EXAMPLES:" >&2
	echo " $ ./mirror_kcna.sh daily" >&2
	echo " $ ./mirror_kcna.sh -dv full" >&2
}

while getopts ":dv" opt; do
	case $opt in
		d)
			mode_dev=1
			;;
	    v)
			mode_verbose=1
			;;
		\?)
			"Invalid option: -$OPTARG" >&2
			print_usage;
			exit 2
			;;
	esac
done

shift $((OPTIND-1))		# shift req cmd ln arg in to $@
if [[ "$@" == "daily" ]] || [[ "$@" == "full" ]]; then
	mode_mirror=$@
else
	 echo "ERROR: choose \"daily\" or \"full\"" >&2; print_usage; exit 2;
fi

# if we are in dev mode, we need to make sure a kcna mirror is present, otherwise exit.
if [[ "$mode_dev" == "1" ]] && [[ ! -d "$test_mirror_path" ]]; then
	echo "ERROR: dev mode specified but you need a sandbox copy of the KCNA mirror.  Try \"make sandbox\"" >&2
	exit 2
fi

# if we are mirroring for the first time, and you've specified "daily" instead of "full", we need to override to "full" for this first run.
if [[ ! -d "$mirrorpath/www.kcna.co.jp" ]] && [[ "$mode_mirror" == "daily" ]]; then
	mode_mirror="full"
	echo "daily specified, but a full mirror doesn't exist yet, overriding to full mirror for this initial run."
fi

# check for wget and exit if it isn't installed
if [ ! -x "$wget" ]; then
	echo "ERROR: wget is required, please install and set path above." >&2
	exit 1
fi

# report on settings for this run.
printf "mirror_kcna.sh starting with: "
if [[ "$mode_dev" == 1 ]]; then
	printf "dev-mode, "
fi
if [[ "$mode_verbose" == 1 ]]; then
	printf "verbose-mode, "
fi
if [[ -n "$mode_mirror" ]]; then
	printf "mirror-mode: $mode_mirror.\n"
fi
############

############
# BUILD WGET COMMAND LINE STRING
######

# APPLY USERS' OPTIONS TO WGET CMD LINE
if [[ "$mode_dev" == 1 ]]; then
	url=$URL_DEV
	wait_delay=$WAIT_DELAY_DEV
else #not `-d` development mode
	url=$URL_PROD
	wait_delay=$WAIT_DELAY_PROD
fi

if [[ "$mode_verbose" == 1 ]]; then
	console_logging=$CONSOLE_LOGGING_VERBOSE
	log_file=$LOG_FILE_VERBOSE
else #not `-v` verbose mode
	console_logging=$CONSOLE_LOGGING_NON_VERBOSE
	log_file=$LOG_FILE_NON_VERBOSE
fi

if [[ "$mode_mirror" == "daily" ]]; then
	depth=$DEPTH_DAILY
	html_only=$HTML_ONLY_DAILY
elif [[ "$mode_mirror" == "full" ]]; then
	depth=$DEPTH_FULL
	html_only=$HTML_ONLY_FULL
fi

wget_cmd=(
	${wget}
	${DIR_PREFIX}
	${ROBOTS_OFF}
	${depth}
	${OVERRIDE_HOST_DIR}
	${SIMPLE_LOGGING}
	${console_logging}
	${RECURSIVE}
	${html_only}
	${TIMESTAMPING}
	${wait_delay}
	${url}
	${log_file}
	)

echo running: [ ${wget_cmd[@]} ] # print for debug
############

############
# Execute wget
######
${wget_cmd[@]}

wget_exit=( ${PIPESTATUS[0]} )

printf "done!\n\n"

if [[ "$wget_exit" > 1 ]] && [[ "$wget_exit}" < 8 ]]; then
	echo "WARNING: some wget error: $wget_exit; lookup on http://www.gnu.org/software/wget/manual/html_node/Exit-Status.html" >&2
elif [[ "$wget_exit" == 8 ]]; then
	echo "WARNING: server issued error response: possible broken links." >&2
fi
############

############
# update git repo of mirror
######
gitpath=$mirrorpath/www.kcna.co.jp
if [ ! -x "${gitpath}/.git/" ]; then
	git --git-dir=${gitpath}/.git init
fi
git --git-dir=${gitpath}/.git/ --work-tree=${gitpath} add .
git --git-dir=${gitpath}/.git/ --work-tree=${gitpath} commit --status -m "incremental update ${script_timestamp}" > $logpath/git_${script_timestamp}.log
git --git-dir=${gitpath}/.git/ --work-tree=${gitpath} log --name-status --pretty=format: -1 >> $logpath/git_${script_timestamp}.log

############

############
# copy git logs if they exist to inbox_queuer
######
echo "RIGHT HERE!"
echo "$logpath/git_${script_timestamp}.log"
echo "$queue_inbox_path"
echo "$queue_inbox_path/git_${script_timestamp}.log"
if [[ -f $logpath/git_${script_timestamp}.log ]]; then
	echo "up in here!"
	if [[ ! -d "$queue_inbox_path" ]]; then
		mkdir -p $queue_inbox_path
	fi
	cp $logpath/git_${script_timestamp}.log $queue_inbox_path/git_${script_timestamp}.log
fi

############

echo "mirror_kcna.sh complete"

#############################################################################