I have everything I need. Writing the review now.

# Cross-AI Plan Review: Phase 6.2 (plans 01–09)

**Scope note.** Plans 01–06 are executed and summarized (commits `eda7018` … `fe51328`); I verified their claims against the current source, not their summaries. Plans 07–09 are pending; those sections carry the actionable findings. HEAD at review time: `d487eb5`. Baseline greps for every literal the pending plans declare as "0 at HEAD" were measured and are all 0.

---

## 06.2-01

**Summary.** Executed. The source matches the plan: `_DeleteMethodGuardMixin` sits between `CrudView` and `generic.DeleteView` (`src/crud_views/lib/views/delete.py:47`), its `dispatch` short-circuits DELETE to `http_method_not_allowed` (`:37-40`), `_allowed_methods` strips DELETE (`:42-44`), `http_method_names` is filtered (`:48`), `has_protected_objects` is captured before the hook (`:205`), and the core filter drops unviewable protected labels (`:194`). Templates gate on the flag (`view_delete.content.html:8`, `related_objects.html:4`). The plan achieved AUTH-01 and the label-confidentiality half of AUTH-03.

**Strengths.**
- The dispatch-guard design is correct about MRO: `GuardianParentPermissionMixin.dispatch` (`mixins.py:235-242`) and `PermissionRequiredMixin` run before the guard, and `GuardianObjectPermissionMixin.has_permission` returns True without object lookup (`mixins.py:48-50`), so "Guardian 405 before `get_object`" holds.
- `DeletionMixin.delete` identity preserved; the Django 4.2 warning test exists (`tests/test1/test_delete.py:396-424`).

**Concerns (historical, now owned by 07/08).**
- **HIGH (historical):** Task 01-02 routed `related.protected` through `_PermittedPks` without a fail-closed rule for models that carry no `view_` permission. The plan's edge truths list "empty, protected-only, single, hidden" but never "model without a grantable view permission" or "auto-created through table", which is exactly G-06.2-1. `_PermittedPks.__call__` still builds `f"{app_label}.view_{model_name}"` (`src/crud_views_guardian/lib/views.py:74-76`); guardian 3.5.2 resolves that through `_get_ct_cached` before its superuser short-circuit (`guardian/shortcuts.py:530-540`, `:650-656`).
- **MEDIUM (historical):** The Round 1 ledger explicitly rejected catching `ProtectedError` ("lifecycle change outside this phase") while D-08 says filtering "must never make deletion appear unblocked". The retained enabled form plus 500 is G-06.2-3. `post()` still honors only `delete_protection_errors` (`delete.py:231-239`).

**Risk.** LOW for what shipped; the two residuals are correctly re-planned.

---

## 06.2-02

**Summary.** Executed. Source confirms the design: `_cv_guardian_create_parent` resolves parent or single-FK own child and denies M2M/unrelated (`src/crud_views_guardian/lib/views.py:138-160`); `_cv_action_enabled_for_context` is overridden for nested create (`:162-171`) and consumed at every advertised call site (`base.py:715`, `buttons.py:109,182,234,291`, `card.py:66,89`, `mixins.py:176`); the parent mixin denies inactive actors before parent logic (`mixins.py:238-239`) and declares the two policy names annotation-only (`:223-225`); the ViewSet helper returns `.none()` for inactive users (`viewset.py:98-100`). The isolated-route fixture contract (registry snapshot, `_VOCAB_CACHE`, `clear_url_caches`, temporary `ROOT_URLCONF`) is implemented (`test_guardian_parent_none.py:34-175`); inactive tests use `AllowAllUsersModelBackend` (`test_guardian_inactive.py:24-31`).

**Strengths.**
- The adapter approach keeps request dispatch calling `cv_action_enabled` directly, so no new public hook was frozen.
- The M2M fail-closed boundary is explicit in code and docstrings, not just in tests.

**Concerns.**
- **LOW (historical, open):** The review's WR-01 ("core nested create still evaluates rendered state against the page object") remains `open` in the disposition and is not in the ACCEPTANCE open-items list. Plan 09-02 leaves it untouched; the Phase 7 handoff should name it (see 09).

**Risk.** LOW.

---

## 06.2-03

**Summary.** Executed. `FormSetMixinBase.get` now sets `self.object` through `get_object()` before `get_template_html` (`src/crud_views/lib/formsets/mixins.py:46-51`), and `get_template_html` runs `_cv_validate_fragment_coordinates` against the authorized root before `get_template` (`:66-75`). The validator (`formsets.py:396+`) checks declared path, parent-prefix grammar, declared child indices, ASCII row indices and FK ancestry with `exists()`, and documents the A19 index-0 limitation in its own docstring. The UUID test models exist (`tests/test1/app/models.py:201-219`).

**Strengths.**
- Validation is read-only and declaration-driven; UUIDs are matched by `FormSet.PK` grammar, not hyphen splitting.
- The A19 deferral is honest and is pinned by a characterization test rather than claimed as a round trip.

**Concerns.**
- **LOW:** IN-04 in the review ("slug-pk roots are now a hard 400") is a consequence of this plan and remains open in the disposition; not carried in ACCEPTANCE. Phase 7 should receive it alongside A19.

**Risk.** LOW.

---

## 06.2-04

**Summary.** Executed. The removed key is rejected by a `mode="before"` validator guarded by `isinstance(data, Mapping)` (`src/crud_views_guardian/lib/viewset.py:38-47`); `STRICT_HELPER_POLICY` feeds both the helper call and the manage context (`viewset.py:11`, `views.py:280`); `get_view_data` projects per-view applicability and policy from the view class (`views.py:318-349`). Manage tests patch the Pydantic singleton rather than `override_settings` (`test_guardian_policy.py:546-550`), which is the only thing that works since the fields are import-time snapshots (`settings.py:27-28`).

**Strengths.**
- Removal and manage reader changed in the same task, so the manage page never broke mid-wave.
- Applicability rule is the same shared resolver dispatch uses (`_guardian_resolve_parent_perm_key`, `mixins.py:248-256`).

**Concerns.**
- **LOW (open info):** IN-02 notes `STRICT_HELPER_POLICY` is a mutable module dict read at call time (`viewset.py:11`, `:101-102`); a `MappingProxyType` would close it. Not in scope for 07–09 but a cheap Phase 7 item.
- The AUTH-06 "unclassified" probe row is still flagged unresolved; the plan and ACCEPTANCE say so plainly, which is correct.

**Risk.** LOW.

---

## 06.2-05

**Summary.** Executed; test-only. Both modules exist (`test_authorization_matrix.py`, 22 functions → 550 parametrized cases; `test_authorization_templates.py`, 12 functions → 32 cases). The locmem override fixture sets `APP_DIRS=False` and places the loader first (`test_authorization_templates.py:93-95`). The matrix delete family `MxDelete` does not set `cv_show_related_objects` and sets `cv_modal=True` (`test_authorization_matrix.py:151-162`), which plan 08 relies on and correctly describes.

**Strengths.**
- Exact-status cells with storage snapshots and hook counters (`_snapshot`, `_assert_no_write`, `:493-507`).
- Manage gate cells patched at the singleton with teardown.

**Concerns.**
- **LOW (historical):** The matrix pinned the 500 as the contract (`test_granted_database_protect_delete_reraises`, `:729-741`), so "post-fix replay" cemented a defect. Plan 08-02 rewrites it; fine.
- **LOW:** No matrix cell deletes a Publisher that owns a Genre, which is why CR-01 reached UAT. 07-01 adds the route regression; consider one matrix delete cell with an M2M row so the family-parametrized replay also covers it (see 07).

**Risk.** LOW.

---

## 06.2-06

**Summary.** Executed. The five Breaking entries and their migration subsections exist (`CHANGELOG.md:160-180`, `docs/migrating-1.0.md:339-490`), the theme section is standalone (`theme.md:325`), and ACCEPTANCE carries measured counts (`06.2-ACCEPTANCE.md:40-46`) with the "database PROTECT still raises" row at line 116 and the retained-500 open item at line 230, exactly as plan 09 cites.

**Strengths.**
- Code-to-doc evidence table names a test per claim.
- Not-run matrix combinations are stated, not implied.

**Concerns.**
- **MEDIUM (historical):** The handoff told Phase 7 the preview was "hardened" while the delete page could 500 on any M2M-bearing root and on any blocked POST. Three documentation sentences now assert the former lifecycle (`delete_view.md:186-187`, `:280-284`) and one copyable recipe carries the colon heading (`theme.md:345-349`). Plan 09 owns all of them.

**Risk.** LOW once 09 lands.

---

## 06.2-07

**Summary.** Pending. The diagnosis is sound and I confirmed it independently: guardian 3.5.2 resolves an app-qualified string via `ContentType.objects.get(app_label, permission__codename)` and requires equality with `get_content_type(klass)` before the superuser check (`shortcuts.py:48-51`, `:530-540`, `:547-562`, `:650`); a bare codename skips `_get_ct_cached` entirely because `ctype` stays `None` until `_compute_queryset` derives it from `klass`. `create_permissions` skips auto-created models, and `get_for_model` inserts a row on miss (`contenttypes/models.py:49-58`), so the `auto_created` short-circuit is needed to avoid a write on GET. The fix shape is the minimal correct one.

**Strengths.**
- Rejects the broad `except` and the review's precheck shape with reasons that hold under a polymorphic `GUARDIAN_GET_CONTENT_TYPE` (`polymorphic/contrib/guardian.py` returns the base CT; `guardian.ctypes.get_content_type` imports the dotted path at call time, so the monkeypatch in 07-02 is effective).
- Superuser parity with core is explicitly decided and tested, including the inactive-superuser guard staying first (`mixins.py:10-17`, `views.py:69`).
- All fixtures the tasks name exist: `client_guardian`, `user_guardian`, `publisher_a`, `cv_guardian_publisher` (`conftest.py:560-609`), `user_guardian_object_perm` (`tests/lib/helper/guardian.py`), and the cascade route (`tests/test1/app/views.py:757-767`).

**Concerns.**
- **MEDIUM — global-fallback codename changes under proxy/polymorphic content types, undocumented.** With `accept_global_perms=True`, guardian checks `user.has_perm(ctype.app_label + "." + code)` (`shortcuts.py:664`). After the fix, `code` is `view_<ct.model>`: for `PublisherProxy` that is `view_publisher`, and for `Car` under the polymorphic base ctype it is `view_vehicle`, not `view_car`. That is guardian's own semantics and probably right, but it is a contract (a global `view_publisher` now reveals proxy-root labels). Plan 07 does not test the global-fallback branch for these modes, and plan 09-01's guardian.md paragraph says only "resolves … against guardian's own content type". Add one direct-call assertion for `accept_global=True` with a global `view_vehicle` under the patched setting, and have 09-01 state the codename rule.
- **MEDIUM — 07-02's verify selection cannot see collateral damage from two new test-app models.** `Royalty` (RESTRICT child of `Publisher`) and `PublisherProxy` add permissions and content types to the `app` label and add a relation to every Publisher cascade. The verify runs only `test_guardian_delete.py`, `test_guardian.py`, `test_polymorphic.py`. Tests that enumerate app permissions/content types or count queries on Publisher deletes (none found in the delete/matrix modules, but `test_manage.py`, `test_checks.py` and any `assert_num_queries` elsewhere were not checked by the plan) would only fail two waves later in 09-03. Add `test_manage.py` and `test_checks.py` to 07-02's selection, or run the full `tests/test1` once at the end of 07.
- **LOW — superuser branch materializes every through-table pk.** `set(model._default_manager.values_list("pk", flat=True))` for an auto-created through model loads all rows of that table, not only those in the tree. This mirrors what guardian's superuser short-circuit already does for other models at `views.py:77`, so it is parity, not regression. Worth a sentence in the docstring.
- **LOW — helper naming.** 07-01 generalizes `_context_contracts(response)` into `_context_instances(response, model)` in `test_guardian_delete.py`, while `test_delete.py` already defines `_context_instances(value, model, depth)` with a different signature (`test_delete.py:150-164`). Pick `_response_instances` to match the core module.

**Suggestions.**
- Add one `test_authorization_matrix.py` delete cell with a Genre linked to `world.a` so the three-family replay covers M2M roots, not only the Guardian cascade route.
- 07-02's proxy test should assert both branches of the ctype: with the default setting (`view_publisher` on concrete CT) and that the proxy's own `view_publisherproxy` grant does **not** count (it lives on the proxy CT, which guardian does not consult). That pins the documented semantics rather than leaving them implicit.

**Risk.** LOW–MEDIUM. The mechanism is right; the gaps are documentation of the codename rule and the narrow verify selection.

---

## 06.2-08

**Summary.** Pending. The root cause is correctly stated: `has_protected_objects` is computed only inside `cv_show_related_objects` (`delete.py:202-205`), `post()` reads only custom errors (`:231`), the form renders unconditionally (`view_delete.content.html:12-18`), and the colon heading serves the empty case (`related_objects.html:5`; `alert_data` picks `TEXT_BODY` with empty text, `messages.py:44`). The fix shape is coherent and mirrors the existing custom-protection page. I confirmed `Model.delete()` collects before any delete SQL (`django/db/models/base.py:1298-1300`) and `NestedObjects` folds `RestrictedError` into `.protected` (`admin/utils.py:209-212`), so the backstop reasoning about storage and `on_commit` is correct, and `cv_get_atomic()` is `nullcontext` when `cv_atomic` is False, which does not change that (`base.py:244-246`). Resource-backed deletes use `CustomFormView`, not `DeleteView` (`docs/reference/resources.md:282-300`, `examples/bootstrap5/resources/views.py:88-90`), so the always-on collector does not reach non-ORM objects. The test base layout has no other `<form>` (`app/crud_views.html`, `base.html`, `nav.html`: 0), so the "no `<form`" assertions are safe. polib 1.2.0 is installed in `.venv`; `msgfmt` is not on PATH.

**Strengths.**
- Blocked POST goes through the server (`post()`), not a disabled button, satisfying D-12.
- The backstop covers the race and the default configuration; the plan reasons correctly about why storage is intact.
- Two-branch copy confines the change; the labelled msgid and its German translation stay byte-identical.
- The revised pins are enumerated exactly and all three exist where stated (`test_delete.py:246`, `test_guardian_delete.py:315`, `test_authorization_matrix.py:729`; heading constants at `test_delete.py:142`, `test_guardian_delete.py:127`, `test_authorization_templates.py:42`).

**Concerns.**
- **MEDIUM — the always-on `NestedObjects` pass is heavier than T-06.2-17 claims.** The threat register accepts the cost because "Django's own `delete()` runs the same collector". It does not: `NestedObjects.can_fast_delete` returns `False` unconditionally (`admin/utils.py:245-250`) and `related_objects` adds `select_related`, so every cascaded row is loaded into memory on every delete GET and POST, including the default `cv_show_related_objects=False` configuration where nothing is displayed. Django's `Collector` fast-deletes where it can and never materializes those rows. For a root with a large cascade (a Publisher with 100k Books) this turns a cheap confirmation page into a full in-memory walk, twice on POST. Suggest: when `cv_show_related_objects` is False, compute the flag with a plain `django.db.models.deletion.Collector` wrapped in `try/except (ProtectedError, RestrictedError)`, and keep `NestedObjects` only for the preview; or at minimum correct the T-06.2-17 rationale and document the cost on the `cv_show_related_objects` reference page so a project can override `cv_get_related_objects`.
- **MEDIUM — a blocked POST carries no form error, so a copied 0.30 template fails silently.** The plan deliberately adds no non-field error ("the stock template omits the form"). A copied `view_delete.content.html` that still gates the include on `related_summary or protected_objects` and keeps its form gets, on a blocked POST with the default configuration, a 200 that re-renders the same form with no notice and no error. The migration guide will say to update the copy, but the failure mode until then is invisible. Adding the generic sentence as `form.add_error(None, …)` in the blocked branch costs nothing on the stock page (the form is not rendered) and makes stale copies show *something*. Decide explicitly; if rejected, say so in the ledger.
- **LOW — 08-01's `read_first` cites `test_delete.py` lines 165-240 for the preview tests and "60-90" for the custom-protection no-form test; the actual protected-preview block starts at 169 and the file has 29 tests.** Line hints drift; the names are what matter and they are correct.
- **LOW — `.po` byte-identity gate is self-referential.** The acceptance "tracked `django.mo` equals a fresh polib compile" passes trivially after 08-03 compiles with polib. That is fine as a sync check, but Phase 5 recorded the tracked `.mo` as msgfmt-identical; after 08-03 that statement in STATE.md is stale. 08-03's SUMMARY note covers it; also update the Phase 5 decision line or add a deferred item so the next catalog sweep knows which tool produced the file.
- **LOW — German sentence length.** "Andere Objekte verweisen noch auf dieses Objekt; entfernen Sie diese Verweise oder ordnen Sie sie neu zu, bevor Sie es löschen." is correct German but long for an alert body; acceptable.

**Suggestions.**
- Document the per-request collector cost next to `cv_show_related_objects` in `delete_view.md` (09-01 can carry it) and name `cv_get_related_objects` as the override point.
- 08-02's backstop test patches `cv_get_related_objects` to return an empty `RelatedObjects`; also assert the response body contains the generic sentence (not just `has_protected_objects is True` in context), since the patched preview context has no labels and the template branch is the thing under test.

**Risk.** MEDIUM. Correctness is sound; the performance characterization in the threat model is wrong and should be fixed before the always-on collector is frozen into the 1.0 delete-page contract by Phase 7.

---

## 06.2-09

**Summary.** Pending; documentation, handoff and re-measure. Every line reference I checked is accurate: `delete_view.md` sections at 172/189/272, `theme.md` section at 325, `migrating-1.0.md` "Delete previews" at 390 with "Guardian manage page" at 427, CHANGELOG `### Fixed` at 239, ACCEPTANCE rows at 116/155-162/202-231, disposition with 8 findings so "open → 6" after two `fixed` is arithmetically right. All five grep anchors are 0 at HEAD. The re-measure loop is the 06-03 loop verbatim plus ruff on `src tests`.

**Strengths.**
- Breaking/migration pairing is enforced by the strict build's anchor check, not by prose.
- Carries the proxy-model `GuardianQuerysetMixin.get_queryset` / `get_objects_for_user` `MixedContentTypeError` risk forward explicitly (`mixins.py:182-195`, `viewset.py:89-108` still pass the app-qualified string), which is the correct scope boundary.

**Concerns.**
- **MEDIUM — the handoff still omits the other open review findings.** The disposition lists WR-01 and IN-01…IN-05 as `open`; ACCEPTANCE's open-items list names only AUTH-06, A19, A25 and the (soon removed) PROTECT bullet. 09-02 should add one line per remaining open finding (or a pointer to the disposition file) so Phase 7 does not inherit a handoff that reads as "two open items" when six review findings are untriaged. WR-01 (core nested create state against page object) and IN-05 (`GuardianParentPermissionMixin.has_permission` returns True for any child composition) are the ones a stability inventory would want to know about.
- **LOW — guardian.md paragraph should state the global-fallback codename rule** (see 07): "a global `view_<guardian content-type model>` permission", so proxy and polymorphic-base projects know which global grant reveals labels.
- **LOW — 09-01 does not mention the collector-cost documentation** that 08's always-on flag introduces; add a sentence under "Protected objects" or "Configuration".
- **LOW — scoped-edit rule has no mechanical check.** 09-02's `fails_when` says a whole-file rewrite fails the task, but nothing measures it. A `git diff --stat` line-count ceiling on the two planning files in the SUMMARY would make it verifiable.

**Suggestions.**
- 09-03: record the Django 4.2 `test_assets.py:332` skip again so the "same single skip" comparison is explicit, as 06-03 did.
- 09-01: the CHANGELOG Fixed entry says "proxy roots and polymorphic children" could 500; add that the fix also changes which global permission the fallback consults for those (ties to the 07 concern).

**Risk.** LOW. Mechanical and well-anchored; the main gap is handoff completeness.

---

## Cross-plan observations

- **Dependency order is right.** 07 before 08 (Royalty is the RESTRICT surface 08 needs; both touch `test_guardian_delete.py`), 09 after both. No same-wave file overlap among 07/08/09.
- **Scope discipline.** 07–09 stay inside G-06.2-1 and G-06.2-3; no new public configuration is added. The one new theme-facing contract ("`has_protected_objects` on every delete page; stock template omits the form while blocked") is the right shape for Phase 7 to freeze, provided the collector-cost point in 08 is settled first.
- **Evidence rules are consistent.** Red-to-green where a defect is reproduced (07-01, 08-01), passing-after for replaced pins (07-02, 08-02), build/catalog evidence for docs and locale (08-03, 09-01). That matches the A03 discipline from plans 01–06.
- **One thing none of the nine plans does:** run the full `tests/test1` suite between 07 and 09. Given two new test-app models, I would add that to 07's close-out rather than wait for 09-03.

## Overall risk assessment

**MEDIUM, driven by plan 08.** Plans 01–06 did what they said and the residuals were found by UAT and are correctly diagnosed. Plan 07 is a small, well-reasoned fix whose only real gap is documenting the global-fallback codename rule under non-default content types. Plan 08 is correct on security and lifecycle but its threat register misstates the cost of the always-on `NestedObjects` pass; because Phase 7 will freeze the delete-page contract immediately after, that cost should be either bounded (plain `Collector` for the flag when the preview is off) or documented as an override point before execution. Plan 09 is sound; widen its handoff to the remaining open review findings.
