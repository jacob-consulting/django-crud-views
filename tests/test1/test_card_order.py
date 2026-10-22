import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.test.client import Client
from django.utils import translation
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


@pytest.mark.django_db
def test_card_order_toolbar_renders(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    form = doc.cssselect("form#cv-card-order-form")
    assert len(form) == 1
    options = doc.cssselect("#cv-card-order-form select[name=order] option")
    values = [o.get("value") for o in options]
    assert values == ["name", "id"]
    labels = [o.text_content().strip() for o in options]
    assert labels == ["Name", "ID"]
    dir_buttons = doc.cssselect("#cv-card-order-form button[name=dir]")
    assert {b.get("value") for b in dir_buttons} == {"asc", "desc"}


@pytest.mark.django_db
def test_card_order_toolbar_marks_active_direction(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc")
    doc = html.fromstring(response.content)
    desc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=desc]")[0]
    asc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=asc]")[0]
    assert "active" in desc_btn.get("class")
    assert "active" not in asc_btn.get("class")


@pytest.mark.django_db
def test_card_order_toolbar_active_class_comes_from_the_table(client_publisher_order, publishers):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card-order:active": "is-active"}):
        response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc")
    doc = html.fromstring(response.content)
    desc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=desc]")[0]
    asc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=asc]")[0]
    assert desc_btn.get("class") == "btn btn-outline-secondary is-active"
    assert asc_btn.get("class") == "btn btn-outline-secondary"


@pytest.mark.django_db
def test_card_order_toolbar_absent_without_fields(client_user_author_view, cv_author, author_douglas_adams):
    # the plain AuthorCardListView has no cv_order_fields -> no toolbar
    response = client_user_author_view.get("/author/card/")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect("form#cv-card-order-form")) == 0


@pytest.mark.django_db
def test_card_pagination_limits_cards(client_publisher_order, publishers):
    # 3 publishers, paginate_by=2 -> page 1 shows 2 cards
    response = client_publisher_order.get("/publisher_order/card/?page=1")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect(".card.mb-3")) == 2
    assert len(doc.cssselect("nav .pagination")) == 1


@pytest.mark.django_db
def test_card_pagination_second_page(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?page=2")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect(".card.mb-3")) == 1  # 3rd item


@pytest.mark.django_db
def test_card_pagination_links_preserve_order_and_filter(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc")
    doc = html.fromstring(response.content)
    hrefs = [a.get("href") for a in doc.cssselect("nav .pagination a.page-link[href]")]
    assert hrefs, "expected page links"
    # every page link keeps order + dir and never duplicates page
    for href in hrefs:
        assert "order=name" in href
        assert "dir=desc" in href
        assert href.count("page=") == 1


# #241: accessible pagination markup, arrows from the icon registry.
# Regenerate the goldens ONLY when a change to the stock markup is intended:
# CV_UPDATE_GOLDEN=1 pytest tests/test1/test_card_order.py
GOLDEN_DIR = Path(__file__).parent / "golden" / "card_pagination"


def _pagination(client, page: int):
    response = client.get(f"/publisher_order/card/?page={page}")
    (ul,) = html.fromstring(response.content).cssselect("nav > ul.pagination")
    nav = ul.getparent()
    return nav


def _check_golden(name: str, nav):
    markup = re.sub(r"\s+", " ", re.sub(r">\s+<", "><", html.tostring(nav, encoding="unicode"))).strip()
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markup + "\n")
    assert markup == path.read_text().strip()


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
def test_card_pagination_golden(client_publisher_order, publishers, page):
    _check_golden(f"page{page}", _pagination(client_publisher_order, page))


@pytest.mark.django_db
def test_card_pagination_current_page_aria_current(client_publisher_order, publishers):
    nav = _pagination(client_publisher_order, 2)
    (current,) = nav.cssselect('.page-item[aria-current="page"]')
    assert "active" in current.get("class")
    assert current.text_content().strip() == "2"


@pytest.mark.django_db
@pytest.mark.parametrize("page, end", [(1, 0), (2, -1)])
def test_card_pagination_disabled_end_is_aria_disabled_link(client_publisher_order, publishers, page, end):
    item = _pagination(client_publisher_order, page).cssselect(".page-item")[end]
    assert "disabled" in item.get("class")
    (link,) = item.cssselect("a.page-link")
    assert link.get("aria-disabled") == "true"
    assert link.get("href") is None


@pytest.mark.django_db
@override_settings(LANGUAGES=[("en", "English"), ("de", "German")])
def test_card_pagination_labels_translated(client_publisher_order, publishers):
    # the test project has no LocaleMiddleware: activate German around the request (as test_i18n.py does)
    with translation.override("de"):
        nav = _pagination(client_publisher_order, 1)
    assert nav.get("aria-label") == "Seitennavigation"
    labels = [s.text_content() for s in nav.cssselect(".page-link .visually-hidden")]
    assert labels == ["zurück", "weiter"]


@pytest.mark.django_db
@override_settings(CRUD_VIEWS_ICONS={"page-previous": "bi:arrow-left", "page-next": "bi:arrow-right"})
def test_card_pagination_arrows_from_icon_registry(client_publisher_order, publishers):
    items = _pagination(client_publisher_order, 1).cssselect(".page-item")
    assert items[0].cssselect("i")[0].get("class") == "bi bi-arrow-left"
    assert items[-1].cssselect("i")[0].get("class") == "bi bi-arrow-right"


@pytest.mark.django_db
def test_filter_form_carries_active_order_as_hidden(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc&name=a")
    doc = html.fromstring(response.content)
    hidden = {i.get("name"): i.get("value") for i in doc.cssselect("form#filter-form input[type=hidden]")}
    assert hidden.get("order") == "name"
    assert hidden.get("dir") == "desc"


@pytest.mark.django_db
def test_order_toolbar_carries_active_filter_as_hidden(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?name=Alp")
    doc = html.fromstring(response.content)
    hidden = {i.get("name"): i.get("value") for i in doc.cssselect("#cv-card-order-form input[type=hidden]")}
    assert hidden.get("name") == "Alp"


@pytest.mark.django_db
def test_reset_filter_preserves_order(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?reset_filter=true&order=name&dir=desc", follow=False)
    assert response.status_code == 302
    assert "order=name" in response.url
    assert "dir=desc" in response.url
    assert "reset_filter" not in response.url
