---
phase: quick-261103-sag
plan: "01"
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [CAN-01, CAN-02, CAN-03, CAN-04, CAN-05, CAN-06, CAN-07]
files_modified:
  - src/crud_views/lib/view/base.py
  - src/crud_views/lib/view/cancel.py
  - src/crud_views/lib/views/mixins.py
  - src/crud_views_guardian/lib/mixins.py
  - src/crud_views_polymorphic/lib/create_select.py
  - tests/test1/test_cancel_quality.py
  - tests/test1/test_cancel_state.py
  - tests/test1/test_cancel_permissions.py
  - tests/test1/test_cancel_rendering.py
  - tests/test1/test_cancel_docs.py
  - tests/browser/cancel-navigation.cjs
  - tests/browser/cancel-navigation.test.cjs
  - .planning/quick/261103-sag-fix-sonarqube-and-codecov-failures-on-pr/finding-dispositions.json
estimate:
  tokens: 24000
  raw_tokens: 24000
  tasks: 3
  confidence: low
must_haves:
  truths:
    - All 49 recorded Sonar findings have a concrete repair and fresh analysis disposition; no broad suppression or threshold reduction is used.
    - Meaningful tests exercise the 14 reported uncovered lines and related branches; final PR patch coverage is at least 96.92 percent.
    - D-01 through D-16 remain intact, including exception propagation, destination authorization, query/session isolation and unchanged success redirects.
    - Browser evidence exercises the shipping worktree source, preserves deterministic sequencing and confirms owned-process cleanup despite secondary failures.
    - Final remote checks and canonical verification refer to the repaired PR head; earlier verification is retained as historical evidence.
  artifacts:
    - path: tests/test1/test_cancel_quality.py
      provides: Behavioral coverage of the reported gaps and refactoring boundaries
    - path: tests/browser/cancel-navigation.cjs
      provides: Safe deterministic source-bound browser acceptance
    - path: .planning/quick/261103-sag-fix-sonarqube-and-codecov-failures-on-pr/finding-dispositions.json
      provides: One disposition for every issue key in sonar-before.json
  key_links:
    - from: tests/test1/test_cancel_quality.py
      to: src/crud_views/lib/view/base.py
      via: Real request/rendering and targeted branch assertions
    - from: tests/browser/cancel-navigation.cjs
      to: tests/browser/cancel_navigation_server.py
      via: Owned server with PYTHONPATH bound to the active worktree and recorded source hashes
---

<objective>
Repair SonarCloud and Codecov failures on existing PR #303 without changing the accepted Cancel contract. Current evidence is 49 Sonar findings and 95.65% patch coverage against a 96.92% target; regular Actions are green. Stay on ship/phase-06.7-cancel-navigation. Do not create a new branch or alter CI/coverage policy.
</objective>

<execution_context>
@/home/alex/.codex/gsd-core/workflows/execute-plan.md
@/home/alex/.codex/gsd-core/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md
@.planning/quick/261103-sag-fix-sonarqube-and-codecov-failures-on-pr/sonar-before.json
@.planning/quick/261103-sag-fix-sonarqube-and-codecov-failures-on-pr/planner-contributions.md
@.planning/phases/06.7-dynamic-cancel-navigation-and-origin-query-state/06.7-CONTEXT.md
@.planning/phases/06.7-dynamic-cancel-navigation-and-origin-query-state/06.7-VERIFICATION.md
@.planning/phases/06.7-dynamic-cancel-navigation-and-origin-query-state/06.7-UAT.md

Discovery level 0: existing internal code, test fixtures and installed runtimes suffice. No packages, schema, external service integration or new UI are introduced. Existing UAT approval is preserved with its recorded browser/AT limits. Quick mode uses one plan and no discussion/research/checker cycle; roadmap is untouched.

The orchestrator supplies CV_CANCEL_PYTHON for the existing Django 5.2 Python runtime, CV_CANCEL_RUFF for existing Ruff, and CV_CANCEL_ASSETS_DIR for the previously verified local assets.json directory. Cached Playwright/Chromium and Node dependencies are reusable. All commands below run from the shipping worktree root, with PYTHONPATH=src:.; the runtime may be shared, the imported source must not be. Record resolved imports before tests. Local Ruff is 0.17.3; CI pins 0.17.2, so local results do not substitute for final CI. No runtime/asset downloads are needed.
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Prove a real Cancel request and repair core transport/resolution findings</name>
  <files>src/crud_views/lib/view/base.py, src/crud_views/lib/view/cancel.py, tests/test1/test_cancel_quality.py, tests/test1/test_cancel_state.py, tests/test1/test_cancel_permissions.py</files>
  <precondition>Current branch is ship/phase-06.7-cancel-navigation; CV_CANCEL_PYTHON is executable and PYTHONPATH=src:. imports crud_views from this worktree.</precondition>
  <behavior>
    - A real client request to an existing form renders an allowed captured Cancel URL, and following it restores repeated/empty query values without a write.
    - Malformed transport falls back; developer hook/coordinate/database errors still propagate; absent or unreversible configured fallbacks remain actionable errors.
    - Core target authorization and state hooks run with the correct object/parent/request once per destination; request overrides do not mutate the bound view.
    - Cover the reported 14 missing lines across base.py (4), cancel.py (3), crispy/form.py (2), views/mixins.py (2), polymorphic/create_select.py (2) and guardian/mixins.py (1), plus meaningful alternate outcomes.
  </behavior>
  <action>First add a real request-to-render-to-return test in test_cancel_quality.py using existing fixtures; run it before refactoring. Characterize the actual uncovered lines using fresh coverage and the PR report, then add outcome assertions in that same file for the six reported modules. Include signed-payload limits/types and invalid input; missing request/origin and fallback paths; reentrant Crispy context restoration even when a kwargs hook raises; list persistence/reset/empty restoration; polymorphic invalid-state forwarding; and Guardian denied/missing-parent policy as indicated by the actual missing lines. Do not test only private helper invocation or fabricate unreachable branches to improve a percentage.

Refactor cv_get_cancel_url and bounded payload reading/validation into small private helpers with one responsibility, each within Sonar's complexity limit of 15. Preserve D-02–D-06 and D-09–D-12: current saved object only, per-call availability memoization, request-copy semantics, origin-before-fallback priority, list/card aliases, explicit static/custom keys, strict size/type/identity limits and same-ViewSet/parent binding. Correct S2583 at the action-object branch using explicit object/no-object control flow and regression coverage; do not remove valid parent behavior to silence the analyzer. Remove redundant exception subclasses without broadening catches, keeping coordinate and application exceptions outside malformed-input handling. Preserve D-15 success behavior. Split flagged composite assertions and move setup outside pytest.raises in test_cancel_state.py and test_cancel_permissions.py so each exception test has one throwing call and retains its precise error assertion. Record tests before/after refactor; characterization tests may already pass before the behavior-preserving change.</action>
  <verify>
    <automated>PYTHONPATH=src:. "$CV_CANCEL_PYTHON" -m pytest tests/test1/test_cancel_quality.py tests/test1/test_cancel_state.py tests/test1/test_cancel_permissions.py -n 4 -q</automated>
    <automated>"$CV_CANCEL_RUFF" check src/crud_views/lib/view/base.py src/crud_views/lib/view/cancel.py tests/test1/test_cancel_quality.py tests/test1/test_cancel_state.py tests/test1/test_cancel_permissions.py</automated>
  </verify>
  <done>The real return path passes, the relevant core Sonar patterns are repaired, and tests assert previously uncovered observable outcomes without changing permission, fallback or exception contracts.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Repair session and extension findings while retaining characterized behavior</name>
  <files>src/crud_views/lib/views/mixins.py, src/crud_views_guardian/lib/mixins.py, src/crud_views_polymorphic/lib/create_select.py, tests/test1/test_cancel_rendering.py, tests/test1/test_cancel_docs.py</files>
  <behavior>
    - Explicit empty/nonempty returns update memory only when persistence is enabled; ordinary reset and bare-list behavior remain unchanged.
    - Guardian target parent/object/queryset/create policies and state hooks preserve their current arguments and denial/error behavior.
    - Selector handoff retains cancel-only state or an invalid marker without forwarding the shared success-origin key.
    - Crispy/native/custom helper rendering and precise exception assertions still pass.
  </behavior>
  <action>Use Task 1's characterization tests before editing. Extract focused private operations from ListViewTableFilterMixin.get, GuardianParentPermissionMixin._cv_cancel_target_available and PolymorphicCreateSelectView.form_valid until each reported function is at or below cognitive complexity 15. Retain D-05–D-08 session semantics, navigation-field cleanup before consumers, reset ordering, repeated/blank values and original polymorphic capture. Retain D-10 destination-owned access including parent-only views, querysets with zero visible rows, inactive actors and the existing composition error; evaluate custom state adapters once. Retain D-03, D-04 and D-15: concrete auto/static settings are independent of the selector, object origins cannot become create origins, and success redirects receive no new shared origin key. Split S9073 assertions in test_cancel_rendering.py/test_cancel_docs.py and move helper setup outside each S5778 exception context; assert the same error types/messages. D-12–D-14 migration recipes and rendered control contract stay unchanged. Avoid unrelated refactoring or changes to public methods/defaults.</action>
  <verify>
    <automated>PYTHONPATH=src:. "$CV_CANCEL_PYTHON" -m pytest tests/test1/test_cancel_quality.py tests/test1/test_cancel_rendering.py tests/test1/test_cancel_docs.py tests/test1/test_cancel_polymorphic.py tests/test1/test_cancel_permissions.py tests/test1/test_cancel_state.py tests/test1/test_success_origin.py -n 4 -q</automated>
    <automated>"$CV_CANCEL_RUFF" check src/crud_views/lib/views/mixins.py src/crud_views_guardian/lib/mixins.py src/crud_views_polymorphic/lib/create_select.py tests/test1/test_cancel_rendering.py tests/test1/test_cancel_docs.py</automated>
  </verify>
  <done>All Python findings from the 49-issue inventory have concrete repairs, extension/session behavior remains covered, and existing success/rendering/migration regressions pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Secure deterministic browser verification and produce fresh quality evidence</name>
  <files>tests/browser/cancel-navigation.cjs, tests/browser/cancel-navigation.test.cjs, .planning/quick/261103-sag-fix-sonarqube-and-codecov-failures-on-pr/finding-dispositions.json</files>
  <behavior>
    - Default reports use an exclusive private temporary location; explicit output remains supported without exposing unsafe default shared filenames.
    - Git subprocesses use a validated explicit executable; source paths and hashes identify this worktree.
    - Sequential scenarios preserve page/session ordering; startup polling remains bounded, and no later step starts before its predecessor settles.
    - Browser-close failure still stops the owned fixture and records the primary error; cleanup/report failures remain secondary and unrelated processes survive.
  </behavior>
  <action>Extend existing Node tests before changing orchestration. Preserve the current VM-based main/finally failure-injection tests; adapt mocks only for genuine interface changes so they still exercise actual orchestration. Resolve S5443 with a securely created private temporary directory/report, and S4036 with explicit validated executable paths rather than command lookup through PATH. Extract asset validation, scenario execution and report/cleanup helpers to reduce both reported complexities; retain real SRI/hash/containment checks and blocked external requests. Add explicit deterministic comparators, use for-of for the growing asset work queue, optional chaining where equivalent, new Error construction, independent content-type selection, and a standalone cleanupErrors assignment for the remaining recorded rules.

Resolve the await-in-loop findings through a small tested sequential runner or event-driven bounded startup waiting. Each scenario/retry/cleanup step must complete before the next step mutates its shared page/session; do not replace these operations with Promise.all. Independent response-body observation may keep its existing concurrent collection. Keep 28 full browser cases/30 Cancel clicks, the single smoke case, repeated invalid modal replacements, tab isolation, protected deletion, permission omission and authorized submit restoration per D-01, D-06–D-08, D-10, D-12, D-15 and D-16. Preserve no-write audits and the primary failure when teardown/reporting also fails.

Create finding-dispositions.json keyed by all 49 original issue keys, recording original rule/file/line, specific repair/test, and fresh-analysis status. No issue may disappear from the ledger; do not mark remote closure from local lint alone. Run the local gates below after the last source edit and retain exact commands, runtime/import identity, source hashes, exits and coverage reports as private evidence before copying required sanitized evidence into the quick directory. Compute a local changed-line coverage estimate against the actual PR base; do not substitute whole-project coverage for patch coverage. If the target remains unmet, add meaningful cases to the Task 1 test file and rerun affected gates before final broad verification.

Hand the committed source revision and evidence to the orchestrator for push to existing PR #303, fresh full CI/Sonar/Codecov observation and canonical 06.7 verification refresh. The orchestrator owns remote checks/report updates; do not claim completion or replace the previous report with an unverified digest. Final remote evidence must identify the repaired head, all four coverage upload rows, patch coverage at least 96.92%, and the disposition of every original finding. No broad suppressions, exclusions, threshold weakening or risk acceptance may substitute for repair.</action>
  <verify>
    <automated>node --test tests/browser/cancel-navigation.test.cjs</automated>
    <automated>node tests/browser/cancel-navigation.cjs --case smoke --output "$CV_CANCEL_EVIDENCE_DIR/browser-smoke.json"</automated>
    <automated>node tests/browser/cancel-navigation.cjs --output "$CV_CANCEL_EVIDENCE_DIR/browser-full.json"</automated>
    <automated>PYTHONPATH=src:. "$CV_CANCEL_PYTHON" -m pytest tests -n 4 -q --cov --cov-report=xml:"$CV_CANCEL_EVIDENCE_DIR/coverage.xml" --cov-report=json:"$CV_CANCEL_EVIDENCE_DIR/coverage.json" --cov-report=term-missing</automated>
    <automated>"$CV_CANCEL_RUFF" check .</automated>
    <automated>"$CV_CANCEL_RUFF" format --check .</automated>
  </verify>
  <done>Harness tests and all 28 real browser cases pass against the repaired worktree; cleanup is verified; broad source-bound coverage and lint pass; the complete issue ledger and source revision are ready for remote gates and canonical report refresh.</done>
</task>

</tasks>

<threat_model>
ASVS level 1; high/critical findings block completion. No new dependency installs.

| Boundary | Description |
|---|---|
| Browser input → cancel transport/resolver | Untrusted query/token must not become authority or hide developer failures. |
| Destination resolver → authorization/session | Refactoring must preserve target policy and independent captures. |
| Harness → filesystem/process/browser | Output creation, executable resolution and teardown must remain confined to owned resources. |

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-261103-sag-01 | Elevation of privilege | Cancel/Guardian resolver | high | mitigate | Tasks 1–2 characterize destination policy and preserve bounded validated sibling resolution and exception boundaries. |
| T-261103-sag-02 | Tampering | Browser report/executables | high | mitigate | Task 3 private exclusive temporary artifacts, explicit executable paths and security regression tests. |
| T-261103-sag-03 | Denial of service | Harness teardown | medium | mitigate | Task 3 bounded startup and independent cleanup; preserve primary error and stop only owned children. |
| T-261103-sag-04 | Repudiation | Quality evidence | medium | mitigate | Issue-key ledger, imported-source assertions, browser source hashes and final-head remote checks. |
| T-261103-sag-SC | Tampering | Package installs | high | mitigate | Reuse installed runtimes/assets; no package-manager installation task exists. |
</threat_model>

<verification>
Before execution, set CV_CANCEL_EVIDENCE_DIR to an exclusively created private directory and resolve existing runtime variables. Assert the real imported package path is the current worktree's src/crud_views. Use four pytest workers for broad runs; Node cleanup tests remain serial where they exercise lifecycle ordering. Browser tests may exceed 60 seconds; collect their existing detailed report. Preserve the 4.2/6.0 supported-runtime coverage through the fresh PR matrix, including existing documented floor exclusions only. Use the existing JavaScript suite with reused node_modules if shared browser helper changes warrant it; no frontend production JavaScript is planned.

The orchestrator must refresh canonical source-bound verification after source changes and await new regular Actions, Sonar quality/security/reliability and Codecov results on the pushed SHA. Recheck the actual base/diff and regenerate coverage if the base changed. A local estimate or old successful check is not a passing current PR status.
</verification>

<source_audit>
| Source | Items | Coverage |
|---|---|---|
| GOAL | Repair actual PR #303 Sonar/Codecov failures | Tasks 1–3 plus orchestrator final-head gates |
| REQ | CAN-01/CAN-02/CAN-05 | Tasks 1–2 preserve resolver, transport and authorization |
| REQ | CAN-03/CAN-04 | Tasks 1–3 preserve session, selector and invalid-submit state |
| REQ | CAN-06/CAN-07 | Tasks 1–3 preserve rendering, recipes and browser/no-write acceptance |
| RESEARCH | No new research requested; existing source/runtime patterns | Level 0 discovery; no installs, integration or schema changes |
| CONTEXT | D-01–D-04 | Core request characterization and unchanged defaults/static/object rules |
| CONTEXT | D-05–D-08 | Transport/session/selector regression tests and real browser sequences |
| CONTEXT | D-09–D-11 | Configuration/input/access distinction and propagated application errors |
| CONTEXT | D-12–D-14 | Shared rendering tests and existing migration recipe assertions |
| CONTEXT | D-15–D-16 | Success, ownership, CSRF, escaping and exclusions retained across all tasks |
| FINDINGS | All 49 sonar-before.json keys; 14 reported missing lines | Complete disposition ledger and fresh local/remote coverage |
</source_audit>

<success_criteria>
All reported issues have evidence-backed resolution, final patch coverage is at least 96.92%, final-head remote checks pass, canonical verification is refreshed, and the accepted Cancel behavior remains unchanged. Implementation commits and push stay on existing PR #303; no merge or new branch is part of this task.
</success_criteria>

<output>
Create .planning/quick/261103-sag-fix-sonarqube-and-codecov-failures-on-pr/261103-sag-SUMMARY.md with commits, verification evidence, issue dispositions and any pending remote handoff. The planning agent only writes this plan; execution, commits, push and canonical report refresh belong to the executor/orchestrator.
</output>
