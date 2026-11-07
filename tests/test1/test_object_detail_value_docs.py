"""Execute the published object-detail value, composition and migration recipes."""

import re
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.template import Context, Template
from django.test import override_settings
from django.utils.translation import override
from lxml import html

from crud_views.lib import check as check_module
from crud_views.lib import viewset as viewset_module
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_object_detail.lib import ObjectDetailMixin, ObjectDetailView, ObjectDetailViewPermissionRequired, conf
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.lib.config import BadgeConfig, parse_property_display, x
from crud_views_object_detail.lib.resolvers import ResolvedProperty, resolve_all, resolve_property
from crud_views_object_detail.templatetags import crud_views_object_detail as tags
from crud_views_polymorphic.lib import PolymorphicDetailViewPermissionRequired
from tests.test1.app.models import Vehicle
from tests.test1.od.test_badge_semantics import render, template_settings
from tests.test1.od_app.models import ChoiceValue, Info
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


@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("badge", [False, True])
def test_object_detail_value_docs_unknown_numeric_locale(language, badge):
    leaf = (
        published_template()
        if badge
        else recipe("docs/reference/object_detail_configuration.md", "text-leaf", "django")
    )
    prop = resolve_property(ChoiceValue(rank=10000), x("rank", badge="info" if badge else None))
    template = "crud_views_object_detail/types/default/badge.html" if badge else "copied.html"
    prop.template = template
    with (
        override_settings(USE_THOUSAND_SEPARATOR=True, TEMPLATES=template_settings({template: leaf})),
        override(language),
    ):
        output = html.fromstring(f"<div>{render(prop)}</div>").text_content().strip()
    assert output == "10000"
    assert type(prop.value) is type(prop.choice_label) is int
    assert prop.value == prop.choice_label == 10000


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


@pytest.mark.parametrize("project", [False, True])
@pytest.mark.parametrize("view_policy", [None, False, True])
def test_object_detail_value_docs_help_instructions(settings, project, view_policy):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = project
    namespace = {}
    exec(recipe("docs/reference/object_detail_settings.md", "help-instructions"), namespace)
    groups = parse_property_display([{"title": "Help", "properties": namespace["properties"]}])
    props = resolve_all(Info(text="Body"), groups, view=SimpleNamespace(cv_object_detail_show_help_text=view_policy))[
        0
    ].properties
    inherited = "The info body text" if (project if view_policy is None else view_policy) else None
    assert [p.detail for p in props] == [
        inherited,
        inherited,
        "The info body text",
        None,
        None,
        "Used for invoices.",
        "Invoice guidance",
    ]


def test_object_detail_value_docs_settings_fixture_refreshes_both(monkeypatch, settings):
    namespace = {}
    exec(recipe("docs/reference/object_detail_settings.md", "settings-fixture"), namespace)
    reset = namespace["fresh_object_detail_settings"].__wrapped__
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = False
    assert conf.crud_views_object_detail_settings.show_help_text is False
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = True
    assert conf.crud_views_object_detail_settings.show_help_text is False  # cached startup policy
    old_tags = tags.crud_views_object_detail_settings
    reset(monkeypatch)
    assert conf.crud_views_object_detail_settings.show_help_text is True
    assert tags.crud_views_object_detail_settings is not old_tags


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,bases,object_fixture,user_fixture",
    [
        ("complete", (ObjectDetailView,), "book_hitchhiker", "user_book_view"),
        ("complete-permission", (ObjectDetailViewPermissionRequired,), "book_hitchhiker", "user_book_view"),
        ("core", (ObjectDetailMixin, DetailViewPermissionRequired), "book_hitchhiker", "user_book_view"),
        ("guardian", (ObjectDetailMixin, GuardianDetailViewPermissionRequired), "book_hitchhiker", "user_guardian"),
        (
            "polymorphic",
            (ObjectDetailMixin, PolymorphicDetailViewPermissionRequired),
            "car_sedan",
            "user_vehicle_view",
        ),
    ],
)
def test_object_detail_value_docs_composition_context(
    monkeypatch, rf, request, name, bases, object_fixture, user_fixture
):
    # Load shared fixtures first, then isolate recipe registration without modifying their ViewSets.
    obj = request.getfixturevalue(object_fixture)
    user = request.getfixturevalue(user_fixture)
    monkeypatch.setattr(viewset_module, "_REGISTRY", OrderedDict())
    monkeypatch.setattr(check_module, "_VOCAB_CACHE", {})
    factory = GuardianViewSet if name == "guardian" else viewset_module.ViewSet
    viewset = factory(model=Vehicle if name == "polymorphic" else type(obj), name=f"recipe_{name.replace('-', '_')}")
    namespace = {"__name__": __name__, "cv_book": viewset, "cv_vehicle": viewset}
    exec(recipe("docs/reference/object_detail_view.md", name), namespace)
    cls = namespace["VehicleDetailView" if name == "polymorphic" else "BookDetailView"]
    assert cls.__bases__ == bases
    if name != "complete":
        assert cls.cv_permission == "view"
    assert cls.cv_viewset is viewset
    if name == "guardian":
        assert isinstance(cls.cv_viewset, GuardianViewSet)
    http_request = rf.get("/recipe/detail/")
    http_request.user = user
    view = cls()
    view.setup(http_request, pk=obj.pk)
    view.object = obj
    context = view.get_context_data(object=obj)
    expected = [obj.name] if name == "polymorphic" else [obj.title, obj.publisher.name]
    assert [p.value for g in context["object_detail_groups"] for p in g.properties] == expected
    output = Template(
        "{% load crud_views_object_detail %}{% render_object_detail object groups=object_detail_groups %}"
    ).render(Context({**context, "request": http_request, "view": view}))
    text = html.fromstring(output).text_content()
    assert all(value in text for value in expected)


def test_object_detail_value_docs_help_and_view_inventories():
    settings = (REFERENCE / "object_detail_settings.md").read_text()
    for contract in [
        "Only Python `True`/`False`",
        "quoted strings and integers",
        "startup configuration, not a live-reload API",
        "once per settings instance",
        "Already-resolved groups retain",
        "raw tags forward",
    ]:
        assert contract in settings
    view = (REFERENCE / "object_detail_view.md").read_text()
    quick = view.split("## Quick Reference", 1)[1].split("## Minimal Pattern", 1)[0]
    for base in [
        "DetailViewPermissionRequired",
        "GuardianDetailViewPermissionRequired",
        "PolymorphicDetailViewPermissionRequired",
    ]:
        assert base in quick
    assert quick.count("Complete view: subclass directly") == 2
    for page in [view, (REFERENCE / "object_detail_configuration.md").read_text()]:
        assert "| `choices_display`" in page
        assert "| `detail`" in page
        assert "object_detail_settings.md#help-text-precedence" in page
    compose = view.split("## Compose Pattern (Guardian / Polymorphic)", 1)[1]
    warning = compose.split("<!-- object-detail-value-recipe: complete -->", 1)[0]
    assert "already include" in warning and "fails at Python class creation" in warning


def test_object_detail_value_docs_restore_project_help(settings):
    namespace = {}
    exec(recipe("docs/migrating-1.0.md", "restore-project-help"), namespace)
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = namespace["CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT"]
    assert resolve_property(Info(text="Body"), x("text")).detail == "The info body text"


def test_object_detail_value_docs_restore_view_help(monkeypatch, settings):
    from tests.test1.app.models import Book

    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = False
    monkeypatch.setattr(viewset_module, "_REGISTRY", OrderedDict())
    monkeypatch.setattr(check_module, "_VOCAB_CACHE", {})
    namespace = {"__name__": __name__, "cv_book": viewset_module.ViewSet(model=Book, name="migration_book")}
    exec(recipe("docs/migrating-1.0.md", "restore-view-help"), namespace)
    cls = namespace["BookDetailView"]
    assert cls.__bases__ == (ObjectDetailViewPermissionRequired,)
    assert cls.cv_object_detail_show_help_text is True
    assert resolve_property(Info(text="Body"), x("text"), view=cls()).detail == "The info body text"
    assert resolve_property(Info(text="Body"), x("text", detail=False), view=cls()).detail is None


def test_object_detail_value_docs_restore_raw_choice():
    namespace = {}
    exec(recipe("docs/migrating-1.0.md", "restore-raw-choice"), namespace)
    prop = resolve_property(ChoiceValue(process="natural"), namespace["process_property"])
    assert prop.value == "natural"
    assert prop.choice_label is None
    assert render(prop).strip() == "natural"


def test_object_detail_value_docs_paired_migration():
    changelog = (ROOT / "CHANGELOG.md").read_text().split("### Breaking", 1)[1].split("### ", 1)[0]
    migration = (ROOT / "docs/migrating-1.0.md").read_text().split("## Object-detail values and help", 1)[1]
    migration = migration.split("\n## ", 1)[0]
    for text in [changelog, migration]:
        for contract in ["choices_display=False", "display_value", "char/text/default", "composition"]:
            assert contract in text
        assert "CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT" in text
        assert "cv_object_detail_show_help_text" in text
    assert "docs/migrating-1.0.md#object-detail-values-and-help" in changelog
    assert "reference/object_detail_configuration.md#copied-text-value-template" in migration
    assert "reference/object_detail_badges.md#native-semantic-badge-template" in migration
