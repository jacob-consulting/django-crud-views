# django-crud-views WorkflowView Reference

## Table of Contents
1. [Installation](#installation)
2. [Model Setup (WorkflowModelMixin)](#model-setup-workflowmodelmixin)
3. [WorkflowComment Enum](#workflowcomment-enum)
4. [BadgeEnum](#badgeenum)
5. [WorkflowForm](#workflowform)
6. [WorkflowView Classes](#workflowview-classes)
7. [Configuration Attributes](#configuration-attributes)
8. [on_transition Hook](#on_transition-hook)
9. [WorkflowInfo (Audit Log)](#workflowinfo-audit-log)
10. [Displaying State in Tables & Detail Views](#displaying-state-in-tables--detail-views)
11. [Import Paths](#import-paths)

---

## Installation

```bash
pip install django-crud-views[workflow]
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django.contrib.contenttypes",  # required for audit log
    "django_fsm",
    "crud_views_workflow.apps.CrudViewsWorkflowConfig",
    ...
]
```

```bash
python manage.py migrate
```

---

## Model Setup (WorkflowModelMixin)

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from crud_views_workflow.lib.enums import WorkflowComment, BadgeEnum
from crud_views_workflow.lib.mixins import WorkflowModelMixin


class CampaignState(models.TextChoices):
    NEW = "new", _("New")
    ACTIVE = "active", _("Active")
    SUCCESS = "success", _("Success")
    CANCELED = "canceled", _("Cancelled")
    ERROR = "error", _("Error")


class Campaign(WorkflowModelMixin, models.Model):
    # Required attributes
    STATE_CHOICES = CampaignState
    STATE_BADGES = {
        CampaignState.NEW: BadgeEnum.LIGHT,
        CampaignState.ACTIVE: BadgeEnum.INFO,
        CampaignState.SUCCESS: BadgeEnum.PRIMARY,
        CampaignState.CANCELED: BadgeEnum.WARNING,
        CampaignState.ERROR: BadgeEnum.DANGER,
    }
    # Optional: fallback badge for states not in STATE_BADGES (default: BadgeEnum.INFO)
    STATE_BADGE_DEFAULT = BadgeEnum.SECONDARY
    # Optional: fallback comment requirement when custom["comment"] is omitted
    COMMENT_DEFAULT = WorkflowComment.OPTIONAL  # default: WorkflowComment.NONE

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

### WorkflowModelMixin Required Attributes

| Attribute | Description |
|-----------|-------------|
| `STATE_CHOICES` | `models.TextChoices` subclass |
| `STATE_BADGES` | Dict mapping state values → `BadgeEnum` (e.g. `BadgeEnum.LIGHT`, `BadgeEnum.SUCCESS`) |

### WorkflowModelMixin Optional Attributes

| Attribute | Default | Description |
|-----------|---------|-------------|
| `STATE_BADGE_DEFAULT` | `BadgeEnum.INFO` | Fallback badge for states absent from `STATE_BADGES` |
| `COMMENT_DEFAULT` | `WorkflowComment.NONE` | Fallback comment requirement when `custom["comment"]` is omitted |

### WorkflowModelMixin Properties & Methods

| Member | Description |
|--------|-------------|
| `state_name` | Human-readable name for current state |
| `state_badge` | HTML `<span>` badge for current state |
| `get_state_name(state)` | Human-readable name for any state value |
| `get_state_badge(state)` | HTML badge for any state value |
| `workflow_data` | List of dicts with full transition history (timestamp, user, states, label, comment) |
| `workflow_get_possible_transitions(user)` | Returns `[(name, label, comment_type)]` for available transitions |
| `workflow_has_any_possible_transition(user)` | Boolean: any transitions available? |
| `workflow_has_transition(user, transition)` | Boolean: specific transition available? |
| `workflow_get_transition_label(name)` | Label string for a transition name |
| `workflow_get_transition_label_map` | Cached dict of all transition names → labels |
| `workflow_get_form_kwargs(user)` | Builds kwargs for `WorkflowForm` |

---

## WorkflowComment Enum

```python
from crud_views_workflow.lib.enums import WorkflowComment
```

| Value | Behaviour |
|-------|-----------|
| `WorkflowComment.NONE` | Comment field hidden |
| `WorkflowComment.OPTIONAL` | Comment shown, not required |
| `WorkflowComment.REQUIRED` | Comment shown and mandatory |

Set per-transition via `custom={"comment": WorkflowComment.REQUIRED}` in the `@transition` decorator.

---

## BadgeEnum

```python
from crud_views_workflow.lib.enums import BadgeEnum
```

`StrEnum` of Bootstrap contextual colours. Use as values in `STATE_BADGES`:

| Value | String |
|-------|--------|
| `BadgeEnum.PRIMARY` | `"primary"` |
| `BadgeEnum.SECONDARY` | `"secondary"` |
| `BadgeEnum.SUCCESS` | `"success"` |
| `BadgeEnum.DANGER` | `"danger"` |
| `BadgeEnum.WARNING` | `"warning"` |
| `BadgeEnum.INFO` | `"info"` |
| `BadgeEnum.LIGHT` | `"light"` |
| `BadgeEnum.DARK` | `"dark"` |

---

## WorkflowForm

Subclass `WorkflowForm` and set `Meta.model`:

```python
from crud_views_workflow.lib.forms import WorkflowForm

class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign
```

Fields provided by `WorkflowForm`:
- `transition` — RadioSelect of available transitions (dynamically populated per user)
- `comment` — Textarea (visibility and requirement controlled by `WorkflowComment` enum)

The form's `clean()` validates comment requirement automatically.

---

## WorkflowView Classes

| Class | Description |
|-------|-------------|
| `WorkflowView` | Base view, no permission check |
| `WorkflowViewPermissionRequired` | Enforces Django `change` permission (recommended for production) |

Both inherit from `CustomFormView` and retrieve the object via the URL `pk` parameter. URLs are auto-registered by the ViewSet.

### Full view example

```python
from crud_views.lib.crispy import CrispyModelViewMixin
from crud_views.lib.views import MessageMixin
from crud_views.lib.viewset import ViewSet
from crud_views_workflow.lib.forms import WorkflowForm
from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
from .models import Campaign

cv_campaign = ViewSet(model=Campaign, name="campaign")


class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign


class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_context_actions = ["list", "detail", "workflow"]
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm
```

---

## Configuration Attributes

| Attribute | Default | Description |
|-----------|---------|-------------|
| `cv_key` | `"workflow"` | ViewSet key for this view |
| `cv_path` | `"workflow"` | URL path segment (`/<pk>/workflow/`) |
| `template_name` | `"crud_views_workflow/view_workflow.html"` | Template path |
| `form_class` | — | **Required.** Set to a `WorkflowForm` subclass |
| `cv_viewset` | — | **Required.** The ViewSet this view belongs to |
| `cv_transition_label` | `"Select a possible workflow action to take"` | Transition radio field label |
| `cv_transition_help_text` | `None` | Transition field help text |
| `cv_comment_label` | `"Please provide a comment for your workflow step"` | Comment field label |
| `cv_comment_help_text` | `None` | Comment field help text |

### System check IDs

| ID | What is checked |
|----|-----------------|
| `E230` | `form_class` is set |
| `E231` | `cv_transition_label` is not `None` |
| `E232` | `cv_comment_label` is not `None` |
| `E233` | Model extends `WorkflowModelMixin` |
| `E234` | `STATE_CHOICES` set on model |
| `E235` | `STATE_BADGES` set on model |

---

## on_transition Hook

Override to run custom logic after a successful transition:

```python
class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm

    def on_transition(self, info, transition, state_old, state_new, comment, user, data):
        # e.g. send notification, trigger async task
        send_notification(self.object, state_new, user)
```

| Parameter | Description |
|-----------|-------------|
| `info` | Newly created `WorkflowInfo` instance |
| `transition` | Transition method name (str) |
| `state_old` | Previous state value |
| `state_new` | New state value |
| `comment` | Comment string or `None` |
| `user` | Requesting `User` |
| `data` | Return value of the transition method (or `None`) |

---

## WorkflowInfo (Audit Log)

Every successful transition creates a `WorkflowInfo` record. Access history via `instance.workflow_data`.

| Field | Description |
|-------|-------------|
| `transition` | Transition method name (e.g. `"wf_activate"`) |
| `state_old` | State before transition |
| `state_new` | State after transition |
| `comment` | User comment or `None` |
| `user` | FK to `User` |
| `timestamp` | Date/time of transition |
| `data` | Optional JSON from transition return value |
| `workflow_object_pk` | PK as string (supports UUID, int, str) |
| `workflow_object_content_type` | FK to `ContentType` |
| `workflow_object` | Generic FK (content type + PK) |

An index on `(workflow_object_pk, workflow_object_content_type)` is defined.

---

## Displaying State in Tables & Detail Views

Use `state_badge` (returns HTML) for display in tables and detail views:

```python
import django_tables2 as tables
from crud_views.lib.table import Table, LinkDetailColumn
from django_object_detail import PropertyConfig

class CampaignTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    state = tables.Column(accessor="state_badge")   # renders HTML badge


class CampaignDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_campaign
    property_display = [
        {
            "title": "Campaign",
            "properties": [
                "name",
                PropertyConfig(path="state_badge", title="State"),
            ],
        },
    ]
```

---

## Import Paths

```python
# Model mixin
from crud_views_workflow.lib.mixins import WorkflowModelMixin

# Enums
from crud_views_workflow.lib.enums import WorkflowComment, BadgeEnum

# Form
from crud_views_workflow.lib.forms import WorkflowForm

# Views
from crud_views_workflow.lib.views import WorkflowView, WorkflowViewPermissionRequired

# Audit model (if needed directly)
from crud_views_workflow.models import WorkflowInfo
```
