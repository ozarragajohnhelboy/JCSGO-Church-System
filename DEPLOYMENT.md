# Church Management System - AWS Deployment Guide

This guide will help you deploy the Church Management System to AWS EC2 using a simple setup without Docker or complex services.

## Prerequisites

1. An AWS EC2 instance running Ubuntu 20.04 LTS or later
2. SSH access to your EC2 instance
3. Security group configured to allow HTTP (port 80) and SSH (port 22) traffic

## Deployment Steps

### 1. Prepare Your EC2 Instance

Connect to your EC2 instance via SSH:

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. Upload Your Project

Upload your project files to the EC2 instance. You can use SCP, SFTP, or Git:

**Option A: Using SCP (from your local machine)**

```bash
scp -i your-key.pem -r . ubuntu@your-ec2-ip:/home/ubuntu/church-project/
```

**Option B: Using Git (on EC2 instance)**

```bash
git clone your-repository-url
cd your-repository-name
```

### 3. Run the Deployment Script

Navigate to your project directory and run the deployment script:

```bash
cd /home/ubuntu/church-project  # or wherever you uploaded the files
chmod +x deploy.sh
./deploy.sh
```

The deployment script will:

- Update system packages
- Install Python 3, pip, and nginx
- Set up the application directory at `/var/www/church`
- Create a virtual environment
- Install Python dependencies
- Configure nginx as a reverse proxy
- Set up Gunicorn as the WSGI server
- Create a systemd service for the application

### 4. Configure Environment Variables

After deployment, edit the environment file:

```bash
sudo nano /var/www/church/.env
```

Update the following variables:

```env
SECRET_KEY=your-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-ec2-ip,your-domain.com,localhost,127.0.0.1

# Email Configuration (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 5. Create a Superuser

Create an admin user for the application:

```bash
cd /var/www/church
source venv/bin/activate
python manage.py createsuperuser --settings=church.settings_production
```

### 6. Restart Services

Restart the application service to apply changes:

```bash
sudo systemctl restart church
sudo systemctl restart nginx
```

## Updating Your Application

To update your deployed application with new code changes:

1. Upload your updated code to the EC2 instance
2. Run the update script:

```bash
./update.sh
```

The update script will:

- Backup the current application
- Copy updated files
- Update dependencies
- Run database migrations
- Collect static files
- Restart the application service

## Useful Commands

### Service Management

```bash
# Check application status
sudo systemctl status church

# Restart application
sudo systemctl restart church

# View application logs
sudo journalctl -u church -f

# Check nginx status
sudo systemctl status nginx

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Application Management

```bash
# Access the application directory
cd /var/www/church

# Activate virtual environment
source venv/bin/activate

# Run Django management commands
python manage.py [command] --settings=church.settings_production

# Create superuser
python manage.py createsuperuser --settings=church.settings_production

# Collect static files
python manage.py collectstatic --noinput --settings=church.settings_production

# Run migrations
python manage.py migrate --settings=church.settings_production
```

## Security Considerations

1. **Firewall**: Configure your EC2 security group to only allow necessary ports (22 for SSH, 80 for HTTP, 443 for HTTPS if using SSL)

2. **SSL Certificate**: Consider setting up SSL/TLS certificate using Let's Encrypt for HTTPS:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

3. **Environment Variables**: Never commit your `.env` file to version control. Keep your `SECRET_KEY` secure.

4. **Database**: For production, consider using a managed database service like AWS RDS instead of SQLite.

## Troubleshooting

### Application Not Starting

```bash
# Check service status
sudo systemctl status church

# View detailed logs
sudo journalctl -u church -f

# Check if port 8000 is in use
sudo netstat -tlnp | grep 8000
```

### Nginx Issues

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:www-data /var/www/church
sudo chmod -R 755 /var/www/church
```

## File Structure After Deployment

```
/var/www/church/
├── church/                 # Django project directory
├── churches/               # Churches app
├── members/                # Members app
├── templates/              # HTML templates
├── static/                 # Static files source
├── staticfiles/            # Collected static files
├── media/                  # User uploaded files
├── logs/                   # Application logs
├── venv/                   # Python virtual environment
├── .env                    # Environment variables
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── db.sqlite3             # SQLite database
```

## Support

If you encounter any issues during deployment, check the logs and ensure all prerequisites are met. The application should be accessible at `http://your-ec2-ip` after successful deployment.
