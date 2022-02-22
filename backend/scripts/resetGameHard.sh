#!/usr/bin/env bash

rm game/migrations/*.py
touch game/migrations/__init__.py
rm ground/migrations/*.py
touch ground/migrations/__init__.py

scripts/resetGame.sh