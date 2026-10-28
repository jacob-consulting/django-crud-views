---
gsd_state_version: "1.0"
current_phase: 06
current_phase_name: Form-button leaf
status: executing
stopped_at: Completed 06-04-PLAN.md
last_updated: "2026-10-28T07:06:20.683Z"
last_activity: 2026-10-28
last_activity_desc: Phase 06 execution started
state_head: e26d78648bb7591ed27326b407a871e2b9a0eab5
progress:
  total_phases: 7
  completed_phases: 5
  total_plans: 23
  completed_plans: 18
  percent: 71
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-27)

**Core value:** Every public theme name settles once, consistently, before 1.0.0 freezes it — no public name changes twice.
**Current focus:** Phase 06 — Form-button leaf

## Current Position

Phase: 06 (Form-button leaf) — EXECUTING
Plan: 5 of 9
Status: Ready to execute
Last activity: 2026-10-28 — Phase 06 execution started

Progress: [███████░░░] 71%

## Performance Metrics

**Velocity:**

- Total plans completed: 14
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | - | - |
| 02 | 1 | - | - |
| 03 | 2 | - | - |
| 04 | 3 | - | - |
| 05 | 3 | - | - |

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
| Phase 03 P01 | 15 min | 3 tasks | 9 files |
| Phase 03 P02 | 7 min | 3 tasks | 8 files |
| Phase 04 P01 | 5 min | 3 tasks | 7 files |
| Phase 04 P02 | 5 min | 2 tasks | 2 files |
| Phase 04 P03 | 10 min | 3 tasks | 9 files |
| Phase 05 P01 | 5 min | 3 tasks | 10 files |
| Phase 05 P02 | 8 min | 2 tasks | 2 files |
| Phase 05 P03 | 9 min | 3 tasks | 9 files |
| Phase 06 P01 | 16 min | 3 tasks | 11 files |
| Phase 06 P02 | 17min | 3 tasks | 20 files |
| Phase 06 P03 | 11 min | 2 tasks | 9 files |
| Phase 06 P04 | 12 min | 2 tasks | 7 files |

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
- [Phase 03]: Filter toggle resolves cv_get_action_label_mode('context', self.key, self) with no target default; leaf falls back to the legacy icon body for absent/unknown modes
- [Phase 03]: list.filter.js unchanged: label-only markup is covered by its empty icon loop, collapse-first ordering and non-rollback persistence
- [Phase 03]: Review fixes supersede A1: malformed resolved filter modes use the shared strict exception or warn-once/context-floor policy before label rendering; startup diagnostics remain.
- [Phase 03]: Preserve a button's resolved mode only in context rendering; list rows always resolve their own mode. Review regression fixed in b78b3d1; 4/4 UAT and 22/22 verification checks passed.
- [Phase 03]: 03-02: filter toggle change is released as Fixed (#262), not Breaking; default output unchanged, migration guide still updated for copied templates
- [Phase 03]: 03-02: documented per-page filter override is view-level cv_context_buttons with FilterContextButton imported from crud_views.lib.view.buttons (no re-export)
- [Phase 04]: 04-01: delegated alert listener ignores a marker outside a role=alert frame (no preventDefault) and calls globalThis.cv.adapters.alert.close at click time with no catch/log/fallback
- [Phase 04]: 04-01: dismissible alert golden is raw bytes (encode utf-8 vs read_bytes, no normalization); baseline commit f6982bfef24f4322cfd01f9f21c3bbed517462fe
- [Phase 04]: 04-02: no product change needed; 32 alert ownership regressions pass against 04-01 adapter/listener and catch every production mutant tried
- [Phase 04]: 04-03: whole-map cv.adapters replacement after core load must provide alert.close(el) (else TypeError); pre-load partial maps get defaults; fix via per-entry assignment, Object.assign or cv.bootstrapAdapters(ns).alert
- [Phase 04]: 04-03: theme.md '### Custom alert frame' recipe is executable (test_documented_alert_frame_override); core data-bs-* confined to the dropdown allowlist by a tmp_path-tested guard
- [Phase 04]: 04-03: browser A/B/C acceptance observed in headless Chrome 156 against the example; ruff format --check stays red on 8 pre-existing .planning files
- [Phase 04]: UAT 2/2 passed; review WR-01/IN-03 fixed in b7b49ae (theme.md data-bs-* claim scoped to core, object-detail layouts named; messages.md TypeError wording); re-verification 21/21 passed
- [Phase 05]: 05-01: table pagination direction blocks enclose their own has_previous/has_next guards; disabled ends render aria-disabled anchors without href/tabindex; pagination:hidden-label (visually-hidden) shared by table and card; table baseline be7daa5, card raw baseline 0275218
- [Phase 05]: 05-01: table template-origin check resolves the package path from crud_views.__file__ so it holds for editable checkouts and nox installs
- [Phase 05]: 05-02: no production change needed; tests prove inherited pagination.previous/next overrides run on disabled ends without page-number calls, pin the 11-block contract, and hold card and table to one accessibility contract on a real three-page card endpoint
- [Phase 05]: 05-02: invalid page inputs keep framework semantics (django-tables2 RequestConfig: non-integer -> 1, empty -> last; Django ListView: missing -> 1, last -> last, out of range/non-integer -> 404); _render_table_pagination is the reusable isolated-Engine override recipe for 05-03
- [Phase 05]: 05-03: table pagination Breaking entry and migrating-1.0.md 'Table pagination overrides' share commit 09549b2; the guarded myproject/table.html recipe (DJANGO_TABLES2_TEMPLATE at startup) is extracted and rendered by tests/test1/test_pagination_docs.py on pages 1/2/3 with class/icon overrides
- [Phase 05]: 05-03: German catalog keeps only the pagination/previous/next reference updates for both templates; django.mo byte-identical to a fresh msgfmt build; unrelated makemessages churn deferred (deferred-items.md)
- [Phase 05]: UAT 2/2 passed; all 7 review findings fixed after review (WR-01/WR-02, IN-01..IN-05, incl. disabled `...` range items and whitespace-free range anchors); re-verification 19/19 passed
- [Phase 06]: 06-01: D-18 gate passed on introduce-gsd @ 49f44cd (Phase 1 lazy floor + Phase 2 finite FORM_KINDS verified; 201 passed); 06-SPEC.md settles FORM_LEAF_KEYS, literal/attribute, template, ownership, helper-lifecycle, icon and golden contracts
- [Phase 06]: 06-01: before-change form-button goldens committed src-free: CRUD 2956f3e, workflow+filter 98b71ed; filter scope is _extract_filter_form_region (raw form#filter-form slice) and 06-05 must reuse it unchanged
- [Phase 06]: 06-01: JS gates run only via 06-js-verify.sh (nvm Node v24.21.0, npm 11.19.0, lock sha 567bff55...); lockfile/manifests unchanged
- [Phase 06]: 06-02: form normalizer input contract cv_key/cv_type/cv_name/cv_value/cv_label/cv_id/cv_css_id/cv_css_class/cv_attrs/cv_label_mode/cv_icon; reserved attributes resolve in the normalizer
- [Phase 06]: 06-02: cv_cancel_url exists for kind cancel only and is None without a URL; leaf emits data-cv-cancel-url only when not None
- [Phase 06]: 06-02: icon-mode form button with empty label renders no title/tooltip (matches action leaf)
- [Phase 06]: 06-02: layout render rejects slots other than form:<FORM_KINDS>; construction and legacy helper.inputs accept any slot
- [Phase 06]: 06-03: form maps (setting/ViewSet/view) are selected whole on the owner; invalid selected maps or values use the shared strict/log fallback to the form floor
- [Phase 06]: 06-03: form-button owner = render form cv_view, else current crispy helper overlay (or private _cv_helper_owner entry), else page (transported _cv_page_owner, else nearest non-None view outside response overlays); identity, quiet
- [Phase 06]: 06-04: layout form buttons pick a semantic icon from the slot kind (submit save, delete delete, cancel cancel, filter-submit filter, filter-reset filter-reset). icon= has a sentinel default, so explicit None/empty means no icon
- [Phase 06]: 06-04: icon precedence is hook kwargs, then the form attribute (CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'), then the adapter kind default. A delete payload moved to slot form:cancel keeps delete_icon
- [Phase 06]: 06-04: registry glyphs save far:floppy-disk/bi:floppy, cancel fas:xmark/bi:x-lg, filter-reset fas:rotate-left/bi:arrow-counterclockwise (distinct from filter-close)

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2: Ruff 0.16.10 is below the manifest range and global formatting flags eight pre-existing planning
  Markdown files; product formatting passes. See phase deferred-items.md and WINDOWS entry 4.
- Phases 6 and 7: each needs a spec or maintainer decision before planning.
- Phase 7: retain the decided stable label-mode names; track the separately planned `no_label` removal before 1.0.
- Phase 7: carry the Phase 5 class key `pagination:hidden-label` into the stability surface.
- Phase 6 must commit before-change goldens; today's goldens contain no form buttons (Phase 4 committed the
  dismissible alert golden first, f6982bf; Phase 5 the table pagination goldens, be7daa5).
- [Phase 4] Four open Info review findings (IN-01 `[role~="alert"]`, IN-02 hand-copied allowlist, IN-04 no guard for
  the non-core data-bs-* sentence, IN-05 missing-script enumeration) — see 04-REVIEW-DISPOSITION.md; candidates for Phase 7.
- Phase 2: Both source-probe classifier limitations remain documented; explicit tests and completed human prose UAT independently establish acceptance. See 02-VERIFICATION.md.
- Phase 06: pre-existing tests/js/list.filter.test.js:159 fails on locked jsdom 30.1.2 (element-scoped '#id > span' selector returns null); every 06-js-verify.sh gate is red until a test-only fix lands (06-01 deferred-items, WINDOWS #5)

### Roadmap Evolution

- Phase 06 edited: User decision D-18: verify completed Phase 1/2 contracts on executing working branch before spec; main merge no longer prerequisite

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-28T07:06:20.271Z
Stopped at: Completed 06-04-PLAN.md
Resume file: None
