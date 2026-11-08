"""Bounded rendering helpers and manage diagnostics of ancestor authorization.

The existing immediate-parent helpers (collection link, create button, ``cv_create_has_access``, cancel) evaluate only
the immediate parent's gate (``immediate_parent_has_permission``): that parent's provider and ancestor fallback, with
the target operation's nearest requirement. A ``none`` parent passes without walking farther; the request still
authorizes the whole chain. Actor, state and custom denials stay; missing parent context denies; an invalid
configuration raises. Manage pages show the declared ancestor policy separately from the endpoint-local Guardian
fallback and make no access claim.
"""

import re
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from crud_views.lib.view.ancestors import immediate_parent_has_permission
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1 import test_guardian_parent_none as parent_none
from tests.test1.ancestor_cases import ancestor_routes, ancestor_scope, chain_objects
from tests.test1.app.models import Book, Genre, Publisher
from tests.test1.test_guardian_parent_none import _url, _user

pn = parent_none.pn
pn_strict = parent_none.pn_strict


def _fresh(user):
    return User.objects.get(pk=user.pk)  # drop Django's per-instance permission cache


def _rendering_view(view_class, user, **kwargs):
    """An initialized (not dispatched) view of ``view_class``, as a page rendering a cancel/control would be."""
    request = RequestFactory().get("/")
    request.user = user
    view = view_class()
    view.setup(request, **kwargs)
    view.object = None
    return view


def _gate_spy(monkeypatch, target):
    """Record the parent every immediate-parent gate of the Guardian helpers receives for ``target``."""
    from crud_views_guardian.lib import mixins, views

    calls: list = []
    original = mixins.immediate_parent_has_permission

    def gate(view_class, user, parent_obj):
        if view_class is target:
            calls.append(parent_obj)
        return original(view_class, user, parent_obj)

    for module in (mixins, views):
        monkeypatch.setattr(module, "immediate_parent_has_permission", gate)
    return calls


# ── existing helpers follow the immediate parent's provider and the target's nearest requirement ─────────────────


def _helper_routes(scope, parent_family):
    from crud_views.lib.views import CreateViewParentMixin
    from crud_views_guardian.lib.views import GuardianCreateViewPermissionRequired, GuardianListViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet

    parent_class = ViewSet if parent_family == "core" else GuardianViewSet
    pub = scope.viewset(parent_class, model=Publisher, name=scope.name("hlppub"))
    book = scope.viewset(
        GuardianViewSet,
        model=Book,
        name=scope.name("hlpbook"),
        parent=ParentViewSet(name=pub.name, attribute="publisher"),
    )
    book_list = scope.view(GuardianListViewPermissionRequired, book, name="HlpBookList")
    book_create = type(
        f"HlpBookCreate{scope.sfx}",
        (CreateViewParentMixin, GuardianCreateViewPermissionRequired),
        {"cv_viewset": book, "__module__": __name__, "fields": ["title"]},
    )
    return SimpleNamespace(pub=pub, book=book, List=book_list, Create=book_create)


def _grant(user, family, codename, publisher):
    if family == "model":
        user.user_permissions.add(Permission.objects.get(codename=f"{codename}_publisher"))
    else:
        from guardian.shortcuts import assign_perm

        assign_perm(f"app.{codename}_publisher", user, publisher)


def _helpers(routes, user, publisher):
    view = _rendering_view(routes.List, user, **{routes.book.parent.get_pk_name(): publisher.pk})
    return {
        "collection_link": routes.List._cv_child_link_has_access(user, publisher),
        "list_cancel": routes.List._cv_cancel_target_available(user, None, view),
        "create_button": routes.Create.cv_has_access(user, publisher),
        "create_has_access": routes.Create.cv_create_has_access(user, view, publisher),
        "create_cancel": routes.Create._cv_cancel_target_available(user, None, view),
    }


@pytest.mark.parametrize("parent_family", ["core", "guardian"])
@pytest.mark.parametrize("grant_family", ["model", "object"])
@pytest.mark.parametrize("codename", ["view", "change"])
@pytest.mark.django_db
def test_existing_helpers_use_immediate_parent_policy(parent_family, grant_family, codename, publisher_a):
    """Core parent: model grants; Guardian parent: object grants. Read targets need ``view``, create ``change``."""
    with ancestor_scope() as scope:
        routes = _helper_routes(scope, parent_family)
        user = _user("helper_actor")
        _grant(user, grant_family, codename, publisher_a)
        user = _fresh(user)

        provider_grant = grant_family == ("model" if parent_family == "core" else "object")
        read = provider_grant and codename == "view"
        write = provider_grant and codename == "change"
        assert _helpers(routes, user, publisher_a) == {
            "collection_link": read,
            "list_cancel": read,
            "create_button": write,
            "create_has_access": write,
            "create_cancel": write,
        }


# ── a none immediate parent: the helper passes without walking farther; the request denies ───────────────────────


@pytest.mark.django_db
def test_none_parent_helper_does_not_walk_farther(client):
    """Publisher → Book → BookNote (``none``) → Attachment: no grant at all."""
    viewset_kwargs = {2: {"ancestor_policy": AncestorPolicy(provider="none")}}
    with ancestor_routes("guardian", 3, viewset_kwargs) as routes:
        ancestors, _rows = chain_objects(3)
        note = ancestors[-1]
        user = _user("no_grants")
        endpoint_list = routes.endpoint.get_view_class("list")
        endpoint_create = routes.endpoint.get_view_class("create")
        higher_tables = {Publisher._meta.db_table, Book._meta.db_table, "guardian_userobjectpermission"}

        with CaptureQueriesContext(connection) as captured:
            assert immediate_parent_has_permission(endpoint_create, user, note) is True
            assert endpoint_create.cv_has_access(user, note) is True
            assert endpoint_create.cv_create_has_access(user, None, note) is True
            assert endpoint_list._cv_child_link_has_access(user, note) is True
        higher_queries = sum(1 for q in captured.captured_queries if any(t in q["sql"] for t in higher_tables))
        assert higher_queries == 0
        assert len(captured.captured_queries) == 0

        # the visible control may lead to a denied request: the farther protected Book decides there
        client.force_login(user)
        assert client.get(routes.url("create", ancestors)).status_code == 403
        assert client.get(routes.url("list", ancestors)).status_code == 403


# ── actor, state and custom denials stay; missing context denies; invalid configuration raises ───────────────────


@pytest.mark.django_db
def test_helper_retains_actor_state_custom_denials(pn, monkeypatch, publisher_a):
    view_kwargs = {pn.book_vs.parent.get_pk_name(): publisher_a.pk}
    user = _user("no_grants")
    view = _rendering_view(pn.BookList, user, **view_kwargs)
    assert pn.BookCreate.cv_create_has_access(user, view, publisher_a) is True  # none parent: no grant needed
    assert pn.BookList._cv_child_link_has_access(user, publisher_a) is True

    # actor: inactive and anonymous actors stay denied even though the parent has provider none
    inactive = _user("inactive", active=False)
    inactive_view = _rendering_view(pn.BookList, inactive, **view_kwargs)
    assert pn.BookCreate.cv_has_access(inactive, publisher_a) is False
    assert pn.BookCreate.cv_create_has_access(inactive, inactive_view, publisher_a) is False
    assert pn.BookList._cv_child_link_has_access(inactive, publisher_a) is False
    assert pn.BookCreate._cv_cancel_target_available(inactive, None, inactive_view) is False
    anonymous = AnonymousUser()
    assert pn.BookList._cv_child_link_has_access(anonymous, publisher_a) is False
    assert pn.BookList._cv_cancel_target_available(anonymous, None, view) is False

    # state: permission passes, the disabled action stays disabled (cancel includes the state)
    pn.state["enabled"] = False
    assert pn.BookCreate.cv_create_has_access(user, view, publisher_a) is True
    assert pn.BookCreate._cv_action_enabled_for_context(user, publisher_a) is False
    assert pn.BookCreate._cv_cancel_target_available(user, None, view) is False
    pn.state["enabled"] = True

    # custom: an application override of the target's own access still denies the link
    monkeypatch.setattr(pn.BookList, "cv_has_access", classmethod(lambda cls, user, obj=None: False))
    assert pn.BookList._cv_child_link_has_access(user, publisher_a) is False


@pytest.mark.parametrize("routes_name", ["pn", "pn_strict"])
@pytest.mark.django_db
def test_helper_missing_parent_context_denies(request, routes_name, publisher_a):
    """No parent object: deny for every provider and actor, including a superuser and a model-grant holder."""
    routes = request.getfixturevalue(routes_name)
    holder = _user("holder")
    routes.pub_vs.assign_perm("change", holder, publisher_a)
    holder = parent_none._grant_global(holder, "change_publisher", "view_publisher")
    for actor in (holder, _user("root", superuser=True)):
        assert immediate_parent_has_permission(routes.BookCreate, actor, None) is False
        assert immediate_parent_has_permission(routes.BookList, actor, None) is False
        assert routes.BookList._cv_child_link_has_access(actor, None) is False
        assert routes.BookCreate.cv_create_has_access(actor, None, None) is False


@pytest.mark.django_db
def test_helper_missing_parent_context_denies_under_a_model_parent(publisher_a):
    with ancestor_scope() as scope:
        routes = _helper_routes(scope, "core")
        holder = _fresh(_grant_model(_user("holder"), "view_publisher", "change_publisher"))
        assert immediate_parent_has_permission(routes.Create, holder, publisher_a) is True
        assert immediate_parent_has_permission(routes.Create, holder, None) is False
        assert routes.List._cv_child_link_has_access(holder, None) is False


def _grant_model(user, *codenames):
    for codename in codenames:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return user


@pytest.mark.django_db
def test_helper_invalid_configuration_raises(pn_strict, monkeypatch, publisher_a):
    """A requirement key missing from the parent's permission map is a configuration error, never False/True."""
    pn = pn_strict
    bad = AncestorPolicy(
        write=AncestorPermissions(nearest="view", higher="view"),
        actions={"create": AncestorPermissions(nearest="approve", higher="view")},
    )
    monkeypatch.setattr(pn.book_vs, "ancestor_policy", bad)
    pn.book_vs._validate_ancestor_policy()
    root = _user("root", superuser=True)
    view = _rendering_view(pn.BookList, root, **{pn.book_vs.parent.get_pk_name(): publisher_a.pk})

    for call in (
        lambda: immediate_parent_has_permission(pn.BookCreate, root, publisher_a),
        lambda: immediate_parent_has_permission(pn.BookCreate, root, None),
        lambda: pn.BookCreate.cv_has_access(root, publisher_a),
        lambda: pn.BookCreate.cv_create_has_access(root, view, publisher_a),
        lambda: pn.BookCreate._cv_cancel_target_available(root, None, view),
    ):
        with pytest.raises(ImproperlyConfigured, match="has no permission 'approve'"):
            call()


@pytest.mark.django_db
def test_helper_undeclared_custom_action_raises_under_a_none_parent(pn, publisher_a):
    """A ``none`` parent skips the permission, not the declaration: an undeclared nested custom endpoint raises."""
    from crud_views_guardian.lib.views import GuardianActionViewPermissionRequired

    approve = type(
        "PnApproveView",
        (GuardianActionViewPermissionRequired,),
        {
            "cv_viewset": pn.book_vs,
            "cv_key": "approve",
            "cv_path": "approve",
            "cv_permission": "change",
            "__module__": __name__,
        },
    )
    root = _user("root", superuser=True)
    for parent in (publisher_a, None):
        with pytest.raises(ImproperlyConfigured, match=r"declare ancestor_policy.actions\['approve'\]"):
            immediate_parent_has_permission(approve, root, parent)


# ── identity: the request-resolved parent; a single-FK child resolves its parent; ambiguous M2M denies ───────────


@pytest.mark.django_db
def test_helper_identity_and_ambiguous_m2m(pn_strict, client, monkeypatch, publisher_a, publisher_b):
    pn = pn_strict
    user = _user("granted")
    for codename in ("view", "change"):
        pn.pub_vs.assign_perm(codename, user, publisher_a)
    client.force_login(user)

    calls = _gate_spy(monkeypatch, pn.BookCreate)
    response = client.get(_url(pn.book_vs, "list", publisher_a.pk))
    assert response.status_code == 200
    resolved = response.context["view"]._cv_ancestor_objects[pn.pub_vs.name]
    assert calls, "the list page evaluated its create button"
    assert all(parent is resolved for parent in calls)

    # a supported single-FK child input resolves its own parent
    calls.clear()
    book = Book.objects.select_related("publisher").get(pk=Book.objects.create(title="Own", publisher=publisher_a).pk)
    assert pn.BookCreate.cv_has_access(user, book) is True
    assert pn.BookCreate.cv_create_has_access(user, None, book) is True
    assert len(calls) == 2
    assert all(parent is book.publisher for parent in calls)

    # an M2M child names no single parent: deny without evaluating any parent gate
    genre = Genre.objects.create(name="Shared")
    genre.publishers.add(publisher_a, publisher_b)
    genre_calls = _gate_spy(monkeypatch, pn.GenreCreate)
    assert pn.GenreCreate.cv_has_access(user, genre) is False
    assert pn.GenreCreate.cv_create_has_access(user, None, genre) is False
    assert genre_calls == []


# ── manage: declared ancestor policy separate from the endpoint-local fallback ──────────────────────────────────


def _manage_routes(scope, *, ancestor_fallback, view_flag):
    from crud_views.lib.views import CreateViewParentMixin, ListView
    from crud_views_guardian.lib.views import GuardianCreateViewPermissionRequired, GuardianListViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet

    pub = scope.viewset(
        GuardianViewSet,
        model=Publisher,
        name=scope.name("mgpub"),
        ancestor_policy=AncestorPolicy(accept_global_perms=ancestor_fallback),
    )
    scope.view(GuardianListViewPermissionRequired, pub, name="MgPubList", cv_guardian_accept_global_perms=view_flag)
    book = scope.viewset(
        GuardianViewSet,
        model=Book,
        name=scope.name("mgbook"),
        parent=ParentViewSet(name=pub.name, attribute="publisher"),
        ancestor_policy=AncestorPolicy(
            cascade=False,
            read=AncestorPermissions(nearest="view", higher="view"),
            actions={"create": AncestorPermissions(nearest="change", higher="change")},
        ),
    )
    scope.view(GuardianListViewPermissionRequired, book, name="MgBookList", cv_guardian_accept_global_perms=view_flag)
    type(
        f"MgBookCreate{scope.sfx}",
        (CreateViewParentMixin, GuardianCreateViewPermissionRequired),
        # a parent-only create: its own flag is never consulted
        {"cv_viewset": book, "__module__": __name__, "fields": ["title"], "cv_guardian_accept_global_perms": True},
    )
    core_pub = scope.viewset(ViewSet, model=Publisher, name=scope.name("mgcorepub"))
    scope.view(ListView, core_pub, name="MgCorePubList")
    core_book = scope.viewset(
        ViewSet,
        model=Book,
        name=scope.name("mgcorebook"),
        parent=ParentViewSet(name=core_pub.name, attribute="publisher"),
    )
    scope.view(ListView, core_book, name="MgCoreBookList")
    scope.mount([pub, book, core_pub, core_book])
    return SimpleNamespace(pub=pub, book=book, core_pub=core_pub, core_book=core_book)


def _manage(client, viewset, parent=None):
    kwargs = {viewset.parent.get_pk_name(): parent.pk} if parent is not None else {}
    response = client.get(reverse(viewset.get_router_name("manage"), kwargs=kwargs))
    assert response.status_code == 200
    return response


def _flat(response):
    return re.sub(r"\s+", " ", response.content.decode())


def _row(setting, declared, effective):
    return re.compile(
        rf"<tr> <td>{re.escape(setting)}</td> <td>{re.escape(declared)}</td> <td>{re.escape(effective)}</td> </tr>"
    )


TOP_LEVEL = {"cascade": None, "effective_cascade": None, "read": None, "effective_read": None}
TOP_LEVEL |= {"write": None, "effective_write": None, "actions": {}}
VIEW = {"nearest": "view", "higher": "view"}
WRITE_DEFAULT = {"nearest": "change", "higher": "view"}


@pytest.mark.parametrize("ancestor_fallback", [True, False])
@pytest.mark.django_db
def test_manage_separates_declared_ancestor_and_local_fallback(client, publisher_a, ancestor_fallback):
    view_flag = not ancestor_fallback  # opposite values: neither label may follow the other
    with ancestor_scope() as scope:
        routes = _manage_routes(scope, ancestor_fallback=ancestor_fallback, view_flag=view_flag)
        client.force_login(_user("root", superuser=True))

        pub = _manage(client, routes.pub)
        assert pub.context["ancestor_config"] == {
            "nested": False,
            "provider": None,
            "effective_provider": "guardian",
            "accept_global_perms": ancestor_fallback,
            **TOP_LEVEL,
        }
        assert pub.context["views"]["list"]["guardian_policy"]["cv_guardian_accept_global_perms"] is view_flag
        content = _flat(pub)
        assert _row("provider", "default", "guardian").search(content)
        fallback_text = "object or model permission" if ancestor_fallback else "object permission only"
        assert _row("accept_global_perms", str(ancestor_fallback), fallback_text).search(content)
        assert _row("cascade", "default", "not applicable: top-level ViewSet").search(content)
        local_text = "strict: object and group grants only"
        if view_flag:
            local_text = "global fallback: model permissions accepted"
        assert re.search(rf"<tr> <td>list</td> <td>{view_flag}</td> <td>{re.escape(local_text)}</td>", content)

        book = _manage(client, routes.book, parent=publisher_a)
        assert book.context["ancestor_config"] == {
            "nested": True,
            "provider": None,
            "effective_provider": "guardian",
            "accept_global_perms": False,
            "cascade": False,
            "effective_cascade": False,
            "read": VIEW,
            "effective_read": VIEW,
            "write": None,
            "effective_write": WRITE_DEFAULT,
            "actions": {"create": {"nearest": "change", "higher": "change"}},
        }
        content = _flat(book)
        assert _row("cascade", "False", "nearest protected ancestor only").search(content)
        assert _row("read", "nearest=view, higher=view", "nearest=view, higher=view").search(content)
        assert _row("write", "default", "nearest=change, higher=view").search(content)
        assert _row("actions['create']", "nearest=change, higher=change", "nearest=change, higher=change").search(
            content
        )
        # nested parent-only create: its local fallback is not applicable, whatever its own flag says
        assert book.context["views"]["create"]["guardian_policy"]["global_fallback_applicable"] is False
        assert re.search(r"<tr> <td>create</td> <td>—</td> <td>not applicable</td>", content)
        # the endpoint-local option is described as local; no description lets it control a parent
        assert "never relaxes an ancestor" in content
        assert "Global fallback is configured on each view class." not in content

        # configuration only: no access claim
        for config in (pub.context["ancestor_config"], book.context["ancestor_config"]):
            assert not any("access" in key or "permission" in key.replace("_perms", "") for key in config)
        assert "does not show whether a user can access" in content


@pytest.mark.django_db
def test_manage_shows_ancestor_policy_on_core_pages(client, publisher_a):
    with ancestor_scope() as scope:
        routes = _manage_routes(scope, ancestor_fallback=False, view_flag=False)
        client.force_login(_user("root", superuser=True))

        top = _manage(client, routes.core_pub)
        assert top.context["ancestor_config"] == {
            "nested": False,
            "provider": None,
            "effective_provider": "model",
            "accept_global_perms": False,
            **TOP_LEVEL,
        }
        assert "guardian_config" not in top.context
        content = _flat(top)
        assert "Ancestor authorization" in content
        assert _row("provider", "default", "model").search(content)
        assert _row("accept_global_perms", "False", "not applicable: provider model").search(content)

        nested = _manage(client, routes.core_book, parent=publisher_a)
        config = nested.context["ancestor_config"]
        assert config["effective_cascade"] is True  # the global default
        assert config["effective_read"] == VIEW
        assert config["effective_write"] == WRITE_DEFAULT
        content = _flat(nested)
        assert _row("cascade", "default", "all protected ancestors").search(content)
        assert _row("read", "default", "nearest=view, higher=view").search(content)
