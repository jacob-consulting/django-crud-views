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
def test_card_order_ascending(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=asc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Alpha", "Bravo"]  # paginate_by=2, asc


@pytest.mark.django_db
def test_card_order_descending(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Charlie", "Bravo"]  # paginate_by=2, desc


@pytest.mark.django_db
def test_card_order_invalid_field_ignored(client_publisher_order, publishers):
    # "bogus" is not in cv_order_fields -> falls back to cv_order_default ("name" asc)
    response = client_publisher_order.get("/publisher_order/card/?order=bogus&dir=asc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Alpha", "Bravo"]


@pytest.mark.django_db
def test_card_order_default_applied(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Alpha", "Bravo"]  # cv_order_default = "name"
