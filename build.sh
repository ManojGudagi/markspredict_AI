#!/usr/bin/env bash
set -o errexit

echo "Installing Dependencies..."
pip install -r requirements.txt

echo "Collecting Static Files..."
python manage.py collectstatic --no-input

echo "Running Database Migrations..."
python manage.py migrate

echo "Training ML Models..."
python ml/train.py

echo "Build Completed Successfully!"
