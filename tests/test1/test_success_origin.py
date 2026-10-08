"""
Dynamic success target: the origin view key travels in the link's query string (shared with
cv_cancel_keys), the target view resolves its post-success redirect through cv_success_keys.
"""

import pytest
from django.urls import reverse

PARAM = "cv_from"
MODAL_HEADERS = {"X-CV-Modal": "true"}
AUTHOR_DATA = {"first_name": "Douglas", "last_name": "Adams", "pseudonym": ""}


def url(viewset, key, pk=None) -> str:
    kwargs = {"pk": pk} if pk is not None else {}
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def check_ids(view_cls) -> list:
    return [m.id for c in view_cls.checks() for m in c.messages()]


@pytest.fixture
def origin_success(monkeypatch):
    """Give the author_origin form views cv_success_keys, with "card" as the static fallback."""
    from tests.test1.app import views

    for cls in (
        views.AuthorOriginCreateView,
        views.AuthorOriginUpdateView,
        views.AuthorOriginDeleteView,
        views.AuthorOriginContactView,
    ):
        monkeypatch.setattr(cls, "cv_success_key", "card")
        monkeypatch.setattr(cls, "cv_success_keys", ["list", "detail"])


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("origin", ["list", "detail"])
def test_update_success_returns_to_origin(
    origin_success, client_user_author_origin, cv_author_origin, author_douglas_adams, origin
):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(f"{url(cv_author_origin, 'update', pk)}?{PARAM}={origin}", AUTHOR_DATA)
    assert response.status_code == 302
    expected = url(cv_author_origin, origin, pk if origin == "detail" else None)
    assert response["Location"] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["", f"?{PARAM}=", f"?{PARAM}=Detail", f"?{PARAM}=../x", f"?{PARAM}=card"])
def test_update_success_falls_back(
    origin_success, client_user_author_origin, cv_author_origin, author_douglas_adams, query
):
    """Missing, malformed or not-allowed origins (card is registered but not listed) -> cv_success_key."""
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(f"{url(cv_author_origin, 'update', pk)}{query}", AUTHOR_DATA)
    assert response.status_code == 302
    assert response["Location"] == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_update_success_falls_back_for_unregistered_allowed_key(
    origin_success, client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch
):
    """An unregistered entry (an ignored viewset.E253) degrades gracefully at runtime."""
    from tests.test1.app.views import AuthorOriginUpdateView

    monkeypatch.setattr(AuthorOriginUpdateView, "cv_success_keys", ["list", "detail", "nope"])
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(f"{url(cv_author_origin, 'update', pk)}?{PARAM}=nope", AUTHOR_DATA)
    assert response["Location"] == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_success_without_success_keys_is_unchanged(client_user_author_origin, cv_author_origin, author_douglas_adams):
    """cv_cancel_keys alone does not affect the success redirect."""
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail", AUTHOR_DATA)
    assert response["Location"] == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_create_success_returns_to_list_origin(origin_success, client_user_author_origin, cv_author_origin):
    response = client_user_author_origin.post(f"{url(cv_author_origin, 'create')}?{PARAM}=list", AUTHOR_DATA)
    assert response.status_code == 302
    assert response["Location"] == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_delete_success_returns_to_list_origin(
    origin_success, client_user_author_origin, cv_author_origin, author_douglas_adams
):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=list", {"confirm": True})
    assert response.status_code == 302
    assert response["Location"] == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_delete_success_never_returns_to_deleted_object(
    origin_success, client_user_author_origin, cv_author_origin, author_douglas_adams
):
    """The object is gone (pk is None after delete) -> an object origin falls back (runtime half of E254)."""
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(
        f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=detail", {"confirm": True}
    )
    assert response.status_code == 302
    assert response["Location"] == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_custom_form_success_returns_to_detail_origin(
    origin_success, client_user_author_origin, cv_author_origin, author_douglas_adams
):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(
        f"{url(cv_author_origin, 'contact', pk)}?{PARAM}=detail", {"subject": "Hi", "body": "there"}
    )
    assert response.status_code == 302
    assert response["Location"] == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_modal_success_redirect_header_uses_origin(client_user_author_modal, author_douglas_adams, monkeypatch):
    from tests.test1.app.views import AuthorModalContactView

    monkeypatch.setattr(AuthorModalContactView, "cv_success_keys", ["detail"])
    pk = author_douglas_adams.pk
    response = client_user_author_modal.post(
        f"/author_modal/{pk}/contact/?{PARAM}=detail",
        {"subject": "Hello", "body": "Nice to meet you."},
        headers=MODAL_HEADERS,
    )
    assert response.status_code == 204
    assert response.headers["X-CV-Redirect"] == f"/author_modal/{pk}/detail/"


@pytest.mark.django_db
def test_action_success_returns_to_detail_origin(client_user_author_change, cv_author, monkeypatch):
    from tests.test1.app.models import Author
    from tests.test1.app.views import AuthorPingView

    monkeypatch.setattr(AuthorPingView, "cv_success_keys", ["detail"])
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_change.post(f"/author/{a.pk}/ping/?{PARAM}=detail")
    assert response.status_code == 302
    assert response["Location"] == url(cv_author, "detail", a.pk)


@pytest.mark.django_db
def test_cv_get_dict_exposes_success_keys(
    origin_success, client_user_author_origin, cv_author_origin, author_douglas_adams
):
    response = client_user_author_origin.get(url(cv_author_origin, "update", author_douglas_adams.pk))
    view = response.context["view"]
    ctx = view.cv_get_dict(context=view.cv_get_view_context())
    assert ctx["cv_success_keys"] == ["list", "detail"]
    assert ctx["cv_success_key"] == "card"


# ---------------------------------------------------------------------------
# Link emission: a target with only cv_success_keys still receives the origin
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_links_carry_origin_for_success_keys_only(
    client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch
):
    from tests.test1.app.views import AuthorOriginUpdateView

    monkeypatch.setattr(AuthorOriginUpdateView, "cv_cancel_keys", None)
    monkeypatch.setattr(AuthorOriginUpdateView, "cv_success_keys", ["detail"])
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    assert f'href="{url(cv_author_origin, "update", pk)}?{PARAM}=detail"' in response.content.decode()


# ---------------------------------------------------------------------------
# System checks E253 / E254
# ---------------------------------------------------------------------------


def test_check_e253_without_viewset_is_skipped():
    from crud_views.lib.views import UpdateView

    class Unbound(UpdateView):
        cv_success_keys = ["nope"]

    assert "viewset.E253" not in check_ids(Unbound)


@pytest.mark.django_db
def test_check_e253_unregistered_key(cv_author_origin):
    from crud_views.lib.views import ActionView

    class BadSuccessKeysView(ActionView):
        cv_viewset = cv_author_origin
        cv_key = "e253_probe"
        cv_path = "e253-probe"
        cv_backend_only = True
        cv_success_keys = ["nope"]

        def action(self, context):
            return True

    assert "viewset.E253" in check_ids(BadSuccessKeysView)


def test_check_e253_registered_keys_pass():
    from tests.test1.app.views import AuthorOriginUpdateView

    class Probe(AuthorOriginUpdateView):
        cv_success_keys = ["list", "detail"]

    assert "viewset.E253" not in check_ids(Probe)


def test_check_e253_list_accepted_on_card_only_viewset():
    from tests.test1.app.views import AuthorWideCardCreateView

    class CardOnlyProbe(AuthorWideCardCreateView):
        cv_success_keys = ["list"]

    assert "viewset.E253" not in check_ids(CardOnlyProbe)


def test_check_e254_delete_rejects_object_keys():
    from tests.test1.app.views import AuthorOriginDeleteView

    class Probe(AuthorOriginDeleteView):
        cv_success_keys = ["list", "detail"]

    assert "viewset.E254" in check_ids(Probe)


def test_check_e254_delete_accepts_no_object_keys():
    from tests.test1.app.views import AuthorOriginDeleteView

    class Probe(AuthorOriginDeleteView):
        cv_success_keys = ["list", "card"]

    assert "viewset.E254" not in check_ids(Probe)


def test_check_e254_only_applies_to_delete():
    from tests.test1.app.views import AuthorOriginUpdateView

    class Probe(AuthorOriginUpdateView):
        cv_success_keys = ["detail"]

    assert "viewset.E254" not in check_ids(Probe)


def test_check_e254_leaves_unregistered_keys_to_e253():
    from tests.test1.app.views import AuthorOriginDeleteView

    class Probe(AuthorOriginDeleteView):
        cv_success_keys = ["nope"]

    ids = check_ids(Probe)
    assert "viewset.E253" in ids
    assert "viewset.E254" not in ids
