# Party Scraper

## Intro

we have two scripts `run_morning.py` and `run_post.py`

- `run_morning.py` scrapes websites and sends todays events to discord
- `run_post.py` takes survey results and posts desired posts to instagram

other files in root folder are for running only parts of the program, debugging, testing etc.

## Configuration

- configuration is done via `configs/` directory
- each configuration has its own `.env.city` file with discord room and instagram tokens.

## How it works under the hooooood

main functionlity is implemented in `src/pipeline.py`

### morning script

1. scrapes club website with all events for that club, usually `/akce`.
2. gets URL and date of each event
3. filters only tomorrow's events
4. uses crawl4ai to scrape today's events details

### post script

// TODO

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
