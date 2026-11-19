I have verified the key mechanisms against source. Two probes were blocked by the sandbox and are reported as open questions rather than findings: listing the companion checkout path outside the repo, and running the root `.venv` interpreter to confirm its Django version and PyYAML.

# Cross-AI Plan Review: Phase 06.40 (Object navbar)

Verification method: every mechanism the plans rely on was read in the current checkout at HEAD `88cd7c70`. Findings below cite `path:line`. No tests were run and no files were modified.

## 06.40-01

**Summary.** The plan correctly grounds the navbar on the existing cooperative-mixin, resolved-ancestor and literal-key facts. The three source claims it depends on all hold: `_resolved_ancestor` reads request-local state without a query (`src/crud_views/lib/ancestors.py:576-585`), both `get_view_class` and `get_router_name` silently substitute `card` for a missing `list` (`src/crud_views/lib/viewset/__init__.py:375-388`), and `cv_is_modal_request` is the header predicate (`src/crud_views/lib/view/base.py:71-73`). The main weaknesses are a missing file in the task-01 file list and an unaddressed check-ordering hazard in task 03.

**Strengths.**
- The access-then-state order is a deliberate inversion of the existing renderers, which evaluate state first (`src/crud_views/lib/view/buttons.py:237-243`). The plan isolates that ordering in navbar code and leaves `buttons.py` untouched, matching D-14.
- Hook signatures quoted in the plan match source exactly: `cv_has_access(cls, user, obj=None)`, `_cv_child_link_has_access(cls, user, parent_obj)`, `_cv_action_enabled_for_rendering(cls, user, obj, rendering_view)` at `base.py:524-566`.
- Owner-item access via core `cv_has_access` ignores the object and checks only the model permission (`base.py:1334-1341`), so hidden Update for a read-only user works as D-09 expects without new policy.
- Owner PK naming reuses `ViewSet.pk_name` (default `"pk"`, `viewset/__init__.py:79`) and child parent-edge naming reuses `ParentViewSet.get_pk_name()` (`parentviewset.py:56-60`), avoiding hard-coded names.
- GET-eligibility detection is right: `ActionView` inherits Django's default method list but defines only `post` (`src/crud_views/lib/views/action.py:12-23`), so the "callable handler" half of the check is necessary.

**Concerns.**
- **MEDIUM. Task 01 acceptance needs a template that is not in the file list.** The acceptance criterion says a real owner GET renders the identity "above ... its unchanged page header". The core test base template `tests/test1/app/templates/app/crud_views.html` contains no `{% cv_navbar %}` and nothing in `files_modified` adds one. Either a test-local template selected through `cv_extends_template` (`base.py:426-431`) or an edit to the shared test base is required; the executor will have to deviate.
- **MEDIUM. Check-time forward references.** Navbar checks are yielded from `view.checks()`, which runs inside `check_viewsets` (`src/crud_views/checks.py:38-47`). That function has no readiness barrier, unlike `check_ancestor_declarations`, which calls `_url_configuration_loaded()` first (`checks.py:172-212`). A-01 says names are strings precisely so a bar can be declared before its child ViewSets exist. Without the barrier, "unknown child" and "not a direct child" errors can fire on an incomplete registry. `ChildContextButton.cv_check_target` (`buttons.py:211-220`) has the same exposure today, so this is an inherited pattern, but the plan's "test valid declarations before ViewSets register" wording needs a concrete mechanism.
- **MEDIUM. Fixture duplication and the registry-leak fix.** The plan says to build isolated registry/URLconf fixtures "inside test_navbar.py", while plan 03 says to reuse plan 01's fixtures via imports. The existing `isolated_routes` helper (`tests/test1/test_ancestor_authorization.py:46-77`) depends on the module-level `import tests.test1.project.urls` at line 38 to avoid order-dependent registry pollution. A copied helper that omits that import reintroduces the failure mode. Prefer importing the existing helper or moving it to a shared module.
- **LOW. Check-ID audit scope.** The plan says to search current IDs. Note that IDs appear in two forms: `id: str = "E255"` on Check subclasses, and literal `id="viewset.E266"` / `id="crud_views.E3xx"` strings in `checks.py:73,87,118,166` and the icon/button modules. A grep for one form alone misses the other.
- **LOW. Task 02 size and estimate.** Task 02 alone covers five child page kinds, grandchild editing, omitted intermediate mixin, custom parent PK names and nested Tenant URLs. The whole plan is estimated at 30k tokens with low confidence; the actual work is several times that.

**Suggestions.**
- Add the test base-template placement to task 01's files, or state the `cv_extends_template` strategy explicitly.
- Gate registry-dependent navbar errors on `_url_configuration_loaded()` or emit them from a dedicated registered check, mirroring `checks.py:198-212`.
- Import `isolated_routes` rather than copying it; if it must be copied, carry the line-38 pre-import.
- Split task 02 into destination resolution and active-section/nested-owner coverage.

**Risk: MEDIUM.** The design is sound; the risks are executor deviations caused by omitted files and a check-ordering edge the plan names but does not resolve.

## 06.40-02

**Summary.** The lazy-context and override-contract plan is consistent with how the package already uses `SimpleLazyObject` (`src/crud_views/lib/views/manage.py:1017-1019`, and `base.py:1162` for `parent_object`). The fixed-template inclusion decorator used by `cv_breadcrumb` (`src/crud_views/templatetags/crud_views.py:446-449`) cannot select a per-bar template, so the context-taking simple tag is the right choice. The breadcrumb's eager build at `breadcrumb.py:280-283` is correctly identified as something not to copy.

**Strengths.**
- Explicit rule that templates never call a builder and that all three leaves guard the same named value keeps split placement independent.
- Forced escaping of `SafeString` captions is the right call: the breadcrumb deliberately preserves `SafeData` titles (`breadcrumb.py:30-37`), and the plan correctly refuses to inherit that behavior for D-11 plain text.
- Using `aria-current="true"` rather than `"page"` on an Item page where Orders is active is a defensible refinement of A-05 and is recorded as such.
- Choosing Bootstrap `text-break` first, with a scoped stylesheet as a fallback, follows the precedent in `src/crud_views/templates/crud_views/view_manage.html:16,282` and `static/crud_views/css/manage.css:18`.

**Concerns.**
- **MEDIUM. "Exact empty string" versus all-hidden admission.** The plan pins exact empty output when zero items are visible, and UI-SPEC requires that the all-hidden case still performs admission once. Both are achievable, but the test must distinguish "builder ran and returned a falsy result" from "builder never ran". The plan's counters should assert build count 1 and hook count N for the all-hidden case, not zero.
- **LOW. Lazy wrapper truthiness.** `{% if cv_navbar %}` evaluates the wrapper, which is desired in consuming templates. The risk is a context processor or debugging aid calling `bool()` or `repr()` on the context and forcing a build on pages that never render the bar. The zero-work tests for omitted consumers should run through the real `CRUD_VIEWS_EXTENDS` page, not a bare `Template(...)`.
- **LOW. Deferred CSS decision.** If the plan-08 browser check later forces a scoped stylesheet, the `css` map in `src/crud_views/lib/settings.py:354-361` is the delivery seam. Adding an entry there changes `{% cv_css %}` output for every page, which would need the nonparticipant byte tests from plan 03 to be rerun. The plan says so; the dependency is just worth tracking explicitly.

**Suggestions.**
- Add an explicit "all-hidden: builds once, hooks N, output empty" case to task 01.
- Run omitted-consumer zero-work tests through a real page render with the test base template.

**Risk: LOW to MEDIUM.** Mostly test-precision details; the mechanism is proven elsewhere in the codebase.

## 06.40-03

**Summary.** The permission and cost plan targets the right seams. Request-time state enforcement for permission-required views exists at `base.py:1315-1331`, so the "state-denied owner GET returns 403" assertion in AC3 is achievable only with a `*PermissionRequired` composition, which the plan says. Guardian's create overrides the child hook to its own parent-aware access (`src/crud_views_guardian/lib/views.py:388-390`) and standalone Guardian queryset compositions skip the parent check (`mixins.py:297-305`), both of which the plan preserves by calling the hook once and never re-deriving policy.

**Strengths.**
- Once-only hook assertion with exact `(user, owner)` arguments mirrors the existing spy pattern in `tests/test1/test_guardian_child_link_visibility.py`.
- The plan separates hook counts from SQL and refuses to promise query-free Guardian checks. This matters: the core child hook calls `_immediate_parent_access` without a `rendering_view` (`base.py:535`), so a Guardian-provider immediate parent is checked with `view=None` and any request-local caching keyed on the view is bypassed.
- Propagation of `ImproperlyConfigured` from `_immediate_parent_access` (`ancestors.py:669-685`) rather than converting to invisibility matches the documented child-link contract.

**Concerns.**
- **MEDIUM. Nonparticipant byte parity relies on where the tag lands.** Task 02 asserts existing goldens byte-for-byte and "pairs equivalent nonparticipant pages before/after tag placement". The core goldens under `tests/test1/golden/` are region snapshots (`action_menus`, `alerts`, `form_buttons`, ...), not whole pages, so they will not catch whitespace added around a new block in `app/crud_views.html`. The paired-page comparison is the real guard and must be defined concretely, since this plan's file list contains no template.
- **LOW. COST.md as a planning artifact.** Documentation in plan 06 quotes measured numbers from `.planning/.../06.40-COST.md`. That file is outside the sdist (`pyproject.toml:113-123`) and outside what tests can import. Fine for a receipt, but the reference should carry the measured conditions in prose rather than linking to a planning path.

**Suggestions.**
- State in task 02 which template receives the tag for the core preservation comparison and whether whitespace-normalized comparison is acceptable.
- Record cold/warm distinctions per hook, since the Guardian `view=None` path is where numbers will differ.

**Risk: MEDIUM.** Sound approach; the risk is weak preservation evidence if the tag placement is left implicit.

## 06.40-04

**Summary.** The example scaffold is consistent with the package's authorization engine. With Tenant as a `GuardianViewSet` using `AncestorPolicy(provider="guardian", accept_global_perms=False)` and Customer as a core ViewSet, a Customer request gates on Tenant object grants through `_authorize_ancestors` (`ancestors.py:525-563`), while Order and Address requests gate on Customer via the model provider `user.has_perm(permission)` (`viewset/__init__.py:507-509`) and on Tenant through the `higher` key because `DEFAULT_CASCADE = True` (`src/crud_views/lib/ancestor_policy.py:19-22`). The approved grant model therefore works without per-record grants.

**Strengths.**
- Reuses the Guardian demo composition pattern verbatim (`examples/bootstrap5/guardian_demo/views.py:21-28`) for Tenant and the nested app pattern for everything below.
- Registration follows the existing append conventions in `examples/bootstrap5/project/settings.py:44-66` and `project/urls.py:30-50`.
- Deferring `FEATURES` registration until the seed module exists is correct: the seed command imports `f"{feature.app}.seed"` for every registered feature (`project/management/commands/seed.py:18-19`), so registering early would break `manage.py seed`.
- Tenant list filtering through `get_objects_for_user` (`src/crud_views_guardian/lib/mixins.py:360-368`) gives the landing page a safe source of permitted tenants.

**Concerns.**
- **MEDIUM. Example Nox environment does not exist yet.** `.nox/` currently holds only `tests-*`, `crispy_floor-*`, `manage_report_floor` and `package`. The first `.venv/bin/nox -s "examples-3.12(django='5.2')"` run provisions it from `.[all,test,examples]` plus `requirements/demo.txt` (`noxfile.py:202-213`). The plan acknowledges this, but the migration-generation step in task 02 depends on it, so the ordering "provision, then makemigrations" must be respected literally.
- **LOW. URL kwarg names.** Uniquely prefixed ViewSet names such as `navbar_tenant` give default parent kwargs like `navbar_tenant_pk` (`parentviewset.py:60`). That is legal but reads poorly in copied URLs that the example is meant to demonstrate. `ParentViewSet(pk_name="tenant_pk")` satisfies the regex at `parentviewset.py:9`.
- **LOW. Two URL routings in two tasks.** Task 01 tests through a test-local URLconf and task 02 through project URLs. Workable, but the task-01 tests get rewritten in task 02. Consider wiring `urls.py` in task 01 and leaving only the migration for task 02.

**Suggestions.**
- Set explicit `pk_name` values on the example's `ParentViewSet` declarations.
- Collapse routing into task 01.

**Risk: LOW to MEDIUM.** Mechanisms verified; residual risk is environment provisioning order.

## 06.40-05

**Summary.** The completion plan covers the approved scenario and the right denial tests. Its weakest point is Charlie discoverability: the account help is hard-coded text, not driven by `DEMO_USERS`, and the templates that carry it are absent from the file list.

**Strengths.**
- Denied-write tests that assert unchanged rows, not only status codes, follow `examples/bootstrap5/nested/tests.py:138-149` and close the "hidden link mistaken for enforcement" threat.
- Keeping the developer account's explicit read list untouched is correct: `ensure_developer_read_access` raises `CommandError` on any permission outside its allowlist (`project/seeding.py:77-85`), so accidental grants would fail the seed loudly.
- Landing choices derived from the Guardian queryset rather than a username gate address T-06.40-13 with existing machinery.

**Concerns.**
- **MEDIUM. Charlie is not discoverable through `DEMO_USERS`.** The plan adds Charlie to `DEMO_USERS` and the seed command's printed help. But the user-facing account text is hard-coded in `project/templates/project/home.html:42-45` and `project/templates/project/base.html:52`, and `project/tests.py:92-94` asserts the alice/bob strings. Neither template is in `files_modified`. UI-SPEC requires Charlie's instructions "alongside Alice/Bob in the example's own intro or shared account help"; as planned, only the landing page could carry them. Either add the two templates or state that the example's own landing is the sole discovery point.
- **LOW. Byte-identical example base template is self-imposed and awkward.** Task 03 requires nonparticipant example pages to stay byte-identical after adding a block to `project/crud_views.html`. No example test asserts whole-page bytes, and any new line in that template emits a newline plus indentation. Meeting it literally forces the new block onto an existing line. A whitespace-normalized comparison, or dropping the requirement for the example and keeping it for core goldens, is more maintainable.
- **LOW. Seed output assertions.** `SeedCommandTest` in `project/tests.py` likely checks the printed account line from `seed.py:17`. The plan allows for updating shared seed tests but should name this file.

**Suggestions.**
- Add `home.html` and `base.html` to task 02's files, or record the narrower discovery scope.
- Relax the example-template byte rule to whitespace-insensitive.

**Risk: MEDIUM.** The scenario and authorization are well-grounded; the discoverability claim is not deliverable from the listed files.

## 06.40-06

**Summary.** Documentation and stability-inventory tasks are correctly aligned with the repository's tooling. The reciprocal-link test computes `DEMO_BASE + reverse(feature.url_name)` and requires it inside an `!!! example` admonition on every referenced page (`examples/bootstrap5/test_doc_links.py:139-147`), so the plan's live URL `https://django-crud-views-demo.onrender.com/object-navbar/` is consistent with the `object-navbar/` include and a `""` landing route from plan 04. The claim that MkDocs navigation is generated is true (`mkdocs.yml:3` has `#nav:` commented out).

**Strengths.**
- The stability inventory is structured by module exactly as `docs/development/stability.md:19-66` does, and the plan explicitly keeps underscore helpers internal, matching the page's rule at lines 9-17.
- Executable documentation tests follow existing precedents (`test_label_mode_docs.py`, `test_theme_adoption_docs.py`, `test_manage_command_docs.py` in `noxfile.py:71,118,131`).
- Limiting new `DocRef`s to pages that receive reciprocal boxes avoids spurious failures in `test_docs_page_links_back_to_demo`.

**Concerns.**
- **LOW. Template-tag reference coverage.** `stability.md` declares public "the tags documented in the reference for the `crud_views` ... tag libraries". The new `cv_navbar` tag therefore needs an entry on whichever page documents template tags, not only in `navbar.md` and the inventory. The file list includes `templates.md` and `theme.md` but does not name a template-tags page; confirm where tags are documented.
- **LOW. Measured costs sourced from a planning file.** As noted under plan 03, quote conditions and totals in prose; a link to `.planning/` is not a shippable reference.

**Suggestions.**
- Name the template-tags documentation page in task 02's files.

**Risk: LOW.**

## 06.40-07

**Summary.** The companion delivery is correctly scoped as a separate repository task. `docs/development/index.md:87-90` confirms the skill moved to `jacob-consulting/skills`, and `06.40-COMPANION-GUIDANCE.md` names the four tracked targets. The plan's safeguards against editing installed mirrors and against overwriting a foreign checkout are appropriate.

**Strengths.**
- Verifying remote identity and `git ls-files` before editing, plus a separate local commit with a recorded SHA, gives a reproducible receipt.
- Using the companion's own `scripts/validate.py` rather than inventing a check keeps the task bounded.

**Concerns.**
- **HIGH (operational). The target path is outside the sandbox.** All four `files_modified` entries resolve to `/home/alex/projects/alex/skills-navbar-06-40`, outside this repository. In this review session the tool layer refused even to list that path ("may only list files in the allowed working directories"). A `gsd-executor` running under the same restrictions cannot clone, read or edit there without an added working directory or explicit permission. The plan does not state that prerequisite, so plan 07 may fail at its first command for reasons unrelated to its content.
- **MEDIUM. Unverified runtime assumptions.** VALIDATION.md asserts the root `.venv` has PyYAML and that the companion checkout was inspected during planning. I could not run `.venv/bin/python` in this session to confirm PyYAML. Treat both as open until the executor records them in COMPANION-DELIVERY.md.
- **LOW. `git show --check`** in the verify block is a diff whitespace check, not a validator; it is fine as evidence of the commit but should not be read as content verification.

**Suggestions.**
- Add an explicit prerequisite step: confirm the harness grants access to the sibling path, or clone into a path inside an allowed directory and adjust the relative paths.
- Record the PyYAML probe output in the receipt.

**Risk: HIGH on execution environment, LOW on content.**

## 06.40-08

**Summary.** The acceptance plan maps to real Nox sessions and preserves their installed-origin assertions. `noxfile.py:30-57` shows the `tests` session runs twice with `PYTHONPATH=""` and the recorder flag, and `-n auto` precedes `*session.posargs`, so a trailing `-n 4` overrides it. `manage_report_floor` appends posargs as extra test paths after its fixed list (`noxfile.py:99-107`) and pins `pydantic==2.2.1`, so appending the navbar modules does prove the floor. New templates ship because the wheel includes whole packages (`pyproject.toml:101-107`) and `scripts/check_dist.py:32-38` allowlists by top-level package, so no allowlist change is needed.

**Strengths.**
- Declared skips for Django 4.2 on Python 3.14/3.15 (`noxfile.py:23-25,205-207`) are explicitly separated from passes.
- Refusing to use the root venv's Django 6.1 as supported evidence is correct given the matrix is 4.2/5.2/6.0.
- Isolated SQLite for the browser run avoids touching `examples/bootstrap5/db.sqlite3`, which `.gitignore:5` already excludes.

**Concerns.**
- **MEDIUM. Browser tooling is a hard dependency the plan cannot create.** Task 01 relies on a Playwright `browser_run_code` tool and a background `runserver`. Research recorded that browser launch was never probed. The plan treats inability as an unmet human-check item, which is the honest fallback, but it means AC8 may end the phase open.
- **MEDIUM. Full matrix needs Python 3.13 and 3.14 interpreters.** `.venv/bin/nox -s tests examples crispy_floor` requests sessions for four Python versions. Research found only 3.12 and 3.15 on PATH. uv may fetch the others; if not, two of the four columns become "unavailable" and AC9's "full test matrix passes" cannot be claimed.
- **LOW. `.pytest_cache` as a settings location.** `.pytest_cache` is not in the repository `.gitignore`; pytest writes its own `.gitignore` inside the directory only when pytest creates it. If the executor creates the directory manually, the settings file is committable. Create it via pytest first, or use `mkdtemp`.
- **LOW. 200% zoom.** Playwright cannot set browser zoom; the plan's "reflow-equivalent CSS viewport" is the right stand-in and is correctly required to be recorded as such.

**Suggestions.**
- Probe browser tool availability at the start of wave 6, before docs settle, so a human verification item can be scheduled early.
- Probe `uv python list` before launching the full matrix and record the outcome in ACCEPTANCE.md.

**Risk: MEDIUM.** Commands are correct; the risk is environmental availability outside the plan's control.

## Cross-plan assessment

**Dependency ordering.** Waves are coherent. Plans 03 and 04 share no files in wave 3. Plan 05's `features.py` edit precedes plan 06's edit of the same file. Plan 07 and 08 are disjoint. One soft dependency is undeclared: plan 02's possible scoped stylesheet would alter `{% cv_css %}` output and require plan 03's nonparticipant tests to rerun; plan 02 mentions it but plan 03 does not.

**Scope.** No over-engineering was found. The plans resist a navbar registry, a class-key table and a second parent gate, and they consume the 06.39 hook at `base.py:528-541` once. The only scope rigidity is the byte-identical rule applied to the example base template in plan 05.

**Security.** Visibility and authority stay separate throughout: destination enforcement at `base.py:1295-1331` and the ancestor guard at `ancestors.py:464-567` remain the authority, and every plan tests real responses. Escaping of `SafeString` captions is explicitly tested. The Guardian `view=None` path in the core child hook is a cost concern, not a security one.

**Performance.** No added queries on nonparticipants is achievable because the mixin is opt-in and the lazy wrapper defers all work. Guardian-parent items will cost per-item queries; plan 03 correctly declines to promise otherwise.

**Does the set achieve the phase goal?** Yes for AC1 through AC7 and AC9's documentation half, with the file-list gaps above fixed. AC8 and the full-matrix half of AC9 depend on browser tooling and interpreter availability that the plans can only report, not guarantee. Plan 07 has an environment-access risk that should be settled before wave 6 starts.

**Overall risk: MEDIUM.** Recommended pre-execution edits, in priority order:

1. Plan 07: add the sandbox-access prerequisite for `../skills-navbar-06-40`, or relocate the checkout.
2. Plan 01: add the test base-template placement to task 01's files and specify the registry-readiness barrier for navbar checks.
3. Plan 05: add `home.html` and `base.html` to task 02 or narrow the Charlie discoverability claim.
4. Plan 01 and 03: converge on reusing `isolated_routes` from `test_ancestor_authorization.py`, keeping its line-38 pre-import.
5. Plan 08: probe browser tooling and uv-managed Pythons at the start of wave 6 and record results.
