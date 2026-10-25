---
phase: 01
cycle: 2
reviewers: [opencode-gemini, opencode-grok, claude-fable]
reviewed_at: 2026-10-25T17:15:45Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md, 01-04-PLAN.md]
plans_revision: 0e15093
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

> Convergence cycle 2. This review covers the plans as revised in `0e15093`, which address cycle-1 findings R1–R14. The full cycle-1 review text is at commit `c1546c2` (`docs: cross-AI review for phase 01`). Its dispositions are summarized under "Cycle-1 findings: resolution status" below.

## OpenCode Review (opencode-gemini)

## 01-01

### 1. Summary
Plan `01-01` introduces the lazy project-wide floor accessor `default_label_mode(location)` and immutable `LABEL_MODE_DEFAULTS` in `src/crud_views/lib/view/label_mode.py`, wires `cv_button_data()` in `src/crud_views/lib/view/button_data.py:83-85` to use the accessor and recover from malformed truthy stamped modes in non-strict mode, and adds `crud_views.E108` in `src/crud_views/lib/settings.py:98-132`. Cycle-1 findings R1 (cross-test `_warned` state isolation), R2 (`frozenset` replacement for `LOCATIONS`), R5 (re-entrant lock deadlock when both stamp and floor are invalid), and R6 (fresh-process verification of deferred imports in `settings.py`) are all properly resolved and grounded in the live source.

### 2. Strengths
- **Re-entrant fallback deadlock eliminated (R5):** In `01-01-01`, `_invalid_label_mode` checks `is_strict()` (`src/crud_views/lib/exceptions.py:32-36`) before evaluating `fallback()`, and in non-strict mode evaluates `fallback()` *before* acquiring `_warned_lock` and logs *after* releasing it. When `cv_button_data()` (`src/crud_views/lib/view/button_data.py:83-85`) has a truthy invalid `cv_label_mode` and `CRUD_VIEWS_LABEL_MODE_DEFAULTS` also has an invalid floor for that location, `ctx.get("cv_label_mode") or default_label_mode(location)` short-circuits to the truthy stamp, fails `is_label_mode(label_mode)`, and enters `_invalid_label_mode` with `lambda: default_label_mode(location)`. Resolving `fallback()` outside `_warned_lock` prevents self-deadlock on the non-reentrant `threading.Lock` while preserving the `"cv_label_mode"` substring required by `test_unknown_cv_label_mode_raises_everywhere` (`tests/test1/test_button_data.py:120-125`).
- **Fresh-process import boundary proof (R6):** `src/crud_views/lib/view/__init__.py:1` eagerly imports `.base`, which imports `django.contrib.auth.mixins` (`src/crud_views/lib/view/base.py:16`) and fails with `AppRegistryNotReady` if imported before `django.setup()` (documented at `tests/test1/test_import_safety.py:6-9`). Task `01-01-02`'s `test_settings_defers_button_data_until_checks` verifies in a child interpreter that importing `crud_views.lib.settings` before `django.setup()` keeps `crud_views.lib.view` and `crud_views.lib.view.button_data` out of `sys.modules` until `crud_views_settings.check_messages` (`src/crud_views/lib/settings.py:135`) executes `_action_settings_messages()`.
- **Autouse test isolation without weakening production dedup (R1):** Adding `isolate_label_mode_warnings(monkeypatch)` as a function-scoped `autouse=True` fixture in `tests/test1/conftest.py` (analogous to `asset_registry` at `tests/test1/conftest.py:11-21`) gives every test a fresh `_warned` set while keeping D-11's process-lifetime once-per-`(location, repr(value))` contract intact across `override_settings` transitions within a test.
- **Immutable `LOCATIONS` monkeypatching (R2):** Because `LOCATIONS = frozenset({"context", "list", "card"})` at `src/crud_views/lib/view/button_data.py:12` is immutable, `01-01-02` specifies `monkeypatch.setattr(button_data, "LOCATIONS", button_data.LOCATIONS | {"test_loc"})` so the deferred `from crud_views.lib.view.button_data import LOCATIONS` inside `_action_settings_messages` picks up the patched module attribute.

### 3. Concerns
- **[LOW] Log capture inside the child subprocess of `test_invalid_stamp_and_floor_recovers_without_deadlock` (`tests/test1/test_button_data.py`):** Task `01-01-01` runs `cv_button_data` in a fresh `subprocess.run([sys.executable, "-c", ...], timeout=10, capture_output=True, text=True)` with `INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"]` and `django.setup()`, and requires asserting "one warning for the equal pair versus two for distinct pairs." In a standalone child script, pytest's `caplog` fixture is not active and Django's default `LOGGING` configuration does not attach a stderr handler for `WARNING` records on the `"crud_views.lib.view.label_mode"` logger unless configured in the child.

### 4. Suggestions
- In `test_invalid_stamp_and_floor_recovers_without_deadlock` (`tests/test1/test_button_data.py`), capture warnings inside the child script using `unittest.TestCase().assertLogs("crud_views.lib.view.label_mode", level="WARNING")` (or attach a `logging.Handler` to `logging.getLogger("crud_views.lib.view.label_mode")`) before asserting the record count (1 for equal bad values, 2 for distinct bad values).

### 5. Risk Assessment
**LOW** — All cycle-1 concurrency, import-cycle, and state-leakage hazards in `label_mode.py`, `button_data.py`, and `settings.py` have been resolved with concrete mechanisms and bounded subprocess tests.

---

## 01-02

### 1. Summary
Plan `01-02` wires `CrudView.cv_get_action_label_mode()` in `src/crud_views/lib/view/base.py:291-317` to `default_label_mode("context")` and `default_label_mode("list")`, guards `cv_icon_mode_checks()` in `src/crud_views/lib/view/buttons.py:405` against strict-mode `ValueError` exceptions from an invalid floor so `check_viewsets` (`src/crud_views/checks.py:20-28`) still returns `crud_views.E108`, and updates stale comments/docstrings in `base.py` and `action_menu.py` (R1, R10, R11).

### 2. Strengths
- **Preserves lazy floor evaluation when an explicit mode wins:** In `src/crud_views/lib/view/base.py:312`, `return target_default or default_label_mode("context")` short-circuits when `target_default` is set, and at `src/crud_views/lib/view/base.py:317`, replacing `mapping.get(key, "icon")` with `mapping[key] if key in mapping else default_label_mode("list")` avoids eagerly evaluating `default_label_mode("list")` when `key` is present in `mapping`. Thus an invalid strict floor never raises or warns when a higher-precedence layer resolves the key.
- **Protects `check_viewsets` from strict-mode floor crashes:** `check_viewsets` (`src/crud_views/checks.py:20-28`) collects `crud_views_settings.check_messages` (including `E108`) at line 23 and then iterates `ViewSet.checks_all()` at lines 25-27 in the same function. Wrapping `cls.cv_get_action_label_mode("context", key, button, target_default)` in `try ... except ValueError: continue` at `src/crud_views/lib/view/buttons.py:405` prevents an invalid floor under `CRUD_VIEWS_STRICT=True` (`tests/test1/conftest.py:29`) from aborting `check_viewsets` and discarding `E108`.
- **Clean resolution of R10 and R11:** Updating the class-attribute comments at `src/crud_views/lib/view/base.py:88-96` and the `viewset.E211` message at `src/crud_views/lib/view/action_menu.py:58-61` ("string or None") aligns the diagnostic text with the optional scalar types while keeping existing `test_e211_message_names_the_card_attribute` (`tests/test1/test_action_label_mode_config.py:113-116`) and `test_e211_string_on_map_names_target_attribute` (`tests/test1/test_context_action_label_mode.py:209-212`) passing.
- **Verified acceptance grep coverage:** Across `src/crud_views/lib/view/*.py`, the three matches of `"both" if card\|or "icon"\|get(key, "icon")` are `button_data.py:83`, `base.py:312`, and `base.py:317`. After `01-01` and `01-02`, the negative grep gate in `01-02-02` is guaranteed to return exit code 1 (zero matches).

### 3. Concerns
- None identified. All cycle-1 findings assigned to `01-02` (R1, R10, R11) are completely addressed, and `01-02`'s `files_modified` list is completely disjoint from parallel Wave 2 plan `01-03`.

### 4. Suggestions
- In `01-02-01`'s multi-route toolbar test (`test_context_floor_renders_unmapped_toolbar` in `tests/test1/test_context_action_label_mode.py`), when comparing card/row action bodies under `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"context": "both"}`, scope the card comparison to `//div[@cv-card-container]` (or the `CardAction` elements inside it) rather than the whole card page, since the card page's top-right `[cv-context-container]` toolbar legitimately switches to `"both"`. (The plan action already notes this distinction; keeping the XPath scoped to `@cv-card-container` makes it airtight.)

### 5. Risk Assessment
**LOW** — Changes in `base.py`, `buttons.py`, and `action_menu.py` are small, localized, and well-tested against both unit and client-rendered HTML assertions.

---

## 01-03

### 1. Summary
Plan `01-03` changes `CardListView.cv_card_actions_label_mode` in `src/crud_views/lib/views/card.py:28` from `"both"` to `str | None = None`, adds the `@classmethod` resolver `cv_get_card_actions_label_mode()`, skips `viewset.E210` when the attribute is `None` (`src/crud_views/lib/views/card.py:112`), updates `docs/reference/card-list-view.md`, and adds the breaking/migration and changelog entries in `docs/migrating-1.0.md` and `CHANGELOG.md`. Cycle-1 findings R3 (`AuthorCardListView`'s `no_label=True` delete button), R4 (using existing anchors in Wave 2 so `mkdocs build --strict` passes), and R13 (updating the existing `#213` bullet in `CHANGELOG.md:43-45`) are all resolved.

### 2. Strengths
- **Accurate handling of stock `AuthorCardListView` (R3):** In `tests/test1/app/views.py:76-81`, `AuthorCardListView.cv_card_actions` defines `detail` and `update` with `label_mode=None`, and `delete` with `no_label=True`. In `src/crud_views/lib/views/card.py:47-52`, `elif action.no_label: label_mode = "icon"` precedes the `else:` branch. Task `01-03-01` now tests the unmodified `AuthorCardListView` under `{"card": "label"}` by asserting `detail` and `update` render text-only while `delete` remains icon-only with its visually hidden label and `title`, directly verifying both LMOD-03 and D-18.
- **Wave-safe strict docs build (R4):** Because `mkdocs.yml:24-25` configures `validation: anchors: warn`, `mkdocs build --strict` aborts on any missing target anchor. Linking `docs/reference/card-list-view.md` to the already-existing `action_menus.md#label-mode` (`docs/reference/action_menus.md:58`) and `settings.md#action-menus` (`docs/reference/settings.md:71`) in `01-03-01` allows `mkdocs build --strict` to pass at the end of Wave 2 before `01-04-01` creates and retargets the new sub-anchors.
- **Consistent 0.29 card restoration recipe across both changelog and migration guide (R13):** Task `01-03-02` updates both `docs/migrating-1.0.md:127-129` and the existing `#213` bullet at `CHANGELOG.md:43-45` so that `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` comes first, `CardListView.cv_card_actions_label_mode = "label"` second, and `CardAction(label_mode="label")` third, alongside the new `"Card label-mode attribute"` breaking entry.

### 3. Concerns
- None identified. All code, check, test, and documentation changes in `01-03` match the live repository state.

### 4. Suggestions
- In `src/crud_views/lib/views/card.py:52`, call `self.cv_get_card_actions_label_mode()` (which resolves via the classmethod on `self`'s class or instance override of `cv_card_actions_label_mode` if accessed as `cls.cv_card_actions_label_mode`), and ensure `test_view_default_applies_and_action_overrides_it` (`tests/test1/test_card_label_mode_render.py:120-138`, which uses `monkeypatch.setattr(AuthorCardListView, "cv_card_actions_label_mode", "label")`) continues to pass unchanged.

### 5. Risk Assessment
**LOW** — The card attribute change is clean, isolated from `01-02`, and thoroughly covered by unit, check, render, and migration-contract checks.

---

## 01-04

### 1. Summary
Plan `01-04` completes the reference documentation across `docs/reference/settings.md`, `docs/reference/action_menus.md`, `docs/reference/card-list-view.md`, `docs/reference/context_buttons.md`, `docs/reference/buttons.md`, and `.planning/PROJECT.md`, adds executable documentation contract tests in `tests/test1/test_label_mode_docs.py`, and runs all phase-wide quality gates (`pytest`, `npm --prefix . test`, `mkdocs build --strict`, `ruff check`, `ruff format --check`, and the protected-path `git diff` check). Cycle-1 findings R4, R7, R8, R9, R11, R12, R13, and R14 are all addressed.

### 2. Strengths
- **Non-vacuous, position-independent executable docs test (R9, R14):** Task `01-04-01` parses Python fenced blocks in `docs/reference/settings.md` with `ast.parse` + `ast.literal_eval`, selects the standalone `CRUD_VIEWS_LABEL_MODE_DEFAULTS` dict containing the `"card"` key, and renders `{% cv_button "card" %}` (`src/crud_views/templatetags/crud_views.py:200-208`) with `cv_access=True` (required by `cv_resolve_action` at `src/crud_views/lib/view/visibility.py:14-18`) and `cv_icon_action="detail"` (required by `tags/button/action.html:8`), paired with an empty-defaults control render that proves the icon renders when the setting is `{}`.
- **Complete cleanup of stale fixed-floor prose in `settings.md` (R7):** Task `01-04-01` rewrites `docs/reference/settings.md:78-79` (`CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` and `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE`) so neither row claims unnamed keys are fixed to `icon` or conflates list resolution with the context-only target-view step.
- **Complete system-checks reference table alignment (R11, R12):** Task `01-04-01` and `01-04-02` update `docs/reference/action_menus.md:238-246` and `docs/reference/buttons.md:437-448` to include `crud_views.E106` and `crud_views.E108`, clarify that `viewset.E210` accepts `None` as unset on optional attributes (`cv_card_actions_label_mode`, `cv_context_action_label_mode`, `CardAction.label_mode`, `ContextButton.label_mode`), and align `viewset.E211`'s scalar description with `"string or None"`.
- **Immutable baseline revision for protected paths (R8):** Verification compares `tests/test1/golden`, `src/crud_views/templates`, and `examples` against commit `ebc7c23259ae35b2e4f34047d0da903e68a48ac8` (`docs(01): capture phase context`) and checks for untracked files in those directories.

### 3. Concerns
- **[LOW] Table column count difference between `docs/reference/action_menus.md:238` and `docs/reference/buttons.md:437`:** In `docs/reference/action_menus.md:238-246`, the `## System checks` table has **2 columns** (`| ID | Meaning |`), whereas in `docs/reference/buttons.md:437-448`, the `## System checks` table has **3 columns** (`| ID | Level | Meaning |`). Task `01-04-01` states "add the E108 Error row" in `action_menus.md` and its acceptance criteria state "E108 is documented as Error." If the executor or `test_label_mode_docs.py` expects an explicit `error` level column in `action_menus.md` (or adds a 3rd column to `action_menus.md`'s 2-column table), the Markdown table formatting or test assertion could mismatch.

### 4. Suggestions
- In `01-04-01`, keep `docs/reference/action_menus.md:238-246` as a 2-column `| ID | Meaning |` table matching its existing rows (e.g., `| \`crud_views.E108\` | error: `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is not a dict, or names an unknown location or invalid label mode |` or assert the level column in `buttons.md:437-448` where the `| ID | Level | Meaning |` table lives).

### 5. Risk Assessment
**LOW** — Documentation changes, cross-page anchor retargeting, and AST-parsed doc tests are well-specified and verified by `pytest` and `mkdocs build --strict`.

---

## Cross-Plan Assessment & Convergence Summary

All 14 cycle-1 review findings (`R1`–`R14`) have been verified against the live codebase and are properly resolved in the revised plans:
- **Wave & file isolation:** Wave 1 (`01-01`), Wave 2 (`01-02` and `01-03` in parallel with zero overlapping `files_modified`), and Wave 3 (`01-04`) have clean dependency edges and no race conditions.
- **No new high or medium risks:** Only two minor (`LOW`) implementation notes remain (using `assertLogs` or a custom handler inside the child script in `01-01-01`, and respecting the 2-column vs 3-column check table layout between `action_menus.md` and `buttons.md` in `01-04`). The plans are ready for execution.

---

## OpenCode Review (opencode-grok)

> Lane note: attempt 1 ended in `spawn error: ETIMEDOUT` at the 660 s lane floor (its stub carried `[reviewed-without-source-citations]` only because it contained no review). The lane was re-run per the timeout guidance with a raised `review.timeouts.opencode`; the review below is the successful retry and cites `file:line` evidence, so no discount marker applies.

I'll verify the revised plans against the source, starting with the files the cycle-1 fixes claim to touch.
I'll read the source the plans cite so the review is against the code, not the plan text.
Cycle-1 fixes R1–R14 match the source. Remaining issues are specification gaps, not wrong mechanisms.

## 01-01

The lazy floor, private recovery helper, and E108 design match the locked decisions and the import graph. R1, R2, R5, and R6 are actually fixed, not just labeled fixed.

**Strengths**
- Deferred `LOCATIONS` import is required: `button_data.py:8` already imports `label_mode`, and `LOCATIONS` is a `frozenset` at `button_data.py:12`. Patching `button_data.LOCATIONS` is the only way the E108 test can see a new key.
- Sentinel plus call-time `getattr` matches `from_settings` (`settings.py:13-14`) without adding a Pydantic field. `check_messages` is an uncached `@property` (`settings.py:134`), so the same instance sees `override_settings`.
- R5 is specified correctly: fallback before a non-reentrant lock, log after release, and a 10s subprocess so a held lock fails the test instead of hanging pytest.
- R1 matches the suite: `pytest-xdist` and `pytest-random-order` are installed (`pyproject.toml:74,77`) but not in `addopts` (`pyproject.toml:130`). The autouse fixture plus an explicit `--random-order` gate is the right isolation.
- Keeping `ctx.get("cv_label_mode") or …` preserves the falsey-stamp contract at `button_data.py:83-85`. Strict tests still match `cv_label_mode` (`test_button_data.py:122-125`) because `CRUD_VIEWS_STRICT=True` (`conftest.py:27-29`).

**Concerns**
- **MEDIUM.** The setting-path fallback must return `LABEL_MODE_DEFAULTS[location]` and must not call `default_label_mode` again. The stamp path’s callable is `default_label_mode(location)`, which re-enters `_invalid_label_mode` on a bad floor. If that inner fallback calls `default_label_mode` too, non-strict recovery recurses. The subprocess timeout turns that into a failed test, but the action text never states the termination.
- **LOW.** The context tracer does not pin raw keys. A context render with only `cv_label` (the card key, `button_data.py:74-78`) gets an empty short label and is forced back to icon mode (`button_data.py:80-87` and `:102-105`). The existing raw tag context is `test_button_leaves.py:490-499` (`cv_action_label`, `cv_icon_action`, `cv_access`).

**Suggestions**
- State that the setting fallback callable is `lambda: LABEL_MODE_DEFAULTS[location]`.
- Copy the `test_button_leaves.py:490-499` keys into the tracer acceptance text, and require a visible short label that is not the icon-mode hidden span.

**Risk Assessment:** LOW. Core contracts are right; the recursion footgun is the only new executor trap.

## 01-02

Toolbar and row floors are wired at the real final fallbacks, and the W292 exception path is the one that would discard E108.

**Strengths**
- Literals are exactly `base.py:312` (`target_default or "icon"`) and `base.py:317` (`mapping.get(key, "icon")`). A membership test is required: `dict.get(key, default_label_mode("list"))` evaluates the floor even when the key exists.
- `target_default or default_label_mode("context")` short-circuits, so a truthy explicit mode never reads a bad floor. Empty view maps still replace lower maps because `cv_first_inline_keys` treats `{}` as set (`base.py:264-265`).
- W292 is the only check-time caller (`buttons.py:405`, reached from `base.py:193`). `check_viewsets` appends viewset messages after `check_messages` (`checks.py:23-28`), so a `ValueError` there drops E108. Catching only that call is the right scope. Default detail actions are unmapped (`detail.py:12`, settings default `home/detail/update/delete`), so the integration test will hit the raise.
- Helpers the tracer names exist (`test_context_action_label_mode.py:40-41`, `test_action_label_mode_render.py:29-70`). Filter buttons are skipped by W292 because `FilterContextButton.get_context` is overridden (`buttons.py:389-395`, `:298-306`).

**Concerns**
- **LOW.** “Exclude filter/custom-template controls” does not name the node. List and card toolbars include `filter` (`settings.py:77-78`, `buttons.py:346`). `context_action_filter.html:3` hardcodes mode `"icon"`, so an assertion over every `fieldset[cv-context-container]` child fails on list and card routes even when ordinary actions are correct.
- **LOW.** `except ValueError: continue` also skips W292 if a future bug in `cv_get_action_label_mode` raises. Today the context path only raises from the floor (`base.py:316` is not taken for `"context"`).

**Suggestions**
- Exclude `[@cv-key="filter"]` by selector, and assert the remaining set is nonempty.
- Comment the `except` as “invalid floor is `crud_views.E108`”; do not catch around the `yield`.

**Risk Assessment:** LOW. Precedence and the check-survival path match the code.

## 01-03

The card attribute change, resolver, and stock-page assertion match the view that actually ships. R3 and R4 are fixed.

**Strengths**
- Stock actions are `detail`/`update` plus `CardAction(key="delete", no_label=True)` (`tests/test1/app/views.py:76-80`). Using `_card` instead of `_author_card` is required: `_author_card` replaces `cv_card_actions` (`test_card_label_mode_render.py:62-64`).
- Resolution order in `views/card.py:46-52` is the chain D-14 keeps. E210 today always runs `label_mode_check` (`views/card.py:112`); `is_label_mode(None)` is false (`label_mode.py:17-18`), so the `is not None` guard is mandatory. `test_default_is_both` (`test_card_label_modes.py:14-15`) must change in the same task.
- Docs links used before wave 3 exist: `action_menus.md:58` (`#label-mode`), `settings.md:71` (`#action-menus`). `mkdocs.yml:24-25` promotes missing anchors to warnings, and this plan now runs `mkdocs build --strict`.
- The `#213` bullet is inside Unreleased `### Breaking` (`CHANGELOG.md:7`, `:43-45`), so the setting-first rewrite and the later order pin target the same bullet. No template in `src/` reads the raw attribute.

**Concerns**
- **LOW.** The 01-03 changelog script only checks that `"Card label-mode attribute"` sits between the first `### Breaking` and the next heading. It does not check setting-before-view-before-button on the `#213` bullet. That pin is deferred to 01-04, so a wave-2 stop can ship the old recipe.
- **LOW.** `card-list-view.md:50` still says `label_mode` inherits the raw attribute. The task updates the attribute table and the order paragraph (`:71-78`) but does not name line 50.

**Suggestions**
- Point line 50 at the resolver, and add the setting-first order to the 01-03 verify script so wave 2 does not depend on wave 3 for D-17.

**Risk Assessment:** LOW. The breaking attribute change is disclosed and the render contract is testable on the stock page.

## 01-04

The docs plan now rewrites the stale sentences and binds one example to a real render. R7, R9, R11–R14 match the files they cite.

**Strengths**
- `settings.md:78-79` still says unnamed context keys are `` `icon` `` and the list row says “The same”. Rewriting both rows, and rejecting that sentence in the context row only, is the right regression.
- Card tracer keys match `cv_button` (`templatetags/crud_views.py:199-208`) and `cv_resolve_action` (`visibility.py:14-16`): `cv_access=True` is required or the tag returns `""`. For location `"card"`, `cv_label` is the label (`button_data.py:74-78`). `"detail"` is a real icon (`icons.py:17`). Empty `{}` stays `both`, so the control render proves the missing icon comes from the setting. `action.html:8` has no icon and no `title` in the label branch.
- Mermaid node id `MICON` is at `context_buttons.md:256` and referenced at `:262`. Keeping the id is required.
- E211 text to update is `action_menu.py:59-60`, `action_menus.md:244`, and `buttons.md:445-446`. E106/E108 are absent from that buttons table.
- Baseline `ebc7c232` exists, message is `docs(01): capture phase context`, and `git diff` of `tests/test1/golden`, `src/crud_views/templates`, and `examples` against it is empty. `npm --prefix . test` matches `package.json:11`.
- `PROJECT.md:55` still says the rename is “tracked separately” while `:96-97` already record D-19/D-20. Updating in place avoids a second decision row.

**Concerns**
- **LOW.** `mkdocs build --strict` will not catch a broken Mermaid node. Fences are client-side (`mkdocs.yml:16-18`). `CRUD_VIEWS_LABEL_MODE_DEFAULTS['context']` puts `]` inside `MICON["…"]`.
- **LOW.** `test_card_migration_contract` must scope to the Unreleased `#213` bullet (`CHANGELOG.md:43-45`), not a later release. The plan says so; the heading split is easy to get wrong because `### Breaking` also appears at `CHANGELOG.md:282`.

**Suggestions**
- Put the setting name in the prose link under the diagram, and keep the node label free of `]`.
- Select the `#213` bullet only from the slice before the next `## ` after Unreleased.

**Risk Assessment:** LOW. The doc contract is executable and the stale rows are named.

## Cross-plan

R1–R14 are incorporated against the current tree, not merely restated. Wave order is sound: 01-02 and 01-03 do not share files; 01-04 retargets anchors only after creating them; goldens stay valid because unconfigured floors remain `icon`/`icon`/`both` and real pages stamp `cv_label_mode` before the leaf (`base.py:631`, `views/card.py:86`).

**Overall risk: LOW.** No wrong mechanism. The one item that can still waste an executor is the non-strict fallback calling `default_label_mode` recursively (01-01). Filter-button exclusion on list/card routes (01-02) is the other likely red test.

---

## Claude Review (claude-fable)

# Cross-AI plan review, cycle 2 — Phase 01 (label-mode defaults)

Reviewed against the working tree at `0e15093` on `introduce-gsd`. Every `file:line` claim in the four plans was checked against source; the ones below are the ones that matter. Two things I could not run in this sandbox (permission-denied): the seeded xdist command and a subprocess probe of the settings import boundary. Where a finding depends on those, I say so.

## 01-01

**Summary.** The core design is right and the cycle-1 fixes landed where claimed. The lazy accessor, sentinel read, deferred `LOCATIONS` import, `repr`-keyed dedup and private `_invalid_label_mode` with a lazy fallback all match the verified code shape (`button_data.py:8` imports `label_mode`, so the import must be deferred; `button_data.py:83-85` is the production crash site; `test_button_data.py:121` already passes `["both"]`, so `repr` keying is required). The remaining issue is that one cycle-1 fix (R5) solved a problem the plan created for itself: the `_warned_lock` is unnecessary, and removing it removes the deadlock argument, the lock-ordering prose and a `django.setup()` subprocess per parametrised case.

**Strengths**
- E108 placement and wording copy the live E106 block exactly (`settings.py:98-132`), and the deferred-import comment already exists at `:100`. `{key!r}` on a non-str key `1` gives `key 1 must be one of […]`, consistent with D-04.
- R2 is correctly fixed, and for the right reason: both E108 and `default_label_mode` import `LOCATIONS` at call time, so `monkeypatch.setattr(button_data, "LOCATIONS", …)` is observed. `button_data.py:12` is a `frozenset`, so the `| {"test_loc"}` replacement is the only way.
- R1's autouse fixture is sound on one condition the plan satisfies: `_invalid_label_mode` must read `_warned` as a module global at call time. The artifact list keeps `_warned` in `label_mode.py` and only `_invalid_label_mode` touches it, so `monkeypatch.setattr(label_mode, "_warned", set())` is seen.
- The tracer uses the real tag path. `cv_button` (`templatetags/crud_views.py:200-208`) goes through `cv_resolve_action`, which hides anything without `cv_access is True` (`visibility.py:14`). Requiring `cv_access=True` in the raw context is the right guard against a vacuous pass. `test_button_leaves.py:492-500` is the exact existing pattern.
- Keeping the `or` in `ctx.get("cv_label_mode") or default_label_mode(location)` preserves the empty-string-means-unset behaviour that `test_card_empty_label_forces_icon` (`test_button_data.py:106-109`) and the goldens depend on.
- D-07 precondition holds: `src/crud_views/__init__.py` is a version string and `src/crud_views/lib/__init__.py` is empty, so importing `crud_views.lib.settings` before `django.setup()` cannot drag in `lib.view`. Its module-level imports (`settings.py:1-10`) are Django, box and pydantic only.

**Concerns**
- **MEDIUM (over-engineering): `_warned_lock` should go.** A check-then-add race on a `set` without a lock costs, at worst, one duplicate warning line on the very first concurrent render. D-11 says "once per process", and a one-line duplicate under a race is not what that decision guards against (log flooding on a hot path). The lock is the sole reason R5 exists, the sole reason for "resolve fallback before acquiring" prose, and the sole reason for `test_invalid_stamp_and_floor_recovers_without_deadlock`, which spins up a configured Django in a child process per parametrised value. Delete the lock and all three disappear. If the maintainer insists on atomicity, a plain `set.add` is already atomic under the GIL for the "add" half; the membership check is the only race, and it is benign.
- **LOW: the bad-value list conflates two levels.** The 01-01-01 action lists `None, "", [], {}, nested dict, ["both"], 1, "Both", " both ", "bοth"` as values to test. `{}` as the *whole setting* is valid (the must-haves say it resolves to package defaults), but `{}` as a *mode value* for one location is invalid. The text does not say which level each value is exercised at. An executor who feeds `{}` into the strict-raise case as the setting contradicts the LMOD-01 truth. State the two levels explicitly.
- **LOW: ruff F401 at the gate.** After the change, `LABEL_MODES` at `button_data.py:8` is unused (the raise moves into `_invalid_label_mode`). `ruff check` fails the phase gate unless the import is dropped. PATTERNS.md notes it; the plan does not.
- **LOW (open, not re-verified): R6 test proves the boundary, not E108's own deferral.** `check_messages` → `_action_settings_messages` already imports `action_menu` → `lib.view` package → `buttons.py` → `button_data` (`buttons.py` is in the `button_data` importer list). So "button_data is loaded after check_messages" is true today, regardless of E108. That is fine for D-07, which is about the module-level boundary, but the test's docstring should not claim it proves E108's deferred import.
- **LOW: non-dict setting at render fans out.** With the dedup key `(location, repr(value))` and a non-dict setting, each of the three locations warns once. Three lines for one bad setting is acceptable, but say so in the action text so the test asserts three, not one.

**Suggestions**
- Drop `_warned_lock`, delete `test_invalid_stamp_and_floor_recovers_without_deadlock`, and replace the R5 ledger row with "resolved by removing the lock". Keep the in-process "same pair reached from both sources warns once" test, which covers the real re-entrancy case (bad stamp whose fallback floor is also bad).
- Split the bad-value list into "whole-setting values" and "per-location mode values" in the action text.
- Add "remove the now-unused `LABEL_MODES` import from `button_data.py`" to the task.

**Risk: LOW–MEDIUM.** Mechanically correct; the medium is self-inflicted complexity, not a functional gap.

## 01-02

**Summary.** Two literal replacements plus one narrow guard, with the cycle-1 wording fixes applied where the live files actually say the stale thing. All cited lines exist: `base.py:312` (`target_default or "icon"`), `base.py:317` (`mapping.get(key, "icon")`), the three attribute comments at `base.py:88-96`, the W292 call at `buttons.py:405` and the E211 wording at `action_menu.py:58-60`. The membership-branch instruction for the list fallback is the correct fix for eager evaluation of `dict.get`'s default.

**Strengths**
- The W292 guard is the right shape. `checks.py:23-27` runs `crud_views_settings.check_messages` and then iterates `ViewSet.checks_all()` in the same function; `checks_all` is a generator (`viewset/__init__.py:155-162`), so a `ValueError` escaping `cv_icon_mode_checks` discards the already-collected E108. Wrapping only the `cv_get_action_label_mode` call and continuing mirrors the existing "invalid counts as unset" pattern at `buttons.py:400-403`.
- Precedence is preserved by construction: the plan changes only the two terminal returns, and the test map reuses the existing helpers (`_client`, `_toolbar`, `_rows`, `_has_icon_and_text` at `test_action_label_mode_render.py:28-75` and `test_context_action_label_mode.py:40-41`).
- R10 and R11 edits target live stale text. `base.py:91` says `then "icon"`; `base.py:96`'s comment says `None: "icon"`; `action_menu.py:59-60` calls both scalars "string-valued". The existing `test_e211_message_names_the_card_attribute` (`test_action_label_mode_config.py:113-116`) asserts only that the attribute name is present, so the rewording cannot break it.
- The filter-toggle exclusion is stated rather than claimed as supported, matching Pitfall 6 in research.

**Concerns**
- **LOW: strict-mode asymmetry the plan quietly relies on.** `base.py:631` passes the raw `cv_context_action_label_mode` as `target_default` into `cv_get_action_label_mode`, while `buttons.py:400-403` sanitises an invalid value to `None` before the same call. Today an invalid target default therefore reaches `cv_button_data` as the stamped mode and raises at `button_data.py:85`. After 01-01 it falls back under D-10 in non-strict mode. That is the intended fix, but 01-02's "explicit value bypasses an invalid floor" tests should include this case so the two call sites are covered together.
- **LOW: the literal gate's grep.** `or "icon"` also matches comment text. The plan says "describe the chain in words without copying expressions matched by the gate", which is the correct precaution; just make sure the rewritten `base.py:91` comment does not keep `then "icon"`.
- **LOW: `test_e211_describes_optional_scalar_modes` pins a phrase.** Pinning the literal `"string or None"` in a test turns diagnostic prose into a contract. Acceptable, but 01-04 pins the same phrase in docs, so one wording change needs three edits. Consider asserting on a shorter token (`"or None"`).

**Suggestions**
- Add one render test with `cv_context_action_label_mode = "nope"` on a target view under `CRUD_VIEWS_STRICT=False`, asserting the floor is used and one warning is logged. This is the D-10 path reached through `base.py:631`.

**Risk: LOW.** Smallest change surface in the phase; disjoint from 01-03 (`base.py`, `buttons.py`, `action_menu.py` vs `views/card.py`, `view/card.py`, docs).

## 01-03

**Summary.** The card slice is correct and the R3 fix is exactly right: `tests/test1/app/views.py:76-80` has `detail` ("Details"), `update` ("Edit") and `delete` with `no_label=True`, so a stock-view render under `{"card": "label"}` must show two text-only buttons and one icon-only button. R4 is fixed for `card-list-view.md`: both fallback anchors exist (`action_menus.md:58` → `#label-mode`, `settings.md:71` → `#action-menus`), and `mkdocs.yml:24-25` (`anchors: warn`) makes a bad one fatal under `--strict`. The gap is that the same anchor discipline is not stated for the two other docs files this plan edits.

**Strengths**
- The resolver as a `@classmethod` beside `cv_get_card_actions_inline` (`views/card.py:102-105`) and the conditional E210 yield mirror the existing per-action pattern at `:117-118`. `cv_get_card_action_data` is an instance method, so `self.cv_get_card_actions_label_mode()` is fine.
- `test_default_is_both` (`test_card_label_modes.py:14-15`) is the only test that pins the old default; the plan replaces it by name. `test_good_values_yield_no_check` (`:38-48`) is extended with `None`.
- Using `_card(_client([AUTHOR_FULL]), reverse(...))` instead of `_author_card` for the stock test is correct: `_author_card` monkeypatches `cv_card_actions` (`test_card_label_mode_render.py:62-64`), which would hide the D-18 exception.
- The CHANGELOG work is correctly split: a new Breaking bullet plus a rewrite of the existing #213 bullet at `CHANGELOG.md:43-45`, which today lists only the per-view and per-button options.
- No template in `src/crud_views/templates` reads `cv_card_actions_label_mode` (grep empty), so the acceptance note's "no Tabler template change needed" is grounded.

**Concerns**
- **LOW–MEDIUM: anchor discipline stated for one file, needed for three.** 01-03-02 edits `docs/migrating-1.0.md` (adds E108 to the checks list at `:44-48`, adds the Breaking bullet near `:127-129`) and `CHANGELOG.md`. Neither task says which anchors those bullets may link to. The canonical targets (`settings.md#label-mode-configuration`, `action_menus.md#card-label-mode-resolution`) do not exist until 01-04. `migrating-1.0.md` is in the mkdocs nav, so the 01-03 strict build would catch a forward link there; `CHANGELOG.md` is not in `mkdocs.yml`, so a forward link there is never checked by any gate. Pin "existing anchors only" for both files, with 01-04 retargeting.
- **LOW: the migration bullet's "no Python compatibility change" prohibition is only prose.** The verify command asserts the lead-in and three names exist; nothing checks that the bullet says `None`. Since the prohibition is flagged unverified anyway, add `"None"` to the `all(x in …)` tuple.
- **LOW: CHANGELOG Fixed bullet.** `### Fixed` is at `CHANGELOG.md:136` and `### Added` at `:167`, both under Unreleased. The plan's verify splits on `### Breaking` only, so a Fixed bullet placed under the wrong heading passes. Minor.

**Suggestions**
- Add one sentence to 01-03-02: "Links in `migrating-1.0.md` and `CHANGELOG.md` use `action_menus.md#label-mode` and `settings.md#action-menus`; 01-04-02 retargets them."
- Extend the verify tuple with `"None"` and `"### Fixed"` presence.

**Risk: LOW.** Small code change, existing scaffolding, one process gap in docs linking.

## 01-04

**Summary.** Documentation, decision handoff and final gates. The executable docs example via `ast.literal_eval` with content-based selection (R14) is a good design, and R9's five-field raw context is sufficient for the `cv_button` path. R7, R11, R12 and R13 all target live stale text: `settings.md:78` ("keys not named are `icon`"), `action_menus.md:245` and `buttons.md:446` ("string-valued"), `buttons.md:435-448` (no E106/E108 rows). R8's baseline provenance is now correct: `ebc7c23` is "docs(01): capture phase context", the protected-path diff against it is empty, and `STATE.md:10` records `0234270`. The one real problem is a new test that reads `.planning/`.

**Strengths**
- `test_documented_card_floor_renders_label_only` binds the recipe to rendering. For location `"card"`, `cv_button_data` reads `cv_label` (`button_data.py:74-78`), so `cv_label="Details"` is the right key; `cv_icon_action="detail"` plus the empty-defaults control render proves the missing icon is caused by the setting, not a missing icon.
- Keeping the Mermaid node id `MICON` is required: it is referenced at `context_buttons.md:262` and in the class list at `:305`.
- The D-23 handling is correct against the live file: `PROJECT.md:96-97` already has the D-19 and D-20 rows, so "retain, do not duplicate, fix the stale Out of Scope bullet at `:55`" is the right instruction.
- `npm --prefix . test` maps to `vitest run` (`package.json:11`) and avoids the package-fetching `npx` wrapper the source plan used.

**Concerns**
- **MEDIUM: `test_label_mode_decision_handoff` reads `.planning/PROJECT.md` from the package test suite.** `tests/test1/test_label_mode_docs.py` is a permanent repo test. `.planning/` is planning state: `gsd-pr-branch` filters `.planning/` commits out of the PR branch, and milestone cleanup archives phase directories. A test that reads `PROJECT.md` fails on every clean PR branch and after archival, and it ties the package's test suite to the GSD workflow. Move the D-23 check into the plan's `<verify>` block as a one-off grep and keep `test_label_mode_docs.py` scoped to `docs/`, `CHANGELOG.md` and `migrating-1.0.md`.
- **LOW: `ast.parse` over every Python fence in `settings.md`.** Any fence on that page that is illustrative rather than parseable (a `...` placeholder, a shell line in a `python` fence) raises `SyntaxError` and fails the test for an unrelated reason. Parse only fences containing the setting name, or catch `SyntaxError` per block and skip.
- **LOW: scoping on `## Unreleased`.** `test_card_migration_contract` selects the #213 bullet "inside Unreleased Breaking". At the 1.0.0 bump that heading becomes `## 1.0.0` and the test breaks. Scope by the bullet's lead-in text or by "the first `### Breaking` after the top heading".
- **LOW: the protected-path gate misses untracked files.** The plan already says to inspect `git status` for new files; make it a command (`git status --porcelain -- tests/test1/golden src/crud_views/templates examples` must print nothing) with its own `fails_when`, since prose steps are skipped.

**Suggestions**
- Remove `test_label_mode_decision_handoff` from the artifact list; replace with a `<verify>` grep on `PROJECT.md` for the two decision rows.
- Pre-filter fences by `"CRUD_VIEWS_LABEL_MODE_DEFAULTS" in block` before `ast.parse`.

**Risk: LOW–MEDIUM.** Docs-only, but one test as specified is guaranteed to break outside the planning branch.

## Cross-plan

- **Wave ordering and ownership are correct.** 01-02 owns `base.py`, `buttons.py`, `action_menu.py` and four context/list test files; 01-03 owns `views/card.py`, `view/card.py`, two card test files, `card-list-view.md`, `migrating-1.0.md`, `CHANGELOG.md`. No overlap. 01-04 takes `card-list-view.md` after 01-03, which is sequential by wave.
- **The acceptance grep will be clean after 01-02.** The three current matches are `button_data.py:83` (01-01), `base.py:312` and `:317` (01-02). `views/card.py:50` (`no_label` → `"icon"`) is not matched by the pattern and stays per D-18.
- **Branch naming has three answers.** Config says `branching_strategy: "phase"` with template `gsd/phase-{phase}-{slug}`; the plans say "keep current branch"; PROJECT.md says `feat/label-mode-defaults`. The executor will follow config. Research "Open Question 1" claims this is resolved, but it is resolved by assertion. State once, in STATE.md or the first plan, which one wins, so the summary does not record a surprise.
- **Deferred research items are correctly refused.** The source-qualified dedup key and `setting_changed` reset are rejected in favour of D-11's literal wording. That is defensible; with the lock removed (01-01 concern), the remaining design is simpler than the research sketch, not more complex.
- **Not re-verified here.** The seeded xdist run ("148 passed" in the audit) and the subprocess import-boundary probe were permission-denied in this session. Both designs check out by reading the code (`pyproject.toml:74,77` installs both plugins; `addopts` enables only `--strict-markers`, so `--random-order` is opt-in as the plan says), but the execution evidence is the audit's, not mine.

**Overall risk: LOW–MEDIUM.** No HIGH findings. The phase goal is achieved by the four plans as written. Three items change what the executor does: drop the lock and its subprocess test (01-01), state existing-anchor discipline for the two other docs files (01-03), and keep `.planning/` out of the committed test suite (01-04). Everything else is wording or test-scoping hygiene.

---

## Consensus Summary

Three reviewers ran: opencode-gemini, opencode-grok, and claude-fable. All three received the prompt, worked from the source, and cited `file:line` evidence. None carries a discount marker. The opencode-grok lane hit `spawn error: ETIMEDOUT` again at the 660 s lane floor. It was re-run once with `review.timeouts.opencode` temporarily raised, and that retry is the review above. The config change was reverted byte-for-byte afterwards. All three reviewers covered every plan id (01-01 … 01-04).

**No reviewer raised a HIGH concern.** Overall risk: gemini LOW, grok LOW, claude LOW–MEDIUM. All three independently confirmed that the cycle-1 findings R1–R14 are incorporated against the live tree, not only labelled as fixed. The remaining items are specification gaps, test-scoping hygiene and wording. No reviewer found a wrong mechanism.

### Cycle-1 findings: resolution status

| Cycle-1 concern | Plan(s) | Status in cycle 2 |
|---|---|---|
| R1 `_warned` leaks across tests | 01-01-02, 01-02-02 | Resolved. All three confirm the autouse fixture and the seeded xdist gate. |
| R2 `LOCATIONS` is a frozenset | 01-01-02 | Resolved (all three). |
| R3 stock delete stays icon-only | 01-03-01 | Resolved (all three). |
| R4 forward anchors before wave 3 | 01-03-01, 01-04-01 | Resolved for `card-list-view.md` (all three). claude notes the same discipline is unstated for `migrating-1.0.md`/`CHANGELOG.md` (new item A10). |
| R5 deadlock under `_warned_lock` | 01-01-01 | Resolved (gemini, grok). claude would rather delete the lock, but 01-01's Deferred table explicitly retains it, so this is an explicit rejection and is not re-counted. |
| R6 D-07 import boundary unproven | 01-01-02 | Resolved. See the source-grounding note on claude's counter-claim. |
| R7 stale `settings.md:78` row | 01-04-01 | Resolved (all three). |
| R8 baseline provenance | 01-04 verification | Resolved (claude, grok). |
| R9 docs tracer access/icon data | 01-04-01 | Resolved (all three). |
| R10 stale `base.py:88-96` comments | 01-02 | Resolved (all three). |
| R11 E211 "string-valued" wording | 01-02-02, 01-04-01 | Resolved (all three). |
| R12 `buttons.md` checks table | 01-04-02 | Resolved (gemini, grok). |
| R13 #213 bullet setting-first order | 01-03-02, 01-04-02 | Resolved. The wave-2 verify script does not yet pin it (A11). |
| R14 example selection by position | 01-04-01 | Resolved. The parse robustness of the selector is a new item (A14). |

### Agreed Strengths
- R1–R14 are incorporated against live source (all three).
- The lazy floor, `_UNSET` sentinel, deferred `LOCATIONS` import and `repr`-keyed dedup match the import graph. `button_data.py:8` imports `label_mode`, and `button_data.py:12` holds the frozenset (all three).
- In the R5 fix, `fallback()` runs before the lock and the log call runs after release, and the bounded subprocess test catches a held lock (gemini, grok).
- The W292 guard is correctly scoped. `checks.py:23-28` collects E108 before it iterates `checks_all()`, and `buttons.py:405` is the only check-time caller (all three).
- The membership branch avoids eager `dict.get` default evaluation, and `target_default or default_label_mode("context")` short-circuits (all three).
- The stock-page card test uses `_card` rather than `_author_card`, which keeps the D-18 `no_label` exception visible (all three).
- Existing anchors `action_menus.md:58` (`#label-mode`) and `settings.md:71` (`#action-menus`) keep the wave-2 `mkdocs --strict` green (all three).
- The `ast.literal_eval` docs tracer uses `cv_access=True`, `cv_icon_action`, and an empty-defaults control render, so it cannot pass vacuously (all three).
- Wave and file ownership are disjoint between 01-02 and 01-03 (all three).

### Agreed Concerns
No HIGH. Concerns raised by two or more reviewers:
1. **[LOW] The 01-03-02 verify script is weaker than its acceptance criteria.** It checks only the lead-in and the three names. It does not check the setting-first order of the #213 bullet (that check waits until 01-04), the `None` disclosure, or Fixed-bullet placement (claude, grok).
2. **[LOW] The `CHANGELOG.md` Unreleased/#213 section selection is fragile.** `### Breaking` also appears at `CHANGELOG.md:282` (0.30.0), and `## Unreleased` gets renamed at the 1.0 bump (claude, grok).
3. **[LOW] The filter toggle exclusion in 01-02 does not name a selector.** `context_action_filter.html:3` hardcodes `"icon"`. An assertion over all `[cv-context-container]` children fails on list and card routes (grok this cycle; grok and claude in cycle 1, not taken into the ledger).

### Divergent Views
- **`_warned_lock`.** claude (MEDIUM, over-engineering) wants the lock and the deadlock subprocess test removed. gemini and grok accept the R5 design. 01-01's "Review Feedback Deferred" table already rejects this ("Retain the lock for atomic check-and-add"), so it is not counted as unresolved.
- **Is 01-02 finished?** gemini reports no concerns. claude and grok each add LOW test-coverage items (A7, A8).
- **Single-reviewer items** (all counted as actionable unless noted):
  - grok [MEDIUM] (judgment): the non-strict invalid-setting fallback must be `LABEL_MODE_DEFAULTS[location]`. If it is not, it re-enters `default_label_mode` and recurses (A1).
  - claude [MEDIUM] (judgment): `test_label_mode_decision_handoff` reads `.planning/PROJECT.md` from the permanent package test suite. Verified: no existing test under `tests/` references `.planning`, and `gsd-pr-branch` filters `.planning/` commits (A13).
  - claude [LOW] (existence): **refuted by source-grounding, not counted.** claude says `check_messages` already loads `button_data` through `action_menu`, so the R6 test cannot prove that E108 defers its import. A fresh-interpreter probe shows otherwise. After `django.setup()` and `crud_views_settings.check_messages`, `sys.modules` contains `crud_views.lib.view.{action_menu,base,buttons,card,context,label_mode,meta,variant,visibility}` but **not** `crud_views.lib.view.button_data`. The planned assertion therefore does prove the new deferred import.

---

## Verification coverage

**Source-grounding pass** (`plan_review.source_grounding: true`). `gsd_run drift-guard authority --raw` returns **`intel`**. Config names `grep`, but `intel.enabled: true` takes precedence. `.planning/intel/API-SURFACE.md` reports *"api-map.json has no entries"*, and every cited symbol is Python. Under the effective authority every symbol is therefore **UNCHECKABLE → INFO, hardBlock false** (`drift-guard severity --status UNCHECKABLE --authority intel` → `{"severity":"INFO","hardBlock":false}`). UNCHECKABLE is not counted as verified. As supplementary evidence, each symbol below was also resolved with grep or a Python probe against tracked source. No MISSING or AMBIGUOUS symbol was found.

Excluded as "Artifacts this phase produces": `LABEL_MODE_DEFAULTS`, `default_label_mode`, `_UNSET`, `_raw_label_mode_defaults`, `logger`, `_warned`, `_warned_lock`, `_invalid_label_mode`, `crud_views.E108`, `CardListView.cv_get_card_actions_label_mode`, `isolate_label_mode_warnings`, `test_settings_defers_button_data_until_checks`, `tests/test1/test_label_mode_docs.py`, every listed new test function, and the four new doc anchors.

Cycle-1 symbols (all still present, unchanged since `c1546c2`): `button_data.LOCATIONS` (`button_data.py:12`), `is_label_mode`/`LABEL_MODES` (`label_mode.py:17`, `:14`), `is_strict` (`exceptions.py:32`), `cv_button_data` (`button_data.py:52`), `_action_settings_messages` (`settings.py:98`), `cv_get_action_label_mode` (`base.py:291`), `cv_icon_mode_checks` (`buttons.py:368`), `check_viewsets` (`checks.py:20`), `cv_first_inline_keys`, `CardListView.*`, `CardAction.*`, E106/E210/E211, setting names, ViewSet fields. All UNCHECKABLE under `intel`, and grep confirms each one.

Symbols newly cited by the cycle-2 revisions:

| Symbol (kind) | Cited by | Authority verdict | Supplementary evidence |
|---|---|---|---|
| `test_import_safety.py` subprocess/textwrap pattern | 01-01-02 | UNCHECKABLE | `tests/test1/test_import_safety.py:12,14,22,33` |
| D-07 boundary (`crud_views.lib.settings` imports no view module) | 01-01-02 | UNCHECKABLE | Probe: after import and `django.setup()`, neither `crud_views.lib.view` nor `button_data` is in `sys.modules`. `check_messages` loads `lib.view.*` but not `button_data`. |
| `check_messages` is an uncached `@property` | 01-01-02 | UNCHECKABLE | `settings.py:134-135` |
| `tests/test1/conftest.py` (autouse fixture host) | 01-01-02 | UNCHECKABLE | exists; `pytest_configure` at `:23` |
| `pytest-random-order` / `pytest-xdist` (`--random-order`, `-n`) | 01-01-02, 01-02-02 | UNCHECKABLE | `pyproject.toml:74,77`; both importable in `.venv`; `addopts` at `:130` is `--strict-markers` only |
| `tests/test1/test_settings_checks.py` | 01-01-02 | UNCHECKABLE | exists |
| `_card`, `_inline`, `_author_card`, `AUTHOR_FULL`, `author_douglas_adams` | 01-03-01 | UNCHECKABLE | `test_card_label_mode_render.py:38,44,62,24`; `conftest.py:172` |
| `action_menu.py` E211 message | 01-02-02 | UNCHECKABLE | `src/crud_views/lib/view/action_menu.py:55-61` ("string-valued") |
| `base.py` attribute comments | 01-02 | UNCHECKABLE | `base.py:88-96` |
| `base.py:631` raw `target_default` pass-through | (claude A7) | UNCHECKABLE | `base.py:631` |
| Anchors `settings.md#action-menus`, `action_menus.md#label-mode` | 01-03-01 | UNCHECKABLE (doc anchors) | `docs/reference/settings.md:71`, `docs/reference/action_menus.md:58` |
| `card-list-view.md` CardAction `label_mode` row | (grok A12) | UNCHECKABLE | `docs/reference/card-list-view.md:50`, which says "inherits the view's `cv_card_actions_label_mode`" |
| `action_menus.md` System checks table (2 columns) | 01-04-01 | UNCHECKABLE | `docs/reference/action_menus.md:238-246` |
| `CHANGELOG.md` headings | 01-03-02, 01-04-02 | UNCHECKABLE | `## Unreleased` :3, `### Breaking` :7 and :282, `### Fixed` :136, `### Added` :167 |
| `button_data.py` `LABEL_MODES` import (F401 after change) | (claude A4) | UNCHECKABLE | `button_data.py:8` import; sole use at `:85` |
| `.planning/` read by tests | (claude A13) | UNCHECKABLE | no file under `tests/` references `.planning` today |
| Baseline `ebc7c23259ae…` | 01-04 | UNCHECKABLE (git object) | commit "docs(01): capture phase context" |
| Function signatures | all | UNCHECKABLE | not assertable under grep/intel |

**Cross-artifact fact-drift pass** (advisory, never counted):
- Phase status: `gsd_run drift-guard phase-status --phase 01` → `verdict: lag` (STATE.md "Ready to execute" vs ROADMAP.md "Not started"). Lag is not a finding.
- ROADMAP Success Criteria ↔ PLAN `must_haves.truths`: no contradiction. The filter toggle narrowing of "every page" is Phase 3 scope, which is `gsd-plan-checker` territory and not drift.
- ROADMAP requirements (LMOD-01…06) ↔ plan `requirements:`: the union covers all six, with no contradiction.
- CONTEXT.md Decisions ↔ PLAN term usage: no contradiction. 01-01 keeps the D-11 `(location, repr(value))` key.
- Advisory, not a judgment pair: branch naming. `.planning/config.json` uses `branching_strategy: "phase"` (`gsd/phase-{phase}-{slug}`), PROJECT.md:77 says `feat/label-mode-defaults`, and the plans say "keep current branch" (current: `introduce-gsd`). This is also listed as A19.
- Nothing was skipped: STATE.md, ROADMAP.md and CONTEXT.md were present.

**Lane diagnostics:** opencode-grok attempt 1 failed with `spawn error: ETIMEDOUT` at the 660 s floor, the same failure mode as cycle 1. Its stub carried `[reviewed-without-source-citations]` only because it contained no review, and it is preserved in `.review-diagnostics/`. The retry succeeded and cites `file:line` evidence, so no discount marker applies. The plan coverage check is complete for all three graded lanes (4/4 ids each).

## Current HIGH Concerns

None.

## Current Actionable Non-HIGH Concerns

- **A1 [MEDIUM] 01-01-01** (grok): state that the non-strict invalid-*setting* fallback callable is `LABEL_MODE_DEFAULTS[location]` and never calls `default_label_mode` again. Otherwise recovery for a bad stamp combined with a bad floor recurses.
- **A2 [LOW] 01-01-01** (gemini): the deadlock subprocess child has no `caplog`. Specify a handler or `assertLogs` on the `label_mode` logger inside the child to count 1 versus 2 warnings.
- **A3 [LOW] 01-01-01** (claude): split the bad-value list by level: whole setting, per-location mode, and stamped value. `{}` is valid as the whole setting.
- **A4 [LOW] 01-01-01** (claude): remove the now-unused `LABEL_MODES` import at `button_data.py:8`, or the ruff F401 gate fails.
- **A5 [LOW] 01-01** (claude; cycle-1 grok): a non-dict setting warns once per location queried. State the expected count (up to three) in the action and tests.
- **A6 [LOW] 01-01-01** (grok): pin the context tracer's raw keys to `test_button_leaves.py:490-499` (`cv_action_label`, `cv_icon_action`, `cv_access`). The context location does not use `cv_label`.
- **A7 [LOW] 01-02** (claude): add a non-strict render test for an invalid target-view `cv_context_action_label_mode`, which reaches the leaf raw via `base.py:631`.
- **A8 [LOW] 01-02-01** (grok; cycle-1 grok/claude): exclude the filter toggle by an explicit selector (`[@cv-key="filter"]` / `#cv-filter-toggle`) and assert a nonempty remainder.
- **A9 [LOW] 01-02-02/01-04** (claude): `"string or None"` is pinned in three places. Pin a shorter token, or accept this explicitly.
- **A10 [LOW–MEDIUM] 01-03-02/01-04** (claude): restrict links in `migrating-1.0.md` and `CHANGELOG.md` to existing anchors, and extend 01-04's retargeting scope to them. `CHANGELOG.md` is outside the mkdocs gate.
- **A11 [LOW] 01-03-02** (claude, grok): extend the verify script to check the #213 setting-before-view-before-button order, the `None` disclosure, and the Fixed bullet under the Unreleased `### Fixed`.
- **A12 [LOW] 01-03-01** (grok): update `card-list-view.md:50` (CardAction `label_mode` "inherits the view's `cv_card_actions_label_mode`") to point at the resolver or floor.
- **A13 [MEDIUM] 01-04-02** (claude): `test_label_mode_decision_handoff` reads `.planning/PROJECT.md` from the permanent test suite. Move the D-23 check to a `<verify>` grep.
- **A14 [LOW] 01-04-01** (claude): parse only Python fences that contain `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, or skip `SyntaxError` per block.
- **A15 [LOW] 01-04-02** (claude, grok): scope the #213 and Unreleased selection so it survives the 1.0 heading rename and ignores `### Breaking` at `CHANGELOG.md:282`.
- **A16 [LOW] 01-04 verification** (claude): make `git status --porcelain -- tests/test1/golden src/crud_views/templates examples` an automated command with its own `fails_when`.
- **A17 [LOW] 01-04-01** (gemini): the `action_menus.md` checks table has 2 columns. Say that the E108 row expresses "error" in the Meaning column.
- **A18 [LOW] 01-04-02** (grok): no gate validates Mermaid. Keep the `MICON` label simple (no `[`/`]`) and put the setting name in the prose link.
- **A19 [LOW] cross-plan** (claude): branch naming conflicts between config `gsd/phase-…`, PROJECT.md `feat/label-mode-defaults`, and the plans' "keep current branch". State once which one wins.
