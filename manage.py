#!/usr/bin/env python
import os
import sys
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

if __name__ == '__main__':
    # Determine the environment (defaults to 'development' if DJANGO_ENV is not set)
    ENV = os.environ.get("DJANGO_ENV", "development")
    dotenv_path = os.path.join(os.path.dirname(__file__), f".env.{ENV}")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        print(f"Warning: {dotenv_path} not found. Ensure you've set your environment variables.")

    # Set the settings module based on the environment.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'myproject.settings.{ENV}')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH? "
            "Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

