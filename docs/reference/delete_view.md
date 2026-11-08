# DeleteView

The `DeleteView` handles deleting model instances. It renders a confirmation form before
deleting.

!!! example "Try it live"
    The [Delete example](https://django-crud-views-demo.onrender.com/delete/project/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## Basic Usage

```python
from crud_views.lib.crispy import CrispyViewMixin, CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired, MessageMixin


class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message_template_code = "Deleted author »{{ object }}«"
```

## View Classes

| Class | Description |
|-------|-------------|
| `DeleteView` | Base delete view without permission checks |
| `DeleteViewPermissionRequired` | Delete view with `delete` permission required |

Both inherit from Django's `generic.DeleteView` and `CrudView`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | from `cv_viewset` | The Django model to delete (auto-derived from ViewSet) |
| `form_class` | `Form` | — | The form class (typically `CrispyDeleteForm`) |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success; must not be an object view such as `detail`, the object is gone (`viewset.E254`) |
| `cv_cancel_key` | `str \| None` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `str \| list[str] \| None` | `"auto"` | Origin keys the cancel button may return to dynamically. See [UpdateView](update_view.md#dynamic-cancel-target) |
| `cv_success_keys` | `list[str] \| None` | `None` | Origin keys the success redirect may return to dynamically; object views such as `detail` are rejected (`viewset.E254`). See [UpdateView](update_view.md#dynamic-success-target) |
| `cv_context_actions` | `list[str]` | `["home", "detail", "update", "delete"]` | Actions shown in the header area |
| `cv_show_related_objects` | `bool` | `False` | Show filtered deletion/protected labels and summaries; inspection and blocked state run even when false |
| `cv_link_related_objects` | `bool` | `False` | Link related objects to their detail views |

## HTTP methods

A delete view answers GET (the confirmation page) and POST (the validated deletion). Deletion only runs through the
POST: the form must validate and `cv_check_delete_protection()` must return no errors.

HTTP `DELETE` is rejected with **405 Method Not Allowed** on every package delete view: the core
`DeleteView` / `DeleteViewPermissionRequired`, the Guardian and the polymorphic delete views. Earlier releases
inherited Django's `DeletionMixin.delete()`, which deleted the object without the form, the protection check or the
form hooks. That was never a documented package API.

The rejection comes after the gates that already ran before it, so it reveals nothing they would hide:

- An anonymous user is still redirected to the login page (or gets the Guardian view's configured 403/404).
- On a core view, a user without the `delete` permission gets 403. The core permission phase also loads the object,
  so a missing object is a 404, and a disabled action state is a 403.
- On a nested view the [ancestor checks](ancestor_authorization.md) run first (404 for a missing or mismatched
  ancestor, 403 when a checked ancestor permission is missing).
  An inactive user gets 403 (see [Inactive users](guardian.md#inactive-users)).
- An active user on a top-level Guardian view gets the 405 before any object lookup, with or without a grant and
  whether or not the object exists.

The 405 response's `Allow` header and an `OPTIONS` response never list `DELETE`, also on a subclass that puts
`"delete"` back into `http_method_names`: the request is still rejected. A modal delete view keeps its
`Vary: X-CV-Modal` header on the 405. The guard sits in `dispatch` and leaves Django's `delete()` method as it is,
so Django 4.2 emits no `DeleteViewCustomDeleteWarning`.

Send a POST with the confirmation field, as the bundled form does. A client or test that sent `DELETE` must post the
form instead; see [Migrating to 1.0.0](../migrating-1.0.md#http-delete-on-delete-views).

## Confirmation Form

`CrispyDeleteForm` provides a confirmation checkbox that the user must check before
the object is deleted:

```python
from crud_views.lib.crispy import CrispyDeleteForm


class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
```

You can create a custom delete form if you need additional fields or different confirmation
logic.

### Delete button

The submit button of `CrispyDeleteForm` is built by two hooks. `get_delete_button_kwargs()` returns the crispy
arguments (default `{"name": "delete", "value": _("Delete")}`) and `get_delete_button()` returns the `Submit` from them,
with its classes from the button class key `form:delete`. Override the kwargs to change the label:

```python
class AuthorDeleteForm(CrispyDeleteForm):
    def get_delete_button_kwargs(self) -> dict:
        return {**super().get_delete_button_kwargs(), "value": _("Delete author")}
```

See [Buttons](buttons.md#forms).

## Messages

Add `MessageMixin` to show a success message after deletion:

```python
class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message_template_code = "Deleted author »{{ object }}«"
```

`cv_message_template_code` is a Django template string; `{{ object }}` renders to the string representation of the deleted instance.
Your base template renders the queued messages with `{% cv_messages %}` — see [Flash messages](messages.md).

## Form Processing Hooks

The same hooks as [CreateView](create_view.md#form-processing-hooks) are available, since
`DeleteView` also uses `CrudViewProcessFormMixin`.

Deletion and `cv_form_valid_hook` run in one transaction by default; side effects belong in
`cv_on_commit`. See [Request lifecycle, transactions & hooks](request_lifecycle.md#call-chains).

## Cascading Deletes Display

Show the supported related deletion effects. Display is opt-in; read-only inspection always runs. Unknown effects
produce an independent incomplete-preview warning, including with display disabled. A partial preview keeps the
ordinary confirmation available unless custom protection or known protected rows block deletion.

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True  # show what will be cascade-deleted
```

When enabled, the delete confirmation page displays:

- A summary of related objects by type and count
- A nested tree of individual related objects
- Warnings for protected relationships (`on_delete=PROTECT` / `RESTRICT`)
- Partial-count headings when some effects remain undescribed

### Display limit

`CRUD_VIEWS_DELETE_PREVIEW_LIMIT` defaults to **50**. An unset `cv_delete_preview_limit` inherits that project
setting; ordinary Python base-view inheritance preserves an explicit value. Set a positive integer to cap displayed
occurrences, or explicitly set `None` for unlimited details. `None` never means inherit. Project settings are
captured at startup, not re-read per request. For example:

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
    cv_delete_preview_limit = 20  # omit to inherit; None explicitly selects unlimited
```

Only raw positive `int` values and `None` are accepted: zero, negative integers, booleans, strings, floats and
containers are invalid, with no coercion or silent fallback. `crud_views.E109` always diagnoses invalid project
configuration, even when a valid explicit view override remains usable. `viewset.E265` diagnoses invalid explicit
or inherited view values. An invalid effective value raises `ImproperlyConfigured` before GET/POST context
preparation, even with previews disabled or non-strict operation; correct the configuration before retrying.

The effective core/Guardian/application visibility filter runs first. One shared budget selects visible protected
objects first in their existing order, then cascade objects depth-first with the remaining slots. Every displayed
occurrence counts, including repeated objects, ancestors and the root; there is no deduplication or per-model limit.
Hidden nodes consume no slot and have no placeholder; their permitted children are promoted in order, also in
unlimited mode. Optional cascade URL hooks run only for selected occurrences when linking is enabled.

`related_summary` and `related_summary_items` retain full filtered counts and any application redaction independently
of selection. Selected details still render with an empty summary, including a solo root. Root alone at limit one
is exact-at-cap; root plus a visible child exceeds it. No selected cascade nodes means no detail heading or empty list.

Detailed context includes `delete_preview_truncated`, true only when a further **visible** occurrence is omitted.
The template shows exactly one translated notice above the object lists:
"This preview is shortened. Additional objects are not shown."
Exactly filling the cap or having only a hidden remainder produces no notice; unlimited mode never truncates.
This flag is absent when previews are off. It is independent of `delete_preview_incomplete`, which describes
uninspected custom effects, is always present and can produce a separate warning at the same time.
Full inspection, blocking decisions and writes are unchanged. Unlimited mode restores all permitted details and
their optional URL/rendering costs; neither mode bounds total graph memory, filtering cost or total queries.

### Linking Related Objects

!!! example "Try it live"
    The [Library example](https://django-crud-views-demo.onrender.com/library/author/)
    demonstrates protected publishing contracts when running this example revision.
    After migrating and seeding locally, sign in as `alice` / `alice`, filter the
    author list's last name by `Guin`, and open Ursula Le Guin's Delete action.
    Read `Earthsea publishing contract` as a plain protected label in the modal,
    or visit `/library/author/<author-pk>/delete/` directly for the full-page preview.
    Compare `bob` / `bob`: he sees only the generic blocked notice, with no Contract
    name or URL. Other seeded authors demonstrate independent Book cascade navigation:
    follow a displayed Book link to its full detail page, including from a modal. See the
    [tutorial setup](../getting_started/tutorial-6-books.md#a-protected-publishing-contract)
    for the model, route, and local startup commands; the hosted demo may run an older release.

Optionally render selected cascade objects as links to their detail views:

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
    cv_link_related_objects = True  # link to detail views when available
```

The shared `cv_get_related_object_url(self, obj) -> str | None` hook selects the first registered ViewSet for the
object's model with a `detail` view and reverses its URL. Its signature, first-match behavior and cascade-tree
behavior are unchanged. There is no fallback registry scan if that candidate cannot be used.

Protected blockers always render plain text with `url=None`; they never call this hook or construct a destination
request. Applications may continue overriding the cascade hook; no new URL policy or authorization API is added.
Missing cascade destinations render as text. A cascade link is navigation, not an access grant: the actual request
enforces its destination's permissions and lookup policy.

Cascade anchors perform ordinary full-page navigation. Activating one from a delete modal leaves the modal,
even if the destination supports modals; no modal/AJAX action attributes are added.

### Permission Filtering

Related objects are filtered based on the current user's permissions:

- Objects the user has `view` permission for: eligible for selection within the display budget
- Objects the user lacks `view` permission for: no labels or placeholders; existing aggregate counts remain

This hides individual object labels but intentionally reveals model names and aggregate counts, even for models
whose rows the user cannot view. Applications that consider those aggregates confidential must override
`cv_filter_related_objects()` to redact the summary as well as labels.
The summary counts (`related_summary`) are deliberately not filtered: they show how much a deletion removes, which is
the existing aggregate policy. (A [conditional formset](conditional.md) with `on_off="purge"` follows its own,
separately documented deletion policy.)

The core view checks the model-level `view_<model>` permission. A Guardian delete view checks per-object grants
instead, with the delete view's own `cv_guardian_accept_global_perms` as the global fallback; see
[Cascading Deletes with Per-Object Permissions](guardian.md#cascading-deletes-with-per-object-permissions).

### Protected objects

`PROTECT` and `RESTRICT` relationships can block deletion. Every delete GET and POST context includes the blocked
state, even with the default `cv_show_related_objects = False`. The stock page omits the whole form while blocked:
confirmation, submit and the form-contained cancel control are absent, just as with custom protection errors.
Permitted labels use the heading "Deletion is blocked by protected relationships:" and a list. With no labels,
the heading has no colon and the notice says "Other objects still reference this one; remove or reassign them before
deleting it." Hidden labels never change the blocked state.

| Key | Contents |
|---|---|
| `has_protected_objects` | Present on every delete GET/POST context, computed from the unfiltered protected collection. Use it for the notice and form guard. |
| `protected_objects` | Present only with previews enabled: selected, filtered ordered entries with exactly `obj` (model instance) and `url` (always `None`). It can be empty while the flag is true; linking enabled still leaves every `url=None`. |
| `related_objects` | Selected cascade nodes with `obj`, optional `url` and nested `children`. Hidden ancestors are omitted and permitted children promoted. |
| `delete_preview_truncated` | Detailed-preview-only boolean for actual visible overflow, independent of `delete_preview_incomplete`. |

A confirmed POST stopped by the early check returns the protection page with **200**, or **422** in a modal,
without executing deletion. Inspection merges native and provider blockers before permission filtering.
A narrow race backstop handles native protection observed during fresh write collection before any executable
custom collection callback. See [Execution Order](#execution-order) for the precise origin and transaction limits.

#### Collection cost and overrides

Inspection reads metadata and full display rows on the selected write alias. It does not instantiate `NestedObjects`
or invoke `Collector.collect`, deletion handlers, `SET(...)` factories, defaults, private collection hooks, model
deletion or delete signals. Ordinary ORM reads can still run managers, converters, model initialization and read
signals. Application providers and display filters are trusted code; the package cannot prove their purity.
Inspection is cached for the view instance; an allowed POST additionally performs fresh write collection. Large
cascades materialize full rows, tree and counts; there is no large-graph performance bound.

Protected presentation performs no destination lookup or URL-hook work. In the core/Guardian component fixtures
(`tests/test1/test_delete_databases.py::test_delete_preview_component_costs`, Python 3.12 / Django 5.2), a deliberately
querying cascade hook performs one query per selected cascade occurrence. With limit 3 and three or more visible
blockers, no cascade occurrence is selected and presentation SQL is zero. With two blockers and a visible root,
one hook call/query remains. Unlimited mode selects the root regardless of blocker count. These are attributed
presentation measurements, not a total-query bound: complete inspection still used 5 core / 6 Guardian queries;
effective filtering used 0 core / 4–6 Guardian queries in these warmed-cache fixtures.
Inspection and visibility process complete relationships before selection. Rendering selected labels, custom
filters and URL hooks may add arbitrary queries. The cap bounds displayed occurrences and optional selected
presentation work, not total graph memory, filtering cost or total queries. Preview off bypasses filtering and
presentation, but full inspection still runs; linking off only bypasses optional cascade URL work.

`cv_get_related_objects()` remains a read-only compatibility accessor returning `RelatedObjects(tree, summary,
protected)`. **Overrides are rejected immediately**, without calling them: `viewset.E263` at startup and
`ImproperlyConfigured` at runtime. Move descriptions to `cv_get_delete_preview` and redaction to
`cv_filter_related_objects`; see [Safe deletion preview overrides](../migrating-1.0.md#safe-deletion-preview-overrides).

### Inspection and provider API

Import `RelatedObjects`, `DeleteInspection`, `DeletePreviewBoundary` and `DeletePreviewContribution` from
`crud_views.lib.deletion`. The old `RelatedObjects` import from `crud_views.lib.views.delete` still works.
`inspect_deletion(target, *, using)` returns `DeleteInspection(related, boundaries)`; its `complete` property is true
exactly when no boundaries remain. `merge_delete_preview(inspection, contributions, *, using)` validates and merges
provider records. Normal views use these through `cv_get_delete_preview(self, boundaries, *, using)`, returning an
iterable of contributions (default `()`). It runs after inspection, including when previews are disabled.

| Record | Fields |
|---|---|
| Frozen `DeletePreviewBoundary` | `kind` (`"model_delete"`, `"on_delete"`, `"private_relation"`), `model`, `field_name` (possibly `None`), `using`, ordered `source_pks` tuple, `field_model` (declaring model; default `None` for `model_delete`) |
| Frozen `DeletePreviewContribution` | `boundary`, `deleted` tuple of saved model instances (default `()`), `protected` tuple of saved model instances (default `()`), `complete` boolean (default `False`) |

`model` and `source_pks` identify the source rows being inspected. `field_model` identifies the model declaring
the relationship: inspecting a Document's reverse `Attachment.document` produces `model is Document` and
`field_model is Attachment`. Parent links and private relations likewise retain their declaring field's model.
Separate owners with the same field name remain independent boundaries, even when one relationship has no rows.
Source PKs batch only within one owner; they are not the related field owner's row identities.

Use a boundary supplied to this invocation, selecting the exact declaring owner as well as source model and field.
Equality includes all six fields: kind, model, field_name, using, **ordered** source_pks and field_model.
Reconstructed descriptors must equal a current supplied descriptor in every field. Ownerless field descriptors
and model-delete descriptors with a field owner raise `ValueError`; `model_delete` retains `field_model=None`.
Unknown, wrong-owner, stale, cross-alias or duplicate boundaries, invalid tuple/boolean fields, unsaved/non-model rows and
rows whose `_state.db` differs from `using` raise `ValueError`. Query providers explicitly with `.using(using)`;
provider exceptions propagate. `complete=True` is the application's attestation about that boundary alone, including
an explicitly described no-effect boundary; it is not a proof of purity or a whole-preview completeness switch.
Attesting one owner never completes another owner's same-name relationship. Migrate existing source/name-only
providers immediately; see [Describing custom deletion effects](../migrating-1.0.md#describing-custom-deletion-effects).

Deleted rows merge as deduplicated direct-root children, with counts added for models other than the root's concrete
model. Identity is `(using, concrete_model, pk)`, preserving UUID/integer values and discovery order; proxy and
concrete descriptions of one stored row deduplicate. Native tree structure and redacted `None` positions remain.
Concrete multi-table parent rows count separately: deleting a Car can include its Vehicle parent in the summary.
Native joins use actual field targets, including `to_field` and parent links whose key differs from the child PK.
For supported native reverse and parent joins, any `None` component means no relationship: inspection does not
turn it into an `IS NULL` match. Unlinked nullable rows neither block nor contribute cascade counts. Unknown
handlers or unsupported metadata still produce owner-qualified boundaries even when the join is null or empty;
they are not silently declared complete. Read and converter failures propagate.

Provider `protected` rows are an **additive veto**, even without a native blocker. Neither contributions nor display
redaction remove native protection. Native `RESTRICT` is reconciled against the supported cascade closure only;
asserting a restricted row in provider `deleted` never clears a blocker outside that closure.

Exact native `CASCADE`, `PROTECT` and `RESTRICT` are inspected through metadata. `SET_NULL` and `DO_NOTHING` have no
deletion traversal. `SET(...)`, `SET_DEFAULT`, unknown handlers/field classes, generic/private bulk relations and
custom root `delete` methods leave boundaries, even on empty relationships. Ordered-model Author and polymorphic
Car therefore normally show incomplete notices; no library override is assumed harmless. Unexpected read, provider
or rendering failures propagate instead of being relabelled incomplete. See the
[custom-effect recipe](../migrating-1.0.md#describing-custom-deletion-effects).

Every delete context contains `delete_preview_incomplete` and `has_protected_objects`. Raw boundaries, aliases and
unfiltered protected instances stay local. Preview keys (`related_objects`, `related_summary`,
`related_summary_items`, `protected_objects`) exist only when display is enabled. Incomplete integer counts are
qualified by the heading, not changed to strings. Aggregate model/count disclosure retains the policy above.

### Custom related-object filters

`cv_filter_related_objects(user, related)` receives the `RelatedObjects` tuple (`tree`, `summary`, `protected`) and
returns the tuple the template context is built from. It is the hook for narrowing what the preview shows. An override
must keep these guarantees:

- Filter `related.protected` as well as the tree, and return only protected objects the user may view. Never return
  the raw `related.protected`.
- Start from the right superclass: call `super().cv_filter_related_objects(user, related)` and narrow its result, so a
  core view keeps the model-level check and a Guardian view keeps its object-grant check. If you replace the filter
  entirely, apply an equivalent authorization check. On a Guardian view, do not run the core model-level filter after
  the Guardian one: it would hide labels that an object grant permits without a global permission.
- Leave `has_protected_objects` alone. It is computed before your hook runs, so a filter that hides every label
  cannot hide the block.
- Keep the summary counts as they are, unless you deliberately change the aggregate policy for your view.

The collector, provider contributions and this filter continue to use model-instance collections in `protected`.
Only the filtered template context projects them into `obj`/`url` entries, after this hook returns. Do not return
template dictionaries from the provider or filter, or recompute hidden labels in a template.

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True

    def cv_filter_related_objects(self, user, related):
        related = super().cv_filter_related_objects(user, related)
        # narrow further: never show archived contracts by name
        return related._replace(protected=[obj for obj in related.protected if not obj.is_archived])
```

### Template Customization

The related objects display uses three overridable templates:

- `crud_views/snippets/delete/related_objects.html` — main container with summary, tree, and warnings
- `crud_views/snippets/delete/related_objects_tree.html` — recursive nested tree of individual objects
- `crud_views/snippets/delete/protected_objects.html` — independent flat protected body consuming caller-context
  `items` entries (`obj`/`url=None`), with explicit autoescape and plain text

Each alert in `related_objects.html` is a `{% cv_alert %}` call, so it renders through the one alert frame,
`crud_views/tags/alert.html` (see [Flash messages](messages.md)). The summary alert lists
`related_summary_items`, the summary as ready strings (`"book: 3"`); `related_summary` (a `{verbose_name: count}`
dict) stays in the context for overrides that read it.

Override these in your project's template directory to customize the rendering. Keep the independent incomplete
warning outside both protection branches, even with previews disabled. A copy of
`crud_views/view_delete.content.html` must include the snippet when
`related_summary or has_protected_objects or related_objects or delete_preview_truncated`, and a
copy of `related_objects.html` must use both notice branches: colon heading with caller-context
`{% with items=protected_objects %}` and `body_template="crud_views/snippets/delete/protected_objects.html"` when
labels exist, colon-free heading with the generic `text=` sentence otherwise. Do not pass entries as generic alert
`items=protected_objects`; access model fields through `item.obj.field`. A copy that still tests
`protected_objects` loses the notice whenever every label is hidden. Guard the entire confirmation form too:

Show one shortening notice for `delete_preview_truncated` above the lists. Guard summaries with `related_summary`
and details separately with `related_objects`; selected solo-root details remain visible with an empty summary,
and no empty detail frame is rendered. These rules apply with finite limits and explicit `None` alike.

```django
{% if not has_protected_objects %}
    <form method="post">
        {% csrf_token %}
        {% cv_render_form %}
    </form>
{% endif %}
```

Keep the existing custom-protection branch around this content. The complete executable content/snippet/body recipe is
in [Copied delete templates](../migrating-1.0.md#copied-delete-templates-with-incomplete-previews); a copied alert leaf must render `alert.text` or
`alert.body_template` as well as its heading and items.

### Protected-preview public surface

The following inventory is the contract for copied templates and the Phase 7 stability reference:

| Public name | Contract |
|---|---|
| `protected_objects` | Selected, ordered, filtered entries with exactly `obj` (model instance) and `url` (always `None`); present only when `cv_show_related_objects=True`. No parallel legacy collection. |
| `has_protected_objects` | Independent unfiltered blocking boolean on every delete context, including preview-off and all-hidden cases; preserves whole-form omission. |
| `crud_views/snippets/delete/protected_objects.html` | Independently overridable body; reads caller-context `items` containing `obj`/`url`. Explicit autoescape; model fields use `item.obj.field`. |
| `crud_views/snippets/delete/related_objects.html` | Binds `items=protected_objects` in caller context and selects the protected body through `cv_alert body_template`; shared alert frame retains heading, icon, role and dismissal. |
| `cv_get_related_object_url(self, obj) -> str \| None` | Existing cascade hook, unchanged signature and first-match behavior; called only for selected cascade occurrences with linking enabled, never for protected entries. |
| Ordinary cascade `<a href>` | Full-page navigation in the current browsing context, including from modals and to modal-capable destinations; no modal/AJAX action metadata. |
| `CRUD_VIEWS_DELETE_PREVIEW_LIMIT` / `cv_delete_preview_limit` | Default 50; unset view inherits project, ordinary base-view inheritance applies; positive integer or explicit `None` for unlimited. Raw validation uses `crud_views.E109`, `viewset.E265` and effective-value `ImproperlyConfigured`. |
| `delete_preview_truncated` | Detailed-preview-only actual visible-overflow boolean; one notice, independent of `delete_preview_incomplete`. |
| `related_summary` / `related_summary_items` | Full summary and application redaction stay independent of selected details. Solo root renders even with empty summary and consumes a slot. |

Protected entries always retain `url=None`, regardless of `cv_link_related_objects`; `cv_show_related_objects=False`
omits detailed collections and truncation state. Collector/provider/filter inputs remain model instances. This is
not a new public authorization extension API, and no generic alert-item API or modal-routing setting is added.

## Delete Protection

Add custom business logic to prevent deletion.

### View Hook

Override `cv_check_delete_protection()` to return error messages:

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher

    def cv_check_delete_protection(self) -> list[str]:
        if self.object.books.filter(is_published=True).exists():
            return ["Cannot delete a publisher with published books."]
        return []
```

When the method returns errors, the delete confirmation form is **not shown at all**. Instead, the user sees the error messages in an alert. This runs on GET, so the user immediately knows the object cannot be deleted.

The check also runs on POST as defense in depth — if a protection error is returned, the object is not deleted.

### Form Hook

For validation that should happen at submit time, use standard Django form validation:

```python
class ProtectedDeleteForm(CrispyDeleteForm):
    def clean(self):
        cleaned_data = super().clean()
        # custom validation logic
        if some_condition:
            raise ValidationError("Cannot delete.")
        return cleaned_data
```

### Execution Order

1. **GET/POST context**: run `cv_check_delete_protection()` and inspect supported effects plus providers, regardless of previews.
   Custom errors take presentation precedence; either block omits the form.
2. **POST**: run `cv_post_hook`, then validate the confirmation form. An invalid form follows the existing invalid
   hook/response path.
3. **Valid POST**: custom protection errors become non-field errors; custom or database protection returns the
   protection page (200 full page / 422 modal), with no write hooks or deletion.
4. **Unblocked POST**: run the existing write lifecycle on the pinned alias. Fresh native collection protection
   can use the race backstop after the transaction unwinds, under the rules below.
5. **Successful deletion**: run the normal success hook, commit callbacks and redirect/204 behavior.

For an exact bound Django `Model.delete`, the package reloads the same model/PK through its base manager on the
pinned alias immediately before collection, inside the existing write lifecycle. This applies even when read and
write aliases are the same: current selected-row non-PK values determine native joins. Parent rows are queried
from actual parent-link values on that alias, including non-PK targets, without dereferencing cached parent
descriptors or substituting the child's PK. Null native joins select no parent or reverse rows.

The original authorized instance remains `self.object`, supplies selector hints, and is the delete signals'
`origin`. Its non-PK values, relation caches and `_state.db` are preserved; only its PK attname is cleared after
successful native return, before the success hook. A failed collection/deletion leaves its PK intact. If the
selected native row has disappeared, its model's `DoesNotExist` propagates before deletion callbacks, success
hooks or commit registration, with the original PK retained. This differs from an initial missing URL target's
404. A later success-hook failure does not restore in-memory PK state, even if atomic writes roll back.

The package inherits Django's SQL deletion executor, signals, counts and return value. This fresh read adds no
row lock or guarantee against changes after the read; inspection is descriptive and never reused as write
instructions. It establishes native protection origin at the operation itself; no
traceback or graph-certification inference is used. Native `PROTECT` stops immediately. Native `RESTRICT` reconciles
at outer closure. Before executing a custom handler, `SET`/default factory or private collector, the collector marks
that a custom callback has been entered. This flag stays set across recursion. Only a native blocker observed before
that point becomes the private marker that `post` catches after the atomic context unwinds. A custom callback that
returns before a later native block still makes that later error propagate. Query/converter errors also propagate.

Every other bound model method runs once on the original authorized object as `delete(using=using)`, including
ordered-model and polymorphic methods. It receives no selected-row replacement or automatic refresh. The custom
method owns its relation routing, additional queries and external side effects; passing `using` alone cannot
guarantee that those operations honor the pinned alias.
Actual Author sibling reordering and Car/Vehicle parent behavior are preserved; their stale `ProtectedError` and
`RestrictedError` propagate. No friendly native response is promised for custom methods. Inspectable methods lacking
a keyword `using` or forwarding `**kwargs` fail `viewset.E264`; opaque or incompatible methods raise
`ImproperlyConfigured` before invocation. See [Delete signatures](../migrating-1.0.md#delete-method-signatures-and-database-selection).

Errors from `cv_post_hook`, custom mutation hooks, success hooks, model overrides, delete signals and `cv_on_commit`
propagate. Non-atomic callback writes can remain after a later block; external I/O cannot be rolled back even with
`cv_atomic=True`. A commit callback error leaves committed deletion intact. Friendly native markers do not imply
rollback of external effects. Delegate custom `post` to the standard path for HTTP protection responses; direct
`cv_form_valid_process` callers own authorization/confirmation and receive no automatic HTTP protection response.

### Database selection

After resolving an authorized saved `self.object`, `cv_get_delete_db_alias()` calls `cv_get_db_alias()` once, validates
its configured nonempty alias and pins it for the view instance. The delete default selects
`router.db_for_write(type(self.object), instance=self.object)`. Inspection, execution, the default atomic block and
`on_commit` registration share that alias, even with `cv_atomic=False`. Calling the accessor before a saved target
exists raises `ImproperlyConfigured`. Request parameters do not select it.

A router/explicit selector can choose a different alias from the loaded instance. Native execution reloads the
same model/PK there with current selected-row relationships and actual parent links; custom methods retain the
original instance and their routing responsibility above. The selector is trusted application policy.
Custom atomic overrides must use `cv_get_delete_db_alias()`; side-effect ORM queries must select their own
alias explicitly. There are no cross-database transactions. See
[Request lifecycle](request_lifecycle.md#transactions) and the
[atomic migration](../migrating-1.0.md#delete-method-signatures-and-database-selection).

---

> To disable an action the user *is* permitted to perform, based on object state
> (e.g. a locked/open parent), see [Conditionally disabling an action](action_enabled.md).
