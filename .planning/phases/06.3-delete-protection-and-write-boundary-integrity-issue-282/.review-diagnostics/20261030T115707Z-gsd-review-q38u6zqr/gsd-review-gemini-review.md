## 06.3-01

### Summary
Gates all Phase 06.3 implementation on a single blocking human maintainer decision (`DEL-01`, `D-16`) over `06.3-DESIGN.md` and plans `06.3-01` through `06.3-09`, recording the approved commit (`reviewed_revision`), `06.3-DESIGN.md` SHA-256 digest, and itemized material design decisions in `06.3-APPROVAL.md`.

### Strengths
- `06.3-01-PLAN.md:70` sets `<task type="checkpoint:decision" gate="blocking-human">`, ensuring the execution workflow cannot auto-advance past `DEL-01` in autonomous mode (`/home/alex/.codex/gsd-core/workflows/execute-plan.md:150`).
- Removes the previously invented `01-02` package-legitimacy checkpoint, `06.3-PACKAGES.md` artifact, and `T-06.3-SC` threat rows (`06.3-01-PLAN.md:7-29,91-96`), keeping routine Django 5.2 nox provisioning automated in `09-01`.
- Ties `06.3-APPROVAL.md` to `reviewed_revision` and the SHA-256 digest of `06.3-DESIGN.md` (`06.3-01-PLAN.md:83`), while allowing downstream execution summaries and matrix evidence to be recorded without invalidating the approved design digest.

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW:** None.

### Suggestions
- None.

### Risk
- **Low.**

---

## 06.3-02

### Summary
Implements the end-to-end tracer (`02-01`) for callback-free relationship inspection (`inspect_deletion`), origin-aware write collection (`execute_deletion` / `_DeleteCollector`), pinned delete alias (`cv_get_delete_db_alias`), and independent incomplete/blocked notices, then migrates all superseded classifier/collector expectations in `tests/test1/test_delete.py` (`02-02`) before running the full-file verification gate.

### Strengths
- Resolves `H02` by completing all legacy test migrations in `02-02` (`_delete_probe` at `tests/test1/test_delete.py:789`, direct classifier imports at `tests/test1/test_delete.py:1143`, `NestedObjects` spy at `tests/test1/test_delete.py:851`, no-`using` `delete(self)` spy at `tests/test1/test_delete.py:1078`, `_assert_handler_error` at `tests/test1/test_delete.py:1122`, and `base.Collector` patch at `tests/test1/test_delete.py:1444`) and verifying `test_delete.py`, `test_guardian_delete.py`, `test_polymorphic.py`, `test_transactions.py`, and `test_form_buttons_golden.py` together (`06.3-02-PLAN.md:119,122`).
- Resolves `H03` by explicitly specifying custom-path behavior for `Author` (`OrderedModel`, `tests/test1/app/models.py:13`) and `Car` (`PolymorphicModel`, `tests/test1/app/models.py:178`), preserving sibling reordering and form-button golden bytes (`tests/test1/test_form_buttons_golden.py:124-126`).
- Resolves `M08` by requiring `cv_get_delete_db_alias()` to raise `ImproperlyConfigured` when called before a saved `self.object` is resolved and pinning unconditionally at `cv_form_valid_process` entry (`src/crud_views/lib/views/mixins.py:48-57`).

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW:** None.

### Suggestions
- None.

### Risk
- **Medium** (core deletion and template wiring changes, well-bounded by the expanded Wave 2 verification suite).

---

## 06.3-03

### Summary
Completes native graph inspection semantics (deferred `RESTRICT` closure, cycles, diamonds, multi-table parent links, non-PK `to_field` joins, auto-created through tables), adds the boundary-scoped `cv_get_delete_preview` extension contract and startup/runtime override diagnostics (`03-01`), and implements English/German partial-count and incomplete-preview notices (`03-02`).

### Strengths
- Resolves `H04` by specifying `field.get_foreign_related_value(source)` and `field.get_local_related_value(related)` across `related_fields` pairs, `field.attname` against actual remote target values for `ForeignKey(to_field=...)`, raw child parent-link queries with `collect_related=False` and separate traversal-mode tracking, and discriminating tests `test_inspection_distinct_parent_link_keys` and `test_inspection_reverse_fk_to_field` (`06.3-03-PLAN.md:107`, `06.3-DESIGN.md:80-85`).
- Resolves `M03`, `M05`, `M07`, `M11`, and `M12` with explicit tree/summary shapes (`dict[str, int]` preserved in `src/crud_views/lib/views/delete.py:314-315`), normalized descriptor indexing with ordered `source_pks`, full-row loading, and `viewset.E...` startup checks paired with runtime `ImproperlyConfigured`.
- Places the incomplete-preview alert outside the `{% if delete_protection_errors %}` branch in `src/crud_views/templates/crud_views/view_delete.content.html:5-21` so `D-03`/`D-12` combinations keep the notice visible.

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW [L01]:** `DeleteView.checks(cls)` (`src/crud_views/lib/views/delete.py:178-188`) is invoked directly on bare `DeleteView` subclasses without a `cv_viewset` or `model` in existing unit tests (`tests/test1/test_modal.py:160-300`, e.g. `GoodModalDeleteView`), as well as on Resource-backed ViewSets (which `ViewSet.checks()` separately flags with `E262` at `src/crud_views/lib/viewset/__init__.py:206-214`). If the new startup check for inspectable `model.delete(using=...)` signatures dereferences `cls.model` or `cls.cv_viewset.model` unconditionally, bare `DeleteView.checks()` calls will raise `AttributeError`.

### Suggestions
- In `03-01`, guard the `model.delete` signature check in `DeleteView.checks(cls)` when resolving the model (`model = cls.model or (cls.cv_viewset.model if cls.cv_viewset is not None and not cls.cv_viewset.is_resource else None)`), skipping the model-method signature check when `model is None`, matching the `cls.cv_viewset is None` guard in `DeleteView.cv_success_object_keys()` (`src/crud_views/lib/views/delete.py:195`).

### Risk
- **Medium.**

---

## 06.3-04

### Summary
Audits and tests `_DeleteCollector` write-time provenance across Django 4.2/5.2/6.0 (`04-01`) and verifies real `transaction=True` commit, rollback, and external callback behavior across `cv_atomic=True` and `cv_atomic=False` (`04-02`).

### Strengths
- Resolves `M04` by specifying immediate termination on nonempty native `PROTECT` (emitting `_NativeDeleteBlocked` only when `not custom_callback_entered`, avoiding subsequent custom handlers, and raising ordinary `ProtectedError` if a custom callback already ran), deferred `RESTRICT` reconciliation at outer closure, non-sticky `SET_NULL`/`DO_NOTHING`, and named test nodes (`06.3-04-PLAN.md:92`, `06.3-DESIGN.md:170-179`).
- Resolves `M02` by recording the Django 4.2/5.2/6.0 `Collector.collect` / `Model.delete` parity table in `04-SUMMARY.md` and `06.3-MATRIX.md` rather than mutating the approved `06.3-DESIGN.md`.
- Tests post-commit (`cv_on_commit`), `cv_form_valid_hook`, signal, converter, and custom handler failures with `transaction=True` and external event lists rather than relying on outer test-transaction rollback.

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW:** None.

### Suggestions
- None.

### Risk
- **Medium.**

---

## 06.3-05

### Summary
Configures an independent `shard` SQLite database in `tests/test1/conftest.py:91-96`, proves single-evaluation instance-aware alias pinning across inspection, deletion, `transaction.atomic`, and `transaction.on_commit` with colliding PKs (`05-01`), and scopes Guardian `_PermittedPks` label projection and caching to the candidate's database alias under a runtime topology predicate (`05-02`).

### Strengths
- Resolves `H05` by specifying a concrete runtime topology predicate in `_PermittedPks` (`src/crud_views_guardian/lib/views.py:59-95`) before all label paths (including active superuser, global fallback, and auto-created through tables), checking `actor._state.db == using`, validating model and join-table query routes (`User`, `Group`, `Permission`, `ContentType`, `user.groups.all().db`, Guardian object-permission models), verifying `ct._state.db == using`, using fresh permission-cache state on an identity-verified same-alias actor for cross-alias global checks, and failing closed to `set()` on any mismatch (`06.3-05-PLAN.md:128`, `06.3-DESIGN.md:222-241`).
- Resolves `M08` and `M09` with `contextvars`-backed routing activated prior to session/authentication middleware and full teardown restoration across `transaction=True, databases=["default", "shard"]` tests.

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW [L02]:** Existing direct-mode unit tests in `tests/test1/test_guardian_delete.py:69,84,95,114,127,157,179` and `tests/test1/test_guardian_inactive.py:404` (which is not modified in Wave 5) invoke `_PermittedPks(user, accept_global)(ModelClass)` with a single `model` argument and no `using` parameter.

### Suggestions
- In `05-02`, give `_PermittedPks.__call__` (`src/crud_views_guardian/lib/views.py:74`) a default `using: str = DEFAULT_DB_ALIAS` parameter (while `_filter_item` at `src/crud_views_guardian/lib/views.py:106` and `cv_filter_related_objects` at `src/crud_views_guardian/lib/views.py:55` pass `using=obj._state.db or DEFAULT_DB_ALIAS`), preserving direct `_PermittedPks(user, accept_global)(ModelClass)` calls in `tests/test1/test_guardian_delete.py` and `tests/test1/test_guardian_inactive.py:404`.

### Risk
- **Medium.**

---

## 06.3-06

### Summary
Adds `_resolve_permission_key` to `GuardianViewSet` (`src/crud_views_guardian/lib/viewset.py:77-108`) so `assign_perm`, `remove_perm`, and `get_objects_for_user` validate configured string permission keys before inactive-user shortcuts or permission writes, freezes `STRICT_HELPER_POLICY` (`src/crud_views_guardian/lib/viewset.py:11`) with `MappingProxyType` (`06-01`), and records the bounded `GUA-01` / residual `AUTH-06` disposition ledger in `06.3-GUARDIAN-REVIEW.md` (`06-02`).

### Strengths
- Resolves `M10` by rejecting non-`str` inputs (`None`, `int`, `list`, `dict`) in `_resolve_permission_key` with the descriptive `ValueError` before any dictionary lookup (`06.3-06-PLAN.md:100`, `06.3-DESIGN.md:252-254`).
- Resolves `M12` by classifying the `KeyError` → `ValueError` change on `GuardianViewSet` helpers as `### Breaking` and handing the exact contract to Plan 08 for paired `CHANGELOG.md` and `docs/migrating-1.0.md` coverage.
- Preserves detached `dict(STRICT_HELPER_POLICY)` copying in `GuardianManageView.get_context_data` (`src/crud_views_guardian/lib/views.py:296`).

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW:** None.

### Suggestions
- None.

### Risk
- **Low.**

---

## 06.3-07

### Summary
Replays actor and native-template authorization boundaries (`tests/test1/test_guardian_delete.py`, `tests/test1/test_authorization_templates.py`, `tests/test1/test_authorization_matrix.py`) with the new inspector and partial previews (`07-01`), and tests real `PolymorphicModel.delete` (`Car`/`Vehicle`) and `OrderedModel.delete` (`Author`) execution, sibling reordering, parent-row removal, partial-preview notices, and stale/custom exception propagation (`07-02`).

### Strengths
- Resolves `H06 / SG-01` by referencing the tracked `@src/crud_views_polymorphic/lib/delete.py` (`06.3-07-PLAN.md:108`).
- Resolves `H03`, `M03`, `M06`, and `M11` by testing `Author` sibling reordering and `Car`/`Vehicle` parent-row deletion through real registered routes with explicit required test node names (`test_partial_native_template_context_shape`, `test_library_delete_author_reorders_and_remains_partial`, `test_library_delete_car_parent_rows_and_partial`).

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW:** None.

### Suggestions
- None.

### Risk
- **Low.**

---

## 06.3-08

### Summary
Updates `docs/reference/delete_view.md`, `docs/reference/request_lifecycle.md`, `docs/reference/guardian.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`, and adds `tests/test1/test_delete_migration_docs.py` to extract and execute the three published migration recipes (`08-01`, `08-02`).

### Strengths
- Resolves `M13` by naming exact target headings in `docs/migrating-1.0.md` (`### Safe deletion preview overrides`, `### Describing custom deletion effects`, `### Copied delete templates with incomplete previews`) and extracting fences via `_section`/`FENCE` (`tests/test1/test_form_button_docs.py:26,56-59`) with heading and fence-count assertions (`06.3-08-PLAN.md:90`).
- Resolves `M12` and `M14` by amending active `Unreleased` entries in `CHANGELOG.md:172-191` and `docs/migrating-1.0.md:400-492` in place, adding the allocated `viewset.E...` check IDs to the `docs/migrating-1.0.md:34-40` table, and pairing every `### Breaking` item.

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW:** None.

### Suggestions
- None.

### Risk
- **Low.**

---

## 06.3-09

### Summary
Provisions the supported Django 5.2 nox session, executes focused and full test suites across Django 4.2, 5.2, and 6.0 alongside `06-js-verify.sh`, `mkdocs build --strict`, and `ruff` (`09-01`), and reconciles `06.3-ACCEPTANCE.md` and `06.3-VALIDATION.md` against all transferred Phase 6.2 and Phase 6.3 obligations (`09-02`).

### Strengths
- Resolves `M01`, `M02`, `M11`, `M15`, and `M16`: removes the obsolete package gate, runs each Django series in separate verification commands, records git HEAD/diff digests and installed module hashes before any `--no-install` rerun, verifies required new test nodes in `--collect-only`, and runs JS checks via `bash .planning/phases/06-form-button-leaf/06-js-verify.sh` (`06.3-09-PLAN.md:82-98`).

### Concerns
- **HIGH:** None.
- **MEDIUM:** None.
- **LOW:** None.

### Suggestions
- None.

### Risk
- **Low.**

---

## Cross-Plan Conclusions and Prior-Concern Closure

### Prior Cycle Concern Closure Matrix (`H01`–`H06`, `M01`–`M16`)

| ID | Prior Severity | Status at `cc5caa7` | Verification in Current Plans / Design |
|---|---|---|---|
| **H01** | HIGH | **CLOSED** | `06.3-01-PLAN.md:70` sets `<task type="checkpoint:decision" gate="blocking-human">` and preserves the `must_haves.prohibitions` rule against inferred approval. |
| **H02** | HIGH | **CLOSED** | `06.3-02-PLAN.md:97,119,122` completes all legacy classifier/preview/Collector/`using`-spy test migrations in `02-02` before the first full-file gate and runs `test_delete.py`, `test_guardian_delete.py`, `test_polymorphic.py`, `test_transactions.py`, and `test_form_buttons_golden.py` together. |
| **H03** | HIGH | **CLOSED** | `06.3-DESIGN.md:78,156-161`, `06.3-02-PLAN.md:97`, `06.3-07-PLAN.md:117`, and `06.3-08-PLAN.md:90` explicitly keep `Author` (`OrderedModel`) and `Car` (`PolymorphicModel`) on the custom `delete(using=using)` path with partial previews, intact form-button goldens, sibling-reordering/parent-row tests, and propagated stale errors. |
| **H04** | HIGH | **CLOSED** | `06.3-DESIGN.md:75,80-85` and `06.3-03-PLAN.md:107` specify `get_foreign_related_value`/`get_local_related_value` across `related_fields`, `to_field` target joins, raw child parent-link queries with `collect_related=False` and mode-aware visited tracking, plus `test_inspection_distinct_parent_link_keys` and `test_inspection_reverse_fk_to_field`. |
| **H05** | HIGH | **CLOSED** | `06.3-DESIGN.md:222-246` and `06.3-05-PLAN.md:128` enforce a runtime topology predicate in `_PermittedPks` before all label paths (superuser, global, through, object/group), validating actor, `ContentType`, auth/join, and grant routes against `using` and failing closed to `set()` on mismatch. |
| **H06 / SG-01** | HIGH | **CLOSED** | `06.3-07-PLAN.md:108` replaces the nonexistent path with `@src/crud_views_polymorphic/lib/delete.py`. |
| **M01** | MEDIUM | **CLOSED** | `01-02`, `06.3-PACKAGES.md`, and `T-06.3-SC` are removed across all plans, `06.3-DESIGN.md`, and `06.3-VALIDATION.md`; `09-01` runs routine Django 5.2 setup directly. |
| **M02** | LOW | **CLOSED** | `06.3-01-PLAN.md:78`, `06.3-04-PLAN.md:92`, and `06.3-09-PLAN.md:82` tie approval to `reviewed_revision` and the `06.3-DESIGN.md` SHA-256 digest and place parity/matrix evidence in `04-SUMMARY.md` and `06.3-MATRIX.md`. |
| **M03** | MEDIUM | **CLOSED** | `06.3-DESIGN.md:89-96`, `06.3-03-PLAN.md:107`, and `06.3-07-PLAN.md:93,117` specify root-inclusive alternating nested lists, `None` redaction positions, direct-root provider attachment, `Car`/`Vehicle` parent counts, and heading-only partial qualification with `related_summary: dict[str, int]`. |
| **M04** | MEDIUM | **CLOSED** | `06.3-DESIGN.md:170-179` and `06.3-04-PLAN.md:92` specify immediate stop on nonempty native `PROTECT`, post-callback `ProtectedError` propagation, outer-closure `RESTRICT` reconciliation, non-sticky `SET_NULL`/`DO_NOTHING`, and named ordering test nodes. |
| **M05** | LOW | **CLOSED** | `06.3-DESIGN.md:190-195` and `06.3-03-PLAN.md:107` specify `viewset.E...` startup checks and runtime signature binding for keyword `using` and `**kwargs` adapters without invoking incompatible callables. |
| **M06** | MEDIUM | **CLOSED** | `06.3-02-PLAN.md:119`, `06.3-04-PLAN.md:92`, `06.3-07-PLAN.md:117`, and `06.3-08-PLAN.md:90` assign function-scoped dynamic model/table/route/metadata fixtures with teardown restoration to each test module and reuse existing `Author`/`Car` models. |
| **M07** | LOW | **CLOSED** | `06.3-DESIGN.md:95-96,115-117` and `06.3-03-PLAN.md:107` load full display rows (no `.only()`/`.defer()` N+1), keep ordered `source_pks` equality, and normalize/index boundary descriptors once per inspection. |
| **M08** | MEDIUM | **CLOSED** | `06.3-DESIGN.md:209-212`, `06.3-02-PLAN.md:97`, and `06.3-05-PLAN.md:105` raise `ImproperlyConfigured` before a saved `self.object` is resolved, pin unconditionally at `cv_form_valid_process` entry, and document read-alias vs write-alias semantics. |
| **M09** | MEDIUM | **CLOSED** | `06.3-DESIGN.md:243-246` and `06.3-05-PLAN.md:105` use `transaction=True, databases=["default", "shard"]`, activate `contextvars` routing before authentication middleware, and restore routers/caches/signals at teardown. |
| **M10** | MEDIUM | **CLOSED** | `06.3-DESIGN.md:252-254` and `06.3-06-PLAN.md:100` reject non-`str` inputs in `_resolve_permission_key` with `ValueError` before dictionary lookup or side effects. |
| **M11** | LOW | **CLOSED** | `06.3-02-PLAN.md`, `06.3-03-PLAN.md`, `06.3-04-PLAN.md`, `06.3-07-PLAN.md`, and `06.3-09-PLAN.md` use exact node selections or full new modules and verify required new test nodes in `--collect-only`. |
| **M12** | MEDIUM | **CLOSED** | `06.3-03-PLAN.md:107`, `06.3-06-PLAN.md:100`, and `06.3-08-PLAN.md:107` allocate unused `viewset.E...` IDs, add them to `docs/migrating-1.0.md`, and pair the `KeyError` → `ValueError` `### Breaking` entry. |
| **M13** | LOW | **CLOSED** | `06.3-08-PLAN.md:90` names the three exact migration headings and asserts heading/fence counts during `_section`/`FENCE` extraction. |
| **M14** | MEDIUM | **CLOSED** | `06.3-08-PLAN.md:90,107` amends active `Unreleased` entries in `CHANGELOG.md` and `docs/migrating-1.0.md` in place and documents additive provider blockers, `.using(using)`, library overrides, and non-atomic callback limits. |
| **M15** | MEDIUM | **CLOSED** | `06.3-09-PLAN.md:82-98` separates series runs, verifies git HEAD/diff digests and installed module hashes before `--no-install` reruns, and requires reinstalling after any source repair. |
| **M16** | MEDIUM | **CLOSED** | `06.3-09-PLAN.md:82,92` and `06.3-VALIDATION.md:207` run JS verification via `bash .planning/phases/06-form-button-leaf/06-js-verify.sh`. |

### Overall Assessment
All 6 prior HIGH concerns (`H01`–`H06`) and all 16 prior MEDIUM/LOW concerns (`M01`–`M16`) are **closed** in commit `cc5caa7`. Only two non-blocking **LOW** implementation hygiene notes (`L01` in `06.3-03` for guarding `cls.model`/`cls.cv_viewset` on bare `DeleteView.checks()` subclasses, and `L02` in `06.3-05` for keeping `using=DEFAULT_DB_ALIAS` defaulted on direct `_PermittedPks(user, accept_global)(ModelClass)` calls) remain. The plan set is coherent, properly sequenced, and ready for the `DEL-01` maintainer review checkpoint in `06.3-01`.
