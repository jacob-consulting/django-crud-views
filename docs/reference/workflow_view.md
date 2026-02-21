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

from crud_views_workflow.lib.enums import WorkflowComment
from crud_views_workflow.lib.mixins import WorkflowMixin


class CampaignState(models.TextChoices):
    NEW = "new", _("New")
    ACTIVE = "active", _("Active")
    SUCCESS = "success", _("Success")
    CANCELED = "canceled", _("Cancelled")
    ERROR = "error", _("Error")


class Campaign(WorkflowMixin, models.Model):
    STATE_ENUM = CampaignState
    STATE_BADGES = {
        CampaignState.NEW: "light",
        CampaignState.ACTIVE: "info",
        CampaignState.SUCCESS: "primary",
        CampaignState.CANCELED: "warning",
        CampaignState.ERROR: "danger",
    }

    name = models.CharField(max_length=128)
    state = FSMField(default=CampaignState.NEW, choices=CampaignState.choices)

    @transition(
        field=state,
        source=CampaignState.NEW,
        target=CampaignState.ACTIVE,
        on_error=CampaignState.ERROR,
        custom={"label": _("Activate"), "comment": WorkflowComment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.SUCCESS,
        on_error=CampaignState.ERROR,
        custom={"label": _("Done"), "comment": WorkflowComment.OPTIONAL},
    )
    def wf_done(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.NEW,
        target=CampaignState.CANCELED,
        on_error=CampaignState.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowComment.REQUIRED},
    )
    def wf_cancel_new(self, request=None, by=None, comment=None):
        pass
```

### 2. Define the ViewSet and views

```python
from crud_views.lib.crispy import CrispyModelViewMixin
from crud_views.lib.views import MessageMixin
from crud_views.lib.viewset import ViewSet
from crud_views_workflow.lib.forms import WorkflowForm
from crud_views_workflow.lib.views import WorkflowView
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
| `WorkflowView` | Base workflow view without permission check |
| `WorkflowViewPermissionRequired` | Workflow view requiring `change` permission |

Both inherit from `CustomFormView` (a `DetailView` with form handling). They fetch the object
from the URL `pk` parameter, render the transition form, and process the selected transition on POST.

`WorkflowViewPermissionRequired` adds `CrudViewPermissionRequiredMixin` with `cv_permission = "change"`.
Authenticated users without the required permission receive a 403; anonymous users are redirected to
the login page.

Use `WorkflowViewPermissionRequired` for production views:

```python
from crud_views_workflow.lib.views import WorkflowViewPermissionRequired

class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_context_actions = ["list", "detail", "workflow"]
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm
```

## WorkflowMixin

`WorkflowMixin` is a model mixin that provides workflow-related properties and helpers.

### Required class attributes

| Attribute | Description |
|-----------|-------------|
| `STATE_ENUM` | A `models.TextChoices` subclass defining all state values and labels |
| `STATE_BADGES` | Dict mapping state values to Bootstrap badge class names |

### Optional class attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `COMMENT_DEFAULT` | `WorkflowComment` | `WorkflowComment.NONE` | Fallback comment requirement for transitions that omit `comment` from their `custom` dict |

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

### WorkflowComment

Each transition declares its comment requirement via the `custom` dict on the `@transition` decorator.
Import `WorkflowComment` from `crud_views_workflow.lib.enums`:

```python
from crud_views_workflow.lib.enums import WorkflowComment

@transition(
    field=state,
    source=CampaignState.NEW,
    target=CampaignState.CANCELED,
    custom={"label": _("Cancel"), "comment": WorkflowComment.REQUIRED},
)
def wf_cancel_new(self, ...):
    ...
```

| Value | Behaviour |
|-------|-----------|
| `WorkflowComment.NONE` | Comment field is hidden |
| `WorkflowComment.OPTIONAL` | Comment field is shown but not required |
| `WorkflowComment.REQUIRED` | Comment field is shown and must be filled |

When a transition does not include `comment` in its `custom` dict, `WorkflowMixin.COMMENT_DEFAULT`
is used as the fallback. Override it on your model class to change the default for all such transitions:

```python
class Campaign(WorkflowMixin, models.Model):
    COMMENT_DEFAULT = WorkflowComment.OPTIONAL
    ...
```

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
| `template_name` | `str` | `"crud_views_workflow/view_workflow.html"` | Template |
| `form_class` | `Form` | — | Must be set to a `WorkflowForm` subclass |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_transition_label` | `str` | `"Select a possible workflow action to take"` | Transition field label |
| `cv_transition_help_text` | `str` | `None` | Transition field help text |
| `cv_comment_label` | `str` | `"Please provide a comment for your workflow step"` | Comment field label |
| `cv_comment_help_text` | `str` | `None` | Comment field help text |

## System checks

`WorkflowView` participates in the crud-views check framework. Checks are run via
`ViewSet.checks()` for every registered view and report configuration errors early.

`WorkflowView.checks()` inherits all parent checks (e.g. `cv_key`, `cv_path`, template
attributes from `CrudView`) and adds:

| ID | What is checked |
|----|----------------|
| `E230` | `form_class` is set (not `None`) |
| `E231` | `cv_transition_label` is not `None` |
| `E232` | `cv_comment_label` is not `None` |
| `E233` | The model associated with `cv_viewset` extends `WorkflowMixin` |
| `E234` | `STATE_ENUM` is set on the model |
| `E235` | `STATE_BADGES` is set on the model |

`WorkflowViewPermissionRequired` additionally inherits the `E202` check for `cv_permission`
from `CrudViewPermissionRequiredMixin`.

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
