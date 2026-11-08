# Nested ViewSets (parent/child)

A child ViewSet can declare a parent ViewSet. Once declared:

- the child's URLs are nested under the parent's URL (`parent_prefix/<parent_pk>/child_prefix/...`)
- every request to the child resolves and authorizes its ancestors first — see
  [Ancestor authorization](#ancestor-authorization)
- the child's querysets are automatically filtered to the current parent object
- create views can auto-set the parent foreign key with `CreateViewParentMixin`
- context buttons can jump up (`parent`), down (`ChildContextButton`), or sideways
  (`SiblingContextButton`) across the hierarchy

!!! example "Try it live"
    The [Nested example](https://django-crud-views-demo.onrender.com/nested/company/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

Nesting is not limited to one level — a child ViewSet can itself be the parent of a
grandchild ViewSet, and a single parent can have any number of children.

The examples on this page come from the `nested` example app
(`examples/bootstrap5/nested/`), which models a three-level hierarchy: `Company` →
`Department` → `Employee`, plus a second child `Office` directly under `Company`.

## Declaring the relationship

Pass `parent=ParentViewSet(name="...")` to the child's `ViewSet`. The name refers to the
*registry name* of the parent ViewSet (its `name=` argument, not the model or variable name):

<!-- cv-sync: nested/views.py -->
```python
cv_department = ViewSet(
    model=Department,
    name="department",
    parent=ParentViewSet(name="company"),
    icon_header="fa-solid fa-people-group",
)
```

Nesting composes: a grandchild simply names its immediate parent. `Employee` is a child of
`Department`, not of `Company`:

<!-- cv-sync: nested/views.py -->
```python
cv_employee = ViewSet(
    model=Employee,
    name="employee",
    parent=ParentViewSet(name="department"),
    icon_header="fa-regular fa-id-badge",
)
```

`ParentViewSet` also accepts:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Registry name of the parent ViewSet |
| `attribute` | `str \| None` | parent's `name` | Model attribute holding the `ForeignKey` to the parent |
| `pk_name` | `str \| None` | `f"{parent.name}_pk"` | Name of the parent's primary key in the URL pattern |
| `many_to_many_through_attribute` | `str \| None` | `None` | Set for a `ManyToMany` parent relation instead of a `ForeignKey` |

Set `attribute` when the `ForeignKey` field name doesn't match the parent's registry name;
set `pk_name` only if the default URL kwarg name would collide with another kwarg.

## URL structure

Each parent level contributes its own primary key segment to the URL, named
`<parent_registry_name>_pk`; the ViewSet's own object views (detail/update/delete) still use
`pk` for their own object:

```text
company/                                                          Company list
company/create/                                                   Company create
company/<pk>/                                                     Company detail
company/<pk>/update/                                               Company update
company/<pk>/delete/                                               Company delete

company/<company_pk>/department/                                  Department list (children of one company)
company/<company_pk>/department/create/                           Department create
company/<company_pk>/department/<pk>/                              Department detail
company/<company_pk>/department/<pk>/update/                       Department update

company/<company_pk>/department/<department_pk>/employee/          Employee list (grandchildren)
company/<company_pk>/department/<department_pk>/employee/<pk>/     Employee detail

company/<company_pk>/office/                                       Office list (second child of company)
company/<company_pk>/office/<pk>/                                  Office detail
```

`Employee`'s URLs carry both `company_pk` and `department_pk` — every ancestor's primary key
is part of the URL, not just the immediate parent's. The child's `get_queryset()` is filtered
by walking this same parent chain, so a `department_pk`/`company_pk` combination that doesn't
match the stored `ForeignKey` chain returns 404 rather than leaking another company's data.

## Creating children

Declaring `parent=` nests the URLs and filters querysets, but it does not by itself set the
parent `ForeignKey` when a new child is created — add `CreateViewParentMixin` to the create
view for that:

<!-- cv-sync: nested/views.py -->
```python
class DepartmentCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_department
    form_class = DepartmentForm
    cv_message_template_code = _("Created department “{{ object }}”")
```

`CreateViewParentMixin` reads the parent object from the URL and sets it on the form instance
before saving, using the same `attribute` (or `many_to_many_through_attribute`) declared on
`ParentViewSet` — so `DepartmentForm` does not need a `company` field at all. Place
`CreateViewParentMixin` before the `CreateView`/`CreateViewPermissionRequired` base in the
MRO, as shown above.

!!! note
    `BreadcrumbMixin` above is a small project-level mixin around
    `CrudViewBreadcrumbMixin` (see [Breadcrumb](breadcrumb.md)) — it is unrelated to nesting
    itself; every view in the example app uses it to render the breadcrumb trail.

## Navigating between parent and child

### Down: table links and `ChildContextButton`

The simplest way to link down to a child collection is a `LinkChildColumn` on the parent's
table — it points at the row's own child list, with the parent PK already applied:

<!-- cv-sync: nested/views.py -->
```python
class CompanyTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    city = tables.Column()
    departments = LinkChildColumn(name="department", verbose_name=_("Departments"), attrs=Table.ca.w10)
    offices = LinkChildColumn(name="office", verbose_name=_("Offices"), attrs=Table.ca.w10)
```

To link down from outside a table row — e.g. a "Departments" button in a detail view's
header — add a `ChildContextButton` to the parent ViewSet's `context_buttons` and reference
its key from `cv_context_actions`:

```python
from crud_views.lib.viewset import ViewSet, context_buttons_default
from crud_views.lib.view import ChildContextButton

cv_company = ViewSet(
    model=Company,
    name="company",
    context_buttons=context_buttons_default()
    + [
        ChildContextButton(key="departments", child_name="department", label_template_code="Departments"),
    ],
)


class CompanyDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_company
    cv_context_actions = ["update", "delete", "departments"]
```

### Up: the `parent` button

Every ViewSet gets a `parent` context button by default (`context_buttons_default()`); it
links up to the parent's list view and renders nothing when the ViewSet has no parent — see
[`ParentContextButton`](context_buttons.md#parentcontextbutton).

### Sideways: linking to a sibling child collection

When a parent has several children (e.g. `Author` → `Book`, `Article`) and you want a button
on one child's pages that jumps to a sibling collection under the *same* parent, use
[`SiblingContextButton`](context_buttons.md#siblingcontextbutton). Place it on the child
ViewSet; it reuses the parent PK from the current URL:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
from crud_views.lib.view import SiblingContextButton

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    context_buttons=context_buttons_default()
    + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)
```

```python
class BookListView(ListViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["parent", "create", "articles"]
```

Use `ChildContextButton` on the parent view to go *down* to a child, and
`SiblingContextButton` on a child view to go *sideways* to a sibling.

## Ancestor authorization

A nested URL names every ancestor: `publisher/<publisher_pk>/book/<pk>/update/` is an update of a Book *under
one Publisher*. Before a nested endpoint does any work of its own, one shared mechanism resolves each
ancestor named in the URL and checks the ancestor permissions that endpoint's operation requires. This applies to
plain and `*PermissionRequired` views, to Guardian views and to manage pages.

Ancestor checks and the endpoint's own checks are independent gates. Passing the ancestors never waives the
child's own permission, queryset, state or form rules, and a child permission never stands in for an ancestor. A
plain child view without a permission of its own is still protected by its ancestors. Top-level ViewSets do no
ancestor work at all.

### Policy fields and their two scopes

Each ViewSet has an `ancestor_policy`, an `AncestorPolicy` value. Import it and `AncestorPermissions` from
`crud_views.lib.viewset`, together with `ParentViewSet` and `ViewSet`. Both are plain validated configuration
values: they hold no request, user or object state.

`AncestorPermissions(nearest=..., higher=...)` is a complete pair of permission-map keys. `nearest` applies to
the nearest protected ancestor, `higher` to every protected ancestor above it. Each key is looked up in the
permission map of the ancestor being checked (`"view"`, `"change"` or a custom key). Both fields are required.
A pair always replaces the whole inherited pair; there is no partial merge and no `None` to skip a level.

| `AncestorPolicy` field | Default | Scope | Meaning |
|---|---|---|---|
| `provider` | `None` | this ViewSet **as an ancestor** | `None`: the class default — `"model"` for `ViewSet`, `"guardian"` for `GuardianViewSet`. Explicit `"model"`, `"guardian"` or `"none"` |
| `accept_global_perms` | `False` | this ViewSet **as an ancestor** | Guardian provider only: also accept the model permission instead of the object grant |
| `cascade` | `None` | requests **to this ViewSet** | `None`: the global setting. `True`: check every protected ancestor. `False`: only the nearest protected one |
| `read` | `None` | requests **to this ViewSet** | `None`: the global Read pair. Otherwise a complete `AncestorPermissions` |
| `write` | `None` | requests **to this ViewSet** | `None`: the global Write pair. Otherwise a complete `AncestorPermissions` |
| `actions` | `{}` | requests **to this ViewSet** | exact registered view key → complete `AncestorPermissions`; replaces the Read/Write pair for that endpoint |

The scopes matter. Requirements for Book requests belong on the Book ViewSet, even though Publisher is the
ancestor being checked. How Publisher is checked (its provider and fallback) belongs on the Publisher ViewSet and
applies to every descendant that reaches it. A ViewSet never inherits `cascade`, `read`, `write` or `actions`
from its ancestors.

The global defaults are three settings, `CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE` (`True`),
`CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS` (`view`/`view`) and `CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS`
(`change`/`view`); see [Settings](settings.md#ancestor-authorization). There is no global provider, fallback or
action map.

Typical declarations:

| On | Declaration | Effect |
|---|---|---|
| a nested ViewSet | `AncestorPolicy(cascade=False)` | requests to it check only the nearest protected ancestor |
| a nested ViewSet | `AncestorPolicy(write=AncestorPermissions(nearest="change", higher="change"))` | its writes need `change` on every checked ancestor |
| a nested ViewSet | `AncestorPolicy(actions={"approve": AncestorPermissions(nearest="change", higher="view")})` | the pair of its registered `approve` endpoint |
| any ViewSet | `AncestorPolicy(provider="none")` | no permission gate where this ViewSet is an ancestor |
| a `GuardianViewSet` | `AncestorPolicy(accept_global_perms=True)` | as an ancestor, a model grant also satisfies its object gate |

### Providers and cascade depth

The provider decides how one ancestor is checked:

| Ancestor | Gate | Counts as protected |
|---|---|---|
| `ViewSet`, provider `None` or `"model"` | the required model permission, e.g. `app.view_publisher` | yes |
| `GuardianViewSet`, provider `None` or `"guardian"` | the required permission granted on the resolved object, directly or through a group | yes |
| any ViewSet, provider `"none"` | no permission check | no: it is skipped when the nearest protected ancestor is chosen |

A `"none"` ancestor is still resolved and its relationship still validated. Only its permission gate is skipped.
`provider="guardian"` on a core `ViewSet` is rejected: use `GuardianViewSet` for object-permission ancestors.

The requested ViewSet's `cascade` overrides the global setting in either direction. An ancestor's own `cascade`
value has no effect on its descendants.

| Global setting | Requested ViewSet | Checked ancestors |
|---|---|---|
| `True` | `None` or `True` | every protected ancestor |
| `True` | `False` | the nearest protected ancestor |
| `False` | `None` or `False` | the nearest protected ancestor |
| `False` | `True` | every protected ancestor |

For Organization → Customer → Address (`provider="none"`) → Instruction, with Organization and Customer
protected:

| Ancestor | Read, full cascade | Write, full cascade | Read, nearest only | Write, nearest only |
|---|---|---|---|---|
| Organization | `view` | `view` | resolved, no permission check | resolved, no permission check |
| Customer | `view` | `change` | `view` | `change` |
| Address | resolved, no permission check | resolved, no permission check | resolved, no permission check | resolved, no permission check |

Every column resolves all three ancestors and validates the whole relationship chain. Nearest-only mode skips
permission checks, not lookups. A denial at the nearest gate is final: a grant on a farther ancestor never
substitutes for it. With an all-`"none"` ancestry no ancestor permission is checked, but existence and
relationships still are.

### Operations: Read, Write and exact actions

Which pair applies is decided by the endpoint's class, never by its key, its HTTP method or its own
`cv_permission`:

| Endpoint | Pair |
|---|---|
| list, card list, detail, `ObjectDetailView`, polymorphic detail, `RedirectChildView`, manage | Read (`view`/`view` by default) |
| create, update, delete (GET included), polymorphic create, update and delete, polymorphic type selection, ordered up/down | Write (`change`/`view` by default) |
| formset fragment requests | the pair of the editor that owns them |
| generic `ActionView`, custom form views, workflow views, any other custom endpoint | an exact `actions` entry is required when nested |

Opening a create, update or delete form is already a Write. Deleting a Book needs Publisher `change` by default,
not Publisher `delete`. Subclasses and renamed keys keep their family. A generic action does not become Read
because it is registered as `detail` or because its `cv_permission` is `"view"`.

An `actions` entry uses the endpoint's literally registered key. A `CardListView` registered as `card` takes
`actions["card"]`. `actions["list"]` is an error unless an endpoint is registered as `list`, even though list
navigation falls back to the card view. When both are registered, each entry applies only to its own endpoint.
Top-level custom endpoints need no entry, and a top-level ViewSet rejects a nonempty `actions`.

### Example: permissions for a nested Book ViewSet

A Book ViewSet under a core Publisher ViewSet, with one custom action. The comments name the ancestor
requirement of each endpoint under the default settings:

```python
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    UpdateViewPermissionRequired,
)

from myapp.models import Book, Publisher

cv_publisher = ViewSet(model=Publisher, name="publisher")  # Publisher's own views are omitted here

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="publisher"),
    ancestor_policy=AncestorPolicy(
        # "approve" is a generic action: nested, it needs a complete pair of its own
        actions={"approve": AncestorPermissions(nearest="change", higher="view")},
    ),
)


class BookListView(ListViewPermissionRequired):  # Read: Publisher view
    cv_viewset = cv_book
    cv_list_actions = ["detail", "update", "delete", "approve"]


class BookDetailView(DetailViewPermissionRequired):  # Read: Publisher view
    cv_viewset = cv_book


class BookUpdateView(UpdateViewPermissionRequired):  # Write: Publisher change, also for GET
    cv_viewset = cv_book
    fields = ["title"]  # no publisher field: this form cannot move a book to another publisher


class BookDeleteView(DeleteViewPermissionRequired):  # Write: Publisher change, not Publisher delete
    cv_viewset = cv_book


class BookApproveView(ActionViewPermissionRequired):  # actions["approve"]: Publisher change
    cv_viewset = cv_book
    cv_key = "approve"
    cv_path = "approve"
    cv_permission = "change"
    cv_icon_action = "fa-solid fa-check"
    cv_action_label_template_code = "Approve"
    cv_action_short_label_template_code = "Approve"

    def action(self, context) -> bool:
        # record the approval of self.object here
        return True
```

What each user needs, with both gates applied:

| Request | Ancestor gate | Endpoint's own gate |
|---|---|---|
| Book list or detail | `view` on Publisher (model permission) | `view` on Book |
| Book update, delete or approve, GET and POST | `change` on Publisher | `change` or `delete` on Book |

A Book editor therefore usually holds Publisher `view` (to read the list) and Publisher `change` (to edit). A
user with every Book permission but no Publisher permission gets 403 on all of these URLs. A user with Publisher
`change` but no Book `change` still gets 403 from the update view's own gate.

### Configuration errors

Mistakes are reported as early as they can be decided, and never turn into weaker access:

| Mistake | Reported |
|---|---|
| unknown field or provider, incomplete pair, empty or padded key, non-boolean `cascade` / `accept_global_perms` | Pydantic `ValidationError` when the value is built |
| `provider="guardian"` on a core `ViewSet`; `accept_global_perms=True` without a Guardian provider | `ValidationError` when the ViewSet is constructed, before it is registered |
| `cascade`, `read`, `write` or a nonempty `actions` on a top-level ViewSet | `ValidationError` naming the ineffective fields (explicit `None` / `{}` stay valid) |
| an incomplete or invalid global setting | `ValidationError` at startup |
| an `actions` key that is not a registered view key | system check `viewset.E267`; `ImproperlyConfigured` at the request |
| a nested generic action, custom form, workflow or other custom endpoint without its `actions` entry | system check `viewset.E268`; `ImproperlyConfigured` at the request, in both cascade modes and with all-`"none"` ancestry |
| an ancestry cycle, an unregistered parent or a relationship that is not one supported field | system check `viewset.E266`; `ImproperlyConfigured` at URL construction and at the request |
| a Resource used as a parent | system check `viewset.E261` |
| a required key missing from the permission map of a checked ancestor | `ImproperlyConfigured` when that gate is reached |

A child ViewSet may still name a parent that is registered later; the reference must resolve by the time URLs
are built. Structural checks read declarations and model metadata only, never the database.

### Request order and responses

A nested request runs these steps, in this order, before the endpoint's own work:

1. **Static validation**, without any database access: the declared ancestry and relationships, the action
   declarations, the operation's pair and the ancestors to check.
2. **Actor admission**, before any ancestor is looked up. If at least one ancestor is protected, an anonymous
   user gets the endpoint's anonymous response (the login redirect, also for plain views; a Guardian view's
   configured `cv_guardian_anonymous_behavior`), and an authenticated inactive user, superuser included, gets
   403. With all-`"none"` ancestry only the endpoint's own early rules apply.
3. **Ancestors, outermost first.** Each ancestor is loaded through its ViewSet queryset, restricted to its URL
   primary key and to the ancestor already resolved above it. A missing, filtered-out or mismatched ancestor is
   404. A checked ancestor's gate runs right after its lookup, before the next deeper lookup; a denial is 403.
4. **The endpoint itself**: its own permission, the child object or list, action state, Resource loading,
   forms, formset fragments, hooks and writes.

An outer denial therefore hides everything below it: a missing deeper ancestor is never probed after a denied
gate. Authorization does not guarantee success: a missing child, a disabled action or an invalid form still
answers as before.

### Ancestor querysets and the resolved parent

Each ancestor is loaded with `ancestor_viewset.get_queryset(view)`, where `view` is the requested child view
(its request, user and URL kwargs). Put visibility rules that every descendant must respect, such as soft
deletion or tenant scope, into an override of the ancestor **ViewSet's** `get_queryset`. A row that override
excludes is a 404 for every descendant, even for a user with a grant. A `get_queryset` override on one of the
ancestor's *views* (its list or detail view) is not used, and no ancestor view is dispatched.

On success the resolved ancestors are kept for this request only. `cv_get_parent_object()`, the
`CreateViewParentMixin` attachment, parent-based action state checks and the shipped parent helpers reuse the
resolved immediate parent: the same row, primary key and database. That holds even when the immediate parent
is `"none"` and a farther ancestor carried the nearest gate. Nothing is cached across requests, so a revoked
grant applies to the next request.

The child is checked against that parent where it is consumed. A child object reached through a `get_queryset`
override that forgot the parent filter is 404 unless it belongs to the URL parent, and a nested list renders
only that parent's children.

### Databases

Nested ViewSets support only the `default` database for their ancestor lookups, their own ORM querysets and
objects, their writes and the authorization records their checks read. A nondefault selection — an explicit
`.using()`, a router answer, an instance hint or a `cv_get_db_alias()` override — raises `ImproperlyConfigured`
where it is reached, before that consumer runs. Nothing is rerouted: the selection is neither stripped nor
forced to `default`. An explicit `.using("default")` is fine. Top-level ViewSets keep their routed behavior, and
a Resource leaf's own loading stays application-owned.

Nested writes select their database with the resolved object as the router's instance hint, so a router that
answers differently for one instance is refused before any hook or write. See
[Nested ViewSets: instance-hinted write routing](request_lifecycle.md#nested-viewsets-instance-hinted-write-routing)
for the executed router example, and the [migration guide](../migrating-1.0.md) for upgrading.

### Resource leaves

A Resource ViewSet may be the leaf of an ORM chain. Its ORM ancestors are authorized before
`cv_get_items()` / `cv_get_item()` run; restricting the rows to the URL parent remains the job of those loaders.
A Resource cannot be an ancestor. See
[Ancestor authorization of a Resource leaf](resources.md#ancestor-authorization-of-a-resource-leaf).

### What URL-path authorization does not cover

Passing the ancestors authorizes the path in the URL, not every effect of the request. Assuming all gates pass
and the form is valid:

| Operation | Outcome |
|---|---|
| update a Genre shared by Publishers A and B, through A | the shared row changes for both; B is not checked |
| update a Book through Publisher A with an editable `publisher` field set to B | the Book moves to B; nothing checks B, and the field is not pinned |
| delete an object shared with another parent | ordinary deletion, not unlinking from A |
| a custom action that changes other objects | its pair covers the URL path only; the action authorizes its other effects itself |

Restrictions like these belong to the application. The example above leaves `publisher` out of
`BookUpdateView.fields`, so its form cannot move a Book. Other options are a separate move operation with its own
authorization, or object permissions and domain rules on shared rows. Full cascade means the higher ancestors on
this URL path, not every parent an object belongs to.

### Visible links and buttons

Request enforcement is authoritative. Buttons and links check at most the immediate parent (its provider and the
target's nearest key); they do not evaluate farther ancestors. A visible link can therefore lead to a 403 from
a higher ancestor, and with a `"none"` immediate parent the link stays visible while the request is denied
further up. The manage page shows the declared policy, not whether a user can pass it.

## See also

- [`examples/bootstrap5/nested/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/nested) — the full three-level example app these snippets are drawn from
- [Context Buttons](context_buttons.md) — `ParentContextButton`, `ChildContextButton`, `SiblingContextButton` in full
- [Breadcrumb](breadcrumb.md) — renders the same parent chain as a Bootstrap breadcrumb
