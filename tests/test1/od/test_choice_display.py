from copy import deepcopy
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.test import override_settings
from django.test.utils import isolate_apps
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy, override
from lxml import html as html_parser

from crud_views_object_detail.lib import resolvers
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.lib.config import BadgeConfig, parse_property_display, x
from crud_views_object_detail.lib.resolvers import ResolvedProperty, _resolve_value, resolve_all, resolve_property
from crud_views_object_detail.templatetags import crud_views_object_detail as tags
from tests.test1.od_app.models import ChoiceContainer, ChoiceValue


def render_value(prop):
    return Template("{% load crud_views_object_detail %}{% render_property_value prop %}").render(
        Context({"prop": prop})
    )


def template_settings(templates):
    engines = deepcopy(settings.TEMPLATES)
    engines[0]["APP_DIRS"] = False
    engines[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", templates),
        "django.template.loaders.app_directories.Loader",
    ]
    return engines


@isolate_apps()
def test_choice_display_tracer():
    class Sample(models.Model):
        process = models.CharField(
            max_length=20, verbose_name="processing method", choices=[("natural", "Naturally processed")]
        )

        class Meta:
            app_label = "od_app"

    obj = Sample(process="natural")
    raw = [{"title": "Sample", "properties": ["process"]}]
    groups = resolve_all(obj, parse_property_display(raw))
    prop = groups[0].properties[0]
    html = Template("{% load crud_views_object_detail %}{% render_object_detail obj property_display=raw %}").render(
        Context({"obj": obj, "raw": raw})
    )
    assert "Naturally processed" in html
    assert "Processing method" in html
    assert prop.value == "natural"
    assert prop.choice_label == "Naturally processed"
    assert prop.type == "char"
    prop.template = "explicit.html"
    with override_settings(TEMPLATES=template_settings({"explicit.html": "{{ value }}|{{ display_value }}"})):
        assert render_value(prop) == "natural|Naturally processed"
    raw_config = [{"title": "Sample", "properties": [x("process", choices_display=False, title="Process code")]}]
    raw_prop = resolve_all(obj, parse_property_display(raw_config))[0].properties[0]
    assert raw_prop.label == "Process code"
    assert raw_prop.value == "natural"
    assert raw_prop.choice_label is None
    assert render_value(raw_prop).strip() == "natural"
    assert render_value(ResolvedProperty("manual", "Manual", "unchanged", type="char")).strip() == "unchanged"


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("field", ["process", "rank", "flag"])
@pytest.mark.parametrize("path_kind", ["nullable", "first_reverse", "deep_reverse"])
@pytest.mark.django_db
def test_choice_display_missing_owner(enabled, field, path_kind, monkeypatch):
    display = Mock(side_effect=AssertionError("missing owner must not call display"))
    monkeypatch.setattr(ChoiceValue, f"get_{field}_display", display)
    if path_kind == "nullable":
        obj, path, raw = ChoiceContainer(foreign=None), f"foreign__{field}", None
    elif path_kind == "first_reverse":
        obj, path, raw = ChoiceValue.objects.create(), f"successor__{field}", None
    else:
        obj = ChoiceContainer(foreign=ChoiceValue.objects.create())
        path, raw = f"foreign__successor__{field}", []
    prop = resolve_property(obj, x(path, choices_display=enabled))
    assert prop.value == raw
    assert prop.choice_label == ""
    assert render_value(prop).strip() == ""
    direct = _resolve_value(obj, path.split("__"), False)
    if path_kind == "deep_reverse":
        assert direct == []
    display.assert_not_called()


@pytest.mark.parametrize(
    "field,value,label",
    [
        ("process", "washed", "Gewaschen — 水"),
        ("process", "", "Blank declared"),
        ("process", "unknown", "unknown"),
        ("rank", 1, "First"),
        ("rank", 9999, 9999),
        ("flag", False, "Disabled"),
        ("flag", True, "Enabled"),
        ("rank", True, "First"),
    ],
)
def test_choice_display_scalar_semantics(field, value, label):
    obj = ChoiceValue(**{field: value})
    prop = resolve_property(obj, x(field))
    assert prop.value == value
    assert prop.choice_label == label
    assert render_value(prop).strip() == str(label)
    assert resolve_property(obj, x(field, choices_display=False)).choice_label is None


@isolate_apps()
def test_choice_display_grouped_and_override():
    class Grouped(models.Model):
        code = models.CharField(max_length=2, choices=[("Group", [("a", "Alpha"), ("b", "Beta")])])

        class Meta:
            app_label = "od_app"

    obj = Grouped(code="b")
    assert resolve_property(obj, x("code")).choice_label == "Beta"
    obj.get_code_display = Mock(return_value="Overridden")
    assert resolve_property(obj, x("code")).choice_label == "Overridden"
    obj.get_code_display.assert_called_once_with()
    obj.get_code_display = Mock(side_effect=RuntimeError("application display error"))
    with pytest.raises(RuntimeError, match="application display error"):
        resolve_property(obj, x("code"))


@pytest.mark.parametrize("relation", ["foreign", "single"])
@pytest.mark.django_db
def test_choice_display_terminal_owner_and_relation_field(relation, django_assert_num_queries):
    target = ChoiceValue.objects.create()
    obj = ChoiceContainer(**{relation: target})
    target.get_process_display = Mock(return_value="Terminal owner")
    with django_assert_num_queries(0):
        prop = resolve_property(obj, x(f"{relation}__process"))
    assert prop.value == "natural"
    assert prop.choice_label == "Terminal owner"
    target.get_process_display.assert_called_once_with()
    # Declared choices on a terminal relation must never replace its model identity.
    prop = resolve_property(obj, x(relation, link="info-detail"))
    assert prop.value is target
    assert prop.choice_label is None
    assert prop.type == "foreignkey"
    assert prop.link_url == f"/info/{target.pk}/"
    assert render_value(prop).strip() == str(target)
    row = Template("{% load crud_views_object_detail %}{% render_property prop %}").render(Context({"prop": prop}))
    node = html_parser.fromstring(row).xpath(".//a")[0]
    assert node.get("href") == prop.link_url
    assert node.text == str(target)


@pytest.mark.parametrize("relation", ["foreign", "single"])
@pytest.mark.parametrize("field", ["process", "plain"])
@pytest.mark.django_db
def test_choice_display_relation_query_baseline(relation, field, django_assert_num_queries):
    target = ChoiceValue.objects.create()
    saved = ChoiceContainer.objects.create(**{relation: target})
    uncached = ChoiceContainer.objects.get(pk=saved.pk)
    with django_assert_num_queries(1):
        prop = resolve_property(uncached, x(f"{relation}__{field}"))
    loaded = ChoiceContainer.objects.select_related(relation).get(pk=saved.pk)
    with django_assert_num_queries(0):
        again = resolve_property(loaded, x(f"{relation}__{field}"))
    assert again.value == prop.value == ("natural" if field == "process" else "ordinary")
    assert prop.choice_label == ("Naturally processed" if field == "process" else None)


@pytest.mark.parametrize("size", [0, 1, 3])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.django_db
def test_choice_display_collection_shape_and_queries(size, reverse, django_assert_num_queries):
    root = ChoiceContainer.objects.create()
    values = [ChoiceValue.objects.create(process=code) for code in ["washed", "natural", "washed"][:size]]
    if reverse:
        anchor = ChoiceValue.objects.create()
        for value in values:
            ChoiceContainer.objects.create(foreign=anchor, single=value)
        obj = ChoiceValue.objects.prefetch_related("containers__single").get(pk=anchor.pk)
        path = "containers__single__process"
    else:
        root.values.set(values)
        obj = ChoiceContainer.objects.prefetch_related("values").get(pk=root.pk)
        path = "values__process"
    with django_assert_num_queries(0):
        prop = resolve_property(obj, x(path))
    assert prop.is_many is True
    assert prop.value == [value.process for value in values]
    assert prop.choice_label is None


def test_choice_display_computed_and_view_fallback(monkeypatch):
    obj = ChoiceValue(process="natural")
    computed = Mock(spec=lambda: None, return_value=SimpleNamespace(process="computed"))
    monkeypatch.setattr(ChoiceValue, "computed", computed, raising=False)
    prop = resolve_property(obj, x("computed__process"))
    assert prop.value == "computed"
    assert prop.choice_label is None
    computed.assert_called_once_with()
    getter = Mock(return_value="property value")
    monkeypatch.setattr(ChoiceValue, "computed_property", property(getter), raising=False)
    assert resolve_property(obj, x("computed_property")).value == "property value"
    getter.assert_called_once_with(obj)
    callback = Mock(return_value=["fallback"])
    assert resolve_property(obj, x("missing"), view=SimpleNamespace(missing=callback)).value == ["fallback"]
    callback.assert_called_once_with(obj)
    # A scalar hop cannot keep treating later segment names as fields on the original model.
    prop = resolve_property(obj, x("plain__process"))
    assert prop.value == []
    assert prop.choice_label is None


@pytest.mark.django_db
def test_choice_display_missing_first_relation_keeps_view_fallback():
    obj = ChoiceValue.objects.create()
    callback = Mock(return_value="application fallback")
    prop = resolve_property(obj, x("successor__process"), view=SimpleNamespace(successor__process=callback))
    assert prop.value == "application fallback"
    assert prop.choice_label is None
    assert render_value(prop).strip() == "application fallback"
    callback.assert_called_once_with(obj)


@pytest.mark.django_db
def test_choice_display_present_reverse_owner_and_dictionary_opt_out(django_assert_num_queries):
    previous = ChoiceValue.objects.create()
    successor = ChoiceValue.objects.create(previous=previous, process="washed")
    loaded = ChoiceValue.objects.select_related("successor").get(pk=previous.pk)
    with django_assert_num_queries(0):
        groups = resolve_all(
            loaded,
            parse_property_display(
                [
                    {
                        "title": "Choices",
                        "properties": [
                            "successor__process",
                            {
                                "path": "successor__process",
                                "title": "Code",
                                "choices_display": False,
                            },
                        ],
                    }
                ]
            ),
        )
    human, raw = groups[0].properties
    assert human.value == raw.value == successor.process
    assert human.choice_label == "Gewaschen — 水"
    assert raw.choice_label is None
    assert raw.label == "Code"
    assert render_value(raw).strip() == "washed"


@pytest.mark.django_db
def test_choice_display_campaign_request(campaign_new, client_user_campaign_view):
    response = client_user_campaign_view.get(f"/campaign/{campaign_new.pk}/detail/")
    assert response.status_code == 200
    prop = next(p for g in response.context["object_detail_groups"] for p in g.properties if p.path == "state")
    assert prop.value == "new"
    assert prop.choice_label == "New"
    document = html_parser.fromstring(response.content)
    row = document.xpath("//*[normalize-space(text())='State']/parent::*")
    assert any("State" in r.text_content() and "New" in r.text_content() for r in row)


@pytest.mark.parametrize(
    "mapped,expected", [(None, "Naturally processed"), ("", "Naturally processed"), ("Explicit", "Explicit")]
)
def test_choice_display_badge_raw_inputs_and_label_fallback(mapped, expected, monkeypatch):
    callback = Mock(return_value="success")
    link = Mock(wraps=resolvers._resolve_link_url)
    monkeypatch.setattr(resolvers, "_resolve_link_url", link)
    config = x("process", badge=BadgeConfig(color_fn=callback, label_map={"natural": mapped}), link="info-detail")
    prop = resolve_property(ChoiceValue(), config)
    node = html_parser.fromstring(render_value(prop))
    assert node.tag == "span"
    assert node.get("class") == "badge text-bg-success"
    assert node.text == expected
    assert prop.value == "natural"
    callback.assert_called_once_with("natural")
    link.assert_called_once_with("natural", config.link, False)


@pytest.mark.parametrize("enabled", [True, False])
def test_choice_display_badge_precedes_explicit_template(enabled):
    obj = ChoiceValue()
    prop = resolve_property(
        obj,
        x(
            "process",
            choices_display=enabled,
            template="explicit.html",
            badge=BadgeConfig(color_map={"natural": "info"}, label_map={"natural": "Explicit"}),
        ),
    )
    with override_settings(TEMPLATES=template_settings({"explicit.html": "CUSTOM {{ value }}|{{ display_value }}"})):
        assert html_parser.fromstring(render_value(prop)).text == "Explicit"
        assert prop.badge_css == "text-bg-info"
        unresolved = resolve_property(
            obj,
            x(
                "process",
                choices_display=enabled,
                template="explicit.html",
                badge=BadgeConfig(color_map={"other": "info"}, label_map={"natural": "Unused"}),
            ),
        )
        assert render_value(unresolved) == "CUSTOM natural|" + ("Naturally processed" if enabled else "natural")
    unresolved.template = None
    assert render_value(unresolved).strip() == ("Naturally processed" if enabled else "natural")


@pytest.mark.parametrize(
    "field,value,expected", [("rank", 1, "First"), ("rank", 10000, "10000"), ("flag", False, "Disabled")]
)
@pytest.mark.parametrize("explicit_type", [None, "boolean", "float"])
def test_choice_display_uses_text_despite_inferred_or_explicit_type(field, value, expected, explicit_type):
    prop = resolve_property(ChoiceValue(**{field: value}), x(field, type=explicit_type))
    assert prop.value == value
    assert render_value(prop).strip() == expected
    assert "<i" not in render_value(prop)


@isolate_apps()
def test_choice_display_ordinary_boolean_and_date_keep_formatting():
    class Ordinary(models.Model):
        active = models.BooleanField(default=False)
        day = models.DateField()

        class Meta:
            app_label = "od_app"

    obj = Ordinary(active=True, day=date(2026, 11, 6))
    boolean = resolve_property(obj, x("active"))
    day = resolve_property(obj, x("day"))
    assert boolean.choice_label is day.choice_label is None
    assert boolean.value is True
    assert 'class="' in render_value(boolean) and "text-success" in render_value(boolean)
    assert day.value == date(2026, 11, 6)
    assert render_value(day).strip() == date_format(obj.day, "DATE_FORMAT")


@pytest.mark.parametrize("declared", [True, False])
@isolate_apps()
def test_choice_display_nullable_choice(declared):
    class Nullable(models.Model):
        code = models.CharField(
            max_length=10, null=True, choices=[("a", "Alpha")] + ([(None, "Not assigned")] if declared else [])
        )

        class Meta:
            app_label = "od_app"

    prop = resolve_property(Nullable(code=None), x("code"))
    assert prop.value is None
    assert prop.choice_label == ("Not assigned" if declared else None)
    if declared:
        assert render_value(prop).strip() == "Not assigned"
    else:
        assert render_value(prop).strip() == '<span class="text-body-tertiary">&mdash;</span>'


@pytest.mark.parametrize("leaf", ["char", "default", None])
def test_choice_display_custom_pack_fallback_context(leaf, monkeypatch):
    templates = (
        {}
        if leaf is None
        else {
            f"crud_views_object_detail/types/choice-test/{leaf}.html": (
                "{{ value }}|{{ display_value }}|{{ prop.choice_label }}"
            )
        }
    )
    with override_settings(
        CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES="choice-test", TEMPLATES=template_settings(templates)
    ):
        monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
        prop = resolve_property(ChoiceValue(rank=1), x("rank"))
        assert render_value(prop).strip() == ("First" if leaf is None else "1|First|First")


@pytest.mark.parametrize("badge", [False, True])
@isolate_apps()
def test_choice_display_escapes_hostile_labels(badge):
    label = '<img src=x onerror="bad()"> & café'

    class Hostile(models.Model):
        code = models.CharField(max_length=10, choices=[("raw", label)])

        class Meta:
            app_label = "od_app"

    prop = resolve_property(Hostile(code="raw"), x("code", badge="info" if badge else None))
    rendered = render_value(prop)
    assert "<img" not in rendered
    assert "&lt;img" in rendered
    assert "&amp; café" in rendered
    if badge:
        assert html_parser.fromstring(rendered).text == label


@isolate_apps()
def test_choice_display_lazy_translation_at_resolution():
    class Translated(models.Model):
        code = models.CharField(max_length=10, choices=[("yes", gettext_lazy("Yes"))])

        class Meta:
            app_label = "od_app"

    obj = Translated(code="yes")
    for language, expected in [("en", "Yes"), ("de", "Ja")]:
        with override(language):
            prop = resolve_property(obj, x("code"))
            assert prop.value == "yes"
            assert prop.choice_label == expected
            assert render_value(prop).strip() == expected


@pytest.mark.parametrize("enabled", [True, False])
def test_choice_display_empty_badge_and_missing_label_key(enabled):
    prop = resolve_property(ChoiceValue(process=""), x("process", choices_display=enabled, badge="info"))
    assert prop.value == ""
    assert render_value(prop).strip() == (
        '<span class="badge text-bg-info">' + ("Blank declared" if enabled else "") + "</span>"
    )
    missing_key = resolve_property(
        ChoiceValue(), x("process", badge=BadgeConfig(color="info", label_map={"other": "Unused"}))
    )
    assert missing_key.badge_label is None
    assert html_parser.fromstring(render_value(missing_key)).text == "Naturally processed"


def test_choice_display_custom_badge_context_keeps_raw_value():
    prop = resolve_property(ChoiceValue(), x("process", badge="info"))
    templates = {
        "crud_views_object_detail/types/default/badge.html": "{{ value }}|{{ display_value }}|{{ prop.choice_label }}"
    }
    with override_settings(TEMPLATES=template_settings(templates)):
        assert render_value(prop) == "natural|Naturally processed|Naturally processed"
