# Cycle 3 Plan Review — Phase 06.10 at `b5d33a1`

Reviewed all six plans against the working tree at `b5d33a1` (confirmed HEAD). Every newly cited internal name was checked against source; file reads are cited inline. No product tests were run and no repository files were edited. The one thing I could not verify from this sandbox is the browser asset manifest under `$HOME/.cache` (outside the allowed directory); plan 06 already gates on a runtime preflight for it.

**Headline: 0 HIGH, 0 MEDIUM, 3 LOW.** All five carried findings are FULLY RESOLVED at plan level. No regression of the six cycle-1 HIGH closures was found.

## Carried-finding closure

| ID | Status | Evidence |
|---|---|---|
| C1-M02 ViewSetError correction | **FULLY RESOLVED** | `cv_get_cls_assert_object` calls `cv_raise(...)` with its default exception (`src/crud_views/lib/view/base.py:550-556`), and that default is `ViewSetError` (`src/crud_views/lib/exceptions.py:16-17,27`). Plan 01 compatibility boundary (01:102), plan 02 hook_contract (02:82) and plan 05 handoff (05:74) now name ViewSetError; the only remaining `CrudViewError` mention in the plans is the correct "do not change unrelated CrudViewError uses" (05:74). |
| C2-M01 cold/cached multilevel view/list and breadcrumb costs | **FULLY RESOLVED** (plan level) | 01-01 records a pre-change baseline; 01-02 `queries_view_multilevel` pins bound-view and N=1/4 list costs for fresh/creation-cached/select_related rows with the stale-grandparent case; 02-02 `navigation_preservation_queries` adds cold breadcrumb fixtures. The retained pin is correctly described: `bc_chain` creates `note` with `book=book` and `book` with `publisher=publisher` (`tests/test1/test_breadcrumb.py:237-241`), so both relations are cached and the own-view segments at `src/crud_views/lib/breadcrumb.py:168-190` add zero queries; the ancestor loop's scoped `get()` per level (`breadcrumb.py:230-237`) is untouched. The 2/0 pin at `test_breadcrumb.py:297-302` can stand. See LOW-2 for the one residual. |
| C2-M02 same-parent Guardian list N=1/4 and safe parent reuse | **FULLY RESOLVED** (plan level) | 03-02 records a pre-gate baseline, 03-03 pins same-parent lists and distinct-parent cards separately by SQL family. The reuse rule is grounded: `_guardian_check_parent` currently discards the parent it loads (`src/crud_views_guardian/lib/mixins.py:370-374`) and `_guardian_user_has_parent_perm` builds a fresh `ObjectPermissionChecker` per call (`mixins.py:366-368`), so retaining model evidence without permission results is the right split. Plan 05 publishes per-action deltas. |
| C2-L01 actual URL-free filter | **FULLY RESOLVED** | `cv_context_has_permission` is a `@register.filter` at `src/crud_views/templatetags/crud_views.py:601-607`; it calls `cls.cv_has_access(view.request.user, getattr(view, "object", None))` outside its `except Exception`, so plan 03-02's "preserve custom exception identity, spy that no URL builder runs" is testable as written. |
| C2-L02 resolver/carrier import boundary | **FULLY RESOLVED** | The boundary described in 01 and 02 matches source: `viewset/__init__.py:15-28` imports `..view` at module scope, so `base.py` must import the resolver locally; `views/child.py:6-9` already documents the submodule workaround; `resource.py:9-16` documents the leaf constraint. The fresh-subprocess smoke in both import orders is the correct test. |

---

## 06.10-01

**Summary.** The resolver plan is internally consistent with the code it replaces. The falsey page-kwargs loop it must retire is exactly `base.py:598-604`; the list-to-card classification it relies on exists at `viewset/__init__.py:339-343`; the M2M fixture (`Genre.publishers`, `many_to_many_through_attribute="genres"`) exists at `tests/test1/app/models.py:55-59` and `app/views.py:457`; Resource's leaf-only constraint is enforced by E261 (`viewset/__init__.py:217-227`). The compatibility boundary is now correct in every exception name.

**Strengths.**
- Pre-change baseline capture before any resolver edit (01-01) gives plan 02 and 05 honest deltas.
- Isolated `NestedUrl*` model family avoids touching Publisher's reverse-deletion graph, with an immediate `test_delete_inspection.py` replay as the guard.
- The error taxonomy keeps `ViewSetKeyFoundError` for `get_view_class` (`viewset/__init__.py:342`) and view callers, `ViewSetError` for the object assertion, and confines the new NoReverseMatch/None translation to the public helper.
- Registered-PK extraction via `_meta.pk.value_from_object` and the to_field rule correctly address the raw-attname pitfall.

**Concerns.**
- LOW — see LOW-2 under 06.10-02 (core-side "already-resolved evidence" source is not named; plan 01's reuse clause may be a no-op for ordinary core list views).

**Suggestions.**
- In 01-02, state explicitly which instance the "already-resolved model evidence" can come from on a core list view, or state that none exists and the measured N×(h−1) is accepted.

**Risk: MEDIUM.** Correct and complete at plan level; risk lies in the coherent-chain logic, which is new code with no analog.

## 06.10-02

**Summary.** The rendering integration is anchored to the right call sites: the ordinary action branch (`base.py:753-775`), `ContextButton`/`ChildContextButton` (`buttons.py:95-129,222-252`), both card branches (`card.py:56-90`), and `cv_get_child_url` (`base.py:985-1005`, whose `viewset.parent.name` read at line 989 does lack the None guard C1-M07 names). The scope-role decisions match source: `SiblingContextButton` checks access with `None` (`buttons.py:301`), `ParentContextButton` reverses its own URL from page kwargs and gates on `cv_get_parent_object()` (`buttons.py:155-189`), and create's state adapter already picks the page parent via `rendering_view.cv_get_parent_object()` (`create.py:52-70`), so the plan's "collection parent A for row B" matches existing state behaviour.

**Strengths.**
- Immutable ContextVar frames with owner thread/task checks and finally-reset; no permission results stored.
- Single invocation of the public `cv_has_access` with original arguments preserved.
- Breadcrumb measurement split into URL-assembly vs total, with cold fixtures separate from the cached pin.

**Concerns.**
- **LOW-1 (precision):** 02-02 says "Missing detail keys still yield the existing column fallback." `LinkDetailColumnMixin.get_url` is wrapped in `ignore_exception(ViewSetKeyFoundError)` (`src/crud_views/lib/table/columns.py:47-50`), and `ignore_exception` re-raises in strict mode (`exceptions.py:39-58`). The test settings set `CRUD_VIEWS_STRICT=True` (`tests/test1/conftest.py:47-49`), so under the test configuration the existing behaviour is a raised `ViewSetKeyFoundError`, not a fallback. The test should either assert the raise under strict and the None under non-strict, or the sentence should read "existing `ignore_exception` behaviour".
- **LOW-2 (cost transparency):** `ViewSet.get_queryset` builds nested list querysets without `select_related` (`viewset/__init__.py:290-301`), and Django's `get_object()` yields a fresh instance. For a core list of a ≥2-level child (e.g. BookNote), D-01 traversal costs one relation load per row (h−1), i.e. N extra queries per page, unless an already-resolved parent instance is reused. Plan 01 permits such reuse but no plan identifies a core-side source for it (Guardian gets `_cv_guardian_resolved_parent` in plan 03; core only has unmemoized `cv_get_parent_object()` calls from `ParentContextButton` and create state). The plans will measure and publish this honestly, which satisfies C2-M01, but the user-facing mitigation is left implicit.

**Suggestions.**
- Either memoize `cv_get_parent_object()` per view instance and let the resolver reuse it when `row.<attr>_id == parent.pk` (registered model/database agreeing), or have plan 05 publish the accepted N×(h−1) cost with a `select_related` recipe for `get_queryset` overrides. Either is a one-line plan addition; D-01 remains untouched.

**Risk: MEDIUM.** The carrier is the most intricate new mechanism; the plan's isolation tests are the right shape.

## 06.10-03

**Summary.** The policy order is consistent with the shipped MRO and dispatch. `GuardianParentPermissionMixin.has_permission` returns True when parented and otherwise delegates (`mixins.py:307-311`), so a top-level create reaches `permission_required`'s assertion (`base.py:1063-1070`); the plan's explicit add-mapping guard turns that into a deliberate `ImproperlyConfigured` while dispatch's anonymous/inactive prelude (`mixins.py:313-318`) stays first. The empty-map retry the migration test depends on is real: `default_permissions` caches only non-empty results (`viewset/__init__.py:436-470`). The certified-adapter ownership flag is justified by source: `_cv_cancel_target_available` calls `cls.cv_has_access(user, obj)` for object targets (`mixins.py:260-262`), which under a new cooperative `cv_has_access` would re-run the parent gate unless told the parent is already certified.

**Strengths.**
- Declaration checks precede superuser/global/checker shortcuts, closing the `perms = (perm,) if perm else ()` hole (`base.py:1085-1089`) and the `perm.split` path (`mixins.py:72,97,368`).
- D-10 checked before any frame when `obj=None`, preserving `SiblingContextButton` and list toolbars.
- Private-to-public forwarding direction is fixed and both override styles are tested without recursion.
- Honest refusal to claim a zero permission-query delta; checker lifetime retained.

**Concerns.** None new. The per-action parent permission SQL will grow linearly with rows × actions; the plan measures it and defers any request-local memo, consistent with the context's deferral of Guardian cache work.

**Suggestions.**
- In 03-03's committed assertions, make the per-action parent-permission increment explicit (queries per added row at fixed action count), so plan 05 can quote one number per workload.

**Risk: MEDIUM.** Authorization-bearing changes with good coverage; the create MRO special case is the piece most likely to need iteration.

## 06.10-04

**Summary.** The delete integration replaces only `cv_get_related_object_url` (`delete.py:192-210`) and keeps the independent certifier (`delete.py:212-372`) intact. The multilevel path is naturally covered by the certifier: `destination.get_queryset()` runs the nested chain filter from `match.kwargs` (`viewset/__init__.py:290-301`), the fetched row is compared by concrete model, PK type, PK and database (`delete.py:321-327`), and the certified parent is bound through the lambda at `delete.py:356-368`. The named test anchors exist: `test_protected_link_request_tracer` (`tests/test1/test_delete.py:64`), `test_protected_adapter_query_budget` (`tests/test1/test_delete_databases.py:222`), `database_routes` (`tests/test1/conftest.py:137`), `guardian_protected_destination` (`tests/test1/test_guardian_delete.py:7`).

**Strengths.**
- Serialized after plan 03 with an explicit reopen rule rather than a parallel note.
- Keeps visibility-before-URL and first-exact-model selection; cascade candidates stay uncertified.
- Remeasures and replaces the N=1/4/8 counters instead of keeping a loose bound.

**Concerns.** None new. Note that `_cv_cancel_parent_object` resolves the immediate parent by PK through `cv_get_parent_object()` (`base.py:1023-1035`) with default routing; the plan's alias tests with `database_routes` and router spies are the right check that intermediate ancestry does not silently default.

**Suggestions.**
- Record in the summary that `strict=False` now also makes M2M-nested or null-parent cascade nodes render as text where the old builder could not produce a PK; it is a behavioural improvement worth a changelog line in plan 05.

**Risk: LOW–MEDIUM.** Mostly reuse of a proven certifier.

## 06.10-05

**Summary.** Documentation obligations are complete and now carry the corrected exception names and the cost-publication contract. The target files exist (`docs/reference/nested.md`, `guardian.md`, `context_buttons.md`, `delete_view.md`, `docs/development/stability.md` with its existing "## Public API" section at line 19). Executable recipe markers follow the proven pattern (`tests/browser/protected-delete.cjs:23-35`).

**Strengths.**
- Breaking plus migration pairing per D-16, with implicit-page-A versus explicit-conflict examples executed.
- Scoped Phase 06.10 handoff subsection; final classification left to Phase 7.
- Measured deltas only, replayed by `reference_examples`.

**Concerns.** None new. The `--site-dir /tmp/cv-069-docs` inherited path is cosmetic.

**Suggestions.**
- If LOW-2 is adopted, the `select_related` preparation guidance should name the nested list `get_queryset` override as the place to apply it.

**Risk: LOW.**

## 06.10-06

**Summary.** The browser plan extends real infrastructure: `requiredCases` and the `smoke|all` assertion (`protected-delete.cjs:12,20`), tracked-only `sourceHashes()` (`protected-delete.cjs:36-40`) mirrored by `source_hashes()` in the server (`protected_delete_server.py:70-80`), the `recipes(source, expected)` signature (`protected-delete.cjs:23`), `CustomLoader` and `FixtureMiddleware` (`protected_delete_server.py:83-135`), and the exported `validateEvidence` (`protected-delete.cjs:247`). The tooltip-recipe markers sit directly before `django` fences (`docs/reference/buttons.md:783-784,801-802`). The middleware currently patches `SOURCES` and `ContractDetailView` for every request (`server.py:100-130`), which is exactly the scope leak C1-M17 confines.

**Strengths.**
- Identical tracked-plus-untracked manifests on both sides with mutation negative tests.
- Family-specific schema validation; old case IDs and screenshot rules unchanged.
- Final persisted-evidence validation after the last gate-driven edit.

**Concerns.**
- **LOW-3 (unverified precondition):** the `CV_CANCEL_ASSETS_DIR` manifest lives outside this sandbox's allowed directory, so its presence could not be confirmed here. The 06-01 precondition already treats missing runtime/assets as missing evidence rather than a pass; no plan change is needed.

**Suggestions.**
- None beyond the existing preflight.

**Risk: MEDIUM.** Browser evidence capture is inherently environment-sensitive; the strict validator design mitigates mislabeling.

---

## Cross-plan assessment

- **Dependency ordering** is correct and serial; plan 04's reopen-to-03-02 rule is explicit, plan 05 depends on 03 and 04, plan 06 on 05.
- **Coverage of the phase goal:** all four roadmap success criteria and D-01–D-16 map to executable tasks; the request-free helper, view builders, Guardian parity with D-09/D-10 limits, multilevel delete candidates, Breaking migration and Phase 7 inventory are each owned by one plan.
- **Scope discipline:** no DataView, navigation, core parent-permission enforcement or cross-request cache is introduced; the only latitude exercised is the private carrier, which is justified by the public-hook signature constraint.
- **Security:** declaration-before-fast-path ordering, request authority preserved, and the certified-parent single-evaluation seam close the two #312 gaps without weakening dispatch.
- **STATE "Ready to plan" versus ROADMAP plan list** remains a status lag, not a finding.

**Overall risk: MEDIUM.** The plans are complete and source-grounded; residual risk is implementation complexity in the resolver's coherent-chain rules and the ContextVar carrier, plus the measured per-row cost increases, which the plans commit to publishing rather than hiding.
