# DeleteView

The `DeleteView` handles deleting model instances. It renders a confirmation form before
deleting.

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
- On a Guardian child view the parent gate runs first (404 for a missing parent, 403 without the parent permission).
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

### Linking Related Objects

!!! example "Try it live"
    The [Library example](https://django-crud-views-demo.onrender.com/library/author/)
    demonstrates protected publishing contracts when running this example revision.
    After migrating and seeding locally, sign in as `alice` / `alice`, filter the
    author list's last name by `Guin`, and open Ursula Le Guin's Delete action.
    Follow `Earthsea publishing contract` to its full detail page from the modal,
    or visit `/library/author/<author-pk>/delete/` directly for the full-page preview.
    Compare `bob` / `bob`: he sees only the generic blocked notice, with no Contract
    name or URL. Other seeded authors still demonstrate Book cascades. See the
    [tutorial setup](../getting_started/tutorial-6-books.md#a-protected-publishing-contract)
    for the model, route, and local startup commands; the hosted demo may run an older release.

Optionally render related objects as links to their detail views:

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

Protected blockers have an additional destination check **after** label visibility filtering. Only inspectable
local registered detail callbacks for the same concrete model, typed PK and database alias are eligible. The
destination's queryset must contain the row, its parent coordinates must resolve correctly, and its own access,
parent permission and action-state policy must allow the request. Source visibility and destination access are
independent: a visible blocker remains plain text when its detail destination is unavailable or disabled.
Guardian destinations additionally require supported co-located actor/child/parent and permission-route topology;
unsupported user, group, auth, content-type or object-grant routing yields plain text. Original anonymous/inactive
actors cannot gain eligibility through stored anonymous grants. Parent topology still matters with parent
permission checks disabled.

Candidates must be root-relative paths under the active script mount. Both raw and percent-decoded paths reject
network-path URLs, backslashes and controls; encoded slashes/backslashes are rejected. Resolution uses the decoded
path without the mount, while the original eligible URL (including its query) is retained in the anchor. External,
unregistered, non-detail, missing-row, wrong-model/PK/alias and uninspectable candidates yield `url=None`.
Callback init overrides that change policy, including `permission_required`, cannot be certified and yield text.
Expected access denial yields text; unexpected application queryset, converter, configuration or operational
errors propagate rather than silently producing a successful preview.

Eligibility binds a separate destination GET with its own URL kwargs/query and without the source modal header.
It does not dispatch a request or run arbitrary middleware, dispatch or custom `get_object` overrides. Those
checks, plus permission/row changes after preview, belong to the actual destination request. A link is navigation,
not an authorization grant. The private adapter is not a new public authorization extension API.

Both cascade and protected anchors perform ordinary full-page navigation. Activating one from a delete modal
leaves the modal, even if the destination supports modals; no modal/AJAX action attributes are added.

### Permission Filtering

Related objects are filtered based on the current user's permissions:

- Objects the user has `view` permission for: shown with full details
- Objects the user lacks `view` permission for: shown as aggregated counts (e.g., "3 book objects")

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
| `protected_objects` | Present only with previews enabled: filtered ordered entries with exactly `obj` (model instance) and `url` (eligible detail URL or `None`). It can be empty while the flag is true; linking disabled keeps the shape with every `url=None`. |

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

Protected linking adds destination lookup and applicable parent, authorization and action-state work **per visible
blocker**, separately from collection/rendering cost. Measured on stock fixtures with warmed permission caches:
for 0/1/4/8 candidates, unparented core used 0/1/4/8 queries; parented Guardian used 0/8/32/64. The regression bounds
are core `Q(N)<=N` and Guardian `Q(N)<=12*N+4`, with at most 12 additional queries per added candidate. These are
fixture measurements and regression bounds, not promises about arbitrary application hooks. Guardian work includes
child lookup, actor certification, parent lookup and parent/child user/group permissions. Disabled preview or
linking adds **zero adapter query cost**, but does not disable deletion inspection. No bulk cache or constant-query
preview is promised; custom querysets and hooks can add their own queries.

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
  `items` entries (`obj`/`url`), with explicit autoescape and ordinary anchors/plain text

Each alert in `related_objects.html` is a `{% cv_alert %}` call, so it renders through the one alert frame,
`crud_views/tags/alert.html` (see [Flash messages](messages.md)). The summary alert lists
`related_summary_items`, the summary as ready strings (`"book: 3"`); `related_summary` (a `{verbose_name: count}`
dict) stays in the context for overrides that read it.

Override these in your project's template directory to customize the rendering. Keep the independent incomplete
warning outside both protection branches, even with previews disabled. A copy of
`crud_views/view_delete.content.html` must include the snippet when `related_summary or has_protected_objects`, and a
copy of `related_objects.html` must use both notice branches: colon heading with caller-context
`{% with items=protected_objects %}` and `body_template="crud_views/snippets/delete/protected_objects.html"` when
labels exist, colon-free heading with the generic `text=` sentence otherwise. Do not pass entries as generic alert
`items=protected_objects`; access model fields through `item.obj.field`. A copy that still tests
`protected_objects` loses the notice whenever every label is hidden. Guard the entire confirmation form too:

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
| `protected_objects` | Ordered, filtered entries with exactly `obj` (model instance) and `url` (string or `None`); present only when `cv_show_related_objects=True`. No parallel legacy collection. |
| `has_protected_objects` | Independent unfiltered blocking boolean on every delete context, including preview-off and all-hidden cases; preserves whole-form omission. |
| `crud_views/snippets/delete/protected_objects.html` | Independently overridable body; reads caller-context `items` containing `obj`/`url`. Explicit autoescape; model fields use `item.obj.field`. |
| `crud_views/snippets/delete/related_objects.html` | Binds `items=protected_objects` in caller context and selects the protected body through `cv_alert body_template`; shared alert frame retains heading, icon, role and dismissal. |
| `cv_get_related_object_url(self, obj) -> str \| None` | Existing public candidate hook, unchanged signature and first-match/cascade behavior; protected candidates additionally undergo private destination eligibility checks. |
| Ordinary `<a href>` | Full-page navigation in the current browsing context, including from modals and to modal-capable destinations; no modal/AJAX action metadata. |

`cv_link_related_objects=False` retains the same entries with `url=None`; `cv_show_related_objects=False` omits the
detailed collection. Collector/provider/filter inputs remain model instances. The private eligibility adapter
is not a new public authorization extension API, and no generic alert-item API or modal-routing setting is added.

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
