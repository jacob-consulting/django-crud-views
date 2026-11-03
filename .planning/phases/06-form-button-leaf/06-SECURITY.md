---
phase: "06"
slug: "form-button-leaf"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-28"
---

# Phase 06 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Form data to HTML | Literal text must not become templates or markup | Button value, label, title, attributes (developer/translated strings) |
| Custom template to contract | Only normalized form fields cross the boundary | `cv_*` leaf fields, never `input` or caller context |
| Embedded form to page | Ownership controls configuration identity | Owner view / label-mode map |
| Shared helper class to request instance | Mutable layouts and ownership must remain instance-local | Filter helper layout, `helper.form` |
| Registry output to button host | Trusted renderer markup and escaped label/host attributes stay separate | Icon markup, host classes |
| Dynamic icon selection to accessible output | Missing icon must not silently create an invisible control | Icon availability, fallback label |
| Developer configuration to checks/render | Malformed configuration must not bypass diagnostics | Form label-mode maps, settings |
| GET controls to filter request | Sort/order values must survive | `sort`/`order`/`dir` query values |
| Browser control to submitted request | Clicked submitter determines action payload | Submitter name/value, CSRF token |
| Documentation to consumer override | Examples become executable template/helper code | Published recipes |
| Locked dependencies to validation | Environment restoration must preserve provenance | npm lock, Node runtime, crispy floor pins |
| Git history to acceptance evidence | Baselines must actually precede product changes | Golden commits `2956f3e`, `98b71ed` |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-06-01 | Repudiation | baseline capture/history | medium | mitigate | Baseline-only commits `2956f3e`/`98b71ed`, ancestral to HEAD, `src` tree `dcc38f4` unchanged (06-ACCEPTANCE §3) | closed |
| T-06-02 | Tampering | form leaf and attributes | high | mitigate | Real-crispy hostile plain/SafeString body/value/title/attribute DOM regressions (`test_crispy_buttons.py`, `test_button_data.py`; high-threat shard 109 passed) | closed |
| T-06-03 | Information disclosure | adapter value rendering | high | mitigate | Leaf bypasses `BaseInput.render`; `{{ request.user }}` stays literal (no-template-evaluation regressions) | closed |
| T-06-04 | Tampering | reserved attributes | medium | mitigate | Alias normalization; one canonical type/name/value/id/class/cancel attribute asserted | closed |
| T-06-05 | Tampering | adapter owner resolution | high | mitigate | Conflicting-owner regressions across render form / helper / page tiers incl. None overlays and falsey owners (06-03; cycle-3 repair shard 102 passed) | closed |
| T-06-06 | Information disclosure | shared render context | medium | mitigate | Unchanged-caller-context, interleaved and failing-render regressions; no instance/global owner cache; `Formsets.render` copies context | closed |
| T-06-07 | Tampering | icon host classes | medium | mitigate | `test_form_host_classes_are_escaped_attributes` and host no-duplicate-inline tests | closed |
| T-06-08 | Tampering | semantic slot and payload | medium | mitigate | `test_delete_form_icon_and_slot_hooks`, `test_kind_icon_follows_the_slot_not_the_name` keep request name/value | closed |
| T-06-09 | Tampering | filter helper shared layout | high | mitigate | Layout deep-copied per helper; interleaved forms and exactly-once actions tested (`test_filter.py`) | closed |
| T-06-10 | Tampering | filter hidden controls | medium | mitigate | Endpoint renders assert sort/order/dir names and values unchanged; filter region byte-identical to baseline | closed |
| T-06-11 | Denial of service | system-check traversal | medium | mitigate | Checks never instantiate forms/helpers or call `get_form_class`/hooks/renderers (`test_checks_never_instantiate_forms_or_helpers`) | closed |
| T-06-12 | Tampering | missing-icon fallback | medium | mitigate | Strict `ValueError` and non-strict literal-label fallback tests (one log per render, no generated title/tooltip/host class) | closed |
| T-06-13 | Tampering | modal FormData | high | mitigate | Native SubmitEvent/FormData modal suite on locked jsdom 30.1.2 asserts clicked submitter + CSRF only (JS 223/223) | closed |
| T-06-14 | Tampering | cancel/reset handlers | medium | mitigate | Nested-click cancel and encoded/non-ASCII filter-reset regressions (`viewset.test.js`, `list.filter.test.js`) | closed |
| T-06-15 | Tampering | published template recipe | high | mitigate | Documented custom template executed with hostile literal value/label/attribute; DOM equals literal, no `<script>` (`test_form_button_docs.py`) | closed |
| T-06-16 | Repudiation | Breaking migration record | medium | mitigate | CHANGELOG Breaking + `docs/migrating-1.0.md` pair in one commit (`b9b9f92`), checked by `test_form_buttons_breaking_entry_pairs_with_migration` | closed |
| T-06-17 | Repudiation | acceptance and validation records | medium | mitigate | 06-ACCEPTANCE.md records exact HEAD, exit codes and unresolved gates; probes re-run, not inherited | closed |
| T-06-SC | Tampering | runtime/package restoration and dependency installation | high | mitigate | `06-js-verify.sh` re-asserts lock sha256 and 71 lock-matched packages; crispy_floor installs declared pins only; no new dependency installed in any plan | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

Out-of-register note (not a phase threat): the dev-only `undici` package (transitive via jsdom) carries high-severity `npm audit` advisories. It is not shipped and not on a form-render path; tracked as WINDOWS #6 for a separate dependency update.

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-28 | 18 | 18 | 0 | /gsd-secure-phase (L1, plan-time register; evidence from 06-09 measurements at `e40b0de`) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-28
