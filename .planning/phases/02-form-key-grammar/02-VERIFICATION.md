---
phase: 02-form-key-grammar
verified: 2026-10-26T13:49:17Z
status: passed
score: 7/7 must-haves verified
covered_files: [
    ".planning/phases/02-form-key-grammar/02-01-PLAN.md",
    ".planning/phases/02-form-key-grammar/02-01-RED-count.json",
    ".planning/phases/02-form-key-grammar/02-01-RED-matrix.json",
    ".planning/phases/02-form-key-grammar/02-01-RED-tracer.json",
    ".planning/phases/02-form-key-grammar/02-01-SUMMARY.md",
    ".planning/phases/02-form-key-grammar/02-CONTEXT.md",
    ".planning/phases/02-form-key-grammar/02-REVIEW.md",
    ".planning/phases/02-form-key-grammar/02-REVIEWS.md",
    ".planning/phases/02-form-key-grammar/02-SECURITY.md",
    ".planning/phases/02-form-key-grammar/02-SOURCE-AUDIT.md",
    ".planning/phases/02-form-key-grammar/02-UAT.md",
    ".planning/phases/02-form-key-grammar/02-UI-REVIEW.md",
    ".planning/phases/02-form-key-grammar/02-VALIDATION.md",
    ".planning/phases/02-form-key-grammar/deferred-items.md",
    "CHANGELOG.md",
    "docs/reference/buttons.md",
    "src/crud_views/checks.py",
    "src/crud_views/lib/button_classes.py",
    "src/crud_views/lib/crispy/buttons.py",
    "src/crud_views/lib/settings.py",
    "src/crud_views/lib/view/button_data.py",
    "src/crud_views/lib/view/label_mode.py",
    "src/crud_views/lib/view/variant.py",
    "src/crud_views/templatetags/crud_views.py",
    "src/crud_views_object_detail/templatetags/crud_views_object_detail.py",
    "tests/test1/test_action_label_mode_config.py",
    "tests/test1/test_action_menus_golden.py",
    "tests/test1/test_button_classes.py",
    "tests/test1/test_button_classes_checks.py",
    "tests/test1/test_button_classes_templates.py",
    "tests/test1/test_crispy_buttons.py",
    "tests/test1/test_label_mode.py",
    "tests/test1/test_label_mode_docs.py"
  ]
covered_digest: "v3:sha256:3276b016eefc254197bb9a55733e5dadb45bb2312cee1e286334c93ed191fc1f"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 11
  total: 11
  not_honored: []
flagged_assumptions:
  - requirement_id: KEYS-01
    category: unclassified
    status: unresolved
    flagged: true
    disposition: "Source-probe classifier limitation remains unresolved; documentation acceptance independently verified and human UAT passed."
  - requirement_id: KEYS-02
    category: unclassified
    status: unresolved
    flagged: true
    disposition: "Source-probe classifier limitation remains unresolved; finite grammar independently inspected and exercised by explicit tests."
---

# Phase 02: Form key grammar Verification Report

**Phase Goal:** The class table has one documented, check-enforced rule for what the second key segment means and which keys take a mode, so form buttons can get mode keys without loosening W362.

**Verified:** 2026-10-26T13:49:17Z  
**Status:** passed  
**Re-verification:** No — initial verification; no previous Phase 02 VERIFICATION.md existed.

## Goal Achievement

All four roadmap success criteria and all seven detailed plan truths are verified. The roadmap requirements are retained verbatim below, with plan detail merged into their supporting truths rather than reducing scope. The score counts the seven detailed truths once.

### Roadmap Contract

| # | Success criterion | Status | Supporting truths and evidence |
|---|---|---|---|
| 1 | `docs/reference/buttons.md#the-class-table` states the chosen grammar: the meanings of the second segment and which of them take a mode. | VERIFIED | Truth 5; actual grammar table and explanatory examples at buttons.md:47–86; completed human prose UAT. |
| 2 | W362 accepts form mode keys of the chosen shape and rejects malformed ones such as `form:submitt:icon` and `form:container:icon`. | VERIFIED | Truths 1, 2 and 4; real registered check API, independent acceptance/rejection matrices, exact diagnostic assertions. |
| 3 | The location sets are split explicitly (e.g. `VARIANT_LOCATIONS`, `FORM_KINDS`), so adding `"form"` to the button-data locations cannot make W362 accept `form:<variant>:<mode>`. | VERIFIED | Truth 3; immutable independent sets at button_classes.py:207–208 and future-location test at test_button_classes_checks.py:228. |
| 4 | The key count quoted in `buttons.md` is correct, and a test fails whenever it drifts from `len(DEFAULT_BUTTON_CLASSES)`. There is no runtime or golden change. | VERIFIED | Truths 6 and 7; live 70-key equality plus verifier-executed missing/duplicate/±1 sensitivity checks; complete product diff preserves resolver, defaults, crispy, templates and goldens. “No runtime change” refers to existing lookup/rendering, consistent with the intended validator extension. |

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | All five form kinds accept icon, both and label through theme registration and settings, without requiring an icon. | VERIFIED | button_classes.py:207–234 recognizes exactly five kinds and shared LABEL_MODES; no icon lookup in recognition. test_all_form_kind_modes_are_accepted_without_icons has 30 independent literal kind/mode/source cases, and test_form_mode_none_and_empty_values_are_valid adds 60 cases. Included in the fresh 528-test review run. |
| 2 | Unknown kinds, variants under form, structural/utility suffixes and malformed segment counts retain unknown-key W362; recognized kinds with invalid/empty modes retain unknown-mode W362. None/empty settings add no overrides; non-string keys warn safely. | VERIFIED | Shape and mode remain distinct stages; unchanged warning branches at button_classes.py:280 onward. test_unknown_shapes_retain_exact_warning, test_known_form_kind_with_bad_mode_retains_exact_warning, test_none_or_empty_settings_add_no_overrides and E361-only tests assert exact classes, IDs, messages, hints and results through check_button_classes. Fresh review run passed. |
| 3 | Class-key variant locations are exactly context/list/card, independent of button-data LOCATIONS. Widening button-data locations cannot admit form/new-location variants. E108 and LABEL_MODE_DEFAULTS retain their separate location contract and reject form floors. | VERIFIED | No button_data import in _action_key_parts. test_class_key_vocabularies_are_finite_and_immutable and test_future_button_data_locations_cannot_widen_class_key_grammar prove both sources. settings.py:105,158 reads button_data.LOCATIONS; label_mode.py:93–99 uses the same location set. Existing floor equality, invalid form floor and dynamic E108-location tests passed in fresh review/regression runs. |
| 4 | Mode presence overrides base even for None/empty values; absent mode falls back once. Settings win the same exact key, theme mode beats settings base, and invalid-mode hints stay sorted regardless of registration order. | VERIFIED | Unchanged get_button_classes/get_button_class at button_classes.py:127–147 merge by exact key then test membership. Independently ran test_form_theme_mode_beats_settings_base_and_settings_wins_same_key: 1 passed in 0.04s, including settings-context enter/exit transitions. Suppression, all-kind fallback and order-independence tests also passed in the fresh 528-test review run. |
| 5 | The canonical class-table anchor contains the variant/kind/structural grammar table, required valid/invalid examples, form fallback example and accurate unchanged crispy-rendering explanation. | VERIFIED | Read buttons.md:47–86 and W362 reference at :238–241; all examples match the actual two-stage parser and resolver. Crispy buttons.py:16–17 supplies only location/slot. User explicitly passed the deferred prose checkpoint in 02-UAT.md, including disclosure of the two unresolved classifier limitations. |
| 6 | Exactly one canonical decimal count is parsed as an integer and compared with len(DEFAULT_BUTTON_CLASSES), currently 70; missing/duplicate/±1 claims fail, with no fixed-count substitute, rounding or mode-combination count. | VERIFIED | Actual test at test_button_classes.py:94–98 uses re.findall, exactly-one assertion and int equality to live len. Verifier invoked that actual function body against the live document and four in-memory mutations: live passes; all mutations raise AssertionError. Docs explicitly exclude addressable mode combinations at buttons.md:144–148. |
| 7 | Shipped defaults, crispy slots, rendering, escaping, templates and goldens remain unchanged; bare-settings import works and the compatible grammar extension has an Unreleased changelog entry. | VERIFIED | Inspected complete base-to-HEAD source diff: only two new constants, shape membership and docstrings change in production. DEFAULT_BUTTON_CLASSES/get_button_class and rendering files have no diff. Fresh review's 528 tests include escaping/crispy/template/golden regressions and its fresh bare-settings interpreter import passed. CHANGELOG.md:187 adds the compatible extension under Added, with no new Breaking entry. |

**Score:** 7/7 truths verified; 0 present but behavior-unverified. No override was needed. No coincidental-reliance item was identified: fixtures supply the same settings/theme inputs as production, and cache invalidation and precedence are implemented by the production code.

### Required Artifacts

The installed artifact verifier returned exit 0, 5/5 substantive artifacts. Manual reads additionally established their use.

| Artifact | Expected | Status | Details |
|---|---|---|---|
| src/crud_views/lib/button_classes.py | Independent finite sets; two-stage validation | VERIFIED | Both frozensets feed _action_key_parts, then LABEL_MODES membership; called by the registered Django check. |
| tests/test1/test_button_classes_checks.py | Real API tracer and boundary/diagnostic matrices | VERIFIED | Imports check_button_classes, exercises both sources, asserts independent expected vocabularies and exact W362 behavior; collected and run by pytest. |
| tests/test1/test_button_classes.py | Fallback/precedence and live documentation-count guard | VERIFIED | Actual config transitions and output values; count guard reads repository documentation. Named precedence and count-sensitivity checks independently executed. |
| docs/reference/buttons.md | Canonical grammar and correct shipped-key count | VERIFIED | Existing class-table anchor retained; examples agree with source; count is consumed by the test; human prose check passed. |
| CHANGELOG.md | Compatible extension release note | VERIFIED | Unreleased Added entry documents both sources, all kinds/modes, unchanged diagnostics and rendering. |

### Key Link Verification

The installed key-link verifier returned exit 0, 4/4 links. Manual tracing confirms actual calls rather than imports alone.

| From | To | Via | Status | Details |
|---|---|---|---|---|
| checks.py:405 | button_classes.py | Registered check delegates to button_class_check_messages | WIRED | Function returns validator messages directly. |
| button_classes.py:217 | view/variant.py | Function-local VARIANTS import | WIRED | Membership used only when location belongs to independent VARIANT_LOCATIONS. |
| button_classes.py:231 | view/label_mode.py | Function-local LABEL_MODES import | WIRED | Shared modes validate recognized shape; sorted vocabulary supplies W362 hint. |
| test_button_classes.py:94 | docs/reference/buttons.md | Repository-relative Path read | WIRED | Parsed decimal compared to live DEFAULT_BUTTON_CLASSES size; mutation check demonstrates sensitivity. |

### Data-Flow Trace (Level 4)

No new dynamic renderer or database API was introduced. The relevant existing configuration-to-output path was still traced.

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| get_button_classes | merged classes | Defaults → registered theme → Django settings | Yes; real settings and registration values, cached and invalidated on setting_changed/registration | FLOWING |
| get_button_class / cv_button_class | selected CSS class string | Exact mode key if present, otherwise base key | Yes; both template-tag libraries return resolver output through autoescaped simple tags | FLOWING |
| Crispy _TableClassMixin | field_classes | Existing form slot through get_button_class | Yes; base slot remains intentionally mode-less in this phase | FLOWING |

Empty registry/cache initializers and empty-string suppression are intentional, populated or consumed by real code; they are not rendering stubs.

### Behavioral Spot-Checks

Fresh verifier checks supplement the orchestrator-authorized recent evidence; the full suite was not rerun.

| Behavior | Command/evidence | Result | Status |
|---|---|---|---|
| Settings/theme transitions preserve mode specificity and exact-key precedence | `.venv/bin/pytest tests/test1/test_button_classes.py::test_form_theme_mode_beats_settings_base_and_settings_wins_same_key -q -p no:cacheprovider` | Exit 0; 1 passed in 0.04s | PASS |
| Actual count guard rejects missing/duplicate/off-by-one claims | `.venv/bin/python -c '<count sensitivity program below>'` | Exit 0; live document passed; missing, duplicate, below, above each rejected | PASS |
| Complete relevant grammar/floor/rendering coverage | Fresh independent deep-review command recorded in 02-REVIEW.md: eight named modules, including both changed tests | 528 passed in 3.33s on Python 3.12.3 / Django 5.2.14 | PASS — reused review evidence |
| Import compatibility | Fresh independent review: bare settings.configure() then import crud_views.lib.button_classes | Exit 0 | PASS — reused review evidence |
| Prior-phase regression and JavaScript preservation | Orchestrator's current-turn 12-module regression and npm test | 531 passed in 20.27s; 126 JS tests across 8 files passed in 4.48s | PASS — supplied current-run evidence |

The 528-test command was:
`.venv/bin/pytest tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes_templates.py tests/test1/test_crispy_buttons.py tests/test1/test_action_menus_golden.py tests/test1/test_label_mode_docs.py -q`.

The count-sensitivity program below was executed in its own process, performs no file mutation and compiles the actual repository test function rather than recreating its assertions:

```python
import ast, pathlib, re
source = pathlib.Path("tests/test1/test_button_classes.py").read_text()
tree = ast.parse(source)
target = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "test_documented_default_key_count_matches_table")
from django.conf import settings
settings.configure()
from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES
document = pathlib.Path("docs/reference/buttons.md").read_text()
class FakePath:
    def __init__(self, *args): pass
    def resolve(self): return self
    @property
    def parents(self): return [self] * 3
    def __truediv__(self, other): return self
    def read_text(self): return current
namespace = {"Path": FakePath, "re": re, "__file__": "unused", "DEFAULT_BUTTON_CLASSES": DEFAULT_BUTTON_CLASSES}
exec(compile(ast.Module(body=[target], type_ignores=[]), "<actual-count-guard>", "exec"), namespace)
current = document
namespace[target.name]()
print("actual count guard: live document PASS")
count = len(DEFAULT_BUTTON_CLASSES)
claim = f"The default table has {count} keys"
cases = {"missing": document.replace(claim, "No canonical count"), "duplicate": document + "\n" + claim, "below": document.replace(claim, f"The default table has {count-1} keys"), "above": document.replace(claim, f"The default table has {count+1} keys")}
for label, current in cases.items():
    try: namespace[target.name]()
    except AssertionError: print(f"actual count guard: {label} correctly rejected")
    else: raise AssertionError(f"{label} incorrectly accepted")

```

### Probe Execution

No phase-declared `probe-*.sh` path or conventional `scripts/*/tests/probe-*.sh` exists. The two scripts present are screenshot/server utilities and are unrelated. Source-audit “probe” rows describe planning classification, not runnable project probes. The retrospective RED records remain historical evidence; their PASS/RED markers were not substituted for current verification. The live count-sensitivity probe was independently executed above.

### Requirements Coverage

| Requirement | Source plan | Description | Status | Evidence |
|---|---|---|---|---|
| KEYS-01 | 02-01 | Maintainer selects grammar and documents canonical rule | SATISFIED | D-01 chooses Option A; actual docs agree with implementation; completed human UAT. |
| KEYS-02 | 02-01 | W362 accepts form modes and rejects malformed keys | SATISFIED | Truths 1–2; exact check-API matrix and shared mode vocabulary. |
| KEYS-03 | 02-01 | Explicit grammar sets independent of button-data locations | SATISFIED | Truth 3; immutable sets and both-source future-location test. |
| KEYS-04 | 02-01 | Parsed documentation count equals actual default table size | SATISFIED | Truth 6; actual count test and verifier-executed sensitivity probe. |

All four Phase 2 traceability IDs are declared in the plan. No orphaned Phase 2 requirement exists. Source-probe classification and requirement satisfaction are separate: the two flagged assumptions remain unresolved classifier limitations, not green automated probe findings.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts.

Installed decision-coverage gate: 11/11 honored, no unhonored decisions, exit 0. This gate is advisory; code and tests supplied the acceptance evidence.

### Test Quality Audit

| Test file | Linked requirements | Active | Skipped | Circular | Assertion level | Verdict |
|---|---|---|---|---|---|---|
| test_button_classes_checks.py | KEYS-02, KEYS-03 | Yes; 30 explicit kind/mode/source acceptance combinations plus rejection, value and boundary matrices | None | No | Exact values/diagnostics and configuration behavior | PASS |
| test_button_classes.py | KEYS-04; KEYS-02/03 preservation | Yes | None | No | Live independent document count, value and multi-step precedence assertions | PASS |
| test_label_mode.py / test_action_label_mode_config.py | KEYS-03 preservation | Yes in fresh review/regression run | None affecting this contract | No | Floor equality, dynamic locations, exact E108 and resolution behavior | PASS |
| Template/crispy/golden/docs regression modules | No-render-change constraint | Yes in fresh review run | None affecting this contract | No newly generated expectations | Rendered values and existing goldens | PASS |

Changed tests use literal expected kind/mode/variant vocabularies, not the production allow-lists as their oracle. The live count test intentionally compares independently authored documentation with production data. No changed test is disabled or writes generated expected fixtures. The pre-existing golden helper writes expectations only when CV_UPDATE_GOLDEN=1; unchanged historical goldens are the regression oracle, and the phase diff shows none were regenerated.

Adversarial disconfirmation checked three likely failure paths: variants admitted through widened button-data locations, None/empty mode values falling through incorrectly, and a count guard passing stale prose. Existing assertions and the independent count probe falsified each concern. No partially met requirement or misleading assertion was found in this scope.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| CHANGELOG.md | 1050, 1181 | Historical TODO/placeholder text describing earlier cleanup | INFO | Release history only; not live implementation debt. |
| button_classes.py | 111–119, 147 | Empty registry, cache sentinel and empty-string suppression | INFO | Real registration/settings paths populate state; suppression is required behavior. |

No unreferenced TBD/FIXME/XXX marker, stub, orphaned artifact or unwired key link was found in the five phase files.

### Human Verification Required

None outstanding. The deferred plan prose check was completed with the user's explicit “pass” in 02-UAT.md, including the two source-probe limitations. There is no new visual surface or unexercised state-transition invariant requiring another checkpoint. No visual certification of existing screens is implied.

### Existing Limits and Hook Results

- **Two unresolved classifier limitations:** KEYS-01 and KEYS-02 source-probe rows remain flagged in the plan, source audit, validation and this report. Their disclosure was included in the completed user checkpoint. They do not represent failed implementation requirements or test-tier prohibitions; the plan declares no prohibitions.
- **Environment scope:** Current fresh Python evidence is Python 3.12.3 / Django 5.2.14. Other matrix combinations were not verified here. Historical full-suite evidence includes a Django 6-only CSP skip; this report does not claim that path passed.
- **Ruff:** Recorded installed version 0.16.10 is outside the manifest's >=0.17,<0.18 range. Recorded lint/product-format success is not a manifest-aligned Ruff gate. Seven pre-existing planning Markdown formatting findings remain documented in deferred-items.md. No installs or dependency changes were made.
- **Other gates:** Security records 4/4 scoped mitigations closed at ASVS L1; code review is clean; Nyquist validation is compliant/validated; UI audit is N/A because no rendering surface changed. These support scope assessment but do not replace the inspected implementation evidence.
- The SUMMARY's historical full-suite, strict-docs and formatter counts are not treated as fresh verifier executions.

### Gaps Summary

No blocking implementation gaps. The full roadmap was checked; form-mode rendering, form label floors and new form utility slots belong explicitly to Phase 6 and are not Phase 02 omissions. No failed Phase 02 truth was deferred to obtain a pass.

The only written file is this verification report. No implementation, other planning artifact or commit was changed.

---

_Verified: 2026-10-26T13:49:17Z_  
_Verifier: the agent (gsd-verifier)_
