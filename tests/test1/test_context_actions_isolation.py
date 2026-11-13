"""
Audit task 2.2 (M6): view registration must not mutate the context-action
lists owned by the settings singleton (copy-on-write), and the
"add manage to context actions" behavior must honor
CRUD_VIEWS_MANAGE_VIEWS_ENABLED instead of a literal `if True`.
"""

import pytest

from crud_views.lib.settings import crud_views_settings
from tests.test1.app.models import Publisher


def test_settings_lists_not_mutated_by_registration(cv_author):
    # cv_author forces import of the app views module, i.e. registration of
    # all test viewsets; the settings singleton's lists must still be pristine
    for name in (
        "list_context_actions",
        "detail_context_actions",
        "create_context_actions",
        "update_context_actions",
        "delete_context_actions",
    ):
        assert "manage" not in getattr(crud_views_settings, name), name


def test_registered_view_class_gets_manage_action(cv_author):
    cls = cv_author.get_view_class("detail")
    assert "manage" in cls.cv_context_actions


def test_view_class_actions_are_not_the_settings_list(cv_author):
    cls = cv_author.get_view_class("detail")
    assert cls.cv_context_actions is not crud_views_settings.detail_context_actions


def test_manage_not_added_when_manage_views_disabled(monkeypatch):
    from crud_views.lib.view import CrudView
    from crud_views.lib.viewset import _REGISTRY, ViewSet

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")

    name = "ctx_actions_probe"
    viewset = ViewSet(model=Publisher, name=name)
    try:

        class ProbeView(CrudView):
            cv_viewset = viewset
            cv_key = "probe"
            cv_path = "probe"
            cv_context_actions = ["home"]

        assert "manage" not in ProbeView.cv_context_actions
    finally:
        _REGISTRY.pop(name, None)


def test_manage_added_when_manage_views_enabled(monkeypatch):
    from crud_views.lib.view import CrudView
    from crud_views.lib.viewset import _REGISTRY, ViewSet

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")

    name = "ctx_actions_probe_enabled"
    viewset = ViewSet(model=Publisher, name=name)
    try:

        class ProbeView(CrudView):
            cv_viewset = viewset
            cv_key = "probe"
            cv_path = "probe"
            cv_context_actions = ["home"]

        assert "manage" in ProbeView.cv_context_actions
    finally:
        _REGISTRY.pop(name, None)


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.parametrize("presentation", ["hide", "disable"])
@pytest.mark.parametrize("mode", ["yes", "no"])
def test_explicit_manage_action_is_hidden_for_nonmember(
    client, user_author_view, cv_author, cv_guardian_author, monkeypatch, family, presentation, mode
):
    from crud_views.lib.view.visibility import cv_resolve_action

    vs = cv_author if family == "core" else cv_guardian_author
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
    monkeypatch.setattr(crud_views_settings, "inaccessible_actions", presentation)
    source = vs.get_view_class("list")
    original_actions = list(source.cv_context_actions)
    monkeypatch.setattr(source, "cv_context_actions", ["manage", "create"])
    target = vs.get_view_class("manage")
    monkeypatch.setattr(target, "cv_inaccessible_actions", "disable")
    assert target.cv_get_inaccessible_actions() == "hide"
    client.force_login(user_author_view)
    response = client.get("/author/" if family == "core" else "/guardian_author/")
    assert response.status_code == 200
    assert b"/manage/" not in response.content
    view = response.context["view"]
    data = view.cv_get_context(key="manage", user=user_author_view, request=view.request, location="context")
    assert not data["cv_access"]
    assert cv_resolve_action(data) is None
    create = view.cv_get_context(key="create", user=user_author_view, request=view.request, location="context")
    resolved = cv_resolve_action(create)
    if presentation == "disable":
        assert resolved["cv_disabled"] is True
        assert b'disabled data-cv-disabled="permission"' in response.content
    else:
        assert resolved is None
    assert "manage" in original_actions


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
def test_custom_manage_subclass_inherits_active_group_gate_and_hiding(
    family, user_author_view, cv_author, cv_guardian_author, rf
):
    from django.contrib.auth.models import Group
    from django.core.exceptions import PermissionDenied

    from crud_views.lib.views.manage import ManageView
    from crud_views_guardian.lib.views import GuardianManageView

    base = ManageView if family == "core" else GuardianManageView

    class CustomManage(base):
        cv_inaccessible_actions = "disable"

    CustomManage.cv_viewset = cv_author if family == "core" else cv_guardian_author
    request = rf.get("/custom-manage/")
    request.user = user_author_view
    assert CustomManage.cv_has_access(user_author_view) is False
    assert CustomManage.cv_get_inaccessible_actions() == "hide"
    with pytest.raises(PermissionDenied):
        CustomManage.as_view()(request)
    user_author_view.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    assert CustomManage.cv_has_access(user_author_view) is True
    response = CustomManage.as_view()(request)
    assert response.status_code == 200
    assert "permission_holders" in response.context_data
