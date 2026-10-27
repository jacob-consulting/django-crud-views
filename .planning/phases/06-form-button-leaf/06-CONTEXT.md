# Phase 6: Form-button leaf - Context

**Gathered:** 2026-10-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Render package form buttons through `crud_views/tags/button/form.html` as real `<button>` elements, with
shared label-mode, icon, class-table, and escaping contracts (FORM-01 through FORM-13; source plan 2, #257).
Preserve submitted names/values, cancel navigation, filter reset, and hidden sort/order inputs.

This discussion settles custom-helper compatibility, template overrides, and view ownership. No separate
SPEC.md exists. Carry these decisions into the roadmap-required form-button design/spec before implementation;
research must resolve the remaining internal and dependency questions listed below. Implementation and the
Phase 7 stability policy are outside this discussion workflow.

</domain>

<decisions>
## Implementation Decisions

### Custom filter helpers
- **D-01:** Existing custom helpers that use `add_input(Submit(...))` retain their existing rendering. Do not
  automatically relocate those controls or globally override crispy templates. Document migration to layout
  `FormActions` to opt into the new leaf, icons, and label modes. Hidden sort/order inputs retain their path.
- **D-02:** This compatibility limitation is documentation-only: no new system-check or runtime warning for
  legacy `add_input()` placement. This does not suppress existing or required configuration diagnostics.
- **D-03:** Preserve the documented `ListViewFilterFormHelper` subclass pattern that declares only filter
  fields in a class-level `layout`. The base helper appends Apply/Reset after those fields, exactly once per
  form. Repeated instantiation/rendering must not accumulate controls in a shared layout.
- **D-04:** Add a filter-helper `get_form_actions()` hook following `CrispyFormMixin`, allowing subclasses to
  replace or omit the default actions. The default returns the Apply/Reset actions through `FormActions`.
  Exact representation of an omitted action group is an implementation detail to document and test.

### Custom button templates
- **D-05:** Honor explicit `template=` on the package's `Submit`, `Button`, and `Reset` adapters. Render custom
  templates with the normalized form-button context and document migration from crispy's old context.
- **D-06:** Expose the new `cv_*` button contract, without a legacy crispy `input` object. Existing custom
  templates must migrate references such as `input.value` to `cv_value`. Preserve the required escaped
  extra-attribute support; this decision does not remove that support.
- **D-07:** Preserve subclass template attributes. Precedence is explicit `template=` argument, then the
  subclass's `template` attribute, then the bundled `crud_views/tags/button/form.html` default.
- **D-08:** Preserve crispy's `%s` template-pack substitution in template names, for example
  `%s/buttons/submit.html`. These templates still consume the new form-button context.

### Which view controls a form
- **D-09:** Resolve ownership in this order: `form.cv_view`, helper `view`, page-context `view`. Explicit form
  ownership wins over an enclosing page, including an embedded form whose owner differs from the page.
- **D-10:** With no owner, render standalone buttons using `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` for the kind,
  then the form label-mode floor. Do not require a crud_views view merely to render a button.
- **D-11:** An explicit ordinary Django view without crud_views configuration stops the owner lookup. Use
  project settings/defaults instead of borrowing a lower-priority helper/page view. This qualifies D-10:
  select the owner first, then determine whether it supplies crud_views configuration.
- **D-12:** Different form/helper/page view references produce no conflict warning or error. Apply the stated
  precedence quietly; embedded forms with different owners are valid.

### Carried-forward requirements and constraints
- **D-13:** Add `form` to button-data locations and the lazy defaults with the package floor `label`.
  Preserve Phase 2's finite `FORM_KINDS` and `form:<kind>:<mode>` grammar independently of variant locations.
  Form mode maps on settings, ViewSet, and view follow existing whole-map selection semantics; do not confuse
  these with the per-key merge of `CRUD_VIEWS_LABEL_MODE_DEFAULTS`.
- **D-14:** Use the new form leaf and normalized contract from FORM-02/03: `cv_type`, `cv_name`, `cv_value`,
  `cv_id`, cancel-only `cv_cancel_url`, and kind in `cv_key`. Add `form:hidden-label` and `form:icon-host`.
  Preserve host and inline icon behavior. Icon mode has hidden text, title, and `data-cv-tooltip="form"`;
  both shows icon plus text; label shows text. Preserve constructor arguments and appended `css_class`.
- **D-15:** Values and labels are escaped literal text, never evaluated as Django templates. Cover markup,
  attribute-breaking strings, and `{{ request.user }}` in both body and value attribute. Record the DOM,
  value-templating, and custom-template-context changes in CHANGELOG Breaking and `docs/migrating-1.0.md`.
- **D-16:** Preserve required icon mappings: submit/save, delete/delete, cancel/cancel,
  filter-submit/filter, filter-reset/filter-reset; workflow submit uses workflow. Per-form `submit_icon`
  wins. Extend E210/E211/W291 and W292 as specified; missing-icon icon-only rendering raises in strict mode,
  otherwise logs and falls back to the label. No-warning choices D-02/D-12 do not weaken these checks.
- **D-17:** Commit before-change goldens before implementation; preserve default names, values, IDs and
  classes while changing element type. Keep delete POST data and `filter-button-reset`. The example enables
  form `both`. Preserve project quality gates and record downstream-theme follow-up in acceptance without
  editing a downstream repository. Follow the project rule against downstream project names in new files.

### Agent's Discretion and Required Research
- No additional product choice was explicitly delegated. Helper placement, test organization, and precise
  documentation wording remain implementation choices within these decisions.
- Resolve a shared `LEAF_KEYS` versus separate form-key set in the required design/spec; preserve the public
  form contract and avoid adding irrelevant action-only fields. Do not ask the user to choose internal sets.
- Verify the lowest supported crispy versions and the `add_input()` versus layout rendering paths. Determine
  the appropriate floor-validation session within current support constraints; do not silently raise floors.
- Verify the roadmap's Django 6.0 `format_html` concern precisely and jsdom `SubmitEvent.submitter` support.
  These are investigation tasks, not findings established by this discussion.
- Define the hook's omission behavior, isolate mutable subclass layouts, and ensure controls are added once.
  Establish the safe normalization and extra-attribute contract before implementation.
- Treat an absent/None view reference as no owner and proceed to the next source; an actual ordinary view
  object is the explicit owner described in D-11. This is an implementation interpretation of ownership,
  not an additional user-selected API.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and prior contracts
- `.planning/ROADMAP.md` — Phase 6 goal, required design/spec questions, and dependency checks.
- `.planning/REQUIREMENTS.md` — FORM-01 through FORM-13 and excluded approaches.
- `.planning/PROJECT.md` — stable public names, compatibility, documentation rules, and quality gates.
- `.planning/phases/01-label-mode-defaults/01-CONTEXT.md` — lazy floors and existing resolution constraints.
- `.planning/phases/02-form-key-grammar/02-CONTEXT.md` — finite form kinds and settled mode-key grammar.
- `superpowers/plans/2026-10-24-concept-review-followups.md` — source plan 2; this discussion settles its
  custom-helper, template-override, and view-lookup questions.
- `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` — review rationale for the form leaf.

### Public documentation and migration
- `docs/reference/buttons.md` — form buttons, leaf contracts, class keys, and live key-count guard.
- `docs/reference/list_view.md` — documented field-only helper subclasses.
- `docs/getting_started/tutorial-5-filters-permissions.md` — helper example and prose to update consistently.
- `docs/reference/action_menus.md` — existing label-mode resolution and new form column.
- `docs/reference/icons.md` — registry names and host placement.
- `docs/reference/settings.md` — label defaults and per-kind form-map documentation.
- `docs/reference/theme.md` — template overrides and theme integration.
- `docs/migrating-1.0.md` — Form buttons section and custom helper/template migration recipes.
- `CHANGELOG.md` — paired Breaking entry.
- `CLAUDE.md` — repository conventions and Breaking/migration rule.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/crud_views/lib/crispy/buttons.py`: small wrappers currently set class-table slots before delegating to
  crispy; preserve constructor/class behavior while adding leaf rendering.
- `src/crud_views/lib/crispy/form.py`: existing `get_form_actions()`, submit/cancel/delete hooks, and explicit
  `cv_view` ownership provide the pattern for filter customization.
- `src/crud_views/lib/view/button_data.py`: shared flat normalization, strict/log-and-fallback behavior,
  and `icon_host_keys()`; form fields and location are not yet present.
- `src/crud_views/lib/view/label_mode.py`: lazy defaults and validation. `src/crud_views/lib/view/base.py`
  supplies whole-map selection; preserve that established distinction from per-key floor merging.
- `src/crud_views/lib/button_classes.py`: finite form grammar already exists; add hidden-label/host keys
  without broadening variant grammar.

### Established Patterns
- The installed crispy Bootstrap `inputs.html` includes `baseinput.html` directly for helper inputs, so a
  button `render()` override alone does not migrate `add_input()` controls. Layout rendering calls the
  adapter and is the selected path for the new leaf.
- The installed crispy `BaseInput` supports constructor/class template overrides and `%s` substitution;
  its current render path evaluates values as templates. The new adapter must bypass value evaluation.
- `ListViewFilterFormHelper` currently adds actions and hidden controls through `add_input()` and stores
  `view`. `ListViewTableFilterMixin` constructs the configured helper with view and request. Documented
  subclasses declare shared class-level layouts, requiring instance isolation before appending actions.
- `CrispyFormMixin` owns `cv_view`; page context supplies `view`. Resolve ownership separately from map
  selection so unrelated page configuration does not leak into explicitly owned forms.

### Integration Points
- `src/crud_views/lib/views/list.py` and `src/crud_views/lib/views/mixins.py`: filter actions and owner wiring.
- `src/crud_views/lib/settings.py`, `src/crud_views/lib/viewset/__init__.py`,
  `src/crud_views/lib/view/base.py`, and checks: per-kind form maps and diagnostics.
- `src/crud_views/templates/crud_views/tags/button/form.html`: new default leaf; action leaf provides
  existing accessible label-mode and icon conventions.
- `src/crud_views_workflow/lib/forms.py`: workflow submit-icon default.
- `tests/test1/test_crispy_buttons.py`, button-data/leaf tests, and `tests/test1/golden/`: default markup,
  override compatibility, isolation, escaping, and golden baselines.
- `src/crud_views/static/crud_views/js/viewset.js`, `modal.js`, and `list.filter.js`: cancel, submitter,
  and reset contracts to verify with real button elements.

</code_context>

<specifics>
## Specific Ideas

- Keep `class AuthorFilterFormHelper(ListViewFilterFormHelper): layout = Layout(...)` working unchanged.
- An overridden `get_form_actions()` can replace or omit Apply/Reset without rewriting the helper.
- `class MySubmit(Submit): template = "my_app/buttons/submit.html"` works; explicit `template=` wins.
- A form owned by an ordinary Django view on a crud_views page uses project settings/defaults, not the
  enclosing page's ViewSet/view map. An embedded form with its own CrudView uses that owner.

</specifics>

<deferred>
## Deferred Ideas

None added. Automatic migration of legacy helper inputs, legacy-placement warnings, rejecting template
overrides, retaining crispy's `input` object, dropping template-pack substitution, and warning on differing
owners were rejected, not deferred. The stability freeze and downstream-theme implementation remain outside
this phase. Required design/spec and compatibility investigation remain Phase 6 work.

</deferred>

---

*Phase: 06-form-button-leaf*
*Context gathered: 2026-10-27*
