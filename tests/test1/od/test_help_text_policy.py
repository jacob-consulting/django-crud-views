from types import SimpleNamespace

import pytest
from django.template import Context, Template
from django.test import override_settings
from django.utils import timezone
from django.utils.functional import lazy
from django.utils.translation import get_language, gettext_lazy, override
from pydantic import ValidationError

from crud_views.lib.views import DetailView
from crud_views_object_detail.lib import conf
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.lib.config import PropertyGroupConfig, x
from crud_views_object_detail.lib.mixins import ObjectDetailMixin
from crud_views_object_detail.lib.resolvers import resolve_all, resolve_group, resolve_property
from tests.test1.od_app.models import Info, Report


def render_detail(obj, groups, view=None):
    return Template("{% load crud_views_object_detail %}{% render_object_detail obj groups %}").render(
        Context({"obj": obj, "groups": groups, "view": view})
    )


def test_help_text_policy_default_hides_rendered_help():
    obj = Info(text="Body")
    groups = resolve_all(obj, [PropertyGroupConfig(title="Info", properties=["text"])])
    html = render_detail(obj, groups)
    assert "Body" in html
    assert "Info text" in html
    assert "The info body text" not in html
    assert groups[0].properties[0].detail is None


@pytest.mark.parametrize(
    "project,view_policy,detail,expected",
    [
        (True, None, None, "The info body text"),
        (False, True, None, "The info body text"),
        (True, False, None, None),
        (False, False, True, "The info body text"),
        (True, True, False, None),
        (True, True, "", None),
        (False, False, "Explicit description", "Explicit description"),
    ],
)
def test_help_text_policy_rendered_precedence(settings, project, view_policy, detail, expected):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = project
    obj = Info(text="Body")
    view = SimpleNamespace(cv_object_detail_show_help_text=view_policy)
    groups = resolve_all(obj, [PropertyGroupConfig(title="Info", properties=[x("text", detail=detail)])], view=view)
    prop = groups[0].properties[0]
    assert prop.detail == expected
    assert not isinstance(prop.detail, bool)
    html = render_detail(obj, groups)
    assert ("The info body text" in html) is (expected == "The info body text")
    assert ("Explicit description" in html) is (expected == "Explicit description")


@pytest.mark.parametrize("invalid", [0, 1, 0.0, 1.0, b"text", b"true", [], {}, ()])
def test_help_text_policy_rejects_nontext_nonbool(invalid):
    with pytest.raises(ValidationError):
        x("text", detail=invalid)


@pytest.mark.parametrize("path", ["info__is_public", "info__computed", "info__text__computed"])
def test_help_text_policy_only_terminal_metadata(path, monkeypatch, settings):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = True
    monkeypatch.setattr(Report._meta.get_field("info"), "help_text", "Intermediate description")
    obj = Report(info=Info(text="Body"))
    assert resolve_property(obj, x(path)).detail is None
    assert resolve_property(obj, x(path, detail="Explicit")).detail == "Explicit"


@pytest.mark.parametrize("source", ["explicit", "metadata"])
def test_help_text_policy_keeps_lazy_text_until_render(source, monkeypatch, settings):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = True
    evaluations = []

    def translated():
        evaluations.append(get_language())
        return "Beschreibung — 水" if get_language() == "de" else "Description"

    description = lazy(translated, str)()
    if source == "metadata":
        monkeypatch.setattr(Info._meta.get_field("text"), "help_text", description)
    prop_config = x("text", detail=description if source == "explicit" else None)
    obj = Info(text="Body")
    with override("en"):
        groups = resolve_all(obj, [PropertyGroupConfig(title="Info", properties=[prop_config])])
    assert groups[0].properties[0].detail is description
    assert evaluations == []
    with override("de"):
        assert "Beschreibung — 水" in render_detail(obj, groups)


@pytest.mark.parametrize("project", [False, True])
@pytest.mark.parametrize("view_policy", [None, False, True])
@pytest.mark.parametrize("instruction", ["omitted", "none", "true", "false", "empty", "text", "lazy", "literal_false"])
def test_help_text_policy_complete_matrix(project, view_policy, instruction, settings):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = project
    descriptions = {
        "none": None,
        "true": True,
        "false": False,
        "empty": "",
        "text": "Explicit — 水",
        "lazy": gettext_lazy("Yes"),
        "literal_false": "False",
    }
    config = x("text") if instruction == "omitted" else x("text", detail=descriptions[instruction])
    view = SimpleNamespace(cv_object_detail_show_help_text=view_policy)
    prop = resolve_property(Info(text="Body"), config, view=view)
    expected = {
        "true": "The info body text",
        "false": None,
        "empty": None,
        "text": descriptions["text"],
        "lazy": descriptions["lazy"],
        "literal_false": "False",
    }.get(instruction, "The info body text" if (project if view_policy is None else view_policy) else None)
    if instruction == "lazy":
        assert prop.detail is descriptions["lazy"]
    else:
        assert prop.detail == expected
    assert not isinstance(prop.detail, bool)


@pytest.mark.parametrize("project", [False, True])
@pytest.mark.parametrize("view_kind", ["absent", "core", "inherit", "enable", "disable"])
@pytest.mark.parametrize("entry", ["property", "group", "all"])
def test_help_text_policy_direct_entry_points(project, view_kind, entry, settings):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = project
    view = None
    effective = project
    if view_kind == "core":
        view = DetailView()
        assert not hasattr(view, "cv_object_detail_show_help_text")
    elif view_kind in {"inherit", "enable", "disable"}:
        view = ObjectDetailMixin()
        if view_kind != "inherit":
            effective = view.cv_object_detail_show_help_text = view_kind == "enable"
        else:
            assert view.cv_object_detail_show_help_text is None
    obj = Info(text="Body")
    group = PropertyGroupConfig(title="Info", properties=["text"])
    if entry == "property":
        prop = resolve_property(obj, group.properties[0], view=view)
    elif entry == "group":
        prop = resolve_group(obj, group, view=view).properties[0]
    else:
        prop = resolve_all(obj, [group], view=view)[0].properties[0]
    assert prop.detail == ("The info body text" if effective else None)


def test_help_text_policy_sequential_settings_and_interleaved_views(monkeypatch):
    obj = Info(text="Body")
    group = PropertyGroupConfig(title="Shared", properties=["text", x("text", detail="Pinned")])
    original = group.model_copy(deep=True)
    enabled = ObjectDetailMixin()
    enabled.cv_object_detail_show_help_text = True
    disabled = ObjectDetailMixin()
    disabled.cv_object_detail_show_help_text = False
    for project in [True, False, True, False]:
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT=project):
            fresh = CrudViewsObjectDetailSettings()
            monkeypatch.setattr(conf, "crud_views_object_detail_settings", fresh)
            assert fresh.show_help_text is project
            assert resolve_group(obj, group).properties[0].detail == ("The info body text" if project else None)
            shown = resolve_all(obj, [group], view=enabled)
            hidden = resolve_all(obj, [group], view=disabled)
            again = resolve_all(obj, [group], view=enabled)
            assert shown == again
            assert shown[0].properties[0].detail == "The info body text"
            assert hidden[0].properties[0].detail is None
            assert "The info body text" in render_detail(obj, shown, disabled)
            assert "The info body text" not in render_detail(obj, hidden, enabled)
            assert "Pinned" in render_detail(obj, hidden, enabled)
            assert group == original
            assert group.properties[0].detail is None
            assert conf.crud_views_object_detail_settings is fresh


@pytest.mark.parametrize("source", ["metadata", "explicit"])
def test_help_text_policy_escapes_ordinary_html(source, monkeypatch, settings):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = True
    text = '<script>alert("help")</script> — 水'
    monkeypatch.setattr(Info._meta.get_field("text"), "help_text", text)
    config = x("text", detail=text if source == "explicit" else None)
    groups = resolve_all(Info(text="Body"), [PropertyGroupConfig(title="Info", properties=[config])])
    html = render_detail(Info(text="Body"), groups)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "— 水" in html


@pytest.mark.parametrize("value", [True, False, 0, b"text", []])
def test_help_text_policy_does_not_broaden_other_lazy_fields(value):
    with pytest.raises(ValidationError):
        x("text", title=value)
    with pytest.raises(ValidationError):
        PropertyGroupConfig(title="Info", description=value, properties=[])


@pytest.mark.django_db
def test_help_text_policy_metadata_survives_missing_related_instance(settings, django_assert_num_queries):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = True
    with django_assert_num_queries(0):
        prop = resolve_property(Report(info=None), x("info__text"))
    assert prop.value is None
    assert prop.detail == "The info body text"


@pytest.mark.django_db
@pytest.mark.parametrize("enabled", [False, True])
def test_help_text_policy_relation_queries_unchanged(enabled, django_assert_num_queries):
    now = timezone.now()
    info = Info.objects.create(text="Body", create_dt=now, update_dt=now)
    saved = Report.objects.create(title="Report", info=info)
    uncached = Report.objects.get(pk=saved.pk)
    loaded = Report.objects.select_related("info").get(pk=saved.pk)
    view = SimpleNamespace(cv_object_detail_show_help_text=enabled)
    with django_assert_num_queries(1):
        first = resolve_property(uncached, x("info__text"), view=view)
    with django_assert_num_queries(0):
        second = resolve_property(loaded, x("info__text"), view=view)
    assert first == second
    assert first.detail == ("The info body text" if enabled else None)
    assert first.value == "Body"


def test_help_text_policy_setting_default():
    assert CrudViewsObjectDetailSettings().show_help_text is False


def test_help_text_policy_setting_is_cached(settings):
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = True
    config = CrudViewsObjectDetailSettings()
    assert config.show_help_text is True
    settings.CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT = False
    assert config.show_help_text is True
    assert CrudViewsObjectDetailSettings().show_help_text is False
