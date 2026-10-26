# Phase 4: Alert dismiss adapter - Research

**Researched:** 2026-10-26
**Domain:** Existing Django alert templates and browser adapter integration
**Confidence:** MEDIUM (official-documentation confidence seam; direct local evidence cited separately)

<user_constraints>
## User Constraints (from CONTEXT.md)

The following decisions and exclusions are copied verbatim. [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:20-65,128-132]

<!-- DATA_29a610cb_START -->
### Locked Decisions

### Frame styling
- **D-01:** Keep the existing literal frame classes, including `btn-close` and `alert-dismissible fade show`.
  Do not introduce new alert class-table keys in Phase 4. The additional frame-class keys remain tracked
  under existing LATER-06.
- **D-02:** Add a short frame-override example in `docs/reference/theme.md`, rather than only explanatory
  prose and links. Show custom frame classes while retaining `role="alert"` on the frame and
  `data-cv-alert-dismiss` on its close control. These hooks preserve the delegated dismissal behavior.
  Keep the example focused on the existing frame contract.

### Custom adapter behavior
- **D-03:** Core calls the theme's `alert.close(el)` and lets exceptions surface. Do not catch and log a
  custom-adapter failure or force removal afterward. Core leaves the alert alone on failure; it does not
  undo any changes already made by the adapter.
- **D-04:** Plain `el.remove()` is a fallback inside the default alert adapter only when the configured
  namespace has no `Alert` component. It is not a second closing path in the delegated handler and is not
  recovery from a throwing custom adapter or Bootstrap component. The theme owns its closing behavior.

### Migration guidance
- **D-05:** Add a compact before/after example in `docs/migrating-1.0.md`, rather than a single migration
  bullet with links alone. Show replacement of `data-bs-dismiss="alert"` with `data-cv-alert-dismiss`,
  explain the required core scripts, and link to the adapter and message references for details.
- **D-06:** Recommend adopting the new hook when upgrading copied alert templates, even when retaining
  Bootstrap. Explain that legacy overrides using `data-bs-dismiss="alert"` still work through Bootstrap's
  own JavaScript; they do not gain the adapter's no-Bootstrap fallback until migrated.

### Carried-forward scope and acceptance
- **D-07:** Commit a golden of today's dismissible alert before changing the markup, so the implementation
  history shows the attribute change (ALRT-01). Preserve other output and non-dismissible behavior.
- **D-08:** Follow the source design: delegate clicks in `viewset.js`, locate the enclosing
  `role="alert"` frame, and call `cv.adapters.alert.close(alertEl)`. Newly inserted alerts, including modal
  content, must close without per-alert initialization. Keep adapter lookup at call time and the existing
  preassigned-adapter preservation and Bootstrap namespace conventions.
- **D-09:** Update `docs/reference/javascript.md`, `docs/reference/messages.md`, and
  `docs/reference/theme.md`. The adapter factory now supplies four adapters. Record the DOM attribute change
  under CHANGELOG Breaking and update the migration guide in the same change. The stock template's remaining
  `data-bs-*` uses must be limited to the dropdown templates already named in `theme.md`.
- **D-10:** Verify closing with Bootstrap, without its `Alert` component, and through a custom adapter;
  cover delegated handling of dynamically inserted alerts and the chosen error behavior. Confirm the
  example project's flash messages still close. Preserve the project's implementation quality gates.

### Agent's Discretion
- No product decision was explicitly delegated. Exact test organization, implementation details of the
  delegated handler, template whitespace, and documentation wording remain implementation choices within
  the decisions and acceptance requirements above.

### Deferred Ideas (OUT OF SCOPE)

Additional alert frame class-table keys remain under existing LATER-06. No new deferred capability was
added. Focus management, auto-dismiss, and downstream theme implementation remain outside this phase.
<!-- DATA_29a610cb_END -->
</user_constraints>


## Summary

Extend the existing factory and document-level event pattern. Commit a deterministic before-change golden first,
then add the default alert adapter, delegate the marker to the nearest alert role, and replace only the stock
dismiss attribute. D-04 supersedes the older source-plan sentence putting removal in the handler: removal belongs
only inside the default adapter when its configured namespace lacks Alert.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:32-60]

Bootstrap owns cancellation, transitions and destruction once its component is present. Never remove the element
after invoking a present Bootstrap/custom adapter, including when it throws. Official tagged source checks the
cancelable close event before scheduling destruction.
[CITED: https://raw.githubusercontent.com/twbs/bootstrap/v5.3.3/js/src/alert.js]

**Primary recommendation:** Plan a dependency chain of baseline commit → implementation/regressions → docs and example
verification. No new dependency or public capability is needed beyond D-01 through D-10.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:22-65]

## Architectural Responsibility Map

Recommended assignments implement the locked scope.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:7-15,22-60]

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Frame, translated label, escaping | Django server rendering | Browser display | Preserve existing data/frame contract |
| Click matching and nearest alert selection | Browser / Client | — | One document listener covers injected content |
| Framework close or fallback | Browser adapter | Optional Bootstrap namespace | Theme owns behavior |
| Script delivery | Static assets | Django asset rendering | Reuse existing scripts |
| Persistence or HTTP operation | None added | — | Dismissal only changes current DOM |

<phase_requirements>
## Phase Requirements

Requirement descriptions below come from the phase requirements.
[CITED: .planning/REQUIREMENTS.md, Alert dismiss (plan 3A)]

| ID | Description | Research Support |
|---|---|---|
| ALRT-01 | Golden of today's dismissible alert is committed before the change | First task captures unchanged render, verifies comparison, commits before product edit |
| ALRT-02 | tags/alert.html renders data-cv-alert-dismiss instead of data-bs-dismiss="alert"; one delegated click handler calls cv.adapters.alert.close(el) | Existing document handler pattern; nearest role; nested and dynamic tests |
| ALRT-03 | cv.adapters.alert.close uses Bootstrap Alert when present and falls back to el.remove() inside the adapter; Vitest covers both | Factory-local branch; preserve lazy namespace and preassigned adapters |
| ALRT-04 | Stock data-bs attributes remain only in documented dropdown templates; update JS/messages/theme docs, CHANGELOG Breaking and migration | Static audit, five-document update, strict docs and example smoke |
</phase_requirements>

## Project Constraints (from AGENTS.md)

The user-supplied AGENTS guidance matches CLAUDE.md. No separate AGENTS file/project skills were found by the local
discovery probes; the agent-skills query returned no configured skills. [VERIFIED: session discovery probes]

Apply these actionable conventions; exact source tokens are quoted.
[VERIFIED: CLAUDE.md:15-47,89-105]

<!-- DATA_b9c573e2_START -->
- Use documented workflows: "task dev", "task test", "pytest tests", "task format", "task check",
  "task build", "task docs", "task bump-patch" for their respective operations.
- Preserve "cv_" class attributes and view keys "list", "detail", "create", "update", "delete", "workflow", "manage".
- Preserve permission mapping "list/detail→view, create→add, update→change, delete→delete".
- Preserve "wf_" workflow prefixes.
- Follow fixture prefixes "cv_<model>", "user_<model>_<permission>", "client_user_<model>_<permission>".
- "Line length: 120 characters (ruff)" and "Quote style: double quotes".
- "Build system: hatchling"; "Version management: bump-my-version". No version bump is in this phase.
- "Pre-commit hook: ruff-format runs on commit."
- A "### Breaking" entry in "CHANGELOG.md" also updates "docs/migrating-1.0.md" before 1.0.
<!-- DATA_b9c573e2_END -->

Honor the project branch policy and byte-preservation rule outside the permitted attribute change. Add no downstream
project names, new frame keys, focus management, auto-dismiss or lifecycle events. Keep full Python/JS/docs/Ruff
shipping gates. [CITED: .planning/PROJECT.md, Constraints]
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:14-15,22-60]

## Standard Stack

Retain classic browser scripts, DOM delegation, existing Django templates, pytest and Vitest/jsdom. These are
observations of the existing stack, not package installation recommendations. No registry/latest-version or package
legitimacy audit is required because this phase installs nothing.
[VERIFIED: src/crud_views/static/crud_views/js/adapters.js:1-44]
[VERIFIED: src/crud_views/static/crud_views/js/viewset.js:15-44]

| Component | Observed version | Use |
|---|---|---|
| Python / Django | 3.12.3 / 5.2.14 | Existing server rendering |
| pytest | 9.1.1 | Render and golden tests |
| Node / npm | 20.20.2 / 10.8.2 | Existing JS harness |
| Vitest / jsdom | 4.1.10 / 29.1.1 | Browser unit tests |
| MkDocs | 1.6.1 | Strict docs build |
| Ruff | 0.16.10 | Existing gate; below declared range |
| Bootstrap | Example uses 5.3.3 | Optional Alert implementation |

Versions are actual local probes; Bootstrap version is the example's inspected CDN reference.
[VERIFIED: session version probes]
[CITED: examples/bootstrap5/project/templates/project/base.html:15-21]

The manifest differs from installed JS/Ruff versions. Keep this limitation explicit; passing focused tests does not
establish a manifest-clean install. Exact declarations:
[VERIFIED: package.json:10-21] [VERIFIED: pyproject.toml:60-64]

<!-- DATA_e8db136a_START -->
- "test": "vitest run"
- "node": ">=20"
- "jsdom": "^30.1.2"
- "vitest": "^5.0.3"
- "ruff>=0.17,<0.18"
<!-- DATA_e8db136a_END -->

**Installation:** None for the feature. If the shipping gate requires environment reconciliation, handle it explicitly
without changing dependency manifests to conceal drift.

## Architecture Patterns

### System Architecture Diagram

Proposed flow, derived from D-03, D-04 and D-08.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:32-37,50-53]

~~~mermaid
flowchart TD
    Render[Django alert render] --> DOM[Initial page or injected modal content]
    DOM --> Click[Click control or descendant]
    Click --> Match{Element and dismiss marker?}
    Match -->|No| Ignore[Ignore]
    Match -->|Yes| Frame{Nearest alert role exists?}
    Frame -->|No| Ignore
    Frame -->|Yes| Adapter[Resolve current alert adapter]
    Adapter --> Custom[Custom close behavior]
    Adapter --> Default[Default resolves namespace]
    Default --> Present{Alert component present?}
    Present -->|Yes| Bootstrap[Get instance and close]
    Present -->|No| Remove[Remove element]
    Custom --> Error[Exceptions surface without core recovery]
    Bootstrap --> Error
~~~

### Component Responsibilities / Proposed Edit Targets

Edit existing modules; proposed new golden placement is an implementation choice.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:95-122]

| Target | Planned responsibility |
|---|---|
| src/crud_views/static/crud_views/js/adapters.js | Factory entry; four-adapter comment |
| src/crud_views/static/crud_views/js/viewset.js | Single delegated handler |
| src/crud_views/templates/crud_views/tags/alert.html | Dismiss attribute substitution only |
| tests/test1/test_alerts.py and test_messages.py | Baseline, render and message regressions |
| tests/js/adapters.test.js and viewset.test.js | Factory, namespace, delegated and error cases |
| Proposed golden under tests/test1/golden/ | Commit current dismissible markup first |
| docs/reference/javascript.md, messages.md, theme.md | Public contract, scripts and frame example |
| CHANGELOG.md and docs/migrating-1.0.md | Paired Breaking entry and before/after migration |

### Preserve lazy lookup and preassigned adapters

Verbatim existing seam:
[VERIFIED: src/crud_views/static/crud_views/js/adapters.js:7-8,43-44]

<!-- DATA_d802f619_START -->
~~~javascript
function resolve(ns) { return (typeof ns === "function" ? ns() : ns) || null; }
function component(ns, name) { const n = resolve(ns); return n && n[name] ? n[name] : null; }
cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {});
~~~
<!-- DATA_d802f619_END -->

Resolve the component within close, and the adapter within the click callback. Do not replace the shallow merge,
capture the default global at load time or add a second removal path.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:32-37,50-53]

### Preserve the frame contract

Exact existing values:
[VERIFIED: src/crud_views/templates/crud_views/tags/alert.html:2-5]

<!-- DATA_a750b632_START -->
- alert-dismissible fade show
- role="alert"
- {% include alert.body_template %}
- <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="{% translate 'Close' %}"></button>
<!-- DATA_a750b632_END -->

Find the nearest role frame from the matched control, not a Bootstrap class or arbitrary target ID. Keep the Element
guard and preventDefault pattern of existing handlers.
[VERIFIED: src/crud_views/static/crud_views/js/viewset.js:37-44]
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:26-29,50-53]

### Documentation checklist

- JS reference: add method row, four-adapter wording, error contract and call-time replacement. Update the script-needs
  table: viewset currently says nothing is required at use time; dismiss clicks will require the alert adapter.
  [CITED: docs/reference/javascript.md:7-59]
- Messages reference: replace old markup and Bootstrap-only closing explanation; require the core scripts. Distinguish
  no-Bootstrap dismissal from the unchanged stock CSS classes.
  [CITED: docs/reference/messages.md:27-38]
  [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:22-45]
- Theme reference: short frame override using custom classes while keeping role, marker, body include, dismissible
  condition and translated accessible close label. Render the complete recipe using the existing locmem override
  helper if included as a working replacement.
  [VERIFIED: src/crud_views/templates/crud_views/tags/alert.html:1-6]
  [VERIFIED: tests/test1/test_form_frame.py:58-68]
- Migration: compact before/after attributes, core-script requirement, recommendation for copied templates, and explicit
  legacy Bootstrap-only path. Add the paired Breaking entry.
  [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:39-57]
- Data-attribute audit: remaining matches must be confined to the documented dropdown templates; do not promise the
  removal of Bootstrap CSS.
  [CITED: docs/reference/theme.md:172-184]

## Don't Hand-Roll

| Problem | Avoid | Reuse | Evidence |
|---|---|---|---|
| Animation/cancellation/teardown | Timers, class toggles, unconditional removal | Bootstrap Alert close | [CITED: https://raw.githubusercontent.com/twbs/bootstrap/v5.3.3/js/src/alert.js] |
| Dynamic alert wiring | Mutation observer or per-alert initialization | Document delegation | [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:50-53] |
| Framework selection | Bootstrap calls in click handler | Adapter factory | [VERIFIED: src/crud_views/static/crud_views/js/adapters.js:7-44] |
| Message rendering | Browser HTML reconstruction | Existing server helper/frame | [VERIFIED: src/crud_views/lib/messages.py:35-54] |
| Test framework | New runner/dependency | Existing pytest/Vitest harness | [VERIFIED: vitest.config.js:1-9] |

## Runtime State Inventory

This is a DOM-hook migration; the inventory is bounded to this repository, not downstream deployments.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:7-15,39-60]

| Category | Observation | Action |
|---|---|---|
| Stored data | Existing helper renders queued messages [VERIFIED: src/crud_views/lib/messages.py:57-84] | No data migration proposed |
| Live service config | Copied templates explicitly need migration; external deployments were not inspected [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:39-45] | Publish guidance; no external service edit |
| OS-registered state | No OS registration in inspected complete JS sources [VERIFIED: src/crud_views/static/crud_views/js/adapters.js:1-44] [VERIFIED: src/crud_views/static/crud_views/js/viewset.js:1-44] | None proposed |
| Secrets/env vars | Scope changes only DOM hook/browser behavior [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:7-15] | No key/setting rename |
| Build artifacts | Copied templates keep the old data API path [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:43-45] | Verify updated markup/scripts together through normal deployment; no package rename |

## Common Pitfalls

1. A post-change snapshot cannot establish ALRT-01. Commit the before-change golden independently before product edits.
   [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:48-49]
2. Forced removal after any adapter call violates theme ownership and Bootstrap cancellation/transition behavior.
   Test custom no-op and throws, as well as success.
   [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:32-37]
   [CITED: https://raw.githubusercontent.com/twbs/bootstrap/v5.3.3/js/src/alert.js]
3. Test namespace present but Alert absent, not only global absence; also test object/function alternate namespaces.
   [VERIFIED: src/crud_views/static/crud_views/js/adapters.js:7-8,43]
4. A delegated exception does not propagate through dispatchEvent to its caller. Observe the window error event and
   original error identity; assert no core log/removal. Suppress reporting in test-only code with finally cleanup.
   [CITED: https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/dispatchEvent]
5. The viewset suite deliberately puts a reload/no-jQuery test last because reloading installs listeners again.
   Add new click cases before it and clean adapter globals between cases.
   [CITED: tests/js/viewset.test.js:26-33,91-101]
6. A server-render check does not prove the example's browser closure. Preserve the actual smoke acceptance.
   [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:58-60]

## Code Examples

### Existing delegated handler

Verbatim local pattern:
[VERIFIED: src/crud_views/static/crud_views/js/viewset.js:37-44]

<!-- DATA_789b3d4a_START -->
~~~javascript
// cancel button navigation via data-cv-cancel-url
document.addEventListener("click", function (e) {
    if (!(e.target instanceof Element)) return;
    const el = e.target.closest("[data-cv-cancel-url]");
    if (!el) return;
    e.preventDefault();
    globalThis.location.href = el.getAttribute("data-cv-cancel-url");
});
~~~
<!-- DATA_789b3d4a_END -->

Proposed alert pseudocode: match marker → find nearest role frame → prevent default → current adapter close.
Default adapter: resolve component → present: getOrCreateInstance then close; absent: remove.
No catch/finally recovery. [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:32-37,50-53]
[CITED: https://getbootstrap.com/docs/5.3/components/alerts/]

### Golden precedent

Existing writer creates the destination before capture:
[VERIFIED: tests/test1/test_form_frame.py:50-55]

<!-- DATA_0f76e2bd_START -->
~~~python
def _check_golden(name: str, markup: str):
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_norm(markup) + "\n")
    assert _norm(markup) == path.read_text().strip()
~~~
<!-- DATA_0f76e2bd_END -->

For this phase use an alert-specific golden and preferably raw deterministic rendering to detect whitespace drift.
Keep locale fixed; pair it with unchanged non-dismissible assertions. Never regenerate unrelated goldens.
This is a test-design recommendation implementing D-07.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:48-49]

## State of the Art

| Existing behavior | Planned behavior | Impact |
|---|---|---|
| Bootstrap data API closes stock alert | Package marker invokes current adapter | Intentional DOM breaking change |
| Three adapters | Four adapters | Additive public method |
| Legacy hook needs Bootstrap | Default adapter removes when component absent | Fallback only for new path |
| Literal frame styling | Same styling, documented override | New class keys remain deferred |

This table describes the locked project transition, not a library release claim.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:22-60]

## Environment Availability

Available: Node, npm, Python/Django, pytest, Vitest/jsdom, MkDocs, Ruff, task and uv. Version probes are listed in
Standard Stack. Context7 MCP and ctx7 CLI were unavailable; official web sources provided the fallback.
No missing tool blocks the focused automated checks actually run. The live example/browser smoke remains unverified.
[VERIFIED: session environment probes]

Do not convert tool-version drift into an unsupported-runtime claim. Focused checks pass with the installed tools;
restoring the declared environment remains a shipping verification question.
[VERIFIED: session focused command output] [VERIFIED: package.json:15-21] [VERIFIED: pyproject.toml:60-64]

## Validation Architecture

### Test Framework

Existing JS configuration declares "environment: \"jsdom\"", "include: [\"tests/js/**/*.test.js\"]" and
"setupFiles: [\"tests/js/helpers/setup.js\"]".
[VERIFIED: vitest.config.js:3-8]

| Property | Value |
|---|---|
| Python framework | pytest 9.1.1 and existing Django setup |
| JS framework | Installed Vitest 4.1.10 / jsdom 29.1.1; manifest drift recorded |
| Python quick | .venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q |
| JS quick | npm test -- tests/js/adapters.test.js tests/js/viewset.test.js |
| Full Python | .venv/bin/pytest tests -n auto |
| Full JS | npm test |
| Docs | .venv/bin/mkdocs build --strict |
| Lint/format | .venv/bin/ruff check ; .venv/bin/ruff format --check (run separately) |

Research baseline: **50 Python tests passed in 1.19 s**, **25 JS tests passed in 841 ms**. Strict docs built successfully
to a temporary output directory. Full suites and Ruff are execution gates, not claimed research results.
[VERIFIED: session focused-test and docs-build output]

### Phase Requirements → Test Map

Rows specify planned regressions using runnable existing suite commands; no invented test selector is required.

| Req ID | Behavior | Type | Automated command | Exists? |
|---|---|---|---|---|
| ALRT-01 | Baseline dismissible render before product edits | Golden/history | .venv/bin/pytest tests/test1/test_alerts.py -q | Suite yes; golden case Wave 0 |
| ALRT-02 | New marker; preserved roles/classes/body/label; no marker when nondismissible | Render | .venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q | Extend existing |
| ALRT-02 | Nested click, nearest role, missing role, unrelated/non-Element targets | JS DOM | npm test -- tests/js/viewset.test.js | Add cases |
| ALRT-02 | Markup inserted after registration, including modal-like subtree | JS DOM | npm test -- tests/js/viewset.test.js | Add cases |
| ALRT-03 | Bootstrap instance close vs absent component removal | JS unit | npm test -- tests/js/adapters.test.js | Add cases |
| ALRT-03 | Alternate object/function namespace, late global, preserved preassigned adapter | JS unit | npm test -- tests/js/adapters.test.js | Extend existing patterns |
| ALRT-03 | Call-time custom swap, no-op, throw, retained adapter mutation | JS DOM | npm test -- tests/js/viewset.test.js | Add cases |
| ALRT-03 | Present component failure surfaces without fallback | JS unit | npm test -- tests/js/adapters.test.js | Add cases |
| ALRT-04 | Only documented dropdown templates retain data-bs attributes | Static audit | rg -n 'data-bs-' src/crud_views/templates | Audit existing tree |
| ALRT-04 | References and paired migration/changelog | Docs | .venv/bin/mkdocs build --strict | Baseline green |
| ALRT-04 | Example config and docs sync | Smoke | Commands below | Baseline green |
| ALRT-04 | Example flash message really closes | Browser/manual | Smoke procedure below | Execution acceptance |

### Meaningful regression matrix

- Factory: absent global, null/empty namespace, namespace with other components but no Alert, explicit namespace with
  Alert, lazy function namespace changing after construction, late global. Verify exact element/call count.
- Present component: a fake close that leaves the element attached detects accidental second removal; a throwing
  getOrCreateInstance/close must surface its error without removal.
- Theme: preassigned adapter identity survives factory initialization; replacing it after viewset load affects the
  next click. A no-op preserves DOM. A throwing adapter does not cause core logging/removal; any adapter mutation
  before throwing remains.
- Delegation: click close and descendants; close nearest role even without Bootstrap classes; insert after script
  load; ignore unmarked/outside-frame/non-Element targets.
- Rendering: explicit alert and flash messages; nondismissible has no control; preserve heading/body/icon/classes,
  translated accessible label, escaped hostile text/extra tags, and existing safe-string behavior.

These are implementation of D-03/D-04/D-07/D-08/D-10, not added product scope.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:32-60]
[VERIFIED: src/crud_views/lib/messages.py:35-54]

Use the existing filter test precedent for expected listener errors, but record the error and assert no core logging;
remove the temporary window listener in finally. Do not globally ignore uncaught exceptions.
[CITED: tests/js/list.filter.test.js:198-213,309-323]
[CITED: https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/dispatchEvent]

### Baseline commit ordering

1. Capture deterministic current dismissible markup with product code unchanged.
2. Run comparison without golden-update mode; confirm legacy attribute is present.
3. Commit only baseline test/golden before any template edit.
4. Implement and update only that golden and intended assertions.
5. Review history and golden diff: attribute replacement only; other goldens/non-dismissible output unchanged.

This is required by ALRT-01/D-07.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:48-49]

### Documentation and example verification

From repo root:

~~~bash
.venv/bin/python examples/bootstrap5/manage.py check
~~~

From examples/bootstrap5:

~~~bash
../../.venv/bin/pytest test_docs_sync.py -q
~~~

Research results: system check **no issues**; docs sync **36 passed in 0.07 s**. Sync covers explicitly marked blocks;
it does not prove a newly added unmarked theme recipe works.
[VERIFIED: session example probes] [CITED: examples/bootstrap5/test_docs_sync.py:1-10,84-92]

Execution browser smoke: start the existing example, create/update an object to produce a real flash message,
confirm new marker and core scripts, click close and wait for Bootstrap transition completion. Repeat with a fresh
alert and a configured namespace lacking Alert; dynamically insert a further alert and close it without initializer.
Record actual observations, browser availability and any blockers. Do not add product UI solely for the smoke.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:50-60]
[CITED: https://getbootstrap.com/docs/5.3/components/alerts/]

### Sampling Rate

- Per task: relevant focused command; baseline comparison before its commit.
- After implementation: both focused commands and full JS suite.
- Phase gate: full Python/JS, strict docs, Ruff, data-attribute audit, golden-history review and example smoke.

[CITED: .planning/PROJECT.md, Constraints]
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:58-60]

### Wave 0 Gaps

- [ ] Add and commit before-change alert golden/test.
- [ ] Add adapter/delegation regressions in existing JS suites.
- [ ] Add/update explicit alert and real message render assertions.
- [ ] Resolve or explicitly disposition installed tool-version drift before shipping validation claims.
- [ ] Complete real example browser smoke during execution.

No new test framework installation is proposed.

## Security Domain

Security enforcement is enabled. Use ASVS 5.0 category names rather than old numbering in generic templates.
[CITED: .planning/config.json, workflow.security_enforcement]
[CITED: https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en]

| ASVS category | Applies | Control / boundary |
|---|---|---|
| V1 Encoding and Sanitization | Preserve | Existing escape/conditional_escape and hostile-content tests |
| V3 Web Frontend Security | Yes | External core script; fixed semantic selectors; no inline handler |
| V6 Authentication | No new behavior | Existing auth untouched |
| V7 Session Management | No new behavior | Existing messages/session untouched |
| V8 Authorization | No new behavior | Local DOM close adds no server access |
| V11 Cryptography | No new behavior | No secrets or crypto changes |

Scope and controls derive from current escaping helper and locked frontend-only change.
[VERIFIED: src/crud_views/lib/messages.py:35-54]
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:7-15,26-37,50-53]

| Threat | STRIDE | Mitigation |
|---|---|---|
| Message/attribute HTML injection | Tampering | Preserve server escaping tests |
| Removal of unrelated DOM | Tampering | Explicit control marker and nearest role frame |
| Hidden adapter failure | Diagnostic loss | Surface error without second close path |

These are scoped review checks, not a full ASVS certification claim.
[VERIFIED: src/crud_views/lib/messages.py:35-54]
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:32-37,50-53]

## Assumptions Log

No new product assumption is promoted to a locked decision. Proposed test organization and golden destination are
implementation choices; tool-version drift and browser smoke are disclosed validation gaps.
[VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:62-65]

| # | Claim | Section | Risk |
|---|---|---|---|
| — | No unverified product assumption | — | — |

## Open Questions

- Installed JS and Ruff versions differ from declarations; report or reconcile before claiming manifest-environment
  verification. Do not infer version incompatibility from this drift.
  [VERIFIED: session version probes] [VERIFIED: package.json:15-21] [VERIFIED: pyproject.toml:60-64]
- Interactive example dismissal is not yet observed; retain as execution acceptance.
  [VERIFIED: session example probes] [VERIFIED: .planning/phases/04-alert-dismiss-adapter/04-CONTEXT.md:58-60]

## Sources

- Local primary evidence: phase context, project/requirements/roadmap/state, CLAUDE.md, source-plan Phase 3A,
  concept-review F7, inspected adapter/viewset/frame/message sources, tests and public docs cited above.
- [Bootstrap alert documentation](https://getbootstrap.com/docs/5.3/components/alerts/) — API and data-API behavior.
- [Bootstrap v5.3.3 source](https://raw.githubusercontent.com/twbs/bootstrap/v5.3.3/js/src/alert.js) — cancellation/teardown.
- [MDN dispatchEvent](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/dispatchEvent) — listener exceptions.
- [ASVS 5.0 index](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en) — version-specific security categories.

## Metadata

Standard stack, architecture and pitfalls: MEDIUM under the official-web confidence seam; direct local facts are
individually source-read or command-tested. The seam returned MEDIUM for provider websearch with official verification.
No registry version/publish-date claim is made because there are no installs.
[VERIFIED: session classify-confidence output]

Research-plan seam used; Context7 unavailable, official web sources used. Digests cached from a temporary working
directory to confine repository edits to this artifact. Graph status reported no graph.
[VERIFIED: session research-plan, research-store, discovery and graph-status outputs]

Research date: 2026-10-26. Refresh when context, adapter harness or dependency declarations change.
No commit: orchestrator explicitly owns subsequent planning and commits.

