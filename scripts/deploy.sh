#!/usr/bin/env bash

rsync -a --progress \
    --exclude _graphics \
    --exclude _build \
    --exclude buildingSraping/ \
    --exclude graphics/ \
    --exclude db.sqlite3 \
    --exclude _static \
    ./ 192.168.1.216:Civilizace/app