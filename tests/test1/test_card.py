import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from django.http import QueryDict
from django.test import override_settings
from django.test.client import Client
from django.urls import reverse
from django.utils import translation
from lxml import html

from crud_views.lib.view import CardAction
from crud_views.lib.view.cancel import navigation_params
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Author
from tests.test1.test_cancel_navigation import checked_action_url, emitted_link, rendered_cancel


@pytest.fixture
def cards_first_recipe():
    reference = Path(__file__).resolve().parents[2] / "docs/reference/card-list-view.md"
    matches = re.findall(r"<!-- card-recipe: cards-first -->\n```python\n(.*?)\n```", reference.read_text(), re.S)
    assert len(matches) == 1, "Publish exactly one complete cards-first recipe"
    return compile(matches[0], str(reference), "exec")


@pytest.fixture
def cv_author_cards_first(request, cards_first_recipe):
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK
    from tests.test1.app.urls import urlpatterns

    snapshot = dict(_REGISTRY)

    def restore_cards_first_registry():
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(snapshot)

    request.addfinalizer(restore_cards_first_registry)
    namespace = {"__package__": "tests.test1.app", "__name__": "tests.test1.app.cards_first_recipe"}
    exec(cards_first_recipe, namespace)
    CardsFirstURLs = type("CardsFirstURLs", (), {"urlpatterns": [*namespace["urlpatterns"], *urlpatterns]})
    with override_settings(ROOT_URLCONF=CardsFirstURLs):
        yield namespace["cv_author_cards_first"]


@pytest.fixture
def client_user_author_cards_first_all(client, cv_author_cards_first):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_cards_first_all", password="password")
    for permission in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author_cards_first, permission)
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_cards_first_urls_and_switching(
    client_user_author_cards_first_all, cv_author_cards_first, author_douglas_adams, author_terry_pratchett
):
    vs = cv_author_cards_first
    client = client_user_author_cards_first_all
    cards_url, table_url = (reverse(vs.get_router_name(key)) for key in ("list", "table"))
    assert cards_url == "/authors_cards_first/"
    assert table_url == "/authors_cards_first/table/"
    assert vs.get_view_class("list").cv_key == "list"
    assert vs.get_view_class("list").cv_path == ""
    assert vs.get_view_class("table").cv_key == "table"
    assert vs.get_view_class("table").cv_path == "table"
    assert vs.get_view_class("table").cv_home_key == "list"

    with translation.override("en"):
        cards = client.get(cards_url)
        assert cards.status_code == 200
        cards_doc = html.fromstring(cards.content)
        assert len(cards_doc.cssselect(".card.mb-3")) == 2
        assert not cards_doc.cssselect("table")
        switch = emitted_link(cards, table_url)
        (table_button,) = cards_doc.xpath("//a[@href=$url]", url=switch)
        assert table_button.text_content().strip() == "Table"
        assert table_button.cssselect("i.fa-regular.fa-rectangle-list")
        assert not table_button.cssselect(".visually-hidden")

        table = client.get(switch)
        assert table.status_code == 200
        table_doc = html.fromstring(table.content)
        assert not table_doc.cssselect(".card.mb-3")
        rows = table_doc.cssselect("table tbody tr")
        assert len(rows) == 2
        for author in (author_douglas_adams, author_terry_pratchett):
            assert str(author) in cards_doc.text_content()
            assert author.first_name in table_doc.text_content()
            assert author.last_name in table_doc.text_content()
        cards_buttons = [
            anchor for anchor in table_doc.cssselect("a.btn[href]") if anchor.cssselect("i.fa-solid.fa-rectangle-list")
        ]
        assert cards_buttons
        assert all(urlsplit(button.get("href")).path == cards_url for button in cards_buttons)
        cards_button = cards_buttons[-1]
        assert cards_button.text_content().strip() == "Cards"
        assert urlsplit(cards_button.get("href")).path == cards_url
        assert cards_button.cssselect("i.fa-solid.fa-rectangle-list")
        assert not cards_button.cssselect(".visually-hidden")
        returned = client.get(cards_button.get("href"))
        assert returned.status_code == 200
        assert len(html.fromstring(returned.content).cssselect(".card.mb-3")) == 2


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["table", "detail", "create", "update"])
@pytest.mark.parametrize("cancel_keys", ["documented", None, []])
def test_cards_first_navigation_targets(
    client_user_author_cards_first_all, cv_author_cards_first, author_douglas_adams, monkeypatch, key, cancel_keys
):
    vs, client = cv_author_cards_first, client_user_author_cards_first_all
    cards_url = reverse(vs.get_router_name("list"))
    cls = vs.get_view_class(key)
    if cancel_keys != "documented" and key in {"create", "update"}:
        monkeypatch.setattr(cls, "cv_cancel_keys", cancel_keys)
    path = reverse(vs.get_router_name(key), kwargs={"pk": author_douglas_adams.pk} if cls.cv_object else {})
    response = client.get(path)
    assert response.status_code == 200
    document = html.fromstring(response.content)
    home = document.xpath("//a[@cv-key='list']")
    assert home and all(node.get("href") == cards_url for node in home)
    breadcrumbs = document.cssselect("nav[aria-label='breadcrumb']")
    assert breadcrumbs
    assert breadcrumbs[0].xpath(".//a[@href=$url]", url=cards_url)
    (current,) = breadcrumbs[0].xpath(".//*[@aria-current='page']")
    assert not current.xpath(".//a")
    if key == "table":
        assert current.text_content().strip() == "Table"
    if key in {"create", "update"}:
        assert rendered_cancel(response) == cards_url
        assert client.get(rendered_cancel(response)).status_code == 200
        before = Author.objects.count()
        assert cls.cv_success_keys is None
        saved = client.post(path, {"first_name": "Octavia", "last_name": "Butler", "pseudonym": "OEB"})
        assert saved.status_code == 302
        assert saved["Location"] == cards_url
        obj = Author.objects.get(first_name="Octavia")
        assert (obj.last_name, obj.pseudonym) == ("Butler", "OEB")
        assert Author.objects.count() == before + (key == "create")
        if key == "update":
            assert obj.pk == author_douglas_adams.pk


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["create", "update"])
@pytest.mark.parametrize("allowed", [False, True])
@pytest.mark.parametrize("query", ["", "sort=last_name&page=1&x=one&x=&x=two"])
def test_cards_first_cancel_origin_and_success(
    client_user_author_cards_first_all, cv_author_cards_first, author_douglas_adams, monkeypatch, key, allowed, query
):
    vs, client = cv_author_cards_first, client_user_author_cards_first_all
    target = vs.get_view_class(key)
    if not allowed:
        monkeypatch.setattr(target, "cv_cancel_keys", "auto")
    cards_url = reverse(vs.get_router_name("list"))
    table_url = reverse(vs.get_router_name("table"))
    form_url = reverse(vs.get_router_name(key), kwargs={"pk": author_douglas_adams.pk} if key == "update" else {})
    source = client.get(table_url + ("?" + query if query else ""))
    assert source.status_code == 200
    link = emitted_link(source, form_url)
    assert checked_action_url(link, source.context["view"]) == form_url
    assert bool(urlsplit(link).query) is allowed
    before = list(Author.objects.order_by("pk").values())
    form = client.get(link)
    assert form.status_code == 200
    cancel = rendered_cancel(form)
    assert urlsplit(cancel).path == (table_url if allowed else cards_url)
    # A later visit cannot change the earlier form's signed capture, including an empty capture.
    later = client.get(table_url + "?sort=-first_name&page=1&x=later")
    assert later.status_code == 200
    assert rendered_cancel(client.get(link)) == cancel
    returned = client.get(cancel)
    assert returned.status_code == 200
    expected = QueryDict(query if allowed else "")
    assert expected == returned.wsgi_request.GET
    assert returned.wsgi_request.META["QUERY_STRING"] == expected.urlencode()
    assert not set(navigation_params()) & returned.wsgi_request.GET.keys()
    if allowed:
        repeated = emitted_link(returned, form_url)
        assert checked_action_url(repeated, returned.context["view"]) == form_url
        assert repeated == link, "Restoration must not accumulate transport in another capture"
    assert list(Author.objects.order_by("pk").values()) == before

    # Save has its own policy: it persists data and returns to cards even with a table origin.
    assert target.cv_success_keys is None
    saved = client.post(link, {"first_name": "Ursula", "last_name": "Le Guin", "pseudonym": "UKL"})
    assert saved.status_code == 302
    assert saved["Location"] == cards_url
    if key == "update":
        author_douglas_adams.refresh_from_db()
        obj = author_douglas_adams
        assert Author.objects.count() == len(before)
    else:
        obj = Author.objects.get(first_name="Ursula")
        assert Author.objects.count() == len(before) + 1
    assert (obj.first_name, obj.last_name, obj.pseudonym) == ("Ursula", "Le Guin", "UKL")
    assert client.get(saved["Location"]).status_code == 200


@pytest.mark.django_db
def test_cards_first_permissions(
    client_user_author_cards_first_all, user_a, cv_author_cards_first, author_douglas_adams, monkeypatch
):
    vs, client = cv_author_cards_first, client_user_author_cards_first_all
    cards_url = reverse(vs.get_router_name("list"))
    table_url = reverse(vs.get_router_name("table"))
    update_url = reverse(vs.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})
    before = list(Author.objects.order_by("pk").values())
    denied_client = Client()
    denied_client.force_login(user_a)
    assert denied_client.get(cards_url).status_code == 403
    assert denied_client.get(table_url).status_code == 403
    source = client.get(table_url + "?sort=last_name&x=")
    captured = emitted_link(source, update_url)
    assert checked_action_url(captured, source.context["view"]) == update_url
    monkeypatch.setattr(vs.get_view_class("table"), "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    cards = client.get(cards_url)
    assert cards.status_code == 200
    document = html.fromstring(cards.content)
    assert not document.xpath("//a[@href=$url]", url=table_url)
    assert client.get(table_url).status_code == 403
    form = client.get(captured)
    assert form.status_code == 200
    assert rendered_cancel(form) == cards_url
    monkeypatch.setattr(vs.get_view_class("list"), "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    assert client.get(cards_url).status_code == 403
    direct = client.get(update_url)
    assert direct.status_code == 200
    assert not html.fromstring(direct.content).xpath("//*[@data-cv-cancel-url] | //*[@id='button-id-reset']")
    assert list(Author.objects.order_by("pk").values()) == before


@pytest.mark.django_db
@pytest.mark.parametrize("source_key,target_key", [("list", "table"), ("table", "list")])
def test_cards_first_switching_keeps_query_state_separate(
    client_user_author_cards_first_all, cv_author_cards_first, author_douglas_adams, source_key, target_key
):
    vs, client = cv_author_cards_first, client_user_author_cards_first_all
    source_url = reverse(vs.get_router_name(source_key))
    target_url = reverse(vs.get_router_name(target_key))
    assert client.get(target_url + "?x=previous").status_code == 200
    source = client.get(source_url + "?sort=last_name&page=1&x=one&x=&x=two")
    assert source.status_code == 200
    switch = emitted_link(source, target_url)
    assert switch == target_url
    returned = client.get(switch)
    assert returned.status_code == 200
    # These unfiltered recipe views do not enable the filter mixin's session persistence.
    assert QueryDict("") == returned.wsgi_request.GET
    assert not returned.wsgi_request.META["QUERY_STRING"]
    assert list(returned.context["object_list"]) == [author_douglas_adams]


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
@override_settings(LANGUAGES=[("en", "English"), ("de", "German")])
def test_card_list_empty_german(client_user_author_view: Client, cv_author):
    # the test project has no LocaleMiddleware: activate German around the request (as test_i18n.py does)
    with translation.override("de"):
        response = client_user_author_view.get("/author/card/")
    content = response.content.decode()
    assert '<p class="text-muted">Keine Einträge gefunden.</p>' in content
    assert "No items found." not in content


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
def test_card_child_action_hidden_without_child_permission(cv_publisher, cv_book, publisher_penguin):
    """Child actions check the child view's permission (#149): no book permission -> no Books button."""
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
    assert len(actions) == 1
    assert "Books" not in card.text_content()
