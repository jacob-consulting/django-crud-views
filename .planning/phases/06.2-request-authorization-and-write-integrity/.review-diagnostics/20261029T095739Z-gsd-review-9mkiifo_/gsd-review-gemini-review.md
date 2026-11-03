## 06.2-01

### Summary
Closes the inherited HTTP `DELETE` bypass across core and Guardian delete views (`D-01`, `D-02`, `AUTH-01`), filters unauthorized `RelatedObjects.protected` labels while introducing an independent `has_protected_objects` context flag and outer/inner template gates (`D-07`, `D-08`, `AUTH-03`), and pins POST form validation, custom delete protection, hooks, and atomic rollback (`D-12`, `D-13`, `AUTH-07`).

### Strengths
- **Complete HTTP `DELETE` and `Allow`/`OPTIONS` closure (closes A18, preserves A05):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:99-101` restricts `DeleteView.http_method_names`, overrides `delete()` to return `http_method_not_allowed` before any `get_object()` or write in `src/crud_views/lib/views/delete.py:27`, and overrides `DeleteView._allowed_methods()` to filter `"DELETE"` from `super()._allowed_methods()`. Because Django's `View.http_method_not_allowed` and `View.options` both read `_allowed_methods()`, this single hook keeps `DELETE` out of `Allow` headers on both 405 and `OPTIONS` responses even when a subclass restores `"delete"` in `http_method_names`. Task `01-03` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:131`) safely tests subclass inheritance by monkeypatching `http_method_names` to a fresh list on existing registered concrete classes (`PublisherDeleteView` at `tests/test1/app/views.py:339`, `GuardianPublisherDeleteView` at `tests/test1/app/views.py:707`) without mutating inherited class lists in place or triggering duplicate `CrudViewMetaClass` registration (`src/crud_views/lib/view/meta.py:17-25`).
- **Outer and inner template gates for protected-only previews (preserves H01):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:54-59, 99` captures `has_protected_objects = bool(related.protected)` in `DeleteView.get_context_data` (`src/crud_views/lib/views/delete.py:179-185`) before `cv_filter_related_objects`, and updates both `src/crud_views/templates/crud_views/view_delete.content.html:8` (`{% if related_summary or protected_objects %}`) and `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:4` (`{% if protected_objects %}`). Because `alert_data` (`src/crud_views/lib/messages.py:42-44`) selects `TEXT_BODY` when `items` is empty, `{% cv_alert "error" heading=_("Deletion is blocked by protected relationships:") items=protected_objects %}` renders the single generic blocked heading with no `<ul>` when all protected labels are filtered out.
- **Clean core vs. Guardian filter hook separation (preserves A01, A02, A04):** Core `DeleteView.cv_filter_related_objects` (`src/crud_views/lib/views/delete.py:147-172`) filters `related.protected` via `_has_view_permission(item._meta.model)`, while `GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects` (`src/crud_views_guardian/lib/views.py:39-50`) removes the `if not related.tree: return related` shortcut (`views.py:42-43`) and filters `related.protected` via `_PermittedPks` (`views.py:53-70`) without invoking core's model-level filter (`06.2-01-PLAN.md:115`). Obsolete tests in `tests/test1/test_delete.py:142-156` and `tests/test1/test_guardian_delete.py:45-73` are explicitly replaced.

### Concerns
- None.

### Suggestions
- None.

### Risk Assessment
- **Low:** The changes are localized to `DeleteView`, `GuardianDeleteRelatedObjectsMixin`, and two delete templates, with explicit coverage for full-page/modal rendering, custom protection (`200`/`422`), and `ProtectedError` preservation.

---

## 06.2-02

### Summary
Unifies parent-`None` permission resolution and independent `cv_action_enabled` enforcement on nested Guardian views (`D-10`, `AUTH-04`), resolves own-child instances to their configured FK parent in Guardian create permission and context-state helpers (`H03`), and enforces inactive-user denial across Guardian dispatch, queryset, callable helper, and preview cache paths (`D-11`, `D-05`, `AUTH-05`).

### Strengths
- **Complete resolution of H03 across permission helpers and context-state call sites:**
  - **Permission helper seam (`02-01`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:107` adds a private parent-object resolver on `GuardianCreateViewPermissionRequired` (`src/crud_views_guardian/lib/views.py:112-207`) that accepts either an actual parent instance (`isinstance(obj, parent_vs.model)`) or an own-child instance (`isinstance(obj, cls.cv_viewset.model)`) resolved via `cls.cv_viewset.parent.get_attribute()` (`src/crud_views/lib/viewset/parentviewset.py:62-66`), denying `None`, missing/broken relations (`ObjectDoesNotExist`), and unrelated models (`Author`). This directly supports `view|cv_context_has_permission:"create"` (`src/crud_views/templatetags/crud_views.py:468-473`) and `cls.cv_has_access(user, obj)` (`src/crud_views/lib/view/base.py:710`) on child detail/update/delete pages where `view.object` is a child instance.
  - **Context-state adapter seam (`02-03`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:136-138` adds `CrudView._cv_action_enabled_for_context(user, obj)` in `src/crud_views/lib/view/base.py:357` (defaulting to `cls.cv_action_enabled(user, obj)`) and routes `_cv_get_action_context` (`src/crud_views/lib/view/base.py:707`), `ContextButton` state call sites (`src/crud_views/lib/view/buttons.py:109, 182, 234, 291`), and both `CardListView.cv_get_card_action_data` branches (`src/crud_views/lib/views/card.py:66, 89`) through it. Overriding `_cv_action_enabled_for_context` on `GuardianCreateViewPermissionRequired` normalizes own-child instances to their FK parent before calling consumer `cv_action_enabled(user, parent)`, while keeping `ViewContext(object=obj)` (`base.py:704`) and URL kwargs (`base.py:536-542`) untouched.
- **Centralized parent-`None` resolution and W280 compliance (preserves A13):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:105, 109` always resolves `parent_obj` via `get_object_or_404` in `GuardianParentPermissionMixin._guardian_check_parent` (`src/crud_views_guardian/lib/mixins.py:230-245`) and evaluates `self.cv_action_enabled(user, parent_obj)` for no-object child views even when the effective parent permission key is `None`, and declares `cv_guardian_accept_global_perms` and `cv_guardian_anonymous_behavior` on `GuardianParentPermissionMixin` (`mixins.py:173`).
- **Comprehensive inactive-actor denial (preserves A03, A08, A10):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:123` denies authenticated inactive users in `GuardianParentPermissionMixin.dispatch` (`mixins.py:196`), `GuardianObjectPermissionMixin.has_permission` and `cv_has_access` (`mixins.py:31, 61`), `GuardianQuerysetMixin.has_permission`, `cv_has_access`, and `get_queryset` (`mixins.py:98, 108, 159`), `_PermittedPks` (`views.py:61`), create helpers (`views.py:123, 158`), and `GuardianViewSet.get_objects_for_user` (`src/crud_views_guardian/lib/viewset.py:63`), tested under `AllowAllUsersModelBackend`.

### Concerns
- None.

### Suggestions
- In `GuardianQuerysetMixin.cv_get_context` (`src/crud_views_guardian/lib/mixins.py:155`), routing `ctx["cv_action_enabled"]` through `target_cls._cv_action_enabled_for_context(user, parent_obj)` (or guarding `parent_obj is not None`) ensures that if `cv_get_parent_object()` fails (`parent_obj = None`), a custom `cv_action_enabled` hook on the create view is not invoked with `None`.

### Risk Assessment
- **Low:** The private `_cv_action_enabled_for_context` adapter is a no-op for all views except nested `GuardianCreateViewPermissionRequired`, preserving all existing `cv_action_enabled` signatures and template contexts.

---

## 06.2-03

### Summary
Enforces target object/parent/editor authorization in `FormSetMixinBase.get` before serving formset fragments and validates declared key paths, ASCII row indices, root identity, and persisted/unsaved FK ancestry (`D-09`, `D-12`, `D-13`, `AUTH-02`, `AUTH-07`), while explicitly bounding and deferring the pre-existing non-first sibling child-declaration fragment index mismatch to proposed Phase 6.3 (`A19`).

### Strengths
- **Cooperative target authorization before fragment rendering:** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:90` updates `FormSetMixinBase.get` (`src/crud_views/lib/formsets/mixins.py:37-45`) to initialize `self.object = self.get_object() if self.cv_object else None` (matching `CrudViewProcessFormMixin.post` at `src/crud_views/lib/views/mixins.py:37`) before `get_template_html(request)`. This triggers `GuardianObjectPermissionMixin.get_object()` (`src/crud_views_guardian/lib/mixins.py:50-58`) and supports `PolymorphicCrudViewMixin.polymorphic_model` (`src/crud_views_polymorphic/lib/utils.py:42-55`) on update views before any formset or `ModelChoiceField` is instantiated.
- **Declaration-aware coordinate and FK ancestry validation (preserves A06, A07, A14, A15):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:104-106` validates ASCII `[0-9]+` indices (rejecting Unicode digits like `²` that pass `str.isdigit()` at `src/crud_views/lib/formsets/mixins.py:54`), validates PKs with `FormSet.PK` (`src/crud_views/lib/formsets/formsets.py:27-29`) and model PK `to_python` without splitting UUID hyphens, normalizes `FormSet.init` prefix keys to `None` when `form.instance._state.adding` is true (`formsets.py:123`), and tests real persisted UUID FK chains using `Author` -> `UUIDFragmentRow` -> `UUIDFragmentLeaf` in `tests/test1/app/models.py:13`.
- **Explicit A19 scope boundary and disposition (closes A19):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:23, 81, 108, 169-176` explicitly documents the discrepancy between `FormSet.init` (`src/crud_views/lib/formsets/formsets.py:159-166`, which passes `index=child_index`) and `FormSets.get_template` (`formsets.py:379`, which passes `index=0`), bounds round-trip positive claims to top-level and first-child-at-each-level declarations, characterizes a two-child declaration in tests, enforces authorization and ancestry checks on all sibling declarations, and defers the output-index lifecycle fix to proposed Phase 6.3.

### Concerns
- None.

### Suggestions
- None.

### Risk Assessment
- **Low:** Browser payload contracts (`template`, `pk`, `num`, `formset_parent_prefix_key`) and `{html, rows}` responses are preserved for all working persisted and unsaved nested flows.

---

## 06.2-04

### Summary
Atomically removes the inert `GuardianViewSet.cv_guardian_accept_global_perms` field with a Mapping-guarded `mode="before"` validator diagnostic (`D-03`, `D-04`, `AUTH-06`), keeps `GuardianViewSet.get_objects_for_user()` strict (`D-05`), and updates `GuardianManageView` and its templates to display per-view effective global-fallback policy and applicability alongside the strict helper policy (`D-06`, `AUTH-07`).

### Strengths
- **Atomic field removal and manage reader update with Mapping-guarded validator (preserves A09, A12, A17):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:92` removes `cv_guardian_accept_global_perms` from `GuardianViewSet` (`src/crud_views_guardian/lib/viewset.py:23`), adds a `@model_validator(mode="before")` guarded by `isinstance(data, collections.abc.Mapping)` so `model_validate(existing_instance)` and non-mapping inputs behave normally, and simultaneously updates `GuardianManageView.get_context_data` (`src/crud_views_guardian/lib/views.py:228-233`), `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html:15-18`, and `tests/test1/test_guardian.py:636-649`. Task `04-02` (`06.2-04-PLAN.md:106`) accurately classifies per-view applicability in `GuardianManageView.get_view_data` (`views.py:270-276`), reporting `not applicable` for plain/manage views, top-level creates, and parent-only views whose resolved parent permission is `None`.
- **Explicit singleton monkeypatching for manage authorization modes (closes A20):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:108` explicitly directs tests to `monkeypatch.setattr` both `manage_views_enabled` and `manage_group` on `crud_views.lib.settings.crud_views_settings` (`src/crud_views/lib/settings.py:27-28, 337`, read by `ManageView.has_permission` at `src/crud_views/lib/views/manage.py:31-39`) while using `override_settings(DEBUG=...)` for live `DEBUG`, matching the established pattern in `tests/test1/test_manage.py:122, 140, 154`.
- **Preserved flagged assumption tracking:** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:80, 163, 175` explicitly preserves `FLAGGED ASSUMPTION AUTH-06/unclassified` for manual review in `06.2-ACCEPTANCE.md` rather than silently dismissing it.

### Concerns
- None.

### Suggestions
- None.

### Risk Assessment
- **Low:** Atomic execution in `04-01` prevents any intermediate broken state on `/guardian_author/manage/`, and constructor failures are verified not to leave stale entries in `_REGISTRY`.

---

## 06.2-05

### Summary
Replays the full direct-request actor, route, and method matrix (`tests/test1/test_authorization_matrix.py`) and six native template overrides via `locmem.Loader` (`tests/test1/test_authorization_templates.py`), verifying server-owned authorization, safe context projection, child-page create control resolution, and manage-mode gates (`D-12`, `D-13`, `D-14`, `AUTH-01`–`AUTH-07`).

### Strengths
- **Complete actor/status/storage oracle including H03 child-page create rows (closes H03 in Wave 4, preserves A10):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:80-106, 110, 123` specifies single exact statuses and storage/hook outcomes for every cell, including three dedicated rows (`06.2-05-PLAN.md:99-101`) for reachable child detail/update/delete pages when parent-create is permitted+enabled (`200`, filter `True`, control available, `POST 302`), denied/revoked (`200`, filter `False`, control hidden/disabled, `GET/POST 403`), and permitted+state-disabled (`200`, filter `True`, `cv_access=True`, `cv_action_enabled=False`, control hidden/disabled, `GET/POST 403`).
- **Explicit singleton patching for manage-mode matrix and overrides (closes A20 in Wave 4):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:108, 123, 139` mandates `monkeypatch.setattr(crud_views_settings, "manage_views_enabled", ...)` and `monkeypatch.setattr(crud_views_settings, "manage_group", ...)` alongside `override_settings(DEBUG=...)` in both `05-01` and `05-02`, with exact `302`/`403` negative controls so the test environment default (`manage_views_enabled="yes"`) cannot cause false passes.
- **Six native template override seams with strict fixture hygiene (preserves A03, A08):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:137-140` exercises `crud_views/view_list.content.html`, `crud_views/tags/card.html`, `crud_views/tags/button/action.html`, `crud_views/view_guardian_manage.html`, `crud_views/tags/alert.html`, and `crud_views/formsets/formset.html` with `locmem.Loader` and full `finally` teardown of `_REGISTRY`, `_VOCAB_CACHE`, `ROOT_URLCONF`, URL caches, and `TEMPLATES`.

### Concerns
- None.

### Suggestions
- None.

### Risk Assessment
- **Low:** Test-only wave with strict fixture isolation and deterministic status/context/storage assertions.

---

## 06.2-06

### Summary
Updates canonical reference docs (`docs/reference/guardian.md`, `docs/reference/delete_view.md`, `docs/reference/formsets.md`, `docs/reference/context_buttons.md`, `docs/faq.md`, `docs/reference/theme.md`), pairs `CHANGELOG.md` `### Breaking` entries with `docs/migrating-1.0.md` (`D-14`), and records dual-environment (Django 4.2 and 6.0) regression and strict `mkdocs` verification plus the Phase 7 contract inventory in `06.2-VALIDATION.md` and `06.2-ACCEPTANCE.md` (`AUTH-01`–`AUTH-07`).

### Strengths
- **Synchronized H03 documentation and wrapper recipes (closes H03 in Wave 5):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:95, 113, 131` owns `docs/reference/context_buttons.md` (`:531-543`) and `docs/faq.md` (`:128-144`) in addition to `docs/reference/guardian.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`. It replaces Round 1's blanket wrong-model migration note with accurate guidance: `GuardianCreateViewPermissionRequired.cv_has_access` accepts either the parent instance or an own-child instance (resolving its FK parent via `ParentViewSet.get_attribute()`), denies `None`, missing-parent, and unrelated instances, keeps `view|cv_context_has_permission:"create"` permission-only on child object pages (`False` on list pages where `view.object` is `None`), and passes the resolved parent to `cv_action_enabled` on create controls without altering `ViewContext` labels.
- **Explicit custom `cv_filter_related_objects` and per-view related-label fallback guidance (closes A21):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:97, 115, 131` documents in `docs/reference/delete_view.md`, `docs/reference/guardian.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md` that custom `cv_filter_related_objects` overrides must filter `RelatedObjects.protected` (delegating to the core or Guardian superclass hook without running core's model-level filter after Guardian's object-level filter), preserve the pre-filter `has_protected_objects` flag and aggregate summary policy, and note that the delete view's `cv_guardian_accept_global_perms` governs global view-permission fallback for related protected models' labels (`src/crud_views_guardian/lib/views.py:45, 67`).
- **Preserved doc-extraction fence/heading contracts and A18/A19/AUTH-06 handoff (closes A18, A19, preserves A11, A16):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:97, 99, 115, 118, 129-134` places new theme guidance in a standalone `##` section of `docs/reference/theme.md` outside the sections parsed by `tests/test1/test_alerts.py:249-255` and `tests/test1/test_form_button_docs.py:168-175, 403-409`, runs all four doc-test suites (`test_alerts.py`, `test_form_button_docs.py`, `test_label_mode_docs.py`, `test_pagination_docs.py`) plus `.venv/bin/mkdocs build --strict`, and records the A19 deferral and `AUTH-06/unclassified` flagged assumption in `06.2-ACCEPTANCE.md`.

### Concerns
- None.

### Suggestions
- None.

### Risk Assessment
- **Low:** Documentation and verification wave guarded by automated AST/regex doc-extraction tests and `mkdocs build --strict`.

---

## Cross-Plan Assessment and Sign-Off

### Explicit Reviewer Sign-Off for H03
- **H03 Status: SIGNED OFF (CLOSED).**
- **Verification of mechanism:**
  1. `06.2-02-PLAN.md:107` (`02-01`) resolves own-child instances (`isinstance(obj, cls.cv_viewset.model)`) to their configured FK parent via `cls.cv_viewset.parent.get_attribute()` (`src/crud_views/lib/viewset/parentviewset.py:62-66`) in `GuardianCreateViewPermissionRequired`, while still denying `None` (so `GuardianQuerysetMixin.cv_get_context` at `src/crud_views_guardian/lib/mixins.py:130-156` continues to handle list pages), missing/broken FK relations, and unrelated model instances.
  2. `06.2-02-PLAN.md:136` (`02-03`) adds `CrudView._cv_action_enabled_for_context(user, obj)` in `src/crud_views/lib/view/base.py`, routing `_cv_get_action_context` (`base.py:707`), `ContextButton` (`src/crud_views/lib/view/buttons.py:109, 182, 234, 291`), and `CardListView.cv_get_card_action_data` (`src/crud_views/lib/views/card.py:66, 89`) through it so nested `GuardianCreateViewPermissionRequired` state hooks receive the resolved parent instance even when rendered from a child detail/update/delete page or child card row, while keeping permission (`cv_access` / `cv_context_has_permission`) and state (`cv_action_enabled`) independent and preserving the child `ViewContext` for labels and URLs.
  3. `06.2-05-PLAN.md:99-101, 110, 123, 139` and `06.2-06-PLAN.md:38-40, 95, 113, 131` synchronize the direct-request matrix, native template overrides, and documentation/migration recipes (`docs/reference/guardian.md`, `docs/reference/context_buttons.md`, `docs/faq.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`).

### Prior-Item Closure Ledger

| ID | Cycle 2 Severity | Plan Ownership & Line Evidence | Closure Status & Verification |
| --- | --- | --- | --- |
| **H03** | HIGH | `06.2-02-PLAN.md:27, 46-58, 92, 107, 132-145`; `06.2-05-PLAN.md:22, 99-101, 110, 123, 139`; `06.2-06-PLAN.md:11-12, 38-40, 95, 113, 131` | **CLOSED (Signed Off).** Own-child instances resolve to their configured FK parent via `ParentViewSet.get_attribute()`; unrelated/`None`/missing-parent inputs deny; `_cv_action_enabled_for_context` passes the resolved parent to create state hooks across base, `ContextButton`, and card actions while keeping permission and state independent. |
| **A18** | LOW | `06.2-01-PLAN.md:24, 101, 131, 197`; `06.2-06-PLAN.md:97, 131, 193` | **CLOSED.** `DeleteView._allowed_methods()` filters `"DELETE"` from `super()._allowed_methods()` for both `http_method_not_allowed` (405) and `options` (`OPTIONS`); `01-03` monkeypatches `http_method_names` with a fresh list on existing registered concrete subclasses with automatic teardown. |
| **A19** | LOW | `06.2-03-PLAN.md:23, 81, 108, 171, 176`; `06.2-05-PLAN.md:110, 207`; `06.2-06-PLAN.md:99, 115, 131, 199` | **CLOSED (Explicit Deferral).** Bounds add-row/POST round-trip claims to top-level and first-child-at-each-level declarations, characterizes the existing `get_template` `index=0` mismatch on a second child declaration, preserves mandatory authorization and ancestry validation on all paths, and defers the output-index lifecycle fix to proposed Phase 6.3. |
| **A20** | MEDIUM | `06.2-04-PLAN.md:108, 170`; `06.2-05-PLAN.md:108, 123, 139, 202` | **CLOSED.** Explicitly patches `crud_views_settings.manage_views_enabled` and `crud_views_settings.manage_group` via `monkeypatch.setattr` with teardown while using `override_settings(DEBUG=...)` for live `DEBUG`, and asserts `302`/`403` negative controls. |
| **A21** | LOW | `06.2-06-PLAN.md:97, 115, 131, 194` | **CLOSED.** Documents custom `cv_filter_related_objects` responsibilities for filtering `RelatedObjects.protected`, delegating to the proper core/Guardian superclass filter without double-filtering, preserving `has_protected_objects` and aggregates, and how the delete view's per-view `cv_guardian_accept_global_perms` governs related protected-model labels. |
| **H01, H02, A01–A17** | Prior (Closed in Cycle 2) | `06.2-01-PLAN.md` through `06.2-06-PLAN.md`; `06.2-VALIDATION.md:165-193` | **PRESERVED (No Regression).** All prior closures remain intact in the revised plans; H03 cleanly refines H02's helper contract for own-child instances while preserving fail-closed denial for unrelated models and `None`. `AUTH-06/unclassified` remains explicitly flagged at `06.2-04-PLAN.md:80` and `06.2-06-PLAN.md:129-131`. |

### Deduplicated List of Genuinely Unresolved Plan Concerns
- **None** (`0` HIGH, `0` MEDIUM, `0` LOW). All six plans are ready for execution.
