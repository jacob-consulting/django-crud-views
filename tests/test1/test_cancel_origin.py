"""
Dynamic cancel button target: the origin view key travels in the link's query string,
the target view resolves it through cv_cancel_keys.
Spec: superpowers/specs/2026-09-08-cancel-button-origin-design.md
"""

import re

import pytest
from django.template import Context, Template
from django.urls import reverse

PARAM = "cv_from"


def url(viewset, key, pk=None) -> str:
    kwargs = {"pk": pk} if pk is not None else {}
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def cancel_url(response) -> str:
    """The URL the crispy cancel button navigates to (data-cv-cancel-url)."""
    match = re.search(r'data-cv-cancel-url="([^"]+)"', response.content.decode())
    assert match, "no cancel button rendered"
    return match.group(1)


def hrefs(response) -> list[str]:
    return re.findall(r'href="([^"]+)"', response.content.decode())


def render_cancel_tag(response) -> str:
    """Render {% cv_cancel_button %} against the response's view; return the href."""
    tpl = Template("{% load crud_views %}{% cv_cancel_button %}")
    html = tpl.render(Context({"view": response.context["view"], "request": response.context["request"]}))
    match = re.search(r'href="([^"]+)"', html)
    assert match, html
    return match.group(1)


# ---------------------------------------------------------------------------
# Resolution (Task 3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_default_without_cancel_keys_is_unchanged(client_user_author_change, cv_author, author_douglas_adams):
    """A view without cv_cancel_keys ignores the parameter entirely."""
    pk = author_douglas_adams.pk
    response = client_user_author_change.get(url(cv_author, "update", pk), {PARAM: "detail"})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_author, "list")
    assert response.context["view"].cv_cancel_keys is None


@pytest.mark.django_db
def test_default_without_cancel_keys_is_unchanged_int_pk(client_user_publisher_change, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_user_publisher_change.get(url(cv_publisher, "update", pk), {PARAM: "detail"})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_publisher, "list")


@pytest.mark.django_db
def test_update_resolves_detail_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)
    assert render_cancel_tag(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_update_resolves_list_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "list"})
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_update_without_origin_falls_back(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk))
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value",
    ["card", "nope", " detail", "de-tail", "Detail", "a/b", "detail%20", "", "2detail"],
    ids=["not-allowed", "unregistered", "space", "dash", "upper", "slash", "encoded", "empty", "digit-first"],
)
def test_invalid_or_disallowed_origin_falls_back(
    client_user_author_origin, cv_author_origin, author_douglas_adams, value
):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: value})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_create_cannot_return_to_object_view(client_user_author_origin, cv_author_origin):
    """detail needs an object; a create view has none -> fallback. list is fine."""
    response = client_user_author_origin.get(url(cv_author_origin, "create"), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "card")
    response = client_user_author_origin.get(url(cv_author_origin, "create"), {PARAM: "list"})
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_no_object_custom_form_cannot_return_to_object_view(client_user_author_origin, cv_author_origin):
    response = client_user_author_origin.get(url(cv_author_origin, "broadcast"), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "card")
    response = client_user_author_origin.get(url(cv_author_origin, "broadcast"), {PARAM: "list"})
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_cv_get_cancel_key_defaults_obj_to_view_object(
    client_user_author_origin, cv_author_origin, author_douglas_adams
):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    view = response.context["view"]
    assert view.cv_get_cancel_key() == "detail"
    assert view.cv_get_cancel_key(obj=None) == "detail"
    assert view.cv_get_origin_key() == "detail"


@pytest.mark.django_db
def test_cv_get_cancel_key_resolves_for_resource_obj(client_user_author_origin, cv_author_origin, author_douglas_adams):
    """A Resource (pydantic BaseModel, no _state) must not be mistaken for an unsaved Django instance."""
    from tests.test1.app.resources import S3File

    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    view = response.context["view"]
    resource_obj = S3File(key="reports/2026/q1.pdf", size=111)
    assert view.cv_get_cancel_key(obj=resource_obj) == "detail"


@pytest.mark.django_db
def test_cv_get_cancel_key_falls_back_for_unsaved_instance(
    client_user_author_origin, cv_author_origin, author_douglas_adams
):
    """An unsaved Django model instance (obj._state.adding is True) cannot return to "detail"."""
    from tests.test1.app.models import Author

    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    view = response.context["view"]
    unsaved = Author(first_name="Unsaved", last_name="Author")
    assert view.cv_get_cancel_key(obj=unsaved) == "card"


@pytest.mark.django_db
def test_cv_get_dict_exposes_cancel_keys(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    view = response.context["view"]
    ctx = view.cv_get_context("update", obj=author_douglas_adams, user=view.request.user, request=view.request)
    assert ctx["cv_cancel_keys"] == ["list", "detail"]
    assert ctx["cv_cancel_key"] == "card"


# ---------------------------------------------------------------------------
# System check E252
# ---------------------------------------------------------------------------


def check_ids(view_cls) -> list:
    return [m.id for c in view_cls.checks() for m in c.messages()]


def test_check_e252_without_viewset_is_skipped():
    from crud_views.lib.views import UpdateView

    class Unbound(UpdateView):
        cv_cancel_keys = ["nope"]

    assert "viewset.E252" not in check_ids(Unbound)


@pytest.mark.django_db
def test_check_e252_unregistered_key(cv_author_origin):
    from crud_views.lib.views import ActionView

    class BadCancelKeysView(ActionView):
        cv_viewset = cv_author_origin
        cv_key = "e252_probe"
        cv_path = "e252-probe"
        cv_backend_only = True
        cv_cancel_keys = ["nope"]

        def action(self, context):
            return True

    assert "viewset.E252" in check_ids(BadCancelKeysView)


@pytest.mark.django_db
def test_check_e252_registered_keys_pass(cv_author_origin):
    from tests.test1.app.views import AuthorOriginUpdateView

    assert "viewset.E252" not in check_ids(AuthorOriginUpdateView)


def test_check_e252_list_accepted_on_card_only_viewset():
    from tests.test1.app.views import AuthorWideCardCreateView

    class CardOnlyProbe(AuthorWideCardCreateView):
        cv_cancel_keys = ["list"]

    # author_wide_card registers "card" but no "list" -> the list->card fallback applies
    assert "viewset.E252" not in check_ids(CardOnlyProbe)


# ---------------------------------------------------------------------------
# Link emission (Task 4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_detail_page_links_carry_detail_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    links = hrefs(response)
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail" in links
    assert f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=detail" in links
    assert f"{url(cv_author_origin, 'contact', pk)}?{PARAM}=detail" in links
    # ViewSet-level ContextButton(key="edit", key_target="update") goes through ContextButton.get_context
    assert links.count(f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail") == 2
    # targets without cv_cancel_keys stay clean
    assert url(cv_author_origin, "detail", pk) in links
    assert url(cv_author_origin, "list") in links
    assert not any(h.startswith(url(cv_author_origin, "detail", pk) + "?") for h in links)


@pytest.mark.django_db
def test_detail_page_create_link_carries_no_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    """The create view has no object, so a link to it from an object view must stay clean (F2)."""
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    links = hrefs(response)
    assert url(cv_author_origin, "create") in links
    assert not any(h.startswith(url(cv_author_origin, "create") + "?") for h in links)


@pytest.mark.django_db
def test_card_only_viewset_emits_list_origin(author_douglas_adams):
    """A ViewSet without a list view: the card page counts as the "list" origin (F1).

    author_wide_card registers "card" but no "list"; AuthorWideCardUpdateView allows both
    "list" and "detail" as origins. The card page must emit ?cv_from=list, the update page
    must resolve it back to the card page, and without the parameter it must fall back to
    cv_cancel_key ("detail").
    """
    from django.contrib.auth.models import User
    from django.test.client import Client

    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import cv_author_wide_card

    user = User.objects.create_user(username="user_wide_card_origin", password="password")
    user_viewset_permission(user, cv_author_wide_card, "view")
    user_viewset_permission(user, cv_author_wide_card, "change")
    client = Client()
    client.force_login(user)

    pk = author_douglas_adams.pk

    response = client.get(url(cv_author_wide_card, "card"))
    assert response.status_code == 200
    assert f"{url(cv_author_wide_card, 'update', pk)}?{PARAM}=list" in hrefs(response)

    response = client.get(url(cv_author_wide_card, "update", pk), {PARAM: "list"})
    assert cancel_url(response) == url(cv_author_wide_card, "card")

    response = client.get(url(cv_author_wide_card, "update", pk))
    assert cancel_url(response) == url(cv_author_wide_card, "detail", pk)


@pytest.mark.django_db
def test_list_page_row_actions_carry_list_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "list"))
    links = hrefs(response)
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=list" in links
    assert f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=list" in links
    assert f"{url(cv_author_origin, 'create')}?{PARAM}=list" in links
    assert url(cv_author_origin, "detail", pk) in links


@pytest.mark.django_db
def test_card_page_actions_carry_card_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    """card is not in cv_cancel_keys of the update view -> the card link stays clean.

    This proves the emitter checks the *target's* allow-list, not just its presence.
    """
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "card"))
    links = hrefs(response)
    assert url(cv_author_origin, "update", pk) in links
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=card" not in links


@pytest.mark.django_db
def test_card_action_carries_origin_when_allowed(
    client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch
):
    from tests.test1.app.views import AuthorOriginUpdateView

    monkeypatch.setattr(AuthorOriginUpdateView, "cv_cancel_keys", ["list", "detail", "card"])
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "card"))
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=card" in hrefs(response)
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "card"})
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_cv_context_url_tag_carries_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    tpl = Template("{% load crud_views %}{% cv_context_url 'update' as u %}{{ u }}")
    out = tpl.render(Context({"view": response.context["view"], "request": response.context["request"]}))
    assert out == f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail"


@pytest.mark.django_db
def test_success_url_stays_clean(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(
        f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail",
        {"first_name": "Douglas", "last_name": "Adams", "pseudonym": ""},
    )
    assert response.status_code == 302
    assert response["Location"] == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_existing_viewset_links_unchanged(client_user_author_change, cv_author, author_douglas_adams):
    """No cv_cancel_keys anywhere on cv_author -> no link gains a parameter."""
    pk = author_douglas_adams.pk
    response = client_user_author_change.get(url(cv_author, "detail", pk))
    assert not any(f"{PARAM}=" in h for h in hrefs(response))


# ---------------------------------------------------------------------------
# Custom parameter name and guardian (Task 4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_custom_origin_param_name(client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch):
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "cancel_origin_param", "origin")
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    assert f"{url(cv_author_origin, 'update', pk)}?origin=detail" in hrefs(response)
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {"origin": "detail"})
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_guardian_update_resolves_detail_origin(
    client_guardian, user_guardian, cv_guardian_author_origin, author_douglas_adams
):
    from tests.lib.helper.guardian import user_guardian_object_perm

    user_guardian_object_perm(user_guardian, cv_guardian_author_origin, "view", author_douglas_adams)
    user_guardian_object_perm(user_guardian, cv_guardian_author_origin, "change", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(url(cv_guardian_author_origin, "detail", pk))
    assert response.status_code == 200
    assert f"{url(cv_guardian_author_origin, 'update', pk)}?{PARAM}=detail" in hrefs(response)
    response = client_guardian.get(url(cv_guardian_author_origin, "update", pk), {PARAM: "detail"})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_guardian_author_origin, "detail", pk)


# ---------------------------------------------------------------------------
# Validation bounces (Task 5): the origin survives an invalid POST re-render
# ---------------------------------------------------------------------------


def form_action(response) -> str:
    match = re.search(r'<form[^>]*class="cv-form"[^>]*action="([^"]*)"', response.content.decode())
    assert match, "no cv-form found"
    return match.group(1)


@pytest.mark.django_db
def test_update_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    origin_url = f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {"first_name": "", "last_name": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_create_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin):
    origin_url = f"{url(cv_author_origin, 'create')}?{PARAM}=list"
    response = client_user_author_origin.post(origin_url, {"first_name": "", "last_name": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_delete_unconfirmed_post_keeps_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    origin_url = f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {})  # confirm missing -> invalid
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_delete_protection_post_keeps_origin(client_user_author_origin, cv_author_origin):
    from tests.test1.app.models import Author

    author = Author.objects.create(first_name="Locked", last_name="Author", pseudonym="protected")
    origin_url = f"{url(cv_author_origin, 'delete', author.pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {"confirm": True})
    assert response.status_code == 200
    assert "This author is protected." in response.content.decode()
    assert Author.objects.filter(pk=author.pk).exists()
    # the protection page hides the form; the GET with origin still resolves for the button context
    response = client_user_author_origin.get(origin_url)
    assert response.context["view"].cv_get_cancel_key() == "detail"


@pytest.mark.django_db
def test_custom_form_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    origin_url = f"{url(cv_author_origin, 'contact', pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {"subject": "", "body": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_no_object_custom_form_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin):
    origin_url = f"{url(cv_author_origin, 'broadcast')}?{PARAM}=list"
    response = client_user_author_origin.post(origin_url, {"subject": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "list")


def test_no_object_custom_form_uses_create_context_actions():
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.views.form import CustomFormNoObjectView

    assert CustomFormNoObjectView.cv_context_actions == crud_views_settings.create_context_actions
