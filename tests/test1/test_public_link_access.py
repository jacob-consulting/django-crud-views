"""Public link decisions from caller-owned objects, without a request or rendering view."""

from enum import Enum
from inspect import Parameter, signature
from pathlib import Path
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import isolate_apps

from crud_views.lib import link_access
from crud_views.lib.resource import ResourceViewMixin
from crud_views.lib.views import DetailView, ListView
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from tests.test1 import test_ancestor_resources as resource_tests
from tests.test1 import test_link_access as private_link_tests
from tests.test1.app.models import Author, Book, BookNote, Car, Publisher, PublisherProxy, Truck, Vehicle
from tests.test1.test_ancestor_authorization import _user, isolated_routes
from tests.test1.test_ancestor_docs import _fence
from tests.test1.test_ancestor_resources import NoteChainFile, PublisherChainFile, TopFile, _ChainFile

core_targets = private_link_tests.core_targets
data = private_link_tests.data
helpers = private_link_tests.helpers
chains = resource_tests.chains

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
