"""Phase 6.2 B7 (AUTH-06): Guardian global-permission fallback is a per-view policy.

The ineffective ``GuardianViewSet.cv_guardian_accept_global_perms`` field is removed (D-04): supplying it fails with a
validation error naming the per-view replacement instead of being silently ignored. Two views on one ViewSet keep
opposite fallback policies (D-03), and ``GuardianViewSet.get_objects_for_user()`` stays strict (D-05).

Every route here is built by a yielding fixture on fresh, uniquely named ViewSets with a temporary ROOT_URLCONF;
the registry, vocabulary cache, URL caches and module registration are restored in ``finally`` (A08).
"""

import sys
import types
import uuid
from types import SimpleNamespace

import pytest
from django.test import override_settings
from django.urls import clear_url_caches, include, path, reverse
from pydantic import ValidationError

ALLOW_INACTIVE = "django.contrib.auth.backends.AllowAllUsersModelBackend"
INACTIVE_BACKENDS = [ALLOW_INACTIVE, "guardian.backends.ObjectPermissionBackend"]
REMOVED_KEY = "cv_guardian_accept_global_perms"

# ── isolated route fixture ────────────────────────────────────────────────────


@pytest.fixture
def pol():
    """Fresh Guardian routes covering every global-fallback applicability category.

    Publisher ViewSet: strict list, global-accepting detail, plain (non-Guardian) update, top-level create with
    fallback=True. Book child (parent permission "view"): global-accepting list and parent-only create. Free child
    (both parent permissions None): strict list and a parent-only create with fallback=True.
    """
    from crud_views.lib import check as check_module
    from crud_views.lib.crispy import CrispyViewMixin
    from crud_views.lib.views import CreateViewParentMixin, UpdateViewPermissionRequired
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Book, Publisher
    from tests.test1.app.views import BookForm, PublisherForm

    sfx = uuid.uuid4().hex[:8]
    names = [f"polpub{sfx}", f"polbook{sfx}", f"polfree{sfx}"]
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    modname = f"tests.test1._pol_urls_{sfx}"

    try:
        pub_vs = GuardianViewSet(model=Publisher, name=names[0], icon_header="fa-regular fa-building")

        class PolPublisherListView(GuardianListViewPermissionRequired):
            cv_viewset = pub_vs  # strict (default)

        class PolPublisherDetailView(GuardianDetailViewPermissionRequired):
            cv_viewset = pub_vs
            cv_guardian_accept_global_perms = True

        class PolPublisherUpdateView(CrispyViewMixin, UpdateViewPermissionRequired):
            form_class = PublisherForm
            cv_viewset = pub_vs  # plain core view: no Guardian policy

        class PolPublisherCreateView(CrispyViewMixin, GuardianCreateViewPermissionRequired):
            form_class = PublisherForm
            cv_viewset = pub_vs
            cv_guardian_accept_global_perms = True  # top-level: the parent mixin never consults it

        book_vs = GuardianViewSet(
            model=Book,
            name=names[1],
            parent=ParentViewSet(name=names[0], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
        )

        class PolBookListView(GuardianListViewPermissionRequired):
            cv_viewset = book_vs
            cv_guardian_accept_global_perms = True

        class PolBookCreateView(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = book_vs  # parent-only view, resolved parent permission "view": strict

        free_vs = GuardianViewSet(
            model=Book,
            name=names[2],
            parent=ParentViewSet(name=names[0], attribute="publisher"),
            icon_header="fa-regular fa-address-book",
            cv_guardian_parent_permission=None,
            cv_guardian_parent_create_permission=None,
        )

        class PolFreeListView(GuardianListViewPermissionRequired):
            cv_viewset = free_vs  # strict queryset policy stays applicable despite the None parent policy

        class PolFreeCreateView(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
            form_class = BookForm
            cv_viewset = free_vs
            cv_guardian_accept_global_perms = True  # parent permission None: fallback never consulted

        module = types.ModuleType(modname)
        module.urlpatterns = [
            *pub_vs.urlpatterns,
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
                    pub_vs=pub_vs,
                    book_vs=book_vs,
                    free_vs=free_vs,
                    PublisherList=PolPublisherListView,
                    PublisherDetail=PolPublisherDetailView,
                    PublisherUpdate=PolPublisherUpdateView,
                    PublisherCreate=PolPublisherCreateView,
                    BookList=PolBookListView,
                    BookCreate=PolBookCreateView,
                    FreeList=PolFreeListView,
                    FreeCreate=PolFreeCreateView,
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
def allow_inactive():
    with override_settings(AUTHENTICATION_BACKENDS=INACTIVE_BACKENDS):
        yield


def _url(viewset, key, pk=None, parent_pk=None):
    kwargs = {}
    if parent_pk is not None:
        kwargs[viewset.parent.get_pk_name()] = parent_pk
    if pk is not None:
        kwargs["pk"] = pk
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def _user(username, *, superuser=False, active=True):
    from django.contrib.auth.models import User

    if superuser:
        user = User.objects.create_superuser(username=username, password="password")
    else:
        user = User.objects.create_user(username=username, password="password")
    if not active:
        user.is_active = False
        user.save()
    return user


def _grant_global(user, *codenames):
    from django.contrib.auth.models import Permission, User

    for codename in codenames:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return User.objects.get(pk=user.pk)  # drop Django's per-instance permission cache


def _pks(qs):
    return sorted(obj.pk for obj in qs)


@pytest.fixture
def publishers(db):
    from tests.test1.app.models import Publisher

    return Publisher.objects.create(name="Alpha Press"), Publisher.objects.create(name="Beta Books")


@pytest.fixture
def unique_name():
    """A fresh ViewSet name that is guaranteed to leave the registry afterwards."""
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK

    name = f"polctor{uuid.uuid4().hex[:8]}"
    try:
        yield name
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)


# ── removed ViewSet flag: constructor diagnostics (D-04, A12) ─────────────────


def test_viewset_field_is_removed():
    from crud_views_guardian.lib.viewset import GuardianViewSet

    assert REMOVED_KEY not in GuardianViewSet.model_fields


@pytest.mark.django_db
@pytest.mark.parametrize("value", [True, False])
def test_removed_flag_keyword_is_rejected_with_per_view_replacement(value, unique_name):
    from crud_views.lib.viewset import _REGISTRY
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Publisher

    with pytest.raises(ValidationError) as excinfo:
        GuardianViewSet(model=Publisher, name=unique_name, **{REMOVED_KEY: value})

    message = str(excinfo.value)
    assert REMOVED_KEY in message
    assert "view class" in message  # names the per-view replacement
    assert "get_objects_for_user" in message  # and that the helper stays strict
    # failed construction never reaches the after-validator's registration
    assert unique_name not in _REGISTRY


@pytest.mark.django_db
@pytest.mark.parametrize("value", [True, False])
def test_removed_flag_in_model_validate_mapping_is_rejected(value, unique_name):
    from crud_views.lib.viewset import _REGISTRY
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Publisher

    with pytest.raises(ValidationError, match=REMOVED_KEY):
        GuardianViewSet.model_validate({"model": Publisher, "name": unique_name, REMOVED_KEY: value})
    assert unique_name not in _REGISTRY


@pytest.mark.django_db
def test_unrelated_extra_keyword_keeps_existing_behavior(unique_name):
    """Only the exact removed key is rejected; other extras keep Pydantic's established (ignore) behavior."""
    from crud_views.lib.viewset import _REGISTRY
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Publisher

    vs = GuardianViewSet(model=Publisher, name=unique_name, cv_guardian_accept_global_permissions=True)
    assert _REGISTRY[unique_name] is vs
    assert not hasattr(vs, "cv_guardian_accept_global_permissions")


@pytest.mark.django_db
def test_model_validate_existing_instance_keeps_after_validator_behavior(pol):
    """A non-mapping instance passes the before-validator untouched (no TypeError). Pydantic still runs the
    after-validator on it, whose registration guard rejects the duplicate name exactly as before (A12)."""
    from crud_views.lib.exceptions import ViewSetError
    from crud_views.lib.viewset import _REGISTRY
    from crud_views_guardian.lib.viewset import GuardianViewSet

    with pytest.raises(ViewSetError, match="already registered"):
        GuardianViewSet.model_validate(pol.pub_vs)
    assert _REGISTRY[pol.pub_vs.name] is pol.pub_vs


@pytest.mark.parametrize("data", [42, "cv_guardian_accept_global_perms", [REMOVED_KEY, True]])
def test_non_mapping_input_is_a_pydantic_validation_error(data):
    from crud_views_guardian.lib.viewset import GuardianViewSet

    with pytest.raises(ValidationError):
        GuardianViewSet.model_validate(data)


# ── per-view policies on one ViewSet; the strict helper (D-03, D-05) ──────────


@pytest.mark.django_db
def test_global_only_user_follows_each_views_own_policy(pol, client, publishers):
    a, b = publishers
    user = _grant_global(_user("global_only"), "view_publisher")
    client.force_login(user)

    # strict list: a model-level permission alone yields no rows
    response = client.get(_url(pol.pub_vs, "list"))
    assert response.status_code == 200
    assert _pks(response.context["object_list"]) == []
    # global-accepting sibling detail on the same ViewSet: the model permission is enough
    assert client.get(_url(pol.pub_vs, "detail", pk=a.pk)).status_code == 200
    assert client.get(_url(pol.pub_vs, "detail", pk=b.pk)).status_code == 200
    # the helper stays strict
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == []


@pytest.mark.django_db
def test_object_grant_user_is_scoped_to_granted_rows_under_both_policies(pol, client, publishers):
    a, b = publishers
    user = _user("object_grant")
    pol.pub_vs.assign_perm("view", user, a)
    client.force_login(user)

    response = client.get(_url(pol.pub_vs, "list"))
    assert response.status_code == 200
    assert _pks(response.context["object_list"]) == [a.pk]
    assert client.get(_url(pol.pub_vs, "detail", pk=a.pk)).status_code == 200
    assert client.get(_url(pol.pub_vs, "detail", pk=b.pk)).status_code == 403
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == [a.pk]


@pytest.mark.django_db
def test_group_object_grant_is_honored_by_views_and_helper(pol, client, publishers):
    from django.contrib.auth.models import Group

    a, b = publishers
    user = _user("group_member")
    group = Group.objects.create(name="pol_readers")
    user.groups.add(group)
    pol.pub_vs.assign_perm("view", group, b)
    client.force_login(user)

    response = client.get(_url(pol.pub_vs, "list"))
    assert _pks(response.context["object_list"]) == [b.pk]
    assert client.get(_url(pol.pub_vs, "detail", pk=b.pk)).status_code == 200
    assert client.get(_url(pol.pub_vs, "detail", pk=a.pk)).status_code == 403
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == [b.pk]


@pytest.mark.django_db
def test_active_superuser_keeps_full_access_and_helper_rows(pol, client, publishers):
    a, b = publishers
    user = _user("super", superuser=True)
    client.force_login(user)

    response = client.get(_url(pol.pub_vs, "list"))
    assert _pks(response.context["object_list"]) == sorted([a.pk, b.pk])
    assert client.get(_url(pol.pub_vs, "detail", pk=a.pk)).status_code == 200
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == sorted([a.pk, b.pk])


@pytest.mark.django_db
def test_inactive_user_is_denied_by_both_policies_and_helper(pol, client, publishers, allow_inactive):
    a, _b = publishers
    user = _grant_global(_user("inactive", active=False), "view_publisher")
    pol.pub_vs.assign_perm("view", user, a)
    client.force_login(user, backend=ALLOW_INACTIVE)

    assert client.get(_url(pol.pub_vs, "list")).status_code == 403
    assert client.get(_url(pol.pub_vs, "detail", pk=a.pk)).status_code == 403
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == []


@pytest.mark.django_db
def test_inactive_superuser_helper_returns_nothing(pol, publishers):
    user = _user("inactive_super", superuser=True, active=False)
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == []


# ── manage renders with the strict helper entry (D-05, A09) ───────────────────


STRICT_HELPER = {"policy": "strict", "accept_global_perms": False, "use_groups": True}


@pytest.mark.django_db
def test_manage_reports_strict_helper_instead_of_removed_flag(pol, client):
    client.force_login(_user("manager"))
    response = client.get(_url(pol.pub_vs, "manage"))
    assert response.status_code == 200

    config = response.context["guardian_config"]
    assert REMOVED_KEY not in config
    assert config["get_objects_for_user"] == STRICT_HELPER

    content = response.content.decode()
    assert "GuardianViewSet.get_objects_for_user()" in content
    assert "global model permissions are not accepted" in content


@pytest.mark.django_db
def test_helper_policy_entry_matches_the_helper_call(pol, publishers, monkeypatch):
    """The displayed strict-helper values are the ones actually passed to guardian."""
    import guardian.shortcuts

    calls: list = []
    original = guardian.shortcuts.get_objects_for_user

    def spy(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(guardian.shortcuts, "get_objects_for_user", spy)
    pol.pub_vs.get_objects_for_user(_user("spy"), "view")

    assert len(calls) == 1
    assert calls[0]["accept_global_perms"] is STRICT_HELPER["accept_global_perms"]
    assert calls[0]["use_groups"] is STRICT_HELPER["use_groups"]
