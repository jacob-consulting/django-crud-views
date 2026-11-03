# Phase 06: Form-button leaf — Design Spec

**Authored:** 2026-10-28 (06-01 task 1), before any Phase 06 product edit and before the baseline commits.
**Status:** Settled design for 06-02 through 06-09. Locked decisions D-01 through D-18 in `06-CONTEXT.md` apply
verbatim by reference; this spec does not restate or reopen them. It settles the internal contracts CONTEXT
delegated to the design (form key set, owner capture/recovery, omission, escaping boundary, attribute
collisions, icon precedence, static-check reach, golden protocol). Where a plan below is named, it owns the
implementation and tests of the contract stated here.

## Prerequisite evidence

D-18 gate, verified on the executing working branch without merge, branch switch or fixed branch name.

| Item | Evidence |
|---|---|
| Executing branch | `introduce-gsd` |
| HEAD SHA at verification | `49f44cd872aec399e7dc240ea8f9d55b1f04ce4d` |
| Verification date | 2026-10-28 |
| Phase 1 completion | `01-VERIFICATION.md` status `passed`, 35/35 must-haves; 01-01..01-05 SUMMARY `status: complete` |
| Phase 2 completion | `02-VERIFICATION.md` status `passed`, 7/7 must-haves; 02-01 SUMMARY `status: complete` (commits a6322d0, 340d29a, d3c63f2) |
| Phase 1 source contract | `src/crud_views/lib/view/label_mode.py:23` immutable `LABEL_MODE_DEFAULTS` (`context`/`list` `icon`, `card` `both`); `default_label_mode()` (84–117) reads `CRUD_VIEWS_LABEL_MODE_DEFAULTS` from `django.conf.settings` on every call (54–58) with shared strict/warn-once fallback `_invalid_label_mode` (61–81) |
| Phase 2 source contract | `src/crud_views/lib/button_classes.py:209–210` independent `VARIANT_LOCATIONS = {context, list, card}` and `FORM_KINDS = {submit, cancel, delete, filter-submit, filter-reset}`; `_action_key_parts` (213–227) admits `form:<kind>:<mode>` only for `FORM_KINDS` |
| Runtime probe at HEAD | `default_label_mode("card")` = `both`; under `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "label"})` = `label`; restored `both` on exit. `_is_action_mode_key`: `form:submit:both` True, `form:primary:both` False, `context:submit:both` False |
| Required test command | `.venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q` → **201 passed, exit 0** |
| Compatibility tracer (existing real-endpoint crispy shard) | `.venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q` → 354 passed; `tests/test1/test_import_safety.py` → 18 passed |

Result: both dependencies are present and valid; the gate passes. No dependency was missing or invalid.

Environment note: `.venv` was absent at execution start and was recreated from the declared dependencies only
(`uv venv --python=3.12`, `uv pip install -e ".[all,dev,test,examples]" -r requirements/demo.txt`). Resolved
versions: Python 3.12.3, Django 6.1.2, django-crispy-forms 2.7, crispy-bootstrap5 2026.9, django-filter 26.2,
django-tables2 3.0.1, pytest 9.2.0. Django 6.1 is newer than the documented 4.2/5.2/6.0 matrix (no upper bound is
declared); the nox matrix and the 06-07 floor session remain the authoritative compatibility evidence.

## Form contract

Carries D-13 and D-14 by reference; FORM-02/03/05/06.

**Location and floor.** `button_data.LOCATIONS` gains `"form"`; `LABEL_MODE_DEFAULTS` gains `"form": "label"`, so
`set(LABEL_MODE_DEFAULTS) == LOCATIONS` still holds and E108 accepts `form` automatically. `VARIANT_LOCATIONS`,
`FORM_KINDS` and the `form:<kind>:<mode>` grammar are unchanged; `form` never becomes a variant location.

**Key set decision.** `LEAF_KEYS` stays exactly as today (action/menu contract). A separate
`FORM_LEAF_KEYS` frozenset is the complete form contract:

| Key | Meaning | Presence |
|---|---|---|
| `cv_location` | always `"form"` | always |
| `cv_key` | the semantic form kind, a `FORM_KINDS` member | always |
| `cv_type` | native button type: `submit`, `button` or `reset` (the adapter's `input_type`) | always |
| `cv_name` | emitted `name` (see Literal text: crispy wordcount/slugify rule) | always |
| `cv_value` | submitted `value`, literal plain `str` | always |
| `cv_label` | visible/hidden text, literal plain `str`; defaults to the same text as `cv_value` | always |
| `cv_id` | element id | always |
| `cv_label_mode` | resolved `label` / `both` / `icon` | always |
| `cv_icon` | resolved semantic icon value or None | always |
| `cv_icon_class`, `cv_icon_inline` | from `icon_host_keys(icon, "form")`; `""`/True in label mode | always |
| `cv_css_class` | class suffix after the class-table classes (see attributes) | always |
| `cv_flat_attrs` | serialized escaped extra attributes (`SafeString`) | always |
| `cv_title` | generated title (= label) | icon mode only |
| `cv_cancel_url` | the cancel navigation URL | kind `cancel` only |

Action-only keys (`cv_href`, `cv_submit_target`, `cv_modal`, `cv_modal_size`, `cv_active`, `cv_tag`,
`cv_disabled`, `cv_disabled_reason`, `cv_variant`, `cv_flex`, `cv_short_label`) never appear in a form result.
06-06 asserts the result keys are a subset of `FORM_LEAF_KEYS` with exactly the presence rules above.

**M-FORM-DATA-KIND.** `cv_button_data(ctx, location, kind="action")` keeps its signature and default. The existing
`KINDS` check still runs first. For `location="form"` the third argument is the rendering category, not a semantic
kind: omitted/default and explicit `kind="action"` are identical; `kind="menu-item"` raises `ValueError` and an
unknown value (e.g. `"pill"`, or a semantic name such as `"submit"`) raises `ValueError` — in both strict and
non-strict mode. Only `ctx["cv_key"]` selects the `FORM_KINDS` member; an unknown `cv_key` or a `cv_type` outside
`{submit, button, reset}` raises `ValueError` independently of the third argument. Context/list/card action and
menu-item validation and rendering are unchanged.

**Branching.** The form branch is taken immediately after argument validation, before any action URL, modal,
target, `cv_tag` or object derivation. The action-only `{% cv_button %}` tag rejects `location="form"` with a
`ValueError` naming `cv_button` and the unsupported location, before `cv_resolve_action`, normalization or
`_BUTTON_LEAVES` selection (L-ACTION-TAG-FORM-ROUTING, 06-02). The form leaf is reached only through the crispy
adapters (and direct `cv_button_data(ctx, "form")` calls in tests).

**Kind source.** The semantic kind comes from the adapter's `slot` (`form:<kind>`), never from the submitted name
(cancel and filter-reset both submit `name="reset"`; a delete hook may choose another slot). On the new layout
render path the slot must be `form:<FORM_KINDS member>`; any other slot (e.g. `formset:control`, `form:unknown`)
raises `ValueError` at render. Legacy `helper.inputs` keep arbitrary slots with no constructor-time rejection and
no warning (M-SLOT; 06-08 records the layout-only Breaking note).

**Empty values.** Missing or None text normalizes to `""`; other falsey data is converted, not blanked
(`0` → `"0"`). A valid empty label stays empty; no text is manufactured.

**Adapter boundary.** `Submit`, `Button`, `Reset` keep `__init__(self, name, value, *, slot=None, **kwargs)` and all
crispy keyword arguments (`css_id`, `css_class`, `template`, extra attrs). Constructor-visible state
(`name`, `value`, `id`, `field_classes`, `flat_attrs`, `template`) stays as crispy computes it, so legacy
`helper.inputs` rendered by the pack's `inputs.html` → `layout/baseinput.html` keep their current markup. Only
`render()` (the layout path) is overridden; it never calls `BaseInput.render`.

## Literal text and attributes

Carries D-15 and D-06 by reference; FORM-05/07.

**No template evaluation.** `BaseInput.render` runs `Template(str(self.value)).render(context)` and assigns the
result to `self.value` (verified in installed crispy 2.7). The adapter never calls it and never compiles any value,
label, name, id or attribute as a template. `{{ request.user }}` stays literal text.

**Normalization.** At render time each textual field is converted to an exact plain `str`: lazy objects resolve
under the active language (`str(value)`), then the result is copied to a `str` that is not `SafeData`
(`str.__str__(...)` on the converted value, or equivalent; tests assert `type(v) is str`). `str()` alone is not
enough: `str(SafeString)` returns the same `SafeString`. Normalization never escapes.

**One escaping boundary.** Plain-`str` fields are escaped exactly once by Django autoescape in the leaf
(`{{ cv_label }}`, `value="{{ cv_value }}"`, `name`, `id`, `title`, class). Extra attributes are serialized once by
the adapter into `cv_flat_attrs` from plain-`str` values with Django's escaping (`flatatt`/`format_html_join`
semantics) and emitted unescaped-again by the leaf. No value is escaped during normalization and again in the leaf;
browser-decoded body/value/title/attributes equal the original strings (06-02 asserts parsed DOM, not substrings).

**Emitted name (M-NAME).** The stored `name` is never mutated. `cv_name` reproduces crispy's original
`baseinput.html` rule at render time: `slugify(name)` when `len(name.split()) > 1` (Django `wordcount`), else the
name unchanged. Probe: `"Search  the Site!"` → `search-the-site`; `"Ünïcode name"` → `unicode-name`. Single-token
names stay literal (including punctuation). Generated ids are upstream's constructor value
`f"{input_type}-id-{slugify(name)}"`, unchanged.

**Reserved attributes — resolved once, one final attribute each:**

1. Underscore aliases are normalized to hyphens first (crispy `flatatt` semantics). When two aliases name the same
   ordinary attribute (`data_x` and `data-x`), the hyphenated spelling wins regardless of keyword order.
2. `type` comes from the adapter class; `name` and `value` from the positional arguments. Extra `type`, `name`,
   `value` keys are discarded.
3. `id`: `css_id` wins over an extra `id`; an extra `id` wins over the generated id.
4. `class`: class-table classes for `form:<kind>[:<mode>]` (via `cv_button_class`), then constructor `css_class`,
   then an extra `class` value — each source appended once, space-separated, no token de-duplication. Host icon
   classes (`cv_icon_class`) follow in the leaf. `cv_css_class` carries the `css_class` + extra-class suffix.
5. Cancel URL: `data_cv_cancel_url` / `data-cv-cancel-url` (hyphen wins) is consumed into `cv_cancel_url` for kind
   `cancel` only and rendered once as `data-cv-cancel-url`. For any other kind no `cv_cancel_url` key exists and
   the value stays an ordinary escaped extra attribute (existing behavior retained).
6. Icon mode generates `title` (= label) and `data-cv-tooltip="form"`; these win over extra `title` /
   `data-cv-tooltip` collisions, which are dropped. In `label` and `both` modes a caller `title` / tooltip remains an
   ordinary escaped extra attribute.
7. Booleans: `True` → bare attribute, `False`/None → omitted (Django `flatatt`).

Attribute **names** are developer-authored code and are the supported input boundary (not an untrusted-key API);
attribute **values** are untrusted literals. No action-only field is added, and crispy's `input` object (or the
adapter object) is never exposed.

**No mutation.** `self.value`, `self.field_classes`, `self.flat_attrs`, kwargs dicts, the normalized input dict and
the caller's `Context` are unchanged after any number of renders; interleaved renders of one shared adapter in two
contexts produce independent output.

## Template selection

Carries D-05, D-06, D-07, D-08 by reference; FORM-03/05.

Precedence: a truthy explicit `template=` argument → a `template` class attribute declared by a subclass of the
package adapter → the bundled default `crud_views/tags/button/form.html`. The package adapters declare the default
as their own class attribute, so crispy's inherited `"%s/layout/baseinput.html"` never wins on the layout path,
and crispy's `self.template = template or self.template` keeps an empty explicit argument falling back
(upstream truthy semantics). `%s` is substituted with the active template pack through
`TemplateNameMixin.get_template_name(template_pack)` (e.g. `%s/buttons/submit.html` → `bootstrap5/...`).

Every selected template — bundled or custom — is rendered with `render_to_string(template, data)` where `data` is
exactly the normalized `FORM_LEAF_KEYS` dict: a scoped context with no outer layers, so no `input` alias, adapter
object, or outer `cv_*` key (even one present in an earlier context layer) can reach it. Custom templates migrate
`input.value` → `cv_value`, `input.name` → `cv_name`, etc. (06-08 documents the migration).

The bundled leaf renders one `<button type="{{ cv_type }}" name="{{ cv_name }}" value="{{ cv_value }}"
id="{{ cv_id }}">` with classes from `{% cv_button_class "form" cv_key cv_label_mode %}`, then `cv_css_class`, then
`cv_icon_class`; `data-cv-cancel-url` only when `cv_cancel_url` is present; `cv_flat_attrs`; and the three bodies:
`icon` — inline icon (when `cv_icon_inline`) plus `<span class="{% cv_button_class 'form' 'hidden-label' %}">`
label, `title` and `data-cv-tooltip="form"`; `both` — inline icon then visible label, no generated title/tooltip;
`label` — label only, no icon, no host classes. Presentation follows `tags/button/action.html`.

## Ownership

Carries D-09, D-10, D-11, D-12 by reference; FORM-11. 06-03 owns implementation and tests.

**Owner recovery (from `Context.dicts`, before any flattening).** Evaluate tiers in order; the first candidate that
`is not None` is the owner and lookup stops (identity, never truthiness — a falsey real object is an owner):

1. **Form tier:** `getattr(form, "cv_view", None)` of the actual `form` argument passed to the adapter's
   `render(form, context, ...)` — never `context["form"]`, never an outer formset/container form.
2. **Current helper tier:** if the package filter helper pushed its private helper-owner entry for this
   invocation, that value; otherwise the `view` key of the **current** crispy invocation's response overlay.
3. **Page tier:** the private transported page owner when present (authoritative, including explicit None meaning
   no page owner); otherwise the nearest non-None `view` in a genuine page layer.

**Overlay provenance.** Crispy's `BasicNode.get_render` builds `node_context = context.__copy__()`, pushes
`{"is_bound": ...}`, then pushes the response dict from `get_response_dict()`. That dict is identified by its
metadata keys (`is_formset`, `template_pack`, `inputs`, `form_method`/`formset_method`, ...) and also carries every
non-underscore helper instance attribute published by `FormHelper.get_attributes()` — which is how `helper.view`
(including `view=None`) arrives and shadows the page. The current overlay is the nearest response overlay scanning
`Context.dicts` from the top; every response overlay (current or enclosing) is a helper layer and is **never** a page
layer. Classification uses this response metadata, never a fixed stack offset: each `FormActions.render` leaves
a pushed layer behind (probe at HEAD with helper `view=None` and page `"PAGE"`: layers for three controls were
`[-, view='PAGE', IS_BOUND, view=None+RESPONSE, -]`, `+FORMACTIONS`, `+FORMACTIONS+FORMACTIONS`, and
`context.get("view")` returned None), and formset rows nest further crispy invocations. No new crispy provenance API
is assumed (H-OVERLAY-PROVENANCE disposition).

**Explicit helpers.** `{% crispy form helper %}` resolves the supplied helper; its attributes reach the response
overlay, so tier 2 reads them there. The adapter never accesses `form.helper` (on `CrispyFormMixin` it is a property
that builds a new helper).

**Filter helper owner entry.** `ListViewFilterFormHelper.render_layout` pushes a private helper-owner context entry
with `context.push(...)` for the duration of its `super().render_layout()` and pops it afterwards (also on
exceptions); no persistent context or instance mutation. Ordinary crispy helpers rely on overlay recovery.

**M-OUTER-HELPER-PAGE.** With page owner P, an enclosing helper owner H, the current row helper `view=None` and row
`cv_view=None`, P wins; with page None, settings/floor apply — H never does. Required real nested-render regressions
(06-03): two FormActions groups plus a later button; nested formset rows with explicit row helpers; page None;
stacked enclosing overlays; ordinary and falsey owners at each tier; explicit row owners overriding P.

**L-FORMSET-PAGE-CONTEXT.** `Formsets.render` flattens context, and `cv_x_formset` is an inclusion tag whose
`InclusionNode` renders with `context.new(...)`, so row crispy invocations lose the page layers. `Formsets.render`
captures only the genuine page-tier owner (same recovery logic, before flattening), puts it under a private Python
context key in a scoped copy, `cv_x_formset` returns that key in its dict (deriving it from a live page Context when
called directly without one), and recursive child inclusions propagate it. The value is consumed only after the row
form and current helper tiers. Explicit None/ordinary/falsey page owners are preserved. Never forward the whole
context, an enclosing/current helper owner, CSRF, or a public `cv_*` key; scope per render; no global/instance cache.

**Configuration after selection.** Once an owner is selected: if it is a CrudView (class or instance) its public
seam is used — `cv_get_action_label_mode("form", kind)` → membership in `cv_get_form_actions_label_mode()` (whole map
via `cv_first_inline_keys(cls.cv_form_actions_label_mode, "form_actions_label_mode")`: view map if not None, else
ViewSet `form_actions_label_mode` if not None, else `crud_views_settings.form_actions_label_mode`), else
`default_label_mode("form")`; subclass overrides of these resolvers are honored. An empty selected map suppresses
lower maps; an unmapped kind reads the floor directly (never a lower map). No target-view scalar or context-button
policy applies to form kinds. An ordinary Django view or no owner uses the settings singleton's form map, then the
floor (D-10/D-11). No warning for differing owners (D-12). Explicit modes never read an invalid strict floor.

**M-SETTINGS-LIFECYCLE.** `CrudViewsSettings.form_actions_label_mode = from_settings("CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE",
default={})` follows the context/list maps: captured when `crud_views.lib.settings` initializes, served by the
`crud_views_settings` singleton. Only the form floor is lazy (`default_label_mode("form")` reads
`CRUD_VIEWS_LABEL_MODE_DEFAULTS` per call). There is no `setting_changed` refresh and none is added: tests change
maps with `monkeypatch.setattr(crud_views_settings, ...)` or explicit `CrudViewsSettings(...)`; a post-import
`override_settings` of the map alone does not change rendering, while a nested floor override does (06-03 proves
the distinction; 06-08 documents it).

New public names (06-03): `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE`, `ViewSet.form_actions_label_mode`,
`CrudView.cv_form_actions_label_mode`, `CrudView.cv_get_form_actions_label_mode()`; `cv_get_action_label_mode`
gains `location="form"`. Owner-recovery helpers and the transport key are private.

## Helper lifecycle

Carries D-01, D-02, D-03, D-04 by reference; FORM-08. 06-05 owns implementation and tests.

**Hook.** `ListViewFilterFormHelper.get_form_actions() -> FormActions | None`. Default:
`FormActions(Submit("submit", _("Apply Filter"), css_id="filter-button", slot="form:filter-submit"),
Reset("reset", _("Reset Filter"), css_id="filter-button-reset"))` (Reset's slot `form:filter-reset`). `None` means
no action group; an empty `FormActions()` is retained as an explicit empty group. A returned group is appended
exactly once per prepared layout.

**Construction.** `__init__(self, view, request, form=None)` is unchanged for callers;
`ListViewTableFilterMixin.get_filterset` keeps `self.formhelper_class(request=self.request, view=self)`. The helper
calls `FormHelper.__init__()` without the form (crispy's initializer replaces any layout with
`build_default_layout(form)` when a form is passed), then sets `self.form = form` when supplied (identity kept).
A class-level declared layout is deep-copied per instance; the class object and other instances are never mutated.
Hidden sort/order/direction controls stay `add_input(Hidden(...))` with today's naming/value logic.

**H-HELPER-TRUTHINESS.** Crispy dispatches `render_layout` only `if helper and helper.layout`, and
`FormHelper.__len__` returns `len(layout.fields)`, so an empty helper is falsey even with a truthy layout.
`ListViewFilterFormHelper.__bool__` returns True, and the prepared instance layout is a private `Layout` subclass
whose `__bool__` returns True. `len(helper)` keeps its field-count meaning. Third-party helper classes are untouched.

**M-EMPTY-REPLACEMENT.** Preparation happens in a `get_attributes()` override before `super()`: crispy's
`get_response_dict` calls it before the truthiness guard. It detects a caller replacement of `helper.layout` by
identity against the prepared instance (including `Layout()` before the first or between renders), deep-copies it,
and wraps an explicitly empty layout as the private truthy layout while preserving its empty field selection.
The genuine no-layout/default-fields case is tracked separately, so an explicit `Layout()` never resurrects
constructor or inferred fields. Preparation is idempotent; lifecycle state uses underscore-prefixed attributes,
which `get_attributes` does not publish.

**render_layout.** For the genuine no-layout case, populate fields from the actual `form.fields` at render time;
then append the hook's group once (tied to the prepared layout identity, not a helper-lifetime flag); push the
owner entry; delegate to `super().render_layout`. Explicit `form=` arguments take the same path without replacing a
declared layout.

**L-SUPPRESSION-MIGRATION.** Clearing `helper.inputs = []` no longer suppresses the stock actions (they are layout
controls now); the migration is overriding `get_form_actions()` to return None, which keeps fields and hidden GET
controls. 06-08 publishes the paired Breaking/migration notice and executes the recipe.

**Pack-owned behavior retained.** Hidden inputs render in the pack's trailing `inputs.html` wrapper after the
visible layout actions (L-HIDDEN-WRAPPER). `display_form.html` still falls back to `uni_form.html` when
`form_html` is empty. No global crispy template override; legacy custom `add_input()` controls stay inputs
without warnings (D-01/D-02).

## Diagnostics and icons

Carries D-16 by reference; FORM-04/09/10/12. 06-04 (icons/leaf) and 06-06 (diagnostics) own implementation.

**Utility keys.** `form:hidden-label` = `"visually-hidden"` and `form:icon-host` = `"{name_class}"` (same default as
the other `*:icon-host` keys) land in 06-02 task 1 with the exhaustive `EXPECTED_KEYS` (71 → 73) and the documented
count; they never accept a mode suffix.

**Icon precedence.** Kind defaults: submit→`save`, delete→`delete`, cancel→`cancel`, filter-submit→`filter`,
filter-reset→`filter-reset`; `save`, `cancel`, `filter-reset` are added to `DEFAULT_ICONS` and `BOOTSTRAP_ICONS`
(06-04). The adapter takes an explicit `icon=` keyword with a sentinel default: omitted → kind default; explicit
None/`""` → intentionally no icon (reaches the missing-icon policy). Forms pass `icon=` through their hooks:
`CrispyFormMixin.submit_icon`, `CrispyDeleteForm.delete_icon`, and `WorkflowForm` supplies `workflow` as its class
default; a per-form `submit_icon` wins. A custom hook's kwargs (icon or slot) win over the standard hook's.

**Placement and the one-render contract.** `icon_host_keys(icon, "form")` decides placement: a valid host icon puts
the `form:icon-host` class on the button and renders nothing inline; a None/empty `form:icon-host` override is the
existing explicit opt-out (no class, nothing inline), not a missing icon. The leaf owns exactly one inline
`{% cv_icon %}` call for icon/both buttons and none for label mode or system checks; no rendered-markup cache and no
new leaf key.

**M-ICON-AVAILABILITY / L-UNREGISTERED-FORM-ICON / L-FONT-ICON-AVAILABILITY.** One private, side-effect-free
availability predicate in `icons.py`, shared by static checks and the form normalizer: `resolve_icon(value)` is None
→ unavailable (explicit None/empty, or a semantic name mapped to None/empty by `CRUD_VIEWS_ICONS`); an empty prefix
(raw CSS class) → available; a nonempty prefix requires a dict library entry in `get_libraries()` and a non-None
`_get_renderers()[prefix]` (resolving the callable is allowed, invoking it is not). For the built-in `font_renderer`
(explicit `"font"` or the omitted default) the `class` template must be a nonempty `str` that formats with the
icon name (and, for host placement, the same validation applies); otherwise unavailable. Custom callable renderers
are available without probes. Never call `render_icon` or any renderer to decide availability. Registry W352 only
visits table entries, so direct per-form values such as `submit_icon="unknown:save"` are covered here. E354 and other
registry diagnostics keep their IDs/messages/severity and are not suppressed.

**Runtime missing-icon policy.** After effective mode and icon resolution, an icon-mode form button with an
unavailable icon: strict (`CRUD_VIEWS_STRICT`) → `ValueError` naming the form kind; non-strict → one warning per
render on the `button_data` logger, switch to `label`, drop generated title/tooltip and host classes, keep the
literal label/value. Empty label as well → keep the empty literal payload and log the both-missing diagnostic.

**Static checks (06-06).** View `cv_form_actions_label_mode`: non-dict or non-str keys → one E211 (stops entry
traversal); a str-keyed dict → one E210 per invalid mode value in insertion order; unknown form kinds with valid
modes → W291 on the view's own attribute only, naming sorted `FORM_KINDS`; None and `{}` valid. Messages name
`cv_form_actions_label_mode`, form kinds and the form floor; context/list `cv_label_mode_checks` messages and
behavior stay byte-compatible. Settings form maps use the existing E106 owner; ViewSet maps use their construction
validator; neither emits W291. The form floor typo path stays E108.
W292 static reach: only concrete statically selected classes whose helper property, action provider and button
hooks are the package implementations — `CrispyDeleteForm` first (delete via `delete_icon` + cancel, never its
inherited `submit_icon`), otherwise `CrispyFormMixin`/workflow (submit via `submit_icon` + cancel); filter helpers
only with inherited default `get_form_actions`; each distinct class of a concrete dict `polymorphic_forms`
(deduplicated per traversal). Never instantiate forms/helpers, call request-dependent `get_form_class`, or execute
custom hooks; overridden providers are dynamic and covered by the runtime policy. `ValueError` is caught only
around mode resolution, so E108/E210/E211 survive strict checking.

## Dependency validation

**Django 6 `format_html`.** Django 6.0 removed only calls without args/kwargs; the function remains (installed
6.1.2 raises `TypeError("args or kwargs must be provided.")` for the zero-argument form). Valid calls, including
`font_renderer`'s, keep working. The literal boundary does not depend on `format_html`.

**jsdom.** Native `SubmitEvent.submitter` and `FormData(form, submitter)` support must be accepted on the reconciled
locked environment (jsdom 30.1.2 under the recorded Node) in 06-07, without polyfills. Inherited probes on jsdom
29.1.1 and the inherited seven-test crispy floor probes are not feature acceptance.

**Floor session.** 06-07 task 3 adds an isolated nox `crispy_floor` session pinning `django-crispy-forms==2.0` and
`crispy-bootstrap5==2023.10`, Python 3.12, Django 4.2 and 6.0, running the expanded Phase 06 feature suite. The
existing matrix and declared floors are preserved; no floor is raised.

**JS runtime (M-NODE-COMMANDS / H-NODE).** Selected runtime: the existing nvm install of the official Node.js
distribution, `/home/alex/.nvm/versions/node/v24.21.0/bin/node` (v24.21.0) with its bundled npm 11.19.0
(`.../lib/node_modules/npm/bin/npm-cli.js`). It satisfies every locked engine range (jsdom 30.1.2
`^22.22.2 || ^24.15.0 || >=26.0.0`, vitest 5.0.3 `^22.12.0 || ^24.0.0 || >=26.0.0`, root `>=20`). Package Legitimacy
Audit rechecked against the checkout: `package-lock.json` (lockfileVersion 3, sha256
`567bff553002a1452d08db94660a206507d70df9711cdd11fd82ee51f4175d2e`) has 96 entries, all `registry.npmjs.org`
sources with integrity; no new package. Restored with `npm ci` (no prior `node_modules`, so no backup needed);
lock hash unchanged; installed jquery 3.7.1, jsdom 30.1.2, vitest 5.0.3. `06-JS-RUNTIME.json` records this and
`06-js-verify.sh` is the single JS gate entry point (re-asserts paths, version, npm identity, lock hash, every
installed package and engine range on each call, then `npm --prefix . test [-- paths]`).
First wrapper run (2026-10-28): all runtime/lock assertions pass (71 installed packages match the lock, 72 engine
ranges, 25 other-platform optionals skipped); 182/183 tests pass. The failure is pre-existing and environmental:
`tests/js/list.filter.test.js:159` uses `toggle.querySelector("#cv-filter-toggle > span:...")` on the element itself,
for which jsdom 30.1.2 returns null (browsers, and the `:scope >` form, return the child). Logged as a deferred item;
the JS gates stay red until it is resolved, and the wrapper must not mask it. `npm audit` reports high-severity
advisories in the transitive dev-only `undici`; not changed here (lockfile is fixed).

### Import safety

After `settings.configure()` and before `django.setup()`, `import crud_views.templatetags.crud_views_formsets` and the
documented `from crud_views_workflow.lib import ... WorkflowForm ...` must stay importable
(`test_templatetags_import_without_app_registry`, `test_workflow_lib_model_mixin_public_path_imports_without_app_registry`).
Importing any `crud_views.lib.view.*` module runs the view package initializer and `base.py`'s Django auth imports,
which need the app registry. Therefore every new dependency of `crispy/buttons.py` (normalizer, owner recovery,
resolver access) and of `crud_views_formsets.py` (page-owner transport) is imported inside `render()` /
`cv_x_formset()` at call time, and the same rule applies to any new transitive import. The bare-settings subprocess
tests are not moved, weakened, or given `django.setup()`. Gate owners: 06-02 task 1 and 06-03 task 2 run that
unchanged two-test shard alongside their real render regressions. Public resolver overrides are preserved.

## Golden history

**FORM-01 / D-17.** Five before-change baselines are committed before any Phase 06 product edit:
`tests/test1/golden/form_buttons/{create,update,delete}.html` (06-01 task 2) and `{workflow,filter}.html`
(06-01 task 3), each commit touching only `tests/test1/test_form_buttons_golden.py` and those fixtures. 06-01-SUMMARY
records both SHAs, `git diff BASELINE^ BASELINE -- src` emptiness and ancestry to HEAD.

**Capture.** Real endpoints through existing clients/fixtures, English and default settings. CRUD and workflow:
individual raw control extraction (submit/delete/cancel controls as exact response substrings, `<input>` or
`<button>` alike, in document order) — no DOM re-serialization, no page normalization, no CSRF token. Filter:
`_extract_filter_form_region` returns the exact raw slice from the unique `<form id="filter-form" ...>` opening tag
through its matching `</form>` — fields, visible actions and the pack-owned hidden-input wrapper — on a GET with
stable nonempty sort/order/direction values; two identical requests must produce identical bytes.

**Comparison.** Tests compare rendered bytes to `read_bytes()`; there is no update-on-test mode. Defaults are also
pinned independently by parsed DOM assertions (text, name, value, id, type, classes; wrapper classes, control
order, hidden names/values, `filter-button-reset`).

**Updates.** Later commits may update only these phase-owned goldens to button markup: 06-02 task 3 the four
layout-control files, 06-05 `filter.html` reusing the unchanged extractor (equality checked with `git show` of the
baseline commit). Each update inspects the raw diff against the baseline commit, which stays in history. No other
golden directory is regenerated. Golden bytes are produced by the installed pack templates (crispy-bootstrap5
`layout/baseinput.html`); they were captured in the environment recorded under Prerequisite evidence.
