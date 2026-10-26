"""#262: the list filter toggle honours the context label mode (icon, both, label) — Phase 3 / FILT-01..04."""

import pytest
from django.template.loader import render_to_string
from django.test import override_settings
from django.utils import translation

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
