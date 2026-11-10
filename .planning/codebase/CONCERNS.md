---
last_mapped_commit: 60c46599983916590d6e6f03af66c78751438ad1
last_mapped_at: 2026-11-10
---
# Codebase Concerns

**Analysis Date:** 2026-11-10

## Tech Debt

**Settings snapshot at module import:**
- Issue: `CrudViewsSettings` fields are populated from Django settings in the model class body (including the Phase 06.18 `CRUD_VIEWS_ANCESTOR_*` settings), and template-tag registration captures `theme_path` in decorators. `override_settings()` does not refresh captured configuration.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`
- Impact: tests and applications that vary CRUD settings after app initialization see stale values; template registration cannot be switched dynamically.
- Fix approach: distinguish startup-only from runtime settings; make runtime reads lazy or respond to `setting_changed`.

**No-op public management command:**
- Issue: `crud_views_show` is registered, but `handle()` only executes `pass` (comment: "placeholder command").
- Files: `src/crud_views/management/commands/crud_views_show.py`
- Impact: `manage.py help` advertises a command that does nothing.
- Fix approach: implement ViewSet/URL inspection or remove it.

**Large central modules concentrate unrelated behavior:**
- Files: `src/crud_views/lib/view/base.py` (1224 lines), `src/crud_views/templatetags/crud_views.py` (667), `src/crud_views/lib/view/buttons.py` (599), `src/crud_views/lib/ancestors.py` (559), `src/crud_views/lib/formsets/formsets.py` (544), `src/crud_views/lib/viewset/__init__.py` (534)
- Impact: shared changes have broad regression surfaces; `base.py` has grown since the previous map.
- Fix approach: extract cohesive subsystems behind current public APIs only when a concrete maintenance need justifies it.

**Ancestor authorization subsystem is new and multi-module:**
- Issue: Phase 06.18 added ancestor authorization across `ancestors.py`, `ancestor_db.py`, `ancestor_policy.py`, with hooks in `viewset/__init__.py`, `breadcrumb.py`, `resource.py`, `views/delete.py`, `views/manage.py`, and `crud_views_polymorphic/lib/create_select.py`. Behavior is configured by three settings dicts (cascade, read, write permissions).
- Impact: new cross-cutting path with hidden state in settings; per CLAUDE.md maintainability rule, changes need to remain traceable by the developer.
- Fix approach: modify via the existing `tests/test1/test_ancestor_*.py` suite (cost, database, guardian, migration, redirect coverage); keep it opt-in/bounded.

## Known Bugs

**Polymorphic create accepts unvalidated content-type ids (code-inspection concern, still open):**
- Symptoms: `polymorphic_model` does `ContentType.objects.get(id=...)` with no handling, so a missing id raises `ContentType.DoesNotExist` (500). `get_form_class` raises `ValueError` for types absent from `polymorphic_forms`, and its message dereferences `self.object`, which does not exist on the create view (likely `AttributeError` instead of the intended error). The URL path only constrains the id to an int.
- Files: `src/crud_views_polymorphic/lib/utils.py` (`polymorphic_model`, `get_form_class`), `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/create_select.py`
- Trigger: request a polymorphic create URL with a nonexistent or non-configured content type id.
- Workaround: none beyond not exposing arbitrary ids. Fix: return 404 for unknown/unconfigured ids and use `self.polymorphic_model` in the error message.

## Security Considerations

**Runtime contracts use Python assertions:**
- Risk: `assert` is stripped under `python -O`, so these guards vanish in optimized deployments.
- Files: `src/crud_views/lib/view/base.py` (lines ~674, 1110, 1118, 1162), `src/crud_views/lib/views/create.py` (94), `src/crud_views/lib/formsets/formsets.py` (240, 530), `src/crud_views/lib/formsets/inline_formset.py`, `src/crud_views/templatetags/crud_views.py` (81), `src/crud_views_workflow/lib/mixins.py` (29, 36, 40), `src/crud_views_polymorphic/lib/utils.py` (14), `src/crud_views_guardian/lib/views.py` (373), `src/crud_views_guardian/lib/mixins.py` (240)
- Current mitigation: system checks catch several configuration errors. The guardian `assert not isinstance(user, str)` guards are the most security-relevant.
- Recommendations: raise explicit exceptions for correctness/security conditions; keep assertions for internal invariants.

## Performance Bottlenecks

**Delete preview limit does not bound inspection cost:**
- Problem: `cv_delete_preview_limit` limits visible entries only after full cascade inspection and visibility filtering.
- Files: `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/deletion.py`, `tests/test1/test_delete_preview_limit.py`
- Improvement path: document as display limit; profile real cascades before designing bounded inspection.

**Guardian permission checks can repeat per rendered object/action:**
- Files: `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/views/card.py`
- Cause: permission evaluation is part of each item's action visibility.
- Improvement path: profile large lists; consider request-scoped `ObjectPermissionChecker` reuse. Ancestor checks add further per-request queries; `tests/test1/test_ancestor_costs.py` pins current costs.

**Resource default lookup is linear:**
- Files: `src/crud_views/lib/resource.py`
- Cause: `cv_get_item()` scans the list from `cv_get_items()`.
- Improvement path: override lookup for sources with direct key access.

## Fragile Areas

**ViewSet registration, routing, and metaclass integration:**
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/path_regs.py`, `src/crud_views/checks.py`
- Why fragile: views register at class construction; routing depends on shared registry, parent chain, PK shape, and checks.
- Safe modification: preserve import-safety constraints in `src/crud_views/lib/resource.py`; test nested URLs and checks for affected combinations.
- Test coverage: broad in `tests/test1/`.

**Template and theme extension surface:**
- Files: `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/icons.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`
- Why fragile: themes consume class keys, button context, icons, template variables and JS adapters as one contract.
- Safe modification: update docs and golden tests with public surface changes; keep escaping at existing boundaries.
- Test coverage: built-in output covered; third-party themes not exercised.

**Nested formset rendering and persistence:**
- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/mixins.py`, `src/crud_views/lib/formsets/inline_formset.py`
- Why fragile: management forms, indexes, save order and errors must align between server and JS cloning.
- Safe modification: cover GET, invalid POST, deletion, nested indexes, transactions.

**Workflow permission recipe and helper boundaries:**
- Files: `src/crud_views_workflow/lib/execution.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/lib/mixins.py`, `docs/reference/workflow_view.md`, `tests/test1/test_workflow_permissions.py`, `tests/test1/test_workflow_execution.py`
- Boundary: `run_transition()` requires persisted actor/object on the chosen write alias; direct django-fsm calls bypass helper validation/history; `workflow_check_transition()` is business validation, not authorization. Page gate and transition permissions stay independent.
- Coverage: request-level tests exist; concurrency and Guardian/nested-object matrices are unverified. These are supported boundaries, not defects.

**Object-detail migration and template ownership:**
- Boundary: model help defaults off, scalar choices show labels. Copied value templates keep old behavior until updated.
- Files: `src/crud_views_object_detail/lib/conf.py`, `src/crud_views_object_detail/lib/resolvers.py`, `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`, `docs/migrating-1.0.md`
- Safe adoption: use documented help restoration or `choices_display=False`; cached settings are startup config.

## Scaling Limits

**Resource lookup and list materialization:**
- Current capacity: `Resource.cv_get_items()` returns a plain list with O(n) default lookup.
- Limit: large external datasets incur full-read memory and linear lookup.
- Scaling path: add paginated/source-native lookup only if large remote collections become supported.

## Dependencies at Risk

**Django 4.2 support line:**
- Risk: upstream support status is time-sensitive; Django 4.2 is past upstream end of life per its published schedule (April 2026), yet the test matrix still includes it (`CLAUDE.md`, `noxfile.py`).
- Impact: security fixes unavailable upstream for that floor.
- Migration plan: decide whether to raise the floor before 1.0.0 via the documented migration process (`docs/migrating-1.0.md`).

## Missing Critical Features

None independently confirmed.

## Test Coverage Gaps

**Polymorphic invalid content-type URL cases:**
- What's not tested: nonexistent ids and unconfigured subtype ids on direct create (no such test in `tests/test1/test_polymorphic.py`, `test_optional_polymorphic.py`, `test_cancel_polymorphic.py`).
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`
- Risk: server errors go unnoticed.
- Priority: High

**Custom user model without `username` in manage view:**
- What's not tested: `CRUD_VIEWS_MANAGE_SHOW_USERS` with an email-only user model; `manage.py` queries `values_list("username")` and `order_by("username")` directly.
- Files: `src/crud_views/lib/views/manage.py` (lines ~87-88)
- Risk: `FieldError` for custom user models.
- Priority: Medium

**Third-party theme contract compatibility:**
- What's not tested: consumer theme overrides across variables, class keys, icons, JS adapters.
- Files: `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`, `docs/development/stability.md`
- Priority: Medium

**Human acceptance items:**
- What's not tested: other-browser, assistive-technology, visual and real third-party theme approval were excluded from the Phase 06.17 review.
- Files: `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-UI-REVIEW.md`
- Priority: Low

**Phase 06.21 snippet-context review follow-ups (all Info, open):**
- What is not tested / documented: Django `{% if %}` operator expressions swallow exceptions from lazy parent resolution; card filter-header snippet behavior; release-proof identification of the snippet-context changelog entry; and top-level `cv_assert_parent()` error behavior.
- Files: `docs/reference/templates.md`, `src/crud_views/lib/view/base.py`, `tests/test1/test_snippet_context.py`, `tests/test1/test_snippet_docs.py`
- Risk: documentation can overstate 404 behavior for operator expressions, a separately implemented card header can drift, and documentation guards can fail on unrelated later changelog edits. Calling `cv_assert_parent()` on a top-level ViewSet raises `AttributeError` because its message references undefined `self.cv_name`; it also repeats an assertion.
- Priority: Low (recorded Info findings IN-01 through IN-04 in `.planning/phases/06.21-snippet-context-exposes-view-and-parent-object/06.21-REVIEW.md`; disposition remains open in `06.21-REVIEW-DISPOSITION.md`).

## Resolved Since Previous Audit

- Phase 06.18 ancestor authorization for nested ViewSets shipped with a dedicated `tests/test1/test_ancestor_*.py` suite (databases, guardian, costs, redirect, migration, docs).
- Earlier resolved: object-detail accordion/tab lifecycle (Phase 06.17), protected delete labels not linked (`src/crud_views/lib/views/delete.py`), workflow opt-in permission request-level tests (`tests/test1/test_workflow_permissions.py`).
- Phase 06.21 review warnings WR-01 and WR-02 are fixed: template-context documentation now reflects button/child-column contexts, and `tests/test1/test_snippet_docs.py` checks runtime metadata keys. The four Info findings IN-01 through IN-04 remain open and are recorded above.

## ViewSet Label Boundaries (Phase 06.20)

- Lazy overrides deliberately receive no construction-time blank check: evaluating them during app loading can raise `AppRegistryNotReady`. Plain blank strings fail validation; padded strings remain unchanged (`src/crud_views/lib/viewset/__init__.py`, `tests/test1/test_viewset_verbose_name.py`).
- Model-centric deletion/404 text keeps model names; short action labels contain no object name. These are documented scope boundaries (`docs/reference/nested.md#labels`).
- Canonical verification passes 15/15 truths; security reports nine closed threats. No required human check remains. Responsive long-label/browser checks are optional downstream work; the supported-version matrix remains a CI condition (`.planning/phases/06.20-viewset-verbose-name-override-for-every-default-label/06.20-VERIFICATION.md`).

## Permission declaration boundaries (Phase 06.22)

- Undeclared core permission keys now fail startup with `viewset.E269`; this closes the previous delayed-discovery gap for `cv_permission` and effective ancestor pairs (`src/crud_views/checks.py`).
- Checks deliberately validate metadata only. They cannot establish that migrations created auth rows or that users hold grants; applications must migrate and grant permissions as documented (`docs/reference/custom_form_view.md`).
- Guardian/Resource paths are excluded, and checks defer when URLconf completion fails. Existing request-time diagnostics remain necessary; exclusions are tested rather than treated as complete startup coverage (`tests/test1/test_permission_declarations.py`).
- Shared helpers add no startup database queries; runtime permission-map query behavior is preserved (`tests/test1/test_viewset.py`, `tests/test1/test_permission_declarations.py`). Existing concerns above remain outside this phase's scope.

---

*Concerns audit: 2026-11-10*
