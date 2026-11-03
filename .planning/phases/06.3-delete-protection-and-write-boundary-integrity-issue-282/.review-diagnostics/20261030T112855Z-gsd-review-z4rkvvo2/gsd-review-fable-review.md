# Cross-AI Plan Review — Phase 06.3, cycle 1, package `1a82767`

**Review basis.** HEAD is `1a827674` (matches the committed package). I read DESIGN, CONTEXT, RESEARCH, VALIDATION, PATTERNS and all nine plans, plus the cited repository source (`src/crud_views/lib/views/delete.py`, `mixins.py`, `view/base.py`, Guardian `views.py`/`viewset.py`/`mixins.py`, both delete templates, `tests/test1/test_delete.py`, `test_transactions.py`, `test_guardian_*`, `test_authorization_*`, `test_polymorphic.py`, `conftest.py`, `app/models.py`, docs and changelog). I also ran read-only probes against the cached nox environments: a diff of Django 4.2.30 vs 6.0.9 `deletion.py`, `Model.delete` in both, `NestedObjects`, the router, and the installed `polymorphic` and `ordered_model` `delete` overrides. No tests were executed and no files were changed.

**Verdict: approve with mandatory revisions.** The architecture is sound and the task decomposition is coherent, but one process defect (01-01 gate), one design gap that hits two of the package's own extension apps (library `delete` overrides), and a test-ownership gap between plans 02/03/04 need fixing before DEL-01 approval. Details follow; design-level findings first because several plans inherit them.

## Design-level findings (inherited by multiple plans)

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D1 | HIGH | **Library `Model.delete` overrides are classified as unknown.** `OrderedModelBase.delete` and `PolymorphicModel.delete` are real overrides, so under DESIGN every ordered-model or polymorphic delete page shows the incomplete-preview notice forever and loses the friendly native stale-protection backstop (custom path propagates). Both are shipped extras of this package (`ordered`, `polymorphic`). No plan mentions `ordered_model` at all; 07-02 accepts polymorphic as "incomplete until explicitly covered" with nobody covering it. The `polymorphic` override with default `keep_parents=False` is a pure `super().delete(using=using, keep_parents=keep_parents)` pass-through; the `ordered_model` override does a sibling reorder update then `super().delete`. Both are auditable by `__func__` identity. | `.nox/crispy_floor-3-12-django-6-0/lib/python3.12/site-packages/polymorphic/models.py:244-276`; `.../ordered_model/models.py:225`; `06.3-DESIGN.md:78`; `tests/test1/app/models.py:13` (`Author(OrderedModel)` backs `/author/…/delete/`, `author_modal`, `guardian_author`), `:168` (`Vehicle(PolymorphicModel)`); `tests/test1/test_form_buttons_golden.py:124-126` (the delete golden page is an Author page) |
| D2 | MEDIUM | **The nested tree shape is an undocumented contract the inspector must reproduce.** `NestedObjects.nested()` returns a root-inclusive `[obj, [children…], …]` list with edges from `getattr(obj, related_name)`. Four consumers depend on exactly that shape, and tests pass string labels through it. DESIGN says provider rows "merge as extra tree branches" without saying where they attach. | `django/contrib/admin/utils.py:186-243`; `src/crud_views/lib/views/delete.py:246-273, 285-297`; `src/crud_views_guardian/lib/views.py:97-107`; `tests/test1/test_guardian_delete.py:235-246`; `tests/test1/test_guardian_inactive.py:443-447`; `06.3-DESIGN.md:107` |
| D3 | MEDIUM | **Native-blocker marker timing is ambiguous.** Django keeps collecting after a PROTECT to aggregate. If the adapter does the same and a later branch dispatches `SET(callable)`, the sticky flag flips and a block found *before* any callback ran is no longer friendly. DESIGN rule 3 does not say whether `_NativeDeleteBlocked` is raised immediately or at end of collect. | `06.3-DESIGN.md:154-161`; Django collect loop in `deletion.py` (aggregation of `protected_objects`) |
| D4 | MEDIUM | **Version parity deltas are small but specific.** 4.2→6.0 diff: `lazy_sub_objs` is set on every `SET(...)` and on `SET_DEFAULT` in 4.2 but only on callable `SET` in 6.0; `keep_parents` moved to `concrete_model in all_parents`; `get_del_batches` passes field objects to `bulk_batch_size`; `Model.delete` validates with `_is_pk_set()` on 6.0 vs `self.pk is None` on 4.2. 5.2 cannot be diffed locally (no cached env). | diff output above; `django/db/models/base.py:1291-1300` (6.0) vs `:1123-1132` (4.2) |
| D5 | MEDIUM | **Runtime-only signature diagnostic for `delete` without `using`.** `def delete(self):` overrides are common in Django apps; DESIGN makes them a request-time error. One existing test does exactly this. | `06.3-DESIGN.md:169-172`; `tests/test1/test_delete.py:1078` (`def delete(self)`) |
| D6 | LOW | Provider `protected` rows feed `has_protected_objects`, so a provider is a second veto path beside `cv_check_delete_protection`. Intentional and conservative, but undocumented. | `06.3-DESIGN.md:122` |
| D7 | LOW | `DeletePreviewBoundary.source_pks` as a tuple participates in equality/hash of a frozen descriptor; large cascades make descriptor comparison O(n). Use a frozenset or exclude it from `__eq__`. | `06.3-DESIGN.md:100-103` |

Confirmations in favor of the design: the default router falls back to `instance._state.db` only after routers decline (`django/db/utils.py:220-237`), so the instance-aware default is native. Guardian's `get_objects_for_user` accepts a `QuerySet` as `klass`, so the bound-candidate projection is feasible. The research's CR-02/03/04 mechanisms match the installed `Collector.collect` (handler errors aggregated inside the per-field `try`, nested collect inside it).

## 06.3-01

**Summary.** Two human checkpoints: maintainer design approval bound to a SHA-256 of DESIGN.md, and package verification before any fresh Django 5.2 install.

**Strengths.**
- Digest binding (`06.3-01-PLAN.md`, task 01-01 verify) invalidates approval on any design edit; this is the right mechanism for D-16.
- The plan refuses to infer approval from passing tests and names the exact design boundaries to present.
- Package handling follows the research SUS verdicts without relabelling.

**Concerns.**
- **HIGH.** Task 01-01 is `type="checkpoint:decision"` with **no `gate` attribute**, while 01-02 carries `gate="blocking-human"`. The executor workflow states that the default `gate="blocking"` is auto-approvable in auto mode and only `blocking-human` always surfaces to a human (`/home/alex/.codex/gsd-core/workflows/execute-plan.md:150`). As written, an auto-mode executor could satisfy DEL-01 without a maintainer. Set `gate="blocking-human"` on 01-01.
- **MEDIUM.** Approval is a single `decision: approved`. RESEARCH lists six open DEL-01 questions and this review adds D1–D3/D5; APPROVAL.md should itemize each with its decision so a blanket approval cannot hide an undecided boundary.
- **LOW.** 01-02 asks to resolve the 5.2 dependency set "without installing"; pip is unavailable (RESEARCH). Name the tool (`uv pip compile` or `uv lock`) so the executor does not improvise.

**Suggestions.** Add the gate attribute; add an itemized decision table to APPROVAL.md; name the resolver tool.

**Risk assessment.** Medium until the gate is fixed; Low afterwards.

## 06.3-02

**Summary.** Tracer: new `deletion.py`, inspector for CASCADE/PROTECT/unknown boundaries, collector adapter plus native/custom dispatcher, pinned alias, template notice, then replacement of unsafe-collection test contracts.

**Strengths.**
- Drives real registered routes with callback-event lists in both atomic modes, which is exactly what `_delete_probe` (`tests/test1/test_delete.py:789-806`) cannot provide.
- Preserves the `RelatedObjects` tuple and import path, so Guardian's filter (`src/crud_views_guardian/lib/views.py:48-56`) keeps working.
- Explicitly prohibits empty-preview substitution and handler invocation for classification.

**Concerns.**
- **HIGH (scope).** 02-01 puts the inspector, the collector adapter, the dispatcher, alias pinning, lifecycle overrides and templates in one "thinnest" task. From wave 2 on the adapter is the production write path for every delete. 02-02's verify runs all of `test_delete.py`, which already exercises RESTRICT (`Royalty`, `tests/test1/app/models.py:93`) and PROTECT, but not M2M through rows (`tests/test1/test_guardian_delete.py:304-345`), MTI (`test_polymorphic.py`) or the lifecycle controls (`test_transactions.py`). A partial adapter can ship green in waves 2–3 and break those modules until wave 5–7.
- **HIGH (ordering/ownership).** `test_delete.py` monkeypatches `cv_get_related_objects` (`:789-806`, `:825-847`, `:1403-1438`), patches `delete.NestedObjects` (`:850-873`) and `django.db.models.base.Collector` (`:1444-1469`), replaces `Publisher.delete` with `def delete(self)` (`:1078`), and imports `_cv_has_native_collection_graph` (`:1143, 1187, 1220, 1257, 1292-1396`). 02-02 says to migrate some and "move" classifier assertions to plan 04, yet 02-02's own verify requires `test_delete.py` green, plan 03 adds the `ImproperlyConfigured` legacy-override diagnostic but does **not** own `test_delete.py`, and plan 04 only reaches `test_delete.py` in wave 4. Resolve: 02-02 migrates or deletes every affected node with a traceability table, and 04 adds new provenance tests instead of moving old ones; or give plan 03 ownership of `test_delete.py`.
- **MEDIUM.** No persistent test model carries a custom `on_delete`, `SET`, `SET_DEFAULT` or private relation (`tests/test1/app/models.py`); the behaviors rely on monkeypatching class-global field metadata, the very mutation DESIGN forbids in production. The test app has no `migrations/` directory, so adding models is cheap, but no plan owns `app/models.py` (PATTERNS marks it conditional).
- **MEDIUM (D1).** Existing routes for `Author` already take the custom path under this design; decide expected notice behavior before wave 2 so `test_transactions.py:353-369` and the golden pages have a defined expectation.
- **LOW.** `_TargetDeleteBlocked` → `_NativeDeleteBlocked` rename is safe; nothing outside `delete.py` references it.

**Suggestions.** Widen 02-02's verify to `test_guardian_delete.py`, `test_polymorphic.py`, `test_transactions.py`; add the test-migration table; claim `tests/test1/app/models.py` and add one model each for `SET(callable)`, `SET_DEFAULT`, custom handler and a `delete` override without `using`.

**Risk assessment.** High. Foundational, largest surface, lowest estimate confidence.

## 06.3-03

**Summary.** Complete inspector semantics (RESTRICT closure, parents, through rows, cycles), the provider contract with per-boundary completeness, legacy-override diagnostics, and the notice/count templates with German catalog.

**Strengths.**
- Correctly keeps completeness and raw blockers out of the filterable tuple, matching the established separation (`src/crud_views/lib/views/delete.py:309-316`).
- Renders the incomplete notice outside the custom-protection branch, which the current template structure requires (`view_delete.content.html:5-20`).
- Provider validation rejects strings/HTML/dicts and cross-alias instances; exceptions propagate.

**Concerns.**
- **HIGH (D1).** The "Root Model.delete override → model_delete boundary" row makes two shipped extras permanently incomplete. Needs a DEL-01 decision: an audited library allowlist by `__func__` identity, or an explicit, tested and documented "always incomplete" disposition for ordered/polymorphic models.
- **MEDIUM (D2).** Specify the nested-list contract and add a shape-equivalence test against `NestedObjects` for native-only graphs.
- **MEDIUM.** Ownership gap for `test_delete.py` (see 02-02).
- **MEDIUM.** Two check-ID namespaces exist: `DeleteView.checks()` yields `viewset.E###` (`src/crud_views/lib/check.py:254-261`, `delete.py:177-188`), module checks use `crud_views.E###` (`src/crud_views/checks.py`). State which namespace the legacy-override error uses; `viewset.E255` is the natural successor to E254.
- **LOW.** Native collect defers non-referenced fields with `.only()`; the inspector must not, or label rendering via `__str__` becomes N+1. `NestedObjects` avoids this through `select_related` (`admin/utils.py:214-218`).
- **LOW.** Document that providers must load contributions with `.using(using)` or the `_state.db` validation rejects them.

**Suggestions.** Resolve D1/D2 in DESIGN before approval; name the check ID and namespace; add the deferral rule to the inspector contract.

**Risk assessment.** Medium-High.

## 06.3-04

**Summary.** Finish the version-audited collector adapter, establish provenance at the native branch, remove the disproven classifier, and prove commits/rollbacks with real transactions.

**Strengths.**
- Addresses CR-03's root cause (aggregation inside Django's per-field `try`) by identity dispatch and no broad catch, rather than another allowlist.
- Real `transaction=True` with persisted side-effect rows and external event lists in both atomic modes.
- Keeps `test_transactions.py` as unchanged baseline evidence.

**Concerns.**
- **MEDIUM (D3).** Define marker timing: raise `_NativeDeleteBlocked` at the first recognized PROTECT before dispatching any further handler; reconcile RESTRICT at the end and propagate if any executable handler ran before reconciliation. Test both PROTECT-before-SET and SET-before-PROTECT field orders.
- **MEDIUM (D4).** Record the parity table concretely: read `lazy_sub_objs` dynamically rather than hardcoding which handlers have it; use `_is_pk_set()` when present; mirror `all_parents` for `keep_parents`; pass field objects to `bulk_batch_size`. The 5.2 comparison is web-sourced until 09 provisions the env; say so in the evidence.
- **LOW.** `test_delete_unknown_collector_type_propagates` (`test_delete.py:1444-1469`) patches `base.Collector`, which the adapter never constructs for exact-native targets; migrate it explicitly rather than letting it pass vacuously.
- **LOW.** The `-k 'native or converter or custom_handler or parity'` selection depends on test naming; acceptable since zero collected fails the command, but name the convention in the task.

**Suggestions.** Add the timing rule and the two ordering tests; add the parity table to the 04 summary.

**Risk assessment.** Medium.

## 06.3-05

**Summary.** Second independent SQLite alias, pinned instance-aware alias through inspection/write/atomic/on_commit, and alias-aware Guardian label projection.

**Strengths.**
- Default `router.db_for_write(type(target), instance=target)` is exactly native `Model.delete` (`django/db/utils.py:220-237`, `base.py:1297`).
- Both asymmetric directions with colliding PKs and real transactions; no mirrored alias.
- Explicit refusal to claim general cross-database Guardian support.

**Concerns.**
- **MEDIUM.** Guardian topology is harder than the task text implies: `request.user` is loaded by auth middleware before the view, so a "request-local router" must already be active there; `post_migrate` creates ContentType rows per database with different ids; guardian stores `content_type_id` in grants. Define the fail-closed predicate up front (for example, hide labels when a candidate's `_state.db` differs from the alias serving `UserObjectPermission` reads) instead of the open-ended "if Guardian cannot support the topology".
- **MEDIUM.** `cv_filter_related_objects(user, related)` has no alias argument. State that `_PermittedPks` derives `using` from each candidate's `_state.db` (set by the inspector's `.using(using)`), so the public filter signature stays stable.
- **LOW.** `depends_on: ["06.3-06"]` is unnecessary (disjoint files) but harmless.
- **LOW.** Adding a second alias in `conftest.py:91-96` makes every session create the shard test DB; `@pytest.mark.django_db` defaults to `default` only, so no leakage, but measure suite-time impact in 09.
- **LOW.** When read and write routers differ, permission and state gates evaluated the read-alias row while the write-alias row is deleted; DESIGN documents this as intended. Add one assertion of which row `cv_action_enabled` saw.

**Suggestions.** Write the fail-closed predicate into DESIGN; document the `_state.db` derivation.

**Risk assessment.** Medium.

## 06.3-06

**Summary.** Shared permission-key resolver before inactive shortcuts and Guardian calls, `MappingProxyType` policy, and the bounded residual AUTH-06 review ledger.

**Strengths.**
- Smallest, best-bounded plan; red-first reproduction of IN-02/IN-03 is explicit.
- `dict(STRICT_HELPER_POLICY)` in manage (`src/crud_views_guardian/lib/views.py:296`) and the existing `is` comparisons (`tests/test1/test_guardian_policy.py:429-445`) work unchanged with a `MappingProxyType`.
- Honest `precision` backstop with a human check instead of a fake predicate.

**Concerns.**
- **LOW.** Current failures are `KeyError` (`viewset.py:81, 87, 104`); switching to `ValueError` changes the exception class for any caller catching `KeyError`. Plan 08 documents it; fine, but say so in the 06 summary too.
- **LOW.** A non-hashable `perm` (list) raises `TypeError` from `in self.permissions` before the resolver; specify the expected outcome for non-string input.
- **LOW.** 06-02 is `type="auto"` producing a review document; its automated verify only replays policy tests. Acceptable given the explicit `<human-check>`.

**Suggestions.** Add a non-string-key case; mention the exception-class change.

**Risk assessment.** Low.

## 06.3-07

**Summary.** Replay authorization and native-template boundaries with the new inspector, and exercise real polymorphic deletion and failure origin.

**Strengths.**
- Asserts context object collections, not just HTML, following `tests/test1/test_authorization_templates.py:325-339`.
- Keeps `PolymorphicModel.delete` on the custom path, which is correct for the installed override.

**Concerns.**
- **HIGH (D1).** 07-02 accepts "polymorphic preview is incomplete until explicitly covered", but no plan covers it, and `ordered_model` (`GuardianAuthorDeleteView`, `AuthorDeleteView`, `AuthorModalDeleteView`) is not mentioned anywhere. With `keep_parents=False` the polymorphic override is a one-line pass-through (`polymorphic/models.py:276`), so an audited identity allowlist is cheap and would preserve the friendly backstop and complete previews for both extras.
- **MEDIUM.** 07-01's verify runs the 550-case matrix; ~5 minutes serial on 6.0 per 06.2 evidence. Fine as an integration gate; note it in the task.
- **LOW.** `-k delete` on `test_polymorphic.py` requires new tests to carry "delete" in their names.

**Suggestions.** Make 07-02 the home of the library-override decision's tests (Car and Author pages: notice present or absent, backstop behavior).

**Risk assessment.** Medium.

## 06.3-08

**Summary.** Rewrite deletion/lifecycle/Guardian docs, publish three executable migration recipes, pair every Breaking entry with migration guidance.

**Strengths.**
- Reuses the proven executable-docs pattern (`tests/test1/test_form_button_docs.py:38-49`; helpers in `test_label_mode_docs.py:14-35`).
- Owns `request_lifecycle.md`, whose `cv_get_db_alias` row (`docs/reference/request_lifecycle.md:98-102`) changes for delete views.

**Concerns.**
- **MEDIUM.** The existing Unreleased "Blocked deletions" Breaking entry and `docs/migrating-1.0.md:436-492`, plus `docs/reference/delete_view.md:193-203` and `:301-327`, currently assert the disproven traceback/native-graph backstop and endorse overriding `cv_get_related_objects`. 08-02 says "add focused Unreleased entries" and "preserve phase history"; it must instead amend those unreleased entries so the changelog does not carry contradictory guarantees.
- **MEDIUM (D1/D3).** Document the library-override decision and the limitation that any `SET`/`SET_DEFAULT`/custom handler reached before a native blocker disables the friendly stale-race backstop (the request then errors by design).
- **LOW.** Recipe 2 ("read-only description of a custom effect") needs a real custom-effect model in the test app (see 02/03 ownership).

**Suggestions.** State "amend, don't append" for the unreleased entries; add the limitation paragraph.

**Risk assessment.** Medium.

## 06.3-09

**Summary.** Provision verified Django 5.2, run three-series focused and full suites plus JS/docs/lint gates, reconcile acceptance.

**Strengths.**
- Records interpreter, import root and HEAD; refuses the main venv's 6.1.2; only the existing crispy-floor deselection.
- Reconciliation keeps unclassified flags and prohibitions visible.

**Concerns.**
- **MEDIUM.** The verify chain runs `npm test` directly. Earlier phases ran JS gates only through a nvm wrapper (`STATE.md`, 06-01 decision: "JS gates run only via 06-js-verify.sh (nvm Node v24.21.0)"). If the executor shell lacks Node on PATH the gate fails spuriously. Use the established script or state the PATH prerequisite.
- **MEDIUM.** `nox -r --no-install -s "tests-3.12(django='5.2')"` presumes the env exists; `--no-install` against a missing env yields an empty venv and import failures. Only `.nox/crispy_floor-3-12-django-{4-2,6-0}` and `.nox/tests-3-12-django-4-2` exist today. Make the two-step explicit (one installing run, then `--no-install` reruns). Also note that session runs `pytest tests -n auto --cov` under `fail_under = 88` (`pyproject.toml:151-154`), so a coverage dip fails the gate.
- **LOW.** Serial full suites on 4.2 and 6.0 were ~5 and ~10 minutes in 06.2; the chained gate will exceed 20 minutes. Acceptable as a phase gate; record durations.

**Suggestions.** Fix the Node and nox provisioning steps in the verify text.

**Risk assessment.** Low-Medium.

## Cross-plan conclusions

**Ordering and ownership.** The wave structure is correct and 03 ∥ 06 is genuinely disjoint. Two gaps break executability as written: `test_delete.py` is owned by 02 and 04 but the diagnostic that invalidates its monkeypatches lands in 03 (fix by moving all migration into 02-02 or giving 03 ownership), and 02-02's integration verify omits the modules the wave-2 adapter already affects (Guardian through rows, polymorphic, lifecycle).

**Mandatory revisions before DEL-01 approval.**
1. `gate="blocking-human"` on 01-01 (process correctness of the maintainer gate).
2. DESIGN decision on audited library `delete` overrides (`PolymorphicModel.delete`, `OrderedModelBase.delete`), with tests in 07-02 and docs in 08 (D1).
3. DESIGN specification of the nested-tree contract and provider attachment point (D2).
4. DESIGN rule for native-blocker marker timing relative to the sticky callback flag, with ordering tests in 04 (D3).
5. Test-ownership and integration-verify fixes in 02/03 described above.

**Recommended revisions.** Startup check for `delete` signatures that cannot bind `using` (D5); explicit Guardian fail-closed predicate in 05; "amend, don't append" for unreleased changelog entries in 08; Node/nox provisioning fixes in 09; `source_pks` as frozenset (D7).

**Security.** The STRIDE registers are coherent and IDs are unique with the shared SC entry. Projection after provider merge, no raw boundary data in context, alias-keyed caches, and immutable policy close the identified threats. Two items to document rather than fix: providers are trusted code, and provider blockers are a veto path (D6).

**Performance.** The inspector is no worse than today's `NestedObjects` traversal and the POST still collects twice (inspect, then write), as today. Avoid `.only()` deferral on display rows (03). Guardian's whole-through-table superuser cache is unchanged.

**Phase fitness.** With revisions 1–5 the plans achieve DEL-02/03/04/06 and GUA-01 as specified. Without the D1 decision, DEL-05 ("core, Guardian and polymorphic authorization… remain coherent") and the project's default-output constraint are at risk for two shipped extras, and Phase 7 would freeze an always-incomplete notice on them. DEL-01 remains a real maintainer checkpoint; this review does not satisfy it.
