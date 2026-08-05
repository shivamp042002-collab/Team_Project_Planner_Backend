"""
Minimal Django settings for this project.

Persistence for this project is local file storage (JSON files under db/),
not the Django ORM — see repositories/base_repository.py. Django is used
here as the mandated application framework / project scaffold, so this
settings module intentionally omits INSTALLED_APPS entries for models,
and does not configure a real database backend.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-local-dev-key-not-for-production"

DEBUG = True

ALLOWED_HOSTS = []

ROOT_URLCONF = "config.urls"

# No database-backed apps are used (see module docstring), so INSTALLED_APPS
# is kept minimal rather than including the full default Django app list.
INSTALLED_APPS = []

MIDDLEWARE = []

# No ORM usage in this project; DATABASES is left unconfigured.
DATABASES = {}

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
