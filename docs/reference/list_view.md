# ListView

The `ListView` displays a list of model instances. It integrates with
[django-tables2](https://django-tables2.readthedocs.io/en/latest/) for table rendering and
[django-filter](https://django-filter.readthedocs.io/en/stable/) for filtering.

!!! example "Try it live"
    The [Library example](https://django-crud-views-demo.onrender.com/library/author/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## Basic Usage

A minimal list view with a table:

```python
import django_tables2 as tables
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import ListViewTableMixin, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(
    model=Author,
    name="author",
    icon_header="far:user",
)


class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()


class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author
```

## View Classes

| Class | Description |
|-------|-------------|
| `ListView` | Base list view without permission checks |
| `ListViewPermissionRequired` | List view with `view` permission required |

Both inherit from Django's `generic.ListView` and `CrudView`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | from `cv_viewset` | The Django model to list (auto-derived from ViewSet) |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_list_actions` | `list[str]` | `["detail", "update", "delete"]` | Actions shown per row in the table |
| `cv_context_actions` | `list[str]` | `["parent", "list", "filter", "create"]` | Actions shown in the header area |
| `paginate_by` | `int` | `10` | Number of items per page |

### Customizing List Actions

Control which action buttons appear per row:

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down"]
```

## Table with django-tables2

Use `ListViewTableMixin` to render the list as a table. Define a table class
using `Table` (which extends django-tables2's `Table`):

```python
import django_tables2 as tables
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkChildColumn
from crud_views.lib.table.columns import NaturalTimeColumn, NaturalDayColumn


class AuthorTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column(attrs=Table.ca.w20)
    books = LinkChildColumn(name="book", verbose_name="Books", attrs=Table.ca.w10)
    created_dt = NaturalDayColumn()
    modified_dt = NaturalTimeColumn()
```

### Column Types

| Column | Description |
|--------|-------------|
| `UUIDLinkDetailColumn` | UUID primary key rendered as a link to the detail view |
| `LinkDetailColumn` | Integer primary key rendered as a link to the detail view |
| `LinkChildColumn` | Link to a child ViewSet's list view |
| `NaturalDayColumn` | Date rendered as natural day (e.g. "today", "yesterday") |
| `NaturalTimeColumn` | DateTime rendered as natural time (e.g. "2 hours ago") |

### Pagination

The table (`crud_views/table/bootstrap5.html`) and the [card list](card-list-view.md)
(`crud_views/snippets/pagination.html`) paginate with the same accessible markup:

- The `<nav>` carries the translated `aria-label` from the `pagination` msgid.
- The arrows are the `page-previous` and `page-next` [icons](icons.md#default-table), rendered as decorative
  standalone icons. Each arrow has a translated hidden label, `previous` or `next`, placed after the previous icon
  and before the next icon.
- The current page is a `<span class="page-link">` inside an `li` with `aria-current="page"`, not a link.
- A direction with no page is still rendered, as `<a class="page-link" aria-disabled="true">` with no `href`; it can
  be neither followed nor focused. The table's `...` range items use the same disabled markup.

The hidden labels take their class from the `pagination:hidden-label` key of the
[class table](buttons.md#the-class-table) (default `visually-hidden`). One setting restyles both components:

```python
CRUD_VIEWS_BUTTON_CLASSES = {"pagination:hidden-label": "sr-only"}
```

To change the arrows, map `page-previous` and `page-next` in [`CRUD_VIEWS_ICONS`](icons.md#crud_views_icons); no
template override is needed. Pagination queries, prefixes and ranges are unchanged. Table links replace only the
table's own prefixed page parameter (`table.prefixed_page_field`) through `{% cv_querystring %}` and keep every
other query value. A table `prefix` keeps several tables on one page apart. The range still comes from
django-tables2's `table_page_range` (`DJANGO_TABLES2_PAGE_RANGE`).

A theme that overrides the table's `pagination.previous` or `pagination.next` block must handle the disabled end
in that block too. See [Table pagination overrides](../migrating-1.0.md#table-pagination-overrides).

## Filtering with django-filter

Add `ListViewTableFilterMixin` and configure a filter set and form helper:

```python
import django_filters
from crispy_forms.layout import Layout, Row
from crud_views.lib.crispy import Column4
from crud_views.lib.views import ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired
from crud_views.lib.views.list import ListViewFilterFormHelper


class AuthorFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(
        Row(Column4("first_name"), Column4("last_name")),
    )


class AuthorFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Author
        fields = ["first_name", "last_name"]


class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author

    # filter config
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
```

### Custom filter helpers

`AuthorFilterFormHelper` above declares only the filter fields. `ListViewFilterFormHelper` appends the Apply and
Reset buttons after them, once per form, as a crispy `FormActions` group. Each helper instance renders its own copy of
the class-level `layout`, so neither the class nor other instances ever collect buttons; a layout you assign to
`helper.layout` later is copied the same way. The copy is a `copy.deepcopy`, so the layout and every object in it
must be deep-copyable; a member that is not (a lock, an open resource, a layout object with `__slots__` that cannot
be copied) raises a `TypeError` naming the helper class when the helper is created (for an assigned layout, when it
next renders). A helper without a `layout`
renders every field of the filter form, then the buttons.

The hidden `sort`, order and direction inputs that keep the table sort or card order across a filter submit are
crispy inputs (`add_input()`). They render in the template pack's inputs wrapper after the visible buttons, with
unchanged names and values.

The buttons come from the hook `get_form_actions()`, like on `CrispyFormMixin`. Return another `FormActions` to replace
them, `FormActions()` to keep an empty group, or `None` for no group at all:

```python
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Layout, Row
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column4, Submit
from crud_views.lib.views.list import ListViewFilterFormHelper


class SearchFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("first_name"), Column4("last_name")))

    def get_form_actions(self):
        # one button only; the filter kind gives it the filter-submit classes and icon
        return FormActions(Submit("submit", _("Search"), css_id="filter-button", slot="form:filter-submit"))
```

#### Removing the filter buttons

Before 1.0 the Apply and Reset buttons were helper inputs, so clearing `self.inputs = []` (or `helper.inputs = []`)
after construction removed them. They are layout buttons now: clearing the inputs leaves Apply and Reset in place
and removes only the hidden sort, order and direction inputs (and any input you added), so a filter submit then
drops the active sort as well. Nothing warns about it. Override `get_form_actions()` to return `None` and leave the
inputs alone:

```python
from crispy_forms.layout import Layout, Row

from crud_views.lib.crispy import Column4
from crud_views.lib.views.list import ListViewFilterFormHelper


class NoButtonsFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("first_name"), Column4("last_name")))

    def get_form_actions(self):
        return None  # no Apply / Reset; the fields and the hidden sort / order / direction inputs stay
```

The helper keeps its fields, its constructor and its hidden inputs. A helper whose `layout` is an empty `Layout()` and
whose hook returns `None` renders nothing of its own; crispy then falls back to rendering every field of the form.

#### Buttons added with `add_input()`

A custom helper that adds its own buttons with `add_input(Submit(...))` keeps rendering them as before: they stay
crispy inputs in the template pack's inputs wrapper, with their old markup, and get no label mode or icon. No check or
warning reports this. To give such a button the form-button leaf ([Forms](buttons.md#forms)), return it from
`get_form_actions()` instead of adding it as an input; keep hidden inputs as inputs.

### Filter Persistence

Filter values are stored in the user session by default, so the filter state is preserved
when navigating away and back. Control this with:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `cv_filter_persistence` | `bool` | `True` | Store filter state in session |

This can also be configured globally via the `CRUD_VIEWS_FILTER_PERSISTENCE` setting.

### Always-visible (pinned) filter

By default the filter is collapsed and opened via the filter toggle button. Set
`cv_filter_pinned = True` on a filtered view to render the filter **always open** and
hide the toggle button entirely:

```python
class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    filterset_class = AuthorFilter
    cv_filter_pinned = True
```

The default comes from the `CRUD_VIEWS_FILTER_PINNED` setting (default `False`). Filter
field values are still persisted to the session when `cv_filter_persistence` is enabled;
only the (now irrelevant) expanded/collapsed state is dropped. Applies equally to
[CardListView](card-list-view.md).

---

> To disable an action the user *is* permitted to perform, based on object state
> (e.g. a locked/open parent), see [Conditionally disabling an action](action_enabled.md).

!!! tip "Many actions?"
    Fold the less common actions into a `⋯` dropdown: see [Action menus](action_menus.md).
