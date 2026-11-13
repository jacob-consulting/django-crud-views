"""
Phase 06.18 plan 10 Task 2 — measured query cost of ancestor authorization against the pre-edit baseline (ANCE-08).

The matrix replays plan 01's ancestor-only observation fixtures (``test_ancestor_authorization._observation_chain``):
one ancestor (Publisher → Book) and three ancestors (Publisher → Book → BookNote → test-scoped leaf), plain and
Guardian leaf views, list / object (detail) / create (form GET), full cascade and nearest-only, each with a cold
and a warm permission vocabulary — 24 depth/provider/operation/mode cells. The pre-edit numbers of the same
fixtures (source ``d5567ba2``, plan 01) are embedded below; legacy had no modes, so its single observation is the
base of both mode cells.

Manage projection is excluded after registration from the concrete leaf classes so its developer-membership
query is not attributed to ancestry. The real projection cost is measured separately in test_manage.py.

Every request is split into the ancestor guard (``ancestors._authorize_ancestors``) and the rest of the request.
The assertions are about attribution and prohibited work, never a query budget:

* every response is the normal 200, cold and warm;
* the guard resolves each ancestor exactly once, outermost first, and no ancestor queryset runs outside it (no
  repeated resolution, no legacy parent gate left in the local path);
* full cascade evaluates one gate per ancestor, nearest-only exactly one — the nearest; higher ancestors are
  never evaluated (an event list, not inferred from totals), and no gate repeats within a request;
* plain views: the work outside the guard equals the pre-edit total, so the guard is the only added work;
* warm requests still query permission rows inside the guard: no persistent access cache hides the cost;
* top-level requests do no ancestor work at all.

A supplementary set renders the leaf list with its create button: the button's immediate-parent helper adds one
gate on the guard-resolved parent and no lookup, separate from the guard. Set ``CV_ANCESTOR_COSTS_DIR`` to write
one JSON file per depth/provider (06.18-COSTS.md is generated from those files). Cold cells clear the ViewSet
vocabulary, ContentType and ``_VOCAB_CACHE`` caches before one request; the warm cell repeats it immediately.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

import tests.test1.project.urls  # noqa: F401 - registers the shared app ViewSets before any registry snapshot
from crud_views.lib import ancestors
from crud_views.lib.viewset import ViewSet
from tests.test1 import test_ancestor_authorization as obs
from tests.test1.app.models import Book, BookNote, Publisher

BASELINE_SHA = "d5567ba2964b1375be2292ffa414bfb2f5cd6292"
# pre-edit totals (cold, warm) per operation, plan 01 evidence/06.18-01/baseline-observations/*.json
BASELINE = {
    (1, "plain"): {"list": (1, 1), "object": (1, 1), "create": (0, 0)},
    (3, "plain"): {"list": (1, 1), "object": (1, 1), "create": (0, 0)},
    (1, "guardian"): {"list": (11, 6), "object": (12, 8), "create": (7, 5)},
    (3, "guardian"): {"list": (11, 6), "object": (12, 8), "create": (7, 5)},
}
MODES = {"full": True, "nearest": False}
DEPTHS = (
    pytest.param(1, id="depth1", marks=pytest.mark.django_db),
    pytest.param(3, id="depth3", marks=pytest.mark.django_db(transaction=True)),
)
PROVIDERS = ("plain", "guardian")


# ── request probe ────────────────────────────────────────────────────────────


class _Probe:
    """Per-request record of the guard's SQL and of every ancestor-relevant event, tagged with the phase it ran
    in (``guard`` inside ``_authorize_ancestors``, ``rest`` anywhere else in the request)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = "rest"
        self.guard_calls = 0
        self.guard_sql: list[str] = []
        self.gates: list[tuple[str, str, str, object]] = []  # (phase, ViewSet, permission, object pk)
        self.querysets: list[tuple[str, str]] = []  # (phase, ViewSet)


@pytest.fixture
def probe(monkeypatch):
    from crud_views_guardian.lib.viewset import GuardianViewSet

    recorder = _Probe()
    original_guard = ancestors._authorize_ancestors
    original_queryset = ViewSet.get_queryset
    gates = {cls: cls.__dict__["_ancestor_has_permission"] for cls in (ViewSet, GuardianViewSet)}

    def guard(view):
        recorder.guard_calls += 1
        recorder.phase = "guard"
        with CaptureQueriesContext(connection) as captured:
            try:
                return original_guard(view)
            finally:
                recorder.phase = "rest"
                recorder.guard_sql.extend(query["sql"] for query in captured.captured_queries)

    def queryset_spy(self, view):
        recorder.querysets.append((recorder.phase, self.name))
        return original_queryset(self, view)

    def gate_spy(original):
        def spy(self, user, permission, obj, *, view):
            recorder.gates.append((recorder.phase, self.name, permission, obj.pk))
            return original(self, user, permission, obj, view=view)

        return spy

    monkeypatch.setattr(ancestors, "_authorize_ancestors", guard)
    monkeypatch.setattr(ViewSet, "get_queryset", queryset_spy)
    for cls, original in gates.items():
        monkeypatch.setattr(cls, "_ancestor_has_permission", gate_spy(original))
    return recorder


def _tables(sqls) -> Counter:
    tables = Counter()
    for sql in sqls:
        match = obs._TABLE.search(sql)
        tables[match.group(1) if match else "other"] += 1
    return tables


def _measure(client: Client, url: str, recorder: _Probe) -> dict:
    recorder.reset()
    with CaptureQueriesContext(connection) as captured:
        response = client.get(url)
    total = _tables(query["sql"] for query in captured.captured_queries)
    guard = _tables(recorder.guard_sql)
    return {
        "status": response.status_code,
        "total": sum(total.values()),
        "guard": sum(guard.values()),
        "rest": sum(total.values()) - sum(guard.values()),
        "by_table": dict(total),
        "guard_by_table": dict(guard),
        "rest_by_table": dict(total - guard),
        "guard_calls": recorder.guard_calls,
        "gates": list(recorder.gates),
        "querysets": list(recorder.querysets),
    }


# ── assertions shared by every nested cell ───────────────────────────────────


def _ancestor_names(chain) -> list[str]:
    return [vs.name for vs in chain.viewsets[:-1]]


def _assert_nested_cell(chain, mode, measured, *, helper_gates=0):
    ancestors_outer_first = _ancestor_names(chain)
    assert measured["status"] == 200, measured
    assert measured["guard_calls"] == 1
    # each ancestor resolved exactly once, in the guard, outermost first; no ancestor queryset anywhere else
    guard_querysets = [name for phase, name in measured["querysets"] if phase == "guard"]
    assert guard_querysets == ancestors_outer_first
    assert not [name for phase, name in measured["querysets"] if phase == "rest" and name in ancestors_outer_first]
    # gates: full → every ancestor once, nearest-only → the nearest only; higher never evaluated nearest-only
    guard_gates = [name for phase, name, _, _ in measured["gates"] if phase == "guard"]
    expected = ancestors_outer_first if mode == "full" else ancestors_outer_first[-1:]
    assert guard_gates == expected
    higher = set(ancestors_outer_first[:-1])
    if mode == "nearest":
        assert [gate for gate in measured["gates"] if gate[1] in higher] == []
    assert len(set(measured["gates"])) == len(measured["gates"])  # no identical gate twice in one request
    rest_gates = [gate for gate in measured["gates"] if gate[0] == "rest"]
    assert len(rest_gates) == helper_gates
    assert all(gate[1] == ancestors_outer_first[-1] for gate in rest_gates)  # helpers: immediate parent only
    # ancestor rows are read only by the guard (no legacy parent gate or second resolution in the local path)
    ancestor_tables = {vs.model._meta.db_table for vs in chain.viewsets[:-1]}
    assert not ancestor_tables & set(measured["rest_by_table"])


def _write(label, payload):
    out = os.environ.get("CV_ANCESTOR_COSTS_DIR")
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"{label}.json"), "w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str)


def _run_matrix(chain, depth, provider, recorder, *, label_suffix="", helper_gates=0, ops=None):
    cells = {}
    for mode, cascade in MODES.items():
        obs._apply_mode(chain.leaf_vs, cascade)
        for op, url in chain.urls().items():
            if ops is not None and op not in ops:
                continue
            obs._reset_vocabulary(chain.viewsets)
            cold = _measure(chain.client, url, recorder)
            warm = _measure(chain.client, url, recorder)
            for vocab, measured in (("cold", cold), ("warm", warm)):
                _assert_nested_cell(chain, mode, measured, helper_gates=helper_gates)
                # warm requests still read permission rows in the guard: no persistent access cache
                assert measured["guard_by_table"].get("auth_permission", 0) > 0, (mode, op, vocab, measured)
            cells[f"{mode}/{op}"] = {"cold": cold, "warm": warm}
    label = f"depth{depth}-{provider}{label_suffix}"
    _write(
        label,
        {"cell": label, "meta": obs._source_metadata(), "baseline_sha": BASELINE_SHA, "observations": cells},
    )
    return cells


@contextmanager
def _chain_context(depth, provider):
    """Ancestor-only chain without manage projection, inside the test-scoped deep leaf when depth is 3."""
    guardian = provider == "guardian"

    def routed(models_chain, fk_names):
        def build(sfx):
            chain = obs._observation_chain(sfx, models_chain, fk_names, guardian)
            return chain, [chain.leaf_vs]

        return obs.isolated_routes(build)

    if depth == 1:
        with routed([Publisher, Book], ["publisher"]) as chain:
            yield chain
        return
    with (
        obs._deep_leaf_model() as leaf,
        routed([Publisher, Book, BookNote, leaf], ["publisher", "book", "note"]) as chain,
    ):
        yield chain


# ── the 24-cell matrix ───────────────────────────────────────────────────────


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("depth", DEPTHS)
def test_cost_matrix_against_the_pre_edit_baseline(depth, provider, probe):
    with _chain_context(depth, provider) as chain:
        for key in ("list", "detail", "create"):
            assert chain.leaf_vs.get_view_class(key).cv_context_actions == []
        cells = _run_matrix(chain, depth, provider, probe)
    assert len(cells) == 6  # 2 modes x 3 operations, each cold and warm
    for name, cell in cells.items():
        op = name.split("/")[1]
        for index, vocab in enumerate(("cold", "warm")):
            measured, legacy_total = cell[vocab], BASELINE[(depth, provider)][op][index]
            if provider == "plain":
                # the guard is the only added work: everything else in the request is the pre-edit request
                assert measured["rest"] == legacy_total, (name, vocab, measured)


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("depth", DEPTHS)
def test_render_helper_work_is_separate_from_the_guard(depth, provider, probe):
    """Supplementary: the nested list renders its create button. Guardian's immediate-parent helper adds one gate
    on the guard-resolved parent (no lookup, no farther ancestor); the core create button adds no ancestor gate."""
    with _chain_context(depth, provider) as chain:
        chain.leaf_vs.get_all_views()["list"].cv_context_actions = ["create"]
        helper_gates = 1 if provider == "guardian" else 0
        _run_matrix(
            chain, depth, provider, probe, label_suffix="-list-with-create-button", helper_gates=helper_gates,
            ops={"list"},
        )  # fmt: skip


# ── top-level controls ───────────────────────────────────────────────────────


@pytest.fixture
def top_level():
    from crud_views.lib.views import DetailView, ListView
    from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def build(sfx):
        plain = ViewSet(model=Publisher, name=f"costtop{sfx}")
        guarded = GuardianViewSet(model=Publisher, name=f"costgtop{sfx}")
        common = {"cv_list_actions": [], "cv_context_actions": []}
        type("TopList", (ListView,), {"cv_viewset": plain, **common})
        type("TopDetail", (DetailView,), {"cv_viewset": plain, **common})
        type("GTopList", (GuardianListViewPermissionRequired,), {"cv_viewset": guarded, **common})
        type("GTopDetail", (GuardianDetailViewPermissionRequired,), {"cv_viewset": guarded, **common})
        return SimpleNamespace(plain=plain, guarded=guarded), [plain, guarded]

    with obs.isolated_routes(build) as ns:
        yield ns


@pytest.mark.django_db
def test_top_level_requests_do_no_ancestor_work(top_level, probe, monkeypatch):
    from guardian.shortcuts import assign_perm

    walks = []
    original_walk = ancestors._validate_ancestor_structure
    monkeypatch.setattr(
        ancestors, "_validate_ancestor_structure", lambda *a, **k: walks.append(a) or original_walk(*a, **k)
    )
    publisher = Publisher.objects.create(name="top")
    user = obs._user("cost_top")
    assign_perm(top_level.guarded.permissions["view"], user, publisher)
    client = obs._client(user)
    results = {}
    for label, vs in (("plain", top_level.plain), ("guardian", top_level.guarded)):
        for key, kwargs in (("list", {}), ("detail", {"pk": publisher.pk})):
            measured = _measure(client, obs._url(vs, key, **kwargs), probe)
            assert measured["status"] == 200, (label, key, measured)
            # the guard returns at once (entered by CrudView.dispatch and, for permission-required views, again by
            # their dispatch, since no state is stored): no queries, no walk, no gate, only the view's own queryset
            assert measured["guard_calls"] >= 1 and measured["guard"] == 0, (label, key, measured)
            assert measured["gates"] == []
            assert {name for _, name in measured["querysets"]} <= {vs.name}
            results[f"{label}/{key}"] = measured
    assert walks == []
    _write("top-level", {"cell": "top-level", "meta": obs._source_metadata(), "observations": results})
