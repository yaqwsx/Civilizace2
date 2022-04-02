#!/usr/bin/env bash

rm core/migrations/*.py
touch core/migrations/__init__.py
rm game/migrations/*.py
touch game/migrations/__init__.py

scripts/resetGame.sh
