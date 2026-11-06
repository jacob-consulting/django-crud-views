from types import SimpleNamespace

import pytest
from django.template import Context, Template
from django.utils.functional import lazy
from django.utils.translation import get_language, override
from pydantic import ValidationError

from crud_views_object_detail.lib.config import PropertyGroupConfig, x
from crud_views_object_detail.lib.resolvers import resolve_all, resolve_property
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
