# project/settings/development.py
from .base import *
import os

DEBUG = True
#ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', '<dbname>'),
        'USER': os.getenv('DB_USER', '<username>'),
        'PASSWORD': os.getenv('DB_PASSWORD', '<password>'),
        'HOST': os.getenv('DB_HOST', '<host>'),
        'PORT': os.getenv('DB_PORT', '<port>'),
    }
}

# Email settings (using Mailpit for local SMTP testing)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DISCOURSE_CONNECT_SECRET='<secret>'
DISCOURSE_SSO_RETURN_URL='<url>'
DISCOURSE_API_KEY='<key>'
DISCOURSE_INSTANCE_URL='<url>'
DISCOURSE_ADMIN_USERNAME='<username>'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.discourse': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


