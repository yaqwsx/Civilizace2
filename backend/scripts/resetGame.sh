#!/usr/bin/env bash

set -xe

rm -rf _stickers
rm -rf _codes

rm db.sqlite3
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py setupgame $1
