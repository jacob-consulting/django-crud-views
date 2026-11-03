---
phase: "02"
slug: form-key-grammar
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-26"
---

# Phase 02 — Security

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Theme/settings → validator | Developer configuration is validated safely | Class keys and values |
| Styling grammar → button-data vocabulary | Separate finite vocabularies | Location and kind names |
| Class strings → template tags | Existing escaping is retained | CSS class text |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-02-01 | Denial of service | Key parsing/checks | low | mitigate | `_action_key_parts` checks string type before splitting and requires three segments; non-string and malformed-key cases in `test_button_classes_checks.py` exercise the real checks. | closed |
| T-02-02 | Tampering | Allow-lists | low | mitigate | Immutable `VARIANT_LOCATIONS` and `FORM_KINDS`; `test_future_button_data_locations_cannot_widen_class_key_grammar` covers independent vocabularies. | closed |
| T-02-03 | Tampering | Class-string encoding | medium | mitigate | Phase diff changes no resolver or template/tag implementation; `test_tag_in_both_libraries_escapes` and rendering regressions passed in recorded execution evidence. | closed |
| T-02-SC | Tampering | Package installation | high | mitigate | No manifest/lock changes in phase diff; execution summary records no installed dependencies, and verification installs none. | closed |

## Accepted Risks Log

No accepted risks.

## Security Audit

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-26 | 4 | 4 | 0 | Codex orchestrator, ASVS L1 |

The plan contains an authored STRIDE register. All four mitigations were found by source/diff inspection;
the ASVS L1 short-circuit applies. Test results referenced here come from 02-01-SUMMARY.md, not a fresh run.
No threat flags appear in the execution summary. Scope is the four planned threats, not a package-wide security audit.

## Sign-Off

- [x] All threats have a disposition.
- [x] No accepted risks required.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set.

**Approval:** verified 2026-10-26
