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

python run_${SCRIPT_TYPE}.py --config configs/${CITY}.yaml