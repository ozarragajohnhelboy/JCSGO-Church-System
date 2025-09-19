#!/bin/bash

# Church Management System Django Project Deployment Script for AWS EC2
# Simple deployment without Docker or complex services
# This version uses home directory instead of /var/www

echo "Starting Church Management System deployment..."

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip if not already installed
echo "Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install nginx
echo "Installing nginx..."
sudo apt install -y nginx

# Create application directory in home
echo "Setting up application directory..."
APP_DIR="/home/$USER/church-app"
mkdir -p $APP_DIR

# Copy project files (assuming you're running this from the project directory)
echo "Copying project files..."
cp -r . $APP_DIR/

# Navigate to project directory
cd $APP_DIR

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit $APP_DIR/.env with your production settings!"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=church.settings_production

# Run migrations
echo "Running database migrations..."
python manage.py migrate --settings=church.settings_production

# Create superuser (optional - you can do this manually)
echo "Creating superuser (optional)..."
echo "You can create a superuser manually by running:"
echo "cd $APP_DIR && source venv/bin/activate"
echo "python manage.py createsuperuser --settings=church.settings_production"

# Set up nginx configuration
echo "Setting up nginx configuration..."
sudo tee /etc/nginx/sites-available/church > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $APP_DIR/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/church /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Create systemd service for Gunicorn
echo "Creating systemd service for Gunicorn..."
sudo tee /etc/systemd/system/church.service > /dev/null <<EOF
[Unit]
Description=Church Management System Django Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=church.settings_production"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 church.wsgi_production:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the service
sudo systemctl daemon-reload
sudo systemctl start church
sudo systemctl enable church

# Check service status
echo "Checking service status..."
sudo systemctl status church --no-pager

echo ""
echo "Deployment completed!"
echo "Your application should now be running at http://your-server-ip"
echo "Application directory: $APP_DIR"
echo ""
echo "Useful commands:"
echo "  Check service status: sudo systemctl status church"
echo "  Restart service: sudo systemctl restart church"
echo "  View logs: sudo journalctl -u church -f"
echo "  Check nginx status: sudo systemctl status nginx"
echo "  View nginx logs: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "To create a superuser, run:"
echo "  cd $APP_DIR && source venv/bin/activate"
echo "  python manage.py createsuperuser --settings=church.settings_production"
echo ""
echo "Don't forget to:"
echo "  1. Edit $APP_DIR/.env with your production settings"
echo "  2. Update ALLOWED_HOSTS in .env with your server IP/domain"
echo "  3. Configure your firewall to allow HTTP (port 80) traffic"
echo "  4. Set up SSL certificate for HTTPS (recommended)"
