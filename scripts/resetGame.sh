#!/usr/bin/env bash

rm /home/xmrazek7/Civilizace/db.sqlite3
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py create entities groups users state