#!/usr/bin/env bash

set -e

. .env/bin/activate

while :
do
    date
    git pull
    pip install -r requirements.txt
    python manage.py tailwind install
    python manage.py tailwind build
    python manage.py collectstatic --noinput
    scripts/resetGame.sh
    sudo systemctl restart gunicorn

    while :
    do
        sleep 61
        git fetch
        if git status | grep 'behind'
        then
            break
        fi
    done
done
