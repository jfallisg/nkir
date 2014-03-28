# Makefile for NKIR data analysis project

KCNAARCHIVE=https://dl.dropboxusercontent.com/s/5bdom93ej8xcbmd/www.kcna.co.jp.zip?dl=1

help:
	@echo 'Makefile for the NKIR data analysis project			'
	@echo '														'
	@echo 'Usage:												'
	@echo 'make clean		initial setup after github checkout	'
	@echo 'make seed_mirror	populate mirror with an archive		'
	@echo 'make sandbox		make a sandbox version of kcna site	'
	@echo 'make day_update	update mirror w/ new articles		'
	@echo 'make full_mirror	full mirror and build zip archive	'
	@echo '														'

clean:
	rm -Rf data
	mkdir -p data/collector_kcna
	mkdir -p data/collector_kcna/inbox_db
	mkdir -p data/collector_kcna/inbox_json
	mkdir -p data/collector_kcna/logs
	mkdir -p data/collector_kcna/mirror
	rm -Rf env
	virtualenv env
	./env/bin/pip install -r requirements.txt

seed_mirror: clean
	curl -L -o data/collector_kcna/mirror/kcnaarchive.zip $(KCNAARCHIVE)
	unzip data/collector_kcna/mirror/kcnaarchive.zip -d data/collector_kcna/mirror
	rm data/collector_kcna/mirror/kcnaarchive.zip

sandbox:
	mkdir -p ./sandbox_kcna
	curl -L -o ./sandbox_kcna/kcnaarchive.zip $(KCNAARCHIVE)
	unzip ./sandbox_kcna/kcnaarchive.zip -d ./sandbox_kcna
	rm ./sandbox_kcna/kcnaarchive.zip

day_update:
	./src/collectors/collector_kcna/mirror_kcna.sh daily

full_mirror:
	./src/collectors/collector_kcna/mirror_kcna.sh -z full