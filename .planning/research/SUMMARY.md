# Project Research Summary

**Project:** django-crud-views — Concept Review Follow-ups (0.30.0 → 1.0.0 theme surface)
**Domain:** Theme surface of a reusable Django UI package (label modes, button class table, crispy form-button leaf,
JS adapters, table pagination, stability policy)
**Researched:** 2026-10-25
**Confidence:** HIGH

## Executive Summary

This milestone is not a product build. It is a pre-1.0 hardening pass on the **theme surface** of a reusable Django
package. The aim is that every public theme name (label-mode defaults, class-table keys, icon names, leaf templates,
`cv.adapters`, DOM attributes) settles once before 1.0.0 freezes it. Packages that let themes restyle **without copying
templates** cost far less to upgrade than packages whose templates are the de-facto API. Here that means a class table,
an icon registry, small leaf templates fed by a flat Python contract, and a JS adapter seam. django-crud-views already
works this way for context, list and card actions. The milestone extends the model to the last holdouts:

- form buttons, which still render crispy `<input>`s
- the filter toggle, which hard-codes `icon`
- the alert close button, the last `data-bs-*` leak outside the dropdowns
- table pagination, which still uses tables2's `&laquo;` markup

Then it writes the freeze down and guards it with a test.

**Recommended approach:**
- **No new dependencies and no floor bumps.** Every API needed exists at the current floors (crispy-forms ≥2.0,
  crispy-bootstrap5 ≥2023.10, tables2 ≥2.5.3, Bootstrap ≥5.0.2).
- **Order the work by dependency:**
  - 1A and 1C run first, in parallel.
  - 1B, 3A and 3B follow, in parallel.
  - Phase 2 (form leaf) is the last code phase.
  - Phase 4 (stability) merges only after every name is final.

**Phase 2 carries most of the risk, and the plan as written has real gaps.** All four researchers found them
independently:

1. Overriding `render()` on crispy `Submit`/`Reset` **does not reach the filter form's buttons**. They are added with
   `helper.add_input()`, and every template pack renders those through `inputs.html` → `baseinput.html` without
   calling `render()`. They must move into a `FormActions` layout.
2. crispy's `BaseInput.render()` template-evaluates the button value. Copying that line is a **template-injection
   hole** and also defeats escaping. The new `render()` must treat the value as plain text.
3. The leaf needs `form:hidden-label` and `form:icon-host` class keys. The plan says "no new keys", but without them
   icon-mode labels render visibly and host-placed icon libraries render no icon at all.
4. Adding `"form"` to `LOCATIONS` without first splitting that set lets W362 silently accept `form:<variant>:<mode>`.
   1C must introduce `VARIANT_LOCATIONS` / `FORM_KINDS`.

The other main risk sits in Phase 4: freezing names too broadly (wildcards, helper signatures, default values) or too
early (the `cv_context_action(s)_label_mode` pair and `no_label` are still undecided).

## Key Findings

### Recommended Stack

Nothing gets added. The research question was which behaviours of the existing dependencies the phases rely on.
Every claim was checked against the installed sources in `.venv` and against upstream tags. Details: STACK.md.

**Core technologies (locked versions, no bumps):**
- **django-crispy-forms 2.6** (Django 4.2 cell: 2.5): `BaseInput.__init__` / `render()` are byte-identical from 2.0
  to 2.7, so a subclass with its own `render()` works across the supported range.
  - Pop `data_cv_*` kwargs **before** `super().__init__()`, because crispy flattens kwargs into `flat_attrs`, mapping
    `_` to `-`.
  - Keep `css_class` separate from `field_classes`, because the mode-dependent class is only known at render time.
- **crispy-bootstrap5 2026.3**: `inputs.html` hard-codes the `baseinput.html` include. Upstream issue #775 about this
  has been open since 2018. Never override pack templates from crud_views.
- **django-tables2 3.0.0**: it renders the table template with an **isolated context** (`{"table": table}`), so only
  context-free tags (`cv_icon`, `cv_button_class`, `cv_querystring`) work there.
  - Keep the block names `pagination`, `pagination.previous`, `pagination.range` and `pagination.next`.
  - Keep the full template copy rather than `{% extends %}`, because the upstream template uses `querystring_replace`,
    which only exists in 3.x.
- **Pydantic 2.13**: settings are snapshotted at import. Do not strictly type new settings fields, because a
  `ValidationError` at import would crash startup before E108 could report anything.
- **Bootstrap 5.3 (host-loaded)**: `Alert.getOrCreateInstance(el).close()` exists from 5.0.2. Bootstrap 6 alpha is
  ESM-only and has no `window.bootstrap`, which confirms that the `el.remove()` fallback is correct. Do **not** add
  Bootstrap 6 support in this milestone.
- **Django 4.2 is past end of support (April 2026)** and pins the 4.2 cell to older crispy versions. This does not
  block anything here, but `stability.md` must name the supported range.

### Expected Features

Details: FEATURES.md.

**Must have (table stakes):**
- **1A**: `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, merged per key, with the E108 check. Output with no configuration stays
  byte-identical.
- **1B**: the filter toggle honours `icon` / `both` / `label`.
  - The label text stays constant (APG toggle rule).
  - `title` and tooltip appear only in `icon` mode.
  - The `"Filter"` literal becomes `gettext_lazy`.
- **1C**: one documented `form:<kind>:<mode>` grammar (Option A, no renames), enforced by W362. A test pins the key
  count quoted in the docs.
- **2**: real `<button type="…">` elements.
  - Visually hidden text gives the accessible name in icon mode.
  - Label, value and title are autoescaped.
  - name, id, value and POST data are byte-compatible.
  - `Hidden` stays an `<input>`.
  - The filter Apply/Reset buttons are converted too.
  - The default form mode is `label`, taken from the 1A map.
  - A Breaking entry plus a section in `migrating-1.0.md`.
- **3A**: alerts close without Bootstrap JS (`data-cv-alert-dismiss` → `cv.adapters.alert.close`).
- **3B**: table pagination uses the same accessible structure as the card pagination from #241:
  - registry icons and hidden text
  - `aria-current`
  - non-focusable disabled ends
  - a translated `<nav>` label
- **4**: `stability.md` lists every name a theme imports, with a "rename/remove is major, adding is minor" rule.
  A **bidirectional** guard test backs it.

**Should have (differentiators):**
- Form buttons share the action-button label-mode contract (setting → ViewSet → view maps, `cv-key`, mode class keys).
  A theme can restyle them without overriding a template, which no crispy pack offers.
- Semantic icons `save`, `cancel` and `filter-reset`. Do not call the last one `reset`: it would collide with the
  cancel button's `name="reset"`.
- Strict-mode safety net (W292, strict raise) for icon-only buttons without an icon, extended to forms and the filter
  toggle.
- Host-placement parity via `form:icon-host`.
- One `pagination:hidden-label` (or `table:hidden-label`) key, with the card snippet switched to a key as well.
- One-line migration recipes, e.g. `{"card": "label"}` restores the 0.29 cards.

**Defer / reject:**
- Defer: Option B variant keys for forms, first/last/page-size pagination, a public `is_library_renderer` (optional,
  but see Gaps), host placement for headings (#259), stale-override detection (#211).
- Reject:
  - per-ViewSet/view entries in the defaults map
  - themes setting label modes
  - whole-dict replacement for the defaults map
  - `StrictButton` or `HTML()` buttons
  - overriding crispy pack templates
  - icon-only as the default for forms
  - upstream focus management or auto-dismiss for alerts
  - wildcard or generated stability docs

### Architecture Approach

The theme surface is a five-layer pipeline: configuration → resolution → normalisation → presentation → client, with
startup checks and a stability policy on top. The 1A defaults map becomes the **single floor** under every
location's resolution chain. Python makes every decision in `cv_button_data` and passes a flat `LEAF_KEYS` dict, so
templates only render markup. JS reaches UI libraries **only** through `cv.adapters`. Details: ARCHITECTURE.md.

**Major components (and the phases that touch them):**
1. `lib/view/label_mode.py`: home of `LABEL_MODE_DEFAULTS` and `default_label_mode(location)`. It is a safe leaf
   module that `button_data.py`, `base.py` and `card.py` can import. (1A)
2. `lib/view/button_data.py`: the leaf contract (`LOCATIONS`, `LEAF_KEYS`, `cv_button_data`). Phase 2 adds a
   separate private `_form_button_data` branch so the action goldens stay unchanged. (1A, 2)
3. `lib/button_classes.py`: the class table, `get_button_class` and W362. 1C splits `LOCATIONS` into
   `VARIANT_LOCATIONS` and `FORM_KINDS`. (1C, 2, 3B)
4. `lib/crispy/{buttons,form}.py` and `lib/views/list.py`: thin crispy adapters plus the filter helper, which has to
   move off `add_input`. (2)
5. `templates/crud_views/tags/button/form.html`: the new leaf, next to `action.html`. (2)
6. `static/crud_views/js/adapters.js` and `viewset.js`: `cv.adapters.alert` with the fallback **inside** the adapter,
   plus a delegated `document` handler. (3A)
7. `templates/crud_views/table/bootstrap5.html`: the #241 markup inside the unchanged block names. (3B)
8. `docs/development/stability.md` and `tests/test1/test_stability_doc.py`. (4)

**Patterns to follow:**
- **Lazy, per-key merged settings, as in the class table.** Do not copy the label-mode maps, which are read at
  import.
- **One floor, many layers.** No location ever has a second hard-coded default. Extend the acceptance grep to
  `lib/crispy/` and `templates/crud_views/tags/`.
- **Isolated leaf rendering.** Use `render_to_string(leaf, fresh_dict)`, never `context.flatten()`.
- **Bootstrap knowledge lives only in `cv.bootstrapAdapters`.**

### Critical Pitfalls

Details: PITFALLS.md.

1. **The filter buttons bypass `render()` (Phase 2).** They are added with `add_input()` and rendered through the
   pack's `inputs.html`, in both bootstrap5 and the Tabler pack.
   - Prevention: move Submit/Reset into `FormActions` at the end of `build_default_layout(form)`. Keep `Hidden` in
     `add_input` and keep the ids `filter-button` and `filter-button-reset`.
   - Verify with a **list-page** golden and with a non-bootstrap5 template pack.
2. **Template-evaluated, SafeString button values (Phase 2).**
   - Prevention: never call `super().render()` or `Template(...)`. Pass `str(value)` at render time so autoescape
     applies.
   - Test `<b>`, `"><script>` and literal `{{ request.user }}` in both the `value` attribute and the body.
   - Record the removal of value templating as Breaking.
3. **Context leakage and instance mutation (Phase 2).** Page-level `cv_*` keys leak into the leaf, and state written
   to `self` in `render()` is shared across requests and languages when a helper is defined at class level.
   - Prevention: build the dict from the button only and resolve into locals.
   - Test with a polluted context, and render twice under two languages and two settings.
4. **name/id/value/type drift in `<input>` → `<button>` (Phase 2).**
   - Prevention: reproduce crispy's multi-word name slugify and its default `{type}-id-{slug}` id. Always emit
     `type`, and an explicit `value`.
   - Write an attribute-parity test parsed with `html.parser`. `test_delete` must post `{"delete": "Delete"}`
     unchanged.
5. **Settings read at import time (1A).** `override_settings` would silently have no effect.
   - Prevention: `default_label_mode()` reads `django.conf.settings` lazily and merges over an immutable package
     constant. At least one test uses `override_settings`.
   - Also: `cv_card_actions_label_mode` becomes `str | None`, and E210 accepts `None`.
6. **Premature or wildcard freeze (Phase 4).**
   - Prevention: no `*` globs. Use three tiers: Stable / Provisional / Internal. Freeze key **names**, not default
     values or helper signatures.
   - List check IDs and `CRUD_VIEWS_*` settings.
   - Settle the label-mode pair and `no_label` before Phase 4.
7. **Alert double close / adapter missing (3A).**
   - Prevention: the stock frame renders **only** `data-cv-alert-dismiss`. Locate the alert via a `[data-cv-alert]`
     frame attribute, with `role="alert"` as a fallback.
   - Guard the call as `cv.adapters?.alert?.close`. Use delegated handling so alerts injected into a modal work.

## Implications for Roadmap

Keep the plan's seven phases (1A, 1B, 1C, 2, 3A, 3B, 4) as seven roadmap phases, one branch/PR each, run in four
waves. The research confirms the plan's dependency graph. It moves some scope earlier: the location-set split goes
into 1C, the lazy read and the non-strict crash fix into 1A. It also adds explicit spec items to Phase 2.

### Phase 1A: Label-mode defaults (`CRUD_VIEWS_LABEL_MODE_DEFAULTS`, E108)
**Rationale:** This is the foundation. Without it, 1B and 2 would each add a literal default that later has to be
removed, which is a public behaviour change twice. It touches no files that 1C touches.
**Delivers:**
- `LABEL_MODE_DEFAULTS` and `default_label_mode()` in `label_mode.py`, read lazily.
- The literals at `button_data.py:83` and `base.py:312/317` replaced by the accessor (the plan's line numbers
  `:311/:318` are off by one).
- `card.py` gets `cv_card_actions_label_mode: str | None = None`, and E210 accepts `None`.
- `crud_views.E108`, validated against the map's own key set so that Phase 2 adding `"form"` is a one-line change.
- Non-strict mode stops crashing on a bad mode: it logs and falls back.
- A docs table with merge-vs-replace and read time for every knob.
- The Mermaid chain fix in `docs/reference/context_buttons.md:256`, not in `action_menus.md`.
- `migrating-1.0.md` recipes.

**Addresses:** T1, T2, T3, D8.
**Avoids:** Pitfalls 6, 7 and 8, and the E108 forward-compatibility problem.
**Also:** raise the undecided label-mode pair and `no_label` in this phase's discussion, because Phase 4 depends on
those decisions.

### Phase 1C: `form:*` key grammar + key-count pin (parallel with 1A)
**Rationale:** Phase 2's mode keys (`form:submit:icon`) must pass W362. Splitting `LOCATIONS` (seam S1) belongs here
because 1C already edits `_action_key_parts`.
**Delivers:**
- Option A, `form:<kind>:<mode>`.
- `FORM_KINDS` as a closed frozenset.
- An explicit `VARIANT_LOCATIONS = {"context", "list", "card"}`.
- Reject tests for `form:submitt:icon` and `form:container:icon`.
- `buttons.md` documents the three meanings of the second segment.
- The count test parses the number from `buttons.md`, which corrects 64 to 70.

**Addresses:** T6, T7, D7. **Avoids:** Anti-pattern 1 (adding `"form"` to an unsplit `LOCATIONS`), A4 (renames).

### Phase 1B: Filter toggle label mode (#262)
**Rationale:** Depends on the context floor from 1A. It is a small, user-visible bug.
**Delivers:**
- A three-way branch in `context_action_filter.html`. No Python resolution code is needed, because
  `cv_get_context()` already stamps `cv_label_mode`.
- `gettext_lazy("Filter")` plus a `.po` entry.
- A 12-case render matrix: 3 modes × 2 placements × 2 expanded states.
- Vitest cases for `label` (no icons; `aria-expanded` still flips) and for host-placed `both`.
- W292 may now cover the toggle.

`list.filter.js` most likely needs no change. The `toolbar_publisher_list.html` golden stays byte-identical.
**Addresses:** T4, T5.
**Avoids:** host icon-font classes restyling the label text; tooltips duplicating visible text.

### Phase 3A: Alert dismiss adapter (parallel, droppable)
**Rationale:** Independent of the other phases, but its DOM attribute is part of the frozen surface, so it should land
before 4 if at all possible.
**Delivers:**
- `data-cv-alert-dismiss` on the stock frame, replacing `data-bs-dismiss`.
- A `data-cv-alert` frame attribute.
- `cv.adapters.alert.close` with the `el.remove()` fallback inside `bootstrapAdapters`.
- A delegated `document` handler.
- A vitest matrix: with and without `Alert`, with the adapter deleted, with an alert injected after load, and with a
  theme that keeps `data-bs-dismiss`.
- Acceptance: `grep data-bs-` lists only the dropdown and language-selector templates.

Before the change, commit a golden of the current dismissible alert.
**Addresses:** T16, T17, D4. **Avoids:** Pitfall 9, anti-pattern 3.

### Phase 3B: Table pagination parity (parallel, droppable)
**Rationale:** Independent of the other phases. It adds one class key, so merge it after 1C and rebase on the count
line.
**Delivers:**
- `{% cv_icon "page-previous/next" %}` and the hidden-label key.
- `aria-current`.
- Disabled ends that are not focusable, with the `{% if %}` moved inside the existing blocks. Document this as a
  change to the block contract.
- The ellipsis rendered as `<span>`.
- A translated nav label, reusing the existing msgids.
- Unchanged block names.

Before the change, commit a golden of the current paginated table.
**Addresses:** T18, T19, D6. **Avoids:** breaking tables2 block overrides; two conventions for the hidden label.

### Phase 2: Form buttons through `tags/button/form.html` (#257)
**Rationale:** The last code phase. It consumes 1A (the `"form"` floor), 1C (mode keys and the location split) and
touches the most files. Start its spec only after 1A and 1C are on `main`.
**Delivers:**
- `"form"` in `LOCATIONS` and in the defaults map (`"form": "label"`).
- The `form.html` leaf and a separate `_form_button_data` builder.
- Thin `Submit`/`Button`/`Reset` subclasses with their own `render()`: no `super()`, no `Template()`, an isolated
  dict, and the view looked up from `form.cv_view`, then `helper.view`, then `context["view"]`, then the floor.
- Filter Submit/Reset moved into `FormActions`.
- New keys `form:hidden-label` and `form:icon-host` (70 → 72).
- Icons `save`, `cancel` and `filter-reset` in `DEFAULT_ICONS` and `BOOTSTRAP_ICONS`.
- `WorkflowForm.submit_icon = "workflow"`.
- A `form_actions_label_mode` setting, ViewSet field and view field.
- E210/E211/W291/W292 extended to forms. Note in the CHANGELOG that silencing W292 now also silences form warnings.
- A Breaking entry covering `<input>` → `<button>`, the wrapper-markup change, value templating removed, and the
  `template=` kwarg being ignored.
- The example project uses `both`.

Before the change, commit goldens of the current create, delete and filter form actions.

**Uses:** crispy `BaseInput` API facts and lxml/cssselect test helpers. Rewrite the `<input\b` regex helper.
**Avoids:** Pitfalls 1–5, the Django 6.0 `format_html()`-without-arguments trap (run the full nox matrix), and dead
mode keys. Add a test that `form:submit:icon` actually lands on an icon-mode submit.

### Phase 4: Theme-surface stability policy + guard test
**Rationale:** It freezes names, so it merges only after 1A–3B. If Phase 3 is dropped, document `tags/alert.html` as a
known Bootstrap-DOM template in `theme.md`.
**Delivers:**
- `stability.md` with Stable / Provisional / Internal tiers. It lists explicitly:
  - icon names, class-table key names, leaf templates and their context keys, `LOCATIONS` (accepted locations only)
  - `cv.adapters.{modal,tooltip,collapse,alert}` method names and `cv.bootstrapAdapters`
  - the DOM attributes and ids, including `#filter-button` and `#filter-button-reset`
  - the tables2 block names, check IDs, `CRUD_VIEWS_*` settings and dependency floors
- It states that default class strings, glyphs and Bootstrap's own `data-bs-*` names are **not** frozen.
- `test_stability_doc.py` checks both directions:
  - every documented dotted name resolves;
  - every code-derived public name (`DEFAULT_ICONS`, `DEFAULT_BUTTON_CLASSES`, `LEAF_KEYS`, `LOCATIONS`, leaf files
    on disk, JS adapter keys) is documented.

  It matches backtick-delimited tokens with a regex, not substrings.

**Avoids:** Pitfall 10 and anti-pattern 5.

### Phase Ordering Rationale

- **Wave 1:** 1A ∥ 1C. They touch disjoint files and each removes a precondition of Phase 2.
- **Wave 2:** 1B ∥ 3A ∥ 3B. 1B needs only 1A. 3A and 3B share no files with the others. 3B should rebase after 1C
  because of the count line.
- **Wave 3:** Phase 2. It consumes seams S1 (location split), S2 (mode keys) and S5 (floor), and the spec must settle
  S3, S7, S8, S9 and the `LEAF_KEYS` split first.
- **Wave 4:** Phase 4. The Core Value says no name changes twice, so freezing comes last.
- **Golden-test prerequisite for 2, 3A and 3B:** no current golden contains form buttons, a dismissible alert or
  table pagination. "Goldens stay byte-identical" therefore protects nothing for these phases until each one first
  commits a golden of today's markup. Check every PR's `git diff --stat tests/test1/golden` against the phase's
  allowed list, and regenerate per node id, never per module.
- **Shared docs** (`CHANGELOG.md`, `migrating-1.0.md`, `theme.md`): rebase before merge and run
  `mkdocs build --strict`.

### Research Flags

Phases that need a spec or deeper research during planning:
- **Phase 2:** the highest risk. It needs its own spec before implementation (the plan already says so). The spec must
  decide:
  - how filter buttons render (the `FormActions` move, and a user `formhelper_class` that still calls `add_input`);
  - the view lookup;
  - dropping value templating;
  - one `LEAF_KEYS` set or a separate `FORM_LEAF_KEYS`;
  - `form:icon-host` (recommended: yes);
  - whether an explicit `template=` kwarg is honoured or rejected;
  - the crispy floor: add a lowest-direct nox session or accept the risk.

  Also verify the Django 6.0 `format_html` removal and jsdom `SubmitEvent.submitter` support.
- **Phase 1B:** needs a short spec (the plan says so) for what "target view default" (#269) means for a button with no
  target view, and whether `both` swaps only the icon.
- **Phase 4:** needs a maintainer decision on the tiers, on `is_library_renderer`, and on whether the reference theme's
  private imports are acceptable at 1.0.

Phases with standard patterns (skip research-phase):
- **Phase 1A:** copy the class table's lazy per-key-merge pattern. All seams are mapped.
- **Phase 1C:** a checks-and-docs change only, with no runtime change.
- **Phase 3A:** Bootstrap's Alert API and the existing adapter seam are fully verified.
- **Phase 3B:** a template-only change with known block contracts. Only the naming of the hidden-label key is open.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against the installed `.venv` sources, upstream tags, changelogs and the PyPI/npm registries. No training-data-only claims. |
| Features | MEDIUM-HIGH | Codebase and third-party sources HIGH. Bootstrap and WAI-ARIA docs were fetched (official, treated as MEDIUM). Comparable-package framing (Wagtail, unfold) is from training data and used only for context. |
| Architecture | HIGH | Every reference was checked at commit `9e6b40e`. It corrects the plan in several places: line numbers, the Mermaid location, "no new keys", "goldens contain forms". |
| Pitfalls | HIGH | Read from the crispy, tables2 and pack sources and from the downstream Tabler theme and pack. The Django 6.0 `format_html` and jsdom `submitter` claims are MEDIUM. |

**Overall confidence:** HIGH

### Gaps to Address

- **Read time of the 1A setting:** STACK.md suggests a Pydantic `Any` field with monkeypatch tests. ARCHITECTURE.md
  and PITFALLS.md argue for a lazy `django.conf.settings` read so that `override_settings` works. **Resolve in favour
  of the lazy read.** Validate in `check_messages` (E108) and merge over an immutable constant.
- **E108 severity for unknown location keys:** Error (FEATURES) or Warning for forward compatibility (PITFALLS).
  Recommendation: Error for a non-dict value or an invalid mode, and decide unknown keys in the 1A discussion. Either
  way, derive the valid keys from the map, not from a literal.
- **Name of the hidden-label key:** one `pagination:hidden-label` key shared by card and table (ARCHITECTURE,
  recommended) or `table:hidden-label` (plan). This is the maintainer's call in 3B, before Phase 4 freezes it.
- **Literal classes in the alert frame** (`btn-close`, `alert-dismissible fade show`): add `alert:*` class keys in 3A,
  or document in `theme.md` that a non-Bootstrap theme overrides the frame. Decide before Phase 4.
- **`LEAF_KEYS`: one set or two:** decide in the Phase 2 spec, because Phase 4 freezes the name.
- **Undecided names that block Phase 4:** the label-mode pair rename and the `no_label` removal are out of scope, but
  each must be either done or marked "provisional/deprecated" in `stability.md`. Record the decision in PROJECT.md Key
  Decisions.
- **Private imports in the reference theme** (`_get_renderers`, `_icon_str`): add a public `is_library_renderer`
  before 1.0, or explicitly accept the dependency. The plan treats it as optional; the research leans towards adding
  it.
- **Untested crispy floor (≥2.0):** the API is verified identical, but no nox session runs at the floor. Add a
  lowest-direct session or raise the floor knowingly.
- **Django 4.2 is past end of support:** outside this milestone, but `stability.md` must state the supported matrix.

## Sources

### Primary (HIGH confidence)
- Repository at commit `9e6b40e`:
  - `lib/view/{button_data,label_mode,base,buttons}.py`, `lib/views/{card,list}.py`
  - `lib/{button_classes,icons,settings,messages}.py`, `lib/crispy/*`
  - templates, `static/crud_views/js/*`, tests and goldens, docs
- Installed third-party sources in `.venv`:
  - crispy-forms 2.6 `layout.py` / `helper.py` / `utils.py`
  - crispy-bootstrap5 2026.3 `inputs.html` / `baseinput.html` / `button.html` / `formactions.html`
  - django-tables2 3.0.0 `bootstrap5.html` and `RenderTableNode`
- Upstream sources at tags: crispy-forms 2.0, 2.5 and 2.7; crispy-bootstrap5 2023.10, 2025.6 and 2026.9.
- Changelogs (crispy-forms, crispy-bootstrap5, django-tables2) and crispy-forms issue #775.
- Registry metadata: PyPI JSON API and npm dist-tags (bootstrap 5.3.8, 6.0.0-alpha.1).
- Bootstrap 5.3 `js/src/alert.js`.
- Bootstrap blog post "Bootstrap 6 Alpha" (2026-10-08).
- Downstream reference consumer `crud_views_tabler` and the `crispy_tabler` pack: overridden templates, private
  imports, tests.

### Secondary (MEDIUM confidence)
- Bootstrap 5.3 Alerts and Pagination docs (webfetch, official).
- WAI-ARIA APG Button Pattern (toggle label must not change; accessible name sources).
- WCAG 2.5.3 Label in Name; `aria-current` / `aria-disabled` usage for pagination.
- Django 5.0 deprecation of `format_html()` without arguments, removed in 6.0 (verify in the Phase 2 spec).
- jsdom `SubmitEvent.submitter` support (verify in Phase 2).

### Tertiary (LOW confidence)
- Wagtail public-API and deprecation policy, the `w-sr-only` pattern, django-unfold/Alpine and django-components
  conventions (training data, framing only).
- WCAG 2.2.1 reasoning on timed alerts (training data, used only to reject auto-dismiss).

---
*Research completed: 2026-10-25*
*Ready for roadmap: yes*
