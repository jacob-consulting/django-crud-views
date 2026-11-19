# Simple bulk selection and action form views

Date: 2026-11-18

**Behavior reviewed November 19, 2026.** The decisions below describe a new opt-in feature for `main`. Public API names and implementation sketches are proposals for planning.

**Revised November 19, 2026 after a design review.** The maintainer approved five changes: an explicit `cv_bulk_max` limit replaces the page-size-derived limit (D-02), modal confirmation is removed (D-04, D-10), ordinary selection mistakes produce a warning and a return to the source instead of a 400, every action reports a default success message, and return navigation reuses the existing origin mechanism. The `bulk_source` field is gone as a result.

Tracked in [issue #387](https://github.com/jacob-consulting/django-crud-views/issues/387).

## 1. Purpose and decisions

Make small, explicit selections useful without requiring the maintainer to own a second view execution framework. The reusable feature collects IDs, resolves them within the ViewSet's scope, and presents an action form. Ordinary registered views own authorization, business policy, and execution.

On November 19 the maintainer ruled out merging phase 06.38 into `main`, describing it as “too complex, not maintainable”. That decision applies to the implementation developed for [issue #378](https://github.com/jacob-consulting/django-crud-views/issues/378). This simpler proposal follows the [developer-maintainability decision](../notes/2026-11-04-opt-in-url-helper-decision.md).

## gsd-handover

Carry D-01 through D-10 and the acceptance criteria into GSD planning. These are the maintainer’s decisions. Public API names, return navigation, and the no-JavaScript controls remain proposals for planning.

### D-01 — Start from main with an opt-in selection mixin

Phase 06.38 will stay off `main`. The maintainer closed #378 as “too complex, not maintainable”. Start from the existing list, card, and custom-form views on `main`. A developer opts a table or card into selection and lists the registered action views it offers in the same ViewSet. The source collects explicit IDs. Each destination is an ordinary action form view that owns admission, business rules, and execution.

### D-02 — Current-page selection and an explicit limit

Users select records on the current page. Cross-page drafts and “select all matching” are outside this feature. Each destination declares `cv_bulk_max`, default 100; a developer whose pages are larger raises it. The limit is deliberately not derived from the source’s pagination: django-tables2 honors a `per_page` URL parameter, so the visible page size is not a fixed server-side value. Count the full submission, including excluded IDs, before loading records. For an oversized or empty selection, show a warning, return the user to the source page, and perform no writes. A system check warns when a source’s configured page size exceeds the `cv_bulk_max` of an action it offers.

### D-03 — Toolbar visibility, scope, and permissions

Show every action configured for that source. Rendering the toolbar performs zero bulk-permission queries and never scans the page for an eligible record. On submission, check destination admission first. Resolve only submitted IDs within the ViewSet queryset, the applicable parent scope, and any narrower destination visibility rules. Developers supply additional per-object permission and business checks. Authorization comes from the destination and its scoped records.

### D-04 — Destination-owned confirmation settings

Each action independently configures skip confirmation with `cv_bulk_confirm` (default `True`). Tables and cards exposing that action use its setting. The review is always a full page: bulk destinations do not support `cv_modal`, and no modal variant is planned. Both simple confirmation forms and custom action forms are supported. An action “requires input” when its form class declares at least one field.

| On submission | What the user sees or the action does |
| --- | --- |
| Confirmation is enabled | Show the review before making changes. |
| Skip is enabled, all selected records qualify, and no input is needed | Execute immediately. |
| Some selected records are blocked | A mixed selection overrides skip. Show the review and let the user explicitly confirm the eligible subset. |
| The action requires input | Show its form even when skip is enabled. The review page is that form: one valid submission confirms the eligible selection and executes the action. |
| All selected records are blocked | Explain the outcome and offer a way back. There is no execution control. |

### D-05 — What confirmation guarantees

Blocked rows are informational. The review has no selection controls. If a previously eligible record becomes blocked, make no changes on that submission and ask the user to confirm the revised selection. A previously excluded record stays excluded even if it becomes eligible. The server can accept an authorized direct execution request based on fresh checks. A stored or signed record of the earlier review is unnecessary.

### D-06 — One eligibility check per request

Resolve and check the selection once on review and once on the separate execution request. For any request that can write, including skip confirmation, perform its single selection check inside the action’s configured transaction before the first write. Use that result for form validation, execution, or redisplay. Deliberately confirming an eligible subset preserves the action’s normal error and transaction semantics.

### D-07 — What blocked records reveal

For a missing, out-of-scope, or permission-denied record, omit its label and show the same message in every case: “This item is unavailable for this action.” When a record passes its permission check but a business rule blocks it, show its name and the specific reason.

### D-08 — Initial model support

Support Django ORM models on the default database with a single scalar primary key, including integer, UUID, and string keys. Defer composite keys, non-ORM Resources such as S3 objects, and operations on other database aliases.

### D-09 — Application-owned bulk delete

Developers implement a bulk delete action using the new form view and may share explicit permission and protection functions with single-record deletion. A leaf model with ordinary deletion and no dependent children is straightforward. A leaf ViewSet alone does not establish that property. For a parent with a locked descendant, a cascade can remove the descendant even if it appears blocked. The application developer decides whether to block the parent or permit and explain deletion of the hierarchy.

### D-10 — Reference guide and runnable examples

Ship a dedicated Bootstrap example app with table and card views over the same seeded documents, including eligible drafts and a locked record. Link the examples and the bulk-action reference guide in both directions.

1. **Delete selected documents** comes first. Demonstrate leaf-model bulk delete and the protection rule shared with single-record deletion. Walk through the folder and locked-descendant decision in the guide.
2. **Archive selected** demonstrates immediate execution for an all-eligible selection and a full-page review when a locked record is included.
3. **Assign owner** shows the selection and the required owner field on one full page. Submitting it confirms and assigns in one step.

## Implementation proposals for planning

These settle details for review; they are not additional claims of prior user approval:

- Two public classes: `BulkMixin` for sources and `BulkFormView` for destinations.
- Return navigation reuses the package’s existing origin mechanism (`cv_get_link_url`, `cv_cancel_keys`, `cv_success_keys`). Cancel returns to the source page with its filter, sort, and page; success goes to `cv_success_key`, or to the origin when the developer lists it in `cv_success_keys`. No bulk-specific return protocol and no `bulk_source` field.
- The source renders ordinary destination buttons as the no-JavaScript baseline. A small script replaces them with an action picker and Continue button. No hidden routing endpoint is required.

## 2. Actual use cases

| Use case | Destination |
| --- | --- |
| Archive, enable, disable, mark reviewed | Empty confirmation form plus an application update loop |
| Assign an owner or category | Normal form containing the chosen owner/category |
| Send messages | Normal form for subject/body or a message template; destination owns delivery behavior |
| Regenerate or retry work | Confirmation form that creates application jobs |
| Delete selected ordinary records | Application delete form with shared business rules and optional deletion inspection |

A large cleanup operation with application-specific scope belongs in its own custom form view. This feature does not need to become a batch-processing system to support it.

## 3. Approaches and tradeoffs

| Approach | Advantages | Costs | Decision |
| --- | --- | --- | --- |
| Adopt the phase 06.38 coordinator and relax compatibility rules | Retains the branch's features and tests | The maintainer would still own lifecycle reconstruction, MRO inspection, drafts, signing, receipts, and delete adaptation | Ruled out by the maintainer |
| Execute all actions inside the list/card mixin | Few classes for trivial actions | List view accumulates action permissions, forms, execution, and confirmation branches | Rejected in favor of separate action views |
| Selection mixin plus ordinary registered form destinations | Small responsibilities; real destination dispatch; custom forms are natural | Application explicitly implements item policy and execution | Chosen direction |

Cross-page selection, exact draft restoration, automatic deletion previews, automatic adaptation of single-record actions, and universal all-or-nothing execution are outside this proposal. Each application defines its action in a registered form view.

## 4. Public shape

Proposed exports from `crud_views.lib.bulk`:

| Class/member | Contract |
| --- | --- |
| `BulkMixin` | Opt-in selection controls for a list/card source |
| `BulkMixin.cv_bulk_actions` | Tuple of registered destination keys in the same ViewSet |
| `BulkFormView` | Permission-required, non-object custom form destination with review and selection handling |
| `cv_bulk_label` | Destination label used in source controls and the confirmation |
| `cv_bulk_max` | Largest accepted submission, counting eligible and excluded IDs; default `100` |
| `cv_bulk_confirm` | `True` (default) always shows the review; `False` lets a field-less action run immediately when nothing is blocked |
| `cv_message_template`, `cv_message_template_code` | Existing `MessageMixin` settings; the default reports how many records were processed |
| `get_queryset()` | Existing view extension point; may narrow visibility. Resolution also intersects it with the ViewSet base scope |
| `cv_bulk_has_permission(obj) -> bool` | Optional read-only item permission check; default `True` means no extra per-item policy beyond endpoint admission and queryset visibility |
| `cv_bulk_check(obj) -> list[str]` | Optional read-only business eligibility check; default `[]` |
| `cv_bulk_objects` | Tuple of freshly resolved eligible model instances available to form hooks |
| `form_class` | Ordinary Django form; defaults to empty `forms.Form` |
| `cv_form_valid(context)` | Existing custom-form execution hook; application owns the operation |
| `cv_atomic`, `cv_on_commit`, `cv_success_key`, `cv_success_keys`, `cv_cancel_keys` | Existing form-view lifecycle and navigation settings, not a new bulk contract |
| `cv_modal` | Not supported on bulk destinations; the existing check rejects it |

The proposed API uses registered view keys for dispatch. The action descriptors and built-in `BulkDelete` belonged to the phase 06.38 branch.

`cv_bulk_has_permission()` defaulting to `True` is deliberately explicit: a model permission does not imply object grants are checked. An application using Guardian or another object policy must implement the hook or narrow its readable queryset appropriately. The library invokes the hook consistently; it does not infer the application's policy.

## 5. Selection, permissions, and form flow

### Authorization scope is mandatory; display filters are not

Every operation is an explicit set of IDs. A search term, sort order, and pagination do not need to be replayed to determine those IDs.

The invariant is:

```text
resolved objects = submitted IDs
                 ∩ ViewSet queryset for the destination request
                 ∩ destination visibility queryset
```

Parent coordinates come from the registered destination URL. Existing ancestor admission applies to that real endpoint. The package's structural parent scoping is retained as a backstop. Tenant/visibility rules placed only in the source list's custom `get_queryset()` do not transfer automatically: put shared restrictions in the ViewSet or an application queryset function used by both views.

A modified hidden field cannot escape this scope. Conversely, the feature does not prove that an ID appeared on the immediately preceding page: authorized callers can submit any eligible IDs in the destination's scope. Page-only selection is the user interface, not an authorization boundary.

### Selection size

The destination compares the number of submitted IDs, eligible plus previously excluded, with its own `cv_bulk_max` before loading objects. This applies to review and to direct execution. An over-limit or empty submission adds a warning message and redirects to the source page without loading or changing anything. The checkboxes are empty after that redirect; the user selects again. Malformed input, such as an unparsable ID or an ID in both lists, only comes from a forged request and stays a 400.

### Confirmation flow

The two-stage flow below applies when confirmation is enabled. The review is a full page.

1. The source submits checked `cv_bulk_ids` directly to a configured destination with `cv_bulk_stage=review` and CSRF protection.
2. Destination dispatch applies its normal permission and ancestor gates.
3. The destination parses, normalizes, and deduplicates IDs, then resolves the complete request through the scoped queryset.
4. Item permission runs before labels or business reasons are rendered. Objects outside the scope are represented only as unavailable.
5. Business checks partition visible, permitted objects into eligible and blocked groups.
6. The response shows an unbound action form, eligible objects, and informational blocked rows.
7. The confirmation carries eligible IDs as `cv_bulk_ids` and excluded IDs as `cv_bulk_blocked_ids`. It posts `cv_bulk_stage=execute` and `cv_bulk_confirmed=1` through the actual submit button, to the same URL including its query string so the origin survives.
8. On the execution POST, the destination enters its configured transaction, resolves and checks the submitted IDs once, then binds and validates the form with those eligible objects.
9. If the candidate membership has changed, nothing executes. The same bound form is rendered with the new partition and a message requesting confirmation again.
10. Otherwise the ordinary custom-form mutation hooks run with `cv_bulk_objects` set to the fresh eligible tuple.

An execute POST goes through all checks even if a caller bypasses the initial review POST. The confirmation button records the user's intent in the normal UI flow.

### Skip confirmation

The source never knows about skip: it always posts `cv_bulk_stage=review`. The destination decides.

```text
review POST arrives
  cv_bulk_confirm is True, or the form class declares fields  -> render the review
  cv_bulk_confirm is False and the form class has no fields   -> open the transaction, check once
        nothing blocked                                       -> execute, redirect with the message
        anything blocked                                      -> render the review, write nothing
```

The destination still enforces scope, permission, and eligibility. Immediate execution and confirmed execution share one private method, so the write path exists once.

An action whose form declares fields needs no special case. Its review page is the form: **Assign owner** shows the eligible documents and asks for the new owner, and clicking **Assign** both confirms that selection and submits the assignment. If the selection has changed at submission, the usual reconfirmation rule applies. “Declares fields” is read from the form class. A form that adds fields dynamically fails validation on an immediate run and is shown to the user, which is the safe direction.

### Result message and return

`BulkFormView` includes the existing `MessageMixin` with a default template: “3 records processed.” A developer overrides `cv_message_template_code` for better wording, for example “3 documents archived.” The library reports only how many records it handed to the action. Per-record outcomes such as “7 sent, 1 failed” are application messages.

The toolbar builds each action URL with the existing `cv_get_link_url`, which carries the origin key and the signed query state of the source page. Cancel, the warning redirect, and a plain GET all return to that page with its filter, sort, and page number. Success follows `cv_success_key`, or the origin when it is listed in `cv_success_keys`.

### Eligible and blocked groups

- Only eligible IDs are candidates for execution.
- Blocked rows cannot be checked, unchecked, or promoted on the confirmation.
- A previously excluded object that becomes eligible remains excluded, with an explanation such as “Excluded from this confirmation; select it again from the list.”
- Reasons are rebuilt on the server. Never post and trust a reason or an eligibility flag.
- Use the same message for a missing record, a record outside the ViewSet or destination scope, and a record denied by the item permission check. Omit the object label in each case.
- A visible object that passes item authorization may display its label and business-rule explanation.
- Zero eligible objects means no execution control. Cancel leads back to the source page.
- Form validation errors preserve the two groups, using hidden IDs only as untrusted input for another resolution.

### Partial selection versus execution failure

The user can intentionally process 8 eligible records while leaving 2 blocked records untouched. That is not a promise to continue after a runtime error on the fifth eligible record.

The destination chooses its normal execution semantics. A database-only action with `cv_atomic=True` can roll back all eight on an exception. A message action can enqueue application delivery jobs or explicitly own delivery outcomes. The generic selection feature does not catch arbitrary exceptions and claim partial success.

No exactly-once execution, locking, durable message delivery, or automatic retry is promised. A lost response or an exception after commit can leave the client uncertain. Application actions that require stronger guarantees implement them explicitly.

## 6. Application examples

The Bootstrap example app uses the same seeded documents for three runnable actions. Include eligible drafts and a locked document so developers can try both immediate execution and a mixed selection.

1. **Delete selected documents** is the first example. The document model has no dependent children. Its single-record and bulk delete views share the same protection rule. The reference guide uses the [folder and locked subfolder](#when-to-offer-bulk-delete) to explain the policy choice for a hierarchy.
2. **Archive selected** skips confirmation when every selected document can be archived. Including a locked document opens a full-page review before any writes. The user can confirm the eligible subset.
3. **Assign owner** opens a full page that shows the eligible documents and the owner field together. Submitting the form assigns the chosen owner to the confirmed documents.

All names under `.models`, `.tables`, `.policies`, and `.delivery` below belong to the consuming application. The proposed package classes are shown in section 7. Models and permissions must be migrated normally.

### Shared scope and source views

```python
from crud_views.lib.bulk import BulkMixin
from crud_views.lib.viewset import ViewSet
from crud_views.lib.views import (
    CardListViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
)

from .models import Document
from .tables import DocumentTable


class DocumentViewSet(ViewSet):
    def get_queryset(self, view):
        # Preserve parent scoping and ordering supplied by the normal ViewSet.
        return super().get_queryset(view).filter(
            organization_id=view.request.user.organization_id,
        )


document_viewset = DocumentViewSet(model=Document, name="document")


class DocumentListView(BulkMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = document_viewset
    table_class = DocumentTable
    cv_bulk_actions = ("archive", "assign_owner", "send_messages", "bulk_delete")


class DocumentCardView(BulkMixin, CardListViewPermissionRequired):
    cv_viewset = document_viewset
    cv_bulk_actions = ("archive", "send_messages")
```

List and card can expose different destinations. The toolbar reads each configured action's label and URL. It does not call destination permission hooks or scan the visible rows for an eligible object. A user who submits an action they cannot enter receives the destination's ordinary permission response. For an admitted user who selects three records on a page of 100, only the three submitted records need item checks.

### Archive with an empty confirmation form

```python
from crud_views.lib.bulk import BulkFormView

from .policies import can_edit_document


class ArchiveDocumentsView(BulkFormView):
    cv_viewset = document_viewset
    cv_key = "archive"
    cv_path = "archive"
    cv_permission = "change"
    cv_bulk_label = "Archive selected documents"
    cv_bulk_confirm = False  # No fields: an all-eligible selection runs immediately.
    cv_success_key = "list"
    cv_success_keys = ["list", "card"]  # Offered from both sources: return to the one used.
    cv_message_template_code = "{{ view.cv_bulk_objects|length }} documents archived."
    cv_atomic = True

    def cv_bulk_has_permission(self, obj):
        return can_edit_document(self.request.user, obj)

    def cv_bulk_check(self, obj):
        if obj.is_locked:
            return ["Locked documents cannot be archived."]
        return [] if obj.status == "draft" else ["Only drafts can be archived."]

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            document.status = "archived"
            document.save(using=self.cv_get_db_alias(), update_fields=["status"])
```

This uses ordinary `save()` semantics. A developer may choose a queryset update for a specific application, but must understand its different model-hook/signal behavior. The selection library does not make that decision.

### Assign an owner using a normal form

```python
from django import forms

from .models import StaffMember


class AssignOwnerForm(forms.Form):
    owner = forms.ModelChoiceField(queryset=StaffMember.objects.none())


class AssignOwnerView(ArchiveDocumentsView):
    cv_viewset = document_viewset  # Explicit declaration registers this subclass.
    cv_key = "assign_owner"
    cv_path = "assign-owner"
    cv_bulk_label = "Assign owner"
    cv_message_template_code = "Owner assigned to {{ view.cv_bulk_objects|length }} documents."
    form_class = AssignOwnerForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["owner"].queryset = StaffMember.objects.filter(
            organization_id=self.request.user.organization_id,
        )
        return form

    def cv_bulk_check(self, obj):
        return ["Locked documents cannot be reassigned."] if obj.is_locked else []

    def cv_form_valid(self, context):
        owner = context["form"].cleaned_data["owner"]
        for document in self.cv_bulk_objects:
            document.owner = owner
            document.save(using=self.cv_get_db_alias(), update_fields=["owner"])
```

Additional form choices need their own scope too. A safe document selection does not authorize an arbitrary owner ID.

### Messages: keep external delivery in the application

Suppose the Document model declares `Meta.permissions = [("send_message", "Can send document messages")]`. The permission key is then mapped through the existing ViewSet permission vocabulary.

```python
from django import forms

from .models import MessageDelivery
from .policies import can_message_document


class MessageForm(forms.Form):
    subject = forms.CharField(max_length=200)
    body = forms.CharField(widget=forms.Textarea)


class SendMessagesView(BulkFormView):
    cv_viewset = document_viewset
    cv_key = "send_messages"
    cv_path = "send-messages"
    cv_permission = "send_message"
    cv_bulk_label = "Prepare messages"
    cv_success_key = "list"
    cv_message_template_code = "{{ view.cv_bulk_objects|length }} messages queued."
    form_class = MessageForm
    cv_atomic = True

    def cv_bulk_has_permission(self, obj):
        return can_message_document(self.request.user, obj)

    def cv_bulk_check(self, obj):
        return [] if obj.accepts_messages else ["The recipient has opted out."]

    def cv_form_valid(self, context):
        data = context["form"].cleaned_data
        for document in self.cv_bulk_objects:
            MessageDelivery.objects.using(self.cv_get_db_alias()).create(
                document=document,
                subject=data["subject"],
                body=data["body"],
                requested_by=self.request.user,
            )
```

`MessageDelivery` and its delivery process are application-owned. This example creates pending deliveries; it must report “queued,” not “sent.” It illustrates a clean database boundary without adding a job system to django-crud-views. Applications may instead send in `cv_on_commit`, but delivery failures cannot roll back committed data and callback invocation is not a durable delivery guarantee. Retries, recipient consent at delivery time, and deduplication remain application policy.

### Row locking is application code

The library takes no row locks. It loads the selected records, checks them, and hands them to `cv_form_valid`; another request can change a record between the check and the write. Do not add `select_for_update()` to `get_queryset()`: the review request runs outside a transaction and would fail.

An action that needs the guarantee reads its records again with a lock and re-runs its own check on the locked rows:

```python
class DocumentChanged(Exception):
    """A selected document changed after it was checked."""


class ArchiveDocumentsView(BulkFormView):
    # Attributes, cv_bulk_has_permission and cv_bulk_check as above.
    cv_atomic = True  # select_for_update() needs the transaction.

    def cv_form_valid(self, context):
        pks = [document.pk for document in self.cv_bulk_objects]
        locked = Document.objects.using(self.cv_get_db_alias()).select_for_update().filter(pk__in=pks)
        for document in locked:
            if self.cv_bulk_check(document):  # The same rule, now on the locked row.
                raise DocumentChanged(document.pk)
            document.status = "archived"
            document.save(using=self.cv_get_db_alias(), update_fields=["status"])
```

This costs one extra query, only in actions that need it. Raising rolls back the whole submission and surfaces as an ordinary error, like any other failure during execution. An application may instead skip the changed record; it then owns an accurate result message. No `cv_bulk_lock` flag is provided: row locks behave differently per database and fail on querysets that use `distinct()` or aggregation, and no consumer has asked for it.

### Explicit object permissions

A Guardian-using application can share its readable-object queryset between source and destination and implement the item hook directly:

```python
def cv_bulk_has_permission(self, obj):
    # Use the application's actual configured permission backend/policy.
    return self.request.user.has_perm("documents.change_document", obj)
```

This example does not infer global-permission fallback. If the application allows a model permission as a fallback, that must be explicit in its policy function. The default endpoint model-permission gate still applies: object grants alone do not enter this `BulkFormView`. An object-grants-only application needs an explicit endpoint admission policy via ordinary `has_permission()`, plus its visibility and item checks. No automatic Guardian view adapter is proposed. A system check warns when a bulk destination in a `GuardianViewSet` keeps the default item hook (section 7.7).

### Shared business deletion rule

```python
from crud_views.lib.views import DeleteViewPermissionRequired


def document_delete_errors(document):
    if document.is_locked:
        return ["Locked documents cannot be deleted."]
    return []


class DocumentDeleteView(DeleteViewPermissionRequired):
    cv_viewset = document_viewset

    def cv_check_delete_protection(self):
        return document_delete_errors(self.object)
```

The bulk destination below calls the same `document_delete_errors()` function. If the application later changes what “locked” means, both views pick up that change. Each view still enforces its own admission and per-object permission rules.

### When to offer bulk delete

Bulk selection tells you which records the user wants to delete. Your model relationships and business rules determine what deleting those records will do. Applications differ on whether removing a parent should also remove its children. The package deliberately leaves that decision to the developer who owns the data.

For a leaf ViewSet whose records have no dependent children and use ordinary Django deletion, a bulk delete view is straightforward to write. Use `BulkFormView` for selection and confirmation, reuse your single-record permission and protection rules, and delete the eligible objects in the action. Check the model relationships when deciding whether this recipe fits. A model can have dependent records even if its ViewSet has no child ViewSets.

For a hierarchy, consider a folder containing a locked subfolder. Deleting the parent can cascade to the locked subfolder even when the review lists the subfolder as blocked. A transaction can successfully commit that cascade. If locked descendants must survive, the application must also block deletion of the parent. If removing the whole hierarchy is intended, the application can allow it and explain that effect in the confirmation. The same model relationship can support either policy.

The first example is the leaf case: documents have no dependent records and use standard model deletion. It needs no deletion inspection and no error handling of its own.

```python
from .policies import can_delete_document


class DeleteDocumentsView(BulkFormView):
    cv_viewset = document_viewset
    cv_key = "bulk_delete"
    cv_path = "bulk-delete"
    cv_permission = "delete"
    cv_bulk_label = "Delete selected documents"
    cv_success_key = "list"
    cv_message_template_code = "{{ view.cv_bulk_objects|length }} documents deleted."
    cv_atomic = True

    def cv_bulk_has_permission(self, obj):
        return can_delete_document(self.request.user, obj)

    def cv_bulk_check(self, obj):
        return document_delete_errors(obj)  # Same rule as the single delete view.

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            document.delete(using=self.cv_get_db_alias())
```

When the model has related records, the guide adds one step: ask the existing inspector in the same check, so a record with protected relations is listed as blocked on the review.

```python
from crud_views.lib.deletion import inspect_deletion


class DeleteDocumentsView(BulkFormView):
    # Attributes, cv_bulk_has_permission and cv_form_valid as above.

    def cv_bulk_check(self, obj):
        errors = document_delete_errors(obj)
        inspection = inspect_deletion(obj, using=self.cv_get_db_alias())
        if inspection.related.protected:
            errors.append("Deletion is blocked by related records.")
        if not inspection.complete:
            # This recipe supports only understood ordinary graphs.
            errors.append("This object's deletion needs a dedicated application action.")
        return errors
```

The recipe does not catch errors raised while deleting. The check and the delete run in the same transaction, moments apart. If another request adds a protecting record in that gap, the delete raises, `cv_atomic` rolls back every deletion of this submission, and the error surfaces like any other server error. No translation of native protection errors into a friendly response is provided or documented.

## 7. Draft package implementation

These sketches are intentionally concrete enough to review the amount of code. They are not production patches. Translation catalogs, theme class slots, check IDs, packaging exports, and full tests remain implementation tasks; section 7.8 lists the deliverables beyond code. The core algorithm and security decisions are specified here rather than hidden behind placeholders.

### 7.1 Source mixin

```python
from typing import ClassVar

import django_tables2 as tables


class BulkMixin:
    cv_bulk_actions: ClassVar[tuple[str, ...]] = ()

    @property
    def cv_bulk_form_id(self):
        # Initial contract: one list/card source per page.
        return "cv-bulk-selection"

    @property
    def cv_bulk_choices(self):
        choices = []
        for key in self.cv_bulk_actions:
            destination = self.cv_viewset.get_view_class(key)
            # Existing origin mechanism: the URL carries this page's key and signed query state.
            choices.append({"key": key, "label": destination.cv_bulk_label, "url": self.cv_get_link_url(destination, key)})
        return choices

    def get_table_kwargs(self):
        # Only table sources call this method; card sources use the checkbox leaf.
        kwargs = super().get_table_kwargs()
        if not self.cv_bulk_actions:
            return kwargs
        columns = list(kwargs.get("extra_columns", ()))
        columns.insert(
            0,
            (
                "cv_bulk_select",
                tables.TemplateColumn(
                    template_name="crud_views/bulk_simple/table_selection.html",
                    verbose_name="Select",
                    orderable=False,
                ),
            ),
        )
        kwargs["extra_columns"] = columns
        return kwargs
```

Keep this mixin before the table/list/card base. Table insertion must respect existing sequence and excluded-column rules; the reserved `cv_bulk_select` name is a small integration constraint, not permission machinery. A normal table `...` sequence includes the added column. Its exact placement is presentation work, and an explicitly restrictive table sequence must include the selection column when bulk is enabled.

This mixin never processes a POST or evaluates a selection queryset. A custom source `get_context_data()` remains normal Django code. An application that overrides the list or card content template needs to include the selection controls when opting in. A custom `cv_card_template` needs nothing: the card checkbox comes from the grid wrapper (section 7.5).

### 7.2 Private review data and ID parsing

```python
from dataclasses import dataclass

from django.core.exceptions import BadRequest, ValidationError


@dataclass(frozen=True)
class _BlockedItem:
    pk: str
    label: str | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class _Review:
    objects: tuple
    blocked: tuple[_BlockedItem, ...]

    @property
    def ids(self):
        return tuple(str(obj.pk) for obj in self.objects)


def _read_ids(post, field):
    # The caller has already bounded the number of submitted values.
    def canonical(values):
        try:
            if any(not isinstance(value, str) or not value for value in values):
                raise ValueError
            return tuple(dict.fromkeys(str(field.to_python(value)) for value in values))
        except (ValidationError, ValueError, TypeError, OverflowError) as error:
            raise BadRequest("Invalid selected object IDs.") from error

    candidates, excluded = canonical(post.getlist("cv_bulk_ids")), canonical(post.getlist("cv_bulk_blocked_ids"))
    if set(candidates) & set(excluded):
        raise BadRequest("An object cannot be both selected and excluded.")
    return candidates, excluded
```

Integer, UUID, and string IDs stay strings in transport. The view bounds the count against `cv_bulk_max` before this function runs, so parsing work is limited; an empty or oversized selection is a user mistake answered with a warning, not an error. Django's standard field/body limits still apply. A malformed request is rejected, not partially accepted. Selection IDs, stage, and confirmation metadata travel in four fields outside the developer's action form: `cv_bulk_ids`, `cv_bulk_blocked_ids`, `cv_bulk_stage`, and `cv_bulk_confirmed`. The `cv_bulk_` prefix is reserved and documented. Because an application form field cannot plausibly use it, no collision check is provided.

### 7.3 Destination scope and item checks

```python
from functools import partial

from django import forms
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, router, transaction
from django.db.models import QuerySet, Subquery
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _

from crud_views.lib.ancestors import _scope_child_queryset
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired
from crud_views.lib.views.mixins import MessageMixin


class BulkFormView(MessageMixin, CustomFormNoObjectViewPermissionRequired):
    cv_object = False
    cv_permission = None  # Require an explicit action permission, not the parent's "view" default.
    cv_modal_supported = False  # The review is always a full page.
    cv_bulk_label = ""
    cv_bulk_max = 100
    cv_bulk_confirm = True
    cv_message_template = "crud_views/snippets/message/bulk.html"  # "3 records processed."
    form_class = forms.Form
    cv_content_template = "crud_views/bulk_simple/form.html"
    cv_header_template_code = "{{ view.cv_bulk_label }}"
    cv_paragraph_template_code = (
        "{% load i18n %}{% translate 'Review the eligible objects before continuing.' %}"
    )
    cv_action_label_template_code = "{% load i18n %}{% translate 'Process selected objects' %}"
    cv_action_short_label_template_code = cv_action_label_template_code

    # Uses the existing ancestor-policy mechanism for the real action endpoint.
    # No new ancestor traversal or impersonation of a source view is necessary.
    _cv_ancestor_operation = "write"

    def cv_bulk_has_permission(self, obj):
        return True

    def cv_bulk_check(self, obj):
        return []

    def _selection_queryset(self):
        base = self.cv_viewset.get_queryset(view=self)
        visible = self.get_queryset()
        for queryset in (base, visible):
            if (
                not isinstance(queryset, QuerySet)
                or queryset.model is not self.cv_viewset.model
                or queryset.query.is_sliced
                or queryset.db != DEFAULT_DB_ALIAS
            ):
                raise ImproperlyConfigured(
                    "Bulk selection requires unsliced querysets for the ViewSet model "
                    "on the default database."
                )
        # Preserve structural parent scope even with a custom ViewSet override.
        base = _scope_child_queryset(self, base)
        return visible.filter(pk__in=Subquery(base.order_by().values("pk")))

    def _review_selection(self, candidates, excluded):
        if self.cv_get_db_alias() != DEFAULT_DB_ALIAS:
            raise ImproperlyConfigured("This bulk form supports the default database only.")
        ids = (*candidates, *excluded)
        queryset = self._selection_queryset().filter(pk__in=ids).order_by()
        objects = {str(obj.pk): obj for obj in queryset}
        eligible, blocked = [], []
        excluded_set = set(excluded)
        unavailable_reason = ("This item is unavailable for this action.",)
        for pk in ids:
            obj = objects.get(pk)
            if obj is None:
                blocked.append(_BlockedItem(pk, None, unavailable_reason))
                continue
            if obj._state.db != DEFAULT_DB_ALIAS or router.db_for_write(type(obj), instance=obj) != DEFAULT_DB_ALIAS:
                raise ImproperlyConfigured("Bulk objects must use the default write database.")
            if not self.cv_bulk_has_permission(obj):
                blocked.append(_BlockedItem(pk, None, unavailable_reason))
                continue
            reasons = tuple(self.cv_bulk_check(obj))
            if reasons or pk in excluded_set:
                blocked.append(
                    _BlockedItem(
                        pk,
                        str(obj),
                        reasons or ("Excluded from this confirmation; select it again from the list.",),
                    )
                )
            else:
                eligible.append(obj)
        return _Review(tuple(eligible), tuple(blocked))
```

The two queryset calls are intentional: a custom `get_queryset()` cannot widen the mandatory ViewSet boundary. Both hooks must be read-only. Duplicate join rows collapse to one selected identity. The implementation must not replace this intersection with a model-manager lookup or silently omit unknown submitted IDs.

The default-database restriction applies to the source data resolved by the destination and to the destination’s write transaction. Application developers remain responsible for any additional writes their hooks perform.

### 7.4 Destination form lifecycle

The following methods belong to the same `BulkFormView` class. They override the existing custom-form coordinator only where the initial review POST and fresh selection require it. They do not replay another view.

```python
    def get(self, request, *args, **kwargs):
        # No IDs in a URL, no side effects, no implicit selection basket.
        return HttpResponseRedirect(self.cv_bulk_back_url())

    def cv_bulk_back_url(self):
        # Existing origin mechanism: the source page with its filter, sort and page.
        return self.cv_get_cancel_url() or self.get_success_url()

    def _bulk_back(self, message):
        messages.warning(self.request, message)
        return HttpResponseRedirect(self.cv_bulk_back_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self._bulk_stage == "review":
            # The source POST opens an unbound message/assignment/confirmation form.
            kwargs.pop("data", None)
            kwargs.pop("files", None)
        return kwargs

    def _review_context(self, candidates, excluded):
        review = self._review_selection(candidates, excluded)
        self.cv_bulk_objects = review.objects
        return self.get_context_data(form=self.get_form(), bulk_review=review)

    def post(self, request, *args, **kwargs):
        self.object = None
        if request.POST.getlist("cv_bulk_stage") not in (["review"], ["execute"]):
            raise BadRequest("Invalid bulk stage.")
        stage = request.POST["cv_bulk_stage"]
        if stage == "execute" and request.POST.getlist("cv_bulk_confirmed") != ["1"]:
            raise BadRequest("Explicit confirmation is required.")

        # User mistakes: warn and return to the source before parsing or loading anything.
        count = len(request.POST.getlist("cv_bulk_ids")) + len(request.POST.getlist("cv_bulk_blocked_ids"))
        if count == 0:
            return self._bulk_back(_("Select at least one record."))
        if count > self.cv_bulk_max:
            return self._bulk_back(_("Select at most %(max)d records.") % {"max": self.cv_bulk_max})
        candidates, excluded = _read_ids(request.POST, self.cv_viewset.model._meta.pk)

        # Skip confirmation: a field-less action may run on the first POST.
        skipped = stage == "review" and not self.cv_bulk_confirm and not self.get_form_class().base_fields
        self._bulk_stage = "execute" if skipped else stage
        if self._bulk_stage == "review":
            return self.render_to_response(self._review_context(candidates, excluded))
        return self._bulk_execute(candidates, excluded, skipped=skipped)

    def _bulk_execute(self, candidates, excluded, *, skipped):
        self._cv_check_nested_write()
        with self.cv_get_atomic():
            context = self._review_context(candidates, excluded)
            review = context["bulk_review"]
            unchanged = bool(review.objects) and review.ids == candidates
            if skipped and not unchanged:
                # First look at a mixed or all-blocked selection: show the review, write nothing.
                return self.render_to_response(context)
            self._cv_check_nested_write(context)
            self.cv_post_hook(context)
            valid = self.cv_form_is_valid(context)
            if not unchanged:
                context["form"].add_error(None, "The eligible selection changed. Review it and confirm again.")
                valid = False
            if not valid:
                self.cv_form_invalid_hook(context)
                return self.cv_form_invalid(context)
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)  # MessageMixin adds the success message here.
            transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())
        return self.cv_form_valid_redirect(context)
```

The limit is the destination’s own `cv_bulk_max`. Nothing about the source’s pagination is read at request time, and no limit supplied by the browser is authoritative. `_bulk_execute` mirrors the hook order of `CrudViewProcessFormMixin.post()` and `cv_form_valid_process()`; a test must pin that order so a later change to the base lifecycle is noticed here.

Normal Django CSRF middleware protects both POSTs. Real dispatch evaluates destination permission on each request. The review and execution POSTs each make one pass over the selected items. A skip-confirmation request can write, so its single pass belongs inside the configured transaction even when a mixed selection leads back to review. The library takes no row locks; an action that needs them uses the recipe in section 6.

Selection-wide rules or rules depending on the user's form values belong in ordinary form validation or `cv_form_is_valid(context)`, using `cv_bulk_objects`. They produce form errors rather than a new generic bulk hook. The supplied per-item hook is deliberately independent of form inputs; stronger revalidation of form-dependent business invariants belongs to the application's mutation code.

`cv_post_hook`, form validation, and all selection checks must be read-only. The mutation belongs in `cv_form_valid`. In this sketch the bulk view opens the transaction before preparing the form so the form and mutation hook share the checked objects. An application overriding `post()` takes responsibility for that lifecycle.

### 7.5 Source markup, card/table checkbox, and small enhancement

Source toolbar, included only when `view.cv_bulk_actions` is nonempty:

```django
<form id="{{ view.cv_bulk_form_id }}" method="post" data-cv-simple-bulk>
  {% csrf_token %}
  <input type="hidden" name="cv_bulk_stage" value="review">
  <div data-bulk-buttons>
    {% for choice in view.cv_bulk_choices %}
      <button type="submit" formaction="{{ choice.url }}"
              data-bulk-destination="{{ choice.url }}">{{ choice.label }}</button>
    {% endfor %}
  </div>
  <span data-bulk-enhancement></span>
</form>
```

Card checkbox. The grid wrapper `view_card.content.html` renders it, not the card template, so an application's own `cv_card_template` needs no change and cannot end up without a checkbox. It straddles the card's top-left corner, half outside the card, so it covers a piece of border and no card content:

```django
{% load l10n crud_views %}
<div class="{{ view.cv_card_container_class }}">
  {% if view.cv_bulk_actions %}
    <div class="{% cv_button_class 'bulk' 'card-cell' %}">
      <input type="checkbox" name="cv_bulk_ids" value="{{ object.pk|unlocalize }}"
             form="{{ view.cv_bulk_form_id }}" data-bulk-item
             class="{% cv_button_class 'bulk' 'card-select' %}"
             aria-label="Select {{ object }}">
      {% cv_card object %}
    </div>
  {% else %}
    {% cv_card object %}
  {% endif %}
</div>
```

Both class names are new keys in the existing registry (`crud_views/lib/button_classes.py`), so a downstream theme or `CRUD_VIEWS_BUTTON_CLASSES` can restyle or move the checkbox:

| Key | Bootstrap 5 default | Purpose |
| --- | --- | --- |
| `bulk:card-cell` | `position-relative` | Positioning context around one card |
| `bulk:card-select` | `form-check-input position-absolute top-0 start-0 translate-middle` | The checkbox, centred on the card's top-left corner |

The default uses Bootstrap utilities only; no package stylesheet is added. Document both keys in `docs/reference/buttons.md` and the card reference. A project whose cards already decorate the top-left corner moves the checkbox through `bulk:card-select`. The toolbar sits above the grid beside the existing “Order by” control and holds the “Select this page” box; its class keys go in the same registry under the `bulk` location.

`table_selection.html`, using the existing `TableWithViewContext` convention:

```django
{% load l10n %}
<input type="checkbox" name="cv_bulk_ids" value="{{ record.pk|unlocalize }}"
       form="{{ table.view.cv_bulk_form_id }}" data-bulk-item
       aria-label="Select {{ record }}">
```

The `form` attribute avoids wrapping row action forms in another form. Selection is native form submission. The enhancement below adds an action picker, a current-page checkbox, and a count. It has no storage, network calls, review token, or receipt handling:

```javascript
document.querySelectorAll("[data-cv-simple-bulk]").forEach(form => {
    const buttons = [...form.querySelectorAll("[data-bulk-destination]")];
    if (!buttons.length) return;
    const items = () => [...document.querySelectorAll("[data-bulk-item]")]
        .filter(input => input.form === form);
    const controls = form.querySelector("[data-bulk-enhancement]");
    const label = document.createElement("label");
    const all = document.createElement("input");
    all.type = "checkbox";
    label.append(all, " Select this page ");
    const picker = document.createElement("select");
    picker.setAttribute("aria-label", "Action");
    buttons.forEach(button => picker.add(new Option(button.textContent, button.dataset.bulkDestination)));
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.textContent = "Continue";
    const count = document.createElement("span");
    count.setAttribute("aria-live", "polite");
    controls.append(label, picker, submit, count);
    const refresh = () => {
        const boxes = items(), selected = boxes.filter(box => box.checked).length;
        all.checked = boxes.length > 0 && selected === boxes.length;
        all.indeterminate = selected > 0 && selected < boxes.length;
        all.disabled = boxes.length === 0;
        submit.disabled = selected === 0;
        count.textContent = ` ${selected} selected`;
        form.action = picker.value;
    };
    all.addEventListener("change", () => {
        items().forEach(box => { box.checked = all.checked; });
        refresh();
    });
    items().forEach(box => box.addEventListener("change", refresh));
    picker.addEventListener("change", refresh);
    window.addEventListener("pageshow", refresh);
    form.querySelector("[data-bulk-buttons]").hidden = true;
    refresh();
});
```

Ship this as an external asset using the existing asset mechanism. Production text must use the package's translation mechanism rather than the English literals shown here. The page checkbox has no server meaning: it merely checks current DOM inputs. Paging/filtering navigates away and creates no cross-page draft. Browser back-form restoration is browser behavior, not a package persistence guarantee.

### 7.6 Destination template

Proposed `bulk_simple/form.html` uses the existing custom-form frame. The example uses Django's normal field rendering for clarity. A theme may render fields differently, but must not create a nested form or duplicate the transport controls.

```django
{% extends "crud_views/snippets/form_frame.html" %}
{% load l10n %}

{% block cv_form_body %}
{# The header already shows cv_bulk_label. The full path keeps the origin query string. #}
<form method="post" action="{{ request.get_full_path }}" enctype="multipart/form-data">
  {% csrf_token %}
  <input type="hidden" name="cv_bulk_stage" value="execute">

  <h3>To process: {{ bulk_review.objects|length }}</h3>
  <ul>
    {% for object in bulk_review.objects %}
      <li>
        {{ object }}
        <input type="hidden" name="cv_bulk_ids" value="{{ object.pk|unlocalize }}">
      </li>
    {% empty %}
      <li>No eligible objects.</li>
    {% endfor %}
  </ul>

  <h3>Blocked / excluded: {{ bulk_review.blocked|length }}</h3>
  <ul>
    {% for item in bulk_review.blocked %}
      <li>
        {% if item.label %}{{ item.label }}{% endif %}
        <ul>{% for reason in item.reasons %}<li>{{ reason }}</li>{% endfor %}</ul>
        <input type="hidden" name="cv_bulk_blocked_ids" value="{{ item.pk }}">
      </li>
    {% endfor %}
  </ul>

  {{ form.as_p }}
  {% if bulk_review.objects %}
    <button type="submit" name="cv_bulk_confirmed" value="1">
      Process {{ bulk_review.objects|length }} objects
    </button>
  {% endif %}
  <a href="{{ view.cv_bulk_back_url }}">Cancel</a>
</form>
{% endblock %}
```

Production markup must use translations and existing theme classes. Every label/reason is autoescaped. There are no editable selection checkboxes here.

### 7.7 Simple system checks

Use a small collector integrated with the existing checks system after registration. This sketch returns messages; implementation assigns unused project check IDs and includes the affected view as `obj`.

```python
def bulk_configuration_errors(viewset):
    errors = []
    for view in viewset.get_all_views().values():
        if issubclass(view, BulkMixin):
            keys = view.cv_bulk_actions
            if not isinstance(keys, tuple) or any(not isinstance(key, str) or not key for key in keys):
                errors.append((view, "cv_bulk_actions must be a tuple of registered view keys."))
                continue
            if len(set(keys)) != len(keys):
                errors.append((view, "Bulk destination keys must be unique."))
            for key in keys:
                if not viewset.is_view_registered(key):
                    errors.append((view, f"Unknown bulk destination: {key}."))
                elif not issubclass(viewset.get_view_class(key), BulkFormView):
                    errors.append((view, f"Bulk destination {key} must inherit BulkFormView."))
                elif (getattr(view, "paginate_by", None) or 0) > viewset.get_view_class(key).cv_bulk_max:
                    # Reported as a warning: a full page could not be submitted to this action.
                    errors.append((view, f"Page size exceeds cv_bulk_max of {key}."))
        if issubclass(view, BulkFormView):
            if viewset.is_resource:
                errors.append((view, "BulkFormView supports ORM models only."))
            if not isinstance(view.cv_bulk_max, int) or view.cv_bulk_max < 1:
                errors.append((view, "cv_bulk_max must be a positive integer."))
            if not view.cv_bulk_label:
                errors.append((view, "Set cv_bulk_label."))
            if not view.cv_permission:
                errors.append((view, "Set the destination's cv_permission."))
            if view.cv_form_valid is CustomFormNoObjectViewPermissionRequired.cv_form_valid:
                errors.append((view, "Implement cv_form_valid; the inherited method does nothing."))
    return errors
```

Also validate supported list/card source types, scalar PKs, normal form subclasses, non-object destination configuration, and registered success keys. The existing `cv_modal_supported` check already rejects `cv_modal = True` on a bulk destination. Prefer existing checks where they already cover these declarations. Do not inspect arbitrary method bodies, trusted owners, wrappers, or effective MROs to guess compatibility. Unknown application behavior remains application code.

**Guardian warning.** In a `GuardianViewSet` the ordinary views require an object grant per record, while `cv_bulk_has_permission()` defaults to `True`. A bulk action could therefore be more permissive than the single-record view beside it. The Guardian package warns at startup when a bulk destination in a `GuardianViewSet` keeps the default. It is a warning, not an error: a developer who enforces the policy by narrowing `get_queryset()` silences it by ID. The check lives in `crud_views_guardian/checks.py`, so core never imports Guardian, and it compares one method with the base class without inspecting method bodies.

```python
def guardian_bulk_warnings(viewset):
    # Called for each GuardianViewSet from the existing crud_views_guardian check function.
    warnings = []
    for view in viewset.get_all_views().values():
        if issubclass(view, BulkFormView) and view.cv_bulk_has_permission is BulkFormView.cv_bulk_has_permission:
            warnings.append(
                (view, "Bulk action in a GuardianViewSet does not override cv_bulk_has_permission: "
                       "every record its queryset shows is treated as permitted.")
            )
    return warnings
```

The collector must not instantiate application forms or execute queryset/permission hooks during startup. These checks describe configuration, not a proof that application hooks are correct.

### 7.8 Deliverables beyond code

| Deliverable | Where |
| --- | --- |
| Bulk-action reference guide (D-10) | New `docs/reference/bulk_actions.md`, linked with the example app in both directions |
| Cross-links from existing pages | `list_view.md`, `card-list-view.md`, `custom_form_view.md`, `guardian.md` (the warning), `buttons.md` (`bulk:card-cell`, `bulk:card-select`, toolbar keys), `javascript.md` (the toolbar script), `messages.md` (the default message) |
| Changelog entry | `CHANGELOG.md` under “Unreleased”, as a feature. Nothing breaks, so `docs/migrating-1.0.md` needs no entry |
| German translations | `src/crud_views/locale/de/` for core strings; `src/crud_views_guardian/locale/de/` for the warning |
| JavaScript test for the toolbar script | `tests/js/`, beside the existing script tests |
| Check IDs | Unused IDs for the core checks and the Guardian warning, documented where existing IDs are listed |
| Public API listing | `docs/development/stability.md` |

The bulk API is listed as **stable** in `docs/development/stability.md`, with no provisional category: `BulkMixin`, `BulkFormView`, the `cv_bulk_*` attributes and hooks of section 4, the four `cv_bulk_*` POST field names, and the `bulk:*` class keys. After 1.0, changing any of them follows the normal deprecation policy.

## 8. Where inspect_deletion helps, and where it does not

The existing `inspect_deletion(obj, using=...)` returns known deletion rows and native protection blockers without invoking deletion. It handles understood ordinary cascade relationships and reports boundaries for custom behavior.

Useful in a bulk delete destination:

- Show a known protected object as blocked before execution.
- Use a generic relationship-blocker reason without exposing related-object labels.
- Let the application explicitly refuse models whose effects it does not support.

Not provided by the inspector:

- Endpoint or item permission.
- The application's `cv_check_delete_protection()` rules.
- Execution, locking, rollback, or guaranteed future eligibility.
- Proof of signal behavior or external effects, even when `complete=True`.
- A universally correct combined-batch deletion graph from independent per-root calls.

`complete` means the inspector reported no unresolved boundaries in its understood model of relationships; it is not “safe to delete under all conditions.” Native protection and other errors can still occur during actual execution.

This design does not aggregate previews, simulate deletion order, inspect arbitrary single-delete forms, or automatically reuse single-delete lifecycle hooks. Shared business functions are the intended reuse mechanism. The inspector still walks related graphs even if the action consumes only `related.protected`, so query/memory costs remain. No new “cheap blocker inspector” is proposed without evidence that it is needed.

## 9. Maintainability boundaries and remaining costs

| Decision | Benefit | Cost or limitation |
| --- | --- | --- |
| Current-page UI | No storage/signing/draft state | Users repeat selection on another page |
| Explicit IDs | Clear user intent and bounded request | No “all matching” or automatic inclusion of new records |
| ViewSet intersection | Mandatory parent/base scope despite destination overrides | Shared tenant/visibility rules still need correct application placement |
| Actual registered form destination | Existing dispatch, permissions, forms, and URLs | Application must define its action and any item policy |
| Informational blocked rows | Deliberate eligible-subset execution | Changed eligibility requires another review |
| Reuse ordinary form lifecycle | Familiar hooks and transaction choice | Does not guarantee external-effect rollback or exactly-once execution |
| No generic delete adaptation | Removes the strict compatibility matrix | Application duplicates thin hook wrappers around shared business functions |
| No row locking in the library | No database-specific lock behavior behind a flag | An action that needs locks re-reads and re-checks its records |
| Default database initially | Avoids alias negotiation and cross-database claims | Multiple-database consumers need a separate future design |
| Explicit `cv_bulk_max` on the destination | One documented number; no source lookup at request time | The developer raises it for larger pages; bounds the number of selected roots only |
| No modal review | No change to the shared modal script | Bulk actions always use a full page |
| Existing origin mechanism for return | Cancel restores the source page; no bulk-specific protocol | Checkbox state is not restored |

The proposed backend should remain a few ordinary classes and private helpers that can be read in one sitting. The sketches are a review aid, not a line-count target. If implementation starts needing general lifecycle classification, view cloning, source HTTP replay, signed recovery, or per-method exemption declarations, stop and reconsider the scope.

## 10. Compatibility with main

Use the existing list, card, custom-form, and single-record delete behavior on `main` as the compatibility baseline. Phase 06.38 remained on its development branch, so introducing this feature requires no migration from its API. The [November 16 design](2026-11-16-bulk-actions-design.md) records the earlier approach for reference.

## 11. Acceptance and verification plan

Test behavior rather than implementation structure:

- Opt-in table/card controls; sources without the mixin stay unchanged.
- Render both source types with configured actions for a user who cannot enter one of them. Verify the action is displayed, the toolbar calls no destination or item permission hooks, and it adds zero bulk-permission queries. On submission, verify denied admission stops before item checks and admitted requests check only submitted records.
- Native no-JS submission and enhanced current-page selection; no cross-page storage or all-results request.
- Destination permission enforced on review and execute, including direct/forged POSTs.
- Parent and tenant scope enforced even when a destination queryset is accidentally broader than its ViewSet queryset.
- Source-only display filtering is not treated as an authorization gate; shared-scope examples demonstrate the correct boundary.
- With `cv_bulk_max = 100`, accept 100 submitted IDs and reject 101 on review and on execution, counting excluded IDs. The rejection is a warning message and a redirect to the source page, before item checks or writes. An empty selection gets the same treatment. A raised `cv_bulk_max` accepts a larger page.
- A system check warns when a source’s configured page size exceeds the `cv_bulk_max` of an action it offers, and rejects `cv_modal = True` on a bulk destination.
- Exercise selections with integer, UUID, and string primary keys on the default database. Reject composite keys, non-ORM Resources, and selection or write routes to another database before mutation.
- IDs normalize and deduplicate; malformed IDs, overlapping candidate/excluded sets, and unsupported querysets fail clearly.
- Missing, out-of-scope, and permission-denied records display identical text and omit the object label. A permitted record blocked by a business rule displays its label and the specific reason.
- Review is read-only and leaves the action form unbound.
- Count eligibility checks per request across review, confirmation, skip confirmation, and redisplay. Each request checks each permitted selected item once. With `cv_atomic=True`, verify that the execution check runs inside the configured transaction before any writes.
- Two groups survive invalid form submissions; reasons come from fresh server checks.
- The confirmation displays the eligible subset and keeps previously excluded objects out of the confirmation submission.
- Expose the same action from a table and a card. Both honor the destination's `cv_bulk_confirm`. With confirmation skipped, an all-eligible selection on a field-less action runs immediately and a mixed selection opens the full-page review from either source.
- Act from a filtered, sorted card page 2 and cancel: the user returns to that same page. The warning redirect returns there too. With `cv_success_keys` listing both sources, success returns to the source used; without it, to `cv_success_key`.
- Every execution, including skipped confirmation, shows a success message with the number of processed records. A custom `cv_message_template_code` replaces the default. A rerender or a rolled-back execution shows no success message.
- Direct execution with confirmation skipped enforces the same scope, permission, and eligibility checks.
- With skip confirmation enabled on an action requiring input, the source opens the form before any writes. One valid submission with unchanged eligibility executes the action without a second confirmation screen.
- With skip confirmation enabled, selecting eight eligible records and two blocked records opens the review before any writes. Confirming the eight processes only those eight.
- Eligibility loss before final execution rerenders, with no mutation, and requires another confirmation.
- A database action rolls back earlier writes after a later exception when `cv_atomic=True`.
- On-commit failure is not described as rollback; external delivery is not reported as completed merely because jobs were created.
- The leaf delete example deletes the eligible documents and blocks a locked one with the rule shared with single-record deletion. With the inspection step, a record with protected relations is listed as blocked without displaying the related objects. A protection error raised during execution rolls back the whole submission and is not caught.
- The example app opens with a runnable leaf-model bulk delete. The bulk-action reference guide links to it, shows the protection rule shared by both delete views, and walks through the parent and locked-descendant case.
- With the same seed data, demonstrate immediate archive, a full-page review for a mixed archive selection, and owner assignment through a full-page form.
- A card source with a fully custom `cv_card_template` renders one checkbox per card from the grid wrapper, at the card's top-left corner. Overriding `bulk:card-select` and `bulk:card-cell` through `CRUD_VIEWS_BUTTON_CLASSES` changes the rendered classes. A card source without bulk actions renders the unchanged markup.
- Source templates avoid nested forms; destination markup is valid, escaped, keyboard accessible, and translated.
- A bulk destination in a `GuardianViewSet` that keeps the default `cv_bulk_has_permission` produces the Guardian warning; overriding the hook or silencing the check ID removes it. Core checks run without Guardian installed.
- `docs/development/stability.md` lists the bulk classes, attributes, POST field names, and class keys as stable public API. Every deliverable in section 7.8 exists.
- The reference guide contains the row-locking recipe and states that the library takes no locks.
- Ordinary custom-form and single-delete regression tests continue to pass.

Use bounded multicore pytest for broad Python runs. Run focused JavaScript tests for the small enhancement and browser checks for the actual table/card/form flow. The snippets in this document require syntax and integration review; they are not evidence that the feature has already been built or tested.

### Validation of this document

The design received an independent builder review. Required frontend snippet defaults and the final eligibility-change invalid-form hook were corrected in response. All 12 Python blocks parse; the core class sketches import and compose against the current repository bases. A small ID-normalization example and the four required snippet configuration checks pass. The Django template examples parse, the JavaScript passes `node --check`, and relative Markdown links resolve. The November 19 revision changed the sketches in sections 6 and 7; they were re-checked for Python syntax only. These are draft checks only: the proposed feature has not been implemented or verified through HTTP, a database test suite, or a browser.

## 12. References to current implementation

- `src/crud_views/lib/viewset/__init__.py`: `ViewSet.get_queryset(view)` and registered endpoints.
- `src/crud_views/lib/view/base.py`: `get_queryset`, real permission/ancestor dispatch, URL helpers, transaction hooks.
- `src/crud_views/lib/views/form.py`: `CustomFormNoObjectViewPermissionRequired`.
- `src/crud_views/lib/views/mixins.py`: `CrudViewProcessFormMixin` lifecycle.
- `src/crud_views/lib/deletion.py`: view-independent `inspect_deletion` and existing execution machinery.
- `src/crud_views/lib/views/delete.py`: business protection hook and single-delete orchestration.
- The phase 06.38 implementation can be inspected locally with `git show gsd/phase-06.38-bulk-actions-378:src/crud_views/lib/bulk/__init__.py`.

The design reuses existing behavior where it is small and explicit. It does not assume that reusing a method name reproduces another view's entire policy.
