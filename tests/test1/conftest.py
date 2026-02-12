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
            'polymorphic',
            'ordered_model',
            'django_tables2',
            "django_object_detail",
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
        CRUD_VIEWS_EXTENDS="app/crud_views.html",
        CRUD_VIEWS_MANAGE_VIEWS_ENABLED="yes",

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
def user_author_add(cv_author):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_author_add", password="password")

    user_viewset_permission(user, cv_author, "add")

    return user


@pytest.fixture
def client_user_author_change(client, user_author_change) -> Client:
    client.force_login(user_author_change)
    return client


@pytest.fixture
def client_user_author_delete(client, user_author_delete) -> Client:
    client.force_login(user_author_delete)
    return client


@pytest.fixture
def client_user_author_add(client, user_author_add) -> Client:
    client.force_login(user_author_add)
    return client


@pytest.fixture
def client_user_a(client, user_a) -> Client:
    client.force_login(user_a)
    return client


@pytest.fixture
def author_terry_pratchett():
    from tests.test1.app.models import Author

    return Author.objects.create(first_name="Terry", last_name="Pratchett")


# --- Publisher fixtures ---

@pytest.fixture
def cv_publisher():
    from tests.test1.app.views import cv_publisher as ret
    return ret


@pytest.fixture
def publisher_penguin():
    from tests.test1.app.models import Publisher
    return Publisher.objects.create(name="Penguin")


@pytest.fixture
def publisher_harpercollins():
    from tests.test1.app.models import Publisher
    return Publisher.objects.create(name="HarperCollins")


@pytest.fixture
def user_publisher_view(cv_publisher):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_publisher_view", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    return user


@pytest.fixture
def client_user_publisher_view(client, user_publisher_view) -> Client:
    client.force_login(user_publisher_view)
    return client


@pytest.fixture
def user_publisher_add(cv_publisher):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_publisher_add", password="password")
    user_viewset_permission(user, cv_publisher, "add")
    return user


@pytest.fixture
def client_user_publisher_add(client, user_publisher_add) -> Client:
    client.force_login(user_publisher_add)
    return client


@pytest.fixture
def user_publisher_change(cv_publisher):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_publisher_change", password="password")
    user_viewset_permission(user, cv_publisher, "change")
    return user


@pytest.fixture
def client_user_publisher_change(client, user_publisher_change) -> Client:
    client.force_login(user_publisher_change)
    return client


@pytest.fixture
def user_publisher_delete(cv_publisher):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_publisher_delete", password="password")
    user_viewset_permission(user, cv_publisher, "delete")
    return user


@pytest.fixture
def client_user_publisher_delete(client, user_publisher_delete) -> Client:
    client.force_login(user_publisher_delete)
    return client


# --- Book fixtures ---

@pytest.fixture
def cv_book():
    from tests.test1.app.views import cv_book as ret
    return ret


@pytest.fixture
def book_hitchhiker(publisher_penguin):
    from tests.test1.app.models import Book
    return Book.objects.create(title="The Hitchhiker's Guide to the Galaxy", publisher=publisher_penguin)


@pytest.fixture
def book_other_publisher(publisher_harpercollins):
    from tests.test1.app.models import Book
    return Book.objects.create(title="Other Book", publisher=publisher_harpercollins)


@pytest.fixture
def user_book_view(cv_book):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_book_view", password="password")
    user_viewset_permission(user, cv_book, "view")
    return user


@pytest.fixture
def client_user_book_view(client, user_book_view) -> Client:
    client.force_login(user_book_view)
    return client


@pytest.fixture
def user_book_add(cv_book):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_book_add", password="password")
    user_viewset_permission(user, cv_book, "add")
    return user


@pytest.fixture
def client_user_book_add(client, user_book_add) -> Client:
    client.force_login(user_book_add)
    return client


@pytest.fixture
def user_book_change(cv_book):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_book_change", password="password")
    user_viewset_permission(user, cv_book, "change")
    return user


@pytest.fixture
def client_user_book_change(client, user_book_change) -> Client:
    client.force_login(user_book_change)
    return client


@pytest.fixture
def user_book_delete(cv_book):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_book_delete", password="password")
    user_viewset_permission(user, cv_book, "delete")
    return user


@pytest.fixture
def client_user_book_delete(client, user_book_delete) -> Client:
    client.force_login(user_book_delete)
    return client


# --- Vehicle (polymorphic) fixtures ---

@pytest.fixture
def cv_vehicle():
    from tests.test1.app.views import cv_vehicle as ret
    return ret


@pytest.fixture
def car_sedan():
    from tests.test1.app.models import Car
    return Car.objects.create(name="Sedan", doors=4)


@pytest.fixture
def truck_semi():
    from tests.test1.app.models import Truck
    return Truck.objects.create(name="Semi", payload_tons=20)


@pytest.fixture
def user_vehicle_view(cv_vehicle):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_vehicle_view", password="password")
    user_viewset_permission(user, cv_vehicle, "view")
    return user


@pytest.fixture
def client_user_vehicle_view(client, user_vehicle_view) -> Client:
    client.force_login(user_vehicle_view)
    return client


@pytest.fixture
def user_vehicle_add(cv_vehicle):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_vehicle_add", password="password")
    user_viewset_permission(user, cv_vehicle, "add")
    return user


@pytest.fixture
def client_user_vehicle_add(client, user_vehicle_add) -> Client:
    client.force_login(user_vehicle_add)
    return client


@pytest.fixture
def user_vehicle_change(cv_vehicle):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_vehicle_change", password="password")
    user_viewset_permission(user, cv_vehicle, "change")
    return user


@pytest.fixture
def client_user_vehicle_change(client, user_vehicle_change) -> Client:
    client.force_login(user_vehicle_change)
    return client


@pytest.fixture
def user_vehicle_delete(cv_vehicle):
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="user_vehicle_delete", password="password")
    user_viewset_permission(user, cv_vehicle, "delete")
    return user


@pytest.fixture
def client_user_vehicle_delete(client, user_vehicle_delete) -> Client:
    client.force_login(user_vehicle_delete)
    return client
