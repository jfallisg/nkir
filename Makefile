# Makefile for NKIR data analysis project
SHELL := /bin/bash
KCNAARCHIVE=https://dl.dropboxusercontent.com/s/dhjjwmalmm6fewf/www.kcna.co.jp.tar.gz?dl=1

help:
	@echo 'Makefile for the NKIR data analysis project				'
	@echo '															'
	@echo 'Usage:													'
	@echo 'make install			initial setup after github checkout	'
	@echo 'make install-dev		initial setup of dev/test tools		'
	@echo 'make seed_mirror 	populate mirror with an archive		'
	@echo 'make update			update mirror w/ new articles		'
	@echo 'make update-dev		update mirror in test environment	'
	@echo '															'


# GENERAL MAKE COMMANDS:
#########################

install: env var data srv

install-dev: test

update: kcna_mirror

update-dev: kcna_mirror_dev

rebuild-data: clean udpate

rebuild-test: clean-test dev

reinstall: clean-everything install

clean:
	rm -rf data
	rm -rf srv

clean-test:
	rm -rf test

clean-everything: clean clean-test
	rm -rf env
	rm -rf var

backup: archive_mirror

# TOP LEVEL DIRECTORIES:
#########################
env:
	virtualenv env
	env/bin/pip install -r requirements.txt

var:
	mkdir -p var/datasets
	mkdir -p var/logs

data: collector_kcna

srv:
	mkdir -p srv/api
	mkdir -p srv/database
	mkdir -p srv/pelican_site
	mkdir -p srv/reports

test: dev_mirror_kcna

# SPECIFIC MAKE OPERATIONS:
#########################
collector_kcna: seed_kcna_mirror
	mkdir -p data/collector_kcna/inbox_db
	mkdir -p data/collector_kcna/inbox_json
	mkdir -p data/collector_kcna/inbox_queuer

kcna_mirror:
	./src/collectors/collector_kcna/mirror_kcna.sh daily

kcna_full_mirror:
	./src/collectors/collector_kcna/mirror_kcna.sh full

kcna_mirror_dev:
	./src/collectors/collector_kcna/mirror_kcna.sh -d daily	

seed_kcna_mirror: var/archives/www.kcna.co.jp.tar.gz
	mkdir -p data/collector_kcna/mirror
	tar -zxf var/archives/www.kcna.co.jp.tar.gz -C data/collector_kcna/mirror

var/archives/www.kcna.co.jp.tar.gz:
	mkdir -p $(dir $@)
	curl -L -o var/archives/www.kcna.co.jp.tar.gz $(KCNAARCHIVE)

archive_mirror:
	pushd data/collector_kcna/mirror; tar -zcf www.kcna.co.jp.tar.gz www.kcna.co.jp/; popd
	mkdir -p var/archives
	mv data/collector_kcna/mirror/www.kcna.co.jp.tar.gz var/archives/www.kcna.co.jp.tar.gz

# TESTING:
#########################
dev_mirror_kcna: var/archives/www.kcna.co.jp.tar.gz
	mkdir -p test/mirror_kcna
	tar -zxf var/archives/www.kcna.co.jp.tar.gz -C test/mirror_kcna
