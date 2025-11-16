#!/bin/bash

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Update dependencies
echo "Updating Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --settings=church.settings_production

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=church.settings_production

# Restart the application service
echo "Restarting application service..."
sudo systemctl restart church

# Check service status
echo "Checking service status..."
sudo systemctl status church --no-pager

echo ""
echo "Update completed!"
echo ""
echo "Useful commands:"
echo "  Check service status: sudo systemctl status church"
echo "  View logs: sudo journalctl -u church -f"
echo "  Restart service: sudo systemctl restart church"
