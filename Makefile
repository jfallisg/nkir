# Makefile for NKIR data analysis project
SHELL := /bin/bash
PROJECT-ROOT := $(dir $(CURDIR)/$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))

COLLECTOR-KCNA-ARCHIVE=https://www.dropbox.com/s/diqb76tphbkssbt/collector_kcna.tar.gz?dl=1

# GENERAL MAKE COMMANDS:
#########################

# make install -> have this install everything to run in production along with dummy data for running in test mode
install: etc

seed-data: ./var/backups/collector_kcna.tar.gz
	mkdir -p data
	tar -zxf var/backups/collector_kcna.tar.gz -C data

# make update -> run collectors to update production data, make backups
update: collector-kcna

#clean-install:
#clean-update:
# make test-update (point at test data for all sources, update local test data)
#test-update:
# make clean-test-update (wipe out and redo from start)
#clean-test-update:
#publish:
#test-publish:

# COLLECTIONS OF FILES:
#########################

etc: ./etc/mongodb.config ./etc/nkir.ini

collector-kcna: mirror-kcna

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

# APPLICATION EXECUTIONS:
mirror-kcna:
	./src/collectors/collector_kcna/mirror_kcna.sh stuff
