#!/bin/bash
# get all PRs with specified label
RESULT=`curl -s https://api.github.com/search/issues?q=is:pr%20label:$1%20repo:OlegZharkov/content`
# check if PR is created by github-actions bot
TOTAL_COUNT=`jq '.items[]|select(.user.login == "github-actions[bot]")' <<< $RESULT`

echo $TOTAL_COUNT

if [ -z $TOTAL_COUNT ]; then
  exit 1
else
  exit 0
fi