# Phase 1: Label-mode defaults - Context

**Gathered:** 2026-10-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Plan 1A, branch `feat/label-mode-defaults`. A project sets the label-mode floor for each button location in one
place, `CRUD_VIEWS_LABEL_MODE_DEFAULTS`. This setting is merged per key over the package defaults
`{"context": "icon", "list": "icon", "card": "both"}`. Every location reads that floor from one accessor,
`crud_views.lib.view.label_mode.default_label_mode(location)`. Check `crud_views.E108` validates the setting. With no
configuration, the rendered output is byte-identical (goldens unchanged).

Requirements: LMOD-01 … LMOD-06. Out of scope: per-ViewSet, per-view or per-variant entries in the defaults map, the
`"form"` location (Phase 6), the filter toggle (Phase 3), and any change to the semantics of the existing per-key maps.

</domain>

<decisions>
## Implementation Decisions

### E108: setting validation
- **D-01:** `crud_views.E108` is an **Error** both for an unknown location key and for an invalid mode value. There is
  no Warning tier and no new W-ID. A typo must fail loudly. The cost is accepted: a setting written for a newer
  minor version fails on an older one. — **Reversibility:** one-way — projects put check IDs in
  `SILENCED_SYSTEM_CHECKS`, and Phase 7 freezes the ID and its severity.
- **D-02:** Valid keys are **derived from `LOCATIONS`** (`button_data.py:12`), never from a literal. `"form"` is **not**
  accepted in Phase 1. Phase 6 adds `"form"` to `LOCATIONS`, and E108 then accepts it automatically. Between Phase 1
  and Phase 6, `{"form": ...}` fails E108. Add a test pinning `set(LABEL_MODE_DEFAULTS) == LOCATIONS`, so that the
  package map and the location set cannot drift. (Phase 2/1C may split `LOCATIONS` into explicit sets. E108 must
  follow the button-data / label-mode location set, not the class-key `VARIANT_LOCATIONS` set.)
- **D-03:** A non-dict value is reported under E108. This includes `None`, a string or a list. There is no special case
  for `None`: an unset setting means the package defaults, but an explicit `None` is invalid. This mirrors how E106
  treats the label-mode maps.
- **D-04:** E108 emits **one message per bad entry**, naming the key and the value. A non-dict value gives one message
  for the whole setting.
- **D-05:** Use the **E106/E210 message wording** and no hint. Example shape: `setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key
  'cotext' must be one of ['card', 'context', 'list'], got ...` and `... key 'card' must be one of ['both', 'icon',
  'label'], got ...`. No did-you-mean hint.
- **D-06:** A nested dict value (e.g. `{"context": {"filter": "both"}}`) is an invalid mode. Nested per-key forms are
  not supported, because the per-key maps already exist.
- **D-07:** E108 goes into `CrudViewsSettings._action_settings_messages` (`settings.py:98-132`) next to E105/E106,
  with deferred imports (settings.py must not import the view package at module level). E108 reads the raw setting
  the same lazy way the accessor does.

### Runtime fallback for bad modes (LMOD-05)
- **D-08:** If the setting holds an invalid mode for a location, `default_label_mode(location)` falls back to the
  **package default for that location** (`LABEL_MODE_DEFAULTS[location]`), never to the setting itself. An unknown
  key in the setting is ignored at render.
- **D-09:** **Strict mode raises, otherwise log and fall back.** This is the same rule as the icon-less guard (#264):
  `is_strict()` (`CRUD_VIEWS_STRICT`, defaults to `DEBUG`) raises `ValueError` at render. Non-strict logs a warning and
  falls back.
- **D-10:** LMOD-05 **also fixes the existing crash** in `cv_button_data` (`button_data.py:84-85`), where a bad stamped
  `cv_label_mode` raises `ValueError` even in production. It follows the same strict/log rule. In non-strict mode it
  falls back to `default_label_mode(location)`, the configured floor. The `cv_no_label` ValueError (`:62-66`) stays as
  it is.
- **D-11:** The fallback warning is logged **once per process per bad `(location, value)` pair**, not on every render
  (renders are hot paths). The mechanism is the agent's choice (see Discretion).
- **D-12:** `default_label_mode(location)` **raises `ValueError` in every mode** for a location outside `LOCATIONS`. A
  wrong location argument is a caller bug, not configuration. This matches `cv_button_data`'s existing contract
  (`:58-59`).
- **D-13 (locked by STATE.md/research):** The setting is read **lazily at call time** from `django.conf.settings`, not
  as an import-time Pydantic snapshot, so `override_settings` works (LMOD-04). At least one test must use
  `override_settings`, not monkeypatch. Never mutate `LABEL_MODE_DEFAULTS` when merging.

### Card view default becomes `None` (LMOD-03)
- **D-14:** `CardListView.cv_card_actions_label_mode: str | None = None`. `None` means "the defaults map". Resolution
  order: `CardAction.label_mode` → `CardAction.no_label` (`"icon"`) → view attribute (if not None) →
  `default_label_mode("card")`. An explicitly set `"both"` still wins over `{"card": "label"}`. E210 on the attribute
  (`card.py:112`) must accept `None`. Fix the type in the code, the docs (`card-list-view.md:71`) and the check
  together.
- **D-15:** Add a **public resolver `cv_get_card_actions_label_mode()`**. It returns the attribute if it is set,
  otherwise `default_label_mode("card")`. `cv_get_card_action_data` uses it. The docs point subclasses and templates
  to this method or to the stamped `cv_label_mode`, never to the raw attribute. — **Reversibility:** one-way — new
  public API that Phase 7 freezes.
- **D-16:** The CHANGELOG gets a **`### Breaking` entry** (code reading the attribute now gets `None`; the rendered
  output is unchanged) plus a bullet in `docs/migrating-1.0.md`, per the AGENTS.md rule. It also gets an `Added` entry
  for the setting, the accessor, the resolver and E108.
- **D-17:** In the `docs/migrating-1.0.md` recipe "restore the 0.29 card look", the **setting comes first**
  (`CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}`). `cv_card_actions_label_mode = "label"` (per view) and
  `CardAction(label_mode="label")` (per button) follow as the finer alternatives.
- **D-18:** `CardAction.no_label` stays **untouched** in Phase 1. It keeps its place in the chain and still maps to
  `"icon"`, with no DeprecationWarning. Removal is LATER-01.

### Names that Phase 7 will freeze
- **D-19:** The `cv_context_actions_label_mode` (per-key dict) / `cv_context_action_label_mode` (target-view default
  string) pair **keeps its names and is frozen as stable**. LATER-02 closes as "won't rename". The Phase 1 docs make
  the distinction clear wherever both names appear. — **Reversibility:** one-way — Phase 7 freezes both names at 1.0.0.
- **D-20:** `CardAction.no_label` / the `cv_no_label` guard is **removed before 1.0** (LATER-01, outside this phase).
  Phase 7 lists it as "deprecated, removed in 1.0.0", never as stable.
- **D-21:** All new Phase 1 names are **public**: the setting `CRUD_VIEWS_LABEL_MODE_DEFAULTS`,
  `default_label_mode(location)`, `LABEL_MODE_DEFAULTS` (documented as read-only) and
  `CardListView.cv_get_card_actions_label_mode()`. — **Reversibility:** one-way — semver surface at 1.0.0.
- **D-22:** The setting name is confirmed as **`CRUD_VIEWS_LABEL_MODE_DEFAULTS`**.
- **D-23:** Record D-19 and D-20 in the PROJECT.md Key Decisions table during this phase, so that Phase 7 finds them
  as decided (PITFALLS: "Decision recorded in PROJECT.md Key Decisions before Phase 4").

### Docs placement
- **D-24:** **One table in `docs/reference/settings.md`** with one row per label-mode knob and the columns "merge or
  replace", "layer" and "keys". The rows are: `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (per-key merge over the package
  defaults), `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` / `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` and the ViewSet/view maps
  (whole replacement per layer), and the card attribute. `action_menus.md` and `card-list-view.md` link to it. Phase 6
  adds the form row. The docs state explicitly that the existing maps' semantics do not change.
- **D-25:** **One canonical resolution-order section** per location (context / list / card) in
  `docs/reference/action_menus.md`. The Mermaid `MICON["icon"]` node in `docs/reference/context_buttons.md` (not
  `action_menus.md` as the plan says) becomes "defaults map" and links to that section. Other pages link instead of
  restating the order.
- **D-26:** The example project stays **untouched** in Phase 1.

### Claude's Discretion
- How "log once per bad (location, value)" is implemented (e.g. a module-level seen-set, `functools.lru_cache` on a
  warn helper, or a cache cleared by a `setting_changed` receiver). It must stay correct under `override_settings` in
  tests.
- Whether the merged map is computed per call or cached behind a `setting_changed` receiver (as
  `reset_button_classes_cache()` does). Either is fine as long as D-13 holds.
- Exact test file split among the files the plan names.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and acceptance
- `superpowers/plans/2026-10-24-concept-review-followups.md` §"Phase 1A" (lines 70-105) — design, file list, tests,
  acceptance; §"Global constraints" (lines 53-66) — goldens, branch, quality gates, CHANGELOG rule
- `.planning/ROADMAP.md` §"Phase 1: Label-mode defaults" — success criteria 1-5 (including the acceptance grep)
- `.planning/REQUIREMENTS.md` — LMOD-01 … LMOD-06; Out of Scope table; LATER-01/LATER-02
- `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` — finding 1 (origin of this phase)

### Research (pitfalls and corrected line numbers)
- `.planning/research/PITFALLS.md` — Pitfall 6 (import-time settings / `override_settings`), Pitfall 7 (merge vs
  replace), Pitfall 8 (card attribute → `None`), "E108: unknown location keys and forward compatibility", Pitfall 10
  (names Phase 7 freezes)
- `.planning/research/ARCHITECTURE.md` — lazy per-key merge pattern (≈ line 137-151), full resolution chain
  (≈ line 156-172), S1 (`LOCATIONS` has three meanings), S6 (card default `None`), S12 (Mermaid node is in
  `context_buttons.md`); corrected literals at `base.py:312` and `:317`
- `.planning/research/STACK.md` — why the field must not be strictly typed Pydantic (import-time ValidationError
  pre-empts E108)

### Docs to change
- `docs/reference/settings.md` — new setting + merge/replace table (D-24)
- `docs/reference/action_menus.md` — canonical resolution order (D-25)
- `docs/reference/context_buttons.md` — Mermaid `MICON` node → "defaults map"
- `docs/reference/card-list-view.md` §Label mode (≈ lines 50-75) — type `str | None`, resolver, order
- `docs/migrating-1.0.md` (≈ lines 124-130) — card recipe (D-17) + Breaking bullet (D-16)
- `CHANGELOG.md` — Added + Breaking entries
- `AGENTS.md` — rule: a `### Breaking` CHANGELOG entry also updates `docs/migrating-1.0.md`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `crud_views/lib/view/label_mode.py`: `LabelMode`, `LABEL_MODES`, `is_label_mode`, `is_label_mode_map`,
  `label_mode_check` (viewset.E210). `LABEL_MODE_DEFAULTS` and `default_label_mode()` go here.
- `crud_views/lib/exceptions.py:32` `is_strict()`: the strict/log switch for D-09/D-10.
- `crud_views/lib/settings.py:98-132` `_action_settings_messages`: E105/E106 pattern and deferred imports to copy
  for E108.
- The class table's lazy per-key merge and `reset_button_classes_cache()` / `setting_changed` receiver
  (`crud_views/lib/button_classes.py`): the pattern for D-13.

### Established Patterns
- Settings fields are typed `Any` and validated in `check_messages`, never strictly typed (an import-time crash
  would beat the check).
- Label-mode maps resolve view → ViewSet → setting through `cv_first_inline_keys` (`base.py:259-268`) with whole
  replacement per layer. This does not change.
- The strict-mode guard for icon-less icon-mode buttons (`button_data.py:88-101`) is the model for D-09/D-10 logging
  and raising.

### Integration Points (literals to replace — acceptance grep)
- `button_data.py:83` `ctx.get("cv_label_mode") or ("both" if card else "icon")` → `default_label_mode(location)`
- `base.py:312` `return target_default or "icon"` and `base.py:317` `mapping.get(key, "icon")` →
  `default_label_mode("context" | "list")`
- `views/card.py:28` `cv_card_actions_label_mode: str = "both"` → `str | None = None`; `:46-52` resolution through
  `cv_get_card_actions_label_mode()`; `:112` E210 skip for `None`
- `view/buttons.py:405` W292 compares against `"icon"` through `cv_get_action_label_mode()`, so it follows the floor
  automatically (`{"context": "both"}` silences W292 for unmapped keys).
- Docstrings and comments that say "keys not named are icon" (`settings.py:61-64`, `base.py:282/287/294`) must
  be updated.

</code_context>

<specifics>
## Specific Ideas

- `{"card": "label"}` is the one-line alternative to the per-view 0.29 recipe (D-17).
- `{"context": "both"}` must make every unmapped toolbar button icon+text on every page, leave rows and cards
  unchanged, and silence W292 for those keys (ROADMAP success criterion 1).
- Tabler follow-up for the acceptance note: grep the Tabler card templates (`view_card.content.html`,
  `tags/card.html`) for direct reads of `cv_card_actions_label_mode`.

</specifics>

<deferred>
## Deferred Ideas

- Removing `CardAction.no_label` / the `cv_no_label` guard: LATER-01, decided "remove before 1.0" (D-20), outside
  this phase.
- LATER-02 (rename of the label-mode pair): decided "won't rename" (D-19). Nothing to implement.
- A did-you-mean hint for E108 unknown keys was considered and rejected (D-05).

</deferred>

---

*Phase: 01-label-mode-defaults*
*Context gathered: 2026-10-25*
