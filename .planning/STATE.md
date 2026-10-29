---
gsd_state_version: "1.0"
milestone: v1.0
current_phase: "06.2"
current_phase_name: Request authorization and write integrity (INSERTED)
status: executing
stopped_at: Completed 06.2-03-PLAN.md
last_updated: "2026-10-29T12:14:57.671Z"
last_activity: 2026-10-29
last_activity_desc: Phase 06.2 execution started
state_head: e2f133069481a168a979ed254f8ee54fbdb6fcb5
progress:
  total_phases: 9
  completed_phases: 7
  total_plans: 33
  completed_plans: 30
milestone_name: milestone
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-29)

**Core value:** Every public theme name settles once, consistently, before 1.0.0 freezes it — no public name changes twice.
**Current focus:** Phase 06.2 — Request authorization and write integrity (INSERTED)

## Current Position

Phase: 06.2 (Request authorization and write integrity (INSERTED)) — EXECUTING
Plan: 4 of 6
Status: Ready to execute
Last activity: 2026-10-29 — Phase 06.2 execution started

Progress: 27/33 plans executed; 7/9 phases complete (78%); Phase 6.2 planned and review-converged

## Performance Metrics

**Velocity:**

- Total plans completed: 27
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
| 06 | 10 | - | - |
| 06.1 | 3 | - | - |

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
| Phase 06 P05 | 15 min | 2 tasks | 5 files |
| Phase 06 P06 | 20 min | 2 tasks | 10 files |
| Phase 06 P07 | 14min | 3 tasks | 7 files |
| Phase 06 P08 | 16 min | 3 tasks | 14 files |
| Phase 06 P09 | 22min | 2 tasks | 3 files |
| Phase 06 P10 | 13min | 3 tasks | 7 files |
| Phase 06.1 P01 | 12 min | 3 tasks | 12 files |
| Phase 06.1 P02 | 8 min | 2 tasks | 4 files |
| Phase 06.1 P03 | 9 min | 2 tasks | 7 files |
| Phase 06.2 P01 | 16 min | 3 tasks | 8 files |
| Phase 06.2 P02 | 30 min | 3 tasks | 9 files |
| Phase 06.2 P03 | 30 min | 2 tasks | 7 files |

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
- [Phase 06]: 06-05: ListViewFilterFormHelper calls FormHelper.__init__() without the form and keeps helper.form identity, so form= never replaces a declared layout
- [Phase 06]: 06-05: filter layouts are deep-copied into a private always-truthy layout, prepared in get_attributes() before crispy's dispatch guard; exactly-once actions keyed on prepared-layout identity
- [Phase 06]: 06-05: get_form_actions() None omits the filter action group, empty FormActions keeps an explicit empty group; hidden sort/order/dir stay add_input(Hidden) after the actions
- [Phase 06]: 06-06: form cv_form_actions_label_mode uses a form-only policy (E211 shape stops traversal, E210 per invalid mode, W291 unknown kinds with valid modes); settings form map is E106 and ViewSet form map a construction error against FORM_KINDS
- [Phase 06]: 06-06: W292 static reach picks the provider first (CrispyDeleteForm delete+cancel, else submit+cancel), filter helpers with inherited get_form_actions, concrete dict polymorphic_forms; overridden hooks and custom get_form_class are runtime-only
- [Phase 06]: 06-06: icons._icon_available decides availability without rendering (registry None/empty, unknown prefix, unusable renderer, invalid built-in font class); the form normalizer raises in strict mode, else logs per render and falls back to label
- [Phase 06]: 06-07: modal.js, viewset.js and list.filter.js stay byte-identical; native submitter, cancel and reset regressions pass on the existing handlers and are proven discriminating by source mutations
- [Phase 06]: 06-07: crispy_floor nox session (py3.12 x Django 4.2/6.0, crispy 2.0 / crispy-bootstrap5 2023.10) deselects only the pack-whitespace-bound filter region golden; test_filter_form_controls_match_golden byte-checks the leaf controls everywhere
- [Phase 06]: 06-07: list.filter.test.js:159 jsdom 30.1.2 selector failure fixed test-only with :scope; full JS gate 223/223
- [Phase 06]: 06-08: Form resolution prose lives once in action_menus.md (Form label-mode resolution, Form checks); settings.md adds separate form rows to the single merge/replace table
- [Phase 06]: 06-08: The migration guide's Form buttons section is a top-level section before A downstream theme, keeping Table pagination overrides adjacent to Silent breaks
- [Phase 06]: 06-08: The example sets only CRUD_VIEWS_LABEL_MODE_DEFAULTS form=both; other locations keep their package floors
- [Phase 06]: 06-09: whole-repo ruff format --check recorded as not green (9 pre-existing planning Markdown files, WINDOWS #4); code and Phase 06 changed files formatted
- [Phase 06]: 06-09: hover tooltip, visual quality, screen reader and migration readability remain pending human; automated Chromium evidence covers names, focus, focus tooltips, cancel, filter reset and modal submit
- [Phase 06]: 06-10: icon= omission is stored as the private bool _cv_kind_icon (sentinel compared in __init__ only); deepcopy isolation of filter layouts kept
- [Phase 06]: 06-10: _form_button_data treats any non-str or whitespace-only cv_icon as None before availability, diagnostics, host classes and the leaf; accepted strings kept exactly
- [Phase 06]: UAT 4/4 passed; review IN-01..IN-03 fixed (aed6003, 92d5430, d75fb31; disposition open 0/6); re-verification 42/42 passed (dbca22e); full suite 4632 passed
- [Phase 06.1]: Cancel link eligibility is cv_key cancel AND native type button; explicit tag validated at adapter construction (None/button quiet), a requires form:cancel slot
- [Phase 06.1]: Invalid selected form:cancel-tag raises in strict mode, else warns and renders button; valid explicit tag never reads the table; E365 for invalid str values, E361 for non-str
- [Phase 06.1]: FORM_TAGS and CANCEL_TAG_KEY live in button_classes (pre-setup importable); form leaf branches on effective cv_tag with byte-identical button branch
- [Phase 06.1]: Cancel links drop WHATWG button-only attributes, name/type/value, extra href and data-cv-cancel-url case-insensitively; filtering only when final cv_tag is a
- [Phase 06.1]: On a link, case variants of generated id/class (and title/data-cv-tooltip in icon mode) are dropped; fallback/default buttons keep every extra byte for byte
- [Phase 06.1]: 06.1-03: tag= keyword change recorded in the existing Form buttons Breaking entry with paired migrating-1.0.md guidance; cancel links are an Added entry
- [Phase 06.1]: 06.1-03: real-browser cancel-link acceptance (no-JS, new tab, disabled) left pending for end-of-phase UAT; jsdom proves handler noninterference only
- [Phase 06.1]: UAT 3/3 passed via automated Chromium (JS-disabled click/Enter/middle-click, disabled fallback, JS-on non-interception), user-confirmed; verification canonicalized to passed
- [Phase 06.2]: HTTP DELETE rejected by a private dispatch guard (_DeleteMethodGuardMixin) between CrudView and Django DeleteView; _allowed_methods drops DELETE from 405 Allow/OPTIONS; DeletionMixin.delete identity kept (no Django 4.2 warning)
- [Phase 06.2]: Delete previews expose has_protected_objects (from the unfiltered collection) and only permitted protected_objects; core filters by model view permission, Guardian by object grant with per-view global fallback (no core re-filter)
- [Phase 06.2]: 06.2-02: Guardian parent-None (permission key None) skips only the permission check; dispatch still resolves the URL parent (404) and runs cv_action_enabled with it; create helpers share the dispatch resolver and accept only the parent or a single-FK own child (M2M/unrelated deny)
- [Phase 06.2]: 06.2-02: Inactive authenticated actors are denied in every Guardian request gate and callable helper (querysets .none(), helpers False, _PermittedPks empty, strict ViewSet helper empty); active superuser semantics unchanged (D-05)
- [Phase 06.2]: 06.2-02: Rendered controls compute state via private CrudView._cv_action_enabled_for_context (ContextButton classes, card branches, view context); Guardian nested create overrides it to pass the resolved parent; request dispatch keeps calling cv_action_enabled directly
- [Phase 06.2]: Fragment requests resolve self.object via get_object() (None for create) before rendering; Guardian object/state gates apply and missing or wrong-parent targets 404
- [Phase 06.2]: Private FormSets._cv_validate_fragment_coordinates validates key path, pk grammar, endpoint root, top/child indices, FK ancestry (exists()) and guarded ASCII indices; failures are 400 before rendering and only canonical values render
- [Phase 06.2]: FormSet.init renders unsaved instances as None even with a default UUID pk (A14); integer-pk output unchanged
- [Phase 06.2]: formset.js pk regex anchored after '-' so multi-digit integer pks are no longer truncated (Rule 1 fix)
- [Phase 06.2]: A19 non-first child emitted-index mismatch stays deferred to proposed 6.3; both siblings keep authorization and ancestry checks

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2: Ruff 0.16.10 is below the manifest range and global formatting flags eight pre-existing planning
  Markdown files; product formatting passes. See phase deferred-items.md and WINDOWS entry 4.

- Phase 7: needs a spec or maintainer decision before planning.
- Phase 7: retain the decided stable label-mode names; track the separately planned `no_label` removal before 1.0.
- Phase 7: carry the Phase 5 class key `pagination:hidden-label` into the stability surface.

- [Phase 4] Four open Info review findings (IN-01 `[role~="alert"]`, IN-02 hand-copied allowlist, IN-04 no guard for
  the non-core data-bs-* sentence, IN-05 missing-script enumeration) — see 04-REVIEW-DISPOSITION.md; candidates for Phase 7.

- Phase 2: Both source-probe classifier limitations remain documented; explicit tests and completed human prose UAT independently establish acceptance. See 02-VERIFICATION.md.
- Phase 7: carry the Phase 6 form surface (`form` location, `tags/button/form.html`, `FORM_LEAF_KEYS`, `get_form_actions()`, icons `save`/`cancel`/`filter-reset`) into the stability doc.
- Phase 7: carry the Phase 6.1 additions (`form:cancel-tag` key, `Button(tag=...)` keyword, `cv_tag` leaf field, `crud_views.E365`) into the stability doc.

### Roadmap Evolution

- Phase 06 edited: User decision D-18: verify completed Phase 1/2 contracts on executing working branch before spec; main merge no longer prerequisite
- Phase 6.1 inserted after Phase 6: Cancel form button as a link (#275); complete before Phase 7 freezes the theme surface (URGENT)
- Phase 6.2 inserted after Phase 6.1: Request authorization and write integrity (analysis B1–B7); complete before Phase 7 freezes the theme surface (URGENT)

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-29T12:14:56.942Z
Stopped at: Completed 06.2-03-PLAN.md
Resume file: None
