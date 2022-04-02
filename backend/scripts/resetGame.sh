#!/usr/bin/env bash

rm -rf _stickers
rm -rf _codes

rm db.sqlite3
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py create users