"""Bounded transport and independent list state, including hostile browser input."""

from copy import deepcopy
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit, urlencode

import pytest
from django.core import signing
from django.http import QueryDict
from django.test import RequestFactory, override_settings

from crud_views.lib.session import SessionData
from crud_views.lib.view.cancel import (
    SALT, capture_cancel_state, clean_navigation_query, encode_cancel_state,
    navigation_params, read_cancel_state,
)


@pytest.fixture
def owner(cv_author_origin):
    view = cv_author_origin.get_view_class("update")()
    view.kwargs = {}
    view.request = RequestFactory().get("/")
    return view


def bind(view, token, origin="list"):
    query = {} if origin is None else {navigation_params()[0]: origin}
    if token is not None:
        query[navigation_params()[1]] = token
    view.request = RequestFactory().get("/", query)
    return view


def payload(view, query=""):
    return signing.Signer(salt=SALT).unsign_object(encode_cancel_state(view, "list", query))


def test_old_session_navigation_is_cleaned_on_read(cv_publisher):
    view = cv_publisher.get_view_class("list")()
    view.kwargs = {}
    view.request = RequestFactory().get("/publisher/")
    view.request.session = {}
    with SessionData.from_view(view) as state:
        state["filter_query_string"] = "name=Penguin&cv_from=detail&cv_from_cancel=bad&cv_from_restore=1"
    response = view.get(view.request)
    assert response["Location"] == "/publisher/?name=Penguin"
    assert SessionData.from_view(view).get("filter_query_string") == "name=Penguin"


@pytest.mark.parametrize("query", ["", None, "x=a&x=&x=a&sort=last_name&page=2", "unicode=%C3%A9&blank="])
def test_capture_multiplicity_and_legacy_null(owner, query):
    token = encode_cancel_state(owner, "list", query)
    capture = read_cancel_state(bind(owner, token))
    assert capture.query == query
    assert capture.origin == "list"
    assert read_cancel_state(bind(owner, token, origin=None)) == capture


@pytest.mark.parametrize("change", [
    {"v": True}, {"v": 2}, {"query": []}, {"query": {}}, {"origin": 1}, {"origin": "x" * 129},
    {"viewset": ["", "wrong"]}, {"viewset": ["", 1]}, {"viewset": ["x" * 257, "a"]},
    {"parents": {"unexpected": "1"}}, {"parents": []}, {"parents": {"x": 1}},
    {"parents": {"x": "x" * 513}}, {"parents": {str(i): "1" for i in range(17)}},
    {"query": "x=" + "a" * 8191}, {"query": "&".join("x=1" for _ in range(129))},
    {"extra": "field"},
])
def test_invalid_signed_payload_is_rejected(owner, change):
    data = {**payload(owner), **change}
    token = signing.Signer(salt=SALT).sign_object(data)
    assert read_cancel_state(bind(owner, token)) is None


@pytest.mark.parametrize("token", ["", "invalid", "é", "x" * 16385, ".compressed", "e30:wrong"])
def test_bad_token_does_not_degrade_to_legacy(owner, token):
    assert read_cancel_state(bind(owner, token)) is None


@pytest.mark.parametrize("field", ["cv_from", "cv_from_cancel"])
def test_duplicate_scalars_rejected(owner, field):
    token = encode_cancel_state(owner, "list", "")
    bind(owner, token)
    owner.request.GET = owner.request.GET.copy()
    owner.request.GET.appendlist(field, owner.request.GET[field])
    assert read_cancel_state(owner) is None


def test_limits_and_compression_rejection(owner):
    assert encode_cancel_state(owner, "list", "x=" + "a" * 8190)
    assert encode_cancel_state(owner, "list", "x=" + "a" * 8191) is None
    assert encode_cancel_state(owner, "list", "&".join("x=1" for _ in range(128)))
    assert encode_cancel_state(owner, "list", "&".join("x=1" for _ in range(129))) is None
    data = payload(owner, "x=" + "a" * 8000)
    compressed = signing.Signer(salt=SALT).sign_object(data, compress=True)
    assert compressed.startswith(".")
    assert read_cancel_state(bind(owner, compressed)) is None
    for data in ([1], {"v": 1}, {**payload(owner), "query": "x" * 13000}):
        assert read_cancel_state(bind(owner, signing.Signer(salt=SALT).sign_object(data))) is None


def test_rotated_signing_keys(owner):
    with override_settings(SECRET_KEY="retired", SECRET_KEY_FALLBACKS=[]):
        token = encode_cancel_state(owner, "list", "x=1")
    with override_settings(SECRET_KEY="current", SECRET_KEY_FALLBACKS=["retired"]):
        assert read_cancel_state(bind(owner, token)).query == "x=1"
    with override_settings(SECRET_KEY="current", SECRET_KEY_FALLBACKS=[]):
        assert read_cancel_state(bind(owner, token)) is None


def test_capture_strips_internal_fields_and_is_deterministic(owner, monkeypatch):
    from crud_views.lib.settings import crud_views_settings
    monkeypatch.setattr(crud_views_settings, "origin_param", "source")
    owner.request = RequestFactory().get("/?x=1&source=detail&source_cancel=bad&source_restore=1&x=2")
    token = capture_cancel_state(owner, "list")
    assert token == capture_cancel_state(owner, "list")
    assert read_cancel_state(bind(owner, token)).query == "x=1&x=2"
    assert navigation_params() == ("source", "source_cancel", "source_restore")


def test_parent_binding_and_programming_errors(cv_book):
    view = cv_book.get_view_class("update")()
    parent_key = cv_book.get_parent_url_args()[0]
    view.kwargs = {parent_key: 1}
    token = encode_cancel_state(view, "list", "x=1")
    assert read_cancel_state(bind(view, token)).query == "x=1"
    view.kwargs[parent_key] = 2
    assert read_cancel_state(bind(view, token)) is None
    other = encode_cancel_state(view, "list", "x=1")
    assert other != token
    view.kwargs = {}
    with pytest.raises(KeyError):
        read_cancel_state(bind(view, token))
