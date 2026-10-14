#!/usr/bin/env bash
set -e
pip install -r backend/requirements.txt
python backend/train_model.py
