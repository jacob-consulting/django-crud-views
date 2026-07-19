# Formsets

Formsets let a create/update view edit a parent object together with a collection of related
child objects — inline, on the same page and the same submit — instead of managing the
children through their own separate CRUD views. A formset can itself declare children, so a
row can carry its own nested formset (e.g. each *question* row carries its own *choices*
formset).

!!! note "Stability"
    This page documents the supported formsets surface: `FormSetMixin`, `FormSets`, `FormSet`,
    `InlineFormSet`, `Formsets`, `FormControl` — exactly the names exported by
    `crud_views.lib.formsets`. The formsets machinery behind them (rendering tree, per-formset
    plumbing) is internal and stays internal in 1.0 — see [API stability](../development/stability.md).

The examples on this page come from the `formsets` example app (`examples/bootstrap5/formsets/`),
which models a `Questionnaire` with nested `Question` and `Choice` child collections.

## Usage

### The child form and its inline formset

A child row is a plain `CrispyModelForm`. Its layout — how a single row is rendered — lives on
an `InlineFormSet` subclass, not on the form itself; `self.form_control_col4` places the
row's add/delete/order controls in a column. The subclass is then bound to the parent/child
model pair with Django's own `inlineformset_factory`:

<!-- cv-sync: formsets/views.py -->
```python
class QuestionForm(CrispyModelForm):
    class Meta:
        model = Question
        fields = ["text"]


class QuestionInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return [Row(Column8("text"), self.form_control_col4)]


QuestionFormSet = inlineformset_factory(
    Questionnaire,
    Question,
    formset=QuestionInlineFormSet,
    form=QuestionForm,
    fields=["text"],
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    can_order=True,
)
```

### Declaring the formset tree with `FormSets`/`FormSet`

`FormSet` wraps a formset class with the metadata the mixin needs to render and drive it:
`title` (section heading), `klass` (the formset class from `inlineformset_factory`), `fields`
(used to detect empty rows), and `pk_field`. Nest a formset under another by passing
`children=` — here every `Question` row carries its own `Choice` formset:

<!-- cv-sync: formsets/views.py -->
```python
cv_formsets: FormSets = FormSets(
    formsets=OrderedDict(
        questions=FormSet(
            title="Questions",
            klass=QuestionFormSet,
            fields=["text"],
            pk_field="id",
            children=OrderedDict(
                choices=FormSet(
                    title="Choices",
                    klass=ChoiceFormSet,
                    fields=["label"],
                    pk_field="id",
                )
            ),
        ),
    )
)
```

### The parent form

The parent's own `CrispyModelForm` only needs to place a `Formsets()` layout element where the
child formsets should render, and turn off `form_tag` — the formsets render their own form
tags:

<!-- cv-sync: formsets/views.py -->
```python
class QuestionnaireForm(CrispyModelForm):
    class Meta:
        model = Questionnaire
        fields = ["title"]

    def get_layout_fields(self):
        return [Row(Column8("title")), Formsets()]

    @property
    def helper(self) -> FormHelper:
        # the formsets render their own form tags
        h = super().helper
        h.form_tag = False
        return h
```

### The view

Mix `FormSetMixin` into the create/update view and set `cv_formsets` to the `FormSets`
instance declared above. `FormSetMixin` builds the formsets into the context, validates them
alongside the main form, and saves them (in the same transaction as the main object) on a
valid submit:

<!-- cv-sync: formsets/views.py -->
```python
class QuestionnaireCreateView(
    BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_questionnaire
    form_class = QuestionnaireForm
    cv_formsets: FormSets = cv_formsets
    cv_message_template_code = "Created questionnaire »{{ object }}«"
```

The update view mirrors this exactly, mixing `FormSetMixin` in against
`UpdateViewPermissionRequired` instead.

## The AJAX template endpoint

Formsets support adding another row without a full page reload. Clicking a row's add control
fires an AJAX `GET` back to the same view URL, with a `template` query parameter identifying
the (possibly nested) formset by its key path — e.g. `questions` or `questions|choices` — plus
`pk`, `num`, and `formset_parent_prefix_key`. `FormSetMixin` recognizes this parameter, renders
a single empty row for that formset, and returns it as JSON (`html` and the new row's
`rows` prefixes) instead of running the view's normal `GET`.

This round trip is handled entirely by the bundled `formset.js` script, which ships
automatically with the theme's JavaScript — no template or client-side wiring is required
beyond placing `Formsets()` in the form layout as shown above. The script inserts the returned
row at the right position, increments the formset's `TOTAL_FORMS` management value, and
re-attaches the row's add/delete/order controls.

## Conditional formsets

A first-level formset can be toggled on/off from a checkbox on the parent form — hidden and
excluded from validation client-side, and authoritatively skipped or purged server-side. This
is a separate, opt-in feature (`ConditionalFormSet`, from `crud_views.lib.conditional`) layered
on top of the plain declaration shown above; see
[Conditional Field-Groups & Conditional FormSets](conditional.md) for the full contract,
including the `on_off="purge"` deletion warning and the first-level-only scope constraint.

## See also

- [`examples/bootstrap5/formsets/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/formsets) — the full `Questionnaire` → `Question` → `Choice` example app these snippets are drawn from
- [Conditional Field-Groups & Conditional FormSets](conditional.md) — toggling field-groups and first-level formsets on/off
- [API stability](../development/stability.md) — what part of the formsets surface is covered by semver
