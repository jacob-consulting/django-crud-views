import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import override_settings
from django.test.client import Client
from django.utils import translation
from lxml import html

from tests.lib.helper.golden import check_golden
from tests.lib.helper.user import user_viewset_permission
from tests.test1.test_table_template import (
    HIDDEN_LABEL_CASES,
    _assert_hidden_labels,
    _assert_pagination_accessibility,
    _href_page,
    _nav,
    _pagination_table,
    _render_table_pagination,
    hidden_label_settings,
    patch_sentinel_translations,
)


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


@pytest.fixture
def publishers_five(publishers):
    """Five publishers: at paginate_by=2 the card list has a real middle page (used by the parity matrix only)."""
    from tests.test1.app.models import Publisher

    return [*publishers, Publisher.objects.create(name="Delta"), Publisher.objects.create(name="Echo")]


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


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
def test_card_pagination_golden(client_publisher_order, publishers, page):
    check_golden(GOLDEN_DIR / f"page{page}.html", _pagination(client_publisher_order, page))


# D-02: the stock card snippet's exact render bytes, frozen before its hidden-label classes moved to the class table.
# Captured once and committed; there is deliberately no regenerate switch, so any drift of the stock bytes fails.
CARD_PAGINATION_RAW = GOLDEN_DIR / "raw_pages.json"


def _render_card_pagination_raw(page: int) -> str:
    paginator = Paginator(range(3), 2)
    context = {"paginator": paginator, "page_obj": paginator.page(page), "is_paginated": True, "base_qs": ""}
    with translation.override("en"):
        return render_to_string("crud_views/snippets/pagination.html", context)


def test_card_pagination_raw_bytes():
    rendered = {f"page{page}": _render_card_pagination_raw(page) for page in (1, 2)}
    stored = json.loads(CARD_PAGINATION_RAW.read_text(encoding="utf-8"))
    assert set(stored) == {"page1", "page2"}
    for name, markup in rendered.items():
        assert markup.encode("utf-8") == stored[name].encode("utf-8")


@pytest.mark.django_db
def test_card_pagination_current_page_aria_current(client_publisher_order, publishers):
    nav = _pagination(client_publisher_order, 2)
    (current,) = nav.cssselect('.page-item[aria-current="page"]')
    assert "active" in current.get("class")
    assert current.text_content().strip() == "2"
    # the current page is a non-link span, never a focusable anchor
    assert current.cssselect("a") == []
    (span,) = current.cssselect("span.page-link")
    assert span.text_content() == "2"
    assert span.get("tabindex") is None


@pytest.mark.django_db
@pytest.mark.parametrize("page, end", [(1, 0), (2, -1)])
def test_card_pagination_disabled_end_is_aria_disabled_link(client_publisher_order, publishers, page, end):
    item = _pagination(client_publisher_order, page).cssselect(".page-item")[end]
    assert "disabled" in item.get("class")
    (link,) = item.cssselect("a.page-link")
    assert link.get("aria-disabled") == "true"
    assert link.get("href") is None
    assert link.get("tabindex") is None


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
def test_card_pagination_shared_hidden_label(client_publisher_order, publishers, page):
    """pagination:hidden-label styles the card arrow labels, available and unavailable alike (D-02)."""

    def labels():
        items = _pagination(client_publisher_order, page).cssselect(".page-item")
        return [
            (item.cssselect(".page-link > span")[0].get("class"), "disabled" in item.get("class"))
            for item in (items[0], items[-1])
        ]

    assert labels() == [("visually-hidden", page == 1), ("visually-hidden", page == 2)]
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"pagination:hidden-label": "sr-only"}):
        assert labels() == [("sr-only", page == 1), ("sr-only", page == 2)]


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
@override_settings(LANGUAGES=[("en", "English"), ("de", "German")])
def test_card_pagination_labels_translated(client_publisher_order, publishers, monkeypatch, page):
    # the test project has no LocaleMiddleware: activate German around the request (as test_i18n.py does)
    with translation.override("de"):
        nav = _pagination(client_publisher_order, page)
    assert nav.get("aria-label") == "Seitennavigation"
    labels = [s.text_content() for s in nav.cssselect(".page-link .visually-hidden")]
    assert labels == ["zurück", "weiter"]
    _assert_pagination_accessibility(nav, page, 2, labels={"previous": "zurück", "next": "weiter"})

    # a sentinel catalog proves the labels come from gettext, not from a hardcoded German or English string
    patch_sentinel_translations(monkeypatch)
    with translation.override("de"):
        nav = _pagination(client_publisher_order, page)
    assert nav.get("aria-label") == "NAV-⚑"
    assert [s.text_content() for s in nav.cssselect(".page-link .visually-hidden")] == ["PREV-⚑", "NEXT-⚑"]


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
@override_settings(CRUD_VIEWS_ICONS={"page-previous": "bi:arrow-left", "page-next": "bi:arrow-right"})
def test_card_pagination_arrows_from_icon_registry(client_publisher_order, publishers, page):
    # page 1: previous disabled, next enabled; page 2: the reverse. The registry icons reach both states.
    items = _pagination(client_publisher_order, page).cssselect(".page-item")
    assert ("disabled" in items[0].get("class").split()) is (page == 1)
    assert ("disabled" in items[-1].get("class").split()) is (page == 2)
    assert items[0].cssselect("i")[0].get("class") == "bi bi-arrow-left"
    assert items[-1].cssselect("i")[0].get("class") == "bi bi-arrow-right"


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
@pytest.mark.parametrize("case", HIDDEN_LABEL_CASES)
def test_card_pagination_hidden_label_values(client_publisher_order, publishers, case, page):
    """Omitted, None, empty, Unicode and hostile shared-class values behave exactly as on the table."""
    mapping, expected = HIDDEN_LABEL_CASES[case]
    with hidden_label_settings(mapping), translation.override("en"):
        response = client_publisher_order.get(f"/publisher_order/card/?page={page}")
    nav = html.fromstring(response.content).cssselect("nav > ul.pagination")[0].getparent()
    _assert_hidden_labels(nav, response.content.decode("utf-8"), expected)
    if case == "unicode":
        assert f'class="{expected}"'.encode() in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2, 3])
def test_pagination_component_parity(client_publisher_order, publishers_five, page):
    """Card and table pagination expose the same accessible structure on first, middle and last pages."""
    with translation.override("en"):
        response = client_publisher_order.get(f"/publisher_order/card/?page={page}")
        table, request = _pagination_table(5, page)
        table_nav = _nav(_render_table_pagination(table, request))
    assert response.status_code == 200
    paginator, page_obj = response.context["paginator"], response.context["page_obj"]
    assert paginator.num_pages == 3
    assert page_obj.number == page
    assert table.paginator.num_pages == 3
    if page == 2:
        assert page_obj.has_previous() and page_obj.has_next()
    (card_ul,) = html.fromstring(response.content).cssselect("nav > ul.pagination")
    card_nav = card_ul.getparent()

    card_tokens = _assert_pagination_accessibility(card_nav, page, 3)
    table_tokens = _assert_pagination_accessibility(table_nav, page, 3)
    assert card_tokens == table_tokens == ["1", "2", "3"]
    for nav in (card_nav, table_nav):
        (current,) = [li for li in nav.cssselect("ul.pagination > li") if "active" in li.get("class").split()]
        assert current.get("aria-current") == "page"

    if page == 2:
        # a real middle page: both arrows are enabled links to pages 1 and 3 in both components
        for nav in (card_nav, table_nav):
            items = nav.cssselect("ul.pagination > li")
            arrows = [items[0].cssselect("a.page-link")[0], items[-1].cssselect("a.page-link")[0]]
            assert [_href_page(link.get("href"), "page") for link in arrows] == [1, 3]


@pytest.mark.django_db
def test_card_pagination_empty_cases(client_publisher_order):
    """No pagination when the card list is unpaginated, empty or a single page."""
    from tests.test1.app.models import Publisher

    paginator = Paginator(range(3), 2)
    context = {"paginator": paginator, "page_obj": paginator.page(1), "is_paginated": False, "base_qs": ""}
    assert render_to_string("crud_views/snippets/pagination.html", context).strip() == ""

    for count, name in ((0, None), (1, "Alpha"), (2, "Bravo")):  # zero records, one record, one full page
        if name:
            Publisher.objects.create(name=name)
        response = client_publisher_order.get("/publisher_order/card/")
        assert response.status_code == 200
        assert response.context["is_paginated"] is False
        doc = html.fromstring(response.content)
        assert len(doc.cssselect(".card.mb-3")) == count
        assert doc.cssselect("ul.pagination, .page-item, .page-link") == []
        assert doc.cssselect('nav[aria-label="pagination"]') == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query, status, current", [("", 200, 1), ("?page=last", 200, 3), ("?page=99", 404, None), ("?page=abc", 404, None)]
)
def test_card_pagination_invalid_page_inputs(client_publisher_order, publishers_five, query, status, current):
    """Django's ListView page semantics: missing is page 1, "last" the last page, out of range or non-integer 404."""
    response = client_publisher_order.get(f"/publisher_order/card/{query}")
    assert response.status_code == status
    if current is not None:
        (ul,) = html.fromstring(response.content).cssselect("nav > ul.pagination")
        _assert_pagination_accessibility(ul.getparent(), current, 3)


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
