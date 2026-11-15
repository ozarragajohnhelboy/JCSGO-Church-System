import os

from django.core.exceptions import ImproperlyConfigured


def get_databases():
    """PostgreSQL only. Run the app through Docker Compose."""
    host = os.getenv('POSTGRES_HOST')
    password = os.getenv('POSTGRES_PASSWORD')

    if not host:
        raise ImproperlyConfigured(
            'POSTGRES_HOST is required. Start the app with Docker Compose '
            'and run management commands with: '
            'docker compose exec web python manage.py <command>'
        )
    if not password:
        raise ImproperlyConfigured('POSTGRES_PASSWORD is required.')

    return {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'jcsgo'),
            'USER': os.getenv('POSTGRES_USER', 'jcsgo'),
            'PASSWORD': password,
            'HOST': host,
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
