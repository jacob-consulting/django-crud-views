# Bulk actions

!!! example "Try it live"
    The [Bulk selection example](https://django-crud-views-demo.onrender.com/bulk-selection/document/) in the live demo
    offers table and card selection, archive, owner assignment and leaf deletion. Log in as `alice` / `alice`.
    See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

Bulk actions operate on an explicit selection from the current table or card page. The source offers registered
action form views in the same ViewSet. Each destination owns admission, scope, eligibility, confirmation and
the application operation. Selection does not carry across pages.

## Classes

Public imports come from `crud_views.lib.bulk`:

| Class | Purpose |
|-------|---------|
| `BulkSelectionMixin` | Opt a table or card source into current-page checkboxes and action buttons. |
| `BulkFormViewPermissionRequired` | Resolve, review and execute a selection in a non-object custom form view. |
| `BulkConfirmForm` | Default fieldless `CrispyForm` with Confirm and Cancel buttons. |

There is one destination class, and it is permission-required. Set its `cv_permission` explicitly to the
appropriate ViewSet permission-map key, such as `change` or `delete`.

## Basic usage

This example assumes a `Document` model with `title`, `is_locked` and `is_archived` fields. Register the source
and destination on one ViewSet, and include its `urlpatterns` as usual:

```python
import django_tables2 as tables

from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.table import Table
from crud_views.lib.views import ListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import ViewSet
from .models import Document

document_viewset = ViewSet(model=Document, name="bulk_document", prefix="document")


class DocumentTable(Table):
    title = tables.Column()


class DocumentListView(BulkSelectionMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = document_viewset
    table_class = DocumentTable
    cv_bulk_actions = ("archive",)


class ArchiveDocumentsView(BulkFormViewPermissionRequired):
    cv_viewset = document_viewset
    cv_key = "archive"
    cv_path = "archive"
    cv_permission = "change"
    cv_action_label_template_code = "Archive selected documents"
    cv_action_short_label_template_code = "Archive"
    cv_icon_action = "fas:box-archive"
    cv_success_key = "list"
    cv_atomic = True

    def cv_bulk_check(self, obj):
        return ["Locked documents cannot be archived."] if obj.is_locked else []

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            document.is_archived = True
            document.save(using=self.cv_get_db_alias(), update_fields=["is_archived"])
```

`cv_bulk_actions` is a tuple of unique destination keys. The destination's short action label and
`cv_icon_action` label its toolbar button; its full action label supplies the review header through the
read-only `cv_bulk_header` property. No separate bulk caption is needed.

## Selection on tables and cards

Place `BulkSelectionMixin` before `ListViewTableMixin`, or before the card view base such as
`CardListViewPermissionRequired`. It is usually the first base; a project mixin which does not define
`get_table_kwargs`, such as the example project's `BreadcrumbMixin`, may precede it.
`ListViewTableMixin.get_table_kwargs` does not call `super()`, so placing the selection mixin after it loses
the selection column.

The mixin prepends a non-orderable checkbox column named `cv_bulk_select`; reserve that name in your tables.
Cards receive their checkbox from the grid wrapper, so a custom `cv_card_template` needs no selection markup.
Checkbox labels and the review list show `str(record)`; the application loads what `__str__` reads, because
a deferred field or a relation can cost one query per record.

An overridden list or card content template must include `crud_views/snippets/bulk_toolbar.html` alongside
its table or grid. Support one bulk source per page. The toolbar renders every configured action without
scanning the page for eligible objects or issuing bulk-permission queries; admission happens on submission.

## How a submission is handled

The `cv_bulk_` POST prefix is reserved. Its transport fields are:

| Field | Meaning |
|-------|---------|
| `cv_bulk_ids` | Repeated candidate primary keys. |
| `cv_bulk_blocked_ids` | Repeated previously excluded primary keys; informational on review. |
| `cv_bulk_stage` | Exactly one of `review` or `execute`. |

The source posts to the destination with CSRF protection and stage `review`. Admission runs first: the real
destination's permission and ancestor checks run before selection resolution. The destination bounds the
submission, parses and deduplicates keys, resolves them within its scope, then calls `cv_bulk_has_permission`
before `cv_bulk_check`. The review contains an unbound action form and the eligible and blocked groups.

Confirm posts stage `execute` to the same destination, retaining the origin query string. The review form
posts as multipart, so file fields work. On execution, the configured transaction contains fresh resolution
and eligibility checks, form validation, and the application write. `self.cv_bulk_objects` is the tuple of
fresh eligible model instances available to form hooks.

The write belongs in `cv_form_valid`; `viewset.E279` rejects a destination which inherits the no-op method,
even if it writes in `cv_form_valid_hook`. Keep `cv_post_hook`, form validation and both item hooks read-only.
A bulk destination does not call `cv_form_valid_process`, because it checks eligibility inside the transaction
before the write and calls `cv_form_valid` and `cv_form_valid_hook` itself inside `cv_get_atomic()`.
An override of `cv_form_valid_process` has no effect on a bulk destination, so override `cv_form_valid` for
the write or `cv_form_valid_hook` for an extension.

`cv_atomic`, `cv_get_db_alias()` and `cv_on_commit` retain the normal
[transaction and hook contracts](request_lifecycle.md). Preserve `super()` when extending the success hook
if you want `MessageMixin` to queue its default message.

## Confirmation

`cv_bulk_confirm = True` is the default. An action requires input when its form class **declares fields**;
use a `CrispyForm` subclass as `form_class` for such an action.

| Confirmation | Input | Eligible selection | Outcome |
|--------------|-------|--------------------|---------|
| `True` | Either | At least one eligible | Show the review and form before execution. |
| `False` | No declared fields | All eligible | Execute immediately after the checks. |
| `False` | No declared fields | Some blocked | Show the review; write nothing until confirmed. |
| `False` | Declared fields | At least one eligible | Show the review and input form. |
| Either | Either | All blocked | Show blocked records and Cancel, without an execution button. |

The review is a full page; modal review is unsupported. `cv_modal = True` fails the existing
`viewset.E251` check: the custom form views listed as supported in that check's message are the stock
custom form views, not bulk destinations.

The live example uses a `Document.Status` enum instead of the introductory recipe's `is_archived` field.
Its `cv_document` is the example's ViewSet, and `_` is Django's `gettext_lazy`.
`BreadcrumbMixin` belongs to the example project and is not needed for bulk actions.
This destination runs immediately for eligible drafts and asks for confirmation when any selected record is blocked:

<!-- cv-sync: bulk_selection/views.py -->
```python
class ArchiveDocumentsView(BreadcrumbMixin, BulkFormViewPermissionRequired):
    cv_viewset = cv_document
    cv_key = "archive"
    cv_path = "archive"
    cv_permission = "change"
    cv_icon_action = "fas:box-archive"
    cv_action_label_template_code = _("Archive selected documents")
    cv_action_short_label_template_code = _("Archive")
    cv_bulk_confirm = False
    cv_success_key = "list"
    cv_success_keys = ["list", "card"]
    cv_message_template_code = (
        "{% load i18n %}{% blocktranslate count count=view.cv_bulk_objects|length %}"
        "{{ count }} document archived.{% plural %}{{ count }} documents archived."
        "{% endblocktranslate %}"
    )

    def cv_bulk_check(self, obj):
        if obj.is_locked:
            return [_("Locked documents cannot be archived.")]
        return [] if obj.status == Document.Status.DRAFT else [_("Only drafts can be archived.")]

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            document.status = Document.Status.ARCHIVED
            document.save(using=self.cv_get_db_alias(), update_fields=["status"])
```

## Eligible and blocked records

`cv_bulk_has_permission(obj)` returns a boolean; its default is `True`. `cv_bulk_check(obj)` returns a list
of business-rule reasons; its default is an empty list. Both hooks must be read-only. Eligibility runs
once per request, inside the configured transaction on any request which can write.

Blocked rows are informational: they cannot be promoted or unchecked on the review. A previously excluded
record remains excluded even if it becomes eligible; select it again from the source to include it.
If a candidate loses eligibility before execution, the request writes nothing and asks for confirmation
again with the fresh groups. Form validation errors also preserve those groups for another resolution.

Missing, out-of-scope and permission-denied records share one unavailable message without a label. A visible,
permitted record blocked by a business rule shows its name and reasons. Reasons are rebuilt on the server,
never trusted from the POST.

There is no stored or signed review record. An authorized direct `execute` POST still runs all checks;
the server does not prove that the user visited a review page or selected those IDs on a preceding page.

## Scope and permissions

The invariant is **submitted IDs ∩ ViewSet queryset ∩ destination queryset ∩ parent scope**. Parent coordinates
come from the registered destination URL and the existing ancestor admission rules apply to that endpoint.
A filter that exists only on the source list is no authorization gate; shared restrictions belong in the ViewSet
or an application queryset function used by both source and destination. A destination may narrow its
`get_queryset()` further, but cannot widen the ViewSet and parent scope.

The default `cv_bulk_has_permission` returns `True`, so it adds no per-object policy. With Guardian, implement
the application policy explicitly, for example:

```python
class GuardianArchiveDocumentsView(ArchiveDocumentsView):
    def cv_bulk_has_permission(self, obj):
        return self.request.user.has_perm("documents.change_document", obj)
```

Use your actual app label and permission codename. `crud_views_guardian.W002` warns when a bulk destination
on a Guardian ViewSet inherits the default hook. If `get_queryset()` already enforces your complete item
policy, silence that ID through `SILENCED_SYSTEM_CHECKS`; see [Guardian](guardian.md).
Additional form choices, such as an owner picker, need their own scope: selection authorization does not
authorize every value of a related form field.

## Selection limit

`cv_bulk_max` defaults to **100**. The destination counts all submitted candidate and excluded IDs before loading
records, on both stages. Empty and oversized selections warn and return without writes; selection is cleared
on return. Invalid keys, duplicate stage fields or overlapping candidate and excluded lists produce HTTP 400.

`viewset.W274` warns when a declared page size exceeds an offered destination's limit. Raise `cv_bulk_max`
deliberately for larger pages. Above about **990** records, also raise Django's `DATA_UPLOAD_MAX_NUMBER_FIELDS`
from its default of 1000, allowing room for CSRF, stage and action-form fields. The limit bounds selected
roots; it does not bound related records loaded by application checks or deletion inspection.

## Result message and return

The included `MessageMixin` renders `crud_views/snippets/message/bulk.html` by default, reporting how many
records the library handed to the action. The default message has singular and plural forms ("1 record
processed." and "N records processed."), while text set through `cv_message_template_code` is the application's
own and owns its wording and plural forms. Per-record results, such as sent versus failed, need application
messages.

The example's template codes use `blocktranslate count` to select the singular or plural form from
`view.cv_bulk_objects|length`, excluding blocked records. Their inline template translations are maintained
in the example catalog and covered by its translation tests.

The success message is queued inside the transaction, so if a later hook raises, writes roll back while the
message may still be shown; see the [hook reference limit](request_lifecycle.md#hook-reference).

Success goes to `cv_success_key`, or to the source used when that origin is listed in `cv_success_keys`.
Success uses the destination's plain URL: a source with filter persistence restores its stored filter,
whereas another source shows its first page in default order.

Cancel, the warning redirect and a plain GET return to the source page with its filter, sort and page number
when its origin is accepted. The warning redirect and plain GET use three steps: origin, else `cv_cancel_key`,
else the success URL when no cancel target is accessible to the user. The success URL is not access-checked.
The Cancel button of the all-blocked page uses the same three steps, including the success URL fallback,
so that page always has a way back. A review page which still offers the action keeps the stock Cancel button,
which is not rendered when no cancel target is accessible.

The origin is carried only for an accepted source key. `cv_cancel_keys = "auto"` accepts the standard list
and card origins; configure other source keys explicitly. `viewset.W275` warns when a source is not accepted,
so Cancel and the warning redirect fall back to `cv_cancel_key` (and ultimately the success URL as above).
The stock Cancel button needs JavaScript unless the theme renders it as a link. Returning never restores
checked boxes.

To make eligible Cancel controls native links that work without JavaScript, add this project setting
(or merge the entry into your existing mapping):

```python
CRUD_VIEWS_BUTTON_CLASSES = {"form:cancel-tag": "a"}
```

The Bootstrap example enables this setting for all its forms. Native Cancel links navigate without
submitting the form, including when a required owner is empty or the selection is all blocked.
Custom forms can explicitly choose `tag="a"` or `tag="button"` on their Cancel control; see
[Cancel links](buttons.md#cancel-links) for precedence and eligibility.

## Bulk delete

Offer bulk delete only when the application can explain what deleting each selected root means. A leaf
model with no dependent records and ordinary Django deletion is a simple starting point; the absence of
child ViewSets alone does not make a model a leaf. Share a module-level protection rule with single-record
deletion, while each endpoint retains its own admission and item permission policy. The live example imports
`CrispyDeleteForm`, `CrispyViewMixin` and `MessageMixin` for its single-record delete view:

<!-- cv-sync: bulk_selection/views.py -->
```python
def document_delete_errors(document):
    return [_("Locked documents cannot be deleted.")] if document.is_locked else []


class DocumentDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_document
    form_class = CrispyDeleteForm

    def cv_check_delete_protection(self):
        return document_delete_errors(self.object)


class DeleteDocumentsView(BreadcrumbMixin, BulkFormViewPermissionRequired):
    cv_viewset = cv_document
    cv_key = "bulk_delete"
    cv_path = "bulk-delete"
    cv_permission = "delete"
    cv_icon_action = "delete"
    cv_action_variant = "danger"
    cv_action_label_template_code = _("Delete selected documents")
    cv_action_short_label_template_code = _("Delete")
    cv_success_key = "list"
    cv_message_template_code = (
        "{% load i18n %}{% blocktranslate count count=view.cv_bulk_objects|length %}"
        "{{ count }} document deleted.{% plural %}{{ count }} documents deleted."
        "{% endblocktranslate %}"
    )

    def cv_bulk_check(self, obj):
        return document_delete_errors(obj)

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            document.delete(using=self.cv_get_db_alias())
```

Add `"bulk_delete"` to the source's `cv_bulk_actions` to offer this destination. For models with related
records, add an inspection step to the business check before offering them for deletion:

```python
from crud_views.lib.deletion import inspect_deletion


def inspected_document_delete_errors(document, using):
    errors = document_delete_errors(document)
    inspection = inspect_deletion(document, using=using)
    if inspection.related.protected:
        errors.append("Deletion is blocked by related records.")
    if not inspection.complete:
        errors.append("This object's deletion needs a dedicated application action.")
    return errors
```

Call this helper from `cv_bulk_check` with `self.cv_get_db_alias()`. `inspect_deletion` reports understood
relationships and native protection; `related.protected` identifies protected relationships, and `complete`
means no unresolved boundary was found in that inspection. It supplies neither permissions nor your
single-delete protection rules, does not prove signal or external effects, and does not combine independent
roots into a universally correct batch deletion graph. Inspection walks related graphs even if you consume
only the blockers; its query and memory cost remains application work.

Consider a folder with a locked subfolder. Deleting the parent may cascade to that descendant even when the
review lists the descendant as blocked; a transaction can successfully commit that cascade. If locked
descendants must survive, block deletion of the parent too. If deleting the whole hierarchy is intended,
allow the parent and explain the cascade in the confirmation. The application chooses and implements either policy.

Errors raised while deleting are not caught by the bulk destination. With `cv_atomic = True`, an error
rolls back every deletion of the submission and surfaces as an error; native protection may change between
inspection and deletion. An on-commit failure is not a rollback. Keep external delivery in application
code, and report queued external delivery as queued, not delivered. No automatic retries, exactly-once
execution or delivery guarantees are supplied.

## Row locking

The library takes no row locks. If an action needs them, re-read and re-check inside `cv_form_valid`, after
the view enters its configured transaction:

```python
class DocumentChanged(Exception):
    """A selected document disappeared or became blocked before the locked read."""


class LockedArchiveDocumentsView(ArchiveDocumentsView):
    cv_key = "archive_locked"
    cv_path = "archive-locked"
    cv_action_short_label_template_code = "Archive with lock"
    cv_atomic = True

    def cv_form_valid(self, context):
        keys = [obj.pk for obj in self.cv_bulk_objects]
        rows = list(
            self.cv_viewset.model._default_manager.using(self.cv_get_db_alias()).select_for_update().filter(pk__in=keys)
        )
        if len(rows) != len(keys):
            raise DocumentChanged("A selected document was deleted.")
        if any(self.cv_bulk_check(obj) for obj in rows):
            raise DocumentChanged("A selected document became blocked.")
        for document in rows:
            document.is_archived = True
            document.save(using=self.cv_get_db_alias(), update_fields=["is_archived"])
```

The count comparison makes a record deleted after the check fail the whole submission instead of silently
leaving it out. A changed business rule also raises before writing; raising rolls back the whole submission.
An application may instead skip a changed record, but then owns an accurate result message.

This recipe repeats `cv_bulk_check` only: it uses the model's default manager, does not repeat the scope of
the ViewSet and destination querysets, and does not call `cv_bulk_has_permission` again. If tenant ownership
or permissions can change between check and write, read the locked rows through your scoped queryset and
repeat the permission hook on them yourself.

Do not put `select_for_update()` in `get_queryset()`: the review runs outside the view's transaction.
Row locks behave differently per database and can fail on querysets using `distinct()` or aggregation;
the application must check its database and query shape. This is why the library has no lock flag.

## Review templates

The full page is `crud_views/view_bulk_form.html`; its content is `crud_views/view_bulk_form.content.html`.
Override these two review snippets independently:

| Template | Purpose |
|----------|---------|
| `crud_views/snippets/bulk/blocked.html` | Warning and informational blocked records with their reasons. |
| `crud_views/snippets/bulk/eligible.html` | Eligible count and plain record names. |

Their override contract is `bulk_review`: `objects` holds eligible model instances, and `blocked` holds items
with `pk`, `label` and `reasons`. An unavailable item's `label` is `None`; its reasons stay generic.
The stock snippets list every record with plain names, without links or collapsed groups. The hidden
transport fields stay in the content template, so changing presentation does not move selection transport.

Source controls use `crud_views/snippets/bulk_toolbar.html` and `crud_views/columns/bulk_select.html`.
The result message uses `crud_views/snippets/message/bulk.html`.

## Toolbar buttons

There is one button per action, with and without JavaScript. These are native form submit buttons rendered by
`crud_views/tags/button/bulk.html`: `type="submit"`, `name="cv_bulk_stage"`, `value="review"` and each destination's
`formaction` preserve JavaScript-free submission. Their visible text, hidden text in icon-only mode and tooltip
all come from the destination's short action label; the icon comes from `cv_icon_action`. The full action label
appears only as the header of the review page.

Each button takes `cv_action_variant` from its destination, with inherited `secondary` as the default.
The source view's variant does not override it. Set `cv_action_variant = "danger"` on destructive destinations,
as in the delete example above. Themes configure `bulk:primary`, `bulk:secondary`, `bulk:tertiary` and `bulk:danger`
in `CRUD_VIEWS_BUTTON_CLASSES`. All four stock defaults are `btn btn-primary`, so declaring `danger` alone keeps
the stock appearance. Bulk buttons no longer inherit a project's `form:submit` override; review Confirm still
uses `form:submit`, and all-blocked Cancel still uses the form leaf and its existing form class contract.

Label mode comes only from the `bulk` location floor in `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, default `both`.
There is no per-action map. A mode-specific class key, such as `bulk:danger:icon`, takes precedence over the base
variant key when present, including an empty string or `None` override. Selection uses the effective label mode:
a missing or disabled icon falls back to `label`, so `bulk:danger:label` applies instead of `bulk:danger:icon`.
The leaf reuses `form:hidden-label` for icon-only text, `form:icon-host` for host-placed icons and the form tooltip
location, `data-cv-tooltip="form"`. Host icons add classes to the button without a duplicate inline icon.
See [Bulk button leaf](buttons.md#bulk-button-leaf) for the exact fields available to themes copying the leaf.

The seven structural class keys remain `bulk:toolbar`, `bulk:controls`, `bulk:select-all`, `bulk:checkbox`,
`bulk:actions`, `bulk:card-cell` and `bulk:card-select`; see
[Bulk selection classes](buttons.md#bulk-selection-classes) for their theme defaults.

## JavaScript

Without JavaScript, checkboxes and each action's submit button still post the selected IDs directly.
The toolbar's hidden default button uses `formmethod="dialog"` to make Enter on a checkbox a no-op;
real action buttons retain POST. Use the source on a full page, outside a native `<dialog>` element.
The enhancement adds select-this-page, a count and empty-selection button disabling, scoped to the current
toolbar through `data-cv-bulk`, `data-cv-bulk-item`, `data-cv-bulk-all`, `data-cv-bulk-count`,
`data-cv-bulk-action` and `data-cv-bulk-enhanced`.
See [Bulk selection toolbar](javascript.md#bulk-selection-toolbar) for script loading and initialization.

## System checks

| ID | Severity | Meaning |
|----|----------|---------|
| `viewset.E271` | Error | `cv_bulk_actions` must be a tuple of unique nonempty strings. |
| `viewset.E272` | Error | Each action must name a registered bulk destination in the same ViewSet. |
| `viewset.E273` | Error | Selection requires an ORM table list or card source. |
| `viewset.W274` | Warning | The declared page size exceeds an offered action's selection limit. |
| `viewset.W275` | Warning | The destination does not accept the source's origin key for Cancel. |
| `viewset.E276` | Error | A destination requires an ORM model with a scalar primary key. |
| `viewset.E277` | Error | `cv_bulk_max` must be a positive integer, not a boolean. |
| `viewset.E278` | Error | `form_class` must be a `CrispyForm` subclass. |
| `viewset.E279` | Error | Implement `cv_form_valid` and keep `cv_object = False`. |
| `crud_views_guardian.W002` | Warning | A Guardian destination inherits the default item permission hook. |

`viewset.W274` compares declared `paginate_by` and `table_pagination`; it does not see a page size computed
in `get_paginate_by()`. It reports nothing for a source without pagination: `table_pagination = False`, or
a card source whose `paginate_by` remains `None`. The existing permission, modal, label, success-key and
cancel-key checks also apply. Guardian's warning is reported by Django's system checks; see
[Guardian bulk actions](guardian.md) for where to find it.

## Limits

Supported models are Django ORM models on the default database with a single scalar primary key
(integer, UUID or string). Before anything is changed, the library checks three routes:

1. The database of the ViewSet queryset and of `get_queryset()`.
2. The write alias the view reports through `cv_get_db_alias()`.
3. Each loaded record's own database and the write route a database router gives for that record.

If any of these is not the default database, the whole request fails with `ImproperlyConfigured`; the record
is not skipped. The write itself is application code: `cv_form_valid` must write through `cv_get_db_alias()`.
The library does not intercept a write the application sends to another alias.

The ViewSet queryset and `get_queryset()` must be unsliced querysets of the ViewSet model yielding model
instances; `values()` and `values_list()` querysets are not supported, and no declaration check detects them.

Not included: cross-page selection, "select all matching", drafts, signing or receipts for the selection,
modal review, automatic deletion previews, automatic adaptation of single-record actions, row locking in
the library, composite keys, non-ORM Resources and other database aliases. The existing signed origin
query state is navigation transport, not a signed selection or review.
