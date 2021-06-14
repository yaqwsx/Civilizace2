#!/usr/bin/env bash

rm -r _stickers
rm -r _codes

rm db.sqlite3
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py create entities groups users state
