# WorkflowView

The `WorkflowView` integrates [django-fsm-2](https://github.com/viewflow/django-fsm) state machines
with the crud-views framework. It renders a form that allows users to execute FSM transitions on a
model instance, enforces comment requirements per transition, and maintains a full audit history via
the `WorkflowInfo` model.

## Installation

Install the `workflow` optional dependency group:

```bash
pip install django-crud-views[workflow]
```

Add the required apps to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django.contrib.contenttypes",  # required for audit log
    "django_fsm",
    "crud_views_workflow.apps.CrudViewsWorkflowConfig",
    ...
]
```

Run migrations to create the `WorkflowInfo` audit table:

```bash
python manage.py migrate
```

## Basic Usage

### 1. Define the model

Mix `WorkflowMixin` into your model and define FSM transitions using django-fsm-2:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from crud_views_workflow.mixins import WorkflowMixin


class Campaign(WorkflowMixin, models.Model):
    class STATE:
        NEW = "new"
        ACTIVE = "active"
        SUCCESS = "success"
        CANCELED = "canceled"
        ERROR = "error"

    STATE_CHOICES = (
        (STATE.NEW, _("New")),
        (STATE.ACTIVE, _("Active")),
        (STATE.SUCCESS, _("Success")),
        (STATE.CANCELED, _("Cancelled")),
        (STATE.ERROR, _("Error")),
    )

    STATE_BADGES = {
        STATE.NEW: "light",
        STATE.ACTIVE: "info",
        STATE.SUCCESS: "primary",
        STATE.CANCELED: "warning",
        STATE.ERROR: "danger",
    }

    name = models.CharField(max_length=128)
    state = FSMField(default=STATE.NEW, choices=STATE_CHOICES)

    @transition(
        field=state,
        source=STATE.NEW,
        target=STATE.ACTIVE,
        on_error=STATE.ERROR,
        custom={"label": _("Activate"), "comment": WorkflowMixin.Comment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.ACTIVE,
        target=STATE.SUCCESS,
        on_error=STATE.ERROR,
        custom={"label": _("Done"), "comment": WorkflowMixin.Comment.OPTIONAL},
    )
    def wf_done(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.NEW,
        target=STATE.CANCELED,
        on_error=STATE.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowMixin.Comment.REQUIRED},
    )
    def wf_cancel_new(self, request=None, by=None, comment=None):
        pass
```

### 2. Define the ViewSet and views

```python
from crud_views.lib.crispy import CrispyModelViewMixin
from crud_views.lib.views import MessageMixin
from crud_views.lib.viewset import ViewSet
from crud_views_workflow.forms import WorkflowForm
from crud_views_workflow.views import WorkflowView
from .models import Campaign

cv_campaign = ViewSet(model=Campaign, name="campaign")


class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign


class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowView):
    cv_context_actions = ["list", "detail", "workflow"]
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm
```

### 3. Register URLs

```python
# urls.py
urlpatterns = cv_campaign.urlpatterns
```

## View Classes

| Class | Description |
|-------|-------------|
| `WorkflowView` | Base workflow view without explicit permission check |

`WorkflowView` inherits from `CustomFormView` (which is a `DetailView` with form handling).
It fetches the object from the URL `pk` parameter, renders the transition form, and processes
the selected transition on POST.

To restrict access by permission, add `CrudViewPermissionRequiredMixin` or combine with
`LoginRequiredMixin` as needed.

## WorkflowMixin

`WorkflowMixin` is a model mixin that provides workflow-related properties and helpers.

### Required class attributes

| Attribute | Description |
|-----------|-------------|
| `STATE` | Inner class with state constants (e.g. `STATE.NEW = "new"`) |
| `STATE_CHOICES` | Tuple of `(value, label)` pairs for the `FSMField` |
| `STATE_BADGES` | Dict mapping state values to Bootstrap badge class names |

### Properties and methods

| Member | Description |
|--------|-------------|
| `state_name` | Human-readable name for the current state |
| `state_badge` | HTML `<span>` badge for the current state |
| `get_state_name(state)` | Human-readable name for a given state value |
| `get_state_badge(state)` | HTML badge for a given state value |
| `workflow_data` | List of dicts with full transition history (timestamp, user, states, label, comment) |
| `workflow_get_possible_transitions(user)` | Available transitions for a user as `[(name, label, comment_type)]` |
| `workflow_has_any_possible_transition(user)` | `True` if any transitions are available |
| `workflow_has_transition(user, transition)` | `True` if a specific transition is available |
| `workflow_get_transition_label(name)` | Human-readable label for a transition name |
| `workflow_get_transition_label_map` | Cached dict of all transition names to labels |
| `workflow_get_form_kwargs(user)` | Builds kwargs for `WorkflowForm` (choices, transition_comments) |

### Comment.NONE / OPTIONAL / REQUIRED

Each transition declares its comment requirement via the `custom` dict on the `@transition` decorator:

```python
@transition(
    field=state,
    source=STATE.NEW,
    target=STATE.CANCELED,
    custom={"label": _("Cancel"), "comment": WorkflowMixin.Comment.REQUIRED},
)
def wf_cancel_new(self, ...):
    ...
```

| Value | Behaviour |
|-------|-----------|
| `Comment.NONE` | Comment field is hidden |
| `Comment.OPTIONAL` | Comment field is shown but not required |
| `Comment.REQUIRED` | Comment field is shown and must be filled |

## WorkflowForm

`WorkflowForm` is the base form class. Subclass it and set `Meta.model`:

```python
class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign
```

The form contains two fields:

| Field | Description |
|-------|-------------|
| `transition` | `RadioSelect` of available transitions (dynamically populated) |
| `comment` | Optional/required `Textarea` (visibility controlled by comment requirement) |

The form's `clean()` validates that a comment is provided when `Comment.REQUIRED` is selected.

## WorkflowInfo (audit log)

Every successful transition creates a `WorkflowInfo` record:

| Field | Description |
|-------|-------------|
| `transition` | The transition method name (e.g. `"wf_activate"`) |
| `state_old` | State value before the transition |
| `state_new` | State value after the transition |
| `comment` | User-provided comment, or `None` |
| `user` | The `User` who triggered the transition |
| `timestamp` | Date/time of the transition |
| `data` | Optional JSON data returned by the transition method |
| `workflow_object` | Generic FK to the transitioned object |

Access the history via `WorkflowMixin.workflow_data`, which returns a list of dicts enriched
with badge HTML and human-readable labels.

## WorkflowView configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `cv_key` | `str` | `"workflow"` | ViewSet key for this view |
| `cv_path` | `str` | `"workflow"` | URL path segment (e.g. `/<pk>/workflow/`) |
| `template_name` | `str` | `"crud_views_workflow/workflow/view_workflow.html"` | Template |
| `form_class` | `Form` | — | Must be set to a `WorkflowForm` subclass |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `transition_label` | `str` | `"Select a possible workflow action to take"` | Transition field label |
| `transition_help_text` | `str` | `None` | Transition field help text |
| `comment_label` | `str` | `"Please provide a comment for your workflow step"` | Comment field label |
| `comment_help_text` | `str` | `None` | Comment field help text |

### `on_transition` hook

Override `on_transition` to run custom logic after a successful transition:

```python
class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowView):
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm

    def on_transition(self, info, transition, state_old, state_new, comment, user, data):
        # send notification, trigger async task, etc.
        send_notification(self.object, state_new, user)
```

| Parameter | Description |
|-----------|-------------|
| `info` | The newly created `WorkflowInfo` instance |
| `transition` | Transition method name (str) |
| `state_old` | Previous state value |
| `state_new` | New state value |
| `comment` | Comment string or `None` |
| `user` | The requesting `User` |
| `data` | Return value of the transition method (or `None`) |

## Displaying state in ListView and DetailView

Use `state_badge` (the HTML badge property) in your table and detail view:

```python
import django_tables2 as tables
from crud_views.lib.table import Table, LinkDetailColumn
from django_object_detail import PropertyConfig

class CampaignTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    state = tables.Column(accessor="state_badge")


class CampaignDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_campaign
    property_display = [
        {
            "title": "Properties",
            "properties": [
                "name",
                PropertyConfig(path="state_badge", title=_("State")),
            ],
        },
    ]
```
