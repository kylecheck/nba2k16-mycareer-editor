#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 was not found. Send this error back for troubleshooting.'
  read -r -p 'Press Enter to close.'
  exit 1
fi
python3 app.py
result=$?
if [ "$result" -ne 0 ]; then
  echo 'The editor could not start. See startup-error.txt in this folder.'
  read -r -p 'Press Enter to close.'
fi
exit "$result"
