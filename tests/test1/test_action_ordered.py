import pytest
from django.test.client import Client

from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Author


@pytest.mark.django_db
def test_ordered_views_registered(cv_author: ViewSet):
    """Up and down action views should be registered on the Author viewset."""
    assert cv_author.has_view("up"), "ViewSet missing view: up"
    assert cv_author.has_view("down"), "ViewSet missing view: down"


@pytest.mark.django_db
def test_ordered_url_patterns(cv_author: ViewSet):
    """URL patterns should include up and down routes."""
    patterns = cv_author.urlpatterns
    routes = [p.name for p in patterns]
    assert "author-up" in routes
    assert "author-down" in routes


@pytest.mark.django_db
def test_move_up(client_user_author_change: Client, cv_author):
    """Moving the second author up should swap positions."""
    a1 = Author.objects.create(first_name="First", last_name="Author")
    a2 = Author.objects.create(first_name="Second", last_name="Author")

    # a1 order=0, a2 order=1
    assert a1.order < a2.order

    # POST to move a2 up
    response = client_user_author_change.post(f"/author/{a2.pk}/up/")
    assert response.status_code == 302

    a1.refresh_from_db()
    a2.refresh_from_db()
    assert a2.order < a1.order


@pytest.mark.django_db
def test_move_up_first_item_noop(client_user_author_change: Client, cv_author):
    """Moving the first item up should be a no-op (already at top)."""
    a1 = Author.objects.create(first_name="First", last_name="Author")
    Author.objects.create(first_name="Second", last_name="Author")

    original_order = a1.order

    response = client_user_author_change.post(f"/author/{a1.pk}/up/")
    assert response.status_code == 302

    a1.refresh_from_db()
    assert a1.order == original_order


@pytest.mark.django_db
def test_move_down(client_user_author_change: Client, cv_author):
    """Moving the first author down should swap positions."""
    a1 = Author.objects.create(first_name="First", last_name="Author")
    a2 = Author.objects.create(first_name="Second", last_name="Author")

    assert a1.order < a2.order

    # POST to move a1 down
    response = client_user_author_change.post(f"/author/{a1.pk}/down/")
    assert response.status_code == 302

    a1.refresh_from_db()
    a2.refresh_from_db()
    assert a1.order > a2.order


@pytest.mark.django_db
def test_move_down_last_item_noop(client_user_author_change: Client, cv_author):
    """Moving the last item down should be a no-op (already at bottom)."""
    Author.objects.create(first_name="First", last_name="Author")
    a2 = Author.objects.create(first_name="Second", last_name="Author")

    original_order = a2.order

    response = client_user_author_change.post(f"/author/{a2.pk}/down/")
    assert response.status_code == 302

    a2.refresh_from_db()
    assert a2.order == original_order


@pytest.mark.django_db
def test_ordered_redirects_to_list(client_user_author_change: Client, cv_author):
    """After up/down, user should be redirected to the list view."""
    a1 = Author.objects.create(first_name="First", last_name="Author")

    response = client_user_author_change.post(f"/author/{a1.pk}/up/")
    assert response.status_code == 302
    assert response.url == "/author/"


@pytest.mark.django_db
def test_ordered_requires_permission(client: Client, cv_author, user_a):
    """User without change permission should get 403."""
    client.force_login(user_a)
    a1 = Author.objects.create(first_name="First", last_name="Author")

    response = client.post(f"/author/{a1.pk}/up/")
    assert response.status_code == 403

    response = client.post(f"/author/{a1.pk}/down/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_ordered_anonymous_redirected(client: Client, cv_author):
    """Anonymous user should be redirected to login."""
    a1 = Author.objects.create(first_name="First", last_name="Author")

    response = client.post(f"/author/{a1.pk}/up/")
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_ordered_get_not_allowed(client_user_author_change: Client, cv_author):
    """GET should not be allowed on action views (POST only)."""
    a1 = Author.objects.create(first_name="First", last_name="Author")

    response = client_user_author_change.get(f"/author/{a1.pk}/up/")
    assert response.status_code == 405
