import os
import re
from pathlib import Path

import pytest
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from django.test.client import Client
from django.utils import translation
from lxml import html

import crud_views
from tests.lib.helper.boostrap5 import Table

TABLE_TEMPLATE = "crud_views/table/bootstrap5.html"
# the package's own table template: the tracked src/ file in a development checkout, its installed copy under nox
TABLE_TEMPLATE_PATH = (Path(crud_views.__file__).resolve().parent / "templates" / TABLE_TEMPLATE).resolve()


def test_cv_querystring_preserves_and_replaces_params():
    """cv_querystring delegates to the installed django-tables2 tag (2.x or 3.x)."""
    request = RequestFactory().get("/?page=1&q=foo")
    template = Template('{% load crud_views %}{% cv_querystring "page"="2" %}')

    rendered = template.render(Context({"request": request}))

    assert "page=2" in rendered
    assert "q=foo" in rendered


@pytest.mark.django_db
@override_settings(DJANGO_TABLES2_TEMPLATE="crud_views/table/bootstrap5.html")
def test_list_renders_with_crud_views_table_template(
    client_user_author_view: Client, cv_author, author_douglas_adams, author_terry_pratchett
):
    """The crud_views list table template renders end-to-end via the cv_querystring wrapper."""
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 2


def test_action_column_carries_no_display_utility():
    """The action column must not change the cell's display.

    `d-flex` is `display: flex !important`; a table cell with it leaves the
    table layout model and is no longer stretched to the row height, so its
    `border-bottom` — the row separator — sits above the neighbouring cells
    and the line visibly steps. The column is marked with a plain
    `cv-col-action` hook instead and aligned with `text-align`.
    """
    from crud_views.lib.table.attrs import ColAttr

    for key in ("th", "td"):
        classes = ColAttr.action[key]["class"]
        assert "cv-col-action" in classes
        assert "d-flex" not in classes


@pytest.mark.django_db
@override_settings(DJANGO_TABLES2_TEMPLATE="crud_views/table/bootstrap5.html")
def test_rendered_action_cell_carries_no_display_utility(
    client_user_author_view: Client, cv_author, author_douglas_adams
):
    """The rendered list markup carries the hook, not the flex utility."""
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200

    body = response.content.decode()
    assert 'class="cv-col-action"' in body
    assert "d-flex justify-content-end" not in body


# PAGE-01/02: table pagination through the real author list. AuthorTable's options captured
# DJANGO_TABLES2_TEMPLATE when the class was defined, so the template is selected on the table class itself.
# Regenerate the goldens ONLY when a change to the stock markup is intended:
# CV_UPDATE_GOLDEN=1 pytest tests/test1/test_table_template.py -k test_table_pagination_golden
TABLE_GOLDEN_DIR = Path(__file__).parent / "golden" / "table_pagination"


@pytest.fixture
def paginated_author_client(
    monkeypatch, client_user_author_view: Client, cv_author, author_douglas_adams, author_terry_pratchett
) -> Client:
    from tests.test1.app.views import AuthorListView, AuthorTable

    monkeypatch.setattr(AuthorListView, "paginate_by", 1)
    monkeypatch.setattr(AuthorTable._meta, "template_name", TABLE_TEMPLATE)
    return client_user_author_view


def _table_pagination(client: Client, page: int, query: str = ""):
    response = client.get(f"/author/?{query}{'&' if query else ''}page={page}")
    assert response.status_code == 200
    # template-origin evidence first: new markup alone does not prove which template rendered
    assert response.context["table"].template_name == TABLE_TEMPLATE
    origins = [
        Path(t.origin.name).resolve()
        for t in response.templates
        if getattr(t, "origin", None) is not None and t.origin.template_name == TABLE_TEMPLATE
    ]
    assert TABLE_TEMPLATE_PATH in origins, f"{TABLE_TEMPLATE} did not render from {TABLE_TEMPLATE_PATH}: {origins}"
    (ul,) = html.fromstring(response.content).cssselect(".table-container nav > ul.pagination")
    return ul.getparent()


def _check_table_golden(name: str, nav):
    markup = re.sub(r"\s+", " ", re.sub(r">\s+<", "><", html.tostring(nav, encoding="unicode"))).strip()
    path = TABLE_GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markup + "\n", encoding="utf-8")
    assert markup == path.read_text(encoding="utf-8").strip()


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
def test_table_pagination_golden(paginated_author_client, page):
    with translation.override("en"):
        nav = _table_pagination(paginated_author_client, page)
    _check_table_golden(f"page{page}", nav)


def _direction(nav, direction: str):
    """The previous/next li (first/last item) and its single page-link anchor."""
    items = nav.cssselect("ul.pagination > li")
    item = items[0] if direction == "previous" else items[-1]
    (link,) = item.cssselect("a.page-link")
    return item, link


@pytest.mark.django_db
@pytest.mark.parametrize("page, disabled, enabled", [(1, "previous", "next"), (2, "next", "previous")])
def test_table_pagination_accessible_structure(paginated_author_client, page, disabled, enabled):
    with translation.override("en"):
        nav = _table_pagination(paginated_author_client, page)
    assert nav.get("aria-label") == "pagination"

    # the unavailable direction is still rendered: a non-navigable, non-focusable aria-disabled anchor
    item, link = _direction(nav, disabled)
    assert item.get("class") == f"{disabled} page-item disabled"
    assert link.get("aria-disabled") == "true"
    assert link.get("href") is None
    assert link.get("tabindex") is None

    # the available direction keeps its prefixed page query link
    item, link = _direction(nav, enabled)
    assert item.get("class") == f"{enabled} page-item"
    assert link.get("aria-disabled") is None
    assert link.get("href") == f"?page={2 if enabled == 'next' else 1}"

    # registry arrows with translated hidden labels: icon before "previous", "next" before icon
    for direction in ("previous", "next"):
        _, link = _direction(nav, direction)
        children = list(link)
        tags = [child.tag for child in children]
        assert tags == (["i", "span"] if direction == "previous" else ["span", "i"])
        (label,) = link.cssselect("span")
        assert label.get("class") == "visually-hidden"
        assert label.text_content() == direction
        assert link.text_content() == direction

    # exactly one current page: a span, not a link; the other numeric page keeps its href
    (current,) = nav.cssselect('li[aria-current="page"]')
    assert current.get("class") == "page-item active"
    assert current.cssselect("a") == []
    (number,) = current.cssselect("span.page-link")
    assert number.text_content().strip() == str(page)
    other = 2 if page == 1 else 1
    hrefs = [a.get("href") for a in nav.cssselect("ul.pagination > li:not(.previous):not(.next) a.page-link")]
    assert hrefs == [f"?page={other}"]


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
@override_settings(
    CRUD_VIEWS_BUTTON_CLASSES={"pagination:hidden-label": "sr-only"},
    CRUD_VIEWS_ICONS={"page-previous": "bi:arrow-left", "page-next": "bi:arrow-right"},
)
def test_table_pagination_shared_hidden_label(paginated_author_client, page):
    """The shared pagination:hidden-label class and the page-* registry icons reach both table arrows."""
    with translation.override("en"):
        nav = _table_pagination(paginated_author_client, page)
    for direction, icon in (("previous", "bi bi-arrow-left"), ("next", "bi bi-arrow-right")):
        _, link = _direction(nav, direction)
        (label,) = link.cssselect("span")
        assert label.get("class") == "sr-only"
        assert label.text_content() == direction
        assert link.cssselect("i")[0].get("class") == icon
    assert nav.cssselect(".visually-hidden") == []
