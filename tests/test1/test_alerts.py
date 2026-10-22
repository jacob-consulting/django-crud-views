"""#250: one alert frame, fed by alert_data(), renders every alert in the package."""

import pytest
from django.utils.safestring import mark_safe

from crud_views.lib.messages import alert_data


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
