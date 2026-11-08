"""Mutation boundary: ancestor authorization covers the URL path only.

Publisher A and B are Guardian ancestors; the actor holds the object grant on A only, and every evaluated ancestor
gate records the parent it checked. Shared rows, an editable parent FK and deletion keep their ordinary Django
semantics: no destination-parent gate, no FK pinning, no unlinking. Applications restrict such effects themselves
(here: an ordinary form that omits the FK). Every test runs in full cascade and nearest-only mode.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from crud_views.lib.viewset import AncestorPolicy, ParentViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.ancestor_cases import FixedTemplateMixin, ancestor_scope
from tests.test1.app.models import Book, Genre, Publisher

CHECKED_PARENTS: list = []
MODES = pytest.mark.parametrize("cascade", [True, False], ids=["cascade", "nearest_only"])


class RecordingPublisherViewSet(GuardianViewSet):
    """Guardian ancestor recording the pk of every parent whose gate it evaluates."""

    def _ancestor_has_permission(self, user, obj, permission):
        CHECKED_PARENTS.append(obj.pk)
        return super()._ancestor_has_permission(user, obj, permission)


@pytest.fixture(autouse=True)
def checked():
    CHECKED_PARENTS.clear()
    yield CHECKED_PARENTS
    CHECKED_PARENTS.clear()


@pytest.fixture
def scope():
    with ancestor_scope() as scope:
        yield scope


def define(scope, viewset, bases, key=None, **attrs):
    bases = bases if isinstance(bases, tuple) else (bases,)
    if key is not None:
        attrs.update(cv_key=key, cv_path=key)
    name = f"{bases[-1].__name__}{key or ''}{scope.sfx}"
    return type(name, (FixedTemplateMixin, *bases), {"cv_viewset": viewset, "__module__": __name__, **attrs})


def chain(scope, model, attribute, cascade, prefix, create=None, **parent_kwargs):
    """RecordingPublisher → ``model`` endpoint with list/create/update/delete views; mounted."""
    from crud_views.lib.views import CreateView, CreateViewParentMixin, DeleteView, ListView, UpdateView

    pub_vs = scope.viewset(RecordingPublisherViewSet, model=Publisher, name=scope.name(f"{prefix}pub"))
    child_vs = scope.viewset(
        model=model,
        name=scope.name(f"{prefix}child"),
        parent=ParentViewSet(name=pub_vs.name, attribute=attribute, **parent_kwargs),
        ancestor_policy=AncestorPolicy(cascade=cascade),
    )
    fields = ["name"] if model is Genre else ["title", "publisher"]
    define(scope, child_vs, ListView)
    define(scope, child_vs, create or (CreateViewParentMixin, CreateView), fields=fields[:1])
    define(scope, child_vs, UpdateView, fields=fields)
    define(scope, child_vs, DeleteView)
    return child_vs


def url(viewset, key, parent, obj=None):
    from django.urls import reverse

    kwargs = {viewset.parent.get_pk_name(): parent.pk}
    if obj is not None:
        kwargs["pk"] = obj.pk
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def actor_for(a):
    """Object ``change`` on Publisher A only (the Write pair's nearest requirement); nothing on B."""
    from guardian.shortcuts import assign_perm

    user = User.objects.create_user(username="editor", password="password")
    assign_perm("app.change_publisher", user, a)
    client = Client()
    client.force_login(user)
    return client


def publishers():
    return Publisher.objects.create(name="A"), Publisher.objects.create(name="B")


@pytest.mark.django_db
@MODES
def test_shared_m2m_edit_only_authorizes_url_path(scope, checked, cascade):
    genre_vs = chain(scope, Genre, "publishers", cascade, "m2m", many_to_many_through_attribute="genres")
    scope.mount([genre_vs])
    a, b = publishers()
    shared = Genre.objects.create(name="Shared")
    shared.publishers.add(a, b)
    client = actor_for(a)

    assert client.post(url(genre_vs, "update", a, shared), {"name": "Renamed"}).status_code == 302
    assert checked == [a.pk]
    # the same row changed for B, which was never checked
    assert list(b.genres.values_list("pk", "name")) == [(shared.pk, "Renamed")]

    # through B the actor holds no grant
    checked.clear()
    assert client.post(url(genre_vs, "update", b, shared), {"name": "Through B"}).status_code == 403
    assert checked == [b.pk]
    assert Genre.objects.get(pk=shared.pk).name == "Renamed"


@pytest.mark.django_db
@MODES
def test_valid_editable_fk_move_remains_application_owned(scope, checked, cascade):
    from crud_views.lib.views import UpdateView

    book_vs = chain(scope, Book, "publisher", cascade, "fk")
    # an application-owned restriction: an ordinary form without the parent FK on its own endpoint
    restricted_vs = scope.viewset(
        model=Book,
        name=scope.name("fkrestricted"),
        parent=ParentViewSet(name=book_vs.parent.name, attribute="publisher"),
        ancestor_policy=AncestorPolicy(cascade=cascade),
    )
    define(scope, restricted_vs, UpdateView, fields=["title"], cv_success_key="update")
    scope.mount([book_vs, restricted_vs])
    a, b = publishers()
    book = Book.objects.create(title="Moving", publisher=a)
    client = actor_for(a)

    # the editable FK moves the book to B; membership under A neither authorizes nor gates B
    payload = {"title": "Moved", "publisher": b.pk}
    assert client.post(url(book_vs, "update", a, book), payload).status_code == 302
    assert checked == [a.pk]
    book.refresh_from_db()
    assert (book.publisher_id, book.title) == (b.pk, "Moved")

    # the restricted form ignores a submitted FK: the book stays where it is
    other = Book.objects.create(title="Staying", publisher=a)
    checked.clear()
    response = client.post(url(restricted_vs, "update", a, other), {"title": "Renamed", "publisher": b.pk})
    assert response.status_code == 302
    assert checked == [a.pk]
    other.refresh_from_db()
    assert (other.publisher_id, other.title) == (a.pk, "Renamed")


@pytest.mark.django_db
@MODES
def test_shared_delete_keeps_normal_semantics(scope, checked, cascade):
    genre_vs = chain(scope, Genre, "publishers", cascade, "del", many_to_many_through_attribute="genres")
    scope.mount([genre_vs])
    a, b = publishers()
    shared = Genre.objects.create(name="Shared")
    shared.publishers.add(a, b)
    client = actor_for(a)

    assert client.post(url(genre_vs, "delete", a, shared)).status_code == 302
    assert checked == [a.pk]
    # deleted, not unlinked from A: B lost it too, and no membership row remains
    assert not Genre.objects.filter(pk=shared.pk).exists()
    assert not b.genres.exists()
    assert not Genre.publishers.through.objects.filter(genre_id=shared.pk).exists()


THROUGH: list = []


@pytest.mark.django_db
@MODES
def test_create_attaches_to_the_resolved_structural_parent(scope, checked, cascade):
    from crud_views.lib.views import CreateView, CreateViewParentMixin

    class ThroughCreate(CreateViewParentMixin, CreateView):
        def cv_parent_many_to_many_through_defaults(self, instance, parent_instance, m2m):
            THROUGH.append((parent_instance, self._cv_ancestor_objects[self.cv_viewset.parent.name]))
            return {}

    genre_vs = chain(
        scope, Genre, "publishers", cascade, "cm2m", create=ThroughCreate, many_to_many_through_attribute="genres"
    )
    book_vs = chain(scope, Book, "publisher", cascade, "cfk")
    scope.mount([genre_vs, book_vs])
    a, b = publishers()
    client = actor_for(a)
    THROUGH.clear()

    assert client.post(url(genre_vs, "create", a), {"name": "Created"}).status_code == 302
    created = Genre.objects.get(name="Created")
    assert list(created.publishers.all()) == [a]
    ((parent, resolved),) = THROUGH
    assert parent is resolved and parent.pk == a.pk

    checked.clear()
    assert client.post(url(book_vs, "create", a), {"title": "Fresh"}).status_code == 302
    assert checked == [a.pk]
    assert Book.objects.get(title="Fresh").publisher_id == a.pk
    # no grant on B: no attachment there
    assert client.post(url(book_vs, "create", b), {"title": "Elsewhere"}).status_code == 403
    assert not Book.objects.filter(title="Elsewhere").exists()
