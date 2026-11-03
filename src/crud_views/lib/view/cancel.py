"""Private, bounded sibling-navigation transport. Signatures are not access grants."""

import binascii
import json
from dataclasses import dataclass
from urllib.parse import parse_qsl

from django.core import signing
from django.http import QueryDict
from django.views.generic.list import MultipleObjectMixin

from ..settings import crud_views_settings

SALT = "crud_views.cancel.v1"
MAX_TOKEN = 16384
MAX_JSON = 12288
MAX_QUERY = 8192
MAX_PAIRS = 128


@dataclass(frozen=True)
class CancelCapture:
    origin: str
    query: str | None


def navigation_params():
    origin = crud_views_settings.origin_param
    return origin, f"{origin}_cancel", f"{origin}_restore"


def clean_navigation_query(querydict):
    query = querydict.copy()
    for name in navigation_params():
        query.pop(name, None)
    return query


def effective_cancel_keys(owner):
    keys = owner.cv_cancel_keys
    if keys != "auto":
        return tuple(dict.fromkeys(keys or ()))
    viewset = owner.cv_viewset
    if viewset is None:
        return ()
    candidates = ("list", "card", "detail") if owner.cv_object else ("list", "card")
    return tuple(
        key
        for key in candidates
        if viewset.is_view_registered(key) or (key == "list" and viewset.is_view_registered("card"))
    )


def is_cancel_list_destination(cls):
    return issubclass(cls, MultipleObjectMixin) and not cls.cv_object


def _coordinates(view):
    return {name: str(view.kwargs[name]) for name in view.cv_viewset.get_parent_url_args()}


def _valid_payload(payload):
    if type(payload) is not dict or set(payload) != {"v", "origin", "query", "viewset", "parents"}:
        return False
    if type(payload["v"]) is not int or payload["v"] != 1:
        return False
    origin, query, identity, parents = (payload[key] for key in ("origin", "query", "viewset", "parents"))
    if type(origin) is not str or not 0 < len(origin) <= 128:
        return False
    if type(identity) is not list or len(identity) != 2:
        return False
    if any(type(item) is not str or len(item) > 256 for item in identity):
        return False
    if type(parents) is not dict or len(parents) > 16:
        return False
    if any(type(k) is not str or type(v) is not str or len(k) > 512 or len(v) > 512 for k, v in parents.items()):
        return False
    if query is not None:
        if type(query) is not str or len(query.encode("utf-8")) > MAX_QUERY:
            return False
        parse_qsl(query, keep_blank_values=True, max_num_fields=MAX_PAIRS)
    return True


def encode_cancel_state(view, origin, query):
    payload = {
        "v": 1,
        "origin": origin,
        "query": query,
        "viewset": [view.cv_viewset.app or "", view.cv_viewset.name],
        "parents": _coordinates(view),
    }
    try:
        if not _valid_payload(payload) or len(signing.JSONSerializer().dumps(payload)) > MAX_JSON:
            return None
        token = signing.Signer(salt=SALT).sign_object(payload, compress=False)
        return token if len(token.encode("ascii")) <= MAX_TOKEN else None
    except (ValueError, UnicodeError):
        return None


def capture_cancel_state(view, origin):
    request = getattr(view, "request", None)
    if request is None:
        return None
    return encode_cancel_state(view, origin, clean_navigation_query(request.GET).urlencode())


def read_cancel_state(view):
    query = view.request.GET
    origin_name, token_name, _ = navigation_params()
    origins, tokens = query.getlist(origin_name), query.getlist(token_name)
    if len(origins) > 1 or len(tokens) > 1:
        return None
    if not tokens:
        origin = view.cv_get_origin_key()
        return CancelCapture(origin, None) if origin else None
    token = tokens[0]
    try:
        if len(token) > MAX_TOKEN or not token.isascii() or token.startswith("."):
            return None
        # Check decoded size before the JSON parser (and never allow decompression).
        encoded = token.rsplit(":", 1)[0]
        if len(signing.b64_decode(encoded.encode("ascii"))) > MAX_JSON:
            return None
        payload = signing.Signer(salt=SALT).unsign_object(token)
        if not _valid_payload(payload):
            return None
        if payload["viewset"] != [view.cv_viewset.app or "", view.cv_viewset.name]:
            return None
        if origins and origins[0] != payload["origin"]:
            return None
        captured = payload["query"]
        if captured is not None:
            captured = clean_navigation_query(QueryDict(captured)).urlencode()
    except (signing.BadSignature, ValueError, UnicodeError, binascii.Error, json.JSONDecodeError):
        return None
    # Coordinate/hook/programming errors are not malformed browser input.
    if payload["parents"] != _coordinates(view):
        return None
    return CancelCapture(payload["origin"], captured)
