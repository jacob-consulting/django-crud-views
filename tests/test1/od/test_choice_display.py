from django.db import models
from django.template import Context, Template
from django.test.utils import isolate_apps

from crud_views_object_detail.lib.config import parse_property_display, x
from crud_views_object_detail.lib.resolvers import ResolvedProperty, resolve_all


def render_value(prop):
    return Template("{% load crud_views_object_detail %}{% render_property_value prop %}").render(Context({"prop": prop}))


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
    html = Template(
        "{% load crud_views_object_detail %}{% render_object_detail obj property_display=raw %}"
    ).render(Context({"obj": obj, "raw": raw}))
    assert "Naturally processed" in html
    assert "Processing method" in html
    assert prop.value == "natural"
    assert prop.choice_label == "Naturally processed"
    assert prop.type == "char"
    raw_config = [{"title": "Sample", "properties": [x("process", choices_display=False, title="Process code")]}]
    raw_prop = resolve_all(obj, parse_property_display(raw_config))[0].properties[0]
    assert raw_prop.label == "Process code"
    assert raw_prop.value == "natural"
    assert raw_prop.choice_label is None
    assert render_value(raw_prop).strip() == "natural"
    assert render_value(ResolvedProperty("manual", "Manual", "unchanged", type="char")).strip() == "unchanged"
