# Conditional Field-Groups & Conditional FormSets

A checkbox toggle can hide a group of fields (or an entire **first-level** formset). When off, the group or formset is hidden client-side and — authoritatively **server-side** — skips validation and clears its data. JavaScript is convenience only: `toggle.js` shows/hides the group and disables its inputs so they are not submitted, but the server enforces the exact same contract on every submit, including tampered or JS-off POSTs.

`toggle.js` ships automatically via the `cv_js` asset registry (`crud_views_settings.javascript()`); no template changes are needed. It also re-initializes inside Bootstrap modals (`cv_modal = True` views) via the `cv:modal:loaded` event.

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
| `ToggleGroup(toggle_field, *fields, css_class=None, legend=None)` | Crispy layout element that wraps the group's fields in a JS-toggled `<div>`, or a titled `<fieldset>` when `legend=` is given |

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

`ToggleGroup(toggle_field, *fields, css_class=None, legend=None)` is a Crispy layout element. By default it renders a `<div cv-data-toggle-group cv-data-toggle-field="…">` wrapper. Pass `legend="…"` to render a titled `<fieldset><legend>…</legend>…</fieldset>` instead; the toggle marker sits on the fieldset, so the whole group (legend included) hides when the toggle is off. The bundled `toggle.js` reads the toggle field's current value on page load and on change, and shows or hides the wrapper accordingly. No custom JavaScript is required.

---

## Kind 2 — Conditional formset

### Core class

| Attribute | Default | Meaning |
|---|---|---|
| `toggle` | — | `ToggleSource` that governs the formset |
| `on_off` | `"skip"` | `"skip"` — leave existing rows untouched when off; `"purge"` — delete them on save |

!!! warning "purge permanently deletes rows"

    With `on_off="purge"`, saving the form while the toggle is off **deletes every
    existing row the formset manages** — there is no undo. Prefer `skip` (the
    default) unless deletion is exactly what you want. `purge` overrides the
    formset's own deletion settings: it deletes rows even when the formset is
    configured with `can_delete=False` or `edit_only=True` (system check
    `crud_views.W321` warns about that combination). The only permission gate is
    the parent object's *change* permission — no per-row delete permission is
    checked, also under django-guardian. The save flow (main form, purge, sibling
    formsets) runs inside a single database transaction, so a failure elsewhere
    rolls the purge back.

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

The parent form must expose the toggle field. **`ConditionalFormSet` toggles are never auto-injected** — only `ConditionalGroup` toggles are (by `ConditionalGroupFormMixin`). So either use a real model/form field, declare the checkbox on the form yourself (`forms.BooleanField(required=False)`), or reuse a `UIFieldToggle` that a `ConditionalGroup` on the same form already injects. A toggle that is missing from the form is flagged by system check `crud_views.E311`; without it the formset would be permanently off — and with `on_off="purge"` that silently deletes rows on every save.

---

## System checks

| ID | Level | Meaning |
|---|---|---|
| `crud_views.E310` | Error | `conditional=` placed on a nested (non-first-level) formset |
| `crud_views.E311` | Error | Toggle field named in a `ConditionalGroup` or `ConditionalFormSet.toggle` is absent from the parent form (and not injected by a group on that form) |
| `crud_views.W320` | Warning | A field cleared by an off group is not `null=True, blank=True` — saves will likely fail |
| `crud_views.W321` | Warning | `on_off="purge"` combined with a formset that forbids row deletion (`can_delete=False` / `edit_only=True`) — the toggle bulk-deletes rows anyway |

---

## Examples

The `examples/bootstrap5/conditional/` app (`conditional/views.py`) shows both kinds side by side:

- `cv_registration` — two field-groups on one form: a `ModelFieldToggle` group (`with_company` → `company_name`, `vat_id`) rendered as a titled `<fieldset>` via `ToggleGroup(..., legend="Company details")`, and a transient `UIFieldToggle` group (`add_note` → `note`), including the pattern of deriving the transient toggle's `initial` from the instance in `__init__`
- `cv_event` — two conditional first-level formsets contrasting the `on_off` modes: `with_sessions` → the `sessions` formset with `"purge"` (rows deleted on save when off), and `with_speakers` → the `speakers` formset with `"skip"` (rows kept)
