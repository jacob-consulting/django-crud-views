"""Phase 6.2 A10/D-12/D-13 (AUTH-01..07): the source note's actor matrix replayed on real registered routes.

Every cell drives a direct ``Client`` request against freshly registered core and Guardian routes and asserts one
exact status (never an allowed-status set), the queryset/rows where applicable, stored rows and write-hook counts.

This module is post-fix replay and preservation evidence (A03). The defects it pins were reproduced red by the
plans that fixed them, without reverting any fix here:

* 06.2-01: HTTP DELETE bypass (DELETE returned 302 and deleted the row) and protected-label leaks.
* 06.2-02: None-policy parent/state skips, inactive-actor queryset leaks, wrong-object create helpers.
* 06.2-03: fragment GETs answered before object authorization (secret choices disclosed) and forged coordinates.
* 06.2-04: the inert ViewSet global-permission flag; the manage gate is replayed unchanged here.

Routes are built by a yielding fixture on fresh, uniquely named ViewSets with a temporary ROOT_URLCONF. The registry,
vocabulary cache, URL caches and module registration are restored in ``finally`` (A08); the cached settings
singleton (manage mode/group) is patched with ``monkeypatch`` so it is restored on every exit (A20).
"""

import sys
import types
import uuid
from collections import Counter
from types import SimpleNamespace

import pytest
from django.db.models import ProtectedError
from django.test import Client, override_settings
from django.urls import clear_url_caches, include, path, reverse

from tests.test1.test_fragment_authorization import CHOICES, SECRET, PublisherMainForm, publisher_formsets

ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"
INACTIVE_BACKENDS = [ALLOW_INACTIVE, "guardian.backends.ObjectPermissionBackend"]
MODAL = {"X-CV-Modal": "true"}
LOGIN = "/accounts/login/"
TOUCHED = "touched-by-action"
MANAGE_GROUP = "mx_manage_admins"

FAMILIES = ("core", "strict", "global")
ACTORS = ("none", "object", "group", "global", "superuser")
OPS = (
    "list",
    "card",
    "detail",
    "update_get",
    "update_post",
    "delete_get",
    "delete_post",
    "action_post",
    "fragment",
    "create_get",
    "create_post",
    "http_delete",
)
# the permission each operation requests; an "object grant for the requested permission only" grants just this
OP_PERM = {
    "list": "view",
    "card": "view",
    "detail": "view",
    "update_get": "change",
    "update_post": "change",
    "delete_get": "delete",
    "delete_post": "delete",
    "action_post": "change",
    "fragment": "change",
    "create_get": "add",
    "create_post": "add",
    "http_delete": "delete",
}
WRITE_HOOKS = ("update", "delete", "action", "create", "book_create", "free_create")


# ── isolated route fixture ────────────────────────────────────────────────────


def _family(vs, kind, hooks):
    """Register list/card/detail/update/editor(formset)/delete/touch(action)/create views on ``vs``."""
    from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
    from crud_views.lib.formsets import FormSetMixin
    from crud_views.lib.views import (
        ActionViewPermissionRequired,
        CardListViewPermissionRequired,
        CreateViewPermissionRequired,
        DeleteViewPermissionRequired,
        DetailViewPermissionRequired,
        ListViewPermissionRequired,
        UpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.views import (
        GuardianActionViewPermissionRequired,
        GuardianCardListViewPermissionRequired,
        GuardianCreateViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
    )
    from tests.test1.app.views import PublisherForm

    if kind == "core":
        bases = SimpleNamespace(
            list=ListViewPermissionRequired,
            card=CardListViewPermissionRequired,
            detail=DetailViewPermissionRequired,
            update=UpdateViewPermissionRequired,
            delete=DeleteViewPermissionRequired,
            action=ActionViewPermissionRequired,
            create=CreateViewPermissionRequired,
        )
    else:
        bases = SimpleNamespace(
            list=GuardianListViewPermissionRequired,
            card=GuardianCardListViewPermissionRequired,
            detail=GuardianDetailViewPermissionRequired,
            update=GuardianUpdateViewPermissionRequired,
            delete=GuardianDeleteViewPermissionRequired,
            action=GuardianActionViewPermissionRequired,
            create=GuardianCreateViewPermissionRequired,
        )

    class MxList(bases.list):
        cv_viewset = vs

    class MxCard(bases.card):
        cv_viewset = vs

    class MxDetail(bases.detail):
        cv_viewset = vs

    class MxUpdate(CrispyViewMixin, bases.update):
        form_class = PublisherForm
        cv_viewset = vs

        def cv_form_valid_hook(self, context):
            super().cv_form_valid_hook(context)
            hooks["update"] += 1

    class MxEditor(CrispyViewMixin, FormSetMixin, bases.update):
        """Formset editor whose fragment GETs render an application ModelChoiceField over every Contract."""

        cv_key = "editor"
        cv_path = "editor"
        form_class = PublisherMainForm
        cv_viewset = vs
        cv_formsets = publisher_formsets()

        def get_template_html(self, request):
            hooks["fragment"] += 1
            return super().get_template_html(request)

    class MxDelete(CrispyViewMixin, bases.delete):
        form_class = CrispyDeleteForm
        cv_viewset = vs
        cv_modal = True

        def get_object(self, *args, **kwargs):
            hooks["delete_get_object"] += 1
            return super().get_object(*args, **kwargs)

        def cv_form_valid_hook(self, context):
            super().cv_form_valid_hook(context)
            hooks["delete"] += 1

    class MxTouch(bases.action):
        cv_key = "touch"
        cv_path = "touch"
        cv_viewset = vs
        cv_icon_action = "fa-solid fa-bolt"
        cv_action_label_template_code = "Touch"
        cv_action_short_label_template_code = "Touch"

        def action(self, context):
            obj = context["object"]
            obj.name = TOUCHED
            obj.save(update_fields=["name"])
            return True

        def cv_action_success_hook(self, context):
            super().cv_action_success_hook(context)
            hooks["action"] += 1

    class MxCreate(CrispyViewMixin, bases.create):
        form_class = PublisherForm
        cv_viewset = vs

        def cv_form_valid_hook(self, context):
            super().cv_form_valid_hook(context)
            hooks["create"] += 1

    return SimpleNamespace(
        vs=vs,
        List=MxList,
        Card=MxCard,
        Detail=MxDetail,
        Update=MxUpdate,
        Editor=MxEditor,
        Delete=MxDelete,
        Touch=MxTouch,
        Create=MxCreate,
    )


@pytest.fixture
def mx(monkeypatch):
    """Fresh routes: core Publisher, Guardian Publisher, its strict Book child and a None-policy Book child."""
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
    from crud_views.lib.formsets import FormSets
    from crud_views.lib.views import CreateViewParentMixin
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, ViewSet
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDeleteViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Book, Publisher
    from tests.test1.app.views import BookForm

    sfx = uuid.uuid4().hex[:8]
    names = [f"mxcore{sfx}", f"mxg{sfx}", f"mxbook{sfx}", f"mxfree{sfx}"]
    modname = f"tests.test1._mx_urls_{sfx}"
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    hooks: Counter = Counter()
    state = {"book": True, "free": True}
    state_calls: dict = {"book": [], "free": []}
    CHOICES["evaluated"] = 0

    original_get_template = FormSets.get_template

    def counting_get_template(self, *args, **kwargs):
        hooks["render"] += 1
        return original_get_template(self, *args, **kwargs)

    monkeypatch.setattr(FormSets, "get_template", counting_get_template)

    try:
        core = _family(ViewSet(model=Publisher, name=names[0], icon_header="fa-regular fa-building"), "core", hooks)
        guardian = _family(
            GuardianViewSet(model=Publisher, name=names[1], icon_header="fa-regular fa-building"), "guardian", hooks
        )

        # strict FK child: the configured attribute ("publisher") differs from the parent ViewSet name
        book_vs = GuardianViewSet(
            model=Book,
            name=names[2],
            parent=ParentViewSet(name=names[1], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
            cv_guardian_parent_permission="view",
            cv_guardian_parent_create_permission="change",
        )
        child_page_actions = ["create"]

        class MxBookListView(GuardianListViewPermissionRequired):
            cv_viewset = book_vs

        class MxBookDetailView(GuardianDetailViewPermissionRequired):
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class MxBookUpdateView(CrispyViewMixin, GuardianUpdateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class MxBookDeleteView(CrispyViewMixin, GuardianDeleteViewPermissionRequired):
            form_class = CrispyDeleteForm
            cv_viewset = book_vs
            cv_context_actions = child_page_actions

        class MxBookCreateView(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = book_vs

            @classmethod
            def cv_action_enabled(cls, user, obj=None):
                state_calls["book"].append(obj)
                return state["book"]

            def cv_form_valid_hook(self, context):
                super().cv_form_valid_hook(context)
                hooks["book_create"] += 1

        free_vs = GuardianViewSet(
            model=Book,
            name=names[3],
            parent=ParentViewSet(name=names[1], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
            cv_guardian_parent_permission=None,
            cv_guardian_parent_create_permission=None,
        )

        class MxFreeListView(GuardianListViewPermissionRequired):
            cv_viewset = free_vs
            cv_context_actions = ["create"]

        class MxFreeCreateView(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = free_vs

            @classmethod
            def cv_action_enabled(cls, user, obj=None):
                state_calls["free"].append(obj)
                return state["free"]

            def cv_form_valid_hook(self, context):
                super().cv_form_valid_hook(context)
                hooks["free_create"] += 1

        module = types.ModuleType(modname)
        module.urlpatterns = [
            *core.vs.urlpatterns,
            *guardian.vs.urlpatterns,
            *book_vs.urlpatterns,
            *free_vs.urlpatterns,
            path("", include("tests.test1.project.urls")),
        ]
        sys.modules[modname] = module

        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield SimpleNamespace(
                    core=core,
                    g=guardian,
                    book=SimpleNamespace(
                        vs=book_vs,
                        List=MxBookListView,
                        Detail=MxBookDetailView,
                        Update=MxBookUpdateView,
                        Delete=MxBookDeleteView,
                        Create=MxBookCreateView,
                    ),
                    free=SimpleNamespace(vs=free_vs, List=MxFreeListView, Create=MxFreeCreateView),
                    hooks=hooks,
                    state=state,
                    state_calls=state_calls,
                )
            finally:
                clear_url_caches()
    finally:
        with _REGISTRY_LOCK:
            for name in names:
                _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        sys.modules.pop(modname, None)
        clear_url_caches()


@pytest.fixture
def world(db, publisher_a, publisher_b):
    """Two publishers; a secret Contract (on B) that only an application choice field would list."""
    from tests.test1.app.models import Contract

    Contract.objects.create(publisher=publisher_b, title=SECRET)
    return SimpleNamespace(a=publisher_a, b=publisher_b)


# ── helpers ───────────────────────────────────────────────────────────────────


def _u(vs, key, pk=None, parent_pk=None):
    kwargs = {}
    if parent_pk is not None:
        kwargs[vs.parent.get_pk_name()] = parent_pk
    if pk is not None:
        kwargs["pk"] = pk
    return reverse(vs.get_router_name(key), kwargs=kwargs)


def _refetch(user):
    from django.contrib.auth.models import User

    return User.objects.get(pk=user.pk)  # drop Django's per-instance permission caches


def _make_actor(kind, perms=(), obj=None, *, active=True, name=None):
    """An actor holding the full permission strings ``perms`` through ``kind``: own object grants on ``obj``, a
    group's object grants on ``obj``, global model permissions, the superuser flag, or nothing ("none")."""
    from django.contrib.auth.models import Group, Permission, User
    from guardian.shortcuts import assign_perm

    username = name or f"mx_{kind}_{'active' if active else 'inactive'}"
    if kind == "superuser":
        user = User.objects.create_superuser(username=username, password="password")
    else:
        user = User.objects.create_user(username=username, password="password")
    if kind == "object":
        for perm in perms:
            assign_perm(perm, user, obj)
    elif kind == "group":
        group = Group.objects.create(name=f"group_{username}")
        user.groups.add(group)
        for perm in perms:
            assign_perm(perm, group, obj)
    elif kind == "global":
        for perm in perms:
            app_label, codename = perm.split(".")
            user.user_permissions.add(Permission.objects.get(content_type__app_label=app_label, codename=codename))
    if not active:
        user.is_active = False
        user.save()
    return _refetch(user)


def _fam(mx, family):
    return mx.core if family == "core" else mx.g


def _set_policy(mx, monkeypatch, family):
    """strict / global: the per-view Guardian fallback on every object and queryset view of the Guardian family."""
    if family == "core":
        return
    for cls in (mx.g.List, mx.g.Card, mx.g.Detail, mx.g.Update, mx.g.Editor, mx.g.Delete, mx.g.Touch):
        monkeypatch.setattr(cls, "cv_guardian_accept_global_perms", family == "global")


def _fragment_query(pk):
    return f"?template=books&num=0&pk={pk}"


def _request(client, mx, family, op, pk):
    vs = _fam(mx, family).vs
    if op in ("list", "card"):
        return client.get(_u(vs, op))
    if op == "detail":
        return client.get(_u(vs, "detail", pk))
    if op == "update_get":
        return client.get(_u(vs, "update", pk))
    if op == "update_post":
        return client.post(_u(vs, "update", pk), {"name": "Updated"})
    if op == "delete_get":
        return client.get(_u(vs, "delete", pk))
    if op == "delete_post":
        return client.post(_u(vs, "delete", pk), {"confirm": "on"})
    if op == "action_post":
        return client.post(_u(vs, "touch", pk))
    if op == "fragment":
        return client.get(_u(vs, "editor", pk) + _fragment_query(pk))
    if op == "create_get":
        return client.get(_u(vs, "create"))
    if op == "create_post":
        return client.post(_u(vs, "create"), {"name": "Created"})
    if op == "http_delete":
        return client.delete(_u(vs, "delete", pk))
    raise AssertionError(op)


def _granted(family, actor):
    return (
        actor
        in {
            "core": ("global", "superuser"),
            "strict": ("object", "group", "superuser"),
            "global": ("object", "group", "global", "superuser"),
        }[family]
    )


def _expected_status(family, actor, op):
    if op in ("create_get", "create_post"):  # top-level create: global add in both families
        if actor not in ("global", "superuser"):
            return 403
        return 200 if op == "create_get" else 302
    if op == "http_delete":  # core: permission gate before the method; Guardian: 405 before any lookup
        if family == "core" and not _granted(family, actor):
            return 403
        return 405
    if op in ("list", "card"):
        if family == "core":
            return 200 if _granted(family, actor) else 403
        return 200  # Guardian list/card: queryset filtering is the gate
    if not _granted(family, actor):
        return 403
    return 302 if op.endswith("_post") else 200


def _expected_rows(family, actor, world):
    both = {world.a.pk, world.b.pk}
    if family == "core":
        return both
    if actor == "superuser" or (family == "global" and actor == "global"):
        return both
    if actor in ("object", "group"):
        return {world.a.pk}
    return set()


def _snapshot():
    from tests.test1.app.models import Book, Contract, Publisher

    return (
        dict(Publisher.objects.values_list("pk", "name")),
        sorted(Book.objects.values_list("pk", "title", "publisher_id")),
        Contract.objects.count(),
    )


def _assert_no_write(mx, before):
    assert _snapshot() == before
    for hook in WRITE_HOOKS:
        assert mx.hooks[hook] == 0, hook


def _assert_no_editor_data(mx, response):
    assert mx.hooks["fragment"] == 0
    assert mx.hooks["render"] == 0
    assert CHOICES["evaluated"] == 0
    assert SECRET.encode() not in response.content


def _pks(object_list):
    return {obj.pk for obj in object_list}


# ── active actor matrix: every family, actor and route/method (A10 tables 1 and 2) ──


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize("actor", ACTORS)
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_active_actor_matrix(mx, client, monkeypatch, world, family, actor, op):
    from tests.test1.app.models import Publisher

    _set_policy(mx, monkeypatch, family)
    perm = _fam(mx, family).vs.permissions[OP_PERM[op]]
    user = _make_actor(actor, [perm], world.a)
    client.force_login(user)
    before = _snapshot()
    response = _request(client, mx, family, op, world.a.pk)

    expected = _expected_status(family, actor, op)
    assert response.status_code == expected
    assert response.wsgi_request.user.pk == user.pk

    if expected == 302:
        hook = {"update_post": "update", "delete_post": "delete", "action_post": "action", "create_post": "create"}
        assert mx.hooks[hook[op]] == 1
        assert sum(mx.hooks[h] for h in WRITE_HOOKS) == 1
        names, books, contracts = before
        if op == "update_post":
            names[world.a.pk] = "Updated"
        elif op == "action_post":
            names[world.a.pk] = TOUCHED
        elif op == "delete_post":
            del names[world.a.pk]
        else:
            created = Publisher.objects.get(name="Created")
            names[created.pk] = "Created"
        assert _snapshot() == (names, books, contracts)
        return

    _assert_no_write(mx, before)
    if op == "http_delete" and family != "core":
        assert mx.hooks["delete_get_object"] == 0  # 405 precedes object lookup, permission and state
    if expected != 200:
        _assert_no_editor_data(mx, response)
        assert "Pan Books" not in response.content.decode()
        return
    if op in ("list", "card"):
        assert _pks(response.context["object_list"]) == _expected_rows(family, actor, world)
    if op == "fragment":
        data = response.json()
        assert set(data) == {"html", "rows"}
        assert data["rows"] == [f"books-{world.a.pk}-0-0"]
        assert mx.hooks["fragment"] == 1
        # D-13: an authorized editor's ordinary application choices are unchanged (the app owns their filtering)
        assert SECRET in data["html"]
    else:
        assert mx.hooks["fragment"] == 0


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize("actor", ACTORS)
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_inactive_actor_matrix(mx, client, monkeypatch, world, family, actor, op):
    """Inactive ordinary/object/group/global/superuser sessions (AllowAllUsersModelBackend): 403 everywhere."""
    _set_policy(mx, monkeypatch, family)
    vs = _fam(mx, family).vs
    user = _make_actor(actor, [vs.permissions[OP_PERM[op]]], world.a, active=False)
    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
        client.force_login(user, backend=ALLOW_INACTIVE)
        before = _snapshot()
        response = _request(client, mx, family, op, world.a.pk)

    # request identity: the session really is authenticated but inactive (not masked as anonymous)
    assert response.wsgi_request.user.is_authenticated is True
    assert response.wsgi_request.user.is_active is False
    assert response.wsgi_request.user.pk == user.pk

    assert response.status_code == 403
    _assert_no_write(mx, before)
    _assert_no_editor_data(mx, response)
    assert mx.hooks["delete_get_object"] == 0
    content = response.content.decode()
    assert "Pan Books" not in content and "Gollancz" not in content
    if family != "core":
        assert list(vs.get_objects_for_user(user, "view")) == []


@pytest.mark.parametrize("op", OPS)
@pytest.mark.django_db
def test_core_anonymous_redirects_to_login(mx, client, world, op):
    before = _snapshot()
    response = _request(client, mx, "core", op, world.a.pk)
    assert response.status_code == 302
    assert response["Location"].startswith(LOGIN)
    _assert_no_write(mx, before)
    _assert_no_editor_data(mx, response)


@pytest.mark.parametrize("op", OPS)
@pytest.mark.parametrize(("mode", "status"), [("redirect", 302), ("403", 403), ("404", 404)])
@pytest.mark.django_db
def test_guardian_anonymous_modes(mx, client, monkeypatch, world, op, mode, status):
    """Guardian anonymous behavior holds for every normal route and method, including DELETE."""
    for cls in (mx.g.List, mx.g.Card, mx.g.Detail, mx.g.Update, mx.g.Editor, mx.g.Delete, mx.g.Touch, mx.g.Create):
        monkeypatch.setattr(cls, "cv_guardian_anonymous_behavior", mode, raising=False)
    before = _snapshot()
    response = _request(client, mx, "strict", op, world.a.pk)
    assert response.status_code == status
    if status == 302:
        assert response["Location"].startswith(LOGIN)
    _assert_no_write(mx, before)
    _assert_no_editor_data(mx, response)
    assert mx.hooks["delete_get_object"] == 0


# ── revocation on the next request (edge AUTH-07 concurrency) ─────────────────

REVOKE_PROBE = {
    "list": "list",
    "detail": "detail",
    "update_post": "update_get",
    "action_post": "update_get",
    "fragment": "fragment",
    "delete_post": "delete_get",
}


@pytest.mark.parametrize("op", list(REVOKE_PROBE))
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_revoked_grant_applies_on_next_request(mx, client, monkeypatch, world, family, op):
    from django.contrib.auth.models import Permission

    _set_policy(mx, monkeypatch, family)
    vs = _fam(mx, family).vs
    perm = vs.permissions[OP_PERM[op]]
    kind = "global" if family == "core" else "object"
    user = _make_actor(kind, [perm], world.a)
    client.force_login(user)

    probe = _request(client, mx, family, REVOKE_PROBE[op], world.a.pk)
    assert probe.status_code == 200
    mx.hooks.clear()
    CHOICES["evaluated"] = 0

    if family == "core":
        app_label, codename = perm.split(".")
        user.user_permissions.remove(Permission.objects.get(content_type__app_label=app_label, codename=codename))
    else:
        vs.remove_perm(OP_PERM[op], user, world.a)

    before = _snapshot()
    response = _request(client, mx, family, op, world.a.pk)
    _assert_no_write(mx, before)
    _assert_no_editor_data(mx, response)
    if op == "list" and family != "core":
        assert response.status_code == 200
        assert _pks(response.context["object_list"]) == set()
    else:
        assert response.status_code == 403


# ── response table: validation, protection and method ordering ────────────────


def _granted_actor(mx, family, world, *perms):
    vs = _fam(mx, family).vs
    kind = "global" if family == "core" else "object"
    return _make_actor(kind, [vs.permissions[p] for p in perms], world.a)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_granted_invalid_posts_render_errors_without_writes(mx, client, monkeypatch, world, family):
    _set_policy(mx, monkeypatch, family)
    vs = _fam(mx, family).vs
    client.force_login(_granted_actor(mx, family, world, "change", "delete"))
    before = _snapshot()

    response = client.post(_u(vs, "update", world.a.pk), {"name": ""})
    assert response.status_code == 200
    assert response.context["form"].errors
    unconfirmed = client.post(_u(vs, "delete", world.a.pk), {})
    assert unconfirmed.status_code == 200
    assert unconfirmed.context["form"].errors
    modal = client.post(_u(vs, "delete", world.a.pk), {}, headers=MODAL)
    assert modal.status_code == 422
    _assert_no_write(mx, before)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_granted_custom_protection_delete_post(mx, client, monkeypatch, world, family):
    _set_policy(mx, monkeypatch, family)
    monkeypatch.setattr(_fam(mx, family).Delete, "cv_check_delete_protection", lambda self: ["Blocked by policy"])
    vs = _fam(mx, family).vs
    client.force_login(_granted_actor(mx, family, world, "delete"))
    before = _snapshot()

    full = client.post(_u(vs, "delete", world.a.pk), {"confirm": "on"})
    assert full.status_code == 200
    assert "Blocked by policy" in full.content.decode()
    modal = client.post(_u(vs, "delete", world.a.pk), {"confirm": "on"}, headers=MODAL)
    assert modal.status_code == 422
    _assert_no_write(mx, before)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_granted_database_protect_delete_reraises(mx, client, monkeypatch, world, family):
    from tests.test1.app.models import Contract, Publisher

    _set_policy(mx, monkeypatch, family)
    contract = Contract.objects.create(publisher=world.a, title="Binding")
    client.force_login(_granted_actor(mx, family, world, "delete"))
    before = _snapshot()

    with pytest.raises(ProtectedError):
        client.post(_u(_fam(mx, family).vs, "delete", world.a.pk), {"confirm": "on"})
    assert Publisher.objects.filter(pk=world.a.pk).exists()
    assert Contract.objects.filter(pk=contract.pk).exists()
    _assert_no_write(mx, before)


@pytest.mark.parametrize("missing", [False, True])
@pytest.mark.parametrize("actor", [*ACTORS, "revoked"])
@pytest.mark.parametrize("family", ["strict", "global"])
@pytest.mark.django_db
def test_guardian_active_http_delete_is_405_before_lookup(mx, client, monkeypatch, world, family, actor, missing):
    _set_policy(mx, monkeypatch, family)
    perm = mx.g.vs.permissions["delete"]
    user = _make_actor("object" if actor == "revoked" else actor, [perm], world.a)
    if actor == "revoked":
        mx.g.vs.remove_perm("delete", user, world.a)
    client.force_login(user)
    pk = 999999 if missing else world.a.pk
    before = _snapshot()

    response = client.delete(_u(mx.g.vs, "delete", pk))
    assert response.status_code == 405
    assert "DELETE" not in response.headers.get("Allow", "")
    assert mx.hooks["delete_get_object"] == 0
    _assert_no_write(mx, before)


@pytest.mark.parametrize(
    ("case", "status"), [("granted", 405), ("ungranted", 403), ("disabled", 403), ("missing", 404)]
)
@pytest.mark.django_db
def test_core_http_delete_ordering(mx, client, monkeypatch, world, case, status):
    """Core dispatch permission and state lookup precede method selection."""
    perm = mx.core.vs.permissions["delete"]
    user = _make_actor("none" if case == "ungranted" else "global", [perm], world.a)
    if case == "disabled":
        monkeypatch.setattr(mx.core.Delete, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    client.force_login(user)
    pk = 999999 if case == "missing" else world.a.pk
    before = _snapshot()

    assert client.delete(_u(mx.core.vs, "delete", pk)).status_code == status
    _assert_no_write(mx, before)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_missing_endpoint_is_404_after_earlier_gates(mx, client, monkeypatch, world, family):
    _set_policy(mx, monkeypatch, family)
    vs = _fam(mx, family).vs
    client.force_login(_make_actor("superuser"))
    before = _snapshot()
    missing = 999999

    assert client.get(_u(vs, "detail", missing)).status_code == 404
    assert client.get(_u(vs, "update", missing)).status_code == 404
    assert client.post(_u(vs, "update", missing), {"name": "Ghost"}).status_code == 404
    assert client.post(_u(vs, "delete", missing), {"confirm": "on"}).status_code == 404
    assert client.post(_u(vs, "touch", missing)).status_code == 404
    response = client.get(_u(vs, "editor", missing) + _fragment_query(missing))
    assert response.status_code == 404
    _assert_no_write(mx, before)
    _assert_no_editor_data(mx, response)


@pytest.mark.parametrize(
    "coords",
    [
        "?template=nope&num=0&pk={a}",
        "?template=books&num=x&pk={a}",
        "?template=books&num=0&pk={b}",
        "?template=books&num=0&pk=None",
        "?template=books&num=0&pk={a}&formset_parent_prefix_key=books-{a}-0",
        "?template=books|notes&num=0&pk=99999&formset_parent_prefix_key=books-{a}-0",
    ],
)
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.django_db
def test_granted_editor_malformed_fragment_coordinates_are_400(mx, client, monkeypatch, world, family, coords):
    _set_policy(mx, monkeypatch, family)
    vs = _fam(mx, family).vs
    client.force_login(_granted_actor(mx, family, world, "change"))
    before = _snapshot()

    response = client.get(_u(vs, "editor", world.a.pk) + coords.format(a=world.a.pk, b=world.b.pk))
    assert response.status_code == 400
    assert mx.hooks["render"] == 0
    assert CHOICES["evaluated"] == 0
    assert SECRET.encode() not in response.content
    _assert_no_write(mx, before)


# ── nested routes: parent gate, URL parent and method ordering ────────────────


@pytest.fixture
def child(world):
    from tests.test1.app.models import Book

    return Book.objects.create(title="Child Page Book", publisher=world.a)


def _book_page_actor(mx, world, child, *, parent_view=True, extra_parents=(), name="book_actor"):
    """Holds view/change/delete on ``child`` and (optionally) the parent 'view' grant needed to reach its pages."""
    from guardian.shortcuts import assign_perm

    user = _make_actor("none", name=name)
    for perm in ("view", "change", "delete"):
        assign_perm(mx.book.vs.permissions[perm], user, child)
    if parent_view:
        assign_perm(mx.g.vs.permissions["view"], user, world.a)
    for parent in extra_parents:
        assign_perm(mx.g.vs.permissions["view"], user, parent)
    return _refetch(user)


def _child_requests(client, mx, parent_pk, pk):
    return {
        "detail": client.get(_u(mx.book.vs, "detail", pk, parent_pk)),
        "update_get": client.get(_u(mx.book.vs, "update", pk, parent_pk)),
        "update_post": client.post(_u(mx.book.vs, "update", pk, parent_pk), {"title": "Changed"}),
        "delete_post": client.post(_u(mx.book.vs, "delete", pk, parent_pk), {"confirm": "on"}),
        "http_delete": client.delete(_u(mx.book.vs, "delete", pk, parent_pk)),
    }


@pytest.mark.django_db
def test_nested_parent_grant_missing_is_403_including_delete(mx, client, world, child):
    """Parent exists, required parent grant missing: the parent dispatch gate precedes method selection."""
    client.force_login(_book_page_actor(mx, world, child, parent_view=False))
    before = _snapshot()
    statuses = {op: r.status_code for op, r in _child_requests(client, mx, world.a.pk, child.pk).items()}
    assert statuses == dict.fromkeys(statuses, 403)
    _assert_no_write(mx, before)


@pytest.mark.django_db
def test_nested_missing_parent_is_404_including_delete(mx, client, world, child):
    client.force_login(_book_page_actor(mx, world, child))
    before = _snapshot()
    statuses = {op: r.status_code for op, r in _child_requests(client, mx, 999999, child.pk).items()}
    assert statuses == dict.fromkeys(statuses, 404)
    _assert_no_write(mx, before)


@pytest.mark.django_db
def test_nested_wrong_url_parent_is_404_with_satisfied_parent_gate(mx, client, world, child):
    """The parent gate passes for B, but the Book belongs to A: object routes 404; DELETE stays 405 (no lookup)."""
    client.force_login(_book_page_actor(mx, world, child, extra_parents=[world.b]))
    before = _snapshot()
    statuses = {op: r.status_code for op, r in _child_requests(client, mx, world.b.pk, child.pk).items()}
    assert statuses == {"detail": 404, "update_get": 404, "update_post": 404, "delete_post": 404, "http_delete": 405}
    _assert_no_write(mx, before)

    # control: the same actor through the real URL parent reaches the pages; DELETE is still 405
    assert client.get(_u(mx.book.vs, "detail", child.pk, world.a.pk)).status_code == 200
    assert client.delete(_u(mx.book.vs, "delete", child.pk, world.a.pk)).status_code == 405
    _assert_no_write(mx, before)


# ── parent-None child creation (D-10) ─────────────────────────────────────────


def _record_contexts(monkeypatch, view_cls):
    records: list = []
    original = view_cls.cv_get_context

    def spy(self, *args, **kwargs):
        ctx = original(self, *args, **kwargs)
        records.append((kwargs.get("key"), ctx))
        return ctx

    monkeypatch.setattr(view_cls, "cv_get_context", spy)
    return records


@pytest.mark.django_db
def test_parent_none_create_enabled_binds_url_parent_even_with_forged_fk(mx, client, monkeypatch, world):
    from tests.test1.app.models import Book, Publisher

    records = _record_contexts(monkeypatch, mx.free.List)
    client.force_login(_make_actor("none"))
    url = _u(mx.free.vs, "create", parent_pk=world.a.pk)

    assert client.get(url).status_code == 200
    response = client.post(url, {"title": "Free Child", "publisher": world.b.pk})
    assert response.status_code == 302
    assert list(Book.objects.filter(title="Free Child").values_list("publisher_id", flat=True)) == [world.a.pk]
    assert mx.hooks["free_create"] == 1
    assert all(type(obj) is Publisher and obj.pk == world.a.pk for obj in mx.state_calls["free"])

    list_response = client.get(_u(mx.free.vs, "list", parent_pk=world.a.pk))
    assert list_response.status_code == 200
    (ctx,) = [c for key, c in records if key == "create"]
    assert (ctx["cv_access"], ctx["cv_action_enabled"]) == (True, True)


@pytest.mark.django_db
def test_parent_none_create_disabled_is_403_and_controls_keep_separate_values(mx, client, monkeypatch, world):
    mx.state["free"] = False
    records = _record_contexts(monkeypatch, mx.free.List)
    client.force_login(_make_actor("none"))
    url = _u(mx.free.vs, "create", parent_pk=world.a.pk)
    before = _snapshot()

    assert client.get(url).status_code == 403
    assert client.post(url, {"title": "Disabled Child"}).status_code == 403
    _assert_no_write(mx, before)

    response = client.get(_u(mx.free.vs, "list", parent_pk=world.a.pk))
    assert response.status_code == 200
    (ctx,) = [c for key, c in records if key == "create"]
    assert (ctx["cv_access"], ctx["cv_action_enabled"]) == (True, False)
    assert f'href="{url}"' not in response.content.decode()


@pytest.mark.django_db
def test_parent_none_create_missing_parent_is_404(mx, client, world):
    client.force_login(_make_actor("none"))
    url = _u(mx.free.vs, "create", parent_pk=999999)
    before = _snapshot()
    assert client.get(url).status_code == 404
    assert client.post(url, {"title": "Orphan"}).status_code == 404
    _assert_no_write(mx, before)
    assert mx.state_calls["free"] == []


# ── H03: create controls on reachable FK child pages agree with direct routes ──

CHILD_PAGES = ["detail", "update", "delete"]
CHILD_CONDITIONS = ["permitted", "denied", "other_parent", "revoked", "disabled", "global_change"]


def _render_permission_filter(response):
    from django.template import Context, Template

    view = response.context["view"]
    template = Template('{% load crud_views %}{{ view|cv_context_has_permission:"create" }}')
    return template.render(Context({"view": view, "request": view.request}))


@pytest.mark.parametrize("condition", CHILD_CONDITIONS)
@pytest.mark.parametrize("policy", ["strict", "global"])
@pytest.mark.parametrize("page", CHILD_PAGES)
@pytest.mark.django_db
def test_child_page_create_control_matches_direct_route(mx, client, monkeypatch, world, child, page, policy, condition):
    from django.contrib.auth.models import Permission
    from guardian.shortcuts import assign_perm

    from tests.test1.app.models import Book, Publisher

    monkeypatch.setattr(mx.book.Create, "cv_guardian_accept_global_perms", policy == "global", raising=False)
    user = _book_page_actor(mx, world, child)  # page access is independent of the create-parent permission
    change = mx.g.vs.permissions["change"]
    if condition in ("permitted", "revoked", "disabled"):
        assign_perm(change, user, world.a)
    elif condition == "other_parent":
        assign_perm(change, user, world.b)
    elif condition == "global_change":
        user.user_permissions.add(Permission.objects.get(codename="change_publisher"))
    mx.state["book"] = condition != "disabled"
    client.force_login(_refetch(user))

    page_url = _u(mx.book.vs, page, child.pk, world.a.pk)
    create_url = _u(mx.book.vs, "create", parent_pk=world.a.pk)
    if condition == "revoked":
        assert f'href="{create_url}"' in client.get(page_url).content.decode()
        mx.g.vs.remove_perm("change", user, world.a)

    permitted = condition in ("permitted", "disabled") or (condition == "global_change" and policy == "global")
    enabled = condition != "disabled"
    records = _record_contexts(
        monkeypatch, {"detail": mx.book.Detail, "update": mx.book.Update}.get(page, mx.book.Delete)
    )
    mx.state_calls["book"].clear()

    response = client.get(page_url)
    assert response.status_code == 200  # the page stays reachable whatever the create permission
    (ctx,) = [c for key, c in records if key == "create"]
    assert ctx["cv_access"] is permitted
    assert ctx["cv_action_enabled"] is enabled
    assert ctx["cv_url"] == create_url  # linked to the actual FK parent, not the child
    assert (f'href="{create_url}"' in response.content.decode()) is (permitted and enabled)
    assert _render_permission_filter(response) == str(permitted)  # permission-only, independent of state
    assert mx.state_calls["book"], "the create state hook was not consulted"
    assert all(type(obj) is Publisher and obj.pk == world.a.pk for obj in mx.state_calls["book"])

    before = _snapshot()
    allowed = permitted and enabled
    assert client.get(create_url).status_code == (200 if allowed else 403)
    response = client.post(create_url, {"title": "H03 Child", "publisher": world.b.pk})
    assert response.status_code == (302 if allowed else 403)
    created = list(Book.objects.filter(title="H03 Child").values_list("publisher_id", flat=True))
    assert created == ([world.a.pk] if allowed else [])
    assert mx.hooks["book_create"] == (1 if allowed else 0)
    if not allowed:
        _assert_no_write(mx, before)
    if condition == "other_parent":  # the grant is real, just for a different parent
        assert client.post(_u(mx.book.vs, "create", parent_pk=world.b.pk), {"title": "On B"}).status_code == 302
        assert Book.objects.get(title="On B").publisher_id == world.b.pk


# ── interleaved actors, view policies and URL parents (edge AUTH-07 concurrency) ──


@pytest.mark.django_db
def test_interleaved_actors_and_policies_on_one_viewset(mx, monkeypatch, world):
    """Strict and global-accepting views on the same Guardian ViewSet; two sessions interleave; a revocation and a
    deactivation between requests apply to the next request only of the affected actor."""
    from tests.test1.app.models import Publisher

    monkeypatch.setattr(mx.g.List, "cv_guardian_accept_global_perms", False)
    monkeypatch.setattr(mx.g.Detail, "cv_guardian_accept_global_perms", True)
    monkeypatch.setattr(mx.g.Update, "cv_guardian_accept_global_perms", False)
    view, change = mx.g.vs.permissions["view"], mx.g.vs.permissions["change"]
    obj_user = _make_actor("object", [view, change], world.a, name="obj_actor")
    glob_user = _make_actor("global", [view, change], name="glob_actor")

    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
        c_obj, c_glob = Client(), Client()
        c_obj.force_login(obj_user, backend=ALLOW_INACTIVE)
        c_glob.force_login(glob_user, backend=ALLOW_INACTIVE)
        list_url = _u(mx.g.vs, "list")

        assert _pks(c_obj.get(list_url).context["object_list"]) == {world.a.pk}
        assert _pks(c_glob.get(list_url).context["object_list"]) == set()  # strict list ignores global perms
        assert c_glob.get(_u(mx.g.vs, "detail", world.b.pk)).status_code == 200  # global-accepting detail
        assert c_obj.get(_u(mx.g.vs, "detail", world.b.pk)).status_code == 403
        assert c_glob.post(_u(mx.g.vs, "update", world.b.pk), {"name": "Glob"}).status_code == 403  # strict update
        assert c_obj.post(_u(mx.g.vs, "update", world.a.pk), {"name": "Obj"}).status_code == 302
        assert dict(Publisher.objects.values_list("pk", "name")) == {world.a.pk: "Obj", world.b.pk: "Gollancz"}
        assert mx.hooks["update"] == 1

        mx.g.vs.remove_perm("view", obj_user, world.a)
        assert _pks(c_obj.get(list_url).context["object_list"]) == set()
        assert c_obj.get(_u(mx.g.vs, "detail", world.a.pk)).status_code == 403
        assert c_glob.get(_u(mx.g.vs, "detail", world.a.pk)).status_code == 200  # other session unaffected
        assert c_obj.get(_u(mx.g.vs, "update", world.a.pk)).status_code == 200  # change grant untouched

        glob_user.is_active = False
        glob_user.save()
        response = c_glob.get(_u(mx.g.vs, "detail", world.a.pk))
        assert response.status_code == 403
        assert response.wsgi_request.user.pk == glob_user.pk and response.wsgi_request.user.is_active is False
        assert c_glob.get(list_url).status_code == 403
        assert c_obj.get(_u(mx.g.vs, "update", world.a.pk)).status_code == 200
    assert mx.hooks["update"] == 1


@pytest.mark.django_db
def test_interleaved_url_parents_bind_each_request(mx, client, world):
    from tests.test1.app.models import Book, Publisher

    user = _make_actor("object", [mx.g.vs.permissions["change"]], world.a)
    client.force_login(user)
    for title, parent, status in [("A1", world.a, 302), ("B1", world.b, 403), ("A2", world.a, 302)]:
        response = client.post(_u(mx.book.vs, "create", parent_pk=parent.pk), {"title": title})
        assert response.status_code == status
    assert dict(Book.objects.filter(title__in=["A1", "B1", "A2"]).values_list("title", "publisher_id")) == {
        "A1": world.a.pk,
        "A2": world.a.pk,
    }
    assert mx.hooks["book_create"] == 2
    assert all(type(obj) is Publisher and obj.pk == world.a.pk for obj in mx.state_calls["book"])


# ── manage: its own administrative gate, replayed under the patched singleton (D-06, A20) ──


@pytest.fixture
def manage_mode(monkeypatch):
    """Patch the import-time settings singleton (not Django settings); monkeypatch restores it either way."""
    from crud_views.lib.settings import crud_views_settings

    def set_mode(mode):
        monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
        monkeypatch.setattr(crud_views_settings, "manage_group", MANAGE_GROUP)
        assert (crud_views_settings.manage_views_enabled, crud_views_settings.manage_group) == (mode, MANAGE_GROUP)

    return set_mode


@pytest.mark.parametrize(
    ("mode", "debug", "actor", "status"),
    [
        ("yes", False, "anonymous", 200),
        ("yes", False, "nongroup", 200),
        ("yes", False, "group", 200),
        ("debug_only", True, "anonymous", 200),
        ("debug_only", True, "nongroup", 200),
        ("debug_only", False, "anonymous", 302),
        ("debug_only", False, "nongroup", 403),
        ("debug_only", False, "group", 200),
        ("no", False, "anonymous", 302),
        ("no", False, "nongroup", 403),
        ("no", False, "group", 200),
    ],
)
@pytest.mark.parametrize("family", ["core", "strict"])
@pytest.mark.django_db
def test_manage_gate_modes(mx, client, manage_mode, world, family, mode, debug, actor, status):
    from django.contrib.auth.models import Group

    manage_mode(mode)
    if actor != "anonymous":
        user = _make_actor("none", name=f"manage_{actor}")
        if actor == "group":
            user.groups.add(Group.objects.get_or_create(name=MANAGE_GROUP)[0])
        client.force_login(user)
    before = _snapshot()
    with override_settings(DEBUG=debug):
        response = client.get(_u(_fam(mx, family).vs, "manage"))

    assert response.status_code == status
    if status == 302:
        assert response["Location"].startswith(LOGIN)
    if status == 200:
        assert "views" in response.context
    _assert_no_write(mx, before)
