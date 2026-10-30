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
from collections import UserDict
from types import MappingProxyType, SimpleNamespace

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
@pytest.mark.parametrize("mapping_type", [UserDict, MappingProxyType])
@pytest.mark.parametrize("value", [True, False])
def test_removed_flag_in_non_dict_mapping_names_replacement_and_never_registers(mapping_type, value, unique_name):
    """AUTH-06/A12: the removed-key guard applies to Mapping input, including callers that wrap config dicts."""
    from crud_views.lib.viewset import _REGISTRY
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Publisher

    data = mapping_type({"model": Publisher, "name": unique_name, REMOVED_KEY: value})
    with pytest.raises(ValidationError) as excinfo:
        GuardianViewSet.model_validate(data)

    message = str(excinfo.value)
    assert REMOVED_KEY in message
    assert "view class" in message
    assert "get_objects_for_user" in message
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
@pytest.mark.parametrize("actor", ["object", "group", "global", "superuser", "inactive"])
def test_strict_helper_intersects_supplied_queryset_and_never_widens_empty_scope(pol, publishers, actor):
    """AUTH-06/D-05: caller scope and object authority both constrain qs=, even when the scope is empty."""
    from django.contrib.auth.models import Group

    from tests.test1.app.models import Publisher

    a, b = publishers
    outside = Publisher.objects.create(name="Outside caller scope")
    user = _user("scoped_helper", superuser=actor == "superuser", active=actor != "inactive")
    if actor == "global":
        user = _grant_global(user, "view_publisher")
    elif actor == "group":
        group = Group.objects.create(name="scoped_readers")
        user.groups.add(group)
        for obj in (a, outside):
            pol.pub_vs.assign_perm("view", group, obj)
    elif actor in {"object", "inactive"}:
        for obj in (a, outside):
            pol.pub_vs.assign_perm("view", user, obj)

    scope = Publisher.objects.filter(pk__in=[a.pk, b.pk])
    expected = sorted([a.pk, b.pk]) if actor == "superuser" else [a.pk] if actor in {"object", "group"} else []
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view", qs=scope)) == expected
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view", qs=Publisher.objects.none())) == []


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


# ── manage: effective global-fallback policy per registered view (D-06, A17) ──


def _policy(*, applicable, accept=None):
    effective = "not applicable"
    if applicable:
        effective = "global fallback" if accept else "strict"
    return {
        "global_fallback_applicable": applicable,
        "cv_guardian_accept_global_perms": accept,
        "effective_policy": effective,
    }


def _manage(client, viewset, parent_pk=None):
    response = client.get(_url(viewset, "manage", parent_pk=parent_pk))
    assert response.status_code == 200
    return response


def _views_policy(response):
    return {key: dict(view["guardian_policy"]) for key, view in response.context["views"].items()}


def _flat(response):
    import re

    return re.sub(r"\s+", " ", response.content.decode())


def _policy_row(view_key, accept_cell, effective_text):
    import re

    return re.compile(
        rf"<tr> <td>{re.escape(view_key)}</td> <td>{re.escape(accept_cell)}</td> <td>{re.escape(effective_text)}</td>"
    )


@pytest.mark.django_db
def test_manage_context_reports_mixed_policies_on_one_viewset(pol, client):
    client.force_login(_user("manager"))
    policies = _views_policy(_manage(client, pol.pub_vs))

    assert policies == {
        "list": _policy(applicable=True, accept=False),  # queryset view, strict
        "detail": _policy(applicable=True, accept=True),  # object view, global fallback
        "update": _policy(applicable=False),  # plain core view
        "create": _policy(applicable=False),  # top-level create: fallback=True never consulted
        "manage": _policy(applicable=False),  # manage itself
    }


@pytest.mark.django_db
def test_manage_context_reports_parent_only_applicability(pol, client, publishers):
    a, _b = publishers
    client.force_login(_user("manager"))

    # parent permission "view": the parent-only create consults its (default, strict) fallback
    book = _views_policy(_manage(client, pol.book_vs, parent_pk=a.pk))
    assert book["list"] == _policy(applicable=True, accept=True)
    assert book["create"] == _policy(applicable=True, accept=False)
    assert book["manage"] == _policy(applicable=False)

    # both parent permissions None: the parent-only create never consults fallback=True; the queryset view still does
    free = _views_policy(_manage(client, pol.free_vs, parent_pk=a.pk))
    assert free["list"] == _policy(applicable=True, accept=False)
    assert free["create"] == _policy(applicable=False)


@pytest.mark.django_db
def test_manage_never_reads_policy_from_the_viewset(pol, client, monkeypatch):
    """Changing a view class flips its row; the row is the view's own class attribute (D-03)."""
    client.force_login(_user("manager"))
    monkeypatch.setattr(pol.PublisherList, "cv_guardian_accept_global_perms", True)
    monkeypatch.setattr(pol.PublisherDetail, "cv_guardian_accept_global_perms", False)

    policies = _views_policy(_manage(client, pol.pub_vs))
    assert policies["list"] == _policy(applicable=True, accept=True)
    assert policies["detail"] == _policy(applicable=True, accept=False)


@pytest.mark.django_db
def test_manage_html_names_each_views_policy_and_the_strict_helper(pol, client):
    client.force_login(_user("manager"))
    content = _flat(_manage(client, pol.pub_vs))

    assert "Global permission fallback" in content
    assert _policy_row("list", "False", "strict: object and group grants only").search(content)
    assert _policy_row("detail", "True", "global fallback: model permissions accepted").search(content)
    assert _policy_row("update", "—", "not applicable").search(content)
    assert _policy_row("create", "—", "not applicable").search(content)
    assert _policy_row("manage", "—", "not applicable").search(content)
    # the helper is reported separately and as strict, never as sharing a view's fallback
    assert "GuardianViewSet.get_objects_for_user() is independent of these view policies and always strict" in content
    assert "strict: object and group grants only; global model permissions are not accepted" in content


@pytest.mark.django_db
def test_manage_html_reports_parent_none_create_as_not_applicable(pol, client, publishers):
    a, _b = publishers
    client.force_login(_user("manager"))
    content = _flat(_manage(client, pol.free_vs, parent_pk=a.pk))

    assert _policy_row("create", "—", "not applicable").search(content)
    assert _policy_row("list", "False", "strict: object and group grants only").search(content)


# ── the reported policies match actual access ─────────────────────────────────


@pytest.mark.django_db
def test_parent_none_create_with_fallback_succeeds_without_grants(pol, client, publishers):
    """Reported "not applicable": the enabled create needs no parent, child or global grant at all."""
    from tests.test1.app.models import Book

    a, _b = publishers
    client.force_login(_user("no_grants"))
    url = _url(pol.free_vs, "create", parent_pk=a.pk)

    assert client.get(url).status_code == 200
    assert client.post(url, {"title": "Free Policy Book"}).status_code == 302
    assert list(Book.objects.filter(title="Free Policy Book").values_list("publisher_id", flat=True)) == [a.pk]


@pytest.mark.django_db
def test_reported_child_policies_match_access_for_a_global_only_user(pol, client, publishers):
    """Reported "global fallback" list admits a model permission; reported "strict" create does not."""
    from tests.test1.app.models import Book

    a, _b = publishers
    book = Book.objects.create(title="Shared Book", publisher=a)
    client.force_login(_grant_global(_user("global_only"), "view_publisher", "view_book"))

    response = client.get(_url(pol.book_vs, "list", parent_pk=a.pk))
    assert response.status_code == 200
    assert _pks(response.context["object_list"]) == [book.pk]
    assert client.get(_url(pol.book_vs, "create", parent_pk=a.pk)).status_code == 403


# ── manage gate preserved (A20): patched singleton modes/groups, live DEBUG ───

MANAGE_GROUP = "pol_manage_admins"


@pytest.fixture
def manage_mode(monkeypatch):
    """Patch the import-time settings singleton (not Django settings); monkeypatch restores it either way."""
    from crud_views.lib.settings import crud_views_settings

    def set_mode(mode):
        monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
        monkeypatch.setattr(crud_views_settings, "manage_group", MANAGE_GROUP)

    return set_mode


def _actor_client(client, actor):
    from django.contrib.auth.models import Group

    if actor == "anonymous":
        return client
    user = _user(f"manage_{actor}")
    if actor == "group":
        user.groups.add(Group.objects.get_or_create(name=MANAGE_GROUP)[0])
    client.force_login(user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mode", "debug", "actor", "status"),
    [
        ("yes", False, "anonymous", 200),
        ("yes", False, "nongroup", 200),
        ("debug_only", True, "anonymous", 200),
        ("debug_only", True, "nongroup", 200),
        ("debug_only", False, "anonymous", 302),
        ("debug_only", False, "nongroup", 403),
        ("debug_only", False, "group", 200),
        ("no", False, "anonymous", 302),
        ("no", True, "anonymous", 302),
        ("no", False, "nongroup", 403),
        ("no", True, "nongroup", 403),
        ("no", False, "group", 200),
    ],
)
def test_manage_gate_is_unchanged(pol, client, manage_mode, mode, debug, actor, status):
    manage_mode(mode)
    with override_settings(DEBUG=debug):
        response = _actor_client(client, actor).get(_url(pol.pub_vs, "manage"))

    assert response.status_code == status
    if status == 302:
        assert "/accounts/login/" in response["Location"]
    if status == 200:
        assert "views" in response.context
    else:
        assert "Global permission fallback" not in response.content.decode()


@pytest.mark.django_db
def test_group_member_sees_policy_rows_under_group_gate(pol, client, manage_mode):
    manage_mode("no")
    response = _actor_client(client, "group").get(_url(pol.pub_vs, "manage"))

    assert response.status_code == 200
    assert _views_policy(response)["detail"] == _policy(applicable=True, accept=True)
    assert _policy_row("detail", "True", "global fallback: model permissions accepted").search(_flat(response))


# ── Phase 6.3: exact configured keys and immutable helper authority ──────────


INVALID_KEYS = ["", "typo", "View", "view ", "v\u0456ew", None, 1, [], {}, b"view"]


def _key_error(perm, permissions):
    alternatives = ", ".join(repr(key) for key in sorted(permissions))
    return f"Invalid permission key {perm!r}. Valid keys: {alternatives}."


@pytest.mark.django_db
@pytest.mark.parametrize("helper", ["assign_perm", "remove_perm", "get_objects_for_user"])
@pytest.mark.parametrize("perm", INVALID_KEYS)
@pytest.mark.parametrize(("active", "superuser"), [(True, False), (True, True), (False, False), (False, True)])
def test_invalid_helper_keys_validate_before_guardian_or_permission_writes(
    pol, publishers, monkeypatch, helper, perm, active, superuser
):
    from unittest.mock import Mock

    import guardian.shortcuts
    from django.contrib.auth.models import Group
    from guardian.models import GroupObjectPermission, UserObjectPermission

    obj, _ = publishers
    user = _user("invalid_key", active=active, superuser=superuser)
    group = Group.objects.create(name="existing_grant")
    pol.pub_vs.assign_perm("view", user, obj)
    pol.pub_vs.assign_perm("view", group, obj)
    before = (list(UserObjectPermission.objects.values()), list(GroupObjectPermission.objects.values()))
    shortcut = Mock(wraps=getattr(guardian.shortcuts, helper))
    monkeypatch.setattr(guardian.shortcuts, helper, shortcut)
    # A valid inactive query may call none(); an invalid key must never even touch the supplied queryset.
    scope = Mock()
    scope.none.side_effect = AssertionError("queryset accessed before key validation")

    with pytest.raises(ValueError) as error:
        if helper == "get_objects_for_user":
            pol.pub_vs.get_objects_for_user(user, perm, qs=scope)
        else:
            getattr(pol.pub_vs, helper)(perm, user, obj)

    assert str(error.value) == _key_error(perm, pol.pub_vs.permissions)
    shortcut.assert_not_called()
    assert (list(UserObjectPermission.objects.values()), list(GroupObjectPermission.objects.values())) == before


@pytest.mark.django_db
def test_invalid_query_key_precedes_default_queryset_access(pol, monkeypatch):
    from unittest.mock import Mock

    user = _user("invalid_default_scope", active=False)
    all_rows = Mock(side_effect=AssertionError("default queryset accessed before key validation"))
    monkeypatch.setattr(pol.pub_vs.model.objects, "all", all_rows)
    with pytest.raises(ValueError) as error:
        pol.pub_vs.get_objects_for_user(user, "typo")
    assert str(error.value) == _key_error("typo", pol.pub_vs.permissions)
    all_rows.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("invalid", ["", "view", "Réviser", "réviser ", "re\u0301viser", "rév\u0456ser", None, [], {}])
@pytest.mark.parametrize("helper", ["assign_perm", "remove_perm", "get_objects_for_user"])
def test_diagnostics_list_sorted_actual_configured_keys(pol, publishers, helper, invalid):
    from collections import OrderedDict

    obj, _ = publishers
    user = _user("custom_diagnostic")
    original = pol.pub_vs.permissions
    pol.pub_vs._default_permissions = OrderedDict(
        [("zebra", original["delete"]), ("réviser", original["view"]), ("alpha", original["change"])]
    )
    with pytest.raises(ValueError) as error:
        if helper == "get_objects_for_user":
            pol.pub_vs.get_objects_for_user(user, invalid)
        else:
            getattr(pol.pub_vs, helper)(invalid, user, obj)
    assert str(error.value) == _key_error(invalid, pol.pub_vs.permissions)


@pytest.mark.django_db
def test_custom_unicode_key_round_trip_preserves_permission_and_queryset_types(pol, publishers, monkeypatch):
    from collections import OrderedDict
    from unittest.mock import Mock

    import guardian.shortcuts
    from django.db.models import QuerySet

    from tests.test1.app.models import Publisher

    obj, other = publishers
    user = _user("unicode_key")
    permission = pol.pub_vs.permissions["view"]
    pol.pub_vs._default_permissions = OrderedDict([("réviser", permission)])
    spies = {name: Mock(wraps=getattr(guardian.shortcuts, name)) for name in ("assign_perm", "remove_perm")}
    for name, spy in spies.items():
        monkeypatch.setattr(guardian.shortcuts, name, spy)
    pol.pub_vs.assign_perm("réviser", user, obj)
    scope = Publisher.objects.filter(pk__in=[obj.pk, other.pk]).order_by("pk")
    result = pol.pub_vs.get_objects_for_user(user, "réviser", qs=scope)
    assert isinstance(result, QuerySet)
    assert result.model is Publisher and result.db == scope.db
    assert list(result) == [obj]
    assert type(result[0].pk) is type(obj.pk)
    assert not pol.pub_vs.get_objects_for_user(user, "réviser", qs=scope.none()).exists()
    pol.pub_vs.remove_perm("réviser", user, obj)
    assert not pol.pub_vs.get_objects_for_user(user, "réviser").exists()
    assert spies["assign_perm"].call_args.args[0] is permission
    assert spies["remove_perm"].call_args.args[0] is permission


def test_strict_helper_policy_rejects_mapping_mutation():
    from crud_views_guardian.lib.viewset import STRICT_HELPER_POLICY

    try:
        with pytest.raises(TypeError):
            STRICT_HELPER_POLICY["accept_global_perms"] = True
    finally:
        if isinstance(STRICT_HELPER_POLICY, dict):
            STRICT_HELPER_POLICY["accept_global_perms"] = False


@pytest.mark.django_db
def test_policy_mutation_cannot_turn_global_permission_into_helper_authority(pol, publishers):
    from contextlib import suppress

    from crud_views_guardian.lib.viewset import STRICT_HELPER_POLICY

    user = _grant_global(_user("mutable_policy"), "view_publisher")
    try:
        with suppress(TypeError):
            STRICT_HELPER_POLICY["accept_global_perms"] = True
        result = _pks(pol.pub_vs.get_objects_for_user(user, "view"))
    finally:
        if isinstance(STRICT_HELPER_POLICY, dict):
            STRICT_HELPER_POLICY["accept_global_perms"] = False
    assert result == []


@pytest.mark.django_db
def test_manage_policy_copies_are_detached_across_requests_and_from_helper(pol, client, publishers):
    user = _grant_global(_user("copy_manager"), "view_publisher")
    client.force_login(user)
    first = _manage(client, pol.pub_vs)
    second = _manage(client, pol.pub_vs)
    first.context["guardian_config"]["get_objects_for_user"]["accept_global_perms"] = True
    first.context["views"]["list"]["guardian_policy"]["cv_guardian_accept_global_perms"] = True

    assert second.context["guardian_config"]["get_objects_for_user"] == STRICT_HELPER
    assert _views_policy(second)["list"] == _policy(applicable=True, accept=False)
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == []
    third = _manage(client, pol.pub_vs)
    assert third.context["guardian_config"]["get_objects_for_user"] == STRICT_HELPER
    assert _views_policy(third)["list"] == _policy(applicable=True, accept=False)


@pytest.mark.django_db
def test_inherited_global_flag_and_explicit_sibling_override_remain_independent(pol, client, publishers, monkeypatch):
    from crud_views_guardian.lib.mixins import GuardianQuerysetMixin

    obj, other = publishers
    user = _grant_global(_user("inherited_policy"), "view_publisher")
    client.force_login(user)
    assert "cv_guardian_accept_global_perms" not in pol.PublisherList.__dict__
    monkeypatch.setattr(GuardianQuerysetMixin, "cv_guardian_accept_global_perms", True)
    monkeypatch.setattr(pol.PublisherDetail, "cv_guardian_accept_global_perms", False)

    assert _pks(client.get(_url(pol.pub_vs, "list")).context["object_list"]) == sorted([obj.pk, other.pk])
    assert client.get(_url(pol.pub_vs, "detail", pk=obj.pk)).status_code == 403
    assert _pks(pol.pub_vs.get_objects_for_user(user, "view")) == []
    policies = _views_policy(_manage(client, pol.pub_vs))
    assert policies["list"] == _policy(applicable=True, accept=True)
    assert policies["detail"] == _policy(applicable=True, accept=False)


@pytest.mark.django_db
def test_strict_helper_preserves_uuid_queryset_identities(author_douglas_adams, author_terry_pratchett):
    from django.db.models import QuerySet

    from tests.test1.app.models import Author
    from tests.test1.app.views import cv_guardian_author

    user = _user("uuid_precision")
    cv_guardian_author.assign_perm("view", user, author_douglas_adams)
    scope = Author.objects.filter(pk__in=[author_douglas_adams.pk, author_terry_pratchett.pk])
    result = cv_guardian_author.get_objects_for_user(user, "view", qs=scope)
    assert isinstance(result, QuerySet) and result.model is Author and result.db == scope.db
    assert list(result) == [author_douglas_adams]
    assert isinstance(result[0].pk, uuid.UUID)
    assert result[0].pk == author_douglas_adams.pk
    assert not cv_guardian_author.get_objects_for_user(user, "view", qs=scope.none()).exists()


@pytest.mark.django_db
def test_registered_proxy_viewset_uses_concrete_permission_without_key_or_pk_coercion(unique_name, publishers):
    from guardian.shortcuts import assign_perm

    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import PublisherProxy

    obj, _ = publishers
    user = _user("proxy_policy")
    viewset = GuardianViewSet(model=PublisherProxy, name=unique_name)

    class ProxyListView(GuardianListViewPermissionRequired):
        cv_viewset = viewset

    assign_perm("view_publisher", user, obj)
    assert viewset.permissions["view"] == "app.view_publisher"
    result = viewset.get_objects_for_user(user, "view")
    assert result.model is PublisherProxy
    assert _pks(result) == [obj.pk]
    assert isinstance(result[0], PublisherProxy)
    view = ProxyListView()
    view.request = SimpleNamespace(user=user)
    view.kwargs = {}
    assert _pks(view.get_queryset()) == [obj.pk]


@pytest.mark.django_db
@pytest.mark.parametrize("path_kind", ["helper", "list"])
def test_registered_polymorphic_base_content_type_policy_residual(unique_name, monkeypatch, path_kind):
    """Reproduce the unresolved AUTH-06 concern; this is evidence of an error, not an access-policy pass."""
    from guardian.conf import settings as guardian_settings
    from guardian.exceptions import MixedContentTypeError
    from guardian.shortcuts import assign_perm

    from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Car

    monkeypatch.setattr(
        guardian_settings, "GET_CONTENT_TYPE", "polymorphic.contrib.guardian.get_polymorphic_base_content_type"
    )
    car = Car.objects.create(name="Residual content type", doors=4)
    user = _user("polymorphic_policy")
    viewset = GuardianViewSet(model=Car, name=unique_name)

    class CarListView(GuardianListViewPermissionRequired):
        cv_viewset = viewset

    assign_perm("view_vehicle", user, car)
    assert viewset.permissions["view"] == "app.view_car"
    view = CarListView()
    view.request = SimpleNamespace(user=user)
    view.kwargs = {}
    with pytest.raises(MixedContentTypeError, match="Content type for given perms and klass differs"):
        if path_kind == "helper":
            viewset.get_objects_for_user(user, "view")
        else:
            view.get_queryset()
