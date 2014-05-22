# Makefile for North Korean Open Data Project
SHELL := /bin/bash
PROJECT-ROOT := $(dir $(CURDIR)/$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))

# Specific paths on internet to downloadable assets
COLLECTOR-KCNA-ARCHIVE=https://www.dropbox.com/s/diqb76tphbkssbt/collector_kcna.tar.gz?dl=1

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
install: etc

# If you don't seed-data from an existing backup,all data will be generated
#  from scratch on first run through.
seed-data: ./var/backups/collector_kcna.tar.gz
	mkdir -p data
	tar -zxf var/backups/collector_kcna.tar.gz -C data

# Runs collectors to update production data and make backups
update: collectors

# Runs reporters to process / analyze / visualize data and serve results
publish: reporters

# Cleans everything but /var, to allow re-generation of data from scratch or backup
# THIS DELETES /etc/! So if you want to save configs in there, do so manually!
clean:
	rm -rf data
	rm -rf etc
	git reset --hard	# revert any modified file
	git clean -fd   	# delete unversioned

###########################################################################
###########################################################################

# COLLECTIONS OF DATA WORKERS:
#########################
collectors: collector-kcna

reporters: reporter-kcna

# SPECIFIC WORKERS:
#########################
collector-kcna: mirror-kcna

reporter-kcna: map-countries-kcna

# COLLECTIONS OF FILES:
#########################
etc: ./etc/mongodb.config ./etc/nkir.ini

# SPECIFIC FILES:
#########################
./etc/mongodb.config:
	@mkdir -p $(@D)
	touch ./etc/mongodb.config
	# MongoDB needs absolute path specified to database in config files
	@echo "dbpath=$(PROJECT-ROOT)srv/database" | tee ./etc/mongodb.config

./etc/nkir.ini:
	@mkdir -p $(@D)
	touch ./etc/nkir.ini

./var/backups/collector_kcna.tar.gz:
	@mkdir -p $(@D)
	curl -L -o var/backups/collector_kcna.tar.gz $(COLLECTOR-KCNA-ARCHIVE)

# SCRIPT CALLS:
#########################
mirror-kcna:
	./src/collectors/collector_kcna/mirror_kcna.sh stuff

# TEST MODES:
#########################
test-inputs-enabled:
	@mkdir -p etc
	touch ./etc/test-inputs-enabled.flag

test-inputs-disabled:
	rm -f ./etc/test-inputs-enabled.flag

test-outputs-enabled:
	@mkdir -p etc
	touch ./etc/test-outputs-enabled.flag

test-outputs-disabled:
	rm -f ./etc/test-outputs-enabled.flag
