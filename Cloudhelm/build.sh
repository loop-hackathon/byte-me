#!/usr/bin/env bash
# exit on error
set -o errexit

# Install backend dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

echo "Build completed successfully!"
