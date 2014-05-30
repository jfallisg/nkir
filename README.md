# NKODP - The North Korean Open Data Project

*a North Korean international relations data science, analytics and visualization project*

***

## Requirements

- [git](http://git-scm.com/)
- [GNU Make](http://www.gnu.org/software/make/)
- [virtualenv for Python](http://virtualenv.readthedocs.org/en/latest/) for Python
- [GNU Wget](https://www.gnu.org/software/wget/) \*
- [mongoDB](http://www.mongodb.org/) \*

*with \* signifying that on Mac OS, required software will have the following prerequisites:*

- [Xcode command line tools](http://railsapps.github.io/xcode-command-line-tools.html)
- [Homebrew](http://brew.sh/)

***

## Installation

1. Clone the project's Github repo locally:

		cd ~/dev
		mkdir nkir
		cd nkir
		git clone https://github.com/jfallisg/nkir.git .

2. Run make to install project

		make install

3. MANUALLY enter your Google API key in the file "{YOUR_PROJECT_ROOT/.google_api.key".

4. (optional) seed data from a backup so you don't have to start data from scratch

		make seed-data

5. (if testing inputs) start the test input HTTP server to not scrape target [kcna.co.jp](http://www.kcna.co.jp/index-e.htm) website.

		make start-test-input-server

6. (if testing outputs) start the test output HTTP server to display visualization locally at [localhost:8871/nk_mention_map.html](http://localhost:8871/nk_mention_map.html).

		make start-test-output-server

***

## Running

*Collectors* are sets of scripts that run as scheduled jobs to repopulate input data. These are run manually or added to a schedular like `cron`, and invoked with `make update`.

*Reporters* are sets of scripts that pull from the NKODP data to create hostable web resources, invoked with `make publish`.

Currently a run of `make publish` will invoke a run of `make update` to make sure all data is updated and available in the srv/public_html directory.

### Add this to a scheduler on your server, or run it locally:

	make publish

With that simple make command, data processing will occur as in the following:

#### Collector - KCNA

1. mirror_kcna.sh runs, mirroring [kcna.co.jp](http://www.kcna.co.jp/index-e.htm) locally

2. queuer_kcna.py runs, reading git commit logs and queueing html articles that have changed or are new

3. jsonifier_kcna.py runs, creating JSON documents of each article in our MongoDB schema

4. dbimporter_kcna.py runs, importing our queued JSON documents in to our MongoDB database

#### Reporter - Map Country Mentions

1. map_countries_kcna.py runs, which updates our article/country data for our published visualization

2. html/css/js deployment to web server, along with updated data files for our visualization
