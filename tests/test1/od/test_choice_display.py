from copy import deepcopy

from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.test import override_settings
from django.test.utils import isolate_apps

from crud_views_object_detail.lib.config import parse_property_display, x
from crud_views_object_detail.lib.resolvers import ResolvedProperty, resolve_all


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
