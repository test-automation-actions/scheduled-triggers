#!/bin/bash

REPO=$1
ENVIRONMENT=$2

# Trigger the workflow in the specified repository and environment
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$REPO/actions/workflows/notify.yml/dispatches \
  -d "{\"ref\":\"main\",\"inputs\":{\"repo\":\"$REPO\",\"environment\":\"$ENVIRONMENT\"}}"
