"""IN-05: an incomplete nested Guardian composition must never bypass child authorization."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import RequestFactory

from crud_views.lib.views import ListViewPermissionRequired, UpdateViewPermissionRequired
from crud_views_guardian.lib.mixins import (
    GuardianObjectPermissionMixin,
    GuardianParentPermissionMixin,
    GuardianQuerysetMixin,
)
from crud_views_guardian.lib.views import (
    GuardianActionViewPermissionRequired,
    GuardianCardListViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)


class UnsafeUpdate(GuardianParentPermissionMixin, UpdateViewPermissionRequired):
    pass


class UnsafeList(GuardianParentPermissionMixin, ListViewPermissionRequired):
    pass


class LateObjectGate(GuardianParentPermissionMixin, UpdateViewPermissionRequired, GuardianObjectPermissionMixin):
    pass


class LateQuerysetGate(GuardianParentPermissionMixin, ListViewPermissionRequired, GuardianQuerysetMixin):
    pass


@pytest.fixture
def child_viewset():
    # Tests need only the composition gate; no parent query or registry mutation is needed.
    return SimpleNamespace(parent=object())


@pytest.mark.parametrize("view_class", [UnsafeUpdate, UnsafeList, LateObjectGate, LateQuerysetGate])
def test_incomplete_child_composition_cannot_bypass_permission_gate(monkeypatch, child_viewset, view_class):
    monkeypatch.setattr(view_class, "cv_viewset", child_viewset)
    with pytest.raises(ImproperlyConfigured, match=r"Guardian.*Mixin"):
        view_class().has_permission()


@pytest.mark.parametrize("view_class", [UnsafeUpdate, UnsafeList, LateObjectGate, LateQuerysetGate])
@pytest.mark.parametrize("method", ["get", "post"])
def test_incomplete_child_composition_rejected_before_parent_or_view_processing(
    monkeypatch, child_viewset, view_class, method
):
    monkeypatch.setattr(view_class, "cv_viewset", child_viewset)
    calls = []
    monkeypatch.setattr(view_class, "_guardian_check_parent", lambda *a, **k: calls.append("parent"))
    monkeypatch.setattr(view_class, method, lambda *a, **k: HttpResponse("unguarded handler reached"), raising=False)
    request = getattr(RequestFactory(), method)("/")
    request.user = SimpleNamespace(is_authenticated=True, is_active=True)
    with pytest.raises(ImproperlyConfigured, match=r"Guardian.*Mixin"):
        view_class.as_view()(request)
    assert calls == []


@pytest.mark.parametrize(
    "view_class",
    [
        GuardianDetailViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        GuardianActionViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianCardListViewPermissionRequired,
        GuardianCreateViewPermissionRequired,
    ],
)
def test_shipped_child_compositions_retain_their_permission_delegation(monkeypatch, child_viewset, view_class):
    monkeypatch.setattr(view_class, "cv_viewset", child_viewset)
    assert view_class().has_permission() is True


def test_top_level_parent_mixin_still_delegates_to_core_permission_gate(monkeypatch):
    monkeypatch.setattr(UnsafeUpdate, "cv_viewset", SimpleNamespace(parent=None))
    monkeypatch.setattr(UpdateViewPermissionRequired, "has_permission", lambda self: False)
    assert UnsafeUpdate().has_permission() is False


@pytest.mark.parametrize(
    "view_class,companion",
    [
        (UnsafeUpdate, "GuardianObjectPermissionMixin"),
        (UnsafeList, "GuardianQuerysetMixin"),
        (LateObjectGate, "GuardianObjectPermissionMixin"),
        (LateQuerysetGate, "GuardianQuerysetMixin"),
    ],
)
def test_system_check_names_missing_child_gate(monkeypatch, child_viewset, view_class, companion):
    from django.core.checks import run_checks

    from crud_views.lib import viewset as registry

    monkeypatch.setattr(view_class, "cv_viewset", child_viewset)
    monkeypatch.setattr(registry, "_REGISTRY", {"unsafe": SimpleNamespace(get_all_views=lambda: {"test": view_class})})
    # The extension's dedicated tag proves ready() registered the check, without invoking unrelated core checks.
    messages = run_checks(tags=["crud_views_guardian"])
    assert len(messages) == 1
    assert messages[0].id == "crud_views_guardian.E001"
    assert messages[0].obj is view_class
    assert companion in messages[0].msg
    assert companion in messages[0].hint


def test_system_check_accepts_shipped_compositions():
    from django.core.checks import run_checks

    assert run_checks(tags=["crud_views_guardian"]) == []
