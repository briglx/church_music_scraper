#!/bin/bash

# Parse command-line arguments
while getopts ":a" opt; do
  case $opt in
    a)
      a_flag=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done


# Get the URL argument
shift $((OPTIND - 1))
url=$1

# Perform actions based on the URL and flag
if [ -n "$url" ]; then
  if [ "$a_flag" = true ]; then
    python main.py --site_url $url -a
  else
    python main.py --site_url $url
  fi
else
  echo "Please provide a valid URL."
fi
