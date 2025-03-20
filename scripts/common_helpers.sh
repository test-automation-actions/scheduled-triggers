#!/bin/bash

# Common helper functions can be added here

# Example: Function to log messages
log_message() {
  local MESSAGE=$1
  echo "$(date +"%Y-%m-%d %H:%M:%S") - $MESSAGE"
}
