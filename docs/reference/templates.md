# Base template

Every crud_views frontend template renders `{% extends cv_extends %}`, where
`cv_extends` is resolved per view. This lets you control which base template
your CRUD pages extend — globally, per ViewSet, or per view.

## Resolution order

`cv_extends` is resolved from the first of these that is set:

1. **View** — `cv_extends_template` on the `CrudView` subclass
2. **ViewSet** — `extends` on the `ViewSet`
3. **Global** — the `CRUD_VIEWS_EXTENDS` setting (required; final fallback)

### Per ViewSet

Set it once and every view in the ViewSet inherits it:

```python
cv_author = ViewSet(
    model=Author,
    name="author",
    extends="myapp/author_base.html",
)
```

### Per view

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_extends_template = "myapp/author_list_base.html"
```

### Shared base via a mixin

To share a base across several ViewSets (or vary it within one), put it on a
mixin and inherit:

```python
class MySpecialBase(CrudView):
    cv_extends_template = "myapp/special_base.html"

class FooListView(MySpecialBase, ListView):
    ...
```

!!! warning "The override template must be a real base template"
    The template named by `cv_extends_template` / ViewSet `extends` is itself
    the base that crud_views extends. It **MUST NOT** contain
    `{% extends cv_extends %}` (nor otherwise re-extend `cv_extends`) — that
    makes the template extend itself and raises
    `django.template.exceptions.TemplateDoesNotExist`.

    Point the override at a normal base template — one that extends your own
    site base (e.g. `{% extends "base.html" %}`) or none at all.

## Validation

If a ViewSet `extends` or a view `cv_extends_template` names a template that
cannot be loaded, Django's system checks report it at startup
(`crud_views.viewset.E111`).
