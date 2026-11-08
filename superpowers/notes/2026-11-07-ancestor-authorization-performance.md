# Ancestor authorization — query measurements

Companion to the [ancestor authorization design v2](2026-11-07-ancestor-authorization-design-v2.md), section
"Performance and caching". Each measurement set is labelled by mode. This note starts with the `legacy` baseline,
taken before any ancestor policy existed; later tasks append the `full` and `nearest` modes for the same operations.

## How to reproduce

```bash
CV_ANCESTOR_PERF_REPORT=/tmp/ancestor-perf.jsonl .venv/bin/pytest tests/test1/test_ancestor_performance.py -n 4 -v
```

Each test appends one JSON line per measured request (mode, family, depth, key, phase, status, queries, categories).
The fixtures live in `tests/test1/ancestor_cases.py`; the measuring test is `tests/test1/test_ancestor_performance.py`
(its `MODE` constant labels the run).

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
