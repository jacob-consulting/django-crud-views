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
    """List cv_has_access returns True even with an object (e.g. parent-button wrong-type case)."""
    from tests.test1.app.views import GuardianAuthorListView

    assert GuardianAuthorListView.cv_has_access(user_guardian, author_douglas_adams) is True


@pytest.mark.django_db
def test_non_guardian_cv_has_access_with_model_perm(client, cv_guardian_author, author_douglas_adams):
    """Non-guardian cv_has_access returns True when user has model-level perm (base.py revert check)."""
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import AuthorDetailView

    user = User.objects.create_user(username="model_perm_user", password="password")
    user_viewset_permission(user, cv_guardian_author, "view")
    user = User.objects.get(pk=user.pk)

    pk = author_douglas_adams.pk
    assert AuthorDetailView.cv_has_access(user, author_douglas_adams) is True
