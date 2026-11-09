"""
Phase 06.18 plan 01 — ancestor authorization tracer and query observations.

Two kinds of evidence live here:

* Behavioral tracer cases for one composition only: a registered *plain* nested Book list (and the plain
  nested create that reuses the resolved parent) under a core Publisher, requested through a real URL with
  database-backed model grants. Other compositions (permission-required, Guardian, manage, Resource, custom
  families) are proven by later plans of the phase.
* A reproducible query-observation helper. It measures one- and three-ancestor plain/Guardian
  list/object/create requests with cold and warm permission vocabulary. Set ``CV_ANCESTOR_OBSERVATIONS_DIR``
  to write one JSON file per cell; without it the test only asserts that every cell responded normally.

Every fixture builds fresh, uniquely named ViewSets behind a temporary ROOT_URLCONF and restores the
ViewSet registry, the permission-vocabulary cache, URL caches and ContentType cache in ``finally``.
"""

from __future__ import annotations

import json
import os
import re
import sys
import types
import uuid
from collections import Counter
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Permission, PermissionsMixin, User
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext, isolate_apps
from django.urls import clear_url_caches, include, path, reverse

from crud_views.lib import check as check_module
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, ViewSet
from tests.test1.app.models import Book, BookNote, Publisher

# ── isolation helpers ────────────────────────────────────────────────────────


@contextmanager
def isolated_routes(build):
    """Run ``build(sfx)`` (which constructs ViewSets/views and returns ``(namespace, viewsets_to_route)``) behind
    a temporary ROOT_URLCONF; restore registry, vocabulary cache, URL caches and ContentType cache afterwards."""
    sfx = uuid.uuid4().hex[:8]
    modname = f"tests.test1._ancestor_urls_{sfx}"
    with _REGISTRY_LOCK:
        registry_snapshot = dict(_REGISTRY)
    vocab_snapshot = dict(check_module._VOCAB_CACHE)
    try:
        namespace, routed = build(sfx)
        module = types.ModuleType(modname)
        module.urlpatterns = [pattern for vs in routed for pattern in vs.urlpatterns]
        module.urlpatterns.append(path("", include("tests.test1.project.urls")))
        sys.modules[modname] = module
        clear_url_caches()
        with override_settings(ROOT_URLCONF=modname):
            clear_url_caches()
            try:
                yield namespace
            finally:
                clear_url_caches()
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(registry_snapshot)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocab_snapshot)
        sys.modules.pop(modname, None)
        clear_url_caches()
        ContentType.objects.clear_cache()


def _url(vs: ViewSet, key: str, **kwargs) -> str:
    return reverse(vs.get_router_name(key), kwargs=kwargs)


def _user(username: str, *model_perms: tuple[type[models.Model], str], superuser: bool = False) -> User:
    if superuser:
        return User.objects.create_superuser(username=username, password="pw")
    user = User.objects.create_user(username=username, password="pw")
    for model, action in model_perms:
        ct = ContentType.objects.get_for_model(model)
        user.user_permissions.add(Permission.objects.get(content_type=ct, codename=f"{action}_{ct.model}"))
    return user


def _client(user: User | None) -> Client:
    client = Client()
    if user is not None:
        client.force_login(user)
    return client


# ── ordered event spies ──────────────────────────────────────────────────────


@pytest.fixture
def events(monkeypatch):
    """Ordered request events: every ViewSet queryset call and every user permission check.

    Spies wrap existing framework seams only (``ViewSet.get_queryset`` and ``PermissionsMixin.has_perm``), so
    the same spy describes the legacy and the new request path.
    """
    recorded: list[tuple[str, str]] = []
    original_queryset = ViewSet.get_queryset
    original_has_perm = PermissionsMixin.has_perm

    def queryset_spy(self, view):
        recorded.append(("queryset", self.name))
        return original_queryset(self, view)

    def has_perm_spy(self, perm, obj=None):
        recorded.append(("has_perm", perm))
        return original_has_perm(self, perm, obj)

    monkeypatch.setattr(ViewSet, "get_queryset", queryset_spy)
    monkeypatch.setattr(PermissionsMixin, "has_perm", has_perm_spy)
    return recorded


# ── tracer composition: core Publisher → plain Book list/create ──────────────


@pytest.fixture
def ancestor_chain():
    """Core Publisher ViewSet with a plain top-level list, and a nested plain Book list/create beneath it."""
    from crud_views.lib.views import CreateView, CreateViewParentMixin, ListView

    def build(sfx):
        pub_vs = ViewSet(model=Publisher, name=f"ancpub{sfx}")

        class PublisherList(ListView):
            cv_viewset = pub_vs
            cv_list_actions = []
            cv_context_actions = []

        book_vs = ViewSet(
            model=Book, name=f"ancbook{sfx}", parent=ParentViewSet(name=pub_vs.name, attribute="publisher")
        )

        class BookList(ListView):  # deliberately plain: no endpoint-local permission gate
            cv_viewset = book_vs
            cv_list_actions = []
            cv_context_actions = []

        class BookCreate(CreateViewParentMixin, CreateView):
            cv_viewset = book_vs
            cv_context_actions = []
            fields = ["title"]

        ns = SimpleNamespace(pub_vs=pub_vs, book_vs=book_vs, PublisherList=PublisherList, BookList=BookList)
        ns.list_url = lambda publisher_pk: _url(book_vs, "list", **{f"{pub_vs.name}_pk": publisher_pk})
        ns.create_url = lambda publisher_pk: _url(book_vs, "create", **{f"{pub_vs.name}_pk": publisher_pk})
        ns.top_url = lambda: _url(pub_vs, "list")
        return ns, [pub_vs, book_vs]

    with isolated_routes(build) as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Hitchhiker", publisher=penguin)
    Book.objects.create(title="Foreign", publisher=other)
    return SimpleNamespace(penguin=penguin, other=other, book=book)


def _child_queryset_calls(events, chain) -> list:
    return [event for event in events if event == ("queryset", chain.book_vs.name)]


@pytest.mark.django_db
def test_plain_nested_list_allows_parent_model_view(ancestor_chain, world, events):
    user = _user("anc_reader", (Publisher, "view"))
    response = _client(user).get(ancestor_chain.list_url(world.penguin.pk))
    assert response.status_code == 200
    assert list(response.context["object_list"]) == [world.book]
    # ancestor resolved through its ViewSet queryset, then its gate, then the child queryset
    pub_lookup = ("queryset", ancestor_chain.pub_vs.name)
    gate = ("has_perm", "app.view_publisher")
    child = ("queryset", ancestor_chain.book_vs.name)
    assert pub_lookup in events and gate in events and child in events
    assert events.index(pub_lookup) < events.index(gate) < events.index(child)


@pytest.mark.django_db
def test_plain_nested_list_denies_without_parent_grant_before_child_queryset(ancestor_chain, world, events):
    # child grants do not substitute for the ancestor gate
    user = _user("anc_child_only", (Book, "view"), (Book, "change"), (Publisher, "change"))
    response = _client(user).get(ancestor_chain.list_url(world.penguin.pk))
    assert response.status_code == 403
    assert ("has_perm", "app.view_publisher") in events
    assert _child_queryset_calls(events, ancestor_chain) == []


@pytest.mark.django_db
def test_plain_nested_list_missing_parent_is_404_before_child_queryset(ancestor_chain, world, events):
    user = _user("anc_reader_missing", (Publisher, "view"))
    response = _client(user).get(ancestor_chain.list_url(world.penguin.pk + 1000))
    assert response.status_code == 404
    # the ancestor was reached through its ViewSet queryset; its gate and the child were not
    assert ("queryset", ancestor_chain.pub_vs.name) in events
    assert ("has_perm", "app.view_publisher") not in events
    assert _child_queryset_calls(events, ancestor_chain) == []


@pytest.mark.django_db
def test_plain_nested_list_anonymous_redirects_to_login_before_parent_lookup(ancestor_chain, world, events):
    response = Client().get(ancestor_chain.list_url(world.penguin.pk + 1000))
    assert response.status_code == 302
    assert response["Location"].startswith("/accounts/login/?next=")
    assert events == []  # no ancestor lookup, no gate, no child queryset


@pytest.mark.django_db
def test_plain_nested_list_inactive_actor_is_denied_before_parent_lookup(ancestor_chain, world, events):
    user = _user("anc_inactive", (Publisher, "view"))
    user.is_active = False
    user.save()
    # ModelBackend would turn an inactive session into AnonymousUser; keep the actor authenticated-but-inactive
    with override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.AllowAllUsersModelBackend"]):
        client = Client()
        client.force_login(user)
        response = client.get(ancestor_chain.list_url(world.penguin.pk))
    assert response.status_code == 403
    assert events == []  # denied before any ancestor lookup or permission evaluation


@pytest.mark.django_db
def test_plain_nested_list_revocation_applies_on_next_request(ancestor_chain, world):
    user = _user("anc_revoked", (Publisher, "view"))
    client = _client(user)
    assert client.get(ancestor_chain.list_url(world.penguin.pk)).status_code == 200
    user.user_permissions.clear()
    assert client.get(ancestor_chain.list_url(world.penguin.pk)).status_code == 403


@pytest.mark.django_db
def test_top_level_list_does_no_ancestor_work(ancestor_chain, world, events):
    response = Client().get(ancestor_chain.top_url())  # anonymous: a plain top-level list stays public
    assert response.status_code == 200
    assert events == [("queryset", ancestor_chain.pub_vs.name)]  # only its own existing queryset


@pytest.mark.django_db
def test_plain_nested_create_requires_parent_change(ancestor_chain, world):
    user = _user("anc_create_viewer", (Publisher, "view"))
    response = _client(user).post(ancestor_chain.create_url(world.penguin.pk), {"title": "Denied"})
    assert response.status_code == 403
    assert not Book.objects.filter(title="Denied").exists()


@pytest.mark.django_db
def test_plain_nested_create_reuses_resolved_parent(ancestor_chain, world):
    user = _user("anc_create_editor", (Publisher, "change"), (Publisher, "view"))
    client = _client(user)
    with CaptureQueriesContext(connection) as captured:
        response = client.post(ancestor_chain.create_url(world.penguin.pk), {"title": "Created"})
    assert response.status_code == 302, response.content[:500]
    created = Book.objects.get(title="Created")
    assert created.publisher_id == world.penguin.pk
    # the parent is read once (by the ancestor guard) and reused for create attachment
    parent_reads = [q["sql"] for q in captured.captured_queries if re.search(r'FROM "app_publisher"', q["sql"])]
    assert len(parent_reads) == 1, parent_reads


# ── query observations (baseline and later comparisons) ──────────────────────

_TABLE = re.compile(r'(?:FROM|INTO|UPDATE)\s+"(\w+)"')


def _measure(client: Client, url: str) -> dict:
    with CaptureQueriesContext(connection) as captured:
        response = client.get(url)
    tables = Counter()
    for query in captured.captured_queries:
        match = _TABLE.search(query["sql"])
        tables[match.group(1) if match else "other"] += 1
    return {"status": response.status_code, "total": len(captured.captured_queries), "by_table": dict(tables)}


def _reset_vocabulary(viewsets) -> None:
    for vs in viewsets:
        vs._default_permissions = None
    ContentType.objects.clear_cache()
    check_module._VOCAB_CACHE.clear()


def _mode_settings(vs: ViewSet) -> list[tuple[str, object]]:
    """(label, cascade override) pairs. Legacy source has no ancestor modes: one request, labelled as such."""
    if "ancestor_policy" not in type(vs).model_fields:
        return [("legacy-no-mode", None)]
    return [("full", True), ("nearest", False)]


def _apply_mode(vs: ViewSet, cascade) -> None:
    if cascade is not None:
        from crud_views.lib.viewset import AncestorPolicy

        vs.ancestor_policy = AncestorPolicy(cascade=cascade)


def _source_metadata() -> dict:
    import subprocess

    import django

    import crud_views

    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src"], capture_output=True, text=True, check=False
    ).stdout.strip()
    return {
        "source_sha": sha,
        "src_dirty": bool(dirty),
        "python": sys.version.split()[0],
        "django": django.get_version(),
        "crud_views_path": crud_views.__file__,
    }


def _observe(chain, label: str) -> dict:
    cells = {}
    for mode_label, cascade in _mode_settings(chain.leaf_vs):
        _apply_mode(chain.leaf_vs, cascade)
        for op, url in chain.urls().items():
            _reset_vocabulary(chain.viewsets)
            cold = _measure(chain.client, url)
            warm = _measure(chain.client, url)
            cells[f"{mode_label}/{op}"] = {"cold": cold, "warm": warm}
    for name, cell in cells.items():
        for vocab in ("cold", "warm"):
            assert cell[vocab]["status"] == 200, (label, name, vocab, cell[vocab])
    result = {"cell": label, "meta": _source_metadata(), "observations": cells}
    out = os.environ.get("CV_ANCESTOR_OBSERVATIONS_DIR")
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"{label}.json"), "w") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
    return result


def _guardian_grant(user, viewset, actions, obj) -> None:
    from guardian.shortcuts import assign_perm

    for action in actions:
        assign_perm(viewset.permissions[action], user, obj)


def _model_grant(user, viewset, actions) -> None:
    for action in actions:
        app_label, codename = viewset.permissions[action].split(".")
        user.user_permissions.add(Permission.objects.get(content_type__app_label=app_label, codename=codename))


def _build_chain(sfx, models_chain, guardian: bool, fk_names):
    """ViewSets over ``models_chain`` (outermost first, leaf last) with list/detail/create on the leaf."""
    from crud_views.lib.views import (
        CreateView,
        CreateViewParentMixin,
        DetailView,
        ListView,
    )
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    vs_class = GuardianViewSet if guardian else ViewSet
    viewsets = []
    parent = None
    for index, model in enumerate(models_chain):
        kwargs = {"model": model, "name": f"obs{'g' if guardian else 'p'}{index}{sfx}"}
        if parent is not None:
            kwargs["parent"] = ParentViewSet(name=parent.name, attribute=fk_names[index - 1])
        parent = vs_class(**kwargs)
        viewsets.append(parent)
    leaf_vs = viewsets[-1]
    list_base = GuardianListViewPermissionRequired if guardian else ListView
    detail_base = GuardianDetailViewPermissionRequired if guardian else DetailView
    create_base = GuardianCreateViewPermissionRequired if guardian else CreateView
    leaf_field = next(f.name for f in models_chain[-1]._meta.fields if isinstance(f, models.CharField))

    type("ObsList", (list_base,), {"cv_viewset": leaf_vs, "cv_list_actions": [], "cv_context_actions": []})
    type("ObsDetail", (detail_base,), {"cv_viewset": leaf_vs, "cv_context_actions": []})
    type(
        "ObsCreate",
        (CreateViewParentMixin, create_base),
        {"cv_viewset": leaf_vs, "cv_context_actions": [], "fields": [leaf_field]},
    )
    return viewsets


def _chain_objects(models_chain, fk_names):
    objects = []
    parent = None
    for index, model in enumerate(models_chain):
        values = {}
        char_field = next(f.name for f in model._meta.fields if isinstance(f, models.CharField))
        values[char_field] = f"obs-{model._meta.model_name}"
        if parent is not None:
            values[fk_names[index - 1]] = parent
        parent = model.objects.create(**values)
        objects.append(parent)
    return objects


def _observation_chain(sfx, models_chain, fk_names, guardian: bool):
    viewsets = _build_chain(sfx, models_chain, guardian, fk_names)
    objects = _chain_objects(models_chain, fk_names)
    leaf_vs, leaf = viewsets[-1], objects[-1]
    parent_kwargs = {f"{vs.name}_pk": obj.pk for vs, obj in zip(viewsets[:-1], objects[:-1], strict=True)}
    user = User.objects.create_user(username=f"observer{sfx}{int(guardian)}", password="pw")
    for vs, obj in zip(viewsets[:-1], objects[:-1], strict=True):
        _model_grant(user, vs, ("view", "change"))  # satisfies the model-provider ancestor defaults
        if guardian:
            _guardian_grant(user, vs, ("view", "change"), obj)  # legacy/object-provider parent gates
    if guardian:
        _guardian_grant(user, leaf_vs, ("view",), leaf)  # local object gate and strict list filter

    def urls():  # reversed lazily, once the temporary URLconf is active
        return {
            "list": _url(leaf_vs, "list", **parent_kwargs),
            "object": _url(leaf_vs, "detail", pk=leaf.pk, **parent_kwargs),
            "create": _url(leaf_vs, "create", **parent_kwargs),
        }

    return SimpleNamespace(viewsets=viewsets, leaf_vs=leaf_vs, urls=urls, client=_client(user))


@contextmanager
def _deep_leaf_model():
    """A test-scoped fourth level below Publisher → Book → BookNote, with its own table and permission rows."""
    with isolate_apps("tests.test1.app"):

        class AncestorObservationLeaf(models.Model):
            note = models.ForeignKey(BookNote, on_delete=models.CASCADE)
            text = models.CharField(max_length=100)

            class Meta:
                app_label = "app"

        with connection.schema_editor() as editor:
            editor.create_model(AncestorObservationLeaf)
        try:
            ct = ContentType.objects.get_for_model(AncestorObservationLeaf)
            for action in ("add", "change", "delete", "view"):
                Permission.objects.get_or_create(
                    content_type=ct, codename=f"{action}_{ct.model}", defaults={"name": f"Can {action} leaf"}
                )
            yield AncestorObservationLeaf
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(AncestorObservationLeaf)
            ContentType.objects.clear_cache()


@pytest.mark.parametrize("guardian", [False, True], ids=["plain", "guardian"])
@pytest.mark.django_db
def test_query_observations_one_ancestor(guardian):
    def build(sfx):
        chain = _observation_chain(sfx, [Publisher, Book], ["publisher"], guardian)
        return chain, [chain.leaf_vs]

    with isolated_routes(build) as chain:
        _observe(chain, f"depth1-{'guardian' if guardian else 'plain'}")


@pytest.mark.parametrize("guardian", [False, True], ids=["plain", "guardian"])
@pytest.mark.django_db(transaction=True)
def test_query_observations_three_ancestors(guardian):
    with _deep_leaf_model() as Leaf:

        def build(sfx):
            chain = _observation_chain(sfx, [Publisher, Book, BookNote, Leaf], ["publisher", "book", "note"], guardian)
            return chain, [chain.leaf_vs]

        with isolated_routes(build) as chain:
            _observe(chain, f"depth3-{'guardian' if guardian else 'plain'}")
