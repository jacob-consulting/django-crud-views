# Nested ViewSets (parent/child)

[ViewSet Navigation](navbar.md) can reuse an owner's identity and section links across selected descendant pages,
including grandchildren. Link visibility is bounded; the destination still enforces the ancestor policy below.

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

The create page's header can name the parent from the URL through `{{ parent_object }}` in
`cv_header_template_code`:

```python
class DepartmentCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_department
    form_class = DepartmentForm
    cv_header_template_code = _("New department for {{ parent_object }}")
```

This costs no extra query on the dispatched request, because the header reuses the resolved immediate parent the
ancestor guard kept for that request (see [the resolved parent](#ancestor-querysets-and-the-resolved-parent)).
[Snippet variables](templates.md#snippet-variables) lists everything a snippet can use.

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

## Labels

The nested Book ViewSet under an author in the Sideways example and a top-level ViewSet on the same `Book` model
both default to the model's `Meta.verbose_name` / `verbose_name_plural`. Every default label that includes the object
name — header, paragraph, full action label, message, breadcrumb container item, `LinkChildColumn` cell and
`ChildContextButton` label — therefore uses the same names. The optional ViewSet fields `verbose_name` and
`verbose_name_plural` rename these defaults in one place. Short labels such as `List` or `Delete` carry no object name
and are unchanged; an explicit `label_template_code` or `cv_*_template_code` still wins.

Add the two arguments to the Sideways `cv_book` declaration above, replacing it with this version. A ViewSet `name`
registers once: declaring a second ViewSet with `name="book"` would be rejected at registration.

```python
from django.utils.translation import gettext_lazy as _

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
    verbose_name=_("title"),
    verbose_name_plural=_("titles"),
)
```

- Each field is resolved independently: setting only `verbose_name_plural` leaves the singular at the model's name.
  There is no automatic plural.
- `None` (the default) means unset. A set value is stored as given, with no stripping or normalisation. `get_meta()`
  applies `capfirst()` and builds the `*_translate` variants from the resolved value; a `gettext_lazy` override is
  translated per request.
- Per-view `cv_*_template_code` (header, paragraph, action label, message), `cv_breadcrumb_container_label` and
  `cv_breadcrumb_label_template_code` still win over the ViewSet default.
- In the Down example, `LinkChildColumn(verbose_name=...)` sets the table column header only. The cell's link text
  and its `Go to …` title come from the child ViewSet's `verbose_name_plural`. A `ChildContextButton` or
  `SiblingContextButton` with its own `label_template_code` still wins; without one, it uses the target ViewSet's
  labels.
- Model-centric text keeps the model's names: the deletion summary of protected and cascaded objects, and the 404
  messages for a missing parent or Resource item. Permission codenames are untouched.
- A plain string that is empty or whitespace-only raises `ValidationError` when the ViewSet is constructed. Lazy
  values are accepted without a blank check because they cannot be evaluated while apps load.
- For a Resource-based ViewSet, the override beats `Resource.Meta.verbose_name` / `verbose_name_plural` — see
  [Resource Meta](resources.md#defining-a-resource). `GuardianViewSet` and polymorphic ViewSets inherit the fields too.

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
| a required key missing from the permission map of a checked ancestor | system check `viewset.E269` when the nested ViewSet and that ancestor are both core ViewSets (the key is resolved against the ancestor model's declared `Meta` permissions); `ImproperlyConfigured` when that gate is reached (Resource leaves and Guardian ViewSets are not checked) |

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

For a denial, start with [cv_access](manage.md#cv_access) or the opt-in [Access check](manage.md#access-check).
The trace shows ordered ancestors and the first deciding failure; later gates remain not reached. It does not
probe deeper objects after an outer denial or grant new authority to the viewer. Project overrides are opaque
[custom method boundaries](manage.md#custom-method-boundaries), not proven inner culprits.

Trace [list counts](manage.md#list-count-boundary) precede context-time parent scoping. An override omitting the parent filter
can report more rows than the rendered parent-scoped list; default ViewSet querysets already include that filter.
Separately, the nested-list database check happens during page construction and is not evaluated by a trace.
These are different boundaries: count adjustment neither builds the page nor validates its database selection.
See all [diagnostic limits](manage.md#diagnostic-limits), including delete preview, submit-time writes and middleware.

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

Both checks need the resolved parent, so they only work once the guard has run. A mixin placed before the
view's crud-views base that loads the child object or list in `dispatch()` before calling `super().dispatch()`
gets `ImproperlyConfigured` instead of an unscoped object or list. For example, `UserPassesTestMixin` with a
`test_func` that calls `get_object()`. Calling `cv_get_parent_object()` that early does not authorize
ancestry: it looks the parent up by its URL primary key, without the ancestor ViewSet's `get_queryset` and
without a gate. Do this kind of work after `super().dispatch()`, or in the view's own methods.

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
for the executed router example, and
[Nested write database selection](../migrating-1.0.md#nested-write-database-selection) for upgrading.

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

Context/parent/sibling buttons, view-key actions and table rows, card own/child actions, navbar items,
the permission filter, core/Guardian Cancel and bulk toolbar use the shared private link check, with the bounded
parent-only Guardian Cancel own-hook omission below. Nested targets check
the immediate parent and known higher ancestors under the destination's policy, then own permission, then state.
Permission denial skips state; the permission-only filter never calls it. Object targets pass their own object
to `cv_has_access`; list/create targets pass `None`. State receives the own object, immediate parent for a nested
list/create, or `None` for a top-level collection. The parent owns the provider and `accept_global_perms` policy: core
parents use model permissions; Guardian parents use object/group grants with model fallback only when that
parent's `AncestorPolicy(accept_global_perms=True)` allows it. `provider="none"` bypasses only this parent gate.
Guardian collections, including standalone queryset-only compositions, check their declared immediate-parent
policy and known higher ancestors. Guardian create runs these gates before `cv_create_has_access`; the default
hook deliberately repeats its bounded immediate-parent check. All nested Guardian links require a signed-in,
active actor even under unprotected ancestry, before any create override. See
[Guardian collection links](guardian.md#parent-to-child-collection-links).

A user with Book `view` and Publisher `change`, but without Publisher `view`, can open Publisher update while
the default Books list GET returns 403. Both child renderers now hide or disable that Books control according
to the destination's setting, with no usable disabled URL. Grant Publisher `view` and the same parent's empty
Books collection is accessible. Custom own denials and action-state policy still apply; state is asked only
after permission passes. Nested Guardian create links use `cv_create_has_access` for their parent permission.

With default policies, parent `view` without `change` also removes child update/delete/create links and the bulk
toolbar; their destination requests already return 403. For a child control its URL's object/row supplies the
immediate parent; other known objects come from guard state and are aligned to the actual target. Unknown
levels stay `None`, unchecked, without shifting farther objects into them. Rendering performs no ancestor
or membership lookup. Missing immediate-parent state denies, including on unguarded create/form pages,
Resource leaves, non-CRUD views and direct calls. Cancel alone uses the existing parent-hook resolver:
guarded requests reuse the parent without SQL; an unguarded view retains its one lookup. Built-in missing rows
mean unavailable, while custom-hook exceptions propagate. Higher Cancel ancestors come only from guard state.
Core create state and parent-button objects now use guard state; put shared annotations/scope in the parent
ViewSet's `get_queryset()`, not a view's `cv_get_parent_object()` override.

Each eligible plain child link invokes its immediate-parent policy plus reached higher gates, not necessarily
one SQL query per gate. Historical stage-2 child cases, remeasured for stage 3a on Python 3.12.3 / Django 6.0.10 /
django-guardian 3.5.2, give 6/4/2/0 SQL queries with a plain parent and 8/6/4/2 with a strict Guardian parent, for both
renderers in fresh-cold/warm-cold/fresh-warm/warm-warm Django model-cache/vocabulary states. These first-load
figures match the earlier historical Django 5.2/Guardian 3.5 totals. Each measured layer fetches a fresh user;
a warm Django model cache does not mean loaded Guardian grants. Repeated links on the same Python user reuse
the same parent's loaded grants, while distinct parents have separate loads and destination permission/state
decisions remain independent. See the canonical
[measurement conditions and permission cost](context_buttons.md#permission-cost-and-configuration-failures) and
[Guardian grant lifetime](guardian.md#object-grant-lifetime), including retained users and normal fresh requests.

Parent-policy configuration errors propagate as `ImproperlyConfigured` during host rendering: a required key
missing from the parent's permission map, a nested operation without requirements, or reached authorization
records routed away from `default`. The parent gate runs before own access, so malformed policy raises even
for an actor whose own access is denied; `provider="none"` retains its early
helper bypass before these validations. These failures are not ordinary hidden/disabled denials.

These historical two-level costs do not measure stage 3b; the linked stage-3a record separates gate calls,
permission SQL and Cancel's parent lookup. Normal requests still receive fresh Python users/checkers.

Request enforcement remains authoritative for unknown levels and membership. Guardian object/list/create
Cancel now checks known higher ancestors with its actor rule and composition validation intact. Parent-only
non-create Cancel omits `cv_has_access`, including custom overrides, but checks actor, higher/immediate gates
and state. Ordinary links still ask that own hook: a `PermissionRequired` base can hide a link whose request
allows because it asks child model permission; a plain base follows its ordinary own hook. See the
[bounded parent-only limitation](guardian.md#parent-only-non-create-limitation).
Navbar child items already used aligned ancestors on every page; page create controls now apply the same
known higher gates. Each button follows its actual target without a key rewrite. See
[known ancestry and Cancel](guardian.md#known-ancestry-and-cancel).
A visible link can still lead to 403 or a queryset-based 404; URL construction proves no authorization. No
request response or login redirect changes, public checker, or public ancestor accessor are introduced.
The manage page shows declared policy, not whether a user can pass it.

## See also

- [`examples/bootstrap5/nested/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/nested) — the full three-level example app these snippets are drawn from
- [Context Buttons](context_buttons.md) — `ParentContextButton`, `ChildContextButton`, `SiblingContextButton` in full
- [Breadcrumb](breadcrumb.md) — renders the same parent chain as a Bootstrap breadcrumb
