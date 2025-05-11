import os
import dotenv
from pathlib import Path

# Define the base directory for the project.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load other environment variables as needed.
DISCOURSE_INSTANCE_URL = os.getenv('DISCOURSE_INSTANCE_URL', '<url>')

# Installed apps should include these core Django apps for the admin to function properly.
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps and your custom apps
    'django_extensions',
    'apps.discourse',
    'apps.forum_links',
]

# Middleware settings must include session, authentication, and message middleware.
# Note the order: SessionMiddleware should come before AuthenticationMiddleware.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # Required by admin (must be first)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Required by admin
    'django.contrib.messages.middleware.MessageMiddleware',  # Required by admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Template configuration including the DjangoTemplates backend.
# This tells Django how and where to load templates (including admin templates).
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Must be defined for admin to work
        'DIRS': [
                  BASE_DIR / 'templates',
                  BASE_DIR / 'myproject/templates',  # Add this if needed
                ],  # Optional: add your custom template directories here

        'APP_DIRS': True,  # Enables Django to search for templates in each app’s 'templates' directory
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Required by admin
                'django.contrib.auth.context_processors.auth',    # Required by admin
                'django.contrib.messages.context_processors.messages',  # Required by admin
                # Add the custom context processor:
                'apps.discourse.context_processors.discourse_forum_url',
            ],
        },
    },
]

# Other settings (e.g., DATABASES, STATIC_URL, etc.) should follow...

# Determine the current environment (default to 'development')
DJANGO_ENV = os.getenv("DJANGO_ENV", "development")

# Load the corresponding .env file
env_file = f".env.{DJANGO_ENV}"
dotenv.load_dotenv(env_file)

# Now, variables from the selected .env file are available via os.getenv()
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DEBUG") == "True"

# Database settings (example)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

# Additional settings like EMAIL, Discourse, etc.
# STATIC_URL is the URL prefix for static files.
STATIC_URL = '/static/'

# Optionally, for serving static files in production, define where static files will be collected.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Optionally, if you have additional static directories in your project (besides each app's static/)
# you can add them here.
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

ALLOWED_HOSTS = ['*']  # Or use '*' for development

ROOT_URLCONF = 'myproject.urls'

LOGIN_REDIRECT_URL = "/discourse/session/sso_provider/?sso={sso}&sig={sig}"
#LOGIN_REDIRECT_URL = "/discourse/session/sso_provider/"
