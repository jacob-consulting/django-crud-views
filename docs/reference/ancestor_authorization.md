# Ancestor authorization

A request to a [nested ViewSet](nested.md) also authorizes the ancestors in its URL. For
`organization/<organization_pk>/customer/<customer_pk>/address/`, the Address list first checks that the Organization
and the Customer exist, that the Customer belongs to the Organization, and that the user holds the required
permission on them. Only then does the Address view run its own permission, queryset, state and form work.

Both plain views and `*PermissionRequired` views take part. The requested endpoint's own rules stay independent:
passing the ancestors never waives the endpoint's local permission, and a local grant never waives an ancestor. A
plain nested view with no local gate is still protected by its ancestors.

| Configuration | Behavior |
| --- | --- |
| ORM chain with `ParentViewSet` foreign-key relationships | The whole URL chain is validated and the selected ancestor permissions are enforced |
| ORM chain with a supported `ManyToMany` relationship | URL membership is validated and the selected permissions are enforced |
| A relationship the `ParentViewSet` metadata cannot express unambiguously | Configuration error (`crud_views.E320`) |
| A [Resource](resources.md) leaf under one or more ORM ViewSets | The ORM ancestry is authorized before the Resource loaders run |
| A Resource as a parent | Configuration error (`viewset.E261`); Resources are leaves |
| A top-level endpoint, including a Resource | Unchanged: no ancestor lookups and no ancestor permission queries |

## Configuration

```python
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
```

Every ViewSet has an `ancestor_policy` field holding its own fresh `AncestorPolicy()`. Both types are strictly
validated configuration values: they evaluate nothing and hold no request, user, object or grant state.

### `AncestorPermissions`

Two required string fields, `nearest` and `higher`. Each is a **key of the ancestor's permission map**
(`viewset.permissions`, for example `"view"` or `"change"`), resolved separately on every ancestor that is checked.

```python
AncestorPermissions(nearest="change", higher="view")
```

A pair is always complete and replaces the inherited pair as a whole. There is no partial merge and no `None` to
skip a level. Empty or whitespace-padded keys, `None` components and unknown fields are rejected.

### `AncestorPolicy`

| Field | Default | Meaning |
| --- | --- | --- |
| `provider` | `None` | How this ViewSet is checked **when it is an ancestor**. `None` is the class default: `"model"` on `ViewSet`, `"guardian"` on `GuardianViewSet`. Explicit values: `"model"`, `"guardian"` (GuardianViewSet only), `"none"` |
| `accept_global_perms` | `False` | **When this GuardianViewSet is an ancestor**: also accept the model permission instead of the object permission |
| `cascade` | `None` | **Requests to this ViewSet**: `None` follows the global setting; `True` checks all protected ancestors, `False` only the nearest one |
| `read` | `None` | **Requests to this ViewSet**: `None` inherits the global Read pair; an `AncestorPermissions` replaces it |
| `write` | `None` | **Requests to this ViewSet**: `None` inherits the global Write pair; an `AncestorPermissions` replaces it |
| `actions` | `{}` | **Requests to this ViewSet**: exact registered view key → complete `AncestorPermissions` |

The fields have two scopes:

- `provider` and `accept_global_perms` describe this ViewSet **as an ancestor** of deeper requests.
- `cascade`, `read`, `write` and `actions` describe **requests that target this ViewSet**. They are never inherited
  from ancestors: the requirements of Book requests belong on the Book ViewSet, even if Publisher is its parent.

`provider=None` means "the class default", never "unprotected"; only `provider="none"` removes a level's gate.
`cascade=False` still checks the nearest protected ancestor; it is not a way to switch the mechanism off.
Changing a ViewSet's provider does not change the local permission behavior of its own views.

### Global settings

```python
# settings.py: the defaults
CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE = True
CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS = {"nearest": "view", "higher": "view"}
CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS = {"nearest": "change", "higher": "view"}
```

Each mapping is validated as a complete pair; a mapping missing either key fails, and only an omitted setting uses
its default. The cascade setting must be a boolean. Like the other package settings, the values are captured at
startup: an invalid value raises a Pydantic `ValidationError` when `crud_views.lib.settings` is imported, and system
check `crud_views.E322` reports a value changed afterwards. There is no global provider, global Guardian fallback or
global action map. See [Settings](settings.md#ancestor-authorization).

### Examples

Application model imports are omitted.

```python
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet

cv_customer = GuardianViewSet(model=Customer, name="customer")
cv_address = ViewSet(
    model=Address,
    name="address",
    parent=ParentViewSet(name="customer"),
    ancestor_policy=AncestorPolicy(provider="none"),
)
```

A write to Address requires the `change` object permission on the Customer. Address's `"none"` provider matters only
when Address is the ancestor of a deeper ViewSet; it does not switch off the checks of Address requests.

Independent alternatives, each declared on the ViewSet named in its comment:

```python
# A nested ViewSet: check only the nearest protected ancestor on its requests.
AncestorPolicy(cascade=False)

# A nested ViewSet: require change on every checked ancestor for its writes.
AncestorPolicy(write=AncestorPermissions(nearest="change", higher="change"))

# A nested ViewSet with a registered "approve" endpoint.
AncestorPolicy(actions={"approve": AncestorPermissions(nearest="change", higher="view")})

# A GuardianViewSet: accept model grants when descendants check it as an ancestor.
AncestorPolicy(accept_global_perms=True)
```

## Providers

The levels that are protected follow from configuration alone, never from the user's grants.

| Ancestor declaration | Gate | Counts as the nearest protected ancestor |
| --- | --- | --- |
| Core `ViewSet` default, or `provider="model"` | The required model permission (`user.has_perm(...)`) | Yes |
| `GuardianViewSet` default, or `provider="guardian"` | The required permission on the resolved object, direct or group grant | Yes |
| `provider="none"` | No permission check at this level | No: the walk passes through |

A level with `"none"` is still resolved and its relationship is still validated. A ViewSet that should not protect
its descendants must declare `"none"`, even when all of its own views are plain.

The **Guardian provider** uses Guardian's configured content type (`GUARDIAN_GET_CONTENT_TYPE`) and counts direct and
group object grants. With `AncestorPolicy(accept_global_perms=True)` on that GuardianViewSet, the model permission is
accepted as well. For an active user, on the correct object:

| Object grant (direct or group) | Model grant | `accept_global_perms=False` | `accept_global_perms=True` |
| --- | --- | --- | --- |
| No | No | Deny | Deny |
| Yes | No | Allow | Allow |
| No | Yes | Deny | Allow |
| Yes | Yes | Allow | Allow |

This ancestor fallback is independent of a view's `cv_guardian_accept_global_perms`, which only affects that view's
own object or queryset gate. Neither one is a default for the other; see
[Guardian: parent ViewSets](guardian.md#parent-viewsets).

Protected providers deny inactive users, superusers included, and keep normal backend semantics for active
superusers. `"none"` adds no actor rule of its own.

`provider="guardian"` on a core `ViewSet` is a construction error: use a `GuardianViewSet` parent, which supplies the
permission map and content-type semantics. `accept_global_perms=True` on a ViewSet whose provider is not
`"guardian"` is a construction error too, because it would have no effect.

## Cascade: which ancestors are checked

| Global `CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE` | Requested ViewSet `cascade` | Checked gates |
| --- | --- | --- |
| `True` | `None` or `True` | All protected ancestors |
| `True` | `False` | The nearest protected ancestor only |
| `False` | `None` or `False` | The nearest protected ancestor only |
| `False` | `True` | All protected ancestors |

The requested ViewSet's explicit value overrides the global one in either direction. An ancestor's own `cascade`
cannot stop a deeper request.

Both depths resolve the full declared ancestry and validate every relationship, including `"none"` levels and
creates. Nearest-only skips the **permission checks** of the higher ancestors, not their lookups. A denial at the
nearest protected ancestor ends the request; a farther ancestor is never tried as an alternative. An ancestry whose
levels are all `"none"` has no ancestor permission gate but keeps the relationship checks and the endpoint's own
checks.

## Read and Write operations

| Effective pair | Nearest protected ancestor (both modes) | Higher protected ancestors (full cascade only) |
| --- | --- | --- |
| Read default | `view` | `view` |
| Write default | `change` | `view` |
| A stricter Write override | `change` | `change` |
| A more permissive Write override | `view` | `view` |

These are requirements on the **ancestors**, separate from the endpoint's own permission. Deleting a child requires
`change` on the parent by default, not `delete`. Opening a create, update or delete form is already a Write: the
HTTP method does not decide the operation.

Each shipped endpoint family, its subclasses and its permission variants have a fixed classification:

| Endpoint family | Operation |
| --- | --- |
| `ListView`, `CardListView`, `DetailView`, `ObjectDetailView`, polymorphic detail | Read |
| `CreateView`, `UpdateView`, `DeleteView` and their polymorphic variants | Write, including the form or confirmation GET |
| Polymorphic create-type selection | Write |
| `OrderedUpView`, `OrderedDownView` | Write |
| `RedirectChildView` | Read |
| `ManageView`, `GuardianManageView` | Read; the manage gate stays in place |
| `ActionView`, `CustomFormView`, `CustomFormNoObjectView`, `WorkflowView`, any other custom endpoint | No classification: a nested one needs an `actions` entry |
| Formset row request | The operation of the editor that owns it |

The classification follows the class, not its name or settings. Renaming a standard view's `cv_key` keeps its
family; naming a generic action `detail`, or setting `cv_permission = "view"` on it, does not make it a Read. An
override that changes what a standard view does (for example a `DetailView` that writes) must declare an `actions`
entry: the framework does not inspect method bodies.

### Action entries

An `actions` entry replaces the family or default pair for exactly one endpoint. It cannot switch traversal off.

The key is the view's **literal registered key** (`cv_key`), checked after registration has completed:

| Registered views on the nested ViewSet | Behavior |
| --- | --- |
| Only `card` | `actions["card"]` is valid; `actions["list"]` is an error |
| Both `list` and `card` | Each entry affects only its own endpoint |
| A `CardListView` registered as `list` | `actions["list"]` is valid; the family is still Read |
| List or card without an entry | The effective Read pair |

Navigation keeps its `list` → `card` fallback. A request that reaches Card that way still uses Card's own key and
entry, never another endpoint's.

### Nested custom endpoints

A nested endpoint without a classification needs a complete pair. For a nested ViewSet with a registered custom
view `cv_key = "approve"`:

```python
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet

cv_invoice = ViewSet(
    model=Invoice,
    name="invoice",
    parent=ParentViewSet(name="customer"),
    ancestor_policy=AncestorPolicy(
        actions={"approve": AncestorPermissions(nearest="change", higher="view")},
    ),
)
```

Both fields are required, and the key must be the registered `cv_key`. Keep any other choices of the ViewSet's
policy in the same `AncestorPolicy(...)`. The same declaration applies to a nested Guardian endpoint, on its
`GuardianViewSet`.

A missing or unknown entry fails in both cascade modes, also when every ancestor is `"none"`:

- `manage.py check` reports `crud_views.E321`, naming the ViewSet and the missing `actions['<key>']` (or the key that
  is not registered).
- A request to the endpoint raises `ImproperlyConfigured` before any lookup, for every actor. Rendering helpers that
  check the endpoint (for example a context button) raise the same error.

Exceptions:

- **Built-in classified endpoints** (the table above) need no entry; add one only to override their pair.
- **Top-level custom endpoints** need no entry. A top-level ViewSet rejects a non-empty `actions`, and any explicit
  `cascade`, `read` or `write`, at construction.

## Request order

For a nested request, every shipped view family follows this order:

1. **Static work.** The ancestor chain, its relationships and the operation's pair are validated and the checked
   gates are selected from configuration. No database access.
2. **Actor.** With at least one protected ancestor, an anonymous user gets the endpoint's no-permission response
   (the login redirect unless configured otherwise) and an inactive user gets 403. The endpoint's existing early
   denials are kept, also for an ancestry that is all `"none"`. No child object is loaded and no state hook runs.
3. **Ancestors, outermost first.** Each ancestor is looked up through its ViewSet queryset, its relationship to the
   level above is checked, and its gate is evaluated if selected, before the next level is touched. A missing,
   excluded or mismatched ancestor is a 404; a denied gate is a 403; the first failure ends the request.
4. **The endpoint.** Local permissions, the child queryset or object, action state, forms, formset rows, Resource
   loaders and writes run on their existing paths. Ancestor endpoints are never dispatched and their state hooks
   never run.

| Situation | Result |
| --- | --- |
| Protected ancestry, anonymous user, nonexistent parent pk | The endpoint's login redirect or denial; the parent is not looked up |
| Guardian endpoint configured for anonymous 403/404, protected ancestry | That configured response |
| Authenticated inactive user, protected ancestry | 403, also for an inactive superuser |
| All-`none` ancestry, the endpoint's existing early rule rejects the user | The same denial for a valid, missing or mismatched parent; no lookup |
| All-`none` ancestry, the endpoint admits the user | No login or inactivity rule is added; relationships and local checks follow |
| Full cascade: an outer gate denies, a deeper ancestor is missing | 403; the deeper ancestor's queryset is never called |
| Earlier gates pass, the next ancestor is missing, excluded or mismatched | 404 |
| Nearest-only: no grant on a higher ancestor, nearest gate passes | Continues to the local checks |
| A checked gate names a key missing from that ancestor's permission map | `ImproperlyConfigured` when reached |

An active user denied at an ancestor gate gets 403, not a login redirect. Plain views without Django's `AccessMixin`
get the default login redirect for protected ancestry. Passing every gate does not guarantee success: existence,
state and form validity still decide the response.

### Early actor rules of each family

| Endpoint | Early actor rule (step 2) |
| --- | --- |
| Plain core view | None of its own; protected ancestry adds the login redirect and the inactive 403 |
| Core `*PermissionRequired` view | Django's permission check alone (`PermissionRequiredMixin.has_permission`), without the object or action state; a failure uses the view's `handle_no_permission()` (`raise_exception`, `login_url`) |
| `ManageView` | The manage gate (`CRUD_VIEWS_MANAGE_VIEWS_ENABLED`, manage group) |
| Guardian views | `cv_guardian_anonymous_behavior` for anonymous users, 403 for inactive users |

A public plain view, a backend that grants anonymous users a permission, and a public manage page keep admitting
anonymous users under an all-`none` ancestry.

**Unsupported:** an override of `has_permission()` on a permission-required view is not consulted in step 2, because
the full method can load the child object and evaluate action state. Under all-`none` ancestry, an override that
admits users the plain permission check would refuse (for example anonymous users) is therefore not honored early:
the user is denied as by the plain check. The override still runs as the local gate after ancestry succeeds.

### Custom dispatch code

The check runs at the start of `dispatch()` in `CrudView`, `CrudViewPermissionRequiredMixin`, `ManageView` and
`GuardianParentPermissionMixin`, once per view instance. A `dispatch()` override must call `super().dispatch()`
before it loads child objects, evaluates state or writes; code placed before that call runs before ancestry.
Dispatch code that bypasses `super().dispatch()`, and a `cv_get_parent_object()` override that substitutes another
object or database, are unsupported. System checks catch known bad Guardian compositions, but cannot verify
arbitrary method bodies.

## Ancestor querysets and identity

The ancestor ViewSet's queryset decides which ancestors are visible:

```python
class TenantCustomerViewSet(ViewSet):
    def get_queryset(self, view):
        return super().get_queryset(view).filter(tenant=view.request.user.profile.tenant)
```

For each ancestor, the mechanism calls `ancestor_viewset.get_queryset(view=<requested view>)` and looks up that
ancestor's URL pk in the result.

| Input | Contract |
| --- | --- |
| `self` in `get_queryset` | The ancestor ViewSet being resolved |
| `view` | The requested endpoint, with its request and URL kwargs; its model, `cv_key` and `pk` describe the child |
| Identity lookup | The ancestor's own URL argument (`ParentViewSet` `pk_name`), never the child's `pk` |
| Ancestor list/detail view `get_queryset` overrides and permission mixins | Not called; put shared scoping on the ViewSet |

An excluded row (soft-deleted, another tenant, a filtering manager) is a 404 even when the user holds a grant on it;
it is never retried through an unfiltered manager. The declared relationship is validated in addition to the
queryset, so a queryset override cannot waive it. These rules apply to `"none"` ancestors and to nearest-only
requests too.

The resolved **immediate structural parent** is reused for the rest of the request: `CreateViewParentMixin`
attaches it (foreign key or `ManyToMany` through defaults), `cv_action_enabled` receives it, and
`cv_get_parent_object()` returns it without another query. That holds when the parent is `"none"` and a farther
ancestor supplies the nearest permission gate.

## Databases

Nested ancestry supports the `default` database only, for the ancestors, the child data and the authorization
records the checks read (users, groups, permissions, content types, Guardian grants). A nondefault queryset
(`.using("shard")`) or `DATABASE_ROUTERS` selection reached on that path raises `ImproperlyConfigured`; the request
is never rerouted to `default`, and a database problem is never reported as a permission denial. An explicit
`.using("default")` is fine. Top-level ViewSets keep their existing multi-database behavior.

The write alias of nested form, action, delete and workflow views is validated before the transaction opens. As
part of this, `cv_get_db_alias()` is now called **before** the write phase on every view, top level included; see
[Request lifecycle](request_lifecycle.md#multiple-databases).

## Resource leaves

A Resource ViewSet may be the leaf under one or more ORM ViewSets. The ORM ancestry is resolved and authorized as
above, and only then are `cv_get_items()` / `cv_get_item()` called with the URL kwargs. The application still scopes
the Resource collection and items to those kwargs; the framework does not validate Resource membership. The
operation, cascade and failure-order rules apply to Resource endpoints, plain ones included. See
[Resources: nesting](resources.md#nesting).

## Manage pages and redirects

A nested manage page needs both the ancestry checks (Read) and the existing manage gate. Neither
`CRUD_VIEWS_MANAGE_VIEWS_ENABLED = "yes"` nor membership of the manage group bypasses an ancestor, and passing the
ancestors does not bypass the manage gate. Top-level manage pages are unchanged. The manage page shows each ViewSet's
declared and effective `ancestor_policy` next to, and separate from, the Guardian views' local fallback; it is
configuration only and says nothing about a user's access to a chain.

`RedirectChildView` is a Read and needs no entry. Its ancestry runs before its object lookup and redirect; the
destination request authorizes its own operation, ancestors and local permissions independently. An explicit entry
can override its pair; other custom redirect views are custom endpoints.

## Mutation boundary

Passing ancestry authorizes the **URL path**. Assuming valid ancestry, passed gates, a valid form and no extra
application rule:

| Operation | Outcome |
| --- | --- |
| Update a Genre shared by Publishers A and B, through A | The shared row changes for both; B is not checked |
| Update a Book under Publisher A with an editable `publisher` field set to B | The Book moves to B; A's gate neither authorizes B nor blocks the move |
| Delete an object shared with another parent | Normal deletion, not unlinking from A |
| A custom action that affects other objects or parents | Its pair covers the URL ancestry; extra effects need their own checks |

Full cascade means the higher ancestors on the same URL path, not all memberships of an object. Rules for shared
objects and reparenting belong to the endpoint or application. For example, leave the parent field out of ordinary
edit forms and offer a separate move action that checks the destination:

```python
from django.core.exceptions import PermissionDenied

from crud_views.lib.crispy import CrispyModelForm
from crud_views.lib.views import ActionViewPermissionRequired


class BookForm(CrispyModelForm):
    class Meta:
        model = Book
        fields = ["title"]  # no "publisher": an ordinary edit cannot move the book


class BookMoveView(ActionViewPermissionRequired):
    cv_viewset = cv_book
    cv_key = "move"
    cv_path = "move"
    cv_permission = "change"

    def action(self, context) -> bool:
        target = cv_publisher.get_queryset(view=self).get(pk=self.request.POST["publisher"])
        if not self.request.user.has_perm("app.change_publisher", target):
            raise PermissionDenied
        self.object.publisher = target
        self.object.save(update_fields=["publisher"])
        return True
```

`move` is a custom endpoint, so the nested Book ViewSet declares
`ancestor_policy=AncestorPolicy(actions={"move": AncestorPermissions(nearest="change", higher="view")})`.

## Links and buttons

Request enforcement is authoritative. Full ancestor-aware visibility of links and buttons is not part of this
release, so a visible link can lead to a denied request. The existing helpers that already checked the immediate
parent now use that parent's provider, ancestor fallback and the target operation's `nearest` key:

| Helper situation | Behavior |
| --- | --- |
| The immediate parent is protected | Its provider and `accept_global_perms` decide, with the target's `nearest` key |
| The immediate parent is `"none"` | That gate is skipped; actor, state and custom denials remain; nothing farther is checked |
| No parent can be established from the inputs | `False`, as before |
| Invalid configuration (undeclared custom endpoint, missing permission key) | `ImproperlyConfigured`; nothing is hidden |

A Guardian list composed from `GuardianQuerysetMixin` without `GuardianParentPermissionMixin` keeps its existing
link rule, so its link can be visible while the request is denied by ancestry. Breadcrumbs, cancel destinations,
tabs and generic buttons are not ancestor-aware.

## Validation and diagnostics

Static configuration is validated without querying the model, `ContentType`, `Permission` or grant tables;
permission-map keys are resolved only at a reached gate.

| Problem | Failure |
| --- | --- |
| Unknown field or provider, non-boolean `accept_global_perms`/`cascade`, empty or padded key, incomplete pair | Pydantic `ValidationError` at construction |
| `provider="guardian"` on a core `ViewSet`; `accept_global_perms=True` without the Guardian provider | `ValidationError` at construction |
| Explicit `cascade`, `read`, `write` or non-empty `actions` on a top-level ViewSet | `ValidationError` at construction, naming the fields |
| A removed `cv_guardian_parent_*` declaration | `ValidationError` at construction |
| Invalid `CRUD_VIEWS_ANCESTOR_*` setting | `ValidationError` at import; `crud_views.E322` |
| Unknown parent, cycle, unsupported relationship | `crud_views.E320`; `ImproperlyConfigured` on URL construction or request |
| Missing or unregistered `actions` key | `crud_views.E321`; `ImproperlyConfigured` on request |
| Key missing from a reached ancestor's permission map | `ImproperlyConfigured` when reached |
| Nondefault database reached on a nested path | `ImproperlyConfigured` when reached |

A ViewSet whose declaration fails construction is not registered and gets no manage view; a corrected declaration
can reuse the name. A child may be declared before its parent; the reference must resolve when URLs are built.

A `ManyToMany` parent is declared with the child-side `attribute` (forward or reverse end) whose related model is the
parent model; `many_to_many_through_attribute` is optional and, when given, must name the other end of the same
relation.

## Performance and caching

Each request resolves one SELECT per ancestor level, plus one membership query per `ManyToMany` edge, and one
evaluation per checked gate. Nearest-only removes the higher permission checks but not the higher lookups. Nothing is
cached across requests: a revoked grant or a deactivated user takes effect on the next request. The existing
per-ViewSet permission-map cache is unrelated to user access.
