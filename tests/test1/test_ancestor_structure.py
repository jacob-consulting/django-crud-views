"""Ancestry structure of nested ViewSets: bounded metadata walks, forward references and declared relationships.

Every structural failure is an ``ImproperlyConfigured`` naming the affected ViewSet, raised before any database access,
and the completed-registry system check reports it as ``crud_views.E320`` (a Resource parent stays ``viewset.E261``).
"""

import signal
from contextlib import contextmanager

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse

from crud_views.checks import check_ancestry
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.resource import Resource
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import DetailView, ListView
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views.lib.viewset.ancestry import validate_relationships, walk_ancestors
from tests.test1.ancestor_cases import ancestor_scope
from tests.test1.app.models import Book, BookNote, Genre, Publisher


class _WalkDidNotTerminate(Exception):
    pass


@contextmanager
def bounded(seconds: float = 5.0):
    """Interrupt an unbounded walk (a pure Python loop) instead of hanging the worker."""

    def interrupt(signum, frame):
        raise _WalkDidNotTerminate(f"ancestry walk did not terminate within {seconds}s")

    previous = signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def ancestry_messages(*names: str) -> list:
    """crud_views.E320/E321 messages of the completed-registry check that mention one of ``names``."""
    return [message for message in check_ancestry() if any(name in message.msg for name in names)]


def broken_chain(scope, shape: str) -> tuple[ViewSet, str]:
    """A nested ViewSet whose ancestry is a self-cycle, a two-node cycle or names a missing parent.

    Returns the requested ViewSet and the name every error must mention.
    """
    if shape == "self":
        name = scope.name("ancself")
        viewset = scope.viewset(model=Book, name=name, parent=ParentViewSet(name=name, attribute="publisher"))
        affected = name
    elif shape == "pair":
        first, second = scope.name("ancpaira"), scope.name("ancpairb")
        viewset = scope.viewset(model=Book, name=first, parent=ParentViewSet(name=second, attribute="publisher"))
        scope.viewset(model=Publisher, name=second, parent=ParentViewSet(name=first, attribute="books"))
        affected = second
    else:
        missing = scope.name("ancmissing")
        viewset = scope.viewset(
            model=Book, name=scope.name("ancorphan"), parent=ParentViewSet(name=missing, attribute="publisher")
        )
        affected = missing
    scope.view(ListView, viewset)
    return viewset, affected


SHAPES = ["self", "pair", "missing"]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", SHAPES)
def test_url_walk_rejects_cycles_and_missing_parent(shape, django_assert_num_queries):
    with ancestor_scope() as scope:
        viewset, affected = broken_chain(scope, shape)
        scope.mount([viewset])
        with bounded(), django_assert_num_queries(0):
            with pytest.raises(ImproperlyConfigured, match=affected) as walk_error:
                walk_ancestors(viewset)
            with pytest.raises(ImproperlyConfigured, match=affected):
                viewset.urlpatterns  # noqa: B018 - the URL-building walk itself
            # URLconf import: Django reads the module's urlpatterns while resolving
            with pytest.raises(ImproperlyConfigured, match=affected):
                reverse(viewset.get_router_name("list"), kwargs={"x_pk": 1})
        # the message names the requested ViewSet and the chain it walked
        assert viewset.name in str(walk_error.value)
        if shape != "missing":
            assert "cycle" in str(walk_error.value)


@pytest.mark.django_db
def test_child_before_parent_resolves_when_urls_needed(django_assert_num_queries):
    with ancestor_scope() as scope:
        parent_name = scope.name("ancfwdpub")
        child = scope.viewset(
            model=Book, name=scope.name("ancfwdbook"), parent=ParentViewSet(name=parent_name, attribute="publisher")
        )
        scope.view(ListView, child)
        scope.view(DetailView, child)
        # the parent does not exist yet: construction succeeded, the walk names the missing reference
        with pytest.raises(ImproperlyConfigured, match=parent_name):
            walk_ancestors(child)

        parent = scope.viewset(model=Publisher, name=parent_name)
        scope.view(ListView, parent)
        scope.mount([child, parent])

        with django_assert_num_queries(0):
            assert walk_ancestors(child) == (child.parent,)
            validate_relationships(child)
            assert reverse(child.get_router_name("list"), kwargs={f"{parent_name}_pk": 7}) == (
                f"/{parent_name}/7/{child.name}/"
            )
            assert reverse(child.get_router_name("detail"), kwargs={f"{parent_name}_pk": 7, "pk": 3}) == (
                f"/{parent_name}/7/{child.name}/3/detail/"
            )
        assert child.get_parent_url_args() == [f"{parent_name}_pk"]
        assert child.get_parent_url_args(first_only=True) == f"{parent_name}_pk"
        assert child.get_parent_attributes() == ["publisher"]
        assert child.get_parent_attributes(first_only=True) == "publisher"
        assert child.get_path_parent() == rf"{parent_name}/(?P<{parent_name}_pk>\d+)/"
        assert parent.get_parent_url_args() == []
        assert parent.get_path_parent() == ""


@pytest.mark.django_db
def test_walk_is_nearest_first_and_preserves_existing_ordering(django_assert_num_queries):
    with ancestor_scope() as scope:
        publisher = scope.viewset(model=Publisher, name=scope.name("ancordpub"))
        book = scope.viewset(
            model=Book,
            name=scope.name("ancordbook"),
            parent=ParentViewSet(name=publisher.name, attribute="publisher", pk_name="pub_pk"),
        )
        note = scope.viewset(
            model=BookNote, name=scope.name("ancordnote"), parent=ParentViewSet(name=book.name, attribute="book")
        )
        with django_assert_num_queries(0):
            assert walk_ancestors(note) == (note.parent, book.parent)
            assert walk_ancestors(publisher) == ()
        assert note.get_parent_url_args() == [f"{book.name}_pk", "pub_pk"]
        assert note.get_parent_attributes() == ["book", "publisher"]
        assert note.get_path_parent() == (rf"{publisher.name}/(?P<pub_pk>\d+)/{book.name}/(?P<{book.name}_pk>\d+)/")


class _FakeView:
    """The minimal view surface ``ViewSet.get_queryset`` and the breadcrumb walk read."""

    def __init__(self, viewset):
        self.cv_viewset = viewset
        self.kwargs = {}


@pytest.mark.django_db
@pytest.mark.parametrize("shape", SHAPES)
def test_all_supported_walks_terminate(shape, django_assert_num_queries):
    with ancestor_scope() as scope:
        viewset, affected = broken_chain(scope, shape)
        # a subclass without cv_viewset in its body is not registered; it adds the breadcrumb walk
        list_view = type("BreadcrumbList", (CrudViewBreadcrumbMixin, viewset.get_view_class("list")), {})()
        list_view.kwargs = {}
        walks = {
            "url args": viewset.get_parent_url_args,
            "first url arg": lambda: viewset.get_parent_url_args(first_only=True),
            "attributes": viewset.get_parent_attributes,
            "first attribute": lambda: viewset.get_parent_attributes(first_only=True),
            "path": viewset.get_path_parent,
            "queryset": lambda: viewset.get_queryset(view=_FakeView(viewset)),
            "urlpatterns": lambda: viewset.urlpatterns,
            "breadcrumb": lambda: list_view._cv_breadcrumb_ancestors(context=None),
            "relationships": lambda: validate_relationships(viewset),
        }
        for label, walk in walks.items():
            with bounded(), django_assert_num_queries(0), pytest.raises(ImproperlyConfigured, match=affected):
                walk()
                pytest.fail(f"{label} accepted a broken ancestry")

        with bounded(), django_assert_num_queries(0):
            messages = ancestry_messages(viewset.name)
        # every ViewSet on a cycle reports it; the requested ViewSet's message names the affected one
        assert {message.id for message in messages} == {"crud_views.E320"}
        assert len(messages) == (2 if shape == "pair" else 1)
        assert any(affected in message.msg for message in messages)

        # the existing ViewSet checks report diagnostics instead of crashing on the unresolved parent
        with bounded():
            checks = [message for check in viewset.checks() for message in check.messages()]
        assert all(message.id != "viewset.E261" for message in checks)


class _AncFile(Resource):
    key: str

    class Meta:
        pk_field = "key"

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return []


def _relationship(scope, case: str):
    """Build parent → child for ``case``; return (child, ancestor that has to be named on failure)."""
    publisher_name, genre_name = scope.name("ancrelpub"), scope.name("ancrelgenre")
    parent_model, parent_name = Publisher, publisher_name
    child_model, child_kwargs = Book, {"attribute": "publisher"}
    if case == "fk":
        pass
    elif case == "fk explicit url name":
        child_kwargs = {"attribute": "publisher", "pk_name": "publisher_pk"}
    elif case == "m2m forward":
        child_model, child_kwargs = Genre, {"attribute": "publishers", "many_to_many_through_attribute": "genres"}
    elif case == "m2m reverse":
        parent_model, parent_name = Genre, genre_name
        child_model, child_kwargs = Publisher, {"attribute": "genres", "many_to_many_through_attribute": "publishers"}
    elif case == "resource leaf":
        child_model, child_kwargs = _AncFile, {}
    elif case == "wrong target model":
        child_model, child_kwargs = BookNote, {"attribute": "book"}
    elif case == "missing field":
        child_kwargs = {}  # defaults to the (unique) parent name, which is no field of Book
    elif case == "plain field":
        child_kwargs = {"attribute": "title"}
    elif case == "reverse fk":
        parent_model = Book
        child_model, child_kwargs = Publisher, {"attribute": "books"}
    elif case == "m2m reverse attribute only":
        parent_model, parent_name = Genre, genre_name
        child_model, child_kwargs = Publisher, {"attribute": "genres"}
    elif case == "m2m wrong target model":
        parent_model = Book
        child_model, child_kwargs = Genre, {"attribute": "publishers"}
    elif case == "m2m attribute only":
        child_model, child_kwargs = Genre, {"attribute": "publishers"}
    elif case == "m2m wrong through attribute":
        child_model, child_kwargs = Genre, {"attribute": "publishers", "many_to_many_through_attribute": "books"}
    elif case == "m2m unknown through attribute":
        child_model, child_kwargs = Genre, {"attribute": "publishers", "many_to_many_through_attribute": "nothing"}
    elif case == "fk with through attribute":
        child_kwargs = {"attribute": "publisher", "many_to_many_through_attribute": "books"}
    elif case == "resource ancestor":
        parent_model = _AncFile
    else:  # pragma: no cover - guard against typos in the parametrization
        raise AssertionError(case)

    parent_kwargs = {"resource_permissions": None} if parent_model is _AncFile else {}
    scope.viewset(model=parent_model, name=parent_name, **parent_kwargs)
    child_extra = {"resource_permissions": None} if child_model is _AncFile else {}
    child = scope.viewset(
        model=child_model,
        name=scope.name("ancrelchild"),
        parent=ParentViewSet(name=parent_name, **child_kwargs),
        **child_extra,
    )
    return child


VALID_RELATIONSHIPS = [
    "fk",
    "fk explicit url name",
    "m2m forward",
    "m2m reverse",
    "m2m attribute only",
    "m2m reverse attribute only",
    "resource leaf",
]
INVALID_RELATIONSHIPS = [
    "wrong target model",
    "m2m wrong target model",
    "missing field",
    "plain field",
    "reverse fk",
    "m2m wrong through attribute",
    "m2m unknown through attribute",
    "fk with through attribute",
]


@pytest.mark.django_db
@pytest.mark.parametrize("case", VALID_RELATIONSHIPS + INVALID_RELATIONSHIPS + ["resource ancestor"])
def test_declared_relationships_are_validated(case, django_assert_num_queries):
    with ancestor_scope() as scope:
        child = _relationship(scope, case)
        with django_assert_num_queries(0):
            if case in VALID_RELATIONSHIPS:
                validate_relationships(child)
            else:
                with pytest.raises(ImproperlyConfigured, match=child.name):
                    validate_relationships(child)
            messages = ancestry_messages(child.name)
        e261 = [m for check in child.checks() for m in check.messages() if m.id == "viewset.E261"]
        if case in VALID_RELATIONSHIPS:
            assert messages == []
            assert e261 == []
        elif case == "resource ancestor":
            # reported once, by the existing Resource-parent check
            assert messages == []
            assert len(e261) == 1
        else:
            assert [message.id for message in messages] == ["crud_views.E320"]
            assert e261 == []


@pytest.mark.django_db
def test_deeper_relationship_errors_are_reported_once_by_the_owning_viewset():
    with ancestor_scope() as scope:
        publisher = scope.viewset(model=Publisher, name=scope.name("ancdeeppub"))
        book = scope.viewset(
            model=Book, name=scope.name("ancdeepbook"), parent=ParentViewSet(name=publisher.name, attribute="title")
        )
        note = scope.viewset(
            model=BookNote, name=scope.name("ancdeepnote"), parent=ParentViewSet(name=book.name, attribute="book")
        )
        # the leaf's runtime validation covers the whole chain
        with pytest.raises(ImproperlyConfigured, match=book.name):
            validate_relationships(note)
        # the check reports the broken edge once, at the ViewSet declaring it
        messages = ancestry_messages(book.name, note.name)
        assert [message.id for message in messages] == ["crud_views.E320"]
        assert f"{book.name!r}" in messages[0].msg
        assert f"{note.name!r}" not in messages[0].msg


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE", "yes"),
        ("CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS", {"nearest": "view"}),
        ("CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS", {"nearest": "change", "higher": None}),
    ],
)
def test_global_ancestor_settings_check(setting, value, django_assert_num_queries):
    with django_assert_num_queries(0):
        assert [m for m in crud_views_settings.check_messages if m.id == "crud_views.E322"] == []
        with override_settings(**{setting: value}):
            messages = [m for m in crud_views_settings.check_messages if m.id == "crud_views.E322"]
    assert len(messages) == 1
    assert setting in messages[0].msg
