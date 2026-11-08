"""
Phase 06.18 plan 02 Task 2 — operation families, exact registered actions and selection precedence.

* Finite family inventory: every shipped endpoint family and permission variant, ordinary subclasses and
  renamed keys are Read or Write by class, never by key string, HTTP method or local permission name.
  Generic actions, custom forms and workflow are unclassified and need an exact ``actions`` entry when nested.
* Exact keys: ``actions`` entries use literal registration. Card's ``list`` navigation alias is preserved but
  never validates or selects a ``list`` entry; a request reaching Card keeps Card's own key.
* Custom declarations: a nested unclassified endpoint without its entry is a system-check error
  (viewset.E268) and a runtime ``ImproperlyConfigured`` in both cascade modes and with all-none ancestry; an
  entry naming no registered endpoint is viewset.E267. Top-level custom endpoints need nothing.
* Completion barrier: the check first imports the configured root URLconf and every included URLconf, so a
  view registered by a late-imported module is never reported missing; without ROOT_URLCONF, or when that
  import fails or is reentrant, only the completion-dependent checks are deferred.
* Selection precedence (requests): full vs nearest-only, requested override in both directions, ancestor
  cascade isolation, none levels that do not consume the nearest position, all-none chains, and denial at
  the nearest gate that never substitutes a farther grant.
"""

from __future__ import annotations

import sys
import uuid
from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.test import override_settings
from django.urls import clear_url_caches

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import (
    _REGISTRY,
    _REGISTRY_LOCK,
    AncestorPermissions,
    AncestorPolicy,
    ParentViewSet,
    ViewSet,
)
from tests.test1 import test_ancestor_authorization as _auth
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

events = _auth.events  # the ordered queryset / has_perm spy fixture of plan 01

READ = AncestorPermissions(nearest="view", higher="view")
WRITE = AncestorPermissions(nearest="change", higher="view")
STRICT = AncestorPermissions(nearest="change", higher="change")


@pytest.fixture
def sfx():
    return uuid.uuid4().hex[:8]


@pytest.fixture
def registry():
    with _REGISTRY_LOCK:
        snapshot = dict(_REGISTRY)
    try:
        yield
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(snapshot)
        clear_url_caches()


@pytest.fixture
def no_db():
    def blocker(execute, sql, params, many, context):
        raise AssertionError(f"declaration work queried the database: {sql}")

    wrappers = [conn.execute_wrapper(blocker) for conn in connections.all()]
    for wrapper in wrappers:
        wrapper.__enter__()
    try:
        yield
    finally:
        for wrapper in reversed(wrappers):
            wrapper.__exit__(None, None, None)


def _view(base, vs, key=None, **attrs):
    attrs = {"cv_viewset": vs, "cv_list_actions": [], "cv_context_actions": [], "__module__": __name__, **attrs}
    if key is not None:
        attrs["cv_key"] = key
    return type(f"V_{vs.name}_{key or base.cv_key}", (base,), attrs)


# ── finite family inventory ──────────────────────────────────────────────────


def _inventory():
    from crud_views.lib import views as core
    from crud_views.lib.views.child import RedirectChildView
    from crud_views.lib.views.form import (
        CustomFormNoObjectView,
        CustomFormNoObjectViewPermissionRequired,
        CustomFormView,
        CustomFormViewPermissionRequired,
    )
    from crud_views.lib.views.manage import ManageView
    from crud_views_guardian.lib import views as guardian
    from crud_views_object_detail.lib.views import ObjectDetailView, ObjectDetailViewPermissionRequired
    from crud_views_polymorphic.lib import (
        PolymorphicCreateSelectView,
        PolymorphicCreateSelectViewPermissionRequired,
        PolymorphicCreateView,
        PolymorphicCreateViewPermissionRequired,
        PolymorphicDeleteView,
        PolymorphicDeleteViewPermissionRequired,
        PolymorphicDetailView,
        PolymorphicDetailViewPermissionRequired,
        PolymorphicUpdateView,
        PolymorphicUpdateViewPermissionRequired,
    )
    from crud_views_workflow.lib.views import WorkflowView, WorkflowViewPermissionRequired

    read = [
        core.ListView,
        core.ListViewPermissionRequired,
        core.CardListView,
        core.CardListViewPermissionRequired,
        core.DetailView,
        core.DetailViewPermissionRequired,
        ObjectDetailView,
        ObjectDetailViewPermissionRequired,
        PolymorphicDetailView,
        PolymorphicDetailViewPermissionRequired,
        RedirectChildView,
        ManageView,
        guardian.GuardianManageView,
        guardian.GuardianListViewPermissionRequired,
        guardian.GuardianCardListViewPermissionRequired,
        guardian.GuardianDetailViewPermissionRequired,
    ]
    write = [
        core.CreateView,
        core.CreateViewPermissionRequired,
        core.UpdateView,
        core.UpdateViewPermissionRequired,
        core.DeleteView,
        core.DeleteViewPermissionRequired,
        PolymorphicCreateView,
        PolymorphicCreateViewPermissionRequired,
        PolymorphicUpdateView,
        PolymorphicUpdateViewPermissionRequired,
        PolymorphicDeleteView,
        PolymorphicDeleteViewPermissionRequired,
        PolymorphicCreateSelectView,
        PolymorphicCreateSelectViewPermissionRequired,
        core.OrderedUpView,
        core.OrderedUpViewPermissionRequired,
        core.OrderedDownView,
        core.OrderedUpDownPermissionRequired,
        guardian.GuardianCreateViewPermissionRequired,
        guardian.GuardianUpdateViewPermissionRequired,
        guardian.GuardianDeleteViewPermissionRequired,
    ]
    custom = [
        core.ActionView,
        core.ActionViewPermissionRequired,
        CustomFormView,
        CustomFormViewPermissionRequired,
        CustomFormNoObjectView,
        CustomFormNoObjectViewPermissionRequired,
        WorkflowView,
        WorkflowViewPermissionRequired,
        guardian.GuardianActionViewPermissionRequired,
    ]
    return {"read": read, "write": write, None: custom}


def _family_cases():
    for family, classes in _inventory().items():
        for cls in classes:
            yield pytest.param(cls, family, id=f"{family}-{cls.__module__.split('.')[0]}.{cls.__name__}")


@pytest.mark.parametrize(("cls", "family"), list(_family_cases()))
def test_family_inventory(cls, family):
    from crud_views.lib.ancestors import _operation_family

    assert _operation_family(cls) == family
    # an ordinary subclass and a renamed key keep the family
    subclass = type(f"Sub{cls.__name__}", (cls,), {"cv_key": "renamed", "__module__": __name__})
    assert _operation_family(subclass) == family


def test_classification_ignores_key_names_local_permissions_and_django_detail():
    from django.views.generic import DetailView as DjangoDetailView

    from crud_views.lib.ancestors import _operation_family
    from crud_views.lib.views import ActionView, ListView
    from crud_views.lib.views.form import CustomFormView

    misleading = type("DetailNamed", (ActionView,), {"cv_key": "detail", "cv_permission": "view"})
    assert _operation_family(misleading) is None
    # CustomFormView (and therefore workflow) inherits Django's generic DetailView: that is not a family
    assert issubclass(CustomFormView, DjangoDetailView)
    assert _operation_family(CustomFormView) is None
    # a Read family keeps Read whatever its key or local permission says
    writing_name = type("CreateNamed", (ListView,), {"cv_key": "create", "cv_permission": "add"})
    assert _operation_family(writing_name) == "read"


def test_selector_marker_is_private_and_inherited():
    from crud_views.lib.view import CrudView
    from crud_views_polymorphic.lib import PolymorphicCreateSelectView

    assert PolymorphicCreateSelectView._cv_ancestor_operation == "write"
    assert not hasattr(CrudView, "_cv_ancestor_operation")


# ── exact registered keys and pair selection (no database) ───────────────────


def _nested(sfx, *, policy=None, viewset_cls=ViewSet):
    pub_vs = ViewSet(model=Publisher, name=f"op_pub_{sfx}")
    _view(_core("ListView"), pub_vs)
    book_vs = viewset_cls(
        model=Book,
        name=f"op_book_{sfx}",
        parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
        ancestor_policy=policy or AncestorPolicy(),
    )
    return pub_vs, book_vs


def _core(name):
    from crud_views.lib import views

    return getattr(views, name)


def test_family_pairs_and_overrides_select_the_approved_pair(registry, sfx, no_db):
    from crud_views.lib.ancestors import _operation_requirements

    _, book_vs = _nested(sfx)
    list_view, update_view = _view(_core("ListView"), book_vs), _view(_core("UpdateView"), book_vs, fields=["title"])
    delete_view = _view(_core("DeleteView"), book_vs)
    assert _operation_requirements(list_view) == crud_views_settings.ancestor_read_permissions == READ
    assert _operation_requirements(update_view) == crud_views_settings.ancestor_write_permissions == WRITE
    assert _operation_requirements(delete_view) == WRITE  # child deletion needs parent change, not delete

    _, overridden = _nested(
        sfx + "o",
        policy=AncestorPolicy(read=STRICT, write=READ, actions={"delete": STRICT, "list": READ}),
    )
    o_list = _view(_core("ListView"), overridden)
    o_update = _view(_core("UpdateView"), overridden, fields=["title"])
    o_delete = _view(_core("DeleteView"), overridden)
    o_detail = _view(_core("DetailView"), overridden)
    assert _operation_requirements(o_detail) == STRICT  # ViewSet read override (stricter)
    assert _operation_requirements(o_update) == READ  # ViewSet write override (more permissive)
    assert _operation_requirements(o_delete) == STRICT  # exact entry beats the family pair
    assert _operation_requirements(o_list) == READ


def test_renamed_key_uses_its_literal_registration(registry, sfx, no_db):
    from crud_views.lib.ancestors import _operation_requirements, _validate_action_declarations

    _, book_vs = _nested(sfx, policy=AncestorPolicy(actions={"books": STRICT}))
    renamed = _view(_core("ListView"), book_vs, key="books")
    assert _operation_requirements(renamed) == STRICT
    _validate_action_declarations(book_vs)  # 'books' is literally registered

    _, wrong = _nested(sfx + "w", policy=AncestorPolicy(actions={"list": STRICT}))
    _view(_core("ListView"), wrong, key="books")
    with pytest.raises(ImproperlyConfigured, match=r"actions\['list'\].*no registered endpoint"):
        _validate_action_declarations(wrong)


def test_card_only_accepts_card_and_rejects_unregistered_list(registry, sfx, no_db):
    from crud_views.lib.ancestors import _operation_requirements, _validate_action_declarations

    _, card_only = _nested(sfx, policy=AncestorPolicy(actions={"card": STRICT}))
    card = _view(_core("CardListView"), card_only)
    _validate_action_declarations(card_only)
    # navigation alias is preserved, and the alias target keeps Card's own key and entry
    assert card_only.get_view_class("list") is card
    assert _operation_requirements(card_only.get_view_class("list")) == STRICT

    _, alias_misused = _nested(sfx + "a", policy=AncestorPolicy(actions={"list": STRICT}))
    alias_card = _view(_core("CardListView"), alias_misused)
    assert alias_misused.get_view_class("list") is alias_card  # alias exists...
    with pytest.raises(ImproperlyConfigured, match=r"actions\['list'\].*'card'"):  # ...but is no registration
        _validate_action_declarations(alias_misused)
    assert _operation_requirements(alias_card) == READ  # never another endpoint's entry


def test_card_and_list_entries_stay_independent(registry, sfx, no_db):
    from crud_views.lib.ancestors import _operation_requirements, _validate_action_declarations

    _, both = _nested(sfx, policy=AncestorPolicy(actions={"card": STRICT}))
    card = _view(_core("CardListView"), both)
    assert _operation_requirements(card) == STRICT
    # adding a real list later never retargets Card, and list uses its own (family) pair
    real_list = _view(_core("ListView"), both)
    _validate_action_declarations(both)
    assert _operation_requirements(card) == STRICT
    assert _operation_requirements(real_list) == READ
    assert both.get_view_class("list") is real_list

    _, as_list = _nested(sfx + "l", policy=AncestorPolicy(actions={"list": STRICT}))
    card_as_list = _view(_core("CardListView"), as_list, key="list")
    _validate_action_declarations(as_list)  # CardListView actually registered as 'list'
    assert _operation_requirements(card_as_list) == STRICT


@pytest.mark.parametrize("cascade", [True, False, None])
@pytest.mark.parametrize("all_none", [False, True], ids=["protected", "all-none"])
@pytest.mark.parametrize("viewset_kind", ["core", "guardian"])
def test_nested_custom_endpoint_requires_an_exact_entry(registry, sfx, no_db, cascade, all_none, viewset_kind):
    from crud_views.lib.ancestors import _operation_requirements, _validate_action_declarations
    from crud_views_guardian.lib.viewset import GuardianViewSet

    viewset_cls = GuardianViewSet if viewset_kind == "guardian" else ViewSet
    pub_vs, book_vs = _nested(sfx, policy=AncestorPolicy(cascade=cascade), viewset_cls=viewset_cls)
    if all_none:
        pub_vs.ancestor_policy = AncestorPolicy(provider="none")
    approve = _view(_core("ActionView"), book_vs, key="approve")
    with pytest.raises(ImproperlyConfigured, match=rf"{book_vs.name}.*'approve'.*AncestorPermissions"):
        _operation_requirements(approve)
    _validate_action_declarations(book_vs)  # missing entries are reported per endpoint, unknown keys per ViewSet

    _, declared = _nested(sfx + "d", policy=AncestorPolicy(cascade=cascade, actions={"approve": WRITE}))
    declared_approve = _view(_core("ActionView"), declared, key="approve")
    assert _operation_requirements(declared_approve) == WRITE


# ── completed-registry checks and the URLconf readiness barrier ──────────────


def _action_messages(*viewsets):
    from crud_views.checks import _ancestor_action_messages

    return [(m.id, m.obj.name) for m in _ancestor_action_messages(viewsets)]


def test_private_completed_registry_action_checks(registry, sfx, no_db):
    _, unknown = _nested(sfx + "u", policy=AncestorPolicy(actions={"nope": READ}))
    _view(_core("ListView"), unknown)
    _, missing = _nested(sfx + "m")
    _view(_core("ActionView"), missing, key="approve")
    _, complete = _nested(sfx + "c", policy=AncestorPolicy(actions={"approve": WRITE}))
    _view(_core("ActionView"), complete, key="approve")
    _view(_core("ListView"), complete)
    _, card_only = _nested(sfx + "k", policy=AncestorPolicy(actions={"list": READ}))
    _view(_core("CardListView"), card_only)
    top = ViewSet(model=Publisher, name=f"op_top_{sfx}")
    _view(_core("ActionView"), top, key="approve")  # top-level custom endpoints need no declaration

    assert _action_messages(unknown, missing, complete, card_only, top) == [
        ("viewset.E267", unknown.name),
        ("viewset.E268", missing.name),
        ("viewset.E267", card_only.name),
    ]


def _write_module(tmp_path, name, source):
    (tmp_path / f"{name}.py").write_text(source)


@pytest.fixture
def late_modules(tmp_path, monkeypatch, sfx):
    """Root URLconf → included URLconf → late view module that registers ``approve`` on an early ViewSet."""
    monkeypatch.syspath_prepend(str(tmp_path))
    names = SimpleNamespace(root=f"op_root_{sfx}", inner=f"op_inner_{sfx}", late=f"op_late_{sfx}")
    yield names
    for name in vars(names).values():
        sys.modules.pop(name, None)
    clear_url_caches()


def _late_view_source(viewset_name):
    return (
        "from crud_views.lib.viewset import ViewSet\n"
        "from crud_views.lib.views import ActionView\n"
        f"vs = ViewSet.get_viewset({viewset_name!r})\n"
        "class Approve(ActionView):\n"
        "    cv_viewset = vs\n"
        "    cv_key = 'approve'\n"
        "    cv_context_actions = []\n"
    )


def _ours(messages, *viewsets):
    names = {vs.name for vs in viewsets}
    return sorted((m.id, m.obj.name) for m in messages if getattr(m.obj, "name", None) in names)


def test_barrier_imports_root_and_included_urlconfs_before_snapshot(registry, sfx, no_db, tmp_path, late_modules):
    from crud_views.checks import check_ancestor_declarations

    _, early = _nested(sfx, policy=AncestorPolicy(actions={"approve": WRITE}))
    _view(_core("ListView"), early)
    _, invalid = _nested(sfx + "i", policy=AncestorPolicy(actions={"nope": WRITE}))
    _view(_core("ListView"), invalid)
    _write_module(tmp_path, late_modules.late, _late_view_source(early.name))
    _write_module(tmp_path, late_modules.inner, f"import {late_modules.late}\nurlpatterns = []\n")
    _write_module(
        tmp_path,
        late_modules.root,
        f"from django.urls import include, path\nurlpatterns = [path('x/', include({late_modules.inner!r}))]\n",
    )
    assert not early.is_view_registered("approve")
    with override_settings(ROOT_URLCONF=late_modules.root):
        clear_url_caches()
        first = check_ancestor_declarations()
        assert early.is_view_registered("approve")  # registered by the late import, not reported missing
        second = check_ancestor_declarations()  # repeated checks: same answer, no retained ready flag
    assert _ours(first, early, invalid) == [("viewset.E267", invalid.name)]
    assert _ours(second, early, invalid) == _ours(first, early, invalid)


def test_absent_urlconf_defers_only_completion_dependent_checks(registry, sfx, no_db):
    from crud_views.checks import check_ancestor_declarations

    _, invalid = _nested(sfx, policy=AncestorPolicy(actions={"nope": WRITE}))
    _view(_core("ActionView"), invalid, key="approve")
    orphan = ViewSet(model=Book, name=f"op_orphan_{sfx}", parent=ParentViewSet(name=f"op_later_{sfx}"))
    cyclic = ViewSet(model=Book, name=f"op_cyc_{sfx}", parent=ParentViewSet(name=f"op_cyc_{sfx}"))
    with override_settings(ROOT_URLCONF=None):
        messages = check_ancestor_declarations()
    # action keys, missing entries and unresolved parents wait for completion; a cycle is reported now
    assert _ours(messages, invalid, orphan, cyclic) == [("viewset.E266", cyclic.name)]


def test_failed_urlconf_import_is_not_reported_as_completed(registry, sfx, no_db, tmp_path, late_modules):
    from crud_views.checks import check_ancestor_declarations

    _, early = _nested(sfx, policy=AncestorPolicy(actions={"approve": WRITE}))
    _view(_core("ListView"), early)
    _write_module(tmp_path, late_modules.root, "raise RuntimeError('broken urlconf')\n")
    with override_settings(ROOT_URLCONF=late_modules.root):
        clear_url_caches()
        messages = check_ancestor_declarations()
    assert _ours(messages, early) == []  # no misleading missing-action error for the never-imported view


def test_reentrant_check_during_urlconf_import_defers(registry, sfx, no_db, tmp_path, late_modules):
    _, early = _nested(sfx, policy=AncestorPolicy(actions={"approve": WRITE}))
    _view(_core("ListView"), early)
    _write_module(tmp_path, late_modules.late, _late_view_source(early.name))
    _write_module(
        tmp_path,
        late_modules.root,
        "from crud_views.checks import check_ancestor_declarations\n"
        "DURING_IMPORT = check_ancestor_declarations()\n"
        f"import {late_modules.late}\n"
        "urlpatterns = []\n",
    )
    from crud_views.checks import check_ancestor_declarations

    with override_settings(ROOT_URLCONF=late_modules.root):
        clear_url_caches()
        after = check_ancestor_declarations()
        during = sys.modules[late_modules.root].DURING_IMPORT
    assert _ours(during, early) == []  # the partial URLconf is not a completed registry
    assert _ours(after, early) == []


# ── request-level selection and precedence ───────────────────────────────────


def _three_level(sfx, *, pub=None, book=None, note=None):
    """Core Publisher → Book → BookNote with plain views; policies per level."""
    from crud_views.lib.views import ActionView, ListView, UpdateView

    def build(_):
        pub_vs = ViewSet(model=Publisher, name=f"sel_pub_{sfx}", ancestor_policy=pub or AncestorPolicy())
        _view(ListView, pub_vs)
        book_vs = ViewSet(
            model=Book,
            name=f"sel_book_{sfx}",
            parent=ParentViewSet(name=pub_vs.name, attribute="publisher"),
            ancestor_policy=book or AncestorPolicy(),
        )
        _view(ListView, book_vs)
        note_vs = ViewSet(
            model=BookNote,
            name=f"sel_note_{sfx}",
            parent=ParentViewSet(name=book_vs.name, attribute="book"),
            ancestor_policy=note or AncestorPolicy(),
        )
        _view(ListView, note_vs)
        _view(UpdateView, note_vs, fields=["note"])
        _view(ActionView, note_vs, key="approve")
        ns = SimpleNamespace(pub_vs=pub_vs, book_vs=book_vs, note_vs=note_vs)

        def url(key, w, **extra):
            kwargs = {f"{pub_vs.name}_pk": w.pub.pk, f"{book_vs.name}_pk": w.book.pk, **extra}
            return _url(note_vs, key, **kwargs)

        ns.url = url
        return ns, [pub_vs, book_vs, note_vs]

    return isolated_routes(build)


@pytest.fixture
def chain_world(db):
    pub = Publisher.objects.create(name="Pub")
    book = Book.objects.create(title="Book", publisher=pub)
    note = BookNote.objects.create(book=book, note="note")
    return SimpleNamespace(pub=pub, book=book, note=note)


def _gates(events):
    """Ancestor-model permission checks, in order (other checks, e.g. rendered buttons, are ignored)."""
    return [perm for kind, perm in events if kind == "has_perm" and perm.endswith(("_publisher", "_book"))]


def _status(ns, user, key, w, **extra):
    return _client(user).get(ns.url(key, w, **extra)).status_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("global_cascade", "requested", "full"),
    [
        (True, None, True),
        (True, True, True),
        (True, False, False),
        (False, None, False),
        (False, False, False),
        (False, True, True),
    ],
)
def test_requested_cascade_overrides_global_in_both_directions(
    chain_world, events, monkeypatch, sfx, global_cascade, requested, full
):
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", global_cascade)
    with _three_level(sfx, note=AncestorPolicy(cascade=requested)) as ns:
        nearest_only = _user(f"u_near_{sfx}", (Book, "view"))
        both = _user(f"u_both_{sfx}", (Book, "view"), (Publisher, "view"))
        events.clear()
        assert _status(ns, nearest_only, "list", chain_world) == (403 if full else 200)
        if not full:
            # nearest-only: no higher permission evaluation, but the higher ancestor is still resolved
            assert "app.view_publisher" not in _gates(events)
            assert ("queryset", ns.pub_vs.name) in events
        assert _status(ns, both, "list", chain_world) == 200


@pytest.mark.django_db
def test_ancestor_cascade_cannot_stop_descendant_traversal(chain_world, events, sfx):
    # Book's own cascade describes requests to Book; a request to BookNote still checks every protected level
    with _three_level(sfx, book=AncestorPolicy(cascade=False)) as ns:
        nearest_only = _user(f"u_iso_{sfx}", (Book, "view"))
        assert _status(ns, nearest_only, "list", chain_world) == 403
        assert "app.view_publisher" in _gates(events)


@pytest.mark.django_db
@pytest.mark.parametrize("cascade", [True, False])
def test_none_middle_level_does_not_consume_the_nearest_position(chain_world, events, sfx, cascade):
    with _three_level(sfx, book=AncestorPolicy(provider="none"), note=AncestorPolicy(cascade=cascade)) as ns:
        # Write: the nearest *protected* ancestor (Publisher) needs change, Book has no gate in either mode
        pub_view = _user(f"u_pv_{sfx}", (Publisher, "view"))
        pub_change = _user(f"u_pc_{sfx}", (Publisher, "change"))
        events.clear()
        assert _status(ns, pub_view, "update", chain_world, pk=chain_world.note.pk) == 403
        assert _gates(events) == ["app.change_publisher"]
        assert _status(ns, pub_change, "update", chain_world, pk=chain_world.note.pk) == 200
        assert "app.view_book" not in _gates(events) and "app.change_book" not in _gates(events)


@pytest.mark.django_db
def test_all_none_chain_has_no_gate_but_validates_relationships(chain_world, events, sfx):
    with _three_level(sfx, pub=AncestorPolicy(provider="none"), book=AncestorPolicy(provider="none")) as ns:
        nobody = _user(f"u_none_{sfx}")
        assert _status(ns, nobody, "list", chain_world) == 200
        assert _gates(events) == []
        # relationships still hold: a Book of another Publisher is 404
        other = Book.objects.create(title="Other", publisher=Publisher.objects.create(name="P2"))
        mismatched = _url(
            ns.note_vs, "list", **{f"{ns.pub_vs.name}_pk": chain_world.pub.pk, f"{ns.book_vs.name}_pk": other.pk}
        )
        assert _client(nobody).get(mismatched).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("cascade", [True, False])
def test_denied_nearest_gate_never_substitutes_a_farther_grant(chain_world, events, sfx, cascade):
    with _three_level(sfx, note=AncestorPolicy(cascade=cascade)) as ns:
        farther_only = _user(f"u_far_{sfx}", (Publisher, "view"), (Publisher, "change"))
        events.clear()
        assert _status(ns, farther_only, "list", chain_world) == 403
        assert _gates(events)[-1] == "app.view_book"  # the stopping gate is the nearest one
        if cascade:  # outermost first: Publisher passed, then Book denied
            assert _gates(events) == ["app.view_publisher", "app.view_book"]


@pytest.mark.django_db
def test_editor_get_is_write_and_exact_entries_change_requirements(chain_world, sfx):
    with _three_level(sfx) as ns:
        readers = _user(f"u_r_{sfx}", (Book, "view"), (Publisher, "view"))
        writer = _user(f"u_w_{sfx}", (Book, "change"), (Publisher, "view"))
        assert _status(ns, readers, "update", chain_world, pk=chain_world.note.pk) == 403  # GET opens a Write form
        assert _status(ns, writer, "update", chain_world, pk=chain_world.note.pk) == 200
    with _three_level(sfx + "s", note=AncestorPolicy(actions={"update": STRICT})) as ns:
        writer = _user(f"u_ws_{sfx}", (Book, "change"), (Publisher, "view"))
        strict = _user(f"u_s_{sfx}", (Book, "change"), (Publisher, "change"))
        assert _status(ns, writer, "update", chain_world, pk=chain_world.note.pk) == 403
        assert _status(ns, strict, "update", chain_world, pk=chain_world.note.pk) == 200
    with _three_level(sfx + "p", note=AncestorPolicy(actions={"update": READ})) as ns:
        readers = _user(f"u_rp_{sfx}", (Book, "view"), (Publisher, "view"))
        assert _status(ns, readers, "update", chain_world, pk=chain_world.note.pk) == 200


@pytest.mark.django_db
@pytest.mark.parametrize("cascade", [True, False])
@pytest.mark.parametrize("all_none", [False, True], ids=["protected", "all-none"])
def test_nested_custom_request_without_entry_fails_before_any_lookup(chain_world, events, sfx, cascade, all_none):
    none = AncestorPolicy(provider="none")
    with _three_level(
        sfx, pub=none if all_none else None, book=none if all_none else None, note=AncestorPolicy(cascade=cascade)
    ) as ns:
        user = _user(f"u_c_{sfx}", (Book, "change"), (Publisher, "view"))
        with pytest.raises(ImproperlyConfigured, match=r"'approve'"):
            _client(user).get(ns.url("approve", chain_world, pk=chain_world.note.pk))
        assert [e for e in events if e[0] == "queryset"] == []


@pytest.mark.django_db
def test_nested_custom_request_with_entry_is_gated_by_it(chain_world, sfx):
    with _three_level(sfx, note=AncestorPolicy(actions={"approve": STRICT})) as ns:
        writer = _user(f"u_aw_{sfx}", (Book, "change"), (Publisher, "view"))
        strict = _user(f"u_as_{sfx}", (Book, "change"), (Publisher, "change"))
        assert _status(ns, writer, "approve", chain_world, pk=chain_world.note.pk) == 403
        assert _status(ns, strict, "approve", chain_world, pk=chain_world.note.pk) == 405  # gate passed: POST-only


@pytest.mark.django_db
def test_unknown_action_key_fails_nested_requests(chain_world, sfx):
    with _three_level(sfx, note=AncestorPolicy(actions={"nope": READ})) as ns:
        user = _user(f"u_k_{sfx}", (Book, "view"), (Publisher, "view"))
        with pytest.raises(ImproperlyConfigured, match=r"actions\['nope'\]"):
            _client(user).get(ns.url("list", chain_world))


@pytest.mark.django_db
def test_top_level_custom_request_needs_no_declaration(db, events, sfx):
    from crud_views.lib.views import ActionView

    def build(_):
        top = ViewSet(model=Publisher, name=f"sel_top_{sfx}")
        _view(_core("ListView"), top)
        _view(ActionView, top, key="approve")
        return SimpleNamespace(top=top), [top]

    with isolated_routes(build) as ns:
        pub = Publisher.objects.create(name="Top")
        response = _client(_user(f"u_t_{sfx}")).get(_url(ns.top, "approve", pk=pub.pk))
        assert response.status_code == 405  # reached the endpoint: no ancestor work, no declaration needed
        assert _gates(events) == []
