"""#250: one alert frame, fed by alert_data(), renders every alert in the package."""

from pathlib import Path

import pytest
from django.template import Context, Template
from django.test import override_settings
from django.utils.safestring import mark_safe

from crud_views.lib.messages import alert_data
from tests.test1.test_form_frame import _norm, _theme_templates


@pytest.mark.parametrize("level", ["error", "warning", "success", "info", "debug"])
def test_alert_data_keeps_a_known_level(level):
    data = alert_data(level, text="x")
    assert data["level"] == level
    assert data["icon_name"] == f"message-{level}"


@pytest.mark.parametrize("level", ["danger", "ERROR", "", None, 40])
def test_alert_data_unknown_level_is_info(level):
    data = alert_data(level)
    assert data["level"] == "info"
    assert data["icon_name"] == "message-info"


def test_alert_data_picks_the_text_body_without_items():
    assert alert_data("info", text="x")["body_template"] == "crud_views/snippets/alert/text.html"
    assert alert_data("info", items=[])["body_template"] == "crud_views/snippets/alert/text.html"


def test_alert_data_picks_the_list_body_with_items():
    assert alert_data("error", items=["a"])["body_template"] == "crud_views/snippets/alert/list.html"


def test_alert_data_keeps_an_explicit_body_template():
    assert alert_data("warning", items=["a"], body_template="x.html")["body_template"] == "x.html"


def test_alert_data_escapes_heading_and_text():
    data = alert_data("info", heading="<b>h</b>", text="<i>t</i>")
    assert data["heading"] == "&lt;b&gt;h&lt;/b&gt;"
    assert data["text"] == "&lt;i&gt;t&lt;/i&gt;"
    assert alert_data("info", text=mark_safe("<i>t</i>"))["text"] == "<i>t</i>"


def test_alert_data_escapes_items():
    class Hostile:
        def __str__(self):
            return "<script>x</script>"

    items = alert_data("error", items=[Hostile(), mark_safe("<b>ok</b>")])["items"]
    assert items == ["&lt;script&gt;x&lt;/script&gt;", "<b>ok</b>"]


def test_alert_data_blanks_falsy_heading_and_text():
    data = alert_data("info", heading=None, text=None)
    assert data["heading"] == ""
    assert data["text"] == ""


def test_alert_data_escapes_extra_tags_and_defaults():
    data = alert_data("info", extra_tags='">')
    assert data["extra_tags"] == "&quot;&gt;"
    assert data["dismissible"] is False
    assert data["items"] == []


def _render(source, context=None):
    return Template("{% load crud_views %}" + source).render(Context(context or {}))


def test_cv_alert_renders_the_frame_with_a_list():
    html = _norm(_render('{% cv_alert "error" heading="H" items=errs %}', {"errs": ["a", "b"]}))
    assert html == (
        '<div class="alert alert-danger" role="alert"><i class="fa-solid fa-circle-exclamation me-2" '
        'aria-hidden="true"></i><strong>H</strong><ul class="mb-0 mt-2"><li>a</li><li>b</li></ul></div>'
    )


def test_cv_alert_body_template_sees_the_callers_context():
    with _theme_templates({"body.html": "[{{ outer }}]"}):
        html = _render('{% cv_alert "info" body_template="body.html" %}', {"outer": "OUTER"})
    assert "[OUTER]" in html


def test_cv_alert_restores_the_callers_alert():
    html = _render('{% for alert in xs %}{% cv_alert "info" text="t" %}[{{ alert }}]{% endfor %}', {"xs": ["mine"]})
    assert "[mine]" in html


def test_cv_alert_escapes_with_autoescape_off():
    html = _render(
        '{% autoescape off %}{% cv_alert "error" heading=h items=i %}{% cv_alert "info" text=t %}{% endautoescape %}',
        {"h": "<h>", "i": ["<i>"], "t": "<t>"},
    )
    assert "<h>" not in html
    assert "<i>" not in html
    assert "<t>" not in html
    assert "&lt;h&gt;" in html


def test_cv_alert_is_not_dismissible_by_default():
    html = _render('{% cv_alert "warning" text="t" %}')
    assert "btn-close" not in html
    assert "alert-dismissible" not in html


def test_frame_is_overridable_on_its_own():
    with _theme_templates({"crud_views/tags/alert.html": "<x-theme>{{ alert.level }}</x-theme>"}):
        html = _norm(_render('{% cv_alert "error" items=errs %}', {"errs": ["a"]}))
    assert html == "<x-theme>error</x-theme>"


def test_list_body_is_overridable_on_its_own():
    with _theme_templates({"crud_views/snippets/alert/list.html": "<x-theme>{{ alert.items|join:',' }}</x-theme>"}):
        html = _norm(_render('{% cv_alert "error" items=errs %}', {"errs": ["a", "b"]}))
    assert html.startswith('<div class="alert alert-danger" role="alert">')
    assert "<x-theme>a,b</x-theme>" in html
    assert "<ul" not in html


def test_alert_colours_follow_the_class_table():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"alert:error": "notification is-danger"}):
        html = _render('{% cv_alert "error" text="t" %}')
    assert 'class="notification is-danger"' in html


def test_only_the_alert_templates_write_alert_markup():
    """#250: every alert in all five apps goes through tags/alert.html and its body snippets."""
    src = Path(__file__).resolve().parents[2] / "src"
    files = list(src.glob("crud_views*/templates/**/*.html"))
    assert files
    offenders = []
    for path in files:
        name = path.as_posix().split("/templates/", 1)[1]
        if name == "crud_views/tags/alert.html" or name.startswith("crud_views/snippets/alert/"):
            continue
        if 'class="alert' in path.read_text():
            offenders.append(name)
    assert offenders == []


def test_cv_alert_separates_heading_and_text():
    html = _render('{% cv_alert "warning" heading="Note:" text="Something" %}')
    assert "<strong>Note:</strong> Something" in html
