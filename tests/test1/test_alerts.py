"""#250: one alert frame, fed by alert_data(), renders every alert in the package."""

import os
import re
from pathlib import Path

import pytest
from django.template import Context, Template
from django.test import override_settings
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import _trans
from lxml import html as lxml_html

from crud_views.lib.messages import alert_data
from tests.test1.test_form_frame import _norm, _theme_templates
from tests.test1.test_label_mode_docs import _section

ROOT = Path(__file__).resolve().parents[2]
ALERT_GOLDEN_DIR = Path(__file__).parent / "golden" / "alerts"
THEME_MD = ROOT / "docs" / "reference" / "theme.md"
CORE_TEMPLATES = ROOT / "src" / "crud_views" / "templates"
TEMPLATE_FENCE = re.compile(r"^```(?:django|html)\n(.*?)^```", re.MULTILINE | re.DOTALL)
BOOTSTRAP_DATA_ALLOWED = frozenset(
    {
        "crud_views/tags/actions_menu.html",
        "crud_views/tags/actions_menu_toggle.html",
        "crud_views/snippets/language_selector.html",
    }
)


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
    assert "data-cv-alert-dismiss" not in html
    assert lxml_html.fromstring(html).xpath("//button") == []


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


def test_dismissible_alert_golden():
    """ALRT-01 / D-07: the exact rendered bytes of a stock dismissible alert.

    Byte convention: the golden holds ``markup.encode("utf-8")`` of the real ``cv_alert`` render under the English
    locale, compared with ``read_bytes()``. There is no whitespace normalization and no appended trailing newline, so
    any byte of drift in the shared frame fails here. Regenerate ONLY when a change to the stock markup is intended:
    CV_UPDATE_GOLDEN=1 pytest tests/test1/test_alerts.py::test_dismissible_alert_golden
    """
    with translation.override("en"):
        markup = _render('{% cv_alert "success" heading="Saved:" text="The record was saved." dismissible=True %}')
    data = markup.encode("utf-8")
    path = ALERT_GOLDEN_DIR / "dismissible.html"
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    assert data == path.read_bytes()


def _dismissible_frame(markup):
    """The parsed alert frame and its single close control."""
    (frame,) = lxml_html.fragment_fromstring(markup, create_parent="root").xpath('//*[@role="alert"]')
    (control,) = frame.xpath(".//button")
    return frame, control


def test_dismissible_alert_preserves_frame_contract():
    """ALRT-02 / D-01: only the dismiss hook changed; the frame keeps its role, literal classes and close button."""
    with translation.override("en"):
        frame, control = _dismissible_frame(_render('{% cv_alert "success" heading="H" text="t" dismissible=True %}'))
    assert frame.tag == "div"
    assert frame.get("class") == "alert alert-success alert-dismissible fade show"
    assert control.get("type") == "button"
    assert control.get("class") == "btn-close"
    assert "data-cv-alert-dismiss" in control.attrib
    assert control.get("data-cv-alert-dismiss") == ""
    assert "data-bs-dismiss" not in control.attrib
    assert control.get("aria-label") == "Close"


def test_dismissible_alert_close_label_is_translated(monkeypatch):
    """The close control's accessible name goes through Django's active translation, not a hard-coded string."""
    sentinel = "zz-close-sentinel"
    original = _trans.gettext  # resolves (and caches) the real gettext before it is patched

    def gettext(message):
        return sentinel if message == "Close" else original(message)

    with monkeypatch.context() as patch, translation.override("en"):
        patch.setattr(_trans, "gettext", gettext)
        _frame, control = _dismissible_frame(_render('{% cv_alert "info" text="t" dismissible=True %}'))
    assert control.get("aria-label") == sentinel
    assert _trans.gettext is original


def test_dismissible_alert_escapes_heading_text_and_extra_tags():
    """The dismissible branch keeps alert_data's escaping: hostile values stay text, safe strings stay markup."""
    html = _render(
        '{% cv_alert "error" heading=h text=t extra_tags=x dismissible=True %}'
        '{% cv_alert "info" text=safe dismissible=True %}',
        {
            "h": "<script>h</script>",
            "t": "<img src=x onerror=t>",
            "x": '"><script>x</script>',
            "safe": mark_safe("<b>ok</b>"),
        },
    )
    root = lxml_html.fragment_fromstring(html, create_parent="root")
    assert root.xpath("//script") == []
    assert root.xpath("//img") == []
    assert root.xpath("//b/text()") == ["ok"]
    hostile, safe = root.xpath('//*[@role="alert"]')
    assert hostile.get("class") == 'alert alert-danger alert-dismissible fade show "><script>x</script>'
    assert "<script>h</script>" in hostile.text_content()
    for frame in (hostile, safe):
        (control,) = frame.xpath(".//button[@data-cv-alert-dismiss]")
        assert control.get("aria-label")


def test_cv_alert_separates_heading_and_text():
    html = _render('{% cv_alert "warning" heading="Note:" text="Something" %}')
    assert "<strong>Note:</strong> Something" in html


def _documented_alert_frame() -> str:
    """The single django/html fence below "### Custom alert frame" in theme.md's "## Alerts" section."""
    section = _section(_section(THEME_MD.read_text(), "## Alerts"), "### Custom alert frame")
    bodies = TEMPLATE_FENCE.findall(section)
    assert len(bodies) == 1, f"'### Custom alert frame' must hold exactly one django/html fence, found {len(bodies)}"
    return bodies[0]


def test_documented_alert_frame_override(monkeypatch):
    """ALRT-04 / D-02: the theme.md frame recipe renders as a real override and keeps every hook dismissal relies on."""
    recipe = _documented_alert_frame()
    sentinel = "zz-close-sentinel"
    original = _trans.gettext

    def gettext(message):
        return sentinel if message == "Close" else original(message)

    hostile = {
        "h": "<script>h</script>",
        "t": "<img src=x onerror=t>",
        "x": '"><script>x</script>',
        "items": ["<b>a</b>", mark_safe("<em>b</em>")],
    }
    source = (
        '{% cv_alert "error" heading=h text=t extra_tags=x dismissible=True %}'
        '{% cv_alert "warning" items=items %}'
        '{% cv_alert "info" text="plain" %}'
    )
    classes = {"alert:error": "notice-danger"}
    with (
        monkeypatch.context() as patch,
        translation.override("en"),
        override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes),
        _theme_templates({"crud_views/tags/alert.html": recipe}),
    ):
        patch.setattr(_trans, "gettext", gettext)
        html = _render(source, hostile)

    root = lxml_html.fragment_fromstring(html, create_parent="root")
    error, warning, info = root.xpath('//*[@role="alert"]')

    # the documented classes replace the stock ones; the level colour still comes from the class table
    error_classes = error.get("class").split()
    assert error_classes[:3] == ["notice", "notice-danger", "notice-dismissible"]
    assert "alert-dismissible" not in error_classes
    assert error.get("class").endswith(' "><script>x</script>')
    assert warning.get("class").split() == ["notice", "alert", "alert-warning"]

    # dismissible: one accessible, translated, type=button control with only the core hook
    (control,) = error.xpath(".//button")
    assert control.get("type") == "button"
    assert control.get("class") == "notice-close"
    assert "data-cv-alert-dismiss" in control.attrib
    assert "data-bs-dismiss" not in control.attrib
    assert control.get("aria-label") == sentinel

    # non-dismissible alerts render no control
    assert warning.xpath(".//button") == []
    assert info.xpath(".//button") == []

    # escaping is preserved; the list and text bodies are included
    assert root.xpath("//script") == []
    assert root.xpath("//img") == []
    assert error.xpath(".//strong/text()") == ["<script>h</script>"]
    assert "<img src=x onerror=t>" in error.text_content()
    assert [li.text_content() for li in warning.xpath(".//li")] == ["<b>a</b>", "b"]
    assert warning.xpath(".//li/em/text()") == ["b"]
    assert "plain" in info.text_content()


def _assert_core_bootstrap_data_attributes(root: Path) -> None:
    """Bootstrap data attributes under a core template root are confined to the dropdown templates (D-09)."""
    matches = {path.relative_to(root).as_posix() for path in root.rglob("*.html") if "data-bs-" in path.read_text()}
    assert matches, f"no data-bs- attribute found under {root}"
    forbidden = sorted(matches - BOOTSTRAP_DATA_ALLOWED)
    assert not forbidden, f"Bootstrap data attributes outside the dropdown templates: {forbidden}"


def test_stock_bootstrap_data_attributes_are_dropdown_only():
    """ALRT-04: core crud_views templates keep data-bs-* only in the dropdowns named in theme.md; the alert has none."""
    _assert_core_bootstrap_data_attributes(CORE_TEMPLATES)


def test_core_bootstrap_data_attribute_guard_rejects_forbidden_path(tmp_path):
    """The guard accepts an allowed tree and names a forbidden template once one appears."""
    with pytest.raises(AssertionError, match="no data-bs- attribute"):
        _assert_core_bootstrap_data_attributes(tmp_path)

    toggle = tmp_path / "crud_views" / "tags" / "actions_menu_toggle.html"
    toggle.parent.mkdir(parents=True)
    toggle.write_text('<button data-bs-toggle="dropdown"></button>')
    _assert_core_bootstrap_data_attributes(tmp_path)

    (tmp_path / "crud_views" / "tags" / "alert.html").write_text('<button data-bs-dismiss="alert"></button>')
    with pytest.raises(AssertionError, match=re.escape("crud_views/tags/alert.html")):
        _assert_core_bootstrap_data_attributes(tmp_path)
