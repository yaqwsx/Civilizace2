#!/usr/bin/env bash

rm db.sqlite3
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py create entities groups users state