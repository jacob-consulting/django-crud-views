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
