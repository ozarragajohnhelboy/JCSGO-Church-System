#!/bin/bash

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "Pulling latest changes..."
git pull origin main

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --settings=church.settings_production

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=church.settings_production

# Restart the application service
echo "Restarting application service..."
sudo systemctl restart church
sudo systemctl restart nginx

# Check service status
echo "Checking service status..."
sudo systemctl status church --no-pager

echo ""
echo "Update completed!"
