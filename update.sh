#!/bin/bash

# Church Management System Update Script (Home Directory Version)
# Use this script to update your deployed application

echo "Starting Church Management System update..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Please run this script from the project root directory."
    exit 1
fi

# Set application directory
APP_DIR="/home/$USER/church-app"

if [ ! -d "$APP_DIR" ]; then
    echo "Error: Application directory $APP_DIR not found. Please run deploy_home.sh first."
    exit 1
fi

echo "Backing up current application..."
cp -r $APP_DIR $APP_DIR.backup.$(date +%Y%m%d_%H%M%S)

echo "Copying updated files..."
# Copy all files except venv, logs, and media
rsync -av --exclude='venv/' --exclude='logs/' --exclude='media/' --exclude='.git/' --exclude='__pycache__/' --exclude='*.pyc' . $APP_DIR/

# Navigate to application directory
cd $APP_DIR

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
echo ""
echo "If you encounter any issues, you can restore from backup:"
echo "  rm -rf $APP_DIR"
echo "  mv $APP_DIR.backup.YYYYMMDD_HHMMSS $APP_DIR"
echo "  sudo systemctl restart church"
