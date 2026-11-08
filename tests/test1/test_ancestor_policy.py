"""
Phase 06.18 plan 01 — strict ancestor policy values, global settings and declaration safety.

* ``AncestorPermissions`` / ``AncestorPolicy`` reject coercion, unknown fields, incomplete pairs and empty or
  padded keys; omitted / explicit None inheritance and empty ``actions`` keep their meaning.
* Ineffective or invalid owning-ViewSet declarations fail with a Pydantic ``ValidationError`` before registry
  insertion or automatic manage-view creation, so the same name can be retried. These tests run without
  database access (no ``django_db`` mark), which pytest-django enforces.
* Global ``CRUD_VIEWS_ANCESTOR_*`` defaults are validated when the settings singleton is built: invalid values
  are checked in fresh subprocesses without any database configured.
* The request engine honors the global cascade/pairs, the requested ViewSet's overrides in either direction,
  ignores an ancestor's own cascade, and never mutates declarations.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import uuid

import pytest
from pydantic import ValidationError

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import (
    _REGISTRY,
    _REGISTRY_LOCK,
    AncestorPermissions,
    AncestorPolicy,
    ParentViewSet,
    ViewSet,
)
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

# ── AncestorPermissions ──────────────────────────────────────────────────────


def test_pair_requires_both_named_strings():
    pair = AncestorPermissions(nearest="change", higher="view")
    assert (pair.nearest, pair.higher) == ("change", "view")
    assert AncestorPermissions.model_validate({"nearest": "view", "higher": "view"}) == AncestorPermissions(
        nearest="view", higher="view"
    )


@pytest.mark.parametrize(
    "data",
    [
        {"nearest": "view"},
        {"higher": "view"},
        {},
        {"nearest": None, "higher": "view"},
        {"nearest": "view", "higher": None},
        {"nearest": "", "higher": "view"},
        {"nearest": "view", "higher": ""},
        {"nearest": " view", "higher": "view"},
        {"nearest": "view", "higher": "view "},
        {"nearest": "view\n", "higher": "view"},
        {"nearest": "   ", "higher": "view"},
        {"nearest": 1, "higher": "view"},
        {"nearest": b"view", "higher": "view"},
        {"nearest": "view", "higher": "view", "extra": "view"},
    ],
    ids=lambda data: repr(data),
)
def test_pair_rejects_incomplete_none_empty_padded_coerced_and_extra(data):
    with pytest.raises(ValidationError):
        AncestorPermissions.model_validate(data)


# ── AncestorPolicy ───────────────────────────────────────────────────────────


def test_policy_exact_defaults():
    policy = AncestorPolicy()
    assert policy.provider is None
    assert policy.accept_global_perms is False
    assert policy.cascade is None
    assert policy.read is None
    assert policy.write is None
    assert policy.actions == {}


def test_policy_defaults_are_fresh_values():
    first, second = AncestorPolicy(), AncestorPolicy()
    assert first.actions is not second.actions
    first.actions["probe"] = AncestorPermissions(nearest="view", higher="view")
    assert second.actions == {}
    assert AncestorPolicy().actions == {}


@pytest.mark.parametrize("provider", [None, "model", "guardian", "none"])
def test_policy_accepts_documented_providers(provider):
    assert AncestorPolicy(provider=provider).provider == provider


def test_policy_accepts_explicit_none_and_empty_inheritance():
    policy = AncestorPolicy(cascade=None, read=None, write=None, actions={})
    assert policy == AncestorPolicy()


def test_policy_accepts_complete_pairs_as_mappings():
    policy = AncestorPolicy(
        cascade=False,
        read={"nearest": "view", "higher": "view"},
        write=AncestorPermissions(nearest="change", higher="change"),
        actions={"approve": {"nearest": "change", "higher": "view"}},
    )
    assert policy.read == AncestorPermissions(nearest="view", higher="view")
    assert policy.actions["approve"] == AncestorPermissions(nearest="change", higher="view")


@pytest.mark.parametrize(
    "data",
    [
        {"unknown": True},
        {"cv_guardian_parent_permission": "view"},
        {"provider": "object"},
        {"provider": "Model"},
        {"provider": ""},
        {"accept_global_perms": 1},
        {"accept_global_perms": 0},
        {"accept_global_perms": "true"},
        {"accept_global_perms": None},
        {"cascade": 1},
        {"cascade": 0},
        {"cascade": "false"},
        {"read": {"nearest": "view"}},
        {"write": {"higher": "view"}},
        {"read": "view"},
        {"actions": {"approve": None}},
        {"actions": {"approve": {"nearest": "change"}}},
        {"actions": {"": {"nearest": "change", "higher": "view"}}},
        {"actions": {" approve": {"nearest": "change", "higher": "view"}}},
        {"actions": {"approve ": {"nearest": "change", "higher": "view"}}},
        {"actions": None},
    ],
    ids=lambda data: repr(data),
)
def test_policy_rejects_unknown_coerced_and_incomplete_values(data):
    with pytest.raises(ValidationError):
        AncestorPolicy.model_validate(data)


# ── owning ViewSet validation before registration ────────────────────────────


def _registry_state() -> dict:
    with _REGISTRY_LOCK:
        return {name: (vs, dict(vs._views)) for name, vs in _REGISTRY.items()}


@pytest.fixture
def probe_name():
    name = f"ancpolicy{uuid.uuid4().hex[:8]}"
    yield name
    with _REGISTRY_LOCK:
        _REGISTRY.pop(name, None)


def _assert_rejected_without_side_effects(build, name: str, *fragments: str) -> None:
    before = _registry_state()
    with pytest.raises(ValidationError) as excinfo:
        build()
    message = str(excinfo.value)
    assert name in message, message
    for fragment in fragments:
        assert fragment in message, message
    assert _registry_state() == before  # no entry, no automatic manage view, existing entries untouched


@pytest.mark.parametrize(
    ("policy", "field"),
    [
        (AncestorPolicy(cascade=True), "cascade"),
        (AncestorPolicy(cascade=False), "cascade"),
        (AncestorPolicy(read=AncestorPermissions(nearest="view", higher="view")), "read"),
        (AncestorPolicy(write=AncestorPermissions(nearest="change", higher="view")), "write"),
        (AncestorPolicy(actions={"approve": AncestorPermissions(nearest="change", higher="view")}), "actions"),
    ],
    ids=["cascade-true", "cascade-false", "read-default-pair", "write-default-pair", "actions"],
)
def test_top_level_request_policy_is_rejected_before_registration(policy, field, probe_name):
    _assert_rejected_without_side_effects(
        lambda: ViewSet(model=Publisher, name=probe_name, ancestor_policy=policy), probe_name, field
    )
    # the corrected declaration may reuse the name
    vs = ViewSet(model=Publisher, name=probe_name)
    assert _REGISTRY[probe_name] is vs
    assert "manage" in vs._views


@pytest.mark.parametrize(
    "policy",
    [
        AncestorPolicy(),
        AncestorPolicy(cascade=None, read=None, write=None, actions={}),
        AncestorPolicy(provider="model"),
        AncestorPolicy(provider="none"),
        AncestorPolicy(accept_global_perms=False),
    ],
    ids=["omitted", "explicit-none-empty", "model", "none", "fallback-false"],
)
def test_top_level_default_policy_and_provider_choices_are_valid(policy, probe_name):
    vs = ViewSet(model=Publisher, name=probe_name, ancestor_policy=policy)
    assert _REGISTRY[probe_name] is vs
    assert vs.ancestor_policy == policy


def test_core_viewset_rejects_guardian_provider(probe_name):
    _assert_rejected_without_side_effects(
        lambda: ViewSet(model=Publisher, name=probe_name, ancestor_policy=AncestorPolicy(provider="guardian")),
        probe_name,
        "provider",
        "GuardianViewSet",
    )


@pytest.mark.parametrize("provider", [None, "model", "none"])
def test_fallback_flag_requires_guardian_provider(provider, probe_name):
    _assert_rejected_without_side_effects(
        lambda: ViewSet(
            model=Publisher,
            name=probe_name,
            ancestor_policy=AncestorPolicy(provider=provider, accept_global_perms=True),
        ),
        probe_name,
        "accept_global_perms",
    )


def test_constructor_mapping_policy_is_validated_strictly(probe_name):
    before = _registry_state()
    with pytest.raises(ValidationError):
        ViewSet(model=Publisher, name=probe_name, ancestor_policy={"cascade": "yes"})
    with pytest.raises(ValidationError):
        ViewSet(model=Publisher, name=probe_name, ancestor_policy={"unknown": True})
    assert _registry_state() == before


def test_subclass_policy_default_is_validated_before_registration(probe_name):
    class CascadingViewSet(ViewSet):
        ancestor_policy: AncestorPolicy = AncestorPolicy(cascade=True)

    _assert_rejected_without_side_effects(
        lambda: CascadingViewSet(model=Publisher, name=probe_name), probe_name, "cascade"
    )


def test_failed_declaration_for_existing_name_leaves_existing_entry(probe_name):
    original = ViewSet(model=Publisher, name=probe_name)
    _assert_rejected_without_side_effects(
        lambda: ViewSet(model=Publisher, name=probe_name, ancestor_policy=AncestorPolicy(cascade=True)),
        probe_name,
        "cascade",
    )
    assert _REGISTRY[probe_name] is original


def test_nested_request_policy_with_forward_parent_and_unregistered_action_is_valid(probe_name):
    policy = AncestorPolicy(
        cascade=False,
        read=AncestorPermissions(nearest="view", higher="view"),
        write=AncestorPermissions(nearest="change", higher="change"),
        actions={"not_registered_yet": AncestorPermissions(nearest="change", higher="view")},
    )
    vs = ViewSet(
        model=Book,
        name=probe_name,
        parent=ParentViewSet(name=f"{probe_name}_future_parent", attribute="publisher"),
        ancestor_policy=policy,
    )
    assert _REGISTRY[probe_name] is vs


def test_each_viewset_owns_fresh_policy_values():
    first = ViewSet(model=Publisher, name=f"ancfresh{uuid.uuid4().hex[:8]}")
    second = ViewSet(model=Publisher, name=f"ancfresh{uuid.uuid4().hex[:8]}")
    try:
        assert first.ancestor_policy is not second.ancestor_policy
        assert first.ancestor_policy.actions is not second.ancestor_policy.actions
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(first.name, None)
            _REGISTRY.pop(second.name, None)


# ── global settings ──────────────────────────────────────────────────────────


def test_settings_defaults_are_the_approved_pairs():
    assert getattr(crud_views_settings, "ancestor_permission_cascade", None) is True
    assert getattr(crud_views_settings, "ancestor_read_permissions", None) == AncestorPermissions(
        nearest="view", higher="view"
    )
    assert getattr(crud_views_settings, "ancestor_write_permissions", None) == AncestorPermissions(
        nearest="change", higher="view"
    )


def _fresh_settings(settings_source: str, body: str, *, block_guardian: bool = False) -> subprocess.CompletedProcess:
    """Configure Django in a fresh interpreter (no database configured at all) and run ``body``."""
    code = textwrap.dedent(
        f"""
        import sys
        {"sys.modules['guardian'] = None  # Guardian is not installed" if block_guardian else ""}
        from django.conf import settings
        settings.configure(
            INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"],
            {settings_source}
        )
        """
    )
    return subprocess.run([sys.executable, "-c", code + textwrap.dedent(body)], capture_output=True, text=True)


@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", '{"nearest": "view"}'),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", '{"higher": "view"}'),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", '{"nearest": "change", "higher": None}'),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", '{"nearest": "change ", "higher": "view"}'),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", '{"nearest": "change", "higher": "view", "extra": "x"}'),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", '"view"'),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", "None"),
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", "1"),
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", '"true"'),
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", "None"),
    ],
)
def test_invalid_global_settings_fail_at_fresh_settings_initialization(setting, value):
    result = _fresh_settings(f"{setting}={value},", "import crud_views.lib.settings\nprint('IMPORTED')\n")
    assert result.returncode != 0, result.stdout
    assert "IMPORTED" not in result.stdout
    assert "ValidationError" in result.stderr, result.stderr
    field = setting.removeprefix("CRUD_VIEWS_").lower()
    assert field in result.stderr, result.stderr


def test_complete_global_settings_replace_whole_pairs():
    result = _fresh_settings(
        "CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE=False,"
        'CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS={"nearest": "change", "higher": "view"},'
        'CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS={"nearest": "change", "higher": "change"},',
        """
        from crud_views.lib.settings import crud_views_settings as s
        print(s.ancestor_permission_cascade, s.ancestor_read_permissions.model_dump(),
              s.ancestor_write_permissions.model_dump())
        """,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == (
        "False {'nearest': 'change', 'higher': 'view'} {'nearest': 'change', 'higher': 'change'}"
    )


def test_core_policy_configures_without_guardian():
    result = _fresh_settings(
        "",
        """
        import django
        django.setup()
        from django.contrib.auth.models import Group
        from crud_views.lib.settings import crud_views_settings as s
        from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
        top = ViewSet(model=Group, name="core_only_top", ancestor_policy=AncestorPolicy(provider="none"))
        child = ViewSet(
            model=Group,
            name="core_only_child",
            parent=ParentViewSet(name="core_only_top", attribute="permissions"),
            ancestor_policy=AncestorPolicy(cascade=False, write=AncestorPermissions(nearest="view", higher="view")),
        )
        assert "guardian" not in [m for m in sys.modules if sys.modules[m] is not None]
        print("CORE-OK", s.ancestor_permission_cascade, child.ancestor_policy.cascade)
        """,
        block_guardian=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "CORE-OK True False"


# ── engine: global defaults and requested-ViewSet overrides ──────────────────


@pytest.fixture
def two_ancestors():
    """Core Publisher → core Book → plain BookNote list (two protected model-provider ancestors)."""
    from crud_views.lib.views import ListView

    def build(sfx):
        pub_vs = ViewSet(model=Publisher, name=f"ancpp{sfx}")
        book_vs = ViewSet(model=Book, name=f"ancpb{sfx}", parent=ParentViewSet(name=pub_vs.name, attribute="publisher"))
        note_vs = ViewSet(model=BookNote, name=f"ancpn{sfx}", parent=ParentViewSet(name=book_vs.name, attribute="book"))

        class NoteList(ListView):
            cv_viewset = note_vs
            cv_list_actions = []
            cv_context_actions = []

        return SimpleNamespace(pub_vs=pub_vs, book_vs=book_vs, note_vs=note_vs), [note_vs]

    from types import SimpleNamespace

    with isolated_routes(build) as ns:
        yield ns


@pytest.fixture
def chain_world(db):
    publisher = Publisher.objects.create(name="Penguin")
    book = Book.objects.create(title="Hitchhiker", publisher=publisher)
    BookNote.objects.create(book=book, note="note")
    return publisher, book


def _get(chain, world, user):
    publisher, book = world
    url = _url(chain.note_vs, "list", **{f"{chain.pub_vs.name}_pk": publisher.pk, f"{chain.book_vs.name}_pk": book.pk})
    return _client(user).get(url)


def _snapshot(chain) -> tuple:
    return (
        [vs.ancestor_policy.model_dump() for vs in (chain.pub_vs, chain.book_vs, chain.note_vs)],
        crud_views_settings.ancestor_permission_cascade,
        crud_views_settings.ancestor_read_permissions.model_dump(),
    )


@pytest.mark.django_db
def test_global_full_cascade_requires_every_protected_ancestor(two_ancestors, chain_world):
    before = _snapshot(two_ancestors)
    assert _get(two_ancestors, chain_world, _user("book_only", (Book, "view"))).status_code == 403
    assert _get(two_ancestors, chain_world, _user("both", (Book, "view"), (Publisher, "view"))).status_code == 200
    assert _snapshot(two_ancestors) == before  # resolution never mutates declarations or settings


@pytest.mark.django_db
def test_global_nearest_only_checks_nearest_protected_ancestor(two_ancestors, chain_world, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", False)
    assert _get(two_ancestors, chain_world, _user("book_only", (Book, "view"))).status_code == 200
    # nearest denial never substitutes a farther ancestor's grant
    assert _get(two_ancestors, chain_world, _user("publisher_only", (Publisher, "view"))).status_code == 403


@pytest.mark.django_db
def test_requested_cascade_true_overrides_global_false(two_ancestors, chain_world, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", False)
    two_ancestors.note_vs.ancestor_policy = AncestorPolicy(cascade=True)
    assert _get(two_ancestors, chain_world, _user("book_only", (Book, "view"))).status_code == 403


@pytest.mark.django_db
def test_requested_cascade_false_overrides_global_true(two_ancestors, chain_world):
    two_ancestors.note_vs.ancestor_policy = AncestorPolicy(cascade=False)
    assert _get(two_ancestors, chain_world, _user("book_only", (Book, "view"))).status_code == 200


@pytest.mark.django_db
def test_ancestor_cascade_does_not_stop_descendant_traversal(two_ancestors, chain_world):
    two_ancestors.book_vs.ancestor_policy = AncestorPolicy(cascade=False)  # describes Book requests only
    assert _get(two_ancestors, chain_world, _user("book_only", (Book, "view"))).status_code == 403


@pytest.mark.django_db
def test_global_read_pair_replaces_the_default_whole(two_ancestors, chain_world, monkeypatch):
    monkeypatch.setattr(
        crud_views_settings, "ancestor_read_permissions", AncestorPermissions(nearest="change", higher="view")
    )
    viewer = _user("viewer", (Book, "view"), (Publisher, "view"))
    editor = _user("editor", (Book, "change"), (Publisher, "view"))
    assert _get(two_ancestors, chain_world, viewer).status_code == 403
    assert _get(two_ancestors, chain_world, editor).status_code == 200


@pytest.mark.django_db
def test_requested_read_pair_overrides_global(two_ancestors, chain_world, monkeypatch):
    monkeypatch.setattr(
        crud_views_settings, "ancestor_read_permissions", AncestorPermissions(nearest="change", higher="change")
    )
    two_ancestors.note_vs.ancestor_policy = AncestorPolicy(read=AncestorPermissions(nearest="view", higher="view"))
    assert _get(two_ancestors, chain_world, _user("viewer", (Book, "view"), (Publisher, "view"))).status_code == 200


@pytest.mark.django_db
def test_none_provider_level_is_skipped_but_does_not_consume_nearest(two_ancestors, chain_world, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", False)
    two_ancestors.book_vs.ancestor_policy = AncestorPolicy(provider="none")
    # Book is unprotected, so Publisher becomes the nearest protected ancestor
    assert _get(two_ancestors, chain_world, _user("book_only", (Book, "view"))).status_code == 403
    assert _get(two_ancestors, chain_world, _user("publisher_only", (Publisher, "view"))).status_code == 200
