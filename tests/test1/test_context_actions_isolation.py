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
