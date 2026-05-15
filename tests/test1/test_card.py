import pytest
from django.test.client import Client
from lxml import html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission


def test_card_action_requires_key_or_child_name():
    """CardAction must have either key or child_name set."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CardAction()

    with pytest.raises(ValidationError):
        CardAction(key="", child_name=None)


def test_card_action_key_only():
    action = CardAction(key="detail", label="Details")
    assert action.key == "detail"
    assert action.child_name is None
    assert action.child_key == "list"


def test_card_action_child_only():
    action = CardAction(child_name="book", child_key="card", label="Books")
    assert action.key == ""
    assert action.child_name == "book"
    assert action.child_key == "card"


def test_card_action_both_key_and_child():
    """Having both key and child_name is allowed — child_name takes priority in tag."""
    action = CardAction(key="detail", child_name="book", label="Books")
    assert action.key == "detail"
    assert action.child_name == "book"


@pytest.mark.django_db
def test_card_list_empty(client_user_author_view: Client, cv_author):
    response = client_user_author_view.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    # Object cards have class "card mb-3"; the page wrapper card has only "card"
    cards = doc.cssselect(".card.mb-3")
    assert len(cards) == 0
    assert "No items found." in response.content.decode()


@pytest.mark.django_db
def test_card_list_renders_objects(
    client_user_author_view: Client, cv_author, author_douglas_adams, author_terry_pratchett
):
    response = client_user_author_view.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    # Object cards have class "card mb-3"; the page wrapper card has only "card"
    cards = doc.cssselect(".card.mb-3")
    assert len(cards) == 2
    titles = [card.cssselect(".card-title")[0].text_content().strip() for card in cards]
    assert "Douglas Adams" in titles
    assert "Terry Pratchett" in titles


@pytest.fixture
def user_author_all_perms(cv_author):
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_author_all_perms", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    user_viewset_permission(user, cv_author, "delete")
    return user


@pytest.fixture
def client_user_author_all_perms(client, user_author_all_perms) -> Client:
    client.force_login(user_author_all_perms)
    return client


@pytest.mark.django_db
def test_card_actions_render(client_user_author_all_perms: Client, cv_author, author_douglas_adams):
    response = client_user_author_all_perms.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    # Object cards have class "card mb-3"; the page wrapper card has only "card"
    card = doc.cssselect(".card.mb-3")[0]
    actions = card.cssselect("a.btn")
    assert len(actions) == 3

    # "Details" button — primary, flex
    detail_btn = actions[0]
    assert "Details" in detail_btn.text_content()
    assert "btn-primary" in detail_btn.get("class")
    assert "flex-grow-1" in detail_btn.get("class")
    pk = author_douglas_adams.pk
    assert f"/author/{pk}/detail/" in detail_btn.get("href")

    # "Edit" button — secondary (default)
    edit_btn = actions[1]
    assert "Edit" in edit_btn.text_content()
    assert "btn-secondary" in edit_btn.get("class")

    # Delete button — icon-only, tertiary
    delete_btn = actions[2]
    assert "btn-outline-secondary" in delete_btn.get("class")
    assert delete_btn.get("title") is not None


@pytest.mark.django_db
def test_card_action_no_access(client_user_author_view: Client, cv_author, author_douglas_adams):
    """User with only view permission should not see update/delete action buttons."""
    response = client_user_author_view.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    # Object cards have class "card mb-3"; the page wrapper card has only "card"
    card = doc.cssselect(".card.mb-3")[0]
    actions = card.cssselect("a.btn")
    # user_author_view only has view permission, so update and delete buttons should not render
    hrefs = [a.get("href") for a in actions]
    pk = author_douglas_adams.pk
    assert any(f"/author/{pk}/detail/" in h for h in hrefs)
    assert not any("/update/" in h for h in hrefs)
    assert not any("/delete/" in h for h in hrefs)


@pytest.mark.django_db
def test_card_list_permission_denied(client_user_a: Client, cv_author):
    """User without view permission gets 403."""
    response = client_user_a.get("/author/card/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_card_container_class_default(client_user_author_view: Client, cv_author, author_douglas_adams):
    """Default card container uses col-md-6."""
    response = client_user_author_view.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    containers = doc.cssselect(".row > .col-md-6")
    assert len(containers) == 1


@pytest.fixture
def cv_author_wide_card():
    from tests.test1.app.views import cv_author_wide_card as ret

    return ret


@pytest.fixture
def user_author_wide_card_view(cv_author_wide_card):
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_wide_card", password="password")
    user_viewset_permission(user, cv_author_wide_card, "view")
    return user


@pytest.fixture
def client_user_author_wide_card(client, user_author_wide_card_view) -> Client:
    client.force_login(user_author_wide_card_view)
    return client


@pytest.mark.django_db
def test_card_container_class_custom(client_user_author_wide_card: Client, cv_author_wide_card, author_douglas_adams):
    """Custom cv_card_container_class renders in the template."""
    response = client_user_author_wide_card.get("/author_wide_card/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    containers = doc.cssselect(".row > .col-md-12")
    assert len(containers) == 1
    # Verify the default class is NOT present
    default_containers = doc.cssselect(".row > .col-md-6")
    assert len(default_containers) == 0


def test_get_view_class_fallback_list_to_card(cv_author_wide_card):
    """When 'list' is not registered but 'card' is, get_view_class('list') returns the card view."""
    view_class = cv_author_wide_card.get_view_class("list")
    assert view_class.cv_key == "card"


def test_get_view_class_no_fallback_when_list_exists(cv_author):
    """When 'list' is registered, get_view_class('list') returns the list view, not card."""
    view_class = cv_author.get_view_class("list")
    assert view_class.cv_key == "list"


def test_get_view_class_raises_when_neither_list_nor_card(cv_author):
    """When key is not registered and no fallback applies, raises ViewSetKeyFoundError."""
    from crud_views.lib.exceptions import ViewSetKeyFoundError

    with pytest.raises(ViewSetKeyFoundError):
        cv_author.get_view_class("nonexistent")


@pytest.fixture
def user_author_wide_card_add(cv_author_wide_card):
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_wide_card_add", password="password")
    user_viewset_permission(user, cv_author_wide_card, "view")
    user_viewset_permission(user, cv_author_wide_card, "add")
    return user


@pytest.fixture
def client_user_author_wide_card_add(client, user_author_wide_card_add) -> Client:
    client.force_login(user_author_wide_card_add)
    return client


@pytest.mark.django_db
def test_create_view_redirects_to_card_in_card_only_viewset(
    client_user_author_wide_card_add: Client, cv_author_wide_card
):
    """CreateView in a card-only ViewSet redirects to the card view after success."""
    response = client_user_author_wide_card_add.post(
        "/author_wide_card/create/",
        {"first_name": "Isaac", "last_name": "Asimov", "pseudonym": ""},
    )
    assert response.status_code == 302
    assert "/author_wide_card/card/" in response.url


@pytest.fixture
def user_publisher_card_view(cv_publisher, cv_book):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_pub_card", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    user_viewset_permission(user, cv_book, "view")
    return user


@pytest.fixture
def client_user_publisher_card(client, user_publisher_card_view) -> Client:
    client.force_login(user_publisher_card_view)
    return client


@pytest.mark.django_db
def test_card_child_action_renders_url(client_user_publisher_card: Client, cv_publisher, cv_book, publisher_penguin):
    """CardAction with child_name renders a link to the child viewset."""
    response = client_user_publisher_card.get("/publisher/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    actions = card.cssselect("a.btn")
    assert len(actions) == 2

    books_btn = actions[1]
    assert "Books" in books_btn.text_content()
    pk = publisher_penguin.pk
    assert f"/publisher/{pk}/book/" in books_btn.get("href")


@pytest.mark.django_db
def test_card_child_action_always_renders(cv_publisher, publisher_penguin):
    """Child actions render even without explicit child view permission."""
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_pub_no_book", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    client = Client()
    client.force_login(user)

    response = client.get("/publisher/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    actions = card.cssselect("a.btn")
    assert len(actions) == 2
    books_btn = actions[1]
    assert "Books" in books_btn.text_content()
