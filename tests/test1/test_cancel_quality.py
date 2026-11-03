"""Observable regression coverage for the Cancel quality-gate repairs."""

from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from crud_views.lib.crispy.form import CrispyFormMixin
from crud_views.lib.view.cancel import capture_cancel_state, effective_cancel_keys, encode_cancel_state
from tests.test1.app.models import Author
from tests.test1.test_cancel_navigation import emitted_link, rendered_cancel
from tests.test1.test_cancel_permissions import bound


@pytest.mark.django_db
def test_rendered_cancel_restores_repeated_blank_query_without_writes(client_user_author_origin, author_douglas_adams):
    before = list(Author.objects.order_by("pk").values())
    page = client_user_author_origin.get("/author_origin/?x=&x=two&sort=last_name")
    link = emitted_link(page, f"/author_origin/{author_douglas_adams.pk}/update/")
    form = client_user_author_origin.get(link)
    assert form.status_code == 200
    destination = rendered_cancel(form)
    assert parse_qs(urlsplit(destination).query, keep_blank_values=True) == {
        "x": ["", "two"],
        "sort": ["last_name"],
        "cv_from_restore": ["1"],
    }
    returned = client_user_author_origin.get(destination)
    assert returned.status_code == 200
    assert returned.context["view"].request.GET.getlist("x") == ["", "two"]
    assert list(Author.objects.order_by("pk").values()) == before


def test_missing_request_is_configuration_error(cv_author_origin):
    view = cv_author_origin.get_view_class("update")()
    with pytest.raises(ImproperlyConfigured, match="requires a request"):
        view.cv_get_cancel_url()
    assert capture_cancel_state(view, "list") is None
    assert effective_cancel_keys(SimpleNamespace(cv_cancel_keys="auto", cv_viewset=None)) == ()


@pytest.mark.django_db
def test_request_override_does_not_rebind_owner(cv_author_origin, user_author_origin, author_douglas_adams):
    view = bound(cv_author_origin.get_view_class("update"), user_author_origin, author_douglas_adams)
    original = view.request
    token = encode_cancel_state(view, "detail", "x=&x=original")
    override = RequestFactory().get("/", {"cv_from_cancel": token})
    override.user = user_author_origin
    assert view.cv_get_cancel_url(request=override) == (
        f"/author_origin/{author_douglas_adams.pk}/detail/?x=&x=original"
    )
    assert view.request is original
    assert view.cv_get_cancel_url() == "/author_origin/card/"


@pytest.mark.parametrize("fails", [False, True])
def test_reentrant_crispy_context_restored_after_kwargs_hook(fails):
    previous = {"cv_url": "/previous/", "cv_action_label": "Previous"}
    current = {"cv_url": "/current/", "cv_action_label": "Cancel"}

    class Helper(CrispyFormMixin, forms.Form):
        cv_view = SimpleNamespace(
            get_cancel_button_context=lambda **kwargs: current, request=SimpleNamespace(user=None)
        )

        def get_cancel_button_kwargs(self):
            assert self._cv_cancel_button_context is current
            if fails:
                raise RuntimeError("custom kwargs hook")
            return super().get_cancel_button_kwargs()

    helper = Helper(cv_view=Helper.cv_view)
    helper._cv_cancel_button_context = previous
    if fails:
        with pytest.raises(RuntimeError, match="custom kwargs hook"):
            helper.get_cancel_button()
    else:
        button = helper.get_cancel_button()
        assert button.name == "reset"
        assert button.value == "Cancel"
    assert helper._cv_cancel_button_context is previous


def test_crispy_kwargs_can_resolve_context_without_outer_button():
    class Helper(CrispyFormMixin, forms.Form):
        cv_view = SimpleNamespace(
            get_cancel_button_context=lambda **kwargs: {"cv_url": "/allowed/", "cv_action_label": "Cancel"},
            request=SimpleNamespace(user=None),
        )

    assert Helper(cv_view=Helper.cv_view).get_cancel_button_kwargs() == {
        "name": "reset",
        "value": "Cancel",
        "data_cv_cancel_url": "/allowed/",
    }
