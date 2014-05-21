# NKODP - The North Korean Open Data Project

*a North Korean international relations data science, analytics and visualization project*

***

## Requirements

- [git](http://git-scm.com/)
- [GNU Make](http://www.gnu.org/software/make/)
- [virtualenv for Python](http://virtualenv.readthedocs.org/en/latest/) for Python
- [GNU Wget](https://www.gnu.org/software/wget/) \*
- [mongoDB](http://www.mongodb.org/)
- [nginx](http://nginx.org/) \*

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

3. (optional) seed data from a backup so you don't have to start data from scratch

		make seed-data

4. *Collectors* are sets of scripts that run as scheduled jobs to repopulate input data. Run manually or add to a schedular like `cron`

		make update

5. *Reporters* are sets of scripts that pull from the NKODP data to create hostable web resources

		make publish

***

## Running

### Collector - KCNA

ALL of these scripts are scheduled independently, and run when there's new stuff in their respective "INBOX"'s
1. mirror_kcna.sh runs, mirroring the KCNA site locally
	- prereq, can install from a backup
2. queuer_kcna.py runs, reading git commit logs and copying html
3. jsonifier_kcna.py runs, creating json docs of each article
4. dbimporter_kcna.py runs, importing stuff in to mongodb

### Reporter - Map Country Mentions

1. Scheduled: map_countries_kcna.py, which updates resources for vis
2. Deploy: updated files for vis to srv folder
	- prereq, can install from a backup
3. In Dev, you can then run a simple http server locally, or serve with nginx to the internet!
