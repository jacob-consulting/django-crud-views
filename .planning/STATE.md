---
gsd_state_version: "1.0"
milestone: v1.0
current_phase: "06.21"
current_phase_name: "Snippet context exposes `view` and `parent_object` (#339) (INSERTED)"
status: executing
stopped_at: Phase 06.21 context gathered
last_updated: "2026-11-09T20:06:22.220Z"
last_activity: 2026-11-09
last_activity_desc: "Phase 06.19 shipped as PR #340"
state_head: 67a12db413aecd0bf98faf8241639f6a063f758c
progress:
  total_phases: 27
  completed_phases: 22
  total_plans: 154
  completed_plans: 152
milestone_name: milestone
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-09)

**Core value:** Every public theme name settles once, consistently, before 1.0.0 freezes it — no public name changes twice.
**Current focus:** Phase 06.20 — ViewSet `verbose_name` / `verbose_name_plural` override that every default label follows (#338)

## Current Position

Phase: 06.21 (Snippet context exposes `view` and `parent_object` (#339) (INSERTED)) — READY TO EXECUTE
Plan: Not started
Status: Ready to execute
Last activity: 2026-11-09 -- Phase 06.19 shipped as PR #340

Next: Phase 06.20 ($gsd-discuss-phase 06.20); then Phase 06.21

### Phase 06.19 completion — 2026-11-09

- Re-scoped: plans 06.19-01/02 (cv_default_sequence / cv_exclude_actions / cv_list_actions = None) reverted in e35a6b66 under the maintainability rule; replaced by the one-line Meta.sequence check (6bf4cc35), tests/test1/test_table_meta.py (e95730d0) and docs (560bd2a6).
- Verification passed 9/9 (re-scoped goal); full suite 12197 passed multicore; ruff and mkdocs --strict clean. Deep review of the current code: 0 critical, 3 warnings, 3 info — all open in 06.19-REVIEW-DISPOSITION.md.
- Documentation drift: ROADMAP Scope/Success criteria and phase name, CONTEXT D-01..D-16, SECURITY threat register and the superpowers plan still describe the reverted design.

### Phase 06.18 completion — 2026-11-09

- UAT 06.18: 71 rows (5 human, 66 automated). Test 2 failed on an unmigrated example DB (TypeError on the nested Guardian Note list); diagnosed and closed by gap-closure plan 13 (Guardian views fail closed with ImproperlyConfigured on a missing permission key; cv_has_access False). Gap G-06.18-2 resolved by 06.18-13-PLAN.md.
- Quick tasks during UAT: 261109-9rw (examples: nested Guardian Note + core nested ancestor tests), 261109-bf5 (core default_permissions vocabulary N+1 fix), 261109-bvq (06.18-COSTS.md refreshed and number-checked).
- Re-verification passed 52/52 (81188a4b); full suite 12185 passed, 1 skipped on Django 5.2 multicore; incremental review of plan 13: 0 critical, 1 warning (test helper cache restore scope), 2 info — open in 06.18-REVIEW-DISPOSITION.md.

### Phase 06.18 plan 12 — 2026-11-08

- Paired the CHANGELOG `### Breaking` entry "Ancestor authorization for nested ViewSets" with the new docs/migrating-1.0.md#ancestor-authorization-for-nested-viewsets section. It covers removed fields, defaults, provider/fallback, exact actions, nested manage, the nested-write-database-selection anchor for the instance-hinted selector refusal, and boundaries. An executed Guardian approve-pair migration fence and six new test_ancestor_docs.py functions pair both surfaces. nested.md#databases links the anchor.
- Final source 5829cae7 (src identical to e85ed2b4): focused selection 2607 passed on each of Django 4.2.30 / 5.2.19 / 6.0.9 crispy floor (Python 3.12.3); full 5.2 suite 12163 passed, 1 existing skip; scoped Ruff (55 files) and strict MkDocs pass; cost replay identical to plan 10 (5.2 only). The first replay found two test-fixture portability failures (crispy < 2.7 filter helper; Django 4.2 AdminEmailHandler report). They were fixed in tests and logged in deferred-items. All 26 acceptance rows are bound to existing selectors; ANCE-01–08 are marked complete. Not a phase seal. Existing config/state.json/CLAUDE edits preserved; no push or merge.

### Phase 06.18 plan 11 — 2026-11-08

- Published the ancestor-authorization guidance in nested/settings/resources/request_lifecycle/guardian docs, tutorials 5/6 and the reference index. Six published fences are executed by the new test_ancestor_docs.py (31 cases): the canonical Publisher -> Book example with an exact approve pair, settings, Resource leaf scoping, the hint-sensitive router refusal (atomic on/off, top-level control), and the Guardian parent and fallback examples with direct/group grants, child-denial controls and nested manage.
- Full Django 5.2 suite: 12156 passed, 1 existing skip. Strict MkDocs passes. ANCE IDs stay open for plan 12, which owns the Breaking/migration entry, its anchor link from nested.md#databases, and the final gates. Existing config/state.json/CLAUDE edits preserved; no push or merge.

### Phase 06.18 plan 09 — 2026-11-08

- Manage pages report the declared ancestor policy: new ManageView context entry ancestor_policy with as_ancestor (provider, effective provider, ancestor fallback) and requests (cascade/read/write declared vs effective, exact actions; None at top level), rendered as a configuration-only table. Guardian alert rows read the same entry; local per-view fallback and strict helper rows unchanged.
- New test_ancestor_manage.py (34) pins nested manage as ancestry AND the local settings/group gate across core/Guardian, public/group, both cascade modes, all-none and top-level. New test_ancestor_redirect.py (28) pins the built-in redirect as Read before lookup with an independently authorized destination; no child.py change needed (mutation checks 24/16 failed).
- Full Django 5.2 suite: 12068 passed, 1 existing skip. ANCE-03/07 stay open for sibling plans. Existing config/state.json/CLAUDE edits preserved; no push or merge.

### Phase 06.18 plan 08 — 2026-11-08

- Eight legacy Guardian authorization modules migrated to explicit AncestorPolicy declarations. Old None scenarios use their own provider "none" parents, and strict siblings stay protected. Update/delete page overrides are used only where the create control must stay independent of page access. Parent-owned fallback replaces child flags. Every new grant has a paired deny control.
- New test_ancestor_migration.py (21 cases) covers core/Guardian opposite outcomes, the default Write pair, fallback independence across descendants, nested create state without child add, and legacy rejection. Rule 1 fix: the Guardian nested no-object state gate now reads the guard-resolved parent.
- Plan 01 observation command: exit 0, 1522 passed. Full Django 5.2 suite: 12004 passed, 1 existing skip. No H1/H2 transition row remains, and WINDOWS 38 is fixed. ANCE-01/04/07 stay open for sibling plans. Existing config/state.json/CLAUDE edits preserved; no push or merge.

### Phase 06.18 plan 02 — 2026-11-08

- One bounded ancestry walk for URL construction, parent helpers, scoped queryset and the request guard; cycles/missing parents raise a named-chain ImproperlyConfigured with no DB access. Relationships validated from model metadata (E266 + request guard); Resource parents keep the single E261.
- Finite class-based families plus the polymorphic selector marker; exact literal-key actions (E267), nested custom endpoints need an entry (E268 + runtime, all-none too). Checks import root/included URLconfs first and defer completion-dependent messages otherwise. Task gates 40/128/90 passed at 8e7d9d09; scoped Ruff passes.
- Transition: 18 H1-core rows closed with exact Publisher grants and independent controls; 110 open (H1-guardian 91 + 13 newly reached by Card/manage classification → 03.1, action 1 → 03.2, fragment 2 → 04.2, resource 3 → 05.2), zero H2-custom; full 5.2 suite fails only on that set. ANCE-02/03/04 stay open for sibling plans. Existing config/state.json/CLAUDE edits preserved; no push or merge.

### Phase 06.18 plan 01 — 2026-11-08

- Shared request-local ancestor guard in CrudView.dispatch with strict AncestorPolicy/AncestorPermissions, validated CRUD_VIEWS_ANCESTOR_* settings and pre-registration ViewSet policy validation. Behavioral proof is limited to the plain nested list/create composition.
- Pre-edit baseline at d5567ba2 (transition 1475 passed; query observations one/three ancestors, plain/Guardian, list/object/create, cold/warm) retained under evidence/06.18-01. Task gates: 13 and 97 passed at f717e58d; scoped Ruff passes.
- After plan 01 the transition observation has 115 eligible failures (H1-core 18 → 02.3, H1-guardian 91 → 03.1, H1-action 1 → 03.2, H1-fragment 2 → 04.2, H1-resource 3 → 05.2), no collection loss; full 5.2 suite has no failure outside that set. Interim: unclassified nested families do no ancestor work until 02.2 (WINDOWS). ANCE-01/04/08 stay open for sibling plans. Existing config/state.json/CLAUDE edits preserved; no push or merge.

### Phase 06.17 completion — 2026-11-07

- All three plans committed; canonical verification passed15/15, ODT-01–05, D01–D20 and32 UI considerations accounted for. No required human checks or implementation blockers.
- Independent deep review clean19 files; security9/9 closed; Nyquist no gaps; UI preservation24/24. WINDOWS36 documentation classifier-order exception independently reviewed and explicitly waived; historical violation remains recorded.
- Final source full5.2:10,849 passed/one existing skip; focused177 each4.2/5.2/6.0 on Python3.12.3; JS383; browser18/472 with53 matching hashes and cleanup; examples409 plus100subtests. Strict docs/scoped Ruff pass. Broader runtime/visual/AT coverage unclaimed.
- Completion warnings misparse inline commands as paths; actual referenced artifacts exist. No learnings/todos/handoffs require graduation or closure. Phase7 ready for discussion; existing config/state.json/CLAUDE/notes preserved; no push or merge.

### Phase 06.17 plan 03 — 2026-11-07

- Published five-entry adapter/lifecycle/loading contracts, exact-source namespace/map examples, first-open copied accordion recipes and paired Breaking/current migration guidance. No production source changed in this plan.
- Final source e24fec82: full Django5.2 10,849 passed/one existing Django6-only skip in304.72s; focused177 each Django4.2/5.2/6.0, all Python3.12.3/four workers. JS383, browser18 cases/472 assertions with53 matching hashes and cleanup, harness19, strict docs and scoped Ruff pass.
- Summary and acceptance committed; roadmap3/3 remains In Progress, ODT-01–05 complete. Independent reviews/verification remain pending. WINDOWS36 records Task1 documentation edits preceding classifier approval; actual pre-edit RED and final GREEN evidence retained, no silent waiver. Task2 gate order compliant.
- Last-plan SDK reports ready_for_verification; aggregate progress handler declined its existing unscoped read. State prose synchronized. Existing config/state.json/CLAUDE edits and notes/.gitkeep preserved; no phase completion, push or merge.

### Phase 06.17 plan 02 — 2026-11-07

- Lazy tab factory and owned adapter dispatch committed with default/override/no-op/error contracts; existing modal and keyboard ownership preserved. Both tasks have classifier-approved RED and GREEN commits.
- Final focused JS 74, asset tests 8 with four workers, harness guards 19 passed. Real browser 18 cases/472 assertions with 53 matching source hashes proves stock and alias-free tabler initialization, keyboard/repeat/focus and attached disposal during HTTP replacement; cleanup complete. Scoped Ruff passes.
- Summary committed; roadmap 2/3 In Progress, ODT-02/03/04 complete. Plan 03 owns public docs/migrations and final gates. Aggregate progress SDK declined its existing unscoped read; plan counter advanced to 3/3. User edits preserved; no push, merge or phase completion.

### Phase 06.17 plan 01 — 2026-11-07

- First-open accordion state committed with no new controller/configuration; existing Collapse switches and closes all. Both tasks have classifier-approved RED evidence and GREEN commits.
- Final targeted rendering/a11y suite: 139 passed with four workers; heading/identity tracer: 103 passed. Browser: 14 cases/348 assertions, including real fresh modal HTTP loads for one/two groups; cleanup complete. Harness guards: 19 passed; scoped Ruff passes.
- Summary committed; roadmap 1/3 In Progress. ODT-01 complete; shared ODT-04 awaits Plan 02 tab/alternate-namespace acceptance. Plan 03 owns documentation/migration and full phase gates. No human visual/AT, full support matrix, push or merge claimed.

### Phase 06.16 completion — 2026-11-06

- All three plans committed; canonical verification passed21/21 and D01–D20 honored. All five ODV requirements complete; no required human checks or downstream adoption gate.
- Deep review found numeric choice fallback localization; bounded stock/copied-template fix72df30bc independently re-reviewed clean. Review disposition fixed1/open0; security11/11 closed; Nyquist no gaps; UI24/24 source-only, without browser/human acceptance claims.
- Final source: full Django5.2 10,837 passed/one existing Django6-only skip; focused4.2/5.2/6.0 665each; examples409 plus100subtests; independent verifier129 fresh cases. Strict docs/scoped Ruff pass. Broader Python matrix unrun; symbolic key-link CLI limitation covered by direct source/test tracing.
- Phase7 is ready for discussion. No learnings artifacts, matching pending todos or stale phase handoffs. Existing config/state.json/CLAUDE edits preserved; no push or merge.

### Phase 06.16 plan 03 — 2026-11-06

- Published choice/help/raw-display contracts, unique copied badge/text recipes, five complete/core/Guardian/polymorphic context recipes, and paired Breaking migration/restoration paths. The new documentation suite has 35 passing cases.
- Final current-source gates: full Django 5.2.18, 10821 passed/1 expected existing skip in 302.53s; focused Django 4.2.30/6.0.9, 649 passed each. All used Python 3.12.3 and four workers; strict docs and scoped Ruff pass.
- Summary committed; roadmap 3/3 remains In Progress. Shared ODV-01–05 readiness passed and implementation requirements are marked complete; independent phase audits/approval remain pending. No full Python matrix, browser/human approval, downstream adoption, push or merge claimed.

### Phase 06.16 plan 02 — 2026-11-06

- Strict help instructions, view/project inheritance and terminal-only lazy help are committed. Stock char/text/default now mark exact None/empty text while retaining rows, descriptions, raw/custom values and non-text semantics.
- Final combined gate: 590 passed in 12.04s on Python 3.12.3/Django 5.2.18 with four workers; scoped Ruff checks pass. Tasks 1/3 have classifier-approved RED evidence; task 2 is documented test-only expansion of already-implemented behavior.
- Summary committed; roadmap 2/3, next plan 3/3. Shared ODV-02/ODV-03/ODV-05 await plan 03 documentation/migration and final runtime gates. No browser/human acceptance, push or merge claimed; config/state.json/CLAUDE changes preserved.

### Phase 06.16 plan 01 — 2026-11-06

- Scalar choice display, one-walk terminal owners and badge fallback committed with raw callback/template values preserved. Missing scalar owners retain raw None/[]; collections and ordinary paths preserve query costs.
- Final combined gate: 389 passed with four workers on Python 3.12/Django 5.2; scoped Ruff checks pass. Three RED reports classified RED_EVIDENCE_OK before their GREEN commits.
- Summary committed; roadmap 1/3, next plan 2/3. Help policy, exact empty markers, public migration documentation and final phase-wide runtime gates remain with plans 02/03. Shared ODV-01/ODV-05 remain pending; no push or merge.

### Phase 06.16 plan convergence — 2026-11-06

- Three plans across three sequential waves are ready to execute. Fable, Grok and Gemini reviewed all three plans; cycle 4 closed with zero HIGH concerns, zero actionable non-HIGH findings and zero open revision conflicts. Final review: 76725e33; reviewed plans: d328e956.
- All 20 discussion decisions and ODV-01–ODV-05 have executable coverage. Plan frontmatter/structure and post-planning gap checks pass. Implementation and acceptance tests remain pending.
- Source-audit coverage limits are recorded in REVIEWS.md: the intel adapter cannot check Python symbols, and the phase-status seam did not recognize the roadmap section. Supplemental source inspection and other artifact comparisons remain separately attributed.
- No production changes, push or merge. Unrelated CLAUDE.md and state.json edits preserved.

### Phase 06.14 completion — 2026-11-06

- Both plans committed; canonical verification passed12/12, D01–D12 honored, no required human checks. Production change is exactly two empty card blocks; executable docs cover cards-first/table-secondary configuration and independent navigation.
- Full Django5.2 execution10,136 passed/one expected skip; focused4.2/6.0 198each; JS365; scoped Ruff/strict docs pass. Final verifier77 fresh tests pass. Runtime/full-matrix/browser/gettext-extraction limits remain explicit.
- Validation4/4 tasks compliant; security7/7 closed; UI preservation24/24 without visual-browser claim. Deep review found one extraction warning, fixed by gettext_noop markers and independently closed; post-fix24 recipe tests/strict docs pass.
- UI safety gate initially required a missing contract; approved preservation-only UI-SPEC and25 explicit probe truths clear it. Completion warnings misparse the verified git-show baseline command as a path; no missing artifact.
- Next scheduled phase06.13.1 is planned and ready to execute. No LEARNINGS files/todos required graduation or closure. Config/state.json edits preserved; no push or merge performed.

### Phase 06.15 acceptance closeout — 2026-11-06

- User explicitly passed both visual and browser interaction checks. UAT 2/2 and canonical 16/16 passed; shared completion predicate has no blockers. All four plans complete; roadmap/state advanced to planned Phase 06.13.1.
- Isolated UAT instance remains running on port 9000 at https://cv.jacob-consulting.org, with fresh seeded data and source-bound consumer snapshot. Original database and checkout preserved. Existing tests and audit evidence retain their original source attribution.
- Completion scanner misread the command fragment `-c examples/bootstrap5/pytest.ini` as a path; the actual config file exists. No delivery artifact missing. No LEARNINGS files to graduate and no stale phase handoffs. Earlier pending-human statements below are historical.
- No push or merge. Unrelated config edits preserved.

### Phase 06.15 execution and verification — 2026-11-06

- All four plans committed; canonical verification human_needed: 16/16 truths and 19/19 decisions verified, two human items persisted in 06.15-UAT.md.
- Review repaired mapping fallback/mutation and bare Django Model check crashes in 06dca6d5/b2aebe49, with five regressions. Review zero open; security 12/12 closed; validation compliant. UI audit source-only, visual/browser acceptance unclaimed.
- Final source: 90 focused tests each on Django 4.2/5.2/6.0; 8,398 prior-phase regressions plus 100 subtests; 18 consumer tests and warning-level checks; seven independent cases and strict docs passed. Earlier full 5.2 result (10,175 + one skip) remains pre-fix evidence.
- Downstream 542936d/6a8e4f9 remain on gsd/phase-06.15-polymorphic-adoption. Another actor switched its checkout to main and advanced it; final consumer checks used a pinned archive, preserving current checkout and original report edits.
- No phase completion, next-phase advance, push or merge. Unrelated config preserved; codebase map drift advisory.

### Phase 06.13.1 acceptance complete — 2026-11-06

- User explicitly passed both required UAT checks on the external review domain: narrow/wide page/modal presentation and Tab/visible-focus/disabled-action behavior. Canonical verification promoted to passed; shared UAT-plus-verification gate has no blockers. All five plans and WFX-01–05 complete.
- Independent code review is clean; all 15 security threats closed. Automated evidence remains attributed to its original runs: final full Django 5.2 10,413 passed/one existing skip; focused Django 4.2/6.0 1,463 each; browser 37+2. No new runtime, AT or translation-quality acceptance inferred.
- Owned port-9000 fixture stopped and disposable database cleaned; tunnel unchanged. Completion scanner warnings refer to the valid package-relative widget template and an inline multi-file Ruff command, not missing files. No learnings artifacts to graduate. Phase 7 is next; no push or merge performed.

### Phase 06.13.1 independent verification — 2026-11-06

- All five plans committed. Canonical verification is human_needed, 29/31 truths verified, all 17 decisions honored, no implementation blocker. Two explicit plan/UI acceptance items are persisted in 06.13.1-UAT.md: representative narrow/wide page/modal visuals and native Tab/visible-focus/disabled-action behavior. No human approval inferred.
- Deep review is clean after three reproduced fixes: current-source FSM metadata, public-helper refusal isolation, and cooperative Guardian scoped reload. Security closes all 15 threats after literal SafeData POST-error repair and final independent recheck. Validation is compliant; UI audit 21/24 documents evidence limitations.
- Final full Django 5.2: 10,413 passed/one existing CSP skip; focused Django 4.2/6.0: 1,463 each; browser 37+2 with 498 current hashes and separately bound Guardian source. Independent reviewer 56, security 26, verifier 103 Python/65 Node checks pass. Earlier smaller counts below are historical.
- Required regression gate is covered by the final full suite run after all product repairs; no source change followed it. JS 365, strict docs and scoped Ruff remain green. Existing user config/CLAUDE and state.json diffs preserved. No push, merge, publication or phase advance.

### Phase 06.13.1 plan 05 — 2026-11-06

- Exact workflow helper/hook/widget/lifecycle contracts, mandatory routing migration and German source/compiled comment markers are documented and tested. All five plan summaries exist; roadmap remains In Progress pending review/verification.
- Final full Django 5.2: 10356 passed/one existing CSP skip; focused Django 4.2 and 6.0-floor: 705 each; JS 365; German catalog/render 7; strict docs and scoped Ruff passed. The first full run exposed lost stock workflow W292 diagnostics; a bounded provider-recognition fix and regressions restored them.
- Browser receipts refreshed after final source changes: 37 all cases plus 2 smoke, 497 matching source hashes and owned cleanup. R23 observed eight exact unreferenced vendor-wrapper exemptions on Django 4.2/crispy 2026.3; owned IDs/descriptions remain strict. Human visual/screen-reader/copy judgments remain unclaimed.
- WFX-05 passed shared-ID readiness and is complete; overall requirement reconciliation remains with phase verification. Existing CLAUDE/config/state.json edits preserved; no push or merge.

### Phase 06.13.1 plan 04 — 2026-11-06

- Complete native-page/real-modal browser acceptance passed 37 cases plus 2 smoke cases with 497 source hashes and owned cleanup. Four narrow/wide long-content screenshots and all 25 UI consideration mappings are recorded in the plan summary.
- Browser evidence exposed a stock comment-label overflow; bounded button-mode field-column wrapping passed 86 workflow regressions. Independent receipt/asset rejection passed 65 Node tests; scoped Ruff passed.
- WFX-03/WFX-04 are complete under the shared-ID readiness check; WFX-05 waits for plan 05. Human visual, screen-reader and translated-copy judgments remain unclaimed. Phase remains In Progress, 4/5 plans executed; no push or merge.

### Phase 06.13.1 plan convergence — 2026-11-06

- Five plans across three waves are ready for execution. Fable, Grok and Gemini reviewed all five plans in each round; cycle 5 closed with zero HIGH concerns, zero actionable non-HIGH findings and zero open revision conflicts. Final review: 13457c2; reviewed plans: 5d06e11.
- All 17 discussion decisions and WFX-01–WFX-05 have executable coverage. Plan structure, task ownership and diff checks pass. This is planning approval; implementation and new acceptance tests remain pending.
- Database support is a planning choice: explicitly bind workflow writes to one selected alias and reject mismatched loaded identities, including replica-loaded inputs. Plans require Breaking/migration guidance; this restriction is not implied by the standalone helper API or attributed to a user-selected routing requirement.
- Review source-grounding limitations remain recorded in REVIEWS.md. No implementation, push or merge was performed.

### Phase 06.13 shipping — 2026-11-06

- Opened PR #324: https://github.com/jacob-consulting/django-crud-views/pull/324 targeting main from the phase branch; remains unmerged.
- Canonical verification passed; security threats_open is zero. Fresh shipping checks: 190 workflow/Cancel tests passed with four workers, strict MkDocs and scoped Ruff passed. Production/dependencies match main.
- Committed pending guidance/config/state and phase placeholders as f1716cd; generated review diagnostics and research caches retained locally via git info/exclude.
- Phase 7 remains ready for discussion. All seven codebase maps refreshed on this branch, with machine-readable mapping baselines stamped.

### Phase 06.13 completion — 2026-11-05

- Both plans complete; canonical verification passed 9/9, all five WFP requirements and fifteen decisions satisfied. Independent deep review clean; validation compliant; seven security threats closed. UI audit N/A; no human items required for this docs/test scope.
- Full Django 5.2: 10,108 passed/one existing skip; focused Django 4.2 and 6.0 crispy-floor: 131 each. JS regression 365 passed on cached Vitest 5.0.3; scoped Ruff/strict docs/five-fence syntax and anchor checks passed. Fresh verifier checks cover nine new cases and existing Campaign denial.
- One initial registration-inventory failure resolved by adding the new fixture expectation; original failure retained in summary. Production/Campaign unchanged; full Python matrix, concurrent revocation and Guardian/nested policy matrices unclaimed.
- Completion scanner misreads six inline Ruff command strings as file references; actual paths/checks were independently verified. No missing delivery artifact or behavioral debt found. Codebase maps remain stale (nonblocking advisory).
- Phase 7 ready for discussion. Existing PROJECT/config/CLAUDE/state.json edits and the user-authored 6.12 state entry preserved; no push or merge performed.

### Phase 06.10 shipping — 2026-11-05

- Opened PR #317: https://github.com/jacob-consulting/django-crud-views/pull/317 from `ship/phase-06.10-delete-preview-limit` to `main`. Verification passed and security threats_open is zero; all six DPV requirements and seven UAT checks complete.
- Shipping uses a clean managed worktree; original workspace edits preserved. CI started; PR remains unmerged. Independent phase code review is clean; optional additional PR review awaits the maintainer.

### Phase 06.10 acceptance closeout — 2026-11-05

- All seven human UAT checks explicitly passed; canonical verification and shared UAT/completion predicates pass. All five plans and six DPV requirements complete; WINDOWS 34 resolved. Earlier pending acceptance statements below are historical.
- Temporary Cloudflare UAT routes, copied templates, two owned authors, 54 Contracts, two Books and dedicated test user removed. Existing example service on port 9000 still returns HTTP 200.
- Plain protected labels replace synthetic destination requests; cascade navigation remains intact. The visible-occurrence budget bounds display and selected preparation only, not complete inspection/filtering/query cost.
- Phase 7 is ready for discussion. No LEARNINGS files exist for graduation; unrelated user edits remain separate. No push or merge performed.

### Phase 06.10 independent verification — 2026-11-04

- All five plans executed; canonical verification is human_needed, 18/20 deduplicated truths verified, no failed truth or implementation blocker. All 19 decisions honored; 35 original plan truths mapped. Seven human items persisted in 06.10-UAT.md; no approval inferred.
- Validation covers six requirements and thirteen tasks, compliant; fresh 456 Python/29 Node checks pass. Deep code review of 33 files is clean, with fresh 258 Python/13 Node passes. Final verifier adds 21 named passes; current browser evidence validates all 45 cases/557 source inputs/two screenshots.
- Security18/18 closed:17 mitigated plus existing maintainer D-12 aggregate-policy acceptance. SC disposition corrected from planned accept to verified cached/no-install mitigation; no new risk acceptance. UI20/24 with visual/keyboard/kind confirmation pending; font attribution remains historical, no product typography defect established.
- Final-source full5.2 9,671+1expected skip, focused4.2/6.0 2,555 each, examples409+100subtests, JS365, fragments2, Node29, Ruff and strict docs remain current: no product/test/doc changes since acceptance source e59b99a. Runtime and cached Vitest limits remain explicit.
- Phase remains In Progress; no next-phase advance, push, merge or publication. Unrelated PROJECT/config/CLAUDE/state.json and diagnostics preserved. Earlier pending-independent-review entries below are historical.

### Phase 06.10 Plan 05 execution — 2026-11-04

- Existing browser harness now verifies plain blockers, real visible/hidden Books, shared limits 2/3/4/None, preserved book:2 summaries, empty-detail omission and ordinary full-document Book click/Enter navigation. Final 45-case stock/copied page/modal report binds 557 source inputs, exact recipes and two screenshots; owned process/database cleanup passed.
- Required gates passed: full Python 3.12 / Django 5.2: 9,671 passed, 1 expected Django-6-only skip; focused 4.2/6.0: 2,555 each; examples: 409 plus 100 subtests; JS: 365; fragments: 2; Node: 29; whole-tree Ruff and strict MkDocs. Broad Python runs used four workers. The isolated skipped CSP test passed on 6.0; WINDOWS 33 records that coverage.
- Acceptance and raw output artifacts disclose Django 6.0 crispy-floor pins, cached Vitest 5.0.3 versus declared ^5.0.5, and unrun Python/full Cartesian coverage. No dependency install, production change, push or merge occurred in this plan.
- Plan execution is 5/5; phase and shared DPV completion remain pending independent review. Human visual/keyboard/UI-kind acceptance and three presentation checks remain pending (WINDOWS 34); nyquist_compliant and wave_0_complete remain false. SDK roadmap update kept In Progress; unscoped progress update declined. Existing state.json and unrelated user changes were preserved.

### Phase 06.10 Plan 04 execution — 2026-11-04

- Library and Guardian Delete examples teach plain protected labels, retain independent Contract access and full-page Book cascade links, and prove finite/None display never changes blocked GET/POST row preservation. Source-sync and live/tutorial prose tests pass; models, grants, seeds and defaults are unchanged.
- German shortening notice is compiled through existing polib, byte-identical on regeneration, and tested independently of completeness across page/modal overflow/exact/hidden-only/unlimited cases.
- Full examples: 409 passed / 100 subtests; locale selector: 17 passed; preserved inspection/migration gate: 351 passed. Four workers, current source, Python 3.12 / Django 5.2; strict MkDocs and scoped Ruff pass. All final RED records classify RED_EVIDENCE_OK.
- Three tasks and summary committed; roadmap 4/5, plan position 5/5. Plan 05 owns final browser/runtime acceptance; shared DPV requirements, human presentation checks and native-speaker translation review remain unclaimed. SDK progress update declined the unscoped phase; existing state.json edits were preserved.

### Phase 06.10 Plan 03 execution — 2026-11-04

- Exact copied content/related/body recipes retain byte/hash identity and now render one truthful shortening notice, plain protected labels and independently guarded summaries/details, including an unblocked solo root.
- Configuration, Breaking/migration, theme and Guardian guidance document default 50, explicit None, strict checks, protected-first visible selection and full inspection/filter cost limits. Phase 7 handoff records final names and pending acceptance.
- Final migration suite: 129 passed with four workers on current source/Python 3.12/Django 5.2. Strict MkDocs build and scoped Ruff checks passed; RED evidence independently classified RED_EVIDENCE_OK.
- Three tasks and summary committed; roadmap 3/5, plan position 4/5. Plans 04/05 own examples/locale and final browser/runtime acceptance. Shared DPV requirements and human presentation checks remain open. SDK progress update declined the unscoped phase; scoped plan/roadmap counts advanced without marking the phase complete.

### Phase 06.10 Plan 02 execution — 2026-11-04

- Strict raw project/inherited view configuration supports positive integers and explicit None; default 50, E109/E265 and effective-value runtime checks include preview-off/non-strict requests.
- Local protected-first selection preserves visible DFS occurrences, promotes hidden descendants and prepares only selected cascade URLs. One translated shortening notice reflects visible overflow; independent summary/detail guards retain solo roots and omit empty frames.
- Final broad delete/Cancel/form/authorization/settings gate: 2,410 passed with four workers. Component measurement: 108 passed; deliberate one-query hooks match selected occurrence counts while complete inspection/filter costs remain separate.
- All three tasks and summary committed; plan position 3/5, phase In Progress. Plans 03/04 own copied recipes, docs, examples and translations; Plan 05 owns final browser/matrix acceptance. Shared DPV requirements and human presentation/state acceptance remain open.

### Phase 06.10 Plan 01 execution — 2026-11-04

- Plain protected entries preserve obj/url=None and escaped labels; private destination adapter removed. Shared cascade URL, inspection, Guardian, Cancel and body-template source is unchanged.
- Real page/modal GET/POST tracer and read-only provider/write checks pass. Preserved delete/authorization-template gate: 1,453 passed with four workers; final scoped projection/Guardian/component gate: 70 passed.
- Fresh before/after component evidence covers core/Guardian sizes 0/1/4/8 and all preview/link flags. Protected hook/setup calls and presentation queries are zero; full inspection/filter costs remain separate and unbounded.
- Plan 01 summary committed. Plan 02 owns the cap; shared DPV requirements stay unchecked until later obligations are verified. Phase remains In Progress; no browser/human acceptance or full runtime matrix inferred.

### Phase 06.10 plan convergence — 2026-11-04

- Five plans, thirteen tasks, four waves; all nineteen decisions and six DPV requirements covered.
- Converged in four of five permitted cycles. Fable, Grok and Gemini covered all five plans; zero current HIGH, actionable non-HIGH or open plan-revision conflicts remain. Final review: 157aa73.
- Plan checks pass: five valid structures, 25/25 coverage items and 28/28 verification failure directions. Explicit None remains unlimited; no implementation or browser acceptance is claimed.
- Source references were checked; empty intel/signature coverage remains explicitly UNCHECKABLE. Grok's first-cycle database-lock failure recovered with the same reviewer; later OpenCode lanes ran sequentially.

### Phase 06.9 shipping — 2026-11-04

- PR #313: https://github.com/jacob-consulting/django-crud-views/pull/313; ship/phase-06.9-protected-delete-links targets main and includes Library quick task 261104-h24.
- Integrated main cf2bfc0 without conflicts. Refreshed canonical verification passes 31/31; existing UAT 1/1 and security 15/15 closed retained.
- Integrated checks: 1,484 core/delete/form tests, 406 example tests plus 79 subtests, 16 verifier cases and strict docs pass. Earlier full 9,448-test Python and 365-test JavaScript results remain attributed to their pre-merge source.
- Retained browser evidence is historical with one source-hash difference for the upstream checkbox-width change; protected previews omit that form. No new browser run or expanded human acceptance claimed.
- Original checkout and unrelated local changes preserved. PR awaits CI/review; no merge performed.

### Phase 06.9 verification refresh — 2026-11-04

- Canonical verification refreshed after the Library Contract example: passed 31/31, PDL-01–06 satisfied, existing UAT 1/1 and all 19 rules preserved.
- Fresh regression gate: 9,448 Python tests passed with one existing skip using four workers; all 365 JavaScript tests passed. Initial scoped collection required the normal full-suite entry point to initialize Django correctly.
- Validation compliant, security 15/15 closed, no new code-review findings, UI 23/24 with inherited contrast warning. Retained browser evidence was validated without claiming a new browser run.
- Completion warning references illustrative myapp template paths and package-relative template names in the Plan 03 summary; no implementation blocker. Unrelated config/state.json edits preserved. Phase 7 remains unplanned.

### Phase 06.8 verification refresh — 2026-11-04

- Canonical verification refreshed: 30/30 obligations and TIP-01–05 pass; existing UAT3/3 retained, security9/9 closed. Shared changelog/migration additions preserve tooltip recipes and contracts; no implementation changes.
- Fresh regression evidence: 1,011 Python tests with four workers and 365 JavaScript tests pass; verifier added four render-isolation cases and one callback lifecycle test. Retained browser49cases/97controls validated with explicit historical source differences; no new browser run or full Python matrix is claimed.
- Phase06.8 and Phase06.9 complete. Earlier pending or stale entries below are historical. Phase7 remains unplanned.

### Phase 06.9 completion — 2026-11-04

- User explicitly answered "pass" for all four UI surfaces and 19 state rules; UAT 1/1 passed, no issues. Canonical31/31 status promoted to passed; completion predicate has no blockers and all four plans are complete.
- Security15/15 closed. Existing automated evidence remains attributed to its original runs; no new browser, visual or assistive-technology testing is claimed.
- Earlier pending-confirmation entries below are historical and superseded. The transition tool routes to Phase 06.8 because its verification fingerprint is stale on shared changelog/migration docs; no new implementation failure is inferred.

### Phase 06.9 canonical verification — 2026-11-04

- All4plans committed; canonical31/31, status human_needed for one grouped explicit UI classification/state confirmation. No implementation gaps; phase not marked complete.
- Independent code review repaired class/inherited permission eligibility and actual modal/confirmed POST test coverage; rereview closed both with116tests+17descriptor probes. Fixer980passed per cached Django4.2/5.2/6.0; verifier114focused tests pass.
- Current browser17/17 refreshed against repaired source with556hashes, exact recipes,12assets and two screenshots. Original acceptance retained under history/pre-review; prior9439-test full runs are not claimed as final-source reruns. FinalJS365passed.
- Security15/15closed and reassessed after fixes; validation compliant6requirements/8tasks; UI23/24, nonblocking inherited contrast warning and optional visual evidence recommendations.
- Single confirmation persisted in06.9-UAT.md; no human response, risk acceptance or screen-reader observation inferred. Existing config/state.json and unrelated artifacts preserved. No merge, push or publication.

### Phase 06.9 automated execution — 2026-11-04

- All four plans executed; phase remains In Progress pending independent verification and human acceptance.
- Plan 04: 17 Chromium cases, exact copied recipes, 556 source hashes, 12 validated assets and two retained modal screenshots pass; owned server/database cleanup confirmed.
- Cached Python 3.12 / Django 4.2, 5.2 and 6.0 each pass 9439 tests; existing CSP skips and sole Django 6.0 crispy-floor golden exclusion remain explicit. Examples 302 + 43 subtests, JavaScript 365, integration 2, Node 26, strict docs and Ruff pass.
- Tutorial sync regression repaired; first Django 4.2 wrapper exit143 repeated to a measured exit0. No new dependency, product change or test exclusion.
- Validation fixture readiness is true; draft/compliance/phase audit status and 19-state human confirmation remain open. No external-theme, assistive-technology or unperformed Python-version acceptance inferred.

### Phase 06.8 shipping — 2026-11-04

- PR #305: https://github.com/jacob-consulting/django-crud-views/pull/305, branch ship/phase-06.8-action-tooltips, based on merged Phase 06.7 main e0e6e9a.
- UAT 3/3 passed: all six retained images, all six live stock/custom scenarios, and all 19 UI state considerations. Browser/version unspecified; no screen-reader claim.
- Fresh integrated checks: 9188 Python passed with one existing Django-6-only skip, 365 JavaScript passed, 28 Node runner tests passed, Ruff/format/strict docs passed. Canonical verification 30/30; all nine threats closed.
- Historical browser evidence was revalidated with explicit source deltas; no new browser execution or full supported Python matrix is claimed.
- Prior pending-human entries below are historical and superseded. PR awaits CI/review; no merge performed. Original checkout and its unrelated uncommitted files preserved.

### Phase 06.8 execution and verification — 2026-11-03

- All three plans complete. Short icon tooltips preserve full hidden labels; visible menus omit generated tooltips. Exact copied-template migrations and paired Breaking guidance delivered.
- Cached Django4.2/5.2/6.0 each9165 passes with documented skip/floor exclusion; examples302+43subtests; JS365; final Node23; browser49cases/97controls; strict docs/Ruff pass.
- Browser exposed pre-existing Bootstrap disposal callback race: minimal identity guard repaired and independently reviewed; private5.3.3 seam limitation explicit. Runner spawn and hermetic-test review findings fixed/rechecked; zero open code findings.
- Canonical verification30/30; validation complete, security9/9closed, UI checker7/7/audit22/24. Screenshot typography is confirmed inherited JetBrains fontconfig/FiraCode fallback, not product styling. Test-only evidence continuity disclosed.
- Three human checks persisted in06.8-UAT.md: six screenshots, live visual/keyboard flows,19 UI considerations. No human approval or screen-reader testing inferred.
- Existing config/state.json and unrelated untracked artifacts preserved. No phase completion, merge, push or publication.

### Phase 06.8 execution checkpoint — 2026-11-03

- All three plans executed; TIP-01–TIP-05 automated obligations complete. Phase remains In Progress pending independent verification and human acceptance.
- Plan 03: 49 Chromium cases / 97 controls, exact stock/custom recipes, six retained screenshots and source/asset hashes pass. Each cached Django series passes 9165 tests; existing CSP skips and sole floor exclusion remain explicit. Examples 302 plus 43 subtests, JavaScript 365, runner tests 20, strict docs and Ruff pass.
- Real modal acceptance exposed stale Bootstrap transition callbacks after disposal. Authorized guarded completion repair preserves animations and synchronous disposal; its private `_queueCallback` seam requires independent review. Original failing evidence and regression RED are retained.
- UI consideration confirmation, human visual/keyboard review and broader supported Python matrix remain unclaimed. No external application, screen-reader, merge or publication acceptance is inferred.
- Existing config/state.json edits and unrelated untracked artifacts are preserved. The SDK intentionally leaves the overall progress bar unchanged for unscoped phase completion.

### Phase 06.7 completion — 2026-11-03

- All five plans and CAN-01–CAN-07 complete; canonical verification passed and UAT 5/5 passed with no unresolved Cancel issues.
- Maintainer approved the intended contract and migration guidance. Chrome 156.0.8078.79 with Orca passed button/link keyboard, omission, repeated invalid modal focus, and responsive label/both/icon/long-label checks at all three specified sizes.
- The restricted user's save succeeded; its existing list success redirect returned 403. Recorded as an example/fixture limitation, not a Cancel failure; success behavior remains unchanged.
- WINDOWS 30 resolved. Low query-visibility acceptance-record obligation remains open below the configured security threshold; no risk acceptance is inferred.
- Temporary user/author removed; normal example settings restored on port 9000 with the tunnel hostname. Existing configuration and untracked artifacts preserved. No push, merge or release.
- Earlier pending-human entries below are historical and superseded by this completion entry. Phase 7 needs discussion; no new phase implementation started.

### Phase 06.7 canonical verification — 2026-11-03

- All five plans complete. Canonical report human_needed: 32/32 must-haves verified, no implementation blocker; independent 72 Python and 2 cleanup tests pass.
- Full available Django 4.2/5.2/6.0 gates each recorded 8962 passes with exact documented skip/floor exclusion. Examples302+43subtests, JS363, browser28 pass; later diagnostic/test-only changes have explicit continuity and targeted evidence.
- Review repairs: isolated temporary registry, guaranteed cleanup after browser-close failure, robust malformed-config checks and real create recipe coverage. All independently rechecked; 0 open code findings.
- Validation compliant7requirements/12tasks; security13/14closed with0blocking, LOW query-visibility acceptance record remains open; UI22/24 with human/visual limits.
- User authorized exact browser asset downloads;12local files verified,4SRI values match. Earlier missing-assets checkpoint is resolved.
- Four human checks persisted in 06.7-UAT.md: UI/state confirmation, keyboard/focus, responsive visual inspection, migration readability. UI-SPEC remains draft; no human approval inferred.
- Next: $gsd-verify-work 06.7. Phase remains incomplete; existing config and draft/review artifacts preserved, no merge/push/release.

### Phase 06.7 plan 05 prerequisite checkpoint — resolved 2026-11-03

- Original stop: plan 05 had no local asset manifest and made no writes. User subsequently authorized exact fixture asset downloads; the orchestrator supplied `/home/alex/.cache/django-crud-views/cancel-assets-06.7/assets.json`.
- Executor independently validated all 12 hashes and four CSS/JS SRI declarations, then completed both tasks with blocked-network real Chromium acceptance. No package or browser installation occurred.
- Final automated evidence: 28 browser cases/30 Cancel clicks; 8962 tests pass on each Django 4.2, 5.2 and 6.0 series; expected version skips and sole authorized floor exclusion are explicit. Full examples: 302 tests plus 43 subtests; JS: 363; docs/Ruff pass.
- UI-SPEC checker 7/7 is clear per orchestrator; user UI consideration confirmation and human keyboard/focus/visual acceptance remain pending (WINDOWS 30). No phase completion, merge or publication is claimed.

### Phase 06.7 execution checkpoint — 2026-11-03

- Plan 01 complete: 189 focused and 918 migration tests pass, Ruff clean, golden files unchanged.
- Post-wave source compilation and JavaScript regression pass (363 tests across 10 files).
- Plan 02 complete: E256 fallback diagnostics and Guardian target policy; 297 core/Guardian and 676 permission/Crispy tests pass, plus 52 new cases on each cached Django 4.2/6.0 runtime.
- Schema gate clear; codebase mapping drift advisory. UI-SPEC now exists and checker passed 7/7 per orchestrator; human UI consideration confirmation remains pending.
- Plan 03 complete: polymorphic cancel-only handoff and guarded template helper; 730 rendering/modal/success/Crispy and 315 integration tests pass, plus 82 new cases on each cached Django 4.2/6.0 runtime. CAN-04 complete; CAN-06/CAN-07 retain later-plan acceptance obligations.
- Plan 04 complete: 34 documentation recipe tests and 71 example/sync tests plus two legacy subtests pass; strict MkDocs and changed-file Ruff pass. CAN-06 complete, exact Phase 7 helper/default/diagnostic surface recorded in summary.
- Plan 05 complete: source-bound browser and supported-runtime acceptance, scoped standalone Cancel compatibility repair and fixture corrections are committed. CAN-07 automated obligations pass; phase verification and human UI consideration/keyboard/visual acceptance remain pending.
- Existing configuration and untracked review artifacts preserved. No phase completion, merge or publication.

### Phase 06.7 plan convergence — 2026-11-03

- Five plans, twelve tasks, four waves; all seven CAN requirements and sixteen discussion decisions covered.
- Fable, Grok and Gemini completed three review cycles. HIGH/actionable counts: 7/12 → 0/1 → 0/0; final review `0264110` has zero open revision conflicts.
- Revisions cover shared list-family query cleanup, explicit custom-key empty restoration, Guardian destination policies, selector/success isolation, fixture ownership and complete documentation/example migration.
- Structural checks pass; all 26 automated commands have failure signals. Implementation, browser prerequisites and human acceptance remain pending.
- Gemini's timeout increased to 1500 seconds per invocation at the user's request; OpenCode session continuation succeeded. Shared/Grok timeout remains 1200 seconds. Raw attempts and source-grounding limitations remain recorded in review evidence.
- Planning/review artifacts committed; no product implementation, merge or publication. Existing configuration edits remain preserved.

### Phase 06.6 completion — 2026-11-03

- All10 plans complete; THEME-01–06 accepted. Canonical verification25/25, human UAT7/7 and security27/27 passed.
- Parent formset success redirect repaired and user-retested; ignored/untracked IDE metadata classified without weakening source/settings/index checks.
- Fresh final matrix8720/8720/8719/8720 passes; JS363/example301/browser/docs/quality gates pass. Existing skip/exclusion and three unchanged companion failures remain explicit.
- Companion3315eef remains locally committed; user settings and IDE metadata preserved. No merge, push or publication.
- Completion scanner warnings concern command strings, logical template names and relative evidence paths; canonical verifier resolved actual artifacts. Browser/version unspecified and AT untested.
- GSD requirement writer did not find root THEME rows; root checkbox/traceability rows reconciled directly against the passing canonical report.
- Earlier pending-human/source-binding notes below are historical. Phase7 needs discussion; no Phase7 execution started.

### Phase 06.6 plan convergence — 2026-11-02

- Ten plans, 24 tasks, five waves; all 19 decisions and six THEME requirements covered.
- Eight external review cycles completed with Fable, Grok and Gemini; final review `f6f59a5` has zero unresolved HIGH, zero actionable non-HIGH findings and zero open revision conflicts.
- Cycle counts (HIGH/actionable): 12/18 → 1/7 → 0/3 → 0/3 → 1/2 → 0/3 → 0/2 → 0/0. Numerical stalls were reported; user increased the cycle cap to eight.
- Final structure checks pass for all ten plans; 33 verification commands state failure signals. Four warnings concern already-settled decisions, not outstanding approvals. The post-planning gap check covers 25/25 items.
- User authorized companion project changes and local delivery. Source `../tabler-test` at `885dfc7` and its running runtime were inspected; existing settings edits must be preserved. Baseline, implementation and acceptance remain execution work.
- OpenCode timeout saved as `review.timeouts.opencode=1200` seconds (previous 660). Source-grounding limitations, failed attempts and corrected review-prompt mislabel are disclosed in REVIEWS/diagnostics.
- No product implementation or broad acceptance suite was run during planning. No merge or publication. Pre-existing unrelated working-tree changes remain preserved.

### Phase 06.5 completion — 2026-11-02

- Resumed existing UAT: 28/28 passed (five human confirmations and 23 carried automated results), no issues or pending checks. No tests rerun during this resume.
- Canonical verification is current and passed; security has 20/20 threats closed. Completion predicate passed with no blockers.
- All nine plans complete; PRES-01–06 accepted. Heading/icon projection, stable identity boundaries, tab lifecycle, semantic badges and removed aliases are handed to Phase 7.
- Prior checkpoints below are historical and superseded by this completion entry. Existing floor exclusion and runtime/browser coverage limits remain unchanged.
- Phase 7 needs discussion/spec decisions; proposed Phase 6.6 remains unaccepted and is not inserted by this transition.

### Phase 06.5 final verification checkpoint — 2026-11-02

- All nine plan summaries complete. Approved Django 6 floor rerun: 8328 passed with four workers and the exact existing wrapper-golden exclusion; original raw failure evidence preserved.
- Review findings fixed and independently rechecked; security 20/20 closed. Final JavaScript regression: 363 passed.
- Canonical verifier: human_needed, 22/23 truths verified. Required CDN asset failure behavior and changed stock visual/focus inspection remain pending in 06.5-UAT.md.
- No blocking implementation gaps. Phase remains incomplete until verification passes. Historical checkpoints below are superseded by this entry.
- Existing shared planning edits preserved unstaged; no merge or publication.

### Phase 06.5 execution checkpoint — final raw gate

- Plans 01–08 complete. Plan 09 docs, public-surface inventory and all verification outcomes committed; SUMMARY status halted, task 03 acceptance pending.
- Full Django 4.2/5.2 each 8328 passed with existing Django-6-only CSP skip. Raw Django 6.0: 8328 passed, one failed pre-existing crispy-floor wrapper golden; no exclusion/waiver applied.
- JS363, positive integration2/six real fragments, presentation browser12/297, lifecycle browser2/20, strict docs/Ruff/format pass. Exact reports in 09 SUMMARY/VALIDATION and evidence.
- Existing nox crispy-floor policy excludes test_form_buttons_golden.py::test_filter_form_baseline; the reviewed plan explicitly requires the unfiltered floor command. Decision required to reconcile; no package install authorized and .venv Django6.1 is outside the required6.0 series.
- User preference for multicore broad pytest runs recorded in CLAUDE.md/AGENTS.md, commit dfd1fb3. Current full runs were retained serial; future broad runs use xdist unless a concrete constraint applies.
- No phase completion, independent final review/verifier, merge or publication. Existing shared planning edits remain unstaged.

### Phase 06.5 UI contract approval — 2026-11-02

- UI-SPEC approved by independent checker: six PASS dimensions and one nonblocking visual hierarchy FLAG, with clarification added.
- User selected option 1 to accept all six classifications and 28 explicit state rules. Contract committed as adaa4fc.
- UI safety gate now returns block:false; scope attribution remains degraded (no-task-commit-rows). This clears the missing-contract gate, not implementation acceptance.
- Plans 01 and 06 remain complete; resume the other seven plans with $gsd-execute-phase 06.5.

### Phase 06.5 execution checkpoint — 2026-11-02

- Plans 01 and 06 committed with summaries and RED evidence.
- Plan 01: 579 registry/button and 139 heading tests passed. Plan 06: 95 resolver/template and 19 documentation-selection tests passed. Ruff clean.
- Schema gate clear; codebase drift advisory. Blocking UI safety gate: missing UI-SPEC.md. Later waves not dispatched.
- Sequential execution follows fork-base mismatch fallback. Phase branch retains prerequisite-bearing HEAD. Existing shared planning edits preserved and unstaged.
- Next: generate UI contract, resume execution. No phase completion, merge or publication.

### Phase06.4 final acceptance — 2026-11-02

- Canonical10/10 passed with248-file fingerprint; UAT2/2, security44/44, validation compliant.
- Independent31-item assessment verifies authored scoped contracts; original flags/history
  and broader unsupported guarantees remain explicitly preserved.

- Current aggregate20gates passed; final handoff structurally_valid:true,ready:true;
  installed verification and shared UAT-plus-verification completion predicates passed.

- Required regression347tests/9files passed; independent verifier3named tests passed.
- Actual final binding/output/timestamps in post-uat-evidence/final-rebind.json.
- Completion CLI emitted13 advisory summary-reference warnings (relative diagnostic paths
  and command strings interpreted as paths). They do not invalidate verified source-bound
  records; original summaries retained to preserve history and fingerprint stability.

- Shared pre-existing tracking/config edits preserved; no merge, release or deployment.

### Phase06.4 independent security reassessment — 2026-11-02

- Auditor /root/security_uat_reconcile verified all 44 authored mitigations at ASVS1/high.
- T35/T36 close from actual attributed UAT and independent re-review; T40/T43 close their
  demonstrated mitigation-presence/actual-sequence obligations, not current readiness.

- Aggregate20gates, structurally-valid/not-ready handoff, and immutable14observations pass
  at the pre-persistence audit snapshot. Canonical report check fails stale fingerprint.

- SECURITY.md now reflects44/44closed and preserves all historical snapshots verbatim.
- Updating SECURITY intentionally invalidates old helper stable-report binding; preserve
  immutable outcomes and account explicitly for report-only successor changes.

- No product changes, installations, suite replay, risk waiver, phase completion or advancement.

### Phase06.4 Orca acceptance — 2026-11-02

- User installed Orca and replied `pass` to the targeted stock/native screen-reader checklist.
- H1 passes as a reported human observation; prior Chrome pass and H2 acceptance retained.
- Browser/Orca versions and Linux distribution remain unspecified; no physical-device coverage inferred.
- UAT completion predicate passes with two passed checks and no blockers.
- Historical pending-human snapshots below are superseded by these actual responses.
- Phase remains pending until independent security and canonical verification gates resolve.

### Phase06.4 actual UAT responses — 2026-11-02

- User reported `pass` for the browser checklist, then `chrome, I do not have a screen reader`.
  Browser checks pass in Chrome; version/OS unspecified; screen-reader coverage untested.

- User replied `accept` to the exact bounded H2 storage contract and stated exclusions.
  H2 passes as human acceptance, not a newly implemented enforcement route or risk waiver.

- UAT persisted/committed as partial: one passed, one blocked, zero issues, zero pending.
  The completion predicate refuses phase closure because H1 remains blocked.

- Updated UAT changes covered input. Canonical fingerprint/rebind and independently attributed
  security obligations must be reconciled when acceptance work resumes; no old report was
  silently promoted. Shared pre-existing tracking edits remain unstaged.

### Phase06.4 WR-05 execution and independent finalization — 2026-11-01

- Plans23–26/nine tasks completed on the existing phase branch, with atomic task and SUMMARY commits.
- Predicate-local overflow repair has actual RED/GREEN through both CLIs. Full checker67passed, Ruff pass,
  35genuine corruption refusals plus clean positive;17original gate objects unchanged.824source paths,
  822unchanged and exactly runner/tests changed. Prior product totals remain historical.

- Plan24's process survived a user interruption; continuation recovered the actual successful process/output
  without restarting capture. Resumed harness PATH was not substituted into its original attribution.

- Distinct code/security reviewers each recorded14real CLI observations. WR-05/G6closed within scope.
  Independent validation remains partial. Security40/44closed;T35/T36/T40/T43fourhighopen,noacceptedrisk.

- Same independent canonical verifier recorded14actual pre-replacement outcomes and immutable snapshots,
  then human_needed9/10. Final post-summary fingerprint covers221files including all26summaries and UAT.
  Actual live aggregate/handoff check after report binding passes structurally_valid:true,ready:false;
  latest post-summary binding is26-evidence/final-rebind.json,priorobservationpreservedseparately.

- H1pending,H2flagged-unverified,all31flags and19decisions retained. Two actual human tests persisted in UAT.
  Existing UI24/24 is retained within original scope; no new visual/AT/person approval is inferred.

- Final required npm regression347tests/9files passed. Schema/UI gates clear; map drift advisory;
  parent06UATalreadycomplete. No phase.complete,Phase7advancement,releaseormerge.

- Pre-existing shared STATE/ROADMAP/state.json/config and unrelated workspace changes preserved;
  shared tracking remains unstaged. Exact final verification and rebind hashes are in their owned artifacts.

### Phase 06.4 WR-05 gap planning — 2026-11-01

- Plans 23–26: nine tasks across waves 17–20, covering predicate-local overflow diagnostics, both actual CLI regressions, bounded evidence refresh, independent reviews and canonical finalization.
- Independent checker passed after correcting the stale-report-digest verification order and splitting review from finalization. Final review: zero blockers/warnings. Research skipped for gap closure.
- Requirements 11/11 and decisions 19/19 covered; all twelve new verification commands state failure signals. Path probe remains not_applicable, not proof of filesystem resolution.
- G6/WR-05, H1/H2, 31 flags and independently open security obligations remain unresolved until actual execution and acceptance. Canonical verification remains gaps_found; Phase 7 does not advance.
- Shared STATE/ROADMAP/state.json contained pre-existing edits and remain unstaged; only four new plans and their coverage appendix are committed.

### Phase 06.4 remaining gap execution and independent re-verification — 2026-11-01

- Plans 20–22 / seven tasks completed in waves 14–16; atomic task and summary commits on the existing phase branch.
- WR-03/04 repaired and independently closed within scope. Fresh checker suite: 62, Ruff check/format, 33 genuine corruption controls and clean positive pass; final packet: 20 gates valid with 17 original gate records unchanged. Source continuity: 824 paths, 822 unchanged, exactly two checker files changed. Prior product totals remain historical.
- Independent code/security reviews and canonical verifier reproduce new WR-05: an oversized glyph integer raises uncaught OverflowError instead of MATRIX_REJECTED. Rejection remains fail-closed; G6 stays open.
- Canonical VERIFICATION gaps_found 8/10 with fresh 202-file fingerprint; prior report preserved. Final canonical-hash rebind and --check-handoff pass structurally_valid:true,ready:false.
- Security: 38/41 closed; T35/T36/T40 remain three high open obligations, no accepted risks. H1 pending, H2 flagged-unverified, 31 assumptions unresolved. Independent coverage audit remains partial/nyquist=false. Existing UI 24/24 retained within original scope.
- Required regression hook npm test passed 347 tests across 9 files. Schema/UI gates nonblocking; general codebase-map drift remains advisory. Parent 06 UAT already complete/no gaps.
- No phase.complete, Phase 7 advancement, release or merge. Next: $gsd-plan-phase 06.4 --gaps for the bounded WR-05 repair; human checks remain separate.
- Existing shared tracking/config and unrelated changes preserved; updated STATE/ROADMAP/state.json remain unstaged.

### Phase 06.4 remaining gap planning — 2026-11-01

- Plans 20–22: seven tasks across waves 14–16, covering WR-03/04 checker enforcement, bounded provenance-preserving evidence refresh, independent reassessment and end-of-phase acceptance handoff.
- Independent checker passed after five historical research questions received dated, evidence-backed resolutions. Research was not repeated; no product implementation changed.
- Requirements 11/11 and decisions 19/19 covered; all ten new verification commands state failure signals. Path probe remains not_applicable, not proof of resolution.
- H1/H2, all31 flagged assumptions, G6 and outstanding security obligations remain open. Planning completion is not phase acceptance; ready=false persists in acceptance evidence.
- Shared STATE/ROADMAP/state.json contained pre-existing edits and remain unstaged; only new plans and the scoped research reconciliation are committed.

### Phase 06.4 gap execution and canonical re-verification — 2026-11-01

- Plans 11–19 / eighteen tasks executed across waves 9–13 on the existing phase branch; sequential dispatch followed GSD's fork-base mismatch fallback.
- Current matrix: 20 gates; 48,220 Python passes across Django 4.2/5.2/6.0 focused and enabled/Node-free suites; JS347, integration2, runner37; browser36 cases/305 assertions; strict docs/Ruff pass. Only prescribed CSP/golden exclusions. All25 recorded corruption controls genuinely rejected.
- Original CR-01–05/WR-01–02 independently closed within scope. New WR-03/04 leave G6 open: aggregate checker accepts absent/contradictory corruption outcome records and missing/stale screenshot provenance.
- Canonical VERIFICATION: gaps_found, 8/10, nonstale. Security31/37 closed; five high and one medium obligations open, no accepted risk. UI 24/24 closes old host findings; H1/H2 and 31 fallback flags remain explicit. VALIDATION remains partial.
- Two necessary integration corrections: strengthened required reclean test-family guard; DELETE fields supplied in two synthetic template fixtures. Invalidated attempts are preserved, final evidence freshly captured.
- No phase.complete, Phase 7 advancement, release or merge. Next: $gsd-plan-phase 06.4 --gaps; unchanged completed plans are not rerun.
- Pre-existing edits to STATE/ROADMAP/state.json/config and unrelated files preserved; shared tracking remains unstaged. Canonical report, scoped requirement descriptions and rebound handoff are committed separately.

### Phase 06.4 gap planning — 2026-11-01

- Plans 11–19: eighteen tasks in waves 9–13; independent checker passed without actionable defects.
- G1–G6/CR-01–05/WR-01–02 and linked security obligations have executable repair and regression tasks.
- Requirement coverage 11/11; decision coverage 19/19; command failure-direction checks pass. Path probe returned not_applicable, not affirmative resolution.
- Research skipped for gap closure. Original plans/evidence retained; final evidence follows changed source and required integration gates.
- H1/H2 remain pending human dispositions; planning does not close implementation gaps or authorize Phase 7.
- Shared STATE/ROADMAP/state.json had pre-existing edits and remain unstaged; only newly authored planning artifacts are committed.

### Phase 06.4 execution and canonical verification — 2026-11-01

- Ten plans / twenty tasks executed and committed on `gsd/phase-06.4-conditional-and-formset-correctness-lifecycle`.
- Recorded matrix: 47,617 Python passes across focused and enabled/Node-free full suites on Django 4.2/5.2/6.0; JavaScript 309; conditional Chromium 20 cases/126 assertions; retained modal 12/133; docs/Ruff pass. Only prescribed prior exclusions.
- Independent deep review and verifier reproduced CR-01–05 and WR-01/02: recleaning policy bypass, clean JS CI runtime coupling, absent DELETE fields, reorder capability identity, ambiguous-binding state loss, incomplete quality-gate validation and stale runtime-override reuse.
- Canonical VERIFICATION is `gaps_found`, 4/10 merged goal truths. SECURITY reopened six obligations (three high blockers); no risks accepted. VALIDATION is partial after counterexamples.
- COND-01/02, FSET-01/02 and LIFE-02 require repairs. LIFE-01 human UI judgment and the descriptor-less prohibition remain explicit; passing subcontracts and scoped A19 evidence are retained.
- No phase.complete, phase advancement, release or merge. Resume with `$gsd-plan-phase 06.4 --gaps`; do not rerun unchanged completed plans.
- Existing ROADMAP/state.json/config and unrelated workspace edits were preserved; updated ROADMAP/state.json remain unstaged because they contained pre-existing changes.

### Phase 06.3 completed — 2026-11-01

- All 20 plans / 45 mapped tasks complete; canonical verification passed **91/91**, no overrides and no outstanding in-scope human checks.
- All twelve original owner responses preserved; four detector fallbacks dismissed by reproducible investigation.
- Guardian identity contract clarified for tested integer/UUID/exact-key/queryset/alias cases. Broader custom-PK/backend/collation compatibility remains unverified follow-up in issue #286.
- Fresh gates: JavaScript 266 passed; Django 4.2 Guardian 298 passed; preceding Django 6.0 bounded review 531 passed; current twelve-case browser evidence and approval bindings validated.
- Source/test/docs/manifest continuity confirmed for 624 tracked files from reviewed implementation 8a26b39; recorded three-series backend evidence remains scoped to its original runs.
- Independent code review clean; CR-01/02/03, CT-01, CR-04/UI-F01 and CR-05 closed. Security 36/36 closed; validation coverage complete within reconciled scope.
- GSD phase.complete advanced tracking to Phase 7: 9/10 phases complete, 56/56 executed plans.
- Completion scanner's nine path-reference warnings were checked: all referenced files exist relative to the phase or the installed Django package; no missing evidence was found.
- Review harness service/tunnel was not changed by this reconciliation. No release, merge or GitHub issue #282 closure is inferred.

The following dated checkpoints and accumulated decisions preserve execution history; current status is above.

### Phase 06.3 focus approval

- Maintainer replied `approve`; exact response and four matching hashes recorded in bdea5a0.
- FOCUS_APPROVAL_BOUND passes. Plan 18 is complete; the checkpoint history below is superseded.

### Phase 06.3 focus approval checkpoint (history)

- Review binding covers FOCUS-DESIGN and plans 18–20 at revision 3f44f5cbeb2d1c62c4c51977d3234d12c14b50e1.
- Task 18-01: FOCUS_REVIEWABLE passes; 28 temporary-copy positive/negative controls and scoped Ruff pass.
- Task 18-02 remains blocking-human. No FOCUS-APPROVAL.md or actual response exists; real approval gate correctly fails.
- Resume from the recorded checkpoint, not task 18-01. Plan 18 SUMMARY is halted, not complete; plans 19/20 remain dependent.
- No product source changed; twelve final human acceptance items and canonical gaps_found remain unchanged.

### Phase 06.3 gap execution approval

- Task 10-01: `06.3-GAP-DESIGN.md` committed in `0a95670`; document verification passed.
- Task 10-02: maintainer replied "approve"; GAP-APPROVAL committed in `464bd8e`, including explicit CT-01 scope.
- Plan 10 SUMMARY complete; GAP_DESIGN_REVIEWABLE and GAP_APPROVAL_BOUND both passed.
- Reviewed design SHA-256: `feee0a1bbb36028e6bf95f9cbc8aabf73709a1db3463e64328db1d14bad7b572`.
- Plans 10–17 combined SHA-256: `4de8457efead5268b3463860fcfc1dc0eea32c883d7fd3fd24eb402be2bdbc59`.
- Plan 11 is executed: selected native root/parent identity controls pass; independent final verification remains.
- Plan 12 is executed: configured Guardian CT-01 positive access, custom/default keys and retained actor/cache controls pass.
- Plan 13 is executed: declaring-owner boundaries, partial notices and actual owner-qualified migration recipes pass.
- Plan 14 is executed: absent native null joins retain exact counts, actual blockers, custom boundaries and unrelated parents.
- Plan 15 is executed: actual Guardian migration/access, all deletion recipes and strict docs pass; Breaking guidance is paired.
- Plan 16 is executed: all 2,011 focused cases per series and full 4.2/5.2/6.0 suites pass on identical source; JS234, strict docs and scoped Ruff pass. Exact existing CSP/golden exclusions remain recorded in MATRIX.
- Plan 17 is executed: twelve-row actual-response ledger, 28 real browser screenshots, candidate repair/security/6.2 reconciliation and validation handoff. All twelve final responses remain absent; UI-F01 focus loss after 422 is newly observed on unchanged JS.
- Do not repeat plans 10–17 or unchanged source/quality gates. Independent final review is complete.
- Independent code review closes CR-01/02/03 and CT-01; security confirms all31declared mitigations. Canonical VERIFICATION is gaps_found,75/81; CR-04/UI-F01 focus loss and all twelve human items remain open. AUTH-06/GUA-01 are not globally complete; no phase.complete or next-phase advancement.

### Phase 06.3 gap planning

- Eight new plans (10–17), sixteen tasks, waves 9–15; original plans 01–09 remain executed.
- CR-01/02/03 and CT-01 have concrete repair and regression tasks; eleven requirements and sixteen decisions are covered.
- Independent checker passed revision 1 with no remaining issues. The initial scope warning was resolved by separating plan 16 automated evidence from plan 17 review and reconciliation.
- Research skipped for gap closure; existing context, research, patterns, UI contract and validation retained.
- Plan 10 prepares a reviewable design delta and records actual maintainer approval before product changes. Prior approval does not cover the new material contract changes.
- All twelve unresolved human items remain visible; planning verification does not close implementation defects or grant phase acceptance.
- Verify-command failure-direction probe passes; its path probe does not support these Python command forms and returned not_applicable, not affirmative path validation.

### Phase06.3 execution and final verification

- Maintainer approved DESIGN/all9plans; approval binds revision f1fbc3e and current DESIGN digest.
- All9SUMMARY artifacts and atomic task commits recorded on introduce-gsd; unrelated workspace edits preserved.
- Full tests:4.2 7260passed/1CSPskip/1prescribed golden deselected;5.2 7261passed/1CSPskip;
  6.0 7261passed/1prescribed golden deselected. Focused1767 each; JS234, strictdocs and scoped Ruff passed.

- Final review and independent verifier reproduce CR01 cross-alias unrelated child deletion,
  CR02 collapsed custom boundary completeness, CR03 null alternate-key false blockers on all3series.

- Retained CT01 configured polymorphic Guardian helper/list access failure remains unresolved;
  human/spec/prohibition/visual items remain explicit. SECURITY reopened3obligations; no risk accepted.

- Canonical VERIFICATION status gaps_found,41/51. No phase.complete or next-phase advancement.
- Named6.2 AUTH06 checkbox remains retained per explicit acceptance split;6.3 residual GUA01 stays open.

### Phase 06.3 plan convergence

- User increased this run's maximum from 3 to 5 cycles; convergence reached in cycle 3.
- Cycle 1: 6 HIGH, 16 actionable MEDIUM/LOW findings (Fable, Grok, Gemini succeeded).
- Cycle 2: 0 HIGH, 3 actionable LOW findings (Gemini succeeded; Fable quota failure; Grok unusable/timeout).
- Cycle 3: 0 HIGH, 0 actionable findings (Grok and Gemini succeeded; Fable skipped unavailable).
- Final reviewed plan revision: `1366dac`; final review: `2fddc5e`.
- Nine plan structures and all 16 context decisions verified; no open plan-revision conflicts.
- Python source-grounding index limitations are explicit in `06.3-REVIEWS.md`; direct-source evidence supplements them.
- This planning-stage checkpoint was subsequently approved by the maintainer; see execution results above.

## Performance Metrics

**Velocity:**

- Total plans completed: 148
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
| 06.2 | 9 | - | - |
| 06.3 | 20 | - | - |
| 06.4 | 26 | - | - |
| 06.5 | 9 | - | - |
| 06.6 | 10 | - | - |
| 06.7 | 5 | - | - |
| 06.9 | 4 | - | - |
| 06.8 | 3 | - | - |
| 06.10 | 5 | - | - |
| 06.13 | 2 | - | - |
| 06.13.1 | 5 | - | - |
| 06.14 | 2 | - | - |
| 06.16 | 3 | - | - |
| 06.17 | 3 | - | - |
| 06.18 | 13 | - | - |
| 06.19 | 2 | - | - |

| 06.15 | 4 | - | - |

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
| Phase 06.2 P04 | 14 min | 2 tasks | 6 files |
| Phase 06.2 P05 | 16min | 2 tasks | 2 files |
| Phase 06.2 P06 | 31 min | 3 tasks | 10 files |
| Phase 06.2 P07 | 5min | 2 tasks | 3 files |
| Phase 06.2 P08 | 15min | 3 tasks | 9 files |
| Phase 06.2 P09 | 26min | 3 tasks | 8 files |
| Phase 06.3 P02 | 18min | 2 tasks | 6 files |
| Phase 06.3 P03 | 10min | 2 tasks | 5 files |
| Phase 06.3 P04 | 12min | 2 tasks | 2 files |
| Phase 06.3 P10 | 3min | 2 tasks | 2 files |
| Phase 06.3 P11 | 6min | 2 tasks | 2 files |
| Phase 06.3 P12 | 9min | 2 tasks | 14 files |
| Phase 06.3 P13 | 7min | 2 tasks | 19 files |
| Phase 06.3 P14 | 5min | 2 tasks | 8 files |
| Phase 06.3 P15 | 5min | 2 tasks | 10 files |
| Phase 06.3 P16 | 24min | 2 tasks | 66 files |
| Phase 06.3 P17 | 6min measured artifact window; initial reads excluded | 2 tasks | 13 files |
| Phase 06.4 P01 | 6min | 2 tasks | 9 files |
| Phase 06.4 P02 | 8min | 2 tasks | 4 files |
| Phase 06.4 P05 | 5min | 2 tasks | 2 files |
| Phase 06.4 P03 | 5min | 2 tasks | 5 files |
| Phase 06.4 P04 | 12min | 2 tasks | 6 files |
| Phase 06.4 P06 | 9min | 2 tasks | 7 files |
| Phase 06.4 P07 | 9min | 2 tasks | 4 files |
| Phase 06.4 P08 | 16min | 2 tasks | 10 files |
| Phase 06.4 P09 | 9min | 2 tasks | 8 files |
| Phase 06.4 P10 | 60min | 2 tasks | 7 files |
| Phase 06.6 P01 | 8min | 3 tasks | 11 files |
| Phase 06.6 P04 | 2min | 2 tasks | 6 files |
| Phase 06.6 P06 | 32min | 2 tasks | 5 files |
| Phase 06.6 P02 | 3min | 2 tasks | 6 files |
| Phase 06.6 P03 | 7min | 3 tasks | 9 files |
| Phase 06.6 P05 | 5min | 2 tasks | 5 files |
| Phase 06.6 P07 | 31min | 3 tasks | 9 files |
| Phase 06.6 P08 | 5min | 2 tasks | 7 files |
| Phase 06.6 P10 | 18min | 3 tasks | 13 files |
| Phase 06.6 P09 | 48min | 2 tasks | 78 files |
| Phase 06.7 P01 | 12min | 3 tasks | 19 files |
| Phase 06.7 P02 | 14min | 2 tasks | 7 files |
| Phase 06.7 P03 | 9min | 2 tasks | 9 files |
| Phase 06.7 P04 | 5min | 3 tasks | 16 files |
| Phase 06.7 P05 | 30min | 2 tasks | 17 files |
| Phase 06.8 P01 | 5min | 3 tasks | 17 files |
| Phase 06.8 P02 | 6min | 2 tasks | 8 files |
| Phase 06.8 P03 | 22min | 2 tasks | 20 files |
| Phase 06.9 P01 | 10min | 2 tasks | 7 files |
| Phase 06.9 P02 | 10min | 2 tasks | 5 files |
| Phase 06.9 P03 | 10min | 2 tasks | 6 files |
| Phase 06.9 P03 | 7min | 2 tasks | 6 files |
| Phase 06.9 P04 | 17min | 2 tasks | 10 files |
| Phase 06.10 P01 | 6min | 2 tasks | 7 files |
| Phase 06.10 P02 | 8min | 3 tasks | 14 files |
| Phase 06.10 P03 | 6min | 3 tasks | 9 files |
| Phase 06.10 P04 | 6min | 3 tasks | 15 files |
| Phase 06.10 P05 | 12min | 2 tasks | 12 files |
| Phase 06.13.1 P01 | 9min | 3 tasks | 7 files |
| Phase 06.13.1 P02 | 10min | 2 tasks | 3 files |
| Phase 06.13.1 P03 | 19min | 3 tasks | 7 files |
| Phase 06.13.1 P04 | 22min | 2 tasks | 6 files |
| Phase 06.13.1 P05 | 20min | 2 tasks | 10 files |
| Phase 06.14 P01 | 8min | 2 tasks | 4 files |
| Phase 06.16 P01 | 9min | 3 tasks | 8 files |
| Phase 06.16 P02 | 8min | 3 tasks | 12 files |
| Phase 06.16 P03 | 11min | 3 tasks | 10 files |
| Phase 06.17 P01 | 6min | 2 tasks | 10 files |
| Phase 06.17 P02 | 8min | 2 tasks | 12 files |
| Phase 06.17 P03 | 10min | 3 tasks | 12 files |
| Phase 06.18 P01 | 30 min | 2 tasks | 8 files |
| Phase 06.18 P02 | 37min | 3 tasks | 12 files |
| Phase 06.18 P03 | 19min | 3 tasks | 12 files |
| Phase 06.18 P04 | 33 min | 2 tasks | 7 files |
| Phase 06.18 P05 | 25min | 2 tasks | 7 files |
| Phase 06.18 P06 | 25min | 3 tasks | 10 files |
| Phase 06.18 P07 | 33 min | 3 tasks | 10 files |
| Phase 06.18 P08 | 25 min | 2 tasks | 10 files |
| Phase 06.18 P09 | 14min | 2 tasks | 5 files |
| Phase 06.18 P10 | 20min | 2 tasks | 3 files |
| Phase 06.18 P11 | 20 min | 2 tasks | 9 files |
| Phase 06.18 P12 | 28 min | 2 tasks | 10 files |
| Phase 06.18 P13 | 10min | 2 tasks | 5 files |
| Phase 06.19 P01 | 6 min | 3 tasks | 5 files |
| Phase 06.19 P02 | 6min | 3 tasks | 4 files |

| Phase 06.15 P01 | 8min | 3 tasks | 5 files |
| Phase 06.15 P02 | 5min | 2 tasks | 2 files |
| Phase 06.15 P03 | 12min | 2 tasks | 4 files |
| Phase 06.15 P04 | 9min | 2 tasks | 4 files |

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
- [Phase 06.2]: 06.2-04: GuardianViewSet.cv_guardian_accept_global_perms removed; a mode=before Mapping-guarded validator rejects the key (ValidationError naming the per-view replacement) before registration; unrelated extras still ignored
- [Phase 06.2]: 06.2-04: Manage reports guardian_config.get_objects_for_user from STRICT_HELPER_POLICY (the same values the helper passes to guardian) and views[key].guardian_policy per view; applicable = object/queryset views, or parent-only views with a parent and a non-None resolved parent permission
- [Phase 06.2]: 06.2-05: the A10 actor matrix and six native template overrides are replayed as test-only evidence (582 tests) with no production change; strict and global-accepting Guardian families are the same views with the per-view flag set per test
- [Phase 06.2]: 06.2-05: manage stays its own administrative gate in the matrix (D-06); its mode/group/DEBUG cells are replayed under the patched singleton rather than under object-view inactive policy
- [Phase 06.2]: 06.2-06: Breaking (paired with migrating-1.0.md): HTTP DELETE 405, removed GuardianViewSet key, filtered protected_objects + has_protected_objects, Guardian manage context, nested Guardian create helper contract
- [Phase 06.2]: 06.2-06: Fixed (not Breaking): fragment authorization/400 coordinates, unsaved UUID None prefixes, formset.js multi-digit keys, parent-None gates, inactive Guardian denial
- [Phase 06.2]: 06.2-06: Supported-version evidence limited to cached Django 6.0/4.2 crispy-floor envs; Django 5.2 and Python 3.13-3.15 nox sessions not run (no installs, T-06.2-SC)
- [Phase 06.2]: 06.2-07: Guardian preview uses its own content type and bare view codename; through rows bypass ContentType access and retain active authenticated superuser visibility with whole-model PK caching.
- [Phase 06.2]: 06.2-08: Blocked deletion state is unconditional; one existing full NestedObjects/write-router collection per context supplies only the boolean when previews are off.
- [Phase 06.2]: 06.2-08: Translate only pre-call native graph plus exact target Model.delete/Collector.collect provenance; custom handlers, SET/defaults, loaders, hooks, signals and committed callback failures propagate.
- [Phase 06.2]: 06.2-08: Hidden-label notices use colon-free heading plus generic sentence; labelled heading remains unchanged. German MO now compiled with polib 1.2.0.
- [Phase 06.3]: 06.3-02: metadata-only previews replace NestedObjects; exact Model.delete uses native collector provenance, actual Author/Car methods retain using and stale-error propagation; 359 affected tests pass on both cached supported series
- [Phase 06.3]: 03: E263 rejects legacy collection overrides; E264 diagnoses inspectable incompatible delete(using=...) methods; opaque methods fail without invocation at runtime.
- [Phase 06.3]: 03: Proxy and concrete instances share stored-row identity; genuine multi-table parent models remain distinct; scoped providers validate immutable boundaries and saved same-alias records.
- [Phase 06.3]: Maintainer approved GAP-DESIGN and plans 10–17 including immediate owner-qualified provider migration; actual response and reviewed digests recorded in GAP-APPROVAL.
- [Phase 06.3]: Bounded CT-01 configured-content-type default/custom permission scope explicitly approved; implementation and all twelve human dispositions remain outstanding.
- [Phase 06.3]: 11: Native collection reloads selected values but preserves original authorized origin/state; actual parent-link queries ignore cached descriptors.
- [Phase 06.3]: 12: Guardian default/custom permissions use only the configured content type; exact explicit mappings and retained actor/global/cache policy remain unchanged.
- [Phase 06.3]: 13: Boundary field_model retains declaring owner separately from source rows; exact supplied six-field descriptors reject ownerless field contributions immediately.
- [Phase 06.3]: 13: Actual owner-qualified provider migration and its Breaking entry share commit 7b4ee94; synthetic test metadata owners corrected without an ownerless product fallback.
- [Phase 06.3]: Apply absent-null-join semantics to native reverse/parent inspection and selected parent collection; preserve unknown owner boundaries and propagate read errors.
- [Phase 06.3]: Keep owner-qualified unknown handlers incomplete even for null joins; ordinary confirmation remains available and real custom effects execute only for actual matches.
- [Phase 06.3]: 15: Publish configured Guardian type migration with real grants and registered-list fence execution; preserve explicit maps, startup caches and all twelve pending human items.
- [Phase 06.3]: 16: All three cached runtimes use explicit checkout imports; current-byte source/import/node/JUnit evidence proves focused/full assertions without reinstalling wheels.
- [Phase 06.3]: 16: Reuse completed source/quality runs while source is unchanged; preserve exact checker capture revisions and independently revalidate after evidence-only fixes.
- [Phase 06.3]: 16: All twelve human items and overall phase acceptance remain pending for plan 17 and independent review.
- [Phase 06.3]: 17: Four concrete repair candidates await independent review; canonical verification and the current security gate remain open.
- [Phase 06.3]: 17: All twelve final human dispositions remain pending; actual design approval authorizes the bound repair delta only.
- [Phase 06.3]: 17: Real cached Chromium captures reveal UI-F01 focus loss after 422 on unchanged modal JS; keep it open without unreviewed product scope.
- [Phase 06.4]: 01: Exact bound checkbox names use actual owning-form equality; cv.initConditional is repeat-safe and the Node/jsdom persistence tracer is opt-in only.
- [Phase 06.4]: 01: FSET-02 remains globally pending until later automatic formset lifecycle work is verified.
- [Phase 06.4]: Keep conditional resolver/save signal private; preserve native False-clear/None-no-change file semantics.
- [Phase 06.4]: ImageField evidence is reference-only; disabled-image initial=None uses native no-change without altering production validation or installing Pillow.
- [Phase 06.4]: COND-04 persistence demonstrated across Django 4.2/5.2/6.0; COND-05 remains pending plan 03 static diagnostics.
- [Phase 06.4]: 05: Observe external disabled writes with pending-record drains; compose independent baseline and all bound ancestors without capturing temporary state.
- [Phase 06.4]: 05: Native reset sync uses a macrotask with late-cancellation check; stranded focus remains within owning form; unload releases observation for retained-content reuse.
- [Phase 06.4]: Retire W320 in favor of E312 using the shared resolver on main and inline form classes; server-disabled fields are exempt.
- [Phase 06.4]: Validate clearing configuration in clean before inherited clean, even for active submissions, so request-added unsupported fields cannot reach save.
- [Phase 06.4]: 04: Enforce edit-only and submitted-ID policy after custom clean in the shared XFormSet runtime gate; require authorized queryset membership and exact persisted-instance agreement.
- [Phase 06.4]: 04: Recheck bound main-form errors after child clean; preserve selected-database membership, conditional persistence and inactive managed-queryset skip/purge.
- [Phase 06.4]: 06: cv.initFormsets owns one private controller per actual form; exact DOM prefix/name equality and guarded native actions preserve independent same-prefix forms.
- [Phase 06.4]: 06: Owning-form reorder precedes document modal FormData; cancelled submits and genuine child reorder failures invoke zero fetches, retaining existing modal focus/session authority.
- [Phase 06.4]: 07: Derive selected child fragment indices from ordered declarations; retain authorized coordinates and exact request/response keys.
- [Phase 06.4]: 07: Match raw wrapper predicates with render_rows_only; JavaScript supplies an isolated real-fragment/FormData/POST driver while ordinary Python remains Node-free.
- [Phase 06.4]: 08: Real HTTP/Chromium acceptance passes 20 stock/native cases and 126 assertions; ImageField remains reference-only while real multipart FileField upload discard is verified.
- [Phase 06.4]: 08: New fragment descendants retain the authorized editor path for nested modal actions; focused 89-test fragment suite passes cached Django 4.2/5.2/6.0.
- [Phase 06.4]: 09: Executable bound-wrapper/file-image reference/JSON projection recipes pass all three cached Django series; retain image-byte decoding and final Phase 7 stability limits.
- [Phase 06.4]: 09: Publish root initialization and template-data projection without promoting render-tree/controller constructors or save methods.
- [Phase 06.4]: 09: Requirement readiness is 0/7 pending later-plan acceptance; leave global shared requirements unchanged.
- [Phase 06.4]: 10: Reuse exact-source passing gates; distinguish enabled tracer, Node-free full suites and expected missing-runtime controls in each cached Django series.
- [Phase 06.4]: 10: A19 successful sibling/deeper round trips reconcile only that handoff; canonical prohibition and independent review remain pending, with A8/A25/Guardian and jQuery exclusions retained.
- [Phase 06.6]: 01: Forward FormHelper hooks and override only a fresh get_attributes mapping for render-local CSRF suppression; copy aliases/raising hooks/read-only properties retain compatibility.
- [Phase 06.6]: 04: Alert dismissal utilities preserve default bytes; empty/None dismissal adds no separator, close retains class="", nonempty whitespace is preserved; registry count now 86 before plan03.
- [Phase 06.6]: 06: Keep pinned885dfc7 baseline while preserving user settings-only descendant0b3baa8; ancestry and complete non-settings byte continuity replace live-HEAD equality.
- [Phase 06.6]: 02: Publish validated copied label-mode theme maps by locked rebind; resolve invalid settings via a settings-free theme/package snapshot while retaining owner-first strict errors.
- [Phase 06.6]: 03: Limit the action-group bridge to bootstrap5 plus installed-distribution origin and exact audited2023.10 source; resolve classes per render on a copy and retain custom pack/provider ownership.
- [Phase 06.6]: Plan05 proves workflow full-page ownership separately from inherited custom-form modal bodies; create/update modal support stays false and E251 remains.
- [Phase 06.6]: Plan 07 preserves the live companion settings commit and source/index; exact five-file Tabler patch passed fresh eight-family replay with 205 required purposes unchanged and three source-identical baseline failures retained.
- [Phase 06.6]: Plan08 publishes executable theme defaults, page/helper/copy/standalone migrations with paired Breaking links; strict docs passed, no live companion delivery claim.
- [Phase 06.6]: Plan10 delivered the exact five-file Tabler adaptation in companion3315eef over preserved user commit0b3baa8; core evidence67aca38 binds fresh provisional/committed probes and snapshot-independent preservation. Phase-wide acceptance remains plan09.
- [Phase 06.6]: Plan 09 automated gates pass against final source; retain unchanged companion failures and current-pack Django 6.0 absence; human visual/AT acceptance remains pending.
- [Phase 06.7]: 01: Bound signed cancellation to current ViewSet/parent coordinates; clean all list-family controls before persistence, and validate navigation before golden normalization.
- [Phase 06.7]: 02: Guardian cancel destinations apply target parent/object/queryset policy before one rendering-state evaluation; parent-only routes require no child/model grant.
- [Phase 06.7]: 02: E256 diagnoses missing usable form fallbacks; share Cancel context only within Crispy button construction, preserving kwargs hooks and fresh subsequent evaluation.
- [Phase 06.7]: Polymorphic selection forwards only revalidated cancel state, preserving independent successful-save redirects.
- [Phase 06.7]: Publish URL-or-None cancellation and mandatory omission guards while retaining the key helper and independent success semantics.
- [Phase 06.7]: Follow actual emitted example links and validate signed captures before asserting returned state; retain direct legacy and exact success tests.
- [Phase 06.7]: Plan05 verifies Cancel using exact local SRI assets and source-bound Chromium; supported runtime gates pass after scoped compatibility/fixture repairs, while phase and human UI verification remain pending.
- [Phase 06.7]: Preserve standalone custom Cancel kwargs when cv_view is None; bound views still resolve destination access/state before kwargs and cannot override denial.
- [Phase 06.7]: Retain unchanged-product browser/full5.2 evidence across the two-file filter fixture correction, explicitly recording continuity and focused5.2 plus full4.2/6.0 replay.
- [Phase 06.8]: 01: Short icon titles retain exact full hidden captions, including empty-full behavior; visible overflow items omit generated titles independently of inline mode.
- [Phase 06.8]: 02: Keep complete copied leaves only in buttons.md; migration links to exact tested fences and both existing checklists link to action-tooltips.
- [Phase 06.8]: 02: Raw ContextButton templates delegate through cv_button; flat copied leaves render their own identified roots.
- [Phase 06.8]: Plan 03 verifies 49 Chromium cases / 97 controls using exact recipes and retained screenshots; guard stale Bootstrap callbacks by instance identity while preserving animation and synchronous disposal, with private-hook compatibility disclosed.
- [Phase 06.8]: Use exact documentation bodies with request-local uncached loaders and verify stock/custom/stock plus actual AJAX replacement identities.
- [Phase 06.8]: Retain cached Python 3.12 runtime limits, sole existing floor exclusion and pending human acceptance; do not infer full CI or phase approval.
- [Phase 06.9]: 01: Preserve shared first-match URL hook/cascade behavior; protected candidates use native row identity and one destination-bound access/state evaluation.
- [Phase 06.9]: 02: Protected Guardian links certify actor/child/parent/permission-route topology only after native identity, composition and original-actor guards; shared request policy remains unchanged.
- [Phase 06.9]: 03: Publish exact uniquely adjacent UTF-8/LF recipe fences and hashes; keep protected visibility, destination eligibility and actual-request authority distinct.
- [Phase 06.9]: 04: Exact copied recipes and real page/modal anchors pass seventeen Chromium cases; focused Enter and document requests are required, with cached runtime limits and independent audits retained.
- [Phase 06.10]: Plan 01 removes only protected destination certification; preserves shared cascade, Guardian, Cancel and inspection paths. Plain ordered obj/url=None entries are measured separately from complete inspection/filter costs.
- [Phase 06.10]: Plan 02 resolves inherited view-first finite/None display policy with a private sentinel and independent raw project diagnostics; protected-first local selection precedes per-occurrence cascade URLs while full inspection and visibility remain complete.
- [Phase 06.10]: Plan 03 preserves exact copied-recipe markers and null-URL bodies, migrates independent guards/notices, and documents selected-only presentation costs separately from full inspection/filtering.
- [Phase 06.10]: Plan 04 retains example defaults/models/grants/seeds, uses test-local finite/None overrides, and teaches plain protected labels separately from ordinary Book navigation; German notice uses existing polib regeneration.
- [Phase 06.10]: Final browser acceptance binds current source and exact recipes; human and independent phase/security/Nyquist reviews remain pending.
- [Phase 06.13.1]: Plan 01 confines refusal recovery and alias pinning to WorkflowView; independent business/comment checks share one lazy-exported explicit-actor execution engine.
- [Phase 06.13.1]: Plan 02 binds scalar history identity/readback to the selected database; real default/shard failure-stage tests prove existing atomicity without a product rewrite.
- [Phase 06.13.1]: Keep radio default; button presentation owns the submit slot through the existing form-action seam.
- [Phase 06.13.1]: Namespace IDs before subclass binding and reference crispy error paragraphs instead of version-dependent wrappers.
- [Phase 06.13.1]: Preserve the existing late-refusal engine and form instance; custom integration required regression tests rather than another recovery abstraction.
- [Phase 06.13.1]: Keep stock workflow wrapping on field columns; preserve radio rendering and custom layout ownership.
- [Phase 06.13.1]: Browser acceptance uses cached local assets and runtimes only; missing prerequisites fail without passing skips.
- [Phase 06.13.1]: Document workflow database alignment as a compatibility restriction while preserving DeleteView behavior.
- [Phase 06.13.1]: Restore static stock WorkflowForm icon diagnostics without importing the optional extension or calling custom providers.
- [Phase 06.14]: Plan 01 adds only empty card_root/card_header blocks; frozen request-aware bytes, nonempty CSRF and exact documented inheritance fence verify compatibility.

- [Phase 06.15]: Plan 01: exact model selection and E247 key checks share the existing parser/check traversal; POLY-03 remains pending its plan 03 structural-limit documentation.
- [Phase 06.15]: Plan 02: capfirst formats already-discovered selector names; real requests plus lazy translation, escaping, filtering, custom-form and access regressions preserve the existing contract.
- [Phase 06.15]: Plan 03: publish executable exact-model mapping blocks and list-only tag boundary; full 5.2 and focused 4.2/6.0 pass; POLY-05 remains pending downstream adoption.
- [Phase 06.15]: Downstream catalog verified against explicit phase and pinned extension source roots; task branch retains original report edits unstaged; phase completion awaits independent verification.
- [Phase 06.16]: Choice labels remain separate from raw values; missing supported scalar owners project empty text without normalizing None or lists.
- [Phase 06.16]: Help policy resolves once from strict property instructions, nullable view override and project setting; terminal lazy metadata stays unevaluated until rendering.
- [Phase 06.16]: Stock textual leaves use exact None/empty-string display checks; raw values, custom ownership, non-text behavior and row structure remain intact.
- [Phase 06.16]: Plan 03: exact copied recipes and five real context compositions pass with final full 5.2 and focused 4.2/6.0 evidence; keep independent phase approval pending.
- [Phase 06.17]: Accordion initial state consumes presentation.selected; existing Collapse owns switching and close-all.
- [Phase 06.17]: Tab adapter absence is a no-op; present entries require callable init/dispose, resolved on every owned lifecycle dispatch.
- [Phase 06.17]: Document selected-theme wiring before initialization, including ready documents; late providers require the existing initializer.
- [Phase 06.18]: 06.18-01: interim family table covers only core list/detail (Read) and create/update/delete (Write); other nested endpoints without an exact actions entry do no ancestor work until 06.18-02 Task 2
- [Phase 06.18]: 06.18-01: provider='guardian' is valid only on ViewSet classes whose _ancestor_provider is 'guardian'; GuardianViewSet inherits 'model' until 06.18-03.1
- [Phase 06.18]: 06.18-01: CRUD_VIEWS_ANCESTOR_* defaults are validate_default settings fields; invalid values raise ValidationError when the singleton is built
- [Phase 06.18]: 06.18-02: check IDs viewset.E266 (ancestry structure), E267 (unregistered actions key), E268 (nested custom endpoint without its entry); Resource parents keep the single viewset.E261
- [Phase 06.18]: 06.18-02: urlpatterns validates only a finite, resolved, Resource-free chain; relationships are E266 plus the request guard
- [Phase 06.18]: 06.18-02: completion-dependent checks run after a bounded root/included URLconf import and are deferred without ROOT_URLCONF or on failed/reentrant import
- [Phase 06.18]: 06.18-03: GuardianViewSet ancestors default to a strict object gate (direct/group grants, guardian.ctypes content types); model fallback only from the ancestor's own ancestor_policy.accept_global_perms, never from a child view's cv_guardian_accept_global_perms
- [Phase 06.18]: 06.18-03: Guardian dispatch bridge order is composition error, configured anonymous response, inactive 403, shared ancestor guard, then the no-object state gate on the guard's resolved parent; no second parent lookup
- [Phase 06.18]: 06.18-03: Rendering/access helpers use _immediate_parent_access (immediate parent provider + target nearest key, provider none skips only that gate, no farther ancestor or lookup)
- [Phase 06.18]: 06.18-03: cv_guardian_parent_permission / cv_guardian_parent_create_permission removed; constructor and subclass declarations raise ValidationError before registration
- [Phase 06.18]: 06.18-04: CrudViewPermissionRequiredMixin.dispatch and ManageView.dispatch run the idempotent ancestor guard before PermissionRequiredMixin's state-/group-loading has_permission(); every shipped composition reaches the guard at its first dispatch
- [Phase 06.18]: 06.18-04: actor admission via private _cv_ancestor_actor_response(protected=...) adapters — protected ancestry denies anonymous (endpoint response) and inactive (403); all-none keeps only the endpoint's own early rule (core: model permission for anonymous/inactive only, plain: public, Guardian: configured rules, manage: actual yes/debug_only, anonymous denied)
- [Phase 06.18]: 06.18-04: H1-fragment closed with Publisher change grants; test_resource_views.py::test_nested_detail_scoped_to_parent_404 newly exposed (403 before the Resource loader) and handed to 05.2 with the three H1-resource rows (WINDOWS entry 39)
- [Phase 06.18]: 06.18-06: nested ORM requests refuse a nondefault database where it is reached (ancestor/child querysets, consumed collections, delete alias, write alias/instance route/FK-M2M attachment) via crud_views.lib.ancestor_db; inspect-and-refuse only, never reroute; top-level unchanged
- [Phase 06.18]: 06.18-06: write boundary runs in each POST before the first hook and again at the write wrapper (form mixin, delete, action incl. ordered, workflow), atomic on/off; nested CrudView.cv_get_db_alias passes the resolved object as instance hint (top-level model-only)
- [Phase 06.18]: 06.18-07: nested permission checks validate their own auth records where reached (actor db, object db, Django auth tables + through tables, Guardian generic/direct grant tables via managers and actor/object-hinted routes) with ancestor_db._check_nested_auth, before vocabulary or superuser/fallback shortcuts; no rerouting
- [Phase 06.18]: 06.18-07: the ancestor-gate auth check sits at the gate call site in ancestors.py before the permission map, so a warm vocabulary cannot bypass it; ViewSet.permissions stays side-effect-free and unselected nearest-only levels are never touched
- [Phase 06.18]: 06.18-07: filtered nested lists scope the keyword object_list too (directed Rule 1 fix of the 06.18-06 finding)
- [Phase 06.18]: 06.18-08: child-specific old None scenarios get their own provider='none' Publisher parent ViewSet; the strict parent shared with protected siblings is never set to none
- [Phase 06.18]: 06.18-08: where child page access must stay independent of the create-parent permission, the child ViewSet declares an explicit update/delete=view/view override; the default Write pair and its view-only denial are pinned in test_ancestor_migration.py
- [Phase 06.18]: 06.18-08: every former child-flag parent relaxation uses the parent's ancestor_policy.accept_global_perms, parametrized against the child flag
- [Phase 06.18]: 06.18-08: GuardianParentPermissionMixin.dispatch gates no-object child state with the guard-resolved parent instead of the overridable cv_get_parent_object() hook
- [Phase 06.18]: Core ManageView owns declared ancestor-policy diagnostics (as_ancestor / requests with declared vs effective); Guardian alert rows read the same entry
- [Phase 06.18]: Built-in child redirect needed no production change; Task 2 pins it with tests plus two mutation checks
- [Phase 06.18]: 06.18-10: plan 10 adds pins only, with no production change. The URL-path mutation boundary, fresh-request revocation and the cost matrix were already implemented by plans 01-09; nine reverted mutations show the pins are meaningful.
- [Phase 06.18]: 06.18-10: the cost tests assert attribution and prohibited repeated work (each ancestor resolved once, nearest-only gate event list, plain rest equals the pre-edit baseline, warm guards still query permissions), never a query budget. The baseline totals are embedded with SHA d5567ba2.
- [Phase 06.18]: 06.18-10: one Guardian object-permission pair per ancestor gate is permitted, distinct work. Prefetching all ancestors' permissions would conflict with gating each level before the next lookup (D-32).
- [Phase 06.18]: Published fences use natural registry names; the docs fixture empties and restores the ViewSet registry
- [Phase 06.18]: Nested DB docs link the migration guide page without an anchor until plan 12 creates the ancestor migration section
- [Phase 06.18]: 06.18-12: the ancestor Breaking entry is paired with docs/migrating-1.0.md#ancestor-authorization-for-nested-viewsets (h4 subsection nested-write-database-selection for the instance-hinted selector) and an executed Guardian approve-pair migration fence
- [Phase 06.18]: 06.18-12: cross-series failures in two prior-plan test modules (crispy < 2.7 filter helper, Django 4.2 AdminEmailHandler report) were fixed in fixtures, not the package, and the whole replay rerun at 5829cae7
- [Phase 06.18]: Guardian request gates raise ImproperlyConfigured on a missing own cv_permission key (named ViewSet/view/key + migrate/restart hint); GuardianObjectPermissionMixin.cv_has_access denies every actor, mirroring core #318 (G-06.18-2)
- [Phase 06.19]: Table honours Meta.sequence and appends actions last unless the sequence names it; no Meta.sequence keeps ('...', 'actions') (#337)
- [Phase 06.19]: cv_list_actions = None is the only view-side opt-out for the actions column; [] and () keep the empty column, decision is static (#337)
- [Phase 06.19]: Table exclude merge combines Meta.exclude, caller exclude and actions with an order-preserving dict.fromkeys dedupe (#337)
- [Phase 06.19]: Table.cv_default_sequence inserts "..." before actions when a declared Meta.sequence has none, so django-tables2 never appends its ellipsis after actions (06.19-02, WR-01)
- [Phase 06.19]: Table.__init__ normalises the caller exclude kwarg (falsy -> (), str -> one-tuple) only inside the cv_list_actions = None branch before the order-preserving merge (06.19-02, WR-02/WR-03)

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2: Ruff 0.16.10 is below the manifest range and global formatting flags eight pre-existing planning
  Markdown files; product formatting passes. See phase deferred-items.md and WINDOWS entry 4.

- Phase 7: needs a spec or maintainer decision before planning.
- Phase 7: retain the decided stable label-mode names and document the completed Phase 06.5 `no_label` removal.
- Phase 7: carry the Phase 5 class key `pagination:hidden-label` into the stability surface.

- [Phase 4] Four open Info review findings (IN-01 `[role~="alert"]`, IN-02 hand-copied allowlist, IN-04 no guard for
  the non-core data-bs-* sentence, IN-05 missing-script enumeration) — see 04-REVIEW-DISPOSITION.md; candidates for Phase 7.

- Phase 2: Both source-probe classifier limitations remain documented; explicit tests and completed human prose UAT independently establish acceptance. See 02-VERIFICATION.md.
- Phase 7: carry the Phase 6 form surface (`form` location, `tags/button/form.html`, `FORM_LEAF_KEYS`, `get_form_actions()`, icons `save`/`cancel`/`filter-reset`) into the stability doc.
- [Phase 06.18] Security re-verified 2026-11-09 (29/29 closed, 8768f222). All review findings dispositioned (06.18-REVIEW-DISPOSITION.md: 6 fixed, R1-IN-01 skipped with reason; open 0). Codebase maps are stale (drift gate advisory): run $gsd-map-codebase after $gsd-ship per CLAUDE.md.
- Phase 7: carry the Phase 6.1 additions (`form:cancel-tag` key, `Button(tag=...)` keyword, `cv_tag` leaf field, `crud_views.E365`) into the stability doc.
- Phase 06.2 retained scope complete: CR-02–CR-04 transferred to Phase 6.3 / issue #282 and closed by its 2026-11-01 verification; AUTH-01/03/07 split recorded in ACCEPTANCE and REQUIREMENTS. AUTH-06 residual flag and IN-02/IN-03 transfer completed within 6.3 GUA-01 scope; broader Guardian identity compatibility remains in #286; WR-01 fixed in bd31992; IN-01/IN-04 closed with explicit rationale, IN-05 fixed with startup/runtime composition guards; canonical verification and UAT pass recorded after Playwright checked the final blocked-delete interaction.
- Phase 06.7 complete: canonical verification and UAT passed; carry the dynamic Cancel helper/defaults/omission contract into Phase 7. Low query-visibility acceptance-record obligation remains open below the configured security threshold.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261030-bqk | Reconcile 06.2 closure with #282: defer unresolved CR-02–CR-04 to 6.3, split acceptance, retain older open findings; documentation only | 2026-10-30 | 491ae9c | [261030-bqk-reconcile-phase-06-2-closure-with-issue-](./quick/261030-bqk-reconcile-phase-06-2-closure-with-issue-/) |
| 261030-csg | Fix Phase 06.2 WR-01 core nested-create control state; supported-version regressions pass | 2026-10-30 | bd31992 | [261030-csg-fix-phase-06-2-wr-01-core-nested-create-](./quick/261030-csg-fix-phase-06-2-wr-01-core-nested-create-/) |
| 261103-sag | Fix SonarQube and Codecov failures on PR 303 (local gates passed; remote confirmation pending) | 2026-11-03 | 82fe188 | [261103-sag-fix-sonarqube-and-codecov-failures-on-pr](./quick/261103-sag-fix-sonarqube-and-codecov-failures-on-pr/) |
| 261104-8v8 | Exclude disposable browser harness from Sonar and split six documentation assertions | 2026-11-04 | 7d4cf1d | [261104-8v8-fix-pr-305-sonar-findings-and-exclude-di](./quick/261104-8v8-fix-pr-305-sonar-findings-and-exclude-di/) |
| 261104-h24 | Add protected delete-preview links to the Library example | 2026-11-04 | e8f5a0e | [261104-h24-add-a-protected-delete-preview-links-exa](./quick/261104-h24-add-a-protected-delete-preview-links-exa/) |
| 261109-9rw | Update examples app for 06.18 ancestor authorization (nested Guardian example + core nested grants) | 2026-11-09 | 0cb0cb47 | [261109-9rw-update-examples-app-for-06-18-ancestor-a](./quick/261109-9rw-update-examples-app-for-06-18-ancestor-a/) |
| 261109-bf5 | Fix core ViewSet.default_permissions vocabulary N+1 (one ContentType read per permission row) | 2026-11-09 | 741830cf | [261109-bf5-fix-core-viewset-default-permissions-voc](./quick/261109-bf5-fix-core-viewset-default-permissions-voc/) |
| 261109-bvq | Refresh 06.18-COSTS.md from post-fix evidence (plain cold vocabulary + Guardian guard/rest split after WR-01) | 2026-11-09 | a39efcc7 | [261109-bvq-refresh-06-18-costs-md-from-post-fix-evi](./quick/261109-bvq-refresh-06-18-costs-md-from-post-fix-evi/) |

### Roadmap Evolution

- Phase 06.3 scope extended by user decision: GUA-01 owns bounded AUTH-06 residual review plus IN-02/IN-03. Completed AUTH-06 evidence stays in 6.2; transfer completed within reconciled 6.3 scope on 2026-11-01; WR-01 fixed separately in quick task 261030-csg.

- Phase 06 edited: User decision D-18: verify completed Phase 1/2 contracts on executing working branch before spec; main merge no longer prerequisite
- Phase 6.1 inserted after Phase 6: Cancel form button as a link (#275); complete before Phase 7 freezes the theme surface (URGENT)
- Phase 6.2 inserted after Phase 6.1: Request authorization and write integrity (analysis B1–B7); complete before Phase 7 freezes the theme surface (URGENT)
- Phase 06.3 inserted after Phase 6: Delete protection and write-boundary integrity — issue #282 (URGENT)
- Phase 6.4 inserted after Phase 6.3: Conditional and formset correctness/lifecycle (analysis A1–A7); complete before Phase 7 freezes the theme surface (URGENT)
- Phase 6.5 inserted after Phase 6.4: Remaining presentation contracts and decided cleanup — source analysis §8 (#259, C1/C2, Python no_label and obsolete guard removal) (URGENT)
- Phase 06.6 inserted after Phase 06.5: Theme-adoption seams from the Tabler sync (#277–#280); source analysis §8 slice 6.6; complete before Phase 7 freezes the theme surface (URGENT)
- Phase 06.7 inserted after Phase 06.6: Dynamic cancel navigation and origin query state (#302); approved scope and defaults; complete before Phase 7 freezes the public surface (URGENT)
- Phase 06.8 inserted after Phase 06.7: Action tooltips: short captions and visible-label suppression (#304); complete before Phase 7 freezes the theme surface (URGENT)
- Phase 06.9 inserted after Phase 06.8: Protected delete-preview object links (#307); user insertion schedules the issue before Phase 7 freezes the affected contracts (URGENT)
- Phase 06.10 inserted after Phase 6.9: Issue #316: simplify protected-object previews and cap total displayed objects before Phase 7; no dependency on #312, #314 or the retired URL resolver (URGENT)
- Phase 06.13 inserted after Phase 06.12: Issue #320: document and test opt-in per-transition workflow access; preserve the default change gate. Phase 06.12 is reserved on disk; this phase is independently deliverable. (URGENT)
- Phase 06.13.1 inserted after Phase 06.13: Workflow validation and execution: business blockers, transition buttons, and reusable helper (#322) (URGENT)
- Phase 06.14 inserted after Phase 6: Issue #325: add empty card_root/card_header blocks and document/test cards-first ViewSets with a secondary table; preserve existing rendering, actions, permissions and navigation. Settle these contracts before Phase 7; downstream theme implementation is separate. (URGENT)

- Phase 06.15 inserted after Phase 06.14: Issue #326: polymorphic selector labels and per-model detail groups, including required tabler-test adoption and verification. Phase 06.14 completed in another worktree per user; no card implementation dependency. (URGENT)
- Phase 06.16 inserted after Phase 06.15: Issue #327: object-detail choice labels, help-text policy, empty values, and composition guidance; settled issue decisions are the planning handoff. (URGENT)
- Phase 06.17 inserted after Phase 06.16: Issue #328: open the first accordion group and initialize/dispose tabs through theme adapters; settled issue decisions are the planning handoff. (URGENT)
- Phase 06.18 inserted after Phase 06.17: Ancestor authorization for nested ViewSets; canonical approved specification: superpowers/notes/2026-11-07-ancestor-authorization-design-v2.md. Policy decisions remain locked; planning and implementation pending. (URGENT)
- Phase 06.19 inserted after Phase 06.18: Table honours Meta.sequence and drops the empty actions column (tabler-test finding 26); canonical approved specification: superpowers/plans/2026-11-09-table-sequence-and-actions-column.md. Behaviour decisions are locked in its GSD handoff section; planning and implementation pending. (URGENT)

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-11-09T17:56:16.670Z
Stopped at: Phase 06.21 context gathered
Resume file: .planning/phases/06.21-snippet-context-exposes-view-and-parent-object/06.21-CONTEXT.md
