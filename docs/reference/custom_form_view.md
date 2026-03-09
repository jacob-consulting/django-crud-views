# CustomFormView

The `CustomFormView` provides a custom form attached to an existing model object. Use it when you need a form that operates on an object but does not follow the standard create/update/delete pattern — for example, a contact form, an approval action, or a send-message action.

## View Classes

| Class | Description |
|-------|-------------|
| `CustomFormView` | Object-based custom form view (no permission check) |
| `CustomFormViewPermissionRequired` | Object-based custom form view with `view` permission required |
| `CustomFormNoObjectView` | Non-object-based custom form view (no permission check) |
| `CustomFormNoObjectViewPermissionRequired` | Non-object-based custom form view with `view` permission required |

`CustomFormView` inherits from `CrudViewProcessFormMixin`, `CrudView`, `FormMixin`, and Django's `DetailView` — it loads a model object from the URL just like a detail view, and renders a form alongside it.

`CustomFormNoObjectView` is the same but does not load a model object. Use it for forms that are not tied to a specific instance.

## Basic Usage

Define a form, then a view with `cv_key` and `cv_path` set:

```python
from django.forms.fields import CharField
from django.utils.translation import gettext as _
from crud_views.lib.crispy import Column12, CrispyModelForm, CrispyModelViewMixin
from crud_views.lib.views import MessageMixin
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(model=Author, name="author")


class AuthorContactForm(CrispyModelForm):
    submit_label = _("Send")

    subject = CharField(label="Subject", required=True)
    body = CharField(label="Body", required=True)

    class Meta:
        model = Author
        fields = ["subject", "body"]

    def get_layout_fields(self):
        return Column12("subject"), Column12("body")


class AuthorContactView(MessageMixin, CrispyModelViewMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"
    cv_path = "contact"
    cv_icon_action = "fa-solid fa-envelope"
    cv_viewset = cv_author
    form_class = AuthorContactForm

    cv_message_template_code = "Successfully contacted author »{object}«"
    cv_context_actions = ["parent", "detail", "update", "delete", "contact"]
    cv_header_template_code = _("Contact Author")
    cv_paragraph_template_code = _("Send a message to the Author")

    def cv_form_valid(self, context):
        form = context["form"]
        # process form.cleaned_data here, e.g. send an email
        pass
```

The view is auto-registered with `cv_author` via `cv_key` and `cv_path`, so its URL is included automatically in `cv_author.urlpatterns`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `cv_key` | `str` | — | **Required.** Unique key within the ViewSet (e.g. `"contact"`) |
| `cv_path` | `str` | — | **Required.** URL path segment (e.g. `"contact"`) |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `form_class` | `Form` | — | The form class to render |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after a valid form submission |
| `cv_context_actions` | `list[str]` | from settings | Actions shown in the header area |
| `cv_header_template_code` | `str` | — | Translatable header text |
| `cv_paragraph_template_code` | `str` | — | Translatable paragraph text below the header |

## Form Processing Hooks

Override `cv_form_valid` to handle the submitted form data:

| Hook | Description |
|------|-------------|
| `cv_form_valid(context)` | Called when the form is valid — implement your action here |
| `cv_form_valid_hook(context)` | Called after `cv_form_valid` (used by `MessageMixin`) |

The `context` dict contains at least `"form"` (the bound, validated form) and `"object"` (the loaded model instance, for object-based views).

After `cv_form_valid_hook`, the view redirects to `cv_success_key` (default: `"list"`).

## Adding a Success Message

Combine with `MessageMixin` to display a flash message after a successful submission:

```python
class AuthorContactView(MessageMixin, CrispyModelViewMixin, CustomFormViewPermissionRequired):
    ...
    cv_message_template_code = "Successfully contacted author »{object}«"
```

## Non-Object View

Use `CustomFormNoObjectView` when the form is not tied to a specific model instance:

```python
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired

class SiteFeedbackView(CrispyModelViewMixin, CustomFormNoObjectViewPermissionRequired):
    cv_key = "feedback"
    cv_path = "feedback"
    cv_viewset = cv_site
    form_class = FeedbackForm

    def cv_form_valid(self, context):
        # process feedback
        pass
```

## CrispyModelViewMixin

`CrispyModelViewMixin` (alias of `CrispyViewMixin`) enables crispy-forms support for the view's form. When added to a view, it passes the current view instance (`cv_view`) as an extra argument when constructing the form. This allows the form to generate context-aware submit and cancel buttons.

Add it to any view that uses a `CrispyModelForm` or `CrispyForm`:

```python
class AuthorContactView(CrispyModelViewMixin, CustomFormViewPermissionRequired):
    form_class = AuthorContactForm  # must extend CrispyModelForm or CrispyForm
    ...
```

See [CreateView](create_view.md) for details on defining `CrispyModelForm` forms.
