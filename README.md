# NKIR

*a North Korean International Relations data science and analytics project*

***

## Requirements

- xcode command line tools (if on Mac OS)
- Homebrew (if on mac OS)
- wget
- git
- nginx (if doing development to run a local mirror)

***

## Installation

### Running on a server (production) or locally (development)

1. clone this repo locally
2. `make install`
3. `make seed-mirror`
4. add runs of `make update` to a scheduler like `cron`, daily

### Continue if running locally (development)

5. `make install-dev`
6. set up `nginx` to serve `http://localhost` with your development site mirror, for example by creating a symbolic link with `sudo ln -s ~/dev/nkir/test/mirror_kcna/www.kcna.co.jp /var/www/kcna.co.jp/public_html`.

Now you can update your local copy with `make update-dev` to pull from your local version of the site instead.
