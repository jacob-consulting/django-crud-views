import pytest
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import override_settings
from django.utils import timezone
from lxml import html as html_parser

from crud_views_object_detail.lib.config import PropertyGroupConfig, x
from crud_views_object_detail.lib.resolvers import (
    ResolvedProperty,
    resolve_all,
)
from tests.test1.od_app.models import Info, Report

EMPTY_TEXT_MARKER = '<span class="text-body-tertiary">&mdash;</span>'


def render_value(prop):
    return Template("{% load crud_views_object_detail %}{% render_property_value prop %}").render(
        Context({"prop": prop})
    )


@pytest.mark.parametrize("value_type", ["char", "text", "default", "unknown_type"])
@pytest.mark.parametrize(
    "value,expected",
    [
        (None, EMPTY_TEXT_MARKER),
        ("", EMPTY_TEXT_MARKER),
        (0, "0"),
        (False, "False"),
        ("   ", "   "),
        ("Größe — 水", "Größe — 水"),
        ('<script>"x"</script>', "&lt;script&gt;&quot;x&quot;&lt;/script&gt;"),
        ([], "[]"),
    ],
)
def test_empty_text_value_preserves_distinctions(value_type, value, expected):
    prop = ResolvedProperty(path="value", label="Value", value=value, type=value_type)
    assert render_value(prop) == expected + ("\n" if value_type == "char" else "")


@pytest.mark.parametrize("value_type", ["char", "text", "default"])
@pytest.mark.parametrize("display_value", [None, "", "Declared blank label"])
def test_empty_text_leaf_uses_final_display_value(value_type, display_value):
    html = render_to_string(
        f"crud_views_object_detail/types/default/{value_type}.html",
        {"value": "raw-code", "display_value": display_value, "od_settings": {"property_text_newline": "linebreaksbr"}},
    )
    expected = EMPTY_TEXT_MARKER if display_value is None or display_value == "" else display_value
    assert html == expected + ("\n" if value_type == "char" else "")


@pytest.mark.parametrize("value_type", ["char", "text", "default"])
@pytest.mark.parametrize("value", [None, ""])
def test_empty_text_keeps_label_and_explicit_detail(value_type, value):
    prop = ResolvedProperty("empty", "Empty label", value, detail="Keep this description", type=value_type)
    html = Template("{% load crud_views_object_detail %}{% render_property prop %}").render(Context({"prop": prop}))
    document = html_parser.fromstring(html)
    assert document.xpath("string(.//div[contains(@class, 'col-sm-4')])") == "Empty label"
    assert document.xpath("string(.//small)") == "Keep this description"
    assert document.xpath("string(.//span[@class='text-body-tertiary'])") == "—"
    assert EMPTY_TEXT_MARKER in html


@pytest.mark.parametrize(
    "newline,expected",
    [
        ("linebreaksbr", "A&lt;b&gt;<br>Größe — 水<br><br>Last"),
        ("linebreaks", "<p>A&lt;b&gt;<br>Größe — 水</p>\n\n<p>Last</p>"),
    ],
)
def test_empty_text_preserves_newline_modes(newline, expected, settings):
    settings.CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE = newline
    prop = ResolvedProperty("body", "Body", "A<b>\nGröße — 水\n\nLast", type="text")
    assert render_value(prop) == expected
    prop.value = ""
    assert render_value(prop) == EMPTY_TEXT_MARKER


def test_empty_text_keeps_duplicate_properties_and_order():
    group = PropertyGroupConfig(
        title="Repeated values",
        properties=[x("text", title=title, detail="Description") for title in ["First", "Second", "Third"]],
    )
    obj = Info(text="")
    groups = resolve_all(obj, [group])
    html = Template("{% load crud_views_object_detail %}{% render_object_detail obj groups %}").render(
        Context({"obj": obj, "groups": groups})
    )
    document = html_parser.fromstring(html)
    labels = document.xpath("//div[contains(@class, 'col-sm-4')]/text()")
    assert labels == ["First", "Second", "Third"]
    assert len(document.xpath("//span[@class='text-body-tertiary']")) == 3
    assert document.xpath("//small/text()") == ["Description"] * 3


def test_empty_text_is_local_to_stock_text_leaves():
    custom = ResolvedProperty("custom", "Custom", "", type="char", template="test_custom_value.html")
    assert render_value(custom).strip() == '<span class="custom-rendered"></span>'
    custom.value = "stored"
    custom.choice_label = ""
    assert render_value(custom).strip() == '<span class="custom-rendered">stored</span>'
    badge = ResolvedProperty("badge", "Badge", "", badge_css="text-bg-success")
    assert render_value(badge).strip() == '<span class="badge text-bg-success"></span>'
    relation = ResolvedProperty("relation", "Relation", "", type="foreignkey")
    assert render_value(relation).strip() == ""
    collection = ResolvedProperty("collection", "Collection", [], type="manytomany", is_many=True)
    assert render_value(collection).strip() == EMPTY_TEXT_MARKER


@pytest.fixture
def now():
    return timezone.now()


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        first_name="Test",
        last_name="User",
        password="testpass",
    )


@pytest.fixture
def info(db, now):
    return Info.objects.create(
        text="Some text",
        is_public=True,
        create_dt=now,
        update_dt=now,
    )


@pytest.fixture
def report(db, info, user):
    return Report.objects.create(title="Test Report", info=info, owner=user)


@pytest.fixture
def groups(report):
    configs = [
        PropertyGroupConfig(
            title="Report",
            description="Report details",
            icon="file-text",
            properties=["title", "owner"],
        ),
        PropertyGroupConfig(
            title="Info",
            properties=[
                x("info__text", title="Body"),
                "info__is_public",
            ],
        ),
    ]
    return resolve_all(report, configs)


class TestRenderObjectDetail:
    def test_renders_all_groups(self, groups):
        tpl = Template("{% load crud_views_object_detail %}{% render_object_detail obj groups %}")
        ctx = Context({"obj": None, "groups": groups})
        html = tpl.render(ctx)
        assert "Report" in html
        assert "Info" in html

    def test_renders_property_values(self, groups):
        tpl = Template("{% load crud_views_object_detail %}{% render_object_detail obj groups %}")
        ctx = Context({"obj": None, "groups": groups})
        html = tpl.render(ctx)
        assert "Test Report" in html
        assert "testuser" in html


@pytest.mark.parametrize("project", [False, True])
@pytest.mark.parametrize("view_kind", ["absent", "core", "inherit", "enable", "disable"])
def test_raw_tag_help_policy(project, view_kind, settings):
    from crud_views.lib.views import DetailView
    from crud_views_object_detail.lib.mixins import ObjectDetailMixin

    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = project
    context = {"obj": Info(text="Body"), "raw": [{"title": "Info", "properties": ["text"]}]}
    expected = project
    if view_kind == "core":
        context["view"] = DetailView()
        assert not hasattr(context["view"], "cv_object_detail_show_help_text")
    elif view_kind != "absent":
        view = context["view"] = ObjectDetailMixin()
        if view_kind != "inherit":
            expected = view.cv_object_detail_show_help_text = view_kind == "enable"
        else:
            assert view.cv_object_detail_show_help_text is None
    html = Template("{% load crud_views_object_detail %}{% render_object_detail obj property_display=raw %}").render(
        Context(context)
    )
    assert ("The info body text" in html) is expected
    assert "Body" in html


@pytest.mark.parametrize("resolved_policy", [False, True])
def test_resolved_tag_keeps_help_under_opposite_policy(resolved_policy, settings):
    from crud_views_object_detail.lib.mixins import ObjectDetailMixin

    obj = Info(text="Body")
    view = ObjectDetailMixin()
    view.cv_object_detail_show_help_text = resolved_policy
    groups = resolve_all(obj, [PropertyGroupConfig(title="Info", properties=["text"])], view=view)
    view.cv_object_detail_show_help_text = not resolved_policy
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = not resolved_policy
    html = Template("{% load crud_views_object_detail %}{% render_object_detail obj groups %}").render(
        Context({"obj": obj, "groups": groups, "view": view})
    )
    assert ("The info body text" in html) is resolved_policy
    assert groups[0].properties[0].detail == ("The info body text" if resolved_policy else None)


class TestRenderGroup:
    def test_renders_group_title(self, groups):
        tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
        ctx = Context({"group": groups[0]})
        html = tpl.render(ctx)
        assert "Report" in html
        assert "Report details" in html

    def test_renders_icon(self, groups):
        tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
        ctx = Context({"group": groups[0]})
        html = tpl.render(ctx)
        assert '<i class="file-text' in html

    def test_no_icon(self, groups):
        tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
        ctx = Context({"group": groups[1]})
        html = tpl.render(ctx)
        assert "text-primary fs-5" not in html


class TestRenderProperty:
    def test_renders_label_and_value(self, groups):
        prop = groups[0].properties[0]  # title
        tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
        ctx = Context({"prop": prop})
        html = tpl.render(ctx)
        assert "Report title" in html
        assert "Test Report" in html

    def test_renders_detail(self):
        prop = ResolvedProperty(
            path="test",
            label="Test",
            value="val",
            detail="Detail info",
            type="char",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "Detail info" in html


class TestRenderPropertyValue:
    def test_char_value(self):
        prop = ResolvedProperty(path="t", label="T", value="hello", type="char")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "hello" in html

    def test_boolean_true(self):
        prop = ResolvedProperty(path="t", label="T", value=True, type="boolean")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "fa-circle-check" in html

    def test_boolean_false(self):
        prop = ResolvedProperty(path="t", label="T", value=False, type="boolean")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "fa-circle-xmark" in html

    def test_none_value(self):
        prop = ResolvedProperty(path="t", label="T", value=None, type="char")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "&mdash;" in html or "\u2014" in html

    def test_manytomany_list(self):
        prop = ResolvedProperty(
            path="t",
            label="T",
            value=["Alice", "Bob"],
            type="manytomany",
            is_many=True,
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "Alice" in html
        assert "Bob" in html
        assert "<li>" in html

    def test_custom_template(self):
        prop = ResolvedProperty(
            path="t",
            label="T",
            value="custom-test-value",
            template="test_custom_value.html",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert '<span class="custom-rendered">custom-test-value</span>' in html

    def test_default_fallback(self):
        prop = ResolvedProperty(
            path="t",
            label="T",
            value="anything",
            type="unknown_type",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "anything" in html


class TestRenderPropertyValueText:
    def test_text_default_linebreaksbr(self):
        prop = ResolvedProperty(path="t", label="T", value="line1\nline2", type="text")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "<br>" in html
        assert "<p>" not in html

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE="linebreaks")
    def test_text_linebreaks_setting(self):
        prop = ResolvedProperty(path="t", label="T", value="line1\nline2", type="text")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "<p>" in html


class TestRenderPropertyLink:
    def test_link_rendered_as_anchor(self):
        prop = ResolvedProperty(
            path="t",
            label="Owner",
            value="testuser",
            type="char",
            link_url="/users/1/",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert '<a href="/users/1/">' in html
        assert "testuser" in html
        assert "</a>" in html

    def test_no_link_no_anchor(self):
        prop = ResolvedProperty(
            path="t",
            label="Owner",
            value="testuser",
            type="char",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "<a " not in html
        assert "testuser" in html

    def test_link_wraps_value_not_label(self):
        prop = ResolvedProperty(
            path="t",
            label="Owner",
            value="testuser",
            type="char",
            link_url="/users/1/",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
        html = tpl.render(Context({"prop": prop}))
        # The label should NOT be inside the <a> tag
        anchor_start = html.index("<a href=")
        anchor_end = html.index("</a>") + len("</a>")
        anchor_html = html[anchor_start:anchor_end]
        assert "Owner" not in anchor_html
        assert "testuser" in anchor_html


class TestRenderPropertyBadge:
    def test_badge_renders_with_value(self):
        prop = ResolvedProperty(
            path="t",
            label="Status",
            value="Active",
            type="char",
            badge_css="text-bg-success",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert '<span class="badge text-bg-success">' in html
        assert "Active" in html

    def test_badge_renders_with_label(self):
        prop = ResolvedProperty(
            path="t",
            label="Status",
            value=True,
            type="boolean",
            badge_css="text-bg-success",
            badge_label="Yes",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert '<span class="badge text-bg-success">' in html
        assert "Yes" in html

    def test_badge_pill(self):
        prop = ResolvedProperty(
            path="t",
            label="Status",
            value="OK",
            type="char",
            badge_css="text-bg-primary rounded-pill",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "rounded-pill" in html

    def test_badge_null_value_shows_dash(self):
        prop = ResolvedProperty(
            path="t",
            label="Status",
            value=None,
            type="char",
            badge_css="text-bg-success",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "&mdash;" in html or "\u2014" in html
        assert "badge" not in html

    def test_badge_no_css_uses_type_template(self):
        prop = ResolvedProperty(
            path="t",
            label="Status",
            value=True,
            type="boolean",
        )
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "badge" not in html
        assert "fa-circle-check" in html
