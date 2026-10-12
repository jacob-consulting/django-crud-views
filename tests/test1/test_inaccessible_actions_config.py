"""#149: CRUD_VIEWS_INACCESSIBLE_ACTIONS setting, ViewSet.inaccessible_actions, CrudView.cv_inaccessible_actions."""

import pytest
from django.urls import reverse
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from tests.test1.app.views import PublisherDeleteView, cv_publisher


def test_setting_default_is_hide():
    assert CrudViewsSettings().inaccessible_actions == "hide"


@pytest.mark.parametrize("value", ["grey", "Disable", ""])
def test_invalid_setting_reported_e104(value):
    messages = CrudViewsSettings(inaccessible_actions=value).check_messages
    assert [m.id for m in messages] == ["crud_views.E104"]
    assert "CRUD_VIEWS_INACCESSIBLE_ACTIONS" in messages[0].msg


def test_valid_setting_disable_has_no_messages():
    assert CrudViewsSettings(inaccessible_actions="disable").check_messages == []


def test_viewset_rejects_invalid_value():
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import Publisher

    with pytest.raises(ValidationError):
        ViewSet(model=Publisher, name="publisher_bad_mode_149", inaccessible_actions="Disable")


def test_default_resolves_to_hide():
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "hide"


def test_resolution_falls_back_to_setting(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "inaccessible_actions", "disable")
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "disable"


def test_viewset_overrides_setting(monkeypatch):
    monkeypatch.setattr(cv_publisher, "inaccessible_actions", "disable")
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "disable"


def test_view_overrides_viewset(monkeypatch):
    monkeypatch.setattr(cv_publisher, "inaccessible_actions", "disable")
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", "hide")
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "hide"


def _check_ids(view_cls) -> list[str]:
    return [m.id for c in view_cls.checks() for m in c.messages()]


@pytest.mark.parametrize("value", ["grey", "Disable"])
def test_e207_invalid_view_value(monkeypatch, value):
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", value)
    assert "viewset.E207" in _check_ids(PublisherDeleteView)


@pytest.mark.parametrize("value", [None, "hide", "disable"])
def test_e207_valid_view_values(monkeypatch, value):
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", value)
    assert "viewset.E207" not in _check_ids(PublisherDeleteView)


@pytest.mark.django_db
def test_button_data_carries_target_mode(client_user_publisher_view, publisher_penguin, monkeypatch):
    # the TARGET view's mode travels in the data (delete -> PublisherDeleteView), not the rendering view's
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", "disable")
    resp = client_user_publisher_view.get(
        reverse(cv_publisher.get_router_name("detail"), kwargs={"pk": publisher_penguin.pk})
    )
    view, request = resp.context["view"], resp.context["request"]
    delete_ctx = view.cv_get_context(key="delete", obj=publisher_penguin, user=request.user, request=request)
    update_ctx = view.cv_get_context(key="update", obj=publisher_penguin, user=request.user, request=request)
    assert delete_ctx["cv_inaccessible_actions"] == "disable"
    assert update_ctx["cv_inaccessible_actions"] == "hide"
