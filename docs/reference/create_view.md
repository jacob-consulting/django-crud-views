# CreateView

The `CreateView` handles creating new model instances. It uses Django's form handling
and integrates with [django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/)
for form layout.

## Basic Usage

```python
from crispy_forms.layout import Row
from django.utils.translation import gettext as _
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin
from crud_views.lib.views import CreateViewPermissionRequired, MessageMixin
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(
    model=Author,
    name="author",
    pk=ViewSet.PK.UUID,
    icon_header="fa-regular fa-user",
)


class AuthorCreateForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    form_class = AuthorCreateForm
    cv_viewset = cv_author
    cv_message = "Created author »{object}«"
```

## View Classes

| Class | Description |
|-------|-------------|
| `CreateView` | Base create view without permission checks |
| `CreateViewPermissionRequired` | Create view with `add` permission required |

Both inherit from Django's `generic.CreateView` and `CrudView`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | from `cv_viewset` | The Django model to create (auto-derived from ViewSet) |
| `form_class` | `Form` | — | The form class for the create form |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success |
| `cv_context_actions` | `list[str]` | `["home"]` | Actions shown in the header area |

## Form Classes

### CrispyModelForm

Base class for model forms with crispy-forms layout support:

```python
class AuthorCreateForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))
```

| Attribute | Description |
|-----------|-------------|
| `submit_label` | Text for the submit button |
| `get_layout_fields()` | Return crispy-forms layout fields |

### Layout Helpers

| Helper | Description |
|--------|-------------|
| `Column2` | Column spanning 2 of 12 grid units |
| `Column4` | Column spanning 4 of 12 grid units |
| `Column8` | Column spanning 8 of 12 grid units |
| `Column12` | Full-width column |

## Messages

Add `MessageMixin` to show a success message after creation:

```python
class AuthorCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    form_class = AuthorCreateForm
    cv_viewset = cv_author
    cv_message = "Created author »{object}«"
```

The `{object}` placeholder is replaced with the string representation of the created instance.

## Creating Child Objects

When the model has a ForeignKey to a parent, use `CreateViewParentMixin` to automatically
set the parent reference:

```python
from crud_views.lib.views import CreateViewParentMixin

class BookCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    form_class = BookCreateForm
    cv_viewset = cv_book
```

The `CreateViewParentMixin` reads the parent object from the URL and assigns it to the
form instance before saving. The ViewSet must be configured with a `ParentViewSet`:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet

cv_book = ViewSet(
    model=Book,
    name="book",
    pk=ViewSet.PK.UUID,
    parent=ParentViewSet(name="author"),
)
```

## Form Processing Hooks

The `CrudViewProcessFormMixin` provides hooks for customizing form processing:

| Hook | Description |
|------|-------------|
| `cv_post_hook(context)` | Called at the start of POST processing |
| `cv_form_is_valid(context)` | Override to add custom validation |
| `cv_form_valid(context)` | Called when the form is valid (saves the instance) |
| `cv_form_valid_hook(context)` | Called after `cv_form_valid` (used by `MessageMixin`) |
| `cv_form_invalid(context)` | Called when the form is invalid |
| `cv_form_invalid_hook(context)` | Called after form invalid handling |
