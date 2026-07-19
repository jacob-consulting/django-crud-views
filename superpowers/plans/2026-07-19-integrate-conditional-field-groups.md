# Integrate `feat/conditional-field-groups` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the conditional field-groups / conditional formsets feature from `feat/conditional-field-groups` onto `main`, with a new M3-style example app, updated docs, and a follow-up skill update — losing nothing from the original branch.

**Architecture:** Two-tier port from a fresh branch off `main`. Core library files (`src/crud_views/lib/conditional/*`, `checks.py`, `formsets/formsets.py`, `formsets/render_tree.py`, JS, templates) are byte-identical between `main` and the branch's merge-base, so they are ported with `git show <branch>:<path> > <path>` (full-file, safe). `formsets/mixins.py` changed on `main` since divergence (check-ID renumbering), so it gets a hand-applied one-line edit instead of a full overwrite. The example app is written fresh against the current M3 per-feature-app layout.

**Tech Stack:** Django, django-crispy-forms, Pydantic v2 (for `FormSet`/`ConditionalFormSet`), pytest, ruff.

## Global Constraints

- Local branch `feat/conditional-field-groups` must exist and be reachable for the `git show <ref>:<path>` steps in Tasks 1–3. Do not delete it until Task 6 confirms the full suite green.
- `CrispyModelViewMixin` no longer exists in this codebase (removed post-M2, issue #34). The new example app uses `CrispyViewMixin` instead — the branch's original example used the now-removed name.
- Example apps follow the flat per-app layout used by every other app under `examples/bootstrap5/` (`apps.py`, `models.py`, `views.py`, `seed.py`, `tests.py`, `urls.py`, `migrations/` — no subpackages, no per-app templates; CRUD templates come from the bootstrap5 theme).
- The "About this example" prose and code-snippet panels on every feature page are fully data-driven from `project/features.py`'s `FEATURES` list plus `project/templatetags/example_tags.py` reading `models.py`/`views.py` at runtime — no template work is needed for a new example app.
- Line length 120, double quotes, ruff (`task format`, `task check`) before each commit touching `src/` or `examples/`.
- New system check IDs from the branch (`E310`, `E311`, `W320`) do not collide with current IDs in use (`E100`, `E101`, `E300`, `W110`, `W330`, `W331`) — verified.
- Given another session is active in this same (non-worktree) directory on an unrelated feature, execute this plan in an isolated git worktree (see `superpowers:using-git-worktrees`).

---

### Task 1: Port the `conditional` library package + test fixtures

**Files:**
- Create: `src/crud_views/lib/conditional/__init__.py`
- Create: `src/crud_views/lib/conditional/toggle.py`
- Create: `src/crud_views/lib/conditional/group.py`
- Create: `src/crud_views/lib/conditional/layout.py`
- Create: `src/crud_views/lib/conditional/formset.py`
- Create: `src/crud_views/templates/crud_views/conditional/toggle_group.html`
- Create: `src/crud_views/static/crud_views/js/toggle.js`
- Modify: `tests/test1/app/models.py`
- Test: `tests/test1/test_conditional_toggle.py`, `tests/test1/test_conditional_group.py`, `tests/test1/test_conditional_layout.py`, `tests/test1/test_conditional_exports.py`

**Interfaces:**
- Produces: `crud_views.lib.conditional.{ToggleSource, ModelFieldToggle, UIFieldToggle, ConditionalGroup, ConditionalGroupFormMixin, ConditionalGroupModelForm, ToggleGroup, ConditionalFormSet}` — consumed by Task 2 (`ConditionalFormSet` in `formsets.py`), Task 3 (`checks.py`), and Task 4 (the example app's forms/views).
- Produces: `tests.test1.app.models.{Profile, ProfileItem}` — consumed by Tasks 1–3's ported tests.

- [ ] **Step 1: Create the branch**

```bash
git checkout main
git pull --ff-only
git checkout -b feat/integrate-conditional-field-groups
```

- [ ] **Step 2: Append the `Profile`/`ProfileItem` test fixture models**

Append to the end of `tests/test1/app/models.py` (after the existing `Truck` class):

```python


class Profile(models.Model):
    name = models.CharField(max_length=100)
    with_contact = models.BooleanField(default=False)
    with_items = models.BooleanField(default=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class ProfileItem(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="items")
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label
```

- [ ] **Step 3: Port the test files (expect them to fail — the lib package doesn't exist yet)**

```bash
git show feat/conditional-field-groups:tests/test1/test_conditional_toggle.py > tests/test1/test_conditional_toggle.py
git show feat/conditional-field-groups:tests/test1/test_conditional_group.py > tests/test1/test_conditional_group.py
git show feat/conditional-field-groups:tests/test1/test_conditional_layout.py > tests/test1/test_conditional_layout.py
git show feat/conditional-field-groups:tests/test1/test_conditional_exports.py > tests/test1/test_conditional_exports.py
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `cd tests && pytest test1/test_conditional_toggle.py test1/test_conditional_group.py test1/test_conditional_layout.py test1/test_conditional_exports.py -v`
Expected: FAIL / collection errors — `ModuleNotFoundError: No module named 'crud_views.lib.conditional'`

- [ ] **Step 5: Port the library package, template and JS**

```bash
mkdir -p src/crud_views/lib/conditional
git show feat/conditional-field-groups:src/crud_views/lib/conditional/__init__.py > src/crud_views/lib/conditional/__init__.py
git show feat/conditional-field-groups:src/crud_views/lib/conditional/toggle.py > src/crud_views/lib/conditional/toggle.py
git show feat/conditional-field-groups:src/crud_views/lib/conditional/group.py > src/crud_views/lib/conditional/group.py
git show feat/conditional-field-groups:src/crud_views/lib/conditional/layout.py > src/crud_views/lib/conditional/layout.py
git show feat/conditional-field-groups:src/crud_views/lib/conditional/formset.py > src/crud_views/lib/conditional/formset.py

mkdir -p src/crud_views/templates/crud_views/conditional
git show feat/conditional-field-groups:src/crud_views/templates/crud_views/conditional/toggle_group.html > src/crud_views/templates/crud_views/conditional/toggle_group.html

git show feat/conditional-field-groups:src/crud_views/static/crud_views/js/toggle.js > src/crud_views/static/crud_views/js/toggle.js
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd tests && pytest test1/test_conditional_toggle.py test1/test_conditional_group.py test1/test_conditional_layout.py test1/test_conditional_exports.py -v`
Expected: PASS — all tests green (34 + 92 + 80 + 15 lines of test source across the four files; exact count printed by pytest).

- [ ] **Step 7: Format and lint**

```bash
task format
task check
```

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/conditional src/crud_views/templates/crud_views/conditional src/crud_views/static/crud_views/js/toggle.js tests/test1/app/models.py tests/test1/test_conditional_toggle.py tests/test1/test_conditional_group.py tests/test1/test_conditional_layout.py tests/test1/test_conditional_exports.py
git commit -m "feat(conditional): add conditional field-group library (toggle, group, layout)"
```

---

### Task 2: Wire conditional formsets into the `FormSets` engine

**Files:**
- Modify: `src/crud_views/lib/formsets/formsets.py`
- Modify: `src/crud_views/lib/formsets/render_tree.py`
- Modify: `src/crud_views/lib/formsets/mixins.py:83` (hand-edit — this file changed on `main` since divergence)
- Modify: `src/crud_views/static/crud_views/js/formset.js`
- Modify: `src/crud_views/templates/crud_views/formsets/formsets.html`
- Modify: `tests/test1/app/views_formset.py`
- Test: `tests/test1/test_conditional_formset.py`, `tests/test1/test_formsets.py`

**Interfaces:**
- Consumes: `ConditionalFormSet`, `ToggleSource` from Task 1's `crud_views.lib.conditional`.
- Produces: `FormSet.conditional: ConditionalFormSet | None` field, `FormSets.apply_conditional(main_form)`, `XFormSet.cv_active: bool` and `XFormSet.cv_toggle_field: str` — consumed by Task 3's `checks.py` (`formset.conditional`, `formset.children`) and Task 4's example app (`conditional=ConditionalFormSet(...)` on a `FormSet`).

- [ ] **Step 1: Port the test file (expect it to fail — `FormSet` has no `conditional` field yet)**

```bash
git show feat/conditional-field-groups:tests/test1/test_conditional_formset.py > tests/test1/test_conditional_formset.py
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_formset.py -v`
Expected: FAIL — `TypeError` / pydantic validation error on `FormSet(..., conditional=...)` (unknown field) or `AttributeError: 'FormSets' object has no attribute 'apply_conditional'`.

- [ ] **Step 3: Port `formsets.py` and `render_tree.py` (full overwrite — identical to `main` at the branch's merge-base, safe)**

```bash
git show feat/conditional-field-groups:src/crud_views/lib/formsets/formsets.py > src/crud_views/lib/formsets/formsets.py
git show feat/conditional-field-groups:src/crud_views/lib/formsets/render_tree.py > src/crud_views/lib/formsets/render_tree.py
```

- [ ] **Step 4: Hand-edit `mixins.py` — add the one-line hook (do NOT overwrite the file; it has unrelated check-ID changes on `main`)**

In `src/crud_views/lib/formsets/mixins.py`, find `cv_form_is_valid` and change:

```python
        # order-independent: a child formset's clean() may add_error() to a parent form,
        # which a single-pass tally would miss. See FormSets.all_valid().
        # Evaluate eagerly (do not short-circuit on form_valid) so formset error state is
        # always populated for the re-rendered page, matching the prior behavior.
        all_formsets_valid = formsets.all_valid()
        return form_valid and all_formsets_valid
```

to:

```python
        # Evaluate conditional formsets from the submitted main form (server authority).
        formsets.apply_conditional(context["form"])

        # order-independent: a child formset's clean() may add_error() to a parent form,
        # which a single-pass tally would miss. See FormSets.all_valid().
        # Evaluate eagerly (do not short-circuit on form_valid) so formset error state is
        # always populated for the re-rendered page, matching the prior behavior.
        all_formsets_valid = formsets.all_valid()
        return form_valid and all_formsets_valid
```

- [ ] **Step 5: Port the JS and template (full overwrite — both identical to `main` at the branch's merge-base, safe)**

```bash
git show feat/conditional-field-groups:src/crud_views/static/crud_views/js/formset.js > src/crud_views/static/crud_views/js/formset.js
git show feat/conditional-field-groups:src/crud_views/templates/crud_views/formsets/formsets.html > src/crud_views/templates/crud_views/formsets/formsets.html
```

- [ ] **Step 6: Apply the `form_tag=False` fix to the test app's formset parent form**

In `tests/test1/app/views_formset.py`, in `PublisherFormSetForm`, add a `helper` property right after `get_layout_fields`:

```python
    def get_layout_fields(self):
        return [Row(Column4("name")), Formsets()]

    @property
    def helper(self):
        # The CRUD create/update template already wraps fields in <form class="cv-form">.
        # Without form_tag=False crispy nests a second <form>, which breaks formset.js.
        h = super().helper
        h.form_tag = False
        return h
```

- [ ] **Step 7: Port the `test_formsets.py` regression test for the same fix**

Add `import re` to the top-level imports of `tests/test1/test_formsets.py` (alongside the existing `import pytest`), then add this test right before `test_create_with_nested_formsets`:

```python
@pytest.mark.django_db
def test_formset_create_page_has_no_nested_form(client_user_publisher_formset: Client, cv_publisher_formset):
    """A formset parent form must not emit its own <form> tag.

    The CRUD create/update template already wraps the fields in
    ``<form class="cv-form">``. If the form's crispy helper leaves
    ``form_tag=True`` (the crispy default), a second <form> is nested inside
    cv-form; the browser then closes cv-form early and ``formset.js`` — which
    binds add/reorder handlers to ``form.cv-form`` — can no longer manage the
    formset (rows can't be added). Guard against that regression here.
    """
    response = client_user_publisher_formset.get("/publisher-formset/create/")
    assert response.status_code == 200
    html = response.content.decode("utf-8", "replace")
    start = html.find('class="cv-form"')
    assert start != -1, "cv-form not found on the formset create page"
    # cv-form's own "<form" opening is before its class attribute, so any "<form"
    # found from the class attribute onward is a nested form.
    nested = len(re.findall(r"<form\b", html[start:]))
    assert nested == 0, f"formset parent form nested {nested} <form> tag(s) inside cv-form"
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `cd tests && pytest test1/test_conditional_formset.py test1/test_formsets.py -v`
Expected: PASS — all tests green.

- [ ] **Step 9: Run the full core test suite to check for regressions**

Run: `cd tests && pytest`
Expected: PASS — no regressions from the `mixins.py` hook or the `formsets.html`/`formset.js` changes.

- [ ] **Step 10: Format, lint, commit**

```bash
task format
task check
git add src/crud_views/lib/formsets src/crud_views/static/crud_views/js/formset.js src/crud_views/templates/crud_views/formsets/formsets.html tests/test1/app/views_formset.py tests/test1/test_conditional_formset.py tests/test1/test_formsets.py
git commit -m "feat(conditional): gate first-level formsets behind a toggle (skip/purge)"
```

---

### Task 3: System checks for conditional groups and formsets

**Files:**
- Modify: `src/crud_views/checks.py`
- Test: `tests/test1/test_conditional_checks.py`

**Interfaces:**
- Consumes: `FormSet.conditional`, `FormSet.children` (Task 2); `ConditionalGroup`, `ConditionalGroupFormMixin` (Task 1).
- Produces: `crud_views.checks._conditional_messages(...)`, `crud_views.checks.check_conditional(...)` registered under `@register(TAG)`; check IDs `crud_views.E310`, `crud_views.E311`, `crud_views.W320`.

- [ ] **Step 1: Port the test file (expect it to fail — `check_conditional` doesn't exist yet)**

```bash
git show feat/conditional-field-groups:tests/test1/test_conditional_checks.py > tests/test1/test_conditional_checks.py
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tests && pytest test1/test_conditional_checks.py -v`
Expected: FAIL — `ImportError: cannot import name '_conditional_messages' from 'crud_views.checks'`

- [ ] **Step 3: Port `checks.py` (full overwrite — identical to `main` at the branch's merge-base, safe)**

```bash
git show feat/conditional-field-groups:src/crud_views/checks.py > src/crud_views/checks.py
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_conditional_checks.py -v`
Expected: PASS — all tests green.

- [ ] **Step 5: Run the full core test suite**

Run: `cd tests && pytest`
Expected: PASS — no regressions. This exercises `check_viewsets` and `check_ordered_model_installed` alongside the new `check_conditional`.

- [ ] **Step 6: Format, lint, commit**

```bash
task format
task check
git add src/crud_views/checks.py tests/test1/test_conditional_checks.py
git commit -m "feat(conditional): system checks for nested-formset misuse, missing toggles, non-nullable clears"
```

---

### Task 4: New example app `examples/bootstrap5/conditional/`

**Files:**
- Create: `examples/bootstrap5/conditional/__init__.py`
- Create: `examples/bootstrap5/conditional/apps.py`
- Create: `examples/bootstrap5/conditional/models.py`
- Create: `examples/bootstrap5/conditional/views.py`
- Create: `examples/bootstrap5/conditional/urls.py`
- Create: `examples/bootstrap5/conditional/seed.py`
- Create: `examples/bootstrap5/conditional/tests.py`
- Create: `examples/bootstrap5/conditional/migrations/__init__.py`
- Modify: `examples/bootstrap5/project/features.py`
- Modify: `examples/bootstrap5/project/settings.py`
- Modify: `examples/bootstrap5/project/urls.py`

**Interfaces:**
- Consumes: `ConditionalGroupModelForm`, `ConditionalGroup`, `ToggleGroup`, `ModelFieldToggle`, `ConditionalFormSet` from `crud_views.lib.conditional` (Task 1); `FormSet.conditional=` (Task 2).
- Produces: `conditional.models.{Registration, Event, Session}`, `conditional.views.{cv_registration, cv_event}` — no other task depends on these.

- [ ] **Step 1: Write the app scaffolding**

`examples/bootstrap5/conditional/__init__.py` (empty file):

```python
```

`examples/bootstrap5/conditional/apps.py`:

```python
from django.apps import AppConfig


class ConditionalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "conditional"
```

- [ ] **Step 2: Write the models**

`examples/bootstrap5/conditional/models.py`:

```python
from django.db import models


class Registration(models.Model):
    name = models.CharField(max_length=100)
    with_company = models.BooleanField(default=False, verbose_name="I represent a company")
    company_name = models.CharField(max_length=200, blank=True, null=True)
    vat_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=100)
    with_sessions = models.BooleanField(default=False, verbose_name="This event has sessions")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
```

- [ ] **Step 3: Write the views**

`examples/bootstrap5/conditional/views.py`:

```python
from collections import OrderedDict

import django_tables2 as tables
from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory

from crud_views.lib.conditional import (
    ConditionalFormSet,
    ConditionalGroup,
    ConditionalGroupModelForm,
    ModelFieldToggle,
    ToggleGroup,
)
from crud_views.lib.crispy import Column6, Column8, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, Formsets, InlineFormSet
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

from conditional.models import Event, Registration, Session

# ---------------- Kind 1: conditional field-group ----------------

cv_registration = ViewSet(model=Registration, name="registration", icon_header="fa-solid fa-user-plus")


class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),
            fields=["company_name", "vat_id"],
            required=["company_name"],  # vat_id stays optional even when on
        ),
    ]

    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [
            Row(Column6("name")),
            Row(Column6("with_company")),
            ToggleGroup(
                "with_company",
                Row(Column6("company_name"), Column6("vat_id")),
                legend="Company details",
            ),
        ]


class RegistrationTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_company = tables.Column()


class RegistrationListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_registration
    table_class = RegistrationTable


class RegistrationDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_registration
    cv_property_display = [
        {
            "title": "Registration",
            "icon": "user-plus",
            "properties": ["id", "name", "with_company", "company_name", "vat_id"],
        },
    ]


class RegistrationCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = RegistrationForm
    cv_message = "Created registration »{object}«"


class RegistrationUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = RegistrationForm
    cv_message = "Updated registration »{object}«"


class RegistrationDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_registration
    form_class = CrispyDeleteForm
    cv_message = "Deleted registration »{object}«"


# ---------------- Kind 2: conditional first-level formset ----------------

cv_event = ViewSet(model=Event, name="event", icon_header="fa-solid fa-calendar")


class EventForm(CrispyModelForm):
    class Meta:
        model = Event
        fields = ["name", "with_sessions"]

    def get_layout_fields(self):
        return [Row(Column6("name")), Row(Column6("with_sessions")), Formsets()]

    @property
    def helper(self):
        # the formsets render their own form tags
        h = super().helper
        h.form_tag = False
        return h


class SessionForm(CrispyModelForm):
    class Meta:
        model = Session
        fields = ["title"]


class SessionInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("title"), self.form_control_col4)]


SessionFormSet = inlineformset_factory(
    Event,
    Session,
    formset=SessionInlineFormSet,
    form=SessionForm,
    fields=["title"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

cv_event_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        sessions=FormSet(
            title="Sessions",
            klass=SessionFormSet,
            fields=["title"],
            pk_field="id",
            # Off => formset hidden & never validated. purge deletes existing rows on save.
            conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="purge"),
        ),
    )
)


class EventTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    with_sessions = tables.Column()


class EventListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_event
    table_class = EventTable


class EventDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_event
    cv_property_display = [
        {
            "title": "Event",
            "icon": "calendar",
            "properties": ["id", "name", "with_sessions", {"path": "session_count", "detail": "Number of sessions"}],
        },
    ]

    def session_count(self, instance):
        return instance.sessions.count()


class EventCreateView(CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_formsets: FormSets = cv_event_formsets
    cv_message = "Created event »{object}«"


class EventUpdateView(CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_formsets: FormSets = cv_event_formsets
    cv_message = "Updated event »{object}«"


class EventDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_event
    form_class = CrispyDeleteForm
    cv_message = "Deleted event »{object}«"
```

- [ ] **Step 4: Write `urls.py`**

`examples/bootstrap5/conditional/urls.py`:

```python
from conditional.views import cv_event, cv_registration

urlpatterns = cv_registration.urlpatterns + cv_event.urlpatterns
```

- [ ] **Step 5: Write `seed.py`**

`examples/bootstrap5/conditional/seed.py`:

```python
from django.contrib.auth import get_user_model

from conditional.models import Event, Registration, Session
from project.seeding import grant_model_perms


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        for model in (Registration, Event, Session):
            grant_model_perms(user, model)

    Registration.objects.get_or_create(name="Jane Doe", defaults={"with_company": False})
    Registration.objects.get_or_create(
        name="Acme Corp Attendee",
        defaults={"with_company": True, "company_name": "Acme Corp", "vat_id": "DE123456789"},
    )

    event, _ = Event.objects.get_or_create(name="Annual Conference", defaults={"with_sessions": True})
    for title in ("Opening Keynote", "Deep Dive Workshop", "Closing Panel"):
        Session.objects.get_or_create(event=event, title=title)
    Event.objects.get_or_create(name="Simple Meetup", defaults={"with_sessions": False})
```

- [ ] **Step 6: Register the app — `INSTALLED_APPS`, root `urls.py`, `FEATURES`**

In `examples/bootstrap5/project/settings.py`, append `"conditional"` to `INSTALLED_APPS` (after `"object_detail"`):

```python
    "showcase",
    "object_detail",
    "conditional",
]
```

In `examples/bootstrap5/project/urls.py`, append after the `object-detail/` include:

```python
urlpatterns += [path("object-detail/", include("object_detail.urls"))]
urlpatterns += [path("conditional/", include("conditional.urls"))]
```

In `examples/bootstrap5/project/features.py`, append to the `FEATURES` list (before the closing `]`):

```python
    Feature(
        app="conditional",
        title="Conditional",
        badge="NEW",
        description="A checkbox toggle reveals a field-group or an entire formset, enforced server-side.",
        about=(
            "Two ways a checkbox can govern what's on the form. Registration reveals a fieldset of company "
            "billing details only when 'I represent a company' is ticked, validated and cleared server-side "
            "regardless of JavaScript. Event goes further: ticking 'This event has sessions' reveals the "
            "entire Sessions formset, and untoggling it purges any existing sessions on save."
        ),
        look_at=(
            "RegistrationForm.cv_conditional_groups and its ToggleGroup(..., legend=...) layout; "
            "cv_event_formsets' ConditionalFormSet(toggle=ModelFieldToggle('with_sessions'), on_off='purge')."
        ),
        url_name="registration-list",
        icon="fa-solid fa-toggle-on",
    ),
```

- [ ] **Step 7: Generate migrations**

```bash
cd examples/bootstrap5
mkdir -p conditional/migrations
touch conditional/migrations/__init__.py
uv run manage.py makemigrations conditional
```

Expected: `Migrations for 'conditional': conditional/migrations/0001_initial.py` creating `Registration`, `Event`, `Session`.

- [ ] **Step 8: Write the example app's tests**

`examples/bootstrap5/conditional/tests.py`:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from conditional.models import Event, Registration, Session
from project.testing import field_key, form_payload


class ConditionalTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)


class RegistrationConditionalGroupTest(ConditionalTestCase):
    def test_list_renders_with_snippets(self):
        Registration.objects.create(name="Jane Doe")
        resp = self.client.get(reverse("registration-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Jane Doe")
        self.assertContains(resp, "snippet-panels")

    def test_create_without_company_leaves_company_fields_blank(self):
        resp = self.client.get(reverse("registration-create"))
        payload = form_payload(resp)
        payload["name"] = "Jane Doe"
        resp = self.client.post(reverse("registration-create"), payload)
        self.assertEqual(resp.status_code, 302)
        registration = Registration.objects.get(name="Jane Doe")
        self.assertFalse(registration.with_company)
        self.assertIsNone(registration.company_name)

    def test_create_with_company_requires_company_name(self):
        resp = self.client.get(reverse("registration-create"))
        payload = form_payload(resp)
        payload["name"] = "Acme Attendee"
        payload["with_company"] = "on"
        resp = self.client.post(reverse("registration-create"), payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("company_name", resp.context["form"].errors)

    def test_create_with_company_success(self):
        resp = self.client.get(reverse("registration-create"))
        payload = form_payload(resp)
        payload["name"] = "Acme Attendee"
        payload["with_company"] = "on"
        payload["company_name"] = "Acme Corp"
        resp = self.client.post(reverse("registration-create"), payload)
        self.assertEqual(resp.status_code, 302)
        registration = Registration.objects.get(name="Acme Attendee")
        self.assertEqual(registration.company_name, "Acme Corp")

    def test_toggle_off_clears_company_fields(self):
        registration = Registration.objects.create(
            name="Toggle Test", with_company=True, company_name="Old Co", vat_id="X1"
        )
        url = reverse("registration-update", kwargs={"pk": registration.pk})
        resp = self.client.get(url)
        payload = form_payload(resp)
        payload.pop("with_company", None)
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        registration.refresh_from_db()
        self.assertFalse(registration.with_company)
        self.assertIsNone(registration.company_name)


class EventConditionalFormsetTest(ConditionalTestCase):
    def test_create_with_sessions_off_skips_formset(self):
        resp = self.client.get(reverse("event-create"))
        payload = form_payload(resp)
        payload["name"] = "Simple Meetup"
        # with_sessions checkbox not in payload => off
        resp = self.client.post(reverse("event-create"), payload)
        self.assertEqual(resp.status_code, 302)
        event = Event.objects.get(name="Simple Meetup")
        self.assertEqual(event.sessions.count(), 0)

    def test_create_with_sessions_on_validates_formset(self):
        resp = self.client.get(reverse("event-create"))
        payload = form_payload(resp)
        payload["name"] = "Annual Conference"
        payload["with_sessions"] = "on"
        payload[field_key(payload, "-title")] = "Opening Keynote"
        resp = self.client.post(reverse("event-create"), payload)
        self.assertEqual(
            resp.status_code,
            302,
            getattr(resp, "context", None) and str(resp.context.get("form") and resp.context["form"].errors),
        )
        event = Event.objects.get(name="Annual Conference")
        self.assertTrue(event.sessions.filter(title="Opening Keynote").exists())

    def test_toggle_off_purges_existing_sessions(self):
        event = Event.objects.create(name="To Purge", with_sessions=True)
        Session.objects.create(event=event, title="Existing Session")

        url = reverse("event-update", kwargs={"pk": event.pk})
        resp = self.client.get(url)
        payload = form_payload(resp)
        payload.pop("with_sessions", None)

        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 302)
        event.refresh_from_db()
        self.assertFalse(event.with_sessions)
        self.assertEqual(event.sessions.count(), 0)


class ConditionalSeedTest(TestCase):
    def test_seed_twice(self):
        from django.core.management import call_command

        call_command("seed")
        counts = (Registration.objects.count(), Event.objects.count(), Session.objects.count())
        call_command("seed")
        self.assertEqual(
            (Registration.objects.count(), Event.objects.count(), Session.objects.count()), counts
        )
        self.assertGreater(Registration.objects.count(), 0)
```

- [ ] **Step 9: Run the example app's tests**

```bash
cd examples/bootstrap5
uv run manage.py migrate
uv run pytest conditional/tests.py project/tests.py -v
```

Expected: PASS — including `project/tests.py`'s generic `HomePageTest`/`FeatureRegistryTest`/`ExampleAboutTest`/`SystemChecksTest`, which automatically pick up the new `Feature` entry.

- [ ] **Step 10: Manual smoke check**

```bash
cd examples/bootstrap5
uv run manage.py seed
uv run manage.py runserver 0.0.0.0:8000 &
sleep 2
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/conditional/registration/
kill %1
```

Expected: `302` (redirect to login for an anonymous request) — confirms the URL resolves and the view doesn't 500.

- [ ] **Step 11: Format, lint, commit**

```bash
task format
task check
git add examples/bootstrap5/conditional examples/bootstrap5/project/features.py examples/bootstrap5/project/settings.py examples/bootstrap5/project/urls.py
git commit -m "docs(examples): add conditional example app (field-group + formset toggle)"
```

---

### Task 5: Documentation and CHANGELOG

**Files:**
- Create/Modify: `docs/reference/conditional.md`
- Modify: `docs/reference/.pages`
- Modify: `docs/faq.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing from other tasks (prose-only), but references the app built in Task 4 by name/path.

- [ ] **Step 1: Port `conditional.md` and update its Examples section**

```bash
git show feat/conditional-field-groups:docs/reference/conditional.md > docs/reference/conditional.md
```

Then edit the file's final section, replacing:

```markdown
## Examples

Runnable bootstrap5 examples with both kinds are provided in the test project:

- `cv_registration` — field-group with `ModelFieldToggle` (`with_company` → `company_name`, `vat_id`)
- `cv_event` — conditional first-level formset (`with_sessions` → sessions formset, `on_off="skip"`)
```

with:

```markdown
## Examples

The `examples/bootstrap5/conditional/` app (`conditional/views.py`) shows both kinds side by side:

- `cv_registration` — field-group with `ModelFieldToggle` (`with_company` → `company_name`, `vat_id`), rendered as a titled `<fieldset>` via `ToggleGroup(..., legend="Company details")`
- `cv_event` — conditional first-level formset (`with_sessions` → the `sessions` formset, `on_off="purge"`)
```

- [ ] **Step 2: Add the nav entry**

In `docs/reference/.pages`, change:

```yaml
    - settings.md
    - ...
```

to:

```yaml
    - settings.md
    - Conditional groups: conditional.md
    - ...
```

- [ ] **Step 3: Port the FAQ entry, then fix its stale example**

```bash
git show feat/conditional-field-groups:docs/faq.md > docs/faq.md
```

The branch's own FAQ entry never got updated for the `legend=`/fieldset feature that landed later in its history — fix that now. Replace:

```python
    def get_layout_fields(self):
        return [Row(Column6("name"), Column6("with_company")),
                ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id")))]
```

with:

```python
    def get_layout_fields(self):
        return [
            Row(Column6("name")),
            Row(Column6("with_company")),
            ToggleGroup(
                "with_company",
                Row(Column6("company_name"), Column6("vat_id")),
                legend="Company details",
            ),
        ]
```

- [ ] **Step 4: Add the CHANGELOG bullet**

In `CHANGELOG.md`, under `## Unreleased` → `### Added`, change:

```markdown
### Added

- Community-health files for the repository: a Contributor Covenant Code of
  Conduct, a contributing guide, a security policy, GitHub issue forms (bug
  report / feature request), and a pull request template. These satisfy the
  GitHub community-standards checklist and do not affect the package.

### Changed
```

to:

```markdown
### Added

- Community-health files for the repository: a Contributor Covenant Code of
  Conduct, a contributing guide, a security policy, GitHub issue forms (bug
  report / feature request), and a pull request template. These satisfy the
  GitHub community-standards checklist and do not affect the package.
- Conditional field-groups and conditional formsets: a checkbox toggle can hide a group of fields (or an entire first-level formset). When off, validation is skipped and values are cleared (formsets: `skip` keeps rows, `purge` deletes them). Enforced server-side; bundled `toggle.js` handles show/hide only. See `docs/reference/conditional.md`.

### Changed
```

- [ ] **Step 5: Verify no stale signature remains and the nav file is valid YAML**

```bash
grep -n 'ToggleGroup("with_company", Row(Column6' docs/faq.md
```

Expected: no output (the single-row, no-legend call is gone).

```bash
python3 -c "import yaml; yaml.safe_load(open('docs/reference/.pages'))" && echo OK
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add docs/reference/conditional.md docs/reference/.pages docs/faq.md CHANGELOG.md
git commit -m "docs(conditional): document conditional field-groups and formsets"
```

---

### Task 6: Full verification and completeness check

**Files:** none (verification only)

- [ ] **Step 1: Run the full core test suite**

```bash
cd tests && pytest
```

Expected: PASS, all tests green, coverage at or above the `fail_under = 88` gate.

- [ ] **Step 2: Run the full examples test suite**

```bash
cd examples/bootstrap5 && uv run pytest
```

Expected: PASS, all tests green (including every other feature app's existing tests — confirms no regression from the `formsets.html`/`formset.js`/`mixins.py` changes).

- [ ] **Step 3: Run the nox matrix** (or at minimum the fastest cell, if the full matrix is too slow to run locally)

```bash
task test
```

Expected: PASS across the Python/Django matrix.

- [ ] **Step 4: Confirm nothing from the original branch's `conditional` package was lost**

```bash
diff <(git show feat/conditional-field-groups:src/crud_views/lib/conditional/__init__.py) src/crud_views/lib/conditional/__init__.py
diff <(git show feat/conditional-field-groups:src/crud_views/lib/conditional/toggle.py) src/crud_views/lib/conditional/toggle.py
diff <(git show feat/conditional-field-groups:src/crud_views/lib/conditional/group.py) src/crud_views/lib/conditional/group.py
diff <(git show feat/conditional-field-groups:src/crud_views/lib/conditional/layout.py) src/crud_views/lib/conditional/layout.py
diff <(git show feat/conditional-field-groups:src/crud_views/lib/conditional/formset.py) src/crud_views/lib/conditional/formset.py
```

Expected: no output from any `diff` — the ported files are byte-identical to the branch's final state.

- [ ] **Step 5: Final format/lint pass and push**

```bash
task format
task check
git push -u origin feat/integrate-conditional-field-groups
```

- [ ] **Step 6: Open a PR**

Use `superpowers:finishing-a-development-branch` to decide merge/PR flow, following the project's established PR lifecycle (project memory: PR → wait for CI → fix ruff if needed → squash-merge to `main` → wait for `main` CI green).

---

### Task 7: Port the skill update to the external skills monorepo (follow-up, separate repo)

**Files (in `/home/alex/projects/alex/skills`, NOT this repo):**
- Modify: `plugins/django-crud-views/skills/django-crud-views/SKILL.md`
- Modify: `plugins/django-crud-views/skills/django-crud-views/references/api-reference.md`

This task does not block Task 6's PR — it is a follow-up in a different repository with its own commit-directly-to-`main` workflow (project memory: `skills-monorepo-location`).

- [ ] **Step 1: Add the SKILL.md section**

In `/home/alex/projects/alex/skills/plugins/django-crud-views/skills/django-crud-views/SKILL.md`, find the `## Formsets (Inline Child Records)` section and insert this new section immediately after it (before the next `---`/`## Polymorphic Models` heading):

```markdown
## Conditional Field-Groups & Conditional FormSets

A checkbox toggle can hide a group of fields (or an entire **first-level** formset). When off, the group/formset is hidden client-side and — authoritatively **server-side** — skips validation and clears its data. JS is cosmetic only; the server enforces the contract on every submit (tampered/JS-off POSTs included).

Import from `crud_views.lib.conditional`.

**Kind 1 — field-group in a form** (`ConditionalGroupModelForm` + `ToggleGroup`):

```python
from crud_views.lib.conditional import (
    ConditionalGroupModelForm, ConditionalGroup, ToggleGroup, ModelFieldToggle,
)

class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),   # or UIFieldToggle("...") for a non-model checkbox
            fields=["company_name", "vat_id"],
            required=["company_name"],                  # subset required when toggle is on
        ),
    ]
    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [Row(Column6("name")),
                Row(Column6("with_company")),
                ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id")),
                            legend="Company details")]  # legend=… renders the group as a titled <fieldset>
```

Off ⇒ group fields are cleared (must be `null=True, blank=True`, or pass `empty_values=`). On ⇒ `required` fields enforced.

**Kind 2 — an entire first-level formset** (`ConditionalFormSet` on a `FormSet`):

```python
from crud_views.lib.conditional import ConditionalFormSet, ModelFieldToggle

sessions=FormSet(
    title="Sessions", klass=SessionFormSet, fields=["title"], pk_field="id",
    conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="skip"),
)
```

The parent-form toggle (`with_sessions`) governs the whole formset. `on_off="skip"` (default) leaves existing rows untouched when off; `on_off="purge"` deletes them on save. Only **first-level** formsets may be conditional (nested ⇒ check error `crud_views.E310`).

System checks: `crud_views.E310` (conditional on nested formset), `crud_views.E311` (toggle field missing from form), `crud_views.W320` (cleared field not null/blank).

---
```

- [ ] **Step 2: Add the api-reference.md section and import list entry**

In `/home/alex/projects/alex/skills/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md`, insert this section right after `## Formsets` / before `## Polymorphic Models`:

```markdown
## Conditional Field-Groups

Import all from `crud_views.lib.conditional`.

### Toggle sources

| Class | `inject` | Purpose |
|---|---|---|
| `ToggleSource` | base | Base class; override `is_on(form)` |
| `ModelFieldToggle(name)` | `False` | Toggle backed by a real model/form field |
| `UIFieldToggle(name)` | `True` | Toggle backed by a transient checkbox auto-injected by the mixin |

### `ConditionalGroup`

```python
ConditionalGroup(
    toggle: ToggleSource,
    fields: list[str],               # all fields in the group
    required: list[str] | None,      # required when on (defaults to all fields)
    empty_values: dict[str, Any],    # override cleared value per field (default None)
)
```

### `ConditionalGroupFormMixin` / `ConditionalGroupModelForm`

| Name | Base | Notes |
|---|---|---|
| `ConditionalGroupFormMixin` | — | Mix in before the form base; owns `clean()` authority |
| `ConditionalGroupModelForm` | `ConditionalGroupFormMixin, CrispyModelForm` | Ready-to-use form class |

Declare `cv_conditional_groups: list[ConditionalGroup] = [...]` on the form class.

### `ToggleGroup`

```python
ToggleGroup(toggle_field: str, *fields, css_class: str | None = None, legend: str | None = None)
```

Crispy layout element. By default renders a `<div cv-data-toggle-group cv-data-toggle-field="…">` wrapper that `toggle.js` shows/hides based on the toggle field's value. Pass `legend="…"` to render a titled `<fieldset><legend>…</legend>…</fieldset>` instead (the marker sits on the fieldset, so the whole group hides when off). No custom JavaScript required.

### `ConditionalFormSet`

```python
ConditionalFormSet(
    toggle: ToggleSource,           # governs the whole formset
    on_off: Literal["skip", "purge"] = "skip",
)
```

Attach via `conditional=` on a first-level `FormSet`. `skip` leaves existing rows untouched when off; `purge` deletes them on save.

**System checks:** `crud_views.E310` (on a nested formset), `crud_views.E311` (toggle field absent from parent form), `crud_views.W320` (cleared field not null/blank).

---
```

Then find the "public imports" cheat-sheet block that ends with the `# Formsets` import line, and add right after it:

```python
# Conditional field-groups / formsets
from crud_views.lib.conditional import (
    ToggleSource, ModelFieldToggle, UIFieldToggle,
    ConditionalGroup, ConditionalGroupFormMixin, ConditionalGroupModelForm,
    ToggleGroup, ConditionalFormSet,
)
```

- [ ] **Step 3: Commit and push in the skills repo (single invocation — cwd resets between Bash calls)**

```bash
git -C /home/alex/projects/alex/skills add plugins/django-crud-views/skills/django-crud-views/SKILL.md plugins/django-crud-views/skills/django-crud-views/references/api-reference.md
git -C /home/alex/projects/alex/skills commit -m "docs(django-crud-views): document conditional field-groups and formsets"
git -C /home/alex/projects/alex/skills push
git -C /home/alex/projects/alex/skills rev-parse HEAD
git -C /home/alex/projects/alex/skills rev-parse origin/main
```

Expected: the last two commands print the same commit hash (local `HEAD` matches pushed `origin/main`).

---

## Done when

- All seven tasks' checkboxes are complete.
- `cd tests && pytest` and `cd examples/bootstrap5 && uv run pytest` are both fully green.
- The Task 6 completeness diffs are empty for every file in `src/crud_views/lib/conditional/`.
- `examples/bootstrap5/conditional/` appears on the home page and both its ViewSets are reachable.
- `docs/reference/conditional.md`, `docs/faq.md`, `CHANGELOG.md` are updated and internally consistent (no stale pre-`legend` `ToggleGroup` call anywhere).
- The skills-monorepo commit (Task 7) is pushed and `HEAD == origin/main` there.
