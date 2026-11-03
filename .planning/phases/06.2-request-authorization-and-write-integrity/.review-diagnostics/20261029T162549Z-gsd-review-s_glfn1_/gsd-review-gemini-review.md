## 06.2-01

### 1. Summary
Plan `06.2-01` (already executed) closes the inherited HTTP `DELETE` direct-deletion bypass across core, Guardian, and polymorphic delete views and introduces permission-filtered `protected_objects` alongside an `has_protected_objects` context flag. The HTTP `DELETE` guard in `src/crud_views/lib/views/delete.py:27-48` is cleanly engineered and holds up under MRO inspection. However, the executed preview and write-path design left two significant historical gaps in current source—an unhandled `ContentType.DoesNotExist` / `MixedContentTypeError` crash in Guardian's `_PermittedPks` (`src/crud_views_guardian/lib/views.py:68-78`) when a model lacks a standard `view_<model>` permission, and a preview-only `has_protected_objects` flag (`src/crud_views/lib/views/delete.py:202-205`) that left the confirmation form active and `POST` raising an uncaught `ProtectedError` 500—both of which are now targeted by pending gap-closure plans `06.2-07` and `06.2-08`.

### 2. Strengths
- **Cooperative MRO placement for HTTP `DELETE` rejection (`src/crud_views/lib/views/delete.py:27-48`):** `_DeleteMethodGuardMixin` is placed after `CrudView` and before `generic.DeleteView` (`delete.py:47`). Tracing the MRO confirms `PermissionRequiredMixin.dispatch` (`src/crud_views/lib/view/base.py:886`) and `GuardianParentPermissionMixin.dispatch` (`src/crud_views_guardian/lib/mixins.py:232-240`) execute first, `CrudView.dispatch` (`base.py:227-231`) wraps the response with `Vary: X-CV-Modal`, and `_DeleteMethodGuardMixin.dispatch` (`delete.py:37-40`) short-circuits `DELETE` via `http_method_not_allowed` before `DeletionMixin.delete` or `GuardianObjectPermissionMixin.get_object` (`mixins.py:64-72`).
- **Warning-free Django 4.2 compatibility (`src/crud_views/lib/views/delete.py:33-34,42-45` and `tests/test1/test_delete.py:393-433`):** By filtering `"DELETE"` in `_allowed_methods()` and `http_method_names` without overriding `DeletionMixin.delete`, `view_class.delete is DeletionMixin.delete` remains true across all concrete delete views (`test_delete.py:425-432`), avoiding Django 4.2's `DeleteViewCustomDeleteWarning`.
- **Separation of core and Guardian related-object filters (`src/crud_views/lib/views/delete.py:168-195`, `src/crud_views_guardian/lib/views.py:48-56`):** `GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects` replaces `DeleteView.cv_filter_related_objects` instead of calling `super()`, ensuring an object-level `view` grant is not stripped by a second model-level `user.has_perm` pass (`tests/test1/test_guardian_delete.py:242-254`).

### 3. Concerns
- **[HIGH — Historical gap, addressed by pending plan `06.2-07`]** `GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects` (`src/crud_views_guardian/lib/views.py:51-56`) routes every model in `related.tree` and `related.protected` through `_PermittedPks.__call__` (`views.py:68-78`), which constructs `perm = f"{opts.app_label}.view_{opts.model_name}"` (`views.py:75`) and calls `guardian.shortcuts.get_objects_for_user`. In `guardian/shortcuts.py:515-543,671-679`, `_compute_codenames_and_ctype` resolves that dotted string via `_get_ct_cached` (`ContentType.objects.get(app_label=..., permission__codename=codename)`) *before* `if with_superuser and user.is_superuser:`. Any model without a matching `view_` permission row—such as auto-created M2M through tables (`Genre.publishers.through` in `tests/test1/app/models.py:52`) or models with restricted `Meta.default_permissions`—raises `ContentType.DoesNotExist` (500) on both `GET` and `POST` for all users including superusers.
- **[MEDIUM — Historical gap, addressed by pending plan `06.2-08`]** `DeleteView.get_context_data` (`src/crud_views/lib/views/delete.py:202-205`) only computes `context["has_protected_objects"] = bool(related.protected)` when `self.cv_show_related_objects` is `True` (default `False` at `delete.py:59`). Furthermore, `src/crud_views/templates/crud_views/view_delete.content.html:12-18` still renders the confirmation `<form>` when `has_protected_objects` is `True`, `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:5` renders a trailing colon (`"Deletion is blocked by protected relationships:"`) with an empty body when `protected_objects` is empty (`src/crud_views/lib/messages.py:43-44`), and `DeleteView.post` (`delete.py:224-247`) ignores `has_protected_objects` and lets `self.object.delete()` raise `ProtectedError` (pinned in `tests/test1/test_delete.py:246-259` and `tests/test1/test_guardian_delete.py:315-330`).

### 4. Suggestions
- Retain the `_DeleteMethodGuardMixin` implementation (`src/crud_views/lib/views/delete.py:27-48`) and polymorphic `VehicleDeleteView` regression (`tests/test1/test_polymorphic.py:177-205`) as-is, and execute pending plans `06.2-07` and `06.2-08` to close the two historical gaps above.

### 5. Risk Assessment
- **MEDIUM (Historical):** While the HTTP `DELETE` guard and label-filtering boundary work as intended, the unguarded `_PermittedPks` string lookup (`src/crud_views_guardian/lib/views.py:74-76`) and incomplete blocked-deletion flow (`src/crud_views/lib/views/delete.py:202-247`) require the pending gap-closure plans before Phase 7 freezes the delete contracts.

---

## 06.2-02

### 1. Summary
Plan `06.2-02` (already executed) enforces parent resolution and `cv_action_enabled` state checks when `cv_guardian_parent_permission` is `None`, normalizes Guardian nested create access helpers and rendered-control state hooks to the configured FK parent, and denies authenticated inactive actors across all Guardian request and callable paths. Source inspection confirms the Guardian mixins, viewset helper, and button/card call sites are properly wired, with one residual core/Guardian asymmetry in `_cv_action_enabled_for_context` and one minor unvalidated permission-key lookup.

### 2. Strengths
- **Comprehensive inactive-actor denial (`src/crud_views_guardian/lib/mixins.py:10-17`):** `_guardian_inactive_actor(user)` is checked before any permissive return or superuser short-circuit across `GuardianObjectPermissionMixin` (`mixins.py:48,53,76`), `GuardianQuerysetMixin` (`mixins.py:121,127,186`), `GuardianParentPermissionMixin` (`mixins.py:235,273`), `_PermittedPks` (`src/crud_views_guardian/lib/views.py:69`), `GuardianCreateViewPermissionRequired` (`views.py:200,245`), and `GuardianViewSet.get_objects_for_user` (`src/crud_views_guardian/lib/viewset.py:100`).
- **Annotation-only attributes on `GuardianParentPermissionMixin` (`src/crud_views_guardian/lib/mixins.py:224-225`):** Declaring `cv_guardian_accept_global_perms: bool` and `cv_guardian_anonymous_behavior: str` without default values satisfies `CheckUnknownAttributes` (`W280`) while preventing `GuardianParentPermissionMixin` (which appears first in view MROs at `src/crud_views_guardian/lib/views.py:27-35,94-118`) from shadowing subclassed `GuardianObjectPermissionMixin` or `GuardianQuerysetMixin` attributes.
- **Fail-closed FK vs. M2M own-child resolution (`src/crud_views_guardian/lib/views.py:139-171`):** `_cv_guardian_create_parent` accepts a direct parent instance or resolves single-FK own-child instances via `parent.get_attribute()`, explicitly rejecting M2M own-child instances (`if not isinstance(obj, cls.cv_viewset.model) or parent.many_to_many_through_attribute: return None` at `views.py:154-155`) and catching `ObjectDoesNotExist` (`views.py:158`).

### 3. Concerns
- **[MEDIUM — Residual historical gap (WR-01 in `06.2-REVIEW.md`)]** `CrudView._cv_action_enabled_for_context` (`src/crud_views/lib/view/base.py:369-374`) defaults to `cls.cv_action_enabled(user, obj)`, and only `GuardianCreateViewPermissionRequired` overrides it (`src/crud_views_guardian/lib/views.py:163-171`). For a **core** nested `CreateViewPermissionRequired` under a `ParentViewSet`, `CrudViewPermissionRequiredMixin.has_permission` (`src/crud_views/lib/view/base.py:917-918`) passes `self.cv_get_action_object()`—which resolves `self.cv_get_parent_object()` (`base.py:376-383`)—to `cv_action_enabled`, whereas toolbar/card rendering (`base.py:715`, `src/crud_views/lib/view/buttons.py:109`, `src/crud_views/lib/views/card.py:89`) passes the current page's `obj` (`Book` or `None`).
- **[LOW — Residual edge case (IN-03 in `06.2-REVIEW.md`)]** In `GuardianParentPermissionMixin._guardian_user_has_parent_perm` (`src/crud_views_guardian/lib/mixins.py:278-286`) and `GuardianObjectPermissionMixin` (`mixins.py:66-67,78-87`), `permissions.get(perm_key)` can return `None` if a view or `GuardianViewSet` configures an unknown permission key, causing `parent_perm.split(".")[1]` to raise `AttributeError`.

### 4. Suggestions
- If core nested `CreateViewPermissionRequired` state-hook parity is desired before or after 1.0, move `_cv_guardian_create_parent` and `_cv_action_enabled_for_context` to core `CreateView` (`src/crud_views/lib/views/create.py`) or track WR-01 explicitly in the Phase 7 handoff.
- Guard `if not parent_perm: return False` (or validate permission keys via a system check) in `src/crud_views_guardian/lib/mixins.py:66,78,278`.

### 5. Risk Assessment
- **LOW:** All Phase 6.2 Guardian parent-`None` (B4/B6) and inactive-actor (B5) requirements are met and verified in `tests/test1/test_guardian_parent_none.py` and `tests/test1/test_guardian_inactive.py`.

---

## 06.2-03

### 1. Summary
Plan `06.2-03` (already executed) gates AJAX formset fragment requests (`?template=...`) on target object resolution and authorization before rendering, validates coordinate chains (`key_path`, `pk`, `num`, `formset_parent_prefix_key`) against the `FormSets` declaration and persisted FK ancestry, and normalizes unsaved UUID-default parent instances to `None` in formset prefixes. Source verification in `src/crud_views/lib/formsets/mixins.py` and `src/crud_views/lib/formsets/formsets.py` confirms strong server-side enforcement.

### 2. Strengths
- **Pre-render target resolution and authorization (`src/crud_views/lib/formsets/mixins.py:47-52`):** `FormSetMixinBase.get` executes `self.object = self.get_object() if self.cv_object else None` before `self.get_template_html(request)`, ensuring `GuardianObjectPermissionMixin.get_object()` (`src/crud_views_guardian/lib/mixins.py:64-72`) and URL-parent queryset scoping run before any inline formset or `ModelChoiceField` queryset is evaluated, while avoiding building the full page's `get_context_data()`.
- **Declaration-aware coordinate and FK ancestry validation (`src/crud_views/lib/formsets/formsets.py:396-506`):** `_cv_validate_fragment_coordinates` validates `num` and row indices with ASCII-only `_FRAGMENT_INDEX = re.compile(r"[0-9]{1,9}")` (`formsets.py:25,40-43`), builds a per-level regex from each ancestor's `FormSet.PK` (`formsets.py:490-496`) so UUID hyphens are never split, enforces monotonically `None` identities below any unsaved ancestor (`formsets.py:471-472`), and checks persisted parent ownership via `owner.model._default_manager.filter(pk=value, **{f"{owner.fk.name}__pk": values[j - 1]}).exists()` (`formsets.py:474-478`).
- **Non-destructive unsaved UUID prefix normalization (`src/crud_views/lib/formsets/formsets.py:28-37,145`):** `_cv_prefix_identity(instance)` returns `None` when `instance._state.adding` is `True`, keeping `instance.pk` intact while aligning `FormSet.init` prefixes with `FormSet.template` and `formset.js`.

### 3. Concerns
- **[LOW — Documented deferral A19 (`src/crud_views/lib/formsets/formsets.py:508-514`)]** `FormSets.get_template` calls `formset.template(index=0, ...)` with a hardcoded `index=0`, whereas `FormSet.init` (`formsets.py:181-189`) enumerates `self.children.items()` with `index=child_index`. Non-first sibling child declarations therefore emit `0` in their fragment prefix rather than their `child_index`. This is accurately documented in `formsets.py:417-418` and deferred to proposed Phase 6.3.
- **[LOW — Residual limitation (IN-04 in `06.2-REVIEW.md`)]** `FormSet.PK` (`src/crud_views/lib/formsets/formsets.py:49-51`) supports only `INT` (`\d+`) and lowercase `UUID`, so slug-PK models cannot use formset fragments (`formsets.py:452`).

### 4. Suggestions
- When Phase 6.3 addresses `A19`, pass the resolved child declaration index (`0 if depth == 0 else child_index_at_depth`) into `formset.template(index=..., ...)` at `src/crud_views/lib/formsets/formsets.py:513`.

### 5. Risk Assessment
- **LOW:** The fragment authorization and ancestry validation logic in `src/crud_views/lib/formsets/mixins.py:47-78` and `src/crud_views/lib/formsets/formsets.py:396-506` is sound and thoroughly tested in `tests/test1/test_fragment_authorization.py`.

---

## 06.2-04

### 1. Summary
Plan `06.2-04` (already executed) removes the inert `GuardianViewSet.cv_guardian_accept_global_perms` field with a targeted Pydantic before-validator diagnostic, preserves the strict `GuardianViewSet.get_objects_for_user()` helper, and updates `GuardianManageView` to report each registered view's effective global-fallback policy and applicability. Source inspection in `src/crud_views_guardian/lib/viewset.py` and `src/crud_views_guardian/lib/views.py` confirms all requirements for `AUTH-06` are satisfied.

### 2. Strengths
- **Safe before-validator rejection (`src/crud_views_guardian/lib/viewset.py:39-49`):** `reject_removed_global_perms_flag` checks `if isinstance(data, Mapping) and _REMOVED_GLOBAL_PERMS_KEY in data: raise ValueError(_REMOVED_GLOBAL_PERMS_MESSAGE)` before Pydantic's default `extra="ignore"` discards the key and before `register` (`mode="after"`, `viewset.py:61-75`) mutates `_REGISTRY`. Non-mapping inputs pass through to standard Pydantic validation without raising `TypeError`.
- **Accurate per-view applicability logic (`src/crud_views_guardian/lib/views.py:338-349`):** `_guardian_global_fallback_applicable` marks `GuardianObjectPermissionMixin` and `GuardianQuerysetMixin` subclasses as applicable, and marks parent-only `GuardianParentPermissionMixin` views as applicable only when `self.cv_viewset.parent is not None` and `view_class._guardian_resolve_parent_perm_key() is not None`.

### 3. Concerns
- **[LOW — Residual mutability (IN-02 in `06.2-REVIEW.md`)]** `STRICT_HELPER_POLICY` (`src/crud_views_guardian/lib/viewset.py:11`) is a module-level mutable `dict` read at call time by `GuardianViewSet.get_objects_for_user` (`viewset.py:106-107`). Mutating it in process memory would alter runtime behavior of the helper.
- **[LOW — Residual UI duplication (accepted in `06.2-UAT.md` Test 2)]** `GuardianManageView.get_view_data` (`src/crud_views_guardian/lib/views.py:329-335`) adds `view_data["guardian_policy"]` as a top-level section in `view_data`, so the inherited `view_manage.html` loop renders the raw `guardian_policy` dictionary in each view's detail table in addition to the dedicated summary table in `src/crud_views_guardian/templates/crud_views/view_guardian_manage.html:8-22`.

### 4. Suggestions
- Wrap `STRICT_HELPER_POLICY` in `types.MappingProxyType` at `src/crud_views_guardian/lib/viewset.py:11` (`dict(STRICT_HELPER_POLICY)` in `src/crud_views_guardian/lib/views.py:280` will continue to work unchanged).

### 5. Risk Assessment
- **LOW:** The configuration removal, diagnostic, strict helper, and manage page reporting work as specified and are verified by `tests/test1/test_guardian_policy.py`.

---

## 06.2-05

### 1. Summary
Plan `06.2-05` (already executed) replays the full actor/route/method matrix (`tests/test1/test_authorization_matrix.py`, 550 test cases) and native template overrides (`tests/test1/test_authorization_templates.py`, 32 test cases) across all six template seams. While the test isolation and matrix coverage are strong, `test_authorization_matrix.py` and `test_authorization_templates.py` contain specific assertions and template-override shapes that interact directly with pending gap-closure plan `06.2-08`.

### 2. Strengths
- **Complete route/registry/template teardown (`tests/test1/test_authorization_matrix.py` and `tests/test1/test_authorization_templates.py:88-105`):** Both modules isolate dynamically registered ViewSets, restore `_REGISTRY` and `_VOCAB_CACHE`, clear URL caches, and patch the cached `crud_views_settings` singleton attributes (`manage_views_enabled`, `manage_group`) rather than relying solely on `@override_settings`.
- **Six native template seams verified without template-side permission logic (`tests/test1/test_authorization_templates.py:55-85`):** Locmem overrides for `view_list.content.html`, `tags/card.html`, `tags/button/action.html`, `view_guardian_manage.html`, `tags/alert.html`, and `formsets/formset.html` verify that unauthorized objects and labels are filtered before template rendering.

### 3. Concerns
- **[MEDIUM — Impacts pending plan `06.2-08`]** In `tests/test1/test_authorization_templates.py:81-84`, the locmem override for `crud_views/tags/alert.html` is:
  ```django
  <div role="alert" data-mx-alert="{{ alert.level }}"><strong>MX-ALERT {{ alert.heading }}</strong><ul>{% for item in alert.items %}<li>{{ item }}</li>{% endfor %}</ul></div>
  ```
  Notice that this override renders `{{ alert.heading }}` and `{{ alert.items }}`, but **omits `{{ alert.text }}`** (and `{% include alert.body_template %}`). Pending plan `06.2-08` Task `08-02` instructs: *"Apply the constant change in `tests/test1/test_guardian_delete.py` and `tests/test1/test_authorization_templates.py` (prefix without the colon; add `BLOCKED_SENTENCE` where the hidden case is asserted)."* Because `alert_data()` passes the generic sentence in `alert["text"]`, asserting `BLOCKED_SENTENCE` against the rendered HTML in `test_authorization_templates.py:590-625` will fail unless `OVERRIDES["crud_views/tags/alert.html"]` (`test_authorization_templates.py:81-84`) is also updated to render `{{ alert.text }}` (or `alert["text"]` is asserted via context/updated override).

### 4. Suggestions
- When executing `06.2-08` Task `08-02`, either include `{% if alert.text %}<p>{{ alert.text }}</p>{% endif %}` in `OVERRIDES["crud_views/tags/alert.html"]` (`tests/test1/test_authorization_templates.py:81-84`) or assert `BLOCKED_SENTENCE` only where the stock `tags/alert.html` (`src/crud_views/templates/crud_views/tags/alert.html:4`, which includes `alert.body_template`) is rendered.

### 5. Risk Assessment
- **LOW:** The executed test suites are comprehensive; only the `OVERRIDES["crud_views/tags/alert.html"]` interaction with `06.2-08` needs attention during gap closure.

---

## 06.2-06

### 1. Summary
Plan `06.2-06` (already executed) updates reference documentation (`guardian.md`, `delete_view.md`, `formsets.md`, `context_buttons.md`, `faq.md`, `theme.md`), pairs `CHANGELOG.md` `### Breaking` entries with `docs/migrating-1.0.md` subsections, and records the full-suite baseline/final comparison in `06.2-ACCEPTANCE.md`. It accurately documented the state as of Wave 5, and its delete-preview and `ProtectedError` sections are now scheduled to be updated by pending plan `06.2-09`.

### 2. Strengths
- **Preservation of doc-extraction test contracts (`docs/reference/theme.md:325-352`, `tests/test1/test_alerts.py:249-255`):** The new `## Authorized data in overridden templates` section was placed at the end of `docs/reference/theme.md` (`theme.md:325`), preserving the exact fence counts in `### Custom alert frame`, `### Custom form-button templates`, and `### Cancel links in custom form-button templates`.
- **Traceable code-to-test-to-doc evidence table (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md:94-136`):** Every documented claim and `### Breaking` entry is mapped to concrete source functions, test names, and migration anchors.

### 3. Concerns
- **[MEDIUM — Historical, addressed by pending plan `06.2-09`]** `docs/reference/delete_view.md:179-187,229-233,272-284`, `docs/reference/theme.md:336,343-348`, `docs/migrating-1.0.md:390-415`, `CHANGELOG.md:167-176`, and `06.2-ACCEPTANCE.md:116,155-162,230-231` still describe the pre-UAT delete behavior (`has_protected_objects` only when `cv_show_related_objects` is enabled, single colon heading, and `POST` raising `ProtectedError`).

### 4. Suggestions
- Ensure pending plan `06.2-09` updates not only the new `### Blocked deletions` sections, but also reconciles the existing `### Delete previews and protected objects` prose in `docs/migrating-1.0.md:392-415`, `CHANGELOG.md:167-176`, and `docs/reference/delete_view.md:229-233` (see detailed findings in `## 06.2-09` below).

### 5. Risk Assessment
- **LOW:** All documentation and acceptance artifacts from `06.2-06` are clean and pass `mkdocs build --strict`.

---

## 06.2-07

### 1. Summary
Plan `06.2-07` (pending gap closure for `G-06.2-1` / `CR-01`) fixes the 500 crash in `GuardianDeleteRelatedObjectsMixin` / `_PermittedPks.__call__` (`src/crud_views_guardian/lib/views.py:68-78`) when a delete preview's cascade tree or protected list contains a model whose `view_` permission cannot be resolved via `f"{opts.app_label}.view_{opts.model_name}"`. Tracing the proposed fix against `guardian/shortcuts.py:515-693` and `guardian/ctypes.py:10-28` confirms that resolving `ct = get_content_type(model)` and passing the bare codename `f"view_{ct.model}"` with `klass=model` (after short-circuiting `_guardian_inactive_actor` and `opts.auto_created`) eliminates all three guardian raise modes (`ContentType.DoesNotExist`, `MixedContentTypeError`, `MultipleObjectsReturned`) at the source.

### 2. Strengths
- **Root-cause elimination verified against `guardian/shortcuts.py:515-562,671-680`:** When `perms` is a bare codename (`f"view_{ct.model}"`, containing no `"."`), `_compute_codenames_and_ctype` (`guardian/shortcuts.py:527-543`) leaves `ctype = None` and never calls `_get_ct_cached(app_label, codename)` (`ContentType.objects.get(app_label=..., permission__codename=...)`). Then `_compute_queryset(None, model)` (`guardian/shortcuts.py:551-553`) derives `ctype = get_content_type(queryset.model)` directly from `klass=model`. This completely bypasses the `ContentType.DoesNotExist`, `MultipleObjectsReturned`, and `MixedContentTypeError` raise sites while preserving the `if with_superuser and user.is_superuser: return queryset` short-circuit (`guardian/shortcuts.py:679-680`) and global fallback (`guardian/shortcuts.py:690-691`, which checks `user.has_perm(ctype.app_label + "." + code)`).
- **Zero-write `GET` preview for M2M through models (`src/crud_views_guardian/lib/views.py:68-78`):** Short-circuiting `opts.auto_created` before calling `get_content_type(model)` avoids `ContentType.objects.get_for_model(model)` lazily inserting a `ContentType` row into the database during a `GET` delete preview.
- **Comprehensive mode coverage (`tests/test1/test_guardian_delete.py`, `tests/test1/app/models.py`):** Tasks `07-01` and `07-02` cover auto-created M2M through tables (`Genre.publishers.through`), `Royalty` (`on_delete=models.RESTRICT` with `default_permissions = ("add", "change", "delete")`), `PublisherProxy` (`Meta.proxy = True`), and polymorphic `Car` under `polymorphic.contrib.guardian.get_polymorphic_base_content_type`.

### 3. Concerns
- **[LOW — Actionable detail in `07-01` (`src/crud_views_guardian/lib/views.py:68-78`)]** In the `if opts.auto_created:` branch of `_PermittedPks.__call__`, Task `07-01` says: *"cache and return, before any content-type access, all pks of the model for an active superuser (`set(model._default_manager.values_list("pk", flat=True))`) and an empty set for everyone else."* Ensure the condition checks `bool(getattr(self.user, "is_authenticated", False) and getattr(self.user, "is_superuser", False))` (after `_guardian_inactive_actor(self.user)`) so a custom or mock unauthenticated object with a truthy `is_superuser` attribute cannot take the superuser branch.
- **[LOW — Unbounded table scan on `opts.auto_created` for superusers (`src/crud_views_guardian/lib/views.py:76-77`)]** Materializing `set(model._default_manager.values_list("pk", flat=True))` fetches all PKs of the through table for a superuser (matching what `get_objects_for_user` + `set(qs.values_list("pk", flat=True))` already does for non-`auto_created` models at `views.py:76-77`). This is consistent with the existing `_PermittedPks` design and acceptable for this gap closure.

### 4. Suggestions
- In `src/crud_views_guardian/lib/views.py` (`_PermittedPks.__call__`), write the `opts.auto_created` superuser check as `if getattr(self.user, "is_authenticated", False) and getattr(self.user, "is_superuser", False):` to keep authentication state explicit alongside the preceding `_guardian_inactive_actor(self.user)` guard.

### 5. Risk Assessment
- **LOW:** The mechanism is small, localized to `_PermittedPks.__call__` in `src/crud_views_guardian/lib/views.py:68-78`, and verified against `guardian 3.5.2` internals.

---

## 06.2-08

### 1. Summary
Plan `06.2-08` (pending gap closure for `G-06.2-3` / `WR-02`) makes `has_protected_objects` unconditional on every `DeleteView` `GET` and `POST`, omits the confirmation `<form>` in `view_delete.content.html` when `has_protected_objects` is `True`, splits `related_objects.html` into labelled (colon heading + list) and unlabelled (colon-free heading + generic sentence) branches, updates `DeleteView.post` to return the 200/422 protection response when `has_protected_objects` is `True` or when `cv_form_valid_process` raises `ProtectedError` / `RestrictedError`, and updates the German catalog. Tracing the plan against the codebase confirms the core design is solid, but reveals one actionable test-override mismatch in Task `08-02` (`tests/test1/test_authorization_templates.py:81-84`) and one subtle interaction in `tests/test1/test_transactions.py` / `DeleteView.get_context_data` to watch.

### 2. Strengths
- **Safe exception backstop in `DeleteView.post` (`src/crud_views/lib/views/delete.py:224-245`, `src/crud_views/lib/views/mixins.py:48-58`):** Wrapping `self.cv_form_valid_process(context)` in `try ... except (ProtectedError, RestrictedError):` catches concurrent/raced DB protection outside `with self.cv_get_atomic():` (`mixins.py:54`), after the transaction has rolled back and without scheduling `transaction.on_commit` (`mixins.py:57`). Setting `context["has_protected_objects"] = True` without copying `exc.protected_objects` / `exc.restricted_objects` into `context["protected_objects"]` ensures the backstop never leaks unpermitted object labels while rendering the generic colon-free blocked notice and omitting the form.
- **Template and modal contract alignment (`src/crud_views/templates/crud_views/view_delete.content.html:8-18`, `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:4-6`, `src/crud_views/lib/messages.py:43-54`):** Even when `cv_show_related_objects = False` (`delete.py:59`), `has_protected_objects = True` triggers `{% if related_summary or has_protected_objects %}` in `view_delete.content.html:8`, includes `related_objects.html`, takes the `{% else %}` (`not protected_objects`) branch in `related_objects.html`, and renders the generic error alert via `alert_data()` (`TEXT_BODY`) while omitting `<form>`.
- **Non-destructive `.po` / `.mo` catalog update (`src/crud_views/locale/de/LC_MESSAGES/django.po:224-226`):** Keeping the existing colon-suffixed `msgid "Deletion is blocked by protected relationships:"` for the labelled branch and adding the two new `msgid`s for the unlabelled branch avoids breaking any existing translation lookups.

### 3. Concerns
- **[MEDIUM — Actionable test failure risk in Task `08-02` (`tests/test1/test_authorization_templates.py:81-84,590-625`)]** Task `08-02` states: *"Apply the constant change in `tests/test1/test_guardian_delete.py` and `tests/test1/test_authorization_templates.py` (prefix without the colon; add `BLOCKED_SENTENCE` where the hidden case is asserted)."* However, in `tests/test1/test_authorization_templates.py:81-84`, the locmem template override for `crud_views/tags/alert.html` is:
  ```python
  "crud_views/tags/alert.html": (
      '<div role="alert" data-mx-alert="{{ alert.level }}"><strong>MX-ALERT {{ alert.heading }}</strong>'
      "<ul>{% for item in alert.items %}<li>{{ item }}</li>{% endfor %}</ul></div>"
  ),
  ```
  Because `OVERRIDES["crud_views/tags/alert.html"]` does **not** render `{{ alert.text }}` (or `{% include alert.body_template %}`), `alert.text` (`BLOCKED_SENTENCE`) will never appear in `response.content` in `test_alert_override_receives_only_permitted_protected_labels` (`test_authorization_templates.py:590-625`) unless `OVERRIDES["crud_views/tags/alert.html"]` is updated to render `{{ alert.text }}`!
- **[LOW — Actionable check on `blocked` slice in `tests/test1/test_authorization_templates.py:615-621`]** In `test_authorization_templates.py:615`, `blocked = content.split(f"MX-ALERT {BLOCKED_HEADING}", 1)[1].split("</div>", 1)[0]`. When `BLOCKED_HEADING` is changed to `"Deletion is blocked by protected relationships"` (no colon):
  - For `label_visible=True`, `alert.heading` has a trailing colon (`"Deletion is blocked by protected relationships:"`), so `blocked` begins with `:</strong><ul>...`.
  - For `label_visible=False`, `alert.heading` has no colon (`"Deletion is blocked by protected relationships"`), so `blocked` begins with `</strong><ul>...` (no leading `:`).
  If Task `08-02` wants to verify the colon-free heading vs. colon heading in `test_authorization_templates.py`, asserting `not blocked.startswith(":")` when `not label_visible` (and `blocked.startswith(":")` when `label_visible`) plus rendering `{{ alert.text }}` in `OVERRIDES["crud_views/tags/alert.html"]` will make the test both pass and verify the new contract.
- **[LOW — Unconditional `NestedObjects` collection on `GET` and `POST` (`src/crud_views/lib/views/delete.py:104-118,197-219`)]** Running `self.cv_get_related_objects()` unconditionally in `get_context_data()` means even when `cv_show_related_objects = False`, `NestedObjects.collect([self.object])` walks the entire cascade graph on `GET` and again on `POST` (before `self.object.delete()` runs Django's `Collector` a second time). While `T-06.2-17` explicitly accepts this overhead, `cv_get_related_objects()` also builds `summary` and `collector.nested()` (`delete.py:109-115`) which are discarded when `cv_show_related_objects` is `False`.

### 4. Suggestions
- In Task `08-02`, update `OVERRIDES["crud_views/tags/alert.html"]` at `tests/test1/test_authorization_templates.py:81-84` to include `{% if alert.text %}<p>{{ alert.text }}</p>{% endif %}` (e.g., right before `<ul>`), so asserting `BLOCKED_SENTENCE in blocked` for `label_visible=False` (and `BLOCKED_SENTENCE not in blocked` for `label_visible=True`) actually tests the `alert.text` seam in the custom alert override.
- In `src/crud_views/lib/views/delete.py:229-245`, when `errors = context.get("delete_protection_errors", [])` and `context.get("has_protected_objects")` are both truthy on `POST`, note that `view_delete.content.html:5-6` renders `protection_errors.html` (the `if delete_protection_errors` branch takes precedence over `else`), which is already consistent with `get_context_data()`.

### 5. Risk Assessment
- **MEDIUM:** The production changes in `delete.py`, `view_delete.content.html`, `related_objects.html`, and `django.po` are well-scoped, but Task `08-02` will hit an immediate test failure in `tests/test1/test_authorization_templates.py` if `OVERRIDES["crud_views/tags/alert.html"]` (`line 81-84`) is not updated to output `{{ alert.text }}`.

---

## 06.2-09

### 1. Summary
Plan `06.2-09` (pending gap closure for `G-06.2-1` and `G-06.2-3` documentation, handoff, and re-verification) updates `docs/reference/delete_view.md`, `docs/reference/theme.md`, `docs/reference/guardian.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`, `06.2-ACCEPTANCE.md`, and `06.2-REVIEW-DISPOSITION.md`, and re-runs the targeted and full test suites across both cached Django 6.0 and 4.2 environments. Inspecting the target markdown files reveals a few existing paragraphs in `docs/migrating-1.0.md`, `CHANGELOG.md`, `docs/reference/delete_view.md`, and `06.2-ACCEPTANCE.md` that need to be reconciled so old and new subsections do not contradict each other.

### 2. Strengths
- **Strict adherence to repository Breaking/migration pairing rule (`CLAUDE.md`, `CHANGELOG.md`, `docs/migrating-1.0.md`):** Adding `### Blocked deletions` in `docs/migrating-1.0.md` paired with the `**Blocked deletions.**` `### Breaking` entry in `CHANGELOG.md` and verifying the anchor with `.venv/bin/mkdocs build --strict` satisfies `D-14`.
- **Explicit Phase 7 carry-forward of out-of-scope content-type risks (`06.2-ACCEPTANCE.md`):** Carrying forward the `MixedContentTypeError` risk in `GuardianQuerysetMixin.get_queryset` (`src/crud_views_guardian/lib/mixins.py:182-195`) and `GuardianViewSet.get_objects_for_user` (`src/crud_views_guardian/lib/viewset.py:89-108`) for proxy/polymorphic-base ViewSets ensures Phase 7's stability inventory has an accurate boundary.

### 3. Concerns
- **[MEDIUM — Actionable self-contradiction between adjacent sections in `docs/migrating-1.0.md:390-415` and `CHANGELOG.md:167-176`]** Task `09-01` instructs adding `### Blocked deletions` directly after `### Delete previews and protected objects` in `docs/migrating-1.0.md` (and adding `**Blocked deletions.**` after `**Delete previews and protected objects.**` in `CHANGELOG.md`). However, the existing `### Delete previews and protected objects` section in `docs/migrating-1.0.md:392-415` currently states:
  - Line 392: *"With `cv_show_related_objects`, the context of a delete page changes in two ways... The new `has_protected_objects` is `True` whenever protected objects block the deletion..."* (now inaccurate: `has_protected_objects` is set on every delete page regardless of `cv_show_related_objects`).
  - Lines 406-414: shows a single-branch `{% if has_protected_objects %}` snippet for `crud_views/snippets/delete/related_objects.html` without the two-branch `{% if protected_objects %}...{% else %}...{% endif %}` structure that `### Blocked deletions` immediately below it tells users to adopt.
  - Similarly, `CHANGELOG.md:167-171` says *"With `cv_show_related_objects`, `protected_objects` now holds... The new `has_protected_objects` says whether protected objects block the deletion at all."*
- **[LOW — Actionable omission in `docs/reference/delete_view.md:229-233`]** Task `09-01` lists lines `172-187` and `272-284` of `docs/reference/delete_view.md`, but lines `229-233` (under `### Template Customization`) also describe copying `crud_views/view_delete.content.html` and `related_objects.html` without mentioning `{% if not has_protected_objects %}` around `<form>` or the two-branch `related_objects.html` copy.
- **[LOW — Actionable omission in `06.2-ACCEPTANCE.md:98,129-136`]** Task `09-02` updates row 116 of the `Documentation evidence` table, settled contract 3 (`155-162`), and `Open items` (`202-231`), but does not mention updating:
  1. The `Breaking/migration pairing` table at `06.2-ACCEPTANCE.md:129-136` to include the new `Blocked deletions` | `#blocked-deletions` row.
  2. The `AUTH-03` row in the `Requirement evidence` table at `06.2-ACCEPTANCE.md:98` to reference the `06.2-07` and `06.2-08` commits/tests and `#blocked-deletions`.

### 4. Suggestions
- In Task `09-01`, also update `docs/migrating-1.0.md:392-415`, `CHANGELOG.md:167-176`, and `docs/reference/delete_view.md:229-233` so that `Delete previews and protected objects` does not claim `has_protected_objects` requires `cv_show_related_objects` or show a stale single-branch `related_objects.html` snippet that contradicts `### Blocked deletions`.
- In Task `09-02`, add the `Blocked deletions` | `#blocked-deletions` row to the `Breaking/migration pairing` table at `06.2-ACCEPTANCE.md:129-136` and update the `AUTH-03` row at `06.2-ACCEPTANCE.md:98`.

### 5. Risk Assessment
- **LOW:** Documentation and verification-only plan; addressing the adjacent-section wording in `docs/migrating-1.0.md`, `CHANGELOG.md`, `docs/reference/delete_view.md`, and `06.2-ACCEPTANCE.md` will ensure internal consistency before Phase 7.

---

## Cross-Plan Synthesis & Overall Risk Assessment

- **Executed Plans (`06.2-01` – `06.2-06`):** The implemented guards for HTTP `DELETE` (`src/crud_views/lib/views/delete.py:27-48`), Guardian parent-`None` and inactive actors (`src/crud_views_guardian/lib/mixins.py:10-300`, `src/crud_views_guardian/lib/views.py:139-252`), formset fragment authorization and coordinate ancestry (`src/crud_views/lib/formsets/mixins.py:47-78`, `src/crud_views/lib/formsets/formsets.py:396-506`), and `GuardianViewSet` configuration/manage reporting (`src/crud_views_guardian/lib/viewset.py:39-49`, `src/crud_views_guardian/lib/views.py:254-349`) are well-structured and verified in the codebase.
- **Pending Gap-Closure Plans (`06.2-07` – `06.2-09`):**
  1. **`06.2-07` (Ready to execute, LOW risk):** Resolves `G-06.2-1` / `CR-01` cleanly in `_PermittedPks.__call__` (`src/crud_views_guardian/lib/views.py:68-78`) by short-circuiting `opts.auto_created` and passing a bare codename (`f"view_{ct.model}"`) with `klass=model` to `guardian.shortcuts.get_objects_for_user`.
  2. **`06.2-08` (Needs minor test-override adjustment in `08-02`, MEDIUM risk):** Resolves `G-06.2-3` / `WR-02` in `src/crud_views/lib/views/delete.py`, `view_delete.content.html`, `related_objects.html`, and `django.po`. Before running `08-02`'s verification, ensure `OVERRIDES["crud_views/tags/alert.html"]` in `tests/test1/test_authorization_templates.py:81-84` renders `{{ alert.text }}` if `BLOCKED_SENTENCE` is asserted there.
  3. **`06.2-09` (Needs minor prose reconciliation in `09-01`/`09-02`, LOW risk):** Reconcile the existing `Delete previews and protected objects` text (`docs/migrating-1.0.md:392-415`, `CHANGELOG.md:167-176`, `docs/reference/delete_view.md:229-233`) with the new `### Blocked deletions` section, and add `#blocked-deletions` to the pairing table in `06.2-ACCEPTANCE.md:129-136`.
