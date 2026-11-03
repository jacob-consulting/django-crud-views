"""Observable regression coverage for the Cancel quality-gate repairs."""

from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from django import forms
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from crud_views.lib.crispy.form import CrispyFormMixin
from crud_views.lib.session import SessionData
from crud_views.lib.view.cancel import SALT, capture_cancel_state, effective_cancel_keys, encode_cancel_state
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


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["detail", "list"])
@pytest.mark.parametrize("allowed", [False, True])
def test_cancel_dispatches_concrete_destination_policy(
    cv_author_origin, user_author_origin, author_douglas_adams, monkeypatch, key, allowed
):
    events = []
    original = cv_author_origin.get_view_class(key)

    class Destination(original):
        cv_viewset = None

        @classmethod
        def cv_has_access(cls, user, obj=None):
            events.append(("access", cls, user, obj))
            return allowed

        @classmethod
        def cv_action_enabled(cls, user, obj=None):
            events.append(("state", cls, user, obj))
            return True

    monkeypatch.setattr(Destination, "cv_viewset", cv_author_origin)
    monkeypatch.setitem(cv_author_origin._views, key, Destination)
    owner = bound(cv_author_origin.get_view_class("update"), user_author_origin, author_douglas_adams, {"cv_from": key})
    owner.cv_cancel_keys = [key]
    owner.cv_cancel_key = key
    expected_url = f"/author_origin/{author_douglas_adams.pk}/detail/" if key == "detail" else "/author_origin/"
    assert owner.cv_get_cancel_url() == (expected_url if allowed else None)
    target_obj = author_douglas_adams if key == "detail" else None
    expected = [("access", Destination, user_author_origin, target_obj)]
    if allowed:
        expected.append(("state", Destination, user_author_origin, target_obj))
    assert events == expected


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


@pytest.mark.django_db
@pytest.mark.parametrize("identity", [None, "author_origin", [], [""], ["", "author_origin", "extra"]])
def test_malformed_signed_identity_cannot_restore_query(
    cv_author_origin, user_author_origin, author_douglas_adams, identity
):
    view = bound(cv_author_origin.get_view_class("update"), user_author_origin, author_douglas_adams)
    payload = signing.Signer(salt=SALT).unsign_object(encode_cancel_state(view, "list", "x=untrusted"))
    payload["viewset"] = identity
    token = signing.Signer(salt=SALT).sign_object(payload)
    view.request.GET = RequestFactory().get("/", {"cv_from_cancel": token}).GET
    assert view.cv_get_cancel_url() == "/author_origin/card/"


@pytest.mark.django_db
@pytest.mark.parametrize("origin", ["gone", "detail"])
def test_unregistered_or_unreversible_origin_uses_configured_fallback(
    cv_author_origin, user_author_origin, author_douglas_adams, monkeypatch, origin
):
    view = bound(cv_author_origin.get_view_class("update"), user_author_origin, author_douglas_adams)
    view.cv_cancel_keys = [origin]
    token = encode_cancel_state(view, origin, "x=origin")
    view.request.GET = RequestFactory().get("/", {"cv_from_cancel": token}).GET
    if origin == "detail":
        monkeypatch.setattr(
            cv_author_origin.get_view_class("detail"),
            "cv_get_url_extra_kwargs",
            classmethod(lambda cls: {"unregistered_coordinate": "bad"}),
        )
    assert view.cv_get_cancel_url() == "/author_origin/card/"


@pytest.mark.django_db
def test_create_key_cannot_borrow_explicit_saved_object(cv_author_origin, user_author_origin, author_douglas_adams):
    view = bound(cv_author_origin.get_view_class("create"), user_author_origin, query={"cv_from": "detail"})
    view.cv_cancel_keys = ["detail"]
    assert view.cv_get_cancel_key(obj=author_douglas_adams) == "card"


@pytest.mark.parametrize(
    "query,expected",
    [
        ("reset_filter=true", "/publisher/"),
        ("reset_filter=true&sort=name&order=name&dir=desc", "/publisher/?sort=name&order=name&dir=desc"),
    ],
)
def test_reset_drops_remembered_filter_and_retains_order_controls(cv_publisher, query, expected):
    view = cv_publisher.get_view_class("list")()
    view.kwargs = {}
    view.request = RequestFactory().get("/publisher/?" + query)
    view.request.session = {}
    with SessionData.from_view(view) as state:
        state["filter_query_string"] = "name=Penguin"
    response = view.get(view.request)
    assert response["Location"] == expected
    assert SessionData.from_view(view).get("filter_query_string") is None


@pytest.mark.django_db
def test_selector_unregistered_origin_forwards_invalid_marker(client_user_vehicle_add, cv_vehicle, monkeypatch):
    from django.contrib.contenttypes.models import ContentType

    from tests.test1.app.models import Car

    monkeypatch.setattr(cv_vehicle.get_view_class("create"), "cv_cancel_keys", ["gone"])
    response = client_user_vehicle_add.post(
        "/vehicle/create/select/?cv_from=gone", {"polymorphic_ctype_id": ContentType.objects.get_for_model(Car).pk}
    )
    assert response.status_code == 302
    assert parse_qs(urlsplit(response["Location"]).query) == {"cv_from_cancel": ["invalid"]}


def test_idle_browser_connection_cannot_starve_fixture_requests():
    import socket
    import threading
    from urllib.request import urlopen
    from wsgiref.simple_server import make_server

    from tests.browser.cancel_fixture_http import FixtureServer

    accepted = threading.Event()

    class Server(FixtureServer):
        request_timeout = 0.05

        def get_request(self):
            result = super().get_request()
            accepted.set()
            return result

    def application(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ready"]

    with make_server("127.0.0.1", 0, application, server_class=Server) as server:
        worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        worker.start()
        idle = socket.create_connection(server.server_address, timeout=1)
        try:
            assert accepted.wait(1), "Idle speculative connection was never accepted"
            body = None
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=0.3) as response:
                    body = response.read()
            except TimeoutError:
                pass
            assert body == b"ready", "An idle browser socket blocked the following real request"
        finally:
            idle.close()
            server.shutdown()
            worker.join(timeout=1)
        assert not worker.is_alive()
