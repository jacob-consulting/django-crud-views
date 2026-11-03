---
phase: "05"
slug: table-pagination-parity
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-27"
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Request query string → rendered pagination hrefs | Page, sort and filter parameters from the URL are re-emitted into table pagination links | Untrusted query values (low sensitivity) |
| Project settings → rendered class attributes | `CRUD_VIEWS_*` class-table overrides for `pagination:hidden-label` reach both pagination templates | Developer-controlled configuration |
| Theme/child templates → stock pagination blocks | Downstream overrides of `pagination.previous` / `pagination.next` run inside the stock template | Template code from downstream projects |
| Translation toolchain → shipped catalog | `makemessages` / `msgfmt` regenerate the German `.po` / `.mo` | Build artifacts |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Tampering | Table href rendering | high | mitigate | `table/bootstrap5.html` builds every page href with `cv_querystring table.prefixed_page_field=…` inside quoted attributes; `test_table_pagination_prefixed_query_preservation` covers hostile, non-ASCII and multivalue query values with no injected markup | closed |
| T-05-02 | Tampering | Hidden-label class attributes | high | mitigate | Both `table/bootstrap5.html` and `snippets/pagination.html` emit the class through autoescaped `cv_button_class 'pagination' 'hidden-label'` (no `autoescape off`); `HIDDEN_LABEL_CASES` tests in `test_table_template.py` and `test_card_order.py` keep a hostile value as one escaped attribute | closed |
| T-05-03 | Denial of Service | Stock and copied direction overrides | medium | mitigate | `has_previous` / `has_next` guards now sit inside `pagination.previous` / `pagination.next`; `test_table_pagination_direction_overrides` renders first/middle/last pages and asserts unavailable page-number methods are never called | closed |
| T-05-04 | Information Disclosure | Multi-table navigation | medium | mitigate | Scoped `table.prefixed_page_field` via `cv_querystring` preserves every other query value; prefixed-table regression proves another table's page key is untouched | closed |
| T-05-05 | Denial of Service | Copied direction override recipe | medium | mitigate | `tests/test1/test_pagination_docs.py::test_documented_pagination_direction_overrides` extracts the template from `docs/migrating-1.0.md` and renders it on pages 1/2/3 with guarded calls | closed |
| T-05-06 | Tampering | Locale build | low | accept | Existing trusted gettext toolchain; diff scoped to the core German catalog (source references only, no `msgstr` changes; `.mo` byte-identical to a fresh `msgfmt` build) | closed |
| T-05-SC | Tampering | npm/pip/cargo installs | high | mitigate | No dependency or lockfile changes in the phase (`pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json` unchanged since `7dcfa76`); no installs performed | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-06 | Locale regeneration uses the project's existing trusted gettext toolchain; the resulting diff is reviewed and limited to source references in the core German catalog | plan-time disposition (05-03 threat model) | 2026-10-27 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-27 | 7 | 7 | 0 | gsd-secure-phase (orchestrator, ASVS L1 grep-depth short-circuit) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-27
