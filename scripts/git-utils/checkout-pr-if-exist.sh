#!/bin/bash
# get all opened PRs  with specified label
RESULT=`curl -s https://api.github.com/search/issues?q=is:pr%20state:open%20label:$1%20repo:bio-tools/content`
# check if PR is created by github-actions bot and return pull request-number
PR_NUMBER=`jq '.items[]|select(.user.login == "github-actions[bot]")|.number' <<< $RESULT`

# check if $PR_NUMBER is defined
if [ ! -z $PR_NUMBER ]; then
    echo $PR_NUMBER
    gh pr checkout $PR_NUMBER
    exit 0
else
  exit 1
fi
