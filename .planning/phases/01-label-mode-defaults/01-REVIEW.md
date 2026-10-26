---
phase: 01-label-mode-defaults
reviewed: 2026-10-26T11:13:16Z
depth: deep
files_reviewed: 8
files_reviewed_list:
  - CHANGELOG.md
  - docs/migrating-1.0.md
  - docs/reference/action_menus.md
  - docs/reference/card-list-view.md
  - src/crud_views/lib/views/card.py
  - tests/test1/test_card_label_mode_render.py
  - tests/test1/test_card_label_modes.py
  - tests/test1/test_label_mode_docs.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 01: Code Review Report

**Reviewed:** 2026-10-26T11:13:16Z
**Depth:** deep
**Files Reviewed:** 8
**Status:** clean for the Plan 01-05 gap-closure scope

## Summary

No new actionable defect was found in the instance-aware card label-mode repair. Prior BLOCKER CR-01 is closed:
explicit instance choices now reach the card render path, including Django `as_view()` kwargs and request-time
assignment. This is a scoped review, not a clean bill of health for every historical Phase 01 finding.

Scope came from `/tmp/phase01-review-scope.json`: **degraded**, source `phase-range`, reason
`no-task-commit-rows`, range base `f6b33dedc76ea40c3e91b7487344a917892611e9`. Its eight files match the gap plan.
The production delta and its tests were reviewed in full context; documentation changes were checked against the
actual resolution and rendering behavior. Historical release notes unrelated to this change were not re-audited.
No Fallow structural pre-pass or external reviewer evidence was supplied. None of the eight scoped files is ignored.

## Narrative Findings (AI reviewer)

No new BLOCKER or WARNING findings in this scope.

### Closure of prior CR-01 — BLOCKER, fixed

**File:** `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/views/card.py:46-58`

The former regression was a loss of instance configuration when the render path delegated directly to a
classmethod. The current implementation distinguishes an own instance value with membership in `vars(self)`.
Action `label_mode` and `no_label` still take precedence. An own non-None value is stamped directly; own
`None` consults the live card floor, bypassing an inherited class value. With no own value, the existing
zero-argument resolver is still called through the instance, preserving classmethod overrides using `super()`
and request-dependent instance-method overrides.

Both ordinary and child actions receive the same resolved value
(`/home/alex/projects/alex/django-crud-views/src/crud_views/lib/views/card.py:74` and `:92`).
There is no write to shared class state. A valid explicit choice never evaluates an invalid strict floor.
The public classmethod at `:113-121` retains its signature and class-only meaning.

Concrete regression evidence is in
`/home/alex/projects/alex/django-crud-views/tests/test1/test_card_label_mode_render.py:265-452`:
absent-setting `as_view(label)`, conflicting/invalid floors, runtime assignment in three request hooks, sequential
request isolation, own-None resets and nested settings, subclass fallback hooks, and child permission decisions.
The class-call/super regression is in
`/home/alex/projects/alex/django-crud-views/tests/test1/test_card_label_modes.py:35-47`.

The changelog, migration guide and card references distinguish class-level resolution from the per-action stamp
and retain the raw-attribute `None` breaking-change disclosure.

## Cross-module analysis

Traced the following paths against the current source:

- Django `View.as_view()` → instance constructor/setattr → request hooks → card context construction.
- Card template/`cv_card_action_group` and the direct `cv_card_action` tag →
  `cv_get_card_action_data` → `cv_resolve_action` → `cv_button_data` → action/menu leaves.
- Own instance `None` or the default class resolver → `default_label_mode("card")` →
  live Django settings and existing strict/non-strict malformed-value handling.
- Ordinary/child action construction → target permission and enabled-state checks → hide/disable resolution.

The new branch changes only the source of the stamped mode. Leaf validation and recovery remain downstream;
permission, disabled-state, POST-form and menu rendering behavior are not bypassed. The action-data method still
returns unresolved data: leaf normalization can adjust a malformed mode or an icon-only button with no icon.
No new import edge, public signature, dependency cycle, or shared-state mutation was introduced.

The test-local subclasses do not redeclare `cv_viewset`; `CrudViewMetaClass` therefore does not register them
over the real application views. RequestFactory tests use the real URL resolver context and render the
TemplateResponse before asserting the resulting buttons.

## Historical advisory findings outside this gap scope

These are retained from the review dated 2026-10-26T08:58:11Z and its existing disposition record. They are
**not marked fixed**, not independently reclassified here, and are excluded from this report's new-finding counts.
The earlier source report is preserved in Git at
`f6b33dedc76ea40c3e91b7487344a917892611e9:.planning/phases/01-label-mode-defaults/01-REVIEW.md`.
`01-REVIEW-DISPOSITION.md` remains the historical disposition ledger; this reviewer did not edit it.

| Historical ID | Original tier | Earlier concern | Status in this review |
|---|---|---|---|
| WR-01 | warning | Strict icon-without-icon diagnostic names the wrong configuration knobs for cards and floors | Outside gap scope; not fixed |
| WR-02 | warning | No startup check for icon-less targets made icon-only by the card/list floor | Outside gap scope; not fixed |
| WR-03 | warning | Ten-second subprocess deadlines may flake under CI load | Outside gap scope; not fixed |
| IN-01 | info | Warn-once key can suppress the stamp diagnostic when stamp and floor share a malformed value | Historical advisory; not fixed |
| IN-02 | info | E108 unknown-key diagnostic reports the value as what was received | Historical advisory; not fixed |
| IN-03 | info | Mapping types other than dict are rejected | Historical advisory; not fixed |
| IN-04 | info | W292 catches every ValueError raised by the resolver | Historical advisory; not fixed |
| IN-05 | info | LOCATIONS and LABEL_MODE_DEFAULTS are separate sources of truth | Historical advisory; not fixed |
| IN-06 | info | Live floor settings and import-time label maps have different lifecycles | Historical advisory; not fixed |
| IN-07 | info | Some existing floor tests depend on unmapped test-app defaults | Historical advisory; not fixed |

Prior CR-01 is the only historical finding whose closure this review establishes. The Phase 3 filter toggle and
the plan's broader flagged lifecycle/consumer-completeness assumptions are not resolved by this scoped review.

## Review validation

Independent focused run:

```text
.venv/bin/pytest tests/test1/test_card_label_mode_render.py tests/test1/test_card_label_modes.py tests/test1/test_label_mode_docs.py -q
51 passed in 4.91s
```

The executor separately reported 3,076 Python tests passed with one existing skip, 126 JavaScript tests passed,
strict docs build and lint/format checks passed, and unchanged protected templates/goldens/examples.
Those broader results were read as execution evidence and were not rerun or treated as proof of correctness.

Source files were not modified and no commit was made. The branch remains `feat/label-mode-defaults`.

---

_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
