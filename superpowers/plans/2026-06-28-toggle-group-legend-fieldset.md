# ToggleGroup legend/fieldset mode + registration form layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `ToggleGroup` an optional `legend` parameter that renders the conditional field-group as a titled `<fieldset>`, and update the bootstrap5 registration example to stack the checkbox on its own line and box the company group as a fieldset.

**Architecture:** `ToggleGroup` (a crispy `LayoutObject`) gains a `legend` kwarg. When set, its template renders a `<fieldset>` carrying the existing `cv-data-toggle-group` marker (so `toggle.js` hides the whole fieldset when off) plus a `<legend>`; when unset it renders today's `<div>` unchanged. No `toggle.js` change.

**Tech Stack:** Django, django-crispy-forms, pytest. Spec: `superpowers/specs/2026-06-28-toggle-group-legend-fieldset-design.md`.

## Global Constraints

- Line length: 120 chars; double quotes; ruff-format runs on commit (`ruff-format` pre-commit hook).
- Run tests from `tests/` directory: `cd tests && pytest`.
- Fully backward compatible: `legend` defaults to `None` and must reproduce the current `<div>` rendering exactly. No existing `ToggleGroup(...)` call site changes behavior.
- All `CrudView` attrs use `cv_` prefix (not relevant here, but the toggle marker attrs are `cv-data-toggle-group` / `cv-data-toggle-field`).

---

### Task 1: Add `legend` parameter to `ToggleGroup` and template

**Files:**
- Modify: `src/crud_views/lib/conditional/layout.py` (the `ToggleGroup` class)
- Modify: `src/crud_views/templates/crud_views/conditional/toggle_group.html`
- Test: `tests/test1/test_conditional_layout.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `ToggleGroup(toggle_field, *fields, css_class=None, legend=None)`. When `legend` is truthy the rendered HTML contains a `<fieldset class="cv-toggle-group …" cv-data-toggle-group cv-data-toggle-field="…">` with a `<legend>{legend}</legend>`; when `legend` is `None` it renders the current `<div class="cv-toggle-group …" cv-data-toggle-group …>`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_conditional_layout.py`:

```python
class _LegendLayoutForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "with_contact", "email", "phone"]

    @property
    def helper(self):
        h = FormHelper()
        h.layout = Layout(
            Row(Column6("name")),
            Row(Column6("with_contact")),
            ToggleGroup(
                "with_contact",
                Row(Column6("email"), Column6("phone")),
                legend="Contact details",
            ),
        )
        return h


def test_toggle_group_legend_renders_fieldset():
    form = _LegendLayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert "<fieldset" in html
    assert "<legend>Contact details</legend>" in html
    # marker lives on the fieldset so toggle.js hides the whole group
    assert 'cv-data-toggle-field="with_contact"' in html
    assert "cv-data-toggle-group" in html


def test_toggle_group_without_legend_stays_a_div():
    # backward compat: no legend => current <div> rendering, no fieldset
    form = _LayoutForm()
    html = render_crispy_form(form, helper=form.helper)
    assert "<fieldset" not in html
    assert "<legend" not in html
    assert "cv-data-toggle-group" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_conditional_layout.py -v`
Expected: `test_toggle_group_legend_renders_fieldset` FAILS — `ToggleGroup.__init__() got an unexpected keyword argument 'legend'`. (`test_toggle_group_without_legend_stays_a_div` already passes.)

- [ ] **Step 3: Add the `legend` parameter to `ToggleGroup`**

In `src/crud_views/lib/conditional/layout.py`, replace the `__init__` and `render` so they carry `legend`:

```python
    def __init__(self, toggle_field: str, *fields, css_class: str | None = None, legend: str | None = None):
        self.toggle_field = toggle_field
        self.css_class = css_class
        self.legend = legend
        self.inner = Layout(*fields)

    def render(self, form, context, **kwargs):
        inner_html = self.inner.render(form, context, **kwargs)
        context.update(
            {
                "cv_toggle_field": self.toggle_field,
                "cv_toggle_css": self.css_class or "",
                "cv_toggle_legend": self.legend or "",
                "cv_toggle_inner": inner_html,
            }
        )
        return render_to_string(self.template, context.flatten())
```

Also update the class docstring's first paragraph to mention the fieldset mode:

```python
    """Crispy layout wrapper for a conditional field-group.

    Renders the wrapped fields inside a marker element that ``toggle.js`` keys
    off. Pass ``legend=`` to render a titled ``<fieldset>`` instead of a bare
    ``<div>``; the marker sits on the fieldset so the whole group (legend
    included) hides when the toggle is off. Cosmetic only — validation/clearing
    is enforced server-side by ``ConditionalGroupFormMixin``.
    """
```

- [ ] **Step 4: Update the template to branch on legend**

Replace the body of `src/crud_views/templates/crud_views/conditional/toggle_group.html` with:

```django
{# src/crud_views/templates/crud_views/conditional/toggle_group.html #}
{% load static %}
{% if cv_toggle_legend %}
<fieldset class="cv-toggle-group {{ cv_toggle_css }}" cv-data-toggle-group cv-data-toggle-field="{{ cv_toggle_field }}">
    <legend>{{ cv_toggle_legend }}</legend>
    {{ cv_toggle_inner }}
</fieldset>
{% else %}
<div class="cv-toggle-group {{ cv_toggle_css }}" cv-data-toggle-group cv-data-toggle-field="{{ cv_toggle_field }}">
    {{ cv_toggle_inner }}
</div>
{% endif %}
<script src="{% static 'crud_views/js/toggle.js' %}"></script>
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_conditional_layout.py -v`
Expected: all four tests PASS (the two new ones plus the two existing marker/JS tests).

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/conditional/layout.py \
        src/crud_views/templates/crud_views/conditional/toggle_group.html \
        tests/test1/test_conditional_layout.py
git commit -m "feat(conditional): ToggleGroup legend renders group as a fieldset"
```

---

### Task 2: Update the bootstrap5 registration example layout

**Files:**
- Modify: `examples/bootstrap5/app/views/conditional.py` (`RegistrationForm.get_layout_fields`)

**Interfaces:**
- Consumes: `ToggleGroup(..., legend=...)` from Task 1. `_` is `gettext_lazy`, already imported at the top of the file as `from django.utils.translation import gettext, gettext_lazy as _`.
- Produces: nothing downstream.

- [ ] **Step 1: Edit the layout**

In `examples/bootstrap5/app/views/conditional.py`, replace `RegistrationForm.get_layout_fields` (currently lines ~48-52):

```python
    def get_layout_fields(self):
        return [
            Row(Column6("name")),
            Row(Column6("with_company")),
            ToggleGroup(
                "with_company",
                Row(Column6("company_name"), Column6("vat_id")),
                legend=_("Company details"),
            ),
        ]
```

- [ ] **Step 2: Verify the page renders the fieldset**

Run (the bootstrap5 example already has a superuser `admin`):

```bash
cd examples/bootstrap5 && python manage.py shell -c "
from django.test import Client
from django.contrib.auth import get_user_model
u=get_user_model().objects.filter(is_superuser=True).first()
c=Client(SERVER_NAME='localhost'); c.force_login(u)
html=c.get('/registration/create/').content.decode()
print('fieldset:', html.count('<fieldset'))
print('legend Company details:', 'Company details' in html)
print('with_company on own row:', html.count('cv-data-toggle-field=\"with_company\"'))
"
```

Expected: `fieldset: 1` (or more if nav uses fieldsets — at least 1 from the toggle group), `legend Company details: True`, marker present.

- [ ] **Step 3: Commit**

```bash
git add examples/bootstrap5/app/views/conditional.py
git commit -m "docs(examples): registration form stacks checkbox, boxes group in a fieldset"
```

---

### Task 3: Update documentation

**Files:**
- Modify: `docs/reference/conditional.md` (the `ToggleGroup` table row ~line 21 and the `### ToggleGroup layout` section ~line 68-70)
- Modify: `skills/django-crud-views/SKILL.md` (`get_layout_fields` example ~line 570-572)

**Interfaces:**
- Consumes: `ToggleGroup(..., legend=...)` from Task 1.
- Produces: nothing.

- [ ] **Step 1: Update the reference table row**

In `docs/reference/conditional.md`, replace the table row (line ~21):

```markdown
| `ToggleGroup(toggle_field, *fields, css_class=None, legend=None)` | Crispy layout element that wraps the group's fields in a JS-toggled `<div>`, or a titled `<fieldset>` when `legend=` is given |
```

- [ ] **Step 2: Update the `ToggleGroup layout` prose**

In `docs/reference/conditional.md`, replace the paragraph at line ~70:

```markdown
`ToggleGroup(toggle_field, *fields, css_class=None, legend=None)` is a Crispy layout element. By default it renders a `<div cv-data-toggle-group cv-data-toggle-field="…">` wrapper. Pass `legend="…"` to render a titled `<fieldset><legend>…</legend>…</fieldset>` instead; the toggle marker sits on the fieldset, so the whole group (legend included) hides when the toggle is off. The bundled `toggle.js` reads the toggle field's current value on page load and on change, and shows or hides the wrapper accordingly. No custom JavaScript is required.
```

- [ ] **Step 3: Update the SKILL.md example**

In `skills/django-crud-views/SKILL.md`, replace the `get_layout_fields` body (lines ~570-572):

```python
    def get_layout_fields(self):
        return [Row(Column6("name")),
                Row(Column6("with_company")),
                ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id")),
                            legend="Company details")]  # legend=… renders the group as a titled <fieldset>
```

- [ ] **Step 4: Commit**

```bash
git add docs/reference/conditional.md skills/django-crud-views/SKILL.md
git commit -m "docs(conditional): document ToggleGroup legend/fieldset parameter"
```

---

### Task 4: Full regression check

**Files:** none (verification only).

- [ ] **Step 1: Run the conditional test suite**

Run: `cd tests && pytest test1/test_conditional_layout.py test1/test_conditional_exports.py -v`
Expected: all PASS.

- [ ] **Step 2: Run the full test suite**

Run: `cd tests && pytest -q`
Expected: all PASS (no regressions). If any failure references `toggle_group` rendering or `cv-data-toggle`, revisit Task 1.

---

## Self-Review

- **Spec coverage:** Goal 1 (reusable fieldset mode) → Task 1. Goal 2 (registration layout) → Task 2. Spec "Testing" section → Task 1 Steps 1/5 + Task 4. Spec "Documentation" section → Task 3. Backward-compat requirement → Task 1 `test_toggle_group_without_legend_stays_a_div`.
- **Placeholders:** none — every code/edit step shows full content.
- **Type consistency:** `legend` kwarg name, `cv_toggle_legend` context key, and `cv-data-toggle-group` / `cv-data-toggle-field` markers are used identically across layout.py, the template, and tests.
