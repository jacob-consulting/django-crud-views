---
phase: "03"
slug: filter-toggle-label-mode
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-26"
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Label/configuration → rendered DOM | Ordinary labels and class attributes cross Django's output-encoding boundary; project-owned templates keep their trusted status | Label text, CSS class strings |
| Browser → list persistence endpoint | Toggle sends session-changing JSON through the existing CSRF-protected path | `filter_expanded` boolean, CSRF token |
| Adapter result → local state | Failed/refused collapse must not claim success or emit persistence | Collapse/ARIA state |
| Documentation → consumer template | Advice could lead consumers to omit disclosure semantics or mishandle untrusted labels | Template recipes |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-03-01 | Tampering | Filter label/attribute interpolation | high | mitigate | Phase diff adds no `\|safe`, `mark_safe`, `format_html` or `autoescape off` under `src/`; `tests/test1/test_filter_toggle_label_mode.py` (T-03-01 block) asserts HTML-like labels render as escaped text. | closed |
| T-03-02 | Tampering | Filter state POST | high | mitigate | No endpoint/authorization change; `tests/js/list.filter.test.js` asserts request path, POST, `X-CSRFToken`, JSON content type and boolean `filter_expanded` body. `list.filter.js` unchanged. | closed |
| T-03-03 | Tampering | Collapse and ARIA state ordering | medium | mitigate | JS tests cover adapter throw/false before DOM/fetch, rejected persistence after success, and out-of-order outstanding requests without rollback; regression-sensitivity proven by three reverted fault injections (03-01-SUMMARY). | closed |
| T-03-04 | Information Disclosure | Non-filter/pinned context rendering | medium | mitigate | Early `cv_access: False` returns in `src/crud_views/lib/view/buttons.py` preserved; absence on no-filter/pinned pages covered by existing visibility/filter suites (full suite green). | closed |
| T-03-05 | Tampering | Documented custom filter contract | medium | mitigate | `docs/reference/context_buttons.md` "The filter toggle" keeps required IDs/`aria-expanded` semantics, marks icons optional, adds no unsafe label recipe; `test_filter_toggle_reference_contract` pins it; migration guide links copied templates to it. | closed |
| T-03-SC | Tampering | npm/pip/cargo installs | high | mitigate | No changes to `package.json`, `package-lock.json`, `pyproject.toml` or `uv.lock` in the phase diff; both SUMMARYs record no installs. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*

## Accepted Risks Log

No accepted risks.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-26 | 6 | 6 | 0 | secure-phase orchestrator (ASVS L1 grep-depth short-circuit) |

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-26
