# ToggleGroup legend/fieldset mode + registration form layout

**Date:** 2026-06-28
**Status:** Approved (design)

## Problem

The conditional field-group component `ToggleGroup` renders its wrapped fields
inside a bare `<div class="cv-toggle-group">`. There is no built-in way to give
a conditional group a visible title, and forms that want a titled, boxed group
must hand-roll one. The bootstrap5 registration example also crowds the `name`
field and the `with_company` toggle onto a single row.

## Goals

1. Let any conditional group optionally render as a titled HTML `<fieldset>` with
   a `<legend>`, reusably, via the existing `ToggleGroup` component.
2. Update the registration form example so the `with_company` checkbox sits on
   its own line and the conditional company-details group renders as a fieldset.

## Non-goals

- No change to `toggle.js` behavior or to the server-side validation/clearing in
  `ConditionalGroupFormMixin`.
- No new component; the fieldset is an opt-in mode of the existing `ToggleGroup`.

## Design

### 1. `ToggleGroup` component (`src/crud_views/lib/conditional/layout.py`)

Add an optional `legend` parameter:

```python
def __init__(self, toggle_field, *fields, css_class=None, legend=None):
    self.toggle_field = toggle_field
    self.css_class = css_class
    self.legend = legend
    self.inner = Layout(*fields)
```

`render()` passes `cv_toggle_legend` into the template context alongside the
existing `cv_toggle_field`, `cv_toggle_css`, `cv_toggle_inner`.

- `legend=None` (default): renders exactly as today — a
  `<div class="cv-toggle-group" cv-data-toggle-group cv-data-toggle-field="…">`.
  **Backward compatible**: every existing `ToggleGroup(...)` call is unchanged.
- `legend="…"`: renders a `<fieldset>` carrying the same classes and toggle
  marker attributes, with a `<legend>` containing the legend text.

The `cv-data-toggle-group` marker sits on the `<fieldset>` element itself, so when
the toggle is off the whole fieldset (legend included) hides.

### 2. Template (`src/crud_views/templates/crud_views/conditional/toggle_group.html`)

Single `{% if cv_toggle_legend %}` branch selecting `<fieldset>`+`<legend>` vs the
current `<div>`. Both branches keep identical `class`, `cv-data-toggle-group`, and
`cv-data-toggle-field` attributes and the existing `toggle.js` `<script>` include.
Legend text is auto-escaped and may be a translated (gettext) string.

`toggle.js` requires no changes: `wireGroups` selects `[cv-data-toggle-group]` by
attribute (tag-agnostic) and `apply()` disables inner `input/select/textarea` —
both work identically on a `<fieldset>`.

### 3. Registration form example (`examples/bootstrap5/app/views/conditional.py`)

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

`name` and `with_company` each get their own row (`Column6`, half-width, retained
for a visually narrow form); the conditional group renders as a titled fieldset.

## Testing

- Rendering test: `ToggleGroup(..., legend="X")` output contains a `<fieldset>`,
  a `<legend>X</legend>`, and the `cv-data-toggle-group` / `cv-data-toggle-field`
  markers.
- Backward-compat guard: `ToggleGroup(...)` with no `legend` still renders a
  `<div>` (no `<fieldset>`/`<legend>`), preserving current behavior.

## Documentation

- Update the conditional field-groups docs page to document the `legend`
  parameter and the fieldset rendering.
- Update the django-crud-views `SKILL.md` `ToggleGroup` reference to mention
  `legend=`.

## Backward compatibility

Fully backward compatible. `legend` defaults to `None`, which reproduces the
existing `<div>` rendering byte-for-byte. No migration or call-site changes
required outside the example.
