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

from crud_views.lib import ancestors
from crud_views.lib.link_access import (
    _LINK_ALLOWED,
    _LINK_PERMISSION,
    _LINK_STATE,
    _higher_ancestor_gates,
    _link_access,
    _link_ctx,
    _link_permission,
)
from crud_views.lib.views import CreateView, CreateViewParentMixin, ListView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1 import test_ancestor_helpers as ancestor_helpers
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import _user, isolated_routes
from tests.test1.test_ancestor_helpers import _bound, _grant

helpers = ancestor_helpers.helpers
data = ancestor_helpers.data
provider_calls = ancestor_helpers.provider_calls
lookups = ancestor_helpers.lookups

BACKENDS = ["django.contrib.auth.backends.ModelBackend", "guardian.backends.ObjectPermissionBackend"]
ANONYMOUS_EDITOR = "tests.test1.test_link_access_matrix.AnonymousParentEditorBackend"


def test_child_link_adapter_is_gone():
    from crud_views.lib.view import CrudView
    from crud_views_guardian.lib.mixins import GuardianQuerysetMixin
    from crud_views_guardian.lib.views import GuardianCreateViewPermissionRequired

    for target in (CrudView, GuardianQuerysetMixin, GuardianCreateViewPermissionRequired):
        assert not hasattr(target, "_cv_child_link_has_access"), target
        assert hasattr(target, "_cv_link_permission"), target


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


@pytest.mark.django_db
def test_action_object_follows_request_definition(helpers, data, monkeypatch):
    actor = _user("link_action_objects")
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.pub, "change", data.penguin)
    _grant(actor, helpers.book, "view", data.book)
    for target, own, known, action_object in (
        (helpers.book.Detail, data.book, (data.penguin,), data.book),
        (helpers.book.List, None, (data.penguin,), data.penguin),
        (helpers.book.Create, None, (data.penguin,), data.penguin),
        (helpers.pub.List, None, (), None),
    ):
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        assert _link_access(target, actor, own, known) == _LINK_ALLOWED
        state.assert_called_once_with(actor, action_object)
        assert state.call_args.args[1] is action_object


@pytest.mark.django_db
def test_nested_guardian_create_cv_has_access_none_is_denied_with_parent_grant(helpers, data, provider_calls):
    actor = _user("link_create_none")
    _grant(actor, helpers.pub, "change", data.penguin)
    target = helpers.book.Create
    assert target.cv_has_access(actor, None) is False
    assert provider_calls == []
    assert _link_access(target, actor, None, (data.penguin,)) == _LINK_ALLOWED
    assert provider_calls == [(helpers.pub.vs.name, "app.change_publisher", data.penguin)]
    assert provider_calls[0][2] is data.penguin


@pytest.mark.django_db
def test_nested_guardian_create_seam_calls_cv_create_has_access(helpers, data, monkeypatch):
    actor = _user("link_create_seam")
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.pub, "change", data.penguin)
    view = _bound(helpers.book.List, actor, **{helpers.book.vs.parent.get_pk_name(): data.penguin.pk})
    assert view._cv_ancestor_guard() is None
    parent = view.cv_get_parent_object()
    target = helpers.book.Create
    create_access = Mock(wraps=target.cv_create_has_access)
    own = Mock(wraps=target.cv_has_access)
    monkeypatch.setattr(target, "cv_create_has_access", create_access)
    monkeypatch.setattr(target, "cv_has_access", own)

    for rendering_view in (None, view):
        create_access.reset_mock()
        assert _link_access(target, actor, None, (parent,), rendering_view=rendering_view) == _LINK_ALLOWED
        create_access.assert_called_once_with(actor, rendering_view, parent)
        assert create_access.call_args.args[1] is rendering_view
        assert create_access.call_args.args[2] is parent
        own.assert_not_called()


@pytest.mark.django_db
def test_rendering_view_reaches_only_the_create_hook(helpers, core_targets, data, monkeypatch):
    actor = _user("link_rendering_view", (Publisher, "view"))
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.book, "view", data.book)
    _grant(actor, helpers.book, "change", data.book)
    monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=True))
    view = _bound(
        helpers.note.List,
        actor,
        **{
            helpers.book.vs.parent.get_pk_name(): data.penguin.pk,
            helpers.note.vs.parent.get_pk_name(): data.book.pk,
        },
    )
    assert view._cv_ancestor_guard() is None
    book = view.cv_get_parent_object()
    publisher = ancestors._resolved_ancestor(view, helpers.pub.vs.name)
    calls = []
    originals = {cls: cls._ancestor_has_permission for cls in (ViewSet, GuardianViewSet)}

    for cls, original in originals.items():

        def provider(viewset, user, permission, obj, *, view, _original=original):
            calls.append((viewset.name, permission, obj, view))
            return _original(viewset, user, permission, obj, view=view)

        monkeypatch.setattr(cls, "_ancestor_has_permission", provider)

    assert _link_access(helpers.note.List, actor, None, (book, publisher), rendering_view=view) == _LINK_ALLOWED
    assert calls == [
        (helpers.pub.vs.name, "app.view_publisher", publisher, None),
        (helpers.book.vs.name, "app.view_book", book, None),
    ]

    create_access = Mock(wraps=helpers.note.Create.cv_create_has_access)
    monkeypatch.setattr(helpers.note.Create, "cv_create_has_access", create_access)
    calls.clear()
    assert _link_access(helpers.note.Create, actor, None, (book, publisher), rendering_view=view) == _LINK_ALLOWED
    create_access.assert_called_once_with(actor, view, book)
    assert create_access.call_args.args[1] is view
    assert calls == [
        (helpers.pub.vs.name, "app.view_publisher", publisher, None),
        (helpers.book.vs.name, "app.change_book", book, view),
    ]
    assert calls[1][3] is view

    nearest = Mock(wraps=ancestors._immediate_parent_access)
    monkeypatch.setattr(ancestors, "_immediate_parent_access", nearest)
    calls.clear()
    assert _link_access(core_targets.List, actor, None, (publisher,), rendering_view=view) == _LINK_ALLOWED
    nearest.assert_called_once_with(core_targets.List, actor, publisher)
    assert calls == [(core_targets.parent.name, "app.view_publisher", publisher, None)]


@pytest.mark.django_db
def test_no_decision_is_stored(helpers, data, provider_calls, monkeypatch):
    target = helpers.book.List
    actor = _user("link_fresh_grant")
    known = (data.penguin,)
    _grant(actor, helpers.pub, "view", data.penguin)
    target_before = dict(vars(target))
    user_before = dict(vars(actor))
    assert _link_access(target, actor, None, known) == _LINK_ALLOWED
    assert not {name for name in vars(target).keys() - target_before.keys() if "cv" in name}
    assert not {name for name in vars(actor).keys() - user_before.keys() if "cv" in name}
    remove_perm(helpers.pub.vs.permissions["view"], actor, data.penguin)
    actor = User.objects.get(pk=actor.pk)
    user_before = dict(vars(actor))
    assert _link_access(target, actor, None, known) == _LINK_PERMISSION
    assert provider_calls == [(helpers.pub.vs.name, "app.view_publisher", data.penguin)] * 2
    assert not {name for name in vars(target).keys() - target_before.keys() if "cv" in name}
    assert not {name for name in vars(actor).keys() - user_before.keys() if "cv" in name}

    # Hold these exact objects across both calls: re-fetching a user alone cannot rule out a stored answer.
    for changed, denied in (("gate", _LINK_PERMISSION), ("own", _LINK_PERMISSION), ("state", _LINK_STATE)):
        gate, own, state = Mock(return_value=True), Mock(return_value=True), Mock(return_value=True)
        changing = {"gate": gate, "own": own, "state": state}[changed]
        changing.side_effect = [True, False]
        with monkeypatch.context() as patch:
            for cls in (ViewSet, GuardianViewSet):
                patch.setattr(
                    cls, "_ancestor_has_permission", lambda self, *args, _gate=gate, **kwargs: _gate(*args, **kwargs)
                )
            patch.setattr(target, "cv_has_access", own)
            patch.setattr(target, "cv_action_enabled", state)
            assert _link_access(target, actor, None, known) == _LINK_ALLOWED
            assert _link_access(target, actor, None, known) == denied
        assert changing.call_count == 2
        assert gate.call_count == 2
        assert own.call_count == (1 if changed == "gate" else 2)
        assert state.call_count == (2 if changed == "state" else 1)
        for call in gate.call_args_list:
            assert call.args[0] is actor
            assert call.args[2] is known[0]


def test_link_ctx_maps_outcomes():
    assert _link_ctx(_LINK_ALLOWED) == {"cv_access": True, "cv_action_enabled": True}
    assert _link_ctx(_LINK_PERMISSION) == {"cv_access": False, "cv_action_enabled": True}
    assert _link_ctx(_LINK_STATE) == {"cv_access": True, "cv_action_enabled": False}
