# Nested ViewSets (parent/child)

A child ViewSet can declare a parent ViewSet. Once declared:

- the child's URLs are nested under the parent's URL (`parent_prefix/<parent_pk>/child_prefix/...`)
- the child's querysets are automatically filtered to the current parent object
- create views can auto-set the parent foreign key with `CreateViewParentMixin`
- context buttons can jump up (`parent`), down (`ChildContextButton`), or sideways
  (`SiblingContextButton`) across the hierarchy

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
    cv_message_template_code = "Created department »{{ object }}«"
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
    departments = LinkChildColumn(name="department", verbose_name="Departments", attrs=Table.ca.w10)
    offices = LinkChildColumn(name="office", verbose_name="Offices", attrs=Table.ca.w10)
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
    context_buttons=context_buttons_default() + [
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
    context_buttons=context_buttons_default() + [
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
