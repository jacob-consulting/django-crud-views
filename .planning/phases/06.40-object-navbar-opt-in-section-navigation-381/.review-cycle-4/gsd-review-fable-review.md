Source checks are complete; writing the review now. Nothing further to fetch.

# Cross-AI Plan Review — Phase 06.40, cycle 4/6

Read-only review against the working tree at `eecc8111`. All `file:line` references were read in this session. Planned new artifacts (navbar.py, tests, example app, companion checkout) do not exist yet and are judged as plan readiness only.

## 06.40-01

**Summary.** Plan 01 is the load-bearing plan: declarations, exact-key routing, startup checks, and the R20 remediation. The R20 mechanism is grounded in real source and is sound at planning level. One concrete isolation gap remains in the new R20 regression's test design; it is small and local to Task 03.

**Strengths.**
- The hazard R20 named is real and the proposed ordering fixes it. `check_viewsets` (`src/crud_views/checks.py:38-47`) consumes `ViewSet.checks_all()`, which snapshots `_REGISTRY` but then calls `cv.checks()`, whose final loop iterates `self._views.values()` live (`src/crud_views/lib/viewset/__init__.py:286-287`). Calling `_url_configuration_loaded()` first (`checks.py:172-195`) completes every import before any live dict iteration. `check_ancestor_declarations` already uses exactly this order (`checks.py:209-212`), so the change is a one-line mirror of an existing pattern, not new machinery.
- The `load=False` presence probe is correct against the installed Django. `URLResolver.url_patterns` is a `cached_property` (`.nox/tests-3-12-django-5-2/.../django/urls/resolvers.py:714`) and `cached_property.__get__` writes `instance.__dict__[name]` only after `self.func(instance)` returns (`django/utils/functional.py:47-48`). A failed or in-progress import therefore leaves no cache entry, while a valid empty pattern list does. Reading `resolver.__dict__.get("url_patterns")` performs no import.
- Literal-key guarding is necessary and correctly located: both `get_view_class` (`viewset/__init__.py:375-379`) and `get_router_name` (`:381-387`) silently substitute `card` for a missing `list`.
- Owner/child route-kwarg naming matches source: `ParentViewSet.get_pk_name()` returns `pk_name or f"{viewset.name}_pk"` (`parentviewset.py:56-60`); `_resolved_ancestor` walks `_walk_ancestors` zipped with `state.objects` (`ancestors.py:576-585`), so no new object fetch is needed.
- R1 normalization is correctly scoped: `render_snippet` already `strip()`s and `mark_safe`s (`base.py:592`), so one `html.unescape` plus SafeData removal is the right boundary.
- Check-ID allocation: current allocated IDs are E002–E003, E100–E111, E200–E268, W246, W270, W280, W290–W292. The plan's "search then allocate" instruction is correct; E269 is used by `checks.py` but not via the `Check` class, so the executor must grep both `Check(... id=...)` and `Error(... id="viewset.E...")` forms.

**Concerns.**
- **MEDIUM — R20 regression test isolation does not cover per-ViewSet `_views` mutation.** Task 03 tells the executor to "pre-register one participating view on an existing ViewSet, then let URLconf import register multiple invalid configured views on that same ViewSet" and to restore state "using Task01's isolation ordering." That ordering is `isolated_routes` (`tests/test1/test_ancestor_authorization.py:46-76`), which snapshots and restores only `_REGISTRY` (the dict of ViewSets) plus `_VOCAB_CACHE`, URL caches and ContentType cache. It never snapshots any ViewSet's `_views` dict. If "existing ViewSet" is read as a project ViewSet from `tests.test1.app`, the late test views remain registered after the test and leak into every later test in that xdist worker. The same gap bites the required failed-then-complete case: `register_view_class` raises on a duplicate key (`viewset/__init__.py:352-354`), and a failed module import is evicted from `sys.modules`, so a second import re-executes the class bodies and fails with "already registered" unless `_views` was rolled back between attempts.
  *Plan change needed:* Task 03 must state that the "existing" ViewSet is test-owned (created inside the isolated fixture before the cold import), or must add explicit per-ViewSet `_views` snapshot/restore for any touched ViewSet, and must note the duplicate-key constraint for the failed-then-complete sequence.
- **LOW — preflight behavior change for direct callers.** Adding the preflight to `check_viewsets` means existing direct callers now import `ROOT_URLCONF`. The existing ones are benign (`tests/test1/test_permission_declarations.py:435-438` already calls `check_ancestor_declarations()` first, which does the same import; `test_context_button_check.py:146` calls `checks_all()` directly and is unaffected). The plan should still name "existing direct `check_viewsets()`/`checks_all()` callers keep passing" in Task 03's acceptance, since it owns `checks.py`.

**Suggestions.**
- In the `load=False` docstring, record why `get_resolver()` itself is safe to call: it is `lru_cache`d construction and performs no import.
- Make the "in-progress" case executable by having the temporary URLconf module call `check_viewsets()` during its own import; with the root `url_patterns` unset, `iter(module)` raises `ImproperlyConfigured`, which the existing `except Exception` turns into `False`.

**Risk:** MEDIUM, driven only by the isolation point above. Everything else is source-verified.

## 06.40-02

**Summary.** The template/lazy-result plan is consistent with the data contract from Plan 01 and with the UI-SPEC context shape. Dependencies are real: German catalog present, polib in the test environment (per prior session observation 29173; not re-executed here because the interpreter call needed approval).

**Strengths.**
- The context-taking tag is required: the breadcrumb tag is a fixed `inclusion_tag` bound at import time (`templatetags/crud_views.py:446-449`) and cannot select `NavBar(template=...)`.
- Modal predicate is exactly `request.headers.get("X-CV-Modal") == "true"` (`base.py:71-73`).
- `src/crud_views/locale/de/LC_MESSAGES/django.po` and `django.mo` exist and the msgid `Sections for %(object)s` is absent (grep count 0), so the owned addition is correct and non-duplicating.
- Choosing `aria-current="true"` over `page` is justified: Orders is active on Item pages, which are not that page.

**Concerns.**
- **LOW — `text-break` as initial wrapping choice.** Bootstrap's `text-break` sets `word-wrap/word-break: break-word`, which handles most unbroken tokens but is weaker than `overflow-wrap: anywhere` in flex children with `min-width: auto`. The plan already routes the proof to Plan 08's live reflow and reserves a scoped asset fallback. No plan change needed; this is a covered execution check.

**Suggestions.**
- Pin in Task 01's tests that the mixin's sentinel attribute is set on the view instance, not the class, so two requests served by two instances cannot share a wrapper.

**Risk:** LOW.

## 06.40-03

**Summary.** Permission/state/cost plan reuses real helpers and the existing cost harness. The cache-reset list matches source names.

**Strengths.**
- Hook signatures and order are exact: `_cv_child_link_has_access` (`base.py:528-541`) includes own access, immediate-parent policy, and the protected-actor rule; `_cv_action_enabled_for_rendering` (`base.py:564-566`) is the state adapter. Calling the child hook once and then the state adapter once implements D-09 without reconstructing policy.
- Cold-reset names exist: `reset_discovery` (`test_guardian_child_link_visibility.py:1052-1059`) calls `guardian.shortcuts.clear_ct_cache()` and clears `_default_permissions`; `_VOCAB_CACHE` lives at `src/crud_views/lib/check.py:341`; `_default_permissions` is a `PrivateAttr` (`viewset/__init__.py:109`). `sql_categories` and `rendered_data` exist (`:1027`, `:137`).

**Concerns.**
- **LOW — AC3's "state-denied owner detail GET returns 403" depends on composition.** A plain `DetailView` with a denying `cv_action_enabled` does not necessarily enforce state on request; the research already requires a permission-required composition. Task 01 says "owner detail state denial with actual GET 403" without repeating that constraint. Add the word "permission-required" to the fixture description so an executor does not file a false failure.

**Suggestions.**
- COST.md should list the Django/Guardian versions of the measuring interpreter, since Guardian query counts differ across releases.

**Risk:** LOW.

## 06.40-04

**Summary.** Independent example app foundation. Source-checked compositions are available and the Nox session naming matches the existing cache directory convention.

**Strengths.**
- `AncestorPolicy(provider=..., accept_global_perms=...)` fields exist (`src/crud_views/lib/ancestor_policy.py:46-57`) and the cited Guardian composition is real (`examples/bootstrap5/guardian_demo/views.py:21-28`).
- `ParentViewSet(name=..., attribute=...)` is a declared field (`parentviewset.py:14-15`), so the R2 explicit FK mapping is expressible.
- Example `pytest.ini` discovers `tests.py` (`examples/bootstrap5/pytest.ini:5`); the `examples` Nox session installs `.[all,test,examples]` and runs from `examples/bootstrap5` with posargs (`noxfile.py`, `examples` session), so `-- -n 4 -q navbar_demo/tests.py` is a valid invocation.

**Concerns.**
- **LOW — `.nox/examples-3-12-django-5-2` does not exist yet.** Only `tests-*`, `crispy_floor-*`, `manage_report_floor`, `package` directories are present. Task 02 correctly orders the Nox provisioning run before the `makemigrations --check` command; this is a covered prerequisite, not a gap.

**Suggestions.**
- Task 01 uses a "test-local URLconf built from these ViewSets" while Task 02 switches to project URLs. State that Task 02 removes or converts Task 01's local URLconf so two routing paths are not maintained.

**Risk:** LOW.

## 06.40-05

**Summary.** Completes the hierarchy, seeds, landing and placement. Shared-test ownership claims check out.

**Strengths.**
- `FeatureGroupsTest.test_grouping_matches_spec` exists with a literal ordered `ui` list (`examples/bootstrap5/project/tests.py:457-470`) and `DocRefsPanelTest` is the class the Task 03 `-k` exclusion names (`:386`). No other test in `project/tests.py` iterates `feature.docs` for every feature outside that class (`:193`, `:303`, `:383` are app-specific).
- The shared credential notices are static: `DEMO_USERS` is referenced only in `project/seeding.py`, and `test_i18n.py:185-199` asserts exactly alice, bob, developer with developer last. The plan's decision to add Charlie to `DEMO_USERS` but not to the shared notices is therefore consistent with the unchanged tests.
- The seed command's printed line (`project/management/commands/seed.py:17`) is the only place to update for Charlie; no test asserts that string.

**Concerns.**
- **LOW — `test_every_feature_declares_doc_refs` (`test_doc_links.py:106-108`) will fail between Plan 05 and Plan 06.** Plan 05's commands never run `test_doc_links.py`, and Plan 06 Task 03 runs it after the DocRef exists, so the gap is intentional and bounded. Record it in Plan 05's summary as a known red test for the wave, so a wave-3/4 full example run is not misread.

**Suggestions.**
- None beyond the above.

**Risk:** LOW.

## 06.40-06

**Summary.** Documentation, stability inventory, reciprocal links. Structure claims verified.

**Strengths.**
- `mkdocs.yml` has `nav` commented out and uses `awesome-pages` (`mkdocs.yml:3-8`), so the "no speculative nav edit" statement is correct.
- `docs/reference/templates.md` has a level-two `## Snippet variables` heading at line 161 followed by `## Validation` at 210; the R5 instruction to insert a separate level-two heading before it is executable and leaves the existing section intact.
- `docs/development/stability.md` has the expected `## Public API` / `### crud_views (core)` structure (`:19-21`) for the D-16 inventory.
- The reciprocal-link test computes `DEMO_BASE + reverse(feature.url_name)` and requires it on every DocRef page (`test_doc_links.py:127-146`), matching the plan's "limit DocRefs to pages with Try it live boxes."

**Concerns.**
- None new.

**Suggestions.**
- Task 02's `test_navbar_docs.py` should import the inventory names from the stability doc itself (regex over the bullet list) and `import_string` each one, so the inventory cannot drift from the module.

**Risk:** LOW.

## 06.40-07

**Summary.** Companion delivery. The checkout path is absent, as the plan expects.

**Strengths.**
- `/home/alex/projects/alex/skills-navbar-06-40` does not exist, consistent with "checkout is acquired by Task 01." The plan verifies remote identity, tracked targets and local instructions before editing, and separates local commit from publication.

**Concerns.**
- **LOW (open question).** I cannot verify `scripts/validate.py` or the four target paths without the checkout; the ledger records a blob SHA from planning. Keep "missing checkout leaves delivery unmet" as the governing rule, which the plan already states.

**Suggestions.**
- None.

**Risk:** LOW.

## 06.40-08

**Summary.** Browser evidence and final matrix. Commands match the noxfile.

**Strengths.**
- `tests` session appends posargs after its own `-n auto`, so trailing `-n 4` wins; `manage_report_floor` requires `CV_MANAGE_SCHEMA_EXPORT_DIR` and appends posargs after the fixed test list (`noxfile.py`, both sessions). The Django 4.2 × Python 3.14/3.15 skips are declared in both `tests` and `examples`.
- R12 cleanup ownership is explicit and includes a deliberate failure run.

**Concerns.**
- **LOW — browser tool availability.** No Playwright tool namespace is present in this review runtime. The executing runtime may differ; the plan already keeps AC8 unmet if the browser cannot run. No plan change.

**Suggestions.**
- Record in ACCEPTANCE.md whether uv actually provided Python 3.13/3.14, as the plan already requires.

**Risk:** LOW.

## Cross-plan assessment

**Dependency ordering** is sound: 01 → 02 → {03, 04} → 05 → 06 → {07, 08}, with no shared files inside a wave. **Scope** stays within D-13: one module, one tag, three templates, `checks.py` touched only for the preflight and the keyword-only probe. **Security** boundaries are preserved: visibility never substitutes for request authorization, and every plan tests real destination responses. **Performance**: the preflight adds a URLconf import to `check_viewsets`, which `check_ancestor_declarations` already performs in the same check run, so no net new startup cost.

**R20 verdict:** Closed at planning level, with one retained MEDIUM sub-item. The mechanism (preflight before `checks_all`, import-free `load=False` probe) is verified against `checks.py:38-47`, `viewset/__init__.py:225-232,286-287`, and the installed Django `cached_property` semantics. The sole remaining plan change is the Task 03 isolation sentence above: the "existing ViewSet" in the cold-import regression must be test-owned or its `_views` must be snapshotted and restored, because `isolated_routes` restores only `_REGISTRY` and `register_view_class` rejects re-registration. This does not reopen the mechanism; it hardens the regression that proves it.

**R1–R19:** remain closed. Nothing read in this cycle contradicts the prior dispositions; the ledger entries point at tasks that own executable checks.

**Overall risk:** LOW-to-MEDIUM. The plans achieve the phase goal. Apply the one Plan 01 Task 03 isolation sentence, then proceed to execution.
