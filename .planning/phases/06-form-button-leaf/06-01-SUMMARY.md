---
phase: 06-form-button-leaf
plan: "01"
subsystem: testing
tags: [crispy-forms, golden, design-spec, nvm, npm-ci, jsdom, d-18]

requires:
  - phase: 01-label-mode-defaults
    provides: lazy default_label_mode floor and immutable LABEL_MODE_DEFAULTS (verified at HEAD 49f44cd)
  - phase: 02-form-key-grammar
    provides: finite FORM_KINDS independent of VARIANT_LOCATIONS and form:<kind>:<mode> grammar (verified at HEAD 49f44cd)
provides:
  - 06-SPEC.md settled design (form contract, literal/attribute rules, template precedence, ownership, helper lifecycle, icons/diagnostics, dependency validation, golden protocol)
  - five committed before-change form-button goldens (create, update, delete, workflow, filter)
  - input/button-capable control extractor and unchanged-scope _extract_filter_form_region
  - clicked-submitter delete POST regression
  - 06-JS-RUNTIME.json + 06-js-verify.sh single JS gate entry point
affects: [06-02, 06-03, 06-04, 06-05, 06-06, 06-07, 06-08, 06-09]

actuals:
  tokens: 14451
  tasks: 3
  commits: 3
plan_head_before: 49f44cd872aec399e7dc240ea8f9d55b1f04ce4d
plan_head_after: 98b71edd393caa21d36e5449aa7934c2bce4dd92

tech-stack:
  added: []
  patterns:
    - "Raw-bytes control golden: exact response substrings per control, each + newline, compared with read_bytes(); no update mode"
    - "Filter golden scope: exact source-offset slice of form#filter-form through its matching </form>"
    - "JS gates run only through 06-js-verify.sh, which re-asserts the recorded Node/npm/lock/package/engine identity"

key-files:
  created:
    - .planning/phases/06-form-button-leaf/06-SPEC.md
    - .planning/phases/06-form-button-leaf/06-js-verify.sh
    - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json
    - .planning/phases/06-form-button-leaf/deferred-items.md
    - tests/test1/test_form_buttons_golden.py
    - tests/test1/golden/form_buttons/create.html
    - tests/test1/golden/form_buttons/update.html
    - tests/test1/golden/form_buttons/delete.html
    - tests/test1/golden/form_buttons/workflow.html
    - tests/test1/golden/form_buttons/filter.html
  modified:
    - .planning/WINDOWS.md

key-decisions:
  - "D-18 gate passed on introduce-gsd @ 49f44cd: Phase 1/2 contracts present; prerequisite shard 201 passed, exit 0"
  - "Separate FORM_LEAF_KEYS (cv_location, cv_key, cv_type, cv_name, cv_value, cv_label, cv_id, cv_label_mode, cv_icon, cv_icon_class, cv_icon_inline, cv_css_class, cv_flat_attrs, icon-only cv_title, cancel-only cv_cancel_url); LEAF_KEYS unchanged"
  - "Form templates render with only the normalized FORM_LEAF_KEYS dict (no outer context, no input alias)"
  - "Non-cancel kinds keep data-cv-cancel-url as an ordinary escaped extra attribute; cv_cancel_url exists only for kind cancel"
  - "form:icon-host default is {name_class}, like the other *:icon-host keys"
  - "JS runtime: existing nvm Node v24.21.0 / bundled npm 11.19.0, lock-verified npm ci (no manifest/lock change)"

patterns-established:
  - "Golden capture: write fixtures once from unchanged source via a throwaway capture, never an update switch in the test"
  - "Golden tests use their own fixed-PK objects so object URLs cannot vary between runs"

requirements-completed: [FORM-01, FORM-02, FORM-05, FORM-06, FORM-08, FORM-11]

coverage:
  - id: D1
    description: "D-18 prerequisite verification recorded with HEAD SHA, completion and test evidence before the spec"
    requirement: "FORM-01"
    verification:
      - kind: unit
        ref: ".venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "06-SPEC.md contains all nine required nonempty design sections and the executing-branch HEAD SHA; existing real crispy render shard passes"
    requirement: "FORM-02"
    verification:
      - kind: other
        ref: "Task 1 <automated> spec-section/SHA gate + .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q"
        status: pass
    human_judgment: false
  - id: D3
    description: "Design adequacy of the settled contracts (the spec is prose that later plans implement)"
    requirement: "FORM-11"
    verification: []
    human_judgment: true
    rationale: "Whether the written contracts are complete and correct is a design judgment; tests in 06-02..06-06 will exercise them"
  - id: D4
    description: "Create/update/delete raw control baselines committed alone (2956f3e) against unchanged src, with DOM defaults and clicked-submitter delete POST"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: ".venv/bin/pytest tests/test1/test_form_buttons_golden.py tests/test1/test_crud.py -q"
        status: pass
    human_judgment: false
  - id: D5
    description: "Workflow controls and whole filter-form region baselines committed alone (98b71ed); filter region CSRF-free, deterministic, DOM-pinned"
    requirement: "FORM-08"
    verification:
      - kind: integration
        ref: ".venv/bin/pytest tests/test1/test_form_buttons_golden.py tests/test1/test_filter.py tests/test1/test_workflow.py -q"
        status: pass
    human_judgment: false
  - id: D6
    description: "Selected-runtime JS wrapper re-asserts Node/npm/lock/packages/engines and runs the suite"
    requirement: "FORM-05"
    verification:
      - kind: other
        ref: "bash .planning/phases/06-form-button-leaf/06-js-verify.sh"
        status: fail
    human_judgment: true
    rationale: "Runtime/lock assertions pass, but 1/183 pre-existing JS test fails on locked jsdom 30.1.2 (deferred); gate is red until fixed"

duration: 16min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 01: Prerequisites, design spec and form-button baselines Summary

**D-18 dependency evidence (introduce-gsd @ 49f44cd, 201 passed), a nine-section form-button design spec, an nvm Node 24 / lock-verified JS gate wrapper, and five raw-byte before-change goldens committed in two src-free commits (2956f3e, 98b71ed).**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-28T05:59:24Z
- **Completed:** 2026-10-28T06:15:26Z
- **Tasks:** 3
- **Files modified:** 11 (10 created, 1 ledger modified)

## Accomplishments

- Verified the Phase 1 lazy floor and Phase 2 finite form grammar on the executing branch (D-18) and recorded the evidence in `06-SPEC.md`.
- Wrote the required spec: separate `FORM_LEAF_KEYS`; form third-kind accept/reject rules independent of `cv_key`; one escaping boundary; reserved-attribute collisions; template precedence; tiered owner recovery from crispy response overlays plus the formset page-owner transport; helper truthiness/replacement lifecycle; icon availability and W292 reach; import-safety boundary; golden protocol.
- Prepared the JS runtime without touching manifests: nvm Node v24.21.0 with bundled npm 11.19.0, `npm ci` against the unchanged lock (all 96 entries come from registry.npmjs.org with integrity hashes). `06-js-verify.sh` re-checks the environment on every call.
- Committed the create/update/delete control baselines (`2956f3e`), then the workflow control and full filter-form baselines (`98b71ed`). Neither commit touches `src`.

## Task Commits

1. **Task 1: Trace the existing form render and record the required design** - `198ad43` (docs)
2. **Task 2: Commit raw create, update and delete control baselines** - `2956f3e` (test) — BASELINE 1
3. **Task 3: Commit workflow and filter baselines and close history evidence** - `98b71ed` (test) — BASELINE 2

**Plan metadata:** recorded in the final docs commit for this plan.

## Baseline history evidence

| Baseline | Commit | Files | `git diff B^ B -- src` | `src` tree (parent = commit) | Ancestor of HEAD |
|---|---|---|---|---|---|
| CRUD controls | `2956f3e2ceda9331799279da88df55b466947f79` | create/update/delete.html, test module | empty | `dcc38f4` = `dcc38f4` | yes |
| Workflow + filter | `98b71edd393caa21d36e5449aa7934c2bce4dd92` | workflow/filter.html, test module | empty | `dcc38f4` = `dcc38f4` | yes |

The plan-start `src` tree (`49f44cd:src`) is also `dcc38f4bf63e5fe2e481c1e297adaf08990c8f3e`. No Phase 06 product edit exists yet, so both baselines precede the first one. Committed golden blobs are byte-identical to the captures (only ruff pre-commit hooks run, which leave `.html` alone).

**Extractor contracts for later plans.** CRUD and workflow use `_extract_controls(markup, names)`. It takes exact raw `<input>` start tags, or `<button>…</button>` spans, for the named controls in document order, each name exactly once. Filter uses `_extract_filter_form_region(markup)`, which returns the exact source-offset slice from the unique `<form id="filter-form" ...>` through its matching `</form>`, captured on `GET /publisher/?sort=name&order=name&dir=desc`. 06-05 must reuse that extractor unchanged; compare against `git show 98b71ed:tests/test1/test_form_buttons_golden.py`.

## Files Created/Modified

- `.planning/phases/06-form-button-leaf/06-SPEC.md` - prerequisite evidence and the settled design for 06-02..06-09
- `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json` - selected Node/npm paths and versions, lock SHA256, package versions
- `.planning/phases/06-form-button-leaf/06-js-verify.sh` - the single JS verification entry point
- `.planning/phases/06-form-button-leaf/deferred-items.md` - out-of-scope findings (jsdom selector failure, undici audit)
- `tests/test1/test_form_buttons_golden.py` - golden byte, determinism, DOM-default, extractor and delete-submitter tests (19)
- `tests/test1/golden/form_buttons/{create,update,delete,workflow,filter}.html` - before-change baselines
- `.planning/WINDOWS.md` - ledger entries 5 and 6 for the deferred items

## Decisions Made

- Form templates (bundled and custom) render with only the normalized `FORM_LEAF_KEYS` dict. That is the scoped context, and it keeps `input` and outer `cv_*` keys out.
- For non-cancel kinds, `data-cv-cancel-url` stays an ordinary escaped extra attribute. `cv_cancel_url` exists only for kind `cancel`, so existing markup behavior is kept.
- `form:icon-host` defaults to `{name_class}`, matching the other `*:icon-host` keys.
- The golden test creates its own Author with a fixed UUID, so a pk-bearing control URL cannot vary between runs.
- The test app's `AuthorForm.submit_label = "Create"` is the real default text for the create and update submit buttons, so the baselines pin `Create`, not the package `Save`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Recreated the missing project virtualenv**
- **Found during:** Task 1 (prerequisite test command)
- **Issue:** `.venv` did not exist, so every `.venv/bin/pytest` gate failed with exit 127.
- **Fix:** `uv venv --python=3.12` plus `uv pip install -e ".[all,dev,test,examples]" -r requirements/demo.txt`. This installs only declared dependencies (covered by the research Package Legitimacy Audit), editable so tests exercise `src/` (`task dev` installs non-editable). Django resolved to 6.1.2 because the manifest has no upper bound; this is recorded in the spec.
- **Files modified:** none tracked (`.venv` is gitignored)
- **Verification:** prerequisite shard 201 passed; full suite 3609 passed
- **Committed in:** n/a (environment only)

**2. [Rule 1 - Bug] JS wrapper misclassified libc-specific optional packages**
- **Found during:** Task 1 (first `06-js-verify.sh` run)
- **Issue:** The `@rolldown/binding-linux-x64-musl` and `lightningcss-linux-x64-musl` lock entries are skipped by npm on glibc hosts, but the first draft of the wrapper reported them as missing.
- **Fix:** The wrapper now evaluates the lock entries' `libc` constraint alongside `os`/`cpu`, using the Node process report.
- **Files modified:** `.planning/phases/06-form-button-leaf/06-js-verify.sh`
- **Verification:** wrapper reports 71 installed packages matching the lock, 72 engine ranges satisfied, 25 other-platform optionals skipped
- **Committed in:** `198ad43`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both were needed to run the plan's own gates. No product scope change.

## Issues Encountered

- **Pre-existing JS failure on the lock-backed jsdom 30.1.2 (deferred).** The plan requires running `06-js-verify.sh` in wave 1. Its runtime/lock assertions pass, but the suite result is 182/183. The failing test is `tests/js/list.filter.test.js:159`: `toggle.querySelector("#cv-filter-toggle > span:...")` returns null in jsdom 30.1.2, while the `:scope >` form works. A direct jsdom probe reproduced this. No product source changed, and the test passed on the previously installed jsdom 29.1.1. It is outside this plan's scope, so it is logged in `deferred-items.md` and WINDOWS #5. **Every later Phase 06 JS gate exits nonzero until it is fixed.** A test-only `:scope >` rewrite is the likely fix; it needs an owner (06-07 or a quick task).
- **`npm audit`:** high-severity advisories in the transitive dev-only `undici`. Not fixed, because the plan forbids lockfile changes (deferred, WINDOWS #6).

## Known Stubs

None. The plan adds no product code.

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 06-02 can start: the spec and both baseline commits exist, and `src` is unchanged.
- Open concern: the JS gate is red until the jsdom 30 selector test is fixed (see Issues).

## Self-Check: PASSED

- All 10 created files exist on disk; commits `198ad43`, `2956f3e`, `98b71ed` are ancestors of HEAD.
- Task verifies re-run: Task 1 spec gate + 354 passed; Task 2 16 passed; Task 3 85 passed; full suite `pytest tests -n auto` 3609 passed.
- Plan-level verification: spec present, five baselines present, both baseline commits src-free and ancestral, product source unchanged since plan start.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
