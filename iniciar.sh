#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [[ ! -f .venv/bin/python ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
