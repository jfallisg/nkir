# Makefile for NKIR data analysis project
SHELL := /bin/bash
PROJECT-ROOT := $(dir $(CURDIR)/$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))

KCNA-ARCHIVE=https://dl.dropboxusercontent.com/s/dhjjwmalmm6fewf/www.kcna.co.jp.tar.gz?dl=1

# GENERAL MAKE COMMANDS:
#########################

# make install -> have this install everything to run in production along with dummy data for running in test mode
install: etc

#clean-install:

# make update -> run collectors to update production data, make backups
#update:

#clean-update:

# make load from backup?

# make test-update (point at test data for all sources, update local test data)
#test-update:

# make clean-test-update (wipe out and redo from start)
#clean-test-update:

#publish:

#test-publish:

# SPECIFIC MAKE OPERATIONS:
#########################
etc: ./etc/mongodb.config ./etc/nkir.ini

./etc/mongodb.config:
	@mkdir -p $(@D)
	touch ./etc/mongodb.config
	# MongoDB needs absolute path specified to database in config files
	@echo "dbpath=$(PROJECT-ROOT)srv/database" | tee ./etc/mongodb.config

./etc/nkir.ini:
	@mkdir -p $(@D)
	touch ./etc/nkir.ini

