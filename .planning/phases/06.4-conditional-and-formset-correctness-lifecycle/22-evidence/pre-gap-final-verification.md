---
phase: "06.4-conditional-and-formset-correctness-lifecycle"
verified: "2026-11-01T17:33:24Z"
status: "gaps_found"
score: "8/10 must-haves verified"
covered_files: [".github/workflows/js.yml",".planning/phases/06-form-button-leaf/06-JS-RUNTIME.json",".planning/phases/06-form-button-leaf/06-UAT.md",".planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md",".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-MATRIX.md",".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-REGRESSION-GATE.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-02-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-02-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-03-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-03-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-06-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-06-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-07-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-07-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-08-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-08-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-09-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-09-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-10-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-10-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-11-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-11-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-12-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-12-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-13-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-13-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-14-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-14-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-15-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-15-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-16-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-16-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-17-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-17-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-18-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-18-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-19-PLAN.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-19-SUMMARY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-ACCEPTANCE.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-CONTEXT.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-GAP-COVERAGE.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-MATRIX.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-PUBLIC-SURFACE.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-REVIEW-DISPOSITION.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-REVIEW.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-SECURITY.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-SOURCE-AUDIT.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-UI-REVIEW.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-UI-SPEC.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-VALIDATION.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/08-browser-results.json",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/10-evidence/results.json",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/10-evidence/run.py",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/10-evidence/source-manifest.json",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/16-evidence/ambiguity.json",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/16-evidence/capability.json",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/18-evidence/results.json",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/18-evidence/source-manifest.json",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/19-evidence/code-review.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/19-evidence/security-review.md",".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/19-evidence/ui-review.md",".planning/ui-reviews/06.4-gap-repair/desktop.png",".planning/ui-reviews/06.4-gap-repair/mobile.png",".planning/ui-reviews/06.4-gap-repair/tablet.png","CHANGELOG.md","docs/migrating-1.0.md","docs/reference/conditional.md","docs/reference/formsets.md","docs/reference/javascript.md","examples/bootstrap5/conditional/models.py","package-lock.json","package.json","src/crud_views/checks.py","src/crud_views/lib/conditional/group.py","src/crud_views/lib/conditional/layout.py","src/crud_views/lib/formsets/formsets.py","src/crud_views/lib/formsets/inline_formset.py","src/crud_views/lib/formsets/mixins.py","src/crud_views/lib/formsets/render_tree.py","src/crud_views/lib/view/base.py","src/crud_views/lib/views/mixins.py","src/crud_views/static/crud_views/js/formset.js","src/crud_views/static/crud_views/js/modal.js","src/crud_views/static/crud_views/js/toggle.js","src/crud_views/templates/crud_views/conditional/toggle_group.html","src/crud_views/templates/crud_views/formsets/control.html","src/crud_views/templates/crud_views/formsets/formset.html","src/crud_views/templates/crud_views/formsets/formsets.html","src/crud_views_guardian/lib/mixins.py","tests/browser/conditional-formsets.cjs","tests/browser/conditional_formsets_server.py","tests/browser/modal-focus.cjs","tests/browser/templates/conditional_formsets/native_control.html","tests/browser/templates/conditional_formsets/native_formset.html","tests/browser/templates/conditional_formsets/native_formsets.html","tests/browser/templates/conditional_formsets/native_toggle_group.html","tests/browser/templates/conditional_formsets/page.html","tests/js-integration/formset.test.js","tests/js/adapters.test.js","tests/js/formset.test.js","tests/js/helpers/dom.js","tests/js/list.filter.test.js","tests/js/modal.test.js","tests/js/runtime-contract.test.js","tests/js/toggle.test.js","tests/js/viewset.test.js","tests/test1/app/models.py","tests/test1/conftest.py","tests/test1/test_action_label_mode_config.py","tests/test1/test_action_label_mode_render.py","tests/test1/test_action_menus_golden.py","tests/test1/test_alerts.py","tests/test1/test_authorization_matrix.py","tests/test1/test_authorization_templates.py","tests/test1/test_button_classes.py","tests/test1/test_button_classes_checks.py","tests/test1/test_button_classes_templates.py","tests/test1/test_button_data.py","tests/test1/test_button_leaves.py","tests/test1/test_cancel_origin.py","tests/test1/test_card_label_mode_render.py","tests/test1/test_card_label_modes.py","tests/test1/test_card_order.py","tests/test1/test_conditional_checks.py","tests/test1/test_conditional_formset.py","tests/test1/test_conditional_group.py","tests/test1/test_conditional_layout.py","tests/test1/test_conditional_migration_docs.py","tests/test1/test_conditional_persistence.py","tests/test1/test_context_action_label_mode.py","tests/test1/test_context_button_label_mode.py","tests/test1/test_core_nested_create_state.py","tests/test1/test_crispy_buttons.py","tests/test1/test_crud.py","tests/test1/test_delete.py","tests/test1/test_delete_databases.py","tests/test1/test_delete_inspection.py","tests/test1/test_delete_join_identity.py","tests/test1/test_delete_migration_docs.py","tests/test1/test_delete_provenance.py","tests/test1/test_filter.py","tests/test1/test_filter_toggle_label_mode.py","tests/test1/test_form_button_checks.py","tests/test1/test_form_button_docs.py","tests/test1/test_form_buttons_golden.py","tests/test1/test_formset_pk_boundary.py","tests/test1/test_formsets_bugs.py","tests/test1/test_formsets_controls.py","tests/test1/test_formsets_policy.py","tests/test1/test_formsets_validation_gate.py","tests/test1/test_fragment_authorization.py","tests/test1/test_guardian.py","tests/test1/test_guardian_composition.py","tests/test1/test_guardian_content_type_docs.py","tests/test1/test_guardian_content_types.py","tests/test1/test_guardian_delete.py","tests/test1/test_guardian_inactive.py","tests/test1/test_guardian_parent_none.py","tests/test1/test_guardian_policy.py","tests/test1/test_i18n.py","tests/test1/test_icon_host_leaves.py","tests/test1/test_icons_registry.py","tests/test1/test_import_safety.py","tests/test1/test_label_mode.py","tests/test1/test_label_mode_docs.py","tests/test1/test_messages.py","tests/test1/test_pagination_docs.py","tests/test1/test_polymorphic.py","tests/test1/test_table_template.py","tests/test1/test_transactions.py","vitest.config.js","vitest.integration.config.js"]
covered_digest: "v3:sha256:8cf0adaa67171f9d9a3aa17a2f95c27a45f4268cc5aa0cf9cf40db7d2dafd803"
behavior_unverified: 0
overrides_applied: 0
must_haves: {"truths":["A1: Each conditional group binds to its own intended toggle across sibling/nested rows, shared suffixes, prefixes, multiple forms, modal content and dynamically added rows; compatibility for old markup is explicit.","A2/A3: Baseline disabled reasons and all enclosing groups compose correctly in both nesting orders. Native reset recomputes state after a non-cancelled reset, remains scoped to its form and preserves management inputs.","A4: Inactive supported fields clear with correct persistence semantics, including existing FileField references, explicit empty values, Boolean and M2M; unsupported shapes have a guard and inherited validation is documented.","A5: Active edit_only formsets cannot create forged extras; stock/custom controls agree; invalid initial-row identity rejects without unproven cross-parent mutation claims.","A6/A7: Automatic idempotent page/modal/422/nested initialization supports roots, late scripts/toggles and working Add/Delete/Order/Submit/widget behavior through supported APIs.","Stock and minimal non-Bootstrap templates pass lifecycle/keyboard/focus acceptance and preserve authorization, parent denial, querysets, rollback, skip/purge and jQuery.","Document usable projection and changed identity/root/visibility hooks; preserve fragment/event protocols and pair Breaking migration guidance; A8 classification remains outside this repair.","Every claimed Django series has enabled passed tracer, enabled missing-runtime call failure, and ordinary full Python suite with opt-in absent and Node unavailable.","Focused regressions pass cached Django 4.2/5.2/6.0 with checkout imports and exact full-suite exclusions.","JavaScript, strict docs, touched-file lint and current-source browser evidence pass under declared reproducible runtime and capture contracts."],"prohibitions":[{"statement":"Switching a conditional file field off must not silently authorize deletion of the stored file content.","status":"resolved","verification":"test"}]}
decision_coverage: {"honored":19,"total":19,"not_honored":[]}
re_verification: {"previous_status":"gaps_found","previous_score":"4/10","previous_verified":"2026-11-01T14:20:25Z","historical_report":".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/superseded/06.4-VERIFICATION-20261101T142025Z.md","gaps_closed":["G1 / CR-01","G2 / CR-02","G3 / CR-03","G4 / CR-04","G5 / CR-05"],"gaps_remaining":["G6 / WR-03, WR-04; original WR-01/02 counterexamples closed"],"regressions":["Evidence-validator omissions WR-03/04 reproduced in successor runner; no new demonstrated product-code regression."]}
gaps: [{"id":"G6","review_ids":["WR-03","WR-04"],"truth":"JavaScript, strict docs, touched-file lint and current-source browser evidence pass under declared reproducible runtime and capture contracts.","status":"failed","reason":"The aggregate/handoff validator accepts missing or contradictory corruption subprocess records and absent or stale conditional screenshot provenance. Four current-source in-memory counterexamples reproduce acceptance. Actual captured records and screenshots are genuine; checker enforcement remains incomplete.","requirements":["LIFE-02"],"artifacts":[{"path":".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py","issue":"validate() lines 984–985 trusts checker_controls labels without checker_control_evidence; validate_browser() lines 857,890–924 trusts the recorded canonical exit and omits current conditional capture validation."},{"path":".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py","issue":"37 passing self-tests and 25 genuine corruption controls omit the four reproduced evidence-corruption variants."}],"missing":["Validate the exact corruption-record inventory, command/mode, nonzero exit and rejection diagnostics against summary controls; reject absent/contradictory records.","Revalidate stock/native conditional capture inventory, bounded paths, current bytes/hashes and required viewport/icon/containment observations during aggregate and handoff checking.","Add discriminating missing/contradictory-control and missing/stale-capture regression controls, refresh affected evidence, and obtain independent code/security reassessment."]}]
security_gate: {"status":"OPEN_THREATS","total":37,"closed":31,"high_open":["T-06.4-22","T-06.4-28","T-06.4-33","T-06.4-35","T-06.4-36"],"medium_open":["T-06.4-31"],"risk_acceptance":[]}
prohibition_dispositions: [{"statement":"Switching a conditional file field off must not silently authorize deletion of the stored file content.","status":"unverified","flagged":true,"verification":"test","descriptor_present":false,"reason":"No passing wired enforcement descriptor or attributed human disposition; native reference/storage observations are bounded implementation evidence."}]
pending_human_checks: [{"id":"H1","status":"pending","test":"Evaluate corrected stock and native hosts for discoverability, labels/errors, keyboard/focus/reset/422 and assistive technology.","expected":"Usable controls, readable text, coherent focus and announcements in both hosts; record actual person, environment, results and limits.","why_human":"Headless assertions and three stock screenshots do not establish human accessibility acceptance."},{"id":"H2","status":"flagged-unverified","test":"Resolve the exact conditional file-off storage-deletion prohibition through genuine wired enforcement or an attributed human disposition.","expected":"No implicit authorization to delete storage content; disposition states native-reference, ImageField and consuming-application boundaries.","why_human":"Authored resolved/test has no enforcement descriptor; no person has approved it."}]
fallback_edges: [{"id":1,"requirement":"AUTH-02","category":"concurrency","status":"flagged-unresolved"},{"id":2,"requirement":"COND-01","category":"boundary","status":"flagged-unresolved"},{"id":3,"requirement":"COND-01","category":"adjacency","status":"flagged-unresolved"},{"id":4,"requirement":"COND-01","category":"empty","status":"flagged-unresolved"},{"id":5,"requirement":"COND-01","category":"encoding","status":"flagged-unresolved"},{"id":6,"requirement":"COND-01","category":"ordering","status":"flagged-unresolved"},{"id":7,"requirement":"COND-01","category":"precision","status":"flagged-unresolved"},{"id":8,"requirement":"COND-02","category":"adjacency","status":"flagged-unresolved"},{"id":9,"requirement":"COND-02","category":"empty","status":"flagged-unresolved"},{"id":10,"requirement":"COND-02","category":"ordering","status":"flagged-unresolved"},{"id":11,"requirement":"COND-03","category":"unclassified","status":"flagged-unresolved"},{"id":12,"requirement":"COND-04","category":"idempotency","status":"flagged-unresolved"},{"id":13,"requirement":"COND-04","category":"concurrency","status":"flagged-unresolved"},{"id":14,"requirement":"COND-05","category":"adjacency","status":"flagged-unresolved"},{"id":15,"requirement":"COND-05","category":"empty","status":"flagged-unresolved"},{"id":16,"requirement":"COND-05","category":"ordering","status":"flagged-unresolved"},{"id":17,"requirement":"FSET-01","category":"adjacency","status":"flagged-unresolved"},{"id":18,"requirement":"FSET-01","category":"empty","status":"flagged-unresolved"},{"id":19,"requirement":"FSET-01","category":"ordering","status":"flagged-unresolved"},{"id":20,"requirement":"FSET-01","category":"idempotency","status":"flagged-unresolved"},{"id":21,"requirement":"FSET-01","category":"concurrency","status":"flagged-unresolved"},{"id":22,"requirement":"FSET-02","category":"idempotency","status":"flagged-unresolved"},{"id":23,"requirement":"FSET-02","category":"concurrency","status":"flagged-unresolved"},{"id":24,"requirement":"FSET-03","category":"boundary","status":"flagged-unresolved"},{"id":25,"requirement":"FSET-03","category":"precision","status":"flagged-unresolved"},{"id":26,"requirement":"FSET-03","category":"concurrency","status":"flagged-unresolved"},{"id":27,"requirement":"LIFE-01","category":"adjacency","status":"flagged-unresolved"},{"id":28,"requirement":"LIFE-01","category":"empty","status":"flagged-unresolved"},{"id":29,"requirement":"LIFE-01","category":"ordering","status":"flagged-unresolved"},{"id":30,"requirement":"LIFE-02","category":"empty","status":"flagged-unresolved"},{"id":31,"requirement":"LIFE-02","category":"encoding","status":"flagged-unresolved"}]
nyquist: {"status":"partial","compliant":false,"source":".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-VALIDATION.md"}
---
# Phase 06.4: Conditional and formset correctness/lifecycle Verification Report

**Phase Goal:** Conditional groups and formsets bind to the correct row, preserve disabled-state ownership, enforce server-side save semantics and initialize reliably across page/modal/dynamic-row lifecycles before Phase 7 freezes their theme contracts.

**Verified:** 2026-11-01T17:33:24Z
**Status:** gaps_found
**Score:** 8/10 must-haves verified; 0 present-but-behavior-unverified.
**Re-verification:** Yes — after plans 11–19. The original report is preserved byte-for-byte at [superseded/06.4-VERIFICATION-20261101T142025Z.md](superseded/06.4-VERIFICATION-20261101T142025Z.md).

Five original product/runtime blockers are closed. G6 remains open because the successor checker accepts incomplete or contradictory evidence. H1 remains pending and H2 remains flagged-unverified. The independent security gate retains five high obligations. **The phase is not complete and must not advance to the Phase 7 freeze.**

## Verification Basis

This is goal verification, not acceptance of SUMMARY completion claims. Read the original ten-truth contract, all nineteen PLAN/SUMMARY contracts, current REQUIREMENTS/CONTEXT, gap coverage, source, tests, current packet and independent plan-19 reports. Reuse source-current broad executions; run bounded fresh checks for repaired behavior and remaining defects. No full suite, service/browser startup, install, product change, fabricated human approval or risk acceptance occurred.

The original ten merged truths are retained verbatim in frontmatter, including their prohibition. ROADMAP's seven criteria remain represented by R1–R7; E1–E3 retain the three additional execution/evidence obligations. No scope-reducing override exists. No positive truth declares verification: backstop. Artifacts and links were checked through the GSD owner and manually traced; passing file-presence checks did not decide behavior.

Current packet: [18-evidence/results.json](18-evidence/results.json), twenty gates, source **bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601**, 824 source inputs. Runner SHA-256 **cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c**. Packet SHA-256 **a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674**. Current direct reviews are [code](19-evidence/code-review.md), [security](19-evidence/security-review.md), and [UI](19-evidence/ui-review.md). Their scores/closures are bounded independent observations, not human approval.

## Goal Achievement

### Observable Truths

| ID | Truth | Status | Evidence |
|---|---|---|---|
| R1 | A1: each group follows its own intended toggle across sibling/nested rows, prefixes, multiple forms, modal and dynamic content; old-markup compatibility is explicit. | VERIFIED | layout.py:29 emits add_prefix; toggle.js:23–28 matches exact owning-form checkbox names. ownedStates at :17,:88–103 retains the last state when initForm :137–167 removes an ambiguous listener. Fresh named ambiguity/recovery test passes; both-theme gap-ambiguity observations and all-series enabled renderer→JS→FormData→save tracer prove the runtime chain. COND-01 and D-02/03 hold within declared scope. |
| R2 | A2/A3: independent and enclosing disabled reasons compose in both orders; noncancelled native reset is scoped and preserves management fields. | VERIFIED | toggle.js:31–39,:78–112 drains external mutations before own writes, composes frozen and active ancestors, excludes management inputs and retains values. :121–133 queues reset after native defaults and honors late cancellation. Fresh ambiguity state test, source-current ownership/reset cases and independently rerun 36-case JS selection exercise transitions, not just symbol presence. |
| R3 | A4: supported inactive values persist correctly; FileField reference clearing does not promise storage deletion; explicit values, Boolean/M2M, guards and inherited invariants are accurate. | VERIFIED — retained | group.py:13–77 resolves bounded native pairs; :135–185 applies values before inherited model validation; :193–201 excludes trusted server-disabled fields. render_tree.py:333–339 saves changed existing conditional rows and native save_m2m; checks.py:162 uses the same resolver. Current persistence61/checks25/group18 per series and executable recipes retain prior behavioral proof. H2 remains a separate unverified enforcement obligation. |
| R4 | A5: all accepted active edit_only formsets reject forged extras and invalid initial identities before any save; legitimate operations and stock/custom policy agree. | VERIFIED | render_tree.py:202–263 reapplies and deduplicates mandatory errors in the current native cache; FormSets.all_valid :365–383 performs both traversals before the request save branch. Fresh test_reclean_edit_only_extra_stays_invalid[package] passes. Independent 12-case reclean/late-clean rerun and current package/native HTTP/ID/DELETE/database tests prove zero saves and unchanged main/sibling/nested records. No cross-parent mutation claim. |
| R5 | A6/A7: automatic idempotent page/modal/422/root/late/nested initialization supports Add/Delete/Order/Submit/widgets through supported APIs. | VERIFIED | formset.js:10–23 derives immutable bound identity, :265–279 tolerates native absent extra DELETE, :328–330 applies deletion eligibility; control.html:25 tests actual DELETE presence. Public initializers/events remain wired at file ends. Fresh move-extra/delete-initial/ordered-FormData test passes. Current all-extra ordered/unordered, integration, modal and browser records cover the repaired actions and repeated lifecycle. |
| R6 | Stock/native lifecycle and keyboard/focus acceptance, with two forms, reset, management/re-render, JS-off/tampered POST and preserved authorization/atomic/skip-purge boundaries. | UNCERTAIN — WARNING; H1 human decision required | 24 conditional cases/172 assertions and 12 modal cases/133 assertions pass with actual HTTP/database observations and no page errors. All 54 prior-report Python test paths occur in each current full collection. UI24/24 closes V1/V2/S1; three actual stock captures match. Native has no screenshots. Human discoverability/readability/keyboard orientation/screen-reader acceptance is absent. |
| R7 | Document usable projection and identity/root/visibility hooks; preserve event/request/response contracts, paired Breaking migration, and A8 exclusion. | VERIFIED — retained and updated | Tested reference docs, migration/CHANGELOG and PUBLIC-SURFACE remain wired; docs18/series execute actual fences and projection assertions. formsets.py:523–537 uses the selected declaration index; fragment89/series and real integration/browser records prove non-first/deeper int/UUID management→POST persistence and one outer row event with {prefix, rows}. A8 remains final-policy work, not a repair claim. |
| E1 | Every claimed Django series includes enabled passed tracer, missing-runtime call-failure control, and ordinary full Python route without opt-in/Node. | VERIFIED — retained | Read actual selections/JUnit/runtime facts in all three series. Enabled routes contain the passed tracer; disabled set is enabled minus tracer, variables absent, PATH empty and node/npm unavailable; controls fail the selected tracer call with path diagnostic. No setup/collection failure or skip substitutes for the control. |
| E2 | Focused cached Django4.2/5.2/6.0 regressions use checkout imports; full-suite exclusions are exact. | VERIFIED — retained | Fresh checker accepts twenty-gate packet; 433 focused passes per series and six full routes are source-current. Actual selected/collected cases, package imports and runtimes are recorded. Only established CSP skips/floor-golden deselections occur. No Python3.13–3.15 claim. |
| E3 | JS, strict docs, touched-file lint and source-current browser evidence satisfy reproducible runtime/capture contracts. | FAILED — BLOCKER G6 | Original CR-02/WR-01/02 are repaired. However validate() at runner:984–985 ignores detailed corruption records, and validate_browser() at :857,:890–924 omits current conditional capture validation. This verifier reproduced acceptance after removing controls, converting their failures to success, removing stock captures and making a capture digest stale. Genuine present evidence does not establish fail-closed enforcement. |

**Score: 8/10.** R6 is human-judgment uncertainty; it is not an untested state-transition claim. Every VERIFIED behavior has actual passing execution evidence. No coincidental-reliance flag is needed: actual form ownership, native capabilities, sequencing and per-request authority are established by production code or declared contracts; no new concurrency guarantee is inferred from fixtures.

**PLAN mapping:** original 01[1–3]→R1, 01[4]→E1; 02[1–4]/03[1–3]→R3; 04[1–3]→R4; 05[1–4]→R2; 06[1,3,4]→R5,06[2]→R4/R5; 07[1–4]→R7/R6; 08[1]→R5,08[2]→R6,08[3]→R4,08[4]→R3,08[5]→R2/R7; 09[1,3,4]→R7,09[2]→R3; 10[1]→E2,10[2]→E3,10[3]→E1,10[4]→R7. Gap plans refine this contract: 11→R4;12→E3/R7;13→R5/R4;14→R1/R2/R5;15→E3;16→R4/R5/R6;17→R7/R3/E3;18→E1/E2/E3;19→G6/security and H1/H2 reconciliation. Prepared human requests do not equal completed human checks.

### Gap and Independent Review Reconciliation

| Identity | Current disposition | Basis |
|---|---|---|
| G1 / CR-01 | CLOSED | Native reclean cannot erase mandatory policy across the aggregate validation gate; fresh direct test plus current HTTP/late sibling/child zero-save tests. |
| G2 / CR-02 | CLOSED | Ordinary Vitest includes tests/js only; explicit integration configuration requires CV_FRAGMENT_PYTHON. Node-only clean-copy harness runs all other ordinary files; missing/invalid integration runtime fails. Current packet has the required separate integration lane. |
| G3 / CR-03 | CLOSED | Optional extra DELETE is handled according to native eligibility; actual Django markup and both ordered/unordered integration/browser POSTs work. |
| G4 / CR-04 | CLOSED | Capability uses the bound suffix and INITIAL_FORMS; visual movement cannot change identity. Fresh named action/POST-data test passes. |
| G5 / CR-05 | CLOSED | Frozen ownership is separate from listener binding; zero/two/one-match recovery and disposal are tested. Fresh original counterexample passes. |
| Original WR-01 | CLOSED within original scope | Exact quality commands, case multiplicities and complete JS/integration/docs/lint selections enforced. Independent altered filtered/non-strict/missing-case records reject. |
| Original WR-02 | CLOSED within original scope | Current capture request preflight and per-gate reuse selection are separate from historical checking. Missing requested runtime fails before capture/output mutation; changed runtime invalidates reuse. |
| G6 / new WR-03 and WR-04 | OPEN — BLOCKER to goal | Four deterministic counterexamples show absent/contradictory controls and absent/stale conditional captures accepted. See reproduction below. |
| V1/V2/S1 | CLOSED within evidence-host scope | Icons, viewport and existing container repaired; three stock images match hashes and recorded widths have no horizontal overflow. |
| H1 / H2 | PENDING / FLAGGED-UNVERIFIED | No attributed human response or genuine H2 enforcement descriptor. |

### Required Artifacts

GSD verify.artifacts reports **87/87 declared occurrences present/substantive across nineteen plans**. The original sixty are retained; gap plans add twenty-seven declarations. This only establishes structural existence. Manual reading and execution evidence establish the following usage and behavior.

| Artifact group (repository-relative unless under phase directory) | Expected and actual wiring | Verdict |
|---|---|---|
| src/crud_views/lib/conditional/layout.py; conditional/toggle_group.html | Actual form.add_prefix context renders escaped marker consumed by exact owning-form binding. | VERIFIED, FLOWING |
| src/crud_views/static/crud_views/js/toggle.js | Supported initializer, independent/frozen ancestor ownership, reset/focus, loaded/unload/row events. | VERIFIED in tested scope |
| src/crud_views/lib/conditional/group.py; src/crud_views/checks.py | Shared native clearing resolver, inherited validation, static/runtime configuration guard. | VERIFIED; H2 separate |
| src/crud_views/lib/formsets/formsets.py; render_tree.py; inline_formset.py; mixins.py | Bound native trees, preserved native errors, both validity passes, per-alias authorized identities, atomic save/purge and indexed fragments. | VERIFIED, FLOWING |
| src/crud_views/templates/crud_views/formsets/{formsets,formset,control}.html | Native fields/management/errors and row capabilities feed real DOM and POST. | VERIFIED, FLOWING |
| src/crud_views/static/crud_views/js/{formset,modal}.js | Scoped repeat-safe actions, immutable capability, reorder before modal serialization, session/focus lifecycle. | VERIFIED in tested scope |
| tests/test1/test_conditional_{layout,group,formset,persistence,checks,migration_docs}.py | Renderer/persistence/configuration/executable docs against actual schema/fields, plus enabled tracer. | Active behavioral evidence |
| tests/test1/test_formsets_{policy,validation_gate,controls}.py; test_fragment_authorization.py | Native/package policy after reclean, real HTTP zero saves, rendered capabilities, actual scoped fragment POSTs. | Active behavioral evidence |
| tests/js/{toggle,formset,modal,runtime-contract}.test.js; tests/js/helpers/dom.js | Shipped JS, native capability fixture, repeat/reset/rebind/clean-runtime checks. | Active behavioral evidence; no mandatory skip |
| tests/js-integration/formset.test.js; vitest.integration.config.js; vitest.config.js; package.json; .github/workflows/js.yml | Node-only ordinary selection; mandatory explicit-runtime actual-Django bridge. | VERIFIED; no hosted-CI execution claimed |
| tests/browser/conditional-formsets.cjs; conditional_formsets_server.py; templates/conditional_formsets/* | Real authenticated CSRF HTTP/DB fixture, stock/native projections, repaired host and named browser assertions. | VERIFIED automated scope; H1 open |
| docs/reference/{conditional,formsets,javascript}.md; docs/migrating-1.0.md; CHANGELOG.md; examples/bootstrap5/conditional/models.py | Executable published contracts and paired migration, consumed by docs tests and Phase7 inventory. | VERIFIED |
| Phase PUBLIC-SURFACE, ACCEPTANCE, MATRIX, VALIDATION and GAP-COVERAGE | Qualified contract/evidence indexes, retaining actual historical outcomes and current unresolved gates. | Present and linked; Nyquist partial |
| Phase 15-evidence/{run.py,test_runner.py}; 18-evidence/{results.json,source-manifest.json} | Actual current capture/validation records and source manifest. | WIRED, substantive; enforcement FAILED WR-03/04 |
| Phase 19-evidence/{code-review,security-review,ui-review}.md; handoff.json | Independent bounded dispositions; structurally valid handoff says ready=false. | Present/linked; no completion authority |
| Historical 08-browser-results.json; 10-evidence/*; Phase6.2 ACCEPTANCE | Prior results and A19-only history remain intact. | Historical, not relabeled current |

No production artifact is missing, a stub, orphaned or a static-data replacement. The remaining implementation failure is evidence enforcement.

### Key Link Verification and Data Flow

The mechanical link query resolves **9/37** literal references and misses 28 indirect/native/event/path links. This is a heuristic limitation, not 28 accepted unwired features. For example, PLAN10 uses phase-relative 10-evidence/run.py; Python relative imports, reverse-consumed doc fences and HTML event contracts do not contain literal target paths. Each distinct chain was manually traced below.

| Producer → consumer | Concrete chain | Status |
|---|---|---|
| ToggleGroup → template → toggle.js | layout.py:29 add_prefix → escaped cv-data-toggle-field → form.elements exact name/type/form equality. | WIRED/FLOWING |
| FormSet.init → XFormSet → conditional wrapper | formsets.py:169–173 owning main form → cv_bound_toggle_field → cv_toggle_field property/template. | WIRED/FLOWING |
| Conditional mixin → native ModelForm → save | Resolved off values set before super._post_clean; existing-row change signal reaches render_tree.save; instance.save then form.save_m2m. | WIRED/FLOWING |
| Static check → runtime resolver | checks.py imports resolve_conditional_empty_value at :12 and calls :162; same resolver raises descriptive runtime configuration error. | WIRED |
| Runtime row policy → aggregate → request save | XFormSet.is_valid calls policy every traversal; all_valid consumes both passes; FormSetMixin.cv_form_is_valid returns false before CrudView form-valid branch/atomic writes. | WIRED; reclean behavioral proof |
| Native controls → formset actions → modal submit | actual DELETE presence → immutable bound eligibility; form submit reorders before document modal handler checks defaultPrevented and constructs FormData. | WIRED; ordered FormData tests |
| Fragment request → authorized template → dynamic DOM → DB | FormSetMixin.get resolves target, validates ancestry/coordinates; get_template selects declaration index and renders real rows; JS inserts/update totals/emits one outer event; native binding/save persists intended parent relation. | WIRED/FLOWING |
| Native errors → page/modal422 | Actual native/policy error cache → non_form_errors above rows, retained form values/management → error response/422 replacement. | WIRED/FLOWING |
| Page/modal/row events → public root APIs/widgets | readyState plus DOMContentLoaded, modal loaded/unload and row-added invoke shared initializers; scoped controllers/listeners dispose correctly. | WIRED |
| Docs → executable recipes → public inventory | Tests extract actual fences, execute real APIs and compare projection/protocols; paired migration and inventory retain supported names and internal boundaries. | WIRED |
| Runner → subprocess records → aggregate/handoff | Capture records real cases/commands/runtimes; handoff uses aggregate validation and independently attributed dispositions. | WIRED but control/capture enforcement INCOMPLETE, G6 |

All rendered dynamic values originate in bound forms, authorized querysets, native error caches or actual fragment responses. No chain terminates in mock production data. Fixture inputs describe test scenarios; real schema/save/HTTP/FormData observations establish outcomes.

### Behavioral Spot-Checks and Probe Execution

Commands ran from repository root. P below means .planning/phases/06.4-conditional-and-formset-correctness-lifecycle; PY is .nox/crispy_floor-3-12-django-6-0/bin/python; NODE is /home/alex/.nvm/versions/node/v24.21.0/bin/node.

| Behavior | Command / exact selection | Fresh result |
|---|---|---|
| Source-current aggregate | PY P/15-evidence/run.py --check --output P/18-evidence/results.json | exit0, PHASE64_MATRIX_OK 20 gates and source digest above. Packet check passes; known omitted enforcement still fails adversarial probes. |
| Prepared handoff | PY P/15-evidence/run.py --check-handoff P/19-evidence/handoff.json | exit0; structurally_valid=true, ready=false, disposition=not-ready, before report replacement. Parent must rebind this report hash. |
| Policy survives reclean | PYTHONPATH="$PWD/src:$PWD" PY -m pytest 'tests/test1/test_formsets_policy.py::test_reclean_edit_only_extra_stays_invalid[package]' -q -p no:cacheprovider | exit0; 1 passed in0.75s. |
| Ambiguous inactive ownership and recovery | NODE node_modules/vitest/vitest.mjs run tests/js/toggle.test.js -t 'keeps a formerly bound inactive group safe during ambiguity and uniquely recovers' | exit0; 1 passed;54 unselected. Native validity, FormData, unrelated groups, unique recovery and one listener asserted. |
| Stable identity after movement | NODE node_modules/vitest/vitest.mjs run tests/js/formset.test.js -t 'moves a native extra above an initial row and then deletes the initial row' | exit0;1 passed;61 unselected. Actual action and final ORDER/DELETE FormData asserted. |
| WR-03 controls | Actual imported validate(copy, source()), first without checker_control_evidence, then with all records exit0 / PHASE64_MATRIX_OK / empty stderr | Both ACCEPTED — FAIL of required rejection contract. |
| WR-04 screenshots | Actual imported validate(copy, source()), first stock gap-ambiguity captures=[], then a stock capture sha256="stale" | Both ACCEPTED — FAIL of required rejection contract. |
| Actual control/capture integrity | Independently inspect all detailed exits/diagnostics; SHA-256 current PNG bytes against packet | 25 controls all nonzero with MATRIX_REJECTED;3 stock PNGs all match. No fabricated actual evidence alleged. |
| H2 enforcement | Installed runProhibitionEnforcement(authoredItem, undefined, {mode:"interactive"}) | status=unverified, flagged=true, tier=test, located=false, evidence=[]; no passing wired enforcement. |

Vitest's filtered counts are selection exclusions, not authored disabled cases or acceptance skips. Existing Vite ESM/config-loader warning remains informational. No full matrix/self-test suite/browser was repeated. Direct code re-review's existing fresh twelve Python and thirty-six JS behavioral passes are also source-current and retained.

There are no declared or conventional scripts/*/tests/probe-*.sh files. The runnable phase evidence checker was executed in this verifier's process. The earlier source-audit edge probe skipped because IDs were unassigned; it remains a historical skip, not a retrospectively executed probe. No new server or application state was started or mutated; the named Python test uses disposable test state.

Reproduction for the remaining defect uses the real module and deep in-memory copies only:

~~~python
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json

p = Path(".planning/phases/06.4-conditional-and-formset-correctness-lifecycle")
spec = spec_from_file_location("runner", p / "15-evidence/run.py")
runner = module_from_spec(spec)
spec.loader.exec_module(runner)
packet = json.loads((p / "18-evidence/results.json").read_text())
manifest = runner.source()

copy = deepcopy(packet)
copy.pop("checker_control_evidence")
runner.validate(copy, manifest)  # ACCEPTED; should reject absent detailed controls.

copy = deepcopy(packet)
for record in copy["checker_control_evidence"].values():
    record.update(returncode=0, stdout="PHASE64_MATRIX_OK", stderr="")
runner.validate(copy, manifest)  # ACCEPTED; contradicts rejected summary.

copy = deepcopy(packet)
case = next(c for c in copy["gates"]["conditional-browser"]["browser"]["cases"]
            if c["theme"] == "stock" and c["id"] == "gap-ambiguity")
case["captures"] = []
runner.validate(copy, manifest)  # ACCEPTED; required stock inventory absent.

copy = deepcopy(packet)
case = next(c for c in copy["gates"]["conditional-browser"]["browser"]["cases"]
            if c["theme"] == "stock" and c["id"] == "gap-ambiguity")
case["captures"][0]["sha256"] = "stale"
runner.validate(copy, manifest)  # ACCEPTED; provenance inconsistent.
~~~

Run the snippets with PY from repository root. They do not edit the packet or screenshot files. This is a reproducible bad acceptance, not an opinion inferred from code style.

### Current Broad Evidence and Prior Regression Preservation

| Current route | Recorded result |
|---|---|
| Django4.2/5.2/6.0 focused | 433/433/433 passes, no skips |
| Enabled full | 7820/7821/7821 passes |
| Ordinary Node-free full | 7819/7820/7820 passes |
| Python total | 48,220 passing executions; three deliberate missing-runtime tracer failures separate |
| Ordinary JavaScript | 347 passes across9 files; complete selection |
| Required Django integration | 2 Vitest passes including six real outer/nested × native/default round trips and invalid-runtime control |
| Runner self-tests | 37 passed; existing real capture results reused |
| Browser | Stock/native conditional24 cases/172 assertions plus modal12/133; total36/305; no page errors |
| Quality | Strict docs and scoped23-file Ruff check/format passed |
| Negative evidence controls | 25 genuine failed subprocesses, each containing rejection diagnostics |

This verifier independently repeated the prior-report extraction: existing test references from other phases' *-VERIFICATION.md files yield58 Python paths, of which four are helper/model/view/conftest files. **All54 actual test files are present in every one of the six current full collection inventories.** They include the seven paths absent from the old47-file table: test_delete_databases.py, test_delete_inspection.py, test_delete_join_identity.py, test_delete_migration_docs.py, test_delete_provenance.py, test_guardian_content_type_docs.py and test_guardian_content_types.py. Cited adapters/formset/list.filter/modal/viewset JS suites and modal-focus.cjs remain covered. This is collection/evidence reconciliation, not54 new executions.

Only established exclusions remain: Django4.2/5.2 full routes skip test_assets.py::test_django6_builtin_csp_nonce_roundtrip because built-in CSP middleware requires Django6; floor Django4.2/6.0 full routes deselect test_form_buttons_golden.py::test_filter_form_baseline for known wrapper whitespace. Across six full routes this is four CSP skip events and four golden deselections. Controls golden remains selected. No new mandatory exclusion or skip was accepted. Prior06-UAT approval remains scoped to its original phase.

### Requirements Coverage

All eleven phase-scoped IDs appear in plans and REQUIREMENTS; no orphan requirement was found. Global Phase06.4 checkboxes remain pending. AUTH-02's existing checkbox and named6.2 history are unchanged; only the A19 contribution is assessed.

| Requirement | Source plans including gap work | Verdict and evidence |
|---|---|---|
| COND-01 |01,08–10,14,16–19|SATISFIED implementation — exact binding, frozen ambiguous state, unique recovery, escaped names and real submitted-row tracer.|
| COND-02 |05,06,08,10,13,14,16,18,19|SATISFIED implementation — independent/all-ancestor/frozen owners, action buttons, values and focus.|
| COND-03 |05,08,10,14,16,18,19|SATISFIED automated scope — actual default/cancelled reset, scoped dynamic management state; generic unclassified fallback11 remains flagged.|
| COND-04 |02,08–10,17–19|SATISFIED bounded persistence — native values, stored references, trusted disabled precedence; H2 enforcement remains UNVERIFIED.|
| COND-05 |02,03,09,10,17–19|SATISFIED — E312/shared runtime resolver, custom explicit values and inherited invariants.|
| FSET-01 |04,06,08–11,16–19|SATISFIED implementation — current repeated/late reclean rejection before any main/sibling/nested save; no new PK/authority claim.|
| FSET-02 |01,05,06,08–10,13,14,16–19|SATISFIED implementation — public roots/events, scoped controllers, optional DELETE and stable capabilities, serialization/widgets.|
| FSET-03 |07–10,12,13,16–19|SATISFIED scoped A19 — non-first/deeper int/UUID fragment→management→POST/DB and retained authorization/ancestry.|
| LIFE-01 |08,10,16,18,19|NEEDS HUMAN H1 — current automated36/305 and corrected UI evidence pass; no human accessibility acceptance.|
| LIFE-02 |04,09–12,15,17–19|BLOCKED G6 — repaired documented behavior and original runtime controls pass; corruption/capture enforcement incomplete, independent high security gate remains open.|
| AUTH-02 |07,10,12,16,18,19 (A19 only)|SATISFIED contribution — successful authorized sibling/deeper round trips; preserve all unrelated6.2 boundaries/exclusions.|

### Test Quality Audit

| Test family | Linked requirement | Active/skipped and strongest assertion | Verdict |
|---|---|---|---|
| Conditional layout/persistence/checks/group | COND-01/04/05 | Actual renderer→JS→FormData→refreshed DB; native saved values, storage spies and invariants. Tracer deliberately uncollected only on ordinary Python route. | Behavioral; bounded image/reference claim retained. |
| Policy and validation gate | FSET-01 | Repeated all_valid→full_clean→all_valid; real HTTP after later sibling/child cleaning, zero saves, unchanged rows and positive controls. | Behavioral; original missing reclean coverage repaired. |
| Formset/toggle JS and native integration | COND-01/02/03,FSET-02/03 | Zero/two/one matches, actual controls, stable identity, final ORDER/DELETE payloads and real native-Django markup. | Behavioral; original masking fixtures repaired. |
| Runtime-contract | LIFE-02 | Clean temporary copy with Node-only PATH and no nox/venv; complete other ordinary files, explicit missing/invalid integration failures. | Behavioral; no hosted-CI execution claim. |
| Stock/native browser | LIFE-01 | Real authenticated CSRF requests, 422, save counters, DB/storage, native reset/focus; all named assertions pass. | Automated scope meaningful; H1 absent, native captures empty. |
| Published docs | LIFE-02 | Actual fence execution and complete projection/migration assertions,18 cases/series. | Value/behavior proof; no copied self-generated oracle. |
| Successor validator | LIFE-02 |37 self-tests,25 controls; actual new mutated copies still accepted. | INSUFFICIENT enforcement — WR-03/04, G6. |

No disabled-only requirement test or circular generated expected-output fixture was found in the phase-linked tests. Browser writes record observations; integration writes a temporary driver, not an expected golden. No unreferenced TBD/FIXME/XXX marker was found in the inspected modified implementation/test/runner paths. Initial empty collections and legitimate native no-op returns are not production placeholders.

Disconfirmation was explicit: LIFE-02 is only partly satisfied; green checker_controls summary is misleading without detailed records; conditional stale/missing-capture error handling lacks rejection coverage. Native screenshot .every() assertions over [] are vacuous, so they are not claimed as native visual evidence. Actual current stock PNG hashes were independently checked outside the defective checker.

### Decision Coverage

Owner query: {skipped:false, blocking:false, total:19, honored:19, not_honored:[]}.

**All trackable CONTEXT.md decisions are honored by shipped artifacts.** This is a heuristic mention/coverage result, not a replacement for behavioral verification. D-02/D-11/D-12/D-14/D-15 now have discriminating repaired behavior. D-08's native reference behavior is proven separately from H2's unverified enforcement.

The eight GAP-COVERAGE research rows are retained: responsibility, identity, disabled lifecycle, persistence matrix, A19/projection, runtime, evidence, compatibility. Source/tests substantiate the first six and compatibility within their declared bounds. The evidence row is **partial** because WR-03/04 remain. No new package, distributed lock, custom-PK compatibility, theme adapter or storage authority was inferred.

### Fallback Edge Assumptions

All31 handoff rows retain **flagged-unresolved**; none is silently converted into a new passing truth. These are generic probe categories, not31 independently specified acceptance behaviors. Their bounded requirement evidence is assessed below. Generic concurrency/precision claims are not proved by serial examples; no new API or backend scope follows from the labels. The unclassified COND-03 item lacks a separately testable invariant. Human review of these qualifications is recommended at the existing acceptance checkpoint; the flags remain visible without inventing31 additional product failures.

| ID | Requirement / category | Retained status | Canonical bounded adjudication |
|---|---|---|---|
| 1 | AUTH-02 / concurrency | flagged-unresolved | A19 authorization/ancestry is exercised per request; concurrent-request serializability is unclaimed. |
| 2 | COND-01 / boundary | flagged-unresolved | Exact-name zero/one/multiple, escaped names, nested/two-form isolation and recovery are exercised; no numeric precision contract is introduced. |
| 3 | COND-01 / adjacency | flagged-unresolved | Exact-name zero/one/multiple, escaped names, nested/two-form isolation and recovery are exercised; no numeric precision contract is introduced. |
| 4 | COND-01 / empty | flagged-unresolved | Exact-name zero/one/multiple, escaped names, nested/two-form isolation and recovery are exercised; no numeric precision contract is introduced. |
| 5 | COND-01 / encoding | flagged-unresolved | Exact-name zero/one/multiple, escaped names, nested/two-form isolation and recovery are exercised; no numeric precision contract is introduced. |
| 6 | COND-01 / ordering | flagged-unresolved | Exact-name zero/one/multiple, escaped names, nested/two-form isolation and recovery are exercised; no numeric precision contract is introduced. |
| 7 | COND-01 / precision | flagged-unresolved | Exact-name zero/one/multiple, escaped names, nested/two-form isolation and recovery are exercised; no numeric precision contract is introduced. |
| 8 | COND-02 / adjacency | flagged-unresolved | Baseline/frozen/ancestor composition and both orders are exercised; no universal DOM-layout guarantee. |
| 9 | COND-02 / empty | flagged-unresolved | Baseline/frozen/ancestor composition and both orders are exercised; no universal DOM-layout guarantee. |
| 10 | COND-02 / ordering | flagged-unresolved | Baseline/frozen/ancestor composition and both orders are exercised; no universal DOM-layout guarantee. |
| 11 | COND-03 / unclassified | flagged-unresolved | Native default/cancelled scoped reset is exercised; unclassified detector item has no additional specified invariant. |
| 12 | COND-04 / idempotency | flagged-unresolved | Repeated native clearing and trusted disabled persistence are exercised; no concurrent storage/app-hook or deletion authority guarantee. |
| 13 | COND-04 / concurrency | flagged-unresolved | Repeated native clearing and trusted disabled persistence are exercised; no concurrent storage/app-hook or deletion authority guarantee. |
| 14 | COND-05 / adjacency | flagged-unresolved | Static/runtime unsupported and explicit-value/invariant cases are exercised; arbitrary custom-field semantics require configuration. |
| 15 | COND-05 / empty | flagged-unresolved | Static/runtime unsupported and explicit-value/invariant cases are exercised; arbitrary custom-field semantics require configuration. |
| 16 | COND-05 / ordering | flagged-unresolved | Static/runtime unsupported and explicit-value/invariant cases are exercised; arbitrary custom-field semantics require configuration. |
| 17 | FSET-01 / adjacency | flagged-unresolved | Reclean/late-clean identity and edit-only errors reject before saves; no cross-request lock or universal backend guarantee. |
| 18 | FSET-01 / empty | flagged-unresolved | Reclean/late-clean identity and edit-only errors reject before saves; no cross-request lock or universal backend guarantee. |
| 19 | FSET-01 / ordering | flagged-unresolved | Reclean/late-clean identity and edit-only errors reject before saves; no cross-request lock or universal backend guarantee. |
| 20 | FSET-01 / idempotency | flagged-unresolved | Reclean/late-clean identity and edit-only errors reject before saves; no cross-request lock or universal backend guarantee. |
| 21 | FSET-01 / concurrency | flagged-unresolved | Reclean/late-clean identity and edit-only errors reject before saves; no cross-request lock or universal backend guarantee. |
| 22 | FSET-02 / idempotency | flagged-unresolved | Repeated init/disposal and isolated forms are exercised; concurrent asynchronous insertion semantics beyond existing protocol are unclaimed. |
| 23 | FSET-02 / concurrency | flagged-unresolved | Repeated init/disposal and isolated forms are exercised; concurrent asynchronous insertion semantics beyond existing protocol are unclaimed. |
| 24 | FSET-03 / boundary | flagged-unresolved | Bounded int/UUID coordinates, nested siblings and authorization are exercised; arbitrary PK precision/concurrency remains outside the declared protocol. |
| 25 | FSET-03 / precision | flagged-unresolved | Bounded int/UUID coordinates, nested siblings and authorization are exercised; arbitrary PK precision/concurrency remains outside the declared protocol. |
| 26 | FSET-03 / concurrency | flagged-unresolved | Bounded int/UUID coordinates, nested siblings and authorization are exercised; arbitrary PK precision/concurrency remains outside the declared protocol. |
| 27 | LIFE-01 / adjacency | flagged-unresolved | Both-theme real lifecycle/reset/ordering is exercised; H1 human accessibility remains pending. |
| 28 | LIFE-01 / empty | flagged-unresolved | Both-theme real lifecycle/reset/ordering is exercised; H1 human accessibility remains pending. |
| 29 | LIFE-01 / ordering | flagged-unresolved | Both-theme real lifecycle/reset/ordering is exercised; H1 human accessibility remains pending. |
| 30 | LIFE-02 / empty | flagged-unresolved | Executable docs/runtime failures are exercised, but G6 specifically proves missing-control/capture rejection incomplete. |
| 31 | LIFE-02 / encoding | flagged-unresolved | Executable docs/runtime failures are exercised, but G6 specifically proves missing-control/capture rejection incomplete. |

### Anti-Patterns, Security and Advisory

| Finding | Severity | Evidence / impact |
|---|---|---|
| WR-03, runner:984–985 | Review WARNING; canonical BLOCKER G6 | Summary rejection labels can conceal absent or successful detailed controls. Deterministic current counterexamples; E3 fails. |
| WR-04, runner:857,890–924 | Review WARNING; canonical BLOCKER G6 | Historical canonical-check exit substitutes for current conditional screenshot inventory/bytes. Deterministic current counterexamples; E3 fails. |
| T-06.4-22/28/33 | HIGH, OPEN | Independent security audit links these three obligations to evidence enforcement. No acceptance/transfer. |
| T-06.4-35 | HIGH, OPEN | Actual end-of-phase independent/human dispositions are incomplete; prepared attribution guards do not supply the outcomes. |
| T-06.4-36 | HIGH, OPEN | Descriptor-less H2 has no genuine enforcement or attributed disposition. |
| T-06.4-31 | MEDIUM, OPEN | Conditional capture-count/hash revalidation absent; below high threshold but still unresolved. |

Independent security accounting is **31/37 closed;6 open in total, of which5 high block**. The report's threats_open=5 is the blocking high count, not total open count. UI24/24 closes its original fixture warnings only. Current VALIDATION frontmatter is **status: partial; nyquist_compliant: false**; no stale historical compliant paragraph overrides it. No unrelated tests were generated to force compliance.

**Advisory (new scope, unevidenced): None.** WR-03/04 are not unsupported scope expansion: they concern carried G6, occur in the successor runner modified since the prior verified timestamp (commits229a4d0,944d6a5,36c27bf), and independently reproduce deterministic bad acceptance. No completed product truth is reverted on an unevidenced opinion.

### Canonical Prohibition Disposition

Exact authored PLAN02 prohibition: **“Switching a conditional file field off must not silently authorize deletion of the stored file content.”** Its authored status=resolved and verification=test do not establish enforcement. This verifier called the installed enforcement owner with the actual item and no invented descriptor. It returned:

~~~json
{"status":"unverified","flagged":true,"tier":"test","located":false,"kind":null,"evidence":[],"mode":"interactive"}
~~~

Reason: test-tier prohibition has no passing wired enforcement check; fail closed. **unverified-prohibition — human review recommended.** Native False-clear/None-no-change, unchanged-inline save, storage-delete spies and retained bytes are bounded implementation observations. They are not a locatable enforcement descriptor, application-hook guarantee, fail-first detector or human approval.

### Human Verification Required

#### H1 — Corrected stock/native host and accessibility

**Test:** A real person reviews nested Add/Delete/Move discoverability, full labels/error readability, keyboard/Space/Tab orientation, hidden-content focus, actual reset, modal422 replacement and assistive-technology announcements in both corrected stock and native hosts. Inspect desktop/mobile/tablet evidence and directly evaluate native rendering.

**Expected:** Controls remain discoverable, labels/errors readable, focus usable and announcements coherent in the exercised flows. Record person, timestamp, browser/assistive technology, environment, observed results and limits against source/evidence hashes.

**Why human:** Three stock screenshots, headless Chromium and a positive agent UI score do not certify human usability, native visual behavior, physical devices or screen readers. Native capture inventory is zero. H1 has no actor/time/response.

#### H2 — Exact file-off deletion prohibition

**Test:** Review the exact prohibition above with native reference-clearing/storage evidence, reference-only ImageField and consuming-application hook limits. Supply an actual attributed bounded disposition or a genuine locatable enforcement route.

**Expected:** Switching off does not silently grant storage-content deletion authority. Any disposition identifies the supported boundary and remaining app responsibility; any enforcement is real and demonstrated.

**Why human:** No descriptor or attributed response exists. Ordinary storage tests and earlier06-UAT do not settle this separate item. H2 remains flagged-unverified, and T36 remains high/open.

No literal PLAN <verify><human-check> block exists to harvest; plan19 and handoff explicitly preserve these two end-of-phase items. They remain in pending_human_checks frontmatter despite the higher-priority gaps_found status. No approval is invented and no mid-run human checkpoint is demanded.

### Deferred Items and Scope

No current gap is deferred. The roadmap analysis identifies Phase7 as theme-surface naming/classification/stability documentation with an explicit06.4 dependency; it does not schedule checker corruption validation or these human/enforcement outcomes. G6 therefore remains actionable now.

Retain #210/jQuery, A8 public/internal commit=False final-policy classification, A25 and broader Guardian#286/custom-PK/backend/field/theme boundaries. AUTH-02 remains A19-only. ImageField evidence covers stored references and disabled initial=None/no-change, not image decoding/dimension hooks or nonempty disabled-image validation. Demonstrated environment is Python3.12.3, Django4.2.30/5.2.18/6.0.9 and cached Chromium149.0.7827.55. No wider browser/device/Python certification.

### Fingerprint, History and Ownership

covered_files and covered_digest above are copied verbatim from **gsd_run query verification.fingerprint**, which automatically includes all38 current PLAN/SUMMARY files. It covers the changed implementation/tests/docs, prior regression paths, current runner/results/manifest, three stock PNGs and direct independent reports.

The handoff JSON intentionally is **not fingerprinted**: it embeds this canonical report's hash and the parent must rebind that hash after this write. Including both would create a circular digest. The report uses direct independent reports and packet/manifest as evidence instead. Shared planning-root STATE/ROADMAP/REQUIREMENTS/config/WINDOWS/state.json are outside the fingerprint; they are tracking, not implementation evidence. Their read contracts are captured here.

The previous canonical report was moved unchanged into the dated superseded path. Only this report, that historical copy and six Phase06.4 REQUIREMENTS traceability descriptions were changed; global pending checkboxes and AUTH-02/6.2 history remain untouched. Existing unrelated changes were preserved. No commit, phase.complete, new source or handoff mutation was performed.

### Gaps Summary and Next Action

**One consolidated goal gap remains: G6**, with two concrete repairs WR-03/04. Original G1–G5 and WR-01/02 close within their verified bounds. Five high security obligations and H1/H2 independently prevent acceptance;31 surfaced assumptions remain explicitly flagged.

Repair the detailed-control and current-capture validators with discriminating corruption tests, refresh only affected source-bound evidence and obtain independent code/security reassessment. Gather genuine end-of-phase H1/H2 outcomes or real H2 enforcement. Rebind the handoff to this canonical report without changing ready=false. Re-verify; do not advance Phase7 or claim complete.

_Verified: 2026-11-01T17:33:24Z_
_Verifier: gsd-verifier; no commit or phase completion performed._

