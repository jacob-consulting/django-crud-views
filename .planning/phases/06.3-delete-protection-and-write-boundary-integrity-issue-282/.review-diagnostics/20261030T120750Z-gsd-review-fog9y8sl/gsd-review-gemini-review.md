# Cross-AI Plan Review — Cycle 3 (Phase 06.3, Commit `1366dac`)

## Cycle 2 Closure Verification (`C2-L01`–`C2-L03`, plus `H01`–`H06` / `M01`–`M16`)

| ID | Cycle 2 Severity | Cycle 3 Status | Verification & Mechanism (`file:line`) |
|---|---|---|---|
| **C2-L01** | LOW | **CLOSED** | `.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-03-PLAN.md:105,108`, `06.3-DESIGN.md:191-194`, and `06.3-VALIDATION.md:93` explicitly guard startup `model.delete` signature inspection in `DeleteView.checks()` (`src/crud_views/lib/views/delete.py:178-188`). When `getattr(cls, "cv_viewset", None)` is Resource-based (`src/crud_views/lib/viewset/__init__.py:106-107,191-215`), only `model.delete` signature inspection is skipped so `viewset.E262` (`__init__.py:208`) is preserved. Otherwise, a class `model` or `cv_viewset.model` is inspected only when `isinstance(model, type) and issubclass(model, Model)`, preserving bare/unregistered `DeleteView` subclass checks in `tests/test1/test_modal.py:160-198,280-300` without `AttributeError` or spurious errors, and adding `test_signature_checks_skip_bare_and_resource_views` plus `tests/test1/test_modal.py` to `03-01` verification. |
| **C2-L02** | LOW | **CLOSED** | `.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-05-PLAN.md:14,45-46,75,118,134,137` and `06.3-VALIDATION.md:133` deliberately make `_PermittedPks.__call__(model, *, using)` (`src/crud_views_guardian/lib/views.py:74`) require a keyword-only `using` parameter (no `DEFAULT_DB_ALIAS` fallback), assign `tests/test1/test_guardian_inactive.py` ownership to Wave 5 (`depends_on: ["06.3-04", "06.3-06"]`, after Wave 3's `06.3-06`), migrate all direct `_PermittedPks` callers in `tests/test1/test_guardian_delete.py:69,84,95,97,113,115,126,133,157,179` and `tests/test1/test_guardian_inactive.py:404`, and include `tests/test1/test_guardian_inactive.py` in `05-02`'s verification command (`C0502`). |
| **C2-L03** | LOW | **CLOSED** | `.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-02-PLAN.md:124,195` replaces the nonexistent helper name with the actual helpers `_assert_handler_error` (`tests/test1/test_delete.py:1122`) and `_assert_collection_extension_propagates` (`tests/test1/test_delete.py:1109`). |
| **H01–H06, M01–M16** | HIGH / MEDIUM / LOW | **CLOSED (unchanged)** | All Cycle 1 dispositions signed off in Cycle 2 remain intact at `1366dac`, including the `blocking-human` `DEL-01` checkpoint (`06.3-01-PLAN.md:62`), routine automated Django 5.2 nox setup (`06.3-09-PLAN.md:81`), and preservation of actual `OrderedModel.delete` (`Author` sibling reordering) and `PolymorphicModel.delete` (`Car`/`Vehicle` parent rows) on the custom `delete(using=using)` path (`06.3-DESIGN.md:155-161`, `06.3-07-PLAN.md:124`). |

---

## 06.3-01

- **Summary:** Establishes the Wave 1 `DEL-01` / `D-16` blocking maintainer design-review gate (`01-01`) over `06.3-DESIGN.md` and all nine plans before any production or test code is written, recording the decision, reviewer, package commit (`reviewed_revision`), and `06.3-DESIGN.md` SHA-256 digest in `06.3-APPROVAL.md`.
- **Strengths:**
  - Uses `gate="blocking-human"` (`06.3-01-PLAN.md:62`) and `autonomous: false` (`06.3-01-PLAN.md:8`), preventing automated execution from bypassing maintainer sign-off while noting that external plan convergence cannot satisfy `DEL-01` (`06.3-DESIGN.md:3-5`).
  - Pins approval to the exact `06.3-DESIGN.md` SHA-256 digest and `reviewed_revision` commit (`06.3-01-PLAN.md:70,75`) without coupling to later execution-output edits in `SUMMARY.md`/`MATRIX.md`, and without introducing an unauthorized dependency-installation gate.
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-02

- **Summary:** Implements the Wave 2 end-to-end tracer (`02-01`) for callback-free relationship inspection (`inspect_deletion`), origin-labelled native deletion (`execute_deletion` / `_DeleteCollector` / `_NativeDeleteBlocked`), independent incomplete-preview notices, and delete-scoped alias pinning (`cv_get_delete_db_alias`), then migrates all legacy collection/classifier test contracts in `tests/test1/test_delete.py` (`02-02`).
- **Strengths:**
  - Replaces `NestedObjects.collect` (`src/crud_views/lib/views/delete.py:213-214`) and the disproven frame/metadata classifier (`delete.py:43-126,373-379`) with a callback-free inspector and origin-aware collector while keeping `RelatedObjects(tree, summary, protected)` (`delete.py:33-36`) compatible.
  - Closes `C2-L03` in `02-02` (`06.3-02-PLAN.md:124,195`) by citing the exact helper functions `_assert_handler_error` (`tests/test1/test_delete.py:1122`) and `_assert_collection_extension_propagates` (`tests/test1/test_delete.py:1109`) alongside `_delete_probe` (`test_delete.py:789`), classifier imports (`test_delete.py:1143,1295,1381`), the `NestedObjects` router spy (`test_delete.py:851`), the `delete(self)` spy (`test_delete.py:1078`), and `base.Collector` patching (`test_delete.py:1444`).
  - Preserves `Author` (`OrderedModel`) and `Car` (`PolymorphicModel`) on the custom `delete(using=using)` path (`06.3-02-PLAN.md:99`) and verifies `test_delete.py`, `test_guardian_delete.py`, `test_polymorphic.py`, `test_transactions.py`, and `test_form_buttons_golden.py` together (`06.3-02-PLAN.md:127`).
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-03

- **Summary:** Expands `_DeleteInspector` in Wave 3 to cover full native graph semantics (deferred `RESTRICT` diamond closure, cycles, self-relations, multi-table parents with `collect_related=False`, `ForeignKey(to_field=...)`, proxy and auto-created through models), introduces the boundary-scoped `cv_get_delete_preview` provider contract and startup/runtime override diagnostics (`03-01`), and adds English/German partial-count and incomplete-preview notices (`03-02`).
- **Strengths:**
  - Uses `field.get_foreign_related_value(source)` and `field.get_local_related_value(child)` with `related_fields` and `field.attname` (`06.3-03-PLAN.md:105`) so non-PK `to_field` joins and distinct multi-table parent-link keys are queried accurately on `using`.
  - Closes `C2-L01` in `03-01` (`06.3-03-PLAN.md:105,108,187`) by guarding startup `model.delete` signature inspection in `DeleteView.checks()` (`src/crud_views/lib/views/delete.py:178-188`) when `cv_viewset` is `None`, when `cv_viewset.is_resource` is true (preserving `viewset.E262` at `src/crud_views/lib/viewset/__init__.py:208`), or when `model` is absent/non-`Model`, and by running `tests/test1/test_modal.py` alongside `test_signature_checks_skip_bare_and_resource_views`.
  - Renders the `delete_preview_incomplete` warning in `src/crud_views/templates/crud_views/view_delete.content.html:5-21` outside the `delete_protection_errors` branch so `D-03`/`D-12` combinations (including `cv_show_related_objects=False` and custom protection errors) always display it.
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-04

- **Summary:** Audits and tests `_DeleteCollector` write-side provenance across Django 4.2/5.2/6.0 (`04-01`) and proves real transaction commit/rollback and external side-effect behavior across `cv_atomic=True` and `cv_atomic=False` (`04-02`).
- **Strengths:**
  - Defines deterministic ordering between native `PROTECT`/`RESTRICT` and custom callbacks (`06.3-04-PLAN.md:96`): nonempty native `PROTECT` stops collection immediately (raising `_NativeDeleteBlocked` only if `custom_callback_entered` is `False`, or propagating `ProtectedError` if a custom callback already ran), while `SET_NULL` and `DO_NOTHING` remain native and non-sticky.
  - Tests real durability with `@pytest.mark.django_db(transaction=True)`, external callback event lists, and `connection.in_atomic_block` checks (`06.3-04-PLAN.md:119`) across custom handlers, `SET`/`SET_DEFAULT` callables, nested converters, model overrides, signals, `cv_form_valid_hook`, and `cv_on_commit`.
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-05

- **Summary:** Configures an independent `shard` SQLite database in `tests/test1/conftest.py:91-96`, proves single-evaluation instance-aware alias pinning across inspection, deletion, `transaction.atomic`, and `transaction.on_commit` with colliding PKs (`05-01`), and scopes Guardian `_PermittedPks` label projection and caching to the candidate's database alias under a runtime topology predicate (`05-02`).
- **Strengths:**
  - Enforces a comprehensive runtime topology predicate in `_PermittedPks` (`src/crud_views_guardian/lib/views.py:59-95`) before all label paths (superuser, global fallback, auto-created through tables, and object/group grants), verifying `actor._state.db == using`, model/join query routes (`User`, `Group`, `Permission`, `ContentType`, `user.groups.all().db`, Guardian object-permission models), and `ct._state.db == using`, failing closed to `set()` on any mismatch (`06.3-05-PLAN.md:134`).
  - Closes `C2-L02` in `05-02` (`06.3-05-PLAN.md:14,45-46,75,118,134,137,201`) by making `_PermittedPks.__call__(model, *, using)` require an explicit keyword-only `using` argument, owning `tests/test1/test_guardian_inactive.py` in Wave 5 (after Wave 3's `06.3-06`), migrating all direct `_PermittedPks` callers in `tests/test1/test_guardian_delete.py:69,84,95,97,113,115,126,133,157,179` and `tests/test1/test_guardian_inactive.py:404`, and verifying `test_guardian_inactive.py` in `C0502` (`06.3-VALIDATION.md:133`).
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-06

- **Summary:** Remediates `IN-02` and `IN-03` in `src/crud_views_guardian/lib/viewset.py` by wrapping `STRICT_HELPER_POLICY` in `MappingProxyType` and validating permission keys via `_resolve_permission_key` before inactive-user shortcuts or permission mutations across `assign_perm`, `remove_perm`, and `get_objects_for_user` (`06-01`), and records the bounded `GUA-01` / residual `AUTH-06` policy review (`06-02`).
- **Strengths:**
  - Rejects both unknown string keys and non-`str` / unhashable inputs (`None`, `int`, `list`, `dict`) in `_resolve_permission_key` (`src/crud_views_guardian/lib/viewset.py:77-108`) with a descriptive `ValueError` naming `repr(perm)` and `sorted(self.permissions.keys())` before `_guardian_inactive_actor(user)` (`viewset.py:100`) or Guardian shortcuts run (`06.3-06-PLAN.md:97`).
  - Freezes `STRICT_HELPER_POLICY` (`src/crud_views_guardian/lib/viewset.py:11`) with `MappingProxyType` over a private dict while keeping `dict(STRICT_HELPER_POLICY)` detached in `GuardianManageView.get_context_data` (`src/crud_views_guardian/lib/views.py:296`).
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-07

- **Summary:** Replays actor, parent, state, HTTP method, and native-template authorization boundaries against the new callback-free inspector and safe-preview provider (`07-01`), and verifies actual `PolymorphicModel.delete` (`Car`/`Vehicle`) and `OrderedModel.delete` (`Author`) execution and failure propagation (`07-02`).
- **Strengths:**
  - Verifies that `Author` (`OrderedModel`) and `Car` (`PolymorphicModel`) run their actual bound `delete(using=using)` methods once on confirmed POST (`06.3-07-PLAN.md:124`), preserving `Author` sibling reordering and `Car`/`Vehicle` parent deletion, reporting `delete_preview_incomplete=True` unless covered by a provider, keeping `Author` form-control golden bytes unchanged, and propagating stale errors inside custom overrides.
  - Tests native template overrides and context object collections (`test_partial_native_template_context_shape`) so forbidden model instances never leak into template context (`06.3-07-PLAN.md:96`).
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-08

- **Summary:** Updates `docs/reference/delete_view.md`, `docs/reference/request_lifecycle.md`, `docs/reference/guardian.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md` with paired `### Breaking` and migration entries, and adds `tests/test1/test_delete_migration_docs.py` to extract and execute the published migration fences (`08-01`, `08-02`).
- **Strengths:**
  - Extracts and executes the first Python/Django code fence under three exact headings in `docs/migrating-1.0.md` (`### Safe deletion preview overrides`, `### Describing custom deletion effects`, and `### Copied delete templates with incomplete previews`, `06.3-08-PLAN.md:87`), testing both provider execution and copied-template rendering.
  - Amends active `Unreleased` entries in `CHANGELOG.md` and existing deletion migration sections in `docs/migrating-1.0.md` in place (`06.3-08-PLAN.md:107`), pairing every breaking change (`cv_get_related_objects` override rejection, `delete(using=...)` signature requirement, `cv_get_delete_db_alias()`, copied-template incomplete notice, and Guardian `KeyError`-to-`ValueError` invalid-key diagnostics) with `mkdocs build --strict` verification.
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## 06.3-09

- **Summary:** Provisions the supported Django 5.2 nox environment and runs the focused and full test suites across Django 4.2, 5.2, and 6.0 alongside JS (`06-js-verify.sh`), strict docs (`mkdocs build --strict`), and lint (`ruff check` / `ruff format --check`) gates (`09-01`), then reconciles `06.3-ACCEPTANCE.md` and `06.3-VALIDATION.md` (`09-02`).
- **Strengths:**
  - Uses the existing authorized `.venv/bin/python -m nox -s "tests-3.12(django='5.2')"` workflow (`noxfile.py:3-19`), verifies interpreter versions and imported module hashes before `--no-install` reruns (`06.3-09-PLAN.md:81`), and runs long series gates as separate sessions.
  - Reconciles `CR-02`–`CR-04`, `IN-02`–`IN-03`, `DEL-01`–`DEL-06`, `GUA-01`, and affected `AUTH-01`/`03`/`06`/`07` obligations to fresh versioned test nodes while keeping the four unclassified assumptions and descriptor-less prohibitions explicitly visible for human review (`06.3-09-PLAN.md:119`).
- **Concerns:**
  - **HIGH:** None
  - **MEDIUM:** None
  - **LOW:** None
- **Suggestions:** None
- **Risk:** Low

---

## Overall Verdict

All Cycle 1 (`H01`–`H06`, `M01`–`M16`) and Cycle 2 (`C2-L01`–`C2-L03`) findings are **closed** in commit `1366dac`, and no new HIGH, MEDIUM, or LOW plan-fitness defects were found. The 9-plan package and `06.3-DESIGN.md` are ready to proceed to the `DEL-01` blocking-human maintainer review checkpoint in `06.3-01`.
