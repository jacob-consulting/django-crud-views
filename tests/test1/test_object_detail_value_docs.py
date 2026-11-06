"""Execute the published object-detail value, composition and migration recipes."""

import re
from pathlib import Path

import pytest
from django.template import Context, Template
from django.test import override_settings
from lxml import html

from crud_views_object_detail.lib import conf
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.lib.config import BadgeConfig, parse_property_display, x
from crud_views_object_detail.lib.resolvers import ResolvedProperty, resolve_all, resolve_property
from crud_views_object_detail.templatetags import crud_views_object_detail as tags
from tests.test1.od.test_badge_semantics import render, template_settings
from tests.test1.od_app.models import ChoiceValue
from tests.test1.test_badge_docs import published_template

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference"


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch):
    monkeypatch.setattr(conf, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
    monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())


def recipe(page, name, language="python"):
    source = (ROOT / page).read_text(encoding="utf-8")
    blocks = re.findall(rf"<!-- object-detail-value-recipe: {name} -->\n```{language}\n(.*?)\n```", source, re.S)
    assert len(blocks) == 1, f"Expected one {name} recipe in {page}"
    return blocks[0]


def test_object_detail_value_docs_choices():
    namespace = {}
    exec(recipe("docs/reference/object_detail_configuration.md", "choices"), namespace)
    groups = parse_property_display(namespace["cv_property_display"])
    props = resolve_all(ChoiceValue(process="natural"), groups)[0].properties
    assert [p.value for p in props] == ["natural"] * 3
    assert [p.choice_label for p in props] == ["Naturally processed", None, None]
    assert [render(p).strip() for p in props] == ["Naturally processed", "natural", "natural"]
    assert props[1].label == "Stored process"


@pytest.mark.parametrize(
    "value,label,expected",
    [
        (None, None, "—"),
        ("", None, "—"),
        (0, None, "0"),
        (False, None, "False"),
        ("  ", None, "  "),
        (None, "Declared null label", "Declared null label"),
        ("code", "<script>hostile</script>", "<script>hostile</script>"),
        ("<img src=x>", None, "<img src=x>"),
    ],
)
def test_object_detail_value_docs_copied_text_leaf(value, label, expected):
    leaf = recipe("docs/reference/object_detail_configuration.md", "text-leaf", "django")
    prop = ResolvedProperty(path="value", label="Value", value=value, choice_label=label, template="copied.html")
    with override_settings(TEMPLATES=template_settings({"copied.html": leaf})):
        output = render(prop)
    node = html.fromstring(f"<div>{output}</div>")
    assert node.text_content() == expected
    assert not node.xpath(".//script | .//img")
    assert prop.value is value


@pytest.mark.parametrize("label", [None, "", "Explicit", "<img src=x>"])
def test_object_detail_value_docs_copied_badge_choice_fallback(label):
    prop = resolve_property(
        ChoiceValue(process="natural"),
        x("process", badge=BadgeConfig(color="brand-custom", label_map={"natural": label})),
    )
    with override_settings(
        TEMPLATES=template_settings({"crud_views_object_detail/types/native/badge.html": published_template()}),
        CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES="native",
    ):
        node = html.fromstring(render(prop))
    assert node.text_content() == (label or "Naturally processed")
    assert not node.xpath(".//img")
    assert prop.value == "natural"


@pytest.mark.parametrize("value,expected", [(None, "—"), ("", "")])
def test_object_detail_value_docs_badge_raw_empty_contract(value, expected):
    output = Template(published_template()).render(
        Context({"value": value, "display_value": "" if value == "" else "Declared null label", "prop": {}})
    )
    assert html.fromstring(output).text_content() == expected


def test_object_detail_value_docs_custom_raw_ownership():
    leaf_section = (REFERENCE / "object_detail_layout_packs.md").read_text().split("### native value", 1)[1]
    blocks = re.findall(r"```django\n(.*?)\n```", leaf_section, re.S)
    assert len(blocks) == 1
    prop = resolve_property(ChoiceValue(process="natural"), x("process", template="custom.html"))
    with override_settings(TEMPLATES=template_settings({"custom.html": blocks[0]})):
        node = html.fromstring(render(prop))
    assert node.text == "natural"
    assert prop.choice_label == "Naturally processed"


def test_object_detail_value_docs_context_and_translation_guidance():
    layout = (REFERENCE / "object_detail_layout_packs.md").read_text()
    assert "`prop`, `value`, `display_value`, and `od_settings`" in layout
    assert "`value` stays raw" in layout
    config = (REFERENCE / "object_detail_configuration.md").read_text()
    for contract in [
        "None` means no display result",
        "Unknown-code fallback may preserve non-string types",
        "active when resolved and are not retranslated when pre-resolved groups render",
        "help/detail text instead follows the active language at rendering",
        "including one-member collections",
        "raw `None` or `[]` stays unchanged",
    ]:
        assert contract in config
