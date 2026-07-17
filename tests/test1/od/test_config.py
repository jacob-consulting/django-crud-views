import pytest
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from pydantic import ValidationError

from crud_views_object_detail.lib.config import (
    BadgeConfig,
    LinkConfig,
    PropertyConfig,
    PropertyGroupConfig,
    parse_property_display,
    x,
)


class TestPropertyConfig:
    def test_minimal(self):
        cfg = PropertyConfig(path="title")
        assert cfg.path == "title"
        assert cfg.title is None
        assert cfg.detail is None
        assert cfg.type is None
        assert cfg.template is None

    def test_full(self):
        cfg = PropertyConfig(
            path="info__text",
            title="Custom",
            detail="Detail text",
            type="timestamp",
            template="my/template.html",
        )
        assert cfg.path == "info__text"
        assert cfg.title == "Custom"
        assert cfg.type == "timestamp"


class TestX:
    def test_simple(self):
        cfg = x("title")
        assert isinstance(cfg, PropertyConfig)
        assert cfg.path == "title"

    def test_with_kwargs(self):
        cfg = x("info__text", title="custom", detail="some detail")
        assert cfg.title == "custom"
        assert cfg.detail == "some detail"

    def test_with_template(self):
        cfg = x("info__owner", template="foo/bar.html")
        assert cfg.template == "foo/bar.html"


class TestPropertyGroupConfig:
    def test_string_normalization(self):
        group = PropertyGroupConfig(
            title="Test",
            properties=["title", "owner"],
        )
        assert len(group.properties) == 2
        assert all(isinstance(p, PropertyConfig) for p in group.properties)
        assert group.properties[0].path == "title"
        assert group.properties[1].path == "owner"

    def test_mixed_properties(self):
        group = PropertyGroupConfig(
            title="Test",
            properties=[
                "title",
                x("info__text", title="Custom"),
                {"path": "owner", "type": "foreignkey"},
            ],
        )
        assert len(group.properties) == 3
        assert group.properties[0].path == "title"
        assert group.properties[1].title == "Custom"
        assert group.properties[2].type == "foreignkey"

    def test_optional_fields(self):
        group = PropertyGroupConfig(title="Test", properties=["title"])
        assert group.description is None
        assert group.icon is None

    def test_with_icon_and_description(self):
        group = PropertyGroupConfig(
            title="Info",
            description="Some description",
            icon="info-circle-fill",
            properties=["title"],
        )
        assert group.icon == "info-circle-fill"
        assert group.description == "Some description"

    def test_invalid_property_raises(self):
        with pytest.raises(ValidationError):
            PropertyGroupConfig(title="Test", properties=[123])


class TestParsePropertyDisplay:
    def test_parse_list(self):
        raw = [
            {
                "title": "Report",
                "description": "Report details",
                "properties": ["title", "owner"],
            },
            {
                "title": "Info",
                "properties": [
                    x("info__text", title="custom"),
                    "info__is_public",
                ],
            },
        ]
        groups = parse_property_display(raw)
        assert len(groups) == 2
        assert groups[0].title == "Report"
        assert len(groups[0].properties) == 2
        assert groups[1].properties[0].title == "custom"

    def test_empty_list(self):
        groups = parse_property_display([])
        assert groups == []


class TestLinkConfig:
    def test_create_with_url_only(self):
        lc = LinkConfig(url="report-detail")
        assert lc.url == "report-detail"
        assert lc.args is None
        assert lc.kwargs is None

    def test_create_with_kwargs(self):
        lc = LinkConfig(url="report-detail", kwargs={"pk": "id"})
        assert lc.kwargs == {"pk": "id"}

    def test_create_with_args(self):
        lc = LinkConfig(url="report-detail", args=["pk"])
        assert lc.args == ["pk"]

    def test_string_normalization_on_property_config(self):
        cfg = PropertyConfig(path="owner", link="user-detail")
        assert isinstance(cfg.link, LinkConfig)
        assert cfg.link.url == "user-detail"
        assert cfg.link.args is None
        assert cfg.link.kwargs is None

    def test_x_with_link_string(self):
        cfg = x("owner", link="user-detail")
        assert isinstance(cfg.link, LinkConfig)
        assert cfg.link.url == "user-detail"

    def test_x_with_link_config(self):
        cfg = x("owner", link=LinkConfig(url="user-detail", kwargs={"pk": "id"}))
        assert cfg.link.url == "user-detail"
        assert cfg.link.kwargs == {"pk": "id"}

    def test_dict_normalization_via_group(self):
        group = PropertyGroupConfig(
            title="Test",
            properties=[
                {"path": "owner", "link": "user-detail"},
            ],
        )
        prop = group.properties[0]
        assert isinstance(prop.link, LinkConfig)
        assert prop.link.url == "user-detail"

    def test_no_link_default(self):
        cfg = PropertyConfig(path="title")
        assert cfg.link is None


class TestLazyStringSupport:
    """Lazy translation strings should pass through Pydantic without being evaluated."""

    def test_property_config_title_stays_lazy(self):
        cfg = PropertyConfig(path="title", title=_("Custom Title"))
        assert isinstance(cfg.title, Promise)
        assert str(cfg.title) == "Custom Title"

    def test_property_config_detail_stays_lazy(self):
        cfg = PropertyConfig(path="title", detail=_("Some detail"))
        assert isinstance(cfg.detail, Promise)
        assert str(cfg.detail) == "Some detail"

    def test_group_title_stays_lazy(self):
        group = PropertyGroupConfig(title=_("Group Title"), properties=["title"])
        assert isinstance(group.title, Promise)
        assert str(group.title) == "Group Title"

    def test_group_description_stays_lazy(self):
        group = PropertyGroupConfig(
            title="Test",
            description=_("A description"),
            properties=["title"],
        )
        assert isinstance(group.description, Promise)
        assert str(group.description) == "A description"

    def test_x_helper_with_lazy_title(self):
        cfg = x("title", title=_("Lazy Title"))
        assert isinstance(cfg.title, Promise)

    def test_parse_property_display_with_lazy(self):
        raw = [
            {
                "title": _("Report"),
                "description": _("Report details"),
                "properties": ["title"],
            },
        ]
        groups = parse_property_display(raw)
        assert isinstance(groups[0].title, Promise)
        assert isinstance(groups[0].description, Promise)

    def test_plain_strings_still_work(self):
        cfg = PropertyConfig(path="title", title="Plain", detail="Also plain")
        assert cfg.title == "Plain"
        assert cfg.detail == "Also plain"

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            PropertyConfig(path="title", title=123)


class TestBadgeConfig:
    def test_create_with_color(self):
        bc = BadgeConfig(color="success")
        assert bc.color == "success"
        assert bc.color_map is None
        assert bc.color_fn is None
        assert bc.label_map is None
        assert bc.pill is False

    def test_create_with_color_map(self):
        bc = BadgeConfig(color_map={True: "success", False: "danger"})
        assert bc.color_map == {True: "success", False: "danger"}

    def test_create_with_color_fn(self):
        def fn(v):
            return "success" if v else "danger"

        bc = BadgeConfig(color_fn=fn)
        assert bc.color_fn is fn

    def test_create_with_label_map(self):
        bc = BadgeConfig(color="info", label_map={True: "Yes", False: "No"})
        assert bc.label_map == {True: "Yes", False: "No"}

    def test_pill(self):
        bc = BadgeConfig(color="primary", pill=True)
        assert bc.pill is True

    def test_string_normalization_on_property_config(self):
        cfg = PropertyConfig(path="status", badge="success")
        assert isinstance(cfg.badge, BadgeConfig)
        assert cfg.badge.color == "success"
        assert cfg.badge.pill is False

    def test_x_with_badge_string(self):
        cfg = x("status", badge="warning")
        assert isinstance(cfg.badge, BadgeConfig)
        assert cfg.badge.color == "warning"

    def test_x_with_badge_config(self):
        cfg = x("status", badge=BadgeConfig(color_map={True: "success"}, pill=True))
        assert cfg.badge.color_map == {True: "success"}
        assert cfg.badge.pill is True

    def test_dict_normalization_via_group(self):
        group = PropertyGroupConfig(
            title="Test",
            properties=[
                {"path": "status", "badge": "info"},
            ],
        )
        prop = group.properties[0]
        assert isinstance(prop.badge, BadgeConfig)
        assert prop.badge.color == "info"

    def test_no_badge_default(self):
        cfg = PropertyConfig(path="title")
        assert cfg.badge is None
