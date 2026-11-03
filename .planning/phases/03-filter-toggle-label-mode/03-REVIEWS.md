---
phase: 03
cycle: 3
reviewers: [fable-review, grok-review, gemini-review, deepseek-review]
reviewed_at: 2026-10-26T15:29:16.545850+00:00
plans_reviewed: [03-01-PLAN.md, 03-02-PLAN.md]
models:
  fable-review: "claude-fable-5-1 (reasoning=high)"
  grok-review: "openrouter/x-ai/grok-4.7 (reasoning=high)"
  gemini-review: "openrouter/google/gemini-4-argon (reasoning=high)"
  deepseek-review: "openrouter/deepseek/deepseek-v3.2 (reasoning=high)"
model_sources:
  fable-review: "pinned"
  grok-review: "pinned"
  gemini-review: "pinned"
  deepseek-review: "pinned"
---

# Cross-AI Plan Review — Phase 03

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts

None.
<!-- gsd:plan-revision-conflicts:end -->

> Note: grok-review, gemini-review and deepseek-review share the opencode adapter; their consensus is cross-model, not cross-tool.

Cycle 3 reviewed final plans at `d632410`. All four configured instances completed successfully through `review-lane invoke`, with no retries and no trimming. [Cycle 1](.review-history/03-REVIEWS-cycle1.md) and [Cycle 2](.review-history/03-REVIEWS-cycle2.md), including their source audits, are preserved byte-for-byte; their unresolved counts are historical. The fixed conflict slot above is unchanged.

Coverage: fable-review complete, grok-review complete, gemini-review complete, deepseek-review complete.

## Claude Review (fable-review)

# Cross-AI Plan Review — Cycle 3 (plans at `d632410`)

Scope: independent closure check of C2-A1 and C2-A2 against source, plus a final correctness pass over both plans. Repo read at HEAD `d632410`; no files edited, no product suites run.

## 03-01

**Summary.** The plan is executable as written. Every mechanism it relies on exists in source at the cited location: the resolver precedence (`src/crud_views/lib/view/base.py:312-322`), the builder's seed-then-hooks order (`src/crud_views/lib/view/buttons.py:323-332`), the wrapper restamp it chooses to leave alone (`base.py:640-646`), the icon-less-tolerant JS loop (`src/crud_views/static/crud_views/js/list.filter.js:29`), and the collapse-first/ignore-rejection ordering (`list.filter.js:15-18,33-38`). The two cycle-2 findings are closed. Three low-severity items remain, none blocking.

**C2-A1 closure — CONFIRMED from source.** The four validation paths Task 2 now distinguishes are genuinely different code paths:
- Button `viewset.E210`: `buttons.py:360-361` yields `label_mode_check` for a non-None `label_mode`, and this runs *before* the `if button in defaults: continue` at line 362, so a `FilterContextButton(label_mode="bogus")` is reported. `ContextButton.label_mode` is an unvalidated `str | None` (`buttons.py:33`), so construction succeeds and the check fires.
- View `viewset.E211`: `src/crud_views/lib/view/action_menu.py:46-62`, reads the class attribute via `getattr(cls, attribute)`, so monkeypatching the view class is the correct way to trigger it.
- Settings `crud_views.E106`: `src/crud_views/lib/settings.py:129-135`; the existing assertion shape at `tests/test1/test_action_label_mode_config.py:46-49` matches the plan.
- ViewSet construction: `src/crud_views/lib/viewset/__init__.py:105-111` is a `@field_validator` raising `ValueError`, surfaced as `pydantic.ValidationError`; the pattern at `tests/test1/test_action_label_mode_config.py:56-60` is exactly what Task 2 cites. The plan's warning that monkeypatching a built ViewSet does not produce E211 is correct: E211 checks the *view* attribute, not the ViewSet field.

**Strengths.**
- **Raw-byte baseline is justified, not ceremonial.** `tests/test1/test_action_menus_golden.py:38-55` sorts attributes and class tokens and collapses whitespace, so the normalized `toolbar_publisher_list.html` golden cannot detect a whitespace or attribute-order change. The template's layout (`context_action_filter.html:9-10`, where `{% endif %}cv-key=` sits mid-line inside an `{% if %}`) makes accidental whitespace drift likely when adding branches.
- **Snapshot vs lazy distinction is correct.** `settings.py:67` reads `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` into a module-level instance (`settings.py:320`), so `override_settings` cannot change it; `monkeypatch.setattr(crud_views_settings, ...)` is an established pattern (`tests/test1/test_action_label_mode_render.py:282`, `test_action_menus_config.py:59-64`). The floor is read per call (`label_mode.py:55-58`), so `override_settings` works there. The class-table cache reset on `setting_changed` exists (`button_classes.py:111-113`).
- **Existing tests the plan touches are what it says they are.** `tests/test1/test_context_action_label_mode.py:250` carries the obsolete "fixed mode (Phase 3)" comment and the filter-excluding XPath; `tests/test1/test_button_leaves.py:574-576` is the mode-less helper the plan keeps as a compatibility assertion.
- **Strict/warn isolation is in place.** Tests run with `CRUD_VIEWS_STRICT=True` (`conftest.py:41`), `is_strict()` reads lazily (`exceptions.py:32-36`), and `_warned` is reset per test (`conftest.py:32`), so the strict/non-strict floor cases are testable without leakage.
- **Localization evidence design holds.** No catalog currently contains `msgid "Filter"` (grep across `src/*/locale/de`), `polib` is a test dependency (`pyproject.toml:81`), `USE_I18N=True` with `en-us` default (`conftest.py:98-100`), and `msgfmt` is present. The existing `test_filter_button_default_label` (`test_context_button_template.py:53-57`) keeps passing under either eager or lazy gettext.
- **JS scope claim verified.** The current fixture (`tests/js/list.filter.test.js:5-20`) hardcodes two icon spans and no visible label; `hostFixture` (23-33) has a hidden label only. So "test-only, extend fixtures" is accurate, and the handler needs no change for label mode: no `data-cv-filter-icon-open` means the `else` branch with an empty NodeList.

**Concerns.**
- **LOW — Escaping test could be written against the wrong input.** `CrudView.render_snippet` returns `mark_safe(result.strip())` (`base.py:371`), so any `label_template` / `label_template_code` output is trusted markup by design. Task 2 says "ordinary raw labels stay escaped" and T-03-01 says "asserts HTML-like labels remain text". If the executor tests `label_template_code="<b>x</b>"` expecting escaped output, the test fails and could prompt an unwanted "fix". The plan does say "without altering the trusted-template boundary", but the escaping assertion target is not named.
- **LOW — PATTERNS.md and PLAN disagree on the translation import.** `03-PATTERNS.md:43-46` recommends reusing `gettext_lazy as _` from `base.py:26`; Task 1 specifies `django.utils.translation.gettext as _`. The plan's choice is the better one for the Task 3 sentinel test (patching the module-level callable and asserting it runs inside `get_context`), but an executor reading PATTERNS first may pick lazy.
- **LOW / open question — TDD gate vs passing baseline commit.** Task 1 is `type="tracer" tdd="true"` and prescribes committing a *passing* baseline module before writing the failing tracer test. The execute-plan workflow states "RED must fail". I could not read `gsd-core/references/tdd.md` in this session (permission), so I cannot say whether the gate inspects only the RED commit or the first `test(...)` commit. If the latter, the baseline commit trips it.

**Suggestions.**
- In Task 2, state the escaping assertion explicitly: render the leaf with `cv_action_label="<b>"` in the direct template context and assert `&lt;b&gt;`; do not route it through `label_template_code`, which is trusted by `render_snippet`.
- Add one sentence to Task 1 noting that `gettext` (eager) is intentional over `gettext_lazy`, superseding PATTERNS.md.
- Label the baseline commit as characterization work outside the RED/GREEN cycle (e.g. `test(03-01): raw filter baseline (characterization)`) so a TDD gate that checks commit sequence does not misread it as a non-failing RED.

**Risk: LOW.** All referenced files, helpers, settings and fixtures exist; every verify path in Task 2's command exists (checked by `ls`); the tracer verify has only `<automated>` checks so no mid-flight checkpoint is synthesized.

## 03-02

**Summary.** The documentation plan targets exactly the stale passages that exist today, the doc test it must change is the one it names, and C2-A2 is closed. No blocking findings; one low note on tooling paths.

**C2-A2 closure — CONFIRMED from source.** `docs/migrating-1.0.md:331-339` is the bullet "**The filter toggle** (`tags/context_action_filter.html`)" describing the two-span/host-class instructions unconditionally. Task 3 now owns this paragraph in addition to the checklist, with resolved-`cv_label_mode`, icon-bearing-only qualification, and the required `aria-expanded`/`aria-controls`/`#filter-collapse` retained. The acceptance criteria and must-have truths both cover the detailed contract and the checklist.

**Strengths.**
- **Every stale passage the plan names is real.** `context_buttons.md:81-82` ("icon-only by construction ... the way the bundled ... does"); `context_buttons.md:248` CUSTOM node ("nothing below applies (e.g. the filter toggle)"); `buttons.md:220-221` (host fallback stated unconditionally); `buttons.md:304-306` ("passes `"icon"`"); `action_menus.md:171-172` ("outside this configuration: neither the maps nor ... change it"); `javascript.md:83` (tooltip row); `javascript.md:187-199`; `icons.md:72-73,174-176`.
- **H1 remains closed.** `tests/test1/test_label_mode_docs.py:236-238` asserts `"outside this configuration" in rendering`; Task 1 owns the file and replaces that assertion while keeping the MICON/first-paragraph checks at 277-287, which are intact in source.
- **Import path correction is accurate.** `src/crud_views/lib/view/__init__.py` exports `ContextButton`, `ParentContextButton`, `ChildContextButton`, `SiblingContextButton` but not `FilterContextButton`; `context_buttons.md:505` shows only the former. The plan's "show the real import, add no export" is the right scope call.
- **Fixed classification is defensible.** The change makes previously ignored configuration take effect while default output is byte-protected by 03-01; the plan explicitly names the already-configured-floor effect and reserves Breaking for a real break discovered in execution, consistent with `CLAUDE.md:105`.
- **Link targets exist.** `action_menus.md#context-label-mode-resolution` is already asserted present in `context_buttons.md` by the doc test at 262-265, and `javascript.md:187` has "The filter toggle contract".

**Concerns.**
- **LOW — Tooling path note only.** Task 3 read_first lists `settings_i18n.py`; it lives at repo root, while `taskfile.yaml` runs `compilemessages` from `src` with `PYTHONPATH=..`. Since 03-01 Task 3 compiles with `msgfmt` directly, this is informational, but an executor who follows the taskfile route must run it from `src`.

**Suggestions.**
- None required. Optionally, in Task 1 mention that the new `context_buttons.md` section must not introduce a heading whose slug collides with existing anchors, since `test_label_mode_reference_links_and_diagram` resolves anchors by slug (`test_label_mode_docs.py:255-266`).

**Risk: LOW.** Depends functionally on 03-01 (it reads the summary and the new test module); dependency is declared.

## Synthesis

- **C2-A1 and C2-A2 are closed in source and plan text.** The four validation paths are distinct code paths at the cited lines, and the migration guide's detailed filter contract is exactly where the plan says it is.
- **Nothing from cycles 1–2 is reopened.** A1's normalization rejection stands: the wrapper restamps at `base.py:643-645`, so builder-only normalization would indeed be overwritten. A11's retained wrapper behavior is accurate: `FilterContextButton` returns a truthy `{"cv_access": False}` dict, so the wrapper resolves a mode for hidden toggles.
- **Remaining items are three LOW notes on 03-01** (escaping test input, eager-vs-lazy gettext wording, TDD commit-order open question) and one informational note on 03-02. None changes behavior; each is a one-sentence clarification.
- **Overall risk: LOW.** Both plans are internally consistent, source-grounded, and bounded to the phase. The plans are ready for execution.

---

## OpenCode Review (grok-review)

I'll verify the two cycle-2 findings and the plans' source claims against the current code, then review both plans.
## 03-01

The plan matches the live filter path and closes C2-A1. Nothing in this phase is implemented yet: `FilterContextButton.get_context` still seeds a literal `"Filter"` and never stamps a mode (`src/crud_views/lib/view/buttons.py:323-332`), and `context_action_filter.html:3-13` still hard-codes `"icon"`, a title, and icon markup. The tasks describe that change, they do not claim it already exists.

**Strengths**
- Resolution matches `cv_get_action_label_mode` (`base.py:312-322`): own map entry, then `button.label_mode`, then the whole selected map (`cv_first_inline_keys`, `base.py:263-272`), then the floor only if `target_default` is omitted. Filter data never comes from `cv_get_dict`, so it does not carry `cv_context_label_mode` (`base.py:447`). Passing no target default therefore ignores the list view’s singular `cv_context_action_label_mode`.
- The wrapper restamp (`base.py:640-645`) is explicitly kept. Label templates see the builder stamp inside `get_context` (`buttons.py:55-72`); the leaf sees the wrapper stamp. For a registered button those agree. `cv_resolve_action` still hides `{"cv_access": False}` (`visibility.py:12-18`).
- Literal `"icon"` on the legacy branch is required. `get_button_class` does not treat an unknown mode as icon: a truthy missing mode key falls through to `location:slot` (`button_classes.py:144-147`). Mode-less `_filter_toggle` (`tests/test1/test_button_leaves.py:574-576`) depends on that.
- C2-A1 matches source. Button `label_mode` is `viewset.E210` via `context_button_checks` → `label_mode_check` (`buttons.py:360-361`, `label_mode.py:44-51`, `check.py:260`). The view map is `viewset.E211` via `cv_label_mode_checks` (`action_menu.py:46-62`, wired at `base.py:194`). Settings are `crud_views.E106` on a new `CrudViewsSettings` (`settings.py:128-141`; same assertion as `tests/test1/test_action_label_mode_config.py:45-47`). A ViewSet map fails in `check_label_mode_map` before `register` (`viewset/__init__.py:105-111`, `134-138`), which is the `ValidationError` at `test_action_label_mode_config.py:56-60`. Monkeypatching a built ViewSet is correctly rejected as a stand-in.
- `list.filter.js:15-38` already collapses first, no-ops an empty `[data-cv-filter-icon]` list, and POSTs `X-CSRFToken` plus boolean `filter_expanded` without rolling back on rejection. Leaving the script unchanged is justified. `msgid "Filter"` is absent from the German catalog (nearby entries are `"Apply Filter"` / `"Reset Filter"` only).

**Concerns**
- None. Cycle-2 C2-A1 is in the task body and acceptance criteria, and the four check paths are the ones the code actually uses.

**Suggestions**
- None that change scope. The raw `RAW_DEFAULT_FILTER` gate is the right guard: the toolbar golden sorts attributes and collapses whitespace (`tests/test1/test_action_menus_golden.py:38-55`), so it cannot prove icon-mode bytes.

**Risk Assessment**
- LOW. The remaining execution risk is template whitespace around the current 14-line leaf. The pre-change raw strings and the literal-`icon` fallback cover it.

## 03-02

The docs plan points at the sentences that are still wrong, and C2-A2 is closed as planned work, not as already-edited prose. `docs/migrating-1.0.md:331-339` still tells a copied filter template to always render two icon spans and `hidden`, and the checklist at line 399 still says a copy “shows no icon (0.29) or the wrong icon after the first click (0.30)”. Task 03-02-03 now revises both, keeps the historical icon guidance for icon-bearing modes, and keeps `aria-expanded`, `aria-controls`, and `#filter-collapse` for every mode.

**Strengths**
- Stale claims are the ones the tasks name: bundled filter “icon-only by construction” (`docs/reference/context_buttons.md:81-82`), CUSTOM node “nothing below applies” (`context_buttons.md:248`), filter “outside this configuration” (`docs/reference/action_menus.md:171-172`), hard-coded `"icon"` (`docs/reference/buttons.md:304-306`), and host fallback with no mode qualifier (`buttons.md:221`). `test_label_mode_docs.py:236-237` still requires that exclusion; task 03-02-01 owns that assertion, so the strict-docs plus pytest verify will not fail on the old string after the paired edit. MICON and the post-diagram paragraph (`test_label_mode_docs.py:276-286`) stay.
- `FilterContextButton` is not exported from `crud_views.lib.view` (`src/crud_views/lib/view/__init__.py:1-17`). The planned import `crud_views.lib.view.buttons` is the real path. Never-folded stays (`action_menus.md:182-184`) because the class sets its own template (`buttons.py:304-306`).
- Tooltip and icon pages still describe an always-present marker and a two-icon toggle (`docs/reference/javascript.md:83`, `195-199`; `docs/reference/icons.md:174-176`). Task 03-02-02 qualifies those by mode without inventing a JS change.
- Fixed, not Breaking, stays consistent with unchanged default bytes, and the entry is required to name an already-configured context floor. That matches `default_label_mode` being read only when no earlier map names the key (`label_mode.py:107-111`, `base.py:319-322`).

**Concerns**
- None. C2-A2 is an instruction to edit `migrating-1.0.md:331-339` and the checklist, with acceptance criteria on both. It is not done in the tree, and it should not be: this plan depends on 03-01.

**Suggestions**
- None. Adding another doc-pin for `javascript.md:83` would only duplicate the task text.

**Risk Assessment**
- LOW. Doc edits are reversible and gated by `mkdocs build --strict` plus the existing label-mode doc tests.

Cycle 2 is closed against source. C2-A1’s four ids are different mechanisms, and the plan tests each one. C2-A2’s detailed migration paragraph is in the executable task, not only the checklist. No new plan defect turned up in the resolver, leaf, script, checks, or docs the tasks cite. Phase 3 behavior is still planned, not present in the templates or catalog.

---

## OpenCode Review (gemini-review)

## 03-01

### 1. Summary

Plan `03-01` implements label-mode resolution, three-way presentation (`icon`, `both`, `label`), and German localization for the list filter toggle (`FilterContextButton` and `crud_views/tags/context_action_filter.html`) while leaving the production JavaScript handler (`src/crud_views/static/crud_views/js/list.filter.js`) untouched and adding targeted Python and Vitest regression suites. Independent verification against the repository at `d632410` confirms that Cycle 1 dispositions (`A1`–`A6`, `A11`) and Cycle 2 finding `C2-A1` (distinguishing button `viewset.E210`, view-map `viewset.E211`, settings `crud_views.E106`, and `ViewSet` constructor `pydantic.ValidationError`) are accurately incorporated into the task bodies, behavior specifications, and acceptance criteria. The plan is execution-ready with no remaining blocking defects.

### 2. Strengths

- **Closure of `C2-A1` across all four configuration validation layers:** Task `03-01-02` now matches the actual validation architecture in source:
  - Button-level `label_mode` is checked via `context_button_checks` (`src/crud_views/lib/view/buttons.py:360-361`) yielding `viewset.E210`.
  - View-level `cv_context_actions_label_mode` is checked via `cv_label_mode_checks` (`src/crud_views/lib/view/action_menu.py:46-62`) yielding `viewset.E211`.
  - Settings-level `context_actions_label_mode` is checked via `CrudViewsSettings._action_settings_messages` (`src/crud_views/lib/settings.py:100-135`) yielding `crud_views.E106` (matching `tests/test1/test_action_label_mode_config.py:43-49`).
  - `ViewSet(context_actions_label_mode=...)` is validated at construction time by `@field_validator` `ViewSet.check_label_mode_map` (`src/crud_views/lib/viewset/__init__.py:105-111`), raising `pydantic.ValidationError` (matching `tests/test1/test_action_label_mode_config.py:56-60`).
- **Exact resolver wiring and custom-label ordering:** In `FilterContextButton.get_context` (`src/crud_views/lib/view/buttons.py:308-334`), stamping `data["cv_label_mode"] = context.view.cv_get_action_label_mode("context", self.key, self)` and `data["cv_action_label"] = _("Filter")` before `self._apply_label(data, context)` (`buttons.py:330`) ensures custom `label_template` / `label_template_code` snippets (`buttons.py:55-60`) receive `cv_label_mode` while omitting `target_default` so `CrudView.cv_get_action_label_mode` (`src/crud_views/lib/view/base.py:312-322`) never reads the list view's singular `cv_context_action_label_mode`.
- **Byte-exact default protection:** Because `tests/test1/test_action_menus_golden.py:38-55` normalizes whitespace and sorts attributes/classes, Task `03-01-01` captures raw `render_to_string("crud_views/tags/context_action_filter.html", ...)` baselines (`RAW_DEFAULT_FILTER`) before editing `src/crud_views/templates/crud_views/tags/context_action_filter.html:1-14`, protecting both mode-less direct callers (`tests/test1/test_button_leaves.py:574-576`) and explicit `"icon"` renders.
- **Zero-churn JavaScript verification:** `src/crud_views/static/crud_views/js/list.filter.js:15-30` already runs `cv.adapters.collapse.toggle(panel)` before mutating `aria-expanded`, branches on `button.dataset.cvFilterIconOpen !== undefined`, and otherwise iterates `button.querySelectorAll("[data-cv-filter-icon]")` (a no-op when empty in `"label"` mode). Keeping `list.filter.js` untouched and extending `tests/js/list.filter.test.js:5-160` avoids unnecessary runtime risk.
- **Orthogonal i18n verification:** Since `"Filter"` is spelled identically in English and German, Task `03-01-03` separates `polib` PO verification (`tests/test1/test_i18n.py:65-74`), `gettext.GNUTranslations` MO key lookup (`test_i18n.py:76-82`), and a monkeypatched runtime `gettext` sentinel on `buttons.py`.

### 3. Concerns

- **LOW — Multiline attribute whitespace in `context_action_filter.html` when wrapping `title` and `data-cv-tooltip`:** In `src/crud_views/templates/crud_views/tags/context_action_filter.html:7-10`, `title="{{ cv_action_label }}"` and `data-cv-tooltip="context"` sit on separate indented lines before `{% if cv_open_class and cv_close_class %}`. When gating those two attributes to the legacy `"icon"` fallback branch (`cv_label_mode != "both" and cv_label_mode != "label"`), placing the `{% if %}` / `{% endif %}` tags carelessly around the line breaks or 3-space indentations will fail the `RAW_DEFAULT_FILTER` byte-equality assertion in Task `03-01-01`.

### 4. Suggestions

- In `src/crud_views/templates/crud_views/tags/context_action_filter.html:6-10`, place the opening conditional immediately before the newline+indent preceding `title=` (or immediately before `title=` while keeping the trailing newline+3-space indent inside the `icon` branch) so the rendered `"icon"` string preserves the exact newline and 3-space indentation sequence verified by `RAW_DEFAULT_FILTER`.

### 5. Risk Assessment

- **Risk Level: LOW**
- **Justification:** All mechanisms (`cv_get_action_label_mode`, `cv_button_class`, `cv_icon_class`, `cv_icon`, `list.filter.js`, and `gettext`) already exist in the codebase, default `icon` output is guarded by both raw string comparison and the toolbar golden, and all prior review findings (`A1`–`A6`, `A11`, `C2-A1`) are closed in the plan text.

---

## 03-02

### 1. Summary

Plan `03-02` updates the reference documentation (`context_buttons.md`, `action_menus.md`, `buttons.md`, `javascript.md`, `icons.md`), the executable documentation test suite (`tests/test1/test_label_mode_docs.py`), the migration guide (`docs/migrating-1.0.md`), and `CHANGELOG.md`, then runs the full project quality gates. Verification against source at `d632410` confirms that Cycle 1 findings (`H1`, `A7`–`A10`) and Cycle 2 finding `C2-A2` (updating the detailed filter-toggle migration contract at `docs/migrating-1.0.md:331-339` in addition to the checklist bullet at `docs/migrating-1.0.md:399-400`) are fully addressed in the plan's truths, artifacts, task actions, and acceptance criteria.

### 2. Strengths

- **Closure of `C2-A2` across both migration guide entry points:** Task `03-02-03` explicitly updates both the detailed contract bullet `- **The filter toggle** (\`tags/context_action_filter.html\`).` (`docs/migrating-1.0.md:331-339`) and the silent-breaks checklist item (`docs/migrating-1.0.md:399-400`), qualifying two-span/host-icon instructions to icon-bearing modes, documenting that `cv_label_mode` is now in context and `"label"` mode omits icon hooks, and linking the compact filter contract from both locations.
- **Alignment with `test_label_mode_docs.py` invariants (`H1` and `A7`):**
  - `tests/test1/test_label_mode_docs.py:236-238` currently asserts `"filter toggle" in rendering and "outside this configuration" in rendering` against `docs/reference/action_menus.md:171-172`; Task `03-02-01` pairs the prose update in `action_menus.md` with replacing that assertion in `test_label_mode_docs.py`.
  - `tests/test1/test_label_mode_docs.py:277-287` inspects the Mermaid diagram's `MICON` node (`docs/reference/context_buttons.md:258`) and the first paragraph immediately below the diagram (`context_buttons.md:317-325`); Task `03-02-01` places the new compact filter section after `context_buttons.md:77-82` (before `### Active state` at line 84) and updates only the `CUSTOM` node (`context_buttons.md:248`), preserving all tested `MICON` and first-paragraph invariants.
- **Verified import path (`A8`):** `src/crud_views/lib/view/__init__.py:1-17` exports `ContextButton`, `ParentContextButton`, `ChildContextButton`, and `SiblingContextButton`, but not `FilterContextButton` (defined in `src/crud_views/lib/view/buttons.py:298`). Task `03-02-01` documents `from crud_views.lib.view.buttons import FilterContextButton` in examples and `## Import Paths` (`docs/reference/context_buttons.md:502-507`) without expanding the public `__all__` surface.

### 3. Concerns

- **LOW — Adjacent host-placed icon note in `docs/migrating-1.0.md:324-326`:** Just above `- **The filter toggle**` (`docs/migrating-1.0.md:331-339`), the `- **Host-placed icons** (#258)` bullet (`docs/migrating-1.0.md:320-326`) states: *"A filter-toggle copy renders, for a host library, the current state's class on the button plus `data-cv-filter-icon-open` / `data-cv-filter-icon-close` instead of the two spans ([The filter toggle contract](reference/javascript.md#the-filter-toggle-contract))."* While not contradictory once `331-339` and `javascript.md#the-filter-toggle-contract` are updated, executors should ensure wording in `331-339` harmonizes cleanly with `324-326` (i.e., host classes and swap attributes apply when the filter toggle renders an icon in `icon` or `both` mode).

### 4. Suggestions

- When editing `docs/migrating-1.0.md:331-339` in Task `03-02-03`, keep the phrasing consistent with the adjacent host-icon sentence at `docs/migrating-1.0.md:324-326` so both bullets clearly point to `reference/javascript.md#the-filter-toggle-contract` for icon-bearing (`icon` / `both`) vs. icon-less (`label`) modes.

### 5. Risk Assessment

- **Risk Level: LOW**
- **Justification:** All documentation targets, anchor links, and `test_label_mode_docs.py` assertions have been verified against the live files, and both `H1` and `C2-A2` are completely specified.

---

## Cross-Plan Convergence Summary

Both `03-01` and `03-02` have converged cleanly at `d632410`:
- Cycle 2 findings `C2-A1` (in `03-01-02`) and `C2-A2` (in `03-02-03`) are verified closed against the live codebase (`buttons.py:360-361`, `action_menu.py:46-62`, `settings.py:100-135`, `viewset/__init__.py:105-111`, and `docs/migrating-1.0.md:331-339, 399-400`).
- All four phase requirements (`FILT-01` through `FILT-04`) and locked decisions (`D-01` through `D-11`) are covered without scope creep or unverified assumptions.
- The phase is ready for execution.

---

## OpenCode Review (deepseek-review)

I'll review the two plans for Phase 3 (Filter toggle label mode) by examining the actual codebase and comparing against the plans' claims.
Now let me check the golden test to understand the baseline:
Let me examine the current template more closely and check how label modes are handled:
Let me check the current test files to understand what exists:
Now let me check if there are any existing tests for filter toggle label mode:
Let me check the current documentation about filter label mode:
Let me also check the CHANGELOG to understand the current state:
Now let me examine the 03-01-PLAN.md more closely:
Now I have enough context to provide a structured review. Let me examine a few more key files to understand the current state:
Let me check if there's an existing test file for filter toggle label mode:
Now let me check the migration docs:
Now I have sufficient context to provide a comprehensive review. Based on my examination of the codebase and plans, here's my structured review:

## 03-01

**Summary**: This implementation plan correctly identifies the core issue: the filter toggle currently hard-codes icon mode (`cv_button_class "context" cv_variant|default:"secondary" "icon"` in line 3 of `context_action_filter.html`) and doesn't use the label mode resolver. The plan addresses all four requirements (FILT-01 through FILT-04) with a three-task approach: baseline capture, full implementation with edge cases, and translation handling.

**Strengths**:
- **Accurate analysis**: The plan correctly identifies that `FilterContextButton.get_context()` in `src/crud_views/lib/view/buttons.py:308-334` doesn't stamp `cv_label_mode` and seeds an untranslated `"Filter"` label.
- **Proper reuse**: Leverages existing `cv_get_action_label_mode()` resolver (`src/crud_views/lib/view/base.py:299-322`) with correct parameters `("context", self.key, self)` and no `target_default`.
- **Compatibility focus**: Task 1 emphasizes raw byte preservation with `RAW_DEFAULT_FILTER` baseline capture before implementation.
- **Comprehensive edge cases**: The 14 "truths" in `must_haves` cover resolution precedence, icon placement, JavaScript behavior, translation evidence, and customization.
- **Security awareness**: Maintains existing CSRF protection (`X-CSRFToken`) and POST/JSON contract.

**Concerns**:
- **HIGH**: The template currently uses hardcoded `"icon"` mode in `cv_button_class` call. Changing this to use `cv_label_mode` will affect class selection which could break theme styling if themes rely on specific icon-mode classes. Plan mentions `context:secondary:icon` override testing but doesn't address theme compatibility impact.
- **MEDIUM**: Task 1's `verify` section tests golden files but doesn't explicitly test that `toolbar_publisher_list.html` golden remains byte-identical for default configuration (FILT-01 requirement). Golden comparison normalizes attributes/classes, making byte-exact verification challenging.
- **MEDIUM**: The plan references "mode-less and explicit icon renders" but current template has no mode variable. Adding `cv_label_mode` to template context changes the template's public API.
- **LOW**: Plan doesn't address how `cv_button_class` with `mode=None` falls back. Need to verify `cv_button_class` behavior when `mode` is `None` vs explicit string.

**Suggestions**:
1. Add explicit verification that default icon-mode output remains unchanged after implementation.
2. Document template API change: `cv_label_mode` becomes available in filter template context.
3. Test theme compatibility by verifying `context:secondary:icon` classes still apply when `cv_label_mode="icon"`.
4. Add task to verify `cv_button_class("context", cv_variant|default:"secondary", cv_label_mode)` works correctly with all three mode values.

**Risk Assessment**: **MEDIUM** - Changing template class selection and adding new context variable could affect theme compatibility and requires careful testing.

## 03-02

**Summary**: Documentation update plan correctly identifies that current docs incorrectly describe filter as "icon-only by construction". The plan updates all relevant reference pages and adds proper changelog entry.

**Strengths**:
- **Complete coverage**: Updates all relevant documentation (`context_buttons.md`, `action_menus.md`, `buttons.md`, `javascript.md`, `icons.md`).
- **Proper linking**: Maintains canonical resolution order references instead of duplication.
- **Release management**: Adds `Fixed` changelog entry (not `Breaking`) since default output unchanged.
- **Migration guidance**: Updates `docs/migrating-1.0.md` with copied-template contract.
- **Test integration**: Updates `test_label_mode_docs.py` to verify new documentation.

**Concerns**:
- **MEDIUM**: Task 1 mentions updating Mermaid CUSTOM node in `context_buttons.md` but doesn't specify exact changes needed. Current diagram might not accurately represent filter's new behavior.
- **MEDIUM**: The plan doesn't address potential documentation conflicts if other phases also modify these files (parallel phases 4, 5).
- **LOW**: Plan assumes `mkdocs build --strict` passes; doesn't consider broken links or formatting issues that might exist.

**Suggestions**:
1. Specify exact Mermaid diagram changes needed to reflect filter's resolved mode behavior.
2. Add coordination note about potential documentation conflicts with parallel phases.
3. Include fallback plan if `mkdocs build --strict` fails due to pre-existing issues.

**Risk Assessment**: **LOW** - Documentation updates are relatively safe, though coordination with parallel phases is needed.

## Overall Assessment

**Plan Quality**: **GOOD** - Both plans are well-researched, address all requirements, and follow established project patterns. The 03-01 plan is particularly thorough with edge case coverage.

**Completeness**: **HIGH** - All FILT requirements are addressed with appropriate test coverage.

**Risks**: 
1. **Theme compatibility**: Changing class selection in template could break themes that rely on specific icon-mode classes.
2. **Coordination**: Parallel phases (4, 5) might also touch documentation; need merge coordination.
3. **Golden preservation**: Ensuring byte-identical default output requires careful implementation.

**Recommendations**:
1. Proceed with implementation but add explicit theme compatibility testing.
2. Ensure all golden file comparisons use appropriate normalization vs byte-exact checks.
3. Document template API change (`cv_label_mode` availability) for theme authors.
4. Run full test suite including theme compatibility checks before finalizing.

**Final Risk Level**: **MEDIUM** - The core risk is theme compatibility, but proper testing can mitigate this.

---

## Consensus Summary

All four requested instances completed substantive reviews of both plans at `d632410` through the configured external adapters. Fable, Grok and Gemini independently confirm **C2-A1 and C2-A2 closed** at the planning level. DeepSeek's requested safeguards are already represented in the current executable instructions. This is approval of plan adequacy; implementation and product-test results remain future execution work.

### Agreed Strengths

- Reuse of the existing context resolver with the declared key and no target default; retained customization ordering and generic-wrapper behavior.
- Pre-change raw-string baselines complement the normalized toolbar golden. The unchanged real JavaScript handler already tolerates icon-less markup and preserves collapse/persistence failure semantics.
- Reference corrections, paired documentation assertions, copied-template migration guidance and actual quality-gate reporting remain in scope.

### Agreed Concerns

There is no agreed unresolved concern. Fable, Grok and Gemini flag template whitespace as execution risk; 03-01 already requires exact raw fixtures, immutable baseline capture and wrapping conditionals around existing whitespace. This is covered risk, not a missing instruction.

### Divergent Views

DeepSeek alone assigns HIGH to theme compatibility from mode-aware class selection. It has source citations and no leading evidence-discount marker, so this is a **judgment-class HIGH that is not suppressed by the consensus gate**. Its assertion that theme impact is unaddressed is resolved by verification of the existing plan, documented below. Fable, Grok and Gemini independently sign off the same default-output, class-selection and migration safeguards. No new implementation evidence is claimed.

### Current-cycle finding dispositions

Citations in this table refer to the current plan files in this directory, independently read during synthesis; source references are repository-relative.

| Finding | Disposition and evidence |
|---|---|
| **C2-A1 — distinct ViewSet validation** | **Closed, explicit reviewer sign-off.** `03-01-PLAN.md:286–295` requires button E210, view E211, settings E106 and constructor ValidationError separately, with acceptance at `:326–328`. Source `src/crud_views/lib/view/action_menu.py:46–62`, `src/crud_views/lib/viewset/__init__.py:105–111` and `tests/test1/test_action_label_mode_config.py:43–60` independently support the distinction. Fable, Grok and Gemini confirm closure. |
| **C2-A2 — detailed migration contract** | **Closed, explicit reviewer sign-off.** `03-02-PLAN.md:212–220` owns both the checklist and detailed contract, and `:242–245` requires both. Current `docs/migrating-1.0.md:331–339` is the correct detailed paragraph. Fable, Grok and Gemini confirm closure. |
| **C3-H1 — DeepSeek HIGH: mode-aware classes may break theme styling; impact unaddressed** | **Resolved at plan-review level by source/plan verification, not discounted.** `src/crud_views/lib/button_classes.py:136–147` already implements mode-specific class selection with base-slot fallback. Selecting the requested mode is the locked feature, not a new class API. `03-01-PLAN.md:190–205` mandates fixed default bytes and distinct icon/both overrides; `:215–223` requires literal-icon fallback and explicit-icon coverage; `:267–273` covers the mode matrix and custom variant mode keys. Default compatibility is therefore protected and configured differences are intentional. `03-02-PLAN.md:205–220` explicitly names the already-configured-floor effect and copied-template adoption; `:227–229` records downstream-theme follow-up. The requested theme verification and impact documentation are already executable requirements. Fable/Grok/Gemini sign off these mechanisms. No residual mitigation is absent from PLAN.md. |
| DeepSeek MEDIUM: normalized golden cannot prove default bytes | Already incorporated. `03-01-PLAN.md:190–200` separates raw `render_to_string` baselines from normalized goldens, commits them before production changes and requires the failing tracer. `:235–239` requires both raw strings and the toolbar golden unchanged. The review itself identifies raw baseline capture as a strength. |
| DeepSeek MEDIUM: new cv_label_mode template context needs documentation | Already incorporated. `03-02-PLAN.md:135` states custom templates receive cv_label_mode and own markup; `:215–220` documents that exact copied-template contract. The generic rendering path already stamps cv_label_mode (`src/crud_views/lib/view/base.py:640–645`); the planned builder stamp also makes it available before label customization. |
| DeepSeek LOW: None mode/class fallback and all-mode class testing | Already incorporated. `03-01-PLAN.md:215–217` passes literal icon for absent/None/empty/unknown direct modes; `:284–285` explicitly tests a distinct icon override under a non-icon floor. The full matrix and variant mode keys are required at `:267–273`. It never relies on cv_button_class(mode=None) acting as icon. |
| DeepSeek MEDIUM: unspecified CUSTOM diagram change | Already incorporated. `03-02-PLAN.md:139–146` explicitly replaces the filter exception, says custom/filter templates receive resolved data and own markup, removes the claim that no mode processing applies, and preserves MICON/paragraph invariants. Exact final prose is an execution choice. |
| DeepSeek MEDIUM: possible conflicts with parallel phases 4/5 | No concrete same-wave defect demonstrated. `03-02-PLAN.md:230–233` already assigns branch/PR splitting to the surrounding workflow; the roadmap permits numeric sequential execution (`.planning/ROADMAP.md:20`, `:255`). Within this phase the two plans have distinct waves and declared dependency. A hypothetical future scheduling collision adds no missing Phase 03 product requirement. |
| DeepSeek LOW: pre-existing strict MkDocs failures | Already incorporated. `03-02-PLAN.md:222–226` requires real outcomes and preserves explicit pre-existing failures without claiming green; its full verification includes strict MkDocs. |
| Fable LOW: raw-label escaping assertion might accidentally test trusted templates | Already incorporated distinction. `03-01-PLAN.md:225–226` preserves trusted template hooks and ordinary escaping; `:274–275` explicitly tests plain Unicode/HTML-like input through normal Django interpolation without altering the trusted-template boundary. Source `src/crud_views/lib/view/base.py:371` marks rendered snippets safe. A direct cv_action_label fixture is a suitable implementation of the existing instruction, not a missing behavior or scope change. |
| Fable LOW: PATTERNS suggests gettext_lazy | PLAN.md already states the governing choice unambiguously at `03-01-PLAN.md:212–213`: import gettext and evaluate at get_context call time; Task 3's sentinel verifies it. This repeats cycle-2 advice already excluded for that reason. The earlier PATTERNS analog is not the authoritative task instruction; no extra plan requirement is needed. |
| Fable LOW/open question: passing characterization commit might violate RED gate | Source question resolved. `/home/alex/.codex/gsd-core/references/tdd.md:94–105` validates evidence for the named target test and its intended failing assertion, not the first commit whose subject begins test. `03-01-PLAN.md:196–200` already sequences a baseline-only commit followed by the failing tracer before implementation. A passing baseline must not be submitted as RED, and nothing in the plan asks for that. No gate conflict was found. |
| Fable informational: settings_i18n.py/taskfile working directory | No change required; reviewer explicitly calls it informational. `03-01` Task 3 specifies direct msgfmt compilation. The cited settings file is an existing reference, not an alternate required command. |
| Fable optional: avoid duplicate documentation anchor | Already covered by canonical linking and strict MkDocs/doc-contract verification in `03-02` Task 1. No specific colliding heading is proposed or found. |
| Gemini LOW: multiline template whitespace | Explicitly incorporated at `03-01-PLAN.md:190–197` and `:218–223`; exact output is an acceptance criterion and automated gate. |
| Gemini LOW: adjacent migration host-icon sentence | Already covered by `03-02-PLAN.md:217–220`, which qualifies two-span/host-icon instructions to icon-bearing modes and links the compact contract, and Task 2's optional-icon reference correction. Gemini expressly says the adjacent sentence is not contradictory once those instructions execute. |

All historical cycle-1 findings remain closed or explicitly adjudicated in the PLAN.md ledgers. Their original findings and cycle-2 counts are preserved in history and are not recounted.

### Evidence quality and counting

Every final lane has both plan IDs, concrete source citations, and no leading evidence-discount marker. No lane was substituted, skipped, retried, or failed. Shared OpenCode transport is recorded separately from model independence. DeepSeek's HIGH is preserved verbatim above and expressly resolved on existing plan coverage; it is not silently suppressed as a single-reviewer opinion. Non-HIGH advice already incorporated in actions, tests, acceptance criteria or scope decisions is excluded under the counting contract. No product suite was run and no product source or plan was modified in this review.

CYCLE_SUMMARY: current_high=0 current_actionable=0

## Current HIGH Concerns

None.

## Current Actionable Non-HIGH Concerns

None.


## Verification coverage

Source-grounding runs against revised plans at d632410, using the deterministic CLI seams.
No product test suite was run. Every unique literal path is listed with a quoted current plan occurrence;
repeated citations share the checked declaration. Direct reads corroborate names and mechanisms, not signatures.

## Authority and severity

```json
{
  "authority": "intel",
  "severity": {
    "VERIFIED": {
      "severity": "none",
      "hardBlock": false
    },
    "MISSING": {
      "severity": "needs-acknowledgement",
      "hardBlock": false
    },
    "AMBIGUOUS": {
      "severity": "MEDIUM",
      "hardBlock": false
    },
    "UNCHECKABLE": {
      "severity": "INFO",
      "hardBlock": false
    }
  },
  "phase_status": {
    "verdict": "consistent",
    "phase": "03",
    "stateStatus": "Ready to execute",
    "roadmapStatus": "Planned",
    "stateRank": 1,
    "roadmapRank": 1,
    "authority": "STATE.md"
  }
}
```

The effective authority remains **intel**. Its API-SURFACE.md declares the inventory incomplete and no
api-map.json is present. All Python declarations/signatures and template/browser/CLI semantics are
**UNCHECKABLE / INFO** under that adapter; no empty index absence is called MISSING. Supplemental direct
source evidence follows. Filesystem existence is VERIFIED independently of language analysis.
No hard block is emitted. New test symbols and execution reports are explicitly skipped phase outputs.

## Cited path inventory

| Path | Quoted current plan reference | Verdict | Evidence |
|---|---|---|---|
| `.planning/PROJECT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:92` — “@.planning/PROJECT.md” | VERIFIED | Filesystem presence; `.planning/PROJECT.md:1` |
| `.planning/ROADMAP.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:93` — “@.planning/ROADMAP.md” | VERIFIED | Filesystem presence; `.planning/ROADMAP.md:1` |
| `.planning/STATE.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:94` — “@.planning/STATE.md” | VERIFIED | Filesystem presence; `.planning/STATE.md:1` |
| `.planning/phases/02-form-key-grammar/deferred-items.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:203` — “<read_first>CHANGELOG.md Unreleased Fixed; docs/migrating-1.0.md detailed filter-toggle contract at lines 331–339 and copied-template checklist; .planning/PROJECT.md quality gates; .planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md; .planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md environment caveats; .planning/phases/02-form-key-grammar/deferred-items.md</read_first>” | VERIFIED | Filesystem presence; `.planning/phases/02-form-key-grammar/deferred-items.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:411` — “Create .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md with baseline capture commit/source HEAD,” | SKIPPED — phase output | Explicitly produced by 03-01:118–130 / 03-02:74–78 |
| `.planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:85` — “It produces .planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md as its execution report, including the” | SKIPPED — phase output | Explicitly produced by 03-01:118–130 / 03-02:74–78 |
| `.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:95` — “@.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:97` — “@.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-PATTERNS.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:96` — “@.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-RESEARCH.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:98` — “@.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-SOURCE-AUDIT.md:1` |
| `.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:99` — “@.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md” | VERIFIED | Filesystem presence; `.planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md:1` |
| `.venv/bin/mkdocs` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:160` — “<automated>.venv/bin/mkdocs build --strict</automated>” | VERIFIED | Filesystem presence; `.venv/bin/mkdocs` (binary/executable, no text line) |
| `.venv/bin/pytest` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:179` — “<precondition>The Phase 1 cv_get_action_label_mode and default_label_mode implementations exist in the tracked view modules, and .venv/bin/pytest plus the installed npm test harness are runnable.</precondition>” | VERIFIED | Filesystem presence; `.venv/bin/pytest` (binary/executable, no text line) |
| `.venv/bin/ruff` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:282` — “<automated>.venv/bin/ruff check</automated>” | VERIFIED | Filesystem presence; `.venv/bin/ruff` (binary/executable, no text line) |
| `/home/alex/.codex/gsd-core/templates/summary.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:88` — “@/home/alex/.codex/gsd-core/templates/summary.md” | VERIFIED | Filesystem presence; `/home/alex/.codex/gsd-core/templates/summary.md:1` |
| `/home/alex/.codex/gsd-core/workflows/execute-plan.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:87` — “@/home/alex/.codex/gsd-core/workflows/execute-plan.md” | VERIFIED | Filesystem presence; `/home/alex/.codex/gsd-core/workflows/execute-plan.md:1` |
| `CHANGELOG.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:15` — “- CHANGELOG.md” | VERIFIED | Filesystem presence; `CHANGELOG.md:1` |
| `CLAUDE.md` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `CLAUDE.md:1` |
| `docs/migrating-1.0.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:13` — “- docs/migrating-1.0.md” | VERIFIED | Filesystem presence; `docs/migrating-1.0.md:1` |
| `docs/reference/action_menus.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:9` — “- docs/reference/action_menus.md” | VERIFIED | Filesystem presence; `docs/reference/action_menus.md:1` |
| `docs/reference/buttons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:10` — “- docs/reference/buttons.md” | VERIFIED | Filesystem presence; `docs/reference/buttons.md:1` |
| `docs/reference/context_buttons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:8` — “- docs/reference/context_buttons.md” | VERIFIED | Filesystem presence; `docs/reference/context_buttons.md:1` |
| `docs/reference/icons.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:12` — “- docs/reference/icons.md” | VERIFIED | Filesystem presence; `docs/reference/icons.md:1` |
| `docs/reference/javascript.md` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:11` — “- docs/reference/javascript.md” | VERIFIED | Filesystem presence; `docs/reference/javascript.md:1` |
| `docs/test` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:157` — “docs before completing the paired docs/test change. Link related pages; keep the compact D-08 scope.” | UNCHECKABLE | Reference is a fragment/glob or uncreated artifact; no missing-source inference |
| `settings_i18n.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:337` — “<read_first>tests/test1/test_i18n.py; src/crud_views/locale/de/LC_MESSAGES/django.po; src/crud_views/lib/view/buttons.py as changed by Task 1; tests/test1/test_context_button_template.py; taskfile.yaml i18n tasks; settings_i18n.py</read_first>” | VERIFIED | Filesystem presence; `settings_i18n.py:1` |
| `src/crud_views/lib/button_classes.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/button_classes.py:1` |
| `src/crud_views/lib/settings.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/settings.py:1` |
| `src/crud_views/lib/view/__init__.py` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:128` — “<read_first>docs/reference/context_buttons.md custom-template, rendering diagram and Import Paths sections; docs/reference/action_menus.md context resolution, Rendering and never-folded sections; docs/reference/buttons.md host fallback and mode class lookup; tests/test1/test_label_mode_docs.py test_canonical_label_mode_resolution_sections and test_label_mode_reference_links_and_diagram; src/crud_views/lib/view/__init__.py; src/crud_views/templates/crud_views/tags/context_action_filter.html; .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/__init__.py:1` |
| `src/crud_views/lib/view/action_menu.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/action_menu.py:1` |
| `src/crud_views/lib/view/base.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:61` — “to: src/crud_views/lib/view/base.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/base.py:1` |
| `src/crud_views/lib/view/button_data.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/button_data.py:1` |
| `src/crud_views/lib/view/buttons.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:8` — “- src/crud_views/lib/view/buttons.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/buttons.py:1` |
| `src/crud_views/lib/view/label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/view/label_mode.py:1` |
| `src/crud_views/lib/views/mixins.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:73` — “to: src/crud_views/lib/views/mixins.py” | VERIFIED | Filesystem presence; `src/crud_views/lib/views/mixins.py:1` |
| `src/crud_views/lib/viewset/__init__.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/lib/viewset/__init__.py:1` |
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:11` — “- src/crud_views/locale/de/LC_MESSAGES/django.mo” | VERIFIED | Filesystem presence; `src/crud_views/locale/de/LC_MESSAGES/django.mo` (binary/executable, no text line) |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:10` — “- src/crud_views/locale/de/LC_MESSAGES/django.po” | VERIFIED | Filesystem presence; `src/crud_views/locale/de/LC_MESSAGES/django.po:1` |
| `src/crud_views/static/crud_views/js/list.filter.js` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:69` — “to: src/crud_views/static/crud_views/js/list.filter.js” | VERIFIED | Filesystem presence; `src/crud_views/static/crud_views/js/list.filter.js:1` |
| `src/crud_views/templates/crud_views/tags/button/action.html` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `src/crud_views/templates/crud_views/tags/button/action.html:1` |
| `src/crud_views/templates/crud_views/tags/context_action_filter.html` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:9` — “- src/crud_views/templates/crud_views/tags/context_action_filter.html” | VERIFIED | Filesystem presence; `src/crud_views/templates/crud_views/tags/context_action_filter.html:1` |
| `src/crud_views/templatetags/crud_views.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:65` — “to: src/crud_views/templatetags/crud_views.py” | VERIFIED | Filesystem presence; `src/crud_views/templatetags/crud_views.py:1` |
| `taskfile.yaml` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:337` — “<read_first>tests/test1/test_i18n.py; src/crud_views/locale/de/LC_MESSAGES/django.po; src/crud_views/lib/view/buttons.py as changed by Task 1; tests/test1/test_context_button_template.py; taskfile.yaml i18n tasks; settings_i18n.py</read_first>” | VERIFIED | Filesystem presence; `taskfile.yaml:1` |
| `tests/js/list.filter.test.js` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:16` — “- tests/js/list.filter.test.js” | VERIFIED | Filesystem presence; `tests/js/list.filter.test.js:1` |
| `tests/lib/helper/icons.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/lib/helper/icons.py:1` |
| `tests/test1/test_action_label_mode_config.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_action_label_mode_config.py:1` |
| `tests/test1/test_action_menus_context.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:316` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_context_button_label_mode.py tests/test1/test_context_action_label_mode.py tests/test1/test_button_class_label_mode.py tests/test1/test_filter_pinned.py tests/test1/test_filter.py tests/test1/test_action_menus_context.py -q</automated>” | VERIFIED | Filesystem presence; `tests/test1/test_action_menus_context.py:1` |
| `tests/test1/test_action_menus_golden.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_action_menus_golden.py:1` |
| `tests/test1/test_button_class_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_button_class_label_mode.py:1` |
| `tests/test1/test_button_leaves.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:13` — “- tests/test1/test_button_leaves.py” | VERIFIED | Filesystem presence; `tests/test1/test_button_leaves.py:1` |
| `tests/test1/test_context_action_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:14` — “- tests/test1/test_context_action_label_mode.py” | VERIFIED | Filesystem presence; `tests/test1/test_context_action_label_mode.py:1` |
| `tests/test1/test_context_button_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_context_button_label_mode.py:1` |
| `tests/test1/test_context_button_template.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_context_button_template.py:1` |
| `tests/test1/test_filter.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:316` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_context_button_label_mode.py tests/test1/test_context_action_label_mode.py tests/test1/test_button_class_label_mode.py tests/test1/test_filter_pinned.py tests/test1/test_filter.py tests/test1/test_action_menus_context.py -q</automated>” | VERIFIED | Filesystem presence; `tests/test1/test_filter.py:1` |
| `tests/test1/test_filter_pinned.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | VERIFIED | Filesystem presence; `tests/test1/test_filter_pinned.py:1` |
| `tests/test1/test_filter_toggle_label_mode.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:12` — “- tests/test1/test_filter_toggle_label_mode.py” | SKIPPED — phase output | Explicitly produced by 03-01:118–130 / 03-02:74–78 |
| `tests/test1/test_i18n.py` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:15` — “- tests/test1/test_i18n.py” | VERIFIED | Filesystem presence; `tests/test1/test_i18n.py:1` |
| `tests/test1/test_label_mode_docs.py` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:14` — “- tests/test1/test_label_mode_docs.py” | VERIFIED | Filesystem presence; `tests/test1/test_label_mode_docs.py:1` |

## Declaration and field inventory

| Symbol | Quoted current plan reference | Effective-authority verdict | Supplemental source evidence |
|---|---|---|---|
| `FilterContextButton` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:26` — “- "EDGE-FILT-01-empty: A None button mode and an empty or unrelated view map reach the live context floor; the selected view map replaces lower maps. Direct FilterContextButton instances use their own override and declared key, never the list view's singular target default (D-01, D-02)."” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:298` — “class FilterContextButton(ContextButton):” |
| `FilterContextButton.get_context` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:308` — “def get_context(self, context: ViewContext) -> dict:” |
| `CrudView` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:104` — “CrudView.cv_get_action_label_mode(location, key, button=None, target_default=None) returns a mode. For context,” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:61` — “class CrudView(metaclass=CrudViewMetaClass):” |
| `cv_get_action_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:44` — “contains: "cv_get_action_label_mode"” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:299` — “def cv_get_action_label_mode(” |
| `cv_get_context` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:624` — “def cv_get_context(” |
| `cv_context_action_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:134` — “no target view and therefore ignores the current list view's singular cv_context_action_label_mode (D-01/D-02).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:100` — “cv_context_action_label_mode: str \| None = None” |
| `ViewContext` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/context.py:9` — “class ViewContext(BaseModel, arbitrary_types_allowed=True):” |
| `_apply_label` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:61` — “def _apply_label(self, data: dict, context: ViewContext) -> None:” |
| `_apply_variant` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:74` — “def _apply_variant(self, data: dict) -> None:” |
| `_inject_template` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:109` — “_apply_label, _apply_variant and _inject_template remain the customization chain; stamp cv_label_mode before them.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:79` — “def _inject_template(self, data: dict) -> None:” |
| `cv_button_class` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:525` — “def cv_button_class(location, slot, mode=None):” |
| `cv_icon_class` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:519` — “def cv_icon_class(value, location):” |
| `cv_icon` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:66` — “via: cv_button_class receives resolved mode; cv_icon_class/cv_icon retain placement behavior” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:513` — “def cv_icon(value, css=""):” |
| `cv_context_action` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:199` — “cv_context_action rendering path and the existing session POST/GET path. Observe its behavioral failure before” | UNCHECKABLE / INFO | `src/crud_views/templatetags/crud_views.py:228` — “def cv_context_action(context, key, obj=None):” |
| `ListViewTableFilterMixin` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:111` — “ListViewTableFilterMixin.post persists filter_expanded; cv_filter_expanded reads that session state for the next GET.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:299` — “class ListViewTableFilterMixin(FilterView):” |
| `ListViewTableFilterMixin.post` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:111` — “ListViewTableFilterMixin.post persists filter_expanded; cv_filter_expanded reads that session state for the next GET.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:336` — “def post(self, request, *args, **kwargs):” |
| `cv_filter_expanded` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/views/mixins.py:323` — “def cv_filter_expanded(self) -> bool:” |
| `default_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/view/label_mode.py:84` — “def default_label_mode(location: str) -> str:” |
| `HOST_LIBRARY` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:264` — “otherwise render the existing two children, including a host icon's standalone form (D-03). Use HOST_LIBRARY and” | UNCHECKABLE / INFO | `tests/lib/helper/icons.py:3` — “HOST_LIBRARY = {” |
| `HOST_ICONS` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:265` — “HOST_ICONS from the existing helper, and test both mixed directions plus empty/None host-slot configuration.” | UNCHECKABLE / INFO | `tests/lib/helper/icons.py:7` — “HOST_ICONS = {” |
| `ELIGIBLE` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:276` — “Replace the obsolete fixed-filter-mode comment beside ELIGIBLE in test_context_action_label_mode.py with a precise” | UNCHECKABLE / INFO | `tests/test1/test_context_action_label_mode.py:251` — “ELIGIBLE = './*[@cv-key][not(@cv-key="filter") and not(@id="cv-filter-toggle")]'” |
| `_filter_toggle` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:182` — “<read_first>CLAUDE.md; src/crud_views/lib/view/buttons.py; src/crud_views/lib/view/base.py cv_get_action_label_mode and cv_get_context; src/crud_views/lib/settings.py context_actions_label_mode; src/crud_views/lib/button_classes.py setting_changed receiver; src/crud_views/templates/crud_views/tags/context_action_filter.html; src/crud_views/templates/crud_views/tags/button/action.html; tests/test1/test_context_button_template.py; tests/test1/test_action_menus_golden.py; tests/test1/test_button_leaves.py _filter_toggle; tests/js/list.filter.test.js; src/crud_views/static/crud_views/js/list.filter.js</read_first>” | UNCHECKABLE / INFO | `tests/test1/test_button_leaves.py:574` — “def _filter_toggle(expanded: bool):” |
| `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:132` — “Show CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}” | UNCHECKABLE / INFO | `src/crud_views/lib/settings.py:67` — “context_actions_label_mode: Any = from_settings("CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE", default={})” |
| `label_template_code` | Implicit in “both label_template mechanisms” at 03-01-PLAN.md:273 | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:29` — “label_template_code: str \| None = None” |
| `label_template` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:273` — “priority. Cover both label_template mechanisms, variant mode keys and an empty custom label's fallback (D-07).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:28` — “label_template: str \| None = None” |
| `template_code` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:271` — “test-local in-memory templates for file-based custom labels and whole-button overrides, alongside template_code;” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:31` — “template_code: str \| None = None” |
| `label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:33` — “label_mode: str \| None = None  # None: the view's context label-mode maps; one of LABEL_MODES (#264)” |
| `variant` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:273` — “priority. Cover both label_template mechanisms, variant mode keys and an empty custom label's fallback (D-07).” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:32` — “variant: str \| None = None  # None: the target view's cv_action_variant” |
| `self.key` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:62` — “via: cv_get_action_label_mode("context", self.key, self), with no target_default argument” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:303` — “key: str = "filter"” |
| `cv_access` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:107` — “FilterContextButton.get_context(ViewContext) returns {cv_access: False} for a non-filter view or pinned filter.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:311` — “dict_kwargs = {"cv_access": False}” |
| `cv_key` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:325` — “data["cv_key"] = self.key” |
| `cv_action_label` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:326` — “data["cv_action_label"] = "Filter"” |
| `cv_icon_action` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:327` — “data["cv_icon_action"] = "filter"” |
| `cv_url` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:329` — “data["cv_url"] = list_url” |
| `cv_label_mode` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:47` — “contains: "cv_label_mode"” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:645` — “data = {**data, "cv_label_mode": mode, "cv_action_key": key}” |
| `target_default` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:62` — “via: cv_get_action_label_mode("context", self.key, self), with no target_default argument” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:300` — “cls, location: str, key: str, button: ContextButton \| None = None, target_default: str \| None = None” |
| `gettext` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:38` — “- "EDGE-FILT-04-empty: The core German PO contains a non-fuzzy translated Filter entry and the compiled catalog contains the key explicitly; a missing entry cannot pass through gettext's identical-string fallback (D-09)."” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/utils/translation/__init__.py:95` — “def gettext(message):” |
| `override_settings` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/test/utils.py:468` — “class override_settings(TestContextDecorator):” |
| `translation.override` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:348` — “call with a different sentinel and custom-label precedence. Use translation.override("de") for the authenticated” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/utils/translation/__init__.py:189` — “class override(ContextDecorator):” |
| `render_to_string` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:193` — “compare render_to_string output directly: retain leading/trailing whitespace, attribute ordering and class ordering.” | UNCHECKABLE / INFO | `./.venv/lib/python3.12/site-packages/django/template/loader.py:52` — “def render_to_string(template_name, context=None, request=None, using=None):” |
| `ViewSet` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:105` — “an own named view-map entry wins, then the supplied button override, then the selected whole ViewSet/settings map,” | UNCHECKABLE / INFO | `src/crud_views/lib/viewset/__init__.py:45` — “class ViewSet(BaseModel):” |
| `check_label_mode_map` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/viewset/__init__.py:107` — “def check_label_mode_map(cls, value):” |
| `cv_label_mode_checks` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/view/action_menu.py:46` — “def cv_label_mode_checks(cls, attribute: str, known_keys: Iterable[str] \| None) -> Iterator[Check]:” |
| `test_viewset_rejects_bad_value` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `tests/test1/test_action_label_mode_config.py:58` — “def test_viewset_rejects_bad_value(field, value):” |
| `test_invalid_setting_e106` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `tests/test1/test_action_label_mode_config.py:45` — “def test_invalid_setting_e106(field, value):” |
| `cv_button_data` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/view/button_data.py:52` — “def cv_button_data(ctx: dict, location: str, kind: str = "action") -> dict:” |
| `context_button_checks` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/view/buttons.py:350` — “def context_button_checks(context, viewset, buttons: list[ContextButton] \| None):” |
| `_action_settings_messages` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:248` — “<read_first>tests/test1/test_filter_toggle_label_mode.py from Task 1; tests/test1/test_context_button_label_mode.py; tests/test1/test_context_action_label_mode.py; tests/test1/test_context_button_template.py; tests/test1/test_filter_pinned.py; tests/test1/test_button_class_label_mode.py; tests/test1/test_action_label_mode_config.py test_invalid_setting_e106 and test_viewset_rejects_bad_value; tests/lib/helper/icons.py; src/crud_views/lib/view/buttons.py context_button_checks; src/crud_views/lib/view/action_menu.py cv_label_mode_checks; src/crud_views/lib/viewset/__init__.py check_label_mode_map; src/crud_views/lib/view/label_mode.py; src/crud_views/lib/view/button_data.py normalization policy; src/crud_views/lib/settings.py _action_settings_messages; src/crud_views/static/crud_views/js/list.filter.js; tests/js/list.filter.test.js</read_first>” | UNCHECKABLE / INFO | `src/crud_views/lib/settings.py:100` — “def _action_settings_messages(self) -> list[CheckMessage]:” |
| `crud_views_settings` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/settings.py:320` — “crud_views_settings = CrudViewsSettings()” |
| `setting_changed` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|” | UNCHECKABLE / INFO | `src/crud_views/lib/button_classes.py:111` — “@receiver(setting_changed)” |
| `CRUD_VIEWS_BUTTON_CLASSES` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:203` — “use override_settings(CRUD_VIEWS_BUTTON_CLASSES=...) and its existing setting_changed cache-reset path on entry/exit;” | UNCHECKABLE / INFO | `src/crud_views/lib/button_classes.py:124` — “return getattr(settings, "CRUD_VIEWS_BUTTON_CLASSES", None) or {}” |
| `test_canonical_label_mode_resolution_sections` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:45` — “contains: "test_canonical_label_mode_resolution_sections"” | UNCHECKABLE / INFO | `tests/test1/test_label_mode_docs.py:180` — “def test_canonical_label_mode_resolution_sections():” |
| `test_label_mode_reference_links_and_diagram` | `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:128` — “<read_first>docs/reference/context_buttons.md custom-template, rendering diagram and Import Paths sections; docs/reference/action_menus.md context resolution, Rendering and never-folded sections; docs/reference/buttons.md host fallback and mode class lookup; tests/test1/test_label_mode_docs.py test_canonical_label_mode_resolution_sections and test_label_mode_reference_links_and_diagram; src/crud_views/lib/view/__init__.py; src/crud_views/templates/crud_views/tags/context_action_filter.html; .planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md</read_first>” | UNCHECKABLE / INFO | `tests/test1/test_label_mode_docs.py:245` — “def test_label_mode_reference_links_and_diagram():” |
| `render_snippet` | `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:194` — “Explain in the fixture docstring that boundary whitespace is deliberately protected even where render_snippet strips” | UNCHECKABLE / INFO | `src/crud_views/lib/view/base.py:357` — “def render_snippet(cls, data: dict, template: str \| None = None, template_code: str \| None = None) -> str:” |

## Produced symbols excluded

- `_publisher_view` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `_render_filter` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `_filter_node` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `RAW_DEFAULT_FILTER` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:119` — “_publisher_view, _render_filter, _filter_node, and RAW_DEFAULT_FILTER (the two inline, exact pre-change”; declared new phase artifact, skipped.
- `test_filter_raw_default_bytes` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:120` — “strings). Tests are test_filter_raw_default_bytes, test_filter_both_tracer, test_filter_mode_placement_matrix,”; declared new phase artifact, skipped.
- `test_filter_both_tracer` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:50` — “contains: "test_filter_both_tracer"”; declared new phase artifact, skipped.
- `test_filter_mode_placement_matrix` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:120` — “strings). Tests are test_filter_raw_default_bytes, test_filter_both_tracer, test_filter_mode_placement_matrix,”; declared new phase artifact, skipped.
- `test_filter_host_slot_fallback` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; declared new phase artifact, skipped.
- `test_filter_mode_resolution` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; declared new phase artifact, skipped.
- `test_filter_declared_key_and_direct_button` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:121` — “test_filter_host_slot_fallback, test_filter_mode_resolution, test_filter_declared_key_and_direct_button,”; declared new phase artifact, skipped.
- `test_filter_live_floor` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_customization` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_visibility` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_label_escaping` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:122` — “test_filter_live_floor, test_filter_customization, test_filter_visibility, test_filter_label_escaping,”; declared new phase artifact, skipped.
- `test_filter_catalog_entry` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:126` — “Existing tests/test1/test_i18n.py gains test_filter_catalog_entry, test_filter_gettext_at_render_time, and”; declared new phase artifact, skipped.
- `test_filter_gettext_at_render_time` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:126` — “Existing tests/test1/test_i18n.py gains test_filter_catalog_entry, test_filter_gettext_at_render_time, and”; declared new phase artifact, skipped.
- `test_filter_german_render` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:127` — “test_filter_german_render; existing JS fixtures gain mode/label/initial-state options and described behavior cases.”; declared new phase artifact, skipped.
- `test_filter_direct_mode_fallback` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:123` — “test_filter_direct_mode_fallback, and test_filter_invalid_configuration_policy;”; declared new phase artifact, skipped.
- `test_filter_invalid_configuration_policy` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:123` — “test_filter_direct_mode_fallback, and test_filter_invalid_configuration_policy;”; declared new phase artifact, skipped.

## Additional uncheckable contracts

All signatures named in the interfaces section remain UNCHECKABLE. The ViewSet field_validator decorator exists at src/crud_views/lib/viewset/__init__.py:105; its Python semantics remain UNCHECKABLE under intel; @path entries are context imports. Pydantic/context attributes are covered above; no dataclass
or struct is required. Bare filenames alias full paths in the inventory. No missing source declaration was
confirmed by direct reads. The following semantics are UNCHECKABLE under intel:

- `gettext.GNUTranslations` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:345` — “the installed polib facility, and compiled membership as well as gettext result using gettext.GNUTranslations;”; UNCHECKABLE semantic/CLI contract.
- `polib` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:345` — “the installed polib facility, and compiled membership as well as gettext result using gettext.GNUTranslations;”; UNCHECKABLE semantic/CLI contract.
- `monkeypatch.setattr` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:200` — “implementation. Set the snapshot map with monkeypatch.setattr(crud_views_settings, "context_actions_label_mode",”; UNCHECKABLE semantic/CLI contract.
- `override_settings` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:150` — “\| A2 — snapshot settings and isolated class overrides \| MEDIUM \| Task 1 names crud_views_settings.context_actions_label_mode monkeypatch and override_settings for button classes, with setting_changed cache restoration. \|”; UNCHECKABLE semantic/CLI contract.
- `NodeList` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:112` — “The JavaScript handler already tolerates an empty icon NodeList and preserves state after a rejected POST.”; UNCHECKABLE semantic/CLI contract.
- `cv_context_actions_label_mode` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:288` — “cv_context_actions_label_mode map yields viewset.E211 through cv_label_mode_checks; construct CrudViewsSettings”; UNCHECKABLE semantic/CLI contract.
- `cv_context_label_mode` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:210` — “_inject_template, per D-01/D-02/D-07. Do not introduce cv_context_label_mode, which the wrapper would treat as a target”; UNCHECKABLE semantic/CLI contract.
- `cv_filter_expanded` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:108` — “Otherwise its context contains cv_key, cv_action_label, cv_icon_action, cv_filter_expanded, cv_url and template hooks.”; UNCHECKABLE semantic/CLI contract.
- `cv-filter-toggle` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:71` — “pattern: "cv-filter-toggle"”; UNCHECKABLE semantic/CLI contract.
- `aria-expanded` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:70` — “via: Stable toggle/panel IDs, aria-expanded, and optional host or child icon hooks”; UNCHECKABLE semantic/CLI contract.
- `aria-controls` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:262` — “render a visible label without title/tooltip while retaining type, IDs, cv-key, aria-expanded and aria-controls”; UNCHECKABLE semantic/CLI contract.
- `filter-collapse` — `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:219` — “are present and the required aria-expanded, aria-controls and filter-collapse ID for every mode. Link the compact”; UNCHECKABLE semantic/CLI contract.
- `data-cv-filter-icon` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:205` — “direct path. Inspect icons as descendants of data-cv-filter-icon wrappers and visible labels with”; UNCHECKABLE semantic/CLI contract.
- `context:secondary:both` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:202` — “override_settings alone does not change this captured action map. For a distinct context:secondary:both class value,”; UNCHECKABLE semantic/CLI contract.
- `context:secondary:icon` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:204` — “do not register theme classes persistently. Also test a distinct context:secondary:icon override for the mode-less”; UNCHECKABLE semantic/CLI contract.
- `X-CSRFToken` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:30` — “- "EDGE-FILT-02-encoding: Each successful toggle sends the existing request path, POST method, X-CSRFToken and JSON content type with a boolean filter_expanded payload; label characters do not enter that payload (D-06, D-10)."”; UNCHECKABLE semantic/CLI contract.
- `filter_expanded` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:30` — “- "EDGE-FILT-02-encoding: Each successful toggle sends the existing request path, POST method, X-CSRFToken and JSON content type with a boolean filter_expanded payload; label characters do not enter that payload (D-06, D-10)."”; UNCHECKABLE semantic/CLI contract.
- `E210` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|”; UNCHECKABLE semantic/CLI contract.
- `E211` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|”; UNCHECKABLE semantic/CLI contract.
- `E106` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:160` — “\| A1 — extend runtime normalization to malformed configured map/button values \| Rejected as an expansion of the existing filter contract: the filter bypasses cv_button_data, while cv_get_context restamps resolver output. Builder-only normalization would be overwritten. Adding wrapper behavior, a second resolver or new template API is unnecessary for valid-mode support. Existing E210/E211/E106 checks remain authoritative; malformed map/button values have no new runtime recovery guarantee. Invalid floor strict/log recovery remains unchanged through default_label_mode. \|”; UNCHECKABLE semantic/CLI contract.
- `--check` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:359` — “<automated>msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po</automated>”; UNCHECKABLE semantic/CLI contract.
- `--check-format` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:359` — “<automated>msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po</automated>”; UNCHECKABLE semantic/CLI contract.
- `--strict` — `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:160` — “<automated>.venv/bin/mkdocs build --strict</automated>”; UNCHECKABLE semantic/CLI contract.
- `--prefix` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:231` — “<automated>npm --prefix . test -- tests/js/list.filter.test.js</automated>”; UNCHECKABLE semantic/CLI contract.
- `-q` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:229` — “<automated>.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_action_menus_golden.py tests/test1/test_button_leaves.py -q</automated>”; UNCHECKABLE semantic/CLI contract.
- `-n auto` — `.planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md:276` — “<automated>.venv/bin/pytest tests -n auto</automated>”; UNCHECKABLE semantic/CLI contract.
- `--check` — `.planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md:359` — “<automated>msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po</automated>”; UNCHECKABLE semantic/CLI contract.

Browser querySelectorAll/textContent, Promise settlement and DOM identity are uncheckable semantics.
Direct evidence: list.filter.js:15 collapse first, :29 optional icon loop, :34–38 per-click captured payload and
rejection-only handler, :51 reset; context_action_filter.html:4–13 disclosure/icon/label attributes.
CLI names pytest/npm/mkdocs/ruff/msgfmt and all command signatures remain UNCHECKABLE; executable presence
is distinct from running checks. Catalog references resolve to existing test_i18n.py:66–88 patterns.
Future baseline commit capture is execution work, not an invented verified commit.

## Cross-artifact fact drift

The phase-status CLI result above is consistent. Other comparisons are independent judgment checks:

| Same fact | Authority | Current plan evidence | Verdict |
|---|---|---|---|
| Mode/default-output contract | ROADMAP.md:115–116 | 03-01 must_haves truths and Task 1 raw/default behavior | Consistent; raw fixture is additive |
| Icon-less persistence | ROADMAP.md:117–118 | 03-01 Task 2 requires no hooks, collapse and boolean POST | Consistent |
| Constant visible text | ROADMAP.md:119 | 03-01 truths and Task 2 require node/text identity | Consistent |
| German translation | ROADMAP.md:120 | 03-01 Task 3 requires PO/MO membership, runtime sentinel, German render | Consistent; distinct evidence claims refine the criterion |
| FILT-01..04 | ROADMAP.md:112 | Both plan frontmatter requirements | Identical IDs |
| No target default and declared key | CONTEXT.md:23–29 | 03-01 resolver instruction and 03-02 examples | Consistent |
| Host fallback, label constancy, accessibility | CONTEXT.md:32–45 | 03-01 three-mode and error matrices | Consistent |
| Customization, compact docs, gettext | CONTEXT.md:48–55 | 03-01 Tasks 1/3 and 03-02 Task 1 | Consistent |
| Stable behavior and release gates | CONTEXT.md:58–61 | 03-01 no JavaScript change; 03-02 Fixed/migration and full gates | Consistent |

No authoritative pair contradicts. Discretion/deferred ideas are excluded. A source-plan branch name and
observed retained branch describe provenance versus execution, not a conflicting domain fact; branch changes
remain outside scope. Scope omissions and cross-plan disagreements belong to the checker, not this drift pass.

## Cycle 3 closure source notes

- C2-A1: plan 03-01-PLAN.md:286–295 separates all four malformed-mode paths. The established examples at tests/test1/test_action_label_mode_config.py:43–60 construct CrudViewsSettings and ViewSet, and the latter expects ValidationError. Source cv_label_mode_checks (action_menu.py:46–62) only checks a view attribute; ViewSet.check_label_mode_map (viewset/__init__.py:105–111) is a Pydantic field validator. Direct reads confirm this distinction; the intel authority cannot certify Python signatures or exception propagation.
- C2-A2: plan 03-02-PLAN.md:214–221 explicitly revises the detailed migration filter contract as well as the checklist; its acceptance criteria at :242–245 require both. The current migration paragraph at docs/migrating-1.0.md:331–339 contains the historical two-span/hidden/ARIA contract that the plan correctly retains and qualifies.
- pydantic.ValidationError and pytest.raises are cited in 03-01-PLAN.md:290–292; exception and context-manager semantics are UNCHECKABLE / INFO under intel, with the existing tests above as supplemental evidence. Author is the existing test model (tests/test1/app/models.py); model construction signatures remain UNCHECKABLE.
