"""Direct contract of the private link check, independent of page rendering."""

from inspect import Parameter, signature
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import remove_perm

from crud_views.lib.link_access import (
    _LINK_ALLOWED,
    _LINK_PERMISSION,
    _higher_ancestor_gates,
    _link_access,
    _link_permission,
)
from crud_views.lib.views import CreateView, CreateViewParentMixin, ListView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1 import test_ancestor_helpers as ancestor_helpers
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import _user, isolated_routes
from tests.test1.test_ancestor_helpers import _grant

helpers = ancestor_helpers.helpers
data = ancestor_helpers.data
provider_calls = ancestor_helpers.provider_calls
lookups = ancestor_helpers.lookups

BACKENDS = ["django.contrib.auth.backends.ModelBackend", "guardian.backends.ObjectPermissionBackend"]
ANONYMOUS_EDITOR = "tests.test1.test_link_access_matrix.AnonymousParentEditorBackend"


class InactiveAncestorBackend(BaseBackend):
    """Grant the checked parent permissions even to an inactive signed-in actor."""

    def has_perm(self, user_obj, perm, obj=None):
        return (
            user_obj.is_authenticated
            and not user_obj.is_active
            and perm
            in {
                "app.view_publisher",
                "app.change_publisher",
                "app.view_book",
            }
        )


@pytest.fixture
def core_targets():
    """Plain core targets under a core parent, isolated with the shared route helper."""

    def build(suffix):
        parent = ViewSet(model=Publisher, name=f"linkcorepub{suffix}")
        child = ViewSet(
            model=Book,
            name=f"linkcorebook{suffix}",
            parent=ParentViewSet(name=parent.name, attribute="publisher"),
        )
        common = {"cv_viewset": child, "cv_context_actions": []}
        family = SimpleNamespace(
            parent=parent,
            vs=child,
            List=type("LinkCoreList", (ListView,), {**common, "cv_list_actions": []}),
            Create=type("LinkCoreCreate", (CreateViewParentMixin, CreateView), {**common, "fields": ["title"]}),
        )
        return family, [parent, child]

    with isolated_routes(build) as family:
        yield family


def test_signature_is_the_concept_interface():
    for function in (_link_access, _link_permission):
        parameters = list(signature(function).parameters.values())
        assert [(p.name, p.kind) for p in parameters] == [
            ("target", Parameter.POSITIONAL_OR_KEYWORD),
            ("user", Parameter.POSITIONAL_OR_KEYWORD),
            ("obj", Parameter.POSITIONAL_OR_KEYWORD),
            ("known_ancestors", Parameter.POSITIONAL_OR_KEYWORD),
            ("rendering_view", Parameter.KEYWORD_ONLY),
        ]
        assert [p.default for p in parameters] == [Parameter.empty, Parameter.empty, None, (), None]
    assert [(p.name, p.kind, p.default) for p in signature(_higher_ancestor_gates).parameters.values()] == [
        (name, Parameter.POSITIONAL_OR_KEYWORD, Parameter.empty) for name in ("target", "user", "known_ancestors")
    ]


@pytest.mark.django_db
def test_ancestors_two_level_list_gates_every_level(helpers, data, provider_calls, lookups, monkeypatch):
    target = helpers.note.List
    monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=True))
    actor = _user("link_two_levels")
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.book, "view", data.book)
    outer = (helpers.pub.vs.name, "app.view_publisher", data.penguin)
    nearest = (helpers.book.vs.name, "app.view_book", data.book)

    with CaptureQueriesContext(connection) as captured:
        assert _link_access(target, actor, known_ancestors=(data.book, data.penguin)) == _LINK_ALLOWED
    assert provider_calls == [outer, nearest]
    assert provider_calls[0][2] is data.penguin
    assert provider_calls[1][2] is data.book
    assert lookups == []
    for query in captured.captured_queries:
        for model in (Publisher, Book):
            for clause in ("from", "join"):
                assert f'{clause} "{model._meta.db_table}"' not in query["sql"].lower()

    remove_perm(helpers.pub.vs.permissions["view"], actor, data.penguin)
    actor = User.objects.get(pk=actor.pk)
    provider_calls.clear()
    assert _link_access(target, actor, known_ancestors=(data.book, data.penguin)) == _LINK_PERMISSION
    assert provider_calls == [outer]

    provider_calls.clear()
    assert _link_access(target, actor, known_ancestors=(data.book,)) == _LINK_ALLOWED
    assert provider_calls == [nearest]

    monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=False))
    provider_calls.clear()
    assert _link_access(target, actor, known_ancestors=(data.book, data.penguin)) == _LINK_ALLOWED
    assert provider_calls == [nearest]
    assert lookups == []


@pytest.mark.django_db
def test_ancestors_unprotected_parent_moves_nearest_key_up(helpers, data, provider_calls, monkeypatch):
    target = helpers.open_note.Create
    monkeypatch.setattr(helpers.open_note.vs, "ancestor_policy", AncestorPolicy(cascade=True))
    reader = _user("link_upper_reader")
    _grant(reader, helpers.pub, "view", data.penguin)
    assert _link_access(target, reader, known_ancestors=(data.book,)) == _LINK_ALLOWED
    assert provider_calls == []

    reader = User.objects.get(pk=reader.pk)
    assert _link_access(target, reader, known_ancestors=(data.book, data.penguin)) == _LINK_PERMISSION
    expected = [(helpers.pub.vs.name, "app.change_publisher", data.penguin)]
    assert provider_calls == expected

    editor = _user("link_upper_editor")
    _grant(editor, helpers.pub, "change", data.penguin)
    provider_calls.clear()
    assert _link_access(target, editor, known_ancestors=(data.book, data.penguin)) == _LINK_ALLOWED
    assert provider_calls == expected
    assert provider_calls[0][2] is data.penguin


@pytest.mark.django_db
def test_ancestors_missing_immediate_parent_is_denied(helpers, data, provider_calls, monkeypatch):
    actor = _user("link_missing_parent")
    for target, obj in ((helpers.book.List, None), (helpers.book.Create, None), (helpers.book.Detail, data.book)):
        own = Mock(return_value=True)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        for known in ([], [None], [None, data.penguin]):
            assert _link_access(target, actor, obj, known) == _LINK_PERMISSION
        own.assert_not_called()
        state.assert_not_called()
    assert provider_calls == []


@pytest.mark.django_db
def test_order_parent_gate_runs_before_own_access(helpers, data, monkeypatch):
    actor = _user("link_order")
    target = helpers.book.List
    _grant(actor, helpers.pub, "view", data.penguin)
    calls = []
    original_gate = GuardianViewSet._ancestor_has_permission

    def gate(viewset, user, permission, obj, *, view):
        calls.append(("gate", user, permission, obj, view))
        return original_gate(viewset, user, permission, obj, view=view)

    own = Mock(side_effect=lambda user, obj: calls.append(("own", user, obj)) or True)
    state = Mock(side_effect=lambda user, obj: calls.append(("state", user, obj)) or True)
    monkeypatch.setattr(GuardianViewSet, "_ancestor_has_permission", gate)
    monkeypatch.setattr(target, "cv_has_access", own)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    assert _link_access(target, actor, known_ancestors=(data.penguin,)) == _LINK_ALLOWED
    assert calls == [
        ("gate", actor, "app.view_publisher", data.penguin, None),
        ("own", actor, None),
        ("state", actor, data.penguin),
    ]


@pytest.mark.django_db
def test_order_state_hook_not_called_when_permission_denies(helpers, data, provider_calls, monkeypatch):
    actor = _user("link_denied_order")
    target = helpers.book.List
    own = Mock(return_value=True)
    state = Mock(return_value=True)
    monkeypatch.setattr(target, "cv_has_access", own)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    expected = [(helpers.pub.vs.name, "app.view_publisher", data.penguin)]

    assert _link_access(target, actor, known_ancestors=(data.penguin,)) == _LINK_PERMISSION
    assert provider_calls == expected
    own.assert_not_called()
    state.assert_not_called()

    _grant(actor, helpers.pub, "view", data.penguin)
    actor = User.objects.get(pk=actor.pk)
    own.return_value = False
    provider_calls.clear()
    assert _link_access(target, actor, known_ancestors=(data.penguin,)) == _LINK_PERMISSION
    assert provider_calls == expected
    own.assert_called_once_with(actor, None)
    state.assert_not_called()

    own.return_value = True
    provider_calls.clear()
    assert _link_access(target, actor, known_ancestors=(data.penguin,)) == _LINK_ALLOWED
    assert provider_calls == expected
    state.assert_called_once_with(actor, data.penguin)


@pytest.mark.django_db
def test_actor_rule_for_protected_ancestry(helpers, core_targets, data, provider_calls, monkeypatch):
    inactive = _user("link_inactive")
    inactive.is_active = False
    inactive.save(update_fields=["is_active"])
    inactive = User.objects.get(pk=inactive.pk)
    anonymous = AnonymousUser()
    granting = [*BACKENDS, "tests.test1.test_link_access.InactiveAncestorBackend", ANONYMOUS_EDITOR]
    # A list can use change as its nearest Read key, so the same anonymous backend grants its gate too.
    monkeypatch.setattr(
        helpers.core_book.vs,
        "ancestor_policy",
        AncestorPolicy(read=AncestorPermissions(nearest="change", higher="view")),
    )
    with override_settings(AUTHENTICATION_BACKENDS=granting):
        for actor in (anonymous, inactive):
            assert actor.has_perm("app.change_publisher") is True
            for target in (core_targets.Create, helpers.core_book.List):
                state = Mock(return_value=True)
                monkeypatch.setattr(target, "cv_action_enabled", state)
                assert _link_access(target, actor, known_ancestors=(data.penguin,)) == _LINK_PERMISSION
                state.assert_not_called()

        for parent in (core_targets.parent, helpers.cpub):
            monkeypatch.setattr(parent, "ancestor_policy", AncestorPolicy(provider="none"))
        provider_calls.clear()
        for actor in (anonymous, inactive):
            state = Mock(return_value=True)
            monkeypatch.setattr(core_targets.Create, "cv_action_enabled", state)
            assert _link_access(core_targets.Create, actor, known_ancestors=(data.penguin,)) == _LINK_ALLOWED
            state.assert_called_once_with(actor, data.penguin)
            guardian_state = Mock(return_value=True)
            monkeypatch.setattr(helpers.core_book.List, "cv_action_enabled", guardian_state)
            assert _link_access(helpers.core_book.List, actor, known_ancestors=(data.penguin,)) == _LINK_PERMISSION
            guardian_state.assert_not_called()
        assert provider_calls == []

    # L2 / D-35: nested Guardian create retains its hook's actor rule under a model-provider parent.
    monkeypatch.setattr(helpers.cpub, "ancestor_policy", AncestorPolicy())
    target = helpers.core_book.Create
    for actor, backends, outcome in (
        (inactive, granting, _LINK_PERMISSION),
        (anonymous, BACKENDS, _LINK_PERMISSION),
        (anonymous, granting, _LINK_ALLOWED),
    ):
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        provider_calls.clear()
        with override_settings(AUTHENTICATION_BACKENDS=backends):
            assert _link_access(target, actor, known_ancestors=(data.penguin,)) == outcome
        if outcome == _LINK_PERMISSION:
            state.assert_not_called()
        else:
            state.assert_called_once_with(actor, data.penguin)
            assert provider_calls == [(helpers.cpub.name, "app.change_publisher", data.penguin)]


@pytest.mark.django_db
def test_higher_ancestor_gates_order_and_absent_levels(helpers, data, provider_calls, monkeypatch):
    target = helpers.note.List
    anonymous = AnonymousUser()
    inactive = _user("link_upper_inactive")
    inactive.is_active = False
    active = _user("link_upper_active")
    monkeypatch.setattr(
        helpers.note.vs,
        "ancestor_policy",
        AncestorPolicy(cascade=True, read=AncestorPermissions(nearest="view", higher="change")),
    )
    with override_settings(
        AUTHENTICATION_BACKENDS=[*BACKENDS, "tests.test1.test_link_access.InactiveAncestorBackend", ANONYMOUS_EDITOR]
    ):
        for actor in (anonymous, inactive):
            assert actor.has_perm("app.change_publisher") is True
            assert _higher_ancestor_gates(target, actor, (data.book, data.penguin)) is False
            assert provider_calls == []
    monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=False))
    assert _higher_ancestor_gates(target, anonymous, (data.book, data.penguin)) is True
    assert provider_calls == []
    monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=True))
    assert _higher_ancestor_gates(target, active, (data.book, None)) is True
    assert provider_calls == []

    _grant(active, helpers.pub, "view", data.penguin)
    assert _higher_ancestor_gates(target, active, (data.book, data.penguin)) is True
    assert provider_calls == [(helpers.pub.vs.name, "app.view_publisher", data.penguin)]
    provider_calls.clear()

    monkeypatch.setattr(
        helpers.note.vs,
        "ancestor_policy",
        AncestorPolicy(cascade=True, read=AncestorPermissions(nearest="view", higher="approve")),
    )
    with pytest.raises(ImproperlyConfigured, match="approve"):
        _higher_ancestor_gates(target, active, (data.book, data.penguin))
    assert _higher_ancestor_gates(target, anonymous, (data.book, data.penguin)) is False
    assert provider_calls == []
