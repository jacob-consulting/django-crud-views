---
phase: 03-filter-toggle-label-mode
verified: 2026-10-26T16:21:30Z
status: human_needed
score: 22/22 must-haves verified
covered_files:
  - .planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md
  - .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md
  - .planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md
  - .planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md
  - CHANGELOG.md
  - docs/migrating-1.0.md
  - docs/reference/action_menus.md
  - docs/reference/buttons.md
  - docs/reference/context_buttons.md
  - docs/reference/icons.md
  - docs/reference/javascript.md
  - src/crud_views/lib/view/buttons.py
  - src/crud_views/locale/de/LC_MESSAGES/django.mo
  - src/crud_views/locale/de/LC_MESSAGES/django.po
  - src/crud_views/static/crud_views/js/list.filter.js
  - src/crud_views/templates/crud_views/tags/context_action_filter.html
  - tests/js/list.filter.test.js
  - tests/test1/golden/action_menus/toolbar_publisher_list.html
  - tests/test1/test_button_leaves.py
  - tests/test1/test_context_action_label_mode.py
  - tests/test1/test_filter_toggle_label_mode.py
  - tests/test1/test_i18n.py
  - tests/test1/test_label_mode_docs.py
covered_digest: "v3:sha256:2ad320408d19ab7e8448a48ab135142e37bed7ce6e82a82c2ab928a859526a77"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 11
  total: 11
  not_honored: []
requirements:
  FILT-01: satisfied
  FILT-02: satisfied
  FILT-03: satisfied
  FILT-04: satisfied
human_verification:
  - test: "Open docs/reference/context_buttons.md#the-filter-toggle and compare the two configuration examples, the three-mode table and the prose against decisions D-01..D-10 in 03-CONTEXT.md and the rendered behavior (run `pytest tests/test1/test_filter_toggle_label_mode.py -q`). Confirm the section links the canonical resolution order instead of restating it, and that the toggle is still described as never folded."
    expected: "One canonical resolution order (action_menus.md#context-label-mode-resolution); no second precedence list; examples use the real import `from crud_views.lib.view.buttons import FilterContextButton`; 'no target view, so no target-view default' stated; never-folded rule present."
    why_human: "Planner-deferred end-of-phase check (03-02-PLAN task 1). Prose-to-decision fidelity and 'reads as one canonical order' are editorial judgments grep cannot make; the doc tests pin anchors and phrases, not meaning."
  - test: "Read docs/reference/javascript.md#the-filter-toggle-contract and docs/reference/icons.md (filter paragraphs) side by side with the vitest fixtures in tests/js/list.filter.test.js (`modeFixture` LAYOUTS: label/element, both/element, both/host) and the Python placement matrix (`PLACEMENTS` in tests/test1/test_filter_toggle_label_mode.py: element, host, mixed)."
    expected: "The optional-icon prose matches the fixtures exactly: host form only when both open and close resolve to usable host classes; mixed or switched-off pairs render two element spans in icon/both; label mode has no spans, no host classes and no data-cv-filter-icon-* attributes; tooltip marker only in icon mode; labels are never icon hooks."
    why_human: "Planner-deferred end-of-phase check (03-02-PLAN task 2). No doc test pins javascript.md/icons.md prose (03-02-SUMMARY D3 human_judgment: true)."
  - test: "Read the CHANGELOG Unreleased Fixed bullet 'Filter toggle label mode' (#262) and both migration entry points in docs/migrating-1.0.md (the detailed 'The filter toggle' bullet near line 332 and the checklist bullet near line 404). Compare with observed behavior: `pytest tests/test1/test_filter_toggle_label_mode.py::test_filter_live_floor -q` (floor impact) and `git diff 3a51f81 -- tests/test1/golden/` (default goldens)."
    expected: "Fixed (not Breaking) matches: default output unchanged; the context floor impact on already-configured projects is named; both migration locations say copied templates must branch on the resolved cv_label_mode and that icons are optional; the downstream-theme follow-up in 03-02-SUMMARY stays generic and actionable. Also judge IN-02: the Fixed sentence currently reads as if `FilterContextButton(label_mode=\"label\")` selects `\"icon\"` — decide whether to split it."
    why_human: "Planner-deferred end-of-phase check (03-02-PLAN task 3). Release-note classification and migration-guide completeness are judgment calls (03-02-SUMMARY D4 human_judgment: true)."
  - test: "In the example project (or any list view with a filterset), set `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {\"filter\": \"both\"}`, load the list page, click the filter toggle twice; repeat with `\"label\"`, and once with the setting removed. Optionally switch the language to German."
    expected: "both: funnel icon + visible 'Filter' with a normal gap, no tooltip; the icon swaps to funnel-x when open and the text never changes. label: text-only button with no icon; the panel still opens/closes and the state survives a reload. Default: identical to before this phase (icon-only, title tooltip). German: 'Filter' (identical spelling), toolbar label 'Aktionen'. Note whether the label-only button gives any visual cue that it is a disclosure and whether it is currently open (03-UI-REVIEW warning 1)."
    why_human: "Visual appearance and real-browser interaction. 03-UI-REVIEW captured no screenshots (no dev server reachable) and its interaction findings were code-derived; all toggle behavior here was proven in jsdom and Django test client only."
---

# Phase 3: Filter toggle label mode Verification Report

**Phase Goal:** The list filter toggle follows the configured label mode like every other context button, and stays accessible in each mode.
**Verified:** 2026-10-26T16:21:30Z
**Status:** human_needed
**Re-verification:** No — initial verification

Stance: assumed the goal was missed until the code proved otherwise. SUMMARY claims were not used as evidence; every truth below rests on a file read or a named test run in this session.

## Goal Achievement

### Observable Truths

Roadmap success criteria (SC-1..SC-4) are the contract and are listed first; the 14 PLAN 03-01 truths and 4 PLAN 03-02 truths follow. Where a PLAN truth restates a SC it is still listed, with its more specific evidence.

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| SC-1 | `{"filter": "both"}` renders icon + "Filter" with no `title`; `"label"` renders text only; default icon output byte-identical (toolbar golden) | ✓ VERIFIED | `context_action_filter.html` lines 3, 7, 11, 13 branch on `cv_label_mode` (both: ` <span>{{ cv_action_label }}</span>` with no `title`/`data-cv-tooltip`; label: no icon-class lookup, no wrapper spans, no `data-cv-filter-icon-*`). Ran `test_filter_both_tracer`, `test_filter_raw_default_bytes[False/True]`, `test_action_menus_golden.py::test_toolbar_list_with_filter` → 4 passed; `test_filter_mode_placement_matrix` label cases → 24 passed. `git diff 3a51f81 -- tests/test1/golden/` empty; `tests/test1/golden/action_menus/toolbar_publisher_list.html` last touched 2026-10-22 (before this phase). |
| SC-2 | In `label` mode (no icon spans) a click still flips `aria-expanded` and persists the state (vitest label-only case) | ✓ VERIFIED | Behavior-dependent (state transition + persistence). Ran `npx vitest run tests/js/list.filter.test.js -t "label-mode toggle"` → 6 passed: two-click cases assert `aria-expanded` per click and `expectPost` with `{filter_expanded: <bool>}`, CSRF header and JSON content type; `list.filter.js` is unchanged (`git diff 3a51f81` empty) and its `querySelectorAll("[data-cv-filter-icon]")` loop tolerates zero icons. Server side: `test_filter_both_tracer` POSTs `{"filter_expanded": true}` then GETs and asserts `aria-expanded="true"`. |
| SC-3 | The toggle's visible text never changes between states; only `aria-expanded` and the icon change | ✓ VERIFIED | Behavior-dependent. Ran `-t "keeps the label"` → 12 passed (label, both/element, both/host × default/Unicode label × both initial states): asserts the same label node identity (`visibleLabel(f.toggle)).toBe(f.label)`) and `textContent` after each of two clicks. Server side: `_assert_label` in the Python matrix asserts exactly one visible label per state in both/label and the hidden label + `title` in icon. |
| SC-4 | "Filter" is a translated msgid and renders in German with the German catalog | ✓ VERIFIED | `buttons.py:5` `from django.utils.translation import gettext as _`, `:330` `data["cv_action_label"] = _("Filter")` at `get_context` time. PO entry (`django.po:46-48`, `#: lib/view/buttons.py:330`, non-fuzzy). `GNUTranslations._catalog` contains `'Filter'` (checked with `python3 -I`). Ran `pytest tests/test1/test_i18n.py -k filter` → 5 passed (`test_filter_catalog_entry`, `test_filter_gettext_at_render_time` with two distinct Unicode sentinels, `test_filter_german_render[icon/both/label]` asserting the toolbar's `aria-label="Aktionen"` proves the active language). |
| 1 | EDGE-FILT-01-empty: None button mode + empty/unrelated view map reach the live floor; selected map replaces lower maps; direct instances use their own override and declared key, never the list singular default (D-01, D-02) | ✓ VERIFIED | `cv_get_action_label_mode` (`base.py:312-322`) — own map → button `label_mode` → selected map → `target_default or default_label_mode("context")`; `FilterContextButton.get_context` (`buttons.py:329`) passes no `target_default`. Tests `test_filter_mode_resolution` (9 cases incl. `empty-view-map-replaces-lower-maps`, `floor`), `test_filter_ignores_list_singular_default[label/both]`, `test_filter_declared_key_and_direct_button`, `test_filter_live_floor` — all in the 199-passed focused run. |
| 2 | EDGE-FILT-01-encoding: mode-less and explicit-icon renders equal pre-change raw strings; absent/unknown direct modes select icon classes; toolbar golden unchanged; icon keeps hidden label/title/tooltip, both has spaced visible text without them (D-05) | ✓ VERIFIED | `RAW_DEFAULT_FILTER` captured in `cf17af2` (touches only the test file; first production edit is `4036e97`), so the oracle is the pre-change template. `test_filter_raw_default_bytes` and `test_filter_direct_mode_fallback[absent/None/""/"text" × 2]` passed. Template `{% else %}` branch passes literal `"icon"` to `cv_button_class`. Both-branch separator: literal space before `<span>` (line 13), asserted by `labels[0].getprevious().tail`. |
| 3 | EDGE-FILT-02-adjacency: shared host class tokens survive both swaps; mixed/unusable host placement renders standalone children; label mode has neither icon markup nor host hooks (D-03, D-06) | ✓ VERIFIED | JS fixture `HOST = {open: "icon icon-funnel", close: "icon icon-x"}` shares the `icon` token; `expectIcons` asserts the inactive token is absent and `btn`/`m-<mode>` survive. Python `_assert_icons` covers element, host, open-host/close-element, open-element/close-host; `_assert_no_icons` for label. Template line 1 skips `cv_icon_class` entirely in label mode; line 11 guards the wrapper spans with `cv_label_mode != "label"`. |
| 4 | EDGE-FILT-02-empty: label-only toggle still calls collapse and persists; absent toggles on no-filter/pinned pages stay absent; script loading harmless (D-06, D-10) | ✓ VERIFIED | Behavior-dependent; vitest label-mode cases passed (collapse spy called once per click, one POST per click). `test_filter_visibility` (author page without filter; pinned) passed; `test_filter_pinned.py` in the focused run; JS `loads harmlessly on a page without a toggle` passed (36/36). `get_context` keeps both early `{"cv_access": False}` returns (`buttons.py:312-318`). |
| 5 | EDGE-FILT-02-encoding: each toggle sends the existing path, POST, X-CSRFToken, JSON content type, boolean payload; label chars never enter the payload (D-06, D-10) | ✓ VERIFIED | `list.filter.js:34-38` — `fetch(config.request.path, {method: "POST", headers: {"X-CSRFToken": ..., "Content-Type": "application/json; charset=utf-8"}, body: JSON.stringify({filter_expanded: next})})`. `expectPost` asserts the exact call tuple; Unicode-label cases prove the label is not in the body. |
| 6 | EDGE-FILT-02-ordering: collapse before ARIA/icon/persistence; thrown/false adapter leaves DOM and requests unchanged; rejected POST preserves the toggle (D-06) | ✓ VERIFIED | Behavior-dependent. `list.filter.js:15-17` returns before any mutation when `toggle(panel) === false`; `.catch(() => {})` after fetch. Vitest `collapses before it changes the DOM or persists` (×3 layouts), `changes nothing on a label-only toggle when the collapse adapter throws/refuses`, `keeps a successful label-only toggle when the state POST fails` — all passed in the 36/36 run. |
| 7 | EDGE-FILT-02-idempotency: two accepted clicks restore the initial state with exactly one opposite-state POST per click; a refused click produces none (D-06, D-10) | ✓ VERIFIED | Behavior-dependent. Two-click cases assert `fetchMock` call count == click index and `expectPost(..., state)`; adapter-refusal cases assert `fetchMock` not called. 12 + 6 passed by name. |
| 8 | EDGE-FILT-02-concurrency: out-of-order settlement never rolls back the latest DOM state; no server ordering guarantee introduced (D-06, D-10) | ✓ VERIFIED | Behavior-dependent. `never rolls back the latest state when persistence settles out of order` (×3 layouts) rejects the latest request first, resolves the earlier one late, asserts `aria-expanded="false"`, icons and label node unchanged. Passed in 36/36. `list.filter.js` has no `.then` that touches the DOM. |
| 9 | EDGE-FILT-03-empty: an empty custom label result preserves the translated seed; label-only markup keeps a nonempty accessible visible name without icon hooks (D-04, D-07, D-09) | ✓ VERIFIED | `test_filter_gettext_at_render_time`: `label_template_code="{% if False %}x{% endif %}"` → `cv_action_label` equals the sentinel. `_assert_label` for label mode asserts one visible span with text `Filter` and `data-cv-filter-icon is None`. |
| 10 | EDGE-FILT-03-encoding: default and Unicode custom labels keep exact `textContent` across expansion/collapse; untrusted text is escaped (D-04, D-07) | ✓ VERIFIED | Vitest Unicode cases (`Ünïcødé ✓ 搜索`) assert `textContent` after each click. `test_filter_label_escaping[mode × '<b onclick="x()">Fïltér & «Ω»</b>' / 'Filtrer ✓']` passed; template uses `{{ cv_action_label }}` with autoescape, no `safe`. |
| 11 | EDGE-FILT-03-idempotency: both-mode element/host and label-only toggles preserve the label node and text through two clicks from either start state (D-03, D-04) | ✓ VERIFIED | Same 12 named vitest cases as SC-3 (`toBe(f.label)` node identity). |
| 12 | EDGE-FILT-03-concurrency: adapter refusal/throw and delayed/rejected/reordered persistence never alter the visible label (D-04, D-06) | ✓ VERIFIED | Out-of-order test asserts `visibleLabel(f.toggle)).toBe(f.label)` and `textContent === "Ünïcødé ✓"` after both settlements; refusal/throw tests assert unchanged DOM. |
| 13 | EDGE-FILT-04-empty: core German PO has a non-fuzzy translated Filter entry; compiled catalog contains the key explicitly (D-09) | ✓ VERIFIED | `django.po:46-48` read directly; `gettext.GNUTranslations(...)._catalog` membership `True` (independent `python3 -I` check); `test_filter_catalog_entry` asserts `not entry.obsolete`, `"fuzzy" not in entry.flags`, occurrence `lib/view/buttons.py`. |
| 14 | EDGE-FILT-04-encoding: Unicode sentinel proves runtime gettext; German render proves active-language integration; PO/MO checks prove the shipped catalog; custom labels override the seed (D-07, D-09) | ✓ VERIFIED | `test_filter_gettext_at_render_time` patches `buttons._` twice with distinct sentinels and asserts `calls == ["Filter", "Filter"]`; `test_filter_german_render` under `translation.override("de")` asserts `Aktionen` + `Filter` + custom `Suchen` wins, and that the language restores to `en`. 5 passed. |
| 15 | 03-02: Projects can configure filter mode via a settings-map example or `FilterContextButton` override, with the declared key and no target-view default explained and the canonical order linked (D-01, D-02, D-08) | ✓ VERIFIED | `docs/reference/context_buttons.md` `### The filter toggle` (read in full): `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` block, `cv_context_buttons = [FilterContextButton(label_mode="label")]` block with the real import, `key="search"` paragraph, "no target view, so it has no target-view default", link to `action_menus.md#context-label-mode-resolution`; import added at line 552. `test_filter_toggle_reference_contract` + `test_canonical_label_mode_resolution_sections` passed by name. Key link `action_menus.md#context-label-mode-resolution` verified by `verify.key-links`. |
| 16 | 03-02: Theme authors find all three modes, host/mixed placement, constant translated/custom labels, optional icon hooks and whole-template ownership in a compact contract (D-03..D-09) | ✓ VERIFIED | Three-mode table present; "The label stays the same when the panel opens or closes"; "default label `Filter` is translated"; host placement "when both resolve to host classes ... two icon spans otherwise"; "A whole-button `template` / `template_code` receives the resolved `cv_label_mode` and owns its markup". `buttons.md:221,306-309` and `icons.md:174-179` corrected to mode-qualified prose (read). Prose matches the template logic I read (line 1 host-class lookup, line 3 `cv_open_class and cv_close_class` gate). Residual `FilterContextButton` exceptions at `context_buttons.md:140,466` concern navigation target / target checks, not label mode — not stale. |
| 17 | 03-02: Docs preserve the stable disclosure IDs, collapse/error behavior, persistence, reset and never-folded rules (D-06, D-10) | ✓ VERIFIED | `javascript.md:187-217` names `#cv-filter-toggle`, `filter-collapse`, `aria-expanded`/`aria-controls`, collapse-first, no rollback after failed POST, `#filter-button-reset` unaffected; `action_menus.md:186` never-folded bullet updated. `verify.key-links` pattern `cv-filter-toggle` found in `javascript.md`. `mkdocs build --strict` exit 0 (run here, 0.5 s). |
| 18 | 03-02: Unreleased Fixed explains the configured-floor effect; migration contract and checklist guide copied templates; default goldens unchanged; every quality gate has an explicit result (D-05, D-11) | ✓ VERIFIED | `CHANGELOG.md:156-164` Fixed bullet with "A project that already sets `CRUD_VIEWS_LABEL_MODE_DEFAULTS["context"]` to `"both"` or `"label"` now gets that mode on the filter toggle too"; `docs/migrating-1.0.md:332-340` detailed contract ("Its context carries the resolved `cv_label_mode` ... a copy that ignores it renders the icon form in every mode", icon instructions qualified to icon/both) and `:404-407` checklist bullet linking the compact contract. No `### Breaking` entry added, so the CLAUDE.md migration-doc rule is not triggered beyond what was done. Goldens unchanged. 03-02-SUMMARY gate table records the one red gate honestly (repo-wide `ruff format --check` on pre-existing planning Markdown; `src tests` clean). |

**Score:** 22/22 truths verified (0 present, behavior-unverified)

Behavior-dependent truths (SC-2, SC-3, 4, 6, 7, 8, 11, 12) were each upgraded to VERIFIED by a named test run in this session, not by symbol presence.

Reliance check (advisory): no `coincidental-reliance` flags. The one candidate — rendered and direct resolution agreeing (review WR-01) — rests on a precondition the code itself establishes (`FilterContextButton.get_context` never merges `cv_get_dict()`, so `cv_context_label_mode` is never present), and `test_filter_mode_resolution` asserts both paths explicitly (`(expected, expected)`), so it is not undeclared.

### Required Artifacts

`gsd_run query verify.artifacts` → 03-01: 6/6 passed (exit 0); 03-02: 6/6 passed (exit 0). Levels 2-4 checked by reading.

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `src/crud_views/lib/view/buttons.py` | `FilterContextButton` context with declared-key resolution and render-time gettext | ✓ VERIFIED | `get_context` lines 309-340: early `cv_access=False` returns kept; `cv_label_mode` stamped from `cv_get_action_label_mode("context", self.key, self)` before `_apply_label/_apply_variant/_inject_template`; `_("Filter")` per call. Wired: called by `CrudView._cv_get_action_context` → `cv_get_context`. |
| `src/crud_views/templates/crud_views/tags/context_action_filter.html` | Three accessible modes using existing class and icon registries | ✓ VERIFIED | Read with `cat -A`: explicit both/label branches, legacy icon `{% else %}` with literal `"icon"`; `type`, `id`, `aria-expanded`, `aria-controls`, `cv-key` in every mode. Wired via `FilterContextButton.template` default. |
| `tests/test1/test_filter_toggle_label_mode.py` | Raw baseline + full mode/resolution/customization matrix | ✓ VERIFIED | 593 lines, 88 cases, 0 skipped; contains `test_filter_both_tracer`. |
| `tests/js/list.filter.test.js` | Label-only and constant-label regression coverage | ✓ VERIFIED | 370 lines, 36 cases, 0 skipped/only; `LAYOUTS` includes `["label", "element"]`. |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | Extracted and translated Filter msgid | ✓ VERIFIED | Entry at lines 46-48 with source reference. |
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` | Compiled German Filter entry | ✓ VERIFIED | `_catalog` membership confirmed independently. |
| `docs/reference/context_buttons.md` | Compact filter-mode contract and examples | ✓ VERIFIED | Section read in full (see truth 15/16). |
| `docs/reference/action_menus.md` | Canonical resolution + never-folded | ✓ VERIFIED | `### Context label-mode resolution` at line 87; filter bullet at 186. |
| `docs/reference/javascript.md` | Optional icon hooks and disclosure/error contract | ✓ VERIFIED | `## The filter toggle contract` lines 187-217. |
| `CHANGELOG.md` | Public correction and unchanged-default note | ✓ VERIFIED | Fixed bullet, contains `#262`. |
| `tests/test1/test_label_mode_docs.py` | Executable doc contract | ✓ VERIFIED | 3 named tests passed. |
| `docs/migrating-1.0.md` | Copied-template contract and checklist | ✓ VERIFIED | Lines 332-340 and 404-407. |

### Key Link Verification

`gsd_run query verify.key-links` → 03-01: 4/4 (exit 0); 03-02: 2/2 (exit 0). Each confirmed by reading the source.

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `buttons.py` | `base.py` | `cv_get_action_label_mode("context", self.key, self)` with no `target_default` | ✓ WIRED | `buttons.py:329`; resolver `base.py:299-322`. |
| `context_action_filter.html` | `templatetags/crud_views.py` | `cv_button_class` receives the resolved mode | ✓ WIRED | Line 3: `{% cv_button_class "context" cv_variant\|default:"secondary" cv_label_mode %}`; `test_filter_both_tracer` sees `context:secondary:both` class override reach the button. |
| `context_action_filter.html` | `list.filter.js` | Stable IDs, `aria-expanded`, optional icon hooks | ✓ WIRED | `id="cv-filter-toggle"`, `aria-controls="filter-collapse"`, `data-cv-filter-icon-open/close` only when host classes resolve; JS reads exactly these. |
| `list.filter.js` | `lib/views/mixins.py` | CSRF-protected boolean `filter_expanded` POST, session-backed GET | ✓ WIRED | JS body `{filter_expanded: next}`; tracer POST → 200 → GET shows `aria-expanded="true"`. |
| `context_buttons.md` | `action_menus.md` | `#context-label-mode-resolution` link | ✓ WIRED | Link present; `mkdocs --strict` validates anchors. |
| `javascript.md` | `list.filter.js` | Documented IDs and failure semantics | ✓ WIRED | Prose matches the handler's collapse-first return and `.catch(() => {})`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `context_action_filter.html` | `cv_label_mode` | `FilterContextButton.get_context` → `view.cv_get_action_label_mode` → view map / button / ViewSet+settings map / lazy floor | Yes (9 resolution cases produce 3 distinct modes) | ✓ FLOWING |
| `context_action_filter.html` | `cv_action_label` | `_("Filter")` then `_apply_label` (custom templates) | Yes (sentinel test, German render, `Suchen` override) | ✓ FLOWING |
| `context_action_filter.html` | `cv_filter_expanded` | `ListViewTableFilterMixin.cv_filter_expanded` (session) | Yes (POST then GET flips it) | ✓ FLOWING |
| `context_action_filter.html` | `cv_open_class` / `cv_close_class` | `cv_icon_class "filter"/"filter-close" "context"` (icon registry) | Yes (host vs element matrix) | ✓ FLOWING |
| `list.filter.js` | `next` → POST body | `aria-expanded` attribute (or panel visibility fallback) | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

All run in this session from the checkout root; no servers started, no state mutated outside pytest's in-memory DB.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| both-mode render + persisted toggle; raw default bytes; toolbar golden | `pytest tests/test1/test_filter_toggle_label_mode.py::test_filter_both_tracer ::test_filter_raw_default_bytes tests/test1/test_action_menus_golden.py::test_toolbar_list_with_filter -q` | 4 passed in 0.62s | ✓ PASS |
| label mode across 2 states × 4 placements | `pytest tests/test1/test_filter_toggle_label_mode.py -k "mode_placement_matrix and label" -q` | 24 passed | ✓ PASS |
| translated default (PO/MO, sentinel, German render) | `pytest tests/test1/test_i18n.py -k filter -q` | 5 passed | ✓ PASS |
| label-only click flips ARIA + persists (SC-2) | `npx vitest run tests/js/list.filter.test.js -t "label-mode toggle"` | 6 passed, 30 skipped (filter) | ✓ PASS |
| constant label over two clicks (SC-3) | `npx vitest run tests/js/list.filter.test.js -t "keeps the label"` | 12 passed | ✓ PASS |
| focused Python modules (once) | `pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_button_leaves.py tests/test1/test_context_action_label_mode.py tests/test1/test_filter_pinned.py -q` | 199 passed in 12.8s | ✓ PASS |
| filter JS file (once) | `npx vitest run tests/js/list.filter.test.js` | 36 passed | ✓ PASS |
| doc contract tests | `pytest tests/test1/test_label_mode_docs.py::test_filter_toggle_reference_contract ::test_canonical_label_mode_resolution_sections ::test_label_mode_reference_links_and_diagram -q` | 3 passed | ✓ PASS |
| strict docs build | `.venv/bin/mkdocs build --strict -d <scratchpad>` | exit 0, built in 0.54s | ✓ PASS |
| compiled catalog membership | `python3 -I -c "... GNUTranslations ... 'Filter' in t._catalog"` | `True 'Filter'` | ✓ PASS |
| goldens / handler unchanged | `git diff 3a51f81 --stat -- tests/test1/golden/ src/crud_views/static/crud_views/js/list.filter.js` | empty | ✓ PASS |
| commits exist | `gsd_run query verify.commits <11 hashes>` | `all_valid: true` | ✓ PASS |

The full suite was not re-run here; the orchestrator reports the post-merge run (3457 passed, 1 skipped; JS 149 passed) and 03-02-SUMMARY records the same.

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` exist and neither PLAN declares probes.

### Requirements Coverage

Both plans declare `requirements: [FILT-01, FILT-02, FILT-03, FILT-04]`. REQUIREMENTS.md maps exactly FILT-01..04 to Phase 3; no orphaned requirements.

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| FILT-01 | 03-01, 03-02 | `{"filter": "both"}` → icon + "Filter", no `title`; `"label"` → text only; default byte-identical (golden) | ✓ SATISFIED | SC-1, truths 1-2, 15; golden unchanged |
| FILT-02 | 03-01, 03-02 | `list.filter.js` toggles `aria-expanded` and persists for a toggle without icon spans (vitest label-only) | ✓ SATISFIED | SC-2, truths 3-8; 6 named vitest label-mode cases |
| FILT-03 | 03-01, 03-02 | Visible text constant; only `aria-expanded` and the icon change | ✓ SATISFIED | SC-3, truths 9-12; 12 named vitest cases + Python `_assert_label` |
| FILT-04 | 03-01, 03-02 | "Filter" is a translated msgid; German catalog updated | ✓ SATISFIED | SC-4, truths 13-14; PO/MO + 5 i18n tests |

### Decision Coverage

`gsd_run query check.decision-coverage-verify` → All trackable CONTEXT.md decisions are honored by shipped artifacts (11/11, `not_honored: []`). Non-blocking gate; recorded for drift tracking.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `tests/test1/test_filter_toggle_label_mode.py` | FILT-01..03 | 88 | 0 | No — `RAW_DEFAULT_FILTER` was captured from the pre-change template at `3a51f81` in `cf17af2` (test-only commit, before `4036e97`), i.e. the oracle is the prior system, which is exactly what an "unchanged bytes" requirement demands | Value / behavioral (exact class lists, XPath node sets, POST→GET) | OK |
| `tests/js/list.filter.test.js` | FILT-02, FILT-03 | 36 | 0 | No | Behavioral (multi-click, node identity, exact fetch tuple, out-of-order promises) | OK |
| `tests/test1/test_i18n.py` (filter tests) | FILT-04 | 5 | 0 | No — PO/MO parsed with polib/gettext, sentinel patch, German page | Value | OK (IN-03: reaches into private `_catalog`; cosmetic) |
| `tests/test1/test_label_mode_docs.py` | FILT-01..04 (docs) | 3 named | 0 | No | Value (phrase/anchor presence) | OK |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0. **Insufficient assertions:** 0.

Note on JS fixtures: the vitest cases build the label-mode markup in `modeFixture` rather than rendering the Django template. This is acceptable because the Python matrix independently asserts the server-rendered label-mode markup has the same shape the fixture assumes (`#cv-filter-toggle`, `aria-expanded`, no `[data-cv-filter-icon]`, no host attributes). A future template change that diverged from the fixture would be caught on the Python side, not the JS side.

### Anti-Patterns Found

Scanned all 20 phase-modified files for `TBD|FIXME|XXX`, `TODO|HACK|PLACEHOLDER`, placeholder prose, empty returns and hardcoded-empty props.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No debt markers in any phase file | — | — |
| `tests/test1/test_button_leaves.py` | 145-149, 649-650 | word "placeholder" | ℹ️ Info | False positive: the fixed-width icon placeholder span `cv-icon-fw` under test, not a stub |
| `docs/reference/buttons.md` | 342, 481 | word "placeholder" | ℹ️ Info | False positive: format-string placeholder `{name_class}` and icon placeholder prose |
| `src/crud_views/lib/view/buttons.py:329` + `base.py:642-645` | — | WR-01 double resolution of `cv_label_mode` (direct stamp, then pipeline re-stamp) | ⚠️ Warning | Does not undermine any must-have: both paths produce the same value under the current class and the resolution test asserts both. Explicitly retained by the plan (A11 disposition). Side effect: an invalid floor is evaluated twice per render. Follow-up candidate, not a gap. |
| `src/crud_views/templates/crud_views/tags/context_action_filter.html` | 1, 3, 7, 11, 13 | WR-02 malformed stamped mode (e.g. `"text"`) renders the icon form with no error even under `CRUD_VIEWS_STRICT`, unlike `cv_button_data()` for stock leaves | ⚠️ Warning | Does not undermine the phase goal (valid configured modes) and is the plan's explicit A1 disposition; the four static diagnostics (E210/E211/E106/pydantic) are tested. It does leave a documented inconsistency with the strict-mode promise of the preceding CHANGELOG entry. Recommend a follow-up to apply `is_label_mode`/`_invalid_label_mode` at the stamp, as the review suggests. |
| `CHANGELOG.md:157-159` | — | IN-02 sentence reads as if `FilterContextButton(label_mode="label")` selects `"icon"` | ℹ️ Info | Editorial; folded into human check 3. |
| `docs/reference/context_buttons.md:552` | — | IN-04 `FilterContextButton` not re-exported from `crud_views.lib.view`; doc test pins the gap | ℹ️ Info | Scoped out by plan (A8); deferred-items noted. |
| `context_action_filter.html` label branch | — | 03-UI-REVIEW warning 1: label-only button has no on-button visual open/closed cue (only `aria-expanded`) | ℹ️ Info | Accessibility contract (ARIA) is met; the visual affordance question is routed to human check 4. |

No 🛑 Blockers.

### Human Verification Required

The phase is user-facing (a toolbar button), so the infrastructure auto-pass does not apply. Items 1-3 are harvested verbatim in intent from the `<human-check>` blocks in 03-02-PLAN (tasks 1-3), which the planner deferred to end-of-phase under `workflow.human_verify_mode = end-of-phase`; 03-02-SUMMARY lists the same three as open. Item 4 is the verifier's own: visual appearance and real-browser interaction were never observed (03-UI-REVIEW captured no screenshots).

### 1. Compact filter contract vs decisions D-01..D-10

**Test:** Open `docs/reference/context_buttons.md#the-filter-toggle`; compare the two examples, the mode table and the prose against D-01..D-10 in 03-CONTEXT.md and the executed behavior (`pytest tests/test1/test_filter_toggle_label_mode.py -q`).
**Expected:** One canonical resolution order (linked, not restated); real import path; "no target view, so no target-view default"; never-folded rule intact.
**Why human:** Planner-deferred; editorial fidelity is a judgment the doc tests only approximate.

### 2. Optional-icon prose vs fixtures

**Test:** Read `javascript.md#the-filter-toggle-contract` and the filter paragraphs of `icons.md` against the vitest `LAYOUTS` (label/element, both/element, both/host) and the Python `PLACEMENTS` (element, host, two mixed).
**Expected:** Host form only with two usable host classes; mixed/unusable → two element spans in icon/both; label → no spans, no host classes, no `data-cv-filter-icon-*`; tooltip marker only in icon mode.
**Why human:** No doc test pins this prose (03-02-SUMMARY D3 `human_judgment: true`).

### 3. Fixed entry and both migration entry points vs behavior

**Test:** Read the CHANGELOG `#262` Fixed bullet and `docs/migrating-1.0.md` lines ~332-340 and ~404-407; run `pytest tests/test1/test_filter_toggle_label_mode.py::test_filter_live_floor -q` and `git diff 3a51f81 -- tests/test1/golden/`.
**Expected:** Fixed (not Breaking) is right because default output is unchanged; floor impact named; both migration locations cover resolved `cv_label_mode` and optional icons; decide on IN-02's sentence split.
**Why human:** Release-note classification is a judgment (03-02-SUMMARY D4 `human_judgment: true`).

### 4. Browser check of the three modes

**Test:** In the example project set `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}`, load a filtered list, click the toggle twice; repeat with `"label"` and with the setting removed; optionally in German.
**Expected:** both: icon + "Filter" with a normal gap, no tooltip, icon swaps, text constant. label: text-only, panel still toggles, state survives reload. Default: unchanged from before. German: "Filter" / "Aktionen". Note whether the label-only button offers any visual open/closed cue (UI review warning 1).
**Why human:** Visual appearance and real-browser behavior; all evidence so far is jsdom and Django test client.

### Gaps Summary

No gaps. Every roadmap success criterion and every PLAN truth is backed by code read in this session and by named tests run here; artifacts, key links and commits all resolve; goldens and `list.filter.js` are byte-identical to the pre-phase base; the German catalog entry is real and compiled. The two review warnings (WR-01 double resolution, WR-02 silent icon fallback for a malformed stamped mode in strict mode) are genuine inconsistencies with the stock-leaf pipeline but were explicitly dispositioned by the plan (A11, A1), are pinned by tests as limitations, and do not affect any configured valid mode — they are recorded as warnings for follow-up, not as gaps. Status is `human_needed` solely because the plan deferred three documentation judgment checks to end-of-phase and no browser observation of the three modes exists yet.

---

_Verified: 2026-10-26T16:21:30Z_
_Verifier: Claude (gsd-verifier)_
