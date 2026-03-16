# Party Scraper

## Intro

we have two scripts `run_morning.py` and `run_post.py`

- `run_morning.py` scrapes websites and sends todays events to discord
- `run_post.py` takes survey results and posts desired posts to instagram

other files in root folder are for running only parts of the program, debugging, testing etc.

## Configuration

- configuration is done via `configs/` directory
- each configuration has its own `.env.city` file with discord room and instagram tokens.

## Run locally

use `run-locally.sh` script

```bash
chmod +x run-locally.sh
./run-locally.sh
```

## Run on server

to run party-scraper at certain times, use `cron`

command: `crontab -e`
content:

```bash
0 8 * * * /home/ubuntu/party-scraper/run-on-server.sh brno morning

1 0 * * * /home/ubuntu/party-scraper/run-on-server.sh brno post
```
