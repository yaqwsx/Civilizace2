#!/usr/bin/env bash

rsync -a --progress \
    --exclude _graphics \
    --exclude _build \
    --exclude buildingSraping/ \
    --exclude graphics/ \
    --exclude db.sqlite3 \
    --exclude _static \
    --exclude '*__pycache__*' \
    ./ 192.168.1.11:Civilizace2