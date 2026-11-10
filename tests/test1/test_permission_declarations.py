"""#341: declared permission keys, both E269 halves, and their skips and zero-DB contract."""

from __future__ import annotations

from django.core.checks import run_checks
from django.db import models
from django.test.utils import isolate_apps

import tests.test1.project.urls  # noqa: F401 - registers shared ViewSets before any registry snapshot
from crud_views.checks import check_ancestor_declarations
from crud_views.lib.viewset import ViewSet
from tests.test1 import test_ancestor_operations as _ops

# Reuse the registry-restoring and database-blocking fixtures without collecting the source module's tests.
registry, sfx, no_db = _ops.registry, _ops.sfx, _ops.no_db
_view, _ours, _core, _nested = _ops._view, _ops._ours, _ops._core, _ops._nested


def _e269(*viewsets):
    return [
        message
        for message in check_ancestor_declarations()
        if message.id == "viewset.E269" and any(message.obj is viewset for viewset in viewsets)
    ]


def test_undeclared_cv_permission_is_reported_at_startup(registry, sfx, no_db):
    with isolate_apps("tests.test1.app"):

        class Approvable(models.Model):
            class Meta:
                app_label = "app"
                permissions = [("approve_approvable", "Can approve")]

        vs = ViewSet(model=Approvable, name=f"pd_approvable_{sfx}")
        _view(_core("ListViewPermissionRequired"), vs)
        _view(_core("ActionViewPermissionRequired"), vs, key="approve", cv_permission="approve")
        _view(_core("ActionViewPermissionRequired"), vs, key="run", cv_permission="run")

        assert _ours(check_ancestor_declarations(), vs) == [("viewset.E269", vs.name)]
        message = _e269(vs)[0]
        assert message.msg == "cv_permission 'run' of view 'run' is not declared on model app.Approvable"
        assert message.hint == (
            'add ("run_approvable", "...") to Approvable.Meta.permissions, '
            "or use the non-PermissionRequired view variant"
        )
        assert len([m for m in run_checks(tags=["crud_views"]) if m.id == "viewset.E269" and m.obj is vs]) == 1
        assert "viewset.E269" not in [m.id for c in vs.checks() for m in c.messages()]

        Approvable._meta.permissions.append(("run_approvable", "Can run"))
        assert _ours(check_ancestor_declarations(), vs) == []


def test_shared_registry_has_no_e269(no_db):
    assert [m for m in check_ancestor_declarations() if m.id == "viewset.E269"] == []
