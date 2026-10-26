---
phase: "01"
slug: "label-mode-defaults"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-26"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Operator settings / stamped context → mode resolver → template | Malformed Python values must not become template modes or crash non-strict rendering. | `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, `cv_label_mode` stamps (operator-controlled config, non-sensitive) |
| Docs contract test → documented example | Documentation code is parsed as data, never executed. | Markdown Python fences (repository content) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Denial of service | default_label_mode / cv_button_data | high | mitigate | `is_label_mode` type-checks (`isinstance(value, str)`) before membership, so unhashable values cannot raise TypeError; strict raises ValueError, non-strict falls back (`src/crud_views/lib/view/label_mode.py:33-96`) | closed |
| T-01-02 | Denial of service | warning emission | medium | mitigate | `_warned_lock` guards only the dedup check-and-add (`label_mode.py:29-78`); timeout-bounded nested-recovery regression in `tests/test1/test_button_data.py` | closed |
| T-01-03 | Tampering | config → leaf mode | medium | mitigate | `is_label_mode` rejects noncanonical strings; `crud_views.E108` reports raw bad entries (`src/crud_views/lib/settings.py:149`); templates unchanged | closed |
| T-01-04 | Denial of service | W292 / check_viewsets | high | mitigate | Narrow `except ValueError` around the single mode lookup (`src/crud_views/lib/view/buttons.py:407-410`); E108 still returned | closed |
| T-01-05 | Tampering | precedence / eager floor evaluation | medium | mitigate | Explicit membership check before floor read; invalid-floor bypass tests in `test_action_label_mode_config.py` and `test_context_action_label_mode.py` | closed |
| T-01-06 | Elevation of privilege | view permission checks | low | accept | No permission code modified (diff vs `introduce-gsd` touches no permission logic); full suite permission tests green | closed |
| T-01-07 | Denial of service | card mode fallback | medium | mitigate | `cv_get_card_actions_label_mode` returns a set attribute without reading the floor (`src/crud_views/lib/views/card.py:110-115`); leaf validation preserved | closed |
| T-01-08 | Tampering | card precedence / accessible label | medium | mitigate | Render tests assert explicit modes, unchanged `no_label` chain, hidden accessible label/title (`tests/test1/test_card_label_mode_render.py`) | closed |
| T-01-09 | Denial of service | consumer raw attribute access | low | mitigate | Break disclosed with resolver replacement in `CHANGELOG.md` (Breaking) and `docs/migrating-1.0.md` | closed |
| T-01-10 | Tampering | configuration documentation | medium | mitigate | `tests/test1/test_label_mode_docs.py` binds docs sections to precedence/default values and renders the documented setting through `{% cv_button %}` | closed |
| T-01-11 | Elevation of privilege | docs contract test | low | mitigate | `ast.literal_eval` only, never `exec` (`tests/test1/test_label_mode_docs.py:96`) | closed |
| T-01-12 | Information disclosure | published docs / acceptance notes | low | mitigate | Added doc/changelog lines contain only generic examples; no secrets, tokens or downstream project names | closed |

| T-01-13 | Tampering | Instance/card-floor precedence | medium | mitigate | Own-instance branch in `views/card.py`; `test_card_instance_mode_precedence` renders explicit/action/no_label choices against conflicting floors | closed |
| T-01-14 | Information disclosure | Shared class mutation | medium | mitigate | Resolver only reads `vars(self)`; `test_card_request_assignment_is_local` and reset-to-None tests verify sequential request isolation without class mutation | closed |
| T-01-15 | Denial of service | Eager strict-floor evaluation | high | mitigate | Instance non-None branch does not call floor accessor; parameterized strict-invalid-floor render regressions pass | closed |
| T-01-16 | Elevation of privilege | Card access/method gating | low | accept | Permission/method branches unchanged; `test_card_instance_mode_reaches_child_action` asserts granted/denied child rendering, and existing POST/disabled tests pass | closed |
| T-01-SC | Tampering | Dependency supply chain | high | mitigate | No dependency installation or dependency file changes in 01-05 | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-01-06 | Phase changes label rendering only; no permission code is touched. Existing authorized-render and permission tests are the regression guard. | Plan 01-02 threat model (planning) | 2026-10-25 |

| AR-01-02 | T-01-16 | Label-mode repair preserves permission and method code; child permission and existing action regressions pass. | Plan 01-05 threat model | 2026-10-26 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-26 | 12 | 12 | 0 | secure-phase orchestrator (L1 grep-depth, short-circuit) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-26

## Security Audit 2026-10-26

| Metric | Count |
|---|---|
| Threats found | 17 |
| Closed | 17 |
| Open | 0 |

## Gap-Closure Security Evidence

L1 source inspection confirms the four new threat dispositions and shared supply-chain row. The 01-05 summary records 45 card tests and 3,076 full-suite tests passing. Existing T-01-01 through T-01-12 mitigations remain unchanged; no blocking threat remains.
