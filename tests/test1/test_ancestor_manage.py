"""
Phase 06.18 plan 09 Task 1 — nested manage admission and policy diagnostics.

Admission (D-45, A20): a nested manage request needs its ancestry (a Read endpoint: the selected ancestors'
``view``) AND the unchanged local manage gate (public settings, or the manage group). Neither replaces the other:

* public settings (``yes``, ``debug_only`` with DEBUG on) and manage-group membership never bypass a selected
  ancestor, and the local gate is not even reached when an ancestor denies;
* after ancestor success the local group gate still denies a non-member;
* a reached missing or mismatched ancestor is 404;
* both cascade modes select their own ancestors, all-none ancestry keeps the local gate and relationships, and
  top-level manage is unchanged.

Diagnostics (D-19, D-27, D-34, D-41): the manage page shows the ViewSet's *declared* ancestor policy in its two
scopes — as an ancestor of nested requests (provider, ancestor fallback) and for requests to this ViewSet (cascade,
read, write, actions) — with each inheritable value's declared ``None`` next to the effective default. It is
configuration only, never an authorization result, and rendering it loads no ancestor. Guardian's local per-view
fallback and the strict ViewSet helper stay separate rows; parent-only nested create reports its local fallback as
not applicable whatever the ancestor fallback is.

Every fixture builds fresh ViewSets behind a temporary ROOT_URLCONF and restores registry and caches.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group
from django.test import override_settings
from guardian.shortcuts import assign_perm

import tests.test1.project.urls  # noqa: F401 - registers the shared app ViewSets before any registry snapshot
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1 import test_ancestor_authorization as _auth
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

events = _auth.events  # ordered ViewSet queryset / has_perm spy of plan 01

KINDS = ("core", "guardian")
MISSING = 987654


# ── routes ───────────────────────────────────────────────────────────────────


def _view(bases, vs, key=None, **attrs):
    bases = bases if isinstance(bases, tuple) else (bases,)
    attrs = {"cv_viewset": vs, "cv_list_actions": [], "cv_context_actions": [], "__module__": __name__, **attrs}
    if key is not None:
        attrs.update(cv_key=key, cv_path=key)
    return type(f"V_{vs.name}_{key or bases[-1].cv_key}", bases, attrs)


def _build(sfx):
    """Per kind (core ``ViewSet`` / ``GuardianViewSet``) a protected Publisher → Book → BookNote chain and an
    all-none chain (Publisher and Book ``provider="none"``). Guardian Book: ancestor fallback on, its own detail
    view locally permissive; Guardian BookNote: locally strict detail plus a parent-only nested create. A separate
    core BookNote declares every request field explicitly."""
    from crud_views.lib.views import (
        ActionView,
        CreateViewParentMixin,
        DetailView,
        ListView,
    )
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    ns = SimpleNamespace(chains={}, routed=[])
    for kind in KINDS:
        vs_class = GuardianViewSet if kind == "guardian" else ViewSet
        list_base = GuardianListViewPermissionRequired if kind == "guardian" else ListView
        detail_base = GuardianDetailViewPermissionRequired if kind == "guardian" else DetailView
        for chain in ("protected", "none"):
            none = AncestorPolicy(provider="none") if chain == "none" else None
            tag = f"am{kind[0]}{chain[0]}{sfx}"
            grand = vs_class(model=Publisher, name=f"{tag}pub", ancestor_policy=none or AncestorPolicy())
            _view(list_base, grand)
            mid_policy = none or (AncestorPolicy(accept_global_perms=True) if kind == "guardian" else AncestorPolicy())
            mid = vs_class(
                model=Book,
                name=f"{tag}book",
                parent=ParentViewSet(name=grand.name, attribute="publisher"),
                ancestor_policy=mid_policy,
            )
            _view(list_base, mid)
            _view(detail_base, mid, cv_guardian_accept_global_perms=True)
            leaf = vs_class(model=BookNote, name=f"{tag}note", parent=ParentViewSet(name=mid.name, attribute="book"))
            _view(list_base, leaf)
            _view(detail_base, leaf)
            if kind == "guardian":
                _view((CreateViewParentMixin, GuardianCreateViewPermissionRequired), leaf, fields=["note"])
            ns.chains[(kind, chain)] = SimpleNamespace(grand=grand, mid=mid, leaf=leaf)
            ns.routed += [grand, mid, leaf]
    # one core leaf that declares every request-scope field explicitly
    base = ns.chains[("core", "protected")]
    declared = ViewSet(
        model=BookNote,
        name=f"amdecl{sfx}",
        parent=ParentViewSet(name=base.mid.name, attribute="book"),
        ancestor_policy=AncestorPolicy(
            cascade=False,
            read=AncestorPermissions(nearest="change", higher="view"),
            write=AncestorPermissions(nearest="change", higher="change"),
            actions={"approve": AncestorPermissions(nearest="delete", higher="view")},
        ),
    )
    _view(ListView, declared)
    _view(ActionView, declared, key="approve")
    ns.declared = declared
    ns.routed.append(declared)
    return ns, ns.routed


@pytest.fixture
def routes():
    with isolated_routes(_build) as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Hitchhiker", publisher=penguin)
    foreign = Book.objects.create(title="Foreign", publisher=other)
    note = BookNote.objects.create(book=book, note="note")
    return SimpleNamespace(penguin=penguin, other=other, book=book, foreign=foreign, note=note)


def _leaf_manage(chain, publisher_pk, book_pk, leaf=None):
    leaf = leaf or chain.leaf
    return _url(leaf, "manage", **{f"{chain.grand.name}_pk": publisher_pk, f"{chain.mid.name}_pk": book_pk})


def _mid_manage(chain, publisher_pk):
    return _url(chain.mid, "manage", **{f"{chain.grand.name}_pk": publisher_pk})


def _top_manage(chain):
    return _url(chain.grand, "manage")


# ── actors, grants, modes and spies ──────────────────────────────────────────


def _actor(username, *, member=False):
    user = _user(username)
    if member:
        user.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return user


def _grant(kind, user, model, obj):
    """``view`` on one ancestor: a model permission for the core provider, an object grant for Guardian."""
    codename = f"app.view_{model._meta.model_name}"
    if kind == "guardian":
        assign_perm(codename, user, obj)
    else:
        _auth_add_model_perm(user, model)


def _auth_add_model_perm(user, model):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.get_for_model(model)
    user.user_permissions.add(Permission.objects.get(content_type=ct, codename=f"view_{ct.model}"))


def _grant_chain(kind, user, world, *, grand=True, mid=True):
    if grand:
        _grant(kind, user, Publisher, world.penguin)
    if mid:
        _grant(kind, user, Book, world.book)
    return user


@pytest.fixture
def mode(monkeypatch):
    """Patch the import-time settings singleton; ``group`` = debug_only with DEBUG off (the group gate)."""

    def set_mode(value):
        monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes" if value == "yes" else "debug_only")

    return set_mode


def _debug(value):
    return override_settings(DEBUG=value == "debug_on")


@pytest.fixture(params=[True, False], ids=["full", "nearest"])
def cascade(request, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", request.param)
    return request.param


@pytest.fixture
def manage_events(monkeypatch, events):
    from crud_views.lib.views.manage import ManageView

    original = ManageView.has_permission

    def gate_spy(self):
        events.append(("manage_gate", self.cv_viewset.name))
        return original(self)

    monkeypatch.setattr(ManageView, "has_permission", gate_spy)
    return events


def _gate_events(recorded):
    return [event for event in recorded if event[0] == "manage_gate"]


def _querysets(recorded):
    return [event for event in recorded if event[0] == "queryset"]


# ── admission: public settings and group membership never bypass ancestry ───


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("public", ["yes", "debug_on"])
def test_public_manage_settings_do_not_bypass_selected_ancestors(routes, world, mode, manage_events, kind, public):
    chain = routes.chains[(kind, "protected")]
    mode(public)
    stranger = _actor(f"am_pub_stranger_{kind}_{public}")
    reader = _grant_chain(kind, _actor(f"am_pub_reader_{kind}_{public}"), world)
    with _debug(public):
        assert _client(stranger).get(_leaf_manage(chain, world.penguin.pk, world.book.pk)).status_code == 403
        assert _gate_events(manage_events) == []  # the local gate is never reached on ancestor denial
        anonymous = _client(None).get(_leaf_manage(chain, world.penguin.pk, world.book.pk))
        assert anonymous.status_code == 302 and "/accounts/login/" in anonymous["Location"]
        assert _client(reader).get(_leaf_manage(chain, world.penguin.pk, world.book.pk)).status_code == 200
        # top-level manage stays public without any grant
        assert _client(stranger).get(_top_manage(chain)).status_code == 200
        assert _client(None).get(_top_manage(chain)).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_group_membership_does_not_bypass_selected_ancestors(routes, world, mode, manage_events, cascade, kind):
    chain = routes.chains[(kind, "protected")]
    mode("group")
    url = _leaf_manage(chain, world.penguin.pk, world.book.pk)
    member = _actor(f"am_grp_member_{kind}", member=True)
    assert _client(member).get(url).status_code == 403
    assert _gate_events(manage_events) == []
    # the nearest ancestor alone: enough in nearest-only mode, not under full cascade
    nearest = _grant_chain(kind, _actor(f"am_grp_nearest_{kind}", member=True), world, grand=False)
    assert _client(nearest).get(url).status_code == (403 if cascade else 200)
    # a farther grant never substitutes for the nearest one
    farther = _grant_chain(kind, _actor(f"am_grp_farther_{kind}", member=True), world, mid=False)
    assert _client(farther).get(url).status_code == 403
    both = _grant_chain(kind, _actor(f"am_grp_both_{kind}", member=True), world)
    assert _client(both).get(url).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_local_manage_gate_still_denies_after_ancestor_success(routes, world, mode, manage_events, cascade, kind):
    chain = routes.chains[(kind, "protected")]
    mode("group")
    outsider = _grant_chain(kind, _actor(f"am_local_outsider_{kind}"), world)
    del manage_events[:]
    assert _client(outsider).get(_leaf_manage(chain, world.penguin.pk, world.book.pk)).status_code == 403
    gate = ("manage_gate", chain.leaf.name)
    assert gate in manage_events
    # both ancestors were resolved (and gated) before the local gate ran
    assert manage_events.index(("queryset", chain.grand.name)) < manage_events.index(("queryset", chain.mid.name))
    assert manage_events.index(("queryset", chain.mid.name)) < manage_events.index(gate)
    # the same ancestor grants with membership pass both gates
    outsider.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    assert _client(outsider).get(_leaf_manage(chain, world.penguin.pk, world.book.pk)).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("public", ["yes", "group"])
def test_reached_missing_or_mismatched_ancestor_is_404(routes, world, mode, manage_events, cascade, kind, public):
    chain = routes.chains[(kind, "protected")]
    mode(public)
    member = _grant_chain(kind, _actor(f"am_404_{kind}_{public}", member=True), world)
    client = _client(member)
    assert client.get(_leaf_manage(chain, world.penguin.pk, MISSING)).status_code == 404
    assert client.get(_leaf_manage(chain, world.penguin.pk, world.foreign.pk)).status_code == 404  # other parent
    assert client.get(_leaf_manage(chain, MISSING, world.book.pk)).status_code == 404
    assert _gate_events(manage_events) == []


# ── all-none ancestry and top-level manage ───────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_all_none_manage_keeps_local_gate_and_relationships(routes, world, mode, manage_events, cascade, kind):
    chain = routes.chains[(kind, "none")]
    url = _leaf_manage(chain, world.penguin.pk, world.book.pk)
    mode("group")
    anonymous = _client(None).get(url)
    assert anonymous.status_code == 302 and "/accounts/login/" in anonymous["Location"]
    assert _querysets(manage_events) == []  # the manage gate's own early rule, before any lookup
    stranger = _actor(f"am_none_stranger_{kind}")
    assert _client(stranger).get(url).status_code == 403
    assert manage_events.index(("queryset", chain.mid.name)) < manage_events.index(("manage_gate", chain.leaf.name))
    member = _actor(f"am_none_member_{kind}", member=True)
    assert _client(member).get(url).status_code == 200
    assert _client(member).get(_leaf_manage(chain, world.penguin.pk, MISSING)).status_code == 404
    assert _client(member).get(_leaf_manage(chain, world.penguin.pk, world.foreign.pk)).status_code == 404
    mode("yes")
    assert _client(None).get(url).status_code == 200  # public settings stay public without protected ancestry


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_top_level_manage_gate_is_unchanged(routes, world, mode, manage_events, kind):
    chain = routes.chains[(kind, "protected")]
    mode("group")
    anonymous = _client(None).get(_top_manage(chain))
    assert anonymous.status_code == 302 and "/accounts/login/" in anonymous["Location"]
    assert _client(_actor(f"am_top_stranger_{kind}")).get(_top_manage(chain)).status_code == 403
    assert _client(_actor(f"am_top_member_{kind}", member=True)).get(_top_manage(chain)).status_code == 200
    assert _querysets(manage_events) == []  # no ancestor work at top level


# ── diagnostics: declared policy, effective defaults, separate local scopes ──


def _flat(response) -> str:
    return re.sub(r"\s+", " ", response.content.decode())


def _policy_table(response) -> dict[str, tuple[str, str]]:
    """``setting -> (declared, effective)`` rows of the rendered ancestor policy table."""
    match = re.search(r'<table class="table table-striped" id="cv-ancestor-policy">(.*?)</table>', _flat(response))
    assert match, "ancestor policy table missing"
    rows = re.findall(r"<tr> <td>(.*?)</td> <td>(.*?)</td> <td>(.*?)</td> </tr>", match.group(1))
    return {name: (declared, effective) for name, declared, effective in rows}


def _member_with_chain(kind, world, username):
    return _grant_chain(kind, _actor(username, member=True), world)


DEFAULT_REQUESTS = {
    "cascade": {"declared": None, "effective": True},
    "read": {"declared": None, "effective": {"nearest": "view", "higher": "view"}},
    "write": {"declared": None, "effective": {"nearest": "change", "higher": "view"}},
    "actions": {},
}


@pytest.mark.django_db
def test_manage_reports_declared_none_next_to_effective_defaults(routes, world, mode):
    chain = routes.chains[("core", "protected")]
    mode("yes")
    response = _client(_member_with_chain("core", world, "am_diag_default")).get(
        _leaf_manage(chain, world.penguin.pk, world.book.pk)
    )
    assert response.status_code == 200
    assert response.context["ancestor_policy"] == {
        "as_ancestor": {"provider": None, "effective_provider": "model", "accept_global_perms": False},
        "requests": DEFAULT_REQUESTS,
    }
    rows = _policy_table(response)
    assert rows["provider"] == ("None (ViewSet class default)", "model")
    assert rows["accept_global_perms"] == ("False", "False")
    assert rows["cascade"] == ("None (global setting)", "True")
    assert rows["read"] == ("None (global setting)", "nearest: view, higher: view")
    assert rows["write"] == ("None (global setting)", "nearest: change, higher: view")
    assert rows["actions"] == ("none declared", "—")
    assert "Configuration only" in _flat(response)


@pytest.mark.django_db
def test_manage_effective_defaults_follow_the_global_settings_while_declared_stays_none(
    routes, world, mode, monkeypatch
):
    chain = routes.chains[("core", "protected")]
    mode("yes")
    strict = AncestorPermissions(nearest="change", higher="change")
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", False)
    monkeypatch.setattr(crud_views_settings, "ancestor_write_permissions", strict)
    response = _client(_grant_chain("core", _actor("am_diag_global"), world, grand=False)).get(
        _leaf_manage(chain, world.penguin.pk, world.book.pk)
    )
    assert response.status_code == 200
    requests = response.context["ancestor_policy"]["requests"]
    assert requests["cascade"] == {"declared": None, "effective": False}
    assert requests["write"] == {"declared": None, "effective": {"nearest": "change", "higher": "change"}}
    assert requests["read"] == DEFAULT_REQUESTS["read"]
    rows = _policy_table(response)
    assert rows["cascade"] == ("None (global setting)", "False")
    assert rows["write"] == ("None (global setting)", "nearest: change, higher: change")


@pytest.mark.django_db
def test_manage_reports_explicit_request_declarations(routes, world, mode):
    chain = routes.chains[("core", "protected")]
    mode("yes")
    user = _actor("am_diag_declared")
    for model in (Publisher, Book):
        _auth_add_model_perm(user, model)
    from django.contrib.auth.models import Permission

    user.user_permissions.add(Permission.objects.get(codename="change_book"))
    response = _client(user).get(_leaf_manage(chain, world.penguin.pk, world.book.pk, leaf=routes.declared))
    assert response.status_code == 200
    assert response.context["ancestor_policy"]["requests"] == {
        "cascade": {"declared": False, "effective": False},
        "read": {
            "declared": {"nearest": "change", "higher": "view"},
            "effective": {"nearest": "change", "higher": "view"},
        },
        "write": {
            "declared": {"nearest": "change", "higher": "change"},
            "effective": {"nearest": "change", "higher": "change"},
        },
        "actions": {"approve": {"nearest": "delete", "higher": "view"}},
    }
    rows = _policy_table(response)
    assert rows["cascade"] == ("False", "False")
    assert rows["read"] == ("nearest: change, higher: view", "nearest: change, higher: view")
    assert rows["actions[approve]"] == ("nearest: delete, higher: view", "nearest: delete, higher: view")
    assert "actions" not in rows  # the "none declared" row is only for an empty map


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_top_level_manage_reports_request_scope_not_applicable(routes, world, mode, kind):
    chain = routes.chains[(kind, "protected")]
    mode("yes")
    response = _client(_actor(f"am_diag_top_{kind}")).get(_top_manage(chain))
    assert response.status_code == 200
    provider = "guardian" if kind == "guardian" else "model"
    assert response.context["ancestor_policy"] == {
        "as_ancestor": {"provider": None, "effective_provider": provider, "accept_global_perms": False},
        "requests": None,
    }
    rows = _policy_table(response)
    assert rows["provider"] == ("None (ViewSet class default)", provider)
    assert "cascade" not in rows and "read" not in rows
    assert "not applicable: top-level ViewSet" in _flat(response)


@pytest.mark.django_db
def test_guardian_manage_separates_ancestor_fallback_from_local_view_fallback(routes, world, mode):
    """The Book ancestor fallback (on) neither copies into nor overrides the BookNote local view rows, and the
    Book's locally permissive detail does not imply a Publisher ancestor fallback."""
    chain = routes.chains[("guardian", "protected")]
    mode("yes")
    client = _client(_member_with_chain("guardian", world, "am_diag_guardian"))

    leaf = client.get(_leaf_manage(chain, world.penguin.pk, world.book.pk))
    assert leaf.status_code == 200
    # the leaf's own declaration: no ancestor fallback (the parent's is reported on the parent row only)
    assert leaf.context["ancestor_policy"]["as_ancestor"] == {
        "provider": None,
        "effective_provider": "guardian",
        "accept_global_perms": False,
    }
    assert leaf.context["guardian_config"]["ancestor_policy"] == {"provider": "guardian", "accept_global_perms": False}
    assert leaf.context["guardian_config"]["parent_viewset"] == (
        f"{chain.mid.name} (ancestor provider: guardian + model fallback)"
    )
    views = leaf.context["views"]
    assert dict(views["create"]["guardian_policy"]) == {
        "global_fallback_applicable": False,  # parent-only nested create: no local fallback to report
        "cv_guardian_accept_global_perms": None,
        "effective_policy": "not applicable",
    }
    assert dict(views["detail"]["guardian_policy"])["effective_policy"] == "strict"
    assert leaf.context["guardian_config"]["get_objects_for_user"]["accept_global_perms"] is False
    content = _flat(leaf)
    assert "<tr> <td>create</td> <td>—</td> <td>not applicable</td> </tr>" in content
    assert "<tr> <td>detail</td> <td>False</td> <td>strict: object and group grants only</td> </tr>" in content
    assert _policy_table(leaf)["accept_global_perms"] == ("False", "False")

    mid = client.get(_mid_manage(chain, world.penguin.pk))
    assert mid.status_code == 200
    assert mid.context["ancestor_policy"]["as_ancestor"]["accept_global_perms"] is True
    assert _policy_table(mid)["accept_global_perms"] == ("True", "True")
    # its parent (the Publisher) has no ancestor fallback although the Book detail is locally permissive
    assert mid.context["guardian_config"]["parent_viewset"] == f"{chain.grand.name} (ancestor provider: guardian)"
    assert dict(mid.context["views"]["detail"]["guardian_policy"])["effective_policy"] == "global fallback"
    mid_content = _flat(mid)
    assert (
        "<tr> <td>detail</td> <td>True</td> <td>global fallback: model permissions accepted</td> </tr>" in mid_content
    )
    assert "strict: object and group grants only; global model permissions are not accepted" in mid_content


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_rendering_diagnostics_loads_no_farther_ancestor(routes, world, mode, events, kind):
    chain = routes.chains[(kind, "protected")]
    mode("yes")
    client = _client(_member_with_chain(kind, world, f"am_diag_queries_{kind}"))
    del events[:]
    assert client.get(_leaf_manage(chain, world.penguin.pk, world.book.pk)).status_code == 200
    # each ancestor is loaded once, by the request guard; the diagnostics only read declarations
    assert _querysets(events) == [("queryset", chain.grand.name), ("queryset", chain.mid.name)]
