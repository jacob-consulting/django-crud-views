"""Phase 6.2 B5 (AUTH-05, D-11/D-05): inactive actors receive no rows or object access in Guardian views.

The default ``ModelBackend`` refuses inactive sessions (the user becomes anonymous), which masks the defect.
These tests authenticate through ``AllowAllUsersModelBackend`` + Guardian's backend, so the request carries an
authenticated-but-inactive user, and cover ordinary, group-granted, global-only and superuser actors over every
Guardian view type plus the callable query/access helpers. Active actors (including superusers) keep their access.

Already-secure object/parent checks (``ObjectPermissionChecker`` denies inactive users) are preservation tests;
queryset leaks (``get_objects_for_user`` ignores ``is_active``) and the permissive fragment entry were reproduced
red before the fix (A03).
"""

import sys
import types
import uuid
from types import SimpleNamespace

import pytest
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse

from tests.lib.helper.guardian import user_guardian_object_perm

ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"
BACKENDS = [ALLOW_INACTIVE, "guardian.backends.ObjectPermissionBackend"]
ACTORS = ["ordinary", "group", "global", "superuser"]


@pytest.fixture
def allow_inactive():
    with override_settings(AUTHENTICATION_BACKENDS=BACKENDS):
        yield


def _login(client, user):
    client.force_login(user, backend=ALLOW_INACTIVE)
    return client


def _refetch(user):
    from django.contrib.auth.models import User

    return User.objects.get(pk=user.pk)  # drop Django's per-instance permission caches


def _make_actor(kind, *, active, author, publisher, book):
    """An actor holding view/change/delete on ``author``, ``publisher`` and ``book`` (and add on publisher's
    children) through the given channel: own object grants, a group's object grants, global model
    permissions or the superuser flag."""
    from django.contrib.auth.models import Group, Permission, User

    from tests.test1.app.views import cv_guardian_author, cv_guardian_book, cv_guardian_publisher

    name = f"{kind}_{'active' if active else 'inactive'}"
    if kind == "superuser":
        user = User.objects.create_superuser(username=name, password="password")
    else:
        user = User.objects.create_user(username=name, password="password")

    grants = [
        (cv_guardian_author, author, ("view", "change", "delete")),
        (cv_guardian_publisher, publisher, ("view", "change")),
        (cv_guardian_book, book, ("view", "change", "delete")),
    ]
    if kind == "ordinary":
        for viewset, obj, perms in grants:
            for perm in perms:
                user_guardian_object_perm(user, viewset, perm, obj)
    elif kind == "group":
        from guardian.shortcuts import assign_perm

        group = Group.objects.create(name=f"group_{name}")
        user.groups.add(group)
        for viewset, obj, perms in grants:
            for perm in perms:
                assign_perm(viewset.permissions[perm], group, obj)
    elif kind == "global":
        for codename in (
            "view_author",
            "change_author",
            "delete_author",
            "add_author",
            "view_publisher",
            "change_publisher",
            "view_book",
            "change_book",
            "delete_book",
        ):
            user.user_permissions.add(Permission.objects.get(codename=codename))

    if not active:
        user.is_active = False
        user.save()
    return _refetch(user)


@pytest.fixture
def world(db, author_douglas_adams, author_terry_pratchett, publisher_a, book_under_publisher_a):
    return SimpleNamespace(
        author=author_douglas_adams, other=author_terry_pratchett, publisher=publisher_a, book=book_under_publisher_a
    )


def _actor(world, kind, active=False):
    return _make_actor(kind, active=active, author=world.author, publisher=world.publisher, book=world.book)


@pytest.fixture
def accept_global(monkeypatch):
    """Global-only actors are evaluated with each view's per-view global fallback enabled."""
    from tests.test1.app import views

    classes = [
        views.GuardianAuthorListView,
        views.GuardianAuthorCardListView,
        views.GuardianAuthorDetailView,
        views.GuardianAuthorUpdateView,
        views.GuardianAuthorDeleteView,
        views.GuardianBookListView,
        views.GuardianBookDetailView,
        views.GuardianBookCreateView,
    ]
    for cls in classes:
        monkeypatch.setattr(cls, "cv_guardian_accept_global_perms", True, raising=False)


# ── request identity: the backend really carries an inactive session ─────────


@pytest.mark.django_db
def test_allow_all_backend_keeps_inactive_session_authenticated(allow_inactive, client, world):
    user = _actor(world, "ordinary")
    response = _login(client, user).get("/guardian_author/")
    request_user = response.wsgi_request.user
    assert request_user.is_authenticated is True
    assert request_user.is_active is False
    assert request_user.pk == user.pk


@pytest.mark.django_db
def test_default_backend_masks_inactive_session_as_anonymous(client, world):
    """Control: the default backend turns the inactive session anonymous (login redirect), hiding B5."""
    client.force_login(_actor(world, "superuser"))
    response = client.get("/guardian_author/")
    assert response.status_code == 302
    assert response.wsgi_request.user.is_authenticated is False


# ── list / card: no rows (red before the fix: queryset leak) ──────────────────


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.parametrize("url", ["/guardian_author/", "/guardian_author/card/"])
@pytest.mark.django_db
def test_inactive_list_and_card_denied_without_rows(allow_inactive, accept_global, client, world, kind, url):
    response = _login(client, _actor(world, kind)).get(url)
    assert response.status_code == 403
    content = response.content.decode()
    assert "Douglas" not in content
    assert "Pratchett" not in content


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_child_list_denied_without_rows(allow_inactive, accept_global, client, world, kind):
    response = _login(client, _actor(world, kind)).get(f"/guardian_publisher/{world.publisher.pk}/guardian_book/")
    assert response.status_code == 403
    assert "Hitchhiker" not in response.content.decode()


# ── object views, create and DELETE: 403, storage unchanged ───────────────────


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_object_views_denied(allow_inactive, accept_global, client, world, kind):
    """Preservation for GET/POST (the object checker already denies inactive users)."""
    from tests.test1.app.models import Author

    _login(client, _actor(world, kind))
    pk = world.author.pk
    assert client.get(f"/guardian_author/{pk}/detail/").status_code == 403
    assert client.get(f"/guardian_author/{pk}/update/").status_code == 403
    assert client.post(f"/guardian_author/{pk}/update/", {"first_name": "X", "last_name": "Y"}).status_code == 403
    assert client.get(f"/guardian_author/{pk}/delete/").status_code == 403
    assert client.post(f"/guardian_author/{pk}/delete/", {"confirm": "on"}).status_code == 403
    author = Author.objects.get(pk=pk)
    assert (author.first_name, author.last_name) == ("Douglas", "Adams")


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_http_delete_is_403_not_405(allow_inactive, client, world, kind):
    """Inactive dispatch rejects DELETE with 403 before the method guard (active top-level is 405)."""
    from tests.test1.app.models import Author

    response = _login(client, _actor(world, kind)).delete(f"/guardian_author/{world.author.pk}/delete/")
    assert response.status_code == 403
    assert Author.objects.filter(pk=world.author.pk).exists()


@pytest.mark.django_db
def test_active_top_level_http_delete_stays_405(allow_inactive, client, world):
    from tests.test1.app.models import Author

    response = _login(client, _actor(world, "ordinary", active=True)).delete(
        f"/guardian_author/{world.author.pk}/delete/"
    )
    assert response.status_code == 405
    assert Author.objects.filter(pk=world.author.pk).exists()


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_create_denied_without_write(allow_inactive, accept_global, client, world, kind):
    from tests.test1.app.models import Author, Book

    _login(client, _actor(world, kind))
    assert client.get("/guardian_author/create/").status_code == 403
    assert client.post("/guardian_author/create/", {"first_name": "New", "last_name": "Author"}).status_code == 403
    child_url = f"/guardian_publisher/{world.publisher.pk}/guardian_book/create/"
    assert client.get(child_url).status_code == 403
    assert client.post(child_url, {"title": "Inactive Book"}).status_code == 403
    assert not Author.objects.filter(first_name="New").exists()
    assert not Book.objects.filter(title="Inactive Book").exists()


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_child_object_views_denied(allow_inactive, accept_global, client, world, kind):
    base = f"/guardian_publisher/{world.publisher.pk}/guardian_book/{world.book.pk}"
    _login(client, _actor(world, kind))
    assert client.get(f"{base}/detail/").status_code == 403
    assert client.get(f"{base}/update/").status_code == 403
    assert client.post(f"{base}/update/", {"title": "Changed"}).status_code == 403
    world.book.refresh_from_db()
    assert world.book.title == "Hitchhiker's Guide"


# ── isolated action and formset-fragment routes (A08) ─────────────────────────


@pytest.fixture
def routes():
    """Fresh Guardian Publisher routes: list, an action, and a formset update view with fragment GETs."""
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyViewMixin
    from crud_views.lib.formsets import FormSetMixin
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK
    from crud_views_guardian.lib.views import (
        GuardianActionViewPermissionRequired,
        GuardianListViewPermissionRequired,
        GuardianUpdateViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Publisher
    from tests.test1.app.views_formset import PublisherFormSetForm, publisher_formsets

    sfx = uuid.uuid4().hex[:8]
    name = f"inpub{sfx}"
    modname = f"tests.test1._inactive_urls_{sfx}"
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    calls = {"action": 0, "fragment": 0}

    try:
        viewset = GuardianViewSet(model=Publisher, name=name, icon_header="fa-regular fa-building")

        class InPublisherListView(GuardianListViewPermissionRequired):
            cv_viewset = viewset

        class InPublisherPingView(GuardianActionViewPermissionRequired):
            cv_key = "ping"
            cv_path = "ping"
            cv_viewset = viewset
            cv_icon_action = "fa-solid fa-bolt"
            cv_action_label_template_code = "Ping"
            cv_action_short_label_template_code = "Ping"

            def action(self, context):
                calls["action"] += 1
                return True

        class InPublisherUpdateView(CrispyViewMixin, FormSetMixin, GuardianUpdateViewPermissionRequired):
            form_class = PublisherFormSetForm
            cv_viewset = viewset
            cv_formsets = publisher_formsets

            def get_template_html(self, request):
                calls["fragment"] += 1
                return super().get_template_html(request)

        module = types.ModuleType(modname)
        module.urlpatterns = [*viewset.urlpatterns, path("", include("tests.test1.project.urls"))]
        sys.modules[modname] = module

        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield SimpleNamespace(viewset=viewset, calls=calls)
            finally:
                clear_url_caches()
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        sys.modules.pop(modname, None)
        clear_url_caches()


def _publisher_actor(routes, publisher, kind, active):
    from django.contrib.auth.models import Group, Permission, User
    from guardian.shortcuts import assign_perm

    name = f"pub_{kind}_{'active' if active else 'inactive'}"
    if kind == "superuser":
        user = User.objects.create_superuser(username=name, password="password")
    else:
        user = User.objects.create_user(username=name, password="password")
    perms = [routes.viewset.permissions[p] for p in ("view", "change")]
    if kind == "ordinary":
        for perm in perms:
            assign_perm(perm, user, publisher)
    elif kind == "group":
        group = Group.objects.create(name=f"group_{name}")
        user.groups.add(group)
        for perm in perms:
            assign_perm(perm, group, publisher)
    elif kind == "global":
        for codename in ("view_publisher", "change_publisher"):
            user.user_permissions.add(Permission.objects.get(codename=codename))
    if not active:
        user.is_active = False
        user.save()
    return _refetch(user)


def _fragment_url(routes, publisher):
    url = reverse(routes.viewset.get_router_name("update"), kwargs={"pk": publisher.pk})
    return f"{url}?template=books&num=0&pk={publisher.pk}"


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_action_post_denied_without_action(allow_inactive, monkeypatch, routes, client, publisher_a, kind):
    from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin

    monkeypatch.setattr(GuardianObjectPermissionMixin, "cv_guardian_accept_global_perms", kind == "global")
    _login(client, _publisher_actor(routes, publisher_a, kind, active=False))
    url = reverse(routes.viewset.get_router_name("ping"), kwargs={"pk": publisher_a.pk})
    assert client.post(url).status_code == 403
    assert routes.calls["action"] == 0


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_fragment_denied_at_dispatch_before_rendering(
    allow_inactive, monkeypatch, routes, client, publisher_a, kind
):
    """The fragment GET is answered before get_object(); inactive dispatch must stop it first (B5 + B2 entry)."""
    from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin

    monkeypatch.setattr(GuardianObjectPermissionMixin, "cv_guardian_accept_global_perms", kind == "global")
    _login(client, _publisher_actor(routes, publisher_a, kind, active=False))
    response = client.get(_fragment_url(routes, publisher_a))
    assert response.status_code == 403
    assert routes.calls["fragment"] == 0
    assert b"Books" not in response.content


@pytest.mark.parametrize("kind", ["ordinary", "superuser"])
@pytest.mark.django_db
def test_active_action_and_fragment_still_allowed(allow_inactive, routes, client, publisher_a, kind):
    _login(client, _publisher_actor(routes, publisher_a, kind, active=True))
    url = reverse(routes.viewset.get_router_name("ping"), kwargs={"pk": publisher_a.pk})
    assert client.post(url).status_code == 302
    assert routes.calls["action"] == 1
    response = client.get(_fragment_url(routes, publisher_a))
    assert response.status_code == 200
    assert set(response.json()) == {"html", "rows"}
    assert routes.calls["fragment"] == 1


# ── callable helpers return no authority (red before the fix for queryset paths) ──


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_viewset_get_objects_for_user_is_empty(world, kind):
    from tests.test1.app.views import cv_guardian_author

    user = _actor(world, kind)
    assert list(cv_guardian_author.get_objects_for_user(user, "view")) == []


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.parametrize("accept_global", [False, True])
@pytest.mark.django_db
def test_inactive_permitted_pks_cache_is_empty(world, kind, accept_global):
    from crud_views_guardian.lib.views import _PermittedPks
    from tests.test1.app.models import Author

    assert _PermittedPks(_actor(world, kind), accept_global)(Author) == set()


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_access_helpers_deny(world, monkeypatch, kind):
    from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin
    from tests.test1.app.views import (
        GuardianAuthorDetailView,
        GuardianAuthorListView,
        GuardianBookCreateView,
        cv_guardian_book,
    )

    monkeypatch.setattr(GuardianObjectPermissionMixin, "cv_guardian_accept_global_perms", kind == "global")
    monkeypatch.setattr(GuardianBookCreateView, "cv_guardian_accept_global_perms", kind == "global", raising=False)
    user = _actor(world, kind)

    assert GuardianAuthorDetailView.cv_has_access(user, world.author) is False
    assert GuardianAuthorListView.cv_has_access(user) is False
    assert GuardianAuthorListView.cv_has_access(user, world.author) is False
    assert GuardianBookCreateView.cv_has_access(user, world.publisher) is False
    assert GuardianBookCreateView.cv_has_access(user, world.book) is False
    assert GuardianBookCreateView.cv_create_has_access(user, None, world.publisher) is False

    # a None parent policy skips only the permission evaluation — never the inactive denial
    monkeypatch.setattr(cv_guardian_book, "cv_guardian_parent_permission", None)
    monkeypatch.setattr(cv_guardian_book, "cv_guardian_parent_create_permission", None)
    assert GuardianBookCreateView.cv_has_access(user, world.publisher) is False
    assert GuardianBookCreateView.cv_create_has_access(user, None, world.publisher) is False


@pytest.mark.parametrize("kind", ACTORS)
@pytest.mark.django_db
def test_inactive_delete_preview_hides_protected_and_related_labels(world, kind):
    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin

    user = _actor(world, kind)
    related = RelatedObjects(tree=[world.author, [world.other]], summary=[("authors", 2)], protected=[world.author])
    projected = GuardianDeleteRelatedObjectsMixin().cv_filter_related_objects(user, related)
    assert projected.tree == [None, [None]]
    assert projected.protected == []
    assert projected.summary == related.summary


# ── active actors keep their semantics (D-05) ─────────────────────────────────


@pytest.mark.django_db
def test_active_superuser_keeps_full_access(allow_inactive, client, world):
    from tests.test1.app.views import GuardianAuthorDetailView, cv_guardian_author

    root = _actor(world, "superuser", active=True)
    assert set(cv_guardian_author.get_objects_for_user(root, "view")) == {world.author, world.other}
    assert GuardianAuthorDetailView.cv_has_access(root, world.other) is True

    _login(client, root)
    content = client.get("/guardian_author/").content.decode()
    assert "Douglas" in content and "Pratchett" in content
    assert client.get(f"/guardian_author/{world.other.pk}/detail/").status_code == 200


@pytest.mark.parametrize("kind", ["ordinary", "group"])
@pytest.mark.django_db
def test_active_granted_actor_sees_only_granted_rows(allow_inactive, client, world, kind):
    from tests.test1.app.views import cv_guardian_author

    user = _actor(world, kind, active=True)
    assert list(cv_guardian_author.get_objects_for_user(user, "view")) == [world.author]

    _login(client, user)
    response = client.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" in response.content.decode()
    assert "Pratchett" not in response.content.decode()
    assert client.get(f"/guardian_author/{world.author.pk}/detail/").status_code == 200


@pytest.mark.django_db
def test_active_global_only_actor_stays_strict_in_viewset_helper(world):
    """D-05: the ViewSet helper ignores global model permissions for active actors as well."""
    from tests.test1.app.views import cv_guardian_author

    assert list(cv_guardian_author.get_objects_for_user(_actor(world, "global", active=True), "view")) == []


# ── next-request revocation and deactivation (edge AUTH-05 concurrency) ───────


@pytest.mark.django_db
def test_deactivation_applies_on_next_request(allow_inactive, client, world):
    from tests.test1.app.views import cv_guardian_author

    user = _actor(world, "ordinary", active=True)
    _login(client, user)
    assert "Douglas" in client.get("/guardian_author/").content.decode()
    assert client.get(f"/guardian_author/{world.author.pk}/detail/").status_code == 200

    user.is_active = False
    user.save()
    response = client.get("/guardian_author/")
    assert response.status_code == 403
    assert "Douglas" not in response.content.decode()
    assert client.get(f"/guardian_author/{world.author.pk}/detail/").status_code == 403
    assert list(cv_guardian_author.get_objects_for_user(_refetch(user), "view")) == []


@pytest.mark.django_db
def test_superuser_deactivation_applies_on_next_request(allow_inactive, client, world):
    root = _actor(world, "superuser", active=True)
    _login(client, root)
    assert client.get("/guardian_author/").status_code == 200

    root.is_active = False
    root.save()
    response = client.get("/guardian_author/")
    assert response.status_code == 403
    assert "Pratchett" not in response.content.decode()


@pytest.mark.django_db
def test_grant_revocation_applies_on_next_request(allow_inactive, client, world):
    from tests.test1.app.views import cv_guardian_author

    user = _actor(world, "ordinary", active=True)
    _login(client, user)
    assert "Douglas" in client.get("/guardian_author/").content.decode()

    cv_guardian_author.remove_perm("view", user, world.author)
    response = client.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" not in response.content.decode()
    assert client.get(f"/guardian_author/{world.author.pk}/detail/").status_code == 403
