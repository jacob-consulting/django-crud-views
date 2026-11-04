# Cross-AI Plan Review: Phase 06.10 (6 plans)

All six plans were checked against the live checkout at `405c415` on branch `gsd/phase-06.10-…`. I read the URL builders, Guardian mixins, delete adapter, button/card integration, test fixtures, browser runner and server, docs markers and the prior 06.9 gate record. One precondition I could not verify: the cached browser asset directory under `~/.cache` is outside the allowed working directory, so its existence is an open question rather than a finding.

## 06.10-01

**Summary.** The plan correctly targets the real seam. `cv_get_router_and_args` at `src/crud_views/lib/view/base.py:576-609` is the single sibling-URL builder, it reads every parent coordinate from `self.kwargs` (line 600), rejects falsey values (line 601) and mutates the caller's `extra_kwargs` dict in place (line 586). All three defects the plan names are present. The matrix is a faithful expansion of D-01 through D-08, and the choice to classify destinations by the target's `cv_object` through `ViewSet.get_view_class` (`viewset/__init__.py:339-343`) preserves the list-to-card fallback. The weak spots are the rendering consequences of strict mode and an exception-type split the plan does not mention.

**Strengths**
- Metadata reuse is right: `ParentViewSet.get_pk_name()`/`get_attribute()` (`parentviewset.py:56-66`) and the chain walk in `get_parent_url_args` (`viewset/__init__.py:236-252`) are the only declared sources, and the plan refuses to guess relation names.
- The `to_field` guard is necessary. `cv_get_related_object_url` today reads `parent_obj.pk` after loading the relation (`delete.py:203-205`); a raw `attname` shortcut without the `target_field is pk` check would be a regression for the plan's own `NestedUrlChild` fixture, which is declared with a non-PK target.
- The query bounds are internally consistent: Leaf→Child→Parent→Publisher is h=3, and the stated `h-1` for PK targets and `h` for non-PK targets match what descriptor loading costs.
- Test isolation follows a proven pattern: `tests/test1/test_guardian_delete.py:21-29,43-46` already swaps `_REGISTRY` and installs a temporary URLconf with `clear_url_caches()`.

**Concerns**
- **MEDIUM. Strict ValueError now surfaces during ordinary row rendering.** `_cv_get_action_context` computes `cv_url` via `cv_get_link_url` before any access or hide/disable decision (`base.py:761` vs `772`), and `cv_get_link_url` calls strict `cv_get_url` (`base.py:961`). Under D-01 an own-model row with a recognized-unavailable destination (null native relation, unscoped M2M) will raise mid-render instead of hiding the action. Today that cannot happen because page kwargs always exist. The plan pins the helper contract but never states the rendering policy for unavailable object destinations. Plan 02 inherits this silently.
- **MEDIUM. Two exception families for "required object missing".** The view path raises `CrudViewError` via `cv_get_cls_assert_object` (`base.py:555`), while the plan's request-free path raises `ValueError`. Both are "same category" to a caller. D-15 permits ValueError, but the plan should say the view-path behavior is retained unchanged, or cancel code that catches only `NoReverseMatch` (`base.py:899-901`, `919-921`) may see a new exception class.
- **MEDIUM. The M2M fixture gives no "many" case.** `cv_genre` (`tests/test1/app/views.py:454-458`) has `attribute="publishers"`; the "zero/one/many memberships with explicit/page/absent context" matrix is specified but the plan does not name where the many-membership fixture comes from. The SQL-capture assertion (no `genres`/`publishers` manager query) is the right proof, but the fixture must exist first.
- **LOW. Resource `obj.pk` via the per-subclass shim.** `Resource.pk` is a `_PkShim` property (`resource.py:93-95`); reading it is fine, but `type(obj)` checks for "own-model input" must use `isinstance` against `viewset.model`, which the plan's wrong-model rule already implies. Worth a test with a Resource subclass.
- **LOW. "Outside its parent URL context" tracer.** No shipped surface renders a Book action on a non-Book page; `cv_get_context` only targets sibling keys. The honest tracer is `LinkDetailColumn.get_url` (`table/columns.py:49-50`) or a view bound to unrelated kwargs as `test_guardian_delete.py:49-53` does. Pick one explicitly.

**Suggestions**
- Add one sentence to the resolution contract: "A strict failure from `cv_get_link_url` during action rendering propagates; rendering does not convert unavailable object destinations into hidden actions." Then plan 02 can decide whether that is acceptable or whether `_cv_get_action_context` should treat recognized unavailability as inaccessible.
- Make the precedence tests drive both `ViewSet.get_url` and `view.cv_get_url` on the same inputs and assert equality, since the acceptance criterion already demands it.
- Name the many-parent M2M fixture (two Publishers on one Genre) in the Artifacts list.

**Risk Assessment: MEDIUM.** The design is sound and verifiable; the risk is in unstated rendering semantics that the next plan will have to reverse-engineer.

## 06.10-02

**Summary.** The call-site inventory is accurate: URL is computed before access in every shipped location (`base.py:761/772`, `buttons.py:103/114`, `buttons.py:229/242`, `card.py:58/63`, `card.py:77/86`), so publishing the resolution before `cv_has_access` is feasible. The plan's main design choice, a ContextVar carrier keyed by target/user/object with owner-thread and owner-task identity, is the most complex piece of machinery in the phase, and the repository already contains a simpler precedent that solves the same problem.

**Strengths**
- The hook inventory is complete for `cv_get_url_extra_kwargs`: `RedirectChildView` (`views/child.py:27-29`) is the only in-tree override and the plan's "hook runs once, parent values are constraints" rule keeps its `redirect`/`redirect_key` extras intact.
- Polymorphic `create_select.py:100` passes `extra_kwargs`; copying the dict instead of aliasing it (today `base.py:586`) is a real fix.
- `ParentContextButton` and `SiblingContextButton` build URLs with raw `reverse` from page kwargs (`buttons.py:159-169`, `287-288`); the plan correctly leaves their scope intentional rather than routing them through the object resolver.

**Concerns**
- **MEDIUM. Over-engineering: the carrier duplicates an existing adapter pattern.** `_cv_action_enabled_for_rendering(user, obj, rendering_view)` → `_cv_action_enabled_for_context` → public `cv_action_enabled` (`base.py:413-424`) is exactly the "supply rendering context without changing the target's public contract" seam, and Guardian already overrides `_cv_action_enabled_for_context` for nested create (`guardian/lib/views.py:299-307`). A private `_cv_has_access_for_rendering(user, obj, rendering_view, parent_obj=None)` that runs the Guardian parent gate and then calls the public `cv_has_access(user, obj)` once gives every property the plan lists (original obj, single invocation, no class mutation) with no ContextVar, no thread/task identity, no nested-frame semantics and no isolation test matrix. `_cancel_target_available` already receives `rendering_view` (`base.py:73-85`) and delete certification already injects a certified parent through `rendering_view._cv_cancel_parent_object` (`delete.py:368`), so both consumers can pass the parent explicitly.
- **MEDIUM. Two `cv_get_child_url` consumers are not in scope.** `RedirectChildView.get_redirect_url` (`views/child.py:21-24`) and `ChildColumn.render` (`table/columns.py:38-43`) consume the rewritten builder but appear in neither `files_modified`, `read_first` nor `navigation_preservation`. The redirect-child route and the child table column need an explicit preservation assertion.
- **MEDIUM. Rendering policy for strict failures is undefined (carried from 01).** `render_matrix` only covers rows whose destination resolves. A row with a null relation under D-01 raises from `base.py:961` before the carrier is consulted.
- **LOW. The templatetag access path has no URL.** `templatetags/crud_views.py:607` calls `cls.cv_has_access(user, view.object)` directly. That is a legitimate D-09/D-10 fallback path, but the plan should list it so plan 03's "no matching scope" branch is tested against a real caller.

**Suggestions**
- Replace the ContextVar carrier with the explicit private rendering adapter described above. If the carrier is retained, drop the asyncio owner-task check unless an async render path exists in the package; none does today.
- Add `redirect_child` and `ChildColumn` cases to `navigation_preservation`.
- State the strict-failure rendering rule in the plan body.

**Risk Assessment: MEDIUM.** Correct integration points, but the chosen mechanism adds concurrency semantics the package has never needed, and the test burden it creates is the plan's own cost.

## 06.10-03

**Summary.** All four defects are real and the fixes are placed correctly. Core `cv_has_access` turns a missing permission into `has_perms(())`, which is `True` for every user including anonymous (`base.py:1086-1088`). Guardian object access reaches `perm.split(".")` with `None` (`mixins.py:88-97`), the queryset path passes `None` to `get_objects_for_user` (`mixins.py:205-212`), and the parent gate does `parent_perm.split` on a missing key (`mixins.py:360-368`). The policy order is sensible. The serious problem is a cross-plan seam executed in parallel.

**Strengths**
- D-11 is placed before the permissive branches: `cv_guardian_accept_global_perms and user.has_perm(perm)` at `mixins.py:92` and `364` would otherwise still evaluate `has_perm(None)`.
- The post-migrate retry is preserved by design: `default_permissions` deliberately does not cache an empty map (`viewset/__init__.py:452-470`), and the plan forbids a negative cache.
- Create remains special for the right MRO reason: `GuardianCreateViewPermissionRequired.cv_has_access` is defined on the class itself (`guardian/lib/views.py:344`), ahead of the mixin, so new parent composition in `GuardianParentPermissionMixin.cv_has_access` cannot accidentally reach it except through the top-level `super()` call at line 379, which the plan must short-circuit when `parent is None`.

**Concerns**
- **HIGH. `_cv_cancel_target_available` is a shared seam with plan 04, and both run in wave 3.** The object branch at `mixins.py:257-263` checks `_guardian_user_has_parent_perm(user, parent_obj)` on `rendering_view._cv_cancel_parent_object()`. Delete certification relies on exactly that: `delete.py:356-368` certifies the parent on the candidate's alias and then replaces `_cv_cancel_parent_object` with a lambda returning the certified instance. Plan 03 proposes removing the preliminary parent evaluation and binding the parent through the carrier instead. If the new `cv_has_access` resolves the parent from `fetched` via the FK descriptor rather than from the certified instance, the alias/projection guarantees from 06.9-02 are bypassed. Plan 04 acknowledges this only as "record the integration requirement for plan 06", which means wave 3 can finish with the two halves inconsistent. Existing guard-order tests (`test_delete_databases.py::test_protected_guardian_guard_order`) will be the first to notice.
- **MEDIUM. Guardian list access changes semantics for existing no-object callers.** `GuardianQuerysetMixin.cv_has_access` returns `not inactive` (`mixins.py:143-144`) and is called with `obj=None` by `SiblingContextButton` (`buttons.py:301`) and `_cv_cancel_parent_target_access` (`mixins.py:273-274`). Denying on a missing `view` mapping is correct, but the plan should list these callers in `undeclared`.
- **MEDIUM. Core denial applies to superusers and must be documented as intentional.** Today a missing mapping advertises access to everyone; after the change it hides the action even for `is_superuser`. The request side already asserts (`base.py:1066-1069`), so the two agree, but the Breaking/Fixed text in plan 05 has to say so.
- **LOW. Checker-per-call cost.** `ObjectPermissionChecker(user)` is constructed per access call (`mixins.py:71`, `96`, `368`). Linear growth is honest; the plan should not let the "no new cache" rule be read as prohibiting reuse of the already-materialized parent instance within one render.

**Suggestions**
- Serialize: make plan 04 `depends_on: ["06.10-03"]`, or move all `_cv_cancel_target_available` edits into a single wave-4 integration task that owns both `mixins.py` and the certified-parent injection in `delete.py`.
- Whichever carrier/adapter design wins in plan 02, require `test_delete_databases` to assert that the Guardian parent gate during certification evaluates the certified `parent` instance identity, not a freshly loaded FK instance.
- Add a `migration_retry` case that proves a missing mapping on one ViewSet does not suppress a later `migrate`-created permission on a different ViewSet.

**Risk Assessment: HIGH.** The authorization fixes are right, but the plan edits a method that another concurrent plan's correctness depends on, and neither plan owns the combined behavior.

## 06.10-04

**Summary.** The delete integration is tightly scoped and matches the 06.9 contract. Replacing the single-level candidate builder (`delete.py:192-210`, which reads only the immediate `parent_attr` and uses a truthiness test at line 204) with `get_url("detail", obj, strict=False)` is the correct minimal change, and the exact-candidate certification at `delete.py:212-372` stays independent. Query-budget tests from 06.9-02 will need refreshing, not just preserving.

**Strengths**
- Visibility-before-URL is preserved by construction: `cv_filter_related_objects` runs at `delete.py:443` and candidates are built at `446-449` only for `related.protected`.
- Cascade nodes keep the public hook without protected-only certification (`delete.py:452-456`), exactly as the plan states.
- The `except NoReverseMatch: return None` inside the current hook (`delete.py:207-209`) maps cleanly onto `strict=False`, so custom overrides that today depend on `None` keep working.

**Concerns**
- **HIGH (shared with 03).** `_cv_get_protected_object_url` calls `target._cv_cancel_target_available` at `delete.py:369` with the certified-parent lambda installed at line 368. Plan 03 changes that method in parallel. See 06.10-03.
- **MEDIUM. Existing numeric budgets will move.** 06.9-02 pinned core N=1→1, N=4→4, N=8→8 and Guardian N=1→8, N=4→32, N=8→64 around adapter evaluation. The current hook loads `publisher` through the descriptor (`delete.py:203`); an `attname` shortcut for `Contract.publisher_id` removes that load, so measured counts may decrease. The plan says "apply plan 01 ancestry bounds", but should explicitly state that the committed numbers are re-measured and replaced rather than kept as an upper bound.
- **MEDIUM. Multilevel fixture realism.** The only three-level chain in the test app is `cv_booknote_bc → cv_book_bc → cv_publisher_bc` (`tests/test1/app/views.py:1018-1034`), with plain `DetailView` destinations and no permission mixins. A multilevel protected target under Guardian needs a new temporary ViewSet; the plan references plan 01's test-only models, which have no Guardian ViewSets. Name the fixture.
- **LOW. First-match ambiguity.** Multiple ViewSets register `Publisher` in the test app (`cv_publisher`, `cv_publisher_cascade`, `cv_guardian_publisher`, …); `delete.py:196-197` takes registry order. Isolated registry patching, as in `test_guardian_delete.py:21-24`, remains mandatory for every new case.

**Suggestions**
- Add `depends_on: ["06.10-03"]` or extract the shared seam, as above.
- In 04-02, commit the new measured table and the delta explanation in the summary, mirroring the 06.9-02 "Measured Query Budget" section.

**Risk Assessment: MEDIUM** on its own, **HIGH** in combination with plan 03's parallel edit.

## 06.10-05

**Summary.** The documentation plan reuses an executable-recipe pattern that already exists and is consumed by three readers: the Python docs test, `protected_delete_server.py:53-63` and `protected-delete.cjs:23-35`. New `nested-url-recipe` markers in `docs/migrating-1.0.md` are consistent with the existing `protected-delete-recipe` markers at lines 977, 1005 and 1037. The CHANGELOG has an `### Breaking` section under Unreleased (`CHANGELOG.md:3-7`) to extend. Risk is low; the open items are format choices.

**Strengths**
- Executing extracted fences against real ViewSets and a temporary URLconf, rather than text matching, follows `test_delete_migration_docs.py` and gives D-16 a tested migration.
- Separating Fixed entries for the D-11 access corrections from the Breaking routing entry matches D-16's explicit allowance.

**Concerns**
- **MEDIUM. `stability.md` shape.** The current "Public API" section lists class and module names only (`docs/development/stability.md:19-66`); no method-level entries exist. Adding three method signatures there starts a format Phase 7's STAB-01/02 work will restructure. 06.9-03 handled this with a "Phase 7 Public Surface" table in its summary rather than editing stability.md.
- **MEDIUM. Superuser semantics must be in the Fixed text.** See 06.10-03. A user whose superuser dashboard loses actions after upgrade needs to find the explanation.
- **LOW. Migrating recipes touch browser hashes.** `migrating-1.0.md` is in the hashed source set (`protected-delete.cjs:37`); any later edit invalidates plan 06 evidence. Fine as long as plan 06 runs last, which it does.
- **LOW. Site dir name.** `--site-dir /tmp/cv-069-docs` reuses the 06.9 path. Cosmetic.

**Suggestions**
- Put the exact helper inventory in the plan 05 summary and in a clearly marked "Phase 06.10 handoff" subsection of `stability.md`, leaving the existing Public API list untouched.
- Have `reference_examples` include one `strict=False` example whose destination is unavailable and one wrong-model example that raises, so the docs prove D-14 rather than describe it.

**Risk Assessment: LOW.**

## 06.10-06

**Summary.** The browser plan extends an existing, strictly validated runner. The current runner hard-codes a protected-delete schema: `options()` accepts only `smoke|all` (`protected-delete.cjs:20`), `requiredCases` enumerates the protected matrix (line 12), and `validateEvidence` asserts protected-only DOM keys for every case (line 48) and HTTP 200 for every navigation (line 53). The plan recognizes that nested cases need their own schema branch. The sequencing of evidence and gates within the plan is the main risk.

**Strengths**
- Reusing the owned server with request-scoped patches (`protected_delete_server.py:93-136`) and the LF/UTF-8 recipe extraction keeps evidence tied to exact source bytes.
- The inherited Django 6.0 floor command with its single deselection is quoted exactly as recorded (`06.9-ACCEPTANCE.md:116`), and `CV_FRAGMENT_PYTHON` for integration matches line 119.
- Refusing to relabel 06.9 observations is enforced by `validateEvidence` line 69, which compares all hashed sources.

**Concerns**
- **MEDIUM. Evidence/gates ordering within the plan.** Task 06-02 writes the browser JSON with source hashes; task 06-03 then runs the full suites and "routes unresolved failures to owning tasks". Any source fix after 06-02 makes the committed JSON fail its own `sourceHashes` check on revalidation. The plan says "persist fresh evidence only after source stabilizes" but the task order does the opposite.
- **MEDIUM. D-09's documented 403 cannot be expressed in the validator.** Navigation cases must return 200 (`protected-delete.cjs:53`). Either add a case kind that expects a 403 after an unresolved-parent link, or state that the D-09 limit is verified only in Python request tests.
- **MEDIUM. Guardian fixtures in the server.** The server only wires core Contract/Publisher views and a single actor with model permissions (`protected_delete_server.py:193-200`). Opposite-parent grants need object-permission setup and Guardian routes in the server-local URLconf; the plan lists this but should name the Guardian ViewSets it will register.
- **LOW. Browser runtime is an assumption.** The Playwright/Chromium/assets locations are discovered at run time (`protected-delete.cjs:122-128`); I could not inspect `~/.cache`. The plan's preflight handles it.
- **LOW. Only Python 3.12 environments exist.** `.nox/` holds four 3.12 environments; the plan is right to declare 3.13–3.15 unverified.

**Suggestions**
- Reorder: run 06-03's Python/JS/docs/Ruff gates first, fix, then capture the browser matrix, then re-run only the cheap gates. Or add an explicit "if any source changed after 06-02, rerun 06-02" step with a hash check.
- Add a nested case kind with `expectedStatus` so a 403 after an unresolved-parent Guardian link can be recorded as a passing observation of the documented limit.

**Risk Assessment: MEDIUM.**

## Cross-plan assessment

**Ordering.** The one structural defect is wave 3: plans 03 and 04 both touch the `_cv_cancel_target_available` ↔ `_cv_get_protected_object_url` seam (`mixins.py:247-269`, `delete.py:356-369`) while declared parallel. Serialize them or move the seam into one owner.

**Complexity.** The ContextVar carrier in plan 02 is the only piece I would push back on as over-engineering. The package already has the `_cv_action_enabled_for_rendering` adapter pattern (`base.py:413-424`) for precisely this need. A `_cv_has_access_for_rendering` sibling would remove the thread/task isolation tests and the nested-frame semantics entirely.

**Security.** The D-11 fixes close a genuine advertise-without-permission gap (`base.py:1087`, `mixins.py:97`) and the plans keep request authority untouched. The one thing to watch is that the Guardian parent gate during delete certification continues to evaluate the certified instance, as noted above.

**Goal achievement.** With the two changes above, the plans deliver the phase: shared resolver, request-free URLs, view integration, access parity with explicit D-09/D-10 limits, multilevel delete candidates, executable migration and fresh browser evidence. Requirement mapping is complete and the shared-ID gate prevents premature completion marks.

**Overall risk: MEDIUM**, driven by the wave-3 seam and the carrier design, both fixable before execution starts.
