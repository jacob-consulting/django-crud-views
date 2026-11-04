"""The display budget is applied after visibility, independently of deletion authority."""

import pytest
from django.core.exceptions import ImproperlyConfigured

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.views import DeleteView


def test_delete_preview_limit_precedence_default():
    assert getattr(CrudViewsSettings(), "delete_preview_limit", "missing") == 50


@pytest.mark.parametrize("project", [None, 1, 50])
@pytest.mark.parametrize("override", ["unset", None, 3])
def test_delete_preview_limit_precedence(monkeypatch, project, override):
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", project)

    class Base(DeleteView):
        pass

    if override != "unset":
        Base.cv_delete_preview_limit = override

    class Inherited(Base):
        pass

    for view in (Base, Inherited):
        assert view()._cv_get_delete_preview_limit() == (project if override == "unset" else override)
        assert "viewset.E265" not in {message.id for check in view.checks() for message in check.messages()}


@pytest.mark.parametrize("value", [True, False, 1.5, "2", 0, -1, [], {}, object()])
def test_delete_preview_limit_invalid(monkeypatch, value):
    configured = CrudViewsSettings(delete_preview_limit=value)
    assert any(message.id == "crud_views.E109" for message in configured.check_messages)
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", value)
    with pytest.raises(ImproperlyConfigured, match="delete_preview_limit"):
        DeleteView()._cv_get_delete_preview_limit()

    class Invalid(DeleteView):
        cv_delete_preview_limit = value

    assert "viewset.E265" in {message.id for check in Invalid.checks() for message in check.messages()}
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", 50)
    with pytest.raises(ImproperlyConfigured, match="delete_preview_limit"):
        Invalid()._cv_get_delete_preview_limit()


@pytest.mark.django_db
@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize("project,override,valid", [(False, "unset", False), (50, False, False), (False, 2, True), (False, None, True)])
def test_delete_preview_limit_invalid_request(
    client_user_publisher_delete, publisher_penguin, monkeypatch, settings, preview, project, override, valid
):
    from tests.test1.app.views import PublisherDeleteView

    settings.CRUD_VIEWS_STRICT_CHECKS = False
    monkeypatch.setattr(crud_views_settings, "delete_preview_limit", project)
    monkeypatch.setattr(PublisherDeleteView, "cv_show_related_objects", preview)
    if override != "unset":
        monkeypatch.setattr(PublisherDeleteView, "cv_delete_preview_limit", override)
    assert any(m.id == "crud_views.E109" for m in crud_views_settings.check_messages) is (project is False)
    path = f"/publisher/{publisher_penguin.pk}/delete/"
    if valid:
        assert client_user_publisher_delete.get(path).status_code == 200
    else:
        with pytest.raises(ImproperlyConfigured, match="delete_preview_limit"):
            client_user_publisher_delete.get(path)
