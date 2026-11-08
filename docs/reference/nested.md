# Nested ViewSets (parent/child)

A child ViewSet can declare a parent ViewSet. Once declared:

- the child's URLs are nested under the parent's URL (`parent_prefix/<parent_pk>/child_prefix/...`)
- the child's querysets are automatically filtered to the current parent object
- every request to the child first authorizes its ancestors: they must exist, belong together, and grant the
  required permissions (see [Ancestor authorization](ancestor_authorization.md))
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
| `many_to_many_through_attribute` | `str \| None` | `None` | For a `ManyToMany` parent relation: the parent-side end of the same relation (optional) |

Set `attribute` when the `ForeignKey` field name doesn't match the parent's registry name;
set `pk_name` only if the default URL kwarg name would collide with another kwarg.

For a `ManyToMany` parent, `attribute` names the child's relation (either end) whose related model is the parent
model. `many_to_many_through_attribute` may be omitted; when set, it must be the other end of that same relation.
Relationships are validated by system check `crud_views.E320` and before URLs are built: an unknown parent, a cycle,
or a field that does not lead to the parent model is a configuration error.

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

## Ancestor authorization

A nested request is authorized along its whole URL before the child view does any work. With the defaults:

| Request to `Employee` (`company/<company_pk>/department/<department_pk>/employee/...`) | Required on Department (nearest) | Required on Company (higher) |
|---|---|---|
| List, detail (Read) | `view` | `view` |
| Create, update, delete, including the form GET (Write) | `change` | `view` |

Core ViewSets check model permissions; a `GuardianViewSet` ancestor checks object permissions. A missing ancestor,
one hidden by its ViewSet's `get_queryset()`, or a `department_pk` that does not belong to `company_pk` is a 404;
a missing permission on a checked ancestor is a 403. The child view's own permission (for example
`CreateViewPermissionRequired`'s `add`) is checked afterwards and independently.

Configure it per ViewSet with `ancestor_policy`:

```python
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet

cv_office = ViewSet(
    model=Office,
    name="office",
    parent=ParentViewSet(name="company"),
    # writes to offices need only "view" on the company
    ancestor_policy=AncestorPolicy(write=AncestorPermissions(nearest="view", higher="view")),
)
```

`AncestorPolicy(provider="none")` on a ViewSet removes its permission gate when it is an ancestor (its existence and
relationship are still checked), and `AncestorPolicy(cascade=False)` on a nested ViewSet checks only the nearest
protected ancestor for its requests. A nested custom endpoint (`ActionView`, `CustomFormView`, `WorkflowView`, ...)
must declare its pair under `actions`. Global defaults are [settings](settings.md#ancestor-authorization). The full
contract, including Resource leaves, manage pages, databases and the mutation boundary, is in
[Ancestor authorization](ancestor_authorization.md).

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

## See also

- [`examples/bootstrap5/nested/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/nested) — the full three-level example app these snippets are drawn from
- [Context Buttons](context_buttons.md) — `ParentContextButton`, `ChildContextButton`, `SiblingContextButton` in full
- [Breadcrumb](breadcrumb.md) — renders the same parent chain as a Bootstrap breadcrumb
- [Ancestor authorization](ancestor_authorization.md) — how nested requests authorize their ancestors
