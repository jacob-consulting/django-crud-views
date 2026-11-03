---
phase: quick-261030-csg
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - src/crud_views/lib/views/create.py
  - src/crud_views/lib/view/base.py
  - src/crud_views/lib/view/buttons.py
  - src/crud_views/lib/views/card.py
  - tests/test1/test_core_nested_create_state.py
  - .planning/phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW-DISPOSITION.md
  - .planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md
  - .planning/phases/06.2-request-authorization-and-write-integrity/06.2-VALIDATION.md
autonomous: true
requirements: [AUTH-04, AUTH-07]
estimate:
  tokens: 24000
  raw_tokens: 24000
  tasks: 2
  confidence: low
must_haves:
  truths:
    - Core nested-create controls evaluate cv_action_enabled against the same parent as the linked direct GET/POST, for enabled and locked parents.
    - A permitted enabled create remains linked and writes under its URL parent; a locked create is unavailable and direct GET/POST remains 403 without a write.
    - Permission checks, label/page objects, URLs, non-create state arguments, Guardian policy and the IN-05 composition guard retain their existing behavior.
    - WR-01 closure cites observed supported-version evidence and leaves all five Phase 6.3 transfers unresolved, with phase gates and UAT still separately owned.
  artifacts:
    - path: tests/test1/test_core_nested_create_state.py
      provides: Four existing direct-request/control regression cases plus focused rendering-path controls
    - path: src/crud_views/lib/views/create.py
      provides: Core nested-create state normalization within the existing private adapter contract
    - path: .planning/phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW-DISPOSITION.md
      provides: Evidence-backed WR-01 disposition with other findings preserved
  key_links:
    - from: src/crud_views/lib/view/base.py
      to: src/crud_views/lib/views/create.py
      via: Core action context resolves the target create state parent independently of permission and label context
    - from: src/crud_views/lib/view/buttons.py
      to: src/crud_views/lib/views/create.py
      via: ContextButton target evaluation honors the same nested-create state rule
    - from: src/crud_views/lib/views/card.py
      to: src/crud_views/lib/views/create.py
      via: Both card action branches retain target state adapter behavior
---

<objective>
Fix Phase 06.2 WR-01 / AUTH-04: core nested-create controls and direct requests must agree on the action's parent, per D-10. Preserve existing request enforcement, Guardian behavior and IN-05. Record only the resulting scoped evidence; the orchestrator subsequently owns execute-phase 06.2 gates, verify-work UAT and tracking reconciliation.

Work on the current introduce-gsd branch. No new worktree, package installation, schema change or migration is needed. Other agents/user changes are present; retain unrelated edits. This quick task does not implement the Phase 6.3 transfers.
</objective>

<context>
@CLAUDE.md
@.planning/STATE.md
@.planning/REQUIREMENTS.md
@.planning/phases/06.2-request-authorization-and-write-integrity/06.2-CONTEXT.md
@.planning/phases/06.2-request-authorization-and-write-integrity/06.2-RESEARCH.md
@.planning/phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW-DISPOSITION.md
@.planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md
@.planning/phases/06.2-request-authorization-and-write-integrity/06.2-VALIDATION.md
@tests/test1/test_core_nested_create_state.py
@src/crud_views/lib/views/create.py
@src/crud_views/lib/view/base.py
@src/crud_views/lib/view/buttons.py
@src/crud_views/lib/views/list.py
@src/crud_views/lib/views/card.py
@src/crud_views_guardian/lib/views.py
@src/crud_views_guardian/lib/mixins.py
@tests/test1/test_guardian_parent_none.py
@tests/test1/test_guardian_composition.py
</context>

<baseline>
Fresh planner reproduction on 2026-10-30, HEAD a05e7edeafb5e12d356b07217e7179a87ec70169:

- Django 4.2: 4 failed in 1.10s, exit 1.
- Django 6.0: 4 failed in 1.69s, exit 1.
- All failures are the existing four parametrized cases in test_core_nested_create_state.py, at the rendered-link assertion. Before that assertion, actual enabled GET 200 / POST 302 and locked GET/POST 403 with the expected database state pass.
- Enabled list/detail controls are incorrectly absent; locked list/detail controls are incorrectly linked. Observed state arguments are NoneType on list and Book on detail, rather than Publisher.

Commands already run (repo root):
`PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests/test1/test_core_nested_create_state.py -q -p no:cacheprovider --tb=short`
`PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_core_nested_create_state.py -q -p no:cacheprovider --tb=short`

These observed RED results may be reused without repeating when the input files remain unchanged. Compare git hash-object output, in this order:

| File | Observed blob |
| --- | --- |
| src/crud_views/lib/view/base.py | d8a62a0569a99052d97a56eb35f1b3cf3e2fb42d |
| src/crud_views/lib/views/create.py | 117063a47e12d5d1904a458d9d77baf6ded3a364 |
| src/crud_views/lib/view/buttons.py | 5e5b3704569224e381aabcec93c11760ccb895e5 |
| src/crud_views/lib/views/card.py | c5a7f0aec7c0be89f1cb5a004bcc32e77e652cfd |
| tests/test1/test_core_nested_create_state.py | c3fe6dc76b54a4c59d63df21cff5387650845a9d |

If these inputs changed before execution, rerun the two commands before production edits and record the actual outcome. Do not weaken, delete, skip or xfail the four assertions.
</baseline>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Make core nested-create state agree from rendered controls through direct requests</name>
  <files>src/crud_views/lib/views/create.py, src/crud_views/lib/view/base.py, src/crud_views/lib/view/buttons.py, src/crud_views/lib/views/card.py, tests/test1/test_core_nested_create_state.py</files>
  <read_first>Read the files above together with src/crud_views_guardian/lib/views.py, src/crud_views_guardian/lib/mixins.py, tests/test1/test_guardian_parent_none.py and tests/test1/test_guardian_composition.py. The existing core request oracle is CrudView.cv_get_action_object; rendering currently calls _cv_action_enabled_for_context. GuardianCreateViewPermissionRequired already overrides that adapter and GuardianQuerysetMixin.cv_get_context supplies its URL-parent fallback.</read_first>
  <behavior>
    - Retain the four enabled/locked × list/detail cases exactly: every observed core create state argument is the matching Publisher; enabled link/GET/POST/write and locked unavailable-control/403/no-write agree.
    - A renamed ContextButton whose key_target is create obeys the target's state on list and detail pages.
    - Core same-ViewSet card create actions normalize their state object; parent-to-child create controls/card actions retain the explicit parent.
    - Where a rendered create URL carries a parent, state follows that parent. Missing/unresolvable parent context fails closed without calling a custom state hook with None or an unrelated model.
    - Top-level creates and non-create actions retain their existing state arguments. Page/label objects, permission arguments, URLs, origins and hide/disable presentation retain their meaning.
    - Existing Guardian parent-None, FK-own-child, explicit-parent, ambiguous M2M, global fallback, inactive actor and late-parent-resolution controls remain green; IN-05 startup/runtime missing/unreachable-gate cases remain green.
  </behavior>
  <action>
Use the fresh four-case RED evidence above after confirming input identity; otherwise reproduce before editing. Add narrowly focused tests for the other rendered entry points touched by the fix, using existing registered views, monkeypatch and current fixtures in the same regression module. Observe any new defect test fail before its implementation.

Correct core CreateView state normalization and the core rendering callers per D-10. Keep the public cv_action_enabled(user, obj) hook unchanged. The private target adapter should receive the actual parent for nested create: accept the explicit target parent, resolve a configured single-FK own child when no request-parent context is available, and use the parent from the target link's URL context on list/detail rendering. Do not infer a unique parent from an ambiguous M2M child; an explicit URL-bound parent remains usable. Keep state-object resolution separate from cv_has_access and from the ViewContext object used for labels.

Wire that behavior through CrudView._cv_get_action_context and ContextButton target handling, covering renamed buttons as well as ordinary create keys. Inspect ParentContextButton, ChildContextButton and SiblingContextButton against the actual target route: preserve correct explicit-parent inputs and normalize nested-create targets where needed. Both CardListView.cv_get_card_action_data branches must use the same target-state semantics. Use the existing private adapter seam and a bounded rendering helper if URL context must be supplied; retain the adapter's existing subclass override behavior. Avoid a new public configuration or API.

Preserve Guardian's existing adapter and list fallback, particularly its failure-before-state-hook rule; do not replace its permission resolver or loosen callable-helper input rules. Per D-03, D-05, D-10 and D-11, preserve per-view global fallback, strict helpers, parent-None permissions and inactive denial. Leave direct-request authorization and the IN-05 startup/runtime composition validator intact. Per D-12/D-13/D-14, retain write binding, existing parent safeguards and form/cancel behavior. Production edits are limited to the named core files; change only those needed by the proven paths.

Run the four-case module on both cached supported versions after the fix. Then run the focused preservation selection below separately per version. If a selected failure reveals an in-scope regression, correct it and rerun the affected selection. Broader full-suite and phase-gate work belongs to the subsequent orchestrator run.
  </action>
  <verify>
    <automated>PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests/test1/test_core_nested_create_state.py -q -p no:cacheprovider --tb=short</automated>
    <automated>PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_core_nested_create_state.py -q -p no:cacheprovider --tb=short</automated>
    <automated>PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests/test1/test_guardian_parent_none.py tests/test1/test_guardian_composition.py tests/test1/test_action_enabled.py tests/test1/test_view_level_context_button.py tests/test1/test_sibling_context_button.py tests/test1/test_context_button_permission_filter.py -q -p no:cacheprovider --tb=short</automated>
    <automated>PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests/test1/test_guardian_parent_none.py tests/test1/test_guardian_composition.py tests/test1/test_action_enabled.py tests/test1/test_view_level_context_button.py tests/test1/test_sibling_context_button.py tests/test1/test_context_button_permission_filter.py -q -p no:cacheprovider --tb=short</automated>
    <automated>.venv/bin/ruff check src/crud_views/lib/views/create.py src/crud_views/lib/view/base.py src/crud_views/lib/view/buttons.py src/crud_views/lib/views/card.py tests/test1/test_core_nested_create_state.py</automated>
    <automated>.venv/bin/ruff format --check src/crud_views/lib/views/create.py src/crud_views/lib/view/base.py src/crud_views/lib/view/buttons.py src/crud_views/lib/views/card.py tests/test1/test_core_nested_create_state.py</automated>
  </verify>
  <done>All original WR-01 cases and added touched-path regressions pass on Django 4.2/6.0, with real request/write assertions retained; the focused Guardian/IN-05 and existing context/action controls pass on both versions. Scoped lint/format passes. No public hook signature or permission policy changes.</done>
</task>

<task type="auto">
  <name>Task 2: Reconcile WR-01 evidence without closing transferred obligations</name>
  <files>.planning/phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW-DISPOSITION.md, .planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md, .planning/phases/06.2-request-authorization-and-write-integrity/06.2-VALIDATION.md</files>
  <action>
After Task 1 passes, update these existing files using scoped edits. Set only WR-01's disposition to fixed and cite the implementation/test evidence and this quick-task summary. Recalculate the disposition counts: open 0, deferred 5, unresolved 5, total 11. CR-02/CR-03/CR-04 remain deferred to 6.3 DEL-01–06 and IN-02/IN-03 remain deferred to 6.3 GUA-01. Preserve the AUTH-06 unidentified review flag, IN-01/IN-04 rationale, IN-05 fixed status, CR-01/WR-02 prior scope and A19's separate proposed-6.4 ownership.

Update the current WR-01 qualification in ACCEPTANCE's ownership split, AUTH-04 evidence row, normalized-state handoff and older-review disposition section to describe the measured core behavior. Preserve historical measurements and label historical WR-01-open statements by date where retained. Append scoped WR-01 validation evidence: the RED results from this plan, new RED cases if added, final commands/version/results/timing, affected commit IDs when available, Guardian/IN-05 preservation and lint/format results. Differentiate new defect coverage from unchanged preservation controls.

Per D-10/D-12/D-14, make the evidence state precisely what was tested. Keep phase closure pending and nyquist_compliant false; neither this quick fix nor its passing tests constitutes full Phase 06.2 verification, UAT, or acceptance of the 6.3 transfers. Leave ROADMAP, STATE, REQUIREMENTS, VERIFICATION and UAT tracking to the orchestrator's next authorized work. Do not edit source review reports to erase their original findings.
  </action>
  <verify>
    <automated>git diff --check a05e7edeafb5e12d356b07217e7179a87ec70169 -- .planning/phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW-DISPOSITION.md .planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md .planning/phases/06.2-request-authorization-and-write-integrity/06.2-VALIDATION.md</automated>
    <human-check>Compare the three evidence diffs together: WR-01 is fixed with actual 4.2/6.0 evidence; five transferred findings remain deferred/unresolved; phase verification/UAT is still pending; historical results are not relabeled as fresh runs.</human-check>
  </verify>
  <done>The three evidence files agree on WR-01 closure and the 0/5/5/11 disposition counts, include fresh measured results, and preserve all outstanding transfers and phase-level gate ownership.</done>
</task>

</tasks>

<source_audit>
Quick scope is the explicitly authorized WR-01 repair, not a replan of all completed Phase 06.2 work.

| Source | Item | Task | Coverage |
| --- | --- | --- | --- |
| GOAL | Phase 06.2 criterion 4: library-owned create controls/direct-request agreement | 1 | COVERED |
| REQ | AUTH-04 remaining core rendered-state gap | 1–2 | COVERED |
| REQ | AUTH-07 relevant parent/native control preservation and measured evidence | 1–2 | COVERED |
| RESEARCH | B4/B6: parent resolution, independent state, fail-closed missing parent, no new child-add grant | 1 | COVERED |
| CONTEXT | D-10 create-state/parent agreement | 1–2 | COVERED |
| CONTEXT | D-03/D-05/D-11 Guardian policy preservation; D-12/D-13/D-14 retained requests/forms and accurate evidence | 1–2 | COVERED |
| CONTEXT | D-01/D-02/D-04/D-06/D-07/D-08/D-09 existing method/configuration/preview/fragment work | Existing phase plans | Outside this authorized repair; preserve current implementations and open qualifications |
| TRANSFER | CR-02–CR-04, IN-02/IN-03 and AUTH-06 residual review | 2 | Explicitly retained unresolved under 6.3 |
</source_audit>

<planner_hooks>
Active planner contributions applied in registry order: API coverage detector, assumption-delta detector, schema detection, security. Nonplanner steps/contributions are excluded from this quick invocation. The phase-scope probes returned detected:false for API coverage and assumption delta; no schema patterns or installation tasks are present. Security uses ASVS level 1 and blocking threshold high. Discovery level 0: internal established adapter/caller patterns, no dependency or architecture selection. Estimate calibration factor 1, sample_count 0, confidence low.
</planner_hooks>

<threat_model>
ASVS L1; high-severity in-scope regressions block this quick task. IDs continue after the existing Phase 06.2 maximum T-06.2-19.

## Trust Boundaries

| Boundary | Description |
| --- | --- |
| Rendered page/object → target create action | A page child or absent page object must not replace the target route's actual parent |
| Browser request → write authorization | Hidden/disabled controls are presentation; direct GET/POST independently enforce state and permissions |
| Core rendering → Guardian subclass policy | Shared callers must retain Guardian parent resolution, actor checks and composition enforcement |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
| --- | --- | --- | --- | --- | --- |
| T-06.2-20 | Tampering | Core nested-create action state | medium | mitigate | Task 1 compares enabled/locked parent state across actual rendered links and direct GET/POST, including exact parent identity and stored FK. Existing server denial limits current impact. |
| T-06.2-21 | Elevation of privilege | Guardian/core parent and permission boundaries | high | mitigate | Task 1 preserves independent permission checks and replays parent-None, inactive/global, FK/M2M and IN-05 missing/unreachable-gate regressions on both supported versions. |
| T-06.2-22 | Tampering | Acceptance/disposition evidence | medium | mitigate | Task 2 updates only WR-01, retains five unresolved transfers, and records exact observed commands/results without claiming phase UAT or verification. |
| T-06.2-SC | Tampering | Package-manager installation | high | mitigate | No installation is authorized or needed; use the existing cached environments. |
</threat_model>

<verification>
Reuse the unchanged-input RED baseline; execute Task 1's supported-version GREEN and preservation commands, scoped Ruff, then git diff --check. Cached Django 4.2/6.0 evidence is mandatory. Local .venv Python/Django results are supplemental only. Record measured counts and durations; do not describe an unrun full suite as passing.
</verification>

<success_criteria>
WR-01 controls and direct requests use the same parent and all targeted supported-version regressions pass. Guardian and IN-05 remain intact. WR-01 evidence is reconciled without closing any 6.3 transfer or marking phase verification/UAT passed.
</success_criteria>

<output>
Create .planning/quick/261030-csg-fix-phase-06-2-wr-01-core-nested-create-/261030-csg-SUMMARY.md with changed paths, commits, RED/GREEN and preservation evidence, and the handoff to the orchestrator for Phase 06.2 gates and UAT.
</output>

