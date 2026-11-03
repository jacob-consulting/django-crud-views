"""The documented table pagination override recipe (D-05/D-08): extracted from docs/migrating-1.0.md and rendered."""

import re

import pytest
from django.test import override_settings
from django.utils import translation
from lxml import html

from crud_views.lib.button_classes import get_button_class
from crud_views.lib.icons import get_icons
from tests.test1.test_alerts import TEMPLATE_FENCE
from tests.test1.test_label_mode_docs import CHANGELOG_MD, MIGRATING_MD, _section
from tests.test1.test_table_template import (
    TABLE_TEMPLATE,
    _assert_pagination_accessibility,
    _direction,
    _href_page,
    _nav,
    _pagination_table,
    _render_table_pagination,
    _spy_page_numbers,
)

HEADING = "### Table pagination overrides"
CONTRACT_HEADING = "### Contract changes in templates you still override"
SILENT_HEADING = "## Silent breaks"
SETTING = re.compile(r'^DJANGO_TABLES2_TEMPLATE = "([^"]+)"$', re.MULTILINE)
CHILD_PATH = re.compile(r"`([\w./-]+/templates/([\w./-]+\.html))`")
EXTENDS = re.compile(r'{% extends "([^"]+)" %}')
NUM_PAGES = 3
OVERRIDE_CLASSES = {"pagination:hidden-label": "sr-only"}
OVERRIDE_ICONS = {"page-previous": "bi:arrow-left", "page-next": "bi:arrow-right"}


def _migration_section() -> str:
    text = MIGRATING_MD.read_text(encoding="utf-8")
    # placed after the complete contract-changes section and immediately before "## Silent breaks"
    section = _section(text, HEADING)
    assert text.index(CONTRACT_HEADING) < text.index(HEADING) < text.index(SILENT_HEADING)
    assert text.index(HEADING) + len(HEADING) + len(section) == text.index(SILENT_HEADING)
    return section


def _pagination_override_recipe() -> tuple[str, str]:
    """The single django template fence under the heading, and the child name the documented setting selects."""
    section = _migration_section()
    bodies = TEMPLATE_FENCE.findall(section)
    assert len(bodies) == 1, f"{HEADING!r} must hold exactly one django/html fence, found {len(bodies)}"
    (recipe,) = bodies

    (selected,) = SETTING.findall(section)
    paths = set(CHILD_PATH.findall(section))
    assert len(paths) == 1, paths
    ((path, name),) = paths
    # the documented file, the startup setting and the rendered child agree; the child never shadows its base
    assert path.endswith(f"/templates/{name}")
    assert name == selected
    (extends,) = EXTENDS.findall(recipe)
    assert extends == TABLE_TEMPLATE
    assert selected != extends
    return recipe, selected


def _render_recipe(recipe: str, name: str, page: int):
    """Render the recipe as the selected child for five rows at two per page; returns nav, spies and the table."""
    table, request = _pagination_table(5, page, template_name=name)
    assert table.template_name == name
    spies = _spy_page_numbers(table)
    rendered = _render_table_pagination(table, request, table.template_name, {name: recipe})
    return _nav(rendered), spies


def _direction_markup(nav) -> list[str]:
    return [html.tostring(_direction(nav, d)[0], encoding="unicode", with_tail=False) for d in ("previous", "next")]


def _icon_classes(nav) -> dict[str, str]:
    return {d: _direction(nav, d)[1].cssselect("i")[0].get("class") for d in ("previous", "next")}


def _assert_direction_style(nav, label_class: str, icons: dict[str, str], stock_icons: dict[str, str]):
    """Both arrows, enabled or disabled: one label with exactly label_class, one decorative icon, in stock order."""
    for direction in ("previous", "next"):
        _, link = _direction(nav, direction)
        (label,) = link.cssselect("span")
        assert label.get("class") == label_class
        assert label.text_content() == direction
        (icon,) = link.cssselect("i")
        assert icon.get("class") == icons[direction]
        assert icon.get("aria-hidden") == "true"
        assert [child.tag for child in link] == (["i", "span"] if direction == "previous" else ["span", "i"])
        if icons != stock_icons:
            # no default class and no stock chevron fallback survives in the control
            markup = html.tostring(link, encoding="unicode", with_tail=False)
            assert "visually-hidden" not in markup
            assert "chevron" not in markup
            assert not set(stock_icons.values()) & {icon.get("class")}


BOOTSTRAP_ARROWS = {"previous": "bi bi-arrow-left", "next": "bi bi-arrow-right"}


@pytest.mark.parametrize("page, previous, next_", [(1, None, 2), (2, 1, 3), (3, 2, None)])
def test_documented_pagination_direction_overrides(page, previous, next_):
    """The copied recipe renders on first/middle/last pages, keeps the stock contract and honors the shared keys."""
    recipe, name = _pagination_override_recipe()

    with translation.override("en"):
        nav, spies = _render_recipe(recipe, name, page)
        table, request = _pagination_table(5, page)
        stock = _nav(_render_table_pagination(table, request))

    # the guard: an unavailable direction never asks for its page number (that would raise EmptyPage)
    for method, target in (("previous_page_number", previous), ("next_page_number", next_)):
        assert spies[method].calls == (0 if target is None else 1)

    for direction, target, rel in (("previous", previous, "prev"), ("next", next_, "next")):
        item, link = _direction(nav, direction)
        stock_item, _ = _direction(stock, direction)
        # the same li class lists as the stock template, enabled and disabled
        assert item.get("class") == stock_item.get("class")
        if target is None:
            assert item.get("class") == f"{direction} page-item disabled"
            assert link.get("aria-disabled") == "true"
            assert link.get("href") is None
            assert link.get("tabindex") is None
            assert link.get("rel") is None
        else:
            assert item.get("class") == f"{direction} page-item"
            assert link.get("aria-disabled") is None
            assert _href_page(link.get("href"), "page") == target
            assert link.get("rel") == rel

    # the nav label, current page and range are inherited unchanged from the stock blocks
    _assert_pagination_accessibility(nav, page, NUM_PAGES)
    assert nav.get("aria-label") == stock.get("aria-label") == "pagination"
    items, stock_items = nav.cssselect("ul.pagination > li"), stock.cssselect("ul.pagination > li")
    assert [html.tostring(li, with_tail=False) for li in items[1:-1]] == [
        html.tostring(li, with_tail=False) for li in stock_items[1:-1]
    ]
    stock_icons = _icon_classes(stock)
    assert all("chevron" in value for value in stock_icons.values()), stock_icons
    _assert_direction_style(nav, "visually-hidden", stock_icons, stock_icons)

    # the recipe's arrows follow nondefault class and icon settings in both states, and both registries restore
    before_classes = get_button_class("pagination", "hidden-label")
    before_icons = dict(get_icons())
    before = _direction_markup(nav)
    with (
        translation.override("en"),
        override_settings(CRUD_VIEWS_BUTTON_CLASSES=OVERRIDE_CLASSES, CRUD_VIEWS_ICONS=OVERRIDE_ICONS),
    ):
        overridden, _ = _render_recipe(recipe, name, page)
        assert get_button_class("pagination", "hidden-label") == "sr-only"
    _assert_direction_style(overridden, "sr-only", BOOTSTRAP_ARROWS, stock_icons)
    _assert_pagination_accessibility(overridden, page, NUM_PAGES)

    with translation.override("en"):
        after, _ = _render_recipe(recipe, name, page)
    assert _direction_markup(after) == before
    assert get_button_class("pagination", "hidden-label") == before_classes == "visually-hidden"
    assert dict(get_icons()) == before_icons


def test_pagination_breaking_entry_links_migration():
    """The CHANGELOG Breaking entry names the guarded page-number calls and links the migration section."""
    breaking = _section(_section(CHANGELOG_MD.read_text(encoding="utf-8"), "## Unreleased"), "### Breaking")
    (entry,) = [item for item in re.split(r"^- ", breaking, flags=re.MULTILINE) if item.startswith("Table pagination")]
    assert "docs/migrating-1.0.md#table-pagination-overrides" in entry
    for name in ("pagination:hidden-label", "table.page.has_previous", "table.page.has_next", "EmptyPage"):
        assert name in entry
