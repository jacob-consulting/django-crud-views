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

    from crud_views.lib.viewset import _REGISTRY, ViewSet
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


@pytest.mark.django_db
def test_permissions_not_cached_while_empty():
    """An empty permission lookup (rows not created yet) is not cached for the process (#151).

    A server started before ``migrate`` used to cache ``{}`` forever, so every PermissionRequired view of the
    ViewSet failed with "permission view not found" until restart, even after migrate created the rows.
    """
    from django.apps import apps
    from django.contrib.auth.management import create_permissions
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from crud_views.lib.viewset import _REGISTRY, ViewSet
    from tests.test1.app.models import Book

    ct = ContentType.objects.get_for_model(Book)
    Permission.objects.filter(content_type=ct).delete()  # the state before migrate
    name = "book_perm_cache_probe"
    try:
        viewset = ViewSet(model=Book, name=name)
        assert viewset.permissions == {}

        create_permissions(apps.get_app_config(Book._meta.app_label), verbosity=0)  # what migrate does

        assert viewset.permissions["view"] == f"{ct.app_label}.view_book"
    finally:
        _REGISTRY.pop(name, None)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name, extra_codenames, expected",
    [
        (
            "Publisher",
            [],
            [
                ("add", "app.add_publisher"),
                ("change", "app.change_publisher"),
                ("delete", "app.delete_publisher"),
                ("view", "app.view_publisher"),
            ],
        ),
        (
            "Book",
            ["change_book_status"],
            [
                ("add", "app.add_book"),
                ("change", "app.change_book"),
                ("change_book_status", "app.change_book_status"),
                ("delete", "app.delete_book"),
                ("view", "app.view_book"),
            ],
        ),
    ],
    ids=["publisher", "book-custom-permission"],
)
def test_default_permissions_cold_lookup_is_one_content_type_and_one_permission_query(
    django_assert_num_queries, model_name, extra_codenames, expected
):
    """A cold vocabulary lookup is one ContentType lookup plus one Permission query, with the exact mapping.

    Pins the lookup shape the ``default_permissions`` docstring promises and the exact ordered mapping. Regression
    test for the 06.18 cost finding (deferred item "Core ViewSet.default_permissions reads one ContentType per
    permission row"): the loop read the content type through each Permission row, so a four-permission model cost
    five ``django_content_type`` queries instead of one.
    """
    import re
    from collections import Counter

    from django.apps import apps
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from crud_views.lib.viewset import _REGISTRY, ViewSet

    table = re.compile(r'(?:FROM|INTO|UPDATE)\s+"(\w+)"')
    model = apps.get_model("app", model_name)
    ct = ContentType.objects.get_for_model(model)
    for codename in extra_codenames:
        Permission.objects.create(content_type=ct, codename=codename, name=codename.replace("_", " "))

    name = f"{model_name.lower()}_perm_query_shape_probe"
    try:
        viewset = ViewSet(model=model, name=name)
        viewset._default_permissions = None
        ContentType.objects.clear_cache()

        with CaptureQueriesContext(connection) as captured:
            result = viewset.default_permissions
        tables = Counter()
        for query in captured.captured_queries:
            match = table.search(query["sql"])
            tables[match.group(1) if match else "other"] += 1

        assert dict(tables) == {"django_content_type": 1, "auth_permission": 1}
        assert list(result.items()) == expected

        with django_assert_num_queries(0):
            assert viewset.default_permissions is result
    finally:
        _REGISTRY.pop(name, None)
