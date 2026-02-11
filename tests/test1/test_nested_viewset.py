import pytest
from django.test.client import Client

from crud_views.lib.viewset import ViewSet
from tests.lib.helper.boostrap5 import Table
from tests.test1.app.models import Book, Publisher


@pytest.mark.django_db
def test_child_viewset_has_parent(cv_book: ViewSet):
    assert cv_book.parent is not None
    assert cv_book.has_parent is True
    assert cv_book.parent.name == "publisher"


@pytest.mark.django_db
def test_child_viewset_url_patterns(cv_book: ViewSet):
    patterns = cv_book.urlpatterns
    assert len(patterns) >= 5

    # All routes should contain the parent prefix
    routes = [p.pattern.regex.pattern for p in patterns]
    for route in routes:
        assert "publisher/" in route, f"Expected 'publisher/' in route: {route}"
        assert r"\d+" in route, f"Expected INT pk regex in route: {route}"


@pytest.mark.django_db
def test_child_viewset_router_names(cv_book: ViewSet):
    assert cv_book.get_router_name("list") == "book-list"
    assert cv_book.get_router_name("detail") == "book-detail"
    assert cv_book.get_router_name("create") == "book-create"
    assert cv_book.get_router_name("update") == "book-update"
    assert cv_book.get_router_name("delete") == "book-delete"


@pytest.mark.django_db
def test_child_list_books(client_user_book_view: Client, cv_book, publisher_penguin, book_hitchhiker):
    url = f"/publisher/{publisher_penguin.pk}/book/"
    response = client_user_book_view.get(url)
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "Hitchhiker" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_child_list_filters_by_parent(
    client_user_book_view: Client, cv_book,
    publisher_penguin, publisher_harpercollins,
    book_hitchhiker, book_other_publisher
):
    # List books under Penguin — should only see Hitchhiker
    url = f"/publisher/{publisher_penguin.pk}/book/"
    response = client_user_book_view.get(url)
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "Hitchhiker" in table.rows[0].columns[1].text

    # List books under HarperCollins — should only see Other Book
    url = f"/publisher/{publisher_harpercollins.pk}/book/"
    response = client_user_book_view.get(url)
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "Other Book" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_child_create_book(client_user_book_add: Client, cv_book, publisher_penguin):
    url = f"/publisher/{publisher_penguin.pk}/book/create/"
    response = client_user_book_add.get(url)
    assert response.status_code == 200

    response = client_user_book_add.post(url, {"title": "1984"})
    assert response.status_code == 302

    book = Book.objects.get(title="1984")
    assert book.publisher == publisher_penguin


@pytest.mark.django_db
def test_child_update_book(client_user_book_change: Client, cv_book, publisher_penguin, book_hitchhiker):
    url = f"/publisher/{publisher_penguin.pk}/book/{book_hitchhiker.pk}/update/"
    response = client_user_book_change.get(url)
    assert response.status_code == 200

    response = client_user_book_change.post(url, {"title": "H2G2"})
    assert response.status_code == 302

    book_hitchhiker.refresh_from_db()
    assert book_hitchhiker.title == "H2G2"


@pytest.mark.django_db
def test_child_delete_book(client_user_book_delete: Client, cv_book, publisher_penguin, book_hitchhiker):
    pk = book_hitchhiker.pk
    url = f"/publisher/{publisher_penguin.pk}/book/{pk}/delete/"

    response = client_user_book_delete.get(url)
    assert response.status_code == 200

    response = client_user_book_delete.post(url, {"confirm": True})
    assert response.status_code == 302

    assert not Book.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_child_detail_book(client_user_book_view: Client, cv_book, publisher_penguin, book_hitchhiker):
    url = f"/publisher/{publisher_penguin.pk}/book/{book_hitchhiker.pk}/detail/"
    response = client_user_book_view.get(url)
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Hitchhiker" in content


@pytest.mark.django_db
def test_child_permissions_anonymous(client: Client, cv_book, publisher_penguin, book_hitchhiker):
    """Anonymous user should be redirected to login."""
    url = f"/publisher/{publisher_penguin.pk}/book/"
    response = client.get(url)
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_child_permissions_no_perm(client_user_a: Client, cv_book, publisher_penguin, book_hitchhiker):
    """Authenticated user without permissions should get 403."""
    url = f"/publisher/{publisher_penguin.pk}/book/"
    response = client_user_a.get(url)
    assert response.status_code == 403
