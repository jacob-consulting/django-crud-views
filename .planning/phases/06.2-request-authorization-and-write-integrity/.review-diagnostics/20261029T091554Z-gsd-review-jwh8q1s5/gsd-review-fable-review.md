# Cross-AI Plan Review, Phase 6.2, cycle 2/5 (plans at 163bb00)

Repository access was available. Source, templates, tests, Django 6.0.9 and Guardian 3.5.2 in the cached nox environment were read directly. Line numbers below refer to the working tree at 163bb00.

## 06.2-01

**Summary.** Rejects HTTP DELETE on `DeleteView`, moves protected-label filtering into the `cv_filter_related_objects` hooks, captures an independent `has_protected_objects` flag, and gates both the enclosing include and the inner alert on it.

**Strengths.**
- H01 is executably closed. `view_delete.content.html` is in `files_modified` (`06.2-01-PLAN.md:10,43`), the 01-01 action says "Update BOTH" templates (`06.2-01-PLAN.md:99`), and the key link states the mechanism (`:56`). The current gate at `src/crud_views/templates/crud_views/view_delete.content.html:8` and the alert at `snippets/delete/related_objects.html:4` are exactly the two leaks; the root model is excluded from the summary at `src/crud_views/lib/views/delete.py:90-91`, so a protected-only preview really does have an empty summary.
- The DELETE claim ordering is correct. For a top-level Guardian delete, `GuardianParentPermissionMixin.has_permission` returns `True` (`src/crud_views_guardian/lib/mixins.py:191-194`) and `GuardianObjectPermissionMixin.has_permission` returns `True` for any authenticated user (`:31-38`) without calling `cv_get_action_object`; only `get_object()` loads the row (`:50-58`). Core `CrudViewPermissionRequiredMixin.has_permission` loads the object first (`src/crud_views/lib/view/base.py:900-910`). The truth at `06.2-01-PLAN.md:24` matches both.
- A05 fix is right: Django's `DeletionMixin.delete` at `.nox/.../django/views/generic/edit.py:225-228` does `get_object` then `delete()`, so overriding `delete()` and trimming `http_method_names` closes both routes.
- A01 split is correct against source: custom errors re-render at `delete.py:206-214`; `cv_form_valid` at `:222` calls `delete()` with no `ProtectedError` handler, inside `cv_get_atomic()` (`src/crud_views/lib/views/mixins.py:54-57`), so the test client re-raises and storage is intact.
- A02 names the right assertions: `tests/test1/test_delete.py:153` (`len(protected_objects) > 0` with a delete-only user) and `tests/test1/test_guardian_delete.py:50,66,73`. The unnamed `test_delete_alerts_render_through_the_frame` (`test_delete.py:304-318`) stays compatible: it counts one danger alert and never asserts the Contract label.

**Concerns.**
- LOW N-01: a subclass that restores `"delete"` in `http_method_names` still has a `delete` attribute, so Django's `_allowed_methods()` advertises `DELETE` in the 405 `Allow` header and in OPTIONS. The plan pins only the default OPTIONS (`06.2-01-PLAN.md:99`). Pin `Allow` excludes `DELETE` in the subclass-restoration test too, or override `_allowed_methods`.
- LOW N-02: 01-03 must "exercise inherited subclasses restoring the method name" (`06.2-01-PLAN.md:127`) but plan 01 has no route-fixture contract and forbids duplicate view keys. State the mechanism: `monkeypatch.setattr(RegisteredDeleteView, "http_method_names", [...])` on an existing registered class, which auto-restores.

**Suggestions.** Add the `Allow` assertion to 01-01/01-03; name the monkeypatch mechanism in 01-03.

**Risk Assessment.** Low. Decisions are locked, mechanisms verified, remaining items are test precision.

## 06.2-02

**Summary.** Centralizes the parent-permission-key resolver, resolves the URL parent before the optional permission check, always runs the no-object action-state gate, denies inactive actors in dispatch, both `has_permission` overrides, callable helpers, the strict ViewSet helper and `_PermittedPks`, and changes the wrong-type `cv_has_access` fallback from `True` to `False`.

**Strengths.**
- B4 mechanism is exact: `_guardian_check_parent` returns before `get_object_or_404` when the key is `None` (`src/crud_views_guardian/lib/mixins.py:233-235`), and both create helpers do `permissions.get(perm_key)` then `perm.split(".")` (`src/crud_views_guardian/lib/views.py:146-155,195-204`), which is the crash the plan removes.
- B5 placement is correct. Django's `ModelBackend.has_perm` already returns `False` for inactive users (`django/contrib/auth/backends.py:174`), and `ObjectPermissionChecker` denies inactive at `guardian/core.py:76`, so object-checker paths are preservation tests as the plan says (`06.2-02-PLAN.md:103`). The leak is `get_objects_for_user`, which returns the full queryset for any superuser at `guardian/shortcuts.py:679-680` and never consults `is_active`; used at `mixins.py:164-170`, `views.py:67` and `viewset.py:67-73`.
- A13 declaration is safe: the parent mixin is first in every Guardian MRO (`views.py:24-110`), both existing declarations default to the same values (`mixins.py:28-29,95-96`), and leaf overrides still win; existing `raising=False` patches (`tests/test1/test_guardian.py:886,897,916`) keep working.
- A08 fixture contract names `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:146-151`), `_VOCAB_CACHE` (`src/crud_views/lib/check.py:321`), URLConf and URL caches, with cleanup in `finally`.

**Concerns.**
- HIGH N-03: the H02 resolution ("wrong-model parents deny", `06.2-02-PLAN.md:24,89,159`) treats the wrong-type call as "unexpected", but two library render paths legitimately produce it. `_cv_get_action_context` passes the page object to `cls.cv_has_access` for every configured key (`src/crud_views/lib/view/base.py:691-710`), and `cv_get_cls_assert_object` lets a non-object target receive any object (`:497`). The documented filter `cv_context_has_permission` passes `view.object` for any key (`src/crud_views/templatetags/crud_views.py:468-473`; recipe at `docs/reference/context_buttons.md:531-539`, `docs/faq.md:130-136`). On a Guardian child detail, update or delete page, a `create` key in `cv_context_actions` or that filter calls `GuardianBookCreateView.cv_has_access(user, <Book>)`. Today that returns `True`; after plan 02 it returns `False` for every user, including those holding the parent grant, so the create control vanishes or renders disabled while the direct GET still succeeds. Fail-closed, so not a disclosure, but a visible regression of a documented path that no plan task or matrix cell exercises, and plan 06 would ship it as "intentional". A strictly better contract exists: when `isinstance(obj, cls.cv_viewset.model)`, resolve the parent through `cls.cv_viewset.parent.get_attribute()` and check that parent; deny only unrelated types.

**Suggestions.** Rewrite the 02-01 helper contract as: parent instance, check it; own-model child instance, check its FK parent; anything else or `None`, `False`. Add a real request test rendering a `create` action and the `cv_context_has_permission:"create"` filter from a Guardian child detail page with and without the parent grant. Update `test_create_cv_has_access_child_wrong_type_obj` to the new semantics and adjust plan 06's Breaking text.

**Risk Assessment.** Medium. Inactive and parent-None work is sound; the wrong-type decision needs the fix above before execution.

## 06.2-03

**Summary.** Authorizes fragment GETs through the cooperative `get_object` gate before `get_template_html`, adds a private coordinate validator covering key path, root identity, child position, persisted FK ancestry and unsaved `None` chains, adds two UUID test models, and normalizes unsaved UUID-default instances to the `None` sentinel.

**Strengths.**
- The defect mechanism is confirmed: `FormSetMixinBase.get` returns the fragment before `super().get()` (`src/crud_views/lib/formsets/mixins.py:37-45`), and Guardian authorization lives in `get_object()` (`mixins.py:50-58`), so no object gate runs.
- A06 payloads match the wire protocol. The browser derives `pk` from `prefix_key` with the regex `(None|<PK grammar>)-(\d+)` (`src/crud_views/static/crud_views/js/formset.js:150-161`) where the grammar is `XFormSet.data["pk"] = self.pk.value` (`src/crud_views/lib/formsets/render_tree.py:188`), sends `pk`, `num`, `formset_parent_prefix_key` (`formset.js:318-323`), and the top-level parent prefix is `""` (`render_tree.py:135-138`). The nested prefix shape `{pub.pk}-0-{row}` comes from `formsets.py:120-124,159-167`. The table at `06.2-03-PLAN.md:79` is correct.
- A14 is a real latent fix, not only compatibility: `FormSet.init` uses `form.instance.pk` (`formsets.py:123`) and a UUID-default model gets a fresh pk on every unbound form, so GET and POST prefixes would differ; `Author` has such a default (`tests/test1/app/models.py:14`).
- A07 is executable: `tests/test1/app` has no `migrations` directory, so pytest-django creates the new tables directly.
- A15 is confirmed: `num.isdigit()` at `mixins.py:54` accepts `²`, `int(num)` at `:68` raises.

**Concerns.**
- LOW N-04: `FormSets.get_template` always passes `index=0` (`src/crud_views/lib/formsets/formsets.py:379`), while `init` numbers child formsets by declared position (`:159-167`). For a declaration with two child formsets under one parent, the second child's fragment prefix is already wrong today. The validator's "each declared child position" wording (`06.2-03-PLAN.md:102`) could be read as fixing this; it does not, because the request carries no child index. Either pass the declared index into `template()` or scope the claim to the request coordinates and record the multi-child limitation for the 6.3 lifecycle slice.

**Suggestions.** Add the N-04 scoping sentence; otherwise execute as written.

**Risk Assessment.** Medium-low. Highest implementation complexity in the phase, but every claimed coordinate rule is grounded in source.

## 06.2-04

**Summary.** Removes the inert `GuardianViewSet.cv_guardian_accept_global_perms` field with a Mapping-guarded before-validator, atomically replaces the manage reader and config leaf, then adds per-view effective policy and applicability rows.

**Strengths.**
- A09 is closed: 04-01 owns `viewset.py:23`, the reader at `src/crud_views_guardian/lib/views.py:231`, `config_table.html:15-18` and `tests/test1/test_guardian.py:636-648` in one commit (`06.2-04-PLAN.md:92`).
- Blast radius verified: the example constructs `GuardianViewSet` without the flag (`examples/bootstrap5/guardian_demo/views.py:20`); tests set it on view classes only (`tests/test1/test_guardian.py:861,874,886`).
- A17 applicability categories match the resolver: the parent mixin consults the flag only inside `_guardian_has_parent_perm` (`mixins.py:224`), which is skipped when the resolved key is `None` (`:233-234`).
- The before-validator precedent (`src/crud_views/lib/formsets/formsets.py:270-277`) and registration order (`viewset/__init__.py:125-158`) support "failed construction leaves no registry entry".

**Concerns.**
- LOW N-05: `model_validate(existing_instance)` (`06.2-04-PLAN.md:92`) does not run validators under Pydantic's default `revalidate_instances="never"`, so it proves nothing about the Mapping guard. Keep the explicit non-mapping input case as the guard evidence and drop or label the instance case.

**Suggestions.** Also update `docs/reference/guardian.md:239-243`, which still lists the ViewSet flag as a manage row; plan 06-01 covers manage rows generically, so name this line.

**Risk Assessment.** Low.

## 06.2-05

**Summary.** Replays the actor matrix on isolated real routes and proves six native template seams receive only safe context.

**Strengths.**
- Every method-ordering cell checked against source holds: Guardian top-level DELETE 405 before object lookup (`06.2-05-PLAN.md:90`, mechanism in plan 01 strengths); core DELETE 403/403/404 (`:92`, `base.py:900-910` with `cv_get_action_object` raising `Http404` at `:368-375`); nested parent 403/404 before method selection (`mixins.py:196-202,235`); Guardian anonymous 302/403/404 (`mixins.py:204-210`).
- All six override paths exist on disk (`src/crud_views/templates/crud_views/view_list.content.html`, `tags/card.html`, `tags/button/action.html`, `tags/alert.html`, `formsets/formset.html`, `src/crud_views_guardian/templates/crud_views/view_guardian_manage.html`).
- Manage gate rows match `ManageView.has_permission` (`src/crud_views/lib/views/manage.py:30-39`).

**Concerns.**
- MEDIUM N-06: "Set manage settings explicitly" (`06.2-05-PLAN.md:103`) names no mechanism. `crud_views_settings.manage_views_enabled` and `manage_group` are Pydantic snapshots taken at import (`src/crud_views/lib/settings.py:27-28`), so `override_settings(CRUD_VIEWS_MANAGE_VIEWS_ENABLED=...)` leaves the fixture `"yes"` active and the group-mode rows (`:99-101`) pass vacuously, which is the exact masking the plan warns about. Existing precedent is `monkeypatch.setattr(crud_views_settings, "manage_views_enabled", ...)` (`tests/test1/test_manage.py:122,140,154`). `DEBUG` is read live (`manage.py:33-35`), so `override_settings(DEBUG=...)` is correct for that dimension only.

**Suggestions.** Write the monkeypatch mechanism into the matrix preamble and 05-01 action. If N-03 changes the helper contract, add a child-detail-page `create` cell.

**Risk Assessment.** Low once N-06 is pinned.

## 06.2-06

**Summary.** Updates references, pairs Breaking and migration entries, adds a standalone theme section, and records both supported-version runs against the measured baseline.

**Strengths.**
- A11 closed with real numbers (`06.2-06-PLAN.md:80`); the 06-03 loop runs both environments plus the full suite (`:120`).
- A16 placement is safe: `theme.md` headings show the fence-counted sections at `docs/reference/theme.md:136,191,272`, with `tests/test1/test_alerts.py:253` and `tests/test1/test_form_button_docs.py:170-171` enforcing one fence each; a new level-two section after `:318` cannot disturb them.
- `mkdocs` strict is explicitly not treated as semantic proof (`:89`).

**Concerns.**
- LOW N-07: plan 01 moves core protected filtering inside `cv_filter_related_objects` (`06.2-01-PLAN.md:99`). A project override that returns `related.protected` unchanged, which is exactly the shape the Guardian mixin has today (`src/crud_views_guardian/lib/views.py:46-50`), re-leaks labels. Also, the delete view's own `cv_guardian_accept_global_perms` now decides label visibility for other models' protected rows (`views.py:45,67`). Neither appears in 06-01/06-02 (`06.2-06-PLAN.md:89,103`); add both to the migration guidance.
- LOW N-08 (contingent on N-03): `docs/reference/context_buttons.md` and `docs/faq.md` are not in `files_modified`; whichever helper contract is adopted, the `cv_context_has_permission` recipe must state what it means for `create` keys on child object pages.

**Suggestions.** Add the two migration bullets; add the two doc files if N-03 keeps any Breaking semantics.

**Risk Assessment.** Low.

## Cross-plan assessment

Wave ownership is consistent: plans 03 and 04 share wave 3 with disjoint files; plans 01, 02 and 04 edit `src/crud_views_guardian/lib/views.py` sequentially. Plan 02's resolver is a dependency of plan 04's applicability rule and of plan 05's parent-None cells; it is declared class-callable in both places. The only cross-plan inconsistency is N-03: plan 02's helper semantics, plan 05's matrix and plan 06's Breaking entry all encode the "wrong type denies" decision without any task rendering a create action from a child object page.

## Prior-item closure ledger

| Item | Status | Evidence |
| --- | --- | --- |
| H01 | Closed, reviewer sign-off | `06.2-01-PLAN.md:10,43,56,99`; both leak sites `view_delete.content.html:8` and `related_objects.html:4` owned. |
| H02 | Closed as the plan/test conflict; residual gap N-03 | `06.2-02-PLAN.md:89,159` owns `tests/test1/test_guardian.py:337-341` and docs in `06.2-06-PLAN.md:103`. Sign-off is conditional on resolving N-03, because the chosen semantics break the render paths at `base.py:691-710` and `templatetags/crud_views.py:468-473`. |
| A01 | Closed | `06.2-01-PLAN.md:99,113` |
| A02 | Closed | `06.2-01-PLAN.md:99,113` name all three tests |
| A03 | Closed | evidence rules in every plan's `<verification>`; e.g. `06.2-01-PLAN.md:127`, `06.2-05-PLAN.md:128` |
| A04 | Closed | `06.2-01-PLAN.md:99,113` |
| A05 | Closed | `06.2-01-PLAN.md:99` |
| A06 | Closed | `06.2-03-PLAN.md:79`, verified against JS and render tree |
| A07 | Closed | `06.2-03-PLAN.md:37,104` |
| A08 | Closed | contracts in 02, 03, 04, 05 preambles |
| A09 | Closed | `06.2-04-PLAN.md:92` |
| A10 | Closed | `06.2-05-PLAN.md:86-103`, plus `06.2-01-PLAN.md:24,127`, `06.2-02-PLAN.md:89,103` |
| A11 | Closed | `06.2-06-PLAN.md:80,120` |
| A12 | Closed | `06.2-04-PLAN.md:92` |
| A13 | Closed | `06.2-02-PLAN.md:89` |
| A14 | Closed | `06.2-03-PLAN.md:104,154` |
| A15 | Closed | `06.2-03-PLAN.md:102` |
| A16 | Closed | `06.2-06-PLAN.md:103` |
| A17 | Closed | `06.2-04-PLAN.md:106` |

The AUTH-06 unclassified probe remains a flagged assumption at `06.2-04-PLAN.md` and in the plan 06 handoff; it is correctly carried, not resolved, and is not counted as a defect.

## Genuinely unresolved plan concerns (deduplicated)

1. **N-03 HIGH** (plan 02, echoes in 05 and 06): wrong-type `cv_has_access` denial regresses the create control on Guardian child object pages; resolve the parent from an own-model child instance instead, and test that render path.
2. **N-06 MEDIUM** (plan 05): manage-mode cells need `monkeypatch.setattr(crud_views_settings, ...)`, not `override_settings`, or the "yes" default masks them.
3. **N-01 LOW** (plan 01): pin `Allow` header excludes `DELETE` for subclass restoration.
4. **N-02 LOW** (plan 01): name the monkeypatch mechanism for the subclass-restoration test.
5. **N-04 LOW** (plan 03): scope the "declared child position" claim; `get_template` hardcodes `index=0`.
6. **N-05 LOW** (plan 04): `model_validate(instance)` is not guard evidence.
7. **N-07 LOW** (plan 06): migration guidance for `cv_filter_related_objects` overrides and the flag's effect on protected labels.
8. **N-08 LOW** (plan 06, contingent on N-03): `context_buttons.md` and `faq.md` filter recipe.
