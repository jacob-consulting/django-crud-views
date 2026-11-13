import pytest
from django.test.client import Client

from crud_views.lib.viewset import ViewSet


@pytest.mark.django_db
def test_manage_production_request_and_action_require_membership(client, user_author_view, cv_author, settings):
    from django.contrib.auth.models import Group

    from crud_views.lib.settings import crud_views_settings

    settings.DEBUG = False
    client.force_login(user_author_view)
    denied = client.get("/author/manage/")
    assert denied.status_code == 403
    assert b"permission_holders" not in denied.content
    assert b"/author/manage/" not in client.get("/author/").content

    group = Group.objects.create(name=crud_views_settings.manage_group)
    user_author_view.groups.add(group)
    admitted = client.get("/author/manage/")
    assert admitted.status_code == 200
    assert "permission_holders" in admitted.context
    assert b"/author/manage/" in client.get("/author/").content

    user_author_view.groups.remove(group)
    assert client.get("/author/manage/").status_code == 403
    assert b"/author/manage/" not in client.get("/author/").content


def test_manage_unset_setting_defaults_to_yes_on_first_import():
    import os
    import subprocess
    import sys
    from pathlib import Path

    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    code = """
from django.conf import settings
settings.configure(SECRET_KEY="isolated-manage-default")
assert not hasattr(settings, "CRUD_VIEWS_MANAGE_VIEWS_ENABLED")
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
assert CrudViewsSettings.model_fields["manage_views_enabled"].default == "yes"
assert crud_views_settings.manage_views_enabled == "yes"
"""
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.django_db
@pytest.mark.parametrize("evaluations", [1, 3])
def test_manage_membership_query_per_evaluation(cv_author, user_author_view, django_assert_num_queries, evaluations):
    from django.contrib.auth.models import Group

    from crud_views.lib.settings import crud_views_settings

    user_author_view.groups.add(Group.objects.create(name=crud_views_settings.manage_group))
    manage = cv_author.get_view_class("manage")
    with django_assert_num_queries(evaluations) as captured:
        for _ in range(evaluations):
            assert manage.cv_has_access(user_author_view)
    assert all("auth_user_groups" in query["sql"] for query in captured.captured_queries)


@pytest.mark.django_db
@pytest.mark.parametrize("actor,mode,debug", [("anonymous", "yes", True), ("inactive", "yes", True),
                                             ("active", "no", True), ("active", "debug_only", False)])
def test_manage_short_circuits_without_membership_query(
    cv_author, user_author_view, monkeypatch, settings, django_assert_num_queries, actor, mode, debug
):
    from django.contrib.auth.models import AnonymousUser

    from crud_views.lib.settings import crud_views_settings

    settings.DEBUG = debug
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
    user = AnonymousUser() if actor == "anonymous" else user_author_view
    if actor == "inactive":
        user.is_active = False
    with django_assert_num_queries(0):
        assert not cv_author.get_view_class("manage").cv_has_access(user)


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
    from django.contrib.auth.models import Group, User

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


@pytest.mark.django_db
def test_register_uses_custom_manage_view_class():
    """ViewSet.register() wires up the class specified by manage_view_class."""
    import uuid

    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
    from tests.test1.app.models import Author
    from tests.test1.app.views import CustomManageViewForTest

    name = f"test_custom_{uuid.uuid4().hex[:8]}"
    try:
        vs = ViewSet(
            model=Author,
            name=name,
            manage_view_class="tests.test1.app.views.CustomManageViewForTest",
        )
        manage_class = vs.get_all_views()["manage"]
        assert issubclass(manage_class, CustomManageViewForTest)
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)


@pytest.mark.django_db
def test_manage_view_headings_translated(client_user_author_view: Client, cv_author):
    """Headings and column headers follow the active language; attribute names (pk, app, ...) stay as-is."""
    from django.utils import translation
    from lxml import html

    with translation.override("de"):
        response = client_user_author_view.get("/author/manage/")
    doc = html.fromstring(response.content)
    headings = [h.text_content().strip() for h in doc.cssselect("h3, h4")]
    assert {"Eigenschaften", "Berechtigungen", "Berechtigungsinhaber", "Views"} <= set(headings)
    columns = [th.text_content().strip() for th in doc.cssselect("th")]
    assert {"Berechtigung", "Django-Berechtigung", "Zugriff"} <= set(columns)
    assert "pk_name" in columns
