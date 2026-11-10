"""
Phase 06.18 plans 11/12 — the published ancestor-authorization guidance, executed.

Plan 12 adds the release surfaces: the migration guide's custom-endpoint fence is executed like the reference
fences, and the ``### Breaking`` changelog entry is paired with its anchored migration section, including the
nested write-selector change, whose behavior is proven once by the published router example below.

Each executable subsection listed in ``INVENTORY`` has a unique exact heading and exactly one complete Python
fence. The tests extract that fence with the existing ``_section`` / ``FENCE`` convention and ``exec`` the whole
published source (imports, ViewSet construction and view registration included) against ``myapp.*`` modules
backed by the test app's models. Nothing is copied into test strings.

Isolation: the project URLconf is imported first; the ViewSet registry and the permission-vocabulary cache are
snapshotted and the registry is emptied so the published names (``publisher``, ``book``, ...) can register; the
published ViewSets are routed behind a temporary ROOT_URLCONF. Registry, vocabulary cache, URL caches, ContentType
cache, routers and ``sys.modules`` entries are restored afterwards. Strict mode is off: the examples keep their
default context actions, whose unregistered keys (Publisher's own views are omitted) are skipped as in production.
"""

from __future__ import annotations

import ast
import sys
import types
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import router
from django.test import Client, override_settings
from django.urls import clear_url_caches, reverse
from pydantic import ValidationError

import tests.test1.project.urls  # noqa: F401 - registers the shared app ViewSets before any registry snapshot
from crud_views.lib import check as check_module
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, AncestorPermissions, AncestorPolicy, ViewSet
from tests.test1.app.models import Author, Book, BookNote, Publisher
from tests.test1.test_label_mode_docs import CHANGELOG_MD, DOCS, FENCE, MIGRATING_MD, _anchors, _flat, _section

NESTED_MD = DOCS / "reference" / "nested.md"
SETTINGS_MD = DOCS / "reference" / "settings.md"
RESOURCES_MD = DOCS / "reference" / "resources.md"
LIFECYCLE_MD = DOCS / "reference" / "request_lifecycle.md"
GUARDIAN_MD = DOCS / "reference" / "guardian.md"
CUSTOM_FORM_MD = DOCS / "reference" / "custom_form_view.md"
ACTION_VIEW_MD = DOCS / "reference" / "action_view.md"

CANONICAL = (NESTED_MD, "### Example: permissions for a nested Book ViewSet")
SETTINGS_EXAMPLE = (SETTINGS_MD, "## Ancestor authorization")
RESOURCE_SCOPING = (RESOURCES_MD, "### Ancestor authorization of a Resource leaf")
DATABASE_REFUSAL = (LIFECYCLE_MD, "#### Nested ViewSets: instance-hinted write routing")
PROVIDER_MIGRATION = (GUARDIAN_MD, "### Core or Guardian parent")
FALLBACK = (GUARDIAN_MD, "### Ancestor fallback and view fallback")
MIGRATED_ACTION = (MIGRATING_MD, "#### Custom endpoints need an exact entry")
CUSTOM_PERMISSION = (CUSTOM_FORM_MD, "### Require it on the view")  # #341: execute the published permission recipe
TUTORIALS = [DOCS / "getting_started" / name for name in ("tutorial-5-filters-permissions.md", "tutorial-6-books.md")]

# every executable subsection: (page, exact heading); each heading and its single fence occur once
INVENTORY = [
    CANONICAL,
    SETTINGS_EXAMPLE,
    RESOURCE_SCOPING,
    DATABASE_REFUSAL,
    PROVIDER_MIGRATION,
    FALLBACK,
    MIGRATED_ACTION,
    CUSTOM_PERMISSION,
]

REFUSED = r"nested ViewSets support only the 'default' database"


def _fence(page: Path, heading: str) -> str:
    """The one complete Python fence of a uniquely headed subsection (``_section`` asserts the heading once)."""
    fences = FENCE.findall(_section(page.read_text(), heading))
    assert len(fences) == 1, f"{page.name} {heading!r}: expected exactly one python fence, found {len(fences)}"
    return fences[0]


@pytest.mark.parametrize(("page", "heading"), INVENTORY, ids=[h for _, h in INVENTORY])
def test_inventory_heading_and_fence_occur_once(page, heading):
    source = _fence(page, heading)
    ast.parse(source)  # a complete, parseable fence
    assert source.count("\n") > 2


def test_inventory_detects_missing_or_duplicate_sections(tmp_path):
    page, heading = CANONICAL
    text = page.read_text()
    body = _section(text, heading)
    duplicate = tmp_path / "duplicate.md"
    duplicate.write_text(text + f"\n{heading}\n")
    with pytest.raises(AssertionError, match="must appear exactly once"):
        _fence(duplicate, heading)
    missing = tmp_path / "missing.md"
    missing.write_text(text.replace(heading, "### Renamed"))
    with pytest.raises(AssertionError, match="must appear exactly once"):
        _fence(missing, heading)
    two_fences = tmp_path / "two.md"
    two_fences.write_text(text.replace(body, body + "\n```python\nx = 1\n```\n"))
    with pytest.raises(AssertionError, match="exactly one python fence"):
        _fence(two_fences, heading)


# ── isolated execution of published fences ─────────────────────────────────


def _module(name: str, **attrs) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    return module


@contextmanager
def _published_registry(monkeypatch):
    """An empty ViewSet registry for published fences, routed behind a temporary ROOT_URLCONF."""
    with _REGISTRY_LOCK:
        registry_snapshot = dict(_REGISTRY)
        _REGISTRY.clear()
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    urls = _module(f"tests.test1._ancestor_docs_urls_{uuid.uuid4().hex[:8]}", urlpatterns=[])
    files: list[dict] = []
    package = _module("myapp", __path__=[])
    for module in (
        package,
        _module("myapp.models", Author=Author, Book=Book, BookNote=BookNote, Publisher=Publisher),
        _module("myapp.storage", list_files=lambda: list(files)),
        urls,
    ):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    namespace: dict = {"__name__": "myapp.views"}
    controls: list[ViewSet] = []  # test-built control ViewSets routed next to the published ones

    def route():
        published = [value for value in namespace.values() if isinstance(value, ViewSet)]
        urls.urlpatterns = [pattern for vs in (*published, *controls) for pattern in vs.urlpatterns]
        clear_url_caches()

    def run(page: Path, heading: str) -> dict:
        exec(compile(_fence(page, heading), f"{page}:{heading}", "exec"), namespace)
        route()
        return namespace

    def control(vs: ViewSet) -> ViewSet:
        controls.append(vs)
        route()
        return vs

    try:
        with override_settings(ROOT_URLCONF=urls.__name__, CRUD_VIEWS_STRICT=False):
            clear_url_caches()
            yield SimpleNamespace(run=run, control=control, ns=namespace, files=files)
    finally:
        clear_url_caches()
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(registry_snapshot)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        ContentType.objects.clear_cache()


@pytest.fixture
def published(monkeypatch):
    with _published_registry(monkeypatch) as runner:
        yield runner


def _user(username: str, *grants: tuple[type, str]) -> User:
    user = User.objects.create_user(username=username, password="pw")
    for model, action in grants:
        ct = ContentType.objects.get_for_model(model)
        user.user_permissions.add(Permission.objects.get(content_type=ct, codename=f"{action}_{ct.model}"))
    return user


def _client(user: User | None) -> Client:
    client = Client()
    if user is not None:
        client.force_login(user)
    return client


def _url(vs: ViewSet, key: str, **kwargs) -> str:
    return reverse(vs.get_router_name(key), kwargs=kwargs)


@pytest.fixture
def books(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    return SimpleNamespace(
        penguin=penguin,
        other=other,
        book=Book.objects.create(title="Hitchhiker", publisher=penguin),
        foreign=Book.objects.create(title="Foreign", publisher=other),
    )


# ── Task 1: the canonical nested example (policy, operations, custom action, mutation boundary) ──


@pytest.fixture
def canonical(published):
    ns = published.run(*CANONICAL)
    book_vs = ns["cv_book"]
    ns["urls"] = SimpleNamespace(
        list=lambda p: _url(book_vs, "list", publisher_pk=p.pk),
        detail=lambda p, b: _url(book_vs, "detail", publisher_pk=p.pk, pk=b.pk),
        update=lambda p, b: _url(book_vs, "update", publisher_pk=p.pk, pk=b.pk),
        delete=lambda p, b: _url(book_vs, "delete", publisher_pk=p.pk, pk=b.pk),
        approve=lambda p, b: _url(book_vs, "approve", publisher_pk=p.pk, pk=b.pk),
    )
    return SimpleNamespace(**ns)


def test_canonical_declarations_are_the_published_real_api(canonical):
    assert canonical.cv_book.ancestor_policy == AncestorPolicy(
        actions={"approve": AncestorPermissions(nearest="change", higher="view")}
    )
    assert canonical.cv_publisher.ancestor_policy == AncestorPolicy()
    assert canonical.cv_book.parent.get_attribute() == "publisher"
    assert canonical.cv_book.get_view_class("approve") is canonical.BookApproveView


def test_book_reads_need_publisher_view_and_their_own_view(canonical, books):
    urls = canonical.urls
    reader = _client(_user("reader", (Publisher, "view"), (Book, "view")))
    response = reader.get(urls.list(books.penguin))
    assert response.status_code == 200
    assert list(response.context["object_list"]) == [books.book]  # this publisher's books only
    assert reader.get(urls.detail(books.penguin, books.book)).status_code == 200
    # Read never needs Publisher change; Write does — also for the form/confirmation GET
    assert reader.get(urls.update(books.penguin, books.book)).status_code == 403
    assert reader.get(urls.delete(books.penguin, books.book)).status_code == 403
    # local denial control: the ancestor grant never stands in for the endpoint's own permission
    no_book_view = _client(_user("pub_only", (Publisher, "view"), (Publisher, "change")))
    assert no_book_view.get(urls.list(books.penguin)).status_code == 403
    # ancestry denial control: every Book permission, no Publisher permission
    book_only = _client(_user("book_only", *[(Book, a) for a in ("view", "change", "delete")]))
    for url in (
        urls.list(books.penguin),
        urls.detail(books.penguin, books.book),
        urls.update(books.penguin, books.book),
    ):
        assert book_only.get(url).status_code == 403


def test_book_editors_need_publisher_change_and_their_own_change(canonical, books):
    urls = canonical.urls
    editor = _client(_user("editor", (Publisher, "view"), (Publisher, "change"), (Book, "view"), (Book, "change")))
    assert editor.get(urls.update(books.penguin, books.book)).status_code == 200
    response = editor.post(urls.update(books.penguin, books.book), {"title": "Edited"})
    assert response.status_code == 302
    books.book.refresh_from_db()
    assert books.book.title == "Edited"
    # local denial control: Publisher change without Book change
    no_book_change = _client(_user("no_book_change", (Publisher, "view"), (Publisher, "change"), (Book, "view")))
    assert no_book_change.get(urls.update(books.penguin, books.book)).status_code == 403
    assert no_book_change.post(urls.update(books.penguin, books.book), {"title": "x"}).status_code == 403
    books.book.refresh_from_db()
    assert books.book.title == "Edited"


def test_child_delete_needs_publisher_change_not_publisher_delete(canonical, books):
    urls = canonical.urls
    deleter = _client(_user("deleter", (Publisher, "delete"), (Book, "delete")))
    assert deleter.get(urls.delete(books.penguin, books.book)).status_code == 403
    allowed = _client(_user("allowed_deleter", (Publisher, "change"), (Book, "delete")))
    assert allowed.get(urls.delete(books.penguin, books.book)).status_code == 200
    assert allowed.post(urls.delete(books.penguin, books.book)).status_code == 302
    assert not Book.objects.filter(pk=books.book.pk).exists()


def test_custom_approve_action_uses_its_exact_pair(canonical, books, monkeypatch):
    urls = canonical.urls
    calls = []
    original = canonical.BookApproveView.action
    monkeypatch.setattr(
        canonical.BookApproveView, "action", lambda self, context: calls.append(self.object) or original(self, context)
    )
    viewer = _client(_user("viewer", (Publisher, "view"), (Book, "change")))
    assert viewer.post(urls.approve(books.penguin, books.book)).status_code == 403
    assert calls == []
    approver = _client(_user("approver", (Publisher, "change"), (Book, "change")))
    assert approver.post(urls.approve(books.penguin, books.book)).status_code == 302
    assert calls == [books.book]
    # local denial control: the action's own cv_permission
    no_local = _client(_user("no_local", (Publisher, "change")))
    assert no_local.post(urls.approve(books.penguin, books.book)).status_code == 403
    assert calls == [books.book]


def test_published_mutation_restriction_keeps_the_url_parent(canonical, books):
    """The application-owned restriction of the example: the form omits ``publisher``, so a submitted value
    cannot move the Book; a mismatched URL parent stays a 404."""
    urls = canonical.urls
    editor = _client(_user("mover", (Publisher, "view"), (Publisher, "change"), (Book, "view"), (Book, "change")))
    response = editor.post(urls.update(books.penguin, books.book), {"title": "Moved?", "publisher": books.other.pk})
    assert response.status_code == 302
    books.book.refresh_from_db()
    assert (books.book.title, books.book.publisher_id) == ("Moved?", books.penguin.pk)
    assert editor.get(urls.update(books.other, books.book)).status_code == 404
    assert editor.get(urls.detail(books.penguin, books.foreign)).status_code == 404


def test_protected_ancestry_actor_responses(canonical, books):
    urls = canonical.urls
    response = _client(None).get(urls.list(books.penguin))
    assert response.status_code == 302 and "login" in response["Location"]
    inactive = _user("inactive", (Publisher, "view"), (Book, "view"))
    inactive.is_active = False
    inactive.save()
    with override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.AllowAllUsersModelBackend"]):
        assert _client(inactive).get(urls.list(books.penguin)).status_code == 403
    # a missing ancestor is 404 for an authorized actor
    reader = _client(_user("reader404", (Publisher, "view"), (Book, "view")))
    assert reader.get(_url(canonical.cv_book, "list", publisher_pk=999_999)).status_code == 404


def test_core_parent_gate_ignores_object_grants(canonical, books):
    """Core Publisher parent: an object grant alone does not satisfy the model-permission gate."""
    from guardian.shortcuts import assign_perm

    user = _user("object_only", (Book, "view"))
    assign_perm("app.view_publisher", user, books.penguin)
    assert _client(user).get(canonical.urls.list(books.penguin)).status_code == 403


def test_documented_configuration_errors(canonical, books):
    from crud_views.checks import check_ancestor_declarations

    def ancestor_errors():
        return sorted(
            (m.id, m.obj.name) for m in check_ancestor_declarations() if m.id in ("viewset.E267", "viewset.E268")
        )

    assert ancestor_errors() == []
    policy = canonical.cv_book.ancestor_policy
    # an unregistered action key: E267 and a runtime guard
    policy.actions["publish"] = AncestorPermissions(nearest="change", higher="view")
    assert ancestor_errors() == [("viewset.E267", "book")]
    editor = _client(_user("err_editor", (Publisher, "view"), (Book, "view")))
    with pytest.raises(ImproperlyConfigured, match="names no registered endpoint"):
        editor.get(canonical.urls.list(books.penguin))
    del policy.actions["publish"]
    # the nested custom endpoint without its entry: E268 and a runtime guard
    approve = policy.actions.pop("approve")
    assert ancestor_errors() == [("viewset.E268", "book")]
    with pytest.raises(ImproperlyConfigured, match=r"declare ancestor_policy.actions\['approve'\]"):
        _client(_user("err_approver", (Publisher, "change"), (Book, "change"))).post(
            canonical.urls.approve(books.penguin, books.book)
        )
    policy.actions["approve"] = approve
    assert ancestor_errors() == []
    # request fields on a top-level ViewSet, and a Guardian provider on a core ViewSet, fail at construction
    with pytest.raises(ValidationError, match="have no effect"):
        ViewSet(model=Publisher, name="toplevel_actions", ancestor_policy=AncestorPolicy(actions={"x": approve}))
    with pytest.raises(ValidationError, match="use GuardianViewSet"):
        ViewSet(model=Publisher, name="core_guardian", ancestor_policy=AncestorPolicy(provider="guardian"))
    with pytest.raises(ValidationError):
        AncestorPermissions(nearest="change")
    assert "toplevel_actions" not in _REGISTRY and "core_guardian" not in _REGISTRY


# ── Task 1: the settings example ────────────────────────────────────────────


def test_published_settings_example_is_applied_exactly():
    from tests.test1.test_ancestor_policy import _fresh_settings

    source = _fence(*SETTINGS_EXAMPLE)
    assignments = {}
    for node in ast.parse(source).body:  # data only: the published assignments, never exec
        assert isinstance(node, ast.Assign), ast.dump(node)
        (target,) = node.targets
        assignments[target.id] = ast.literal_eval(node.value)
    assert sorted(assignments) == [
        "CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE",
        "CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS",
        "CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS",
    ]
    result = _fresh_settings(
        "".join(f"{name}={value!r}," for name, value in assignments.items()),
        """
        from crud_views.lib.settings import crud_views_settings as s
        print(s.ancestor_permission_cascade, s.ancestor_read_permissions.model_dump(),
              s.ancestor_write_permissions.model_dump())
        """,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == " ".join(
        str(assignments[name])
        for name in (
            "CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE",
            "CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS",
            "CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS",
        )
    )
    # the documented failure: an incomplete mapping is not merged with the default
    result = _fresh_settings(
        'CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS={"nearest": "change"},', "import crud_views.lib.settings\n"
    )
    assert result.returncode != 0 and "ValidationError" in result.stderr


def test_settings_table_names_the_package_defaults():
    from crud_views.lib.ancestor_policy import DEFAULT_CASCADE, DEFAULT_READ_PERMISSIONS, DEFAULT_WRITE_PERMISSIONS

    section = _section(SETTINGS_MD.read_text(), "## Ancestor authorization")
    expected = {
        "CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE": f"`{DEFAULT_CASCADE}`",
        "CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS": f"`{DEFAULT_READ_PERMISSIONS}`".replace("'", '"'),
        "CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS": f"`{DEFAULT_WRITE_PERMISSIONS}`".replace("'", '"'),
    }
    for name, default in expected.items():
        (row,) = [line for line in section.splitlines() if line.startswith(f"| {name} |")]
        assert row.rstrip(" |").endswith(default), row


# ── Task 1: Resource leaf scoping ───────────────────────────────────────────


@pytest.fixture
def resource_leaf(published, books):
    published.run(*CANONICAL)
    ns = published.run(*RESOURCE_SCOPING)
    published.files.extend(
        [
            {"key": "penguin-catalog", "publisher_id": books.penguin.pk},
            {"key": "other-catalog", "publisher_id": books.other.pk},
        ]
    )
    loads = []
    original = ns["PublisherFile"].cv_get_items.__func__

    def spy(cls, request, **url_kwargs):
        loads.append(dict(url_kwargs))
        return original(cls, request, **url_kwargs)

    ns["PublisherFile"].cv_get_items = classmethod(spy)
    vs = ns["cv_publisher_file"]
    return SimpleNamespace(vs=vs, loads=loads, list=lambda p: _url(vs, "list", publisher_pk=p.pk))


def test_resource_leaf_ancestry_precedes_the_application_loader(resource_leaf, books):
    denied = _client(_user("file_denied", (Book, "view")))
    assert denied.get(resource_leaf.list(books.penguin)).status_code == 403
    assert _client(None).get(resource_leaf.list(books.penguin)).status_code == 302
    reader = _client(_user("file_reader", (Publisher, "view")))
    assert reader.get(_url(resource_leaf.vs, "list", publisher_pk=999_999)).status_code == 404
    assert resource_leaf.loads == []  # no denied, anonymous or missing ancestry reached the loader
    response = reader.get(resource_leaf.list(books.penguin))
    assert response.status_code == 200
    # membership is the published loader's: only this publisher's files
    assert [row.key for row in response.context["object_list"]] == ["penguin-catalog"]
    assert resource_leaf.loads == [{"publisher_pk": str(books.penguin.pk)}]  # the raw URL kwarg


def test_resource_cannot_be_a_parent(resource_leaf):
    from crud_views.lib.viewset import ParentViewSet

    leaf_vs = ViewSet(model=Book, name="below_resource", parent=ParentViewSet(name="publisherfile"))
    with pytest.raises(ImproperlyConfigured, match="Resource-based"):
        leaf_vs.urlpatterns  # noqa: B018 - URL construction walks the ancestry


# ── Task 1: the hint-sensitive router example (nested refusal, top-level control) ──


@pytest.fixture
def sharded(published, monkeypatch):
    published.run(*CANONICAL)
    ns = published.run(*DATABASE_REFUSAL)
    monkeypatch.setattr(router, "routers", [ns["BookShardRouter"]()])
    ContentType.objects.clear_cache()
    from crud_views.lib.views import ListView, UpdateView

    # top-level control, not published: the same model and router through a top-level ViewSet
    top_vs = ViewSet(model=Book, name="topbook")
    type("TopBookList", (ListView,), {"cv_viewset": top_vs})
    top_update = type("TopBookUpdate", (UpdateView,), {"cv_viewset": top_vs, "fields": ["title"]})
    published.control(top_vs)
    yield SimpleNamespace(**ns, top_vs=top_vs, TopUpdate=top_update)
    ContentType.objects.clear_cache()


def _shard_rows():
    pairs = {}
    for alias in ("default", "shard"):
        publisher = Publisher.objects.using(alias).create(pk=41, name=f"{alias} publisher")
        book = Book.objects.using(alias).create(pk=71, publisher_id=publisher.pk, title=f"{alias} title")
        pairs[alias] = SimpleNamespace(publisher=publisher, book=book)
    plain = Publisher.objects.create(pk=42, name="plain publisher")
    pairs["plain"] = SimpleNamespace(publisher=plain, book=Book.objects.create(pk=72, publisher=plain, title="plain"))
    return pairs


def _titles(alias):
    return sorted(Book.objects.using(alias).values_list("pk", "title"))


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
@pytest.mark.parametrize("atomic", [True, False], ids=["atomic", "autocommit"])
def test_published_router_refuses_the_instance_selected_nested_write(sharded, monkeypatch, atomic):
    rows = _shard_rows()
    update = sharded.BookUpdateView
    monkeypatch.setattr(update, "cv_atomic", atomic)
    hooks = []
    for name in ("cv_post_hook", "cv_form_valid", "cv_form_valid_hook", "cv_on_commit"):
        original = getattr(update, name)
        monkeypatch.setattr(
            update, name, lambda self, *a, _n=name, _o=original, **kw: hooks.append(_n) or _o(self, *a, **kw)
        )
    editor = _client(_user("shard_editor", (Publisher, "view"), (Publisher, "change"), (Book, "change")))
    url = lambda r: _url(sharded.cv_book, "update", publisher_pk=r.publisher.pk, pk=r.book.pk)  # noqa: E731

    # a model-only lookup gets no answer: default
    assert router.db_for_write(Book) == "default"
    # permitted default selection: the publisher is not sharded
    response = editor.post(url(rows["plain"]), {"title": "plain edited"})
    assert response.status_code == 302
    assert (72, "plain edited") in _titles("default") and "cv_form_valid" in hooks

    # the same router now selects shard for this instance: refused before any hook or write
    hooks.clear()
    sharded.SHARDED_PUBLISHERS.add(41)
    before = (_titles("default"), _titles("shard"))
    with pytest.raises(ImproperlyConfigured, match=REFUSED):
        editor.post(url(rows["default"]), {"title": "never written"})
    assert hooks == []
    assert (_titles("default"), _titles("shard")) == before


@pytest.mark.django_db(transaction=True, databases=["default", "shard"])
def test_published_router_leaves_top_level_routing_unchanged(sharded, rf):
    rows = _shard_rows()
    sharded.SHARDED_PUBLISHERS.add(41)
    # selector: nested consults the instance hint, top-level stays model-only
    nested, top = sharded.BookUpdateView(), sharded.TopUpdate()
    request = rf.post("/")
    nested.setup(request, publisher_pk=41, pk=71)
    top.setup(request, pk=71)
    nested.object = top.object = Book.objects.get(pk=71)
    assert (nested.cv_get_db_alias(), top.cv_get_db_alias()) == ("shard", "default")
    # top-level request: not refused; the default transaction wraps a save() that follows the router
    superuser = User.objects.create_superuser(username="top_super", password="pw")
    response = _client(superuser).post(_url(sharded.top_vs, "update", pk=71), {"title": "top edited"})
    assert response.status_code == 302
    assert (71, "top edited") in _titles("shard") and (71, "default title") in _titles("default")
    assert rows["default"].book.title == "default title"


# ── Task 2: Guardian provider migration, fallback independence, manage ─────


def _grant(viewset, key: str, holder, obj) -> None:
    viewset.assign_perm(key, holder, obj)


@pytest.fixture
def guardian_parent(published, books):
    ns = SimpleNamespace(**published.run(*PROVIDER_MIGRATION))
    book_vs = ns.cv_book
    ns.list = lambda p: _url(book_vs, "list", publisher_pk=p.pk)
    ns.detail = lambda p, b: _url(book_vs, "detail", publisher_pk=p.pk, pk=b.pk)
    ns.update = lambda p, b: _url(book_vs, "update", publisher_pk=p.pk, pk=b.pk)
    ns.create = lambda p: _url(book_vs, "create", publisher_pk=p.pk)
    return ns


def test_guardian_parent_needs_an_object_grant_and_ignores_model_grants(guardian_parent, books):
    g = guardian_parent
    assert g.cv_publisher.ancestor_policy == AncestorPolicy()  # class default: provider "guardian", strict
    # model grant only on Publisher: the Guardian parent denies (a core parent would satisfy, see the core test)
    model_only = _user("g_model_only", (Publisher, "view"))
    _grant(g.cv_book, "view", model_only, books.book)
    assert _client(model_only).get(g.detail(books.penguin, books.book)).status_code == 403
    # object grant only on Publisher, direct
    direct = _user("g_direct")
    _grant(g.cv_publisher, "view", direct, books.penguin)
    _grant(g.cv_book, "view", direct, books.book)
    assert _client(direct).get(g.detail(books.penguin, books.book)).status_code == 200
    assert _client(direct).get(g.list(books.penguin)).status_code == 200
    # ... and through a group
    group = Group.objects.create(name="g_publisher_readers")
    _grant(g.cv_publisher, "view", group, books.penguin)
    member = _user("g_member")
    member.groups.add(group)
    _grant(g.cv_book, "view", member, books.book)
    assert _client(member).get(g.detail(books.penguin, books.book)).status_code == 200
    # the grant is on this Publisher object only
    assert _client(member).get(g.list(books.other)).status_code == 403
    # independent child-denial control: the Publisher grant never replaces the Book object grant
    parent_only = _user("g_parent_only")
    _grant(g.cv_publisher, "view", parent_only, books.penguin)
    assert _client(parent_only).get(g.detail(books.penguin, books.book)).status_code == 403


def test_guardian_parent_write_and_nested_create_without_model_add(guardian_parent, books):
    g = guardian_parent
    viewer = _user("g_viewer")
    _grant(g.cv_publisher, "view", viewer, books.penguin)
    _grant(g.cv_book, "change", viewer, books.book)
    assert _client(viewer).get(g.update(books.penguin, books.book)).status_code == 403  # Write: Publisher change
    assert _client(viewer).get(g.create(books.penguin)).status_code == 403
    editor = _user("g_editor")
    _grant(g.cv_publisher, "change", editor, books.penguin)
    _grant(g.cv_book, "change", editor, books.book)
    assert _client(editor).get(g.update(books.penguin, books.book)).status_code == 200
    # nested create: Publisher change on this object, no add_book model permission required or added
    assert not editor.has_perm("app.add_book")
    assert _client(editor).get(g.create(books.penguin)).status_code == 200
    response = _client(editor).post(g.create(books.penguin), {"title": "Created"})
    assert response.status_code == 302
    assert Book.objects.get(title="Created").publisher_id == books.penguin.pk
    # local denial control: Publisher change without the Book object grant
    no_book = _user("g_no_book")
    _grant(g.cv_publisher, "change", no_book, books.penguin)
    assert _client(no_book).get(g.update(books.penguin, books.book)).status_code == 403
    # the ViewSet helper stays strict: a model grant returns nothing
    model_viewer = _user("g_helper", (Book, "view"))
    assert list(g.cv_book.get_objects_for_user(model_viewer, "view")) == []


def test_removed_guardian_parent_fields_are_rejected(published):
    from crud_views.lib.viewset import ParentViewSet
    from crud_views_guardian.lib.viewset import GuardianViewSet

    GuardianViewSet(model=Publisher, name="publisher")
    for field, value in (("cv_guardian_parent_permission", None), ("cv_guardian_parent_create_permission", "view")):
        with pytest.raises(ValidationError, match="ancestor policy"):
            GuardianViewSet(model=Book, name="book", parent=ParentViewSet(name="publisher"), **{field: value})
        assert "book" not in _REGISTRY


@pytest.fixture
def fallback(published, books):
    ns = SimpleNamespace(**published.run(*FALLBACK))
    books.note = BookNote.objects.create(book=books.book, note="first")
    ns.book_detail = lambda: _url(ns.cv_book, "detail", publisher_pk=books.penguin.pk, pk=books.book.pk)
    ns.note_list = lambda: _url(ns.cv_note, "list", publisher_pk=books.penguin.pk, book_pk=books.book.pk)
    ns.note_manage = lambda: _url(ns.cv_note, "manage", publisher_pk=books.penguin.pk, book_pk=books.book.pk)
    return ns


def test_publisher_ancestor_fallback_does_not_relax_the_strict_book_gate(fallback, books):
    f = fallback
    assert f.cv_publisher.ancestor_policy.accept_global_perms is True
    assert f.BookDetailView.cv_guardian_accept_global_perms is False
    # a Publisher model grant opens the Publisher gate ...
    reader = _user("f_reader", (Publisher, "view"))
    _grant(f.cv_book, "view", reader, books.book)
    assert _client(reader).get(f.book_detail()).status_code == 200
    # ... and the strict Book detail still needs a Book object grant: a Book model grant is not enough
    model_book = _user("f_model_book", (Publisher, "view"), (Book, "view"))
    assert _client(model_book).get(f.book_detail()).status_code == 403
    # control: with neither a Publisher model nor object grant the ancestor denies
    no_parent = _user("f_no_parent")
    _grant(f.cv_book, "view", no_parent, books.book)
    assert _client(no_parent).get(f.book_detail()).status_code == 403


def test_note_view_fallback_does_not_relax_the_strict_book_ancestor(fallback, books):
    f = fallback
    assert f.NoteListView.cv_guardian_accept_global_perms is True
    assert f.cv_book.ancestor_policy.accept_global_perms is False
    # Publisher by model grant (its fallback), Book by model grant only: the strict Book ancestor denies
    model_book = _user("f_note_model_book", (Publisher, "view"), (Book, "view"), (BookNote, "view"))
    assert _client(model_book).get(f.note_list()).status_code == 403
    # a Book object grant opens the Book ancestor; the list's own fallback accepts the Note model permission
    object_book = _user("f_note_object_book", (Publisher, "view"), (BookNote, "view"))
    _grant(f.cv_book, "view", object_book, books.book)
    response = _client(object_book).get(f.note_list())
    assert response.status_code == 200
    assert list(response.context["object_list"]) == [books.note]
    # Publisher's fallback reaches the deeper descendant too: an object grant on Publisher works as well
    group = Group.objects.create(name="f_publisher_group")
    _grant(f.cv_publisher, "view", group, books.penguin)
    member = _user("f_member", (BookNote, "view"))
    member.groups.add(group)
    _grant(f.cv_book, "view", member, books.book)
    assert _client(member).get(f.note_list()).status_code == 200


def test_nested_manage_needs_ancestry_and_its_unchanged_local_gate(fallback, books, monkeypatch):
    from crud_views.lib.settings import crud_views_settings

    f = fallback
    nobody = _user("m_nobody")
    assert _client(nobody).get(f.note_manage()).status_code == 403  # public manage does not bypass ancestry
    reader = _user("m_reader", (Publisher, "view"))
    _grant(f.cv_book, "view", reader, books.book)
    response = _client(reader).get(f.note_manage())
    assert response.status_code == 200
    policy = response.context["ancestor_policy"]
    assert policy["as_ancestor"] == {"provider": None, "effective_provider": "guardian", "accept_global_perms": False}
    assert policy["requests"]["cascade"] == {"declared": None, "effective": True}
    assert policy["requests"]["read"] == {"declared": None, "effective": {"nearest": "view", "higher": "view"}}
    config = response.context["guardian_config"]
    assert config["parent_viewset"] == "book (ancestor provider: guardian)"
    views = response.context["views"]
    assert views["list"]["guardian_policy"]["effective_policy"] == "global fallback"
    # the local manage gate is unchanged: not public and not in the manage group → 403 despite the grants
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")
    assert _client(reader).get(f.note_manage()).status_code == 403
    reader.groups.add(Group.objects.create(name=crud_views_settings.manage_group))
    assert _client(reader).get(f.note_manage()).status_code == 200
    # and the group never bypasses ancestry
    nobody.groups.add(Group.objects.get(name=crud_views_settings.manage_group))
    assert _client(nobody).get(f.note_manage()).status_code == 403


def test_publisher_manage_reports_its_ancestor_fallback(fallback, books):
    superuser = User.objects.create_superuser(username="m_super", password="pw")
    response = _client(superuser).get(_url(fallback.cv_book, "manage", publisher_pk=books.penguin.pk))
    assert response.status_code == 200
    assert response.context["guardian_config"]["parent_viewset"] == (
        "publisher (ancestor provider: guardian + model fallback)"
    )


def test_tutorials_link_the_executed_nested_example():
    anchor = "example-permissions-for-a-nested-book-viewset"
    assert anchor in _anchors(NESTED_MD)
    for tutorial in TUTORIALS:
        text = tutorial.read_text()
        assert f"../reference/nested.md#{anchor}" in text, tutorial.name
        flat = " ".join(text.split())
        assert "Book reads" in flat and "Publisher `view`" in flat and "Publisher `change`" in flat, tutorial.name
    # the canonical example demonstrates exactly those grants (executed above with local-denial controls)
    canonical = _fence(*CANONICAL)
    assert "# Read: Publisher view" in canonical and "# Write: Publisher change" in canonical


# ── Plan 12: the release surfaces (migration fence, paired Breaking entry) ──


@pytest.fixture
def migrated(published, books):
    ns = SimpleNamespace(**published.run(*MIGRATED_ACTION))
    book_vs = ns.cv_book
    ns.list = lambda p: _url(book_vs, "list", publisher_pk=p.pk)
    ns.update = lambda p, b: _url(book_vs, "update", publisher_pk=p.pk, pk=b.pk)
    ns.approve = lambda p, b: _url(book_vs, "approve", publisher_pk=p.pk, pk=b.pk)
    return ns


def test_migrated_guardian_declarations_are_the_published_real_api(migrated):
    assert migrated.cv_publisher.ancestor_policy == AncestorPolicy()
    assert migrated.cv_book.ancestor_policy == AncestorPolicy(
        write=AncestorPermissions(nearest="view", higher="view"),
        actions={"approve": AncestorPermissions(nearest="change", higher="view")},
    )
    assert migrated.cv_book.get_view_class("approve") is migrated.BookApproveView
    assert "cv_guardian_parent_permission" not in type(migrated.cv_book).model_fields


def test_migrated_write_pair_and_approve_pair_are_independent(migrated, books, monkeypatch):
    m = migrated
    calls = []
    original = m.BookApproveView.action
    monkeypatch.setattr(m.BookApproveView, "action", lambda self, ctx: calls.append(self.object) or original(self, ctx))
    # Publisher view object grant: the declared write pair keeps update open, the approve pair needs change
    viewer = _user("mig_viewer")
    _grant(m.cv_publisher, "view", viewer, books.penguin)
    _grant(m.cv_book, "change", viewer, books.book)
    response = _client(viewer).get(m.list(books.penguin))  # Read: the Publisher view grant opens the list ...
    assert response.status_code == 200
    assert list(response.context["object_list"]) == []  # ... and its own filter hides Books without a view grant
    assert _client(viewer).get(m.update(books.penguin, books.book)).status_code == 200
    assert _client(viewer).post(m.approve(books.penguin, books.book)).status_code == 403
    assert calls == []
    approver = _user("mig_approver")
    _grant(m.cv_publisher, "change", approver, books.penguin)
    _grant(m.cv_book, "change", approver, books.book)
    assert _client(approver).post(m.approve(books.penguin, books.book)).status_code == 302
    assert calls == [books.book]
    # the grant is on this Publisher object only: the foreign Book's Publisher denies
    _grant(m.cv_book, "change", approver, books.foreign)
    assert _client(approver).post(m.approve(books.other, books.foreign)).status_code == 403
    # local denial control: the Publisher grant never replaces the Book object grant
    no_book = _user("mig_no_book")
    _grant(m.cv_publisher, "change", no_book, books.penguin)
    assert _client(no_book).post(m.approve(books.penguin, books.book)).status_code == 403
    # strict Guardian parent: model grants on Publisher do not satisfy it
    model_only = _user("mig_model_only", (Publisher, "view"), (Publisher, "change"))
    _grant(m.cv_book, "change", model_only, books.book)
    assert _client(model_only).get(m.update(books.penguin, books.book)).status_code == 403
    assert _client(model_only).post(m.approve(books.penguin, books.book)).status_code == 403
    assert calls == [books.book]


def test_migrated_action_without_its_entry_fails_check_and_request(migrated, books):
    from crud_views.checks import check_ancestor_declarations

    def errors():
        return sorted((m.id, m.obj.name) for m in check_ancestor_declarations() if m.id == "viewset.E268")

    assert errors() == []
    approver = _user("mig_unlisted")
    _grant(migrated.cv_publisher, "change", approver, books.penguin)
    _grant(migrated.cv_book, "change", approver, books.book)
    policy = migrated.cv_book.ancestor_policy
    entry = policy.actions.pop("approve")
    try:
        assert errors() == [("viewset.E268", "book")]
        with pytest.raises(ImproperlyConfigured, match=r"declare ancestor_policy.actions\['approve'\]"):
            _client(approver).post(migrated.approve(books.penguin, books.book))
    finally:
        policy.actions["approve"] = entry
    assert errors() == []


def _ancestor_breaking_entry() -> str:
    breaking = _section(_section(CHANGELOG_MD.read_text(), "## Unreleased"), "### Breaking")
    heading = "- **Ancestor authorization for nested ViewSets.**"
    assert breaking.count(heading) == 1
    entry = breaking[breaking.index(heading) :]
    return entry[: entry.index("\n- **", 1)] if "\n- **" in entry[1:] else entry


ANCESTOR_MIGRATION = "### Ancestor authorization for nested ViewSets"


def test_ancestor_breaking_entry_links_its_matching_migration_anchor():
    entry = _ancestor_breaking_entry()
    anchors = _anchors(MIGRATING_MD)
    for anchor in ("ancestor-authorization-for-nested-viewsets", "nested-write-database-selection"):
        assert anchor in anchors
    assert "docs/migrating-1.0.md#ancestor-authorization-for-nested-viewsets" in entry
    assert "docs/reference/nested.md#ancestor-authorization" in entry
    assert "ancestor-authorization" in _anchors(NESTED_MD)
    # the reference page's database section links the anchored selector migration
    databases = _section(NESTED_MD.read_text(), "### Databases")
    assert "../migrating-1.0.md#nested-write-database-selection" in databases


def _surface(text: str) -> str:
    """Wrap-, backtick- and case-independent release prose for term checks."""
    return _flat(text).replace('all-"none"', "all-none").lower()


def test_both_release_surfaces_state_the_same_migration_contract():
    entry = _surface(_ancestor_breaking_entry())
    migration = _surface(_section(MIGRATING_MD.read_text(), ANCESTOR_MIGRATION))
    for surface in (entry, migration):
        for term in (
            # removed fields, explicit None / old default rejection, no translation
            "cv_guardian_parent_permission",
            "cv_guardian_parent_create_permission",
            "ValidationError",
            "old default",
            "nothing is translated",
            'AncestorPolicy(provider="none")',
            # Write defaults and the provider chosen by the parent's class
            "need `change` on the nearest" if surface is entry else "parent `change`",
            "cascade=False",
            "GuardianViewSet",
            "model permission",
            "object grant",
            # independent ancestor and view fallback
            "cv_guardian_accept_global_perms",
            "AncestorPolicy(accept_global_perms=True)",
            # exact custom entries in both modes and all-none, classified built-in and top-level exceptions
            '{"approve": AncestorPermissions(nearest="change", higher="view")}',
            "viewset.E268",
            "ImproperlyConfigured",
            "all-none",
            "classified built-in",
            "top-level",
            # nested manage
            "manage setting",
            "or group",
            # boundaries
            "get_queryset()",
            "Resource",
            "immediate parent",
        ):
            assert _surface(term) in surface, term


def test_both_release_surfaces_explain_the_nested_selector_refusal():
    lifecycle_anchor = "request_lifecycle.md#nested-viewsets-instance-hinted-write-routing"
    assert "nested-viewsets-instance-hinted-write-routing" in _anchors(LIFECYCLE_MD)
    entry = _ancestor_breaking_entry()
    migration = _section(_section(MIGRATING_MD.read_text(), ANCESTOR_MIGRATION), "#### Nested write database selection")
    assert f"docs/reference/{lifecycle_anchor}" in entry
    assert f"reference/{lifecycle_anchor}" in migration
    for surface in (_surface(entry), _surface(migration)):
        for term in (
            "cv_get_db_alias()",
            "instance",
            "ImproperlyConfigured",
            "hook or write",
            "cv_atomic = False",
            "default",
            "top-level",
            "Delete",
            "workflow",
            "Resource",
            ".using()",
        ):
            assert _surface(term) in surface, term
        # the refusal is explained, never worked around
        assert "do not" in surface and "forc" in surface and "hint" in surface
    # the behavior is proven once, by the executed router example of the linked lifecycle section
    assert "class BookShardRouter" in _fence(*DATABASE_REFUSAL)


# ── custom permission recipe (phase 06.22, #341) ─────────────────────────────


def test_published_permission_recipe_passes_the_startup_check(published):
    from crud_views.checks import check_ancestor_declarations
    from crud_views.lib.ancestors import _declared_permission_keys

    ns = published.run(*CUSTOM_PERMISSION)
    assert [m for m in check_ancestor_declarations() if m.id == "viewset.E269"] == []
    assert ns["AuthorContactView"].cv_permission == "contact"
    assert ns["cv_author"].name == "author"
    assert "contact" in _declared_permission_keys(Author)
    assert Author._meta.ordering == ("order",)
    assert ("contact_author", "Can contact an author") in Author._meta.permissions
    assert '("contact_author", "Can contact an author")' in _fence(
        CUSTOM_FORM_MD, "### Declare the permission on the model"
    )


def test_misspelled_recipe_key_fails_the_startup_check(published, monkeypatch):
    from crud_views.checks import check_ancestor_declarations

    ns = published.run(*CUSTOM_PERMISSION)
    monkeypatch.setattr(ns["AuthorContactView"], "cv_permission", "contct")
    ours = [m for m in check_ancestor_declarations() if m.id == "viewset.E269"]
    assert len(ours) == 1
    assert ours[0].obj.name == "author"
    assert ours[0].msg == "cv_permission 'contct' of view 'contact' is not declared on model app.Author"
    assert 'add ("contct_author", "...") to Author.Meta.permissions' in ours[0].hint


def test_custom_permission_recipe_is_cross_linked():
    assert "a-permission-of-its-own" in _anchors(CUSTOM_FORM_MD)
    assert "custom_form_view.md#a-permission-of-its-own" in _section(ACTION_VIEW_MD.read_text(), "## View Classes")
    guardian = _flat(_section(GUARDIAN_MD.read_text(), "### Configured content-type defaults"))
    for term in ("viewset.E269", "GuardianViewSet", "skips", "request time", "ImproperlyConfigured"):
        assert term in guardian
    assert "permission-key-diagnostics" in _anchors(GUARDIAN_MD)
    nested = _section(NESTED_MD.read_text(), "### Configuration errors")
    assert "viewset.E269" in _flat(nested)
    assert "both core ViewSets" in _flat(nested)
    assert "| a required key missing from the permission map of a checked ancestor |" in nested
    assert "cv_permission" in _section(CUSTOM_FORM_MD.read_text(), "## Configuration")
    assert "example-permissions-for-a-nested-book-viewset" in _anchors(NESTED_MD)
    assert "configured-content-type-defaults" in _anchors(GUARDIAN_MD)
    unreleased = _section(CHANGELOG_MD.read_text(), "## Unreleased")
    added = _section(unreleased, "### Added")
    assert "issues/341" in added
    assert "docs/reference/custom_form_view.md#a-permission-of-its-own" in added
    assert "issues/341" not in _section(unreleased, "### Breaking")
