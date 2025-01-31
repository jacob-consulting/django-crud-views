import django
import pytest
from django.conf import settings
from pathlib import Path

from django.test import Client

from tests.lib.helper.user import user_viewset_permission


def pytest_configure():
    settings.configure(

        BASE_DIR=Path(__file__).resolve().parent.parent,
        SECRET_KEY='django-testing',
        DEBUG=True,
        ALLOWED_HOSTS=[],
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django_bootstrap5',
            'crispy_forms',
            'crispy_bootstrap5',
            'ordered_model',
            'django_tables2',
            "crud_views_bootstrap5.apps.CrudViewsBootstrap5Config",
            "crud_views.apps.CrudViewsConfig",
            'tests.test1.app',
        ],

        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],

        ROOT_URLCONF='tests.test1.project.urls',

        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                        'crud_views.lib.context_processor.crud_views_context'
                    ],
                },
            },
        ],

        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },

        # Internationalization
        LANGUAGE_CODE='en-us',
        TIME_ZONE='UTC',
        USE_I18N=True,
        USE_TZ=True,

        STATIC_URL='static/',

        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',

        # Django ViewSet configuration
        CRUD_VIEWS_THEME="bootstrap5",
        CRUD_VIEWS_EXTENDS="app/crud_views.html",

        # crispy
        CRISPY_TEMPLATE_PACK="bootstrap5",
        CRISPY_ALLOWED_TEMPLATE_PACKS="bootstrap5",

        # django_tables2
        DJANGO_TABLES2_TEMPLATE="django_tables2/bootstrap5.html",
    )

    django.setup()


@pytest.fixture
def user_a():
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_a", password="password")
    return user


@pytest.fixture
def cv_author():
    from tests.test1.app.views import cv_author as ret
    return ret



@pytest.fixture
def user_author_view(cv_author):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_author_view", password="password")

    user_viewset_permission(user, cv_author, "view")

    return user


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def client_user_author_view(client, user_author_view) -> Client:
    client.force_login(user_author_view)
    return client


@pytest.fixture
def user_author_change(cv_author):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_author_change", password="password")

    user_viewset_permission(user, cv_author, "change")

    return user


@pytest.fixture
def user_author_delete(cv_author):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_author_delete", password="password")

    user_viewset_permission(user, cv_author, "delete")

    return user


@pytest.fixture
def author_douglas_adams():
    from tests.test1.app.models import Author

    return Author.objects.create(first_name="Douglas", last_name="Adams")


@pytest.fixture
def author_terry_pratchett():
    from tests.test1.app.models import Author

    return Author.objects.create(first_name="Terry", last_name="Pratchett")
