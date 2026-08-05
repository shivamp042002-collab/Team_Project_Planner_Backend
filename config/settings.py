from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-local-dev-key-not-for-production"

DEBUG = True

ALLOWED_HOSTS = []

ROOT_URLCONF = "config.urls"

INSTALLED_APPS = []

MIDDLEWARE = []

# No ORM usage in this project; DATABASES is left unconfigured.
DATABASES = {}

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
