"""Scoped ancestor resolution: ViewSet querysets with the actual child context, relationships, reached failures in
order, structural-parent identity reuse and the default-database boundary of nested requests.
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from crud_views.lib.viewset import AncestorPolicy
from tests.test1.ancestor_cases import EVENTS, TracedViewSet, ancestor_scope, traced_chain
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_requests import (
    LOGIN,
    TWO,
    FormTrace,
    LocalTrace,
    client_for,
    data,
    define,
    make_user,
)

CONTEXT: list[dict] = []
STATE_OBJECTS: list = []


@pytest.fixture(autouse=True)
def events():
    EVENTS.clear()
    CONTEXT.clear()
    STATE_OBJECTS.clear()
    yield EVENTS
    EVENTS.clear()


@pytest.fixture
def scope():
    with ancestor_scope() as scope:
        yield scope


class HiddenExcludedViewSet(TracedViewSet):
    """Soft-delete-like scope: rows titled "hidden" are invisible through this ViewSet."""

    def get_queryset(self, view):
        return super().get_queryset(view).exclude(title="hidden")


class UnrelatedViewSet(TracedViewSet):
    """A queryset override that drops the parent filtering of the default ViewSet queryset."""

    def get_queryset(self, view):
        super().get_queryset(view)
        return Book.objects.all()


class ContextViewSet(TracedViewSet):
    """Captures the view, request and URL kwargs the ancestor queryset receives."""

    def get_queryset(self, view):
        CONTEXT.append(
            {"view": view, "request": view.request, "kwargs": dict(view.kwargs), "key": view.cv_key, "self": self}
        )
        return super().get_queryset(view)


class ShardViewSet(TracedViewSet):
    def get_queryset(self, view):
        return super().get_queryset(view).using("shard")


class DefaultViewSet(TracedViewSet):
    def get_queryset(self, view):
        return super().get_queryset(view).using("default")


def book_selects(ctx) -> int:
    return sum(1 for query in ctx.captured_queries if 'FROM "app_book"' in query["sql"])


def detail_routes(scope, inner_class=None):
    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, TWO, viewset_classes={1: inner_class} if inner_class else None)
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    return routes


@pytest.mark.django_db
def test_scope_and_relationship_failures_are_reached_in_order(scope, events):
    from crud_views.lib.views import DetailView

    routes = detail_routes(scope)
    publisher, book, note, _attachment, other_book = data()
    client = client_for(make_user("reader", ["view_publisher", "view_book"]))

    events.clear()
    assert client.get(routes.url("detail", [publisher, Book(pk=999999)], obj=note)).status_code == 404
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]

    events.clear()
    assert client.get(routes.url("detail", [publisher, other_book], obj=note)).status_code == 404
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]

    events.clear()
    assert client.get(routes.url("detail", [Publisher(pk=999999), book], obj=note)).status_code == 404
    assert events == ["outer_queryset"]

    # the actor decision precedes every lookup
    events.clear()
    url = routes.url("detail", [Publisher(pk=999999), book], obj=note)
    response = Client().get(url)
    assert (response.status_code, response["Location"], events) == (302, f"{LOGIN}?next={url}", [])

    # an ancestor endpoint's own queryset override is never consulted
    class AncestorEndpointDetail(DetailView):
        cv_viewset = routes.viewsets[1]

        def get_queryset(self):
            EVENTS.append("ancestor_endpoint")
            return super().get_queryset()

    events.clear()
    assert client.get(routes.url("detail", [publisher, book], obj=note)).status_code == 200
    assert events == ["outer_queryset", "outer_gate", "inner_queryset", "inner_gate", "child"]


@pytest.mark.django_db
def test_excluded_ancestor_is_404_without_unfiltered_retry(scope, events):
    routes = detail_routes(scope, HiddenExcludedViewSet)
    publisher, book, note, *_ = data()
    Book.objects.filter(pk=book.pk).update(title="hidden")
    client = client_for(make_user("granted", ["view_publisher", "view_book"]))

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(routes.url("detail", [publisher, book], obj=note))

    assert response.status_code == 404
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]
    assert book_selects(ctx) == 1


@pytest.mark.django_db
def test_relationship_is_validated_when_the_queryset_drops_it(scope, events):
    routes = detail_routes(scope, UnrelatedViewSet)
    publisher, book, note, _attachment, other_book = data()
    client = client_for(make_user("granted", ["view_publisher", "view_book"]))

    assert client.get(routes.url("detail", [publisher, other_book], obj=note)).status_code == 404
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]
    events.clear()
    assert client.get(routes.url("detail", [publisher, book], obj=note)).status_code == 200


class AllPublishersViewSet(TracedViewSet):
    """Drops the M2M membership filter of the default queryset."""

    def get_queryset(self, view):
        super().get_queryset(view)
        return Publisher.objects.all()


@pytest.mark.django_db
@pytest.mark.parametrize("inner_class", [TracedViewSet, AllPublishersViewSet], ids=["default", "unfiltered"])
def test_m2m_membership_is_validated(scope, events, inner_class):
    from crud_views.lib.views import DetailView
    from tests.test1.app.models import Genre

    # Genre → Publisher through the reverse many-to-many accessor "genres" → Book
    spec = ((Genre, None, "outer"), (Publisher, "genres", "inner"), (Book, "publisher", "child"))
    routes = traced_chain(scope, spec, viewset_classes={1: inner_class})
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    publisher, book, *_ = data()
    member = Genre.objects.create(name="Member")
    member.publishers.add(publisher)
    stranger = Genre.objects.create(name="Stranger")
    client = client_for(make_user("reader", ["view_genre", "view_publisher"]))

    assert client.get(routes.url("detail", [member, publisher], obj=book)).status_code == 200
    events.clear()
    assert client.get(routes.url("detail", [stranger, publisher], obj=book)).status_code == 404
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]


@pytest.mark.django_db
def test_actual_child_context_and_parent_identity(scope, events):
    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, TWO, viewset_classes={1: ContextViewSet})
    captured = {}

    class ContextDetail(DetailView):
        def get_object(self, queryset=None):
            captured["view"] = self
            captured["kwargs"] = dict(self.kwargs)
            return super().get_object(queryset)

    define(scope, routes.endpoint, ContextDetail)
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()
    url = routes.url("detail", [publisher, book], obj=note)

    assert client_for(make_user("reader", ["view_publisher", "view_book"])).get(url).status_code == 200

    (context,) = CONTEXT
    assert context["self"] is routes.viewsets[1]
    assert context["view"] is captured["view"]
    assert context["request"] is captured["view"].request
    assert context["kwargs"] == captured["kwargs"]
    assert context["kwargs"]["pk"] == str(note.pk)
    assert context["key"] == "detail"
    assert captured["view"].model is BookNote


@pytest.mark.django_db
def test_none_immediate_parent_is_reused_by_create(scope, events, django_capture_on_commit_callbacks):
    from crud_views.lib.views import CreateViewParentMixin, CreateViewPermissionRequired, ListView

    routes = traced_chain(scope, TWO, policies={1: AncestorPolicy(provider="none")})
    seen = {}

    class IdentityCreate(FormTrace, CreateViewParentMixin, CreateViewPermissionRequired):
        fields = ["note"]

        @classmethod
        def cv_action_enabled(cls, user, obj=None):
            STATE_OBJECTS.append(obj)
            return True

        def cv_form_valid(self, context):
            seen["helper"] = self.cv_get_parent_object()
            seen["resolved"] = self._cv_ancestor_objects[routes.viewsets[1].name]
            super().cv_form_valid(context)
            seen["attached"] = context["form"].instance.book

    define(scope, routes.endpoint, ListView)
    define(scope, routes.endpoint, IdentityCreate)
    scope.mount([routes.endpoint])
    publisher, book, *_ = data()
    client = client_for(make_user("creator", ["change_publisher", "add_booknote"]))

    with CaptureQueriesContext(connection) as ctx, django_capture_on_commit_callbacks(execute=True):
        response = client.post(routes.url("create", [publisher, book]), {"note": "Created"})

    assert response.status_code == 302
    assert book_selects(ctx) == 1
    resolved = seen["resolved"]
    assert (type(resolved), resolved.pk, resolved._state.db) == (Book, book.pk, "default")
    assert seen["helper"] is resolved
    assert seen["attached"] is resolved
    assert [resolved] == STATE_OBJECTS
    assert BookNote.objects.get(note="Created").book_id == book.pk


@pytest.mark.django_db
def test_parent_helper_outside_a_request_keeps_its_own_lookup(scope):
    from django.http import Http404
    from django.test import RequestFactory

    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, TWO)
    view_class = define(scope, routes.endpoint, DetailView)
    publisher, book, *_ = data()
    pk_names = routes.endpoint.get_parent_url_args()
    view = view_class()
    view.setup(RequestFactory().get("/"), **{pk_names[0]: book.pk, pk_names[1]: publisher.pk, "pk": 1})

    with CaptureQueriesContext(connection) as ctx:
        assert view.cv_get_parent_object() == book
    assert book_selects(ctx) == 1

    view.kwargs[pk_names[0]] = 999999
    with pytest.raises(Http404):
        view.cv_get_parent_object()


@pytest.mark.django_db
@pytest.mark.parametrize("level", [0, 1])
def test_reached_nondefault_ancestor_database_is_a_configuration_error(scope, events, level):
    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, TWO, viewset_classes={level: ShardViewSet})
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()
    client = client_for(make_user("reader", ["view_publisher", "view_book"]))

    with pytest.raises(ImproperlyConfigured, match="'shard'"):
        client.get(routes.url("detail", [publisher, book], obj=note))


@pytest.mark.django_db
def test_explicit_default_database_and_outer_denial_before_a_deeper_database(scope, events):
    from crud_views.lib.views import DetailView

    routes = traced_chain(scope, TWO, viewset_classes={0: DefaultViewSet, 1: ShardViewSet})
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()
    url = routes.url("detail", [publisher, book], obj=note)

    # the outer gate denies before the deeper nondefault selection is reached
    assert client_for(make_user("outsider")).get(url).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]


@pytest.mark.django_db
def test_reached_nondefault_child_database_is_a_configuration_error(scope, events):
    from crud_views.lib.views import DetailView, ListView

    routes = traced_chain(scope, TWO, viewset_classes={2: ShardViewSet})
    define(scope, routes.endpoint, ListView)
    define(scope, routes.endpoint, DetailView)
    scope.mount([routes.endpoint])
    publisher, book, *_ = data()
    client = client_for(make_user("reader", ["view_publisher", "view_book"]))

    with pytest.raises(ImproperlyConfigured, match="'shard'"):
        client.get(routes.url("list", [publisher, book]))


@pytest.mark.django_db
def test_local_permission_still_follows_scoped_ancestry(scope, events):
    from crud_views.lib.views import DetailViewPermissionRequired

    routes = traced_chain(scope, TWO, viewset_classes={1: HiddenExcludedViewSet})
    define(scope, routes.endpoint, (LocalTrace, DetailViewPermissionRequired))
    scope.mount([routes.endpoint])
    publisher, book, note, *_ = data()
    Book.objects.filter(pk=book.pk).update(title="hidden")
    client = client_for(make_user("granted", ["view_publisher", "view_book", "view_booknote"]))

    assert client.get(routes.url("detail", [publisher, book], obj=note)).status_code == 404
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]
