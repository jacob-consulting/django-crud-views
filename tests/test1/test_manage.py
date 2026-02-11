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
