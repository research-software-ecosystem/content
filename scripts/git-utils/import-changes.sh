#!/bin/bash
# Please note, all the changes should be BEFORE this script
# if the importing PR exists already, the argument has to be true, otherwise false
git config --local user.email "tpe-bot@github.com"
git config --local user.name "Tools Platform Ecosystem bot"
git add .
if git commit -m "bioconda import on $(date)"; then
  if (( $1 == true )); then
    git push
  else
    git checkout -b bioconda_import-${{ github.run_id }}
    git push --set-upstream origin "bioconda_import${{ github.run_id }}"
    hub pull-request -m "bioconda import on $(date)" -l "bioconda-import"
  fi
else
  echo "nothing new to add, exiting"
fi