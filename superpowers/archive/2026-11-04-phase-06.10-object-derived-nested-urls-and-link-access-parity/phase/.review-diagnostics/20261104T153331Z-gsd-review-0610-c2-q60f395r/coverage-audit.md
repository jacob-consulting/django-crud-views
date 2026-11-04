# Cycle 2 coverage and cross-artifact audit

22/22 locked decisions and requirement IDs have executable plan coverage. 32/32 examined failure directions are represented. This is plan coverage, not executed correctness.

| ID | Evidence |
|---|---|
| D-01 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:113 |
| D-02 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:132 |
| D-03 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:87 |
| D-04 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:88 |
| D-05 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:153 |
| D-06 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| D-07 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:154 |
| D-08 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| D-09 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:80 |
| D-10 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:80 |
| D-11 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:76 |
| D-12 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:155 |
| D-13 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:152 |
| D-14 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| D-15 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:102 |
| D-16 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-05-PLAN.md:79 |
| NURL-01 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:132 |
| NURL-02 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:155 |
| NURL-03 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-04-PLAN.md:83 |
| AUTH-08 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:95 |
| AUTH-09 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:115 |
| NURL-04 | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-06-PLAN.md:135 |

| Failure | Evidence |
|---|---|
| F01 Object page A/row B | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:113 |
| F02 Explicit conflicting parent strict | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:86 |
| F03 Explicit conflicting parent optional | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:86 |
| F04 Collection page wins | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:87 |
| F05 Collection no-page derives | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:88 |
| F06 Partial incompatible chain | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:98 |
| F07 Null object relation cannot repair | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| F08 Independent collection remains usable | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| F09 M2M zero/one/two with scope | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| F10 M2M missing scope strict/optional | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:91 |
| F11 M2M no membership query | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| F12 Resource explicit/page scope without introspection | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:154 |
| F13 Resource leaf-only/subclass | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| F14 Wrong model/malformed identifiers | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| F15 Required object/PK and falsey/zero | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:102 |
| F16 Unknown key/native reverse vs view exceptions | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:102 |
| F17 Native missing versus custom same-class exceptions | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:157 |
| F18 to_field/custom PK/registered inherited identity | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:136 |
| F19 Database mismatch ancestry | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-04-PLAN.md:100 |
| F20 Unloaded/preloaded/deferred query bounds | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md:136 |
| F21 Guardian opposite A/B grants | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:115 |
| F22 Immediate-parent only despite unavailable ancestor | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:82 |
| F23 D09 unresolved child fallback actual request | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:116 |
| F24 D10 no-object sibling fallback | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:80 |
| F25 Nested create selected state/access MRO | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:84 |
| F26 Missing declaration actors and retry | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-PLAN.md:101 |
| F27 Certified parent mandatory gate and override styles | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-04-PLAN.md:81 |
| F28 Hook counts/errors/context ownership | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-02-PLAN.md:110 |
| F29 Protected visibility/first-candidate/cascade | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-04-PLAN.md:83 |
| F30 Paired docs/executable optional errors | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-05-PLAN.md:92 |
| F31 Browser source/recipe/schema failure rejection | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-06-PLAN.md:100 |
| F32 Final stale evidence recapture/regression gates | .planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-06-PLAN.md:135 |

## Cross-artifact pass

STATE/ROADMAP: deterministic seam reports lag (Ready to plan / Planned), not a finding. All four roadmap success criteria and six requirement IDs compared with all plan truths/references; no contradiction. CONTEXT D01–D16 compared against plan scope/error/access contracts; no confirmed contradiction. No axis skipped. Cross-artifact advisories do not contribute to counts.
