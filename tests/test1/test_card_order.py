from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.test.client import Client
from lxml import html

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_publisher_order():
    from tests.test1.app.views import cv_publisher_order as ret

    return ret


@pytest.fixture
def client_publisher_order(client, cv_publisher_order) -> Client:
    user = User.objects.create_user(username="user_pub_order", password="password")
    user_viewset_permission(user, cv_publisher_order, "view")
    client.force_login(user)
    return client


@pytest.fixture
def publishers(db):
    from tests.test1.app.models import Publisher

    return [
        Publisher.objects.create(name="Charlie"),
        Publisher.objects.create(name="Alpha"),
        Publisher.objects.create(name="Bravo"),
    ]


def _card_titles(response) -> list[str]:
    doc = html.fromstring(response.content)
    return [c.text_content().strip() for c in doc.cssselect(".card.mb-3 .card-title")]


@pytest.mark.django_db
def test_card_order_by_id_ascending(client_publisher_order, publishers):
    # id asc == insertion order, which differs from Publisher.Meta.ordering = ["name"].
    # Proves the mixin orders the queryset (and exercises the ("id", "ID") tuple field).
    response = client_publisher_order.get("/publisher_order/card/?order=id&dir=asc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Charlie", "Alpha"]  # paginate_by=2, insertion order


@pytest.mark.django_db
def test_card_order_name_descending(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Charlie", "Bravo"]  # paginate_by=2, desc


@pytest.mark.django_db
def test_card_order_invalid_field_falls_back_to_default(client_publisher_order, publishers):
    # "bogus" is not in cv_order_fields -> falls back to cv_order_default ("-name" desc),
    # which differs from Publisher.Meta.ordering = ["name"] (asc).
    response = client_publisher_order.get("/publisher_order/card/?order=bogus&dir=asc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Charlie", "Bravo"]  # default "-name" desc


@pytest.mark.django_db
def test_card_order_default_applied(client_publisher_order, publishers):
    # no order params -> cv_order_default = "-name" (desc), differs from Meta.ordering asc.
    response = client_publisher_order.get("/publisher_order/card/?page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Charlie", "Bravo"]  # cv_order_default = "-name"


@pytest.mark.django_db
def test_card_order_name_ascending(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=asc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Alpha", "Bravo"]  # paginate_by=2, asc


# --- direct unit tests on cv_get_order() (no HTTP) ---


def _order_view(query: dict):
    from tests.test1.app.views import PublisherOrderCardListView

    view = PublisherOrderCardListView()
    view.request = SimpleNamespace(GET=query)
    return view


def test_cv_get_order_bad_direction_clamped():
    view = _order_view({"order": "name", "dir": "sideways"})
    assert view.cv_get_order() == ("name", "asc")


def test_cv_get_order_tuple_field_whitelisted():
    view = _order_view({"order": "id", "dir": "desc"})
    assert view.cv_get_order() == ("id", "desc")


def test_cv_get_order_invalid_field_uses_default():
    view = _order_view({"order": "bogus"})
    # cv_order_default = "-name" => desc
    assert view.cv_get_order() == ("name", "desc")


def test_cv_get_order_no_field_no_default():
    from tests.test1.app.views import PublisherOrderCardListView

    view = PublisherOrderCardListView()
    view.cv_order_default = None
    view.request = SimpleNamespace(GET={})
    assert view.cv_get_order() == (None, "asc")
