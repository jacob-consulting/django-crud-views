"""Public link decisions from caller-owned objects, without a request or rendering view."""

from enum import Enum
from inspect import Parameter, signature
from pathlib import Path
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext, isolate_apps

from crud_views.lib import link_access
from crud_views.lib.resource import ResourceViewMixin
from crud_views.lib.views import DetailView, ListView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1 import test_ancestor_actors as actor_tests
from tests.test1 import test_ancestor_auth_databases as auth_database_tests
from tests.test1 import test_ancestor_resources as resource_tests
from tests.test1 import test_link_access as private_link_tests
from tests.test1.app.models import Author, Book, BookNote, Car, Publisher, PublisherProxy, Truck, Vehicle
from tests.test1.test_ancestor_authorization import _user, isolated_routes
from tests.test1.test_ancestor_docs import _fence
from tests.test1.test_ancestor_helpers import _grant
from tests.test1.test_ancestor_resources import NoteChainFile, PublisherChainFile, TopFile, _ChainFile

core_targets = private_link_tests.core_targets
data = private_link_tests.data
helpers = private_link_tests.helpers
chains = resource_tests.chains
provider_calls = private_link_tests.provider_calls
lookups = private_link_tests.lookups
resource_events = resource_tests.events
undeclared_custom = actor_tests.undeclared_custom
adb = auth_database_tests.adb
auth_world = auth_database_tests.world
routes = auth_database_tests.routes

LINK_ACCESS_MD = Path(__file__).resolve().parents[2] / "docs" / "reference" / "link_access.md"


def test_public_signature_and_enum():
    check = getattr(link_access, "check_link_access", None)
    assert callable(check), "check_link_access must be importable from crud_views.lib.link_access"
    result_type = getattr(link_access, "LinkAccess", None)
    assert isinstance(result_type, type) and issubclass(result_type, Enum)
    assert [(p.name, p.kind, p.default) for p in signature(check).parameters.values()] == [
        ("target", Parameter.POSITIONAL_OR_KEYWORD, Parameter.empty),
        ("user", Parameter.POSITIONAL_OR_KEYWORD, Parameter.empty),
        ("obj", Parameter.KEYWORD_ONLY, None),
        ("known_ancestors", Parameter.KEYWORD_ONLY, ()),
    ]
    assert list(result_type.__members__) == ["ALLOWED", "DENIED_PERMISSION", "DENIED_STATE"]
    assert len(set(result_type)) == 3
    assert [bool(member) for member in result_type] == [True, False, False]
    for member in result_type:
        assert not isinstance(member, str)
        assert member != member.value


@pytest.mark.django_db
def test_public_object_tracer(core_targets, data):
    assert hasattr(link_access, "check_link_access"), "the documented public callable must exist"
    actor = _user("public_object_tracer", (Publisher, "view"))
    namespace = {"TargetView": core_targets.Detail, "user": actor, "book": data.book, "publisher": data.penguin}
    source = _fence(LINK_ACCESS_MD, "## Object target")
    exec(compile(source, f"{LINK_ACCESS_MD}:Object target", "exec"), namespace)
    assert namespace["result"] is link_access.LinkAccess.ALLOWED


@pytest.fixture(params=["ordinary", "anonymous", "superuser"])
def public_actor(request):
    if request.param == "anonymous":
        return AnonymousUser()
    return User(username="public_actor", is_active=True, is_superuser=request.param == "superuser")


def _watch_authorization(monkeypatch, target):
    """Invalid inputs must stop before either delegation or an authorization/state hook."""
    calls = [Mock(return_value=link_access._LINK_ALLOWED)]
    monkeypatch.setattr(link_access, "_link_access", calls[0])
    for name in ("_cv_link_permission", "cv_has_access", "cv_create_has_access", "cv_action_enabled"):
        if hasattr(target, name):
            hook = Mock(return_value=True)
            monkeypatch.setattr(target, name, hook)
            calls.append(hook)
    return calls


@pytest.mark.parametrize(
    "case",
    [
        "ancestor-wrong-nearest",
        "ancestor-wrong-behind-nearest-hole",
        "ancestor-wrong-behind-interior-hole",
        "own-wrong-model",
        "own-resource-for-model",
        "own-wrong-resource",
        "own-model-for-resource",
        "own-dict-for-resource",
        "missing-own-model",
        "missing-own-resource",
        "unexpected-own-list",
        "unexpected-own-create",
        "excess-trailing-none",
        "excess-all-none",
        "top-level-object-slot",
        "top-level-none-slot",
    ],
)
def test_public_validation_before_authorization(core_targets, chains, public_actor, monkeypatch, case):
    leaf = chains.depth[3].vs["plain"].get_view_class("detail")
    resource = NoteChainFile(key="known")
    book, publisher, note = Book(), Publisher(), BookNote()
    target, obj, known = {
        "ancestor-wrong-nearest": (core_targets.Detail, book, [Author()]),
        "ancestor-wrong-behind-nearest-hole": (leaf, resource, [None, publisher]),
        "ancestor-wrong-behind-interior-hole": (leaf, resource, [note, None, book]),
        "own-wrong-model": (core_targets.Detail, publisher, [publisher]),
        "own-resource-for-model": (core_targets.Detail, resource, [publisher]),
        "own-wrong-resource": (leaf, TopFile(key="other"), [note]),
        "own-model-for-resource": (leaf, book, [note]),
        "own-dict-for-resource": (leaf, {"key": "known"}, [note]),
        "missing-own-model": (core_targets.Detail, None, [publisher]),
        "missing-own-resource": (leaf, None, [note]),
        "unexpected-own-list": (core_targets.List, book, [publisher]),
        "unexpected-own-create": (core_targets.Create, book, [publisher]),
        "excess-trailing-none": (core_targets.Detail, book, [publisher, None]),
        "excess-all-none": (core_targets.List, None, [None, None]),
        "top-level-object-slot": (core_targets.TopList, None, [publisher]),
        "top-level-none-slot": (core_targets.TopList, None, [None]),
    }[case]
    calls = _watch_authorization(monkeypatch, target)
    with pytest.raises(ImproperlyConfigured, match=r"^check_link_access"):
        link_access.check_link_access(target, public_actor, obj=obj, known_ancestors=known)
    for call in calls:
        call.assert_not_called()


@pytest.mark.parametrize("case", ["top-instance", "nested-instance", "higher-instance", "none", "object", "string"])
def test_public_invalid_target(core_targets, helpers, public_actor, monkeypatch, case):
    target_class = {
        "top-instance": core_targets.TopList,
        "nested-instance": core_targets.List,
        "higher-instance": helpers.note.List,
    }.get(case, core_targets.TopList)
    monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=True))
    target = target_class() if case.endswith("instance") else {"none": None, "object": object(), "string": "view"}[case]
    known = [Book(), Publisher()] if case == "higher-instance" else [Publisher()] if case == "nested-instance" else []
    calls = _watch_authorization(monkeypatch, target_class)
    with pytest.raises(ImproperlyConfigured, match=r"^check_link_access.*class"):
        link_access.check_link_access(target, public_actor, known_ancestors=known)
    for call in calls:
        call.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["none", "model", "empty-string", "string", "set", "dict", "generator", "queryset"])
def test_public_invalid_ancestor_container(core_targets, public_actor, monkeypatch, django_assert_num_queries, case):
    consumed = []

    def ancestors():
        consumed.append(True)
        yield Publisher()

    queryset = Publisher.objects.all()
    known = {
        "none": None,
        "model": Publisher(),
        "empty-string": "",
        "string": "publisher",
        "set": {None},
        "dict": {0: Publisher()},
        "generator": ancestors(),
        "queryset": queryset,
    }[case]
    calls = _watch_authorization(monkeypatch, core_targets.List)
    assert queryset._result_cache is None
    with django_assert_num_queries(0), pytest.raises(ImproperlyConfigured, match=r"^check_link_access.*list or tuple"):
        link_access.check_link_access(core_targets.List, public_actor, known_ancestors=known)
    assert queryset._result_cache is None
    assert consumed == []
    for call in calls:
        call.assert_not_called()


@pytest.mark.parametrize("attributes", [{}, {"cv_viewset": None}], ids=["absent", "none"])
def test_public_missing_viewset(public_actor, monkeypatch, attributes):
    target = type("UnconfiguredTarget", (), attributes)
    calls = _watch_authorization(monkeypatch, target)
    with pytest.raises(ImproperlyConfigured, match=r"^check_link_access.*ViewSet"):
        link_access.check_link_access(target, public_actor)
    calls[0].assert_not_called()


@pytest.mark.parametrize("case", ["missing", "cycle", "resource-parent"])
def test_public_declared_ancestry_errors(core_targets, chains, public_actor, monkeypatch, case):
    if case == "missing":
        parent = ParentViewSet(name="public_missing_parent")
        message = "not registered"
    elif case == "cycle":
        parent = ParentViewSet(name=core_targets.vs.name)
        message = "ancestry cycle"
    else:
        parent = ParentViewSet(name=chains.top.name)
        message = "Resource-based"
    monkeypatch.setattr(core_targets.parent, "parent", parent)
    calls = _watch_authorization(monkeypatch, core_targets.List)
    with pytest.raises(ImproperlyConfigured, match=message) as error:
        link_access.check_link_access(core_targets.List, public_actor, known_ancestors=[Publisher()])
    assert not str(error.value).startswith("check_link_access")
    assert error.value.kind == {"resource-parent": "resource_parent"}.get(case, case)
    for call in calls:
        call.assert_not_called()


@pytest.fixture
def publisher_child():
    with isolate_apps("tests.test1.app"):

        class PublicLinkPublisherChild(Publisher):
            class Meta:
                app_label = "app"

        yield PublicLinkPublisherChild


@pytest.mark.parametrize(
    ("case", "location", "accepted"),
    [
        (case, location, accepted)
        for location in ("own", "ancestor")
        for case, accepted in (
            ("exact", True),
            ("proxy", True),
            ("concrete-for-proxy", True),
            ("mti", True),
            ("polymorphic", True),
            ("narrow-base", False),
            ("narrow-sibling", False),
            ("narrow-mti-base", False),
            ("unrelated", False),
        )
    ]
    + [
        ("resource", "own", True),
        ("resource-subclass", "own", True),
        ("resource-sibling", "own", False),
        ("resource-base", "own", False),
    ],
    ids=lambda value: str(value),
)
def test_public_compatible_instances(publisher_child, monkeypatch, case, location, accepted):
    model, supplied = {
        "exact": (Publisher, Publisher()),
        "proxy": (Publisher, PublisherProxy()),
        "concrete-for-proxy": (PublisherProxy, Publisher()),
        "mti": (Publisher, publisher_child()),
        "polymorphic": (Vehicle, Car()),
        "narrow-base": (Car, Vehicle()),
        "narrow-sibling": (Car, Truck()),
        "narrow-mti-base": (publisher_child, Publisher()),
        "unrelated": (Publisher, Author()),
        "resource": (_ChainFile, _ChainFile(key="known")),
        "resource-subclass": (_ChainFile, TopFile(key="known")),
        "resource-sibling": (TopFile, PublisherChainFile(key="known")),
        "resource-base": (TopFile, _ChainFile(key="known")),
    }[case]

    def build(suffix):
        declared = ViewSet(model=model, name=f"publictype{suffix}", ancestor_policy=AncestorPolicy(provider="none"))
        if location == "own":
            bases = (ResourceViewMixin, DetailView) if declared.is_resource else (DetailView,)
            target = type("PublicTypeDetail", bases, {"cv_viewset": declared, "cv_context_actions": []})
            return target, [declared]
        child = ViewSet(model=Book, name=f"publicchild{suffix}", parent=ParentViewSet(name=declared.name))
        target = type("PublicTypeList", (ListView,), {"cv_viewset": child, "cv_context_actions": []})
        return target, [declared, child]

    with isolated_routes(build) as target:
        actor = User(username="compatible", is_active=True)
        own = supplied if location == "own" else None
        known = [supplied] if location == "ancestor" else []
        delegate = Mock(wraps=link_access._link_access)
        monkeypatch.setattr(link_access, "_link_access", delegate)
        if accepted:
            assert (
                link_access.check_link_access(target, actor, obj=own, known_ancestors=known)
                is link_access.LinkAccess.ALLOWED
            )
            delegate.assert_called_once_with(target, actor, own, known, rendering_view=None)
            assert delegate.call_args.args[2] is own
            assert delegate.call_args.args[3] is known
        else:
            with pytest.raises(ImproperlyConfigured, match=r"^check_link_access"):
                link_access.check_link_access(target, actor, obj=own, known_ancestors=known)
            delegate.assert_not_called()


@pytest.mark.parametrize("model", [Publisher, Author], ids=["unset-integer-pk", "default-uuid-pk"])
def test_public_unsaved_own_objects(model, monkeypatch):
    obj = model()
    assert obj._state.adding
    assert (obj.pk is None) is (model is Publisher)

    def build(suffix):
        vs = ViewSet(model=model, name=f"publicunsaved{suffix}")
        return type("PublicUnsavedDetail", (DetailView,), {"cv_viewset": vs, "cv_context_actions": []}), [vs]

    with isolated_routes(build) as target:
        actor = User(username="unsaved")
        assert link_access.check_link_access(target, actor, obj=obj) is link_access.LinkAccess.ALLOWED
        permission = Mock(return_value=True)
        state = Mock(return_value=True)
        monkeypatch.setattr(target, "cv_has_access", permission)
        monkeypatch.setattr(target, "cv_action_enabled", state)
        save, refresh = (
            Mock(side_effect=AssertionError("must not persist")),
            Mock(side_effect=AssertionError("must not load")),
        )
        monkeypatch.setattr(obj, "save", save)
        monkeypatch.setattr(obj, "refresh_from_db", refresh)
        assert link_access.check_link_access(target, actor, obj=obj) is link_access.LinkAccess.ALLOWED
        assert permission.call_args.args[1] is obj
        assert state.call_args.args[1] is obj
        failure = RuntimeError("project hook cannot handle this unsaved object")
        state.side_effect = failure
        with pytest.raises(RuntimeError) as error:
            link_access.check_link_access(target, actor, obj=obj)
        assert error.value is failure
        assert obj._state.adding
        assert (obj.pk is None) is (model is Publisher)
        save.assert_not_called()
        refresh.assert_not_called()


@pytest.mark.parametrize("container", [list, tuple], ids=["list", "tuple"])
@pytest.mark.parametrize("outcome", ["allowed", "permission", "state"])
def test_public_delegation_and_error_propagation(core_targets, monkeypatch, container, outcome):
    obj, parent, actor = Book(), Publisher(), User(username="delegate")
    known = container([parent])
    delegate = Mock(return_value=outcome)
    monkeypatch.setattr(link_access, "_link_access", delegate)
    result = link_access.check_link_access(target=core_targets.Detail, user=actor, obj=obj, known_ancestors=known)
    assert (
        result
        is {
            "allowed": link_access.LinkAccess.ALLOWED,
            "permission": link_access.LinkAccess.DENIED_PERMISSION,
            "state": link_access.LinkAccess.DENIED_STATE,
        }[outcome]
    )
    delegate.assert_called_once_with(core_targets.Detail, actor, obj, known, rendering_view=None)
    assert delegate.call_args.args[2] is obj
    assert delegate.call_args.args[3] is known
    assert delegate.call_args.args[3][0] is parent
    failure = RuntimeError("authorization backend failed")
    delegate.side_effect = failure
    with pytest.raises(RuntimeError) as error:
        link_access.check_link_access(core_targets.Detail, actor, obj=obj, known_ancestors=known)
    assert error.value is failure


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.parametrize("outcome", list(link_access.LinkAccess))
def test_public_direct_outcomes(core_targets, helpers, data, monkeypatch, family, outcome):
    target = core_targets.Detail if family == "core" else helpers.book.Detail
    actor = _user("public_outcome", *((Publisher, "view"),) if family == "core" else ())
    if family == "guardian":
        _grant(actor, helpers.pub, "view", data.penguin)
        if outcome is not link_access.LinkAccess.DENIED_PERMISSION:
            _grant(actor, helpers.book, "view", data.book)
    elif outcome is link_access.LinkAccess.DENIED_PERMISSION:
        monkeypatch.setattr(target, "cv_has_access", Mock(return_value=False))
    state = Mock(return_value=outcome is not link_access.LinkAccess.DENIED_STATE)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    assert link_access.check_link_access(target, actor, obj=data.book, known_ancestors=[data.penguin]) is outcome
    if outcome is link_access.LinkAccess.DENIED_PERMISSION:
        state.assert_not_called()
    else:
        state.assert_called_once_with(actor, data.book)
        assert state.call_args.args[1] is data.book


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.parametrize("shape", ["detail", "list", "create", "top-list"])
@pytest.mark.parametrize("denial", [None, "parent", "own"])
def test_public_state_object_and_order(core_targets, helpers, data, monkeypatch, family, shape, denial):
    actor = _user("public_order", (Publisher, "view"), (Publisher, "change"))
    for action in ("view", "change"):
        _grant(actor, helpers.pub, action, data.penguin)
    _grant(actor, helpers.book, "view", data.book)
    nested = shape != "top-list"
    targets = core_targets if family == "core" else helpers.book
    target = (
        getattr(targets, shape.title()) if nested else core_targets.TopList if family == "core" else helpers.pub.List
    )
    parent = core_targets.parent if family == "core" else helpers.pub.vs
    obj = data.book if shape == "detail" else None
    known = [data.penguin] if nested else []
    action_obj = obj if obj is not None else data.penguin if nested else None
    events = []
    parent_hook = parent._ancestor_has_permission

    def check_parent(*args, **kwargs):
        events.append("parent")
        return False if denial == "parent" else parent_hook(*args, **kwargs)

    monkeypatch.setattr(parent, "_ancestor_has_permission", check_parent)
    own_name = "cv_create_has_access" if family == "guardian" and shape == "create" else "cv_has_access"
    own_hook = getattr(target, own_name)

    def check_own(*args):
        events.append("own")
        return False if denial == "own" else own_hook(*args)

    own = Mock(side_effect=check_own)
    state = Mock(side_effect=lambda *args: events.append("state") or True)
    monkeypatch.setattr(target, own_name, own)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    denied = denial == "own" or (denial == "parent" and nested)
    expected = link_access.LinkAccess.DENIED_PERMISSION if denied else link_access.LinkAccess.ALLOWED
    assert link_access.check_link_access(target, actor, obj=obj, known_ancestors=known) is expected
    if nested and denial == "parent":
        assert events == ["parent"]
        own.assert_not_called()
    else:
        assert events[0] == ("parent" if nested else "own")
        assert events.count("own") == 1
        if own_name == "cv_create_has_access":
            own.assert_called_once_with(actor, None, data.penguin)
            assert own.call_args.args[2] is data.penguin
        else:
            own.assert_called_once_with(actor, obj)
    if denied:
        state.assert_not_called()
    else:
        assert events[-1] == "state"
        state.assert_called_once_with(actor, action_obj)
        assert state.call_args.args[1] is action_obj


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["higher-denied", "immediate-denied", "override-false", "allowed"])
def test_public_guardian_create_admission(helpers, data, monkeypatch, case):
    actor = _user("public_create_admission")
    target = helpers.note.Create
    monkeypatch.setattr(helpers.note.vs, "ancestor_policy", AncestorPolicy(cascade=True))
    if case != "higher-denied":
        _grant(actor, helpers.pub, "view", data.penguin)
    if case != "immediate-denied":
        _grant(actor, helpers.book, "change", data.book)
    create = Mock(return_value=case != "override-false")
    state = Mock(return_value=True)
    monkeypatch.setattr(target, "cv_create_has_access", create)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    expected = link_access.LinkAccess.ALLOWED if case == "allowed" else link_access.LinkAccess.DENIED_PERMISSION
    assert link_access.check_link_access(target, actor, known_ancestors=[data.book, data.penguin]) is expected
    if case.endswith("denied"):
        create.assert_not_called()
    else:
        create.assert_called_once_with(actor, None, data.book)
        assert create.call_args.args[2] is data.book
    if case == "allowed":
        state.assert_called_once_with(actor, data.book)
    else:
        state.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("provider", ["model", "none"])
@pytest.mark.parametrize("kind", ["anonymous", "inactive", "inactive-superuser", "active"])
@pytest.mark.parametrize("shape", ["create", "list", "detail"])
def test_public_guardian_nested_actor_rule(helpers, data, monkeypatch, provider, kind, shape):
    actor = (
        AnonymousUser()
        if kind == "anonymous"
        else _user(
            "public_actor_rule", (Publisher, "view"), (Publisher, "change"), superuser=kind == "inactive-superuser"
        )
    )
    if kind not in ("anonymous", "active"):
        actor.is_active = False
    monkeypatch.setattr(helpers.cpub, "ancestor_policy", AncestorPolicy(provider=provider))
    target = getattr(helpers.core_book, shape.title())
    hook_name = "cv_create_has_access" if shape == "create" else "cv_has_access"
    hook, state = Mock(return_value=True), Mock(return_value=True)
    monkeypatch.setattr(target, hook_name, hook)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    obj = data.book if shape == "detail" else None
    with override_settings(AUTHENTICATION_BACKENDS=[*private_link_tests.BACKENDS, private_link_tests.ANONYMOUS_EDITOR]):
        if kind == "anonymous":
            assert actor.has_perm("app.change_publisher") is True
        expected = link_access.LinkAccess.ALLOWED if kind == "active" else link_access.LinkAccess.DENIED_PERMISSION
        assert link_access.check_link_access(target, actor, obj=obj, known_ancestors=[data.penguin]) is expected
    if kind == "active":
        hook.assert_called_once_with(*(actor, None, data.penguin) if shape == "create" else (actor, obj))
        state.assert_called_once_with(actor, obj if shape == "detail" else data.penguin)
    else:
        hook.assert_not_called()
        state.assert_not_called()


@pytest.mark.django_db
def test_public_top_level_guardian_anonymous_list(helpers, monkeypatch):
    actor = AnonymousUser()
    state = Mock(return_value=True)
    monkeypatch.setattr(helpers.pub.List, "cv_action_enabled", state)
    assert link_access.check_link_access(helpers.pub.List, actor) is link_access.LinkAccess.ALLOWED
    state.assert_called_once_with(actor, None)


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
def test_public_repeated_decisions(core_targets, helpers, data, monkeypatch, family):
    actor = _user("public_repeat", (Publisher, "view"))
    _grant(actor, helpers.pub, "view", data.penguin)
    _grant(actor, helpers.book, "view", data.book)
    target = core_targets.Detail if family == "core" else helpers.book.Detail
    own = Mock(wraps=target.cv_has_access)
    state = Mock(return_value=True)
    monkeypatch.setattr(target, "cv_has_access", own)
    monkeypatch.setattr(target, "cv_action_enabled", state)

    def decide():
        return link_access.check_link_access(target, actor, obj=data.book, known_ancestors=[data.penguin])

    assert decide() is link_access.LinkAccess.ALLOWED
    checker = getattr(actor, "_cv_guardian_checker", None)
    state.return_value = False
    assert decide() is link_access.LinkAccess.DENIED_STATE
    own.return_value = False
    assert decide() is link_access.LinkAccess.DENIED_PERMISSION
    own.return_value = True
    state.return_value = True
    assert decide() is link_access.LinkAccess.ALLOWED
    assert own.call_count == 4
    assert state.call_count == 3
    if family == "guardian":
        assert checker is not None
        assert actor._cv_guardian_checker is checker


@pytest.mark.django_db
@pytest.mark.parametrize("container", [list, tuple], ids=["list", "tuple"])
@pytest.mark.parametrize("cascade", [False, True])
@pytest.mark.parametrize("shape", ["empty", "missing-nearest", "short", "unknown-higher", "interior-hole", "full"])
def test_public_ancestor_alignment(chains, data, provider_calls, monkeypatch, container, cascade, shape):
    target = chains.depth[3].vs["plain"].get_view_class("detail")
    actor = _user("public_alignment", (BookNote, "view"), (Book, "change"), (Publisher, "change"))
    note = BookNote.objects.create(book=data.book, note="known")
    obj = NoteChainFile(key="supplied")
    monkeypatch.setattr(
        target.cv_viewset,
        "ancestor_policy",
        AncestorPolicy(cascade=cascade, read=AncestorPermissions(nearest="view", higher="change")),
    )
    known = container(
        {
            "empty": [],
            "missing-nearest": [None, None, data.penguin],
            "short": [note],
            "unknown-higher": [note, None],
            "interior-hole": [note, None, data.penguin],
            "full": [note, data.book, data.penguin],
        }[shape]
    )
    missing = shape in ("empty", "missing-nearest")
    state = Mock(return_value=True)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    expected = link_access.LinkAccess.DENIED_PERMISSION if missing else link_access.LinkAccess.ALLOWED
    assert link_access.check_link_access(target, actor, obj=obj, known_ancestors=known) is expected
    expected_calls = []
    if not missing:
        if cascade and shape in ("interior-hole", "full"):
            expected_calls.append((chains.pub.name, "app.change_publisher", data.penguin))
        if cascade and shape == "full":
            expected_calls.append((chains.book.name, "app.change_book", data.book))
        expected_calls.append((chains.note.name, "app.view_booknote", note))
    assert provider_calls == expected_calls
    for actual, expected_call in zip(provider_calls, expected_calls, strict=True):
        assert actual[2] is expected_call[2]
    if missing:
        state.assert_not_called()
    else:
        state.assert_called_once_with(actor, obj)
        assert state.call_args.args[1] is obj


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian", "resource"])
@pytest.mark.parametrize("shape", ["short", "unknown-higher", "known-higher"])
def test_public_no_domain_queries(chains, helpers, data, lookups, resource_events, monkeypatch, family, shape):
    actor = _user("public_no_loading", (Publisher, "view"), (Book, "view"), (BookNote, "view"))
    saved_note = BookNote.objects.create(book=data.book, note="cold")
    if family == "guardian":
        target = helpers.note.Detail
        _grant(actor, helpers.pub, "view", data.penguin)
        _grant(actor, helpers.book, "view", data.book)
        _grant(actor, helpers.note, "view", saved_note)
    elif family == "core":
        target = type("PublicColdDetail", (DetailView,), {"cv_viewset": chains.note, "cv_context_actions": []})
    else:
        target = chains.depth[3].vs["plain"].get_view_class("detail")
    monkeypatch.setattr(target.cv_viewset, "ancestor_policy", AncestorPolicy(cascade=True))
    # Assigned fixture FKs are cached. Reload every supplied ORM row outside measurement.
    publisher = Publisher.objects.get(pk=data.penguin.pk)
    book = Book.objects.get(pk=data.book.pk)
    note = BookNote.objects.get(pk=saved_note.pk)
    obj = NoteChainFile(key="caller-owned") if family == "resource" else note
    nearest = note if family == "resource" else book
    known = [nearest] if shape == "short" else [nearest, None]
    if shape == "known-higher":
        known = [note, None, publisher] if family == "resource" else [book, publisher]
    for row in (publisher, book, note):
        assert row._state.fields_cache == {}
        monkeypatch.setattr(row, "save", Mock(side_effect=AssertionError("must not save inputs")))
        monkeypatch.setattr(row, "refresh_from_db", Mock(side_effect=AssertionError("must not refresh inputs")))
    state = Mock(return_value=True)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    assert "publisher" not in book._state.fields_cache
    assert "book" not in note._state.fields_cache
    with CaptureQueriesContext(connection) as captured:
        result = link_access.check_link_access(target, actor, obj=obj, known_ancestors=known)
    assert result is link_access.LinkAccess.ALLOWED
    state.assert_called_once_with(actor, obj)
    assert state.call_args.args[1] is obj
    assert lookups == []
    assert resource_events == []
    for query in captured.captured_queries:
        for model in (Publisher, Book, BookNote):
            for clause in ("from", "join"):
                assert f'{clause} "{model._meta.db_table}"' not in query["sql"].lower()
    for row in (publisher, book, note):
        assert row._state.fields_cache == {}
        row.save.assert_not_called()
        row.refresh_from_db.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
def test_public_membership_is_not_validated(core_targets, helpers, data, monkeypatch, family):
    actor = _user("public_mismatched_parent", (Publisher, "view"))
    _grant(actor, helpers.pub, "view", data.other)
    _grant(actor, helpers.book, "view", data.book)
    target = core_targets.Detail if family == "core" else helpers.book.Detail
    queryset = Mock(side_effect=AssertionError("link decisions do not prove queryset membership"))
    monkeypatch.setattr(type(target.cv_viewset), "get_queryset", queryset)
    assert data.book.publisher_id != data.other.pk
    assert (
        link_access.check_link_access(target, actor, obj=data.book, known_ancestors=[data.other])
        is link_access.LinkAccess.ALLOWED
    )
    queryset.assert_not_called()


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(case, marks=pytest.mark.django_db)
        for case in (
            "missing-nearest-key",
            "missing-higher-key",
            "missing-operation",
            "missing-core-own-key",
            "missing-guardian-own-key",
            "permission-exception",
            "state-exception",
        )
    ]
    + [
        pytest.param(f"{gate}/{fault}", marks=pytest.mark.django_db(transaction=True, databases=["default", "shard"]))
        for gate in ("ancestor-model", "ancestor-guardian", "ancestor-direct", "higher", "own-core", "own-guardian")
        for fault in ("actor", "auth-table", "object")
    ]
    + [
        pytest.param(case, marks=pytest.mark.django_db(transaction=True, databases=["default", "shard"]))
        for case in (
            "own-guardian/grant-table",
            "ancestor-guardian/grant-table",
            "ancestor-direct/grant-table",
            "higher/unselected",
            "ancestor-model/provider-none",
            "own-guardian/parent-denied",
            "own-guardian/inactive",
            "top-core/actor",
            "top-guardian/actor",
        )
    ],
)
def test_public_reached_configuration_errors(request, monkeypatch, case):
    """Only database cells need transaction/default+shard; imported fixtures supply no marks."""
    if "/" not in case:
        helpers = request.getfixturevalue("helpers")
        data = request.getfixturevalue("data")
        actor = _user("public_configuration", (Book, "view"))
        _grant(actor, helpers.pub, "view", data.penguin)
        _grant(actor, helpers.book, "view", data.book)
        target, obj, known = helpers.book.Detail, data.book, [data.penguin]
        expected_error, message, sentinel = ImproperlyConfigured, "missing", None
        if case == "missing-nearest-key":
            monkeypatch.setattr(
                target.cv_viewset,
                "ancestor_policy",
                AncestorPolicy(read=AncestorPermissions(nearest="missing", higher="view")),
            )
        elif case == "missing-higher-key":
            target, obj, known = helpers.note.List, None, [data.book, data.penguin]
            monkeypatch.setattr(
                target.cv_viewset,
                "ancestor_policy",
                AncestorPolicy(cascade=True, read=AncestorPermissions(nearest="view", higher="missing")),
            )
        elif case == "missing-operation":
            undeclared = request.getfixturevalue("undeclared_custom")
            target = undeclared.views["act"].get_view_class("act")
            message = r"ancestor_policy\.actions\["
        elif case.startswith("missing-"):
            if case == "missing-core-own-key":
                from crud_views.lib.views import DetailViewPermissionRequired

                target = type(
                    "PublicMissingPermission",
                    (DetailViewPermissionRequired,),
                    {"cv_viewset": helpers.core_book.vs, "cv_key": "public-missing", "cv_path": "public-missing"},
                )
                monkeypatch.setattr(helpers.cpub, "ancestor_policy", AncestorPolicy(provider="none"))
            monkeypatch.setattr(target, "cv_permission", "missing")
            expected_error = None
        else:
            sentinel = RuntimeError("project hook failure")
            hook = "cv_has_access" if case == "permission-exception" else "cv_action_enabled"
            monkeypatch.setattr(target, hook, Mock(side_effect=sentinel))
            expected_error, message = RuntimeError, "project hook failure"
        if expected_error is None:
            state = Mock(return_value=True)
            monkeypatch.setattr(target, "cv_action_enabled", state)
            assert (
                link_access.check_link_access(target, actor, obj=obj, known_ancestors=known)
                is link_access.LinkAccess.DENIED_PERMISSION
            )
            state.assert_not_called()
        else:
            with pytest.raises(expected_error, match=message) as error:
                link_access.check_link_access(target, actor, obj=obj, known_ancestors=known)
            if sentinel is not None:
                assert error.value is sentinel
            # A reached error is inherited, not a public-boundary reclassification.
            with pytest.raises(expected_error, match=message) as private_error:
                link_access._link_access(target, actor, obj, known)
            assert str(private_error.value) == str(error.value)
        return

    adb = request.getfixturevalue("adb")
    world = request.getfixturevalue("auth_world")
    routes = request.getfixturevalue("routes")
    gate, fault = case.split("/")
    actor = auth_database_tests._actor("public_database", superuser=True)
    obj, known = world.book, [world.publisher]
    if gate.startswith("ancestor-"):
        kind = gate.removeprefix("ancestor-")
        target = adb.child[kind].List
        obj = None
        if kind == "direct":
            known = [world.shelf]
    elif gate == "higher":
        target, obj, known = adb.notes[fault != "unselected"].List, None, [world.book, world.publisher]
    else:
        target = {
            "own-core": adb.CDetail,
            "own-guardian": adb.GDetail,
            "top-core": adb.CTDetail,
            "top-guardian": adb.GTDetail,
        }[gate]
        if gate.startswith("top-"):
            known = []
    if fault == "actor":
        actor = User.objects.using("shard").get(pk=actor.pk)
    elif fault == "auth-table":
        routes.read[auth_database_tests.TABLES["permission"]] = "shard"
    elif fault == "grant-table":
        table = "direct_user_grant" if gate == "ancestor-direct" else "user_grant"
        routes.read[auth_database_tests.TABLES[table]] = "shard"
    elif fault == "object":
        if gate.startswith("own-"):
            obj = Book.objects.using("shard").get(pk=obj.pk)
        else:
            index = 1 if gate == "higher" else 0
            known[index] = type(known[index]).objects.using("shard").get(pk=known[index].pk)
    elif fault == "unselected":
        known[1] = Publisher.objects.using("shard").get(pk=world.publisher.pk)
    elif fault == "provider-none":
        monkeypatch.setattr(adb.anc["model"], "ancestor_policy", AncestorPolicy(provider="none"))
        known[0] = Publisher.objects.using("shard").get(pk=world.publisher.pk)
    elif fault == "parent-denied":
        monkeypatch.setattr(adb.none, "ancestor_policy", AncestorPolicy(provider="model"))
        actor = auth_database_tests._actor("public_parent_denied")
        routes.read[auth_database_tests.TABLES["user_grant"]] = "shard"
    elif fault == "inactive":
        actor.is_active = False
        routes.read[auth_database_tests.TABLES["permission"]] = "shard"
    state = Mock(return_value=True)
    monkeypatch.setattr(target, "cv_action_enabled", state)
    allowed = case == "own-core/object" or fault in ("unselected", "provider-none") or gate.startswith("top-")
    denied = fault in ("parent-denied", "inactive")
    if allowed or denied:
        expected = link_access.LinkAccess.ALLOWED if allowed else link_access.LinkAccess.DENIED_PERMISSION
        assert link_access.check_link_access(target, actor, obj=obj, known_ancestors=known) is expected
        if allowed:
            state.assert_called_once_with(actor, obj if target.cv_object else known[0])
        else:
            state.assert_not_called()
    else:
        with pytest.raises(ImproperlyConfigured, match=auth_database_tests.REFUSED) as error:
            link_access.check_link_access(target, actor, obj=obj, known_ancestors=known)
        operation = (
            "actor database"
            if fault == "actor"
            else "object database"
            if fault == "object"
            else "authorization records"
        )
        assert operation in str(error.value)
        state.assert_not_called()
        with pytest.raises(ImproperlyConfigured, match=auth_database_tests.REFUSED) as private_error:
            link_access._link_access(target, actor, obj, known)
        assert str(private_error.value) == str(error.value)
