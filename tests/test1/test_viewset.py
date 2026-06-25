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


@pytest.mark.django_db
def test_default_permissions_parses_action_containing_model_name():
    """Custom permission whose codename contains the model name parses to the full action.

    Regression (#33): default_permissions split the codename on the first "_<model>"
    occurrence, truncating any action that contains "_<model>" before its end. For model
    "book", a custom permission "change_book_status" was truncated to "change" -- colliding
    with the standard "change" permission. Stripping "_<model>" only as a suffix keeps the
    custom action intact ("change_book_status") and leaves the standard key untouched.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from crud_views.lib.viewset import ViewSet, _REGISTRY
    from tests.test1.app.models import Book

    ct = ContentType.objects.get_for_model(Book)  # ct.model == "book"
    Permission.objects.create(content_type=ct, codename="change_book_status", name="Can change book status")

    name = "book_perm_parsing_probe"
    try:
        viewset = ViewSet(model=Book, name=name)
        permissions = viewset.default_permissions
    finally:
        _REGISTRY.pop(name, None)  # keep the global registry clean for other tests

    # custom action keeps its full name instead of being truncated to "change"
    assert "change_book_status" in permissions
    assert permissions["change_book_status"] == f"{ct.app_label}.change_book_status"
    # the standard "change" permission is not clobbered by the truncated custom one
    assert permissions["change"] == f"{ct.app_label}.change_book"
    # standard actions still parse
    for action in ("add", "change", "delete", "view"):
        assert action in permissions
