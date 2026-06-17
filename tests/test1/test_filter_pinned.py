import pytest
from django.contrib.auth.models import User
from django.test.client import Client

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_publisher_order():
    from tests.test1.app.views import cv_publisher_order as ret

    return ret


@pytest.fixture
def client_publisher_order(client, cv_publisher_order) -> Client:
    user = User.objects.create_user(username="user_pinned_card", password="password")
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


def test_filter_pinned_default_comes_from_setting():
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.views import ListViewTableFilterMixin

    assert ListViewTableFilterMixin.cv_filter_pinned == crud_views_settings.filter_pinned
    assert crud_views_settings.filter_pinned is False


@pytest.mark.django_db
def test_pinned_view_forces_filter_expanded_context(client_publisher_order, publishers, monkeypatch):
    from tests.test1.app.views import PublisherOrderCardListView

    response = client_publisher_order.get("/publisher_order/card/")
    assert response.status_code == 200
    assert response.context["cv_filter_pinned"] is False
    assert response.context["cv_filter_expanded"] is False

    monkeypatch.setattr(PublisherOrderCardListView, "cv_filter_pinned", True)
    response = client_publisher_order.get("/publisher_order/card/")
    assert response.status_code == 200
    assert response.context["cv_filter_pinned"] is True
    assert response.context["cv_filter_expanded"] is True


@pytest.mark.django_db
def test_pinned_hides_filter_toggle_button(client_publisher_order, publishers, monkeypatch):
    from lxml import html

    from tests.test1.app.views import PublisherOrderCardListView

    # not pinned: toggle button present
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert doc.cssselect("#cv-filter-toggle"), "toggle should be present when not pinned"

    # pinned: toggle button hidden
    monkeypatch.setattr(PublisherOrderCardListView, "cv_filter_pinned", True)
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert not doc.cssselect("#cv-filter-toggle"), "toggle should be hidden when pinned"


@pytest.mark.django_db
def test_pinned_renders_filter_without_collapse(client_publisher_order, publishers, monkeypatch):
    from lxml import html

    from tests.test1.app.views import PublisherOrderCardListView

    # not pinned: collapse wrapper present, filter form present
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert doc.cssselect("#filter-collapse"), "collapse wrapper expected when not pinned"
    assert doc.cssselect("form#filter-form"), "filter form expected"

    # pinned: no collapse wrapper, but filter form still rendered
    monkeypatch.setattr(PublisherOrderCardListView, "cv_filter_pinned", True)
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert not doc.cssselect("#filter-collapse"), "collapse wrapper must be gone when pinned"
    assert doc.cssselect("form#filter-form"), "filter form must still render when pinned"
