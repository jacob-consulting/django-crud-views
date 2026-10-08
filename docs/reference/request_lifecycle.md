# Request lifecycle, transactions & hooks

Every write in django-crud-views (create, update, delete, custom forms, workflow transitions and
actions) goes through one of three POST handlers. This page shows the order in which your
overrides are called, which of them run inside the database transaction, and where to put side
effects such as e-mails or Celery tasks.

!!! note "Changed in 0.27.0"
    Before 0.27.0 only formsets and workflow transitions ran in a transaction, and there was no
    `cv_on_commit`. See [Migrating](#migrating) if you override `cv_form_valid_hook` or the action
    hooks.

## Overview

GET requests never write. POST requests are handled by one of three methods:

| POST handler | Used by |
|---|---|
| `CrudViewProcessFormMixin.post` | `CreateView`, `UpdateView`, `CustomFormView`, `CustomFormNoObjectView`, `WorkflowView`, polymorphic create/update |
| `DeleteView.post` | `DeleteView`, polymorphic delete |
| `ActionView.post` | `ActionView`, `OrderedUpView`, `OrderedDownView` |

Each handler has three phases:

1. **Outside the transaction:** load the object, build the context, validate.
2. **In the transaction (the write phase):** your write code and its follow-up hook. If anything
   raises, everything written in this phase is rolled back.
3. **After the commit:** `cv_on_commit(context)`, then the redirect.

## Call chains

`[atomic: …]` is the block inside `cv_get_atomic()`. `⇢ cv_on_commit` means "registered here,
runs after the commit".

### Form views

```text
get_object (if cv_object) → get_context_data → cv_post_hook → cv_form_is_valid
  valid:   cv_form_valid_process [atomic: cv_form_valid → cv_form_valid_hook ⇢ cv_on_commit]
           → cv_form_valid_redirect
  invalid: cv_form_invalid_hook → cv_form_invalid
```

### Delete views

```text
get_object → get_context_data (delete protection, related objects) → cv_post_hook → cv_form_is_valid
  valid + protection errors: render the form again (422 in a modal)
  valid:   cv_form_valid_process [atomic: cv_form_valid (delete) → cv_form_valid_hook ⇢ cv_on_commit]
           → cv_form_valid_redirect
  invalid: cv_form_invalid_hook → cv_form_invalid
```

The success URL is resolved after the delete, so it must not point at the deleted object
(system check `viewset.E254`).

### Action views

```text
get_object → get_context_data
  → cv_action_process [atomic: action() → cv_action_success (message + hook) ⇢ cv_on_commit
                                       | cv_action_error (message + hook)]
  → get_success_url → redirect
```

`cv_form_valid_process(context)` and `cv_action_process(context)` own the transaction. If you
override `post()`, call them instead of `cv_form_valid` / `action()` directly to keep it.

## Hook reference

| Hook | Views | Phase | Use it for | DB writes | Side effects | Call `super()`? |
|---|---|---|---|---|---|---|
| `cv_post_hook(context)` | form, delete | outside | preparing the context | not atomic | no | optional (base is empty) |
| `cv_form_is_valid(context) -> bool` | form, delete | outside | extra validation | no | no | yes (formsets extend it) |
| `cv_form_valid(context)` | form, delete | in transaction | the write itself | yes | no, use `cv_on_commit` | yes, unless you replace the save |
| `cv_form_valid_hook(context)` | form, delete | in transaction | follow-up writes, messages (`MessageMixin`) | yes | no, use `cv_on_commit` | yes (`MessageMixin` relies on it) |
| `cv_parent_many_to_many_through_defaults(...)` | create with m2m parent | in transaction | through-model defaults | n/a | no | no |
| `on_transition(info, ...)` | workflow | in transaction | database follow-ups of a transition | yes | no, use `cv_on_commit` | optional (base is empty) |
| `action(context) -> bool` | action | in transaction | the action itself | yes | no, use `cv_on_commit` | n/a |
| `cv_action_success_hook(context)` | action | in transaction | follow-up writes | yes | no, use `cv_on_commit` | optional |
| `cv_action_error_hook(context)` | action | in transaction | failure audit rows | yes | no | optional |
| `cv_on_commit(context)` | form, delete, action | after commit | mail, Celery, webhooks, cache invalidation | not atomic with the write | **yes** | optional (base is empty) |
| `cv_check_delete_protection() -> list[str]` | delete | outside | vetoing a delete | no | no | optional |
| `cv_form_invalid(context)` | form, delete | outside | custom invalid response | no | no | optional |
| `cv_form_invalid_hook(context)` | form, delete | outside | logging invalid submits | no | no | optional |
| `cv_form_valid_redirect(context)` | form, delete | after the write phase | custom success response | no | no | optional |

`cv_on_commit` runs only on success: never for an invalid form, never after a rollback, never when
`action()` returned `False`. `context["object"]` is the saved object where the view has one (for
deletes, the deleted instance with `pk=None`). For workflow views, `context["workflow_info"]` is the `WorkflowInfo` record
of the transition.

## Transactions

| Name | Kind | Default | Meaning |
|---|---|---|---|
| `cv_atomic` | attribute | `True` (`False` on `ResourceViewMixin`) | wrap the write phase in `transaction.atomic()` |
| `cv_get_db_alias()` | method | `router.db_for_write(viewset.model)` | database of the transaction and of `cv_on_commit` |
| `cv_get_atomic()` | method | `atomic(using=cv_get_db_alias())`, or `nullcontext()` when `cv_atomic` is `False` | the context manager around the write phase |

When `cv_on_commit` runs:

| Situation | `cv_on_commit` runs |
|---|---|
| `cv_atomic = True`, autocommit (Django's default) | right after the view's transaction commits, before the redirect |
| `cv_atomic = False`, autocommit | immediately, because there is no transaction to wait for |
| `ATOMIC_REQUESTS = True` | when the request transaction commits, after the view has returned |
| the write phase raised, or `transaction.set_rollback(True)` was called | never |

With `ATOMIC_REQUESTS = True` the view's own `atomic()` becomes a savepoint inside the request
transaction. That costs almost nothing, and an error in the write phase still rolls back only that
phase.

Formsets and workflow transitions have their own inner `atomic()` on the same database. It keeps
"purge + formset saves" and "state change + `WorkflowInfo`" all-or-nothing even with
`cv_atomic = False`.

If `cv_on_commit` raises, the data stays committed and the request ends with a server error.

## Recipes

### Side effects after commit

Never send mail, start Celery tasks or call webhooks from `cv_form_valid_hook`, `action()` or
`on_transition`: they run before the commit. A Celery worker can pick up the task before the row
is visible (`DoesNotExist`), and if the transaction rolls back, the mail is already gone. Use
`cv_on_commit`:

```python
from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.views import CreateViewPermissionRequired, MessageMixin


class OrderCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_order
    form_class = OrderForm

    def cv_on_commit(self, context):
        send_order_confirmation.delay(self.object.pk)
```

Workflow views get the transition record in the context:

```python
from crud_views_workflow.lib import WorkflowViewPermissionRequired


class CampaignWorkflowView(CrispyViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm

    def cv_on_commit(self, context):
        info = context["workflow_info"]
        send_notification(self.object, info.state_new, info.user)
```

In tests, `cv_on_commit` callbacks only run when you capture them, for example with
pytest-django's `django_capture_on_commit_callbacks(execute=True)` fixture or Django's
`TestCase.captureOnCommitCallbacks(execute=True)`.

### Rolling back a failed action

Returning `False` from `action()` shows the error message but does **not** roll back what
`action()` already wrote; a failure audit row written in `cv_action_error_hook` should survive. To
undo the action's writes, mark the transaction for rollback:

```python
from django.db import transaction

from crud_views.lib.views import ActionViewPermissionRequired


class ArchiveView(ActionViewPermissionRequired):
    cv_viewset = cv_document
    cv_key = "archive"
    cv_path = "archive"

    def action(self, context) -> bool:
        self.object.archived = True
        self.object.save()
        if not archive_storage.store(self.object):
            transaction.set_rollback(True)  # undo the save above
            return False
        return True
```

`set_rollback(True)` needs a transaction: with `cv_atomic = False` it raises
`TransactionManagementError`.

### Catching IntegrityError

`cv_form_valid` runs inside a transaction. On PostgreSQL, a caught database error leaves that
transaction unusable, and the next query raises `TransactionManagementError`. Wrap the statement
that may fail in its own `atomic()` so only that savepoint is rolled back:

```python
from django.db import IntegrityError, transaction


class TagCreateView(CrispyViewMixin, CreateViewPermissionRequired):
    cv_viewset = cv_tag
    form_class = TagForm

    def cv_form_valid(self, context):
        try:
            with transaction.atomic(using=self.cv_get_db_alias()):
                super().cv_form_valid(context)
        except IntegrityError:
            # a concurrent request created the same tag: use that one
            self.object = Tag.objects.get(name=context["form"].cleaned_data["name"])
            context["object"] = self.object
```

### Durable services

A service that opens `transaction.atomic(durable=True)` refuses to run inside another transaction
and raises `RuntimeError`. Turn the view's transaction off and let the service own it:

```python
from crud_views.lib.views.form import CustomFormViewPermissionRequired


class ImportView(CustomFormViewPermissionRequired):
    cv_viewset = cv_dataset
    cv_key = "import"
    cv_path = "import"
    form_class = ImportForm
    cv_atomic = False  # run_import() opens atomic(durable=True) itself

    def cv_form_valid(self, context):
        run_import(self.object, context["form"].cleaned_data["file"])
```

For a different boundary (for example `savepoint=False`), override `cv_get_atomic()` and return
your own context manager.

### Resource views writing ORM rows

`ResourceViewMixin` sets `cv_atomic = False`: a database transaction cannot roll back an S3 upload
or an API call. If a Resource view also writes ORM rows that must commit together, turn the
transaction on, name the database, and move the external call to `cv_on_commit` so it only happens
once the rows are committed:

```python
from django.db import router

from crud_views.lib.resource import ResourceViewMixin
from crud_views.lib.views import ActionViewPermissionRequired


class S3FileArchiveView(ResourceViewMixin, ActionViewPermissionRequired):
    cv_viewset = cv_s3file
    cv_key = "archive"
    cv_path = "archive"
    cv_atomic = True

    def cv_get_db_alias(self) -> str:
        return router.db_for_write(ArchiveLog)

    def action(self, context) -> bool:
        ArchiveLog.objects.create(key=self.object.key, user=self.request.user)
        return True

    def cv_on_commit(self, context):
        s3.copy_to_archive(self.object.key)
```

### Multiple databases

`cv_get_db_alias()` asks your `DATABASE_ROUTERS` for the write database of the ViewSet's model;
the transaction and `cv_on_commit` both use it. Override it when the write phase mainly targets
another model. Django has no transactions across databases: writes to a second database inside
`cv_form_valid` are not rolled back with the first.

## Limitations

- **No transactions across databases.** If a router sends `WorkflowInfo` or formset child models
  to a different database than the view's model, those writes are not atomic with the main write.
- **Checks run before the transaction.** Delete protection (`cv_check_delete_protection`) and the
  workflow permission check run outside the transaction and do not lock rows
  (no `select_for_update`). Two concurrent requests can both pass the check.
- **Inner blocks are always atomic.** Formset saves and workflow transitions keep their own
  `atomic()` even with `cv_atomic = False`.

## Migrating

Coming from 0.26 or earlier, four behaviours changed:

**1. `cv_form_valid_hook`, `cv_action_success_hook` and `cv_action_error_hook` run before the
commit.** Move side effects to `cv_on_commit`:

```python
# before
def cv_form_valid_hook(self, context):
    super().cv_form_valid_hook(context)
    notify_team.delay(self.object.pk)

# after
def cv_on_commit(self, context):
    notify_team.delay(self.object.pk)
```

**2. An exception in those hooks rolls back the write.** Before, the object stayed saved and the
request failed. If you relied on "saved even if the follow-up fails", catch the exception in the
hook or move the follow-up to `cv_on_commit`.

**3. `try/except IntegrityError` inside `cv_form_valid` needs a nested `atomic()`** on PostgreSQL.
See [Catching IntegrityError](#catching-integrityerror).

**4. `atomic(durable=True)` called from the write phase raises `RuntimeError`.** Set
`cv_atomic = False` on that view. See [Durable services](#durable-services).

To get the old behaviour for one view, set `cv_atomic = False`. Hooks then run in autocommit mode
as before, and `cv_on_commit` runs immediately after the write phase.
