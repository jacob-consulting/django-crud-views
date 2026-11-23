"""Direct contract of the private link check, independent of page rendering."""

from inspect import Parameter, signature
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import remove_perm

from crud_views.lib import ancestors, link_access
from crud_views.lib.link_access import (
    _LINK_ALLOWED,
    _LINK_PERMISSION,
    _LINK_STATE,
    _higher_ancestor_gates,
    _link_access,
    _link_ctx,
    _link_permission,
)
from crud_views.lib.view import ContextButton, ParentContextButton, SiblingContextButton
from crud_views.lib.views import CreateView, CreateViewParentMixin, DetailView, ListView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1 import test_ancestor_helpers as ancestor_helpers
from tests.test1 import test_guardian_parent_none as parent_none
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes
from tests.test1.test_ancestor_helpers import _bound, _grant
from tests.test1.test_guardian_child_link_visibility import parent_spy

helpers = ancestor_helpers.helpers
data = ancestor_helpers.data
provider_calls = ancestor_helpers.provider_calls
lookups = ancestor_helpers.lookups
pn = parent_none.pn

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
            Detail=type("LinkCoreDetail", (DetailView,), dict(common)),
            TopList=type("LinkCoreTopList", (ListView,), {"cv_viewset": parent}),
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


def _page_view(target, actor, parent, obj=None, *, guarded=True):
    """Bind a real page view and let its request guard resolve the URL parent."""
    kwargs = {target.cv_viewset.parent.get_pk_name(): parent.pk}
    if obj is not None:
        kwargs["pk"] = obj.pk
    view = _bound(target, actor, **kwargs)
    view.request.resolver_match = SimpleNamespace(url_name=target.cv_viewset.get_router_name(target.cv_key))
    if guarded:
        assert view._cv_ancestor_guard() is None
    return view


@pytest.mark.django_db
def test_page_link_ancestors_only_for_nested_guardian_create(helpers, core_targets, data):
    actor = _user("page_seam", (Publisher, "view"))
    _grant(actor, helpers.pub, "view", data.penguin)
    view = _page_view(helpers.book.Detail, actor, data.penguin, data.book)
    for target in (
        core_targets.List,
        core_targets.Create,
        helpers.book.List,
        helpers.book.Detail,
        helpers.pub.Create,
    ):
        seam = getattr(target, "_cv_page_link_ancestors", None)
        assert callable(seam), "the private page seam must exist"
        assert seam(view, data.book) is None
    known = helpers.book.Create._cv_page_link_ancestors(view, data.book)
    assert isinstance(known, tuple)
    assert len(known) == 1
    assert known[0] is view.cv_get_parent_object()


@pytest.mark.django_db
def test_page_link_ancestors_keep_documented_denials(helpers, data, django_assert_num_queries):
    actor = _user("page_seam_denials")
    _grant(actor, helpers.pub, "view", data.penguin)
    view = _page_view(helpers.book.Detail, actor, data.penguin, data.book)
    genre_view = _page_view(helpers.genre.Detail, actor, data.penguin, data.genre)
    parent = view.cv_get_parent_object()
    target = helpers.book.Create
    unguarded = _bound(helpers.book.Detail, actor, **view.kwargs)
    # The cached FK costs no query too: identity, not query count, proves the URL parent wins.
    mismatched = Book(pk=data.book.pk, title="Different FK", publisher=data.other)
    assert mismatched.publisher is data.other
    with django_assert_num_queries(0):
        for obj in (None, data.author, data.penguin):
            assert target._cv_page_link_ancestors(view, obj) == ()
        assert helpers.genre.Create._cv_page_link_ancestors(genre_view, data.genre) == ()
        assert target._cv_page_link_ancestors(unguarded, data.book) == ()
        for obj in (data.book, mismatched):
            known = target._cv_page_link_ancestors(view, obj)
            assert len(known) == 1
            assert known[0] is parent
            assert known[0] is not data.other


@pytest.mark.django_db
def test_page_action_object_follows_request_definition(helpers, data, django_assert_num_queries):
    actor = _user("page_action_object")
    _grant(actor, helpers.pub, "view", data.penguin)
    view = _page_view(helpers.book.Detail, actor, data.penguin, data.book)
    parent = view.cv_get_parent_object()
    unguarded = _bound(helpers.book.Detail, actor, **view.kwargs)
    action_object = getattr(link_access, "_page_action_object", None)
    assert callable(action_object), "the page action-object helper must exist"
    with django_assert_num_queries(0):
        assert action_object(view, helpers.book.Detail, data.book) is data.book
        assert action_object(view, helpers.book.List, data.book) is parent
        assert action_object(view, helpers.book.Create, data.book) is parent
        assert action_object(view, helpers.pub.List, data.book) is None
        assert action_object(unguarded, helpers.book.List, data.book) is None


@pytest.mark.django_db
def test_context_controls_keep_core_targets_on_their_code_path(core_targets, data, monkeypatch):
    actor = _user("page_core_controls", (Publisher, "view"))
    view = _page_view(core_targets.Detail, actor, data.penguin, data.book)
    parent = view.cv_get_parent_object()
    for target, key, own_obj, state_obj in (
        (core_targets.List, "home", None, parent),
        (core_targets.List, "list", None, parent),
        (core_targets.Detail, "detail", data.book, data.book),
        (core_targets.Create, "create", None, parent),
    ):
        with monkeypatch.context() as patch:
            gate = parent_spy(patch, target)
            calls = []
            own = Mock(side_effect=lambda *args, _calls=calls: _calls.append("own") or False)
            state = Mock(side_effect=lambda *args, _calls=calls: _calls.append("state") or True)
            patch.setattr(target, "cv_has_access", own)
            patch.setattr(target, "cv_action_enabled", state)
            ctx = view.cv_get_context(key, obj=data.book, user=actor, location="list" if key == "detail" else "context")
            assert ctx["cv_access"] is False
            assert ctx["cv_action_enabled"] is True
            assert calls == ["state", "own"]
            own.assert_called_once_with(actor, own_obj)
            state.assert_called_once_with(actor, state_obj)
            assert state.call_args.args[1] is state_obj
            gate.assert_not_called()


@pytest.mark.django_db
def test_context_controls_send_nested_guardian_create_through_the_check(helpers, data, monkeypatch):
    target = helpers.book.Create
    alias = ContextButton(key="new_book", key_target="create")
    monkeypatch.setattr(helpers.book.Detail, "cv_context_buttons", [alias])
    for permitted in (True, False):
        actor = _user(f"page_guardian_create_{permitted}")
        _grant(actor, helpers.pub, "view", data.penguin)
        _grant(actor, helpers.book, "view", data.book)
        if permitted:
            _grant(actor, helpers.pub, "change", data.penguin)
        view = _page_view(helpers.book.Detail, actor, data.penguin, data.book)
        parent = view.cv_get_parent_object()
        assert actor.has_perm("app.change_publisher", data.other) is False
        # Parent A is authorized, parent B is cached on the child and has no create grant.
        mismatched = Book(pk=data.book.pk, title="Different FK", publisher=data.other)
        assert mismatched.publisher is data.other
        for key in ("create", "new_book"):
            with monkeypatch.context() as patch:
                gate = parent_spy(patch, target)
                create_access = Mock(wraps=target.cv_create_has_access)
                own = Mock(wraps=target.cv_has_access)
                state = Mock(return_value=True)
                patch.setattr(target, "cv_create_has_access", create_access)
                patch.setattr(target, "cv_has_access", own)
                patch.setattr(target, "cv_action_enabled", state)
                with CaptureQueriesContext(connection) as queries:
                    ctx = view.cv_get_context(key, obj=mismatched, user=actor)
                assert ctx["cv_access"] is permitted
                assert ctx["cv_action_enabled"] is True
                create_access.assert_called_once_with(actor, None, parent)
                assert create_access.call_args.args[2] is parent
                gate.assert_called_once_with(actor, parent)
                assert gate.call_args.args[1] is parent
                own.assert_not_called()
                if permitted:
                    state.assert_called_once_with(actor, parent)
                else:
                    state.assert_not_called()
                for query in queries.captured_queries:
                    for clause in ("from", "join"):
                        assert f'{clause} "{Publisher._meta.db_table}"' not in query["sql"].lower()

    actor = _user("page_guardian_kept_hidden")
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.pub, "change", data.penguin)
    for page, obj, create in (
        (helpers.genre.Detail, data.genre, helpers.genre.Create),
        (helpers.book.Create, None, target),
    ):
        view = _page_view(page, actor, data.penguin, obj)
        with monkeypatch.context() as patch:
            patch.setattr(page, "cv_context_buttons", [alias])
            gate = parent_spy(patch, create)
            create_access = Mock(wraps=create.cv_create_has_access)
            state = Mock(return_value=True)
            patch.setattr(create, "cv_create_has_access", create_access)
            patch.setattr(create, "cv_action_enabled", state)
            for key in ("create", "new_book"):
                ctx = view.cv_get_context(key, obj=obj, user=actor)
                assert ctx["cv_access"] is False
                assert ctx["cv_action_enabled"] is True
            gate.assert_not_called()
            create_access.assert_not_called()
            state.assert_not_called()


@pytest.mark.django_db
def test_unguarded_view_keeps_core_controls(helpers, core_targets, data, monkeypatch):
    actor = _user("page_unguarded")
    view = _page_view(core_targets.Detail, actor, data.penguin, data.book, guarded=False)
    for target, key in ((core_targets.List, "home"), (core_targets.Create, "create")):
        with monkeypatch.context() as patch:
            gate = parent_spy(patch, target)
            own, state = Mock(return_value=True), Mock(return_value=True)
            patch.setattr(target, "cv_has_access", own)
            patch.setattr(target, "cv_action_enabled", state)
            ctx = view.cv_get_context(key, obj=data.book, user=actor)
            assert ctx["cv_access"] is True
            assert ctx["cv_action_enabled"] is True
            own.assert_called_once_with(actor, None)
            state.assert_called_once_with(actor, None if key == "home" else data.penguin)
            gate.assert_not_called()

    _grant(actor, helpers.pub, "change", data.penguin)
    view = _page_view(helpers.book.Detail, actor, data.penguin, data.book, guarded=False)
    gate = parent_spy(monkeypatch, helpers.book.Create)
    create_access = Mock(wraps=helpers.book.Create.cv_create_has_access)
    monkeypatch.setattr(helpers.book.Create, "cv_create_has_access", create_access)
    routes = ModuleType("unguarded_guardian_page_urls")
    routes.urlpatterns = helpers.book.vs.urlpatterns
    with override_settings(ROOT_URLCONF=routes):
        ctx = view.cv_get_context("create", obj=data.book, user=actor)
    assert ctx["cv_access"] is False
    assert ctx["cv_action_enabled"] is True
    create_access.assert_not_called()
    gate.assert_not_called()


@pytest.mark.django_db
def test_parent_and_sibling_button_state_object(helpers, data, monkeypatch):
    actor = _user("parent_sibling_objects", superuser=True)
    note = BookNote.objects.create(book=data.book, note="Nested")
    cases = [
        (
            helpers.book.Detail,
            data.book,
            helpers.pub.List,
            ParentContextButton(key="up", key_target="list"),
            None,
            None,
        ),
        (
            helpers.note.Detail,
            note,
            helpers.book.List,
            ParentContextButton(key="up", key_target="list"),
            None,
            data.penguin,
        ),
        (
            helpers.book.Detail,
            data.book,
            helpers.pub.Detail,
            ParentContextButton(key="up", key_target="detail"),
            data.penguin,
            data.penguin,
        ),
        (
            helpers.book.Detail,
            data.book,
            helpers.genre.List,
            SiblingContextButton(key="across", sibling_name=helpers.genre.vs.name),
            None,
            data.penguin,
        ),
    ]
    for page, obj, target, button, own_obj, state_obj in cases:
        kwargs = {helpers.book.vs.parent.get_pk_name(): data.penguin.pk, "pk": obj.pk}
        if page is helpers.note.Detail:
            kwargs[helpers.note.vs.parent.get_pk_name()] = data.book.pk
        response = _client(actor).get(_url(page.cv_viewset, page.cv_key, **kwargs))
        assert response.status_code == 200
        view = response.context["view"]
        with monkeypatch.context() as patch:
            gate = parent_spy(patch, target)
            own, state = Mock(return_value=True), Mock(return_value=True)
            patch.setattr(target, "cv_has_access", own)
            patch.setattr(target, "cv_action_enabled", state)
            ctx = button.get_context(view.cv_get_view_context(object=response.context["object"]))
            assert ctx["cv_access"] is True
            own.assert_called_once_with(actor, own_obj)
            state.assert_called_once_with(actor, state_obj)
            if state_obj is not None and not target.cv_object:
                assert state.call_args.args[1] is ancestors._resolved_ancestor(view, target.cv_viewset.parent.name)
            gate.assert_not_called()


@pytest.mark.django_db
def test_parent_button_reaches_nested_guardian_create_through_the_check(helpers, data, monkeypatch):
    target = helpers.book.Create
    note = BookNote.objects.create(book=data.book, note="Nested")
    button = ParentContextButton(key="parent_create", key_target="create", label_mode="both")
    for page in (helpers.note.Detail, helpers.note.List):
        monkeypatch.setattr(page, "cv_context_buttons", [button])
        monkeypatch.setattr(page, "cv_context_actions", ["parent_create"])
    for book_create_allowed in (True, False):
        actor = _user(f"parent_create_{book_create_allowed}")
        for family, obj in ((helpers.pub, data.penguin), (helpers.book, data.book), (helpers.note, note)):
            _grant(actor, family, "view", obj)
        _grant(
            actor,
            helpers.pub if book_create_allowed else helpers.book,
            "change",
            data.penguin if book_create_allowed else data.book,
        )
        for page in (helpers.note.Detail, helpers.note.List):
            with monkeypatch.context() as patch:
                gates = {cls: parent_spy(patch, cls) for cls in (target, helpers.note.Create)}
                create_access = Mock(wraps=target.cv_create_has_access)
                own, state = Mock(wraps=target.cv_has_access), Mock(return_value=True)
                patch.setattr(target, "cv_create_has_access", create_access)
                patch.setattr(target, "cv_has_access", own)
                patch.setattr(target, "cv_action_enabled", state)
                records = parent_none._record_contexts(patch, page)
                kwargs = {
                    helpers.book.vs.parent.get_pk_name(): data.penguin.pk,
                    helpers.note.vs.parent.get_pk_name(): data.book.pk,
                }
                if page is helpers.note.Detail:
                    kwargs["pk"] = note.pk
                response = _client(actor).get(_url(page.cv_viewset, page.cv_key, **kwargs))
                assert response.status_code == 200
                contexts = [ctx for key, ctx in records if key == "parent_create"]
                assert len(contexts) == 1
                ctx = contexts[0]
                parent = ancestors._resolved_ancestor(response.context["view"], helpers.pub.vs.name)
                create_access.assert_called_once_with(actor, None, parent)
                assert create_access.call_args.args[2] is parent
                own.assert_not_called()
                gates[target].assert_called_once_with(actor, parent)
                if book_create_allowed:
                    state.assert_called_once_with(actor, parent)
                else:
                    state.assert_not_called()
                if page is helpers.note.Detail:
                    assert ctx["cv_access"] is book_create_allowed
                    gates[helpers.note.Create].assert_not_called()
                else:
                    # L1 / D-34: stage 3 may change this overwrite; stage 1 keeps the page's own create answer.
                    assert ctx["cv_access"] is not book_create_allowed
                    gates[helpers.note.Create].assert_called_once_with(actor, data.book)
                assert ctx["cv_url"] == _url(
                    helpers.book.vs, "create", **{helpers.book.vs.parent.get_pk_name(): data.penguin.pk}
                )


@pytest.mark.django_db
@pytest.mark.parametrize("sibling_key", ["list", "create"])
@pytest.mark.parametrize("create_grant", [False, True])
def test_sibling_button_under_create_key_gets_page_create_result(pn, data, monkeypatch, sibling_key, create_grant):
    # L1 / D-34: stage 3 may change the override; stage 1 preserves the page's create answer and sibling URL.
    parent_none._strict_policy(pn, monkeypatch)
    actor = parent_none._child_page_actor(pn, data.penguin, data.book, create_grant=create_grant)
    target = pn.free_genre_vs.get_view_class(sibling_key)
    button = SiblingContextButton(key="create", sibling_name=pn.free_genre_vs.name, sibling_key=sibling_key)
    monkeypatch.setattr(pn.BookList, "cv_context_buttons", [button])
    monkeypatch.setattr(pn.BookList, "cv_context_actions", ["create"])
    page_gate, sibling_gate = parent_spy(monkeypatch, pn.BookCreate), parent_spy(monkeypatch, target)
    sibling_create = Mock(wraps=pn.FreeGenreCreate.cv_create_has_access)
    monkeypatch.setattr(pn.FreeGenreCreate, "cv_create_has_access", sibling_create)
    records = parent_none._record_contexts(monkeypatch, pn.BookList)
    response = _client(actor).get(parent_none._url(pn.book_vs, "list", data.penguin.pk))
    assert response.status_code == 200
    contexts = parent_none._create_contexts(records)
    assert len(contexts) == 1
    assert contexts[0]["cv_access"] is create_grant
    assert contexts[0]["cv_url"] == parent_none._url(pn.free_genre_vs, sibling_key, data.penguin.pk)
    page_gate.assert_called_once_with(actor, data.penguin)
    sibling_gate.assert_not_called()
    sibling_create.assert_not_called()
