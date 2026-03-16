#!/bin/bash

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <city> <script_type>"
  echo "script_type: morning | post"
  exit 1
fi

CITY="$1"
SCRIPT_TYPE="$2"

if [ "$SCRIPT_TYPE" != "morning" ] && [ "$SCRIPT_TYPE" != "post" ]; then
  echo "Invalid script_type. Use 'morning' or 'post'."
  exit 1
fi

cd /home/ubuntu/party-scraper && \
/home/ubuntu/party-scraper/venv/bin/python \
/home/ubuntu/party-scraper/run_${SCRIPT_TYPE}.py \
--config /home/ubuntu/party-scraper/configs/${CITY}.yaml \
>> /home/ubuntu/party-scraper/run_${SCRIPT_TYPE}.log 2>&1