# Ancestor authorization — query measurements

Companion to the [ancestor authorization design v2](2026-11-07-ancestor-authorization-design-v2.md), section
"Performance and caching". Each measurement set is labelled by mode: the `legacy` baseline was taken before any
ancestor policy existed (Task 1); the [final comparison](#final-comparison-modes-full-and-nearest) adds the shipped
`full` (global cascade) and `nearest` (`AncestorPolicy(cascade=False)` on the requested ViewSet) modes for the
identical fixture operations, plus top-level requests.

## How to reproduce

```bash
CV_ANCESTOR_PERF_REPORT=/tmp/ancestor-perf.jsonl .venv/bin/pytest tests/test1/test_ancestor_performance.py -n 4 -v
```

Each measured test appends one JSON line per request (mode, family, depth, key, phase, status, queries, categories).
The fixtures live in `tests/test1/ancestor_cases.py`; the measuring tests are
`test_one_and_three_level_query_costs` (modes `full` and `nearest`) and `test_no_top_level_ancestor_queries`
(mode `top-level`) in `tests/test1/test_ancestor_performance.py`. The `legacy` rows came from the same fixture at
the Task 1 baseline, where the test carried a `MODE = "legacy"` constant; that code path no longer exists.

## Fixture and operations (identical for every mode)

- **Chains.** Depth 1: Publisher → Book (endpoint Book). Depth 3: Publisher → Book → BookNote → AncestorAttachment
  (endpoint AncestorAttachment, a test-only model). Every chain is built with unique ViewSet names, its own URL
  module, and restores the registry, the settings singleton, URL caches, and permission vocabulary afterwards.
- **Families.** `core`: core `ViewSet`s with plain `ListView`, `DetailView`, and `CreateViewParentMixin` +
  `CreateView` (no local permission gate). `guardian`: `GuardianViewSet`s with
  `GuardianListViewPermissionRequired`, `GuardianDetailViewPermissionRequired`, and `CreateViewParentMixin` +
  `GuardianCreateViewPermissionRequired`. Ancestor levels register list and detail views of the same family.
- **Requests.** One `GET` per endpoint key: `list` (two rows), `detail` (first row), `create` (form display; a Write
  operation). Navigation actions are disabled (`cv_context_actions = []`, `cv_list_actions = []`) and every view
  renders one fixed template without context processors.
- **Grants.** One ordinary active user. `core`: model `view`, `add`, and `change` on every chain model. `guardian`:
  object `view` and `change` on every ancestor object and both endpoint rows; no model permissions. These grants
  satisfy every mode, so all modes measure the same successful operations.
- **Cold/warm.** Cold: content-type cache, `check._VOCAB_CACHE`, and each chain ViewSet's `_default_permissions` are
  cleared just before the request. Warm: the identical request repeated immediately afterwards.
- **Categories.** Each statement is attributed to the table it reads (first `FROM`), or to the Guardian grant table
  when it joins one (`guardian_userobjectpermission` / `guardian_groupobjectpermission`).

## Baseline: mode `legacy`

- Baseline revision: `016d402a` (branch `feat/ancestor-authorization`), plus only the test-only `AncestorAttachment`
  model and the two test modules above; no authorization code changed.
- Python 3.12.3, Django 6.1.2, django-guardian 3.5.2, Pydantic 2.14.1, SQLite in-memory.
- Every request returned status 200.

| Family | Depth | Key | Phase | Queries | SQL categories |
| --- | --- | --- | --- | --- | --- |
| core | 1 | list | cold | 1 | app_book 1 |
| core | 1 | list | warm | 1 | app_book 1 |
| core | 1 | detail | cold | 1 | app_book 1 |
| core | 1 | detail | warm | 1 | app_book 1 |
| core | 1 | create | cold | 0 | — |
| core | 1 | create | warm | 0 | — |
| core | 3 | list | cold | 1 | app_ancestorattachment 1 |
| core | 3 | list | warm | 1 | app_ancestorattachment 1 |
| core | 3 | detail | cold | 1 | app_ancestorattachment 1 |
| core | 3 | detail | warm | 1 | app_ancestorattachment 1 |
| core | 3 | create | cold | 0 | — |
| core | 3 | create | warm | 0 | — |
| guardian | 1 | list | cold | 11 | app_book 1, app_publisher 1, auth_permission 2, auth_user 1, django_content_type 3, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 1 | list | warm | 6 | app_book 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 1 | detail | cold | 12 | app_book 1, app_publisher 1, auth_permission 2, auth_user 1, django_content_type 2, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 |
| guardian | 1 | detail | warm | 8 | app_book 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 |
| guardian | 1 | create | cold | 7 | app_publisher 1, auth_permission 1, auth_user 1, django_content_type 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 1 | create | warm | 5 | app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 3 | list | cold | 11 | app_ancestorattachment 1, app_booknote 1, auth_permission 2, auth_user 1, django_content_type 3, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 3 | list | warm | 6 | app_ancestorattachment 1, app_booknote 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 3 | detail | cold | 12 | app_ancestorattachment 1, app_booknote 1, auth_permission 2, auth_user 1, django_content_type 2, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 |
| guardian | 3 | detail | warm | 8 | app_ancestorattachment 1, app_booknote 1, auth_user 1, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 |
| guardian | 3 | create | cold | 7 | app_booknote 1, auth_permission 1, auth_user 1, django_content_type 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 3 | create | warm | 5 | app_booknote 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |

Observations on the baseline:

- Plain core endpoints perform no ancestor work at all: no session/user load, no parent lookup, and no permission
  query. Their list/detail querysets filter by the URL parent keys in one statement.
- Legacy Guardian authorization checks only the immediate parent (`app_publisher` at depth 1, `app_booknote` at
  depth 3): depth 3 costs the same as depth 1, and Publisher and Book are neither loaded nor checked.
- Each Guardian object check is a user-grant plus a group-grant lookup. Detail performs two (parent and object),
  list and create one (parent). Cold extra statements are permission-vocabulary and content-type discovery.

## Final comparison: modes `full` and `nearest`

- Revision: `33c1d9fe` (all Tasks 1–7 shipped) plus the Task 8 test changes only; same machine and virtualenv as the
  baseline: Python 3.12.3, Django 6.1.2, django-guardian 3.5.2, Pydantic 2.14.1, SQLite in-memory.
- Command: `CV_ANCESTOR_PERF_REPORT=<file> .venv/bin/pytest tests/test1/test_ancestor_performance.py -n 4 -v`
  (32 passed). A serial rerun (`-p no:xdist`) produced the identical table.
- Every measured request returned status 200 in both modes; the fixture, grants and operations are the Task 1 ones
  unchanged, so `legacy`, `full` and `nearest` measure the same successful requests.
- `nearest` equals `full` at depth 1 by definition (one ancestor). Its single cold-list difference (10 vs 11) is a
  process-state artefact: the case runs directly after the `full` case in the same worker, and a Guardian-side content
  type lookup stays cached; run in isolation both cases issue 11 statements.

| Family | Depth | Key | Phase | legacy | full | nearest | Δ full | full SQL categories | nearest differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| core | 1 | list | cold | 1 | 12 | 12 | +11 | app_book 1, app_publisher 1, auth_permission 3, auth_user 1, django_content_type 5, django_session 1 | same |
| core | 1 | list | warm | 1 | 6 | 6 | +5 | app_book 1, app_publisher 1, auth_permission 2, auth_user 1, django_session 1 | same |
| core | 1 | detail | cold | 1 | 12 | 12 | +11 | app_book 1, app_publisher 1, auth_permission 3, auth_user 1, django_content_type 5, django_session 1 | same |
| core | 1 | detail | warm | 1 | 6 | 6 | +5 | app_book 1, app_publisher 1, auth_permission 2, auth_user 1, django_session 1 | same |
| core | 1 | create | cold | 0 | 11 | 11 | +11 | app_publisher 1, auth_permission 3, auth_user 1, django_content_type 5, django_session 1 | same |
| core | 1 | create | warm | 0 | 5 | 5 | +5 | app_publisher 1, auth_permission 2, auth_user 1, django_session 1 | same |
| core | 3 | list | cold | 1 | 26 | 14 | +25 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 5, auth_user 1, django_content_type 15, django_session 1 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 3, auth_user 1, django_content_type 5, django_session 1 |
| core | 3 | list | warm | 1 | 8 | 8 | +7 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 2, auth_user 1, django_session 1 | same |
| core | 3 | detail | cold | 1 | 26 | 14 | +25 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 5, auth_user 1, django_content_type 15, django_session 1 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 3, auth_user 1, django_content_type 5, django_session 1 |
| core | 3 | detail | warm | 1 | 8 | 8 | +7 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 2, auth_user 1, django_session 1 | same |
| core | 3 | create | cold | 0 | 25 | 13 | +25 | app_book 1, app_booknote 1, app_publisher 1, auth_permission 5, auth_user 1, django_content_type 15, django_session 1 | app_book 1, app_booknote 1, app_publisher 1, auth_permission 3, auth_user 1, django_content_type 5, django_session 1 |
| core | 3 | create | warm | 0 | 7 | 7 | +7 | app_book 1, app_booknote 1, app_publisher 1, auth_permission 2, auth_user 1, django_session 1 | same |
| guardian | 1 | list | cold | 11 | 11 | 10 | +0 | app_book 1, app_publisher 1, auth_permission 2, auth_user 1, django_content_type 3, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 | app_book 1, app_publisher 1, auth_permission 2, auth_user 1, django_content_type 2, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 1 | list | warm | 6 | 6 | 6 | +0 | app_book 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 | same |
| guardian | 1 | detail | cold | 12 | 12 | 12 | +0 | app_book 1, app_publisher 1, auth_permission 2, auth_user 1, django_content_type 2, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 | same |
| guardian | 1 | detail | warm | 8 | 8 | 8 | +0 | app_book 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 | same |
| guardian | 1 | create | cold | 7 | 7 | 7 | +0 | app_publisher 1, auth_permission 1, auth_user 1, django_content_type 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 | same |
| guardian | 1 | create | warm | 5 | 5 | 5 | +0 | app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 | same |
| guardian | 3 | list | cold | 11 | 21 | 12 | +10 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 4, auth_user 1, django_content_type 5, django_session 1, guardian_groupobjectpermission 3, guardian_userobjectpermission 3 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 2, auth_user 1, django_content_type 2, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 3 | list | warm | 6 | 12 | 8 | +6 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 3, guardian_userobjectpermission 3 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 3 | detail | cold | 12 | 22 | 14 | +10 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 4, auth_user 1, django_content_type 4, django_session 1, guardian_groupobjectpermission 4, guardian_userobjectpermission 4 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_permission 2, auth_user 1, django_content_type 2, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 |
| guardian | 3 | detail | warm | 8 | 14 | 10 | +6 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 4, guardian_userobjectpermission 4 | app_ancestorattachment 1, app_book 1, app_booknote 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 2, guardian_userobjectpermission 2 |
| guardian | 3 | create | cold | 7 | 17 | 9 | +10 | app_book 1, app_booknote 1, app_publisher 1, auth_permission 3, auth_user 1, django_content_type 3, django_session 1, guardian_groupobjectpermission 3, guardian_userobjectpermission 3 | app_book 1, app_booknote 1, app_publisher 1, auth_permission 1, auth_user 1, django_content_type 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | 3 | create | warm | 5 | 11 | 7 | +6 | app_book 1, app_booknote 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 3, guardian_userobjectpermission 3 | app_book 1, app_booknote 1, app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |

Top-level requests (`test_no_top_level_ancestor_queries`; one cold request each; traversal, gate selection, both
providers and the authorization-route validation are patched to fail, so any ancestor work would raise):

| Family | Key | Queries | SQL categories |
| --- | --- | --- | --- |
| core | create | 0 | — |
| core | detail | 1 | app_publisher 1 |
| core | list | 1 | app_publisher 1 |
| guardian | create | 4 | auth_permission 2, auth_user 1, django_session 1 |
| guardian | detail | 5 | app_publisher 1, auth_user 1, django_session 1, guardian_groupobjectpermission 1, guardian_userobjectpermission 1 |
| guardian | list | 4 | app_publisher 1, auth_user 1, django_content_type 1, django_session 1 |

### What changed and why

The legacy baseline was a weaker policy, so higher counts are expected where the new contract does more work. The
differences, by cause:

- **Core plain endpoints now authorize their ancestors.** Legacy plain core views performed no actor or ancestor work
  at all (1 query for list/detail, 0 for the create form). They now load the session and user (2), resolve each
  ancestor through its ViewSet queryset (1 SELECT per level, so +1 at depth 1 and +3 at depth 3), and evaluate model
  permissions: Django's `ModelBackend` loads the actor's user and group permissions once per request (2 statements,
  then cached on the request's user object), so further model gates in the same request are free when warm. Warm:
  depth 1 = 6 (list/detail) / 5 (create), depth 3 = 8 / 7, identical in both modes.
- **Cold permission vocabulary.** The first request per process resolves each gated ancestor's permission map
  (`ViewSet.default_permissions`): one `get_for_model` content-type lookup, one `auth_permission` query, then one
  `django_content_type WHERE id = …` lookup per permission row (4 for the default permissions). Those four identical
  lookups come from the existing vocabulary builder reading `permission.content_type` per row
  (`src/crud_views/lib/viewset/__init__.py`, `default_permissions`); they occur once per ViewSet per process and are
  cached afterwards. They are not repeated ancestor checks. A `select_related("content_type")` there would remove
  them; it is pre-existing code outside this feature and is left as a follow-up. At depth 3, `full` pays this for
  three ancestors (15 content-type statements) and `nearest` for one (5).
- **Guardian depth 1 is unchanged** (11/6 list, 12/8 detail, 7/5 create): the immediate parent was already loaded once
  and checked with one user-grant plus one group-grant lookup; the shared mechanism does the same work.
- **Guardian depth 3, full cascade** adds the two higher ancestors: +2 SELECTs (Publisher, Book) and +2 grant
  lookup pairs (+4), plus cold vocabulary for them; legacy checked only the immediate parent. Warm: +6 for every
  endpoint. The endpoint's own object gate (detail) and list filtering are independent local work and unchanged.
- **Guardian depth 3, nearest-only** still resolves Publisher and Book (+2 SELECTs, relationship validation) but
  evaluates only the nearest gate, so the grant lookups equal legacy: warm +2 over legacy, −4 against `full`.
- **Parent reuse.** Each ancestor is selected exactly once per request (`app_publisher 1`, `app_book 1`,
  `app_booknote 1` in every row). The create form's structural parent and the Guardian nested state gate reuse the
  resolved object, so create performs no second parent lookup.
- **No duplicate ancestor checks.** Every selected gate issues exactly one evaluation (one grant pair per Guardian
  gate; one permission load per request for the model provider). The dispatch bridges are idempotent per view
  instance; `test_guardian_order_matches_core_order` asserts one `authorize_ancestors` call for both Guardian mixin
  orders, so bridge reentry adds no work.
- **Top level** performs no ancestor work: core list/detail 1 query and create 0, as in the legacy plain views;
  Guardian top-level counts are only the endpoint's own actor, permission and filtering work.

No fixed backend-independent query budget is asserted: counts vary across Django versions, backends, caches and
custom querysets. Cascade depth is a cost control (it removes higher gate evaluation), not a claim that traversal is
free; the relationship and visibility reads of higher levels remain in both modes.

### Behavioural guarantees backing the numbers

| Test | Asserts |
| --- | --- |
| `test_ancestor_performance.py::test_no_top_level_ancestor_queries` (6) | core/Guardian list, detail and create on a top-level ViewSet never enter traversal, gate selection, a provider or route validation |
| `test_ancestor_performance.py::test_nearest_only_never_checks_higher_permissions` (core, guardian) | only the nearest gate is evaluated (`near_gate`, `app.view_booknote`), while `top`/`mid` querysets still run (1 Publisher and 1 Book SELECT); the same grants under full cascade stop at the outermost gate (403) |
| `test_ancestor_guardian.py::test_revocation_applies_on_next_request` (6) | Guardian direct grant, group grant, group membership, Guardian ancestor model fallback, core model grant and core group model grant: a revoke between two requests of one session denies the next request |
| `test_ancestor_performance.py::test_one_and_three_level_query_costs` (24) | status 200 for the cold and warm request of every case in both modes; counts recorded |
