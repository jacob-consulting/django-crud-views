"""
Django settings for the django-crud-views example project.

One self-contained example app per crud_views feature — see the home page.
"""

from pathlib import Path

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-example-project-do-not-use-in-production"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_bootstrap5",
    "crispy_forms",
    "crispy_bootstrap5",
    "ordered_model",
    "django_fsm",
    "django_tables2",
    "crud_views_object_detail",
    "polymorphic",
    "guardian",
    "crud_views.apps.CrudViewsConfig",
    "crud_views_workflow.apps.CrudViewsWorkflowConfig",
    "crud_views_polymorphic.apps.CrudViewsPolymorphicConfig",
    "crud_views_guardian.apps.CrudViewsGuardianConfig",
    "project",
    # example feature apps (one per crud_views feature)
    "library",
    "nested",
    "formsets",
    "workflow",
    "polymorphic_demo",
    "guardian_demo",
    "resources",
    "showcase",
    "object_detail",
    "conditional",
    "breadcrumbs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "crud_views.lib.context_processor.crud_views_context",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"

LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
    ("fr", _("French")),
    ("es", _("Spanish")),
    ("pt", _("Portuguese")),
    ("it", _("Italian")),
    ("zh-hans", _("Simplified Chinese")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# django-crud-views
CRUD_VIEWS_EXTENDS = "project/crud_views.html"
CRUD_VIEWS_BREADCRUMB_PREFIX = [{"title": _("Home"), "url_name": "home"}]

# crispy forms
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# django-tables2
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"

# crud_views_object_detail
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"
CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"
CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE = "solid"

# django-guardian
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]
ANONYMOUS_USER_NAME = None
