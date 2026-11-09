"""
Phase 06.18 plan 09 Task 2 — the built-in child redirect and its independently authorized destination.

* ``RedirectChildView`` is a Read endpoint by class (D-05, D-31, D-46): it needs no ``actions`` entry, also as an
  ordinary subclass under a renamed key, and an explicit exact entry replaces the Read pair.
* Its ancestry is authorized before its own object lookup and before the redirect URL is built: a denied ancestor
  (403) or a reached missing/mismatched one (404) never reaches the child queryset or ``get_redirect_url``.
* An allowed redirect authorizes nothing downstream: following it is a fresh request that evaluates the
  destination's own operation pair, cascade mode and local gate, and may deny.
* The classification is by class, not by behavior or key: a custom ``ActionView`` (or any other unclassified
  view) that returns a redirect needs an exact entry even under the key ``redirect_child``; without one it is a
  check error (viewset.E268) and a runtime ``ImproperlyConfigured``.

Core (model provider) and Guardian (strict object provider) ancestors, in both cascade modes. Every fixture builds
fresh ViewSets behind a temporary ROOT_URLCONF and restores registry and caches.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.views import generic
from guardian.shortcuts import assign_perm

import tests.test1.project.urls  # noqa: F401 - registers the shared app ViewSets before any registry snapshot
from crud_views.lib.ancestors import _action_declaration_problems
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import ActionView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1 import test_ancestor_authorization as _auth
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

events = _auth.events  # ordered ViewSet queryset / has_perm spy of plan 01

KINDS = ("core", "guardian")
MISSING = 987654


# ── routes ───────────────────────────────────────────────────────────────────


def _view(bases, vs, key=None, **attrs):
    bases = bases if isinstance(bases, tuple) else (bases,)
    attrs = {"cv_viewset": vs, "cv_list_actions": [], "cv_context_actions": [], "__module__": __name__, **attrs}
    if key is not None:
        attrs.update(cv_key=key, cv_path=key)
    return type(f"V_{vs.name}_{key or bases[-1].cv_key}", bases, attrs)


def _build(sfx):
    """Per kind a Publisher → Book chain whose Book ViewSet carries four built-in child redirects, each to its own
    BookNote destination list:

    * ``redirect_child`` → ``note``: default Read destination;
    * ``go`` (a subclass, renamed key) → ``note_higher``: Read pair ``view``/``change`` (Publisher change under full
      cascade only);
    * ``go_change`` → ``note_change``: Read pair ``change``/``view`` (Book change in both modes);
    * ``go_local`` → ``note_local``: default pair, local BookNote ``view`` permission gate.

    Plus a Book ViewSet with an explicit write-like ``redirect_child`` entry, and one whose ``redirect_child`` is a
    custom ``ActionView`` returning a redirect (with a generic redirect view beside it), both without an entry."""
    from crud_views.lib.view import CrudView
    from crud_views.lib.views import ListView, ListViewPermissionRequired, RedirectChildView
    from crud_views_guardian.lib.viewset import GuardianViewSet

    class RenamedRedirect(RedirectChildView):
        """An ordinary subclass under another key stays a built-in Read redirect."""

    ns = SimpleNamespace(chains={}, routed=[])
    letters = sfx.translate(str.maketrans("0123456789", "ghijklmnop"))  # the redirect path segment is [a-z_]+
    for kind in KINDS:
        vs_class = GuardianViewSet if kind == "guardian" else ViewSet
        tag = f"ar{kind[0]}{letters}"
        pub = vs_class(model=Publisher, name=f"{tag}pub")
        _view(ListView, pub)
        chain = SimpleNamespace(pub=pub, books={}, notes={})

        def book(name, policy=None, *, pub=pub, chain=chain, vs_class=vs_class, tag=tag):
            vs = vs_class(
                model=Book,
                name=f"{tag}{name}",
                parent=ParentViewSet(name=pub.name, attribute="publisher"),
                ancestor_policy=policy or AncestorPolicy(),
            )
            chain.books[name] = vs
            return vs

        def note(name, parent, policy=None, *, chain=chain, vs_class=vs_class, tag=tag):
            vs = vs_class(
                model=BookNote,
                name=f"{tag}{name}",
                parent=ParentViewSet(name=parent.name, attribute="book"),
                ancestor_policy=policy or AncestorPolicy(),
            )
            chain.notes[name] = vs
            return vs

        main = book("book")
        destinations = {
            "redirect_child": note("note", main),
            "go": note("note_higher", main, AncestorPolicy(read=AncestorPermissions(nearest="view", higher="change"))),
            "go_change": note(
                "note_change", main, AncestorPolicy(read=AncestorPermissions(nearest="change", higher="view"))
            ),
            "go_local": note("note_local", main),
        }
        for key, destination in destinations.items():
            base = RenamedRedirect if key == "go" else RedirectChildView
            _view(
                base,
                main,
                key=None if key == "redirect_child" else key,
                cv_redirect=destination.name,
                cv_redirect_key="list",
            )
            list_base = ListViewPermissionRequired if key == "go_local" else ListView
            _view(list_base, destination)
        chain.destinations = destinations

        override = book(
            "book_override",
            AncestorPolicy(actions={"redirect_child": AncestorPermissions(nearest="change", higher="view")}),
        )
        override_note = note("note_override", override)
        _view(RedirectChildView, override, cv_redirect=override_note.name, cv_redirect_key="list")
        _view(ListView, override_note)

        custom = book("book_custom")
        custom_note = note("note_custom", custom)
        _view(ListView, custom_note)

        class ActionRedirect(ActionView):
            """A custom action that answers with a redirect: still an unclassified custom endpoint."""

            cv_key = "redirect_child"
            cv_path = "redirect_child"

            def get(self, request, *args, **kwargs):
                return self.post(request, *args, **kwargs)

            def action(self, context):
                return True

            def get_success_url(self):
                return "/"

        _view(ActionRedirect, custom, key="redirect_child")

        class GenericRedirect(CrudView, generic.RedirectView):
            cv_key = "jump"
            cv_path = "jump"
            cv_object = False
            cv_pk = False
            url = "/"

        _view(GenericRedirect, custom, key="jump")
        ns.chains[kind] = chain
        ns.routed += [pub, *chain.books.values(), *chain.notes.values()]
    return ns, ns.routed


@pytest.fixture
def routes():
    with isolated_routes(_build) as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Hitchhiker", publisher=penguin)
    foreign = Book.objects.create(title="Foreign", publisher=other)
    BookNote.objects.create(book=book, note="note")
    return SimpleNamespace(penguin=penguin, other=other, book=book, foreign=foreign)


@pytest.fixture(params=[True, False], ids=["full", "nearest"])
def cascade(request, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "ancestor_permission_cascade", request.param)
    return request.param


def _redirect_url(chain, key="redirect_child", *, book="book", publisher_pk, book_pk):
    vs = chain.books[book]
    destination = vs.get_view_class(key).cv_redirect
    return _url(
        vs,
        key,
        **{f"{chain.pub.name}_pk": publisher_pk, "pk": book_pk, "redirect": destination, "redirect_key": "list"},
    )


def _destination_url(chain, note, world):
    vs = chain.notes[note]
    return _url(vs, "list", **{f"{chain.pub.name}_pk": world.penguin.pk, f"{vs.parent.name}_pk": world.book.pk})


# ── grants ───────────────────────────────────────────────────────────────────


def _grant(kind, user, model, action, obj):
    """``action`` on one ancestor: a model permission for core, an object grant for Guardian."""
    if kind == "guardian":
        assign_perm(f"app.{action}_{model._meta.model_name}", user, obj)
    else:
        ct = ContentType.objects.get_for_model(model)
        user.user_permissions.add(Permission.objects.get(content_type=ct, codename=f"{action}_{ct.model}"))


def _actor(kind, username, world, *, publisher=("view",), book=()):
    user = _user(username)
    for action in publisher:
        _grant(kind, user, Publisher, action, world.penguin)
    for action in book:
        _grant(kind, user, Book, action, world.book)
    return user


# ── spies ────────────────────────────────────────────────────────────────────


@pytest.fixture
def trace(monkeypatch, events):
    """Adds the redirect's own steps to the ordered queryset / has_perm events."""
    from crud_views.lib.views import RedirectChildView

    original_object = RedirectChildView.get_object
    original_url = RedirectChildView.get_redirect_url

    def object_spy(self, queryset=None):
        events.append(("child_lookup", self.cv_viewset.name))
        return original_object(self, queryset)

    def url_spy(self, *args, **kwargs):
        url = original_url(self, *args, **kwargs)
        events.append(("redirect_url", self.cv_viewset.name))  # recorded once the URL is built
        return url

    monkeypatch.setattr(RedirectChildView, "get_object", object_spy)
    monkeypatch.setattr(RedirectChildView, "get_redirect_url", url_spy)
    return events


def _child_work(recorded, vs):
    return [
        event
        for event in recorded
        if event in {("queryset", vs.name), ("child_lookup", vs.name), ("redirect_url", vs.name)}
    ]


# ── built-in Read classification ─────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_builtin_redirect_is_read_without_an_action_entry(routes, world, trace, cascade, kind):
    chain = routes.chains[kind]
    main = chain.books["book"]
    assert "redirect_child" not in main.ancestor_policy.actions and "go" not in main.ancestor_policy.actions
    assert _action_declaration_problems(main) == []  # no E267/E268 for the built-in redirects
    reader = _actor(kind, f"ar_read_{kind}", world)  # Publisher view only: the Read pair's nearest
    for key in ("redirect_child", "go"):  # the plain registration and a renamed subclass
        del trace[:]
        response = _client(reader).get(_redirect_url(chain, key, publisher_pk=world.penguin.pk, book_pk=world.book.pk))
        assert response.status_code == 302
        expected = _url(
            chain.destinations[key],
            "list",
            **{f"{chain.pub.name}_pk": world.penguin.pk, f"{main.name}_pk": world.book.pk},
        )
        assert response["Location"] == expected
        # ancestor first, then the redirect's own lookup, then its URL
        assert trace.index(("queryset", chain.pub.name)) < trace.index(("child_lookup", main.name))
        assert trace.index(("child_lookup", main.name)) < trace.index(("redirect_url", main.name))


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_ancestor_denial_precedes_redirect_lookup_and_response(routes, world, trace, cascade, kind):
    chain = routes.chains[kind]
    main = chain.books["book"]
    stranger = _actor(kind, f"ar_deny_{kind}", world, publisher=(), book=("view", "change"))  # child grants only
    for key in ("redirect_child", "go"):
        del trace[:]
        url = _redirect_url(chain, key, publisher_pk=world.penguin.pk, book_pk=world.book.pk)
        assert _client(stranger).get(url).status_code == 403
        assert ("queryset", chain.pub.name) in trace  # the ancestor was resolved and gated ...
        assert _child_work(trace, main) == []  # ... and nothing of the redirect itself ran
    anonymous = _client(None).get(_redirect_url(chain, publisher_pk=world.penguin.pk, book_pk=world.book.pk))
    assert anonymous.status_code == 302 and "/accounts/login/" in anonymous["Location"]


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_reached_missing_parent_is_404_before_redirect_lookup(routes, world, trace, cascade, kind):
    chain = routes.chains[kind]
    main = chain.books["book"]
    reader = _actor(kind, f"ar_404_{kind}", world)
    del trace[:]
    assert _client(reader).get(_redirect_url(chain, publisher_pk=MISSING, book_pk=world.book.pk)).status_code == 404
    assert _child_work(trace, main) == []
    # an existing parent is reached; the child of another parent is then not found by the redirect's own lookup
    del trace[:]
    url = _redirect_url(chain, publisher_pk=world.penguin.pk, book_pk=world.foreign.pk)
    assert _client(reader).get(url).status_code == 404
    assert ("child_lookup", main.name) in trace and ("redirect_url", main.name) not in trace


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_explicit_entry_replaces_the_read_pair(routes, world, trace, cascade, kind):
    chain = routes.chains[kind]
    override = chain.books["book_override"]
    url = _redirect_url(chain, book="book_override", publisher_pk=world.penguin.pk, book_pk=world.book.pk)
    reader = _actor(kind, f"ar_ovr_reader_{kind}", world)
    assert _client(reader).get(url).status_code == 403  # Publisher view no longer suffices
    assert _child_work(trace, override) == []
    editor = _actor(kind, f"ar_ovr_editor_{kind}", world, publisher=("change",))
    assert _client(editor).get(url).status_code == 302
    # the entry is local to that ViewSet: the plain Book redirect keeps the Read pair
    assert (
        _client(reader).get(_redirect_url(chain, publisher_pk=world.penguin.pk, book_pk=world.book.pk)).status_code
        == 302
    )


# ── the destination is a separate, independently authorized request ─────────


def _follow(client, response, recorded):
    """Follow a redirect as a fresh request; return (destination response, its own events)."""
    assert response.status_code == 302
    mark = len(recorded)
    followed = client.get(response["Location"])
    return followed, recorded[mark:]


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_allowed_redirect_does_not_authorize_a_stricter_destination(routes, world, trace, cascade, kind):
    chain = routes.chains[kind]
    main = chain.books["book"]
    client = _client(_actor(kind, f"ar_dest_{kind}", world, book=("view",)))  # Publisher view + Book view

    # higher=change on the destination: needs Publisher change under full cascade only
    redirect = client.get(_redirect_url(chain, "go", publisher_pk=world.penguin.pk, book_pk=world.book.pk))
    before = list(trace)
    followed, own = _follow(client, redirect, trace)
    assert followed.status_code == (403 if cascade else 200)
    # separate event sequences: the redirect never touched the destination; the destination resolved its own
    # ancestors again and never re-ran the redirect
    destination = chain.notes["note_higher"]
    assert ("queryset", destination.name) not in before
    assert ("queryset", chain.pub.name) in own  # the destination resolves its ancestors itself, top-down
    assert ("child_lookup", main.name) not in own and ("redirect_url", main.name) not in own
    if cascade:
        # denied at the Publisher gate (higher=change): neither the Book ancestor nor the destination is loaded
        assert ("queryset", main.name) not in own and ("queryset", destination.name) not in own
    else:
        order = [("queryset", chain.pub.name), ("queryset", main.name), ("queryset", destination.name)]
        assert [event for event in own if event in order] == order

    # nearest=change on the destination: Book change needed in both modes
    redirect = client.get(_redirect_url(chain, "go_change", publisher_pk=world.penguin.pk, book_pk=world.book.pk))
    followed, own = _follow(client, redirect, trace)
    assert followed.status_code == 403
    assert ("queryset", chain.notes["note_change"].name) not in own

    # with the stricter grants the same redirect target is allowed
    editor = _client(
        _actor(kind, f"ar_dest_editor_{kind}", world, publisher=("view", "change"), book=("view", "change"))
    )
    for key in ("go", "go_change"):
        redirect = editor.get(_redirect_url(chain, key, publisher_pk=world.penguin.pk, book_pk=world.book.pk))
        assert _follow(editor, redirect, trace)[0].status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_allowed_redirect_does_not_waive_the_destination_local_gate(routes, world, trace, cascade, kind):
    chain = routes.chains[kind]
    reader = _actor(kind, f"ar_local_{kind}", world, book=("view",))
    client = _client(reader)
    redirect = client.get(_redirect_url(chain, "go_local", publisher_pk=world.penguin.pk, book_pk=world.book.pk))
    followed, own = _follow(client, redirect, trace)
    assert followed.status_code == 403  # ancestry passes; the destination's own BookNote view gate denies
    assert ("has_perm", "app.view_booknote") in own
    reader.user_permissions.add(Permission.objects.get(codename="view_booknote"))
    client = _client(reader)
    redirect = client.get(_redirect_url(chain, "go_local", publisher_pk=world.penguin.pk, book_pk=world.book.pk))
    assert _follow(client, redirect, trace)[0].status_code == 200


# ── arbitrary redirects are not built-in redirects ───────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("kind", KINDS)
def test_custom_redirecting_views_need_an_exact_entry(routes, world, cascade, kind):
    chain = routes.chains[kind]
    custom = chain.books["book_custom"]
    problems = _action_declaration_problems(custom)
    assert {code for code, _ in problems} == {"E268"}
    redirecting_action = custom.get_view_class("redirect_child")
    assert issubclass(redirecting_action, ActionView)
    messages = [message for _, message in problems]
    assert any(f"'redirect_child' ({redirecting_action.__name__})" in message for message in messages)
    assert any("'jump'" in message for message in messages)
    assert len(messages) == 2

    superuser = _user(f"ar_custom_super_{kind}", superuser=True)
    client = _client(superuser)
    kwargs = {f"{chain.pub.name}_pk": world.penguin.pk}
    with pytest.raises(ImproperlyConfigured, match=r"actions\['redirect_child'\]"):
        client.get(_url(custom, "redirect_child", pk=world.book.pk, **kwargs))
    with pytest.raises(ImproperlyConfigured, match=r"actions\['jump'\]"):
        client.get(_url(custom, "jump", **kwargs))
