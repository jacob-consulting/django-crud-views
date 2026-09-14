"""
Card ordering in *signed* mode: the direction is encoded in the order choice
(``-name`` / ``name``) so the toolbar needs no asc/desc buttons.
"""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.test.client import Client
from lxml import html

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_publisher_signed_order():
    from tests.test1.app.views import cv_publisher_signed_order as ret

    return ret


@pytest.fixture
def client_publisher_signed_order(client, cv_publisher_signed_order) -> Client:
    user = User.objects.create_user(username="user_pub_signed_order", password="password")
    user_viewset_permission(user, cv_publisher_signed_order, "view")
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


def _signed_view(query: dict):
    from tests.test1.app.views import PublisherSignedOrderCardListView

    view = PublisherSignedOrderCardListView()
    view.request = SimpleNamespace(GET=_querydict(query))
    return view


def _querydict(query: dict):
    from django.http import QueryDict

    qd = QueryDict(mutable=True)
    for k, v in query.items():
        qd[k] = v
    return qd


# --- mode detection ---


def test_signed_mode_detected_from_signed_entries():
    from tests.test1.app.views import PublisherSignedOrderCardListView

    assert PublisherSignedOrderCardListView().cv_order_is_signed() is True


def test_plain_entries_keep_legacy_mode():
    from tests.test1.app.views import PublisherOrderCardListView

    assert PublisherOrderCardListView().cv_order_is_signed() is False


# --- cv_get_order() in signed mode ---


def test_cv_get_order_signed_descending():
    assert _signed_view({"order": "-name"}).cv_get_order() == ("name", "desc")


def test_cv_get_order_signed_ascending_is_bare_name():
    assert _signed_view({"order": "name"}).cv_get_order() == ("name", "asc")


def test_cv_get_order_signed_ignores_dir_param():
    # direction lives in the value; a stray dir=desc must not flip it
    assert _signed_view({"order": "id", "dir": "desc"}).cv_get_order() == ("id", "asc")


def test_cv_get_order_signed_rejects_unlisted_direction():
    # only "id" and "-id" are whitelisted for id; "+id" is not a valid URL value
    assert _signed_view({"order": "+id"}).cv_get_order() == ("name", "desc")


def test_cv_get_order_signed_invalid_field_uses_default():
    assert _signed_view({"order": "bogus"}).cv_get_order() == ("name", "desc")


def test_cv_get_order_signed_no_param_uses_default():
    assert _signed_view({}).cv_get_order() == ("name", "desc")


def test_cv_get_order_signed_no_param_no_default():
    view = _signed_view({})
    view.cv_order_default = None
    assert view.cv_get_order() == (None, "asc")


# --- cv_get_order_choices() in signed mode ---


def test_signed_choices_values_are_normalised_signed_keys():
    choices = _signed_view({}).cv_get_order_choices()
    assert [c["name"] for c in choices] == ["-name", "name", "id", "-id"]


def test_signed_choices_labels_explicit_and_auto_translated():
    choices = _signed_view({}).cv_get_order_choices()
    assert [c["label"] for c in choices] == ["Name Z-A", "Name A-Z", "Id (ascending)", "Id (descending)"]


def test_signed_choices_select_default_when_no_param():
    choices = _signed_view({}).cv_get_order_choices()
    assert [c["name"] for c in choices if c["selected"]] == ["-name"]


def test_signed_choices_select_current_ascending():
    choices = _signed_view({"order": "id"}).cv_get_order_choices()
    assert [c["name"] for c in choices if c["selected"]] == ["id"]


def test_signed_choices_select_current_descending():
    choices = _signed_view({"order": "-id"}).cv_get_order_choices()
    assert [c["name"] for c in choices if c["selected"]] == ["-id"]


# --- HTTP: queryset ordering ---


@pytest.mark.django_db
def test_signed_order_descending_via_http(client_publisher_signed_order, publishers):
    response = client_publisher_signed_order.get("/publisher_signed_order/card/?order=-name&page=1")
    assert response.status_code == 200
    assert _card_titles(response) == ["Charlie", "Bravo"]


@pytest.mark.django_db
def test_signed_order_ascending_via_http(client_publisher_signed_order, publishers):
    response = client_publisher_signed_order.get("/publisher_signed_order/card/?order=name&page=1")
    assert response.status_code == 200
    assert _card_titles(response) == ["Alpha", "Bravo"]


@pytest.mark.django_db
def test_signed_order_plain_entry_is_ascending_via_http(client_publisher_signed_order, publishers):
    # "id" plain entry in signed mode == ascending == insertion order
    response = client_publisher_signed_order.get("/publisher_signed_order/card/?order=id&page=1")
    assert response.status_code == 200
    assert _card_titles(response) == ["Charlie", "Alpha"]


# --- HTTP: toolbar rendering ---


@pytest.mark.django_db
def test_signed_toolbar_has_no_direction_buttons(client_publisher_signed_order, publishers):
    response = client_publisher_signed_order.get("/publisher_signed_order/card/")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect("form#cv-card-order-form")) == 1
    assert doc.cssselect("#cv-card-order-form button[name=dir]") == []


@pytest.mark.django_db
def test_signed_toolbar_select_submits_on_change(client_publisher_signed_order, publishers):
    response = client_publisher_signed_order.get("/publisher_signed_order/card/")
    doc = html.fromstring(response.content)
    select = doc.cssselect("#cv-card-order-form select[name=order]")[0]
    assert select.get("data-cv-action") == "submit-on-change"


@pytest.mark.django_db
def test_signed_toolbar_marks_active_option(client_publisher_signed_order, publishers):
    response = client_publisher_signed_order.get("/publisher_signed_order/card/?order=-id")
    doc = html.fromstring(response.content)
    selected = doc.cssselect("#cv-card-order-form select[name=order] option[selected]")
    assert [o.get("value") for o in selected] == ["-id"]


@pytest.mark.django_db
def test_legacy_toolbar_unchanged(client_publisher_signed_order, publishers):
    # the legacy (buttons) view keeps its dir buttons and does not auto-submit
    from tests.test1.app.views import cv_publisher_order

    user = User.objects.create_user(username="user_pub_order_legacy", password="password")
    user_viewset_permission(user, cv_publisher_order, "view")
    client_publisher_signed_order.force_login(user)
    response = client_publisher_signed_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect("#cv-card-order-form button[name=dir]")) == 2
    select = doc.cssselect("#cv-card-order-form select[name=order]")[0]
    assert select.get("data-cv-action") is None
