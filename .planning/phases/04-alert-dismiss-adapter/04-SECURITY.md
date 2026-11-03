---
phase: "04"
slug: alert-dismiss-adapter
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-26"
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Message/context data → rendered HTML | Heading, body, items and class attributes keep Django's output encoding | Flash message text, `extra_tags` |
| Document click → DOM removal | Only an explicit `data-cv-alert-dismiss` marker inside its nearest `role="alert"` frame reaches an adapter | DOM element reference |
| Theme/component adapter → core listener | Adapter errors and DOM changes stay owned by the adapter; core performs no recovery | Adapter exceptions, DOM mutations |
| Dynamic document content → frame selection | Controls inserted after load only target their nearest enclosing alert | DOM element reference |
| Documentation recipe → copied template | Published custom frame must keep escaped content and the semantic hooks | Template recipe |
| Upgrade guidance → deployed scripts/markup | Hook and core scripts must ship together; legacy behaviour documented accurately | Migration text |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-04-01 | Tampering | `alert.html` and message rendering | high | mitigate | Template diff only swaps `data-bs-dismiss="alert"` for `data-cv-alert-dismiss`; no new unescaped interpolation. `tests/test1/test_alerts.py::test_dismissible_alert_escapes_heading_text_and_extra_tags` plus existing escaping tests (`test_alert_data_escapes_*`, `test_cv_alert_escapes_with_autoescape_off`). | closed |
| T-04-02 | Tampering | `viewset.js` click dispatch | medium | mitigate | Fixed selectors `closest("[data-cv-alert-dismiss]")` → `closest('[role="alert"]')`; tracer in `tests/js/viewset.test.js` keeps the sibling; 04-02 adds orphan/non-Element/unmarked-body cases. | closed |
| T-04-03 | Tampering | `adapters.js` default and custom close path | medium | mitigate | `alert.close` falls back to `el.remove()` only when no `Alert` component exists; `tests/js/adapters.test.js` proves no-op retention, surfaced errors and retained prior mutations (12 fault injections caught, 04-02-SUMMARY). | closed |
| T-04-04 | Tampering | `viewset.js` dynamic/repeated dispatch | medium | mitigate | `tests/js/viewset.test.js` covers nearest nested frame, modal-like dynamic insertion, two controls, one call per attached event and detached-subtree boundary. | closed |
| T-04-05 | Tampering | `theme.md` custom frame recipe | high | mitigate | `tests/test1/test_alerts.py::test_documented_alert_frame_override` renders the published recipe with hostile content/`extra_tags` and asserts safe output (8 doc mutations caught, 04-03-SUMMARY). | closed |
| T-04-06 | Denial of Service | Copied close controls after upgrade | medium | mitigate | `docs/migrating-1.0.md` + CHANGELOG Breaking describe copied-template migration and post-load adapter replacement; browser acceptance A/B/C in `04-ACCEPTANCE.md`. | closed |
| T-04-SC | Tampering | Package installation | high | mitigate | No dependency manifest changed in the phase (`package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock` untouched since 1b77934); installed-tool drift disclosed, not fixed by install. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

## Accepted Risks Log

No accepted risks.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-26 | 7 | 7 | 0 | secure-phase orchestrator (L1 short-circuit; register authored at plan time) |

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-26
