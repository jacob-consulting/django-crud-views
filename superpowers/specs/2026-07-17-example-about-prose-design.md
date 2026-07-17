# Example "About this example" prose — design spec

**Date:** 2026-07-17
**Status:** approved design, ready for implementation plan
**Scope:** `examples/bootstrap5/` only (no package changes, no release)

## Goal

Every crud_views example page already renders **"The code behind this page"** (the app's real
`models.py`/`views.py` via pygments). But a visitor landing on, say, `/polymorphic/` still has to
*guess* what the example is demonstrating — the title alone ("Polymorphic") only helps if you already
know the concept.

Add a short **prose explanation to every example page** so the page explains itself: what this example
is for, and where to look in the code.

## Current state

- `project/features.py` defines a frozen `Feature(app, title, description, url_name, icon)` dataclass and a
  `FEATURES` list with one entry per example app. The `description` is a terse one-liner shown **only** on
  the home-page cards.
- `project/crud_views.html` is the `CRUD_VIEWS_EXTENDS` base every crud_views page extends. Its
  `{% block content %}` renders the CRUD card, then `{% snippet_panels %}`.
- `project/templatetags/example_tags.py` has `snippet_panels` (a `takes_context=True` inclusion tag) which
  resolves the current view's app via `_feature_app_for(view)` (`type(view).__module__.split(".")[0]`,
  gated on membership in `{f.app for f in FEATURES}`), then renders `<app>/models.py` + `<app>/views.py`.
  `project/templates/project/snippet_panels.html` renders the accordion under the id `snippet-panels`.

The plumbing to resolve "which feature does this page belong to" already exists — this feature reuses it.

## Design

### 1. Data: two new `Feature` fields

`Feature` gains two **required** fields (no defaults):

```python
@dataclass(frozen=True)
class Feature:
    app: str
    title: str
    description: str   # terse one-liner — home-page cards (unchanged)
    about: str         # NEW: 2-4 sentence teaching paragraph — shown on every page of the app
    look_at: str       # NEW: one-sentence code pointer — shown next to "The code behind this page"
    url_name: str
    icon: str
```

Required (not `= ""`) so all eight entries must supply them and a test can assert each is non-empty — no
example ships without an explanation. The one-liner `description` stays exactly as-is for the dense
home-card grid.

### 2. Rendering

Both pieces are resolved from the current view's app, the same way `snippet_panels` already does.
Generalise the existing helper:

```python
def _feature_for(view) -> Feature | None:
    """The Feature a view class belongs to, or None for non-feature views."""
    from project.features import FEATURES
    app = type(view).__module__.split(".")[0]
    return next((f for f in FEATURES if f.app == app), None)
```

`_feature_app_for` is re-expressed in terms of it (or replaced; `snippet_panels` only needs the app name).

**Top callout** — a new inclusion tag:

```python
@register.inclusion_tag("project/example_about.html", takes_context=True)
def example_about(context):
    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    return {"feature": feature}
```

`project/templates/project/example_about.html` renders a light, bordered callout (not a loud alert, so it
doesn't compete with the CRUD card) — rendering **nothing** when there is no feature or `about` is empty:

```html
{% if feature.about %}
    <div class="alert alert-light border d-flex gap-3 mb-4" id="example-about">
        <i class="fa-solid fa-circle-info fs-4 text-secondary mt-1"></i>
        <div>
            <h6 class="mb-1">About this example — {{ feature.title }}</h6>
            <p class="mb-0">{{ feature.about }}</p>
        </div>
    </div>
{% endif %}
```

In `project/crud_views.html`, render it as the first thing inside `{% block content %}`, above the CRUD card:

```html
{% block content %}

    {% example_about %}

    <div class="card">
    ...
```

**"Look at:" line** — `snippet_panels` is extended to also pass the pointer:

```python
@register.inclusion_tag("project/snippet_panels.html", takes_context=True)
def snippet_panels(context):
    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    app = feature.app if feature else None
    panels = [...]  # unchanged
    return {"panels": panels, "look_at": feature.look_at if feature else ""}
```

`snippet_panels.html` renders the pointer between the "The code behind this page" heading and the accordion:

```html
{% if panels %}
    <div class="mt-4" id="snippet-panels">
        <h5><i class="fa-solid fa-code"></i> The code behind this page</h5>
        {% if look_at %}
            <p class="text-body-secondary"><strong>Look at:</strong> {{ look_at }}</p>
        {% endif %}
        <div class="accordion" id="snippetAccordion">
        ...
```

### 3. Empty / non-feature handling

Both tags render nothing when the view has no feature (the crud_views `manage` view, or any future
non-feature crud page) or when the value is empty — identical to today's `snippet_panels` behaviour. No
page breaks if a blurb is missing; the non-empty test is what guarantees they're present for real features.

### 4. Content — the eight blurbs

`about` = the prose paragraph (top callout). `look_at` = the code pointer (with the code panel). Verified
against the real symbol names in each app's `views.py` / `models.py`.

**library** (Library)
- **about:** "The starting point: a plain CRUD interface built from a ViewSet. Authors and books each get a list, detail, create, update and delete view that link to one another and respect Django's permissions. The author list adds a django-tables2 table with a django-filter search box; books show manual up/down ordering."
- **look_at:** "the cv_author and cv_book ViewSets and their List/Detail/Create/Update/Delete views; AuthorTable and AuthorFilter for the table and filter; BookUpView / BookDownView for ordering."

**nested** (Nested)
- **about:** "ViewSets that nest inside a parent. A Company owns Departments, a Department owns Employees, and a Company also owns Offices. Each child list is automatically scoped to its parent, and creating a child fills in the parent link for you — notice how the URLs stack the parent keys (company → department → employee)."
- **look_at:** "parent=ParentViewSet(...) on the cv_department / cv_employee / cv_office ViewSets, and CreateViewParentMixin in the create views (it sets the parent foreign key); the stacked company_pk / department_pk URL kwargs."

**formsets** (Formsets)
- **about:** "Editing a record together with its children on one page. A Questionnaire is edited alongside its Questions, and each Question alongside its Choices, using Django inline formsets wired through crud_views' supported FormSetMixin. Add and remove rows without leaving the form."
- **look_at:** "the QuestionInlineFormSet / ChoiceInlineFormSet definitions and the cv_formsets = FormSets(...) tree in views.py, plus FormSetMixin on QuestionnaireCreateView / QuestionnaireUpdateView."

**workflow** (Workflow)
- **about:** "A state machine driving the UI. A Campaign moves through draft → active → complete (or cancelled) using django-fsm transitions, which crud_views renders as action buttons — only the transitions valid from the current state appear. Every transition is recorded as audit history."
- **look_at:** "the FSMField state and the @transition-decorated wf_activate / wf_complete / wf_cancel methods on Campaign in models.py; WorkflowModelMixin for the audit trail; CampaignWorkflowView in views.py."

**polymorphic_demo** (Polymorphic)
- **about:** "One ViewSet over several concrete model types. Vehicle is a django-polymorphic base; Car, Truck and Motorcycle each add their own fields. The list shows all three together, and 'Add' first asks which type you want, then shows that type's own form."
- **look_at:** "the create-select flow — VehicleCreateSelectView (pick a type) → VehicleCreateView — and the polymorphic_forms mapping (POLYMORPHIC_FORMS = {Car: CarForm, Truck: TruckForm, Motorcycle: MotorcycleForm}) in views.py."

**guardian_demo** (Guardian)
- **about:** "Per-object permissions with django-guardian. Documents are owned by individual users: sign in as alice or bob (password same as the username) and each sees only their own documents, except one that is explicitly shared. Creating a document grants its creator full object-level rights."
- **look_at:** "the GuardianViewSet and the Guardian*ViewPermissionRequired views, and DocumentCreateView.cv_form_valid, which assigns object permissions to the creator via cv_document.assign_perm."

**resources** (Resources)
- **about:** "A ViewSet over data that isn't in the database at all. Here the 'records' are entries in a fake S3 bucket held in memory, exposed through crud_views' Resource abstraction — the same list, detail and action UI, with no model or queryset behind it. Useful for external APIs, config trees or object stores."
- **look_at:** "the S3File(Resource) class and its cv_get_items() reading FAKE_BUCKET in views.py; ResourceViewMixin on the views; and the delete and touch actions."

**showcase** (Showcase)
- **about:** "Presentation building blocks gathered in one place. Recipes are shown as a grid of cards instead of a table, the detail page groups fields into labelled fieldsets, deletion happens in a modal, and a custom 'favorite' action toggles a flag straight from the list. Mix these into your own views as needed."
- **look_at:** "RecipeCardListView (the card grid), the cv_property_display fieldset groups on RecipeDetailView, cv_modal on RecipeDeleteView, and the RecipeFavoriteView custom action in views.py."

### 5. Testing (`project/tests.py`)

Extend the existing suite:

- **`test_every_feature_page_shows_about`** — for each `Feature`, `force_login` an admin, GET
  `feature.url_name`, assert status 200, assert the page contains the marker `id="example-about"` (or the
  literal "About this example") and a distinctive substring of `feature.about`.
- **`test_every_feature_declares_about_and_look_at`** — assert `feature.about` and `feature.look_at` are
  both non-empty for every entry (guards against a future app forgetting them).
- **`test_look_at_appears_with_code_panel`** — on one feature landing page, assert the "Look at:" text and a
  substring of that feature's `look_at` appear.
- **`test_example_about_empty_for_non_feature_view`** — unit test mirroring the existing
  `SnippetPanelsTest`: `example_about({"view": HomeView()})["feature"]` is `None`.

## Out of scope (YAGNI)

- **Per-view** prose (one blurb per example, shown on all of that example's pages — not per list/detail/…).
- Markdown / rich formatting in `about` or `look_at` — plain text rendered by Django autoescaping.
- Changing the home-page cards (they keep the terse `description`).
- Any package (`src/`) change.

## File-level change list

- **Modify** `examples/bootstrap5/project/features.py` — add `about` + `look_at` to the dataclass and to all
  eight `FEATURES` entries.
- **Modify** `examples/bootstrap5/project/templatetags/example_tags.py` — add `_feature_for`, the
  `example_about` inclusion tag; extend `snippet_panels` to pass `look_at`.
- **Create** `examples/bootstrap5/project/templates/project/example_about.html`.
- **Modify** `examples/bootstrap5/project/templates/project/crud_views.html` — `{% example_about %}` at the
  top of `{% block content %}`.
- **Modify** `examples/bootstrap5/project/templates/project/snippet_panels.html` — render the "Look at:" line.
- **Modify** `examples/bootstrap5/project/tests.py` — the four tests above.
