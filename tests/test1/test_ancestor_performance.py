"""Query measurements of nested requests for the ancestor-authorization performance note, plus the measurable-work
contracts: no ancestor work on top-level requests and no higher permission evaluation in nearest-only mode.

Each measured case builds an isolated chain (``tests.test1.ancestor_cases``), grants every permission any mode needs,
and issues one cold request (fresh content-type cache and permission vocabulary) followed by one warm repeat of the
same request. ``mode`` is ``full`` (global cascade) or ``nearest`` (``AncestorPolicy(cascade=False)`` on the requested
ViewSet); the ``legacy`` baseline (before ancestor policies existed) is recorded in the performance note. Counts are
recorded, not asserted: they vary across Django versions and the note explains them.

Set ``CV_ANCESTOR_PERF_REPORT=<path>`` to append one JSON line per measured request for the performance note.
"""

import json
import os
import re
from collections import Counter

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from crud_views.lib.viewset import AncestorPolicy, ViewSet
from tests.test1.ancestor_cases import (
    CHECKED,
    EVENTS,
    FixedTemplateMixin,
    ancestor_routes,
    ancestor_scope,
    chain_objects,
    grant_all,
    traced_chain,
)
from tests.test1.app.models import AncestorAttachment, Book, BookNote, Publisher

_TABLE = re.compile(r'\bFROM\s+"([^"]+)"', re.IGNORECASE)
_WRITE = re.compile(r'^\s*(INSERT INTO|UPDATE|DELETE FROM)\s+"([^"]+)"', re.IGNORECASE)
_GUARDIAN_JOIN = re.compile(r'\bJOIN\s+"(guardian_[^"]+)"', re.IGNORECASE)

# Publisher (top) → Book (mid) → BookNote (near) → AncestorAttachment (endpoint)
THREE = (
    (Publisher, None, "top"),
    (Book, "publisher", "mid"),
    (BookNote, "book", "near"),
    (AncestorAttachment, "note", "child"),
)


def _category(sql: str) -> str:
    """The table a statement reads (or writes); a Guardian grant lookup is named by its grant table."""
    match = _WRITE.match(sql)
    if match:
        return f"{match.group(1).split()[0].lower()} {match.group(2)}"
    match = _GUARDIAN_JOIN.search(sql)
    if match:
        return match.group(1)
    match = _TABLE.search(sql)
    return match.group(1) if match else sql.split()[0].upper()


def _measure(client: Client, url: str) -> tuple[int, int, dict[str, int]]:
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url)
    categories = Counter(_category(query["sql"]) for query in ctx.captured_queries)
    return response.status_code, len(ctx.captured_queries), dict(sorted(categories.items()))


def _report(record: dict) -> None:
    path = os.environ.get("CV_ANCESTOR_PERF_REPORT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


@pytest.fixture(autouse=True)
def events():
    EVENTS.clear()
    CHECKED.clear()
    yield EVENTS
    EVENTS.clear()
    CHECKED.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["full", "nearest"])
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.parametrize("depth", [1, 3])
@pytest.mark.parametrize("key", ["list", "detail", "create"])
def test_one_and_three_level_query_costs(mode, family, depth, key):
    from django.contrib.auth.models import User

    viewset_kwargs = {depth: {"ancestor_policy": AncestorPolicy(cascade=False)}} if mode == "nearest" else {}
    with ancestor_routes(family, depth, viewset_kwargs) as routes:
        ancestors, rows = chain_objects(depth)
        user = User.objects.create_user(username="ancestor-perf", password="password")
        grant_all(user, routes, ancestors, rows)
        client = Client(raise_request_exception=True)
        client.force_login(user)
        url = routes.url(key, ancestors, obj=rows[0] if key == "detail" else None)

        routes.reset_vocabulary()
        cold = _measure(client, url)
        warm = _measure(client, url)

        for label, (status, total, categories) in (("cold", cold), ("warm", warm)):
            assert status == 200, (label, url, status)
            _report(
                {
                    "mode": mode,
                    "family": family,
                    "depth": depth,
                    "key": key,
                    "phase": label,
                    "status": status,
                    "queries": total,
                    "categories": categories,
                }
            )


def _endpoint_views(scope, viewset, family: str) -> None:
    """Fixed-template list, detail and create views of ``family`` on a top-level ``viewset``."""
    from crud_views.lib.views import CreateView, DetailView, ListView

    if family == "guardian":
        from crud_views_guardian.lib.views import (
            GuardianCreateViewPermissionRequired as CreateView,
        )
        from crud_views_guardian.lib.views import (
            GuardianDetailViewPermissionRequired as DetailView,
        )
        from crud_views_guardian.lib.views import (
            GuardianListViewPermissionRequired as ListView,
        )
    attrs = {"cv_viewset": viewset, "__module__": __name__}
    type(f"TopList{scope.sfx}", (FixedTemplateMixin, ListView), dict(attrs))
    type(f"TopDetail{scope.sfx}", (FixedTemplateMixin, DetailView), dict(attrs))
    type(f"TopCreate{scope.sfx}", (FixedTemplateMixin, CreateView), {**attrs, "fields": ["name"]})


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.parametrize("key", ["list", "detail", "create"])
def test_no_top_level_ancestor_queries(monkeypatch, family, key):
    """A top-level request never enters ancestor traversal, a provider or the authorization-route validation."""
    from django.contrib.auth.models import Permission, User

    from crud_views.lib.view import ancestors
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def fail(*args, **kwargs):
        raise AssertionError("ancestor work on a top-level request")

    for target, name in (
        (ancestors, "authorize_ancestors"),
        (ancestors, "walk_ancestors"),
        (ancestors, "selected_gates"),
        (ancestors, "validate_authorization_databases"),
        (ViewSet, "_ancestor_has_permission"),
        (GuardianViewSet, "_ancestor_has_permission"),
    ):
        monkeypatch.setattr(target, name, fail)

    with ancestor_scope() as scope:
        viewset_class = GuardianViewSet if family == "guardian" else ViewSet
        viewset = scope.viewset(viewset_class, model=Publisher, name=scope.name("anctop"))
        _endpoint_views(scope, viewset, family)
        scope.mount([viewset])
        publisher = Publisher.objects.create(name="Top")
        Publisher.objects.create(name="Top 2")
        user = User.objects.create_user(username="ancestor-top", password="password")
        user.user_permissions.add(Permission.objects.get(codename="add_publisher", content_type__app_label="app"))
        if family == "guardian":
            viewset.assign_perm("view", user, publisher)
        client = Client(raise_request_exception=True)
        client.force_login(user)
        kwargs = {"pk": publisher.pk} if key == "detail" else {}
        status, total, categories = _measure(client, reverse(viewset.get_router_name(key), kwargs=kwargs))

    assert status == 200
    assert EVENTS == [] and CHECKED == []
    _report(
        {
            "mode": "top-level",
            "family": family,
            "depth": 0,
            "key": key,
            "phase": "cold",
            "status": status,
            "queries": total,
            "categories": categories,
        }
    )


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
def test_nearest_only_never_checks_higher_permissions(family):
    """Nearest-only evaluates only the nearest protected gate; the higher levels are still resolved through their
    querysets (existence and relationship reads), and the same grants fail under full cascade at the outermost gate."""
    from django.contrib.auth.models import Permission, User

    from crud_views.lib.views import ListView
    from tests.test1.test_ancestor_guardian import TracedGuardianViewSet

    with ancestor_scope() as scope:
        classes = dict.fromkeys(range(3), TracedGuardianViewSet) if family == "guardian" else {}
        nearest = traced_chain(scope, THREE, {3: AncestorPolicy(cascade=False)}, classes, prefix="n")
        full = traced_chain(scope, THREE, {}, classes, prefix="f")
        for routes in (nearest, full):
            type(
                f"NearestList{routes.endpoint.name}",
                (FixedTemplateMixin, ListView),
                {"cv_viewset": routes.endpoint, "__module__": __name__},
            )
        scope.mount([nearest.endpoint, full.endpoint])

        publisher = Publisher.objects.create(name="P")
        book = Book.objects.create(title="B", publisher=publisher)
        note = BookNote.objects.create(book=book, note="N")
        user = User.objects.create_user(username="nearest-only", password="password")
        # only the nearest protected ancestor's Read permission; nothing on Publisher or Book
        if family == "guardian":
            nearest.viewsets[2].assign_perm("view", user, note)
            full.viewsets[2].assign_perm("view", user, note)
        else:
            user.user_permissions.add(Permission.objects.get(codename="view_booknote", content_type__app_label="app"))
        client = Client()
        client.force_login(user)

        status, _total, categories = _measure(client, nearest.url("list", [publisher, book, note]))
        assert status == 200
        assert EVENTS == ["top_queryset", "mid_queryset", "near_queryset", "near_gate", "child"]
        assert categories.get("app_publisher") == 1 and categories.get("app_book") == 1  # higher reads still occur
        if family == "core":
            assert CHECKED == [("near", "app.view_booknote")]

        EVENTS.clear()
        CHECKED.clear()
        assert client.get(full.url("list", [publisher, book, note])).status_code == 403
        assert EVENTS == ["top_queryset", "top_gate"]
