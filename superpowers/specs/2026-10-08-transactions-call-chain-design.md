# Transactions around write operations + call-chain documentation — design

- Issue: [#31](https://github.com/jacob-consulting/django-crud-views/issues/31) (scope widened from workflow-only to all write views)
- Date: 2026-10-08
- Status: approved in brainstorming, pending spec review

## Goal

Every django-crud-views write operation (form, delete and action POSTs) runs its write phase in one database
transaction, with a dedicated post-commit hook for side effects. The call chain, the transaction boundary and every
overridable hook are documented in one reference page, with FAQ entries linking to the recipes.

## Background: current state (verified in code)

There are three POST seams that write:

| Seam | Used by |
|---|---|
| `CrudViewProcessFormMixin.post` (`crud_views/lib/views/mixins.py`) | Create, Update, CustomForm, CustomFormNoObject, Polymorphic Create/Update, Workflow |
| `DeleteView.post` (`crud_views/lib/views/delete.py`) | Delete, Polymorphic Delete |
| `ActionView.post` (`crud_views/lib/views/action.py`) | Action, OrderedUp/Down |

Two POST handlers that do not write to the database stay unchanged: `PolymorphicCreateSelectView.form_valid`
(redirect only) and `ListViewTableFilterMixin.post` (session only).

Existing `transaction.atomic()` blocks: `FormSetMixinBase.cv_form_valid` and `WorkflowView.cv_form_valid`. Both
use the `default` alias, not the model's write database.

Gaps fixed by this work:

1. `ModelForm.save()` runs `instance.save()` and `save_m2m()` without a common transaction.
2. `CreateViewParentMixin` (m2m-through branch) saves the object, then calls `m2m.add()`; if `add()` fails, the
   object is left without a parent.
3. `ActionView.action()` and `OrderedUp/DownView` writes are not atomic.
4. The existing `atomic()` blocks ignore database routing.
5. `docs/reference/workflow_view.md` recommends sending notifications and async tasks from `on_transition`, which
   runs inside an open transaction (tasks may run before the commit, or for a rolled-back write).

## Decisions

- **Boundary (option C):** `cv_form_valid` + `cv_form_valid_hook` (resp. `action()` + success/error hook) run
  inside the transaction. The new `cv_on_commit(context)` runs after the commit and is the documented place for
  side effects.
- **Configuration (option 2):** class attribute `cv_atomic: bool` (default `True`) plus overridable methods. No
  global setting. It can be added later without breaking anything if a need appears.
- **`action()` returning `False` does not roll back automatically.** `False` is a business outcome, and an automatic
  rollback would also discard writes made in `cv_action_error_hook`. Actions that want a rollback call
  `transaction.set_rollback(True)`.
- **`MessageMixin` keeps adding its message in `cv_form_valid_hook`.** Moving it would change behavior for
  subclasses that override the hook without calling `super()`.
- **The inner workflow and formset `atomic()` blocks stay** (as savepoints when `cv_atomic=True`), because their
  atomicity is something the workflow and formsets depend on, not a per-view choice.
- **Out of scope:** `select_for_update`/row locking, transactions across databases, `on_commit(robust=True)`, and a
  system check for `cv_atomic`.

## Design

### 1. Core mechanism (`CrudView`, `crud_views/lib/view/base.py`)

```python
cv_atomic: bool = True

def cv_get_db_alias(self) -> str:
    """Database alias for the write phase; follows DATABASE_ROUTERS."""
    return router.db_for_write(self.cv_viewset.model)

def cv_get_atomic(self):
    """Context manager wrapping the write phase of a POST."""
    if not self.cv_atomic:
        return nullcontext()
    return transaction.atomic(using=self.cv_get_db_alias())

def cv_on_commit(self, context: dict) -> None:
    """Runs after the write phase is committed. Put side effects here (mail, Celery, webhooks)."""
```

`cv_atomic` must be declared so that `CheckUnknownAttributes` (W280) accepts it.

Each seam calls a new method that wraps the write phase in the transaction, so a subclass that overrides `post()`
can call it and keep the transaction:

```python
# CrudViewProcessFormMixin (and therefore DeleteView)
def cv_form_valid_process(self, context: dict) -> None:
    with self.cv_get_atomic():
        self.cv_form_valid(context)
        self.cv_form_valid_hook(context)
        transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())

# ActionView
def cv_action_process(self, context: dict) -> bool:
    with self.cv_get_atomic():
        result = self.action(context)
        if result:
            self.cv_action_success(context)
            transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())
        else:
            self.cv_action_error(context)
    return result
```

When `cv_on_commit` runs:

| Situation | `cv_on_commit` runs |
|---|---|
| `cv_atomic=True`, autocommit | right after the view's `atomic()` commits |
| `cv_atomic=False`, autocommit | immediately (Django runs `on_commit` at once outside a transaction) |
| `ATOMIC_REQUESTS=True` | when the request transaction commits, after the view returns |
| rollback (exception, `set_rollback(True)`) | never |

`on_commit` is registered without `robust=`: if `cv_on_commit` raises, the data stays committed and the error
surfaces as a 500.

These stay outside the transaction: `get_object`, `get_context_data`, `cv_post_hook`, `cv_form_is_valid`, the
invalid branch, and `cv_form_valid_redirect` / `get_success_url`. The ordering from #167, where DeleteView
resolves the success URL after `delete()`, is kept.

### 2. Per-view call chains

`[atomic: …]` = inside `cv_get_atomic()`; `⇢ cv_on_commit` = registered here, runs after commit.

Form views (`CrudViewProcessFormMixin.post`):

```
get_object (if cv_object) → get_context_data → cv_post_hook → cv_form_is_valid
  valid:   cv_form_valid_process [atomic: cv_form_valid → cv_form_valid_hook ⇢ cv_on_commit]
           → cv_form_valid_redirect
  invalid: cv_form_invalid_hook → cv_form_invalid
```

DeleteView (`DeleteView.post`):

```
get_object → get_context_data (delete protection, related objects) → cv_post_hook → cv_form_is_valid
  valid + protection errors: render (422 for modal)
  valid:   cv_form_valid_process [atomic: cv_form_valid (delete) → cv_form_valid_hook ⇢ cv_on_commit]
           → cv_form_valid_redirect
  invalid: cv_form_invalid_hook → cv_form_invalid
```

ActionView (`ActionView.post`):

```
get_object → get_context_data
  → cv_action_process [atomic: action() → cv_action_success (message + hook) ⇢ cv_on_commit
                                       | cv_action_error (message + hook)]
  → get_success_url → redirect
```

Breaking changes (pre-1.0, ship in a minor release):

1. `cv_form_valid_hook`, `cv_action_success_hook` and `cv_action_error_hook` now run before the commit; side
   effects belong in `cv_on_commit`.
2. An exception raised in those hooks now rolls back the write (before: the data stayed, then a 500).
3. `try/except IntegrityError` inside `cv_form_valid` needs a nested `atomic()` on PostgreSQL, otherwise the next
   query raises `TransactionManagementError`.
4. Code calling `atomic(durable=True)` from inside the write phase raises `RuntimeError`; fix with `cv_atomic = False`
   or by overriding `cv_get_atomic()`.

### 3. Workflow, formsets, Resource views

**Workflow (`crud_views_workflow/lib/views.py`):**

- The inner `transaction.atomic()` gets `using=self.cv_get_db_alias()`.
- `on_transition` stays inside it and is documented as the hook for database follow-ups that must roll back
  together with the transition.
- `cv_form_valid` sets `context["workflow_info"] = info`, so `cv_on_commit` can read the transition record.
- The `on_transition` example in `workflow_view.md` is rewritten as a `cv_on_commit` example.
- Limitation: if `WorkflowInfo` is routed to another database than the workflow model, the two writes are not atomic.

**Formsets (`crud_views/lib/formsets/mixins.py`):** the inner `transaction.atomic()` gets
`using=self.cv_get_db_alias()`. A conditional purge followed by the formset saves stays all-or-nothing even with
`cv_atomic=False`. Limitation: formset child models routed to another database are not covered.

**Resource views (`crud_views/lib/resource.py`, `ResourceViewMixin`):**

- `cv_atomic = False`.
- `cv_get_db_alias()` returns `DEFAULT_DB_ALIAS` without consulting routers, so a pydantic `Resource` class
  never reaches custom routers. `cv_on_commit` therefore runs immediately under autocommit, or at request commit
  under `ATOMIC_REQUESTS`.
- A Resource view that also writes ORM rows sets `cv_atomic = True` and, if needed, overrides `cv_get_db_alias()`.

**Inherited without changes:** the Polymorphic Create/Update/Delete views go through the same seams, and Guardian
only overrides `dispatch()`/`get_object()` (its permission checks run before the transaction).

### 4. Documentation

**New page `docs/reference/request_lifecycle.md`** ("Request lifecycle, transactions & hooks"), in the Reference nav
next to the view pages. Sections (anchors are stable link targets):

1. Overview: GET vs. POST, the three POST seams, call-chain diagram.
2. Call chains: the three chains from §2, each step labelled *outside*, *in transaction* or *after commit*.
3. Hook reference (`#hook-reference`): a table with phase, purpose, whether DB writes are safe, whether side effects
   are safe, and whether `super()` is required, for `cv_post_hook`, `cv_form_is_valid`, `cv_form_valid`,
   `cv_form_valid_hook`, `cv_on_commit`, `cv_form_invalid`, `cv_form_invalid_hook`, `cv_form_valid_redirect`,
   `action`, `cv_action_success_hook`, `cv_action_error_hook`, `on_transition`, `cv_check_delete_protection` and
   `cv_parent_many_to_many_through_defaults`.
4. Transactions (`#transactions`): `cv_atomic`, `cv_get_atomic()`, `cv_get_db_alias()`, behavior matrix from §1.
5. Recipes:
   - `#side-effects-after-commit`: mail / Celery from `cv_on_commit`
   - `#rolling-back-a-failed-action`: `transaction.set_rollback(True)` in `action()`
   - `#catching-integrityerror`: nested `atomic()`
   - `#durable-services`: `durable=True` with `cv_atomic = False` / overriding `cv_get_atomic()`
   - `#resource-views-writing-orm-rows`
   - `#multiple-databases`
6. Limitations: no transactions across databases; delete-protection and workflow-permission checks run outside the
   transaction (no `select_for_update`); the inner workflow and formset blocks are always atomic.
7. Migrating from 0.26 and earlier (`#migrating`): the four breaking changes with before/after code.

**FAQ entries (`docs/faq.md`)**, each a 2–5 line answer linking to the recipe:

| Question | Links to |
|---|---|
| How do I send an email or start a Celery task after a save? | `#side-effects-after-commit` |
| Why does my Celery task sometimes raise `DoesNotExist`? | `#side-effects-after-commit`, `#transactions` |
| How do I undo an action's changes when `action()` returns `False`? | `#rolling-back-a-failed-action` |
| Why do I get `TransactionManagementError` after catching `IntegrityError`? | `#catching-integrityerror` |
| How do I turn off the transaction for one view? | `#transactions`, `#durable-services` |
| Where does each hook run, and which one should I override? | `#hook-reference` |

**Other doc edits:**

- `create_view.md`, `update_view.md`, `delete_view.md`, `action_view.md`, `custom_form_view.md`,
  `workflow_view.md`: link to the new page, and add a phase column to their hook tables.
- `docs/development/stability.md`: add `cv_atomic`, `cv_get_atomic`, `cv_get_db_alias`, `cv_on_commit`,
  `cv_form_valid_process` and `cv_action_process` to the documented API.
- `formsets.md` and `conditional.md`: update the existing transaction sentences to link to the new page.
- `mkdocs.yml`: add `validation: {anchors: warn}` so `mkdocs build --strict` fails on broken FAQ/recipe anchors.
  Fix any existing broken anchors this surfaces in the same change.

### 5. Tests

New file `tests/test1/test_transactions.py`. Use `django_capture_on_commit_callbacks` for `cv_on_commit` assertions;
use `transactional_db` for the autocommit "runs immediately" case.

- **Form views:**
  - an exception in `cv_form_valid_hook` leaves no row
  - with `cv_atomic=False` the same exception leaves the row
  - a failing m2m `add` in `CreateViewParentMixin` leaves no orphan
  - `cv_on_commit` runs exactly once on success, not for an invalid form, not after a rollback
- **Delete:** an exception in `cv_form_valid_hook` leaves the object in place.
- **Action:**
  - an exception in the success hook rolls back
  - `False` means no `cv_on_commit` and no automatic rollback
  - OrderedUp/Down still work
- **Workflow:**
  - `context["workflow_info"]` is available in `cv_on_commit`
  - an exception in `on_transition` rolls back both the state and `WorkflowInfo`
- **Formsets:** with `cv_atomic=False` the purge and save stay atomic; `test_conditional_formset.py` stays green.
- **Resource:**
  - `cv_atomic` is `False`
  - `cv_get_db_alias()` returns `default` without calling the router
  - `cv_on_commit` runs
- **Routing:** `cv_get_db_alias()` follows `router.db_for_write`. The test project has one database, so patch the
  router instead of adding a second database.
- **Inherited views:** one smoke test each for Polymorphic and Guardian views going through the new seam.

### 6. Changelog, issue, skill

- `CHANGELOG.md` under Unreleased:
  - `### Added`: transaction boundary, `cv_atomic`, `cv_get_atomic`, `cv_get_db_alias`, `cv_on_commit`, the
    request-lifecycle docs page and FAQ entries
  - `### Fixed`: non-atomic `save_m2m`, the parent-less object case in `CreateViewParentMixin`, routing (`using=`) for
    the formset and workflow transactions
  - `### BREAKING`: the four changes from §2
- Version bump and release are separate and happen only when the maintainer asks.
- Issue #31: comment explaining the wider scope; the PR closes it.
- Skill (`../skills`, django-crud-views plugin): short hooks/transactions section and a Common Mistakes entry
  ("side effects in `cv_form_valid_hook` → use `cv_on_commit`"); re-run the drift-audit harness.

## Success criteria

- All three POST seams run their write phase in one transaction on the model's write database; the four documented
  breaking changes are the only behavior changes.
- `cv_on_commit` never runs for a rolled-back write and always runs after a successful one.
- The new docs page, FAQ entries and cross-links build with `mkdocs build --strict` and anchor validation on.
- Full test matrix (nox) and ruff are green.
