# Part 2 — The list view

With the `Author` model and its `ViewSet` in place ([Part 1](tutorial-1-setup.md)),
let's finish the list view. `ListViewTableMixin` gives you a sortable table,
pagination, and permission-gated action buttons (detail/update/delete) for
free — you supply the table columns and django-crud-views handles the rest.

## The table

`Table` extends django-tables2's `tables.Table`. Here's `AuthorTable`:

<!-- cv-sync: library/views.py -->
```python
class AuthorTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()
```

Three plain columns, plus `id`, which uses `UUIDLinkDetailColumn` instead of a
regular column: it renders the primary key as a link to the row's detail
view, and `attrs=Table.ca.ID` attaches the standard column attributes
(alignment, width) crud_views uses for identifier columns. If your model has
an integer or slug primary key instead, use `LinkDetailColumn` — the
non-UUID equivalent — in the same spot.

## The view

For now, the list view just needs `table_class`:

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    table_class = AuthorTable
```

This is enough to browse and sort authors. We'll add filtering — search
boxes above the table — in Part 5; the final version of this view lands
there.

## Permissions

`ListViewPermissionRequired` is Django's `generic.ListView` combined with
`PermissionRequiredMixin`: visiting the list view requires the `view`
permission on `Author`. This is the mapping every crud_views operation
follows:

| Operation | Django permission |
|-----------|--------------------|
| list, detail | `view` |
| create | `add` |
| update | `change` |
| delete | `delete` |

To try this out, either create a Django superuser (`python manage.py
createsuperuser`) and log in, or run the bundled example project (`task
run` from `examples/bootstrap5/`) and log in as the demo user `alice` /
`alice`, who already has `view`/`add`/`change`/`delete` on `Author`.

## Seed some data

If you're following along in your own project rather than the bundled
example, create an author from the shell so there's something to see:

```bash
python manage.py shell -c "
from library.models import Author
Author.objects.create(first_name='Ursula', last_name='Le Guin')
"
```

Visiting the list URL now shows a sortable, paginated table of authors:

![Author list view](assets/tutorial-author-list.png)

Next: [Part 3 — Create, update, delete](tutorial-3-forms.md)
