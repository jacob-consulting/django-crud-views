import pytest


@pytest.mark.django_db
def test_related_objects_not_shown_by_default(client_user_publisher_delete, cv_publisher, publisher_penguin):
    """Default DeleteView does not include related_objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_delete.get(f"/publisher/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" not in response.context


@pytest.mark.django_db
def test_related_objects_shown_when_enabled(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """DeleteView with cv_show_related_objects=True includes related objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Book.objects.create(title="Book B", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" in response.context
    assert "related_summary" in response.context
    summary = response.context["related_summary"]
    assert summary["book"] == 2


@pytest.mark.django_db
def test_related_objects_rendered_in_template(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """Related objects are rendered in the delete page HTML."""
    from django.contrib.auth.models import Permission

    from tests.test1.app.models import Book

    Book.objects.create(title="Hitchhiker's Guide", publisher=publisher_penguin)

    # Grant view permissions so objects are visible in the tree
    user = client_user_publisher_cascade_delete.session
    from django.contrib.auth.models import User

    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user_obj.user_permissions.add(perm)

    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    content = response.content.decode()
    assert "Hitchhiker" in content
    assert "book" in content.lower()


@pytest.mark.django_db
def test_delete_protection_view_hook(client_user_publisher_protected_delete, cv_publisher_protected, publisher_penguin):
    """cv_check_delete_protection returning errors prevents deletion."""
    pk = publisher_penguin.pk
    response = client_user_publisher_protected_delete.post(f"/publisher_protected/{pk}/delete/", {"confirm": True})
    assert response.status_code == 200
    from tests.test1.app.models import Publisher

    assert Publisher.objects.filter(pk=pk).exists()
    assert "Cannot delete" in response.content.decode()
