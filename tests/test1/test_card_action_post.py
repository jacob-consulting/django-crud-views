import pytest
from django.test.client import Client
from lxml import html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def user_author_view_change(cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view_change", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    user_viewset_permission(user, cv_author, "delete")
    return user


@pytest.fixture
def client_user_author_view_change(client, user_author_view_change) -> Client:
    client.force_login(user_author_view_change)
    return client


@pytest.mark.django_db
def test_card_post_action_renders_submit_form(
    client_user_author_view_change: Client, cv_author, author_douglas_adams, monkeypatch
):
    """A CardAction targeting a POST-only view renders a submit-form trigger + hidden POST form, not a GET link."""
    from tests.test1.app.views import AuthorCardListView

    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [CardAction(key="detail", label="Details"), CardAction(key="up", label="Up")],
    )

    response = client_user_author_view_change.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    pk = author_douglas_adams.pk

    # POST action -> submit-form trigger anchor (href="#", not the action URL)
    trigger = card.cssselect("a[data-cv-action='submit-form']")
    assert len(trigger) == 1
    target = trigger[0].get("data-cv-target")
    assert target.startswith("cv_form_")
    assert trigger[0].get("href") == "#"

    # POST action -> hidden form present, tied to the trigger by id, with the action URL and a CSRF token
    form = card.cssselect(f"form#{target}")
    assert len(form) == 1
    assert form[0].get("action") == f"/author/{pk}/up/"
    assert form[0].get("method") == "post"
    assert "d-none" in form[0].get("class")
    assert len(form[0].cssselect("input[name='csrfmiddlewaretoken']")) == 1

    # The "Up" button must NOT be a bare GET link to the action URL
    hrefs = [a.get("href") for a in card.cssselect("a.btn")]
    assert f"/author/{pk}/up/" not in hrefs


@pytest.mark.django_db
def test_card_modal_action_renders_modal_trigger(
    client_user_author_view_change: Client, cv_author, author_douglas_adams, monkeypatch
):
    """A CardAction targeting a modal-enabled view renders a modal trigger (data-cv-modal), not a plain link."""
    from tests.test1.app.views import AuthorCardListView, AuthorDeleteView

    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    monkeypatch.setattr(AuthorDeleteView, "cv_modal_size", "lg")
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="delete", label="Delete")])

    response = client_user_author_view_change.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    pk = author_douglas_adams.pk

    modal_trigger = card.cssselect("a[data-cv-modal='true']")
    assert len(modal_trigger) == 1
    assert modal_trigger[0].get("data-cv-modal-size") == "lg"
    assert modal_trigger[0].get("href") == f"/author/{pk}/delete/"

    # A modal action is neither a submit-form trigger nor does it emit a hidden form
    assert len(card.cssselect("a[data-cv-action='submit-form']")) == 0
    assert len(card.cssselect("form.d-none")) == 0


@pytest.mark.django_db
def test_card_get_action_stays_plain_link(
    client_user_author_view_change: Client, cv_author, author_douglas_adams, monkeypatch
):
    """GET card actions still render as plain href links (no submit-form, no form, no modal)."""
    from tests.test1.app.views import AuthorCardListView

    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", label="Details")])

    response = client_user_author_view_change.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    pk = author_douglas_adams.pk

    detail = card.cssselect("a.btn")[0]
    assert detail.get("href") == f"/author/{pk}/detail/"
    assert detail.get("data-cv-action") is None
    assert detail.get("data-cv-modal") is None
    assert len(card.cssselect("form")) == 0
