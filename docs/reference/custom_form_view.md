# CustomFormView

!!! example "Try it live"
    The [Custom Form View example](https://django-crud-views-demo.onrender.com/custom-form/contact/) in the live demo
    shows this in action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets
    and wake-up time.

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

The reusable `*PermissionRequired` defaults remain `cv_permission = "view"`. Choose an appropriate write or
execution permission explicitly when a form changes data or performs an action. In the seeded examples,
`ContactRemindView` sets `cv_permission = "change"` (`custom_form.change_contact`), `ContactInviteView` sets
`cv_permission = "add"` (`custom_form.add_contact`), and the flash notification composer sets
`cv_permission = "add"` (`flash_messages.add_notice`). These gates cover both opening and submitting the form.
Alice and Bob retain these grants; `developer/developer` has reads and diagnostics only and cannot execute them.
See the [demo account guide](../getting_started/demo.md#developer-account-and-seeded-reads).

## Basic Usage

Define a form, then a view with `cv_key` and `cv_path` set:

```python
from django.forms.fields import CharField
from django.utils.translation import gettext as _
from crud_views.lib.crispy import Column12, CrispyModelForm, CrispyViewMixin
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


class AuthorContactView(MessageMixin, CrispyViewMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"
    cv_path = "contact"
    cv_icon_action = "fas:envelope"
    cv_viewset = cv_author
    form_class = AuthorContactForm

    cv_message_template_code = "Successfully contacted author »{{ object }}«"
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
| `cv_permission` | `str` | `"view"` | Permission-map key the `*PermissionRequired` variants require (`CustomFormView` itself has none); see [A permission of its own](#a-permission-of-its-own) |
| `form_class` | `Form` | — | The form class to render |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after a valid form submission |
| `cv_cancel_key` | `str \| None` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `str \| list[str] \| None` | `"auto"` | Origin keys the cancel button may return to dynamically (no-object views only to non-object keys). See [UpdateView](update_view.md#dynamic-cancel-target) |
| `cv_success_keys` | `list[str] \| None` | `None` | Origin keys the success redirect may return to dynamically. See [UpdateView](update_view.md#dynamic-success-target) |
| `cv_context_actions` | `list[str]` | from settings | Actions shown in the header area |
| `cv_header_template_code` | `str` | — | Translatable header text |
| `cv_paragraph_template_code` | `str` | — | Translatable paragraph text below the header |

## Form Processing Hooks

Override `cv_form_valid` to handle the submitted form data:

| Hook | Phase | Description |
|------|-------|-------------|
| `cv_form_valid(context)` | in transaction | Called when the form is valid — implement your action here |
| `cv_form_valid_hook(context)` | in transaction | Called after `cv_form_valid` (used by `MessageMixin`) |
| `cv_on_commit(context)` | after commit | Side effects: mail, Celery, webhooks |

The `context` dict contains at least `"form"` (the bound, validated form) and `"object"` (the loaded model instance, for object-based views).

After `cv_form_valid_hook`, the view redirects to `cv_success_key` (default: `"list"`), or to the origin view when it is listed in [`cv_success_keys`](update_view.md#dynamic-success-target).

See [Request lifecycle, transactions & hooks](request_lifecycle.md) for the full call chain.

## Adding a Success Message

Combine with `MessageMixin` to display a flash message after a successful submission
(rendered by `{% cv_messages %}` in your base template — see [Flash messages](messages.md)):

```python
class AuthorContactView(MessageMixin, CrispyViewMixin, CustomFormViewPermissionRequired):
    ...
    cv_message_template_code = "Successfully contacted author »{{ object }}«"
```

## Non-Object View

Use `CustomFormNoObjectView` when the form is not tied to a specific model instance:

```python
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired


class SiteFeedbackView(CrispyViewMixin, CustomFormNoObjectViewPermissionRequired):
    cv_key = "feedback"
    cv_path = "feedback"
    cv_viewset = cv_site
    form_class = FeedbackForm

    def cv_form_valid(self, context):
        # process feedback
        pass
```

## A permission of its own

A view outside the standard CRUD operations, such as a contact form or an approval, can require a permission of
its own instead of reusing `view` or `change`. `cv_permission` is a key of the ViewSet's permission map: the model's
permission codename with its exact terminal `_<model_name>` suffix removed, as `ViewSet.default_permissions` does.
For `Author`, `view_author` becomes `view` and `contact_author` becomes `contact`. A codename without that suffix
keeps its full name: `change_book_status` on `Book` stays `change_book_status`. The recipe has two declarations:
the permission on the model and its key on the view.

### Declare the permission on the model

Add the custom permission to your existing model:

```python
class Author(models.Model):
    ...

    class Meta:
        # only the permissions entry is new; keep the model's other Meta options
        permissions = [("contact_author", "Can contact an author")]
```

Create the migration with `makemigrations` and apply it with `migrate`: Django's auth app creates a `Permission`
row for each `Meta.permissions` entry, and that row must exist before you can grant it to a user.

### Require it on the view

Extend the contact form example with `cv_permission = "contact"`:

```python
from django.forms.fields import CharField
from crud_views.lib.crispy import Column12, CrispyModelForm, CrispyViewMixin
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from myapp.models import Author

cv_author = ViewSet(model=Author, name="author")


class AuthorContactForm(CrispyModelForm):
    subject = CharField(label="Subject", required=True)
    body = CharField(label="Body", required=True)

    class Meta:
        model = Author
        fields = ["subject", "body"]

    def get_layout_fields(self):
        return Column12("subject"), Column12("body")


class AuthorContactView(CrispyViewMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"
    cv_path = "contact"
    cv_viewset = cv_author
    cv_permission = "contact"  # contact_author without its _author suffix
    form_class = AuthorContactForm

    def cv_form_valid(self, context):
        # Process context["form"].cleaned_data here, e.g. send the contact message.
        pass
```

The same keying applies to `CustomFormNoObjectViewPermissionRequired`: the `SiteFeedbackView` above sets
`cv_permission` against `cv_site`'s model. It also applies to
[`ActionViewPermissionRequired`](action_view.md).
A nested custom endpoint additionally needs an `ancestor_policy.actions` pair whose keys resolve on the
*ancestor's* model; see
[Example: permissions for a nested Book ViewSet](nested.md#example-permissions-for-a-nested-book-viewset).

The startup system check `viewset.E269` reports a `cv_permission` that names no declared permission before the
first request. It reads only `Meta.default_permissions` and `Meta.permissions`, never the database, so it can
run before `migrate`; migrations still need to create the permission rows. It resolves proxies to their concrete
model, matching the runtime map, and its hint spells out the `Meta.permissions` entry to add.
`GuardianViewSet`s are not covered because their map comes from the type Guardian's content-type resolver selects;
an undeclared key still fails at request time (`ImproperlyConfigured` on Guardian list, card and object views).
See [Configured content-type defaults](guardian.md#configured-content-type-defaults).

## CrispyViewMixin

`CrispyViewMixin` enables crispy-forms support for the view's form. When added to a view, it passes the current view instance (`cv_view`) as an extra argument when constructing the form. This allows the form to generate context-aware submit and cancel buttons.

Add it to any view that uses a `CrispyModelForm` or `CrispyForm`:

```python
class AuthorContactView(CrispyViewMixin, CustomFormViewPermissionRequired):
    form_class = AuthorContactForm  # must extend CrispyModelForm or CrispyForm
    ...
```

See [CreateView](create_view.md) for details on defining `CrispyModelForm` forms.
