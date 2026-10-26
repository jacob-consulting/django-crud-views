"""#262: the list filter toggle honours the context label mode (icon, both, label) — Phase 3 / FILT-01..04."""

import pytest
from django.template.loader import render_to_string
from django.test import override_settings
from django.urls import reverse
from django.utils import translation
from lxml import html as lxml_html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.buttons import FilterContextButton
from tests.test1.app.views import PublisherListView, cv_publisher

FILTER_TOGGLE = "crud_views/tags/context_action_filter.html"

# default icon / class tables: an explicit empty settings layer (setting_changed resets both caches on entry and exit)
default_tables = override_settings(CRUD_VIEWS_ICONS={}, CRUD_VIEWS_ICON_LIBRARIES={}, CRUD_VIEWS_BUTTON_CLASSES={})

RAW_DEFAULT_FILTER = {
    False: (
        "\n"
        '<button type="button"\n'
        '   class="btn btn-outline-primary btn-lg"\n'
        '   id="cv-filter-toggle"\n'
        '   aria-expanded="false"\n'
        '   aria-controls="filter-collapse"\n'
        '   title="Filter"\n'
        '   data-cv-tooltip="context"\n'
        '   cv-key="filter">\n'
        '    <span data-cv-filter-icon="open"><i class="fa-solid fa-filter" aria-hidden="true"></i></span>\n'
        '    <span data-cv-filter-icon="close" hidden>'
        '<i class="fa-solid fa-filter-circle-xmark" aria-hidden="true"></i></span>\n'
        '    <span class="visually-hidden">Filter</span>\n'
        "</button>\n"
    ),
    True: (
        "\n"
        '<button type="button"\n'
        '   class="btn btn-outline-primary btn-lg"\n'
        '   id="cv-filter-toggle"\n'
        '   aria-expanded="true"\n'
        '   aria-controls="filter-collapse"\n'
        '   title="Filter"\n'
        '   data-cv-tooltip="context"\n'
        '   cv-key="filter">\n'
        '    <span data-cv-filter-icon="open" hidden><i class="fa-solid fa-filter" aria-hidden="true"></i></span>\n'
        '    <span data-cv-filter-icon="close">'
        '<i class="fa-solid fa-filter-circle-xmark" aria-hidden="true"></i></span>\n'
        '    <span class="visually-hidden">Filter</span>\n'
        "</button>\n"
    ),
}
"""The exact pre-change render_to_string output of the stock filter toggle, collapsed and expanded.

Captured from the untouched template (source HEAD 3a51f81) and never regenerated. Unlike the normalized toolbar
golden, which sorts attributes and class tokens and collapses whitespace, this is a raw byte comparison: the leading
newline after the load line, the attribute indentation and the trailing newline are protected deliberately, even
though render_snippet() strips the boundary whitespace in page output. A passing golden cannot prove this.
"""


def _render_filter(expanded: bool, mode: str | None = None, **extra) -> str:
    """Render the filter leaf directly; mode None leaves cv_label_mode out of the context (a pre-#262 caller)."""
    ctx = {"cv_filter_expanded": expanded, "cv_action_label": "Filter", "cv_key": "filter", **extra}
    if mode is not None:
        ctx["cv_label_mode"] = mode
    return render_to_string(FILTER_TOGGLE, ctx)


@default_tables
@pytest.mark.parametrize("expanded", [False, True])
def test_filter_raw_default_bytes(expanded):
    with translation.override("en"):
        # a context without cv_label_mode (hand-built, or a pre-#262 override) keeps the exact pre-change output ...
        assert _render_filter(expanded) == RAW_DEFAULT_FILTER[expanded]
        # ... and so does the resolved default mode
        assert _render_filter(expanded, "icon") == RAW_DEFAULT_FILTER[expanded]


# DOM selectors specific to the filter toggle: its icons sit inside data-cv-filter-icon wrapper spans, so the generic
# "an unclassed span is the visible label" predicate of ordinary actions would count those wrappers as labels
VISIBLE_LABEL = "./span[not(@class) and not(@data-cv-filter-icon)]"
WRAPPERS = "./span[@data-cv-filter-icon]"
WRAPPED_ICONS = "./span[@data-cv-filter-icon]//i"


def _filter_node(markup: str):
    """The one filter toggle button in a page or fragment."""
    nodes = lxml_html.fromstring(markup).xpath("//button[@id='cv-filter-toggle']")
    assert len(nodes) == 1, markup
    return nodes[0]


def _publisher_view(client):
    """The rendered publisher list view (the stock page whose toolbar has the filter toggle)."""
    resp = client.get(reverse(cv_publisher.get_router_name("list")))
    assert resp.status_code == 200
    return resp.context["view"]


def _page_toggle(client):
    resp = client.get(reverse(cv_publisher.get_router_name("list")))
    assert resp.status_code == 200
    return _filter_node(resp.content.decode())


def _select_settings_map(monkeypatch, mapping):
    """Select CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE: captured at import, so patch the snapshot, and clear the more
    specific view and ViewSet maps so the setting is the first map found."""
    monkeypatch.setattr(PublisherListView, "cv_context_actions_label_mode", None)
    monkeypatch.setattr(cv_publisher, "context_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", mapping)


BOTH_CLASSES = {"context:secondary:both": "btn cv-test-both"}


@pytest.mark.django_db
def test_filter_both_tracer(client_user_publisher_view, monkeypatch):
    """A settings-map "both" entry reaches the toggle through the real toolbar and survives the persisted toggle."""
    _select_settings_map(monkeypatch, {"filter": "both"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=BOTH_CLASSES):
        # the direct builder context carries the resolved mode
        view = _publisher_view(client_user_publisher_view)
        ctx = FilterContextButton().get_context(view.cv_get_view_context())
        assert ctx.get("cv_label_mode") == "both"

        for expanded in (False, True):
            if expanded:
                post = client_user_publisher_view.post(
                    reverse(cv_publisher.get_router_name("list")),
                    data='{"filter_expanded": true}',
                    content_type="application/json",
                )
                assert post.status_code == 200
            button = _page_toggle(client_user_publisher_view)
            # the both-specific class key reaches the button
            assert button.get("class").split() == ["btn", "cv-test-both"]
            assert button.get("aria-expanded") == str(expanded).lower()
            assert button.get("aria-controls") == "filter-collapse"
            assert button.get("cv-key") == "filter"
            # a visible label: no title and no tooltip marker
            assert button.get("title") is None
            assert button.get("data-cv-tooltip") is None
            labels = button.xpath(VISIBLE_LABEL)
            assert [label.text for label in labels] == ["Filter"]
            assert button.xpath("./span[@class]") == []  # no hidden label next to the visible one
            # element icons: both wrappers, the inactive one hidden
            wrappers = {w.get("data-cv-filter-icon"): w for w in button.xpath(WRAPPERS)}
            assert set(wrappers) == {"open", "close"}
            assert (wrappers["open"].get("hidden") is not None) is expanded
            assert (wrappers["close"].get("hidden") is not None) is not expanded
            assert len(button.xpath(WRAPPED_ICONS)) == 2
            # the label is separated from the icons by whitespace
            assert labels[0].getprevious().tail.strip() == ""
            assert labels[0].getprevious().tail != ""


@pytest.mark.django_db
def test_filter_direct_context_mode_less_icon_class(client_user_publisher_view, monkeypatch):
    """Without a configured mode the direct context resolves the context floor and the leaf keeps icon classes."""
    _select_settings_map(monkeypatch, {})
    view = _publisher_view(client_user_publisher_view)
    assert FilterContextButton().get_context(view.cv_get_view_context()).get("cv_label_mode") == "icon"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:secondary:icon": "btn cv-test-icon"}):
        for expanded in (False, True):
            assert _filter_node(_render_filter(expanded)).get("class").split() == ["btn", "cv-test-icon"]
            assert _filter_node(_render_filter(expanded, "icon")).get("class").split() == ["btn", "cv-test-icon"]
