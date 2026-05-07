import pytest
from django.test.client import Client

from tests.lib.helper.guardian import user_guardian_object_perm


# ── Object-level enforcement: detail/update/delete ──────────────────────────


@pytest.mark.django_db
def test_object_perm_granted_detail(client_guardian, user_guardian, cv_guardian_author, author_douglas_adams):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_object_perm_denied_detail(client_guardian, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_object_perm_granted_update(client_guardian, user_guardian, cv_guardian_author, author_douglas_adams):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "change", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/update/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_object_perm_denied_update(client_guardian, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/update/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_object_perm_granted_delete(client_guardian, user_guardian, cv_guardian_author, author_douglas_adams):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "delete", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/delete/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_object_perm_denied_delete(client_guardian, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/delete/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_model_level_perm_only_is_denied_in_strict_mode(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams
):
    """User with model-level view_author but no per-object grant is denied (strict mode)."""
    from tests.lib.helper.user import user_viewset_permission

    user_viewset_permission(user_guardian, cv_guardian_author, "view")
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 403


# ── List queryset filtering ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_list_shows_only_permitted_objects(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, author_b
):
    """User sees only authors they have per-object view permission on."""
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    response = client_guardian.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" in response.content.decode()
    assert "Pratchett" not in response.content.decode()


@pytest.mark.django_db
def test_list_empty_when_no_object_perms(client_guardian, author_douglas_adams, author_b):
    """User with no per-object grants sees empty list."""
    response = client_guardian.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" not in response.content.decode()
    assert "Pratchett" not in response.content.decode()


@pytest.mark.django_db
def test_list_respects_group_permissions(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, author_b
):
    """User in a group with per-object perm sees the object."""
    from django.contrib.auth.models import Group
    from guardian.shortcuts import assign_perm

    group = Group.objects.create(name="editors")
    user_guardian.groups.add(group)
    assign_perm(cv_guardian_author.permissions["view"], group, author_douglas_adams)
    response = client_guardian.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" in response.content.decode()
    assert "Pratchett" not in response.content.decode()


# ── Create views ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_top_level_create_requires_model_level_add_perm(client_guardian, user_guardian, cv_guardian_author):
    """Top-level create uses model-level add permission (no object exists yet)."""
    from tests.lib.helper.user import user_viewset_permission

    user_viewset_permission(user_guardian, cv_guardian_author, "add")
    response = client_guardian.get("/guardian_author/create/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_level_create_denied_without_model_level_perm(client_guardian):
    """Top-level create is denied when user has no add permission."""
    response = client_guardian.get("/guardian_author/create/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_child_create_requires_parent_change_perm(client_guardian, user_guardian, cv_guardian_publisher, publisher_a):
    """Child create requires cv_guardian_parent_create_permission ('change') on parent."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher/{pk}/guardian_book/create/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_child_create_denied_with_only_view_perm_on_parent(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    """Child create is denied when user only has 'view' on parent (needs 'change')."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher/{pk}/guardian_book/create/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_child_create_denied_without_parent_perm(client_guardian, publisher_a):
    """Child create is denied when user has no permission on parent."""
    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher/{pk}/guardian_book/create/")
    assert response.status_code == 403


# ── Parent permission (child list/detail/update/delete) ──────────────────────


@pytest.mark.django_db
def test_child_list_requires_parent_view_perm(client_guardian, user_guardian, cv_guardian_publisher, publisher_a):
    """Child list requires cv_guardian_parent_permission ('view') on parent."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher/{pk}/guardian_book/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_child_list_denied_without_parent_perm(client_guardian, publisher_a):
    """Child list is denied when user has no view permission on parent."""
    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher/{pk}/guardian_book/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_child_detail_denied_without_parent_view_perm(
    client_guardian, user_guardian, cv_guardian_book, publisher_a, book_under_publisher_a
):
    """Child detail denied even with per-object book perm if parent perm missing."""
    user_guardian_object_perm(user_guardian, cv_guardian_book, "view", book_under_publisher_a)
    pub_pk = publisher_a.pk
    book_pk = book_under_publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher/{pub_pk}/guardian_book/{book_pk}/detail/")
    assert response.status_code == 403


# ── cv_has_access ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cv_has_access_with_grant(user_guardian, cv_guardian_author, author_douglas_adams):
    from tests.test1.app.views import GuardianAuthorDetailView

    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    assert GuardianAuthorDetailView.cv_has_access(user_guardian, author_douglas_adams) is True


@pytest.mark.django_db
def test_cv_has_access_without_grant(user_guardian, author_douglas_adams):
    from tests.test1.app.views import GuardianAuthorDetailView

    assert GuardianAuthorDetailView.cv_has_access(user_guardian, author_douglas_adams) is False


@pytest.mark.django_db
def test_cv_has_access_no_object_returns_false(user_guardian):
    from tests.test1.app.views import GuardianAuthorDetailView

    assert GuardianAuthorDetailView.cv_has_access(user_guardian) is False


# ── accept_global_perms = True ───────────────────────────────────────────────


@pytest.mark.django_db
def test_accept_global_perms_allows_model_level_on_detail(client, cv_guardian_author, author_douglas_adams):
    """With accept_global_perms=True, model-level perm grants object access."""
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import GuardianAuthorDetailView

    user = User.objects.create_user(username="global_perm_user", password="password")
    user_viewset_permission(user, cv_guardian_author, "view")
    # Refresh from DB to clear Django's permission cache after granting permissions
    user = User.objects.get(pk=user.pk)

    original = GuardianAuthorDetailView.cv_guardian_accept_global_perms
    GuardianAuthorDetailView.cv_guardian_accept_global_perms = True
    client.force_login(user)
    try:
        pk = author_douglas_adams.pk
        response = client.get(f"/guardian_author/{pk}/detail/")
        assert response.status_code == 200
    finally:
        GuardianAuthorDetailView.cv_guardian_accept_global_perms = original


# ── cv_has_access for list views ──────────────────────────────────────────────


@pytest.mark.django_db
def test_list_cv_has_access_no_object_returns_true(user_guardian):
    """List cv_has_access returns True when no object — list is always accessible."""
    from tests.test1.app.views import GuardianAuthorListView

    assert GuardianAuthorListView.cv_has_access(user_guardian) is True


@pytest.mark.django_db
def test_list_cv_has_access_with_object_returns_true(user_guardian, author_douglas_adams):
    """List cv_has_access returns True even with a non-None obj — buttons always visible."""
    from tests.test1.app.views import GuardianAuthorListView

    assert GuardianAuthorListView.cv_has_access(user_guardian, author_douglas_adams) is True


@pytest.mark.django_db
def test_non_guardian_cv_has_access_with_model_perm(author_douglas_adams):
    """Non-guardian cv_has_access returns True when user has model-level perm (base.py revert check)."""
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import AuthorDetailView, cv_author

    user = User.objects.create_user(username="model_perm_user", password="password")
    user_viewset_permission(user, cv_author, "view")
    user = User.objects.get(pk=user.pk)

    assert AuthorDetailView.cv_has_access(user, author_douglas_adams) is True


# ── cv_has_access for create views ────────────────────────────────────────────


@pytest.mark.django_db
def test_create_cv_has_access_top_level_with_add_perm(user_guardian, cv_guardian_author):
    """Top-level create: True when user has model-level add perm."""
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import GuardianAuthorCreateView

    user_viewset_permission(user_guardian, cv_guardian_author, "add")
    user_guardian = User.objects.get(pk=user_guardian.pk)
    assert GuardianAuthorCreateView.cv_has_access(user_guardian) is True


@pytest.mark.django_db
def test_create_cv_has_access_top_level_without_add_perm(user_guardian):
    """Top-level create: False when user has no model-level add perm."""
    from tests.test1.app.views import GuardianAuthorCreateView

    assert GuardianAuthorCreateView.cv_has_access(user_guardian) is False


@pytest.mark.django_db
def test_create_cv_has_access_child_no_object_with_parent_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """Child create, obj=None: False regardless of parent perm — parent obj is not available so access cannot be confirmed."""
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    # Permission state does not matter here: this branch returns False unconditionally.
    # The rendering list view (GuardianQuerysetMixin.cv_get_context) handles the real check.
    assert GuardianBookCreateView.cv_has_access(user_guardian, None) is False


@pytest.mark.django_db
def test_create_cv_has_access_child_no_object_without_parent_perm(user_guardian):
    """Child create, obj=None: False — no parent obj, cannot determine access."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_has_access(user_guardian, None) is False


@pytest.mark.django_db
def test_create_cv_has_access_child_with_parent_obj_and_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """Child create, obj=parent instance: True when user has change perm on that parent."""
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    assert GuardianBookCreateView.cv_has_access(user_guardian, publisher_a) is True


@pytest.mark.django_db
def test_create_cv_has_access_child_with_parent_obj_without_perm(user_guardian, publisher_a):
    """Child create, obj=parent instance: False when user has no change perm on that parent."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_has_access(user_guardian, publisher_a) is False


@pytest.mark.django_db
def test_create_cv_has_access_child_wrong_type_obj(user_guardian, book_under_publisher_a):
    """Child create, obj=wrong model type: True (fallback — cannot determine access)."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_has_access(user_guardian, book_under_publisher_a) is True


# ── cv_create_has_access ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cv_create_has_access_returns_false_when_parent_obj_is_none(user_guardian):
    """Default cv_create_has_access returns False when parent_obj is None."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_create_has_access(user_guardian, None, None) is False


@pytest.mark.django_db
def test_cv_create_has_access_returns_true_with_parent_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """Default cv_create_has_access returns True when user has required guardian perm on parent."""
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    assert GuardianBookCreateView.cv_create_has_access(user_guardian, None, publisher_a) is True


@pytest.mark.django_db
def test_cv_create_has_access_returns_false_without_parent_perm(user_guardian, publisher_a):
    """Default cv_create_has_access returns False when user lacks required guardian perm on parent."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_create_has_access(user_guardian, None, publisher_a) is False


# ── GuardianQuerysetMixin.cv_get_context create button ────────────────────────


def _make_book_list_view(user_guardian, publisher_a):
    """Instantiate GuardianBookListView with request and URL kwargs for publisher_a."""
    from unittest.mock import MagicMock
    from django.test import RequestFactory
    from tests.test1.app.views import GuardianBookListView, cv_guardian_book

    rf = RequestFactory()
    request = rf.get(f"/guardian_publisher/{publisher_a.pk}/guardian_book/")
    request.user = user_guardian
    # cv_get_context uses resolver_match.url_name for cv_is_active; provide a stub
    resolver_match = MagicMock()
    resolver_match.url_name = cv_guardian_book.get_router_name("list")
    request.resolver_match = resolver_match

    view = GuardianBookListView()
    view.request = request
    view.args = []
    view.kwargs = {"guardian_publisher_pk": str(publisher_a.pk)}
    return view


@pytest.mark.django_db
def test_cv_get_context_create_with_parent_perm_shows_button(user_guardian, cv_guardian_publisher, publisher_a):
    """cv_get_context resolves parent and grants access when user has change perm on parent."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    view = _make_book_list_view(user_guardian, publisher_a)
    ctx = view.cv_get_context(key="create", obj=None, user=user_guardian)
    assert ctx["cv_access"] is True


@pytest.mark.django_db
def test_cv_get_context_create_without_parent_perm_hides_button(user_guardian, publisher_a):
    """cv_get_context resolves parent and denies access when user lacks change perm on parent."""
    view = _make_book_list_view(user_guardian, publisher_a)
    ctx = view.cv_get_context(key="create", obj=None, user=user_guardian)
    assert ctx["cv_access"] is False


@pytest.mark.django_db
def test_cv_get_context_non_create_key_not_affected(user_guardian, cv_guardian_publisher, publisher_a):
    """cv_get_context override does not interfere with non-create keys (obj=None case)."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    view = _make_book_list_view(user_guardian, publisher_a)
    # "list" is a context action with obj=None — override must not fire for non-create keys
    ctx = view.cv_get_context(key="list", obj=None, user=user_guardian)
    # cv_access is determined by normal cv_has_access, not our override
    # GuardianListView has list access for this user so result should be True
    assert ctx["cv_access"] is True


@pytest.mark.django_db
def test_cv_get_context_respects_cv_create_has_access_override(user_guardian, publisher_a):
    """An override of cv_create_has_access on the create view class is called by cv_get_context."""
    from tests.test1.app.views import GuardianBookCreateView

    original = GuardianBookCreateView.cv_create_has_access

    @classmethod
    def always_true(cls, user, rendering_view, parent_obj):
        return True

    GuardianBookCreateView.cv_create_has_access = always_true
    try:
        view = _make_book_list_view(user_guardian, publisher_a)
        # user has no perm on publisher_a, but override returns True
        ctx = view.cv_get_context(key="create", obj=None, user=user_guardian)
        assert ctx["cv_access"] is True
    finally:
        GuardianBookCreateView.cv_create_has_access = original


# ── GuardianManageView ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_guardian_manage_view_registered(cv_guardian_author):
    """GuardianManageView should be auto-registered on guardian viewsets."""
    from crud_views_guardian.lib.views import GuardianManageView

    assert cv_guardian_author.has_view("manage")
    assert issubclass(cv_guardian_author.get_all_views()["manage"], GuardianManageView)


@pytest.mark.django_db
def test_guardian_manage_context_has_guardian_config(client_guardian, cv_guardian_author):
    """GuardianManageView context includes guardian_config dict."""
    response = client_guardian.get("/guardian_author/manage/")
    assert response.status_code == 200
    assert "guardian_config" in response.context
    config = response.context["guardian_config"]
    assert "cv_guardian_parent_permission" in config
    assert "cv_guardian_parent_create_permission" in config
    assert "cv_guardian_accept_global_perms" in config
    assert config["cv_guardian_accept_global_perms"] is False
    assert "parent_viewset" in config
    # cv_guardian_author has no parent, so parent_viewset should be None
    assert config["parent_viewset"] is None


@pytest.mark.django_db
def test_guardian_manage_permission_holders_has_object_count(client_guardian, cv_guardian_author):
    """Permission holders includes guardian object count after assigning per-object group perm."""
    from django.contrib.auth.models import Group
    from guardian.shortcuts import assign_perm
    from tests.test1.app.models import Author

    group = Group.objects.create(name="editors")
    author = Author.objects.create(first_name="Test", last_name="Author")
    assign_perm("app.change_author", group, author)

    response = client_guardian.get("/guardian_author/manage/")
    holders = response.context["permission_holders"]

    editor_rows = [r for r in holders if r["group"] == "editors" and r["permission"] == "change"]
    assert len(editor_rows) == 1
    assert editor_rows[0]["object_count"] == 1
    assert editor_rows[0]["has_model_perm"] is False


@pytest.mark.django_db
def test_guardian_manage_views_have_mixin_info(client_guardian, cv_guardian_author):
    """Each view in context includes guardian_mixin info derived from MRO."""
    response = client_guardian.get("/guardian_author/manage/")
    views = response.context["views"]
    assert "list" in views
    assert "guardian_mixin" in views["list"]["base"]
    assert "QuerysetMixin" in views["list"]["base"]["guardian_mixin"]
    assert "guardian_mixin" in views["detail"]["base"]
    assert "ObjectPermissionMixin" in views["detail"]["base"]["guardian_mixin"]


# ── Anonymous user behavior ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_guardian_anonymous_list_redirects(client, cv_guardian_author):
    """Anonymous user on list view gets redirect to login (not 500)."""
    response = client.get("/guardian_author/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_guardian_anonymous_detail_redirects(client, cv_guardian_author, author_douglas_adams):
    """Anonymous user on detail view gets redirect to login (not 500)."""
    pk = author_douglas_adams.pk
    response = client.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_guardian_anonymous_child_list_redirects(client, cv_guardian_publisher, publisher_a):
    """Anonymous user on child list view gets redirect to login (not 500)."""
    pk = publisher_a.pk
    response = client.get(f"/guardian_publisher/{pk}/guardian_book/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_guardian_anonymous_behavior_404(client, cv_guardian_author, monkeypatch):
    """cv_guardian_anonymous_behavior='404' returns 404 for anonymous users."""
    from crud_views_guardian.lib.mixins import GuardianQuerysetMixin

    monkeypatch.setattr(GuardianQuerysetMixin, "cv_guardian_anonymous_behavior", "404")
    response = client.get("/guardian_author/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_guardian_anonymous_create_redirects(client, cv_guardian_author):
    """Anonymous user on top-level create view gets redirect to login (not 500)."""
    response = client.get("/guardian_author/create/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_guardian_anonymous_behavior_403(client, cv_guardian_publisher, publisher_a, monkeypatch):
    """cv_guardian_anonymous_behavior='403' returns 403 for anonymous users on child list (dispatch path)."""
    from tests.test1.app.views import GuardianBookListView

    monkeypatch.setattr(GuardianBookListView, "cv_guardian_anonymous_behavior", "403")
    pk = publisher_a.pk
    response = client.get(f"/guardian_publisher/{pk}/guardian_book/")
    assert response.status_code == 403


# ── manage_view_class customization ───────────────────────────────────────────


def test_guardian_get_manage_view_class_default(cv_guardian_author):
    """Default: GuardianViewSet.get_manage_view_class() returns GuardianManageView."""
    from crud_views_guardian.lib.views import GuardianManageView

    assert cv_guardian_author.get_manage_view_class() is GuardianManageView


def test_guardian_get_manage_view_class_global_setting(cv_guardian_author, monkeypatch):
    """Global guardian setting: get_manage_view_class() returns the named class."""
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(
        crud_views_settings, "guardian_manage_view_class", "tests.test1.app.views.CustomGuardianManageViewForTest"
    )
    from tests.test1.app.views import CustomGuardianManageViewForTest

    assert cv_guardian_author.get_manage_view_class() is CustomGuardianManageViewForTest


def test_guardian_get_manage_view_class_per_viewset_field(cv_guardian_author, monkeypatch):
    """Per-viewset field on GuardianViewSet: get_manage_view_class() returns the named class."""
    monkeypatch.setattr(
        cv_guardian_author, "manage_view_class", "tests.test1.app.views.CustomGuardianManageViewForTest"
    )
    from tests.test1.app.views import CustomGuardianManageViewForTest

    assert cv_guardian_author.get_manage_view_class() is CustomGuardianManageViewForTest


def test_guardian_get_manage_view_class_field_wins_over_setting(cv_guardian_author, monkeypatch):
    """Priority: per-viewset field beats guardian global setting."""
    from crud_views.lib.settings import crud_views_settings
    from crud_views_guardian.lib.views import GuardianManageView

    monkeypatch.setattr(
        crud_views_settings, "guardian_manage_view_class", "crud_views_guardian.lib.views.GuardianManageView"
    )
    monkeypatch.setattr(
        cv_guardian_author, "manage_view_class", "tests.test1.app.views.CustomGuardianManageViewForTest"
    )
    from tests.test1.app.views import CustomGuardianManageViewForTest

    result = cv_guardian_author.get_manage_view_class()
    assert result is CustomGuardianManageViewForTest
    assert result is not GuardianManageView


@pytest.mark.django_db
def test_guardian_register_uses_custom_manage_view_class():
    """GuardianViewSet.register() wires up the class specified by manage_view_class."""
    import uuid
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Author
    from tests.test1.app.views import CustomGuardianManageViewForTest

    name = f"test_gv_custom_{uuid.uuid4().hex[:8]}"
    try:
        vs = GuardianViewSet(
            model=Author,
            name=name,
            manage_view_class="tests.test1.app.views.CustomGuardianManageViewForTest",
        )
        manage_class = vs.get_all_views()["manage"]
        assert issubclass(manage_class, CustomGuardianManageViewForTest)
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)
