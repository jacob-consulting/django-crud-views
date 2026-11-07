---
last_mapped_commit: 8e1298538ef8e45fcc5c6eede15e3c6c3c067271
last_mapped_at: 2026-11-07
---
# Codebase Concerns

**Analysis Date:** 2026-11-07

## Tech Debt

**Settings snapshot at module import:**
- Issue: `CrudViewsSettings` fields are populated from Django settings in the model class body, and template-tag registration captures `theme_path` in decorators. `override_settings()` does not refresh captured configuration; changing the theme path after import is unsupported.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`
- Impact: tests and applications that vary CRUD settings after app initialization may see stale values; template registration cannot be switched dynamically.
- Fix approach: distinguish startup-only settings from runtime settings; make runtime reads lazy or respond to `setting_changed`. Template registration needs a deliberate dynamic-resolution design.

**No-op public management command:**
- Issue: `crud_views_show` is registered, but `handle()` only executes `pass`.
- Files: `src/crud_views/management/commands/crud_views_show.py`
- Impact: `manage.py help` advertises a command that provides no behavior.
- Fix approach: implement its documented ViewSet/URL inspection purpose or remove it until useful.

**Large central modules concentrate unrelated behavior:**
- Issue: shared view behavior, button rendering, template tags, formsets, and ViewSet routing have large modules.
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/viewset/__init__.py`
- Impact: shared changes have broad regression surfaces and are harder to review in isolation.
- Fix approach: extract cohesive subsystems behind current public APIs only when a concrete maintenance need justifies the added abstraction.

## Known Bugs

**Polymorphic create accepts unvalidated content-type ids (code-inspection concern):**
- Symptoms: direct `polymorphic_model` lookup may raise `ContentType.DoesNotExist` for a missing id; direct create does not appear to repeat the selection view's allowed-subtype filtering.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/create_select.py`
- Trigger: request a polymorphic create URL with a nonexistent content type id or a type outside the configured subtype set.
- Workaround: use `polymorphic_forms` only for intended child models and avoid exposing arbitrary ids. This remains an inspection finding; runtime reproduction is not recorded.

## Security Considerations

**Runtime contracts use Python assertions:**
- Risk: `assert` statements are removed under optimized Python (`-O`), so conditions used as runtime validation do not protect those paths in optimized deployments.
- Files: `src/crud_views/lib/views/create.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/lib/mixins.py`
- Current mitigation: Django system checks catch several related configuration errors, but assertions remain in runtime paths.
- Recommendations: use explicit exceptions for conditions required for correctness or security; reserve assertions for internal invariants.

## Performance Bottlenecks

**Delete preview selection budget does not bound inspection or query cost:**
- Problem: `cv_delete_preview_limit` limits visible selected occurrences; it is applied after deletion inspection and visibility filtering. It does not cap full cascade inspection, database work, or traversal of hidden/unselected entries.
- Files: `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/deletion.py`, `tests/test1/test_delete_preview_limit.py`
- Cause: the display selection must preserve deletion-authority and visibility semantics while inspection computes the complete deletion graph.
- Improvement path: document it strictly as a display limit. If inspection cost becomes a measured bottleneck, profile real cascade shapes before designing a bounded or database-native inspection mechanism.

**Guardian permission checks can repeat per rendered object/action:**
- Problem: object permission checks in per-item list/card rendering can multiply by rows and available actions; request-level reuse/prefetch is not guaranteed across these paths.
- Files: `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/views/card.py`
- Cause: permission evaluation is integrated into each item's action visibility.
- Improvement path: profile representative large lists, then consider request-scoped `ObjectPermissionChecker` reuse and permission prefetching if repeated queries are confirmed.

**Resource default lookup is linear:**
- Problem: `Resource.cv_get_item()` scans the full list returned by `cv_get_items()` until it finds a matching key.
- Files: `src/crud_views/lib/resource.py`
- Cause: the base implementation is list-oriented and materializes rows for lookup.
- Improvement path: override lookup for sources with direct key access; retain the default for small read-all collections.

## Fragile Areas

**ViewSet registration, routing, and metaclass integration:**
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/path_regs.py`, `src/crud_views/checks.py`
- Why fragile: view classes register during class construction; routing depends on the shared registry, parent relationships, model PK shape, and configuration checks.
- Safe modification: preserve import-safety constraints in `src/crud_views/lib/resource.py`. Cover class declaration, duplicate/invalid registration, nested URLs, and Django checks for affected combinations.
- Test coverage: broad behavior exists in `tests/test1/`; add focused regressions for new parent, PK, and view-declaration combinations.

**Template and theme extension surface:**
- Files: `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/icons.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`
- Why fragile: themes consume class keys, button context, icon identifiers, template variables, and JavaScript adapters as a coordinated contract.
- Safe modification: update reference docs and theme/golden tests when the public surface changes; retain escaping at existing rendering boundaries.
- Test coverage: built-in output has golden and integration coverage; third-party theme compatibility is not exhaustively exercised.

**Nested formset rendering and persistence:**
- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/mixins.py`, `src/crud_views/lib/formsets/inline_formset.py`
- Why fragile: management forms, generated indexes, parent-child save order, and validation errors must align across server rendering and JavaScript cloning.
- Safe modification: cover GET rendering, invalid POST re-render, deletion, nested indexes, and transaction behavior for affected combinations.
- Test coverage: focused tests are extensive; the combination space remains a maintenance risk.

**Workflow permission recipe scope:**
- Files: `docs/reference/workflow_view.md`, `tests/test1/test_workflow_permissions.py`
- Why fragile: the opt-in recipe selects the page's `view` gate and adds explicit transition permission rules; other workflow views keep the default `change` gate. It is documented and tested with real requests, including execution recheck and denial behavior.
- Safe modification: preserve independent page authorization and transition authorization; keep default behavior unchanged unless separately intended.
- Test coverage: request-level proof exists. It does not establish concurrency/race behavior or a Guardian/nested-object permission matrix; those remain unverified coverage boundaries, not observed defects.

**Workflow helper contract boundaries:**
- Issue: `run_transition()` is a deliberately bounded execution API: the actor and object must already be persisted on the selected write alias; direct django-fsm decorated-method calls bypass helper validation/history; and `workflow_check_transition()` is model business validation, not a replacement for transition permissions or the view's page permission.
- Files: `src/crud_views_workflow/lib/execution.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/lib/mixins.py`, `tests/test1/test_workflow_execution.py`.
- Impact: callers that bypass the helper or supply unsaved/cross-database identities do not receive the helper's transactional/history guarantees; consumers must retain permission gates separately.
- Safe use: call the exported helper or use `WorkflowView`; keep business checks side-effect-free; place transactional database follow-up in `on_transition()` and external effects in `cv_on_commit()`. Tests cover alias routing, late refusal, rollback, callback timing, identity validation and direct-call boundary. These are supported API boundaries, not known defects.

**Object-detail migration and template ownership:**
- Boundary: automatic model help now defaults to off and scalar choices display labels by default. Existing copied value templates retain their own behavior until updated; raw callback/custom-template values remain available.
- Files: `src/crud_views_object_detail/lib/conf.py`, `src/crud_views_object_detail/lib/resolvers.py`, `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`, `docs/migrating-1.0.md`.
- Safe adoption: use the documented project/view help restoration or per-property `choices_display=False`; preserve badge precedence and escaping when copying leaves. Cached settings are startup configuration; tests explicitly replace the singleton rather than assuming `override_settings()` invalidates cached values.
- Verification: choice/help/query regressions and executable migration recipes cover the supported scalar/collection boundary. This is an intentional migration contract, not an unresolved defect.

## Scaling Limits

**Resource lookup and list materialization:**
- Current capacity: `Resource.cv_get_items()` returns a plain list; default `cv_get_item()` uses a linear scan.
- Limit: large external datasets incur full-read memory and O(n) lookup costs unless subclasses override lookup.
- Scaling path: add paginated/source-native list and direct lookup abstractions only if large remote collections become a supported use case.

## Dependencies at Risk

**Django 4.2 support line:**
- Risk: upstream support status is time-sensitive and not established by repository inspection.
- Impact: consumers may eventually need a newer supported Django series for security fixes and compatibility.
- Migration plan: confirm support policy before release and change the floor through the documented compatibility and migration process.

## Missing Critical Features

No independently confirmed missing critical feature is recorded. The polymorphic direct-create validation concern above is based on code inspection and may warrant a focused reproduction.

## Test Coverage Gaps

**Polymorphic invalid content-type URL cases:**
- What's not tested: nonexistent ids and direct requests for unrelated or excluded subtype ids.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `tests/test1/`
- Risk: server errors or unintended subtype forms may go unnoticed.
- Priority: High

**Custom user model without `username` in manage view:**
- What's not tested: `CRUD_VIEWS_MANAGE_SHOW_USERS` with an email-only user model.
- Files: `src/crud_views/lib/views/manage.py`, `tests/test1/`
- Risk: optional manage diagnostics may fail with a database field lookup error for supported custom user models.
- Priority: Medium

**Third-party theme contract compatibility:**
- What's not tested: consumer theme overrides across template variables, class keys, icons, and JS adapters.
- Files: `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`, `docs/development/stability.md`
- Risk: downstream theme breakage can escape in-repository tests.
- Priority: Medium

**Human acceptance items:**
- What's not tested: the Phase 06.17 review explicitly excludes other-browser, assistive-technology, human visual, and actual third-party theme approval; its audits identify no required human gate left open.
- Files: `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-UI-REVIEW.md`, `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-REVIEW-DISPOSITION.md`
- Risk: the bounded automated/source review does not establish broader browser, accessibility, visual, or downstream theme compatibility.
- Priority: Low

## Resolved Historical Concerns

**Object-detail accordion initial state and tab lifecycle:**
- Status: Phase 06.17 verified 15/15 must-haves. Independent deep review of 19 changed files found zero findings; security review closed all 9/9 threats; UI review passed 24/24 with no required priority fixes. Broader human/browser/accessibility/theme certification remains outside the bounded phase.
- Evidence: `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-VERIFICATION.md`, `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-REVIEW-DISPOSITION.md`, `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-SECURITY.md`, `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-UI-REVIEW.md`.

**Protected delete labels:**
- Status: protected-object entries are not linked; link generation is reserved for selected visible cascade objects. The old concern that protected labels could be linked is resolved.
- Evidence: `src/crud_views/lib/views/delete.py`, `tests/test1/test_delete_preview_limit.py`.

**Workflow opt-in permission evidence:**
- Status: Phase 06.13 now tests actual requests and keeps the page gate independently required. The former gap of lacking request-level authorization evidence is resolved; concurrency and Guardian/nested matrices remain untested as stated above.
- Evidence: `tests/test1/test_workflow_permissions.py`, `.planning/phases/06.13-workflow-permissions-document-and-test-opt-in-per-transition/06.13-01-SUMMARY.md`.

---

*Concerns audit: 2026-11-07*
