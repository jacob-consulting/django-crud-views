# Simple bulk selection and action form views

Date: 2026-11-18

Status: design proposal for review, including implementation sketches. This document does not authorize or implement replacement of the shipped bulk feature. The Python and template examples below describe proposed APIs, not APIs available today.

## 1. Purpose and decisions

Make small, explicit selections useful without requiring the maintainer to own a second view execution framework. The reusable feature collects IDs, resolves them within the ViewSet's scope, and presents an action form. Ordinary registered views own authorization, business policy, and execution.

This design follows the [developer-maintainability decision](../notes/2026-11-04-opt-in-url-helper-decision.md). It proposes a smaller replacement for the approach in [the original bulk design](2026-11-16-bulk-actions-design.md), rather than incremental exemptions to its compatibility checker.

### Decisions established in the discussion

- A list/card mixin provides selection and points to a registered bulk action view.
- Explicit selected IDs are sufficient. Across-page drafts and selecting all matching results are unnecessary for the basic feature.
- A bulk action can have a custom form or a simple confirmation form.
- The target view owns the permission to perform the action at all.
- Developers supply additional per-object permission and business checks where their application needs them.
- The confirmation separates objects to process from blocked objects with reasons. The user can deliberately process the eligible subset.
- Blocked rows are informational. There are no selection controls on the confirmation page.
- Every resolution of submitted IDs must be constrained by the ViewSet's queryset. Additional restrictions can narrow this scope, never broaden it.
- Reuse useful deletion primitives without automatically adapting the registered single-delete view.

### Concrete proposals made by this document

These settle details for review; they are not additional claims of prior user approval:

- Two public classes: `BulkMixin` for sources and `BulkFormView` for destinations.
- Every shipped bulk destination uses the review/form step. Direct execution can remain an application-owned custom view; it needs no new generic switch initially.
- The first implementation supports ordinary ORM models with scalar PKs and the default database. UUID, integer, and string PKs stay strings in transport. Composite PKs, Resources, and multiple databases are outside this first contract.
- A destination has a positive `cv_bulk_max_items`, default 100. There is no unlimited mode or additional global setting initially.
- If a previously eligible submitted object is now blocked, redisplay the revised confirmation and execute nothing on that request.
- Previously blocked IDs are carried forward only for informational redisplay. They are never automatically promoted.
- Back/success destinations are ordinary configured ViewSet keys. No new arbitrary return-URL or exact source-filter restoration protocol.
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
| Keep current coordinator and relax compatibility rules | Retains existing features and tests | Still owns lifecycle reconstruction, MRO inspection, drafts, signing, receipts, and delete adaptation | Not recommended for this maintainability objective |
| Execute all actions inside the list/card mixin | Few classes for trivial actions | List view accumulates action permissions, forms, execution, and confirmation branches | Rejected in favor of separate action views |
| Selection mixin plus ordinary registered form destinations | Small responsibilities; real destination dispatch; custom forms are natural | Application explicitly implements item policy and execution | Chosen direction |

The smaller feature intentionally loses automatic reuse of arbitrary single-record actions, cross-page selection, exact draft restoration, automatic deletion previews, and universal all-or-nothing execution. Its value is a reusable selection/form experience, not transparent compatibility with every existing view customization.

## 4. Public shape

Proposed exports from `crud_views.lib.bulk`:

| Class/member | Contract |
| --- | --- |
| `BulkMixin` | Opt-in selection controls for a list/card source |
| `BulkMixin.cv_bulk_actions` | Tuple of registered destination keys in the same ViewSet |
| `BulkFormView` | Permission-required, non-object custom form destination with review and selection handling |
| `cv_bulk_label` | Destination label used in source controls and the confirmation |
| `cv_bulk_max_items` | Positive maximum for the complete submitted selection, including excluded IDs; default 100 |
| `get_queryset()` | Existing view extension point; may narrow visibility. Resolution also intersects it with the ViewSet base scope |
| `cv_bulk_has_permission(obj) -> bool` | Optional read-only item permission check; default `True` means no extra per-item policy beyond endpoint admission and queryset visibility |
| `cv_bulk_check(obj) -> list[str]` | Optional read-only business eligibility check; default `[]` |
| `cv_bulk_objects` | Tuple of freshly resolved eligible model instances available to form hooks |
| `form_class` | Ordinary Django form; defaults to empty `forms.Form` |
| `cv_form_valid(context)` | Existing custom-form execution hook; application owns the operation |
| `cv_atomic`, `cv_on_commit`, `cv_success_key` | Existing form-view lifecycle and navigation settings, not a new bulk contract |

There is no action descriptor, action-class registry, method-name dispatch, source replay, or compatibility whitelist. Existing `BulkAction`, `BulkActionContext`, and built-in `BulkDelete` are not part of this proposed replacement API.

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

### Two-stage POST

1. The source submits checked `ids` directly to a configured destination with `bulk_stage=review` and CSRF protection.
2. Destination dispatch applies its normal permission and ancestor gates.
3. The destination parses, normalizes, and deduplicates IDs, then resolves the complete request through the scoped queryset.
4. Item permission runs before labels or business reasons are rendered. Objects outside the scope are represented only as unavailable.
5. Business checks partition visible, permitted objects into eligible and blocked groups.
6. The response shows an unbound action form, eligible objects, and informational blocked rows.
7. The confirmation carries eligible IDs as `ids` and excluded IDs as `blocked_ids`. It posts `bulk_stage=execute` and `confirmed=1` through the actual submit button.
8. The destination binds the normal form, resolves/checks again, and validates form fields. It repeats item resolution/checks immediately before execution inside its normal configured transaction context.
9. If the candidate membership has changed, nothing executes. The same bound form is rendered with the new partition and a message requesting confirmation again.
10. Otherwise the ordinary custom-form mutation hooks run with `cv_bulk_objects` set to the fresh eligible tuple.

An execute POST still goes through all checks even if a caller bypasses the initial review POST. Hidden fields and `confirmed=1` are not proof of prior review. Requiring cryptographic proof would reintroduce a different contract and is intentionally excluded.

### Eligible and blocked groups

- Only eligible IDs are candidates for execution.
- Blocked rows cannot be checked, unchecked, or promoted on the confirmation.
- A previously excluded object that becomes eligible remains excluded, with an explanation such as “Excluded from this confirmation; select it again from the list.”
- Reasons are rebuilt on the server. Never post and trust a reason or an eligibility flag.
- Missing, moved, hidden, or unauthorized objects get a generic unavailable/not-allowed label. Do not query outside the allowed scope to obtain their names.
- A visible object that passes item authorization may display its label and business-rule explanation.
- Zero eligible objects means no execution control. Back leads to the configured list/card destination.
- Form validation errors preserve the two groups, using hidden IDs only as untrusted input for another resolution.

### Partial selection versus execution failure

The user can intentionally process 8 eligible records while leaving 2 blocked records untouched. That is not a promise to continue after a runtime error on the fifth eligible record.

The destination chooses its normal execution semantics. A database-only action with `cv_atomic=True` can roll back all eight on an exception. A message action can enqueue application delivery jobs or explicitly own delivery outcomes. The generic selection feature does not catch arbitrary exceptions and claim partial success.

No exactly-once execution, locking, durable message delivery, or automatic retry is promised. A lost response or an exception after commit can leave the client uncertain. Application actions that require stronger guarantees implement them explicitly.

## 6. Application examples

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

List and card can expose different destinations. Destination permission is authoritative regardless of which source supplied the IDs. Initially, source controls may show a destination the user cannot enter; the destination returns its ordinary permission response. Permission-aware hiding is optional presentation work, not another authorization engine.

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
    cv_success_key = "list"
    cv_atomic = True

    def cv_bulk_has_permission(self, obj):
        return can_edit_document(self.request.user, obj)

    def cv_bulk_check(self, obj):
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

### Explicit object permissions

A Guardian-using application can share its readable-object queryset between source and destination and implement the item hook directly:

```python
def cv_bulk_has_permission(self, obj):
    # Use the application's actual configured permission backend/policy.
    return self.request.user.has_perm("documents.change_document", obj)
```

This example does not infer global-permission fallback. If the application allows a model permission as a fallback, that must be explicit in its policy function. The default endpoint model-permission gate still applies: object grants alone do not enter this `BulkFormView`. An object-grants-only application needs an explicit endpoint admission policy via ordinary `has_permission()`, plus its visibility and item checks. No automatic Guardian view adapter is proposed.

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

The same function can be used by the bulk destination. The existing single-delete hook is not a combined permission/database-protection API: its default implementation simply returns `[]`.

### Bounded application bulk deletion

The following is deliberately an application recipe, not a proposed universal `BulkDeleteView`. It assumes ordinary Document roots that cannot cascade-delete one another, standard model deletion, and database-contained effects. Other models need an explicit application decision.

```python
from django.db.models.deletion import ProtectedError, RestrictedError
from django.http import HttpResponse

from crud_views.lib.deletion import inspect_deletion

from .policies import can_delete_document


class _DocumentDeletionBlocked(Exception):
    pass


class DeleteDocumentsView(BulkFormView):
    cv_viewset = document_viewset
    cv_key = "bulk_delete"
    cv_path = "bulk-delete"
    cv_permission = "delete"
    cv_bulk_label = "Delete selected documents"
    cv_success_key = "list"
    cv_atomic = True

    def cv_bulk_has_permission(self, obj):
        return can_delete_document(self.request.user, obj)

    def cv_bulk_check(self, obj):
        errors = document_delete_errors(obj)
        inspection = inspect_deletion(obj, using=self.cv_get_db_alias())
        if inspection.related.protected:
            errors.append("Deletion is blocked by related records.")
        if not inspection.complete:
            # This recipe intentionally supports only understood ordinary graphs.
            errors.append("This object's deletion needs a dedicated application action.")
        return errors

    def cv_form_valid(self, context):
        for document in self.cv_bulk_objects:
            try:
                document.delete(using=self.cv_get_db_alias())
            except (ProtectedError, RestrictedError) as error:
                # This application's known native deletion path only.
                raise _DocumentDeletionBlocked from error

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except _DocumentDeletionBlocked:
            # The form lifecycle has left its atomic block: prior writes rolled back.
            # Discard in-memory objects whose PKs may have been cleared by delete().
            self.cv_bulk_objects = ()
            # Do not render protected exception objects or their labels.
            return HttpResponse(
                "Deletion was blocked. Nothing was deleted by this attempt. "
                "Return to the list and review the selection again.",
                status=409,
            )
```

The error response belongs at the actual `post()` boundary. Returning a response from `cv_form_valid_process()` would be ignored by the existing lifecycle. The local exception marks only the application's delete call, so errors from inspection, other hooks, and commit callbacks are not relabeled as native write blockers. This recipe assumes no custom model/signal behavior raising these native exception types for unrelated reasons; it does not recreate the package's general execution-provenance machinery. Do not broaden this catch to arbitrary exceptions. A production template can provide a normal Back link instead of the minimal text response shown here.

## 7. Draft package implementation

These sketches are intentionally concrete enough to review the amount of code. They are not production patches. Translation catalogs, theme class slots, check IDs, packaging exports, and full tests remain implementation tasks. The core algorithm and security decisions are specified here rather than hidden behind placeholders.

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
        return [
            {
                "key": key,
                "label": self.cv_viewset.get_view_class(key).cv_bulk_label,
                "url": self.cv_get_url(key),
            }
            for key in self.cv_bulk_actions
        ]

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

This mixin never processes a POST or evaluates a selection queryset. A custom source `get_context_data()` remains normal Django code. Existing template overrides need to include the selection controls when opting in.

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


class _SelectionChanged(Exception):
    def __init__(self, review):
        self.review = review


def _read_ids(post, field, maximum):
    candidates = post.getlist("ids")
    excluded = post.getlist("blocked_ids")
    if not candidates and not excluded:
        raise BadRequest("Select at least one object.")
    if len(candidates) + len(excluded) > maximum:
        raise BadRequest("Too many selected objects; select fewer records.")

    def canonical(values):
        try:
            if any(not isinstance(value, str) or not value for value in values):
                raise ValueError
            return tuple(dict.fromkeys(str(field.to_python(value)) for value in values))
        except (ValidationError, ValueError, TypeError, OverflowError) as error:
            raise BadRequest("Invalid selected object IDs.") from error

    candidates, excluded = canonical(candidates), canonical(excluded)
    if set(candidates) & set(excluded):
        raise BadRequest("An object cannot be both selected and excluded.")
    return candidates, excluded
```

Counts are bounded before deduplication as a simple request-work limit. Django's standard field/body limits still apply. A malformed request is rejected, not partially accepted. Selection IDs, stage, and confirmation metadata are outside the developer's action form; reserved names must not collide with its fields.

### 7.3 Destination scope and item checks

```python
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models import QuerySet, Subquery

from crud_views.lib.ancestors import _scope_child_queryset
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired


class BulkFormView(CustomFormNoObjectViewPermissionRequired):
    cv_object = False
    cv_permission = None  # Require an explicit action permission, not the parent's "view" default.
    cv_bulk_label = ""
    cv_bulk_max_items = 100
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
        for pk in ids:
            obj = objects.get(pk)
            if obj is None:
                blocked.append(_BlockedItem(pk, None, ("Unavailable.",)))
                continue
            if obj._state.db != DEFAULT_DB_ALIAS or router.db_for_write(type(obj), instance=obj) != DEFAULT_DB_ALIAS:
                raise ImproperlyConfigured("Bulk objects must use the default write database.")
            if not self.cv_bulk_has_permission(obj):
                blocked.append(_BlockedItem(pk, None, ("Not allowed.",)))
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

This default-only limit is a proposed simplification, not an assertion that multiple databases are impossible. Arbitrary writes in application hooks are still application-owned; inspecting selected roots cannot prove where all related writes will occur.

### 7.4 Destination form lifecycle

The following methods belong to the same `BulkFormView` class. They override the existing custom-form coordinator only where the initial review POST and fresh selection require it. They do not replay another view.

```python
    def get(self, request, *args, **kwargs):
        # No IDs in a URL, no side effects, no implicit selection basket.
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self._bulk_stage == "review":
            # The source POST opens an unbound message/assignment/confirmation form.
            kwargs.pop("data", None)
            kwargs.pop("files", None)
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        reserved = {"ids", "blocked_ids", "bulk_stage", "confirmed"}
        if reserved.intersection(form.fields):
            raise ImproperlyConfigured("Action form fields conflict with bulk selection fields.")
        return form

    def _review_context(self, review, form):
        self.cv_bulk_objects = review.objects
        return self.get_context_data(form=form, bulk_review=review)

    def post(self, request, *args, **kwargs):
        self.object = None
        if request.POST.getlist("bulk_stage") not in (["review"], ["execute"]):
            raise BadRequest("Invalid bulk stage.")
        self._bulk_stage = request.POST["bulk_stage"]
        if self._bulk_stage == "execute" and request.POST.getlist("confirmed") != ["1"]:
            raise BadRequest("Explicit confirmation is required.")
        self._bulk_candidates, self._bulk_excluded = _read_ids(
            request.POST, self.cv_viewset.model._meta.pk, self.cv_bulk_max_items
        )
        review = self._review_selection(self._bulk_candidates, self._bulk_excluded)
        self.cv_bulk_objects = review.objects
        form = self.get_form()
        context = self._review_context(review, form)
        if self._bulk_stage == "review":
            return self.render_to_response(context)

        self._cv_check_nested_write(context)
        self.cv_post_hook(context)
        valid = self.cv_form_is_valid(context)
        if not review.objects or review.ids != self._bulk_candidates:
            form.add_error(None, "The eligible selection changed. Review it and confirm again.")
            valid = False
        if not valid:
            self.cv_form_invalid_hook(context)
            return self.cv_form_invalid(context)

        try:
            self.cv_form_valid_process(context)
        except _SelectionChanged as changed:
            form.add_error(None, "The eligible selection changed. Review it and confirm again.")
            context = self._review_context(changed.review, form)
            self.cv_form_invalid_hook(context)
            return self.cv_form_invalid(context)
        return self.cv_form_valid_redirect(context)

    def cv_form_valid_process(self, context):
        from functools import partial

        from django.db import transaction

        self._cv_check_nested_write(context)
        with self.cv_get_atomic():
            fresh = self._review_selection(self._bulk_candidates, self._bulk_excluded)
            if not fresh.objects or fresh.ids != self._bulk_candidates:
                raise _SelectionChanged(fresh)
            self.cv_bulk_objects = fresh.objects
            context["bulk_review"] = fresh
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())
```

Normal Django CSRF middleware protects both POSTs. Do not exempt either stage. Per-view permission is evaluated by real dispatch on every request; per-item checks repeat immediately before execution. This is not a concurrency lock or a transaction-wide reauthorization of every possible custom backend cache. Actions needing stronger semantics must implement them.

Selection-wide rules or rules depending on the user's form values belong in ordinary form validation or `cv_form_is_valid(context)`, using `cv_bulk_objects`. They produce form errors rather than a new generic bulk hook. The supplied per-item hook is deliberately independent of form inputs; stronger revalidation of form-dependent business invariants belongs to the application's mutation code.

`cv_post_hook`, form validation, and all selection checks must be read-only. The mutation belongs in `cv_form_valid`. As with other forms, overriding `post()` or `cv_form_valid_process()` transfers responsibility for preserving the lifecycle to the application. No override blacklist is introduced.

The final method mirrors the existing small form lifecycle because selection must be refreshed inside its transaction. If implementation can reuse an existing prewrite extension point without changing unrelated views, do so; do not redesign every form view merely to remove a few repeated lines here.

### 7.5 Source markup, card/table checkbox, and small enhancement

Source toolbar, included only when `view.cv_bulk_actions` is nonempty:

```django
<form id="{{ view.cv_bulk_form_id }}" method="post" data-cv-simple-bulk>
  {% csrf_token %}
  <input type="hidden" name="bulk_stage" value="review">
  <div data-bulk-buttons>
    {% for choice in view.cv_bulk_choices %}
      <button type="submit" formaction="{{ choice.url }}"
              data-bulk-destination="{{ choice.url }}">{{ choice.label }}</button>
    {% endfor %}
  </div>
  <span data-bulk-enhancement></span>
</form>
```

Card checkbox, outside existing card links and any row-action forms:

```django
{% load l10n %}
<label>
  <input type="checkbox" name="ids" value="{{ object.pk|unlocalize }}"
         form="{{ view.cv_bulk_form_id }}" data-bulk-item>
  Select {{ object }}
</label>
```

`table_selection.html`, using the existing `TableWithViewContext` convention:

```django
{% load l10n %}
<input type="checkbox" name="ids" value="{{ record.pk|unlocalize }}"
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
<h2>{{ view.cv_bulk_label }}</h2>
<form method="post" action="{{ request.path }}" enctype="multipart/form-data">
  {% csrf_token %}
  <input type="hidden" name="bulk_stage" value="execute">

  <h3>To process: {{ bulk_review.objects|length }}</h3>
  <ul>
    {% for object in bulk_review.objects %}
      <li>
        {{ object }}
        <input type="hidden" name="ids" value="{{ object.pk|unlocalize }}">
      </li>
    {% empty %}
      <li>No eligible objects.</li>
    {% endfor %}
  </ul>

  <h3>Blocked / excluded: {{ bulk_review.blocked|length }}</h3>
  <ul>
    {% for item in bulk_review.blocked %}
      <li>
        {{ item.label|default:"Unavailable object" }}
        <ul>{% for reason in item.reasons %}<li>{{ reason }}</li>{% endfor %}</ul>
        <input type="hidden" name="blocked_ids" value="{{ item.pk }}">
      </li>
    {% endfor %}
  </ul>

  {{ form.as_p }}
  {% if bulk_review.objects %}
    <button type="submit" name="confirmed" value="1">
      Process {{ bulk_review.objects|length }} objects
    </button>
  {% endif %}
  <a href="{{ view.get_success_url }}">Back to list</a>
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
        if issubclass(view, BulkFormView):
            if viewset.is_resource:
                errors.append((view, "BulkFormView supports ORM models only."))
            if not view.cv_bulk_label:
                errors.append((view, "Set cv_bulk_label."))
            if type(view.cv_bulk_max_items) is not int or view.cv_bulk_max_items <= 0:
                errors.append((view, "cv_bulk_max_items must be a positive integer."))
            if not view.cv_permission:
                errors.append((view, "Set the destination's cv_permission."))
            if view.cv_form_valid is CustomFormNoObjectViewPermissionRequired.cv_form_valid:
                errors.append((view, "Implement cv_form_valid; the inherited method does nothing."))
    return errors
```

Also validate supported list/card source types, scalar PKs, normal form subclasses, non-object destination configuration, registered success keys, and reserved action-form field names (`ids`, `blocked_ids`, `bulk_stage`, `confirmed`). Prefer existing checks where they already cover these declarations. Do not inspect arbitrary method bodies, trusted owners, wrappers, or effective MROs to guess compatibility. Unknown application behavior remains application code.

The collector must not instantiate application forms or execute queryset/permission hooks during startup. A dynamic form that introduces reserved fields must be rejected at form preparation. These checks describe configuration, not a proof that application hooks are correct.

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
| Default database initially | Avoids alias negotiation and cross-database claims | Multiple-database consumers need a separate future design |
| Fixed positive cap | Bounds selection bookkeeping | Does not bound cascade size or action runtime |

The proposed backend should remain a few ordinary classes and private helpers that can be read in one sitting. The sketches are a review aid, not a line-count target. If implementation starts needing general lifecycle classification, view cloning, source HTTP replay, signed recovery, or per-method exemption declarations, stop and reconsider the scope.

## 10. Compatibility and transition

Do not silently reinterpret today's `cv_bulk_actions = [BulkActionClass, ...]` as destination keys. Existing public classes, settings, JavaScript behavior, and template contracts have consumers and tests.

After this design is approved, choose and document a migration before implementation:

1. Inventory current users and examples of the shipped API.
2. Replace class declarations with registered `BulkFormView` endpoints and key tuples.
3. Move business rules into application functions shared with single-record views.
4. Explain the loss of cross-page selection, signed reviews, automatic delete adaptation, and old public settings.
5. Remove obsolete coordinator/routes/compatibility/draft assets and checks rather than permanently maintaining both engines.
6. Preserve single-record delete code and tests except for deliberate application example extraction.
7. Update `CHANGELOG.md` with a Breaking entry and `docs/migrating-1.0.md`, as required before 1.0.

This document itself changes no API, roadmap, milestone, or historical design. It records the proposed replacement and its costs. The actual migration/release decision remains separate from writing this design.

## 11. Acceptance and verification plan

Test behavior rather than implementation structure:

- Opt-in table/card controls; sources without the mixin stay unchanged.
- Native no-JS submission and enhanced current-page selection; no cross-page storage or all-results request.
- Destination permission enforced on review and execute, including direct/forged POSTs.
- Parent and tenant scope enforced even when a destination queryset is accidentally broader than its ViewSet queryset.
- Source-only display filtering is not treated as an authorization gate; shared-scope examples demonstrate the correct boundary.
- IDs normalize and deduplicate; malformed, overlapping candidate/excluded sets, oversized requests, and unsupported querysets fail clearly.
- One unavailable/denied object does not leak labels; visible business-blocked objects display reasons.
- Review is read-only and leaves the action form unbound.
- Two groups survive invalid form submissions; reasons come from fresh server checks.
- Confirmed eligible subset executes; excluded objects never execute or get promoted.
- Eligibility loss before final execution rerenders, with no mutation, and requires another confirmation.
- A database action rolls back earlier writes after a later exception when `cv_atomic=True`.
- On-commit failure is not described as rollback; external delivery is not reported as completed merely because jobs were created.
- The bounded delete recipe handles known native protection without displaying hidden related objects and without catching unrelated exceptions as blockers.
- Source templates avoid nested forms; destination markup is valid, escaped, keyboard accessible, and translated.
- Ordinary custom-form and single-delete regression tests continue to pass.

Use bounded multicore pytest for broad Python runs. Run focused JavaScript tests for the small enhancement and browser checks for the actual table/card/form flow. The snippets in this document require syntax and integration review; they are not evidence that the feature has already been built or tested.

### Validation of this document

The design received an independent builder review. Required frontend snippet defaults and the final eligibility-change invalid-form hook were corrected in response. All 12 Python blocks parse; the core class sketches import and compose against the current repository bases. A small ID-normalization example and the four required snippet configuration checks pass. The Django template examples parse, the JavaScript passes `node --check`, and relative Markdown links resolve. These are draft checks only: the proposed feature has not been implemented or verified through HTTP, a database test suite, or a browser.

## 12. References to current implementation

- `src/crud_views/lib/viewset/__init__.py`: `ViewSet.get_queryset(view)` and registered endpoints.
- `src/crud_views/lib/view/base.py`: `get_queryset`, real permission/ancestor dispatch, URL helpers, transaction hooks.
- `src/crud_views/lib/views/form.py`: `CustomFormNoObjectViewPermissionRequired`.
- `src/crud_views/lib/views/mixins.py`: `CrudViewProcessFormMixin` lifecycle.
- `src/crud_views/lib/deletion.py`: view-independent `inspect_deletion` and existing execution machinery.
- `src/crud_views/lib/views/delete.py`: business protection hook and single-delete orchestration.
- `src/crud_views/lib/bulk/`: current implementation proposed for replacement after approval and migration planning.

The design reuses existing behavior where it is small and explicit. It does not assume that reusing a method name reproduces another view's entire policy.
