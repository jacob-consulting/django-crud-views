# WorkflowView

The `WorkflowView` integrates [django-fsm-2](https://github.com/viewflow/django-fsm) state machines
with the crud-views framework. It renders a form that allows users to execute FSM transitions on a
model instance, enforces comment requirements per transition, and maintains a full audit history via
the `WorkflowInfo` model.

!!! example "Try it live"
    The [Workflow example](https://django-crud-views-demo.onrender.com/workflow/campaign/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

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

Mix `WorkflowModelMixin` into your model and define FSM transitions using django-fsm-2:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowModelMixin


class CampaignState(models.TextChoices):
    NEW = "new", _("New")
    ACTIVE = "active", _("Active")
    SUCCESS = "success", _("Success")
    CANCELED = "canceled", _("Cancelled")
    ERROR = "error", _("Error")


class Campaign(WorkflowModelMixin, models.Model):
    STATE_CHOICES = CampaignState
    STATE_BADGES = {
        CampaignState.NEW: BadgeEnum.LIGHT,
        CampaignState.ACTIVE: BadgeEnum.INFO,
        CampaignState.SUCCESS: BadgeEnum.PRIMARY,
        CampaignState.CANCELED: BadgeEnum.WARNING,
        CampaignState.ERROR: BadgeEnum.DANGER,
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
from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.views import MessageMixin
from crud_views.lib.viewset import ViewSet
from crud_views_workflow.lib import WorkflowForm, WorkflowView
from .models import Campaign

cv_campaign = ViewSet(model=Campaign, name="campaign")


class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign


class CampaignWorkflowView(CrispyViewMixin, MessageMixin, WorkflowView):
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
from crud_views_workflow.lib import WorkflowViewPermissionRequired


class CampaignWorkflowView(CrispyViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_context_actions = ["list", "detail", "workflow"]
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm
```

## Opt-in per-transition permissions

`WorkflowViewPermissionRequired` keeps its default `change` gate. To let a user execute a dedicated step
without general change permission, explicitly select `cv_permission = "view"` and give each restricted
transition its own django-fsm `permission=` rule. Lowering the page gate alone does not restrict transitions
that have no permission rule. See [django-fsm-2 permissions](https://github.com/django-commons/django-fsm-2#permissions).

This complete basic recipe uses an app named `requests_app`. Follow the
[installation and base-template setup](../getting_started/tutorial-1-setup.md) and
[getting started](../getting_started/index.md)
guidance for core apps and the base template, add `requests_app` to `INSTALLED_APPS`, and complete the
[workflow installation](#installation) above. The regression fixture uses the installed test app label
`app`; the example below uses `requests_app` consistently instead.

### Model and transition rules

In `requests_app/models.py`, both transitions start from `NEW`, so their different availability for users
comes from their permission rules:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowModelMixin


class WorkflowRequestState(models.TextChoices):
    NEW = "new", _("New")
    PROCESSED = "processed", _("Processed")
    CANCELED = "canceled", _("Canceled")


class WorkflowRequest(WorkflowModelMixin, models.Model):
    STATE_CHOICES = WorkflowRequestState
    STATE_BADGES = {
        WorkflowRequestState.NEW: BadgeEnum.LIGHT,
        WorkflowRequestState.PROCESSED: BadgeEnum.PRIMARY,
        WorkflowRequestState.CANCELED: BadgeEnum.WARNING,
    }

    name = models.CharField(max_length=128)
    state = FSMField(default=WorkflowRequestState.NEW, choices=WorkflowRequestState.choices)

    class Meta:
        permissions = [("process_workflowrequest", "Can process workflow request")]

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=WorkflowRequestState.NEW,
        target=WorkflowRequestState.PROCESSED,
        permission="requests_app.process_workflowrequest",
        custom={"label": "Process", "comment": WorkflowComment.NONE},
    )
    def wf_process(self, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=WorkflowRequestState.NEW,
        target=WorkflowRequestState.CANCELED,
        permission="requests_app.change_workflowrequest",
        custom={"label": "Cancel", "comment": WorkflowComment.NONE},
    )
    def wf_cancel(self, by=None, comment=None):
        pass
```

Create the app migration with `makemigrations requests_app`, then apply it with `migrate` to create the table
and permissions, including the custom permission declared in `Meta`. Declaring that permission alone does
not enforce it: the transition's `permission=` rule provides the restriction here.

For a dedicated-step actor, grant `requests_app.view_workflowrequest` and
`requests_app.process_workflowrequest`, without `requests_app.change_workflowrequest`. For an ordinary
change actor, grant `requests_app.view_workflowrequest` and `requests_app.change_workflowrequest`, without
the dedicated permission. Use ordinary users, since superusers would not demonstrate this separation.

### Form, ViewSet and registered views

In `requests_app/views.py`, register list and detail siblings alongside the workflow view. These supply
the action, home, success and Cancel destinations. The plain siblings are minimal navigation targets;
the generic detail body is intentionally empty. Add your own detail presentation separately if needed.

```python
from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired, MessageMixin
from crud_views.lib.viewset import ViewSet
from crud_views_workflow.lib import WorkflowForm, WorkflowViewPermissionRequired

from .models import WorkflowRequest


cv_workflowrequest = ViewSet(model=WorkflowRequest, name="workflowrequest")


class WorkflowRequestListView(ListViewPermissionRequired):
    cv_viewset = cv_workflowrequest
    cv_list_actions = ["detail", "workflow"]
    cv_context_actions = ["list"]


class WorkflowRequestDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_workflowrequest
    cv_context_actions = ["list", "detail", "workflow"]


class WorkflowRequestWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = WorkflowRequest


class WorkflowRequestWorkflowView(CrispyViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_viewset = cv_workflowrequest
    cv_permission = "view"
    cv_context_actions = ["list", "detail", "workflow"]
    form_class = WorkflowRequestWorkflowForm
```

In `requests_app/urls.py`, import the ViewSet after its views have registered:

```python
from .views import cv_workflowrequest

urlpatterns = cv_workflowrequest.urlpatterns
```

Include the app URLs in the project's `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("requests_app.urls")),
]
```

For a saved object, the workflow page is `/workflowrequest/<pk>/workflow/`. A successful step redirects
to the registered list view, which these actors can access with their view permission.

### Authorization layers and basic outcomes

Keep these checks distinct when adapting the recipe:

1. **Page permission:** `cv_permission = "view"` requires the model's view permission. A dedicated step
   permission cannot replace it.
2. **Application object, queryset and parent policy:** retain any existing restrictions on which object
   can be accessed and within which parent. This minimal example adds no such custom policy; the step
   permission does not replace those checks in an application that has them.
3. **Optional action-enabled request gate:** the separate variant below checks whether any step is
   permitted. The basic recipe above leaves the existing hook unchanged.
4. **State/user transition filtering:** `workflow_get_possible_transitions(user)` uses django-fsm's
   available user transitions to build the offered choices for the object's current state.
5. **Submitted-choice validation:** the form's `ChoiceField` rejects a submitted method absent from those
   choices, including a forged same-source transition belonging to the other role.
6. **Execution-time recheck:** after valid form submission, `workflow_has_transition(user, transition)`
   is checked again before the transition method, object save and `WorkflowInfo` creation.

Rendering an action or offering a choice earlier does not authorize execution. These request outcomes are
covered by the isolated `WorkflowRequest` regression fixture, with a fresh `NEW` object for each case:

| Configuration / actor | Request and result | Persisted state and object-scoped history |
|-----------------------|--------------------|------------------------------------------|
| Basic; view + dedicated step, no change | GET 200 offers only `wf_process`; POST `wf_process` returns 302; redirect GET 200 | `PROCESSED`; one new record for `wf_process`, actor and object |
| Basic; view + change, no dedicated step | GET 200 offers only `wf_cancel`; POST `wf_cancel` returns 302; redirect GET 200 | `CANCELED`; one new record for `wf_cancel`, actor and object |
| Basic; view + dedicated step forges `wf_cancel` | GET omits `wf_cancel`; forged POST returns 200 with a transition field error | Unchanged |
| Basic; dedicated step without view | Direct GET and POST return 403 for the authenticated user | Unchanged |
| Basic; view only, no permitted steps | GET 200 shows the empty message; POST `wf_process` returns 200 with a transition field error | Unchanged |
| Basic; valid offered choice denied by the execution recheck | POST returns 400 (`SuspiciousOperation`) | Unchanged |
| Optional hook; view only, no permitted steps | Sibling detail GET 200 renders a disabled workflow action; direct workflow GET and POST return 403 | Unchanged |
| Optional hook; view + dedicated step | Workflow GET 200; POST `wf_process` returns 302; redirect GET 200 | `PROCESSED`; one new record for `wf_process`, actor and object |

In the basic variant, a page viewer with no permitted steps sees:
“There are no workflow steps available from the current state.” Applicable application access checks
must still pass. The controlled execution-recheck test first establishes an offered, valid choice and
then makes the model's recheck return false during the actual POST. It proves this rejection path,
without establishing concurrent permission-revocation or race protection.

### Optional: disable the action and deny no-step requests

To deny the workflow page when no step is permitted, insert the following attributes and method **inside
the existing `WorkflowRequestWorkflowView` class** above, with class-body indentation. This is an insertion
snippet, not a second registered workflow view:

```python
cv_inaccessible_actions = "disable"

@classmethod
def cv_action_enabled(cls, user, obj=None):
    return obj is None or obj.workflow_has_any_possible_transition(user)
```

When the hook returns false, a sibling page rendering the workflow action shows it disabled, and the
server also denies authenticated direct workflow GET and POST requests with 403. This variant does not
leave the empty workflow page accessible. A user with a permitted transition still passes the hook;
`obj is None` also allows evaluation where no object is supplied. Page and applicable object/parent
checks remain required, as do choice validation and the execution recheck.

The hook runs for rendered actions and direct requests. Checking transition permissions can add permission
backend lookups; this recipe makes no fixed query-count or performance guarantee. Keep application policy
within the existing hooks and retain the default `change` gate on other workflow views unless they also
deliberately opt in.

## WorkflowModelMixin

`WorkflowModelMixin` is a model mixin that provides workflow-related properties and helpers.

### Required class attributes

| Attribute | Description |
|-----------|-------------|
| `STATE_CHOICES` | A `models.TextChoices` subclass defining all state values and labels |
| `STATE_BADGES` | Dict mapping state values to `BadgeEnum` badge colours |

### Optional class attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `STATE_BADGE_DEFAULT` | `BadgeEnum` | `BadgeEnum.INFO` | Badge colour used for states not present in `STATE_BADGES` |
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
Import `WorkflowComment` from `crud_views_workflow.lib`:

```python
from crud_views_workflow.lib import WorkflowComment

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

When a transition does not include `comment` in its `custom` dict, `WorkflowModelMixin.COMMENT_DEFAULT`
is used as the fallback. Override it on your model class to change the default for all such transitions:

```python
class Campaign(WorkflowModelMixin, models.Model):
    COMMENT_DEFAULT = WorkflowComment.OPTIONAL
    ...
```

### BadgeEnum

`BadgeEnum` is a `StrEnum` covering all Bootstrap contextual colours. Import it alongside `WorkflowModelMixin`:

```python
from crud_views_workflow.lib import BadgeEnum, WorkflowModelMixin
```

| Value | Bootstrap class |
|-------|----------------|
| `BadgeEnum.PRIMARY` | `primary` |
| `BadgeEnum.SECONDARY` | `secondary` |
| `BadgeEnum.SUCCESS` | `success` |
| `BadgeEnum.DANGER` | `danger` |
| `BadgeEnum.WARNING` | `warning` |
| `BadgeEnum.INFO` | `info` |
| `BadgeEnum.LIGHT` | `light` |
| `BadgeEnum.DARK` | `dark` |

States not listed in `STATE_BADGES` fall back to `STATE_BADGE_DEFAULT` (default: `BadgeEnum.INFO`).

## Themeable state badges

Current and historical badges share `get_state_badge(state)` and the existing
`crud_views_workflow/badge.html` override path. `BadgeEnum`, `STATE_BADGES` and `STATE_BADGE_DEFAULT` retain their
model APIs. First the model chooses the colour: an unmapped state uses `STATE_BADGE_DEFAULT`. Then the class
registry resolves `workflow:badge-<colour>`. This is a complete class string, not a colour-formatting setting.

Workflow's AppConfig supplies [eight badge and two history defaults](buttons.md#optional-workflow-defaults).
Core plus installed-app defaults sit below theme registrations, which sit below `CRUD_VIEWS_BUTTON_CLASSES`.
The [theme recipe](theme.md#optional-workflow-classes) registers complete light/custom classes only when workflow
is installed. Project settings examples below assume that app is installed.

A custom colour such as `purple` without a registered key keeps the original Bootstrap construction:
`badge rounded-pill text-bg-purple`. Missing a class key does **not** substitute `STATE_BADGE_DEFAULT`.
A present `None` or `""` disables all badge classes while preserving its escaped text, and stops fallback.
Values are literal class strings; they are escaped, never evaluated as templates.

The leaf context retains `state` (raw state), `name` (display label), and `class` (selected colour).
The additive `badge_class` is the complete resolved string, `""` for a disabled entry, or `None` as the missing-entry
sentinel. The stock leaf uses the original Bootstrap construction only for the sentinel (also when rendering
the leaf with old context lacking `badge_class`). Legacy copied leaves keep their chosen markup until changed
to consume the new value. Remove a redundant badge leaf to adopt registry classes without maintaining a copy.

### Project workflow classes

Project settings override theme choices per key, including explicit disabled entries:

```python
CRUD_VIEWS_BUTTON_CLASSES = {
    "workflow:badge-success": "badge project-success",
    "workflow:badge-purple": "badge project-purple",
    "workflow:badge-warning": None,
    "workflow:badge-dark": "",
    "workflow:history-wrapper": "table-responsive",
    "workflow:history-table": "table table-striped",
}
```

Custom colours need not be in the defaults, but must have one nonempty colour segment without whitespace or
colon. Workflow keys in settings or theme registrations produce `crud_views.W362` when workflow is absent.
Values other than strings or `None` produce `crud_views.E361`.

## Action frame and history layout

Full-page history comes first, followed by actions. Empty history renders neither a heading nor a table.
`workflow:history-wrapper` styles a div directly around only the table; `workflow:history-table` styles the
semantic table itself. Stock values are `table-responsive` and `table`. The history heading sits outside the
scrolling region, with the horizontal scrollbar immediately below the table. Override each class independently;
keep the wrapper local so wide history does not scroll the action form or widen the page.

The action template extends `crud_views/snippets/form_frame.html` and fills `cv_form_body` inside `cv_form_frame`.
Stock framing adds no decoration. With choices, both the heading and the page-owned form are inside the frame,
with one CSRF input and the existing crispy renderer. With no choices, only the no-transitions message is framed:
no action heading, form, CSRF input or controls. History remains outside that frame. See the complete
[copied action recipe](theme.md#copied-workflow-action-template).

Supported workflow modals keep `crud_views/view_custom_form.content.html`, including its generic no-choice form;
unavailable transitions still reject on submission. Do not reroute them to the full-page workflow content.
The shared theme frame retains ownership of its modal decoration rules. Permissions, transition validation,
execution and history queries are unaffected by these presentation hooks.

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
| `workflow_object_pk` | `CharField(max_length=255)` — the PK of the transitioned object (supports UUID, int, and string PKs) |
| `workflow_object_content_type` | FK to `ContentType` of the transitioned object |
| `workflow_object` | Generic FK combining `workflow_object_content_type` and `workflow_object_pk` |

An index on `(workflow_object_pk, workflow_object_content_type)` is defined for efficient history lookups.

Access the history via `WorkflowModelMixin.workflow_data`, which returns a list of dicts enriched
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
| `E233` | The model associated with `cv_viewset` extends `WorkflowModelMixin` |
| `E234` | `STATE_CHOICES` is set on the model |
| `E235` | `STATE_BADGES` is set on the model |

`WorkflowViewPermissionRequired` additionally inherits the `E202` check for `cv_permission`
from `CrudViewPermissionRequiredMixin`.

### `on_transition` hook

Override `on_transition` for **database** follow-ups of a transition. It runs inside the
transaction, so its writes roll back together with the transition:

```python
class CampaignWorkflowView(CrispyViewMixin, MessageMixin, WorkflowView):
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm

    def on_transition(self, info, transition, state_old, state_new, comment, user, data):
        CampaignAudit.objects.create(campaign=self.object, state=state_new, user=user)
```

Send notifications and start async tasks from `cv_on_commit` instead. It runs after the commit,
and `context["workflow_info"]` holds the `WorkflowInfo` record:

```python
    def cv_on_commit(self, context):
        info = context["workflow_info"]
        send_notification(self.object, info.state_new, info.user)
```

See [Side effects after commit](request_lifecycle.md#side-effects-after-commit).

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
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired, PropertyConfig


class CampaignTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    state = tables.Column(accessor="state_badge")


class CampaignDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_property_display = [
        {
            "title": "Properties",
            "properties": [
                "name",
                PropertyConfig(path="state_badge", title=_("State")),
            ],
        },
    ]
```
