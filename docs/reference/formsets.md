# Formsets

Formsets let a create/update view edit a parent object together with a collection of related
child objects — inline, on the same page and the same submit — instead of managing the
children through their own separate CRUD views. A formset can itself declare children, so a
row can carry its own nested formset (e.g. each *question* row carries its own *choices*
formset).

!!! example "Try it live"
    The [Formsets example](https://django-crud-views-demo.onrender.com/formsets/questionnaire/) and the
    [Formsets + Conditional example](https://django-crud-views-demo.onrender.com/formsets-conditional/conference/)
    in the live demo show this in action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md)
    for data resets and wake-up time.

!!! note "Stability"
    This page documents the supported formsets surface: `FormSetMixin`, `FormSets`, `FormSet`,
    `InlineFormSet`, `Formsets`, `FormControl`, `CompactColumn`, `CompactLayout`, `CompactWidgetCompatible` — the names exported by
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
child formsets should render. The inherited library helper already uses `form_tag=False`;
the page owns the outer form and its CSRF token:

<!-- cv-sync: formsets/views.py -->
```python
class QuestionnaireForm(CrispyModelForm):
    class Meta:
        model = Questionnaire
        fields = ["title"]

    def get_layout_fields(self):
        return [Row(Column8("title")), Formsets()]
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
    cv_context_actions = ["home", "create", "compact_create"]
    cv_context_actions_inline = []
    cv_action_label_template_code = _("Create classic")
    cv_action_short_label_template_code = _("Create classic")
    cv_message_template_code = _("Created questionnaire “{{ object }}”")
```

The update view mirrors this exactly, mixing `FormSetMixin` in against
`UpdateViewPermissionRequired` instead.

## Compact layout

Set `FormSet.compact_layout` to opt one formset into shared desktop column headings and labelled mobile
cards. Omit it or use `None` to retain the classic helper and `form_show_labels` behavior, without compact
metadata work. In compact mode, the columns declaration **replaces** `get_helper_layout_fields()`;
the classic helper is never consulted. Do not duplicate the same row in crispy layout objects.

For a runnable comparison, open **Formsets** from the Bootstrap 5 example home page and sign in as
`alice` / `alice` or `bob` / `bob`. Open **More actions** for **Create classic** / **Create compact**.
Use **Edit classic** / **Edit compact** on each questionnaire list row or in the detail/editor **More actions**
menu. Both presentations edit the same questionnaire,
questions and choices. The code panel shows `cv_compact_formsets`, with independently declared question
and choice columns, and factories using ordinary `InlineFormSet` without duplicate crispy row layouts.
The classic `cv_formsets` tree retains its helper layouts.

### Standalone compact recipe

This recipe uses your application's existing `Publisher`, `Book` and `BookNote` models: `Book.publisher`
is a foreign key to `Publisher`, `Book.title` is a character field, and `BookNote.book` points to `Book`
with a character field `note`. Import these models from your own app. The ordinary Django model forms
accept the existing `cv_view` keyword supplied by `InlineFormSet`; no crispy form subclass or row helper
override is needed. The recipe is executed by the documentation tests through a real update GET and POST.

```python
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from crud_views.lib.formsets import CompactColumn, CompactLayout, FormSet, FormSets, InlineFormSet

from .models import Book, BookNote, Publisher


class InlineRowForm(forms.ModelForm):
    def __init__(self, *args, cv_view=None, **kwargs):
        self.cv_view = cv_view
        super().__init__(*args, **kwargs)


class BookForm(InlineRowForm):
    class Meta:
        model = Book
        fields = ["title"]
        labels = {"title": _("Book title")}


class NoteForm(InlineRowForm):
    class Meta:
        model = BookNote
        fields = ["note"]
        labels = {"note": _("Note")}


BookFormSet = inlineformset_factory(
    Publisher,
    Book,
    form=BookForm,
    formset=InlineFormSet,
    extra=1,
    can_delete=True,
    can_order=False,
)
NoteFormSet = inlineformset_factory(
    Book,
    BookNote,
    form=NoteForm,
    formset=InlineFormSet,
    extra=1,
    can_delete=True,
    can_order=False,
)

cv_formsets = FormSets(
    formsets={
        "books": FormSet(
            title=_("Books"),
            klass=BookFormSet,
            compact_layout=CompactLayout(columns=[CompactColumn("title", span=8)], controls_span=4),
            children={
                "notes": FormSet(
                    title=_("Notes"),
                    klass=NoteFormSet,
                    compact_layout=CompactLayout(columns=[CompactColumn("note", span=8)], controls_span=4),
                ),
            },
        ),
    }
)
```

Assign this `cv_formsets` to your existing `FormSetMixin` create/update view. Keep the main form's
`Formsets()` placement, page-owned outer form and CSRF token, permission checks and normal validation/save
flow from [Usage](#usage). The compact row helper emits neither another form nor another CSRF token.
Load the bundled Bootstrap theme and `crud_views/css/formset.css` along with the existing formset JavaScript.

Each node chooses independently. To use **compact books / classic notes**, retain the books declaration
and use your existing classic notes `FormSet` under `children["notes"]`, with `compact_layout=None` and its
existing `InlineFormSet` subclass implementing `get_helper_layout_fields()`. For **classic books / compact
notes**, retain your classic books declaration and attach the recipe's compact notes declaration under its
`children`. Compact/compact and classic/classic also work, as do independently configured siblings. Merely
removing `compact_layout` from this recipe's bare `InlineFormSet` is insufficient: classic rendering needs
its usual helper implementation. Existing custom classic helpers remain valid and unchanged.

### Declaration and validation

The public constructors are `CompactColumn(field: str, *, span: int)` and
`CompactLayout(columns: list[CompactColumn] | tuple[CompactColumn, ...], *, controls_span: int)`.
Both are frozen dataclasses; columns are copied into an immutable tuple. `FormSet.compact_layout` accepts
a `CompactLayout` instance or `None`, not a dictionary or string shorthand.

Columns render in declaration order. Names must be nonempty exact field names without whitespace or
duplicates. Spans and `controls_span` must be actual integers from 1 through 12, excluding booleans and
coercible strings/floats. At least one column is required. Field spans plus controls must total at most 12;
an underfilled row keeps trailing empty space rather than stretching. The controls width stays reserved on
desktop even when no buttons are available. Width does not grant add/delete/order capabilities.

Bad declarations raise `ValueError` during construction, for example `CompactColumn.span must be an integer
from 1 to 12`, `CompactLayout.columns must not contain duplicate field names`, or
`CompactLayout field and controls spans must total at most 12`. Pydantic rejects an invalid
`FormSet.compact_layout` value when constructing `FormSet`.

Field/schema validation occurs against request-time forms when compact headings or helpers are first
accessed for rendering, including invalid POST redisplays and fragments. It raises Django
`ImproperlyConfigured`, with messages such as `FormSet 'books' compact field 'title': visible field is missing
from CompactLayout`, `field does not exist`, `hidden and identity/control fields cannot be compact columns`,
`unsupported compact widget or custom template`, or `a nonempty effective label is required` (each reason
uses the same formset/field prefix). Rows must have uniform field types, labels, required state and widget
shapes; disagreement reports `rows must have uniform field types, labels, required state and widget shapes`.
These are configuration errors, not user-input validation errors or a silent fallback to classic rendering.

### Fields, labels and supported widgets

Forms own fields, widgets, attributes, labels, help text, required state and validation. Every ordinary
visible field must appear once, including optional and disabled fields. Hidden fields, model PK, parent FK,
`ORDER` and `DELETE` stay outside the columns; existing hidden values and management fields still render.
Do not declare them as visible compact columns. Hidden-field errors remain visible with their owning row.

Unmarked widgets use these **exact stock Django widget classes** with standard templates and input types:

| Widget | Template | Input type |
| --- | --- | --- |
| `TextInput` | `django/forms/widgets/text.html` | `text` |
| `NumberInput` | `django/forms/widgets/number.html` | `number` |
| `DateInput` | `django/forms/widgets/date.html` | `text` |
| `Select` | `django/forms/widgets/select.html` | `select` |

`Select` also requires the stock `django/forms/widgets/select_option.html` and single selection. This includes
`ModelChoiceField` using `Select`. Unmarked subclasses, custom widget/option templates, changed `input_type`,
multiple selection and unlisted widgets are rejected. Unmarked checkboxes, radio groups, multiwidgets, file
inputs, password inputs and textareas are unsupported. Stock `DateInput` remains a text input; setting its
type to `date` is outside this default boundary. Ordinary attributes remain form-owned.

For explicit opt-in, inherit `CompactWidgetCompatible` alongside the widget class. Descendants inherit the
marker too. This bypasses **all widget-specific restrictions**: widget family, widget and option templates,
input/option types and multiple selection. Other widget families, radio groups and multiselects may therefore
pass admission. The shared checks still require full declared-field coverage (including optional/disabled
fields), exclude hidden/identity/control fields, require nonempty effective labels and compare actual row
field types, widget types, labels and required state. Classic rendering is unchanged.

The marker is the widget author's promise about the complete integration. It supplies no rendering behavior
and neither inspects nor validates arbitrary HTML, CSS or JavaScript, nor guarantees equal heights. Authors
must provide accessible associated row labels or group semantics, shared desktop headings and mobile row
labels, visible necessary option labels, readable help and errors, correct prefixed IDs/names, and any
dynamic-row initialization their widget needs. Test focus, invalid redisplay and added/deleted rows at both
widths. Built-in `CheckboxInput` support and its desktop/mobile label fix are a **separate issue**; marking a
checkbox alone does not repair its labels. A marked checkbox needs an application-owned adaptation.

Effective form labels, including constructor changes and lazy translation resolved in the current request,
supply both headings and associated row labels. They must be nonblank and uniform within each formset.
There is no second label dictionary or global translated-label cache. Compact mode takes precedence over
`form_show_labels=False`: it always emits associated labels, visually clips them at desktop widths and
shows them on mobile. Required markers, help text and field errors remain available at every width; row
non-field errors and formset errors stay with their respective owners.

### Custom widget compatibility recipe

This self-contained widget uses ordinary choice values and preserves Django's option attributes through
`super().create_option()`. Use `ProductSelect` as your form field's `widget` (including in `Meta.widgets`
for a model choice). The documentation test copies this exact fence into a compact Book form and renders
the nonempty `beans` option, including its label and metadata, through an authenticated update request.

```python
from django import forms

from crud_views.lib.formsets import CompactWidgetCompatible


class ProductSelect(CompactWidgetCompatible, forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value == "beans":
            option["attrs"]["data-beans"] = "1"
        return option
```

Keep ordinary option labels and help text as ordinary strings so Django/crispy can escape them. For model
choices, configure the widget when constructing the field so Django binds its choice iterator. The marker
does not add choices, initialize JavaScript or certify another widget's output.

### Metadata and query boundary

Headings reuse actual row forms without evaluating choices, rendering widgets or consulting classic helpers.
For a **zero-total** formset, compact constructs one metadata-only form using the formset's `form` class and
`get_form_kwargs(None)`. It does not call `empty_form` or inline `add_fields()`, so it does not clear an
unsaved parent's default primary key. Custom form constructors and `get_form_kwargs(None)` must be query-free
and supply index-independent field/label/required/widget metadata. Do not supply the live parent as that
metadata form's `instance`; this raises `compact metadata cannot use the live parent instance`.
Adding or changing compact columns in `add_fields()` is unsupported because that hook is not part of the
zero-total metadata path. Keep column metadata in the form constructor or field declarations.

Compact itself adds no database queries merely for headings. This is not a promise that rendering a formset
is query-free: authorized row querysets and normal model-choice widget rendering can query the database.
Classic formsets do not construct compact metadata forms.

### Responsive nesting, controls and empty cases

At **768px and wider** (Bootstrap `md`), one heading strip per compact formset aligns with the declared
field and control widths. It belongs to the formset, outside its rows, and survives first-row deletion or
reordering. Below 768px, headings are hidden visually and each row becomes a full-width labelled card.
Inputs keep their own programmatic labels at every width. Resizing changes presentation, not form values,
IDs or focus. Descriptive labels/help/errors wrap; native controls retain native value display behavior.

Children remain expanded inside their parent row. Each compact child has its own heading strip and small
local inset, without a full grid-column offset at each compact level. Classic children retain classic
geometry. Existing recursion supports a verified grandchild composition; this adds neither an arbitrary-depth
guarantee nor a new depth limit. Top-level rows-only AJAX fragments omit duplicate headings; a new parent row
can contain complete child wrappers and their headings.

Existing add/delete/order controls, flags and scoped row identities remain authoritative. Delete is still
a reversible mark until save. `can_delete_extra=False` can omit `DELETE` on extra rows; compact neither
requires nor fabricates it. Read-only/edit-only/no-control rows reserve the declared desktop control width.

- **Zero initial rows with `extra > 0`:** blank extra rows render with headings, labels and existing controls.
- **Zero total rows:** management data and headings remain, but there is no row-owned Add control and no new
  empty-state recovery button.
- **`extra=0`:** existing rows can render, but the existing Add fragment path needs an extra form. Requesting
  Add raises `IndexError`/HTTP 500 and inserts nothing. Compact does not fix that existing limitation; configure
  an extra form when adding is required.
- Failed AJAX retains the existing absence of visible error/retry UI. Authorization, prefixes, row-added
  events, validation, deletion/order policy, transactions and saving continue through the existing lifecycle.

### Compact theme surface and exclusions

The additive public surface is `CompactColumn`, `CompactLayout`, `CompactWidgetCompatible`,
`FormSet.compact_layout`, these six CSS hooks
and the overridable `crud_views/formsets/compact_headings.html` include:

| Hook | Owner / purpose |
| --- | --- |
| `cv-formset-compact` | Opted-in formset fieldset |
| `cv-formset-compact-headings` | Shared heading strip outside all rows |
| `cv-formset-row-compact` | Opted-in row boundary and padding |
| `cv-formset-compact-fields` | Row's own field/control grid, excluding child formsets |
| `cv-formset-compact-label` | Associated label with responsive visual clipping |
| `cv-formset-compact-child` | Compact child node's local inset; absent on classic children |

Theme styles should target each node's own hooks or direct owned structure to avoid affecting classic
descendants. Keep `div.cv-formset-row`, `.cv-formset-form`, `.cv-formset-content`, prefix/control attributes and
the existing row-added event contract. Use the existing `formset:*` button class registry for controls; no new
registry is introduced. The heading include uses escaped form labels and declared spans. Private projection
and helper functions, and the runtime render tree, remain implementation details.

Arbitrary crispy layout inference/objects, custom HTML cells, multiple row layouts, per-row conditional
columns, heterogeneous/polymorphic schemas, collapsing children, sticky headings, computed/numbered summaries,
configurable mobile variants, separate bottom Add buttons and new empty-state controls are excluded.
There is no promise to implement these later. jQuery removal is separate work. Existing legend rendering is
reused; this adds no legend-hook API (issue #346). Downstream theme adoption is separate follow-up work.

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

Policy is reapplied after native recleaning, including when later custom child cleaning replaces an earlier
formset's cached errors. Repeated validation must still reject the same prohibited addition or invalid identity
before **any** main, sibling or nested save. This applies to package inline formsets and accepted native/custom
adapters; a client capability flag never grants persistence authority.

Ordinary full-page invalid submissions re-render with HTTP **200**; modal invalid submissions re-render with HTTP
**422**. No save hooks run for these policy failures. Native form/model errors, errors added to the main form during
child cleaning, and routed atomic rollback remain authoritative. A disabled or hidden browser action is no substitute
for this server validation. Inactive conditional formsets use their separate default skip/opt-in managed-queryset purge
policy, including ignored inactive management data, as described under [Conditional formsets](#conditional-formsets).

### Repeated validation regression recipe

The documentation test supplies a bound runtime tree named `formsets`, with an active edit-only extra or invalid
existing identity, and `expected_code` equal to `cv_additions_not_allowed` or `cv_invalid_row`. This executable
regression snippet deliberately inspects internal test plumbing; it is not an application validation/save API.
Applications continue to use `FormSetMixin`'s normal view flow. `XForm`/`XFormSet` and their methods remain private.

```python
assert formsets.all_valid() is False
for _ in range(2):
    formsets.x_formsets[0].instance.full_clean()
    for _ in range(2):
        assert formsets.all_valid() is False
        errors = formsets.x_formsets[0].instance.non_form_errors().as_data()
        assert sum(error.code == expected_code for error in errors) == 1
```

The test runs this exact sequence with package and native adapters and verifies zero save calls and unchanged rows.
Inherited field/nonfield/model validation and selected-queryset/database checks remain authoritative.

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
`cv-formset-row` with `cv-data-formset-form-prefix`/`cv-data-formset-form` on each row. Retain each row's
`cv-data-formset-prefix` identifying its containing formset. Render management inputs, nonform errors, the actual
form/helper, and nested formsets. Render Django JSON strings with normal template
escaping in attributes. In row-only fragments omit the containing fieldset/content/management wrapper together;
keep original opening/closing wrappers balanced.

Action hooks are native `<button type="button">` controls with `cv-form-ctrl-add`, `cv-form-ctrl-delete`,
`cv-form-ctrl-up` or `cv-form-ctrl-down`, plus `cv-data-formset-form-prefix` identifying their row. Give each an
accessible name. Preserve capability predicates and `data-cv-class`/`data-cv-class-danger` for delete styling.
The controller ignores actions that are disabled, hidden, inert, ARIA-disabled/hidden or disallowed by capabilities;
non-button synthetic substitutes are outside this contract. Owning-form initialization isolates identical prefixes
in separate forms. Submit reorders only that form before modal FormData serialization; cancellation or reorder failure
prevents fetch. See [initialization](javascript.md#conditional-and-formset-initialization).

### Native row capability recipe

Native Django forms expose `DELETE` only for rows eligible for deletion: `can_delete=True` enables it for initial
rows, while extra rows also require `can_delete_extra=True`. Test **`'DELETE' in form.fields`** rather than the
truthiness of `form.DELETE` or a row's current visual position. Moving or inserting rows never changes their native
initial/extra eligibility. A missing DELETE field is normal on a nondeletable extra; it must not disable permitted
Add, Move or submission. `edit_only` independently prevents Add, and `can_order` independently permits Move.

This complete minimal `crud_views/formsets/control.html` override receives `form` and the `formset` declaration.
It keeps native buttons, accessible names, exact bound prefixes and delete styling hooks; customize its labels or
classes as needed. Keep the actual form fields, management inputs and enclosing row/content hooks described above.

```django
{% load crud_views i18n %}
<div class="cv-form-ctrl">
{% if formset.can_order %}
    <button type="button" class="cv-form-ctrl-up" aria-label="{% translate 'Move up' %}"
            cv-data-formset-form-prefix="{{ form.prefix }}">{% translate 'Move up' %}</button>
    <button type="button" class="cv-form-ctrl-down" aria-label="{% translate 'Move down' %}"
            cv-data-formset-form-prefix="{{ form.prefix }}">{% translate 'Move down' %}</button>
{% endif %}
{% if not formset.edit_only %}
    <button type="button" class="cv-form-ctrl-add" aria-label="{% translate 'Add row' %}"
            cv-data-formset-form-prefix="{{ form.prefix }}">{% translate 'Add row' %}</button>
{% endif %}
{% if 'DELETE' in form.fields %}
    <button type="button" class="cv-form-ctrl-delete" aria-label="{% translate 'Delete row' %}"
            data-cv-class="{% cv_button_class 'formset' 'control' %}"
            data-cv-class-danger="{% cv_button_class 'formset' 'control-danger' %}"
            cv-data-formset-form-prefix="{{ form.prefix }}">{% translate 'Delete row' %}</button>
{% endif %}
</div>
```

The documentation test renders this exact recipe against real native initial and extra forms with
`can_delete_extra=False`: both retain Add/Move, and only the initial row exposes Delete.

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
