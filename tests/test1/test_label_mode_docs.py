"""The label-mode configuration contract in the reference docs: an executable recipe and canonical cross-links."""

import ast
import re
from pathlib import Path

from django.template import Context, Template
from django.test import override_settings
from lxml import html as lxml_html

from crud_views.lib.view import label_mode

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SETTINGS_MD = DOCS / "reference" / "settings.md"
ACTION_MENUS_MD = DOCS / "reference" / "action_menus.md"

SETTING = "CRUD_VIEWS_LABEL_MODE_DEFAULTS"
FENCE = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)
HEADING = re.compile(r"^(#{1,6}) (.+)$", re.MULTILINE)
ANY_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def _headings(text: str) -> list[re.Match]:
    """The markdown headings of a page, ignoring "# comment" lines inside fenced code."""
    fences = [m.span() for m in ANY_FENCE.finditer(text)]
    return [m for m in HEADING.finditer(text) if not any(a <= m.start() < b for a, b in fences)]


def _section(text: str, heading: str) -> str:
    """The body below a markdown heading, up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    headings = _headings(text)
    matches = [m for m in headings if m.group(0) == heading]
    assert len(matches) == 1, f"{heading!r} must appear exactly once, found {len(matches)}"
    start = matches[0].end()
    for m in headings:
        if m.start() >= start and len(m.group(1)) <= level:
            return text[start : m.start()]
    return text[start:]


def _row(text: str, first_cell: str) -> list[str]:
    """The cells of the unique table row whose first cell is first_cell."""
    rows = [line for line in text.splitlines() if line.startswith(f"| {first_cell} |")]
    assert len(rows) == 1, f"row {first_cell!r} must appear exactly once, found {len(rows)}"
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", rows[0])[1:-1]]


def _anchors(path: Path) -> set[str]:
    """The anchors mkdocs derives from the headings of a page (toc slugify of the heading text)."""
    anchors = set()
    for m in _headings(path.read_text()):
        slug = re.sub(r"[^\w\s-]", "", m.group(2).strip().lower())
        anchors.add(re.sub(r"[\s]+", "-", slug))
    return anchors


def _render_card_button(defaults: dict):
    raw = {"cv_access": True, "cv_url": "/u/", "cv_key": "detail", "cv_label": "Details", "cv_icon_action": "detail"}
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=defaults):
        markup = Template('{% load crud_views %}{% cv_button "card" %}').render(Context(raw))
    return lxml_html.fragment_fromstring(markup, create_parent="div")


def test_documented_card_floor_renders_label_only():
    # select by content: the one standalone assignment of the setting whose literal dict has a card key
    examples = []
    for block in FENCE.findall(SETTINGS_MD.read_text()):
        if SETTING not in block:
            continue
        for node in ast.parse(block).body:  # a relevant block must parse: no swallowed SyntaxError
            if isinstance(node, ast.Assign) and [getattr(t, "id", None) for t in node.targets] == [SETTING]:
                value = ast.literal_eval(node.value)  # data only, never exec
                if isinstance(value, dict) and "card" in value:
                    examples.append(value)
    assert len(examples) == 1, examples
    assert examples[0] == {"card": "label"}

    root = _render_card_button(examples[0])
    actions = root.cssselect("a")
    assert len(actions) == 1
    a = actions[0]
    assert a.get("href") == "/u/"
    assert a.text_content().strip() == "Details"
    assert [span.text for span in a.cssselect("span")] == ["Details"]
    assert not a.cssselect("span.visually-hidden")
    assert not a.cssselect("i, svg")
    assert a.get("title") is None

    # the same raw data under empty defaults renders the package card floor "both": the setting removed the icon
    root = _render_card_button({})
    a = root.cssselect("a")[0]
    assert len(a.cssselect("i")) == 1
    assert a.text_content().strip() == "Details"


def test_label_mode_configuration_table():
    text = SETTINGS_MD.read_text()
    menus = _section(text, "## Action menus")

    # the setting row of the Action menus table: exact effective defaults and its check
    cells = _row(menus, SETTING)
    assert ast.literal_eval(cells[3].strip("`")) == dict(label_mode.LABEL_MODE_DEFAULTS)
    assert cells[2] == "`dict[str, str]`"
    assert "crud_views.E108" in cells[1]
    assert "merged per location" in cells[1]

    # the existing map rows: configurable floor, no fixed icon floor; the list row has no target-view step
    context = _row(menus, "CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE")[1]
    assert "keys not named are `icon`" not in context
    assert context.index("cv_context_action_label_mode") < context.index(f'"context"` entry of `{SETTING}')
    assert "(#label-mode-configuration)" in context
    listing = _row(menus, "CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE")[1]
    assert f'"list"` entry of `{SETTING}' in listing
    assert "cv_context_action_label_mode" not in listing
    assert "The same for" not in listing
    assert "(#label-mode-configuration)" in listing

    config = _section(text, "### Label-mode configuration")
    assert "| Knob | merge or replace | layer | keys |" in config
    assert "Existing per-action maps keep whole-dict replacement semantics." in config
    expected = {
        f"`{SETTING}`": ("merged per location", "project floor", '"card"'),
        "`CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`": ("replace", "setting", "context toolbar action key"),
        "`CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE`": ("replace", "setting", "list row action key"),
        "`ViewSet` `context_actions_label_mode` / `list_actions_label_mode`": ("replace", "ViewSet", "action key"),
        "`CrudView` `cv_context_actions_label_mode` / `cv_list_actions_label_mode`": ("replace", "view", "action key"),
        "`cv_context_action_label_mode`": ("scalar", "target view", "one string"),
        "`cv_card_actions_label_mode`": ("scalar", "card view", "one string"),
    }
    for knob, (merge, layer, keys) in expected.items():
        cells = _row(config, knob)
        assert merge in cells[1] and layer in cells[2] and keys in cells[3], (knob, cells)
    for knob in list(expected)[3:5]:
        assert "`None` inherits" in _row(config, knob)[1] and "`{}` selects an empty map" in _row(config, knob)[1]
    assert '`None` means the `"card"` floor' in _row(config, "`cv_card_actions_label_mode`")[1]

    # the public API at its exact module path, with lazy reads and the strict / non-strict distinction
    flat = " ".join(config.split())
    for name in ("default_label_mode", "LABEL_MODE_DEFAULTS"):
        assert hasattr(label_mode, name)
        assert f"`crud_views.lib.view.label_mode.{name}" in flat
    for phrase in (
        "`CardListView.cv_get_card_actions_label_mode()`",
        "`override_settings`",
        "on every call",
        "read-only",
        "`crud_views.E108` (error)",
        "raises `ValueError` in every mode",
        "raises `ValueError` in strict mode",
        "logs one warning",
        "unknown key is ignored",
    ):
        assert phrase in flat, phrase


def test_canonical_label_mode_resolution_sections():
    text = ACTION_MENUS_MD.read_text()
    label_section = _section(text, "## Label mode")
    for heading in ("Context", "List", "Card"):
        assert f"\n### {heading} label-mode resolution\n" in label_section
    assert "\n### Target-view default\n" in label_section
    assert "Any key not named is" not in label_section
    assert 'then `"icon"`.' not in label_section
    assert "(settings.md#label-mode-configuration)" in label_section

    def steps(heading: str) -> list[str]:
        body = _section(text, heading)
        return [item.replace("\n", " ") for item in re.findall(r"^\d+\. (.+?)(?=^\d+\. |\n\n)", body, re.M | re.S)]

    context = steps("### Context label-mode resolution")
    markers = (
        "own `cv_context_actions_label_mode`",
        "`ContextButton.label_mode`",
        "selected whole",
        "`cv_context_action_label_mode`",
        '`default_label_mode("context")`',
    )
    assert len(context) == len(markers)
    for step, marker in zip(context, markers, strict=True):
        assert marker in step, (marker, step)
    assert "if it names the key" in context[2]
    assert "`CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`" in context[2]

    listing = steps("### List label-mode resolution")
    assert len(listing) == 2
    assert "selected whole" in listing[0] and "if it names the key" in listing[0]
    assert '`default_label_mode("list")`' in listing[1]
    assert "never read" in _section(text, "### List label-mode resolution")

    card = steps("### Card label-mode resolution")
    markers = (
        "`CardAction.label_mode`",
        "no_label=True",
        "`cv_card_actions_label_mode`",
        '`default_label_mode("card")`',
    )
    assert len(card) == len(markers)
    for step, marker in zip(card, markers, strict=True):
        assert marker in step, (marker, step)
    assert '"both"' in card[3]
    assert "`CardListView.cv_get_card_actions_label_mode()`" in _section(text, "### Card label-mode resolution")

    target = _section(text, "### Target-view default")
    assert "above the project floor" in target
    assert "| `cv_context_actions_label_mode` | dict |" in target
    assert "| `cv_context_action_label_mode` | str |" in target

    rendering = _section(text, "### Rendering")
    assert "filter toggle" in rendering and "outside this configuration" in rendering
    assert "icon and short label in every mode" in rendering

    checks = _section(text, "## System checks")
    assert "error" in _row(checks, "`crud_views.E108`")[1]
    assert _row(checks, "`viewset.E211`")[1].count("string or None") == 2


def test_label_mode_reference_links_and_diagram():
    # phase-owned links point at the canonical sections, and those sections exist as headings
    links = {
        DOCS / "reference" / "card-list-view.md": (
            "(settings.md#label-mode-configuration)",
            "(action_menus.md#card-label-mode-resolution)",
        ),
        DOCS / "migrating-1.0.md": (
            "(reference/settings.md#label-mode-configuration)",
            "(reference/action_menus.md#card-label-mode-resolution)",
        ),
    }
    for source, targets in links.items():
        text = source.read_text()
        for target in targets:
            assert target in text, (source.name, target)
            page, anchor = target.strip("()").split("#")
            assert anchor in _anchors((source.parent / page).resolve()), (source.name, target)
    assert {"label-mode", "target-view-default"} <= _anchors(ACTION_MENUS_MD)
