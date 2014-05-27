# Makefile for North Korean Open Data Project
SHELL := /bin/bash
PROJECT-ROOT := $(dir $(CURDIR)/$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))

# Specific paths on internet to downloadable assets
SEED-DATA-ARCHIVE=https://www.dropbox.com/s/1j3hz10wpttoir2/seed-data.tar.gz?dl=1
SEED-TEST-ARCHIVE=https://www.dropbox.com/s/x9j5litr3bjz3g7/seed-test.tar.gz?dl=1

# Ports for testing
TEST-MIRROR-PORT=8870
TEST-OUTPUT-PORT=8871

help:
	@echo ''
	@echo 'Makefile for North Korean Open Data Project'
	@echo ''
	@echo 'Usage:'
	@echo 'make install  			- initial setup after github checkout'
	@echo 'make seed-data			- load data from backup (or else data will generate from scratch)'
	@echo 'make clean    			- delete all data/configs except ./var/; revert to head of GitHub repo'
	@echo ''
	@echo 'make update 			- run collectors to update production data and make backups'
	@echo 'make publish			- run reporters to process / analyze / visualize data and serve results'
	@echo ''
	@echo 'make test-inputs-enabled  	- process all on local test/debug data'
	@echo 'make test-outputs-enabled 	- serve outputs on local test/debug server'
	@echo 'make test-inputs-disabled 	- revert inputs back to production mode'
	@echo 'make test-outputs-disabled	- revert outputs back to production mode'
	@echo ''

###########################################################################
###########################################################################

# GENERAL MAKE COMMANDS INTENDED FOR USER:
#########################

# Installs all config files and sets you up for test environment
install: env etc seed-test

# If you don't seed-data from an existing backup,all data will be generated
#  from scratch on first run through.
seed-data: ./var/assets/seed-data.tar.gz
	rm -rf data
	mkdir -p data
	tar -zxf var/assets/seed-data.tar.gz -C data

# Runs collectors to update production data and make backups
update: collectors

# Runs reporters to process / analyze / visualize data and serve results
publish: reporters

# Cleans everything but /var, to allow re-generation of data from scratch or backup
# THIS DELETES /etc/! So if you want to save configs in there, do so manually!
clean: test-inputs-disabled test-outputs-disabled
	rm -rf data
	rm -rf env
	rm -rf etc
	rm -rf test
	git reset --hard	# revert any modified file
	git clean -fd   	# delete unversioned

###########################################################################
###########################################################################


# COLLECTIONS OF DATA WORKERS:
#########################
collectors: collector_kcna

reporters: reporter_kcna


# COLLECTOR_KCNA:
#########################
collector_kcna: queuer_kcna

queuer_kcna: mirror_kcna
	source ./env/bin/activate
	python ./src/collectors/collector_kcna/queuer_kcna.py

mirror_kcna:
	./src/collectors/collector_kcna/mirror_kcna.sh full


# REPORTER_KCNA:
#########################
reporter_kcna: map_countries_kcna


###########################################################################
###########################################################################

# INSTALLATION HELPERS:
#########################
env:
	virtualenv env
	source ./env/bin/activate
	env/bin/pip install -r requirements.txt

#

etc: ./etc/mongodb.config ./etc/nkir.ini

./etc/mongodb.config:
	@mkdir -p $(@D)
	touch ./etc/mongodb.config
	# MongoDB needs absolute path specified to database in config files
	@echo "dbpath=$(PROJECT-ROOT)srv/database" | tee ./etc/mongodb.config

./etc/nkir.ini:
	@mkdir -p $(@D)
	touch ./etc/nkir.ini

#

# seed-data:

./var/assets/seed-data.tar.gz:
	@mkdir -p $(@D)
	curl -L -o var/assets/seed-data.tar.gz $(SEED-DATA-ARCHIVE)

#

seed-test: ./var/assets/seed-test.tar.gz
	rm -rf test
	mkdir -p test
	tar -zxf var/assets/seed-test.tar.gz -C test

./var/assets/seed-test.tar.gz:
	@mkdir -p $(@D)
	curl -L -o var/assets/seed-test.tar.gz $(SEED-TEST-ARCHIVE)


# TEST MODES:
#########################
test-inputs-enabled:
	@mkdir -p etc
	touch ./etc/test-inputs-enabled.flag
	source ./env/bin/activate
	@(pushd test/collector_kcna/mirror/www.kcna.co.jp; \
	python -m SimpleHTTPServer $(TEST-MIRROR-PORT) & \
	srv_pid="$$!"; \
	popd; \
	sleep 1; \
	echo "$$srv_pid" | tee ./etc/srv.pid)

test-inputs-disabled: stop-test-server
	rm -f ./etc/test-inputs-enabled.flag

stop-test-server:
	kill -9 `cat ./etc/srv.pid`
	rm -f ./etc/srv.pid

test-outputs-enabled:
	@mkdir -p etc
	touch ./etc/test-outputs-enabled.flag

test-outputs-disabled:
	rm -f ./etc/test-outputs-enabled.flag
