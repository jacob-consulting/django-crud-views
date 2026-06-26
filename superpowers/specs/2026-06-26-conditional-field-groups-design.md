# Conditional field-groups & conditional formsets — design

Date: 2026-06-26
Status: Approved (ready for implementation plan)

## Problem

A create/update form has a **group of fields** (not all of them) whose relevance
is governed by a checkbox toggle:

- When the toggle is **on**, the group is shown and editable; its fields may be
  **required**.
- When the toggle is **off**, the group is hidden and must **not** cause
  validation to fail — even though some of its fields are declared required.

Doing this only in JavaScript is insufficient: a form submitted with the toggle
off must validate and save correctly regardless of client-side behavior
(disabled JS, tampered DOM, direct POST). **The server is the sole authority;
JS is purely cosmetic.**

## Requirements (decided during brainstorming)

1. **Toggle source is pluggable**: the toggle is either a persisted model
   `BooleanField`, or a transient UI-only checkbox not stored on the model.
2. **Off ⇒ logically absent**: when off, skip validation on the group *and*
   clear the dependent fields on save (write nulls/blanks).
3. **Scope**: the main form plus **first-level** formset rows. Nested formsets
   (e.g. tags → annotations under Choices) are explicitly out of scope.
4. **Batteries-included client**: the package ships the show/hide JS and a
   crispy layout helper — but it is cosmetic only and never the authority.
5. **Server-side enforcement is mandatory**, independent of JS.

## Two distinct constructs

The example app (`examples/bootstrap5`) makes the distinction concrete:
`Question` is the parent form and **"Choices"** is a *first-level formset*
(`ChoiceFormSet`, an inline of `QuestionChoice` on `Question`). Two different
things may be made conditional:

### Kind 1 — a field-group *inside a single form* (`ConditionalGroup`)

A group of fields within one form. Because `clean()` runs per form instance,
the **same** mechanism works in three places identically:

- the parent form (e.g. a `has_details` toggle hiding some `Question` fields),
- **each first-level formset row** (e.g. a per-row `has_help` toggle that
  hides/optional-izes `help_text` for that row only).

### Kind 2 — toggling an *entire first-level formset* (`ConditionalFormSet`)

A checkbox on the **parent** form (e.g. `with_choices`) that governs whether the
whole Choices formset is shown and validated. The authority is **not** any single
form's `clean()` — it is the formset validity gate (`FormSets.all_valid()` /
the parent-presence machinery from #55/#69).

Both constructs reuse the same `ToggleSource` abstraction and the same
"off ⇒ skip-validation + clear" contract.

## Shared abstraction — `ToggleSource`

Resolves on/off from submitted data, never from JS. One method:
`is_on(form) -> bool`.

- `ModelFieldToggle("with_choices")` — toggle is a real `BooleanField` already
  on the form/model; read from `cleaned_data`.
- `UIFieldToggle("has_details")` — the mixin injects a non-model
  `forms.BooleanField(required=False)` into the form; read from `cleaned_data`,
  never saved. On **update**, its initial checked-state is derived: any dependent
  field populated (Kind 1) / any child rows exist (Kind 2) ⇒ on.

## Kind 1 — server-side authority

Form mixin owning the contract; nothing depends on JS:

```python
class ConditionalGroupFormMixin:
    cv_conditional_groups: list[ConditionalGroup] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disarm Django's premature field-level required-check; we own it in clean()
        for group in self.cv_conditional_groups:
            for name in group.fields:
                self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        for group in self.cv_conditional_groups:
            if group.is_on(self):                       # toggle ON
                for name in group.required_fields:
                    if cleaned.get(name) in self.empty_values:
                        self.add_error(name, self.fields[name].error_messages["required"])
            else:                                        # toggle OFF ⇒ logically absent
                for name in group.fields:
                    cleaned[name] = group.empty_value_for(name)
        return cleaned
```

Rationale:

- Fields are set `required=False` in `__init__` so Django's field-level cleaning
  never raises a spurious "required" error for an off group. Required is
  re-imposed **only when the toggle is on**, inside `clean()`. This is the
  standard Django idiom for conditionally-required fields and avoids fighting
  the framework.
- When off, dependent fields are overwritten with their empty value in
  `cleaned_data`, so `form.save()` writes nulls/blanks — the "clear on off"
  behavior.

Server-authority outcomes (independent of JS):

- Off + smuggled values in POST ⇒ values **cleared**.
- On + required field missing ⇒ submission **rejected**.

## Kind 2 — server-side authority

Declared on the `FormSet` entry, referencing a parent-form toggle:

```python
choices=FormSet(
    title=_("Choices"), klass=ChoiceFormSet, fields=["choice", "help_text"], pk_field="id",
    conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_choices"),
                                   on_off="skip"),   # or "purge"
    children=...,
)
```

Enforcement lives in `FormSets.all_valid()`: if the toggle is off, the Choices
formset is excluded from the gate (no parent-required errors, no per-row
required errors).

**Off-behavior is configurable per formset** (default non-destructive):

- `on_off="skip"` (default): existing child rows are left untouched in the DB;
  toggling back on shows them again.
- `on_off="purge"`: on save, all existing child rows are deleted (cascade to
  nested tags/annotations via the child FK `on_delete`).

## Public API surface

Kind 1:

```python
class QuestionForm(ConditionalGroupModelForm):   # = ConditionalGroupFormMixin + CrispyModelForm
    cv_conditional_groups = [
        ConditionalGroup(toggle=UIFieldToggle("has_details"),
                         fields=["detail_a", "detail_b"], required=["detail_a"]),
    ]
    def get_layout_fields(self):
        return [Row(Column4("question")),
                ToggleGroup("has_details", Row(Column6("detail_a"), Column6("detail_b"))),
                Formsets()]
```

Kind 2: the `ConditionalFormSet(...)` entry on a `FormSet`, shown above.

## Client JS (cosmetic only)

One `toggle.js` (jQuery, same `cv-data-*` convention, row-scoped like
`formset.js`):

- `ToggleGroup` renders
  `<div cv-data-toggle-group cv-data-toggle-field="has_details">`; JS binds the
  matching checkbox → show/hide + `disabled` on the group inputs.
- Kind 2 targets the existing
  `cv-formset-content[cv-data-formset-prefix=...]` block.
- Scoped to the checkbox's nearest form/row so per-row toggles don't cross-talk.
- **If JS never runs, the server still produces correct data**: disabled inputs
  simply aren't submitted, and `clean()` / the gate handle on/off identically.

## Guardrails — Django system checks

Reusing `checks.py`:

- **Warn** if a `ConditionalGroup` clears a model field that is not `null=True` /
  `blank=True` (clear-on-off would fail at DB write).
- **Error** if a declared toggle name resolves to neither an existing form field
  nor an injectable UI field.
- **Note/validate** cascade behavior for `ConditionalFormSet(on_off="purge")`.

## Testing (TDD, server-authority focused)

- `clean()` with toggle **on**: missing required ⇒ error.
- `clean()` with toggle **off**: submitted values ⇒ cleared.
- **Tampering POST** (proves JS-independence): off + smuggled values ⇒ cleared;
  on + missing required ⇒ rejected.
- Formset gate: `skip` leaves rows untouched; `purge` deletes them.
- Update-flow initial-state derivation for `UIFieldToggle` (Kind 1 and Kind 2).
- Per-row toggles in a first-level formset don't cross-talk.
- Nested formsets explicitly unaffected (out of scope).

## Examples (bootstrap5 example app)

The feature ships with two worked, runnable examples in
`examples/bootstrap5`, isolated in a dedicated `conditional` module so the
existing Question/Choices example stays as the plain-formset reference. Both
are wired into `app/urls.py` and backed by a new migration.

### Kind 1 example — conditional field-group in a single form

Model `Registration`:

- `name = CharField`
- `with_company = BooleanField(default=False)` — the toggle (persisted ⇒
  `ModelFieldToggle("with_company")`)
- `company_name = CharField(blank=True, null=True)` — in the group, **required
  when on**
- `vat_id = CharField(blank=True, null=True)` — in the group, **optional even
  when on** (demonstrates per-field `required=[...]` granularity)

The `RegistrationForm` uses `ConditionalGroupModelForm` with one
`ConditionalGroup(toggle=ModelFieldToggle("with_company"),
fields=["company_name", "vat_id"], required=["company_name"])` and a
`ToggleGroup("with_company", …)` in its layout. Registered as `cv_registration`.

### Kind 2 example — conditional first-level formset (the `with_choices` case)

Parent `Event` with a `with_sessions = BooleanField(default=False)` toggle, and
child `Session` (`FK(Event)`, `title`). The `sessions` first-level formset
declares
`conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"),
on_off="skip")` (default non-destructive; a comment shows how to switch to
`"purge"`). Registered as `cv_event`. This mirrors the structure of the
existing Choices formset and directly demonstrates a `with_<child>` parent
toggle governing a whole first-level formset.

## Documentation & skill

The feature is documented in three places, all kept consistent:

- **User docs (mkdocs)**: a new `docs/reference/conditional.md` reference page,
  added to `mkdocs.yml` nav, covering both constructs, `ToggleSource`, the
  off ⇒ skip-validation + clear contract, `on_off="skip"|"purge"`, the
  first-level-only scope, the system-check ids, and links to the two example
  ViewSets.
- **Bundled skill** (`skills/django-crud-views/`): a new
  "Conditional Field-Groups & Conditional FormSets" section in `SKILL.md`
  (placed next to the Formsets section) with the minimal usage pattern for
  both kinds and the "server-side is authoritative" caveat; a matching
  `## Conditional Field-Groups` section in `references/api-reference.md`; and
  new entries in that file's Import Paths Cheatsheet
  (`crud_views.lib.conditional`).
- **CHANGELOG.md**: an `Added` entry.

## Out of scope

- Conditional groups/formsets inside **nested** (2nd-level and deeper) formsets.
- Cross-field conditions beyond a single boolean toggle (e.g. "show when
  status == X"). The `ToggleSource` abstraction leaves room to add these later.
```
