---
last_mapped_commit: 38f49b77fdd3ac823a2d31a907b58a433212b423
last_mapped_at: 2026-11-02
---
# Codebase Concerns

**Analysis Date:** 2026-11-02

## Tech Debt

**Settings snapshot at module import:**
- Issue: `CrudViewsSettings` fields are populated from Django settings in the model class body, and template-tag registration captures `theme_path` in decorators. `override_settings()` therefore does not refresh captured configuration and changing the theme path after import is unsupported.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`
- Impact: tests and applications that vary CRUD settings after app initialization may see stale values; template registration cannot be switched dynamically.
- Fix approach: distinguish intentionally startup-only settings from runtime settings, and make runtime reads lazy or respond to Django's `setting_changed` signal. Template names registered by inclusion tags need a deliberate dynamic resolution design.

**No-op public management command:**
- Issue: `crud_views_show` is registered as a Django management command, but `handle()` only executes `pass`.
- Files: `src/crud_views/management/commands/crud_views_show.py`
- Impact: `manage.py help` advertises a command that produces no output or useful behavior.
- Fix approach: implement the documented ViewSet/URL inspection purpose or remove the command until it has behavior.

**Large central modules concentrate unrelated behavior:**
- Issue: `CrudView` implementation, button rendering, template tags, formsets, and ViewSet routing each have large modules (for example `src/crud_views/lib/view/base.py`, `src/crud_views/lib/view/buttons.py`, and `src/crud_views/templatetags/crud_views.py`).
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/viewset/__init__.py`
- Impact: changes to shared code have broad regression surfaces and are harder to review in isolation.
- Fix approach: extract cohesive subsystems behind current public APIs, with regression tests around registration, request lifecycle, and template output before moving behavior.

## Known Bugs

**Polymorphic create accepts unvalidated content-type ids:**
- Symptoms: `polymorphic_model` fetches a `ContentType` directly from the supplied URL id. Missing ids raise `ContentType.DoesNotExist`; unrelated or excluded types are not checked against the ViewSet's allowed polymorphic children before form resolution.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/create_select.py`
- Trigger: request a polymorphic create URL with a nonexistent content type id or a type outside the configured subtype set.
- Workaround: configure `polymorphic_forms` only for intended child models and avoid exposing arbitrary ids. This behavior is confirmed by code inspection; runtime reproduction is pending.

## Security Considerations

**Polymorphic subtype selection trusts URL input:**
- Risk: an invalid or unrelated content-type id can produce a server error, and a configured form for a disallowed subtype may be reached through a crafted create URL.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`
- Current mitigation: selection view filters candidate child types; direct create URL resolution does not repeat that validation.
- Recommendations: apply the same allowlist to the direct create path and translate missing/disallowed content types to `Http404` or a controlled client error.

**Runtime contracts use Python assertions:**
- Risk: `assert` statements are removed under optimized Python (`-O`), so conditions used as runtime validation do not protect those execution paths in optimized deployments.
- Files: `src/crud_views/lib/views/create.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/lib/mixins.py`
- Current mitigation: several related configuration errors are caught by Django system checks; assertions remain in runtime code paths.
- Recommendations: use explicit exceptions for conditions required for correctness or security; keep assertions only for internal invariants.

## Performance Bottlenecks

**Guardian permission checks can repeat for each rendered object/action:**
- Problem: object permission helpers instantiate or invoke object-level checks from per-object rendering flows; list and card rendering can multiply checks by rows and available actions.
- Files: `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/views/card.py`
- Cause: permission evaluation is integrated into each item's action visibility, with no clear request-level prefetch guarantee across these paths.
- Improvement path: profile representative large lists, then reuse a request-scoped `ObjectPermissionChecker` and prefetch object permissions for the rendered page.

**Resource default lookup is linear:**
- Problem: `Resource.cv_get_item()` scans the full list returned by `cv_get_items()` until a matching primary key is found.
- Files: `src/crud_views/lib/resource.py`
- Cause: the base implementation is intentionally list-oriented and materializes all rows for lookup.
- Improvement path: override `cv_get_item()` for sources with direct key lookup (API, object storage, or indexed data); retain the default for small read-all collections.

## Fragile Areas

**ViewSet registration, routing, and metaclass integration:**
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/path_regs.py`, `src/crud_views/checks.py`
- Why fragile: view classes register during class construction and routing derives from that shared registry, parent relationships, model PK shape, and configuration checks.
- Safe modification: preserve import-safety constraints documented in `src/crud_views/lib/resource.py`; cover class declaration, duplicate/invalid registration, nested URLs, and Django checks when changing registration or route generation.
- Test coverage: broad behavior exists in `tests/test1/`; add focused regressions for new combinations of parent, PK, and view declarations.

**Template and theme extension surface:**
- Files: `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/icons.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`
- Why fragile: themes consume class keys, button context, icon identifiers, template variables, and JavaScript adapters as a coordinated contract.
- Safe modification: update the relevant reference docs and theme/golden tests with any intentional public-surface change; keep escaping at the existing rendering boundaries.
- Test coverage: built-in output has golden and integration coverage; third-party theme compatibility depends on documented contracts and is not exhaustively exercised by this repository.

**Nested formset rendering and persistence:**
- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/mixins.py`, `src/crud_views/lib/formsets/inline_formset.py`
- Why fragile: nested management forms, generated indices, parent-child save order, and validation errors must remain aligned across server rendering and JavaScript cloning.
- Safe modification: cover GET rendering, invalid POST re-render, deletion, nested indexes, and transaction behavior for affected formset combinations.
- Test coverage: extensive focused tests exist in `tests/test1/`; breadth of combinations remains a maintenance risk due to the number of interacting formset types.

## Scaling Limits

**Resource lookup and list materialization:**
- Current capacity: `Resource.cv_get_items()` is required to return a plain list; `cv_get_item()` performs a linear scan.
- Limit: large external datasets incur full-read memory and O(n) lookup costs unless subclasses override the lookup method.
- Scaling path: implement paginated/source-native list and direct item lookup abstractions if large remote collections become a supported use case.

## Dependencies at Risk

**Django 4.2 support line:**
- Risk: the supported test matrix includes Django 4.2, whose upstream support status changes over time and is not verified as part of this code inspection.
- Impact: security fixes and compatibility may require consumers to move to a newer supported Django series.
- Migration plan: confirm the support policy before the next release and remove the floor only through the documented compatibility and migration process.

## Missing Critical Features

**No explicit validation on direct polymorphic create subtype selection:**
- Problem: the direct-create path does not enforce the selection view's configured subtype allowlist.
- Blocks: robust handling of malformed or crafted polymorphic create URLs; see Known Bugs and Security Considerations.

## Test Coverage Gaps

**Polymorphic invalid content-type URL cases:**
- What's not tested: nonexistent content-type ids and direct requests for unrelated or excluded subtype ids.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `tests/test1/`
- Risk: server errors or unintended subtype forms may go unnoticed.
- Priority: High

**Custom user model without `username` in manage view:**
- What's not tested: `CRUD_VIEWS_MANAGE_SHOW_USERS` with an email-only user model.
- Files: `src/crud_views/lib/views/manage.py`, `tests/test1/`
- Risk: optional manage diagnostics can fail with a database field lookup error for supported custom user models.
- Priority: Medium

**Third-party theme contract compatibility:**
- What's not tested: consumer theme overrides against package changes across all template variables, class keys, icons, and JS adapters.
- Files: `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`, `docs/development/stability.md`
- Risk: downstream theme breakage can escape in-repository tests.
- Priority: Medium

**Human acceptance items remain pending:**
- What's not tested: CDN asset failure behavior and visual/focus inspection of changed stock UI are still pending in the current phase state; these are acceptance checks, not confirmed code defects.
- Files: `.planning/STATE.md`, `.planning/phases/06.5*/06.5-UAT.md`
- Risk: deployment-facing fallback behavior and visual/focus regressions have not yet received the recorded human verification.
- Priority: Medium

---

*Concerns audit: 2026-11-02*
