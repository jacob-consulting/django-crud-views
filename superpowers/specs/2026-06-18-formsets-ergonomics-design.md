# Formsets ergonomics (issue #29) — Design

**Issue:** [#29 — Formsets ergonomics: derive fields/pk_field from the formset class, configurable labels](https://github.com/jacob-consulting/django-crud-views/issues/29)

**Descoped:** the original third bullet (revisit `parent_form` handling / placeholder parent-required validation) is split out to [#55](https://github.com/jacob-consulting/django-crud-views/issues/55) and is **not** part of this spec.

## Overview & scope

Two additive, backward-compatible ergonomic improvements to the formsets subsystem:

1. **Derive `FormSet.fields` and `FormSet.pk_field`** from the formset `klass` so callers stop repeating data the class already holds.
2. **Make `form_show_labels` configurable** via `FormSet` config instead of being hardcoded in the inline helper.

All production changes are confined to `src/crud_views/lib/formsets/formsets.py` and `src/crud_views/lib/formsets/inline_formset.py`. The render/JS layer is untouched: `render_tree.py` and `static/crud_views/js/formset.js` keep reading `formset.fields` / `formset.pk_field` exactly as before — those attributes are simply now auto-populated when omitted.

## Part 1 — Derive `fields` / `pk_field` from `klass`

### Current state

`FormSet` requires both fields, and every declaration repeats what the `klass` already encodes:

```python
# tests/test1/app/views_formset.py
books=FormSet(
    title="Books",
    klass=BookFormSet,        # inlineformset_factory(Publisher, Book, ..., fields=["title"])
    fields=["title"],         # redundant with klass.form
    pk_field="id",            # redundant with Book._meta.pk.name
    children=OrderedDict(
        notes=FormSet(title="Notes", klass=BookNoteFormSet, fields=["note"], pk_field="id"),
    ),
)
```

### Change

In `formsets.py`, make both optional and derive them in a `model_validator(mode="after")`:

```python
class FormSet(BaseModel, arbitrary_types_allowed=True):
    ...
    fields: List[str] | None = None     # derived from klass.form when omitted
    pk_field: str | None = None         # derived from klass.model pk when omitted

    @model_validator(mode="after")
    def derive_fields_and_pk(self) -> Self:
        if self.fields is None:
            self.fields = list(self.klass.form.base_fields.keys())
        if self.pk_field is None:
            self.pk_field = self.klass.model._meta.pk.name
        return self
```

Explicit values still override (escape hatch). The existing `validate_formset` validator already confirms `klass` is a `BaseInlineFormSet` subclass; derivation can rely on that.

### Why the derivation is correct

- `klass.form.base_fields` is the inline ModelForm's field set. `inlineformset_factory` excludes the parent FK, and the management fields (`ORDER`, `DELETE`, the `id`/pk hidden field) are added per-form-instance via `add_fields`, **not** present in the form-class `base_fields`. So `base_fields.keys()` yields exactly the editable model fields — the same list callers write by hand today (`["title"]`, `["note"]`).
- `klass.model._meta.pk.name` is the child model's PK field name (`"id"` for the examples).
- The client-side `formset.js reorder()` uses `fields` to detect empty rows and `pk_field` to find the PK input; the derived values produce identical strings, so JS behavior is unchanged.

### Edge cases

- Polymorphic formsets use `cv_polymorphic_formsets` and a different mixin; they do not construct `FormSet` with these params, so they are unaffected.
- A pathological `klass` whose `form` lacks `base_fields` cannot occur for a validated `BaseInlineFormSet`; if one were forced in it would `AttributeError` loudly at construction, consistent with the existing `validate_formset` behavior.

## Part 2 — Configurable `form_show_labels` (Scope A)

### Current state

Two hardcoded, opposite call sites in `inline_formset.py`:

- `InlineFormSet.get_helper()` → `helper.form_show_labels = False` (standard inline rows; has `self.formset`).
- `CrispyInlineFormMixin.helper` → `helper.form_show_labels = True` (polymorphic form mixin; **no** `FormSet` object in scope).

### Change

Add a config field to `FormSet` (default preserves current row behavior) and read it in the inline helper:

```python
# formsets.py
class FormSet(BaseModel, ...):
    ...
    form_show_labels: bool = False

# inline_formset.py — InlineFormSet.get_helper()
    helper.form_show_labels = self.formset.form_show_labels
```

### Scope decision: `InlineFormSet` only

The issue targets "InlineFormSet helpers". `CrispyInlineFormMixin` is a **form** mixin used by polymorphic inlines — it holds no `FormSet` config, and labels-on is correct-by-design for those type-picker forms. Threading config into it would require a separate mechanism (class attr or form kwarg) for a path the issue does not target. We leave its `True` hardcoded and document that polymorphic inline labels are not governed by `form_show_labels`.

## Error handling

No new exceptions are introduced. Derivation reads only attributes Django guarantees on a validated inline formset class.

## Testing

New/updated tests under `tests/test1/`:

1. **Derivation** — a `FormSet` built without `fields`/`pk_field` derives `["title"]` and `"id"` from `BookFormSet`; equals the explicit-value form.
2. **Override** — explicit `fields`/`pk_field` still win over derivation.
3. **`form_show_labels` default** — omitted → `InlineFormSet(...).get_helper().form_show_labels is False`.
4. **`form_show_labels` set** — `FormSet(..., form_show_labels=True)` → helper reflects `True`.
5. **Regression** — drop `fields`/`pk_field` from the `views_formset.py` declarations; the existing nested book/note integration flow still renders and saves. Full suite stays green (currently 403 passed / 1 skipped).

## Docs & skill updates

- **CHANGELOG.md** — new "Changed" entry under Unreleased: `FormSet.fields`/`pk_field` are now optional and derived from `klass`; new `FormSet.form_show_labels` (default `False`).
- **Skill** (`~/.claude/skills/django-crud-views/`): update the canonical FormSet example in `SKILL.md` (~line 341) and `references/api-reference.md` (~line 440) to drop the now-redundant `fields=`/`pk_field=` and mention `form_show_labels`.
- **Project docs**: no formsets reference page exists today; creating one is out of scope for #29. The CHANGELOG covers the change.

## Backward compatibility

Both parts are purely additive — optional params and a new defaulted field. Every existing `FormSet(...)` declaration keeps working unchanged. The example/test declarations are simplified to demonstrate the new ergonomics, not because the old form breaks.
