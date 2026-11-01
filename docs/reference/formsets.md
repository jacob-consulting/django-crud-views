# Formsets

Formsets let a create/update view edit a parent object together with a collection of related
child objects — inline, on the same page and the same submit — instead of managing the
children through their own separate CRUD views. A formset can itself declare children, so a
row can carry its own nested formset (e.g. each *question* row carries its own *choices*
formset).

!!! example "Try it live"
    The [Formsets example](https://django-crud-views-demo.onrender.com/formsets/questionnaire/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

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
            title=_("Questions"),
            klass=QuestionFormSet,
            fields=["text"],
            pk_field="id",
            children=OrderedDict(
                choices=FormSet(
                    title=_("Choices"),
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
alongside the main form, and saves them (in the same [transaction](request_lifecycle.md#transactions) as the main object) on a
valid submit:

<!-- cv-sync: formsets/views.py -->
```python
class QuestionnaireCreateView(
    BreadcrumbMixin, CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_questionnaire
    form_class = QuestionnaireForm
    cv_formsets: FormSets = cv_formsets
    cv_message_template_code = _("Created questionnaire “{{ object }}”")
```

The update view mirrors this exactly, mixing `FormSetMixin` in against
`UpdateViewPermissionRequired` instead.

## Control button classes

The row controls take their classes from the [button class table](buttons.md): `formset:control` for the move and add
buttons, `formset:container` for the groups and `formset:control-danger` for the delete toggle of a row marked for
deletion. `formsets/control.html` passes the two delete-toggle classes to `formset.js` in `data-cv-class` and
`data-cv-class-danger`; a project override of that template needs both attributes for the toggle to change colour.
Restyle them with `CRUD_VIEWS_BUTTON_CLASSES`.

## The AJAX template endpoint

Formsets support adding another row without a full page reload. Clicking a row's add control
fires an AJAX `GET` back to the same view URL, with a `template` query parameter identifying
the (possibly nested) formset by its key path — e.g. `questions` or `questions|choices` — plus
`pk`, `num`, and `formset_parent_prefix_key`. `FormSetMixin` recognizes this parameter, renders
a single empty row for that formset, and returns it as JSON (an `html` fragment plus a `rows`
key holding the new row's form-prefix strings) instead of running the view's normal `GET`.

This round trip is handled entirely by the bundled `formset.js` script, which ships
automatically with the theme's JavaScript — no template or client-side wiring is required
beyond placing `Formsets()` in the form layout as shown above. The script inserts the returned
row at the right position, increments the formset's `TOTAL_FORMS` management value, and
re-attaches the row's add/delete/order controls. `formset.js` is built on jQuery, so pages with formsets
need jQuery loaded by `DOMContentLoaded`; see [JavaScript](javascript.md#jquery).

### Who may request a row

A row request is answered only for a user who may open the editor itself. Before rendering anything, the endpoint
runs the gates of the page it belongs to:

- An update view loads its object through `get_object()`. A Guardian view therefore checks the object permission and
  the action state, and a missing object, or one under a different URL parent, is a 404.
- A create view runs its dispatch gates: the model-level `add` permission at top level, the parent permission and the
  parent's action state for a nested create.
- A core view checks its permission and action state as on the full page.

A denied request gets 403, or the login redirect or configured anonymous behavior for an anonymous user. An inactive
user gets 403 on Guardian views. No row is rendered and none of the row's choices are evaluated. A row request never
builds the full editor context.

### Coordinates are validated

The endpoint then checks the request's coordinates against the `FormSets` declaration and the stored data. Any
mismatch is a **400** before anything renders:

- `template` must name a declared key path.
- `num` and every index must be 1 to 9 ASCII digits.
- Every identity in `pk` and `formset_parent_prefix_key` must match its declaration's `FormSet.PK` grammar and convert
  with the owning model's primary key field.
- The root identity must be the endpoint's own object, or `None` on a create page. The top-level formset index is
    always `0`, and every nested level must use the declared child index (the zero-based position in its parent's
    ordered `children` mapping).
- Each saved identity must be a stored row whose foreign key points at the identity above it. This ancestry is checked
  on every request, so moving a row to another parent takes effect on the next request. Once an identity is `None`
  (an unsaved row), every deeper one must be `None` too.
- A top-level formset takes no `formset_parent_prefix_key` (or an empty one). A nested formset needs one with exactly
  the declared depth.

!!! note "Supported primary keys"
    Formset row prefixes support integer keys (`FormSet.PK.INT`) and UUID keys (`FormSet.PK.UUID`).
    Slug and arbitrary text primary keys are not supported by the row-prefix protocol, even when the ViewSet's
    ordinary URLs support them. A slug such as `parent-with-hyphens` is rejected with HTTP 400 by the fragment
    endpoint; selecting `INT` or `UUID` does not add slug support. This is an existing client/server protocol
    limitation, not a permission denial. Supporting slugs requires a coordinated client/server prefix design.

Requests that `formset.js` builds for supported primary keys pass these checks. The request parameters and the JSON response (`html` and
`rows`) are unchanged.

An unsaved parent row is `None` in the form prefixes even when a default, such as `uuid.uuid4`, already gave it a
primary key. New-object create pages and extra rows with UUID keys therefore render `None` prefixes, as integer keys
always did, and the rows added in the browser bind on POST. Saved rows keep their primary keys in the prefix.

The endpoint only decides who may receive the editor's rows. Which choices a row's `ModelChoiceField` offers to a user
who may open the editor is still up to your form: restrict its `queryset` as you would on any form. A conditional
formset's server-side purge keeps its own policy; see [Conditional formsets](#conditional-formsets).

Second and deeper sibling declarations now retain their declared index in both page and fragment prefixes.
For example `books|memos`, after sibling `notes`, uses child index `1`. Authorized integer/UUID second-sibling and
deeper additions bind through management data and save; newly inserted descendants also retain the editor endpoint
inside modals. This replaces the former first-declared-child limitation, with real fragment/POST tests and stock/native
HTTP browser acceptance. The integer/UUID grammar and permission/ancestry boundaries above still apply. Row-choice
queryset filtering remains the application's responsibility; unrelated Guardian and primary-key extensions are excluded.

The `pk` request parameter is the actual authorized parent row identity or the unsaved `None` sentinel. It is distinct
from the `pk` grammar/type metadata in the [JSON projections](#exact-json-projections) below; do not send a regex or
`PK.INT` as the request's row identity.

## Validation before saves

Active formsets enforce `edit_only` and submitted row identity after ordinary/custom cleaning, before main, sibling
or nested saves. Nonempty extra rows (including DELETE-marked or nested-only extras) in an edit-only collection
receive nonform error `cv_additions_not_allowed` ("Additions are not allowed."). Missing, malformed, foreign or
filtered existing IDs, and IDs disagreeing with the retained persisted instance, receive generic `cv_invalid_row`
("Invalid row."). Membership uses the authorized managed queryset and its selected database alias. Native/custom
inline formset subclasses cannot bypass this policy with a `clean()` override.

Ordinary full-page invalid submissions re-render with HTTP **200**; modal invalid submissions re-render with HTTP
**422**. No save hooks run for these policy failures. Native form/model errors, errors added to the main form during
child cleaning, and routed atomic rollback remain authoritative. A disabled or hidden browser action is no substitute
for this server validation. Inactive conditional formsets use their separate default skip/opt-in managed-queryset purge
policy, including ignored inactive management data, as described under [Conditional formsets](#conditional-formsets).

## Template projection and native controls

Theme overrides may consume the runtime data passed by the shipped formset templates. This supports rendering;
it does not make `XForm`/`XFormSet` constructors, validation/save methods or JavaScript controllers public APIs.

| Context / projection | Supported rendering data |
|---|---|
| `formsets.x_formsets` | Collection supplied to `crud_views/formsets/formsets.html` |
| `x_formset` | `prefix`, `prefix_key`, `key`, `title`, `management_form`, `instance.non_form_errors`, `forms`; nested/rows-only flags `has_parent`, `render_rows_only`; `cv_active`, bound `cv_toggle_field` |
| Layout data | `level`, `has_pre_col`, `col`, `col_pre`, `css_col`, `css_col_pre` |
| Each `x_form` | `prefix`, `prefix_key`, `key`, `form`, `helper`, nested `formsets` |
| Capabilities | `x_formset.formset.can_delete`, `can_delete_extra`, `can_order`, `edit_only`; these also appear in formset JSON |
| `x_formset.json_data` | `key`, `prefix`, `prefix_key`, `hierarchy`, `parent_prefix`, `parent_prefix_key`, `can_delete`, `can_delete_extra`, `can_order`, `edit_only`, `path`, `fields`, `pk_field`, `pk` |
| `x_form.json_data` | `key`, `prefix`, `prefix_key`, `formset_prefix`, `pk` |

Retain `cv-formset-content` and `cv-data-formset-prefix`/`cv-data-formset` on the content container, and
`cv-formset-row` with `cv-data-formset-form-prefix`/`cv-data-formset-form` on each row. Render management inputs,
and retain each row's `cv-data-formset-prefix` identifying its containing formset. Render
nonform errors, the actual form/helper, and nested formsets. Render Django JSON strings with normal template
escaping in attributes. In row-only fragments omit the containing fieldset/content/management wrapper together;
keep original opening/closing wrappers balanced.

Action hooks are native `<button type="button">` controls with `cv-form-ctrl-add`, `cv-form-ctrl-delete`,
`cv-form-ctrl-up` or `cv-form-ctrl-down`, plus `cv-data-formset-form-prefix` identifying their row. Give each an
accessible name. Preserve capability predicates and `data-cv-class`/`data-cv-class-danger` for delete styling.
The controller ignores actions that are disabled, hidden, inert, ARIA-disabled/hidden or disallowed by capabilities;
non-button synthetic substitutes are outside this contract. Owning-form initialization isolates identical prefixes
in separate forms. Submit reorders only that form before modal FormData serialization; cancellation or reorder failure
prevents fetch. See [initialization](javascript.md#conditional-and-formset-initialization).

### Exact JSON projections

These are separate complete examples for a declaration named `rows`, editor path `/editor/`, one extra row, native
default deletion capabilities and no ordering/edit-only. `prefix_key` is coordinates, not a standalone object ID.
In **XFormSet.data**, `pk` is the declaration's **grammar** (`FormSet.PK.value`), not an actual row identity.
In **XForm.data**, the retained `pk` is the enum spelling `PK.INT` or `PK.UUID`; do not normalize it or rename keys.

Integer declaration with parent ID `42` and field `title`, formset JSON:

```json
{"key":"rows","prefix":"rows-42-0","prefix_key":"42-0","hierarchy":["rows"],"parent_prefix":"","parent_prefix_key":"","can_delete":true,"can_delete_extra":true,"can_order":false,"edit_only":false,"path":"/editor/","fields":["title"],"pk_field":"id","pk":"\\d+"}
```

Its first row JSON (row index `0`):

```json
{"key":"rows","prefix":"rows-42-0-0","prefix_key":"42-0-0","formset_prefix":"rows-42-0","pk":"PK.INT"}
```

UUID declaration with parent ID `12345678-1234-1234-1234-123456789abc` and field `text`, formset JSON:

```json
{"key":"rows","prefix":"rows-12345678-1234-1234-1234-123456789abc-0","prefix_key":"12345678-1234-1234-1234-123456789abc-0","hierarchy":["rows"],"parent_prefix":"","parent_prefix_key":"","can_delete":true,"can_delete_extra":true,"can_order":false,"edit_only":false,"path":"/editor/","fields":["text"],"pk_field":"id","pk":"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"}
```

Its first row JSON:

```json
{"key":"rows","prefix":"rows-12345678-1234-1234-1234-123456789abc-0-0","prefix_key":"12345678-1234-1234-1234-123456789abc-0-0","formset_prefix":"rows-12345678-1234-1234-1234-123456789abc-0","pk":"PK.UUID"}
```

An unsaved parent instead uses `None` in these coordinates, even if a UUID default has assigned a prospective PK.
The `prefix_key` segments also carry nested parent coordinates and declaration indices, as validated by the fragment
endpoint. Both integer and UUID examples are compared with real runtime projections in the documentation tests.

### Initializing widgets in added rows

A row added this way arrives after page load, so scripts that initialize widgets on
`DOMContentLoaded` never see it. After inserting a row, `formset.js` therefore dispatches a
bubbling `cv:formset:row-added` CustomEvent on the new `div.cv-formset-row` element — the
formset counterpart of the [modal's `cv:modal:loaded`](modals.md#extending). Listen on
`document` and initialize inside `event.target`:

```javascript
document.addEventListener("cv:formset:row-added", function (event) {
    // event.target: the new row element
    // event.detail.prefix: its form prefix, e.g. "questions-None-0-3"
    // event.detail.rows: every form prefix the server returned for this add
    initMyWidgets(event.target);
});
```

When the new row contains rows of nested formsets, only the outermost row gets the event —
its `event.target` already contains the nested rows, so a listener never initializes the same
element twice. The package's own scripts (tooltips, [conditional field-groups](conditional.md))
listen for this event already; widget packages such as
[django-crud-views-extensions](https://django-crud-views-extensions.readthedocs.io/) do too.

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
