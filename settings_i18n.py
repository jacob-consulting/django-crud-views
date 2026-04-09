"""
Minimal Django settings for running management commands (makemessages, compilemessages).
Usage:
    python -m django makemessages -l de --settings=settings_i18n
    python -m django compilemessages --settings=settings_i18n
"""

SECRET_KEY = "settings-i18n-only"
USE_I18N = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "crud_views",
    "crud_views_workflow",
]
