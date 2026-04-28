import pytest
from django.test.client import Client

from crud_views.lib.viewset import ViewSet


@pytest.mark.django_db
def test_manage_view_auto_registered(cv_author: ViewSet):
    """Manage view should be auto-registered when CRUD_VIEWS_MANAGE_VIEWS_ENABLED=yes."""
    assert cv_author.has_view("manage")


@pytest.mark.django_db
def test_manage_url_pattern(cv_author: ViewSet):
    """Manage URL should be in the viewset's urlpatterns."""
    routes = [p.name for p in cv_author.urlpatterns]
    assert "author-manage" in routes


@pytest.mark.django_db
def test_manage_view_accessible(client_user_author_view: Client, cv_author):
    """Manage view should be accessible (has_permission always returns True)."""
    response = client_user_author_view.get("/author/manage/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_manage_view_shows_viewset_info(client_user_author_view: Client, cv_author):
    """Manage view should display viewset name and config."""
    response = client_user_author_view.get("/author/manage/")
    content = response.content.decode("utf-8")

    assert "author" in content
    assert "ViewSet" in content


@pytest.mark.django_db
def test_manage_view_shows_permissions(client_user_author_view: Client, cv_author):
    """Manage view should list the viewset's permissions."""
    response = client_user_author_view.get("/author/manage/")
    content = response.content.decode("utf-8")

    assert "add" in content
    assert "change" in content
    assert "delete" in content
    assert "view" in content


@pytest.mark.django_db
def test_manage_view_shows_registered_views(client_user_author_view: Client, cv_author):
    """Manage view should list all registered views for the viewset."""
    response = client_user_author_view.get("/author/manage/")
    content = response.content.decode("utf-8")

    for key in cv_author.get_all_views():
        assert key in content


@pytest.mark.django_db
def test_manage_context_has_cv(client_user_author_view: Client, cv_author):
    """Template context should contain the viewset as 'cv'."""
    response = client_user_author_view.get("/author/manage/")
    assert response.context["cv"] is cv_author


@pytest.mark.django_db
def test_manage_context_has_permission_rows(client_user_author_view: Client, cv_author):
    """Template context 'data' should contain permission rows with access info."""
    response = client_user_author_view.get("/author/manage/")
    data = response.context["data"]

    assert len(data) >= 4
    keys = [row["viewset"] for row in data]
    assert "add" in keys
    assert "view" in keys

    # user_author_view has view permission, so that row should show True
    view_row = next(r for r in data if r["viewset"] == "view")
    assert view_row["has_permission"] is True

    # user_author_view does NOT have add permission
    add_row = next(r for r in data if r["viewset"] == "add")
    assert add_row["has_permission"] is False


@pytest.mark.django_db
def test_manage_context_has_view_data(client_user_author_view: Client, cv_author):
    """Template context 'views' should contain view metadata dicts."""
    response = client_user_author_view.get("/author/manage/")
    views = response.context["views"]

    assert "list" in views
    assert "detail" in views
    assert "create" in views

    # Each view entry should have base, templates, icons sections
    list_view = views["list"]
    assert "base" in list_view
    assert "templates" in list_view
    assert "icons" in list_view
    assert list_view["base"]["cv_key"] == "list"


@pytest.mark.django_db
def test_manage_registered_on_all_viewsets(cv_author, cv_publisher, cv_book):
    """Manage view should be auto-registered on all viewsets in debug mode."""
    assert cv_author.has_view("manage")
    assert cv_publisher.has_view("manage")
    assert cv_book.has_view("manage")


# ── Group-based access and permission holders ──────────────────────────────────


@pytest.mark.django_db
def test_manage_accessible_via_crud_views_manage_group(client, cv_author, monkeypatch):
    """User in CRUD_VIEWS_MANAGE group can access manage view even when setting is 'no'."""
    from django.contrib.auth.models import User, Group
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")

    group = Group.objects.create(name="CRUD_VIEWS_MANAGE")
    user = User.objects.create_user(username="manage_user", password="password")
    user.groups.add(group)
    client.force_login(user)

    response = client.get("/author/manage/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_manage_blocked_without_group_or_setting(client, cv_author, monkeypatch):
    """Authenticated user without CRUD_VIEWS_MANAGE group gets 403 when setting is 'no'."""
    from django.contrib.auth.models import User
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")

    user = User.objects.create_user(username="plain_user", password="password")
    client.force_login(user)

    response = client.get("/author/manage/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_manage_anonymous_user_redirected(client, cv_author, monkeypatch):
    """Anonymous user gets a redirect (not 500) when manage_views_enabled is 'no'."""
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")
    response = client.get("/author/manage/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_manage_context_has_permission_holders(client_user_author_view, cv_author):
    """Manage view context includes permission_holders list."""
    response = client_user_author_view.get("/author/manage/")
    assert "permission_holders" in response.context
    assert isinstance(response.context["permission_holders"], list)


@pytest.mark.django_db
def test_manage_permission_holders_shows_groups(client_user_author_view, cv_author):
    """Groups with model-level permissions appear in permission_holders."""
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from tests.test1.app.models import Author

    ct = ContentType.objects.get_for_model(Author)
    perm = Permission.objects.get(content_type=ct, codename="view_author")
    group = Group.objects.create(name="viewers")
    group.permissions.add(perm)

    response = client_user_author_view.get("/author/manage/")
    holders = response.context["permission_holders"]

    viewer_rows = [r for r in holders if r["group"] == "viewers" and r["permission"] == "view"]
    assert len(viewer_rows) == 1
    assert viewer_rows[0]["has_model_perm"] is True


def test_settings_manage_view_class_default():
    """manage_view_class setting should default to None."""
    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.manage_view_class is None


def test_settings_guardian_manage_view_class_default():
    """guardian_manage_view_class setting should default to None."""
    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.guardian_manage_view_class is None


def test_get_manage_view_class_default(cv_author):
    """Default: get_manage_view_class() returns ManageView."""
    from crud_views.lib.views.manage import ManageView

    assert cv_author.get_manage_view_class() is ManageView


def test_get_manage_view_class_global_setting(cv_author, monkeypatch):
    """Global setting: get_manage_view_class() returns the class named by the setting."""
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_view_class", "tests.test1.app.views.CustomManageViewForTest")
    from tests.test1.app.views import CustomManageViewForTest

    assert cv_author.get_manage_view_class() is CustomManageViewForTest


def test_get_manage_view_class_per_viewset_field(cv_author, monkeypatch):
    """Per-viewset field: get_manage_view_class() returns the class named by the field."""
    monkeypatch.setattr(cv_author, "manage_view_class", "tests.test1.app.views.CustomManageViewForTest")
    from tests.test1.app.views import CustomManageViewForTest

    assert cv_author.get_manage_view_class() is CustomManageViewForTest


def test_get_manage_view_class_field_wins_over_setting(cv_author, monkeypatch):
    """Priority: per-viewset field beats global setting."""
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.views.manage import ManageView

    monkeypatch.setattr(crud_views_settings, "manage_view_class", "crud_views.lib.views.manage.ManageView")
    monkeypatch.setattr(cv_author, "manage_view_class", "tests.test1.app.views.CustomManageViewForTest")
    from tests.test1.app.views import CustomManageViewForTest

    result = cv_author.get_manage_view_class()
    assert result is CustomManageViewForTest
    assert result is not ManageView
