# Phase 03: Filter toggle label mode - Research

**Researched:** 2026-10-26
**Domain:** Django context-button rendering, icon placement, disclosure interaction, localization
**Confidence:** MEDIUM overall; concrete repository findings are tool-verified below.

<user_constraints>
## User Constraints (from CONTEXT.md)

The following blocks reproduce the phase decisions verbatim. [VERIFIED: .planning/phases/03-filter-toggle-label-mode/03-CONTEXT.md]

<!-- DATA_m8Kp2xQ4_START -->
### Locked Decisions

### Default inheritance
- **D-01:** The filter toggle has no target view. Do not use the current list view's singular
  `cv_context_action_label_mode` as a target default. Resolve through the existing context chain without a
  target-default argument: the view's own per-key map, button override, resolved ViewSet/settings map,
  then the context floor. Preserve existing whole-map replacement semantics.
- **D-02:** Resolve using the button's declared key, not a hard-coded `filter` key.
  `FilterContextButton(key="search")` uses the `search` entry; the default instance still uses `filter`.
  Use the existing `cv_get_action_label_mode()` resolver and preserve its precedence.

### Icon placement and modes
- **D-03:** In `both` mode retain the existing placement rule. When both open/close icons provide usable host
  classes, place the active classes on the button and swap them on toggle. Otherwise render child icons
  and switch their visibility. Mixed placements use child icons, including the existing standalone rendering
  of a host-configured icon. Do not introduce a rule that always forces child icons in `both` mode.
- **D-04:** The visible label stays constant while toggling; only the icon and expanded state change.
  This applies to custom labels as well as the default `Filter` label.
- **D-05 (carried from requirements):** `icon` retains the current hidden accessible label, title, tooltip,
  and icon behavior. With default configuration its markup remains byte-identical to the existing
  `toolbar_publisher_list.html` golden. `both` shows icon plus visible label without a title; follow the
  existing action-button convention of no tooltip marker when a visible label is present.
- **D-06 (carried from source plan):** `label` renders visible text without icon spans, host icon classes,
  or open/close icon data attributes. It still toggles the panel, updates `aria-expanded`, and persists state.
  Preserve the existing failure behavior: a collapse adapter that throws or returns false changes no state;
  a failed persistence request does not undo a successful toggle.

### Customization and documentation
- **D-07:** Preserve existing label templates, variants, and whole-button template overrides. Custom templates
  receive resolved `cv_label_mode` and control their own markup. No new precedence or customization API is needed.
- **D-08:** Add a compact contract with examples, not a full custom-template walkthrough. Show filter mode
  configuration, explain the absence of a target-view default, and document all three modes and optional icon
  hooks. Link to the canonical resolution order instead of duplicating it. Correct documentation that currently
  describes the bundled filter toggle as icon-only by construction.
- **D-09 (carried from requirements):** Translate the default `Filter` msgid and update the German catalog.
  Existing custom label templates continue to override the default label.

### Carried-forward constraints
- **D-10:** Keep no-filter and pinned-filter visibility behavior, DOM IDs, collapse integration, persistence,
  and reset behavior unchanged. This phase changes label-mode support, not filtering semantics.
- **D-11:** Record the public behavior change in CHANGELOG.md. Any Breaking entry also requires a matching
  update in docs/migrating-1.0.md. Preserve the project quality gates and unchanged default goldens.

### Agent's Discretion

- No product choice was explicitly delegated. Exact helper placement, test organization, template whitespace
  management, and documentation wording remain implementation details within these decisions.
- Verify whether JavaScript needs a functional change: its current icon loop already tolerates no matches.
  Add meaningful regression coverage without requiring a needless rewrite.

### Deferred Ideas (OUT OF SCOPE)

None added. Always using child icons in both mode and a full custom-template walkthrough were rejected,
not deferred. Downstream theme implementation remains outside this repository; record any follow-up in acceptance.
<!-- DATA_m8Kp2xQ4_END -->
</user_constraints>

## Project Constraints (from AGENTS.md)

The user supplied the repository instructions, also present in CLAUDE.md. Apply these actionable constraints:
[VERIFIED: CLAUDE.md; user-provided AGENTS.md instructions]

- Use the existing ViewSet/CrudView architecture and permission conventions; CrudView attributes use the cv_ prefix.
- Keep view keys and permission mappings consistent; workflow methods retain their wf_ prefix if touched.
- Keep fixtures consistent with the existing ViewSet, user, and authenticated-client naming conventions.
- Use 120-character lines, double quotes, Ruff formatting, and the existing commit formatting hook.
- Keep the hatchling build and synchronized bump-my-version version workflow; this phase needs no version bump.
- Use existing pytest/nox, JavaScript, documentation, lint and formatting workflows.
- Record public behavior changes in CHANGELOG.md. A new Breaking entry requires a companion migration-guide update.

Additional project gates are stated verbatim: "pytest tests -n auto", "vitest", "mkdocs build --strict",
"ruff check", "ruff format --check"; source hygiene includes "No downstream project names in any file".
Use generic wording for the downstream theme acceptance follow-up. [VERIFIED: .planning/PROJECT.md:71-84]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FILT-01 | Configured both renders icon and Filter without title; label renders text only; default icon golden unchanged | Resolver call, placement decision table, class-mode lookup, raw compatibility guard |
| FILT-02 | Icon-less toggle still updates expanded state and persists | Existing empty icon loop plus focused JS regression |
| FILT-03 | Text stays constant; expanded state and icons change | Visible-label identity assertions over two clicks and both starting states |
| FILT-04 | Filter is translated and German catalog updated | Runtime gettext, PO/MO catalog update, anti-false-positive translation tests |

Requirement descriptions above summarize the supplied requirements. [VERIFIED: .planning/REQUIREMENTS.md:34-39]
</phase_requirements>

## Summary

This is a small extension of an existing rendering contract. The filter context builder seeds its own label, key,
and icon; the generic context wrapper can already stamp a resolved mode. The filter template ignores that mode
and hard-codes icon presentation. Stamp the mode directly in the filter builder as well, using the declared button
key and the existing resolver without a target default. This also makes direct builder calls and custom label
templates consistent. [VERIFIED: src/crud_views/lib/view/buttons.py:298-334;
src/crud_views/lib/view/base.py:299-328,624-646]

Keep the specialized template and the existing host-versus-child decision. In label-only mode omit all icon
markup and host swap hooks. JavaScript already has a harmless empty selector loop and performs collapse before
state mutation, followed by a persistence request whose failure is ignored. New tests, rather than a required
JavaScript rewrite, should establish these contracts. [VERIFIED: src/crud_views/static/crud_views/js/list.filter.js:6-38]

**Primary recommendation:** implement context + template + localization in one cohesive slice, add Python and
JavaScript behavior tests, then correct the compact documentation contract and run existing quality gates.
This is a planning recommendation derived from D-01 through D-11.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Resolve mode and translated default label | Frontend server / Django context builder | Existing configuration resolver | Render-time decisions belong beside the button context |
| Mode-specific markup and icon placement | Frontend server / Django template | Icon and button-class registries | Reuse server-rendered icon hooks |
| Collapse, state changes, icon swaps | Browser / Client | Existing collapse adapter | User interaction is already delegated through that adapter |
| Persist expanded state | Existing backend endpoint | Browser POST | Preserve current request and error contract |
| Catalog compilation | Build/development tooling | Django translation loader | Ship the translated compiled catalog |

Tier assignments are recommendations based on the inspected context builder and browser handler.
[VERIFIED: src/crud_views/lib/view/buttons.py:308-334;
src/crud_views/static/crud_views/js/list.filter.js:1-38]

## Standard Stack

Retain the installed project stack; **no new packages or dependency upgrades are required by this phase**.
This is an implementation recommendation, not a claim that installed versions satisfy every manifest constraint.

| Component | Observed local version | Role |
|-----------|------------------------|------|
| Python / Django | 3.12.3 / 5.2.14 | Context builder, templates, localization |
| Pydantic | 2.13.4 | Existing context-button model |
| pytest / pytest-django | 9.1.1 / 4.14.0 | Python rendering and integration tests |
| Vitest / jsdom | 4.1.10 / 29.1.1 | Existing browser test harness |
| polib / GNU gettext | 1.2.0 / 0.21 | Catalog assertions and compilation |
| MkDocs | 1.6.1 | Documentation gate |

Versions were measured using Python importlib.metadata, Node package metadata, and CLI version probes.
[VERIFIED: environment probes, 2026-10-26]

Manifest quotations: "django (>=4.2.0)", "pydantic (>=2.2.1)", "ruff>=0.17,<0.18";
"vitest": "^5.0.3", "jsdom": "^30.1.2". Installed Ruff is 0.16.10, below its declared range;
installed Vitest and jsdom are also older than the declared ranges. Existing focused tests nevertheless pass;
do not claim lockfile reproducibility or full supported-matrix validation from this run.
[VERIFIED: pyproject.toml:26-34,60-80; package.json:18-22; environment probes]

**Installation:** none for phase scope. Package legitimacy audit and latest-registry/publish-date research are
inapplicable because no external package installation or version selection is recommended.

## Architecture Patterns

### System Architecture Diagram

~~~mermaid
flowchart TD
    A[Page request and current language] --> B{Filter available and not pinned?}
    B -->|No| C[No toggle]
    B -->|Yes| D[Resolve declared key mode and translate default label]
    D --> E[Apply existing label variant and whole-template overrides]
    E --> F{Resolved presentation}
    F -->|Label| G[Visible text without icon hooks]
    F -->|Icon or both| H{Both host classes usable?}
    H -->|Yes| I[Host class and swap data]
    H -->|No| J[Child icons including standalone mixed placement]
    G --> K[Button with existing IDs and expanded state]
    I --> K
    J --> K
    K --> L[Click invokes collapse adapter]
    L --> M{Adapter succeeds?}
    M -->|No| N[Leave state untouched]
    M -->|Yes| O[Update expanded state and optional icons]
    O --> P[POST state through existing backend]
    P --> Q[Keep successful toggle even if persistence fails]
~~~

This is a recommended extension of the current server/client flow, with failure handling verified in the existing
script. [VERIFIED: src/crud_views/lib/view/buttons.py:308-334;
src/crud_views/static/crud_views/js/list.filter.js:6-38]

### Component Responsibilities

File references below identify files inspected in this session, not new filesystem-layout proposals.

| Component | Recommended work |
|-----------|------------------|
| src/crud_views/lib/view/buttons.py | Translate seeded label; stamp resolved mode using self.key and self |
| src/crud_views/templates/crud_views/tags/context_action_filter.html | Three presentation modes; retain existing icon placement and default bytes |
| src/crud_views/static/crud_views/js/list.filter.js | Leave functional behavior unless regression tests expose a gap |
| tests/test1/test_context_button_template.py and a focused filter-mode test module | Direct context, custom templates, precedence, rendered matrix |
| tests/js/list.filter.test.js | Icon-less and constant-label cases including failure semantics |
| tests/test1/test_i18n.py and core German catalog | Extracted msgid, compiled translation and rendering |
| Context-buttons, action-menus, buttons and JavaScript reference pages | Compact contract, examples and corrected claims |
| CHANGELOG.md | Public behavior entry; migration companion only if adding Breaking |

### Pattern 1: Resolve with declared key and no target default

The resolver returns the view's own named entry, then the supplied button mode, then the selected whole map, then
the optional target default or live context floor. Supplying self preserves a directly instantiated button's override
even if it is not discoverable from the view's registered buttons. [VERIFIED:
src/crud_views/lib/view/base.py:299-328]

The outer cv_get_context wrapper already stamps the mode, so avoid changing its generic behavior. The specialized
builder must itself provide the mode before invoking custom label rendering; the current label renderer receives
the builder's data. [VERIFIED: src/crud_views/lib/view/base.py:640-646;
src/crud_views/lib/view/buttons.py:55-72,323-332]

Verbatim resolver evidence:
<!-- DATA_b3Vq7Hn9_START -->
~~~python
if button is not None and button.label_mode is not None:
    return button.label_mode
mapping = cls.cv_get_context_actions_label_mode()
if key in mapping:
    return mapping[key]
return target_default or default_label_mode("context")
~~~
<!-- DATA_b3Vq7Hn9_END -->
[VERIFIED: src/crud_views/lib/view/base.py:317-322]

### Pattern 2: Keep icon placement independent of visible text

Mode vocabulary is defined verbatim as LABEL = "label", ICON = "icon", BOTH = "both".
[VERIFIED: src/crud_views/lib/view/label_mode.py:12-20]

| Mode | Usable host classes for both icons | Child icons | Label | Title/tooltip marker |
|------|------------------------------------|-------------|-------|----------------------|
| icon | Active host class and both swap data attributes | Only when host test fails | Hidden accessible span | Present |
| both | Same host behavior | Same fallback, including mixed placement | Visible and constant | Absent |
| label | No host classes or swap data | None | Visible and constant | Absent |

This table implements locked D-03 through D-06. The existing host decision is literally
"if cv_open_class and cv_close_class"; fallback is "if not cv_open_class or not cv_close_class".
[VERIFIED: src/crud_views/templates/crud_views/tags/context_action_filter.html:3,9-13]

Pass the resolved mode to cv_button_class, preserving the existing secondary variant fallback. Do not route this
button through cv_button_data: its two-state icons and no-target semantics are already specialized.
The tag delegates directly to get_button_class(location, slot, mode).
[VERIFIED: src/crud_views/templatetags/crud_views.py:524-527]

Also test host slots configured empty or None: the current filter fallback intentionally renders standalone
children when host classes are unusable. [VERIFIED: docs/reference/buttons.md:218-222;
src/crud_views/templates/crud_views/tags/context_action_filter.html:1-13]

### Pattern 3: Translate only the seeded default

Call Django gettext at get_context execution time, then retain _apply_label, _apply_variant and _inject_template.
The current seed is literally data["cv_action_label"] = "Filter"; the existing hooks follow immediately.
[VERIFIED: src/crud_views/lib/view/buttons.py:323-332]

Runtime gettext and catalog extraction/compilation are the existing framework facilities.
[CITED: https://docs.djangoproject.com/en/5.2/topics/i18n/translation/]

### Anti-Patterns to Avoid

- Do not hard-code the configured key or borrow the rendering list view's singular target default (D-01/D-02).
- Do not merge maps per entry; reuse the existing whole-map selection (D-01).
- Do not force child icons in both mode or leak host classes into label mode (D-03/D-06).
- Do not change the visible label on expansion or replace disclosure semantics with pressed-state semantics (D-04).
- Do not rewrite JavaScript merely to add a guard around an empty selector loop (Agent's Discretion).
- Do not regenerate the existing golden to make a markup regression pass (D-05/D-11).

## Don't Hand-Roll

| Problem | Use instead | Reason |
|---------|-------------|--------|
| Precedence, floor validation and fallback | Existing cv_get_action_label_mode | Retains whole-map semantics and lazy floor |
| Theme-specific icon rendering | cv_icon_class and cv_icon | Preserves host/element and standalone mixed rendering |
| Mode-specific classes | cv_button_class third argument | Existing registry handles mode fallback |
| Translation | Django gettext and catalog tooling | Existing active-language and compilation behavior |
| Collapse control | Existing cv.adapters.collapse | Preserves adapter failure semantics |

These recommendations reuse inspected components. [VERIFIED: src/crud_views/lib/view/base.py:299-328;
src/crud_views/templatetags/crud_views.py:512-527; src/crud_views/static/crud_views/js/list.filter.js:15-38]
Translation rationale: [CITED: https://docs.djangoproject.com/en/5.2/topics/i18n/translation/]

## Common Pitfalls

### 1. A passing golden is weaker than byte equality

The golden helper sorts attributes and class tokens and normalizes whitespace before comparing. Therefore its
passing result cannot prove raw template output equality. Verbatim evidence: "attrs = sorted(el.attrib.items())",
'value = " ".join(sorted(value.split()))', and 'return re.sub(r"\s+", " ", markup).strip()'.
[VERIFIED: tests/test1/test_action_menus_golden.py:38-55]

**Recommendation:** before editing the template, capture a raw direct-template baseline for default configuration,
at least collapsed and expanded. Keep an exact string assertion alongside the unchanged canonical toolbar golden.
Wrap new conditional tags around existing whitespace rather than reformatting the default branch. Do not use the
golden-update environment variable.

The canonical directory is created by "GOLDEN_DIR.mkdir(parents=True, exist_ok=True)" and populated by
'path.write_text(actual + "\n")'; its definition is 'Path(__file__).parent / "golden" / "action_menus"'.
The filter comparison names "toolbar_publisher_list".
[VERIFIED: tests/test1/test_action_menus_golden.py:32,77-82,132-135]

### 2. A German render can pass without translation

**Recommendation:** use the natural German catalog entry Filter → Filter, but do not rely only on equality of the
rendered word. Assert a non-fuzzy translated catalog entry, verify the compiled catalog contains it, and monkeypatch
the imported gettext callable to return a distinct sentinel in a direct builder test. Verify a custom label still
wins. The existing i18n tests already validate translated/fuzzy entries and compiled catalog loading.
[VERIFIED: tests/test1/test_i18n.py:65-81]

### 3. Direct template tests may omit the new mode

**Recommendation:** update new test helpers to pass a real resolved mode; do not silently invent a second mode
resolver in the template. Prefer the public builder for integration tests and explicit modes for template matrices.
The builder is the contract boundary in D-07.

### 4. Stale docs hide the new capability

The context-buttons reference currently calls the bundled filter "icon-only by construction"; the buttons reference
says it passes "icon"; action-menus says neither maps nor floors change it. Correct all three and the JavaScript
tooltip table/optional icon contract. Keep the never-folded rule: owning a whole-button template still makes the
filter special. [VERIFIED: docs/reference/context_buttons.md:77-82; docs/reference/buttons.md:304-306;
docs/reference/action_menus.md:168-184; docs/reference/javascript.md:83,187-202]

### 5. Existing broad floor tests deliberately exclude the filter

The Phase 1 integration selector is literally
'./*[@cv-key][not(@cv-key="filter") and not(@id="cv-filter-toggle")]'.
Do not treat those existing passes as filter coverage. Add dedicated filter-floor coverage and remove the obsolete
comment saying its mode is fixed, or intentionally extend those tests where their assertions fit.
[VERIFIED: tests/test1/test_context_action_label_mode.py:250-251]

## Code Examples

The following is a proposed insertion, not existing implementation. Its string values are quoted above from the
live mode/resolver/label sources. Import gettext using the project's usual translation alias.

~~~python
data["cv_label_mode"] = context.view.cv_get_action_label_mode("context", self.key, self)
data["cv_action_label"] = _("Filter")
self._apply_label(data, context)
self._apply_variant(data)
self._inject_template(data)
~~~

Resolver/context values are already present verbatim as "context", "cv_label_mode", "cv_action_label", and "Filter".
[VERIFIED: src/crud_views/lib/view/base.py:299-322,640-645; src/crud_views/lib/view/buttons.py:323-332]
The gettext API comes from official Django documentation.
[CITED: https://docs.djangoproject.com/en/5.2/topics/i18n/translation/]

Existing icon-less behavior needs no new special case:
<!-- DATA_h4Dq9Ln2_START -->
~~~javascript
button.querySelectorAll("[data-cv-filter-icon]").forEach((icon) => (icon.hidden = !icon.hidden));
~~~
<!-- DATA_h4Dq9Ln2_END -->
[VERIFIED: src/crud_views/static/crud_views/js/list.filter.js:29]

Recommended test reuse: the existing host fixture defines
"placement": "host", "standalone": "icon {name_class}", "filter": "ui:funnel", "filter-close": "ui:x".
Use that fixture rather than a new icon library; configure mixed directions by overriding just one icon.
[VERIFIED: tests/lib/helper/icons.py:3-13]

## State of the Art

| Topic | Current evidence | Planning consequence |
|-------|------------------|----------------------|
| Label-mode floors | Live context floor is reached only after named entries and optional target default | Reuse existing resolver rather than hard-coded icon |
| Browser interaction | Existing native DOM handler already tolerates empty icon collections | Add tests; avoid unnecessary framework or adapter changes |
| Accessible semantics | This is a disclosure with expanded/controls state | Preserve semantics and locked constant label |
| Security taxonomy | ASVS 5 uses V1 encoding and V3 web frontend categories | Do not label the older V2/V3/V4 authentication/session/access mapping as current |

Repository claims: [VERIFIED: src/crud_views/lib/view/base.py:299-328;
src/crud_views/static/crud_views/js/list.filter.js:1-38]
Standards: [CITED: https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/]
[CITED: https://asvs.owasp.org/]

The APG constant-label rule for an aria-pressed toggle is a different pattern from this disclosure. Keep the constant
label because D-04/FILT-03 require it, and retain aria-expanded; do not add aria-pressed.
[CITED: https://www.w3.org/WAI/ARIA/apg/patterns/button/]
[CITED: https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/]

## Environment Availability

| Dependency | Available | Observed | Planner action |
|------------|-----------|----------|----------------|
| Python project environment | Yes | Python 3.12.3, Django 5.2.14 | Run python -m pytest to use project interpreter |
| Node / npm | Yes | 20.20.2 / 10.8.2 | Existing focused JS test passes |
| GNU gettext msgfmt | Yes | 0.21 | Compile changed core catalog |
| uv / Task | Yes | 0.11.32 / 3.54.0 | Existing project tooling |
| MkDocs | Yes | 1.6.1 | Strict documentation build |
| Ruff | Present, manifest mismatch | 0.16.10 | Record existing mismatch; resolve environment if gate requires |
| Context7 MCP/CLI | Unavailable in this agent | No matching MCP tool; ctx7 absent | Official web documentation used |

[VERIFIED: tool discovery and environment probes, 2026-10-26]

The repository tracks compiled message catalogs, including the core German catalog, as confirmed by git ls-files.
The compilation task reads 'cmd: PYTHONPATH=.. python -m django compilemessages --settings=settings_i18n' under
'dir: src'. Update the core PO and compiled MO together; keep unrelated catalog churn out of the phase.
[VERIFIED: git ls-files '*django.mo'; taskfile.yaml:102-105]

**Missing blocking dependencies:** none demonstrated by the focused runs.
**Environment limits:** dependency-version mismatches are explicit above; no supported matrix was run.
**Baseline:** 49 Python tests passed in 3.35s across golden, template, host leaf, i18n, and pinned-filter modules;
13 JavaScript filter tests passed. [VERIFIED: focused pytest and npm test runs, 2026-10-26]

## Validation Architecture

Validation is enabled: "nyquist_validation": true. [VERIFIED: .planning/config.json:20-25]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-django 4.14.0; Vitest 4.1.10 + jsdom 29.1.1 observed |
| Config | Existing pyproject pytest options; existing vitest configuration |
| Quick Python command | python -m pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_i18n.py tests/test1/test_action_menus_golden.py -q |
| Quick JavaScript command | npm test -- tests/js/list.filter.test.js |
| Full suite | python -m pytest tests -n auto && npm test |
| Other project gates | mkdocs build --strict; ruff check; ruff format --check |

The dedicated filter test module in the quick command is **proposed Wave 0 work**, not an existing path.
Existing framework configuration: 'addopts = "--strict-markers"', 'environment: "jsdom"',
'include: ["tests/js/**/*.test.js"]', 'setupFiles: ["tests/js/helpers/setup.js"]'.
[VERIFIED: pyproject.toml:129-130; vitest.config.js:3-8; environment probes]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| FILT-01 | Modes, precedence, declared key, classes, customizations, default bytes | Python integration/template | python -m pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_action_menus_golden.py -q | Dedicated module proposed; golden exists |
| FILT-02 | Icon-less expanded state and POST; adapter/persistence errors | JS unit | npm test -- tests/js/list.filter.test.js | Yes; cases needed |
| FILT-03 | Default/custom visible labels unchanged across two toggles | JS unit + Python render | npm test -- tests/js/list.filter.test.js | Yes; cases needed |
| FILT-04 | Extracted and compiled German entry, gettext sentinel, custom override | Python integration | python -m pytest tests/test1/test_i18n.py tests/test1/test_filter_toggle_label_mode.py -q | Existing i18n; dedicated module proposed |

Commands and proposed tests are planning recommendations. Existing suite behavior was inspected and baseline-tested.
[VERIFIED: tests/js/list.filter.test.js; tests/test1/test_i18n.py; tests/test1/test_action_menus_golden.py]

### Required Coverage Matrix

- Presentation: all three modes × collapsed/expanded × element/host/mixed-open-host/mixed-close-host.
- Host fallback: empty/None host slot produces standalone children for icon-bearing modes, no icons for label mode.
- Resolver: own named map > button override > selected ViewSet/settings map > live floor; unrelated or empty view map
  replaces lower maps; own list singular default ignored; renamed declared key; direct button instance.
- Lazy behavior: override_settings changes the context floor; an explicit valid mode avoids reading an invalid strict
  floor. Use existing setting monkeypatch patterns for per-action maps.
- Customization: label template, label template code, variant mode classes, whole template and template-code override
  receive the resolved mode. No-filter and pinned-filter cases remain absent.
- Browser: icon-less button toggles twice from either starting state; host and element visible labels stay identical;
  throws/false adapter leaves state and requests unchanged; rejected POST keeps successful state.
- Localization: catalog entry and compiled entry, German active-language render, distinct gettext sentinel, custom label wins.
- Compatibility: unchanged existing golden plus exact raw default-template output.

This matrix implements D-01 through D-11 and FILT-01 through FILT-04; it is a test-design prescription, not a claim
that these cases already exist.

### Sampling Rate

- **Per task:** focused Python/JS commands relevant to the touched contract.
- **Per wave:** both focused suites plus unchanged toolbar golden and pinned-filter regression suite.
- **Phase gate:** full Python and JavaScript suites, strict docs, Ruff checks; record pre-existing tool/format blockers
  separately from new regressions.

### Wave 0 Gaps

- Add the dedicated Python filter-mode module (proposed path shown above).
- Capture raw pre-change default template output before implementation.
- Extend existing JS fixtures for label-only and visible-label variants.
- Add localization assertions that cannot pass merely because English and German spell Filter identically.
- No framework installation is needed for the observed environment.

## Security Domain

Security is enabled: "security_enforcement": true, "security_asvs_level": 1.
[VERIFIED: .planning/config.json:48-51]

### Applicable ASVS Categories

| ASVS 5 category | Applicability | Standard control / phase action |
|-----------------|---------------|---------------------------------|
| V1 Encoding and Sanitization | Relevant to label and attribute output | Keep Django escaping; do not introduce safe-marked user content |
| V3 Web Frontend Security | Relevant to persistence request and DOM handling | Preserve CSRF header, existing POST, safe class/state mutation |
| Authentication, sessions, access control | Existing boundaries; no new design in this phase | Preserve existing visibility and backend behavior |
| Cryptography | No new cryptographic operation in scoped design | Introduce none |

ASVS category names/control guidance verified against official V1/V3 documents; applicability is a scope assessment.
[CITED: https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x10-V1-Encoding-and-Sanitization.md]
[CITED: https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x12-V3-Web-Frontend-Security.md]

| Threat | STRIDE | Mitigation / regression check |
|--------|--------|-------------------------------|
| New label interpolation bypasses escaping | Tampering | Keep existing template interpolation and trusted-template boundary |
| Icon-less path drops persistence protections | Tampering | Assert unchanged POST header and JSON shape in JS tests |
| Failed collapse makes UI state disagree with panel | Tampering / integrity | Assert throw/false leaves state and persistence untouched |

The current request includes the literal header "X-CSRFToken" and the JSON key "filter_expanded".
[VERIFIED: src/crud_views/static/crud_views/js/list.filter.js:34-38]

## Assumptions Log

No unverified product decisions are proposed as locked requirements. Recommendations are explicitly identified.
The observed versions are environment facts, not claims of current registry releases or full compatibility.
No [ASSUMED] factual claims are used.

## Open Questions

1. **Release-note classification:** use a public behavior entry; if maintainers choose Breaking because configured
   filters now honor existing modes, add the migration companion. D-11 allows either classification with its rule.
2. **Strict raw compatibility fixture location:** choose a focused inline expected string or separate fixture;
   preserve raw bytes in either case. This is implementation discretion.
3. **Environment reproducibility:** manifest/test-run version drift exists. Focused tests pass with installed packages;
   final gates must report their actual tooling, without silently upgrading dependencies as phase scope.

No unresolved product decision blocks planning.

## Sources

### Primary repository evidence

- Phase 03 context, project, requirements, roadmap and state; Phase 01/02 contexts; source concept review and follow-up plan.
- Current filter builder/resolver/template/script, icon helpers and template tags.
- Existing context-mode, custom-template, pinned-filter, icon-host, golden and i18n tests.
- Current manifests, task definitions and German catalog.

All listed sources were opened in this session. Codebase maps were not treated as authoritative.
[VERIFIED: session file reads]

### Official documentation (MEDIUM confidence by research seam)

- https://docs.djangoproject.com/en/5.2/topics/i18n/translation/ — runtime translation and catalogs.
- https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/ — expanded/controls disclosure contract.
- https://www.w3.org/WAI/ARIA/apg/patterns/button/ — constant-name advice is about pressed toggles.
- https://asvs.owasp.org/ — current ASVS release.
- Official ASVS v5.0.0 V1 and V3 source documents linked above — output encoding and CSRF.

The research-plan seam selected Context7 for Django and websearch for standards; Context7 MCP and CLI were absent,
so official web documentation was used. The confidence seam returned MEDIUM for websearch with official verification.
Digests were cached under the research-plan keys. [VERIFIED: research-plan, tool discovery,
classify-confidence and research-store command outputs]

## Metadata

| Area | Level | Reason |
|------|-------|--------|
| Standard stack | MEDIUM | Installed stack inspected and tests pass; manifests differ from local environment |
| Architecture | MEDIUM | Official-source tier from seam; concrete implementation findings directly source-grounded |
| Pitfalls | MEDIUM | Golden normalization and no-icon behavior inspected; targeted baselines pass |

**Research date:** 2026-10-26
**Valid until:** recheck after relevant source changes; environment inventory is a point-in-time observation.
**Planning shape:** one implementation/test plan, followed by a compact docs/final-validation plan is sufficient.
