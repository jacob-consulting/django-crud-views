import os
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import django_tables2
import pytest
from django.template import Context, Engine, Template
from django.template.loader_tags import BlockNode
from django.test import RequestFactory, override_settings
from django.test.client import Client
from django.utils import translation
from django_tables2 import RequestConfig
from django_tables2.templatetags.django_tables2 import table_page_range
from lxml import html

import crud_views
from tests.lib.helper.boostrap5 import Table

TABLE_TEMPLATE = "crud_views/table/bootstrap5.html"
# the package's own templates: the tracked src/ files in a development checkout, their installed copy under nox
TEMPLATES_ROOT = (Path(crud_views.__file__).resolve().parent / "templates").resolve()
TABLE_TEMPLATE_PATH = (TEMPLATES_ROOT / TABLE_TEMPLATE).resolve()


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


# D-04/D-05/D-07: the preserved block names as a theme extension point. Child templates live only in an isolated
# Engine (locmem children over the package's own templates), so no global loader is mutated.


class PaginationTable(django_tables2.Table):
    """A bare framework table: dictionary rows, no view context, no action column."""

    value = django_tables2.Column()


def _rows(count: int) -> list[dict]:
    return [{"value": f"row {i}"} for i in range(1, count + 1)]


def _pagination_table(rows: int, page=None, *, per_page=2, paginate=True, prefix="", query=None, **table_kwargs):
    """A fresh PaginationTable configured from a real request carrying the chosen prefixed page field."""
    table = PaginationTable(_rows(rows), prefix=prefix, **table_kwargs)
    data = dict(query or {})
    if page is not None:
        data[table.prefixed_page_field] = str(page)
    request = RequestFactory().get("/", data=data)
    RequestConfig(request, paginate={"per_page": per_page} if paginate else False).configure(table)
    return table, request


def _pagination_engine(children: dict[str, str] | None = None) -> Engine:
    return Engine(
        loaders=[
            ("django.template.loaders.locmem.Loader", dict(children or {})),
            ("django.template.loaders.filesystem.Loader", [str(TEMPLATES_ROOT)]),
        ],
        libraries={
            "crud_views": "crud_views.templatetags.crud_views",
            "django_tables2": "django_tables2.templatetags.django_tables2",
            "i18n": "django.templatetags.i18n",
        },
        autoescape=True,
    )


def _render_table_pagination(table, request, template_name: str = TABLE_TEMPLATE, children=None) -> str:
    """Render ``template_name`` (a stock or locmem child template) for a prepared table and explicit request."""
    children = dict(children or {})
    assert TABLE_TEMPLATE not in children, "the test renders a child under its own name; the stock template is the base"
    engine = _pagination_engine(children)
    # the extended base resolves through the filesystem loader to the package's own tracked template
    base = engine.get_template(TABLE_TEMPLATE)
    assert Path(base.origin.name).resolve() == TABLE_TEMPLATE_PATH, base.origin.name
    context = Context({"table": table, "request": request}, autoescape=True)
    had_context = hasattr(table, "context")
    previous = getattr(table, "context", None)
    table.context = context
    try:
        table.before_render(request)
        return engine.get_template(template_name).render(context)
    finally:
        if had_context:
            table.context = previous
        else:
            del table.context


def _nav(rendered: str):
    """The single pagination nav of a rendered table."""
    (ul,) = html.fromstring(rendered).cssselect("nav > ul.pagination")
    return ul.getparent()


class _PageNumberSpy:
    """Counts calls of a Page number method; a plain callable, so the template engine calls it normally."""

    def __init__(self, method):
        self.method = method
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.method()


def _spy_page_numbers(table) -> dict[str, _PageNumberSpy]:
    # attach after RequestConfig.configure(): rendering then observes the very Page object it reads
    spies = {name: _PageNumberSpy(getattr(table.page, name)) for name in ("previous_page_number", "next_page_number")}
    for name, spy in spies.items():
        setattr(table.page, name, spy)
    return spies


DIRECTION_OVERRIDE_CHILD = """{% extends "crud_views/table/bootstrap5.html" %}{% load crud_views %}
{% block pagination.previous %}
{% if table.page.has_previous %}
<li class="theme-previous" data-state="enabled">
  <a href="{% cv_querystring table.prefixed_page_field=table.page.previous_page_number %}">back</a>
</li>
{% else %}
<li class="theme-previous" data-state="disabled"><span>back</span></li>
{% endif %}
{% endblock pagination.previous %}
{% block pagination.next %}
{% if table.page.has_next %}
<li class="theme-next" data-state="enabled">
  <a href="{% cv_querystring table.prefixed_page_field=table.page.next_page_number %}">forward</a>
</li>
{% else %}
<li class="theme-next" data-state="disabled"><span>forward</span></li>
{% endif %}
{% endblock pagination.next %}
"""

RANGE_OVERRIDE_CHILD = """{% extends "crud_views/table/bootstrap5.html" %}
{% block pagination.range %}
<li class="theme-range">{{ table.page.number }}/{{ table.paginator.num_pages }}</li>
{% endblock pagination.range %}
"""


@pytest.mark.parametrize("page, previous, next_", [(1, None, 2), (2, 1, 3), (3, 2, None)])
def test_table_pagination_direction_overrides(page, previous, next_):
    """Each direction block runs on enabled AND disabled ends; a guarded override never asks for a missing page."""
    table, request = _pagination_table(5, page)
    spies = _spy_page_numbers(table)
    nav = _nav(
        _render_table_pagination(table, request, "theme/table.html", {"theme/table.html": DIRECTION_OVERRIDE_CHILD})
    )

    for css, target, method in (
        ("theme-previous", previous, "previous_page_number"),
        ("theme-next", next_, "next_page_number"),
    ):
        (item,) = nav.cssselect(f"li.{css}")
        if target is None:
            assert item.get("data-state") == "disabled"
            assert item.cssselect("a") == []
            assert spies[method].calls == 0
        else:
            assert item.get("data-state") == "enabled"
            (link,) = item.cssselect("a")
            assert link.get("href") == f"?page={target}"
            assert spies[method].calls == 1
    # the overrides replaced the stock direction items; the stock range survives between them
    assert nav.cssselect("li.previous, li.next") == []
    (current,) = nav.cssselect('li[aria-current="page"]')
    assert current.text_content().strip() == str(page)

    # the stock blocks are guarded the same way
    table, request = _pagination_table(5, page)
    spies = _spy_page_numbers(table)
    _render_table_pagination(table, request)
    assert spies["previous_page_number"].calls == (0 if previous is None else 1)
    assert spies["next_page_number"].calls == (0 if next_ is None else 1)


@pytest.mark.parametrize("page", [1, 2, 3])
def test_table_pagination_range_override(page):
    """A pagination.range override replaces only the range; the inherited stock direction items remain."""
    table, request = _pagination_table(5, page)
    nav = _nav(_render_table_pagination(table, request, "theme/table.html", {"theme/table.html": RANGE_OVERRIDE_CHILD}))

    items = nav.cssselect("ul.pagination > li")
    assert [item.get("class").split()[0] for item in items] == ["previous", "theme-range", "next"]
    assert items[1].text_content() == f"{page}/3"
    # the stock numeric range is gone: no current-page item, no numeric link
    assert nav.cssselect('li[aria-current="page"]') == []
    assert [a.text_content().strip() for a in nav.cssselect("a.page-link")] == ["previous", "next"]
    for direction, enabled in (("previous", page > 1), ("next", page < 3)):
        _, link = _direction(nav, direction)
        assert (link.get("href") is not None) is enabled
        assert (link.get("aria-disabled") == "true") is not enabled


# every block of the stock table template, mapped to the blocks nested inside it
TABLE_BLOCKS = {
    "table-wrapper": {
        "table",
        "table.thead",
        "table.tbody",
        "table.tbody.row",
        "table.tbody.empty_text",
        "table.tfoot",
        "pagination",
        "pagination.previous",
        "pagination.range",
        "pagination.next",
    },
    "table": {"table.thead", "table.tbody", "table.tbody.row", "table.tbody.empty_text", "table.tfoot"},
    "table.thead": set(),
    "table.tbody": {"table.tbody.row", "table.tbody.empty_text"},
    "table.tbody.row": set(),
    "table.tbody.empty_text": set(),
    "table.tfoot": set(),
    "pagination": {"pagination.previous", "pagination.range", "pagination.next"},
    "pagination.previous": set(),
    "pagination.range": set(),
    "pagination.next": set(),
}


def test_table_template_block_contract():
    """The stock template keeps every django-tables2 block name and its nesting."""
    template = _pagination_engine().get_template(TABLE_TEMPLATE)
    assert Path(template.origin.name).resolve() == TABLE_TEMPLATE_PATH
    blocks = template.nodelist.get_nodes_by_type(BlockNode)
    assert sorted(block.name for block in blocks) == sorted(TABLE_BLOCKS)
    nested = {block.name: {inner.name for inner in block.nodelist.get_nodes_by_type(BlockNode)} for block in blocks}
    assert nested == TABLE_BLOCKS


@pytest.mark.parametrize("block", sorted(TABLE_BLOCKS))
def test_table_template_block_reachable(block):
    """Overriding any block (keeping block.super) reaches the rendered output of a real paginated or empty table."""
    child = (
        '{% extends "crud_views/table/bootstrap5.html" %}'
        f'{{% block {block} %}}<b data-cv-block="{block}"></b>{{{{ block.super }}}}{{% endblock {block} %}}'
    )
    if block == "table.tbody.empty_text":
        table, request = _pagination_table(0, empty_text="nothing here")
    else:
        table, request = _pagination_table(5, 2)
    rendered = _render_table_pagination(table, request, "theme/table.html", {"theme/table.html": child})
    assert rendered.count(f'data-cv-block="{block}"') == (2 if block == "table.tbody.row" else 1)
    # block.super keeps the stock content: the table and, when paginated, the stock pagination still render
    doc = html.fromstring(rendered)
    assert len(doc.cssselect("table")) == 1
    if block != "table.tbody.empty_text":
        assert len(doc.cssselect("nav > ul.pagination")) == 1


# PAGE-02/03/04 edges: shared accessibility contract, query/range handling, empty states, translations, icons and
# class values. _assert_pagination_accessibility, _assert_hidden_labels and HIDDEN_LABEL_CASES are reused by
# test_card_order.py so both components are held to one semantic contract.


def _href_query(href: str) -> dict[str, list[str]]:
    assert href.startswith("?"), href
    return parse_qs(urlsplit(href).query, keep_blank_values=True, strict_parsing=True)


def _href_page(href: str, page_param: str) -> int:
    (value,) = _href_query(href)[page_param]
    return int(value)


def _assert_pagination_accessibility(nav, page: int, num_pages: int, page_param: str = "page", labels=None):
    """The accessible pagination structure shared by table and card; returns the rendered range tokens.

    Compares semantics only: the table's previous/next item hooks and the card nav's spacing class may differ.
    """
    labels = labels or {"previous": "previous", "next": "next"}
    previous, *numbers, next_ = nav.cssselect("ul.pagination > li")
    for item, direction, target in (
        (previous, "previous", page - 1 if page > 1 else None),
        (next_, "next", page + 1 if page < num_pages else None),
    ):
        classes = item.get("class").split()
        assert "page-item" in classes
        (link,) = item.cssselect("a.page-link")
        # icon before the "previous" label, the "next" label before its icon; the icon is decorative
        assert [child.tag for child in link] == (["i", "span"] if direction == "previous" else ["span", "i"])
        icon = link.find("i")
        assert icon.get("aria-hidden") == "true"
        assert icon.text_content() == ""
        assert link.find("span").text_content() == labels[direction]
        assert link.text_content() == labels[direction]
        assert link.get("tabindex") is None
        if target is None:
            assert "disabled" in classes
            assert link.get("aria-disabled") == "true"
            assert link.get("href") is None
        else:
            assert "disabled" not in classes
            assert link.get("aria-disabled") is None
            assert _href_page(link.get("href"), page_param) == target

    (current,) = [item for item in numbers if item.get("aria-current") == "page"]
    assert {"page-item", "active"} <= set(current.get("class").split())
    assert current.cssselect("a") == []
    (number,) = current.cssselect("span.page-link")
    assert number.text_content().strip() == str(page)

    tokens = []
    for item in numbers:
        tokens.append(item.text_content().strip())
        if item is current:
            continue
        assert "active" not in item.get("class").split()
        (link,) = item.cssselect("a.page-link")
        assert link.get("tabindex") is None
        if tokens[-1] == "...":
            assert link.get("href") is None  # an ellipsis is never navigable
        else:
            assert _href_page(link.get("href"), page_param) == int(tokens[-1])
    return tokens


HOSTILE_QUERY = 'Grüße, Zoë ✓ "><script>alert(1)</script>&authors-page=9 \'<b onclick="x()">\''


def test_table_pagination_prefixed_query_preservation():
    """Links replace only this table's prefixed page key; every other decoded query value survives as data."""
    query = {"authors-sort": "value", "books-page": "4", "q": HOSTILE_QUERY, "tag": ["a", "b"]}
    table, request = _pagination_table(5, 2, prefix="authors-", query=query)
    assert table.prefixed_page_field == "authors-page"
    assert request.GET.getlist("tag") == ["a", "b"]
    rendered = _render_table_pagination(table, request)
    nav = _nav(rendered)

    _assert_pagination_accessibility(nav, 2, 3, page_param="authors-page")
    hrefs = [a.get("href") for a in nav.cssselect("a[href]")]
    assert len(hrefs) == 4  # previous, pages 1 and 3, next: real links before any negative assertion
    targets = []
    for href in hrefs:
        parsed = _href_query(href)
        (target,) = parsed.pop("authors-page")
        targets.append(int(target))
        assert parsed == {"authors-sort": ["value"], "books-page": ["4"], "q": [HOSTILE_QUERY], "tag": ["a", "b"]}
    assert targets == [1, 1, 3, 3]

    # the hostile value stays attribute data: no injected element or attribute anywhere in the pagination
    assert html.fromstring(rendered).cssselect("script") == []
    assert [element.tag for element in nav.iter()].count("b") == 0
    for link in nav.cssselect("a"):
        assert set(link.attrib) <= {"class", "href", "aria-disabled"}


@pytest.mark.parametrize(
    "case, rows, page, paginate",
    [
        ("unpaginated", 5, None, False),
        ("zero records", 0, None, True),
        ("one record", 1, None, True),
        ("one full page", 2, None, True),
        ("long range", 30, 15, True),
    ],
)
@override_settings(DJANGO_TABLES2_PAGE_RANGE=10)
def test_table_pagination_range_and_empty_cases(case, rows, page, paginate):
    per_page = 1 if case == "long range" else 2
    table, request = _pagination_table(rows, page, per_page=per_page, paginate=paginate, empty_text="No rows")
    rendered = _render_table_pagination(table, request)
    doc = html.fromstring(rendered)
    body_rows = doc.cssselect("table > tbody > tr")

    if case != "long range":
        # no paginator/page, or a single page: no pagination at all, the established table rendering stays
        assert doc.cssselect("nav") == []
        assert doc.cssselect(".pagination, .page-item, .page-link") == []
        if rows == 0:
            (row,) = body_rows
            (cell,) = row.cssselect("td")
            assert (cell.get("colspan"), cell.text_content()) == ("1", "No rows")
        else:
            assert [row.text_content().strip() for row in body_rows] == [f"row {i}" for i in range(1, rows + 1)]
        return

    # django-tables2's own range algorithm, unchanged: numeric order with non-navigable ellipses
    expected = [str(token) for token in table_page_range(table.page, table.paginator)]
    assert expected == ["1", "...", "12", "13", "14", "15", "16", "17", "...", "30"]
    tokens = _assert_pagination_accessibility(_nav(rendered), 15, 30)
    assert tokens == expected
    numbers = [int(token) for token in tokens if token != "..."]
    assert numbers == sorted(numbers)
    ellipses = [li for li in _nav(rendered).cssselect("li.page-item") if li.text_content().strip() == "..."]
    assert len(ellipses) == 2
    for li in ellipses:
        (link,) = li.cssselect("a.page-link")
        assert "disabled" in li.get("class").split()
        assert (link.get("aria-disabled"), link.get("href")) == ("true", None)
    (current,) = _nav(rendered).cssselect('li[aria-current="page"]')
    assert current.cssselect("span.page-link")[0].text_content() == "15"
    assert [row.text_content().strip() for row in body_rows] == ["row 15"]


@pytest.mark.parametrize("raw, expected", [("abc", 1), ("99", 3), ("0", 3)])
def test_table_pagination_invalid_page_inputs(raw, expected):
    """django-tables2's own RequestConfig semantics: a non-integer page is page 1, an empty page the last page."""
    table, request = _pagination_table(5, raw)
    _assert_pagination_accessibility(_nav(_render_table_pagination(table, request)), expected, 3)


SENTINEL_LABELS = {"pagination": "NAV-⚑", "previous": "PREV-⚑", "next": "NEXT-⚑"}


def patch_sentinel_translations(monkeypatch):
    """Route the three pagination msgids through the active gettext to sentinels; restored by monkeypatch."""
    real = translation._trans.gettext
    monkeypatch.setattr(translation._trans, "gettext", lambda message: SENTINEL_LABELS.get(message, real(message)))


def _label_texts(nav) -> tuple[str, list[str]]:
    return nav.get("aria-label"), [_direction(nav, d)[1].find("span").text_content() for d in ("previous", "next")]


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
@override_settings(LANGUAGES=[("en", "English"), ("de", "German")])
def test_table_pagination_labels_translated(paginated_author_client, monkeypatch, page):
    """German labels on enabled and disabled ends; a sentinel catalog proves the labels are translated, not literal."""
    with translation.override("de"):
        nav = _table_pagination(paginated_author_client, page)
    assert _label_texts(nav) == ("Seitennavigation", ["zurück", "weiter"])
    _assert_pagination_accessibility(nav, page, 2, labels={"previous": "zurück", "next": "weiter"})

    patch_sentinel_translations(monkeypatch)
    with translation.override("de"):
        nav = _table_pagination(paginated_author_client, page)
    assert _label_texts(nav) == ("NAV-⚑", ["PREV-⚑", "NEXT-⚑"])


@pytest.mark.parametrize("page", [1, 2, 3])
@override_settings(CRUD_VIEWS_ICONS={"page-previous": "bi:arrow-left", "page-next": "bi:arrow-right"})
def test_table_pagination_registry_overrides(page):
    """Overridden page-* registry icons reach both arrows, enabled and disabled alike."""
    table, request = _pagination_table(5, page)
    nav = _nav(_render_table_pagination(table, request))
    for direction, icon, disabled in (
        ("previous", "bi bi-arrow-left", page == 1),
        ("next", "bi bi-arrow-right", page == 3),
    ):
        item, link = _direction(nav, direction)
        assert ("disabled" in item.get("class").split()) is disabled
        (element,) = link.cssselect("i")
        assert element.get("class") == icon
    assert "fa-chevron" not in html.tostring(nav, encoding="unicode")


NO_SETTING = object()
HOSTILE_CLASS = 'x" onclick="alert(1)" data-injected=\'<b>z</b>\''
# case id -> (CRUD_VIEWS_BUTTON_CLASSES, expected class attribute of both arrow labels)
HIDDEN_LABEL_CASES = {
    "no setting": (NO_SETTING, "visually-hidden"),
    "key omitted": ({"card-order:active": "is-active"}, "visually-hidden"),
    "sr-only": ({"pagination:hidden-label": "sr-only"}, "sr-only"),
    "None": ({"pagination:hidden-label": None}, ""),
    "empty": ({"pagination:hidden-label": ""}, ""),
    "unicode": ({"pagination:hidden-label": "versteckt-ä ✓ 隠す"}, "versteckt-ä ✓ 隠す"),
    "hostile": ({"pagination:hidden-label": HOSTILE_CLASS}, HOSTILE_CLASS),
}


def hidden_label_settings(mapping):
    return override_settings() if mapping is NO_SETTING else override_settings(CRUD_VIEWS_BUTTON_CLASSES=mapping)


def _assert_hidden_labels(nav, raw: str, expected: str):
    """Both arrow labels carry exactly one class attribute with the configured value, labels and icons intact."""
    items = nav.cssselect("ul.pagination > li")
    for item, direction in ((items[0], "previous"), (items[-1], "next")):
        (link,) = item.cssselect("a.page-link")
        (label,) = link.cssselect("span")
        assert dict(label.attrib) == {"class": expected}
        assert label.text_content() == direction
        assert len(link.cssselect("i[aria-hidden=true]")) == 1
        if expected == "":
            # None and "" both render an explicitly empty attribute, never a dropped label
            assert raw.count(f'<span class="">{direction}</span>') == 1
    for element in nav.iter():
        assert element.tag != "b"
        assert "onclick" not in element.attrib and "data-injected" not in element.attrib
    if expected:
        # code points round-trip: the decoded attribute equals the configured string (UTF-8 in the raw response)
        assert len([s for s in nav.iter("span") if s.get("class") == expected]) == 2


@pytest.mark.django_db
@pytest.mark.parametrize("page", [1, 2])
@pytest.mark.parametrize("case", HIDDEN_LABEL_CASES)
def test_table_pagination_hidden_label_values(paginated_author_client, case, page):
    mapping, expected = HIDDEN_LABEL_CASES[case]
    with hidden_label_settings(mapping), translation.override("en"):
        response = paginated_author_client.get(f"/author/?page={page}")
        nav = _table_pagination(paginated_author_client, page)
    raw = response.content.decode("utf-8")
    _assert_hidden_labels(nav, raw, expected)
    if case == "unicode":
        assert f'class="{expected}"'.encode() in response.content
