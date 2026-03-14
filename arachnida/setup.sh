#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x ./arachnida/00_spider/spider.py
chmod +x ./arachnida/01_scorpion/scorpion.py