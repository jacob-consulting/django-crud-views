"""Compile the actual published heading recipes with native styling and hostile input."""

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.template import Context, Engine, Template
from django.test import override_settings
from django.utils.html import escape
from django.utils.translation import gettext_lazy
from lxml import html

from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView
from tests.test1.test_heading_icons import HOST_LIBRARY

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "docs/reference/templates.md"
THEME = ROOT / "docs/reference/theme.md"
ICONS = ROOT / "docs/reference/icons.md"
RECIPES = [
    (TEMPLATES, "### Page title recipe", "page", "h2", "native-size-3", "mb-0"),
    (TEMPLATES, "### Modal title recipe", "modal", "h2", "native-size-5", "modal-title"),
    (ICONS, "### Plain group title recipe", "group", "h3", "native-size-5", 'utility" onclick="bad'),
    (ICONS, "### Title-button recipe", "group", "button", "", 'utility" onclick="bad'),
]


def recipe(path, section, language="django"):
    text = path.read_text()
    assert text.count(section) == 1, f"Missing or duplicated section: {section}"
    content = text.split(section, 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0]
    fences = re.findall(rf"^```{language}\n(.*?)^```", content, re.MULTILINE | re.DOTALL)
    assert len(fences) == 1, f"Expected one complete {language} fence in {section}"
    return fences[0]


def native_classes():
    namespace = {}
    exec(compile(recipe(THEME, "### Native heading class table", "python"), str(THEME), "exec"), namespace)
    return namespace["CRUD_VIEWS_BUTTON_CLASSES"]


def test_documented_heading_icon_defaults_match_registry():
    """Theme authors can copy the reference without changing presence/fallback semantics."""
    section = ICONS.read_text().split("## Heading icons", 1)[1].split("### Plain group title recipe", 1)[0]
    rows = re.findall(r"^\| `(heading(?:-(?:page|modal|group))?:icon-(?:host|inline))` \| (.*?) \|$", section, re.M)
    assert len(rows) == 8
    documented = dict(rows)
    for key, value in documented.items():
        if value == "Absent (inherits shared styling)":
            assert key not in DEFAULT_BUTTON_CLASSES
        else:
            assert value.startswith('`"') and value.endswith('"`')
            assert DEFAULT_BUTTON_CLASSES[key] == value[2:-2]
    assert {key for key in DEFAULT_BUTTON_CLASSES if ":icon-" in key and key.startswith("heading")} == {
        key for key, value in documented.items() if value != "Absent (inherits shared styling)"
    }


@pytest.mark.parametrize("path,section,location,tag,size,utility", RECIPES)
@pytest.mark.parametrize("icon", ["host:edit", "fas:pen", None, "", "disabled"])
@pytest.mark.parametrize("clear_size", [False, True])
@pytest.mark.parametrize("hostile_classes", [False, True])
def test_published_heading_recipe(
    monkeypatch, path, section, location, tag, size, utility, icon, clear_size, hostile_classes
):
    monkeypatch.setattr(crud_views_settings, "header_level", 2)
    classes = native_classes()
    assert {f"heading:size-{n}" for n in range(1, 7)} <= classes.keys()
    if clear_size:
        classes.update({f"heading:size-{n}": None if n % 2 else "" for n in range(1, 7)})
    suffix = '" onload="bad' if hostile_classes else ""
    if hostile_classes:
        classes = {key: value + suffix if value else value for key, value in classes.items()}
    title = gettext_lazy('<script>Title & "translated"</script>')

    class View(CrudView):
        cv_header = title

        def cv_get_header_icon(self):
            return icon

    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_ICONS={"disabled": None},
        CRUD_VIEWS_BUTTON_CLASSES=classes,
    ):
        rendered = Template(recipe(path, section)).render(
            Context({"view": View(), "group": SimpleNamespace(title=title, icon=icon), "title_classes": utility})
        )
    node = html.fromstring(rendered)
    assert node.tag == tag
    assert node.text_content().strip() == str(title)
    assert not node.cssselect("script")
    assert set(node.attrib) == ({"type", "class"} if tag == "button" else {"class"})
    expected = " ".join(
        value
        for value in (
            size + suffix if size and not clear_size else "",
            utility,
            "native-icon icon-edit" + suffix if icon == "host:edit" else "",
        )
        if value
    )
    assert node.get("class") == expected
    assert not any(re.fullmatch(r"h[1-6]", token) for token in node.get("class").split())
    icons = node.cssselect("i")
    assert len(icons) == (1 if icon == "fas:pen" else 0)
    if icons:
        assert icons[0].get("class") == "fa-solid fa-pen native-inline" + suffix
        assert icons[0].get("aria-hidden") == "true"
        assert set(icons[0].attrib) == {"class", "aria-hidden"}
    if location == "modal":
        if icons:
            assert f"</i> {escape(title)}" in rendered
        else:
            assert node.text.startswith(" ")


def test_published_page_visible_title_block_is_overridable(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "header_level", 2)
    engine = Engine(
        loaders=[
            (
                "django.template.loaders.locmem.Loader",
                {
                    "base.html": recipe(TEMPLATES, "### Page title recipe"),
                    "child.html": '{% extends "base.html" %}{% block cv_header %}{{ custom_title }}{% endblock %}',
                },
            )
        ],
        libraries={"crud_views": "crud_views.templatetags.crud_views"},
    )
    result = engine.get_template("child.html").render(Context({"custom_title": "<b>My title</b>"}))
    heading = html.fromstring(result)
    assert heading.tag == "h2"
    assert heading.text_content().strip() == "<b>My title</b>"
    assert len(heading) == 0
