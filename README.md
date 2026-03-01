##

we have two scripts `run_morning.py` and `run_post.py` and `run_get_ig_session.py`.

first one scrapes websites and sends todays events to discord
second one takes survey results and posts desired posts to instagram.
third one gets instagram session for a given city.

other files in root folder are for running only parts of the program, debugging, tes

##

configuration is done via `configs/` directory
each configuration has its own `.env.city` file with credentials and discord room.

##

each party-scraper has to have it's own `ig_session` for instagram authentication.
ig sessions are stored in `ig_sessions/` directory. to get the session run `run_get_ig_session.py` with config `python ./run_get_ig_session.py --config ./configs/brno.yaml`.
then put the whole `ig_sessions` folder to the server by `scp` or just anything, same as `.env` files.

##

to run party-scraper at certain times, use `cron`

command: `crontab -e`
content:

```bash
0 8 * * * /home/ubuntu/party-scraper/run.sh brno morning

1 0 * * * /home/ubuntu/party-scraper/run.sh brno post
```

##

```bash
scp -i "C:\Users\msuch\.ssh\oracle-cloud.key" -r "C:\Users\msuch\Desktop\programko\party-scraper\ig_sessions" ubuntu@130.61.72.167:~/party-scraper/
```
