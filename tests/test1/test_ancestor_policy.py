"""Ancestor policy configuration: strict public types, global defaults and owning-ViewSet validation.

Construction-time failures must be Pydantic ``ValidationError``s raised before any registry insertion, automatic
manage-view creation or database query, so a corrected declaration may reuse the same name.
"""

import subprocess
import sys
import textwrap
import uuid

import pytest
from django.test import override_settings
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.viewset import (
    _REGISTRY,
    _REGISTRY_LOCK,
    AncestorPermissions,
    AncestorPolicy,
    ParentViewSet,
    ViewSet,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, Publisher

PAIR = {"nearest": "change", "higher": "view"}


@pytest.fixture
def names():
    """Unique ViewSet names, removed from the registry afterwards."""
    created: list[str] = []

    def make(prefix: str = "ancpol") -> str:
        name = f"{prefix}{uuid.uuid4().hex[:8]}"
        created.append(name)
        return name

    yield make
    with _REGISTRY_LOCK:
        for name in created:
            _REGISTRY.pop(name, None)


@pytest.fixture
def manage_spy(monkeypatch):
    """Record every automatic manage-view creation (core and Guardian)."""
    calls: list[str] = []
    for cls in (ViewSet, GuardianViewSet):
        original = cls.__dict__["get_manage_view_class"]

        def spy(self, _original=original):
            calls.append(self.name)
            return _original(self)

        monkeypatch.setattr(cls, "get_manage_view_class", spy)
    return calls


@pytest.fixture
def rejected(names, manage_spy, django_assert_num_queries):
    """Assert a declaration fails structurally with no queries, registry change or manage view."""

    def check(viewset_class, match: str | None = None, **kwargs):
        name = kwargs.setdefault("name", names())
        with _REGISTRY_LOCK:
            before = dict(_REGISTRY)
        with django_assert_num_queries(0), pytest.raises(ValidationError, match=match) as excinfo:
            viewset_class(**kwargs)
        with _REGISTRY_LOCK:
            assert dict(_REGISTRY) == before
        assert name not in _REGISTRY
        assert name not in manage_spy
        return excinfo.value

    return check


def _fresh_settings() -> CrudViewsSettings:
    """A settings object reading the current Django settings (the singleton captured them at import)."""
    return CrudViewsSettings()


# ── public types ───────────────────────────────────────────────────────────────


def test_policy_defaults_are_independent(names, db):
    first = ViewSet(model=Publisher, name=names())
    second = ViewSet(model=Publisher, name=names())

    assert first.ancestor_policy is not second.ancestor_policy
    assert first.ancestor_policy.actions is not second.ancestor_policy.actions
    first.ancestor_policy.actions["approve"] = AncestorPermissions(**PAIR)
    assert second.ancestor_policy.actions == {}
    assert AncestorPolicy().actions == {}

    policy = second.ancestor_policy
    assert (policy.provider, policy.accept_global_perms, policy.cascade, policy.read, policy.write) == (
        None,
        False,
        None,
        None,
        None,
    )


def test_policy_types_are_frozen():
    """Post-construction assignment would bypass validation and leak into every ViewSet sharing the object."""
    policy = AncestorPolicy(read=AncestorPermissions(**PAIR))
    with pytest.raises(ValidationError):
        policy.cascade = True
    with pytest.raises(ValidationError):
        policy.read.nearest = "delete"


def test_policy_types_are_exported_from_viewset_package():
    import crud_views.lib.ancestor_policy as module
    import crud_views.lib.viewset as package

    assert package.AncestorPolicy is module.AncestorPolicy
    assert package.AncestorPermissions is module.AncestorPermissions


INVALID_PAIRS = [
    pytest.param({"nearest": "view"}, id="missing-higher"),
    pytest.param({"higher": "view"}, id="missing-nearest"),
    pytest.param({"nearest": "view", "higher": None}, id="none-component"),
    pytest.param({"nearest": None, "higher": "view"}, id="none-nearest"),
    pytest.param({"nearest": "", "higher": "view"}, id="empty"),
    pytest.param({"nearest": "   ", "higher": "view"}, id="blank"),
    pytest.param({"nearest": " view", "higher": "view"}, id="leading-space"),
    pytest.param({"nearest": "view", "higher": "view\n"}, id="trailing-newline"),
    pytest.param({"nearest": 1, "higher": "view"}, id="int"),
    pytest.param({"nearest": b"view", "higher": "view"}, id="bytes"),
    pytest.param({"nearest": "view", "higher": "view", "lowest": "view"}, id="unknown-field"),
]

INVALID_POLICIES = [
    pytest.param({"provider": "object"}, id="unknown-provider"),
    pytest.param({"provider": ""}, id="empty-provider"),
    pytest.param({"provider": "Model"}, id="cased-provider"),
    pytest.param({"provider": False}, id="bool-provider"),
    pytest.param({"accept_global_perms": "true"}, id="accept-str"),
    pytest.param({"accept_global_perms": 1}, id="accept-1"),
    pytest.param({"accept_global_perms": 0}, id="accept-0"),
    pytest.param({"accept_global_perms": None}, id="accept-none"),
    pytest.param({"cascade": "true"}, id="cascade-str"),
    pytest.param({"cascade": 1}, id="cascade-1"),
    pytest.param({"cascade": 0}, id="cascade-0"),
    pytest.param({"read": {"nearest": "view"}}, id="read-incomplete"),
    pytest.param({"write": {"nearest": "change", "higher": None}}, id="write-none-component"),
    pytest.param({"actions": {"approve": None}}, id="action-none"),
    pytest.param({"actions": {"approve": {"nearest": "change"}}}, id="action-incomplete"),
    pytest.param({"actions": {"": PAIR}}, id="action-empty-key"),
    pytest.param({"actions": {" approve": PAIR}}, id="action-padded-key"),
    pytest.param({"actions": {"approve ": PAIR}}, id="action-trailing-key"),
    pytest.param({"actions": {1: PAIR}}, id="action-int-key"),
    pytest.param({"actions": None}, id="actions-none"),
    pytest.param({"cascade_mode": "full"}, id="unknown-field"),
]


@pytest.mark.parametrize("data", INVALID_PAIRS)
def test_strict_pair_and_policy_values_pairs(data):
    with pytest.raises(ValidationError):
        AncestorPermissions(**data)
    with pytest.raises(ValidationError):
        AncestorPolicy(read=data)


@pytest.mark.parametrize("data", INVALID_POLICIES)
def test_strict_pair_and_policy_values(data):
    with pytest.raises(ValidationError):
        AncestorPolicy(**data)


@pytest.mark.django_db
@pytest.mark.parametrize("viewset_class", [ViewSet, GuardianViewSet])
@pytest.mark.parametrize("data", INVALID_POLICIES)
def test_strict_policy_values_attached(rejected, viewset_class, data):
    rejected(
        viewset_class,
        model=Book,
        parent=ParentViewSet(name="ancpol-unregistered-parent", attribute="publisher"),
        ancestor_policy=data,
    )


@pytest.mark.parametrize("data", INVALID_PAIRS)
@pytest.mark.django_db
def test_strict_pair_values_attached(rejected, data):
    rejected(
        ViewSet,
        model=Book,
        parent=ParentViewSet(name="ancpol-unregistered-parent", attribute="publisher"),
        ancestor_policy={"actions": {"approve": data}},
    )


def test_valid_standalone_policy_may_hold_request_settings():
    pair = AncestorPermissions(nearest="change", higher="change")
    policy = AncestorPolicy(
        provider="none",
        cascade=False,
        read=AncestorPermissions(nearest="view", higher="view"),
        write=pair,
        actions={"approve": pair, "cv-export_2": {"nearest": "view", "higher": "view"}},
    )
    assert policy.write == pair
    assert policy.actions["cv-export_2"] == AncestorPermissions(nearest="view", higher="view")
    for provider in ("model", "guardian", "none", None):
        assert AncestorPolicy(provider=provider, accept_global_perms=True).provider == provider


# ── global defaults ────────────────────────────────────────────────────────────


def test_global_defaults_and_explicit_partial_pairs():
    read = AncestorPermissions(nearest="view", higher="view")
    write = AncestorPermissions(nearest="change", higher="view")

    for values in (crud_views_settings, _fresh_settings()):
        assert values.ancestor_permission_cascade is True
        assert values.ancestor_read_permissions == read
        assert values.ancestor_write_permissions == write

    with override_settings(
        CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE=False,
        CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS={"nearest": "change", "higher": "change"},
    ):
        values = _fresh_settings()
    assert values.ancestor_permission_cascade is False
    assert values.ancestor_write_permissions == AncestorPermissions(nearest="change", higher="change")
    assert values.ancestor_read_permissions == read


@pytest.mark.parametrize(
    "setting,value",
    [
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", {"nearest": "view"}),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", {"higher": "view"}),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", None),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", {"nearest": "view", "higher": None}),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", {"nearest": "view", "higher": "view", "extra": "view"}),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", {"nearest": "change"}),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", None),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", {"nearest": " change", "higher": "view"}),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", {}),
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", "true"),
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", 1),
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", 0),
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", None),
    ],
)
def test_invalid_global_settings_fail(setting, value):
    with override_settings(**{setting: value}), pytest.raises(ValidationError):
        _fresh_settings()


# ── owning-ViewSet validation ──────────────────────────────────────────────────

OWNER_CASES = [
    pytest.param(
        ViewSet,
        {"provider": "guardian"},
        {"provider": "model"},
        "GuardianViewSet",
        id="core-guardian-provider",
    ),
    pytest.param(
        ViewSet,
        {"accept_global_perms": True},
        {"accept_global_perms": False},
        "accept_global_perms",
        id="core-fallback",
    ),
    pytest.param(
        ViewSet,
        {"provider": "none", "accept_global_perms": True},
        {"provider": "none"},
        "accept_global_perms",
        id="core-none-fallback",
    ),
    pytest.param(
        GuardianViewSet,
        {"provider": "model", "accept_global_perms": True},
        {"provider": "model"},
        "accept_global_perms",
        id="guardian-model-fallback",
    ),
    pytest.param(
        GuardianViewSet,
        {"provider": "none", "accept_global_perms": True},
        {"accept_global_perms": True},
        "accept_global_perms",
        id="guardian-none-fallback",
    ),
    pytest.param(ViewSet, {"cascade": False}, {}, "cascade", id="core-top-level-cascade"),
    pytest.param(
        GuardianViewSet, {"actions": {"approve": PAIR}}, {"actions": {}}, "actions", id="guardian-top-actions"
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize("viewset_class,bad,good,match", OWNER_CASES)
def test_owner_policy_validates_before_registration(rejected, manage_spy, viewset_class, bad, good, match):
    name = f"ancown{uuid.uuid4().hex[:8]}"
    rejected(viewset_class, match=match, model=Publisher, name=name, ancestor_policy=AncestorPolicy(**bad))

    try:
        viewset = viewset_class(model=Publisher, name=name, ancestor_policy=AncestorPolicy(**good))
        assert ViewSet.get_viewset(name) is viewset
        assert list(viewset.get_all_views()) == ["manage"]
        # GuardianViewSet.register() replaces the base manage view it inherits, so it asks for the class twice
        assert set(manage_spy) == {name}
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)


@pytest.mark.django_db
def test_failed_declaration_leaves_existing_entries_intact(rejected, names):
    existing = ViewSet(model=Publisher, name=names())
    rejected(ViewSet, model=Publisher, ancestor_policy=AncestorPolicy(provider="guardian"))
    assert ViewSet.get_viewset(existing.name) is existing


def test_provider_defaults_and_explicit_choices(names, db):
    assert ViewSet(model=Publisher, name=names())._ancestor_provider() == "model"
    assert GuardianViewSet(model=Publisher, name=names())._ancestor_provider() == "guardian"
    for viewset_class in (ViewSet, GuardianViewSet):
        for provider in ("model", "none"):
            viewset = viewset_class(model=Publisher, name=names(), ancestor_policy=AncestorPolicy(provider=provider))
            assert viewset._ancestor_provider() == provider
    explicit = GuardianViewSet(model=Publisher, name=names(), ancestor_policy=AncestorPolicy(provider="guardian"))
    assert explicit._ancestor_provider() == "guardian"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "policy,fields",
    [
        pytest.param({"cascade": True}, ["cascade"], id="cascade-true"),
        pytest.param({"cascade": False}, ["cascade"], id="cascade-false"),
        pytest.param({"read": {"nearest": "view", "higher": "view"}}, ["read"], id="read-matching-default"),
        pytest.param({"write": {"nearest": "change", "higher": "view"}}, ["write"], id="write-matching-default"),
        pytest.param({"actions": {"approve": PAIR}}, ["actions"], id="actions"),
        pytest.param(
            {"cascade": False, "read": PAIR, "write": PAIR, "actions": {"approve": PAIR}},
            ["cascade", "read", "write", "actions"],
            id="all",
        ),
    ],
)
@pytest.mark.parametrize("viewset_class", [ViewSet, GuardianViewSet])
def test_top_level_policy_scope(rejected, viewset_class, policy, fields):
    error = rejected(viewset_class, model=Publisher, ancestor_policy=AncestorPolicy(**policy))
    for field in fields:
        assert field in str(error)


@pytest.mark.parametrize(
    "viewset_class,policy",
    [
        (ViewSet, None),
        (ViewSet, AncestorPolicy(cascade=None, read=None, write=None, actions={})),
        (ViewSet, AncestorPolicy(provider="model", accept_global_perms=False)),
        (ViewSet, AncestorPolicy(provider="none")),
        (GuardianViewSet, None),
        (GuardianViewSet, AncestorPolicy(accept_global_perms=True)),
        (GuardianViewSet, AncestorPolicy(provider="guardian", accept_global_perms=True)),
        (GuardianViewSet, AncestorPolicy(provider="none")),
    ],
)
def test_top_level_policy_scope_accepts(names, db, viewset_class, policy):
    kwargs = {} if policy is None else {"ancestor_policy": policy}
    viewset = viewset_class(model=Publisher, name=names(), **kwargs)
    assert viewset.ancestor_policy == (policy or AncestorPolicy())


@pytest.mark.parametrize("viewset_class", [ViewSet, GuardianViewSet])
def test_nested_request_settings_construct_with_unresolved_parent(names, db, viewset_class):
    """A child may precede its parent: request settings are accepted without resolving the parent."""
    policy = AncestorPolicy(
        provider="none",
        cascade=False,
        read=AncestorPermissions(nearest="view", higher="view"),
        write=AncestorPermissions(nearest="change", higher="change"),
        actions={"approve": AncestorPermissions(**PAIR)},
    )
    parent_name = names()
    child = viewset_class(
        model=Book,
        name=names(),
        parent=ParentViewSet(name=parent_name, attribute="publisher"),
        ancestor_policy=policy,
    )
    assert child.ancestor_policy is policy
    assert parent_name not in _REGISTRY


# ── core without Guardian ──────────────────────────────────────────────────────


def test_core_policy_import_without_guardian():
    code = textwrap.dedent(
        """
        import sys


        class BlockGuardian:
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] in ("guardian", "crud_views_guardian"):
                    raise ImportError(f"blocked {name}")
                return None


        sys.meta_path.insert(0, BlockGuardian())

        import django
        from django.conf import settings

        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "crud_views.apps.CrudViewsConfig"],
            DATABASES={},
        )
        django.setup()

        from django.contrib.auth.models import Group

        from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ViewSet

        viewset = ViewSet(model=Group, name="group", ancestor_policy=AncestorPolicy(provider="none"))
        assert viewset._ancestor_provider() == "none"
        assert AncestorPermissions(nearest="view", higher="view").higher == "view"
        assert not [name for name in sys.modules if name.split(".")[0] in ("guardian", "crud_views_guardian")]
        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout
