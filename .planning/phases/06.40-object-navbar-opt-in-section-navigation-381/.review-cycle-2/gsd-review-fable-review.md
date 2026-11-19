Review complete. Verification was done against HEAD `0ed46a40` by reading the cited source; no tests were run and nothing was edited. Four probes were refused by the sandbox approval layer and are reported as open, not as findings: importing `polib` from the cached nox env, `nox -l`, `uv python list`, and listing the sibling companion path.

# Cross-AI Plan Review, Phase 06.40, cycle 2

## 06.40-01

**Summary.** The traced path, destination resolution and startup checks are grounded in current source. All eight R-items this plan owns (R1, R7, R8, R9, R10, R11, R13, R14) now name a concrete mechanism that exists in the checkout. Two small clarifications remain actionable.

**Strengths.**
- R1 mechanism matches source. `render_snippet` wraps the rendered snippet in `mark_safe` (`src/crud_views/lib/view/base.py:592`) and the stock short-label snippets are plain `blocktranslate` text (`src/crud_views/templates/crud_views/snippets/action_short/detail.html:3`). One `html.unescape` pass plus `str.__str__` reconversion is the right boundary for that output. Raw captions are never decoded. This closes R1.
- R7 is feasible as written. `cv_get_extends_template` honours `cv_extends_template` first (`base.py:427-428`), the core test base has no navbar tag (`tests/test1/app/templates/app/crud_views.html`), and the test settings use a single engine with `APP_DIRS` (`tests/test1/conftest.py:83-96`), so a test-local loader override is a standard `override_settings`.
- R8 reuses a real barrier. `_url_configuration_loaded` exists, remembers nothing between calls and returns False on failed or in-progress import (`src/crud_views/checks.py:172-195`).
- R9 reuses the proven fixture. `isolated_routes` preimports `tests.test1.project.urls` at module level (`tests/test1/test_ancestor_authorization.py:38`), snapshots `check_module._VOCAB_CACHE` (`:54`, defined at `src/crud_views/lib/check.py:341`), and `_default_permissions` is a per-ViewSet private attribute (`src/crud_views/lib/viewset/__init__.py:109`).
- R14's capability rule is correct: `cv_object = False` is set by list, card, create, manage, form and polymorphic create-select views, not only list and create.
- Literal-key guard is necessary: both `get_view_class` and `get_router_name` rewrite a missing `list` to `card` (`viewset/__init__.py:376-386`).

**Concerns.**
- **MEDIUM. The ViewContext for default owner labels is unspecified.** `cv_get_action_short_label(context)` calls `cls.cv_viewset.get_meta(context)` (`base.py:638-643`), and `get_meta` merges `context.to_dict()`, which is only `{"object": context.object}` (`viewset/__init__.py:539`, `src/crud_views/lib/view/context.py:44-45`). Task 01 says to normalize that label but never says which object the context carries. If the executor passes the rendering view's own context, an owner label template that mentions `{{ object }}` shows the Item on an Item page and the Customer on a Customer page, which contradicts the "same owner at every depth" acceptance. Specify `ViewContext(view=rendering_view, object=owner)` for owner items and test a `cv_action_short_label_template_code` that references `object`.
- **LOW. Attribute name slip.** Task 02 says "for owner links use owner.pk_name". The attribute lives on the ViewSet (`viewset/__init__.py:79`), not the model instance. Write `owner_viewset.pk_name`.
- **LOW. Active-section index rule is implied, not stated.** `_walk_ancestors` yields `(edge, ancestor)` nearest-first (`src/crud_views/lib/ancestors.py:89-121`). The active section is the ViewSet one step below the owner: the rendering ViewSet when its first ancestor is the owner, otherwise `chain[i-1][1]` where `chain[i][1]` is the owner. Stating this prevents an executor from selecting `ancestor.name`, which would highlight the owner.
- **LOW. Reuse `CheckTemplate` instead of re-implementing it.** R10's described logic is exactly `CheckTemplate.messages` (`src/crud_views/lib/check.py:245-252`), and `Check.context` accepts any object (`check.py:30`), so `CheckTemplate(context=bar, attribute="template", id=...)` works on the NavBar instance.

**Suggestions.** Add the owner-bound ViewContext to task 01's action and test matrix. Fix the `pk_name` wording. Add one sentence giving the chain index rule for the active child.

**Risk Assessment: LOW to MEDIUM.** The one real gap is the label context; everything else is wording.

## 06.40-02

**Summary.** The lazy contract, leaf split and German landmark are consistent with the source. R15 is now fully owned. The remaining gap is an explicit all-hidden assertion that UI-SPEC requires but no task states.

**Strengths.**
- Per-bar template selection needs a context-taking tag because the breadcrumb tag is a fixed inclusion tag (`src/crud_views/templatetags/crud_views.py:446-449`). `theme_path` is the constant `"crud_views"` (`src/crud_views/lib/settings.py:322-324`), so loader precedence is the real global seam.
- Empty-icon suppression is real: `render_icon` returns an empty SafeString for an unresolvable value (`src/crud_views/lib/icons.py:239-242`) and `Icon.NONE` is `""` (`icons.py:15-19`).
- R15 closes correctly. The core German catalog has 333 msgids and no `Sections for` entry; `django.mo` is tracked (`git ls-files src/crud_views/locale`); `polib` is in the `test` extra (`pyproject.toml:81`). The verify command includes `tests/test1/test_i18n.py`, whose `test_no_empty_or_fuzzy_msgstr` and `test_mo_files_load` (`tests/test1/test_i18n.py:65-81`) will fail on an untranslated or uncompiled entry. The literal German assertion blocks the English-fallback hole.
- The percent-interpolation concern stays rejected: a `blocktranslate with object=...` yields msgid `Sections for %(object)s` and interpolates once.

**Concerns.**
- **MEDIUM. All-hidden admission count has no owning assertion.** UI-SPEC's scenario table requires "all-hidden case performs admission once", and the VALIDATION UI map assigns identity/empty to tasks 02-01 and 02-02. Task 01 pins "exact empty string when zero items visible" but never pins build count 1 and hook count N for that case; task 02 of plan 03 lists omitted-consumer, modal and no-mixin controls but not all-hidden. Without the count assertion, a builder that short-circuits before admission would pass. Add "all-hidden: builder once, each item hook once, zero state calls, empty output" to plan 02 task 01 or plan 03 task 02.
- **LOW. Keep the items landmark out of the example's navbar slicer.** `navbar_html` in `examples/bootstrap5/project/tests.py:499-503` finds the site navbar with `body.index('<nav class="navbar')`. The planned `nav nav-pills` classes do not match that prefix, but the plan should state that the items partial never emits `<nav class="navbar…` so a later restyle cannot break `NavGroupsTest`.

**Suggestions.** Add the all-hidden count case. Add one sentence forbidding the `navbar` class prefix on the landmark.

**Risk Assessment: LOW to MEDIUM.**

## 06.40-03

**Summary.** Admission order and cost measurement target the right seams, and R7/R9 are now concrete. One cold-cache detail is missing relative to the helper the plan says it mirrors.

**Strengths.**
- Hook signatures match `base.py:524-566`; Guardian create's child hook delegates to its parent-aware `cv_has_access` (`src/crud_views_guardian/lib/views.py:387-390`), so calling it once is correct and a second parent check would be wrong.
- `_immediate_parent_access` raises `ImproperlyConfigured` for missing keys, missing requirements and off-default auth records (`ancestors.py:654-690`), matching the propagation requirement.
- The guard resolves every structural ancestor and stores them regardless of which gates are selected (`ancestors.py:498-566`), so `_resolved_ancestor` on a deep page costs no query. `CreateView._cv_action_enabled_for_rendering` reuses that state and only falls back to a lookup outside a guarded request (`src/crud_views/lib/views/create.py:66-72`). The plan's decision to measure on dispatched requests is therefore necessary, not optional.

**Concerns.**
- **LOW. Cold-cache definition omits Guardian's content-type cache.** The helper the plan mirrors clears `guardian.shortcuts.clear_ct_cache()` as well as `ContentType.objects.clear_cache()` and `_default_permissions` (`tests/test1/test_guardian_child_link_visibility.py:1052-1059`). Task 02 names the latter two plus "any exercised Guardian checker cache"; name `clear_ct_cache` explicitly so Guardian cells are reproducible.
- **LOW. COST.md is a planning artifact.** Plan 06 quotes it into prose, which is correct; make sure the reference never links to the `.planning/` path.

**Suggestions.** Add `clear_ct_cache()` to the cold definition list.

**Risk Assessment: LOW.**

## 06.40-04

**Summary.** The Tenant/Customer slice is consistent with the authorization engine and both R2 and R16 are closed by concrete text and commands.

**Strengths.**
- R2 is necessary and now explicit: `ParentViewSet.get_attribute` defaults to the parent ViewSet name (`src/crud_views/lib/viewset/parentviewset.py:62-66`), so `attribute="tenant"` is required with a `navbar_tenant` ViewSet name.
- R16 is executable: `examples/bootstrap5/manage.py` exists and the drift command is in the verify block with its own exit status.
- The examples nox session installs `.[all,test,examples]` and runs pytest with posargs from `examples/bootstrap5` (`noxfile.py:202-213`); `pytest-xdist` is in the `test` extra (`pyproject.toml:77`), so `-n 4` is valid.
- Deferring `FEATURES` registration is right: the seed command imports `{app}.seed` for every feature (`examples/bootstrap5/project/management/commands/seed.py:18-19`).
- `AncestorPolicy(provider="guardian", accept_global_perms=False)` and `cascade=None` inheriting `DEFAULT_CASCADE = True` are real fields (`src/crud_views/lib/ancestor_policy.py:19-22,50-60`).

**Concerns.**
- **LOW. The Notes view inherits the "Detail" short label.** `DetailView.cv_action_short_label_template` is `action_short/detail.html` (`src/crud_views/lib/views/detail.py:17`). Plan 05 overrides the navbar label, but context buttons and the manage page also read the view's own label. Set `cv_action_short_label_template_code` and `cv_action_label_template_code` on the Notes view so every consumer says "Notes".
- **LOW. Environment ordering.** `.nox/` currently holds only `tests-*`, `crispy_floor-*`, `manage_report_floor` and `package`; the first examples run provisions the env. Task 02 already orders provisioning before `makemigrations`; keep that literal.

**Suggestions.** Add the Notes label templates to task 01.

**Risk Assessment: LOW to MEDIUM** (environment provisioning only).

## 06.40-05

**Summary.** R2, R3, R4 and R6 are all addressed with the right files and contracts. I re-checked the shared tests that previously broke a naive edit, and the chosen path survives them.

**Strengths.**
- R3: `FeatureGroupsTest.test_grouping_matches_spec` asserts the exact ordered `ui` list (`examples/bootstrap5/project/tests.py:457-477`); `feature_groups()` buckets in `FEATURES` order (`features.py:741-751`) and `theming` is the last entry, so appending `navbar_demo` yields the plan's expected order. The plan owns the test file.
- R4: the landing contracts are real (`project/tests.py:75-81,238-247,278-284,394-403`), `project.views.BreadcrumbMixin` exists (`project/views.py:7`), and the theming composition the plan copies is at `theming/views.py:21-34` and `theming/templates/theming/index.html`. `_feature_for` keys on the view module's top package (`project/templatetags/example_tags.py:72-77`), so defining the landing view in `navbar_demo/views.py` is required and planned.
- R6: the shared notices are hard-coded (`registration/login.html:15-17`, `project/base.html:52-53`, `project/home.html:42-45`). `test_demo_account_notices_include_developer` requires developer last (`examples/bootstrap5/test_i18n.py:185-199`) and `test_published_demo_credentials_match_seed_output` only iterates alice, bob and developer (`:201-215`). Adding Charlie to `DEMO_USERS` and the printed seed line breaks neither; keeping the shared notices unchanged is the safe path the plan chose.
- Excluding `DocRefsPanelTest` in this wave is correct, and `test_every_feature_declares_doc_refs` (`examples/bootstrap5/test_doc_links.py:105-107`) is not in this plan's command.

**Concerns.**
- **LOW. `SystemChecksTest` runs in task 03's command.** It loads every ViewSet; the example's navbar checks and the `cv_object` attachment rule must be clean for the example views, including that Customer list/create never carry the mixin. The plan says this; just note that the shared suite, not only `navbar_demo/tests.py`, is the gate for it.
- **LOW. Charlie in docs.** `docs/getting_started/demo.md:6` lists the three current accounts and is owned by plan 06 task 03, so the handoff is complete; no change needed here.

**Suggestions.** None beyond keeping task 03's command as written.

**Risk Assessment: LOW to MEDIUM.** The HIGH items from cycle 1 are closed.

## 06.40-06

**Summary.** Documentation and stability work matches the repository tooling. R5 is closed by the heading placement; one prose detail in `templates.md` needs updating.

**Strengths.**
- R5: `_section` splits on the next `\n## ` and requires exactly one occurrence of `## Snippet variables` (`tests/test1/test_snippet_docs.py:27-36`). A new level-two section placed before it is safe, and the verify command includes `test_snippet_docs.py`.
- Reciprocal links are computed as `DEMO_BASE + reverse(feature.url_name)` (`examples/bootstrap5/test_doc_links.py:127-147`), consistent with the `/object-navbar/` include and a `""` landing route.
- MkDocs nav is commented out (`mkdocs.yml:3-5`), so no nav edit is needed. The reference index has an "Actions & navigation" list to extend (`docs/reference/index.md:28-35`).

**Concerns.**
- **LOW. "All four" prose.** The base-template table lists four tags and the next sentence says "All four `{% load crud_views %}` and render nothing when they have nothing to show" (`docs/reference/templates.md:16-25`). Adding the `{% cv_navbar %}` row requires changing that count.
- **LOW. Context-name ambiguity for readers.** `cv_navbar` is both the class attribute holding the declaration and the template context value holding built data. In a page template `{{ view.cv_navbar }}` is the declaration and `{{ cv_navbar }}` is the data. Both names are locked by D-03 and A-02; the reference should say this in one sentence.

**Suggestions.** Update the count sentence; add the two-meanings note.

**Risk Assessment: LOW.**

## 06.40-07

**Summary.** Scope and provenance checks are appropriate. The checkout path is outside this reviewer's sandbox, so its presence is an open question, not a finding; the plan already treats a missing or wrong checkout as an unmet gate.

**Strengths.**
- Remote identity, `git ls-files` on the four targets and a separate scoped commit give a reproducible receipt. `docs/development/index.md:87-91` confirms the external repository.

**Concerns.**
- **LOW.** `git show --check` only checks whitespace in the commit; the content comparison in task 02 is the real review step. Already understood by the plan.

**Suggestions.** None.

**Risk Assessment: LOW on content; environment-dependent on acquisition.**

## 06.40-08

**Summary.** Commands match the nox sessions, and R12 adds the cleanup lifecycle. Residual risk is environmental and the plan reports it honestly.

**Strengths.**
- `tests` session passes posargs after `-n auto` (`noxfile.py:36-46`), so a trailing `-n 4` is the effective value. `manage_report_floor` appends posargs after its fixed list and pins Pydantic 2.2.1 (`noxfile.py:88-107`). `package` runs on Python 3.13 (`noxfile.py:216-217`).
- `.pytest_cache` already exists and contains pytest's own `.gitignore`, so the transient settings file cannot be committed; R12's cleanup removes it anyway.
- Declared skips for Django 4.2 on Python 3.14/3.15 are separated from passes (`noxfile.py:23-25,205-207`).
- `crispy_floor` runs the `format_html` audit over `src/` (`noxfile.py:170-186`); any `format_html` call in `navbar.py` must pass arguments. Already in the plan's gate.

**Concerns.**
- **LOW (open).** Browser tool availability, Python 3.13/3.14 runtimes and the companion checkout could not be probed from this sandbox. The plan's fail-closed wording covers all three.

**Suggestions.** None.

**Risk Assessment: MEDIUM**, driven by environment availability outside the plan's control.

## Cross-plan assessment

**R1–R16 disposition check.** Every ledger entry names a mechanism that exists at HEAD and is used correctly:

| Item | Verified against |
|---|---|
| R1 | `base.py:592,638-643`; plain-text snippets |
| R2 | `parentviewset.py:62-66` |
| R3 | `project/tests.py:457-477`; `features.py:741-751` |
| R4 | `project/tests.py:75-81,238-247,278-284,394-403`; `theming/views.py:21-34` |
| R5 | `test_snippet_docs.py:27-36` |
| R6 | templates `login.html:15-17`, `base.html:52-53`, `home.html:42-45`; `test_i18n.py:185-215` |
| R7 | `base.py:427-428`; `conftest.py:83-96`; test base template |
| R8 | `checks.py:172-195` |
| R9 | `test_ancestor_authorization.py:38,46-76`; `check.py:341`; `viewset/__init__.py:109` |
| R10 | `check.py:232-253` |
| R11, R13, R14 | `cv_object = False` set on list/card/create/manage/form/create-select |
| R12 | plan text only; no source dependency |
| R15 | `pyproject.toml:81`; `test_i18n.py:65-81`; tracked `.mo` |
| R16 | `examples/bootstrap5/manage.py`; verify block |

None of the sixteen remains open.

**New actionable items, in priority order.**
1. Plan 01 task 01: pass `ViewContext(view=rendering_view, object=owner)` when rendering default owner labels, and test an owner label template that references `object` (MEDIUM).
2. Plan 02 task 01 or plan 03 task 02: add the all-hidden case with builder count 1, one hook per item, zero state calls and empty output (MEDIUM).
3. Plan 01: fix `owner.pk_name` wording; state the chain index rule for the active child; reuse `CheckTemplate` (LOW).
4. Plan 03 task 02: name `guardian.shortcuts.clear_ct_cache()` in the cold definition (LOW).
5. Plan 04 task 01: give the Notes view its own action label templates (LOW).
6. Plan 02 or 05: forbid a `navbar`-prefixed class on the items landmark so `navbar_html` keeps slicing the site navbar (LOW).
7. Plan 06: update the "All four" sentence in `templates.md`; document the two meanings of `cv_navbar` (LOW).

**Ordering and ownership.** Waves remain coherent. Wave 3 plans touch disjoint files; `navbar.py` edits are sequential across plans 01, 02 and 03; `features.py` is edited by plan 05 then 06; plans 07 and 08 share no files. The guard's unconditional ancestor resolution (`ancestors.py:498-566`) supports the omitted-intermediate-mixin scenario without new queries.

**Security and performance.** Visibility and authority remain separate; destination requests still run the full guard. Escaping is handled at one boundary. No added work on nonparticipants is achievable because the mixin is opt-in and the lazy wrapper defers all work.

**Overall risk: LOW to MEDIUM.** The plans are executable as written once the two MEDIUM clarifications are added. Remaining risk is environmental: browser tooling, interpreter availability and the companion checkout, all of which the plans already treat as explicit unmet gates rather than passes.
