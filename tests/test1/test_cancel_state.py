"""Bounded transport and independent list state, including hostile browser input."""

from copy import deepcopy
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core import signing
from django.http import QueryDict
from django.test import RequestFactory, override_settings

from crud_views.lib.session import SessionData
from crud_views.lib.view.cancel import (
    SALT,
    capture_cancel_state,
    encode_cancel_state,
    navigation_params,
    read_cancel_state,
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
    assert read_cancel_state(bind(owner, token, origin="detail")) is None


def test_signed_internal_query_fields_are_removed(owner):
    token = encode_cancel_state(owner, "list", "x=1&cv_from=detail&cv_from_cancel=bad&cv_from_restore=1&x=")
    assert read_cancel_state(bind(owner, token)).query == "x=1&x="


@pytest.mark.parametrize(
    "change",
    [
        {"v": True},
        {"v": 2},
        {"query": []},
        {"query": {}},
        {"origin": 1},
        {"origin": "x" * 129},
        {"viewset": ["", "wrong"]},
        {"viewset": ["", 1]},
        {"viewset": ["x" * 257, "a"]},
        {"parents": {"unexpected": "1"}},
        {"parents": []},
        {"parents": {"x": 1}},
        {"parents": {"x": "x" * 513}},
        {"parents": {str(i): "1" for i in range(17)}},
        {"query": "x=" + "a" * 8191},
        {"query": "&".join("x=1" for _ in range(129))},
        {"extra": "field"},
    ],
)
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


@pytest.mark.parametrize("query", [None, ""])
@pytest.mark.django_db
def test_token_only_and_legacy_empty_are_distinct(owner, client_user_author_origin, author_douglas_adams, query):
    from tests.test1.test_cancel_navigation import rendered_cancel

    token = encode_cancel_state(owner, "list", query)
    response = client_user_author_origin.get(
        f"/author_origin/{author_douglas_adams.pk}/update/", {"cv_from_cancel": token}
    )
    expected = "/author_origin/" + ("?cv_from_restore=1" if query == "" else "")
    assert rendered_cancel(response) == expected
    assert response.context["view"].get_success_url() == "/author_origin/"


@pytest.mark.django_db
def test_copied_detail_capture_uses_current_form_object(
    owner, client_user_author_origin, author_douglas_adams, author_terry_pratchett
):
    from tests.test1.test_cancel_navigation import rendered_cancel

    token = encode_cancel_state(owner, "detail", "tab=one")
    data = {"cv_from": "detail", "cv_from_cancel": token}
    first = client_user_author_origin.get(f"/author_origin/{author_douglas_adams.pk}/update/", data)
    second = client_user_author_origin.get(f"/author_origin/{author_terry_pratchett.pk}/update/", data)
    for response, obj in ((first, author_douglas_adams), (second, author_terry_pratchett)):
        assert rendered_cancel(response) == f"/author_origin/{obj.pk}/detail/?tab=one"
        assert response.context["view"].cv_get_cancel_url() == rendered_cancel(response)
    create = client_user_author_origin.get("/author_origin/create/", data)
    assert create.context["view"].cv_get_cancel_url(obj=author_douglas_adams) == "/author_origin/card/"


@pytest.mark.parametrize("length", [16384, 16385])
def test_encoded_bound_precedes_decode(owner, monkeypatch, length):
    calls = []
    original = signing.b64_decode
    monkeypatch.setattr(signing, "b64_decode", lambda value: calls.append(len(value)) or original(value))
    assert read_cancel_state(bind(owner, "x" * length)) is None
    assert bool(calls) is (length == 16384)


@pytest.mark.parametrize("length", [12288, 12289])
def test_decoded_json_bound_is_independent(owner, monkeypatch, length):
    from crud_views.lib.view import cancel

    # Isolate the decoded ceiling: the default encoded ceiling is tighter once the signature is included.
    monkeypatch.setattr(cancel, "MAX_TOKEN", 20000)
    raw = signing.JSONSerializer().dumps(payload(owner)).ljust(length, b" ")
    token = signing.Signer(salt=SALT).sign(signing.b64_encode(raw).decode())
    capture = read_cancel_state(bind(owner, token))
    assert (capture is not None) is (length == 12288)


@pytest.mark.parametrize("raw", [b"not-json", b"[" * 2000 + b"0" + b"]" * 2000])
def test_signed_invalid_json_is_unusable(owner, raw):
    token = signing.Signer(salt=SALT).sign(signing.b64_encode(raw).decode())
    assert read_cancel_state(bind(owner, token)) is None


def test_query_unicode_bytes_and_scalar_schema_boundaries(owner):
    from crud_views.lib.view.cancel import _valid_payload

    data = payload(owner)
    assert _valid_payload({**data, "query": "x=" + "é" * 4095})
    assert not _valid_payload({**data, "query": "x=" + "é" * 4095 + "a"})
    # JSON escaping can hit the independent payload/token limits before the query-byte ceiling.
    assert encode_cancel_state(owner, "list", "x=" + "é" * 4095) is None
    for field, at_limit, over_limit in (
        ("origin", "x" * 128, "x" * 129),
        ("viewset", ["x" * 256, "y" * 256], ["x" * 257, "y"]),
        ("parents", {str(i): "x" * 512 for i in range(16)}, {str(i): "x" for i in range(17)}),
        ("parents", {"x" * 512: "y" * 512}, {"x" * 513: "y"}),
    ):
        assert _valid_payload({**data, field: at_limit})
        assert not _valid_payload({**data, field: over_limit})


@pytest.mark.parametrize("marker", ["", "0", "true", ["1", "1"]])
def test_restore_marker_invalidity_is_not_explicit_restore(cv_publisher, marker):
    view = cv_publisher.get_view_class("list")()
    view.kwargs = {}
    view.request = RequestFactory().get("/publisher/", {"cv_from_restore": marker, "cv_from": "list"})
    view.request.session = {}
    with SessionData.from_view(view) as state:
        state["filter_query_string"] = "name=Penguin"
    response = view.get(view.request)
    assert response["Location"] == "/publisher/?name=Penguin"
    assert not view.request._cv_cancel_restored
    assert view.request.META["QUERY_STRING"] == ""


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
    bind(view, token)
    with pytest.raises(KeyError):
        read_cancel_state(view)


@pytest.mark.django_db
def test_parent_lookup_and_custom_failures_have_distinct_outcomes(cv_book, book_hitchhiker, monkeypatch):
    from types import SimpleNamespace

    from crud_views.lib.view.base import CrudView

    owner = cv_book.get_view_class("update")()
    owner.kwargs = {cv_book.get_parent_url_args()[0]: book_hitchhiker.publisher_id}
    target = cv_book.get_view_class("list")
    actor = SimpleNamespace(has_perms=lambda perms: True)
    seen = []
    monkeypatch.setattr(
        target,
        "_cv_action_enabled_for_rendering",
        classmethod(lambda cls, user, obj, rendering_view: seen.append(obj) or True),
    )
    assert target._cv_cancel_target_available(actor, book_hitchhiker, owner)
    assert seen == [book_hitchhiker.publisher]
    owner.kwargs[cv_book.get_parent_url_args()[0]] = 99999999
    assert not target._cv_cancel_target_available(actor, book_hitchhiker, owner)
    owner.kwargs = {}
    with pytest.raises(KeyError):
        target._cv_cancel_target_available(actor, book_hitchhiker, owner)
    owner.kwargs = {cv_book.get_parent_url_args()[0]: book_hitchhiker.publisher_id}
    for hook in ("cv_has_access", "_cv_action_enabled_for_rendering"):

        def broken(*args):
            raise RuntimeError("application policy failed")

        with monkeypatch.context() as scoped:
            scoped.setattr(target, hook, classmethod(broken))
            with pytest.raises(RuntimeError, match="application policy"):
                target._cv_cancel_target_available(actor, book_hitchhiker, owner)
    assert owner.cv_get_parent_object.__func__ is CrudView.cv_get_parent_object


@pytest.fixture
def state_routes(request):
    import uuid

    from django_filters import FilterSet

    from crud_views.lib.views.list import ListViewFilterFormHelper
    from crud_views.lib.views.mixins import ListViewTableFilterMixin
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
    from tests.test1.app.models import Author
    from tests.test1.app.urls import urlpatterns
    from tests.test1.app.views import (
        AuthorCardListView,
        AuthorDeleteView,
        AuthorDetailView,
        AuthorListView,
        AuthorUpdateView,
    )

    # URL fixtures register forms globally; preserve the registry object imported
    # by checks and inventory tests while removing this fixture's registrations.
    snapshot = dict(_REGISTRY)

    def restore_registry():
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(snapshot)

    request.addfinalizer(restore_registry)
    vs = ViewSet(model=Author, name="cancel_state_" + uuid.uuid4().hex[:8])

    class AuthorFilter(FilterSet):
        class Meta:
            model = Author
            fields = ["last_name"]

    classes = {}
    for key, parent, filtered in (
        ("list", AuthorListView, False),
        ("card", AuthorCardListView, False),
        ("filtered", AuthorListView, True),
        ("filtered_card", AuthorCardListView, True),
        ("archive", AuthorListView, True),
    ):
        bases = (ListViewTableFilterMixin, parent) if filtered else (parent,)
        classes[key] = type(
            "State" + key.title(),
            bases,
            {
                "cv_viewset": vs,
                "cv_key": key,
                "cv_path": key,
                "cv_header_template_code": "Authors",
                "cv_header_template": None,
                "filterset_class": AuthorFilter if filtered else None,
                "formhelper_class": ListViewFilterFormHelper if filtered else None,
                "paginate_by": 1,
                "cv_order_fields": ["last_name"],
            },
        )
    update = type("StateUpdate", (AuthorUpdateView,), {"cv_viewset": vs})
    type("StateDetail", (AuthorDetailView,), {"cv_viewset": vs})
    type("StateDelete", (AuthorDeleteView,), {"cv_viewset": vs})
    module = type("StateURLs", (), {"urlpatterns": [*vs.urlpatterns, *urlpatterns]})
    with override_settings(ROOT_URLCONF=module):
        yield vs, classes, update


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["list", "card", "filtered", "filtered_card", "archive"])
@pytest.mark.parametrize("persistence", [True, False])
@pytest.mark.parametrize("query", ["", "last_name=Adams&x=a&x=&x=a&order=last_name&page=1"])
def test_list_family_returns_clean_state(
    state_routes,
    client_user_author_origin,
    author_douglas_adams,
    author_terry_pratchett,
    key,
    persistence,
    query,
    monkeypatch,
):
    from django.urls import reverse
    from lxml import html

    from tests.test1.test_cancel_navigation import emitted_link, rendered_cancel

    vs, classes, update = state_routes
    monkeypatch.setattr(classes[key], "cv_filter_persistence", persistence, raising=False)
    monkeypatch.setattr(update, "cv_cancel_keys", [key])
    path = reverse(vs.get_router_name(key))
    client = client_user_author_origin
    source = client.get(path + ("?" + query if query else ""))
    assert source.status_code == 200
    obj = source.context["object_list"][0]
    link = emitted_link(source, reverse(vs.get_router_name("update"), kwargs={"pk": obj.pk}))
    form = client.get(link)
    cancel = rendered_cancel(form)
    assert urlsplit(cancel).path == path
    assert parse_qs(urlsplit(cancel).query)[navigation_params()[2]] == ["1"]
    # Simulate the later tab's memory without changing the earlier open form.
    session = client.session
    source.context["view"].request.session = session
    with SessionData.from_view(source.context["view"]) as sd:
        sd["filter_query_string"] = "last_name=Pratchett"
        sd["filter_expanded"] = True
    session.save()
    remembered = deepcopy(dict(client.session))
    returned = client.get(cancel)
    assert returned.status_code == 200
    view = returned.context["view"]
    assert QueryDict(query) == view.request.GET
    assert view.request.META["QUERY_STRING"] == QueryDict(query).urlencode()
    document = html.fromstring(returned.content)
    for name in navigation_params():
        assert not document.xpath("//input[@type='hidden'][@name=$name]", name=name)
    for anchor in document.xpath("//a[@href]"):
        params = parse_qs(urlsplit(anchor.get("href")).query)
        if navigation_params()[1] in params:
            data = signing.Signer(salt=SALT).unsign_object(params[navigation_params()[1]][0])
            assert not set(navigation_params()) & set(parse_qs(data["query"]))
        else:
            assert not set(navigation_params()) & params.keys()
    second_link = emitted_link(returned, reverse(vs.get_router_name("update"), kwargs={"pk": obj.pk}))
    assert second_link == link, "Repeated navigation must not grow its capture"
    if persistence and key in {"filtered", "filtered_card", "archive"}:
        state = SessionData.from_view(view)
        assert state.get("filter_query_string", "") == QueryDict(query).urlencode()
        assert state.get("filter_expanded") is True
        bare = client.get(path)
        assert bare.status_code == (302 if query else 200)
        if query:
            assert bare["Location"] == path + "?" + QueryDict(query).urlencode()
        else:
            assert bare.context["paginator"].count == 2
    else:
        assert dict(client.session) == remembered
    # Order and pagination controls are plain list requests with no transport recursion.
    controls = client.get(path + "?order=last_name&page=1")
    assert controls.status_code == 200
    assert not set(navigation_params()) & controls.context["view"].request.GET.keys()


@pytest.mark.django_db
def test_auto_does_not_admit_custom_list_key(state_routes, client_user_author_origin, author_douglas_adams):
    from django.urls import reverse

    from tests.test1.test_cancel_navigation import emitted_link, rendered_cancel

    vs, _, _ = state_routes
    response = client_user_author_origin.get(reverse(vs.get_router_name("archive")))
    path = reverse(vs.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})
    link = emitted_link(response, path)
    assert link == path
    assert rendered_cancel(client_user_author_origin.get(link)) == reverse(vs.get_router_name("list"))


@pytest.mark.django_db
def test_invalid_capture_never_borrows_success_origin(
    client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch
):
    from django.urls import reverse

    from tests.test1.test_cancel_navigation import emitted_link, rendered_cancel

    cls = cv_author_origin.get_view_class("update")
    monkeypatch.setattr(cls, "cv_success_keys", ["detail"])
    origin = reverse(cv_author_origin.get_router_name("detail"), kwargs={"pk": author_douglas_adams.pk})
    target = reverse(cv_author_origin.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})
    response = client_user_author_origin.get(origin + "?x=" + "a" * 8200)
    link = emitted_link(response, target)
    assert parse_qs(urlsplit(link).query) == {"cv_from": ["detail"], "cv_from_cancel": ["invalid"]}
    form = client_user_author_origin.get(link)
    assert rendered_cancel(form) == reverse(cv_author_origin.get_router_name("card"))
    assert form.context["view"].get_success_url() == origin
    monkeypatch.setattr(cls, "cv_success_keys", None)
    response = client_user_author_origin.get(origin + "?x=" + "a" * 8200)
    assert emitted_link(response, target) == target


@pytest.mark.django_db
def test_open_forms_bind_distinct_current_parents(
    client, user_author_origin, cv_book, book_hitchhiker, book_other_publisher, monkeypatch
):
    from django.urls import path, reverse
    from django_filters import FilterSet

    from crud_views.lib.views.list import ListViewFilterFormHelper
    from crud_views.lib.views.mixins import ListViewTableFilterMixin
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.models import Book
    from tests.test1.app.urls import urlpatterns
    from tests.test1.app.views import BookListView
    from tests.test1.test_cancel_navigation import emitted_link, rendered_cancel

    for permission in ("view", "change"):
        user_viewset_permission(user_author_origin, cv_book, permission)
    client.force_login(user_author_origin)

    class BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = ["title"]

    class FilteredBooks(ListViewTableFilterMixin, BookListView):
        cv_viewset = None
        filterset_class = BookFilter
        formhelper_class = ListViewFilterFormHelper

    monkeypatch.setattr(FilteredBooks, "cv_viewset", cv_book)
    parent_key = cv_book.get_parent_url_args()[0]
    root = type(
        "NestedURLs",
        (),
        {
            "urlpatterns": [
                path(f"publisher/<int:{parent_key}>/book/", FilteredBooks.as_view()),
                *urlpatterns,
            ]
        },
    )
    captures = []
    before = list(Book.objects.order_by("pk").values())
    with override_settings(ROOT_URLCONF=root):
        for book in (book_hitchhiker, book_other_publisher):
            kwargs = {parent_key: book.publisher_id}
            source = client.get(reverse(cv_book.get_router_name("list"), kwargs=kwargs) + "?x=equal&x=")
            target = reverse(cv_book.get_router_name("update"), kwargs={**kwargs, "pk": book.pk})
            form_link = emitted_link(source, target)
            captures.append((form_link, rendered_cancel(client.get(form_link)), kwargs))
        assert (
            parse_qs(urlsplit(captures[0][0]).query)["cv_from_cancel"]
            != parse_qs(urlsplit(captures[1][0]).query)["cv_from_cancel"]
        )
        client.get(reverse(cv_book.get_router_name("list"), kwargs=captures[1][2]) + "?title=other-tab")
        for _, cancel, kwargs in captures:
            returned = client.get(cancel)
            assert returned.status_code == 200
            assert returned.context["view"].kwargs == kwargs
            assert returned.context["view"].request.GET.getlist("x") == ["equal", ""]
            assert all(book.publisher_id == kwargs[parent_key] for book in returned.context["object_list"])
        token = parse_qs(urlsplit(captures[0][0]).query)["cv_from_cancel"][0]
        replay = client.get(urlsplit(captures[1][0]).path, {"cv_from": "list", "cv_from_cancel": token})
        assert rendered_cancel(replay) == reverse(cv_book.get_router_name("list"), kwargs=captures[1][2])
    assert list(Book.objects.order_by("pk").values()) == before
