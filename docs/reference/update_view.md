# UpdateView

The `UpdateView` handles updating existing model instances. It works the same way as
the [CreateView](create_view.md), using Django's form handling and
[django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/) for layout.

## Basic Usage

```python
from django.utils.translation import gettext as _
from crud_views.lib.crispy import CrispyModelForm, CrispyViewMixin, Column4
from crud_views.lib.views import UpdateViewPermissionRequired, MessageMixin
from crispy_forms.layout import Row


class AuthorUpdateForm(CrispyModelForm):
    submit_label = _("Update")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message_template_code = "Updated author »{{ object }}«"
```

## View Classes

| Class | Description |
|-------|-------------|
| `UpdateView` | Base update view without permission checks |
| `UpdateViewPermissionRequired` | Update view with `change` permission required |

Both inherit from Django's `generic.UpdateView` and `CrudView`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | from `cv_viewset` | The Django model to update (auto-derived from ViewSet) |
| `form_class` | `Form` | — | The form class for the update form |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success |
| `cv_cancel_key` | `str \| None` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `str \| list[str] \| None` | `"auto"` | Origin keys the cancel button may return to dynamically; see [Dynamic cancel target](#dynamic-cancel-target) |
| `cv_success_keys` | `list[str] \| None` | `None` | Origin keys the success redirect may return to dynamically; see [Dynamic success target](#dynamic-success-target) |
| `cv_context_actions` | `list[str]` | `["home", "detail", "update", "delete"]` | Actions shown in the header area |

## Dynamic cancel target

Standard form views default to `cv_cancel_keys="auto"`: Cancel returns to an accessible registered
`list` or `card` origin, and object-based forms also accept `detail`. Detail uses the form's current saved
object; detail → create is excluded. Explicit lists can allow other registered keys. `None` or `[]`
selects the static `cv_cancel_key` fallback (default `"list"`, resolving to card when no list exists).
Successful submission is configured independently:

<!-- cv-sync: library/views.py -->
```python
class AuthorUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message_template_code = _("Updated author “{{ object }}”")
    cv_success_keys = ["list", "detail"]  # Save selects a key, without Cancel query restoration
```

Links into eligible forms carry the origin key plus signed query state: filters, ordering, pagination,
repeated values and empty values. Per-key value order is preserved. URLs are reversed within the same
ViewSet and current parent coordinates; no external return path is accepted. See
[Origin parameter and captured query](settings.md#origin-parameter) for limits and session behavior.

`view.cv_get_cancel_url(obj=None, user=None, request=None)` returns the accessible destination URL,
or `None` if neither origin nor fallback is accessible. Omitted arguments use `view.object`,
`request.user` and `view.request`; a request is required. Core and Guardian destination permissions,
parent/object rules and action state apply independently of permission to submit the current form.
Invalid, disallowed or unusable request origins use the configured fallback. If that fallback is
needed but missing or structurally unusable, runtime raises `ImproperlyConfigured`; startup check
`viewset.E256` diagnoses the configuration. `viewset.E255` remains the unrelated context-button check.
`viewset.E252` validates explicit allowed keys (including list-to-card fallback).

The original capture survives invalid submissions because forms post to `request.get_full_path`.
Supported delete/custom/workflow modal paths keep it through invalid replacements. Create/update
modal opt-in remains unsupported (`viewset.E251`). Polymorphic selectors forward validated cancel
state into concrete creation without expanding `cv_success_keys`.

Code that builds sibling links itself (themes, custom columns) should call
`view.cv_get_link_url(target_cls, key, obj)` instead of `view.cv_get_url(key, obj)` so the link
carries the origin. On a ViewSet without a list view, the card page counts as the `list` origin,
the same list-to-card fallback used by `viewset.E252` applies.

Works the same on `CreateView`, `DeleteView`, `CustomFormView` and `CustomFormNoObjectView`.

### Custom Cancel templates

Use the context-taking tag `cv_cancel_url(context, obj=None)` with `view` and `request` in context.
It delegates to the URL resolver and does not hide configuration errors. An optional object argument
uses the view object when omitted, empty or unresolved. Preserve your theme classes and translated label:

<!-- cancel-recipe: guarded-template -->
```django
{% load crud_views i18n %}
{% cv_cancel_url as url %}
{% if url %}<a href="{{ url }}" class="btn btn-secondary">{% translate "Cancel" %}</a>{% endif %}
```

Keep autoescaping enabled. The old key-only recipe is unsupported for Cancel immediately; migrate
copied templates using [the migration guide](../migrating-1.0.md#dynamic-cancel-navigation).
`cv_get_cancel_key()` remains a key helper for other callers; it does not provide the URL-level
permission omission or captured query contract.

### Explicit cancellation settings

These mixins can precede your standard form view in its bases. Singular `cv_cancel_key=None` means
the current view as fallback; plural `cv_cancel_keys=None` disables origin selection:

<!-- cancel-recipe: configuration -->
```python
class StaticCancelMixin:
    cv_cancel_keys = None
    cv_cancel_key = "list"


class CurrentViewCancelMixin:
    cv_cancel_keys = None
    cv_cancel_key = None


class CustomOriginCancelMixin:
    cv_cancel_keys = ["list", "contact"]  # contact must be registered and usable
    cv_cancel_key = "list"
```

### Custom form action groups

`get_cancel_button()` returns `Button | None`. Filter `None` before constructing custom groups or
layouts; `get_cancel_button_kwargs()` remains a dict customization hook for accessible outcomes.
This mixin keeps the ordinary submit action and the page-owned form provided by `CrispyModelForm`:

<!-- cancel-recipe: actions -->
```python
from crispy_forms.bootstrap import FormActions


class CancelAwareActionsMixin:
    def get_form_actions(self):
        buttons = [self.get_submit_button(), self.get_cancel_button()]
        return FormActions(*[button for button in buttons if button is not None])
```

Place it before your `CrispyModelForm` subclass. For a custom delete helper, use
`get_delete_button()` for the primary action, keep `helper.form_tag = False`, and apply the same
filter before adding controls to `Layout`/`FormActions`. Do not wrap the page's existing form again.

<!-- cancel-recipe: delete-helper -->
```python
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout


class CancelAwareDeleteHelperMixin:
    @property
    def helper(self):
        helper = FormHelper()
        helper.form_tag = False
        buttons = [self.get_delete_button(), self.get_cancel_button()]
        helper.layout = Layout("confirm", FormActions(*[button for button in buttons if button is not None]))
        return helper
```

Place this mixin before your `CrispyDeleteForm` subclass; it keeps the confirmation field and Delete action.

## Dynamic success target

*Available since 0.26.0.*

By default a successful submit redirects to `cv_success_key` (`"list"`). With `cv_success_keys`
it redirects to the sibling view the user came from instead, so saving from the detail page
lands back on the detail page (see the example above).

It shares the origin parameter with `cv_cancel_keys` and keeps its existing key-based resolution:

- A link into the view carries the origin when the key is allowed by `cv_cancel_keys` **or**
  `cv_success_keys`. Both lists are resolved independently, so a view can return Cancel to the
  detail page while Save always goes to the list.
- `cv_get_success_key()` returns the origin when it is valid, listed in `cv_success_keys` and
  registered; otherwise `cv_success_key`. The form posts to `request.get_full_path`, so the origin
  reaches the POST without extra fields.
- An object view such as `detail` needs a persisted object. That is always true after an update
  or a custom form on an object, and after a create (the new object). It is never true after a
  delete: `DeleteView` falls back to `cv_success_key`, and system check `viewset.E254` rejects
  object views in a delete view's `cv_success_keys` and `cv_success_key` at startup.
- Modal forms use the resolved URL in their `X-CV-Redirect` header. `ActionView` and the ordered
  up/down views honour `cv_success_keys` too, so an action started from the detail page can return there.
- System check `viewset.E253` fails at startup when an entry of `cv_success_keys` is not a
  registered view key (`"list"` is accepted when only a card view is registered).

Save retains its existing key-based redirect behavior; it does not restore Cancel's captured query.
Cancel query restoration does not change successful-save/deletion redirects or modal redirect headers.

## Reusing the Create Form

Often the update form has the same fields as the create form. You can inherit from the
create form and just change the submit label:

```python
class AuthorCreateForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorUpdateForm(AuthorCreateForm):
    submit_label = _("Update")
```

## Messages

Add `MessageMixin` to show a success message after updating, rendered by
`{% cv_messages %}` in your base template — see [Flash messages](messages.md):

```python
class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message_template_code = "Updated author »{{ object }}«"
```

## Form Processing Hooks

The same hooks as [CreateView](create_view.md#form-processing-hooks) are available:

| Hook | Phase | Description |
|------|-------|-------------|
| `cv_post_hook(context)` | outside | Called at the start of POST processing |
| `cv_form_is_valid(context)` | outside | Override to add custom validation |
| `cv_form_valid(context)` | in transaction | Called when the form is valid (saves the instance) |
| `cv_form_valid_hook(context)` | in transaction | Called after `cv_form_valid` (used by `MessageMixin`) |
| `cv_on_commit(context)` | after commit | Side effects: mail, Celery, webhooks |
| `cv_form_invalid(context)` | outside | Called when the form is invalid |
| `cv_form_invalid_hook(context)` | outside | Called after form invalid handling |

The full call chain, the transaction settings and recipes are in
[Request lifecycle, transactions & hooks](request_lifecycle.md).
