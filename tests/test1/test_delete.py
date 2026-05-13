import pytest
from django.test.client import Client

from tests.lib.helper.user import user_viewset_permission


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


@pytest.mark.django_db
def test_permission_filtering_hides_restricted_objects(cv_publisher_cascade, publisher_penguin):
    """User without view permission on Book sees counts, not individual objects."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Book

    Book.objects.create(title="Secret Book A", publisher=publisher_penguin)
    Book.objects.create(title="Secret Book B", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_no_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Secret Book A" not in content
    assert "Secret Book B" not in content
    assert "book" in content.lower()  # summary still shows model name


@pytest.mark.django_db
def test_permission_filtering_shows_permitted_objects(cv_publisher_cascade, publisher_penguin):
    """User with view permission on Book sees individual object details."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book

    Book.objects.create(title="Visible Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_with_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")
    perm = Permission.objects.get(codename="view_book")
    user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Visible Book" in content


@pytest.mark.django_db
def test_protected_objects_shown_as_warning(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """Protected objects (on_delete=PROTECT) are shown as a warning."""
    from tests.test1.app.models import Contract

    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    context = response.context
    assert len(context["protected_objects"]) > 0
    content = response.content.decode()
    assert "blocked" in content.lower() or "protected" in content.lower()


@pytest.mark.django_db
def test_delete_protection_form_clean(publisher_penguin):
    """Form clean() raising ValidationError prevents deletion."""
    from django.contrib.auth.models import User

    from tests.test1.app.models import Publisher
    from tests.test1.app.views import cv_publisher_form_protected

    user = User.objects.create_user(username="user_form_clean_test", password="password")
    user_viewset_permission(user, cv_publisher_form_protected, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.post(f"/publisher_form_protected/{pk}/delete/", {"confirm": True})
    assert response.status_code == 200
    assert Publisher.objects.filter(pk=pk).exists()
    assert "Form-level" in response.content.decode()


@pytest.mark.django_db
def test_successful_cascade_delete(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    """With cv_show_related_objects=True, POST still deletes object and cascaded relations."""
    from tests.test1.app.models import Book, Publisher

    book = Book.objects.create(title="Doomed Book", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.post(f"/publisher_cascade/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert not Publisher.objects.filter(pk=pk).exists()
    assert not Book.objects.filter(pk=book.pk).exists()


@pytest.mark.django_db
def test_related_objects_linking(publisher_penguin):
    """With cv_link_related_objects=True, related objects with ViewSets are rendered as links."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_publisher_linked

    Book.objects.create(title="Linked Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_link_test", password="password")
    user_viewset_permission(user, cv_publisher_linked, "delete")
    # Grant view permissions so related objects are visible
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_linked/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    # Related book should be rendered as a clickable link
    import re

    assert re.search(r"<a\s[^>]*>Linked Book</a>", content)


@pytest.mark.django_db
def test_related_objects_linking_context_has_dict_tree(publisher_penguin):
    """With cv_link_related_objects=True, context['related_objects'] is a list of dicts with url keys."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book
    from tests.test1.app.views import cv_publisher_linked

    Book.objects.create(title="Context Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_link_ctx_test", password="password")
    user_viewset_permission(user, cv_publisher_linked, "delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_linked/{pk}/delete/")
    assert response.status_code == 200

    related_objects = response.context["related_objects"]
    assert isinstance(related_objects, list)
    assert len(related_objects) > 0
    # Each node should be a dict with obj, url, children keys
    node = related_objects[0]
    assert "obj" in node
    assert "url" in node
    assert "children" in node


@pytest.mark.django_db
def test_related_objects_no_linking_when_disabled(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """With cv_link_related_objects=False (default), related objects are NOT rendered as links."""
    from django.contrib.auth.models import Permission, User

    from tests.test1.app.models import Book

    Book.objects.create(title="Unlinked Book", publisher=publisher_penguin)

    # Grant view permissions so objects are visible in the tree
    user_obj = User.objects.get(username="user_publisher_cascade_delete")
    for codename in ("view_publisher", "view_book"):
        perm = Permission.objects.get(codename=codename)
        user_obj.user_permissions.add(perm)

    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Unlinked Book" in content
    # The related object text should NOT appear inside an <a> tag
    import re

    assert not re.search(r"<a\s[^>]*>Unlinked Book</a>", content)
