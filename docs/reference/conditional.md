# Conditional Field-Groups & Conditional FormSets

A checkbox toggle can hide a group of fields or an entire **first-level** formset. A native single-choice dropdown
or radio set can also activate [choice-driven groups](#choice-driven-groups). An off field-group clears
editable fields using the [clearing matrix](#clearing-matrix); an off formset skips its rows by default, or
purges its managed queryset when explicitly configured. JavaScript provides immediate native visibility and
disabled controls; server validation and persistence remain authoritative, including for tampered or JS-off POSTs.

!!! example "Try it live"
    The [Conditional example](https://django-crud-views-demo.onrender.com/conditional/registration/) and the
    [Formsets + Conditional example](https://django-crud-views-demo.onrender.com/formsets-conditional/conference/)
    in the live demo show this in action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md)
    for data resets and wake-up time.

    For three choices and four groups, open [Customers](https://django-crud-views-demo.onrender.com/conditional/customer/)
    or [Create Radio](https://django-crud-views-demo.onrender.com/conditional/customer/create-radio/).
    Both editors save the same model; its detail page distinguishes `None`, blank text and `unset`.
    These are the deployment destinations; availability follows deployment of this release.

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
| `ValueToggle(name, values=[...])` | Match explicit values of an existing native single-choice field; no injected field |
| `ConditionalGroup(toggle, fields, required, empty_values)` | Declares one toggled group of fields |
| `ConditionalGroupFormMixin` | Server-side authority mixin (mix in before the form base) |
| `ConditionalGroupModelForm` | `CrispyModelForm` with `ConditionalGroupFormMixin` pre-applied |
| `ToggleGroup(toggle_field, *fields, css_class=None, legend=None)` | Crispy layout element that wraps the group's fields in a JS-toggled `<div>`, or a titled `<fieldset>` when `legend=` is given |

### Contract

- **Off** ⇒ editable group fields receive their field-aware empty value on save. Ordinary errors on those fields
  are suppressed and submitted values discarded. Inherited `clean()` nonfield errors, model validation,
  uniqueness and database invariants remain authoritative; an off group is not a validation bypass.
- **On** ⇒ the `required` subset is enforced (defaults to all `fields` if `required` is not passed).

The mixin disarms Django's field-level `required` check for group fields so the conditional required rule in `clean()` is the sole arbiter.

Server-side `Field.disabled=True` takes precedence over clearing, including explicit `empty_values`: Django uses
the trusted initial value and retains its validation errors. A browser `disabled` attribute alone is not this policy.

### Clearing matrix

Automatic values support the following standard Django form/model pairs. Custom subclasses or overridden persistence
hooks require explicit `empty_values`; this is a bounded contract, not arbitrary custom-field/backend compatibility.
The resulting model state must satisfy your application's constraints.

| Editable field pair | Automatic off value | Persistence |
|---|---|---|
| Native text form fields with nullable Char/Text/Email/URL/Slug model fields | `None` | SQL NULL, including omitted fields with model defaults |
| Native text fields with nonnullable, `blank=True` text models | `""` | Empty text, including defaulted fields |
| Nonnullable BooleanField | `False` | False |
| Nullable BooleanField with NullBooleanField | `None` | SQL NULL |
| Nullable integer/float/decimal/date/time/datetime/duration/UUID model fields with matching native form fields | `None` | SQL NULL |
| Nullable ForeignKey with ModelChoiceField | `None` | Clears the relation |
| FileField with FileField | `False` | Clears the stored reference; leaves stored bytes intact |
| ImageField with ImageField | `False` | Clears the stored reference; same reference-only evidence boundary below |
| ManyToManyField with ModelMultipleChoiceField | `[]` | Clears relations via native `save_m2m()` |
| Plain-form native text / MultipleChoice / Boolean / NullBoolean fields | field's `empty_value` / `[]` / `False` / `None` | Cleaned data; the application owns subsequent persistence |

Explicit dictionary membership wins, including falsy values: `False`, `""`, `None` and `[]` are never replaced by
a fallback. For file/image fields, `False` and `""` clear the reference; explicit `None` means native **no change**.
Clearing does not call storage deletion or implement file cleanup. A changed conditional state is persisted even
for an existing inline row whose ordinary `has_changed()` is false; blank extra rows are not created for clearing.
With `commit=False`, save the instance and call `save_m2m()` as for an ordinary ModelForm.

ImageField is supported for this reference-clearing contract. Its False/None, disabled and unchanged-inline evidence
uses existing stored references and no uploaded image bytes: it is **reference-only**, not an image-byte decoding
or image-upload-validation guarantee. The disabled-image fixture uses native `initial=None`/no-change to retain the
stored reference without decoding it. Actual upload-discard evidence uses multipart FileField data, separately from
images. Django ImageField upload decoding retains its existing Pillow prerequisite in consuming applications;
this phase adds no dependency and does not exercise image-byte decoding.

Unsupported automatic shapes (for example a nonnullable numeric field or custom field subclass) fail static
`crud_views.E312` checks where inspectable. Request-added fields are checked during `clean()` and raise a descriptive
`ImproperlyConfigured` naming the group and field, even on an active submission. Supply an explicit native-compatible
`empty_values` value and verify its model constraints. E312 replaces the former W320 warning; it is not a user error.

### Explicit file reference recipe

For an application model with a BooleanField `active` and an editable FileField `attachment` (or ImageField `image`),
this factory declares explicit native values. Import your model and call
`reference_form(Document, field_name="attachment", empty_value=False)` to clear, or use `empty_value=None` to retain
its reference. For `field_name="image"`, this example concerns existing references only, without uploaded bytes.

```python
from django import forms
from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupFormMixin, ModelFieldToggle


def reference_form(model_class, *, field_name="attachment", empty_value=False):
    class ReferenceForm(ConditionalGroupFormMixin, forms.ModelForm):
        cv_conditional_groups = [
            ConditionalGroup(ModelFieldToggle("active"), [field_name], empty_values={field_name: empty_value})
        ]

        class Meta:
            model = model_class
            fields = ["active", field_name]

    return ReferenceForm
```

### Usage

```python
from crispy_forms.layout import Row
from crud_views.lib.conditional import (
    ConditionalGroupModelForm,
    ConditionalGroup,
    ToggleGroup,
    ModelFieldToggle,
)
from crud_views.lib.crispy import Column6


class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),  # checkbox field already on the model
            fields=["company_name", "vat_id"],
            required=["company_name"],  # only company_name is required when on
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

The stock legend uses the independent `conditional:legend` [class-table key](buttons.md#the-class-table),
which defaults to `""`. See the [theme and project examples](buttons.md#legend-classes).

### Copied conditional wrapper

In `crud_views/conditional/toggle_group.html`, `cv_toggle_field` is the **exact bound HTML controller name**,
already computed with `form.add_prefix(...)`. For a form prefix `editor-0`, toggle `active` means `editor-0-active`.
Render it directly with ordinary escaping; do not prepend another prefix or use suffix matching. This complete
minimal override retains the optional legend and generated inner content:

```django
{% if cv_toggle_legend %}
<fieldset cv-data-toggle-group cv-data-toggle-field="{{ cv_toggle_field }}"{% if cv_toggle_values %} cv-data-toggle-values="{{ cv_toggle_values }}"{% endif %} class="{{ cv_toggle_css }}">
    <legend>{{ cv_toggle_legend }}</legend>
    {{ cv_toggle_inner }}
</fieldset>
{% else %}
<div cv-data-toggle-group cv-data-toggle-field="{{ cv_toggle_field }}"{% if cv_toggle_values %} cv-data-toggle-values="{{ cv_toggle_values }}"{% endif %} class="{{ cv_toggle_css }}">
    {{ cv_toggle_inner }}
</div>
{% endif %}
```

To adopt the class hook in a copied wrapper, load the existing tag library with `{% load crud_views %}`
and add `class="{% cv_button_class 'conditional' 'legend' %}"` to its legend. The minimal recipe above
keeps ordinary legend text escaping; copied wrappers opt in to the hook themselves.

`cv_toggle_values` is serialized JSON for a ValueToggle, otherwise `None`. Render with ordinary attribute escaping
in **both** wrapper branches: never add `safe`, interpolate executable code or serialize it again. Omitting this
attribute keeps the existing checkbox contract. Radio peers share the same exact bound name and owning form.

Conditional formset wrappers likewise render their `x_formset.cv_toggle_field` directly; it is the parent form's
bound toggle name. Checkbox lookup uses exact `name` equality and actual owning-form identity, including native
`form=` ownership. Repeated names in separate forms are independent. Multiple matching checkboxes in one form log
`console.warn("crud_views: ambiguous conditional toggle", name)`. On first initialization an unresolved group
(missing or ambiguous checkbox) leaves its own presentation unmanaged. A previously bound group that becomes
unresolved retains its **last owned on/off state**, without learning a new disabled baseline from its temporary state.
That own state still composes with all bound ancestors and independent disabled reasons: an off ancestor continues
to hide/disable descendants even when their own binding is unresolved. Other groups remain independent.
Both missing and ambiguous bindings are retryable: restore exactly one checkbox and call `cv.initConditional(root)`
again to apply its current checked state, without duplicate handlers or baseline loss.
See [root initialization](javascript.md#conditional-and-formset-initialization).

### Visibility, disabled ownership, focus and reset

Visibility changes immediately, without animation or Bootstrap. Controls retain unsaved values across off/on.
An editable control is enabled only when its independent disabled baseline and **all** bound ancestor groups allow it.
External `disabled` changes, including setting it true while it is already temporarily disabled, update that baseline.
Native input/select/textarea/button controls participate. Hidden `TOTAL_FORMS`, `INITIAL_FORMS`, `MIN_NUM_FORMS` and
`MAX_NUM_FORMS` management inputs remain enabled by the conditional layer so invalid re-renders retain row counts;
an independently disabled management input stays disabled.

When hiding strands focus inside a group, focus returns to a usable governing checkbox, then a usable ancestor toggle,
then the owning form. Focus already outside the hidden content is left alone. This composes with the modal's existing
focus restoration and completed `onHidden` contract.

A noncancelled native reset resynchronizes after the browser restores defaults. Cancellation, including by later
reset listeners, preserves presentation. Only that form is synchronized; dynamic rows and management counts remain.
This does not define a new final reset policy for dynamically added formset rows (A8 remains deferred).

---

## Choice-driven groups

Use one `ValueToggle` descriptor in both `ConditionalGroup(toggle=...)` and `ToggleGroup(...)` so browser and
server share the condition. Several groups can follow the same controller, and several can be active together.
Each group's controlled fields must be disjoint. No group may control its own or another group's controller.
These checks apply to declarations involving value groups; existing checkbox-only configurations retain their behavior.

The runnable Customer example uses this matrix:

| Group | Consumer | Wholesale | Distributor |
|---|---|---|---|
| Consumer preferences: `consumer_note` | Active | Inactive | Inactive |
| Business details: `company`, `price_tier`, `payment_terms` | Inactive | Active | Active |
| Wholesale terms: `wholesale_terms` | Inactive | Active | Inactive |
| Distribution details: `distribution_region` | Inactive | Inactive | Active |

For the `Customer` model in `examples/bootstrap5/conditional/models.py`, both presentations share these rules:

```python
from django import forms
from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupModelForm, ToggleGroup, ValueToggle

consumer = ValueToggle("kind", values=["consumer"])
business = ValueToggle("kind", values=["wholesale", "distributor"])
wholesale = ValueToggle("kind", values=["wholesale"])
distributor = ValueToggle("kind", values=["distributor"])


class CustomerForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(consumer, ["consumer_note"], required=[]),
        ConditionalGroup(
            business,
            ["company", "price_tier", "payment_terms"],
            required=["company", "price_tier"],
            empty_values={"payment_terms": "unset"},
        ),
        ConditionalGroup(wholesale, ["wholesale_terms"]),
        ConditionalGroup(distributor, ["distribution_region"]),
    ]

    class Meta:
        model = Customer
        fields = [
            "name",
            "kind",
            "consumer_note",
            "company",
            "price_tier",
            "payment_terms",
            "wholesale_terms",
            "distribution_region",
        ]

    def get_layout_fields(self):
        return [
            "name",
            "kind",
            ToggleGroup(consumer, "consumer_note", legend="Consumer preferences"),
            ToggleGroup(business, "company", "price_tier", "payment_terms", legend="Business details"),
            ToggleGroup(wholesale, "wholesale_terms", legend="Wholesale terms"),
            ToggleGroup(distributor, "distribution_region", legend="Distribution details"),
        ]


class CustomerRadioForm(CustomerForm):
    class Meta(CustomerForm.Meta):
        widgets = {"kind": forms.RadioSelect}
```

`required=None` (or omitted) requires all controlled fields while active. An explicit subset requires only those
fields and must belong to the group. `required=[]` makes them optional while active; it does **not** retain them
while inactive. Native validation still rejects invalid active choices.

Switching away and back **before submitting** retains unsaved entries. Wholesale → Distributor leaves Business
details active, retaining company/price/payment data; saving clears wholesale-only terms. Switching to Consumer
and saving clears both business and distributor data, while the outside `name` stays intact. Reopen the saved
detail or either editor to inspect this: `price_tier` is `None`, despite its model default `"A"`, and
`payment_terms` is the explicit `"unset"` sentinel (no business terms). After save/reopen there is no history from
which to restore cleared values.

### Matching and supported controllers

Controllers are exact stock `forms.ChoiceField` or `forms.TypedChoiceField` instances with exact native
`forms.Select` (single select) or `forms.RadioSelect` widgets. Use static choices, including ordinary optgroups.
Match values are a nonempty collection of nonempty strings or integers, including zero. Tokens match exactly:
integer `0` and HTML `"0"` agree; whitespace/case are not normalized. Duplicate normalized tokens are rejected,
and every configured match must belong to the declared nonempty choices. Booleans and `None` are not match values.

Typed controllers support `str`, `int`, or native text/integer model-field conversion only. Every nonempty choice
must round-trip to the same HTML token: e.g. integer coercion of `"01"` to `1` is refused. Standard text models are
Char/Text/Email/URL/Slug; standard integer models include Integer/Small/Big and their Positive variants. An empty
sentinel must not collide with a declared choice. Native empty choice placeholders (`""`/`None`) are admitted but
inactive and excluded from integer coercion checks; explicitly configured **empty match values** are rejected.

Callable choices, custom subclasses/widgets, arbitrary or token-changing coercion, relation-backed selectors and
multiselect controllers are unsupported. Each group has one controller and explicit membership only: no arbitrary
predicates, multiple-controller expressions or dependency graph. Whole-formset `ValueToggle` activation is explicitly
refused by `ConditionalFormSet`; use its existing checkbox descriptors. Product-dependent per-row conditions
(finding 20), expanded compact-radio admission and downstream theme adoption are outside this contract.

### Choice clearing

For controlled standard choice fields, exact native ChoiceField/TypedChoiceField and text/integer model pairs with
native conversion and persistence hooks support this automatic matrix:

| Model field with choices | Inactive value |
|---|---|
| Nullable text, including `blank=True` | `None` |
| Nonnullable text with `blank=True` | `""` |
| Nullable integer | `None` |
| Nonnullable integer | Explicit `empty_values` required |
| Nonnullable text with `blank=False` | Explicit `empty_values` required |

The order is **server-disabled field > explicit dictionary membership > inference**. For editable fields, entries
including `None`, `""`, `False`, `0` and application sentinels are authoritative; native conversion and model/database
constraints still apply. Defaults are not clearing instructions. Plain-form controlled choice fields and nonstandard
form/model pairs require explicit native-compatible `empty_values`; no database nullability is guessed.

The server discards forged inactive editable data and applies clearing even without JavaScript. Only a successful
save persists it. Invalid controller errors are retained; raw submitted data cannot reactivate a group after native
or inherited cleaning rejected/removed the controller. Server-disabled controls use trusted initial values.
Missing controllers retain E311, unsupported automatic clearing retains E312, and value declaration conflicts or
unsupported controller shapes produce E313 where statically inspectable and `ImproperlyConfigured` at runtime.

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
    formsets) runs inside a single database [transaction](request_lifecycle.md#transactions), so a failure elsewhere
    rolls the purge back.

### Scope constraint

Only **first-level** formsets may be conditional. Attaching `ConditionalFormSet` to a nested formset (one with a `parent` key) raises system-check error `crud_views.E310`.

### Usage

```python
from crud_views.lib.conditional import ConditionalFormSet, ModelFieldToggle
from crud_views.lib.formsets import FormSet, FormSets, FormSetMixin

cv_formsets = FormSets(
    formsets={
        "sessions": FormSet(
            title="Sessions",
            klass=SessionFormSet,
            fields=["title"],
            pk_field="id",
            conditional=ConditionalFormSet(
                toggle=ModelFieldToggle("with_sessions"),
                on_off="skip",  # default; use "purge" to delete rows on save
            ),
        ),
    }
)
```

The parent form must expose the toggle field. **`ConditionalFormSet` toggles are never auto-injected** — only `ConditionalGroup` toggles are (by `ConditionalGroupFormMixin`). So either use a real model/form field, declare the checkbox on the form yourself (`forms.BooleanField(required=False)`), or reuse a `UIFieldToggle` that a `ConditionalGroup` on the same form already injects. A toggle that is missing from the form is flagged by system check `crud_views.E311`; without it the formset would be permanently off — and with `on_off="purge"` that silently deletes rows on every save.

---

## System checks

| ID | Level | Meaning |
|---|---|---|
| `crud_views.E310` | Error | `conditional=` placed on a nested (non-first-level) formset |
| `crud_views.E311` | Error | Toggle field named in a `ConditionalGroup` or `ConditionalFormSet.toggle` is absent from the parent form (and not injected by a group on that form) |
| `crud_views.E312` | Error | No supported automatic clearing value for the inspected editable form/model field pair; configure `empty_values` explicitly (replaces W320) |
| `crud_views.E313` | Error | Invalid value-group controller, match values, overlapping controlled fields, controlled controller or required subset |
| `crud_views.W321` | Warning | `on_off="purge"` combined with a formset that forbids row deletion (`can_delete=False` / `edit_only=True`) — the toggle bulk-deletes rows anyway |

---

## Examples

The `examples/bootstrap5/conditional/` app (`conditional/views.py`) shows both kinds side by side:

- `cv_registration` — two field-groups on one form: a `ModelFieldToggle` group (`with_company` → `company_name`, `vat_id`) rendered as a titled `<fieldset>` via `ToggleGroup(..., legend="Company details")`, and a transient `UIFieldToggle` group (`add_note` → `note`), including the pattern of deriving the transient toggle's `initial` from the instance in `__init__`
- `cv_event` — two conditional first-level formsets contrasting the `on_off` modes: `with_sessions` → the `sessions` formset with `"purge"` (rows deleted on save when off), and `with_speakers` → the `speakers` formset with `"skip"` (rows kept)
- `cv_customer` — Dropdown and Radio editors share four value-driven groups and a saved detail view; follow
  **Choice-driven customers** from Registration, then **Choice-driven groups** in the documentation panel.
