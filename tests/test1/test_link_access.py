"""Direct contract of the private link check, independent of page rendering."""

import ast
from inspect import Parameter, signature
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.template import Context, Template
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from guardian.shortcuts import remove_perm

from crud_views.lib import ancestors
from crud_views.lib.link_access import (
    _LINK_ALLOWED,
    _LINK_PERMISSION,
    _LINK_STATE,
    _higher_ancestor_gates,
    _known_link_ancestors,
    _link_access,
    _link_ctx,
    _link_permission,
)
from crud_views.lib.navbar import NavBar, NavItem
from crud_views.lib.navbar import _build as _build_navbar
from crud_views.lib.view import CardAction, ChildContextButton, ContextButton, ParentContextButton, SiblingContextButton
from crud_views.lib.views import CreateView, CreateViewParentMixin, DetailView, ListView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views.templatetags.crud_views import cv_context_has_permission
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1 import test_ancestor_helpers as ancestor_helpers
from tests.test1 import test_guardian_parent_none as parent_none
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes
from tests.test1.test_ancestor_helpers import _bound, _grant
from tests.test1.test_guardian_child_link_visibility import parent_spy
from tests.test1.test_link_access_matrix import _actor, _get, _page_scene

helpers = ancestor_helpers.helpers
data = ancestor_helpers.data
provider_calls = ancestor_helpers.provider_calls
lookups = ancestor_helpers.lookups
pn = parent_none.pn

BACKENDS = ["django.contrib.auth.backends.ModelBackend", "guardian.backends.ObjectPermissionBackend"]
ANONYMOUS_EDITOR = "tests.test1.test_link_access_matrix.AnonymousParentEditorBackend"


@pytest.mark.django_db
@pytest.mark.parametrize("provider", ["model", "none"])
@pytest.mark.parametrize("kind", ["anonymous", "inactive", "inactive-superuser"])
def test_guardian_create_gate_before_override(helpers, data, monkeypatch, provider, kind):
    """Nested actor admission applies to direct default hooks and true overrides alike."""
    actor = AnonymousUser() if kind == "anonymous" else _user("create_actor", superuser=kind == "inactive-superuser")
    if kind != "anonymous":
        actor.is_active = False
    monkeypatch.setattr(helpers.cpub, "ancestor_policy", AncestorPolicy(provider=provider))
    target = helpers.core_book.Create
    state = Mock(return_value=True)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    with override_settings(AUTHENTICATION_BACKENDS=[*BACKENDS, ANONYMOUS_EDITOR]):
        if kind == "anonymous":
            assert actor.has_perm("app.change_publisher") is True
        assert target.cv_create_has_access(actor, None, data.penguin) is False
        create = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_create_has_access", create)
        assert _link_access(target, actor, known_ancestors=(data.penguin,)) == _LINK_PERMISSION
    create.assert_not_called()
    state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", ["child-button", "filter"])
def test_guardian_create_gate_before_override_at_consumers(helpers, data, monkeypatch, consumer):
    actor = _user("create_override_consumer")
    _grant(actor, helpers.pub, "view", data.penguin)
    if consumer == "child-button":
        view = _bound(helpers.pub.Detail, actor, pk=data.penguin.pk)
        view.object = data.penguin
        view.request.resolver_match = SimpleNamespace(url_name=helpers.pub.vs.get_router_name("detail"))
    else:
        view = _page_view(helpers.book.List, actor, data.penguin)
    target = helpers.book.Create
    create, state = Mock(return_value=True), Mock(return_value=True)
    monkeypatch.setattr(target, "cv_create_has_access", create)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    button = ChildContextButton(key="create", child_name=helpers.book.vs.name, child_key="create")

    def render():
        if consumer == "filter":
            return cv_context_has_permission(view, "create")
        return button.get_context(view.cv_get_view_context(object=data.penguin))["cv_access"]

    assert render() is False
    create.assert_not_called()
    state.assert_not_called()
    destination = _url(helpers.book.vs, "create", **{helpers.book.vs.parent.get_pk_name(): data.penguin.pk})
    assert _client(actor).get(destination).status_code == 403

    _grant(actor, helpers.pub, "change", data.penguin)
    fresh = User.objects.get(pk=actor.pk)
    view.request.user = fresh
    create.return_value = False
    assert render() is False
    parent = data.penguin if consumer == "child-button" else view._cv_ancestor_state.parent
    create.assert_called_once_with(fresh, None if consumer == "child-button" else view, parent)
    state.assert_not_called()
    assert _client(fresh).get(destination).status_code == 200

    create.reset_mock()
    state.reset_mock()
    create.return_value = True
    assert render() is True
    create.assert_called_once_with(fresh, None if consumer == "child-button" else view, parent)
    if consumer == "filter":
        state.assert_not_called()
    else:
        state.assert_called_once_with(fresh, data.penguin)


@pytest.mark.django_db
@pytest.mark.parametrize("protected", [False, True])
@pytest.mark.parametrize("kind", ["anonymous", "inactive", "inactive-superuser", "active"])
@pytest.mark.parametrize("shape", ["stock-object", "stock-list", "object-only", "queryset-only", "parent-only"])
def test_guardian_nested_actor_compositions(protected, kind, shape, monkeypatch):
    from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired
    from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired
    from crud_views_guardian.lib.mixins import (
        GuardianObjectPermissionMixin,
        GuardianParentPermissionMixin,
        GuardianQuerysetMixin,
    )
    from tests.test1.test_link_consumer_costs import consumer_actor, consumer_routes, consumer_world

    def routes(suffix):
        ns, families = consumer_routes(suffix, "guardian")
        ns.book.vs.ancestor_policy = AncestorPolicy(
            actions={"actor": AncestorPermissions(nearest="view", higher="view")}
        )
        bases = {
            "object-only": (GuardianObjectPermissionMixin, DetailViewPermissionRequired),
            "queryset-only": (GuardianQuerysetMixin, ListViewPermissionRequired),
            "parent-only": (GuardianParentPermissionMixin, CustomFormNoObjectViewPermissionRequired),
        }
        ns.Target = (
            ns.book.Detail
            if shape == "stock-object"
            else ns.book.List
            if shape == "stock-list"
            else type(
                "ActorTarget",
                bases[shape],
                {"cv_viewset": ns.book.vs, "cv_key": "actor", "cv_path": "actor", "cv_permission": "view"},
            )
        )
        return ns, families

    with isolated_routes(routes) as ns:
        world = consumer_world()
        actor = consumer_actor(ns, world)
        if kind == "anonymous":
            actor = AnonymousUser()
        elif kind != "active":
            actor.is_active = False
            actor.is_superuser = kind == "inactive-superuser"
        ns.pub.vs.ancestor_policy = AncestorPolicy(provider="guardian" if protected else "none")
        target = ns.Target
        own, state = Mock(wraps=target.cv_has_access), Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", own)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        obj = world.book if target.cv_object else None
        assert _link_access(target, actor, obj, (world.pub,)) == (
            _LINK_ALLOWED if kind == "active" else _LINK_PERMISSION
        )
        if kind == "active":
            own.assert_called_once_with(actor, obj)
            state.assert_called_once_with(actor, obj if target.cv_object else world.pub)
        else:
            own.assert_not_called()
            state.assert_not_called()
        # The top-level list keeps its independent anonymous eligibility.
        if kind == "anonymous":
            assert _link_access(ns.pub.List, actor) == _LINK_ALLOWED


def test_child_link_adapter_is_gone():
    from crud_views.lib.view import CrudView
    from crud_views_guardian.lib.mixins import GuardianQuerysetMixin
    from crud_views_guardian.lib.views import GuardianCreateViewPermissionRequired

    for target in (CrudView, GuardianQuerysetMixin, GuardianCreateViewPermissionRequired):
        assert not hasattr(target, "_cv_child_link_has_access"), target
        assert hasattr(target, "_cv_link_permission"), target


def test_removed_link_helpers_have_no_production_references():
    retired = {"_cv_page_link_ancestors", "_cv_action_enabled_for_context", "_cv_action_enabled_for_rendering"}
    source_root = Path(__file__).resolve().parents[2] / "src"
    source_files = sorted(source_root.rglob("*.py"))
    assert source_files, "Production sources are required for the retired-helper audit"
    references = []
    for path in source_files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in retired:
                references.append(f"{path.relative_to(source_root)}:{node.lineno}: definition {node.name}")
            elif isinstance(node, ast.Attribute) and node.attr in retired:
                references.append(f"{path.relative_to(source_root)}:{node.lineno}: access {node.attr}")
    assert references == [], "\n".join(references)


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

    # D-46: even a granting model backend cannot admit an anonymous nested Guardian create.
    monkeypatch.setattr(helpers.cpub, "ancestor_policy", AncestorPolicy())
    target = helpers.core_book.Create
    for actor, backends, outcome in (
        (inactive, granting, _LINK_PERMISSION),
        (anonymous, BACKENDS, _LINK_PERMISSION),
        (anonymous, granting, _LINK_PERMISSION),
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
    assert provider_calls == [(helpers.pub.vs.name, "app.change_publisher", data.penguin)] * 2
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
    assert not {
        name for name in vars(actor).keys() - user_before.keys() if "cv" in name and name != "_cv_guardian_checker"
    }
    remove_perm(helpers.pub.vs.permissions["view"], actor, data.penguin)
    actor = User.objects.get(pk=actor.pk)
    user_before = dict(vars(actor))
    assert _link_access(target, actor, None, known) == _LINK_PERMISSION
    assert provider_calls == [(helpers.pub.vs.name, "app.view_publisher", data.penguin)] * 2
    assert not {name for name in vars(target).keys() - target_before.keys() if "cv" in name}
    assert not {
        name for name in vars(actor).keys() - user_before.keys() if "cv" in name and name != "_cv_guardian_checker"
    }

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
def test_page_link_ancestors_align_every_target_directly(helpers, core_targets, data):
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
        assert not hasattr(target, "_cv_page_link_ancestors")
        known = _known_link_ancestors(target, view)
        assert len(known) == len(ancestors._walk_ancestors(target.cv_viewset))
    known = _known_link_ancestors(helpers.book.Create, view)
    assert isinstance(known, tuple)
    assert len(known) == 1
    assert known[0] is view.cv_get_parent_object()


@pytest.mark.django_db
def test_page_link_ancestors_use_known_route_without_relation_lookup(helpers, data, django_assert_num_queries):
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
        assert _known_link_ancestors(helpers.genre.Create, genre_view) == (genre_view._cv_ancestor_state.parent,)
        assert _known_link_ancestors(target, unguarded) == (None,)
        for obj in (None, data.author, data.penguin, data.book, mismatched):
            view.object = obj
            known = _known_link_ancestors(target, view)
            assert len(known) == 1
            assert known[0] is parent
            assert known[0] is not data.other


@pytest.mark.django_db
def test_context_controls_keep_core_targets_on_their_code_path(core_targets, data, monkeypatch):
    actor = _user("page_core_controls", (Publisher, "view"), (Publisher, "change"))
    view = _page_view(core_targets.Detail, actor, data.penguin, data.book)
    parent = view.cv_get_parent_object()
    for target, key, own_obj in (
        (core_targets.List, "home", None),
        (core_targets.List, "list", None),
        (core_targets.Detail, "detail", data.book),
        (core_targets.Create, "create", None),
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
            # Behaviors 1/2: every view key now gates permission before state.
            assert calls == ["own"]
            own.assert_called_once_with(actor, own_obj)
            state.assert_not_called()
            gate.assert_called_once_with(actor, parent)


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
                # D-49 gates before the hook; D-40 keeps its actual same-ViewSet page.
                if permitted:
                    create_access.assert_called_once_with(actor, view, parent)
                    assert create_access.call_args.args[2] is parent
                else:
                    create_access.assert_not_called()
                assert [call.args for call in gate.call_args_list] == [(actor, parent)] * (2 if permitted else 1)
                assert all(call.args[1] is parent for call in gate.call_args_list)
                own.assert_not_called()
                if permitted:
                    state.assert_called_once_with(actor, parent)
                else:
                    state.assert_not_called()
                for query in queries.captured_queries:
                    for clause in ("from", "join"):
                        assert f'{clause} "{Publisher._meta.db_table}"' not in query["sql"].lower()

    actor = _user("page_guardian_known_parent")
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
                assert ctx["cv_access"] is True
                assert ctx["cv_action_enabled"] is True
            parent = view._cv_ancestor_state.parent
            assert [call.args for call in gate.call_args_list] == [(actor, parent)] * 4
            assert [call.args for call in create_access.call_args_list] == [(actor, view, parent)] * 2
            assert [call.args for call in state.call_args_list] == [(actor, parent)] * 2


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
            # Behavior 3: missing guard parent denies both consumers before own/state.
            assert ctx["cv_access"] is False
            assert ctx["cv_action_enabled"] is True
            own.assert_not_called()
            state.assert_not_called()
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
            if target.cv_viewset.has_parent:
                gate.assert_called_once_with(actor, ancestors._resolved_ancestor(view, target.cv_viewset.parent.name))
            else:
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
                if book_create_allowed:
                    create_access.assert_called_once_with(actor, None, parent)
                    assert create_access.call_args.args[2] is parent
                else:
                    create_access.assert_not_called()
                own.assert_not_called()
                assert [call.args for call in gates[target].call_args_list] == [(actor, parent)] * (
                    2 if book_create_allowed else 1
                )
                if book_create_allowed:
                    state.assert_called_once_with(actor, parent)
                else:
                    state.assert_not_called()
                assert ctx["cv_access"] is book_create_allowed
                gates[helpers.note.Create].assert_not_called()
                assert ctx["cv_url"] == _url(
                    helpers.book.vs, "create", **{helpers.book.vs.parent.get_pk_name(): data.penguin.pk}
                )
                # Request authorization remains independent of the page's colliding create key.
                assert _client(actor).get(ctx["cv_url"]).status_code == (200 if book_create_allowed else 403)


@pytest.mark.django_db
@pytest.mark.parametrize("sibling_key", ["list", "create"])
@pytest.mark.parametrize("create_grant", [False, True])
def test_sibling_button_under_create_key_uses_actual_target(pn, data, monkeypatch, sibling_key, create_grant):
    # The sibling target uses its own operation's parent permission, without a page-create rewrite.
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
    assert contexts[0]["cv_access"] is (sibling_key == "list" or create_grant)
    assert contexts[0]["cv_url"] == parent_none._url(pn.free_genre_vs, sibling_key, data.penguin.pk)
    page_gate.assert_not_called()
    if sibling_key == "list":
        sibling_gate.assert_called_once_with(actor, response.context["view"]._cv_ancestor_state.parent)
        sibling_create.assert_not_called()
    else:
        parent = response.context["view"]._cv_ancestor_state.parent
        assert [call.args for call in sibling_gate.call_args_list] == [(actor, parent)] * (2 if create_grant else 1)
        if create_grant:
            sibling_create.assert_called_once_with(actor, None, parent)
        else:
            sibling_create.assert_not_called()

    # The actual sibling destination keeps its request rule, independent of the page create control.
    assert _client(actor).get(contexts[0]["cv_url"]).status_code == (
        200 if sibling_key == "list" or create_grant else 403
    )


@pytest.mark.django_db
def test_card_action_without_own_object_gets_none(pn, data, monkeypatch):
    actor = _user("card_objects", superuser=True)
    for page, row in ((pn.PublisherCard, data.penguin), (pn.BookCard, data.book)):
        monkeypatch.setattr(page, "cv_card_actions", [])
        monkeypatch.setattr(page, "cv_context_actions", [])
        kwargs = {pn.book_vs.parent.get_pk_name(): data.penguin.pk} if page is pn.BookCard else {}
        response = _client(actor).get(_url(page.cv_viewset, "card", **kwargs))
        assert response.status_code == 200
        view = response.context["view"]
        for key in ("list", "detail"):
            target = page.cv_viewset.get_view_class(key)
            with monkeypatch.context() as patch:
                gate = parent_spy(patch, target)
                own, state = Mock(return_value=True), Mock(return_value=True)
                patch.setattr(target, "cv_has_access", own)
                patch.setattr(target, "cv_action_enabled", state)
                ctx = view.cv_get_card_action_data(CardAction(key=key), row, actor)
                assert ctx["cv_access"] is True
                own.assert_called_once_with(actor, row if key == "detail" else None)
                state_obj = row if key == "detail" else view.cv_get_parent_object() if page is pn.BookCard else None
                state.assert_called_once_with(actor, state_obj)
                assert state.call_args.args[1] is state_obj
                if page is pn.BookCard:
                    gate.assert_called_once_with(actor, view._cv_ancestor_state.parent)
                else:
                    gate.assert_not_called()


@pytest.mark.django_db
def test_card_action_and_filter_reach_nested_guardian_create_through_the_check(pn, data, monkeypatch):
    parent_none._strict_policy(pn, monkeypatch)
    target = pn.BookCreate
    for page in (pn.BookCard, pn.BookDetail):
        monkeypatch.setattr(page, "cv_context_actions", [])
    monkeypatch.setattr(pn.BookCard, "cv_card_actions", [])
    for permitted in (True, False):
        actor = parent_none._child_page_actor(
            pn, data.penguin, data.book, create_grant=permitted, name=f"card_filter_{permitted}"
        )
        for key in ("card", "detail"):
            response = _client(actor).get(
                parent_none._url(pn.book_vs, key, data.penguin.pk, data.book.pk if key == "detail" else None)
            )
            assert response.status_code == 200
            view = response.context["view"]
            parent = view.cv_get_parent_object()
            with monkeypatch.context() as patch:
                gate = parent_spy(patch, target)
                own = Mock(wraps=target.cv_has_access)
                create_access = Mock(wraps=target.cv_create_has_access)
                state = Mock(return_value=False)
                patch.setattr(target, "cv_has_access", own)
                patch.setattr(target, "cv_create_has_access", create_access)
                patch.setattr(target, "cv_action_enabled", state)
                if key == "card":
                    ctx = view.cv_get_card_action_data(CardAction(key="create"), data.book, actor)
                    assert ctx["cv_access"] is permitted
                    assert ctx["cv_action_enabled"] is not permitted
                else:
                    assert cv_context_has_permission(view, "create") is permitted
                # D-49 gates before the hook; D-40 preserves the real same-ViewSet page.
                if permitted:
                    create_access.assert_called_once_with(actor, view, parent)
                    assert create_access.call_args.args[2] is parent
                else:
                    create_access.assert_not_called()
                assert [call.args for call in gate.call_args_list] == [(actor, parent)] * (2 if permitted else 1)
                own.assert_not_called()
                if permitted and key == "card":
                    state.assert_called_once_with(actor, parent)
                else:
                    state.assert_not_called()

    # The page renders under Read; an invalid nearest Write key still raises out of the filter.
    monkeypatch.setattr(
        pn.book_vs, "ancestor_policy", AncestorPolicy(write=AncestorPermissions(nearest="missing", higher="view"))
    )
    response = _client(actor).get(parent_none._url(pn.book_vs, "detail", data.penguin.pk, data.book.pk))
    assert response.status_code == 200
    with pytest.raises(ImproperlyConfigured, match="missing"):
        cv_context_has_permission(response.context["view"], "create")


@pytest.mark.django_db
def test_nested_guardian_create_filter_and_sibling_button_use_known_parent(helpers, data, monkeypatch):
    actor = _user("filter_sibling_denials")
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.pub, "change", data.penguin)
    _grant(actor, helpers.genre, "view", data.genre)
    for page, obj in ((helpers.book.List, None), (helpers.genre.Detail, data.genre)):
        kwargs = {helpers.book.vs.parent.get_pk_name(): data.penguin.pk}
        if obj is not None:
            kwargs["pk"] = obj.pk
        response = _client(actor).get(_url(page.cv_viewset, page.cv_key, **kwargs))
        assert response.status_code == 200
        view = response.context["view"]
        target = page.cv_viewset.get_view_class("create")
        with monkeypatch.context() as patch:
            gate = parent_spy(patch, target)
            own, create_access = Mock(wraps=target.cv_has_access), Mock(wraps=target.cv_create_has_access)
            patch.setattr(target, "cv_has_access", own)
            patch.setattr(target, "cv_create_has_access", create_access)
            assert cv_context_has_permission(view, "create") is True
            own.assert_not_called()
            parent = view._cv_ancestor_state.parent
            create_access.assert_called_once_with(actor, view, parent)
            assert [call.args for call in gate.call_args_list] == [(actor, parent)] * 2
        assert target.cv_has_access(actor, None) is False

    target = helpers.book.Create
    gate = parent_spy(monkeypatch, target)
    own, create_access = Mock(wraps=target.cv_has_access), Mock(wraps=target.cv_create_has_access)
    monkeypatch.setattr(target, "cv_has_access", own)
    monkeypatch.setattr(target, "cv_create_has_access", create_access)
    button = SiblingContextButton(key="new_book", sibling_name=helpers.book.vs.name, sibling_key="create")
    assert button.get_context(view.cv_get_view_context(object=data.genre))["cv_access"] is True
    own.assert_not_called()
    parent = view._cv_ancestor_state.parent
    create_access.assert_called_once_with(actor, None, parent)
    assert [call.args for call in gate.call_args_list] == [(actor, parent)] * 2


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["core", "guardian"])
@pytest.mark.parametrize("kind", ["object", "list", "create"])
def test_action_object_same_for_link_and_request(data, monkeypatch, composition, kind):
    from tests.test1.app import views

    if composition == "core":
        family = {"object": views.BookDetailView, "list": views.BookListView, "create": views.BookCreateView}
    else:
        family = {
            "object": views.GuardianBookDetailView,
            "list": views.GuardianBookListView,
            "create": views.GuardianBookCreateView,
        }
    target = family[kind]
    page = family["object" if kind == "list" else "list"]
    assert page is not target
    monkeypatch.setattr(target, "cv_context_actions", [])
    monkeypatch.setattr(
        page, "cv_context_actions", ["home"] if kind == "list" else ["create"] if kind == "create" else []
    )
    monkeypatch.setattr(family["list"], "cv_list_actions", ["detail"] if kind == "object" else [])
    actor = _user(f"parity_{composition}_{kind}", superuser=True)
    client = _client(actor)
    calls = []
    building_page = False
    original_context = target.get_context_data

    def get_context_data(self, *args, **kwargs):
        nonlocal building_page
        building_page = True
        return original_context(self, *args, **kwargs)

    def state(cls, user, obj=None):
        calls.append((building_page, obj))
        return True

    monkeypatch.setattr(target, "get_context_data", get_context_data)
    monkeypatch.setattr(target, "cv_action_enabled", classmethod(state))
    kwargs = {target.cv_viewset.parent.get_pk_name(): data.penguin.pk}
    target_kwargs = {**kwargs, "pk": data.book.pk} if kind == "object" else kwargs
    response = client.get(_url(target.cv_viewset, target.cv_key, **target_kwargs))
    assert response.status_code == 200
    assert building_page, "the target must build its page after enforcement"
    enforcement = [obj for rendering, obj in calls if not rendering]
    assert enforcement, "no request enforcement call was recorded"

    calls.clear()
    page_kwargs = {**kwargs, "pk": data.book.pk} if kind == "list" else kwargs
    response = client.get(_url(page.cv_viewset, page.cv_key, **page_kwargs))
    assert response.status_code == 200
    assert type(response.context["view"]) is page
    rendering = [obj for _, obj in calls]
    assert rendering, "no link rendering call was recorded"

    expected = data.book if kind == "object" else data.penguin
    for obj in [*enforcement, *rendering]:
        assert type(obj) is type(expected)
        assert obj.pk == expected.pk


@pytest.mark.django_db
@pytest.mark.parametrize("superuser", [False, True])
def test_nested_guardian_create_cv_has_access_fails_closed_for_every_argument(
    helpers, data, provider_calls, django_assert_num_queries, superuser
):
    actor = _user("narrow_create", superuser=superuser)
    _grant(actor, helpers.pub, "change", data.penguin)
    with django_assert_num_queries(0):
        for target, own_child in ((helpers.book.Create, data.book), (helpers.genre.Create, data.genre)):
            for obj in (None, data.penguin, own_child, data.author):
                assert target.cv_has_access(actor, obj) is False
    assert provider_calls == []


def _assert_control_own_access(control, target, expectation, calls):
    """Require this control's own observation, then validate every observed argument."""
    target_calls = [obj for called, obj in calls if called is target]
    if expectation == "asked":
        assert target_calls, f"{control}: target cv_has_access was not asked"
    else:
        assert expectation == "not asked"
        assert not target_calls, f"{control}: nested Guardian create cv_has_access was asked"
    for called, obj in calls:
        assert obj is None or (called.cv_object and isinstance(obj, called.cv_viewset.model)), (control, called, obj)


@pytest.mark.django_db
@pytest.mark.parametrize("composition", ["plain", "guardian"])
def test_no_package_call_site_passes_a_parent_to_cv_has_access(request, monkeypatch, composition):
    # Each control owns its recording: another control aimed at the same class cannot satisfy its row.
    with _page_scene(composition, "card", request, monkeypatch) as scene:
        actor = _actor("superuser", scene.parents, children=[scene.obj])
        child, parent, sibling = scene.vs, scene.parent, scene.sibling
        calls = []
        for viewset in (child, parent, sibling):
            for target in set(viewset.get_all_views().values()):
                original = target.cv_has_access.__func__

                def record(cls, user, obj=None, *, _original=original):
                    calls.append((cls, obj))
                    return _original(cls, user, obj)

                monkeypatch.setattr(target, "cv_has_access", classmethod(record))
                # Page rendering establishes request context; controls are built separately below.
                monkeypatch.setattr(target, "cv_context_actions", [])
                monkeypatch.setattr(target, "cv_list_actions", [], raising=False)
                monkeypatch.setattr(target, "cv_card_actions", [], raising=False)

        views = {}
        for viewset, page in (
            (parent, "detail"),
            (parent, "card"),
            (child, "list"),
            (child, "detail"),
            (child, "card"),
        ):
            page_cls = viewset.get_view_class(page)
            kwargs = {viewset.parent.get_pk_name(): scene.parents[0].pk} if viewset.has_parent else {}
            if page_cls.cv_object:
                kwargs[viewset.pk_name] = (scene.obj if viewset is child else scene.parents[0]).pk
            response = _get(actor, _url(viewset, page, **kwargs))
            assert response.status_code == 200
            views[viewset.name, page] = response.context["view"]

        create_expectation = "not asked" if composition == "guardian" else "asked"
        # control, page ViewSet/key, target ViewSet/key, expectation; each tuple is built and checked once.
        rows = [
            ("child-context", parent, "detail", child, "list", "asked"),
            ("child-context", parent, "detail", child, "create", create_expectation),
            ("card-child", parent, "card", child, "list", "asked"),
            ("card-child", parent, "card", child, "create", create_expectation),
            ("navbar-child", parent, "detail", child, "list", "asked"),
            ("navbar-child", parent, "detail", child, "create", create_expectation),
            ("list-create", child, "list", child, "create", create_expectation),
            ("row", child, "list", child, "detail", "asked"),
            ("row", child, "list", child, "update", "asked"),
            ("row", child, "list", child, "delete", "asked"),
            ("home", child, "detail", child, "list", "asked"),
            ("context", child, "detail", child, "detail", "asked"),
            ("context", child, "detail", child, "update", "asked"),
            ("context", child, "detail", child, "delete", "asked"),
            ("context", child, "detail", child, "create", create_expectation),
            ("card", child, "card", child, "create", create_expectation),
            ("card", child, "card", child, "detail", "asked"),
            ("parent", child, "detail", parent, "list", "asked"),
            ("parent", child, "detail", parent, "detail", "asked"),
            ("sibling", child, "detail", sibling, "list", "asked"),
            ("sibling", child, "detail", sibling, "create", create_expectation),
            ("filter", child, "detail", child, "create", create_expectation),
            ("filter", child, "detail", child, "update", "asked"),
        ]
        with pytest.raises(AssertionError, match="was not asked"):
            _assert_control_own_access("unbuilt control", child.get_view_class("detail"), "asked", [])

        for control, page_vs, page, target_vs, key, expectation in rows:
            view = views[page_vs.name, page]
            target = target_vs.get_view_class(key)
            row_name = f"{composition}/{control}/{key}"
            row_obj = scene.parents[0] if page_vs is parent else scene.obj
            calls.clear()
            if control == "navbar-child":
                view.cv_navbar = NavBar(viewset=parent.name, items=[NavItem(child=child.name, key=key)])
                result = _build_navbar(view)
                assert result and len(result["items"]) == 1, row_name
            elif control in {"card-child", "card"}:
                action = (
                    CardAction(child_name=child.name, child_key=key) if control == "card-child" else CardAction(key=key)
                )
                result = view.cv_get_card_action_data(action, row_obj, actor)
            elif control == "filter":
                template = Template('{% load crud_views %}{{ view|cv_context_has_permission:"' + key + '" }}')
                result = template.render(Context({"view": view, "request": view.request}))
                assert result in {"True", "False"}, row_name
            else:
                action_key = key
                if control == "child-context":
                    action_key = f"child_{key}"
                    view.cv_context_buttons = [
                        ChildContextButton(key=action_key, child_name=child.name, child_key=key, label_mode="label")
                    ]
                elif control == "parent":
                    action_key = f"parent_{key}"
                    view.cv_context_buttons = [ParentContextButton(key=action_key, key_target=key, label_mode="label")]
                elif control == "sibling":
                    action_key = f"sibling_{key}"
                    assert not child.is_view_registered(action_key)
                    view.cv_context_buttons = [
                        SiblingContextButton(
                            key=action_key, sibling_name=sibling.name, sibling_key=key, label_mode="label"
                        )
                    ]
                elif control == "home":
                    action_key = "home"
                result = view.cv_get_context(
                    action_key,
                    obj=None if control == "list-create" else row_obj,
                    user=actor,
                    location="list" if control == "row" else "context",
                )
            assert result, f"{row_name}: control was not built"
            _assert_control_own_access(row_name, target, expectation, calls)
