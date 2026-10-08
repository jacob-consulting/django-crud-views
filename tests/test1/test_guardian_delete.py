import pytest

from tests.lib.helper.guardian import user_guardian_object_perm


@pytest.mark.django_db
def test_guardian_per_object_filtering(client_guardian, user_guardian, cv_guardian_publisher, publisher_a):
    """Guardian delete view filters related objects by per-object view permission."""
    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_guardian_book, cv_guardian_publisher_cascade

    book_visible = Book.objects.create(title="Visible Book", publisher=publisher_a)
    Book.objects.create(title="Hidden Book", publisher=publisher_a)

    # Grant per-object delete on publisher (needed to access the delete page)
    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    # Grant per-object view on only one book
    user_guardian_object_perm(user_guardian, cv_guardian_book, "view", book_visible)

    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Visible Book" in content
    assert "Hidden Book" not in content


@pytest.mark.django_db
def test_guardian_delete_still_works(client_guardian, user_guardian, cv_guardian_publisher, publisher_a):
    """Guardian delete with cv_show_related_objects=True still deletes successfully."""
    from tests.test1.app.models import Publisher
    from tests.test1.app.views import cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    pk = publisher_a.pk
    response = client_guardian.post(f"/guardian_publisher_cascade/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert not Publisher.objects.filter(pk=pk).exists()


# ── cv_filter_related_objects, called directly ────────────────────────────────


@pytest.mark.django_db
def test_filter_related_objects_empty_tree_is_returned_unchanged(user_guardian):
    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin

    related = RelatedObjects(tree=[], summary={}, protected=[])
    assert GuardianDeleteRelatedObjectsMixin().cv_filter_related_objects(user_guardian, related) is related


@pytest.mark.django_db
def test_filter_related_objects_hides_unpermitted_and_keeps_structure(
    user_guardian, cv_guardian_publisher, publisher_a, publisher_b
):
    """Permitted objects stay, unpermitted ones become None, non-model entries
    (e.g. the string labels Django's collector emits) and nesting are preserved."""
    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    related = RelatedObjects(
        tree=[publisher_a, ["label", publisher_b, [publisher_a]], None],
        summary={"x": 1},
        protected=["p"],
    )

    result = GuardianDeleteRelatedObjectsMixin().cv_filter_related_objects(user_guardian, related)

    assert result.tree == [publisher_a, ["label", None, [publisher_a]], None]
    assert result.summary == {"x": 1}
    assert result.protected == ["p"]
