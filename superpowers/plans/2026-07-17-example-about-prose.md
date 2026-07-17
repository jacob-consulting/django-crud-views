# Example "About this example" prose — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a short teaching paragraph on every crud_views example page ("About this example") plus a "Look at:" code pointer next to "The code behind this page", so a visitor never has to guess what an example demonstrates.

**Architecture:** Two required fields (`about`, `look_at`) are added to the existing `Feature` dataclass in `project/features.py`. A new `{% example_about %}` inclusion tag renders the top callout; the existing `{% snippet_panels %}` tag is extended to also render the `look_at` line. Both resolve "which feature does this page belong to" from the current view's app the same way `snippet_panels` already does, via a shared `_feature_for(view)` helper.

**Tech Stack:** Django 4.2–6.0 templates + template tags, django-crud-views (this repo), pytest + pytest-django. Example project at `examples/bootstrap5/`.

**Spec:** `superpowers/specs/2026-07-17-example-about-prose-design.md`

## Global Constraints

- All work is under `examples/bootstrap5/` only. No package (`src/`) change. No version bump, no release.
- English only — zero non-English strings.
- ruff: line length 120, double quotes; `ruff format` + `ruff check` must pass. The pre-commit hook is NOT installed in this environment — run `uv run ruff format examples && uv run ruff check --fix examples` from the repo root manually before every commit.
- Run example tests with `uv run` from inside `examples/bootstrap5`: `cd examples/bootstrap5 && uv run pytest`. `pytest.ini` already discovers `tests.py` files (it sets `python_files = test_*.py *_test.py tests.py`), so `project/tests.py` runs.
- Commit with a scoped pathspec (`git add examples/bootstrap5/...`). NEVER `git add -A` at the repo root — there is an untracked `cred.prompt.md` at the repo root that must never be staged. Verify with `git status` before committing.
- Branch: work continues on `m3-examples` (the example work is not yet merged). Do not create a new branch.
- `description` (the terse home-card one-liner) is unchanged. `about`/`look_at` are new and shown only on the example pages.

## File structure (target)

```
examples/bootstrap5/project/
  features.py                         # MODIFY: Feature gains about + look_at; all 8 entries filled
  templatetags/example_tags.py        # MODIFY: add _feature_for + example_about; extend snippet_panels
  templates/project/
    example_about.html                # NEW: the top "About this example" callout
    crud_views.html                   # MODIFY: {% example_about %} at top of block content
    snippet_panels.html               # MODIFY: render the "Look at:" line
  tests.py                            # MODIFY: 4 new tests
```

Interfaces later tasks rely on:

- `project.features.Feature` gains `about: str` and `look_at: str` (both required, no default), positioned between `description` and `url_name`.
- `project.templatetags.example_tags._feature_for(view) -> Feature | None` — returns the `Feature` a view class belongs to (by top-level module name), or `None`.
- `{% example_about %}` inclusion tag → context `{"feature": Feature | None}`, template `project/example_about.html`, renders the marker `id="example-about"` when `feature.about` is set.
- `{% snippet_panels %}` inclusion tag → context now also includes `"look_at": str` (empty for non-feature views).

---

### Task 1: Add `about` + `look_at` to the feature registry

**Files:**
- Modify: `examples/bootstrap5/project/features.py`
- Test: `examples/bootstrap5/project/tests.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Feature.about: str` and `Feature.look_at: str` (required fields, between `description` and `url_name`), populated on all eight `FEATURES` entries.

- [ ] **Step 1: Write the failing test** — append to `examples/bootstrap5/project/tests.py`:

```python
class FeatureRegistryTest(TestCase):
    def test_every_feature_declares_about_and_look_at(self):
        from project.features import FEATURES

        for feature in FEATURES:
            self.assertTrue(feature.about.strip(), f"{feature.app} has no about text")
            self.assertTrue(feature.look_at.strip(), f"{feature.app} has no look_at text")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd examples/bootstrap5 && uv run pytest project/tests.py::FeatureRegistryTest -v`
Expected: FAIL with `AttributeError: 'Feature' object has no attribute 'about'` (the module still imports because no entry passes `about` yet).

- [ ] **Step 3: Add the two fields to the dataclass** — in `examples/bootstrap5/project/features.py`, change the `Feature` definition to:

```python
@dataclass(frozen=True)
class Feature:
    app: str  # python package name of the example app, e.g. "library"
    title: str  # card/nav title on the home page
    description: str  # one-liner on the home page card
    about: str  # 2-4 sentence teaching paragraph shown on every page of the app
    look_at: str  # one-sentence code pointer shown next to "The code behind this page"
    url_name: str  # URL name of the app's landing page, e.g. "author-list"
    icon: str  # font-awesome classes
```

- [ ] **Step 4: Fill all eight entries** — replace the whole `FEATURES` list body with (each entry gains `about=` and `look_at=` between `description` and `url_name`):

```python
FEATURES: list[Feature] = [
    # example feature apps append their entry here
    Feature(
        app="library",
        title="Library",
        description="Plain CRUD — list, detail, create, update, delete — plus tables, filters and ordering.",
        about=(
            "The starting point: a plain CRUD interface built from a ViewSet. Authors and books each get a "
            "list, detail, create, update and delete view that link to one another and respect Django's "
            "permissions. The author list adds a django-tables2 table with a django-filter search box; books "
            "show manual up/down ordering."
        ),
        look_at=(
            "the cv_author and cv_book ViewSets and their List/Detail/Create/Update/Delete views; AuthorTable "
            "and AuthorFilter for the table and filter; BookUpView / BookDownView for ordering."
        ),
        url_name="author-list",
        icon="fa-solid fa-book",
    ),
    Feature(
        app="nested",
        title="Nested",
        description="Parent/child ViewSets with nested URLs: Company → Department → Employee, plus Offices.",
        about=(
            "ViewSets that nest inside a parent. A Company owns Departments, a Department owns Employees, and "
            "a Company also owns Offices. Each child list is automatically scoped to its parent, and creating "
            "a child fills in the parent link for you — notice how the URLs stack the parent keys "
            "(company → department → employee)."
        ),
        look_at=(
            "parent=ParentViewSet(...) on the cv_department / cv_employee / cv_office ViewSets, and "
            "CreateViewParentMixin in the create views (it sets the parent foreign key); the stacked "
            "company_pk / department_pk URL kwargs."
        ),
        url_name="company-list",
        icon="fa-solid fa-sitemap",
    ),
    Feature(
        app="formsets",
        title="Formsets",
        description="Inline formsets: edit a questionnaire with its questions and choices on one page.",
        about=(
            "Editing a record together with its children on one page. A Questionnaire is edited alongside its "
            "Questions, and each Question alongside its Choices, using Django inline formsets wired through "
            "crud_views' supported FormSetMixin. Add and remove rows without leaving the form."
        ),
        look_at=(
            "the QuestionInlineFormSet / ChoiceInlineFormSet definitions and the cv_formsets = FormSets(...) "
            "tree in views.py, plus FormSetMixin on QuestionnaireCreateView / QuestionnaireUpdateView."
        ),
        url_name="questionnaire-list",
        icon="fa-solid fa-list-check",
    ),
    Feature(
        app="workflow",
        title="Workflow",
        description="django-fsm state machine: transitions as form actions, with audit history.",
        about=(
            "A state machine driving the UI. A Campaign moves through draft → active → complete (or "
            "cancelled) using django-fsm transitions, which crud_views renders as action buttons — only the "
            "transitions valid from the current state appear. Every transition is recorded as audit history."
        ),
        look_at=(
            "the FSMField state and the @transition-decorated wf_activate / wf_complete / wf_cancel methods "
            "on Campaign in models.py; WorkflowModelMixin for the audit trail; CampaignWorkflowView in "
            "views.py."
        ),
        url_name="campaign-list",
        icon="fa-solid fa-bullhorn",
    ),
    Feature(
        app="polymorphic_demo",
        title="Polymorphic",
        description="One list over Car, Truck and Motorcycle with type-specific create and update forms.",
        about=(
            "One ViewSet over several concrete model types. Vehicle is a django-polymorphic base; Car, Truck "
            "and Motorcycle each add their own fields. The list shows all three together, and 'Add' first "
            "asks which type you want, then shows that type's own form."
        ),
        look_at=(
            "the create-select flow — VehicleCreateSelectView (pick a type) → VehicleCreateView — and the "
            "polymorphic_forms mapping (POLYMORPHIC_FORMS = {Car: CarForm, Truck: TruckForm, "
            "Motorcycle: MotorcycleForm}) in views.py."
        ),
        url_name="vehicle-list",
        icon="fa-solid fa-car",
    ),
    Feature(
        app="guardian_demo",
        title="Guardian",
        description="Per-object permissions: alice and bob each see their own documents; one is shared.",
        about=(
            "Per-object permissions with django-guardian. Documents are owned by individual users: sign in as "
            "alice or bob (password same as the username) and each sees only their own documents, except one "
            "that is explicitly shared. Creating a document grants its creator full object-level rights."
        ),
        look_at=(
            "the GuardianViewSet and the Guardian*ViewPermissionRequired views, and "
            "DocumentCreateView.cv_form_valid, which assigns object permissions to the creator via "
            "cv_document.assign_perm."
        ),
        url_name="document-list",
        icon="fa-solid fa-user-lock",
    ),
    Feature(
        app="resources",
        title="Resources",
        description="A ViewSet over non-ORM data: a fake S3 bucket listing with delete and touch actions.",
        about=(
            "A ViewSet over data that isn't in the database at all. Here the 'records' are entries in a fake "
            "S3 bucket held in memory, exposed through crud_views' Resource abstraction — the same list, "
            "detail and action UI, with no model or queryset behind it. Useful for external APIs, config "
            "trees or object stores."
        ),
        look_at=(
            "the S3File(Resource) class and its cv_get_items() reading FAKE_BUCKET in views.py; "
            "ResourceViewMixin on the views; and the delete and touch actions."
        ),
        url_name="s3file-list",
        icon="fa-solid fa-cloud",
    ),
    Feature(
        app="showcase",
        title="Showcase",
        description="Presentation extras: card list, detail fieldsets, modal delete, custom actions.",
        about=(
            "Presentation building blocks gathered in one place. Recipes are shown as a grid of cards instead "
            "of a table, the detail page groups fields into labelled fieldsets, deletion happens in a modal, "
            "and a custom 'favorite' action toggles a flag straight from the list. Mix these into your own "
            "views as needed."
        ),
        look_at=(
            "RecipeCardListView (the card grid), the cv_property_display fieldset groups on RecipeDetailView, "
            "cv_modal on RecipeDeleteView, and the RecipeFavoriteView custom action in views.py."
        ),
        url_name="recipe-card",
        icon="fa-solid fa-wand-magic-sparkles",
    ),
]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd examples/bootstrap5 && uv run pytest project/tests.py::FeatureRegistryTest -v`
Expected: PASS.

- [ ] **Step 6: Run the full example suite to confirm nothing else broke**

Run: `cd examples/bootstrap5 && uv run pytest -q`
Expected: all PASS (the home page and every landing page still render — `description` is unchanged; the new fields are not yet rendered anywhere).

- [ ] **Step 7: Format and commit**

```bash
cd /home/alex/projects/alex/django-crud-views
uv run ruff format examples && uv run ruff check --fix examples
git add examples/bootstrap5/project/features.py examples/bootstrap5/project/tests.py
git status   # confirm cred.prompt.md is NOT staged
git commit -m "M3 examples: add about + look_at prose to the feature registry"
```

---

### Task 2: `example_about` tag + top callout on every example page

**Files:**
- Modify: `examples/bootstrap5/project/templatetags/example_tags.py`
- Create: `examples/bootstrap5/project/templates/project/example_about.html`
- Modify: `examples/bootstrap5/project/templates/project/crud_views.html`
- Test: `examples/bootstrap5/project/tests.py`

**Interfaces:**
- Consumes: `Feature.about` (Task 1).
- Produces: `_feature_for(view) -> Feature | None` and the `example_about` inclusion tag (context `{"feature": ...}`). The callout renders the marker `id="example-about"`.

- [ ] **Step 1: Write the failing tests** — append to `examples/bootstrap5/project/tests.py`:

```python
class ExampleAboutTest(TestCase):
    def setUp(self):
        admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        self.client.force_login(admin)

    def test_every_feature_page_shows_about(self):
        from django.utils.html import escape

        for feature in FEATURES:
            resp = self.client.get(reverse(feature.url_name))
            self.assertContains(resp, 'id="example-about"', msg_prefix=feature.app)
            # a distinctive slice of the prose actually reaches the page.
            # escape() because Django autoescapes the rendered {{ feature.about }}
            # (e.g. an apostrophe becomes &#x27;), so the raw substring would not match.
            self.assertContains(resp, escape(feature.about[:40]), msg_prefix=feature.app)

    def test_example_about_empty_for_non_feature_view(self):
        from project.templatetags.example_tags import example_about
        from project.views import HomeView

        result = example_about({"view": HomeView()})
        self.assertIsNone(result["feature"])
```

(`FEATURES`, `get_user_model`, `reverse` are already imported at the top of `project/tests.py`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/bootstrap5 && uv run pytest project/tests.py::ExampleAboutTest -v`
Expected: FAIL — `test_example_about_empty_for_non_feature_view` raises `ImportError` (no `example_about`); `test_every_feature_page_shows_about` fails the `id="example-about"` assertion (nothing renders it yet).

- [ ] **Step 3: Add `_feature_for` and the `example_about` tag** — in `examples/bootstrap5/project/templatetags/example_tags.py`, add the helper and tag (place `_feature_for` above `_feature_app_for`, and `example_about` below `get_features`):

```python
def _feature_for(view):
    """The Feature a view class belongs to, or None for non-feature views."""
    from project.features import FEATURES

    app = type(view).__module__.split(".")[0]
    return next((f for f in FEATURES if f.app == app), None)


@register.inclusion_tag("project/example_about.html", takes_context=True)
def example_about(context):
    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    return {"feature": feature}
```

- [ ] **Step 4: Create the callout template** — `examples/bootstrap5/project/templates/project/example_about.html`:

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

(When `feature` is `None`, Django resolves `feature.about` to an empty string, so the `{% if %}` renders nothing — the same graceful-empty behaviour as `snippet_panels`.)

- [ ] **Step 5: Render it at the top of every example page** — in `examples/bootstrap5/project/templates/project/crud_views.html`, add `{% example_about %}` as the first line inside `{% block content %}` (the `{% load example_tags %}` line is already present at the top of the file). The block start becomes:

```html
{% block content %}

    {% example_about %}

    <div class="card">
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd examples/bootstrap5 && uv run pytest project/tests.py::ExampleAboutTest -v`
Expected: PASS (both tests).

- [ ] **Step 7: Format and commit**

```bash
cd /home/alex/projects/alex/django-crud-views
uv run ruff format examples && uv run ruff check --fix examples
git add examples/bootstrap5/project/templatetags/example_tags.py \
        examples/bootstrap5/project/templates/project/example_about.html \
        examples/bootstrap5/project/templates/project/crud_views.html \
        examples/bootstrap5/project/tests.py
git status   # confirm cred.prompt.md is NOT staged
git commit -m "M3 examples: 'About this example' callout on every example page"
```

---

### Task 3: "Look at:" pointer next to "The code behind this page"

**Files:**
- Modify: `examples/bootstrap5/project/templatetags/example_tags.py`
- Modify: `examples/bootstrap5/project/templates/project/snippet_panels.html`
- Test: `examples/bootstrap5/project/tests.py`

**Interfaces:**
- Consumes: `Feature.look_at` (Task 1), `_feature_for` (Task 2).
- Produces: `snippet_panels` context now also includes `"look_at": str`; the panel renders the pointer under the heading when set.

- [ ] **Step 1: Write the failing test** — append to `examples/bootstrap5/project/tests.py`:

```python
class LookAtTest(TestCase):
    def test_look_at_appears_with_the_code_panel(self):
        from django.utils.html import escape

        admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        self.client.force_login(admin)
        feature = next(f for f in FEATURES if f.app == "polymorphic_demo")
        resp = self.client.get(reverse(feature.url_name))
        self.assertContains(resp, "Look at:")
        # escape() because {{ look_at }} is autoescaped in the rendered panel
        self.assertContains(resp, escape(feature.look_at[:40]))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd examples/bootstrap5 && uv run pytest project/tests.py::LookAtTest -v`
Expected: FAIL — the page has no "Look at:" text yet.

- [ ] **Step 3: Extend `snippet_panels` to pass `look_at`** — in `examples/bootstrap5/project/templatetags/example_tags.py`, replace the `snippet_panels` function (and remove the now-unused `_feature_app_for`) with:

```python
@register.inclusion_tag("project/snippet_panels.html", takes_context=True)
def snippet_panels(context):
    view = context.get("view")
    feature = _feature_for(view) if view is not None else None
    app = feature.app if feature else None
    panels = []
    if app:
        for name in SNIPPET_FILES:
            path = Path(settings.BASE_DIR) / app / name
            if path.exists():
                panels.append(
                    {
                        "id": f"snippet-{app}-{name.replace('.', '-')}",
                        "title": f"{app}/{name}",
                        "html": mark_safe(_highlight(path.read_text())),
                    }
                )
    return {"panels": panels, "look_at": feature.look_at if feature else ""}
```

Delete the `_feature_app_for` function (lines defining it) — `_feature_for` from Task 2 replaces it and it now has no callers.

- [ ] **Step 4: Render the pointer** — in `examples/bootstrap5/project/templates/project/snippet_panels.html`, add the "Look at:" line between the heading and the accordion:

```html
{% if panels %}
    <div class="mt-4" id="snippet-panels">
        <h5><i class="fa-solid fa-code"></i> The code behind this page</h5>
        {% if look_at %}
            <p class="text-body-secondary"><strong>Look at:</strong> {{ look_at }}</p>
        {% endif %}
        <div class="accordion" id="snippetAccordion">
            {% for panel in panels %}
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                                data-bs-target="#{{ panel.id }}" aria-controls="{{ panel.id }}">
                            {{ panel.title }}
                        </button>
                    </h2>
                    <div id="{{ panel.id }}" class="accordion-collapse collapse" data-bs-parent="#snippetAccordion">
                        <div class="accordion-body overflow-auto">{{ panel.html }}</div>
                    </div>
                </div>
            {% endfor %}
        </div>
    </div>
{% endif %}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd examples/bootstrap5 && uv run pytest project/tests.py::LookAtTest -v`
Expected: PASS.

- [ ] **Step 6: Run the full example suite**

Run: `cd examples/bootstrap5 && uv run pytest -q`
Expected: all PASS — including the pre-existing `SnippetPanelsTest::test_snippet_panels_empty_for_non_feature_view` (still returns `panels == []` for `HomeView`, now also `look_at == ""`) and `SystemChecksTest`.

- [ ] **Step 7: Format and commit**

```bash
cd /home/alex/projects/alex/django-crud-views
uv run ruff format examples && uv run ruff check --fix examples
git add examples/bootstrap5/project/templatetags/example_tags.py \
        examples/bootstrap5/project/templates/project/snippet_panels.html \
        examples/bootstrap5/project/tests.py
git status   # confirm cred.prompt.md is NOT staged
git commit -m "M3 examples: 'Look at:' code pointer next to the source panels"
```

---

## Manual verification (after Task 3)

Not a task, but recommended before considering the feature done: `cd examples/bootstrap5 && uv run manage.py runserver`, open a couple of example pages (e.g. `/polymorphic/`, `/guardian/`), and confirm the "About this example" callout shows at the top and the "Look at:" line shows above the code accordion. Tests cover the presence of the text; this confirms the visual placement.
