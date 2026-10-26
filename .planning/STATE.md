---
gsd_state_version: "1.0"
current_phase: 02
current_phase_name: Form key grammar
status: verifying
stopped_at: Completed 02-01-PLAN.md; Phase 02 awaiting external review and verification
last_updated: "2026-10-26T12:42:14.649Z"
last_activity: 2026-10-26
last_activity_desc: Phase 02 plan implemented; awaiting external review and verification
state_head: 398006457ff00eb9169bf0b30894b4ec304e9293
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 6
  completed_plans: 6
  percent: 14
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-26)

**Core value:** Every public theme name settles once, consistently, before 1.0.0 freezes it — no public name changes twice.
**Current focus:** Phase 02 — Form key grammar

## Current Position

Phase: 02 (Form key grammar) — AWAITING REVIEW
Plan: 1 of 1
Status: Plan implemented — awaiting external review and phase verification
Last activity: 2026-10-26 — Phase 02 plan implemented; awaiting external review and verification

Progress: [█░░░░░░░░░] 14%

## Performance Metrics

**Velocity:**

- Total plans completed: 5
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 7 min | 2 tasks | 9 files |
| Phase 01 P02 | 6 min | 2 tasks | 7 files |
| Phase 01 P03 | 4 min | 2 tasks | 7 files |
| Phase 01 P04 | 10 min | 2 tasks | 9 files |
| Phase 01 P05 | 8 min | 3 tasks | 10 files |
| Phase 02 P01 | 20 min | 3 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in the PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: one roadmap phase per source-plan phase. Numbering: 1=1A, 2=1C, 3=1B, 4=3A, 5=3B, 6=2, 7=4.
- Roadmap: Phases 4 and 5 (plan 3A/3B) can be dropped if 1.0.0 ships early.
- Research: the 1A setting is read lazily from `django.conf.settings`, not as a Pydantic snapshot, so
  `override_settings` works.
- Phase 1 completed on `feat/label-mode-defaults`; user explicitly requested staying on the current branch.
- [Phase 01]: 01-01: Label-mode warn-once dedup is process-lifetime, keyed (location, repr(value)), no source dimension, no setting_changed reset; tests isolate via autouse conftest fixture
- [Phase 01]: 01-01: default_label_mode reads the raw setting every call (no merged-map cache); setting fallbacks return LABEL_MODE_DEFAULTS[location] directly so nested recovery terminates
- [Phase 01]: 01-01: E108 (Error, no hint) gives one message per bad entry in insertion order, unknown location before invalid mode; keys from button_data.LOCATIONS imported at check time
- [Phase 01]: 01-02: context floor resolves as target_default or default_label_mode('context'); list floor via explicit membership branch, never an eager dict.get default; W292 catches ValueError only around mode resolution so E108 survives strict check_viewsets
- [Phase 01]: Card chain is CardAction.label_mode, then no_label -> icon, then cv_get_card_actions_label_mode() (attribute, else default_label_mode('card')); no_label untouched (D-18)
- [Phase 01]: A valid explicit cv_card_actions_label_mode short-circuits the floor read, so an invalid strict card floor never raises for that view
- [Phase 01]: Label-mode precedence is stated once per location in action_menus.md (context/list/card resolution sections); other pages link instead of restating
- [Phase 01]: settings.md#label-mode-configuration is the single merge-or-replace table: CRUD_VIEWS_LABEL_MODE_DEFAULTS merges per location, per-action maps replace whole
- [Phase 01]: Card action rendering honors own instance values before the class resolver; own None reads the live card floor, while absent own values retain subclass fallback hooks.
- [Phase 02]: Form kinds accept all three class-key modes; context/list/card retain variants under independent immutable location allow-lists.
- [Phase 02]: Form class keys do not enable form label floors or change crispy rendering; those remain Phase 6 work.

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2: Option A is implemented; external-AI review, phase verification and human prose review remain pending.
- Phase 2: Ruff 0.16.10 is below the manifest range and global formatting flags seven pre-existing planning
  Markdown files; product formatting passes. See phase deferred-items.md and WINDOWS entry 4.
- Phase 3, 6, 7: each needs a spec or maintainer decision before planning.
- Phase 7: retain the decided stable label-mode names; track the separately planned `no_label` removal before 1.0.
- Phase 5: confirm the hidden-label key name (`pagination:hidden-label` vs `table:hidden-label`) before Phase 7.
- Phases 4, 5 and 6 must commit before-change goldens. Today's goldens contain no form buttons, dismissible alerts or
  table pagination.

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-26T12:42:14.551Z
Stopped at: Completed 02-01-PLAN.md; Phase 02 awaiting external review and verification
Resume file: None
