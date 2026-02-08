import pytest

from crud_views.lib.viewset import ViewSet


@pytest.mark.django_db
def test_viewset_has_views(cv_author: ViewSet):
    expected_views = ["list", "detail", "create", "update", "delete"]
    for view_name in expected_views:
        assert cv_author.has_view(view_name), f"ViewSet missing view: {view_name}"


@pytest.mark.django_db
def test_viewset_url_patterns(cv_author: ViewSet):
    patterns = cv_author.urlpatterns
    assert len(patterns) >= 5


@pytest.mark.django_db
def test_viewset_permissions_mapping(cv_author: ViewSet):
    permissions = cv_author.permissions
    assert "add" in permissions
    assert "change" in permissions
    assert "delete" in permissions
    assert "view" in permissions

    for key, value in permissions.items():
        assert "." in value, f"Permission {key} should be in 'app.codename' format, got {value}"


@pytest.mark.django_db
def test_viewset_get_router_name(cv_author: ViewSet):
    assert cv_author.get_router_name("list") == "author-list"
    assert cv_author.get_router_name("detail") == "author-detail"
    assert cv_author.get_router_name("create") == "author-create"
    assert cv_author.get_router_name("update") == "author-update"
    assert cv_author.get_router_name("delete") == "author-delete"
