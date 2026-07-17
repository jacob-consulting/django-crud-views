import pytest
from django.template import Template, Context
from django.test import override_settings
from django.utils import timezone

from crud_views_object_detail.lib import conf
from crud_views_object_detail.lib.config import x
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.lib.resolvers import (
    ResolvedProperty,
    resolve_all,
)
from crud_views_object_detail.lib.config import PropertyGroupConfig
from crud_views_object_detail.templatetags import crud_views_object_detail as tags
from tests.test1.od_app.models import Info, Report


@pytest.fixture(autouse=True)
def _fresh_singleton(monkeypatch):
    """Both conf.py and the templatetags module hold their own bound reference to the
    settings singleton (the latter via `from ... import crud_views_object_detail_settings`),
    and cached_property values persist across tests. Reset both before each test so
    @override_settings actually takes effect through the templatetags module."""
    monkeypatch.setattr(conf, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
    monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())


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
        assert "bi-file-text" in html

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
        assert "check-circle-fill" in html

    def test_boolean_false(self):
        prop = ResolvedProperty(path="t", label="T", value=False, type="boolean")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "x-circle-fill" in html

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
        assert "check-circle-fill" in html
