# Concept review follow-ups: phased implementation plan

> **For agentic workers:** this is a phase plan, not a task-by-task plan. Phases 1A, 1C, 3A, 3B and 4 are small enough
> to implement from this document with superpowers:executing-plans. Phase 1B (#262) and Phase 2 (#257) each need
> their own spec through superpowers:brainstorming first; this document fixes their scope, inputs and acceptance.

**Goal:** Land the five ranked findings of `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` before
1.0.0, in an order that lets each change be reviewed on its own and never forces a public name to change twice.

**Source:** the review note (Synthesis, "Five findings that matter most"), issues #257, #262, #89.

## The question: separate phases, one change, or groups?

**Groups.** Neither extreme works:

- **All at once** would put a design decision (the `form:*` key grammar), a new setting (label-mode defaults), a
  breaking markup change (`<input>` → `<button>`, #257), two Bootstrap leak fixes and a documentation policy into one
  review. The #257 diff alone touches crispy integration, the leaf contract, the class-table checks, the icon tables,
  the example project, the migration guide and the Tabler theme. Nobody can review the decision inside that.
- **Five separate phases in rank order** fails on dependencies. Finding 4 (#257) needs finding 1 (the defaults map,
  or #257 adds a fourth hard-coded default) and finding 2 (the key grammar, or #257 ships keys the W362 check
  rejects). Finding 3 (stability policy) must come **last**, after every name it would freeze has settled. Finding 5
  depends on nothing.

The dependency graph:

```
1A defaults map ──┬──► 1B filter toggle label mode (#262)
                  │
1C form:* grammar ┴──► 2  form buttons through a leaf (#257) ──► 4 stability policy
                                                                   ▲
3A alert dismiss adapter ──────────────────────────────────────────┤
3B table pagination arrows ────────────────────────────────────────┘
```

So: **four phases**. Phase 1 is the foundation (three small PRs, 1A before 1B, 1C independent). Phase 2 is the one
large change and consumes Phase 1. Phase 3 is two small, independent PRs that can run in parallel with anything.
Phase 4 is documentation and closes the release.

| Phase | Finding | Size | Breaking | Needs a spec | Depends on |
|---|---|---|---|---|---|
| 1A | 1: one label-mode default per location | S | no (defaults unchanged) | no | — |
| 1B | #262: filter toggle honours the label mode | M | no (default stays `icon`) | yes | 1A |
| 1C | 2: `form:*` second-segment decision | S | no | decision only | — |
| 2 | 4: form buttons through a leaf (#257) | L | yes (`<input>` → `<button>`) | yes | 1A, 1C |
| 3A | 5: alert dismiss through an adapter | S | DOM attribute change | no | — |
| 3B | 5: table pagination arrows from the registry | S | DOM change | no | — |
| 4 | 3: theme surface in `stability.md` | S | no | no | 1A, 1C, 2, 3A |

Everything lands before 1.0.0. If the release has to ship earlier, Phase 3 is the one to drop (both fixes are
additive DOM changes with a one-line migration note each), and Phase 4 then documents the surface as it is.

## Global constraints

- Without new configuration every template renders what it renders today: the goldens under `tests/test1/golden/`
  stay byte-identical in Phases 1A, 1C, 4 and must change only where a phase says so (1B: none; 2: the form
  buttons; 3A: the alert close button; 3B: the table pagination).
- One PR per phase letter, one branch each (`feat/label-mode-defaults`, `feat/filter-toggle-label-mode`,
  `feat/form-key-grammar`, `feat/form-button-leaf`, `feat/alert-dismiss-adapter`, `feat/table-pagination-icons`,
  `docs/stability-theme-surface`). `pytest tests -n auto`, `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs
  run`, `mkdocs build --strict`, `ruff check`, `ruff format --check` green before each push.
- Every phase with a public-surface change adds its CHANGELOG entry; a `### Breaking` entry also updates
  `docs/migrating-1.0.md` (CLAUDE.md rule).
- No downstream project names in any file. Line length 120, double quotes.
- The Tabler follow-up of each phase is written down in the phase's acceptance note (as #250's was), not done in
  this repository.

---

## Phase 1A: one label-mode default per location (finding 1)

**Problem.** Three hard-coded defaults: `button_data.py:83` (`"both" if card else "icon"`), the `"icon"` fallback at
the end of `cv_get_action_label_mode` (`base.py:311`, `:318`), and `cv_card_actions_label_mode = "both"` on the card
view. The filter toggle hard-codes a fourth (`context_action_filter.html`), #257 proposes a fifth.

**Design.**

- New setting `CRUD_VIEWS_LABEL_MODE_DEFAULTS: dict[str, str]`, merged **per key** over the package defaults
  `{"context": "icon", "list": "icon", "card": "both"}` (per-key merge like the class table, not whole-dict
  replacement like the per-key maps; the docs must say which is which). Phase 2 adds `"form": "label"`.
- One accessor, `crud_views.lib.view.label_mode.default_label_mode(location: str) -> str`, read by:
  - `cv_button_data()` in place of the literal (`button_data.py:83`),
  - `cv_get_action_label_mode()` in place of the two `"icon"` fallbacks,
  - `CardListView.cv_card_actions_label_mode`, whose default becomes `None` meaning "the map" (resolution:
    `CardAction.label_mode` → `no_label` → view attribute → map),
  - `cv_icon_mode_checks()` (W292) follows automatically through `cv_get_action_label_mode()`.
- Not a per-ViewSet or per-view knob: those exist already (the maps, the button field, the target-view string). This
  is the project-wide floor under all of them.
- Check `crud_views.E108`: unknown location key or invalid mode in the setting.

**Files.** Modify `src/crud_views/lib/settings.py`, `lib/view/label_mode.py`, `lib/view/button_data.py`,
`lib/view/base.py`, `lib/views/card.py`, `docs/reference/settings.md`, `docs/reference/action_menus.md` (the order,
the Mermaid diagram's `MICON` node becomes "defaults map"), `docs/reference/card-list-view.md`, `CHANGELOG.md`
(Added). Tests: `tests/test1/test_label_mode.py`, `test_button_data.py` (`test_card_label_mode_defaults_to_both`
gains a settings variant), `test_card_label_modes.py`, `test_context_action_label_mode.py`, `test_check_messages.py`.

**Acceptance.**

- [ ] `grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py` returns nothing.
- [ ] `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"context": "both"}` turns every unmapped toolbar button into icon+text on
  every page; rows and cards unchanged. W292 stops firing for those keys.
- [ ] `{"card": "label"}` restores the 0.29 card look without touching a view (the migration guide's
  `cv_card_actions_label_mode = "label"` recipe gets this as the one-line alternative).
- [ ] An invalid value fails E108; goldens unchanged; `cv_card_actions_label_mode = "both"` set explicitly still wins.

## Phase 1B: the filter toggle honours the label mode (#262)

**Scope.** As the issue describes: `FilterContextButton` resolves its mode through `cv_get_action_label_mode("context",
"filter")` (which after 1A falls back to the defaults map), `tags/context_action_filter.html` branches on
`cv_label_mode` the way `tags/button/action.html` does, `list.filter.js` tolerates a toggle with no icon spans and
no open/close data attributes. Needs a spec because of the three-way template branch combined with the two icon
placements (element and host) and the host-swap in JS.

**Depends on 1A** so the toggle has no literal left to remove.

**Acceptance.** `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` renders icon + "Filter" with no `title`;
`"label"` renders text only and the JS toggle still flips `aria-expanded` and persists; default output is
byte-identical to today (`toolbar_publisher_list.html` golden). Vitest: `list.filter.test.js` gains the label-only
case.

## Phase 1C: the `form:*` second segment (finding 2)

**Problem.** `location:slot[:mode]` has a variant in the second segment for `context` / `list` / `card`, a *kind*
for `form` (`form:submit`, `form:cancel`, `form:delete`, `form:filter-submit`, `form:filter-reset`), a *part* for the
rest. Only variant keys take a mode (`_action_key_parts`, `button_classes.py:207-218`;
`test_button_classes_checks.py:79` pins `form:submit:icon` as invalid). #257 needs mode keys for form buttons.

**Decision to make (maintainer).** Two options, written up in `docs/reference/buttons.md#the-class-table` as the
rule, whichever wins:

- **A. Keep kinds, extend the shape.** `form:<kind>:<mode>` is valid for the five kinds. Nothing renames.
- **B. Variants everywhere.** `form:primary`, `form:secondary`, `form:danger`; the kind goes to `cv-key` only.
  Renames five shipped keys that a theme already registers (`form:delete` is in the Tabler table) and the
  `slot=` keyword of `Submit` / `Button` / `Reset`.

**Recommendation: A.** The five form buttons are fixed in number and role; a project does not need a variant knob for
"the submit button", it needs "the submit button's classes". B buys consistency at the price of renaming public keys
weeks before freezing them, and the mode-key fallback rule works identically with kinds.

**Implementation (option A).**

- `FORM_KINDS = frozenset({"submit", "cancel", "delete", "filter-submit", "filter-reset"})` next to `LOCATIONS`.
- `_action_key_parts()` accepts `("form", kind, mode)` with `kind in FORM_KINDS`; `_is_action_mode_key()` unchanged.
- `test_w362_rejects_bad_mode_shape`: move `form:submit:icon` to the accept list; add `form:submitt:icon` and
  `form:container:icon` to the reject list.
- `buttons.md`: one paragraph stating the three meanings of the second segment and which two take a mode; fix the key
  count at `buttons.md:112` (64 → 70) and make `test_button_classes.py::test_default_table_is_complete` also assert
  the number quoted in the docs (read the line, parse the integer), so the two cannot drift again.
- No behaviour change: `get_button_class("form", "submit", mode)` already reads a mode key when present.

**Acceptance.** Checks accept `form:<kind>:<mode>` and reject anything else with a mode; docs state the rule; the count
is right and pinned.

---

## Phase 2: form buttons through a crud_views leaf (#257, finding 4)

**Scope.** Issue #257 with the six changes from the review note. Needs its own spec; this section fixes what the spec
must contain.

**Inputs from Phase 1.** The `form` default comes from `CRUD_VIEWS_LABEL_MODE_DEFAULTS["form"] = "label"` (1A), the
class keys are `form:<kind>:<mode>` (1C). The issue's own `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` dict (per button key),
ViewSet `form_actions_label_mode` and view `cv_form_actions_label_mode` stay as the per-key override layer, shaped and
resolved like the context / list maps (`cv_first_inline_keys`).

**Design points the spec must settle.**

1. **`"form"` joins `LOCATIONS`** (`button_data.py:12`) and `cv_button_data(ctx, "form")` builds the contract. New
   contract keys: `cv_type` (`submit` | `button` | `reset`), `cv_name`, `cv_value`, `cv_id`, `cv_cancel_url`
   (present only for the cancel button). `cv_href`, `cv_submit_target`, `cv_modal`, `cv_active` are absent for
   `form`. `LEAF_KEYS` grows accordingly; `cv_key` is the kind (`submit`, `cancel`, …).
2. **A new leaf `crud_views/tags/button/form.html`**, not `action.html`: a submit needs `type="submit" name value`,
   a cancel `type="button" data-cv-cancel-url`; forcing both into the action leaf adds branches to every theme's
   override. The leaf renders the same three label-mode bodies as `action.html` (icon + hidden label with `title` and
   `data-cv-tooltip="form"`, icon + text, text) and takes its classes from
   `{% cv_button_class "form" cv_key cv_label_mode %}`.
3. **The crispy objects become thin adapters.** `Submit`, `Button`, `Reset` in `crud_views/lib/crispy/buttons.py`
   keep their constructor signature (`name`, `value`, `slot=`, `css_class=`, `css_id=`, `**kwargs` → attrs) and
   render through the leaf: override `render()` to call `cv_button_data()` and `render_to_string()` of the leaf,
   bypassing crispy's `baseinput.html` and `button.html`. `css_class` is appended to the table classes as today
   (`test_project_css_class_still_appended`). Extra kwargs render as attributes (`data_cv_cancel_url` → the
   `cv_cancel_url` key, everything else as `flat_attrs`).
4. **Escaping.** The leaf autoescapes `cv_value` / `cv_label` and `cv_title`; crispy's `button.html` with
   `{{ button.content|safe }}` is never used. A test posts a form whose `submit_label` contains `<b>` and asserts the
   escaped text.
5. **Icons.** New names `save` and `cancel`; **`filter-reset`**, not `reset` (the cancel button is also
   `name="reset"`, `form.py:76`). `submit` → `save`, `delete` → `delete`, `cancel` → `cancel`, `filter-submit` →
   `filter`, `filter-reset` → `filter-reset`. `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` both grow (the sync test enforces
   it). `CrispyFormMixin.submit_icon = "save"`, `WorkflowForm.submit_icon = "workflow"`,
   `CrispyDeleteForm.delete_icon = "delete"`, `ListViewFilterFormHelper` uses `filter` / `filter-reset`.
6. **Checks.** E210 covers `cv_form_actions_label_mode` values, E211 the map shape, W291 unknown keys (the five kinds
   are the key set), W292 extended to form buttons whose resolved mode is `icon` while their icon is empty.
7. **Breaking.** `<input type="submit|button|reset">` becomes `<button type="…">`. CHANGELOG `### Breaking`,
   `docs/migrating-1.0.md` section "Form buttons" (CSS and test selectors on `input[type=submit]`; `name` and `value`
   unchanged so POST data is unchanged; `viewset.js` cancel handler and `modal.js` `event.submitter` already work
   with `<button>`, `viewset.js:37-44`, `modal.js:75-83`).
8. **Example project** turns on `both` for submit, delete and cancel through `CRUD_VIEWS_LABEL_MODE_DEFAULTS`.

**Files.** `lib/view/button_data.py`, `lib/view/label_mode.py`, `lib/view/base.py` (map resolution),
`lib/viewset/__init__.py` (`form_actions_label_mode`), `lib/settings.py`, `lib/crispy/buttons.py`,
`lib/crispy/form.py`, `lib/views/list.py` (filter helper), `lib/icons.py`, `lib/button_classes.py` (no new keys;
mode keys already valid after 1C), `templates/crud_views/tags/button/form.html` (new),
`crud_views_workflow/lib/forms.py`, `checks.py` / `lib/view/buttons.py` (W292), docs `buttons.md#forms`,
`icons.md` (three names), `action_menus.md#label-mode` (a fourth column `Form`), `settings.md`, `theme.md` (one more
leaf), `migrating-1.0.md`, `CHANGELOG.md`, `examples/bootstrap5/project/settings.py`. Tests: rewrite
`test_crispy_buttons.py` (its `tag()` helper matches `<input\b` only), extend `test_button_data.py`,
`test_button_leaves.py`, `test_label_mode.py`, `test_icons_registry.py`, goldens that contain a form.

**Acceptance (from #257, amended).**

- [ ] With nothing configured: `<button>` with the same text, classes, `name`, `value`, `id`; POST data unchanged
  (`test_delete`, `test_cancel_origin` green without edits beyond the `<input>` selector).
- [ ] `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`: save, delete, cancel and both filter buttons show icon and
  text; `{"form": "icon"}`: text is the hidden label, `title` and `data-cv-tooltip="form"` present.
- [ ] The workflow submit shows the `workflow` icon; a per-form `submit_icon` wins.
- [ ] Setting → ViewSet → view per-key maps resolve; `form:submit:icon` style keys apply.
- [ ] An icon-only form button without an icon raises under strict mode, logs and renders the label otherwise; W292
  reports the static cases.
- [ ] A label containing markup renders escaped.
- [ ] Tabler follow-up written into the acceptance note: map `save` → `tabler:device-floppy`, `cancel` → `tabler:x`,
  `filter-reset` → `tabler:filter-off` (paths to add to `ICONS`); `test_delete_form_is_the_stock_crispy_delete_form`
  and the `<input type="submit"` assertion change; the theme overrides nothing new.

---

## Phase 3A: alert dismiss through an adapter (finding 5)

**Problem.** `tags/alert.html` closes with `<button class="btn-close" data-bs-dismiss="alert">`: the only stock
template left that drives Bootstrap through its data API instead of `cv.adapters`. A non-Bootstrap theme copies the
frame for one attribute; the modal had the same leak until `data-cv-modal-dismiss`.

**Design.** Mirror the modal: the frame renders `data-cv-alert-dismiss`; a delegated click handler (in
`viewset.js`, next to the cancel handler) calls `cv.adapters.alert.close(alertEl)` where `alertEl` is
`closest('[role="alert"]')`; `adapters.js` gains `alert: {close(el) { component(ns, "Alert")?.getOrCreateInstance(el).close(); }}`
inside `bootstrapAdapters()`. Without an `Alert` component the handler removes the element (`el.remove()`), so a
non-Bootstrap page still closes the alert. A theme override that keeps `data-bs-dismiss="alert"` keeps working under
Bootstrap's data API, as the modal docs already say for `data-bs-dismiss`.

**Files.** `templates/crud_views/tags/alert.html`, `static/crud_views/js/adapters.js`, `static/crud_views/js/viewset.js`,
`docs/reference/javascript.md` (adapter table row, `cv.bootstrapAdapters` sentence "all four"), `docs/reference/messages.md`
(the close button paragraph), `docs/reference/theme.md#templates-that-follow-bootstraps-dom` (remove the alert from the
leak list, or add it if 3A is dropped), `CHANGELOG.md` (Breaking: DOM attribute), `docs/migrating-1.0.md` (one bullet).
Tests: `tests/test1/test_alerts.py`, `test_messages.py` (attribute), vitest `adapters.test.js` and `viewset.test.js`
(close with and without an `Alert` component).

**Acceptance.** `grep -rn 'data-bs-' src/crud_views/templates` lists only the dropdown templates named in `theme.md`
(`actions_menu*.html`, `language_selector.html`). The example project's flash messages still close.

## Phase 3B: table pagination arrows from the registry (finding 5)

**Problem.** `templates/crud_views/table/bootstrap5.html` still renders `&laquo;` / `&raquo;` and `previous` / `next`
text while `snippets/pagination.html` moved to `page-previous` / `page-next` with accessible markup (#241). Two
paginations, two conventions.

**Design.** Take the #241 markup over: `{% cv_icon "page-previous" %}` plus a `visually-hidden` translated label (the
`<location>:hidden-label` key is `context`-scoped; use the `card:hidden-label` key or add `table:hidden-label`; the
latter is one more key, the former a misnomer; recommendation: `table:hidden-label`, default `visually-hidden`),
`aria-current="page"` on the active item, a disabled end as `<a class="page-link" aria-disabled="true">`, the
`<nav>` label translated ("Table navigation" is untranslated today).

**Files.** The template, `lib/button_classes.py` (one key, if chosen), `docs/reference/buttons.md` (key table and
count; the count test from 1C catches the number), `docs/reference/list_view.md` (one sentence), `CHANGELOG.md`
(Breaking: DOM, like #241's entry), `docs/migrating-1.0.md` (extend the #241 bullet). Tests: the list goldens that
include a paginated table, `test_crud.py` or a new `test_table_pagination.py`, the `.po` files for the new msgid.

**Acceptance.** Both paginations render the same arrow icons and the same accessible structure; Tabler's own table
override already does this (`crud_views_tabler/templates/crud_views/table/bootstrap5.html`), so the theme is
unaffected.

---

## Phase 4: the theme surface in the stability policy (finding 3)

**Problem.** `docs/development/stability.md` lists `crud_views.lib.button_classes` (`stability.md:29`) and nothing else
a theme imports. The Tabler theme uses `register_icon_library`, `register_icons`, `render_icon`, the 34 icon names,
`alert_data` indirectly through `tags/alert.html`'s context, the leaf contract, and `cv.adapters`.

**Design.** Add to "Public API", after the names of Phases 1 to 3 are final:

- **Icons** `crud_views.lib.icons`: `register_icon_library`, `register_icons`, `render_icon`, `get_icons`,
  `get_libraries`, `BOOTSTRAP_ICONS`, and the semantic names in `DEFAULT_ICONS` (adding a name is minor; renaming or
  removing one is major).
- **Buttons**: the class-table keys in `DEFAULT_BUTTON_CLASSES` (same rule), `Variant`, `LabelMode`,
  `cv_button_data`, `LEAF_KEYS`, `LOCATIONS`, the leaf templates `tags/button/{action,menu_item,menu_item_label,
  container,form}.html` and their documented context, `get_container_layout` / `ContainerLayout`.
- **Alerts** `crud_views.lib.messages`: `alert_data`, `message_alerts`, `LEVELS`; the context of `tags/alert.html`.
- **JavaScript**: `cv.adapters.{modal,tooltip,collapse,alert}` and their method names, `cv.bootstrapAdapters`,
  `cv.initTooltips`, the events `cv:modal:loaded`, `cv:modal:unload`, `cv:formset:row-added`, the DOM contract
  (`#cv-modal`, `#cv-modal-dialog`, `#cv-modal-content`, `#cv-filter-toggle`, `#filter-collapse`, `data-cv-*`
  attributes, `cv-key`, `cv-<location>-container`).
- **Theme hooks**: `register_button_classes`, `register_icon_library`, `register_icons`, `register_assets`, the
  template names a theme is told to override in `theme.md`.

Add a test, `tests/test1/test_stability_doc.py`, that reads `stability.md` and asserts each of those dotted names and
template paths appears, so a new public name cannot ship undocumented. Cross-reference from `theme.md` ("what a theme
may rely on"). Closes the theme part of #89.

**Acceptance.** The test is green; `mkdocs build --strict` passes; every name the Tabler theme imports from
`crud_views.lib.*` appears in `stability.md` (checked by grepping the theme's `apps.py`, `checks.py`, `tests.py`:
the two underscore names it imports, `_get_renderers` and `_icon_str`, are the ones that should stay private, and
the note recommends a public `is_library_renderer(prefix, callable)` helper instead; optional).

---

## Out of scope here, tracked for 1.0.0 anyway

From the review's "settle before 1.0.0" list but not among the five: removing `CardAction.no_label` and the
`cv_no_label` guard (#254 adjacent); the one-letter pair `cv_context_actions_label_mode` / `cv_context_action_label_mode`
(rename or keep, decide with 1A since the docs page is open anyway); an E36x check for `container-tag`; #259 host
placement for headings; #211 stale-override detection. None of them blocks a phase above.

## Order of work, concretely

1. 1A and 1C in parallel (different files, no conflicts); merge both.
2. 1B (needs 1A), 3A and 3B in parallel; 3A and 3B touch no file 1B touches.
3. Brainstorm the Phase 2 spec once 1A and 1C are on `main`; implement; write the Tabler follow-up into its
   acceptance note.
4. Phase 4 after Phase 2 merges; it is the last change before the 1.0.0 version bump.
