#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# If running from repository root, navigate into config directory
if [ -d "config" ]; then
    cd config
fi

echo "Installing Dependencies..."
pip install -r requirements.txt

echo "Collecting Static Files..."
python manage.py collectstatic --no-input

echo "Running Database Migrations..."
python manage.py migrate

echo "Training & Saving ML Models..."
python ml/train.py

echo "Build Completed Successfully!"
