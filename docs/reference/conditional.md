# Conditional Field-Groups & Conditional FormSets

A checkbox toggle can hide a group of fields (or an entire **first-level** formset). When off, the group or formset is hidden client-side and — authoritatively **server-side** — skips validation and clears its data. JavaScript is cosmetic only; the server enforces the contract on every submit, including tampered or JS-off POSTs.

Import everything from `crud_views.lib.conditional`.

---

## Kind 1 — Conditional field-group in a form

### Core classes

| Class / Type | Role |
|---|---|
| `ToggleSource` | Base class for toggle descriptors |
| `ModelFieldToggle(name)` | Toggle backed by a real model/form field |
| `UIFieldToggle(name)` | Toggle backed by a transient checkbox injected by the mixin |
| `ConditionalGroup(toggle, fields, required, empty_values)` | Declares one toggled group of fields |
| `ConditionalGroupFormMixin` | Server-side authority mixin (mix in before the form base) |
| `ConditionalGroupModelForm` | `CrispyModelForm` with `ConditionalGroupFormMixin` pre-applied |
| `ToggleGroup(toggle_field, *fields)` | Crispy layout element that wraps the group's fields in a JS-toggled `<div>` |

### Contract

- **Off** ⇒ group fields are cleared to their empty value on every save. Fields must be `null=True, blank=True` in the model (or provide explicit `empty_values=` in `ConditionalGroup`). Validation is skipped entirely for the group.
- **On** ⇒ the `required` subset is enforced (defaults to all `fields` if `required` is not passed).

The mixin disarms Django's field-level `required` check for group fields so the conditional required rule in `clean()` is the sole arbiter.

### Usage

```python
from crispy_forms.layout import Row
from crud_views.lib.conditional import (
    ConditionalGroupModelForm, ConditionalGroup, ToggleGroup, ModelFieldToggle,
)
from crud_views.lib.crispy import Column6

class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),   # checkbox field already on the model
            fields=["company_name", "vat_id"],
            required=["company_name"],                  # only company_name is required when on
        ),
    ]

    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column6("with_company")),
            ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id"))),
        ]
```

Use `UIFieldToggle` when the checkbox is a transient UI control that is not stored in the database. The mixin auto-injects the field; no manual `BooleanField` declaration is needed:

```python
ConditionalGroup(
    toggle=UIFieldToggle("show_extras"),
    fields=["extra_note", "extra_ref"],
)
```

### `ToggleGroup` layout

`ToggleGroup(toggle_field, *fields, css_class=None)` is a Crispy layout element. It renders a `<div cv-data-toggle-group cv-data-toggle-field="…">` wrapper. The bundled `toggle.js` reads the toggle field's current value on page load and on change, and shows or hides the wrapper accordingly. No custom JavaScript is required.

---

## Kind 2 — Conditional formset

### Core class

| Attribute | Default | Meaning |
|---|---|---|
| `toggle` | — | `ToggleSource` that governs the formset |
| `on_off` | `"skip"` | `"skip"` — leave existing rows untouched when off; `"purge"` — delete them on save |

### Scope constraint

Only **first-level** formsets may be conditional. Attaching `ConditionalFormSet` to a nested formset (one with a `parent` key) raises system-check error `crud_views.E310`.

### Usage

```python
from crud_views.lib.conditional import ConditionalFormSet, ModelFieldToggle
from crud_views.lib.formsets import FormSet, FormSets, FormSetMixin

cv_formsets = FormSets(formsets={
    "sessions": FormSet(
        title="Sessions",
        klass=SessionFormSet,
        fields=["title"],
        pk_field="id",
        conditional=ConditionalFormSet(
            toggle=ModelFieldToggle("with_sessions"),
            on_off="skip",   # default; use "purge" to delete rows on save
        ),
    ),
})
```

The parent form must expose the toggle field (either a real model field or a `UIFieldToggle`-injected field via `ConditionalGroupFormMixin`).

---

## System checks

| ID | Level | Meaning |
|---|---|---|
| `crud_views.E310` | Error | `conditional=` placed on a nested (non-first-level) formset |
| `crud_views.E311` | Error | Toggle field named in `ConditionalFormSet.toggle` is absent from the parent form |
| `crud_views.W320` | Warning | A field cleared by an off group is not `null=True, blank=True` — saves will likely fail |

---

## Examples

Runnable bootstrap5 examples with both kinds are provided in the test project:

- `cv_registration` — field-group with `ModelFieldToggle` (`with_company` → `company_name`, `vat_id`)
- `cv_event` — conditional first-level formset (`with_sessions` → sessions formset, `on_off="purge"`)
