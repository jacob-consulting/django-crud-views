---
phase: 01
cycle: 3
reviewers: [opencode-gemini, opencode-grok, claude-fable]
reviewed_at: 2026-10-25T18:02:00Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md, 01-04-PLAN.md]
plans_revision: bdd445c
models:
  opencode-gemini: "openrouter/google/gemini-4-argon (reasoning=high)"
  opencode-grok: "openrouter/x-ai/grok-4.7 (reasoning=high)"
  claude-fable: "claude-fable-5-1 (reasoning=high)"
model_sources:
  opencode-gemini: "pinned"
  opencode-grok: "pinned"
  claude-fable: "pinned"
---

> Note: opencode-gemini and opencode-grok share the opencode adapter; their consensus is cross-model, not cross-tool.

# Cross-AI Plan Review — Phase 01

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts
<!-- gsd:plan-revision-conflicts:end -->

> Convergence cycle 3 (final). This review covers the plans as revised in `bdd445c`, which address the cycle-2 findings A1–A19. The cycle-2 review text is at commit `bbbf16a` and the cycle-1 text at `c1546c2`. Cycle-1 findings R1–R14 were confirmed resolved in cycle 2. New findings in this cycle are numbered B1–B6.

## OpenCode Review (opencode-gemini)

## 01-01

### 1. Summary
Plan `01-01` introduces `LABEL_MODE_DEFAULTS`, the lazy `default_label_mode(location)` accessor, and private `_invalid_label_mode` strict/warn-once recovery in `src/crud_views/lib/view/label_mode.py`, wires `cv_button_data` in `src/crud_views/lib/view/button_data.py:82-85` to use them, and adds lazy `crud_views.E108` validation in `src/crud_views/lib/settings.py:98-132`. All cycle-2 dispositions assigned to this plan (A1–A6, A19) are accurately incorporated against the live codebase. One LOW lint-interaction detail remains around the Greek-omicron lookalike test literal (`"bοth"`).

### 2. Strengths
- **Non-recursive setting fallback (A1) and lock-free fallback evaluation (R5):** `.planning/phases/01-label-mode-defaults/01-01-PLAN.md:107-115` specifies that invalid-setting recovery returns `LABEL_MODE_DEFAULTS[location]` directly without calling `default_label_mode` again, and evaluates `fallback()` before acquiring `_warned_lock`, preventing both recursion and re-entrant lock deadlock when `cv_button_data` recovers a bad stamp over a bad floor.
- **Structured warning verification in subprocess deadlock test (A2):** `.planning/phases/01-label-mode-defaults/01-01-PLAN.md:122-124` uses `unittest.TestCase().assertLogs("crud_views.lib.view.label_mode", level="WARNING")` inside the child process to assert 1 warning for equal bad values and 2 for distinct bad values.
- **Input matrices separated by validation level (A3) and non-dict fanout pinned (A5):** `.planning/phases/01-label-mode-defaults/01-01-PLAN.md:107-112,128-131` separates whole-setting non-dicts (`{}` valid), per-location setting entries (`{}` invalid), and stamped `cv_label_mode` values (falsey `None`/`""`/`[]`/`{}` keep unset fallback at `src/crud_views/lib/view/button_data.py:83`), while pinning cumulative warning counts `1/2/3` across `context`, `list`, and `card` for a non-dict setting.
- **Unused import removal (A4) and realistic raw context tracer keys (A6):** `.planning/phases/01-label-mode-defaults/01-01-PLAN.md:126,133` removes the otherwise-unused `LABEL_MODES` import at `src/crud_views/lib/view/button_data.py:8` (whose only current use is `:85`) and feeds `{% cv_button "context" %}` the exact raw context keys required by `src/crud_views/lib/view/visibility.py:14` (`cv_access=True`) and `src/crud_views/lib/view/button_data.py:80-81` (`cv_action_label`, `cv_action_short_label`, `cv_icon_action`), matching `tests/test1/test_button_leaves.py:490-500`.
- **Verified D-07 import boundary test (R6):** `src/crud_views/lib/settings.py:98-132` currently defers `crud_views.lib.view.action_menu` and `label_mode`, neither of which imports `button_data.py`, so `test_settings_defers_button_data_until_checks` in `tests/test1/test_import_safety.py` (`.planning/phases/01-label-mode-defaults/01-01-PLAN.md:166`) genuinely proves that `crud_views.lib.view.button_data` is absent before `check_messages` and loaded when E108 runs.

### 3. Concerns
- **[LOW] Literal `"bοth"` (Greek omicron) in test files will trigger Ruff `RUF001` at the phase gate:** `.planning/phases/01-label-mode-defaults/01-01-PLAN.md:128-131` instructs adding `"bοth"` (with U+03BF GREEK SMALL LETTER OMICRON) to the invalid-input matrices in `tests/test1/test_label_mode.py` and `tests/test1/test_button_data.py`. In `pyproject.toml:118-127`, Ruff enables `"RUF"` with `allowed-confusables = ["›"]` and only ignores `["RUF012"]` for `"tests/**"`. Because `01-01-01`'s verify step (`.planning/phases/01-label-mode-defaults/01-01-PLAN.md:139`) runs `ruff check` only on `src/crud_views/lib/view/label_mode.py src/crud_views/lib/view/button_data.py`, a raw `"bοth"` literal in the test files will pass Wave 1 and fail Wave 3's repo-wide `.venv/bin/ruff check` (`.planning/phases/01-label-mode-defaults/01-04-PLAN.md:214`) with `RUF001` unless written as `"b\u03bfth"` or annotated with `# noqa: RUF001`.

### 4. Suggestions
- Write the Greek-omicron lookalike string as `"b\u03bfth"` (or add `# noqa: RUF001`) in `tests/test1/test_label_mode.py` and `tests/test1/test_button_data.py`, and include the modified test files in `01-01-01`'s `ruff check` command.

### 5. Risk Assessment
**LOW** — All runtime, concurrency, and system-check mechanics are grounded in `src/crud_views/lib/view/label_mode.py`, `src/crud_views/lib/view/button_data.py`, and `src/crud_views/lib/settings.py`.

---

## 01-02

### 1. Summary
Plan `01-02` replaces the hardcoded `"icon"` fallbacks in `CrudView.cv_get_action_label_mode` (`src/crud_views/lib/view/base.py:312,317`) with `default_label_mode("context")` and `default_label_mode("list")`, updates stale class-attribute comments (`src/crud_views/lib/view/base.py:88-96`) and the `viewset.E211` scalar description (`src/crud_views/lib/view/action_menu.py:59-60`), and guards `cv_icon_mode_checks` (`src/crud_views/lib/view/buttons.py:405`) against strict `ValueError` raises from an invalid floor so `check_viewsets` (`src/crud_views/checks.py:20-28`) still returns `crud_views.E108`. All cycle-2 dispositions (A7, A8, A9, A19) are cleanly integrated.

### 2. Strengths
- **End-to-end non-strict recovery test for invalid target-view `cv_context_action_label_mode` (A7):** `.planning/phases/01-label-mode-defaults/01-02-PLAN.md:83,94` traces the exact path where `src/crud_views/lib/view/base.py:435,631` passes `cls.cv_context_action_label_mode` (`"nope"`) into `cv_get_action_label_mode`, which returns `target_default` truthily at `src/crud_views/lib/view/base.py:312` and stamps `cv_label_mode="nope"` (`base.py:633`) for `cv_button_data` (`src/crud_views/lib/view/button_data.py:83-85`) to recover to `default_label_mode("context")` (`"both"`) with a single warning across two HTTP GETs.
- **Explicit filter toggle exclusion in multi-route toolbar tests (A8):** `.planning/phases/01-label-mode-defaults/01-02-PLAN.md:90` excludes `@cv-key="filter"` and `@id="cv-filter-toggle"` (matching `src/crud_views/templates/crud_views/tags/context_action_filter.html:4,10`, which hardcodes `"icon"` until Phase 3) and asserts a nonempty remaining action set on every route (`tests/test1/app/views.py:63-124`).
- **Short-circuit floor evaluation on mapped keys:** `.planning/phases/01-label-mode-defaults/01-02-PLAN.md:112` replaces `mapping.get(key, "icon")` at `src/crud_views/lib/view/base.py:317` with `mapping[key] if key in mapping else default_label_mode("list")`, avoiding eager argument evaluation when a key is explicitly mapped.
- **Deliberate three-surface consistency contract for E211 wording (A9):** `.planning/phases/01-label-mode-defaults/01-02-PLAN.md:116` pins only the short `"string or None"` phrase for `src/crud_views/lib/view/action_menu.py:59-60` rather than coupling tests to the full sentence.

### 3. Concerns
- None. All mechanisms and selectors match the live views and templates.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Changes are confined to two fallback lines, comments/docstrings, one diagnostic string, and a narrow `try/except ValueError` in `src/crud_views/lib/view/buttons.py:405`, with zero file overlap against parallel plan `01-03`.

---

## 01-03

### 1. Summary
Plan `01-03` changes `CardListView.cv_card_actions_label_mode` from `"both"` to `str | None = None` (`src/crud_views/lib/views/card.py:28`), adds the `@classmethod` resolver `cv_get_card_actions_label_mode()`, skips `viewset.E210` when the attribute is `None` (`src/crud_views/lib/views/card.py:112`), and updates `docs/reference/card-list-view.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`. Dispositions A10, A11, A12, and A19 are thoroughly addressed.

### 2. Strengths
- **Complete `card-list-view.md` table updates and Wave-2-safe anchors (R4, A12):** `.planning/phases/01-label-mode-defaults/01-03-PLAN.md:86-88` updates both the `CardAction` fields table (`docs/reference/card-list-view.md:50`) and the view attribute table (`docs/reference/card-list-view.md:71`), and links only to existing anchors (`action_menus.md#label-mode` at `docs/reference/action_menus.md:58` and `settings.md#action-menus` at `docs/reference/settings.md:71`) so `.venv/bin/mkdocs build --strict` (`mkdocs.yml:24-25`) passes at the end of Wave 2.
- **Stock `AuthorCardListView` render test preserves D-18 `no_label=True` behavior (R3):** `.planning/phases/01-label-mode-defaults/01-03-PLAN.md:84` tests `AuthorCardListView` (`tests/test1/app/views.py:74-81`) directly via `_card` (`tests/test1/test_card_label_mode_render.py:38-41`), asserting that `detail` and `update` become text-only under `{"card": "label"}` while `CardAction(key="delete", no_label=True, variant="tertiary")` stays icon-only.
- **Comprehensive Wave-2 verify script and anchor discipline for migration/changelog (A10, A11):** `.planning/phases/01-label-mode-defaults/01-03-PLAN.md:105-127` uses existing anchors (`settings.md#action-menus`, `action_menus.md#label-mode`) in `docs/migrating-1.0.md` and `CHANGELOG.md` and verifies setting-before-view-before-button order in both `docs/migrating-1.0.md:127-129` and `CHANGELOG.md:43-45` (`(#213)`), the `None`/`both`/resolver disclosure in both `"Card label-mode attribute"` bullets, and the `"Malformed stamped label modes"` bullet inside `### Fixed` (`CHANGELOG.md:136`).

### 3. Concerns
- **[LOW] Unicode-lookalike mode literal in `tests/test1/test_card_label_modes.py` can trigger Ruff `RUF001`:** `.planning/phases/01-label-mode-defaults/01-03-PLAN.md:45,77` requires testing Unicode-lookalike modes in `test_card_attribute_exact_modes`. As in `01-01`, a raw confusable character literal in `tests/test1/test_card_label_modes.py` will fail `.venv/bin/ruff check` (`pyproject.toml:118-120`) in Wave 3 unless written with a `\u` escape (`"b\u03bfth"`) or `# noqa: RUF001`.

### 4. Suggestions
- Use `"b\u03bfth"` (or `# noqa: RUF001`) in `tests/test1/test_card_label_modes.py::test_card_attribute_exact_modes`.

### 5. Risk Assessment
**LOW** — The runtime change in `src/crud_views/lib/views/card.py` is small and self-contained, and Wave 2 verification enforces both `mkdocs build --strict` and the full changelog/migration contract.

---

## 01-04

### 1. Summary
Plan `01-04` publishes the canonical configuration table in `docs/reference/settings.md`, the three canonical resolution-order sections in `docs/reference/action_menus.md`, retargets the Wave-2 links in `docs/reference/card-list-view.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`, updates `docs/reference/context_buttons.md`, `docs/reference/buttons.md`, and `.planning/PROJECT.md`, adds `tests/test1/test_label_mode_docs.py`, and runs all phase-level quality gates. All cycle-2 dispositions (A9, A10, A13–A19) are properly incorporated.

### 2. Strengths
- **Prefiltered AST extraction and non-vacuous template-tag tracer (R9, R14, A14):** `.planning/phases/01-label-mode-defaults/01-04-PLAN.md:105-107` prefilters Python fences in `docs/reference/settings.md` for `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, parses matching blocks strictly with `ast.parse`/`ast.literal_eval`, selects the dict containing `"card"`, and renders `{% cv_button "card" %}` with `cv_access=True` and `cv_icon_action="detail"` alongside an empty-defaults control render.
- **Two-column vs three-column checks tables respected (R12, A17) and bracket-free Mermaid label (A18):** `.planning/phases/01-label-mode-defaults/01-04-PLAN.md:104,137,142` keeps `docs/reference/action_menus.md:238-246` as a two-column `ID | Meaning` table with `"error"` in the `Meaning` text while adding `Level = error` rows to the three-column table in `docs/reference/buttons.md:437-448`, and uses `MICON["defaults map (default icon)"]` in `docs/reference/context_buttons.md:256`.
- **Permanent test suite decoupled from `.planning/` (A13) and release-header-resilient changelog test (A15):** `.planning/phases/01-label-mode-defaults/01-04-PLAN.md:148,154,160` checks `.planning/PROJECT.md:96-97` via a one-off `<verify>` grep rather than a permanent pytest test, and selects the target release block in `CHANGELOG.md` by locating the `### Breaking` section containing `"Card label-mode attribute"` (ignoring `## 0.30.0`'s `### Breaking` at `CHANGELOG.md:282` and surviving the `## Unreleased` → `## 1.0.0` rename).
- **Protected-path diff and untracked-file status gates (R8, A16):** `.planning/phases/01-label-mode-defaults/01-04-PLAN.md:218-221` combines `git diff --exit-code ebc7c23259ae35b2e4f34047d0da903e68a48ac8` with `git status --porcelain -- tests/test1/golden src/crud_views/templates examples`.

### 3. Concerns
- **[LOW] Staging of `test_label_mode_docs.py` functions across tasks `01-04-01` and `01-04-02`:** `.planning/phases/01-label-mode-defaults/01-04-PLAN.md:65-72` lists all six test functions in the plan-level artifact inventory, and task `01-04-01` runs `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q` (`.planning/phases/01-label-mode-defaults/01-04-PLAN.md:110`) before task `01-04-02` edits `docs/reference/context_buttons.md`, `docs/reference/buttons.md`, and `CHANGELOG.md`. While lines 102 and 107 note that `CHANGELOG.md` link retargeting and diagram/remaining-reference assertions belong to `01-04-02`, writing `test_button_label_mode_check_reference` or the `CHANGELOG.md` canonical-anchor check inside `01-04-01` would fail `01-04-01`'s pytest run before `01-04-02` executes.

### 4. Suggestions
- In `01-04-01`, define only `test_documented_card_floor_renders_label_only`, `test_label_mode_configuration_table`, `test_canonical_label_mode_resolution_sections`, and the `card-list-view.md`/`migrating-1.0.md` link assertions in `tests/test1/test_label_mode_docs.py`, then add `test_button_label_mode_check_reference`, `test_card_migration_contract`, and the `context_buttons.md`/`CHANGELOG.md` assertions in `01-04-02`.

### 5. Risk Assessment
**LOW** — Documentation anchors, tables, and verification gates are tightly aligned with the live files and tested against both `pytest` and `mkdocs build --strict`.

---

## Cross-Plan Assessment & Overall Risk

- **Cycle-2 Disposition Verification (A1–A19):** All 19 findings from cycle 2 are verified as incorporated across `.planning/phases/01-label-mode-defaults/01-01-PLAN.md` through `01-04-PLAN.md`, with single branch authority (A19) centralized in `01-01-PLAN.md:72`.
- **Overall Risk Level:** **LOW** — No HIGH or MEDIUM concerns remain; the only two LOW items are execution hygiene notes (`"b\u03bfth"` escape for Ruff `RUF001` and staged test additions between `01-04-01` and `01-04-02`). The plans are ready to execute.

---

## OpenCode Review (opencode-grok)

I'll verify the four plans against the source they cite, then check that the A1–A19 revisions actually landed.
The plans cite specific source lines. I'll check those against the current files before judging the dispositions.
A1–A19 are in the plan text and match the current source. Residual risk is low. Two documentation leftovers are new.

## 01-01

The floor, the strict/log recovery, and E108 are specified against the real leaf and the real check method. The cycle-2 hazards (re-entrant fallback, unhashable values, import boundary, test isolation) are turned into executable tests, not comments.

- The accessor stays off the Pydantic model. `settings.py:279` builds `CrudViewsSettings()` at import, so a typed field would still beat E108. The `_UNSET` sentinel matches D-03. `getattr(..., None)` would hide an explicit `None`.
- `button_data.py:8` already imports `label_mode`, and `LOCATIONS` is a `frozenset` at `button_data.py:12`. The deferred import and the `monkeypatch.setattr` of the module attribute are the only ways E108 can track that object.
- `button_data.py:83-85` still raises on every bad stamp. Routing only truthy stamps through `_invalid_label_mode`, and keeping the `or`, preserves the falsey-unset contract. `LABEL_MODES` is used only in that error, so dropping the import is safe.
- Dedup key `(location, repr(value))` matches D-11, not the research suggestion. The lock is held only around check-and-add. The equal-pair subprocess test is the right bound for the re-entry the plan itself introduces.
- The tracer keys match `test_button_leaves.py:490-500`. `visibility.py:14` treats a missing `cv_action_enabled` as usable when `cv_access is True`.

- **LOW** — `.planning/phases/01-label-mode-defaults/01-01-PLAN.md:122` says non-dict settings follow “the same strict/non-strict policy as invalid location values.” D-12 and the task’s own behavior block say an unknown location always raises. Read as “invalid mode for a location,” the sentence is fine. Read literally, it tells the executor to log-and-fallback on `default_label_mode("nope")`.

- Treat `01-01-PLAN.md:122` as invalid mode values only. Keep the behavior-block rule: unknown caller locations raise in every mode.

**Risk: LOW.** Acceptance criteria already require the D-12 raise. The sentence is the only new trap.

## 01-02

This plan is the one that makes LMOD-02 true for ordinary pages. It changes only the final fallbacks and keeps whole-map replacement. That matches `base.py:302-317`.

- `target_default or default_label_mode("context")` short-circuits, so a truthy explicit mode never evaluates a bad floor. The list side correctly refuses `dict.get(key, default_label_mode(...))`, which would call the accessor even on a hit.
- `base.py:631` stamps `data.get("cv_context_label_mode")` raw. `buttons.py:402-404` already turns an invalid target into `None` for W292 only. A7’s non-strict GET is the render path, not a second sanitizer. Two requests plus the autouse fixture are enough to prove one warning.
- `context_action_filter.html:4` and `:10` are `id="cv-filter-toggle"` and `cv-key="{{ cv_key }}"`. Excluding both, and requiring a nonempty remainder, matches the fixed icon mode at `:3`.
- `checks.py:23-28` appends E108, then runs viewset checks in the same function. A `ValueError` from `buttons.py:405` drops E108. Catching only that call is the right width. `_cv_find_context_button` (`base.py:540-548`) does not raise.
- Comments at `base.py:88-95` are the three fixed-floor strings. E211’s “string-valued” wording is `action_menu.py:59-60`. The literal gate does not match `then "icon"`, so the “don’t copy the grep expressions” note is necessary.

- No new functional gap. Filter and custom templates are excluded on purpose. Menu items already render icon plus text (`action_menus.md:128`), so success criterion 1 still holds.

- None.

**Risk: LOW.** Precedence, W292, and the golden constraint are pinned to the current call chain.

## 01-03

The card slice is the only intentional Python break, and the plan discloses it on both required surfaces. Rendered output stays on the existing leaf.

- `views/card.py:28` is `str = "both"`. `:46-52` is label_mode, then `no_label` to `"icon"`, then the attribute. `:112` always yields E210. The resolver and the `is not None` guard match that chain. `AuthorCardListView` at `tests/test1/app/views.py:76-80` has `no_label=True` on delete and explicit labels on detail/update, so the stock-page assertion is real.
- `view/card.py:12` still says the attribute is the resolved mode. A12 names that Fields row (`card-list-view.md:50`).
- Wave-2 links target anchors that exist today: `settings.md:71` (`## Action menus`) and `action_menus.md:58` (`## Label mode`). `CHANGELOG.md:43-45` is the `#213` recipe. `### Fixed` is at `CHANGELOG.md:136`. The one-off script can see those sections.
- `button_data.py:125-126` clears the icon for `"label"`, so a text-only DOM assertion is meaningful. `no_label` is left in the chain, per D-18.

- **LOW** — `CHANGELOG.md:175` (Unreleased `#269`) still says the target-view mode “is the last fallback before `"icon"`.” `01-03-02` rewrites `#213` and adds the new bullets. It does not touch this adjacent sentence, and `01-04` only retargets links. A 1.0 reader of the same Unreleased block still sees the old floor.

- Add one clause to that `#269` bullet, or point it at the new setting, in `01-03-02` or `01-04-02`.

**Risk: LOW.** Behavior, checks, and the migration contract are covered. The leftover sentence is documentation drift, not a render bug.

## 01-04

The docs plan is the right place for the single merge/replace table and the three resolution headings. The executable example is data, not `exec`. The protected-path gates match the repo.

- `ebc7c232` is `docs(01): capture phase context`. `git diff` of `tests/test1/golden`, `src/crud_views/templates`, and `examples` against it is empty. `git status --porcelain` on those paths is empty. `npm --prefix . test` is `vitest run` (`package.json:11`).
- `action_menus.md:238` is ID/Meaning only. `buttons.md:437` has a Level column. A17 matches both.
- `context_buttons.md:256` is `MICON["icon"]`. `:262` and `:305` reference the id. A bracket-free label keeps those edges valid.
- `PROJECT.md:55` still says the rename is “tracked separately,” while `:96-97` already record D-19 and D-20. The one-off grep is right. A permanent test must not read `.planning/`.
- Selecting the `#213` bullet by content, not by the `## Unreleased` heading, matters: `CHANGELOG.md:280` starts 0.30.0, which has its own Breaking section.

- **LOW** — `01-04-PLAN.md:144` updates the card paragraph (`buttons.md:423`) and the checks table, not the leaf-contract cell. `buttons.md:331` still says context/list mode is `'"icon" unless a map...'`. That restates the old floor on the page theme authors use. D-25 and this plan’s must-have say secondary pages should link, not restate.

- In `01-04-02`, replace that parenthetical with a link to `#context-label-mode-resolution` / `#list-label-mode-resolution`. Do not edit the class-key sections.

**Risk: LOW.** Gates, anchors, and the decision handoff are executable. The leaf-contract cell is the remaining public contradiction.

## Cross-plan

No dependency or file-overlap problem. `01-02` and `01-03` do not share files. `01-04` retargets links only after the headings exist. `01-02`’s E211 wording can land before `01-03` accepts `None`. The new test pins the message text, not the card check.

A1–A19 are incorporated and should not be re-opened. The deferred choices (no source dimension on the warning key, no production `setting_changed` reset, no `no_label` removal) match D-11 and D-18. Overall phase risk is **LOW**. Fix the two stale sentences (`buttons.md:331`, `CHANGELOG.md:175`) in the existing docs tasks so 1.0 readers do not keep the old floor.

---

## Claude Review (claude-fable)

Source verification is complete except for one dry-run the sandbox would not approve. I'm writing the review now.

# Cross-AI Plan Review — Phase 01 (cycle 3, plans at `bdd445c`)

All findings below were checked against the working tree. Every cited `file:line` was opened this session. One check could not run: the sandbox declined to execute a bare-process Python child, so the premise of 01-01-02's subprocess test is reasoned from source, not executed (noted under 01-01).

## 01-01

**Summary.** The core slice is mechanically correct and every A1–A6 disposition is present in the task text. The accessor's short-circuits, the D-10 recovery path and the E108 placement all match the live code they modify (`button_data.py:83-85`, `settings.py:98-132`, `checks.py:23-27`). The one thing that did not change with A19 is tooling: the plan declares a branch "authority" that the configured workflow will not honour.

**Strengths.**
- A1 is real, not cosmetic: the setting-level fallback returns `LABEL_MODE_DEFAULTS[location]` directly and only the stamp path calls the accessor, so recovery terminates at an immutable value. Combined with `button_data.py:83`'s `or`, an explicit valid stamp never evaluates a bad floor.
- A4 verified: `LABEL_MODES` is imported at `button_data.py:8` and used only at `:85`; moving that error into `_invalid_label_mode` leaves it unused, and the scoped `ruff check` gate will catch a leftover F401.
- A3's three-level matrix is consistent with existing behaviour: falsey stamps (`None`, `""`, `[]`, `{}`) already fall through at `:83`; the existing strict test uses only truthy bad values (`test_button_data.py:121`). Goldens cannot move.
- A6 tracer keys match `test_button_leaves.py:490-499`, and the visible text will be the short label per `button_data.py:102-105`, so asserting "Detail" is correct.

**Concerns.**
- **LOW — A19 is documentation, not an incorporated fix.** `.planning/config.json` still has `git.branching_strategy: "phase"` with `phase_branch_template: "gsd/phase-{phase}-{slug}"`. The execute-phase workflow reads config, not plan prose, so execution will land on `gsd/phase-01-label-mode-defaults`, not `feat/label-mode-defaults` as `PROJECT.md:77` and the plan's execution_context claim. Recoverable (rename, or `gsd-pr-branch`), but the ledger marks it addressed when it is only asserted. `01-RESEARCH.md:463` still says the opposite ("keep `introduce-gsd`").
- **LOW — subprocess boundary test premise unverified by execution.** `check_messages` (`settings.py:195-223`) also imports `crud_views.lib.check` and `crud_views.lib.breadcrumb` after `_action_settings_messages`. From source these have no app-registry dependency and the child runs after `django.setup()`, so the test should pass, but I could not run the child here. If it trips, the fix is in the test fixture, not production.
- **LOW — dedup collapses two different problems.** Keying `(location, repr(value))` without a source dimension means a bad setting `"nope"` and a bad stamped `"nope"` for the same location log once between them. This is the plan's explicit reading of D-11; acceptable, but the single warning's text must then be generic enough not to mislead (the plan already includes `source` in the message, which is fine).
- **LOW — accepted over-engineering.** `_warned_lock` plus a per-case subprocess deadlock test survives from round 1 by explicit decision. With the fallback resolved before lock acquisition, re-entrancy is impossible by construction, so the test guards a path that cannot occur. Not re-raised; noted as cost.

**Suggestions.**
- Either change `phase_branch_template` in config or drop the override claim and let `gsd-pr-branch` produce the `feat/` branch at ship time. Pick one and say so in STATE.md.
- In the autouse fixture, assert `_warned` is referenced as a module global by `_invalid_label_mode` (a one-line test that monkeypatching changes behaviour), otherwise a future refactor to a closure silently breaks isolation.

**Risk: LOW.** No source claim in the ledger was wrong; residual risk is process (branch) and one unexecuted test premise.

## 01-02

**Summary.** The toolbar/row integration is the smallest change surface and A7/A8 are grounded in real mechanisms. The Pitfall-2 fix is correctly scoped. EDGE-LMOD-02 can be closed: the whole-tree scan confirms the consumer set.

**Strengths.**
- A7 trace is correct end to end: `base.py:435` puts the raw `cv_context_action_label_mode` into the dict, `base.py:631` hands it unsanitized to the resolver, `:312` returns it, and `button_data.py:84` is the first validator. Only `buttons.py:400-403` sanitizes, and only at check time. Two GETs with one captured warning is exactly what the D-10 path produces.
- Pitfall 2 is real and the fix is minimal: `checks.py:23-27` builds settings messages then iterates `ViewSet.checks_all()` in the same function, so an uncaught `ValueError` from `buttons.py:405` discards E108. Wrapping only that call preserves every other message.
- A8's selector matches `context_action_filter.html:3-4` (`id="cv-filter-toggle"`, `cv-key="{{ cv_key }}"`, hard-coded `"icon"` class slot), and the nonempty-remainder assertion stops the test passing vacuously.
- The membership branch for `:317` is necessary: `dict.get(key, default_label_mode("list"))` would evaluate the accessor and could raise in strict mode even for mapped keys.

**Concerns.**
- **LOW — EDGE-LMOD-02 is resolvable now; the plan leaves it flagged.** A scan of all five packages (`.py` and `.html`) for `"both" if`, `or "icon"`, `get(key, "icon")` and `cv_card_actions_label_mode` returns only `button_data.py:83`, `base.py:312`, `base.py:317`, `views/card.py:28/52/112`, plus comments at `action_menu.py:59` and `view/card.py:12`. No extension app reads the card attribute or hardcodes a floor. The consumer set is complete; the plan should record this rather than carry the flag to verification.
- **LOW — A9 duplication accepted.** Pinning "string or None" in `action_menu.py`, `action_menus.md` and `buttons.md` is a three-surface coupling by choice. Fine, but a future wording tweak will fail three tests at once; the ledger says as much.

**Suggestions.**
- Replace the "Flagged assumptions" paragraph with the grep result above and mark EDGE-LMOD-02 resolved.
- In the W292 integration test, also assert the message count for E108 equals one for `{"context": "nope"}` so a future change that reports it twice (check plus render) is caught.

**Risk: LOW.** Disjoint files from 01-03, mechanisms verified, no incorrect claims.

## 01-03

**Summary.** The card slice is small and R3/A10–A12 are correctly grounded. The test-app fixture really does exercise the D-18 exception, and the wave-2 doc links target anchors that exist today. The verification script is sound for the current CHANGELOG, with one self-detecting fragility.

**Strengths.**
- R3 is correctly targeted: `tests/test1/app/views.py:75-79` defines `detail` ("Details"), `update` ("Edit") and `delete` with `no_label=True`. Under `{"card": "label"}` the first two go text-only and delete stays icon-only through `views/card.py:49-50`. Using `_card` with the stock view (not `_author_card`, which monkeypatches actions at `test_card_label_mode_render.py:62-64`) is the right call.
- A10 anchors exist: `action_menus.md:58` (`## Label mode`), `settings.md:71` (`## Action menus`), `card-list-view.md:57`. `mkdocs.yml:24-25` has `validation: anchors: warn`, so `--strict` would fail on a forward link; running the strict build here is justified.
- A12 confirmed at `card-list-view.md:50`: the `label_mode` row says "inherits the view's `cv_card_actions_label_mode`", which becomes wrong once the attribute is `None`.
- The verification script's section regex splits only on `^## ` / `^### `, nested sub-bullets (e.g. `CHANGELOG.md:287`) fold into their parent, and `(#213)` appears once in each target (`CHANGELOG.md:43`, `migrating-1.0.md:127`).

**Concerns.**
- **LOW — new bullets must not contain the literal `(#213)`.** The script asserts exactly one `(#213)` bullet per target. If the new "Card label-mode attribute" bullet cross-references #213 (natural, since it explains the same change), the gate fails. Self-detecting, but the task text should say so.
- **LOW — `test_good_values_yield_no_check` extension needs the E210 guard first.** `test_card_label_modes.py:46-48` loops `monkeypatch.setattr(...)`; adding `None` to the tuple only passes once `views/card.py:112` is conditional. The task does both in one slice, so ordering inside the task matters for TDD red/green but not for the outcome.

**Suggestions.**
- Add to 01-03-02: "neither new bullet may contain `(#213)`".
- The acceptance note should state the Tabler result already known from research (`01-RESEARCH.md:240`: no template reads the attribute), so the downstream audit is a confirmation, not a search.

**Risk: LOW.** Small code change, docs discipline fixed, prohibition correctly carried as unverified.

## 01-04

**Summary.** The docs and gate plan incorporates A13–A18 correctly. The permanent test no longer reads `.planning/`, the changelog selector is release-name independent, and the protected-path gates have a verified baseline. The remaining concerns are about what the gates assume rather than what they check.

**Strengths.**
- A13 verified: no permanent test references `.planning/`; D-23 is a one-off grep. `PROJECT.md:96-97` rows exist and the grep for "removed in 1.0.0" in row 97 is an intended red state the task must turn green.
- A15 verified against structure: `CHANGELOG.md` has `## Unreleased`:3, `### Breaking`:7, `### Fixed`:136, `### Added`:167, and a second `### Breaking`:282 under 0.30.0. Selecting the release via the stable bullet avoids both the heading rename and the older Breaking section.
- A16/R8 verified: `ebc7c23` is "docs(01): capture phase context" and its protected-path diff is empty today; `git status --porcelain` on those paths is also empty. Both gates start green.
- A17 verified: `action_menus.md:238` is two-column (ID / Meaning); `buttons.md:437` has a Level column. Putting "error" in the Meaning cell is the right accommodation.
- R9 tracer is sound: `cv_button` (`templatetags/crud_views.py:200-208`) routes through `cv_resolve_action` (`visibility.py:14`), which hides anything without `cv_access=True`; the card path takes `cv_label` and needs no `cv_oid` for an `a` tag.

**Concerns.**
- **LOW — `settings.md` row scan is only as good as its negative phrase.** The acceptance says the context-map row "must not contain `keys not named are \`icon\``" (live text at `settings.md:78`). A rewrite that keeps the idea in different words passes the gate while still being stale. Pair the negative with a positive: the row must name the target-view step and `CRUD_VIEWS_LABEL_MODE_DEFAULTS`.
- **LOW — EDGE-LMOD-04 can be closed.** Nothing caches the merged value; the only persistent state is `_warned`, which is process-lifetime by decision and reset per test by the autouse fixture. Nested `override_settings` enter/exit is covered by 01-01's tests. There is no further lifecycle case; the flag should be resolved, not carried.
- **LOW — vitest gate runs unchanged JS.** Harmless, but the plan should say the gate is a regression guard, not evidence for this phase.

**Suggestions.**
- Resolve both unclassified edges in the final summary with the evidence above instead of carrying them.
- Add the positive assertion to `test_label_mode_configuration_table`.

**Risk: LOW–MEDIUM.** Medium only because this plan carries every full-suite gate and the branch-name question surfaces here at PR time.

## Cross-plan assessment

**Dispositions A1–A19:** 18 are incorporated as described. A19 is asserted in plan text but not enforced; `config.json` still drives the opposite branch name. No cycle-2 fix introduced a regression in another plan.

**New issues this cycle:** the config/plan branch mismatch (LOW), the `(#213)` token fragility in 01-03-02's gate (LOW), and two unclassified edges that the source now allows you to close (LOW).

**Dependency order** is sound: 01-02 and 01-03 share no files; 01-04 retargets links only after 01-04-01 creates the anchors; 01-03 links only to anchors that exist today.

**Phase goal:** achieved by the plans as written. Every literal the acceptance grep names (`button_data.py:83`, `base.py:312`, `:317`) has a specific replacement, the card attribute change is disclosed in both required surfaces, E108 survives strict mode through the W292 guard, and goldens are protected by two gates against a verified baseline.

**Overall risk: LOW.** No HIGH or MEDIUM findings remain. The phase can proceed to execution. Before it does, decide the branch question once and record it in STATE.md, because the plans and the tooling currently disagree.

---

## Consensus Summary

Three reviewers ran: opencode-gemini, opencode-grok and claude-fable. All three worked from the source and cited `file:line` evidence. None carries a discount marker. All three covered every plan id (01-01 to 01-04). This cycle opencode-grok completed on its **first attempt** (no ETIMEDOUT), so no retry was needed and `.planning/config.json` was never modified. Its SHA-256 is unchanged at `95c21cfe…`.

**No reviewer raised a HIGH or MEDIUM concern.** Overall risk: gemini LOW, grok LOW, claude LOW (claude rates 01-04 LOW–MEDIUM only because it carries the full-suite gates). All three independently confirm that A1–A19 are present in the plan text and grounded in live source. claude qualifies A19 (see B3). No reviewer found a wrong mechanism or a regression introduced by the `bdd445c` revisions.

### Cycle-2 findings: resolution status

| Cycle-2 concern | Plan(s) | Status in cycle 3 |
|---|---|---|
| A1 setting fallback must not recurse | 01-01-01 | Resolved (all three). |
| A2 child-process log capture | 01-01-01 | Resolved. `assertLogs` is used in the child (gemini). |
| A3 bad-value levels split | 01-01-01 | Resolved (gemini, claude). |
| A4 unused `LABEL_MODES` import | 01-01-01 | Resolved, with a scoped ruff gate (all three). |
| A5 non-dict warning fanout 1/2/3 | 01-01-01 | Resolved (gemini). |
| A6 context tracer raw keys | 01-01-01 | Resolved (all three). |
| A7 invalid target mode render test | 01-02-01 | Resolved (all three). |
| A8 filter toggle selector | 01-02-01 | Resolved (all three). |
| A9 `"string or None"` pinned three times | 01-02-02, 01-04 | Explicitly accepted in the plans (all three). |
| A10 existing-anchor discipline and retargeting | 01-03-02, 01-04 | Resolved (all three). |
| A11 wave-2 verify script strength | 01-03-02 | Resolved. claude flags the `(#213)` token fragility (B4). |
| A12 `card-list-view.md:50` row | 01-03-01 | Resolved (all three). |
| A13 no `.planning/` reads in permanent tests | 01-04-02 | Resolved (all three). |
| A14 fence prefilter | 01-04-01 | Resolved (gemini). |
| A15 release-name-independent selector | 01-04-02 | Resolved (all three). |
| A16 `git status --porcelain` gate | 01-04 verification | Resolved (all three). |
| A17 two-column `action_menus.md` table | 01-04-01 | Resolved (all three). |
| A18 bracket-free Mermaid label | 01-04-02 | Resolved (gemini, grok). |
| A19 single branch authority | all | Resolved in plan text. claude notes that config still drives the other branch name (B3). |

### Agreed Strengths
- All of A1–A19 are present in the plan text and grounded in live source (all three).
- A7 traces the real path end to end. `base.py:435`/`:631` passes the raw target mode, `:312` returns it, and `button_data.py:83-85` is the first validator (all three).
- The A8 selectors match `context_action_filter.html:4,10`, and a nonempty remainder is asserted (all three).
- The W292 guard is correctly scoped. `checks.py:23-28` collects E108 before it iterates `checks_all()` (all three).
- The membership branch for `base.py:317` avoids eager evaluation of the `dict.get` default (all three).
- The stock `AuthorCardListView` test keeps the D-18 `no_label` exception visible (all three).
- The protected-path gates start green against the verified baseline `ebc7c23` (claude, grok).

### Agreed Concerns
None. No concern was raised by two or more reviewers this cycle. Every new item below is single-reviewer and LOW.

### Divergent Views
- **Single-reviewer items** (all LOW and actionable unless marked otherwise):
  - **B1** gemini (existence; **confirmed by source-grounding**): the Greek-omicron literal `"bοth"` in the new test matrices (01-01, 01-03) triggers ruff `RUF001`. `pyproject.toml` selects `RUF` and allows only `›` as a confusable, and `tests/**` ignores only `RUF012`. A probe `ruff check` on a file holding `"bοth"` reports `RUF001`. The scoped 01-01-01 ruff gate covers only `src/`, so the failure would first appear at the 01-04 repo-wide gate.
  - **B2** grok (judgment): `01-01-PLAN.md:122` says "Non-dict settings use the same strict/non-strict policy as invalid location values". Read literally, this conflicts with D-12 and the behaviour block (an unknown caller location always raises). It should say "invalid per-location mode values".
  - **B3** claude (judgment): A19 is asserted, not enforced. `.planning/config.json` keeps `branching_strategy: "phase"` with `gsd/phase-{phase}-{slug}`, so execute-phase will create `gsd/phase-01-label-mode-defaults`, not `feat/label-mode-defaults`. The plans should state the concrete mechanism, for example a pre-execution check that `HEAD` is `feat/label-mode-defaults`, or a `gsd-pr-branch` rename at ship time, recorded in STATE.md. Because the config carries the user's uncommitted edits, the fix belongs in plan or STATE text, not in a config commit.
  - **B4** claude (judgment): the 01-03-02 verify script requires exactly one `(#213)` bullet per target. The new "Card label-mode attribute" bullet must therefore not contain the literal `(#213)`. The task text should say so.
  - **B5** grok (existence; **confirmed**): `CHANGELOG.md:173-177` (Unreleased #269 bullet) still says the target-view mode "is the last fallback before `"icon"`". Neither 01-03-02 nor 01-04-02 names this bullet.
  - **B6** grok (existence; **confirmed**): the leaf-contract `cv_label_mode` cell at `docs/reference/buttons.md:331` says context/list mode is `"icon"` unless a map, a button or the target view says otherwise. 01-04-02 edits only the card paragraph and the checks table. Source-grounding also found `buttons.md:52` ("toolbar and row buttons are `icon`"). That line sits in the class-key grammar section, which 01-04-02 reserves for Phase 2. Either name it as a one-phrase floor fix that is explicitly outside the grammar change, or defer it to Phase 2 explicitly.
  - claude, **not counted (already incorporated):** the `settings.md` context row needs a positive assertion. `01-04-PLAN.md:108` and the acceptance at `:131` already require the replacement to name the target-view step and the configured floor.
  - gemini, **not counted (already incorporated):** split the docs-test functions across 01-04-01 and 01-04-02. `01-04-PLAN.md:116` ("add diagram/remaining-reference assertions in 01-04-02") and the A10 note (CHANGELOG retargeting is not expected in 01-04-01) already stage them.
  - claude, **not counted (accepted decisions or informational):** a single dedup entry covers both setting and stamp (D-11, accepted); `_warned_lock` cost (rejected in round 1); A9 coupling (accepted); TDD ordering inside 01-03-01; the vitest gate being a regression guard only; optional suggestions (a module-global `_warned` self-test, an E108 count of one).
  - claude, **reviewer confirmation for the flagged edges (no plan change required):** claude's whole-tree scan confirms that the EDGE-LMOD-02 consumer set is complete. claude also finds no further EDGE-LMOD-04 lifecycle case. The plans deliberately carry these rows to verification ("never auto-dismiss"), and this confirmation is evidence for that step.
  - claude, **open premise now verified by source-grounding:** claude could not run the R6 subprocess premise. A fresh-interpreter probe ran: `settings.configure(...)` → `import crud_views.lib.settings` → `django.setup()` → `check_messages`. It raises no `AppRegistryNotReady`, `crud_views.lib.view` and `button_data` are absent throughout today, and only `crud_views.E100` is returned. The test is therefore red before E108's deferred `LOCATIONS` import and green after it, as designed.

---

## Verification coverage

**Source-grounding pass** (`plan_review.source_grounding: true`). `gsd_run drift-guard authority --raw` returns **`intel`** (config names `grep`, but `intel.enabled: true` takes precedence). `.planning/intel/API-SURFACE.md` has no entries, and every cited symbol is Python. Under the effective authority every symbol is therefore **UNCHECKABLE → INFO, hardBlock false** (`drift-guard severity --status UNCHECKABLE --authority intel` → `{"severity":"INFO","hardBlock":false}`). UNCHECKABLE is not counted as verified. As supplementary evidence, each symbol below was resolved with grep, ruff or a Python probe against tracked source. No MISSING or AMBIGUOUS symbol was found.

Excluded as "Artifacts this phase produces": `LABEL_MODE_DEFAULTS`, `default_label_mode`, `_UNSET`, `_raw_label_mode_defaults`, `logger`, `_warned`, `_warned_lock`, `_invalid_label_mode`, `crud_views.E108`, `CardListView.cv_get_card_actions_label_mode`, `isolate_label_mode_warnings`, `test_settings_defers_button_data_until_checks`, `test_invalid_stamp_and_floor_recovers_without_deadlock`, `test_invalid_target_mode_renders_configured_floor`, `tests/test1/test_label_mode_docs.py` and its test functions, every other listed new test, and the four new doc anchors.

The symbols from cycles 1 and 2 are unchanged since `bbbf16a` (no `src/`, `tests/` or `docs/` commits since then) and were re-confirmed by grep. The table below lists symbols newly cited by the `bdd445c` revisions or by cycle-3 findings:

| Symbol (kind) | Cited by | Authority verdict | Supplementary evidence |
|---|---|---|---|
| Raw tracer keys `cv_action_label`, `cv_icon_action`, `cv_list_action_method`, `cv_oid`, `cv_access`, `cv_url` | 01-01-01 (A6) | UNCHECKABLE | `tests/test1/test_button_leaves.py:490-499` |
| `cv_action_short_label` (context short label) | 01-01-01 (A6) | UNCHECKABLE | `button_data.py:80-81`; becomes visible text at `:102-105` |
| `LABEL_MODES` import / sole use | 01-01-01 (A4) | UNCHECKABLE | `button_data.py:8`, `:85` |
| `unittest.TestCase().assertLogs` | 01-01-01 (A2) | UNCHECKABLE (stdlib) | standard library |
| `id="cv-filter-toggle"`, `cv-key="{{ cv_key }}"` | 01-02-01 (A8) | UNCHECKABLE (template) | `src/crud_views/templates/crud_views/tags/context_action_filter.html:4,10` |
| `base.py:631` raw target default | 01-02-01 (A7) | UNCHECKABLE | `base.py:631` |
| CHANGELOG structure for the 01-03-02 regex script | 01-03-02 (A11) | UNCHECKABLE | First `## ` is `Unreleased` (:3). Its subsections are Breaking/Removed/Changed/Fixed/Added/Internal, each unique. `(#213)` occurs once in Breaking (:43) and once in `migrating-1.0.md:127`. Dry run: the script parses today's tree and fails on the missing setting-first token (intended red). |
| Link targets `reference/settings.md#action-menus`, `reference/action_menus.md#label-mode` (and the `docs/`-prefixed forms from CHANGELOG) | 01-03-02 (A10) | UNCHECKABLE (doc anchors) | `docs/reference/settings.md:71`, `docs/reference/action_menus.md:58` |
| `PROJECT.md` decision rows for the one-off grep | 01-04-02 (A13) | UNCHECKABLE | `.planning/PROJECT.md:96-97`. Row 97 lacks "removed in 1.0.0" today, which is the intended red state. |
| `git status --porcelain -- tests/test1/golden src/crud_views/templates examples` | 01-04 (A16) | UNCHECKABLE (git) | empty output today |
| Ruff `RUF001` on the `"bοth"` literal | B1 | UNCHECKABLE (lint rule) | `pyproject.toml` `select` includes `RUF`, `allowed-confusables = ["›"]`, `tests/**` ignores only `RUF012`. The probe `ruff check` reports `RUF001 String contains ambiguous ο`. No existing file under `tests/` or `src/` contains U+03BF. |
| `CHANGELOG.md` #269 "last fallback before `"icon"`" | B5 | UNCHECKABLE | `CHANGELOG.md:175` |
| `buttons.md` leaf-contract `cv_label_mode` cell | B6 | UNCHECKABLE | `docs/reference/buttons.md:331`; also `:52` (class-key section) |
| D-07 boundary premise (R6 test) | claude (open) | UNCHECKABLE | Probe after `settings.configure`, import and `django.setup()`, then `check_messages`: no view module loaded, returns `[crud_views.E100]` |
| Function signatures | all | UNCHECKABLE | cannot be asserted under grep/intel |

**Cross-artifact fact-drift pass** (advisory, never counted):
- Phase status: `gsd_run drift-guard phase-status --phase 01` → `verdict: lag` (STATE.md "Ready to execute" vs ROADMAP.md "Not started"). Lag is not a finding.
- ROADMAP Success Criteria ↔ PLAN `must_haves.truths`: no contradiction.
- ROADMAP requirements (LMOD-01…06) ↔ plan `requirements:`: the union covers all six, with no contradiction.
- CONTEXT.md Decisions ↔ PLAN term usage: one possible wording contradiction. The `01-01-PLAN.md:122` sentence on non-dict settings sits next to D-12 (unknown location always raises). This is the same item as B2. It is advisory here and counted once, in the actionable list.
- Advisory, not a judgment pair: branch naming. `.planning/config.json` (`gsd/phase-{phase}-{slug}`) disagrees with the plans' A19 authority (`feat/label-mode-defaults`). This is the same item as B3. `01-RESEARCH.md:463` still recommends the current branch, and 01-01's execution_context explicitly supersedes it.
- Nothing was skipped: STATE.md, ROADMAP.md and CONTEXT.md were present.

**Lane diagnostics:** all three lanes succeeded on their first attempt: gemini 18:32→18:38, claude 18:38→18:46 and grok 18:46→18:54 local time. Their `.err` captures are empty. Plan coverage is complete for all three graded lanes (4/4 ids each), so the `plan_coverage` frontmatter key is omitted. No lane was trimmed, so `trimmed_reviewers` is omitted.

## Current HIGH Concerns

None.

## Current Actionable Non-HIGH Concerns

- **B1 [LOW] 01-01-01, 01-03-01** (gemini; confirmed by source-grounding): write the Greek-omicron case as `"b\u03bfth"` (or add `# noqa: RUF001`) in the new test matrices, and add the touched test files to 01-01-01's scoped ruff gate.
- **B2 [LOW] 01-01-01** (grok): reword `01-01-PLAN.md:122` to "the same strict/non-strict policy as invalid per-location mode values". Unknown caller locations still raise in every mode (D-12).
- **B3 [LOW] cross-plan** (claude): give A19 a concrete mechanism. Config still selects `gsd/phase-…`. Add a pre-execution assertion that `HEAD` is `feat/label-mode-defaults`, or state that `gsd-pr-branch` or a rename produces it at ship time, and record the choice in STATE.md. Do not change the config.
- **B4 [LOW] 01-03-02** (claude): state that the new "Card label-mode attribute" bullets must not contain the literal `(#213)`, because the verify script requires exactly one `(#213)` bullet per target.
- **B5 [LOW] 01-03-02 or 01-04-02** (grok; confirmed): update the Unreleased #269 bullet at `CHANGELOG.md:175` ("last fallback before `"icon"`") so that it names the configurable context floor, and assert it in the docs test.
- **B6 [LOW] 01-04-02** (grok; confirmed): replace the old-floor parenthetical in the `buttons.md:331` leaf-contract cell with links to `#context-label-mode-resolution` / `#list-label-mode-resolution`. Either fix `buttons.md:52` ("toolbar and row buttons are `icon`") as a phrase-only floor correction, or explicitly defer it to Phase 2's class-key section.
