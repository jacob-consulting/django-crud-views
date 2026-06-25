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
    """Custom permission whose codename embeds the model name parses to the full action.

    Regression (#33): default_permissions split the codename on the first "_<model>"
    occurrence, so an action that itself contains the model name (e.g. "rebook_book" for
    model "book") was truncated to "re". It now strips "_<model>" as a suffix -> "rebook".
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from crud_views.lib.viewset import ViewSet, _REGISTRY
    from tests.test1.app.models import Book

    ct = ContentType.objects.get_for_model(Book)  # ct.model == "book"
    Permission.objects.create(content_type=ct, codename="rebook_book", name="Can rebook book")

    name = "book_perm_parsing_probe"
    viewset = ViewSet(model=Book, name=name)
    try:
        permissions = viewset.default_permissions
    finally:
        _REGISTRY.pop(name, None)  # keep the global registry clean for other tests

    assert "rebook" in permissions  # full action, not the truncated "re"
    assert "re" not in permissions
    assert permissions["rebook"] == f"{ct.app_label}.rebook_book"
    for action in ("add", "change", "delete", "view"):
        assert action in permissions  # standard actions still parse
