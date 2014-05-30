# Makefile for North Korean Open Data Project
SHELL := /bin/bash
PROJECT-ROOT := $(dir $(CURDIR)/$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST)))
ts := $(shell /bin/date "+%Y%m%d-%H%M%S")

# Specific paths on internet to downloadable assets
SEED-DATA-ARCHIVE=https://www.dropbox.com/s/1j3hz10wpttoir2/seed-data.tar.gz?dl=1
SEED-TEST-ARCHIVE=https://www.dropbox.com/s/x9j5litr3bjz3g7/seed-test.tar.gz?dl=1

# Ports
MONGO-DB-PORT=28017
TEST-INPUT-PORT=8870
TEST-OUTPUT-PORT=8871

help:
	@echo ''
	@echo 'Makefile for North Korean Open Data Project'
	@echo ''
	@echo 'Usage:'
	@echo 'make install  			- initial setup after github checkout'
	@echo 'make seed-data			- load data from backup (or else data will generate from scratch)'
	@echo 'make clean    			- delete all data/configs except ./var/; revert to head of GitHub repo'
	@echo 'make clean-all			- clean like above but also delete ./var/'
	@echo ''
	@echo 'make update 			- run collectors to update production data and make backups'
	@echo 'make publish			- run reporters to process / analyze / visualize data and serve results'
	@echo ''
	@echo 'make backups    		- backup all below'
	@echo 'make backup-data		- backup /data/ directory to /var/backups/data_<TIMESTAMP>.tar.gz'
	@echo 'make backup-srv 		- backup /srv/ directory to /var/backups/var_<TIMESTAMP>.tar.gz'
	@echo 'make backup-logs		- backup /var/logs/ directory to /var/backups/logs_<TIMESTAMP>.tar.gz'
	@echo ''
	@echo 'make start-test-input-server 	- process all on local test/debug data'
	@echo 'make start-test-output-server	- serve outputs on local test/debug server'
	@echo 'make stop-test-input-server  	- revert inputs back to production mode'
	@echo 'make stop-test-output-server 	- revert outputs back to production mode'
	@echo 'make start-mongodb-server    	- start MongoDB server'
	@echo 'make test-mongodb-shell      	- start MongoDB shell attached to our MongoDB server'
	@echo 'make stop-mongodb-server     	- stop MongoDB server'
	@echo ''
	@echo 'make test-suite			- runs in order: install, seed-data, start-test-input-server, start-test-output-server, publish'
	@echo ''

###########################################################################
###########################################################################

# GENERAL MAKE COMMANDS INTENDED FOR USER:
#########################

# Installs all config files and sets you up for test environment
install: env etc .google_api.key seed-test

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

backups: backup-data backup-srv backup-logs

# Cleans everything but /var, to allow re-generation of data from scratch or backup
# THIS DELETES /etc/! So if you want to save configs in there, do so manually!
clean: stop-test-input-server stop-test-output-server stop-mongodb-server
	rm -rf data
	rm -rf env
	rm -rf etc
	rm -rf srv
	rm -rf test
	git reset --hard	# revert any modified file
	git clean -fd   	# delete unversioned

clean-all: stop-test-input-server stop-test-output-server stop-mongodb-server
	rm -rf data
	rm -rf env
	rm -rf etc
	rm -rf srv
	rm -rf test
	rm -rf var	# DIFFERENCE with clean
	git reset --hard
	git clean -fd

test-suite: install seed-data start-test-input-server start-test-output-server publish

.PHONY: install seed-data update publish backups clean clean-all test-suite
###########################################################################
###########################################################################


# COLLECTIONS OF DATA WORKERS:
#########################
collectors: collector_kcna

reporters: reporter_kcna

.PHONY: collectors reporters

# COLLECTOR_KCNA:
#########################
collector_kcna: dbimporter_kcna
	@:

dbimporter_kcna: jsonifier_kcna start-mongodb-server
	source ./env/bin/activate; python ./src/collectors/collector_kcna/dbimporter_kcna.py

jsonifier_kcna: queuer_kcna
	source ./env/bin/activate; python ./src/collectors/collector_kcna/jsonifier_kcna.py

queuer_kcna: mirror_kcna
	source ./env/bin/activate; python ./src/collectors/collector_kcna/queuer_kcna.py

mirror_kcna:
	./src/collectors/collector_kcna/mirror_kcna.sh full

.PHONY: collector_kcna dbimporter_kcna jsonifier_kcna queuer_kcna mirror_kcna

# REPORTER_KCNA:
#########################
reporter_kcna: choropleth-country-mentions-kcna
	@:

# code for choropleth visualization of country mentions over time from KCNA
choropleth-country-mentions-kcna: map_countries_kcna ./srv/public_html/nk_mention_map.css ./srv/public_html/nk_mention_map.html ./srv/public_html/nk_mention_map.js ./srv/public_html/topo_countries.json
	@:

./srv/public_html/nk_mention_map.css:
	@mkdir -p $(@D)
	@cp -p ./src/reporters/reporter_kcna/nk_mention_map/nk_mention_map.css ./srv/public_html/nk_mention_map.css

./srv/public_html/nk_mention_map.html:
	@mkdir -p $(@D)
	@cp -p ./src/reporters/reporter_kcna/nk_mention_map/nk_mention_map.html ./srv/public_html/nk_mention_map.html

./srv/public_html/nk_mention_map.js: copy-js-libs
	@mkdir -p $(@D)
	@cp -p ./src/reporters/reporter_kcna/nk_mention_map/nk_mention_map.js ./srv/public_html/nk_mention_map.js

copy-js-libs:
	rsync -rupE ./src/reporters/reporter_kcna/nk_mention_map/js/ ./srv/public_html/js/

# generate TopoJSON of country map in ./srv/public_html directory
./srv/public_html/topo_countries.json: ./data/reporter_kcna/output_topo_countries/topo_countries.json
	@mkdir -p $(@D)
	@cp -p ./data/reporter_kcna/output_topo_countries/topo_countries.json ./srv/public_html/topo_countries.json

./data/reporter_kcna/output_topo_countries/topo_countries.json: ./data/reporter_kcna/output_topo_countries/countries.json
	topojson -p adm0_a3 -o ./data/reporter_kcna/output_topo_countries/topo_countries.json ./data/reporter_kcna/output_topo_countries/countries.json

./data/reporter_kcna/output_topo_countries/countries.json: ./data/reporter_kcna/output_topo_countries/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp
	ogr2ogr -f GeoJSON ./data/reporter_kcna/output_topo_countries/countries.json ./data/reporter_kcna/output_topo_countries/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp

./data/reporter_kcna/output_topo_countries/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp: ./var/datasets/ne_110m_admin_0_countries.zip
	@mkdir -p $(@D)
	unzip -o ./var/datasets/ne_110m_admin_0_countries.zip -d ./data/reporter_kcna/output_topo_countries/ne_110m_admin_0_countries/

# generate prerequisitve country text search results from KCNA
map_countries_kcna: update start-mongodb-server
	source ./env/bin/activate; python ./src/reporters/reporter_kcna/map_countries_kcna.py

.PHONY: reporter_kcna choropleth-country-mentions-kcna copy-js-libs map_countries_kcna

###########################################################################
###########################################################################

# INSTALLATION HELPERS:
#########################
env:
	virtualenv env
	source ./env/bin/activate
	env/bin/pip install -r requirements.txt

#

etc: ./etc/nkir.ini
	@:

./etc/nkir.ini:
	@mkdir -p $(@D)
	touch ./etc/nkir.ini

#

# User needs to manually override contents of this file with actual Google API key
.google_api.key:
	touch .google_api.key

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

.PHONY: env etc seed-test

# SERVERS:
#########################
start-mongodb-server:
ifeq (,$(wildcard $(PROJECT-ROOT)etc/mongod.pid))
	mkdir -p srv/database
	@echo "Starting MongoDB server"
	mongod \
		--port=$(MONGO-DB-PORT) \
		--logappend \
		--logpath="$(PROJECT-ROOT)var/logs/mongodb.log" \
		--dbpath="$(PROJECT-ROOT)srv/database" \
		--pidfilepath="$(PROJECT-ROOT)etc/mongod.pid" \
		--fork
endif

test-mongodb-shell: start-mongodb-server
	mongo --shell --port=$(MONGO-DB-PORT)

stop-mongodb-server:
ifneq (,$(wildcard $(PROJECT-ROOT)etc/mongod.pid))
	kill `cat ./etc/mongod.pid`
	rm -f ./etc/mongod.pid
endif

start-test-input-server:
ifeq (,$(wildcard $(PROJECT-ROOT)etc/test-input-server.pid))
	source ./env/bin/activate; \
	pushd test/collector_kcna/mirror/www.kcna.co.jp; \
	python -m SimpleHTTPServer $(TEST-INPUT-PORT) & \
	srv_pid="$$!"; \
	popd; \
	sleep 1; \
	echo "$$srv_pid" | tee ./etc/test-input-server.pid
endif

stop-test-input-server:
ifneq (,$(wildcard $(PROJECT-ROOT)etc/test-input-server.pid))
	kill -9 `cat ./etc/test-input-server.pid`
	rm -f ./etc/test-input-server.pid
endif

start-test-output-server:
ifeq (,$(wildcard $(PROJECT-ROOT)etc/test-output-server.pid))
	mkdir -p srv/public_html
	source ./env/bin/activate; \
	pushd srv/public_html; \
	python -m SimpleHTTPServer $(TEST-OUTPUT-PORT) & \
	srv_pid="$$!"; \
	popd; \
	sleep 1; \
	echo "$$srv_pid" | tee ./etc/test-output-server.pid
endif

stop-test-output-server:
ifneq (,$(wildcard $(PROJECT-ROOT)etc/test-output-server.pid))
	kill -9 `cat ./etc/test-output-server.pid`
	rm -f ./etc/test-output-server.pid
endif

.PHONY: start-mongodb-server test-mongodb-shell stop-mongodb-server start-test-input-server stop-test-input-server start-test-output-server stop-test-output-server

# BACKUPS:
#########################
backup-data:
	tar -zcf data_$(ts).tar.gz data/
	@mkdir -p ./var/backups
	mv ./data_$(ts).tar.gz ./var/backups/data_$(ts).tar.gz

backup-srv:
	tar -zcf srv_$(ts).tar.gz srv/
	@mkdir -p ./var/backups
	mv ./srv_$(ts).tar.gz ./var/backups/srv_$(ts).tar.gz

backup-logs:
	pushd ./var/; tar -zcf logs_$(ts).tar.gz logs/; popd
	@mkdir -p ./var/backups
	mv ./var/logs_$(ts).tar.gz ./var/backups/logs_$(ts).tar.gz

.PHONY: backup-data backup-srv backup-logs
