---
phase: 01
reviewers: [opencode-gemini, opencode-grok, claude-fable]
reviewed_at: 2026-10-25T16:15:41Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md, 01-04-PLAN.md]
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

## OpenCode Review (opencode-gemini)

## 01-01

### 1. Summary
Plan `01-01` introduces the lazy `CRUD_VIEWS_LABEL_MODE_DEFAULTS` floor reader (`default_label_mode`), the immutable `LABEL_MODE_DEFAULTS` mapping (`{"context": "icon", "list": "icon", "card": "both"}`), non-strict recovery with once-per-process warning deduplication (`_invalid_label_mode`), leaf fallback wiring in `cv_button_data()`, and `crud_views.E108` validation in `CrudViewsSettings._action_settings_messages()`. Verified against `src/crud_views/lib/view/label_mode.py`, `src/crud_views/lib/view/button_data.py`, and `src/crud_views/lib/settings.py`, the design cleanly avoids the import-time snapshot trap of `from_settings()` and breaks the `button_data` ↔ `label_mode` circular import, with two medium-severity concurrency/test-isolation subtleties around `_invalid_label_mode` and `_warned` to watch during implementation.

### 2. Strengths
- **Circular import avoidance verified against module graph (`src/crud_views/lib/view/button_data.py:8`, `src/crud_views/lib/settings.py:100-102`)**: `button_data.py:8` imports `from .label_mode import LABEL_MODES, is_label_mode` at module top level, and `src/crud_views/templatetags/crud_views.py:17` imports `button_data` early. Deferring `from .button_data import LOCATIONS` inside `default_label_mode()` and `_action_settings_messages()` follows the established pattern in `src/crud_views/lib/button_classes.py:213` and keeps `tests/test1/test_import_safety.py` green.
- **Lazy fallback callable preserves strict-mode error attribution (`src/crud_views/lib/view/button_data.py:83-85`, `tests/test1/test_button_data.py:120-125`)**: Passing `fallback: Callable[[], str]` into `_invalid_label_mode` and checking `is_strict()` (`src/crud_views/lib/exceptions.py:32-36`) *before* calling `fallback()` ensures that a bad stamped `cv_label_mode` raises `ValueError` matching `"cv_label_mode"` even when `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is simultaneously invalid (fixing the eager-argument bug in `RESEARCH.md` Pattern 2).
- **Explicit `None` visibility via `_UNSET` sentinel (`src/crud_views/lib/settings.py:118-131`)**: Unlike `src/crud_views/lib/button_classes.py:124` (`getattr(settings, ..., None) or {}`), reading `getattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS", _UNSET)` distinguishes an unset setting from `CRUD_VIEWS_LABEL_MODE_DEFAULTS = None`, allowing `crud_views.E108` and `default_label_mode()` to reject explicit `None` per D-03.
- **Unhashable bad values handled safely (`tests/test1/test_button_data.py:121`)**: Keying `_warned` with `repr(value)` prevents `TypeError: unhashable type: 'list'` (or `'dict'`) when non-strict mode encounters `["both"]` or nested dicts `{"context": {"filter": "both"}}`.

### 3. Concerns
- **[MEDIUM] Potential deadlock in `_invalid_label_mode` if `_warned_lock` is a non-reentrant `threading.Lock` held across `fallback()` (`src/crud_views/lib/view/button_data.py:83-85`, `src/crud_views/lib/view/label_mode.py`)**: Task `01-01-01` specifies guarding `_warned` check-and-add with a `Lock` and passing a deferred `default_label_mode(location)` callable as `fallback` from `cv_button_data()`. In non-strict mode, `_invalid_label_mode` evaluates `fallback()` to obtain the fallback mode. If both the stamped `cv_label_mode` and `CRUD_VIEWS_LABEL_MODE_DEFAULTS[location]` are invalid (a scenario `test_same_bad_pair_warns_once_across_sources` exercises), `fallback()` calls `default_label_mode(location)`, which calls `_invalid_label_mode()` re-entrantly on the same thread. If `_warned_lock` wraps the `fallback()` call, a standard `threading.Lock` will deadlock.
- **[MEDIUM] Cross-test pollution of process-global `_warned` under `pytest-random-order` (`pyproject.toml`, `tests/test1/conftest.py:27-29`)**: Task `01-01-01` intentionally omits a `setting_changed` receiver reset for `_warned` and relies on unit tests monkeypatching `_warned`. However, `01-02-02` adds non-strict invalid-floor fallback tests in `tests/test1/test_action_label_mode_config.py` without mentioning monkeypatching `_warned`. Under `pytest-random-order`, if another test file triggers a non-strict fallback for a pair like `("context", "'nope'")` without isolating `_warned`, subsequent `caplog` tests in the same xdist worker will see the warning suppressed unless every test (or an `autouse` fixture / `setting_changed` receiver) isolates `_warned`.
- **[LOW] `LOCATIONS` is a `frozenset` in `src/crud_views/lib/view/button_data.py:12`**: Task `01-01-02` says to test `LOCATIONS` derivation in `test_e108_uses_button_locations` by "temporarily extending the imported button-data set with a test-only location". Because `LOCATIONS` is a `frozenset`, mutating it in-place is impossible; the test must replace the attribute with `monkeypatch.setattr(button_data, "LOCATIONS", button_data.LOCATIONS | {"test_loc"})`.

### 4. Suggestions
- In `_invalid_label_mode` (`src/crud_views/lib/view/label_mode.py`), either evaluate `resolved_fallback = fallback()` *before* acquiring `_warned_lock` (note that if `fallback()` itself warns on the same `(location, repr(value))` pair, the inner call will record the pair in `_warned` first), or use `threading.RLock()` and acquire the lock only around the `if key not in _warned: _warned.add(key)` block.
- Either clear `_warned` in a `setting_changed` receiver (which `01-CONTEXT.md` explicitly permits under Discretion and which never fires in production) or add a small `autouse` fixture in `tests/test1/conftest.py` (or `monkeypatch.setattr(label_mode, "_warned", set())` across all non-strict fallback tests, including `01-02-02`) so random test ordering cannot leak `_warned` state between test modules.
- In `01-01-02`, use `monkeypatch.setattr("crud_views.lib.view.button_data.LOCATIONS", frozenset({*LOCATIONS, "custom"}))` for `test_e108_uses_button_locations`.

### 5. Risk Assessment
- **Risk Level: LOW-MEDIUM** — The scope is well-contained within three existing modules (`label_mode.py`, `button_data.py`, `settings.py`), and default behavior is unchanged when `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is unset. The only meaningful risks are the re-entrant lock ordering in `_invalid_label_mode` and cross-test `_warned` isolation under `pytest-random-order`, both of which are straightforward to prevent.

---

## 01-02

### 1. Summary
Plan `01-02` wires `default_label_mode("context")` and `default_label_mode("list")` into `CrudView.cv_get_action_label_mode()` (`src/crud_views/lib/view/base.py:291-317`), protects `cv_icon_mode_checks()` (`src/crud_views/lib/view/buttons.py:405`, check `viewset.W292`) against strict-mode `ValueError` exceptions from invalid floors so `check_viewsets` (`src/crud_views/checks.py:20-28`) still returns `crud_views.E108`, and adds HTTP/unit tests across `test_context_action_label_mode.py`, `test_context_button_label_mode.py`, `test_action_label_mode_config.py`, and `test_action_label_mode_render.py`. The plan accurately reflects the precedence chain and whole-dict map replacement in `base.py`.

### 2. Strengths
- **Prevents W292 from masking E108 during `check_viewsets` (`src/crud_views/checks.py:20-28`, `src/crud_views/lib/view/buttons.py:405`)**: In `checks.py:23-28`, `check_viewsets()` assigns `errors = crud_views_settings.check_messages` and then loops over `ViewSet.checks_all()` in the same function before returning `errors`. Because `cv_icon_mode_checks` calls `cls.cv_get_action_label_mode("context", key, button, target_default)` at `buttons.py:405` *before* checking `target_cls.cv_icon_action` at `buttons.py:410`, an invalid floor with `CRUD_VIEWS_STRICT=True` (default when `DEBUG=True`) would raise `ValueError` and abort `check_viewsets()`. Wrapping line 405 in `try ... except ValueError: continue` directly prevents this failure mode.
- **Avoids eager fallback evaluation on mapped list keys (`src/crud_views/lib/view/base.py:317`)**: Replacing `mapping.get(key, "icon")` with `mapping[key] if key in mapping else default_label_mode("list")` (instead of `mapping.get(key, default_label_mode("list"))`) ensures that when `key` is present in `mapping`, `default_label_mode("list")` is never called, avoiding spurious strict-mode `ValueError` raises or non-strict log warnings when the `"list"` floor is malformed.
- **Exact match on the acceptance grep (`src/crud_views/lib/view/*.py`)**: Verified against the live repo that `grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py` currently matches only `button_data.py:83`, `base.py:312`, and `base.py:317`; after `01-01` and `01-02-02`, the grep returns exit code `1` (zero matches).

### 3. Concerns
- **[LOW] Inline class-attribute comments on `CrudView` (`src/crud_views/lib/view/base.py:88-95`) still hardcode `"icon"`**: Tasks `01-02-01` and `01-02-02` update the method docstrings at `src/crud_views/lib/view/base.py:282`, `:287`, and `:294`, but miss the three class-attribute comments at `src/crud_views/lib/view/base.py:88-95` (`# label mode per action key (#216): "label" / "icon" / "both"; unnamed keys are "icon"...` at `:88`, `...then "icon"` at `:91`, and `...None: "icon"` at `:94`).
- **[LOW] Non-strict fallback test in `01-02-02` (`tests/test1/test_action_label_mode_config.py`) can pollute `label_mode._warned`**: Task `01-02-02` tests "true fallthrough under strict/non-strict modes" in `test_action_label_mode_config.py`. Because `01-01-01` keeps `label_mode._warned` across `override_settings`, if `test_action_label_mode_config.py` does not isolate `label_mode._warned` via `monkeypatch`, it will record a warning key in the shared worker process.

### 4. Suggestions
- In `01-02-01` / `01-02-02`, also update the three inline comments on `cv_list_actions_label_mode`, `cv_context_actions_label_mode`, and `cv_context_action_label_mode` at `src/crud_views/lib/view/base.py:88-95` so they reference `CRUD_VIEWS_LABEL_MODE_DEFAULTS` instead of `"icon"`.
- In `01-02-02`, ensure the non-strict fallthrough test in `tests/test1/test_action_label_mode_config.py` resets or monkeypatches `label_mode._warned` if `01-01` does not clear `_warned` on `setting_changed`.

### 5. Risk Assessment
- **Risk Level: LOW** — Changes to `src/crud_views/lib/view/base.py` and `src/crud_views/lib/view/buttons.py` are surgical (two fallback expressions, one `try/except ValueError` guard, and comments/docstrings) and are well-covered by existing golden and rendering tests.

---

## 01-03

### 1. Summary
Plan `01-03` changes `CardListView.cv_card_actions_label_mode` from `"both"` to `None` (`src/crud_views/lib/views/card.py:28`), adds the public `@classmethod def cv_get_card_actions_label_mode(cls) -> str` resolver, skips `viewset.E210` when the attribute is `None` (`src/crud_views/lib/views/card.py:112`), updates `src/crud_views/lib/view/card.py:12`, `docs/reference/card-list-view.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`, and updates/extends `tests/test1/test_card_label_modes.py` and `tests/test1/test_card_label_mode_render.py`. Verified against `src/crud_views/lib/views/card.py` and `mkdocs.yml`, the plan is cohesive and properly sequences cross-doc anchor verification after Wave 3.

### 2. Strengths
- **Consistent `@classmethod` resolver and `E210` check guard (`src/crud_views/lib/views/card.py:28, 46-52, 102-119`)**: Implementing `cv_get_card_actions_label_mode(cls) -> str` as a `@classmethod` matches `cv_get_card_actions_inline(cls)` (`src/crud_views/lib/views/card.py:102-105`), and guarding line 112 with `if cls.cv_card_actions_label_mode is not None:` matches the per-action check guard at `src/crud_views/lib/views/card.py:117-118` (`if action.label_mode is not None:`).
- **Simultaneous update of existing pinned test (`tests/test1/test_card_label_modes.py:14-15, 38-48`)**: `test_card_label_modes.py:14-15` currently asserts `CardListView.cv_card_actions_label_mode == "both"`. Updating it in `01-03-01` alongside `src/crud_views/lib/views/card.py:28` prevents an immediate test regression in Wave 2.
- **Correct deferral of `mkdocs build --strict` to Wave 3 (`mkdocs.yml:24-25`, `docs/reference/card-list-view.md`)**: `mkdocs.yml:24-25` configures `validation: anchors: warn`, which causes `mkdocs build --strict` to fail if a target `#anchor` does not exist yet. Since `01-03-01` links to `action_menus.md#card-label-mode-resolution` and `settings.md#label-mode-configuration` (created in `01-04-01`), deferring the strict MkDocs build to `01-04` while keeping `## Label mode` (`#label-mode`) in `docs/reference/card-list-view.md:57` avoids a Wave 2 false failure.

### 3. Concerns
- **[LOW] `AuthorCardListView` default actions include `CardAction(key="delete", no_label=True)` (`tests/test1/app/views.py:76-81`)**: On `AuthorCardListView`, `detail` and `update` have `label_mode=None` and `no_label=False`, whereas `delete` sets `no_label=True` (`views.py:80`). Because `action.no_label` precedes `self.cv_get_card_actions_label_mode()` (`src/crud_views/lib/views/card.py:49-52`), rendering `AuthorCardListView` with `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` without overriding `cv_card_actions` will render `detail` and `update` as label-only while `delete` remains icon-only. Task `01-03-01`'s `test_card_floor_renders_label_only` should either assert `detail`/`update` are label-only while `delete` stays icon-only, or pass explicit `CardAction` items via `_author_card()` (`tests/test1/test_card_label_mode_render.py:62-64`).
- **[LOW] Existing `#213` bullet in `CHANGELOG.md:43-45` under `## Unreleased` → `### Breaking` lists only per-view and per-button options**: `CHANGELOG.md:43-45` (in the same `## Unreleased` section) currently states: ``CardListView.cv_card_actions_label_mode = "label"` restores the old markup for a view; `CardAction(label_mode="label")` for one button.`` Adding a separate `### Breaking` bullet for "Card label-mode attribute" without mentioning `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` at line 44 leaves line 44 out of sync with the updated recipe in `docs/migrating-1.0.md:127-129`.

### 4. Suggestions
- In `tests/test1/test_card_label_mode_render.py`, have `test_card_floor_renders_label_only` test `AuthorCardListView`'s stock `cv_card_actions` (`tests/test1/app/views.py:76-81`) by asserting `_icons(_inline(card, "detail")) == []`, `_icons(_inline(card, "update")) == []`, and `len(_icons(_inline(card, "delete"))) == 1` — this simultaneously proves `{"card": "label"}` works on an untouched view AND that `no_label=True` still wins over the floor (D-14, D-18).
- In `01-03-02`, also prepend `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` to `CHANGELOG.md:44` (or cross-reference it) so the `#213` Unreleased bullet and `docs/migrating-1.0.md:127-129` give the same setting-first restoration order.

### 5. Risk Assessment
- **Risk Level: LOW** — The Python attribute default change (`"both"` → `None`) is a documented pre-1.0 breaking change for raw attribute readers, while default rendered HTML remains byte-identical and all internal callers go through `cv_get_card_actions_label_mode()`.

---

## 01-04

### 1. Summary
Plan `01-04` completes the canonical documentation in `docs/reference/settings.md`, `docs/reference/action_menus.md`, `docs/reference/context_buttons.md`, and `docs/reference/buttons.md`, updates `.planning/PROJECT.md` for the D-19/D-20 handoff to Phase 7, adds `tests/test1/test_label_mode_docs.py` (which parses the documented `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` example with `ast.literal_eval` and renders it through `{% cv_button %}`), and runs all phase quality gates (`pytest`, `npm test`, `mkdocs build --strict`, `ruff`, and protected-path `git diff`).

### 2. Strengths
- **Correctly locates the Mermaid diagram in `docs/reference/context_buttons.md:256` and prose at `:315`**: The source plan (`superpowers/plans/2026-10-24-concept-review-followups.md:93`) mistakenly placed the `MICON` Mermaid node in `action_menus.md`. Plan `01-04-02` targets the actual location (`docs/reference/context_buttons.md:256`, `M4 -- "no" --> MICON["icon"]`, and `:262, 305`) as well as the prose sentence immediately below the diagram at `docs/reference/context_buttons.md:315`.
- **Preserves existing anchor targets across `docs/reference/` (`mkdocs.yml:24-25`)**: Keeping `## Label mode` (`#label-mode`) and `### Target-view default` (`#target-view-default`) in `docs/reference/action_menus.md:58, 91` while adding `### Context label-mode resolution`, `### List label-mode resolution`, and `### Card label-mode resolution` ensures existing inbound links (`docs/reference/settings.md:78`, `docs/reference/card-list-view.md:81`, `docs/reference/context_buttons.md:318`) and new inbound links from `01-03-01` both pass `mkdocs build --strict`.
- **Avoids duplicate rows in `.planning/PROJECT.md:94-95` and fixes stale Out-of-Scope text at `.planning/PROJECT.md:37`**: Verified against `.planning/PROJECT.md` that lines 94-95 already contain the D-19 and D-20 rows in the Key Decisions table while line 37 still says `Renaming the cv_context_actions_label_mode / cv_context_action_label_mode pair — tracked separately`. Task `01-04-02` explicitly accounts for this current file state.
- **Safe executable doc test (`tests/test1/test_label_mode_docs.py`)**: Using `ast.parse` + `ast.literal_eval` to extract the `CRUD_VIEWS_LABEL_MODE_DEFAULTS` dict from `docs/reference/settings.md` and feeding it into `override_settings` + `{% cv_button %}` verifies the documented example end-to-end without `exec`.

### 3. Concerns
- **[LOW] `docs/reference/buttons.md:435-448` (`## System checks`) is not updated alongside `docs/reference/action_menus.md:236-247`**: Task `01-04-02` edits `docs/reference/buttons.md:423-424`, right above `## System checks` (`docs/reference/buttons.md:435-448`). In that table, line 445 says `viewset.E210` fires when `CardAction.label_mode`, `cv_card_actions_label_mode`, `ContextButton.label_mode` or `cv_context_action_label_mode` `is not one of "label", "icon", "both"` (omitting `None` when unset), and `crud_views.E108` (and `E106`) are absent from the table even though `E210`, `E211`, `W291`, and `W292` are listed there.
- **[LOW] Hardcoded commit SHA in `<verification>` (`ebc7c23259ae35b2e4f34047d0da903e68a48ac8`) vs `.planning/STATE.md:10` (`02342703bcb65a94dcb8d1117721c828850a81fa`)**: `01-04` `<verification>` states "The baseline is the pre-planning STATE.md state_head" and runs `git diff --exit-code ebc7c23259ae35b2e4f34047d0da903e68a48ac8 -- tests/test1/golden src/crud_views/templates examples`, whereas `.planning/STATE.md:10` now records `state_head: 02342703bcb65a94dcb8d1117721c828850a81fa`. (Both commits have identical trees for those three paths, so the command still succeeds.)

### 4. Suggestions
- In `01-04-02`, also add `crud_views.E106` and `crud_views.E108` to the `## System checks` table in `docs/reference/buttons.md:437-448` (or clarify `None` on `viewset.E210` at line 445) so `buttons.md` and `action_menus.md:238-246` stay consistent.
- Ensure `test_documented_card_floor_renders_label_only` in `tests/test1/test_label_mode_docs.py` passes `cv_access=True`, `cv_url="/u/"`, `cv_key="detail"`, `cv_label="Details"`, and `cv_icon_action="detail"` into `Context` when rendering `{% load crud_views %}{% cv_button "card" %}` (`src/crud_views/templatetags/crud_views.py:200-208`), so `cv_resolve_action()` does not return `None` (`crud_views.py:205-207`) and so an icon would have rendered if the mode were still `"both"`.

### 5. Risk Assessment
- **Risk Level: LOW** — Plan `01-04` modifies only documentation, `.planning/PROJECT.md`, and a new documentation test file (`tests/test1/test_label_mode_docs.py`), and gates completion on the full test suite, Vitest, `mkdocs build --strict`, and Ruff.

---

## Cross-Plan Summary & Overall Risk Assessment

- **Wave & Dependency Structure**: Wave 1 (`01-01`) → Wave 2 (`01-02` and `01-03` in parallel) → Wave 3 (`01-04`) is sound. File ownership between `01-02` and `01-03` is completely disjoint (`base.py`, `buttons.py`, and context/list test files in `01-02` vs `views/card.py`, `view/card.py`, card tests, `card-list-view.md`, `migrating-1.0.md`, and `CHANGELOG.md` in `01-03`).
- **Unclassified Probe Assumptions (`EDGE-LMOD-04-unclassified` in `01-01`, `EDGE-LMOD-02-unclassified` in `01-02`)**:
  - Verified against all `src/` occurrences of `cv_button_data`, `cv_get_action_label_mode`, and `cv_card_actions_label_mode` that no other label-mode floor consumers exist in Phase 1 (`tags/context_action_filter.html:3` is explicitly scoped to Phase 3 / Plan 1B, and form buttons to Phase 6 / Plan 2).
  - Verified that lazy `getattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS", _UNSET)` on every `default_label_mode()` call handles nested `override_settings` enter/exit without cache staleness.
- **Overall Risk: LOW** — Addressing the `_warned_lock` re-entrancy order in `01-01` and ensuring `_warned` isolation across test files (`01-01` / `01-02`) eliminates the only non-trivial runtime/test hazards.


---

## OpenCode Review (opencode-grok)

> Lane note: the first attempt ended in `spawn error: ETIMEDOUT` (host suspend during the run; stub carried `[reviewed-without-source-citations]` because it contained no review). The lane was re-run per the timeout guidance; the review below is the successful retry and cites `file:line` evidence, so no discount marker applies.

I'll review the four plans against the source, not the plan text alone. Loading the package skill and opening the files the plans cite.
Planning files aren't where the glob expected them. I'll read the cited source and tests next and check the claims against those.
## 01-01

The floor, the strict/log recovery, and E108 are specified against the real call sites. The leaf path, the import cycle, and the check/render split are right. Two verification holes can still produce a green task that does not lock the decisions.

**Strengths**
- The import cycle is real: `button_data.py:8` imports `label_mode`, and `LOCATIONS` lives at `button_data.py:12`. Deferring that import matches `button_classes.py:213`.
- No Pydantic field is the correct exception. `crud_views_settings = CrudViewsSettings()` is built at `settings.py:279`, and `from_settings()` runs at class definition. A typed field would raise before E108. E108 is free (`settings.py:187` is E107).
- Raising before the fallback callable is required. `test_button_data.py:122-125` matches `cv_label_mode`, and `conftest.py:27-29` runs the suite strict. A floor error that fires first would break that test.
- `ctx.get("cv_label_mode") or …` at `button_data.py:83` is falsey-preserving. Keeping `or` (not `is None`) is what keeps goldens stable.
- `cv_button` returns `""` when `cv_resolve_action` hides the action (`visibility.py:14-18`). Requiring `cv_access=True` stops a vacuous tracer.

**Concerns**
- **MEDIUM:** Warn-once state is process-global and is not cleared on `setting_changed`, while the suite uses `pytest-xdist` and `pytest-random-order` (`pyproject.toml:74,77`). Isolation is only "monkeypatch `_warned`". One test that forgets that shares a `(location, repr(value))` with another and flakes. D-11 allows process-wide once; the research receiver was the test harness, and this plan drops it.
- **MEDIUM:** "Extending the imported button-data set" cannot be `LOCATIONS.add()`. It is a `frozenset` (`button_data.py:12`). E108 imports `LOCATIONS` inside the method, so only a monkeypatch of `button_data.LOCATIONS` is visible. A local alias or an in-place add fails or tests nothing.
- **MEDIUM:** `tests/test1/test_import_safety.py:1-10` does not import `settings.py`. The verify command does not prove D-07. A module-level view import can still pass that file.
- **LOW:** A non-dict setting warns once per location queried, while E108 emits one message. Consistent with D-11, easy to mis-test as "one warning total".

**Suggestions**
- Add an autouse fixture that clears `_warned`, and still assert one log line inside a test. Do not add a production `setting_changed` reset if D-11 stays literal.
- Pin the LOCATIONS test as `monkeypatch.setattr(button_data, "LOCATIONS", LOCATIONS | {"extra"})`.
- Add a subprocess import of `crud_views.lib.settings` that asserts `button_data` is not in `sys.modules` before `check_messages` runs.

**Risk Assessment:** MEDIUM. The design matches D-08–D-13 and the source contracts. The risk is test isolation and a check that does not actually lock the import rule.

## 01-02

This plan is the one that makes the setting real for toolbars and rows, and it correctly refuses the eager `dict.get` default. The W292 escape is a real bug in the current check runner, and the planned catch is in the right function.

**Strengths**
- `checks.py:23-28` builds E108, then iterates `ViewSet.checks_all()` in the same function. `base.py:193` yields `cv_icon_mode_checks`, which calls `cv_get_action_label_mode` at `buttons.py:405`. A strict `ValueError` there discards E108. Narrow `try/except` around that call is the right fix. Invalid `target_default` is already coerced to `None` at `buttons.py:402-404`.
- `return mapping.get(key, default_label_mode("list"))` would call the accessor even when the key exists (`base.py:317`). The membership branch is mandatory, and the plan says so.
- `target_default or "icon"` at `base.py:312` short-circuits. Replacing only the `"icon"` side preserves "explicit target beats floor". No test view sets `cv_context_action_label_mode`, so unmapped toolbar keys do reach the floor.
- Filter exclusion is required, not optional. `context_action_filter.html:3` hardcodes `"icon"`, and line 7 always sets `title`. `FilterContextButton` also has its own template (`buttons.py:303-306`), so W292 already skips it (`buttons.py:389-395`).
- Helpers the plan names exist: `_client`, `_toolbar`, `_button` in `test_action_label_mode_render.py:29-72`; `_has_icon_and_text` in `test_context_action_label_mode.py:40-41`.
- The literal gate matches the only three hits: `button_data.py:83`, `base.py:312`, `base.py:317`. After 01-01, only the `base.py` lines remain, and this plan owns them.

**Concerns**
- **LOW:** `_toolbar` returns the whole `fieldset[@cv-context-container]` (`test_action_label_mode_render.py:39-42`), which includes `#cv-filter-toggle`. A loop over every `button` will fail the "no title" assertion even when the floor works. The plan says to exclude custom templates; the helper does not.
- **LOW:** `continue` on any `ValueError` from that call will also hide a future caller bug. Acceptable if the `except` stays on that one line, as written.
- **LOW:** The phase grep is `lib/view/*.py`. The card literal `= "both"` is in `lib/views/card.py:28`, so this gate can pass before 01-03. 01-03's rewritten `test_default_is_both` is the real guard.

**Suggestions**
- Assert by `cv-key`, and skip `filter` plus any node with `id="cv-filter-toggle"`. Require a nonempty allowlist on list, detail, create, update, and card.
- In the context branch, write `return target_default or default_label_mode("context")`, not an eager `floor = default_label_mode(...)` above the `or`. The list task already states the eager-evaluation rule; the context task should too.
- In the `check_viewsets` test, assert some other existing message is still present, not only E108.

**Risk Assessment:** LOW. Precedence, the check crash, and the filter boundary match the code. The remaining risk is a broad DOM assertion, and the plan already forbids it.

## 01-03

The attribute change, the resolver, and the migration note match D-14–D-18 and the current resolution chain. The HTTP assertion will fail if it treats every card action on the fixture view as label-only.

**Strengths**
- Today the chain is `CardAction.label_mode`, then `no_label` → `"icon"`, then the attribute (`views/card.py:47-52`). The plan keeps that order and only replaces the last step. `AuthorCardListView` does not override the attribute, so `None` inherits and `default_label_mode("card")` still yields `"both"`. Unconfigured goldens stay byte-identical.
- E210 is unconditional at `views/card.py:112`, and `is_label_mode(None)` is false (`label_mode.py:17-18`). Skipping the yield only when the attribute is `None` is required. Empty string, `"Both"`, and lookalikes still fail the check.
- `test_default_is_both` (`test_card_label_modes.py:14-15`) will fail until rewritten. The plan names that rewrite.
- `docs/migrating-1.0.md:127-129` still tells readers to set the attribute, and does not say it will read `None`. The Breaking bullet is necessary, not cosmetic. `CHANGELOG.md:7` is the Unreleased `### Breaking` section the verify script splits on.
- No template reads `cv_card_actions_label_mode`. `action.html:8` reads only the stamped `cv_label_mode`. The acceptance note can say templates need no change.

**Concerns**
- **MEDIUM:** `AuthorCardListView` keeps `CardAction(key="delete", no_label=True)` on purpose (`tests/test1/app/views.py:79-80`). Under `{"card": "label"}` that button stays icon-only. Acceptance text "text-only card actions" will fail if the test does not exclude `no_label`. D-18 says that alias stays.
- **LOW:** An empty-string attribute is not `None`, so the resolver returns `""`, E210 fires, and `cv_button_data`'s `or` then treats the stamp as unset and uses the floor. Do not assert that `""` raises at render.
- **LOW:** `card-list-view.md` will link to `#card-label-mode-resolution` and `#label-mode-configuration` before 01-04 creates them. Wave order is correct, and this plan does not run `mkdocs`. A mid-wave strict docs build fails until 01-04.

**Suggestions**
- Assert `detail` and `update` are text-only, and assert `delete` is still icon-only with no `DeprecationWarning`.
- Keep the label-mode decision above the `child_name` branch (`views/card.py:47-52`), so both URL shapes share it.

**Risk Assessment:** LOW. The break is limited to readers of the raw attribute, and both required docs are in this plan. The fixture's `no_label` button is the only likely false failure.

## 01-04

The doc contract matches the code that 01-01–01-03 will have produced, and the gates are real. One existing settings sentence can survive and contradict the new table.

**Strengths**
- Mermaid node `MICON` is referenced at `context_buttons.md:256`, `:262`, and `:305`. Keeping the id and changing the label is the only safe edit.
- `action_menus.md:70` and `:83-84` still say the floor is `"icon"`. Replacing that with three canonical headings is what D-25 asks for. `menu_item.html` never branches on `cv_label_mode`, so "menu items stay icon plus text" is true.
- `ast.literal_eval` of one assignment, then `override_settings` and the real `cv_button` tag, locks the recipe to output. Rendering `location="card"` is required; a context render would ignore `{"card": "label"}`.
- D-19/D-20 rows already exist at `.planning/PROJECT.md:96-97`. The stale rename bullet is still at line 55 ("tracked separately"). The plan updates that wording and forbids a second row.
- Gates check out: `package.json` script `test` is `vitest run`; baseline `ebc7c23259ae35b2e4f34047d0da903e68a48ac8` is an ancestor; `git diff` of that SHA against `tests/test1/golden`, `src/crud_views/templates`, and `examples` is empty.

**Concerns**
- **MEDIUM:** `docs/reference/settings.md:78` says context-map keys not named are `` `icon` ``. The task adds a new table and a new row, and does not say to rewrite that sentence. After 01-04 a reader of the old row still sees a literal icon floor.
- **LOW:** The card tracer must pass `cv_access=True` (`visibility.py:14-18`) and `cv_icon_action` if it asserts an icon is absent rather than an empty render. 01-01 states this; 01-04 only says "authorized raw card-action data".
- **LOW:** The protected-path gate fails closed if that SHA is rebased away. That is the right failure, but it is not a content check of untracked new files. The plan already says to inspect `git status` for those. Keep that step.

**Suggestions**
- In the same edit as the new table, change `settings.md:78` to "keys not named fall through to the target-view default, then `CRUD_VIEWS_LABEL_MODE_DEFAULTS`" and point at `#label-mode-configuration`.
- Have `test_label_mode_configuration_table` fail if the Action menus row still contains "keys not named are `icon`".

**Risk Assessment:** LOW. Precedence, names, and gates match the repo. The stale settings sentence is the one doc hole that a strict MkDocs build will not catch.

## Cross-plan

Wave order is sound. 01-02 and 01-03 do not share files. Both depend only on 01-01's accessor. 01-04 depends on both, which is when the anchors 01-03 links to must exist. Default output stays `"icon"` / `"icon"` / `"both"`, so goldens do not depend on wave-2 order.

**EDGE-LMOD-04 (do not auto-dismiss):** No extra lifecycle is required if the accessor keeps reading `django.conf.settings` on every call and never caches the merge. Nested `override_settings` then works without a `setting_changed` receiver. Confirm that in the 01-01 summary. A cache added later reopens the edge.

**EDGE-LMOD-02 (do not auto-dismiss):** The in-scope consumers are exactly the three grep hits plus the card attribute at `views/card.py:52`, stamped through `base.py:633` and `views/card.py:68,86`. `context_action_filter.html:3` is a fourth consumer and is correctly left for Phase 3. No other `cv_label_mode` stamp exists under `src/`.

The theme-policy prohibition is not violated: no theme knob is added. The transparency prohibition is the 01-03 Breaking entry; it is not done until that bullet says the attribute reads `None` and the render does not change.

**Overall risk: MEDIUM.** The phase achieves LMOD-01–LMOD-06 if all four plans land. Nothing here is a wrong mechanism. The items that can still slip through are warn-once flakes, a frozenset "extend" that does not patch the module global, a card assertion that ignores `no_label`, and the old settings sentence that still says the floor is `icon`.


---

## Claude Review (claude-fable)

# Phase 01 Plan Review: Label-mode defaults

Verification method: I read every source, test and docs file the four plans cite and checked each line reference and mechanism claim against the working tree at `28e3e79` (branch `introduce-gsd`). All cited literals exist where the plans say. Findings below cite the evidence.

## 01-01

**Summary.** The plan correctly locates the three fallback literals and the production crash it fixes, picks the right home for the accessor, and avoids the import cycle. Its one deliberate deviation from research, the warn-once key without a source dimension and without a signal reset, is weaker than the research design and rests on a mistaken premise about production cost. E108 placement and wording are sound.

**Strengths**
- The target literal is exactly where claimed: `src/crud_views/lib/view/button_data.py:83` reads `ctx.get("cv_label_mode") or ("both" if card else "icon")`, and `:84-85` raise `ValueError` unconditionally. That raise is the production crash D-10 fixes.
- Keeping the `or` preserves falsy-stamp behaviour. `tests/test1/test_button_data.py:106-109` (`test_card_empty_label_forces_icon`) and the goldens depend on an empty stamp falling to the default.
- The circular-import hazard is real. `button_data.py:8` imports `label_mode`, so a deferred `LOCATIONS` import inside `default_label_mode` is required. The same approach already exists at `src/crud_views/lib/button_classes.py:213`.
- Lazy `_raw_label_mode_defaults()` with a sentinel is correct for D-03. `button_classes.py:124` uses `or {}`, which would hide an explicit `None`; the plan rightly does not copy that.
- E108 placement next to E106 matches `src/crud_views/lib/settings.py:98-132`, which already uses the deferred-import pattern at `:100-102` and the `got {value!r}` wording at `:127-128`.
- The strict switch exists as described: `src/crud_views/lib/exceptions.py:32-36`. The test suite runs strict (`tests/test1/conftest.py:27-29`), so the plan's insistence on `override_settings(CRUD_VIEWS_STRICT=False)` for fallback tests is necessary.
- The tracer through the real tag is viable. `src/crud_views/templatetags/crud_views.py:200-208` calls `cv_button_data(ctx, location, kind)` on the flattened context, so a raw dict with no `cv_label_mode` hits the floor. `tests/test1/test_button_leaves.py:479-504` already renders `{% cv_button "context" %}` from a raw dict with `cv_access: True`.
- The "test pins `set(LABEL_MODE_DEFAULTS) == LOCATIONS`" check works with a `MappingProxyType` and a `frozenset`.
- Deferring the W292 integration test to 01-02 is correct. Until `base.py:312` changes, `cv_get_action_label_mode` never calls the accessor, so the check-time raise is unreachable after 01-01 alone.

**Concerns**
- **MEDIUM. Warn-once key and no reset.** The plan drops the `source` dimension and keeps `_warned` across `setting_changed`, arguing this honours "once per process". But `setting_changed` is only sent by `override_settings` and test utilities, never in production. A receiver like `button_classes.py:111-114` costs nothing in production and removes the xdist and random-order fragility that research Pitfall 5 describes. Without it, every caplog test must remember to monkeypatch `_warned`. Dropping `source` also means a bad setting value warns once for `("context", "'nope'")` and then suppresses the differently worded warning for a later bad stamped `cv_label_mode="nope"`. The plan even pins that suppression in `test_same_bad_pair_warns_once_across_sources`. D-11 says the mechanism is the agent's choice, so the research design is permitted.
- **LOW. Lock is over-engineering.** `set.add` is atomic under the GIL and a duplicated warning under a race is harmless. `_warned_lock` adds code with no benefit.
- **LOW. "Temporarily extending" `LOCATIONS`.** `button_data.py:12` is a `frozenset`. The test must `monkeypatch.setattr(button_data, "LOCATIONS", LOCATIONS | {"x"})`. That works only because both E108 and the accessor import it at call time. The plan should say so, or an executor may try `.add()`.
- **LOW. Non-dict setting at render.** The plan chooses strict raise for an explicit `None` setting at every render. That is consistent with D-03, but a project that writes `CRUD_VIEWS_LABEL_MODE_DEFAULTS = None` in a `DEBUG=True` dev server gets a 500 on every page in addition to E108. The CONTEXT locks only the check behaviour; the plan should state the runtime choice in the docs.

**Suggestions**
- Key the dedup set by `(source, location, repr(value))` and add a `setting_changed` receiver that clears it for `CRUD_VIEWS_LABEL_MODE_DEFAULTS` and `CRUD_VIEWS_STRICT`. Drop the lock.
- Note in the task that the E108 `LOCATIONS` test replaces the module attribute with a new frozenset.
- Keep the strict `ValueError` text for a bad stamp containing the literal substring `cv_label_mode`. `tests/test1/test_button_data.py:120-125` matches on it.

**Risk Assessment: LOW-MEDIUM.** The core design is right. The warn-once choice is the only item likely to produce flaky tests.

## 01-02

**Summary.** The plan integrates the floor at the two remaining literal sites without touching precedence, and it correctly identifies that a strict raise inside the W292 generator would discard E108. The eager `dict.get` default trap is called out. The test plan uses existing helpers that exist. One scope claim ("every page") needs the filter exclusion it already states.

**Strengths**
- Both literals are where claimed. `src/crud_views/lib/view/base.py:312` is `return target_default or "icon"` and `:317` is `return mapping.get(key, "icon")`. My grep over `src/crud_views/lib/` and `docs/` finds no other `or "icon"` or `get(key, "icon")`, so the acceptance grep will go clean once these two change.
- The precedence claim matches the code. `base.py:302-312` reads view map, then button, then resolved map, then `target_default`, then the literal. Changing only the last step is correct.
- Refusing `mapping.get(key, default_label_mode("list"))` is right. Python evaluates the default eagerly, so a mapped key would still evaluate the floor and could raise in strict mode or log.
- The W292 hazard is real. `src/crud_views/checks.py:23-27` collects settings messages and then iterates `ViewSet.checks_all()` in the same function; `src/crud_views/lib/viewset/__init__.py:155-162` is a plain generator. An exception from `cv_icon_mode_checks` at `src/crud_views/lib/view/buttons.py:405` escapes and E108 is lost. The narrow `try/except ValueError` mirrors the existing "invalid counts as unset" handling at `:401-404`.
- `buttons.py:405` is the only check-time caller of `cv_get_action_label_mode`. The other caller, `base.py:631`, is render-time. So the catch covers the whole check path.
- Success criterion 1 ("W292 stops firing") follows automatically: with a `both` floor, `:405` returns a non-`icon` mode and the generator continues.
- The named test helpers exist: `_client`, `_toolbar`, `_rows`, `_detail_url`, `_button` in `tests/test1/test_action_label_mode_render.py:29-72`, `_has_icon_and_text` at `test_context_action_label_mode.py:40-41`, `_w292` and `_target` in `test_context_button_label_mode.py`.
- The test app sets no label-mode overrides. A grep of `tests/test1/app/views.py` for `label_mode` finds nothing, so unmapped keys really reach the floor.

**Concerns**
- **LOW. "Every page" needs care on the list and card pages.** Their default toolbar is `["parent", "list", "filter", "create"]` (`settings.py:77-79`). `filter` has its own template (`context_action_filter.html`) and `list` is the active page. The plan already excludes the filter toggle. The test should also tolerate the active button, or assert on `create` and `parent` only.
- **LOW. Non-dict map values.** With `key in mapping` on a view attribute that is a string, Python does a substring test and `mapping[key]` raises `TypeError`. Today's `mapping.get` raises `AttributeError` on the same input, so this is not a regression, and E211 reports it. Worth a comment, not a change.
- **LOW. Shared test file with 01-01.** Both plans edit `tests/test1/test_action_label_mode_config.py`. They are sequential waves, so no conflict, but the SUMMARY of 01-01 should list which E108 tests it added so 01-02 extends rather than duplicates.

**Suggestions**
- In the integration test, call `crud_views.checks.check_viewsets()` and assert `any(m.id == "crud_views.E108" for m in msgs)` rather than an exact list. Other viewset checks in the test app may emit unrelated messages.
- Update the three docstrings at `base.py:282`, `:287` and `:294` in the same task, as the plan says. Avoid writing `or "icon"` in prose, or the acceptance grep will match the docstring.

**Risk Assessment: LOW.** The changes are two lines plus a guard, and the hazards are already identified.

## 01-03

**Summary.** The card slice is correct and small. The attribute, resolver, check and docs change together as D-14 requires, the `no_label` branch stays, and the CHANGELOG plus migration handling follow the AGENTS.md rule. The one real issue is that 01-03 writes two cross-page links whose anchors 01-04 creates, and `mkdocs.yml` promotes missing anchors to warnings, which `--strict` turns into a failure.

**Strengths**
- All three card sites are where claimed: `src/crud_views/lib/views/card.py:28` (attribute), `:47-52` (resolution with `no_label` at `:49-50`), `:112` (unconditional E210 yield). The conditional-yield pattern to copy is at `:117-118`.
- `cv_get_card_actions_inline` at `:102-105` is a `@classmethod`, so the new resolver as a classmethod matches its sibling.
- The existing test that pins the old default is `tests/test1/test_card_label_modes.py:14-15`. The plan replaces it. `test_good_values_yield_no_check` at `:38-48` is the right place to add `None`.
- `test_view_default_applies_and_action_overrides_it` at `tests/test1/test_card_label_mode_render.py:120-137` already exercises the per-view attribute, so the new floor test can mirror it with `override_settings`.
- No template reads the attribute. A grep of `src/crud_views/templates` finds no `cv_card_actions_label_mode`, which supports the "no Tabler template change" acceptance note.
- The CHANGELOG verify script is sound: `## Unreleased` is at `CHANGELOG.md:3` and its `### Breaking` at `:7`, so splitting on the first `### Breaking` lands in the right section.
- `docs/migrating-1.0.md:127-129` holds the recipe to reorder, and `:44-48` holds the check-ID list to extend with E108.

**Concerns**
- **MEDIUM. Red docs gate between waves.** `mkdocs.yml:24-25` sets `validation: anchors: warn`. Under `--strict`, a link to a missing anchor fails the build. 01-03 adds links to `action_menus.md#card-label-mode-resolution` and `settings.md#label-mode-configuration`, which only exist after 01-04. The plan admits this, but its own `<verification>` block never runs mkdocs, so a phase that stops after wave 2 leaves the repo with a failing quality gate on the branch.
- **LOW. Empty-string attribute at render.** With `is not None` guarding both the E210 yield and the resolver, an attribute of `""` passes through the resolver, is stamped as `""`, and then falls to the floor through the `or` in `button_data.py:83`. E210 still fires, so the behaviour is the same as today. The plan's truth "an empty-string attribute still produces E210" is accurate; just do not describe the resolver as "always returns a valid mode".
- **LOW. Stale wording outside any plan's file list.** `src/crud_views/lib/view/action_menu.py:59` and `docs/reference/action_menus.md:244` describe `cv_card_actions_label_mode` as "string-valued". After this plan it is `str | None`. `tests/test1/test_action_label_mode_config.py:113-116` only asserts the attribute name, so nothing breaks, but no plan owns `action_menu.py`.

**Suggestions**
- Either move the two forward links from `card-list-view.md` into 01-04, or have 01-03 link to the existing `action_menus.md#label-mode` anchor and let 01-04 retarget it. Alternatively, add a one-line mkdocs check to 01-03's verification so the failure is visible at the wave boundary.
- Add `action_menu.py:59` and `action_menus.md:244` to the docstring touch list ("string or None").

**Risk Assessment: LOW.** The code change is a handful of lines with existing test scaffolding. The docs-gate ordering is the only process risk.

## 01-04

**Summary.** The docs plan is thorough and its executable-example test is a good idea. The headings and anchors it introduces match the links 01-03 writes. The final gate list matches the project constraints and uses tools that exist locally. Two provenance details are wrong but harmless.

**Strengths**
- The Mermaid node is at `docs/reference/context_buttons.md:256` as `MICON["icon"]`, referenced at `:262` and `:305`. Keeping the id and changing only the label is the correct minimal edit.
- The settings table to extend is `docs/reference/settings.md:71-79`; line 78 contains the "keys not named are `icon`" wording the plan says to replace. The canonical-order prose to replace is `docs/reference/action_menus.md:70` and `:83-84`; the singular/plural table already exists at `:115-120`.
- `docs/reference/buttons.md:423-424` says the card default is `"both"` on the attribute, which the plan rewords.
- `PROJECT.md:96-98` already has the D-19, D-20 and E108 rows, so "preserve without duplication" is accurate. The stale Out of Scope bullet is at `PROJECT.md:55`.
- The gate commands are runnable. `package.json:11` defines `"test": "vitest run"`, `tests/test1/test_import_safety.py` exists, and `git diff --stat ebc7c23 HEAD -- tests/test1/golden src/crud_views/templates examples` is empty today, so the protected-path check starts from a clean baseline.
- Parsing the documented setting with `ast.literal_eval` rather than `exec` is the right call for a docs-driven test.

**Concerns**
- **LOW. Baseline provenance is misstated.** The plan calls `ebc7c23` "the pre-planning STATE.md state_head". `STATE.md:10` records `02342703`. `ebc7c23` is the "capture phase context" commit, five commits earlier. Both predate implementation and the diff is empty for either, so the gate works, but the justification text is wrong.
- **LOW. Fragile example extraction.** The plan puts two standalone assignments in `settings.md` (`{"card": "label"}` and `{"context": "both"}`) and tells the test to parse "only the standalone card assignment". The test needs a deterministic selector, for example the first fenced block whose parsed dict has key `card`, or it will break the first time a docs editor reorders examples.
- **LOW. Anchor slugs not machine-verified here.** I could not run the slugify check in this session. Under Python-Markdown's default `slugify` the four headings should produce `label-mode-configuration`, `context-label-mode-resolution`, `list-label-mode-resolution` and `card-label-mode-resolution`. The `mkdocs build --strict` gate in this plan will confirm it.
- **LOW. Heading nesting.** `action_menus.md` already has `### Target-view default` and `### Rendering` under `## Label mode`. Three more `###` siblings there is fine, but the plan should say where in the section they go so the prose at `:79-89` is replaced rather than duplicated.

**Suggestions**
- Correct the baseline sentence to name the commit by subject, or switch to `02342703` to match STATE.md.
- Have the docs test select the example by content (`"card" in literal`) not by position.
- Add `action_menus.md:244` to the E211 wording update, since this plan already owns that file.

**Risk Assessment: LOW.** Documentation and gates only; the test it adds hardens the docs rather than the code.

## Cross-plan assessment

**Dependency ordering.** The waves are correct. 01-01 provides the accessor; 01-02 and 01-03 have disjoint `files_modified` sets; 01-04 depends on both. The only cross-wave coupling that bites is the docs anchor ordering noted under 01-03.

**Scope.** No scope creep. The plans stay inside LMOD-01 to LMOD-06, leave `no_label` and the filter toggle alone, do not touch templates, goldens or the example project, and defer the `"form"` location to Phase 6. The `Lock` in 01-01 is the only piece of unneeded machinery.

**Do the plans achieve the phase goal?** Yes. After 01-02 the acceptance grep is empty (only `base.py:312` and `:317` match today), all three consumers read `default_label_mode`, the card attribute is `None` with a public resolver, E108 validates the setting, and `override_settings` works because nothing snapshots the setting at import.

**Security and performance.** Nothing new reaches a template unvalidated; `tags/button/action.html:8` only compares the stamped mode against literals. The accessor is a `getattr` on settings per call, which is negligible. The warn-once mechanism prevents log flooding, provided the dedup key is fixed as suggested.

**Overall risk: LOW-MEDIUM.** Two items change executor behaviour and both are small: use a source-qualified dedup key with a `setting_changed` reset in 01-01, and keep the docs gate green across waves by moving or stubbing the two forward links in 01-03. Everything else is wording or test-hygiene detail.


---

## Consensus Summary

Three reviewers ran: opencode-gemini, opencode-grok (successful retry) and claude-fable. All three were prompt-fed and source-grounded with `file:line` citations; none carries a discount marker. All three covered every plan id (01-01 … 01-04). **No reviewer raised a HIGH concern.** Overall risk: LOW–MEDIUM (gemini LOW, claude LOW-MEDIUM, grok MEDIUM). Every reviewer found the mechanisms sound. The open items are test hygiene, gate ordering, and stale wording.

### Agreed Strengths
- The import cycle is real (`button_data.py:8` imports `label_mode`; `LOCATIONS` at `button_data.py:12`). Deferring the `LOCATIONS` import follows `button_classes.py:213` (all three).
- Raising before the lazy fallback callable keeps the strict error naming `cv_label_mode` (`test_button_data.py:120-125`) when the floor is also bad (all three).
- The `_UNSET` sentinel correctly distinguishes an explicit `None` from an absent setting. `button_classes.py:124` uses `or {}`, which would hide `None` (gemini, claude).
- The W292 hazard is real: `checks.py:23-28` collects E108, then iterates `checks_all()`. A strict `ValueError` at `buttons.py:405` would discard E108, and the narrow `try/except` is the right fix (all three).
- Refusing `mapping.get(key, default_label_mode("list"))` avoids eager floor evaluation (all three).
- The literal gate currently matches only `button_data.py:83`, `base.py:312` and `base.py:317`, all owned by 01-01/01-02 (all three).
- The card change is minimal and correct (`views/card.py:28,47-52,112`), and the `test_default_is_both` rewrite is required (all three).
- The wave structure is sound: 01-02 and 01-03 have disjoint `files_modified` (all three).
- The `ast.literal_eval` docs test is safe and binds the recipe to rendered output (all three).

### Agreed Concerns
1. **[MEDIUM] Process-global `_warned` with no reset under `pytest-xdist` + `pytest-random-order`** (`pyproject.toml:74,77`). Raised by gemini, grok and claude (all MEDIUM). Isolation relies on each test monkeypatching `_warned`, and 01-02-02's non-strict fallthrough tests do not mention it. Needed: an autouse fixture that clears `_warned`, or a test-only `setting_changed` reset, plus explicit isolation in the 01-02 non-strict tests.
2. **[MEDIUM/LOW] `LOCATIONS` is a `frozenset`** (`button_data.py:12`). "Temporarily extending the imported set" must be `monkeypatch.setattr(button_data, "LOCATIONS", LOCATIONS | {...})`. Raised by all three.
3. **[MEDIUM/LOW] The card-floor HTTP test meets `AuthorCardListView`'s `CardAction(key="delete", no_label=True)`** (`tests/test1/app/views.py:79-80`). Under `{"card": "label"}` that button stays icon-only, so "text-only card actions" fails unless the test asserts detail/update as text-only and delete as still icon-only. Raised by grok (MEDIUM) and gemini (LOW).
4. **[MEDIUM/LOW] Strict mkdocs build is red between wave 2 and wave 3.** `mkdocs.yml:24-25` sets `validation: anchors: warn`. 01-03 adds links to anchors that 01-04 creates, and 01-03's verification never runs mkdocs. Raised by claude (MEDIUM) and grok (LOW).
5. **[LOW] Baseline SHA provenance is misstated.** 01-04 calls `ebc7c23` "the pre-planning STATE.md state_head", but `STATE.md:10` records `02342703`. The diff is empty for either, so the gate still works. Raised by gemini and claude.
6. **[LOW] The docs-test card tracer must pass `cv_access=True` and `cv_icon_action`.** Otherwise `cv_resolve_action` returns `None`, or "no icon" passes vacuously (`visibility.py:14-18`, `crud_views.py:200-208`). Raised by gemini and grok.

### Divergent Views
- **Docs gate ordering.** gemini treats deferring `mkdocs --strict` to 01-04 as a strength. claude and grok treat the red interim state as a gap. Both are consistent with `mkdocs.yml:24-25`; the open question is whether a mid-phase stop should leave a failing gate on the branch.
- **Warn-once lock.** gemini warns of a possible re-entrant deadlock if `_warned_lock` is held across `fallback()`: `fallback` → `default_label_mode` → `_invalid_label_mode` when both the stamp and the floor are bad. claude calls the lock over-engineering under the GIL. Both point to the same fix: evaluate `fallback()` outside the lock, or drop the lock.
- **Dedup key.** claude prefers `(source, location, repr(value))` plus a `setting_changed` reset. 01-01 explicitly rejects the source dimension to honour D-11, so this is treated as an explicit rejection. gemini and grok accept process-wide dedup but want test isolation (Agreed Concern 1).
- **Single-reviewer items** (verified against source where noted):
  - grok [MEDIUM]: `tests/test1/test_import_safety.py` never imports `crud_views.lib.settings`, so it does not prove D-07 (verified: the file only imports templatetags modules).
  - grok [MEDIUM]: `docs/reference/settings.md:78` still says "keys not named are `icon`", and 01-04 does not say to rewrite it (verified).
  - gemini [LOW]: the class-attribute comments at `base.py:88-95` still hardcode `"icon"` (verified).
  - claude [LOW]: `action_menu.py:59` and `action_menus.md:244` call `cv_card_actions_label_mode` "string-valued" (verified for `action_menu.py:59`).
  - gemini [LOW]: the `buttons.md` System checks table lacks E106/E108.
  - gemini [LOW]: the `CHANGELOG.md:43-45` #213 bullet lists only the per-view and per-button recipes (verified).
  - claude [LOW]: the docs-example selector should match by content, not by position.

---

## Verification coverage

**Source-grounding pass** (`plan_review.source_grounding: true`). Effective authority from `gsd_run drift-guard authority --raw` is **`intel`**. Config names `source_grounding_authority: grep`, and the seam resolved `intel` because `intel.enabled: true`. `.planning/intel/API-SURFACE.md` reports *"api-map.json has no entries (intel extraction is regex/JS-only or not yet populated)"*, and every cited symbol is Python. Under the effective authority, every symbol is therefore **UNCHECKABLE → severity INFO, hardBlock false** (`drift-guard severity --status UNCHECKABLE --authority grep` → `{"severity":"INFO","hardBlock":false}`). UNCHECKABLE is not counted as verified. As supplementary evidence, every symbol below was also resolved by grep against tracked `src/`, and all were found as real declarations. No MISSING or AMBIGUOUS symbol was found.

Symbols excluded because they appear under each plan's "Artifacts this phase produces" section: `LABEL_MODE_DEFAULTS`, `default_label_mode`, `_UNSET`, `_raw_label_mode_defaults`, `_warned`, `_warned_lock`, `_invalid_label_mode`, `crud_views.E108`, `CardListView.cv_get_card_actions_label_mode`, `tests/test1/test_label_mode_docs.py`, all new test functions, and the four new doc anchors.

| Symbol (kind) | Cited by | Authority verdict | Supplementary grep evidence |
|---|---|---|---|
| `button_data.LOCATIONS` (const) | 01-01, 01-02 | UNCHECKABLE | `src/crud_views/lib/view/button_data.py:12` (frozenset) |
| `label_mode.is_label_mode` (fn) | 01-01 | UNCHECKABLE | `src/crud_views/lib/view/label_mode.py:17` |
| `label_mode.LABEL_MODES` (const) | 01-01 | UNCHECKABLE | `src/crud_views/lib/view/label_mode.py:14` |
| `exceptions.is_strict` (fn) | 01-01 | UNCHECKABLE | `src/crud_views/lib/exceptions.py:32` |
| `cv_button_data` (fn) | 01-01 | UNCHECKABLE | `src/crud_views/lib/view/button_data.py:52` |
| `CrudViewsSettings._action_settings_messages` (method) | 01-01 | UNCHECKABLE | `src/crud_views/lib/settings.py:98` |
| `crud_views.E106` / `E107` (check ids; E108 free) | 01-01 | UNCHECKABLE | `settings.py:125`, `settings.py:187` |
| `CrudView.cv_get_action_label_mode` (classmethod) | 01-02 | UNCHECKABLE | `src/crud_views/lib/view/base.py:291` |
| `cv_icon_mode_checks` (fn) / `W292` | 01-02 | UNCHECKABLE | `src/crud_views/lib/view/buttons.py:368`, `:409` |
| `checks.check_viewsets` (fn) | 01-02 | UNCHECKABLE | `src/crud_views/checks.py:20` |
| `cv_first_inline_keys` (classmethod) | 01-02 | UNCHECKABLE | `src/crud_views/lib/view/base.py:259` |
| `cv_context_actions_label_mode` / `cv_context_action_label_mode` / `cv_list_actions_label_mode` (attrs) | 01-02, 01-04 | UNCHECKABLE | `base.py:92`, `:96`, `:89` |
| `ContextButton` (class), `.label_mode` | 01-02 | UNCHECKABLE | `src/crud_views/lib/view/buttons.py:21` |
| `CardListView.cv_card_actions_label_mode` (attr) | 01-03 | UNCHECKABLE | `src/crud_views/lib/views/card.py:28` |
| `CardListView.cv_get_card_actions_inline` / `cv_get_card_action_data` | 01-03 | UNCHECKABLE | `views/card.py:103`, `:44` |
| `CardAction` (class), `.label_mode`, `.no_label` | 01-03 | UNCHECKABLE | `src/crud_views/lib/view/card.py:8,12`; `views/card.py:49` |
| `label_mode_check` / `E210` | 01-03 | UNCHECKABLE | `views/card.py:112`; `label_mode.py:29-32` |
| `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` / `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` (settings) | 01-04 | UNCHECKABLE | `settings.py:65-66` |
| ViewSet `context_actions_label_mode` / `list_actions_label_mode` (fields) | 01-04 | UNCHECKABLE | `src/crud_views/lib/viewset/__init__.py:85-86` |
| Test helpers `_client`, `_detail_url`, `_toolbar`, `_button`, `_has_icon_and_text`, `_author_card`, `_inline`, `_one` | 01-02, 01-03, 01-01 | UNCHECKABLE | `test_action_label_mode_render.py`, `test_context_action_label_mode.py`, `test_card_label_mode_render.py`, `test_button_leaves.py` |
| Cited test files (`test_label_mode.py`, `test_button_data.py`, `test_button_leaves.py`, `test_action_label_mode_config.py`, `test_settings_checks.py`, `test_import_safety.py`, golden/render suites) | all | UNCHECKABLE (file paths) | all present under `tests/test1/` |
| Cited docs (`settings.md`, `action_menus.md`, `context_buttons.md`, `buttons.md`, `card-list-view.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`) | 01-03, 01-04 | UNCHECKABLE (file paths) | all present |
| Tooling (`.venv/bin/pytest`, `mkdocs`, `ruff`, `pytest-xdist`, `package.json`, `superpowers/plans/2026-10-24-concept-review-followups.md`) | all | UNCHECKABLE | all present; xdist importable |
| Baseline commit `ebc7c23259ae…` | 01-04 | UNCHECKABLE (git object) | `git cat-file -t` → commit |
| Function signatures | all | UNCHECKABLE | signatures cannot be asserted under grep/intel |

**Cross-artifact fact-drift pass** (advisory, never counted):
- Phase status: `gsd_run drift-guard phase-status --phase 01` returns `verdict: lag` (STATE.md "Ready to execute" vs ROADMAP.md "Not started"). Lag is not a finding.
- ROADMAP Success Criteria ↔ PLAN `must_haves.truths`: no contradiction flagged. Roadmap SC1 says "every unmapped toolbar button … on every page". 01-02 excludes the filter toggle, whose label mode the roadmap assigns to Phase 3. That narrowing is a scope question for `gsd-plan-checker` (Dimension 7b), not drift.
- ROADMAP `**Requirements:**` (LMOD-01…06) ↔ plan `requirements:`: the union of the four plans covers LMOD-01…06 with no contradiction.
- CONTEXT.md Decisions ↔ PLAN term usage: no contradiction flagged. 01-01's dedup key deliberately diverges from RESEARCH (not CONTEXT) and cites D-11.
- Advisory provenance note, not a judgment pair: 01-04 calls `ebc7c23` "the pre-planning STATE.md state_head", while `STATE.md:10` records `02342703`. Also listed as Agreed Concern 5.
- Nothing was skipped: STATE.md, ROADMAP.md and CONTEXT.md were all present.

**Lane diagnostics:** the opencode-grok attempt 1 failed with `spawn error: ETIMEDOUT` (preserved in `.review-diagnostics/`), and the retry succeeded. The plan coverage check is complete for all three graded lanes (4/4 ids each).
