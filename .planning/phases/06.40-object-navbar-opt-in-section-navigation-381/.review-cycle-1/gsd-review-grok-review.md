I'll verify each plan against the source, starting with the files the plans treat as the contract.
## 06.40-01

The core contract is source-aligned: one opt-in module, literal keys before the list-to-card fallback, and target-specific reverse instead of the rendering view's URL helper. The main risk is an easy active-section inversion, not a missing feature.

**Strengths**
- `get_view_class` and `get_router_name` both rewrite an unregistered `list` to `card` (`src/crud_views/lib/viewset/__init__.py:375-388`). Requiring literal registration first is the right guard.
- Owner links must use `ViewSet.pk_name` (default `"pk"`, `src/crud_views/lib/viewset/__init__.py:79`). Child links must use `ParentViewSet.get_pk_name()` (`src/crud_views/lib/viewset/parentviewset.py:56-60`). The plan keeps those distinct and does not call `cv_get_router_and_args`, which is bound to the rendering ViewSet and lets extra kwargs overwrite parent kwargs (`src/crud_views/lib/view/base.py:717-749`).
- `_resolved_ancestor` reads request state and does not query (`src/crud_views/lib/ancestors.py:576-585`). Modal detection is `X-CV-Modal == "true"` (`src/crud_views/lib/view/base.py:71-73`). Cooperative `checks()` already exists on the breadcrumb mixin (`src/crud_views/lib/breadcrumb.py:98-106`) and is reached through `ViewSet.checks` (`src/crud_views/lib/viewset/__init__.py:286-287`) and `check_viewsets` (`src/crud_views/checks.py:38-46`).
- `ActionView` defines `post` only (`src/crud_views/lib/views/action.py:12-23`), so the dual GET check is necessary.

**Concerns**
- MEDIUM: `_walk_ancestors` yields `(edge, ancestor)` nearest-first, not the child ViewSet (`src/crud_views/lib/ancestors.py:89-121`). The active section is the ViewSet that owns the edge whose ancestor is the navbar owner. Selecting `ancestor.name` highlights the owner, not Orders.
- MEDIUM: Issue A-01 locks `NavBar(viewset: str, ...)` so the bar can be built before child registration (`06.40-ISSUE-381.md:328-332`). The task signature says `NavBar(viewset, items, template=None)` and does not pin `str`. A ViewSet instance would register too early and fight the isolated-registry tests.
- LOW: Startup rejection is specified for owner list/create. `CreateView.cv_object` and `ListView.cv_object` are both `False` (`src/crud_views/lib/views/create.py:17`, `src/crud_views/lib/views/list.py:26`), and `CardListView` is also non-object. An owner card or custom no-object page would pass this list and then fail at render because there is no owner object. Reject every owner attachment with `cv_object is False`.

**Suggestions**
- Spell the active-child walk: from the rendering ViewSet, the node whose parent name is the navbar owner.
- Write `viewset: str` and `child: str | None` into the task action.
- Treat any owner non-object attachment as the list/create error.

**Risk Assessment:** MEDIUM. The routing and check design matches the code; the active-section indexing is the likely AC2 miss.

## 06.40-02

Template splitting and the one-wrapper lazy contract match the approved UI fields and the existing eager breadcrumb, which must not be copied.

**Strengths**
- Breadcrumb context builds immediately (`src/crud_views/lib/breadcrumb.py:280-283`). Manage already uses `SimpleLazyObject` (`src/crud_views/lib/views/manage.py:1010-1018`). Keeping one wrapper and forbidding a boolean test is the right fix for Django's lazy wrapper.
- The fixed inclusion tag at `src/crud_views/templatetags/crud_views.py:446-449` cannot choose `NavBar.template`. A context-taking tag is required. `theme_path` is `"crud_views"` (`src/crud_views/lib/settings.py:322-324`), so loader overrides are the real global seam.
- `render_icon("")` returns empty (`src/crud_views/lib/icons.py:203-214,239-242`). `Icon.NONE` is `""` (`src/crud_views/lib/icons.py:15-19`). Empty-icon suppression is real.
- `aria-current="true"` matches the UI-SPEC because a descendant page activates another section. That is an adopted refinement, not a hole.

**Concerns**
- MEDIUM: The landmark is specified as `Sections for %(object)s` with `str(object)`. `%`-interpolation raises or mis-formats when the caption contains `%`. Captions are model text and must be escaped after formatting, including `SafeString`.
- MEDIUM: No plan updates `src/crud_views/locale/de/LC_MESSAGES/django.po` or the compiled `.mo`. `tests/test1/test_i18n.py:65-73` only fails on empty or fuzzy entries already in the catalog, so an untranslated public landmark still passes.
- LOW: Split-placement "build once" is not guaranteed if a template copies the unevaluated wrapper. The plan allows a private sentinel only after a failing test. That is acceptable if the counter test is written first.

**Suggestions**
- Format the landmark with a method that does not interpret `%` in the caption, then `escape()` the result.
- Add the German catalog entry and `.mo` rebuild to this plan or to 06.40-06, and assert the rendered German accessible name.

**Risk Assessment:** MEDIUM. Layout and laziness are sound; the caption format and catalog are the gaps.

## 06.40-03

Admission order is specified against the real hooks, including the Guardian create override that must not be called twice. Cost measurement is separated from hook counts, which the existing child-link tests already require.

**Strengths**
- Child admission is `target._cv_child_link_has_access(user, owner)` once (`src/crud_views/lib/view/base.py:528-541`). Guardian create's override returns `cv_has_access` and must not be wrapped again (`src/crud_views_guardian/lib/views.py:387-390`).
- Context buttons do the opposite order: state, then access (`src/crud_views/lib/view/buttons.py:237-243`). Not reusing that renderer is correct.
- `_immediate_parent_access` raises `ImproperlyConfigured` for a missing key, missing operation requirement, or non-default auth database (`src/crud_views/lib/ancestors.py:654-670`). Propagating those errors matches the helper.
- Core `cv_has_access` is `user.has_perms`, not a row count (`src/crud_views/lib/view/base.py:1334-1341`), so an empty collection stays visible.

**Concerns**
- MEDIUM: `CreateView._cv_action_enabled_for_rendering` can ignore the passed owner and call `get_object_or_404` when `_resolved_ancestor` is missing (`src/crud_views/lib/views/create.py:52-75`, `src/crud_views/lib/view/base.py:1169-1188`). A builder invoked outside `dispatch` will show an owner reload that a guarded request does not. Cost tests must go through the ancestor guard or they will either false-fail or hide a real extra query.
- LOW: "No collection count/exists" needs a query assertion, not only a spy on the access hook. Guardian collection access is not a count (`src/crud_views_guardian/lib/mixins.py:287-305`), but a later template `if items` on a queryset would still scan.

**Suggestions**
- Assert SQL for create-item state on a dispatched grandchild request, and assert the same owner instance is passed into the child hook.
- Keep collection visibility tests on an empty table with `assertNumQueries` around the builder.

**Risk Assessment:** MEDIUM. The policy is right; the create-state adapter is the measurement trap.

## 06.40-04

The Tenant/Customer slice matches `GuardianViewSet` usage and does not import another example's models. Verification does not prove the installed package or the migration gate the acceptance text names.

**Strengths**
- `AncestorPolicy(provider="guardian", accept_global_perms=False)` is the existing guardian example (`examples/bootstrap5/guardian_demo/views.py:21-28`). `cascade` is a target-request field, defaulting to inherit (`src/crud_views/lib/ancestor_policy.py:9-11,46-57`). `DEFAULT_CASCADE` is `True` (`src/crud_views/lib/ancestor_policy.py:19-22`).
- Example URLs are plain `include`s with no namespace (`examples/bootstrap5/project/urls.py:30-50`), so `reverse(viewset.get_router_name(key))` works when `app` is unset.
- Unique `navbar_*` names avoid the process-global registry (`src/crud_views/lib/viewset/__init__.py:206-211`).
- A test-local URLconf before `project.urls` wiring is a reasonable first slice.

**Concerns**
- MEDIUM: Example pytest imports installed `crud_views`, not checkout `src`. `noxfile.py:209-213` installs `.[all,test,examples]` and runs pytest with the session environment. The verify command does not set `PYTHONPATH`. A reused examples venv that does not reinstall the local project will miss `navbar.py`. The plan's `PYTHONPATH=../../src:.` note applies only to migration generation, not to the gate.
- MEDIUM: Acceptance requires `makemigrations --check --dry-run`, but `<verify>` is only pytest. Drift is not a failing gate.
- LOW: Task 01 can pass on a test URLconf while task 02 is what actually publishes `/object-navbar/`. That split is fine if task 02's tests reverse through `project.urls`.

**Suggestions**
- Make the verify command print `crud_views.__file__` and fail unless it is the session install of this checkout, or force-reinstall before pytest.
- Add the migration check to `<verify>`, using the examples interpreter and `PYTHONPATH` only if generation must see uninstalled source.

**Risk Assessment:** MEDIUM. The authorization shape is right; the example gate can test the wrong package.

## 06.40-05

The hierarchy, grant boundary, and Item-page assertions match D-15. Charlie's discoverability is required by the task and is not owned by any plan's file list.

**Strengths**
- Cascading Tenant denial is the right security test, and the plan keeps business grants at model level. `ensure_developer_read_access` is an explicit allowlist and raises on extra developer permissions (`examples/bootstrap5/project/seeding.py:42-81`), so omitting `navbar_demo` from that dict is the correct way to avoid expanding developer.
- Placement before the card matches layout B (`examples/bootstrap5/project/templates/project/crud_views.html:10-14`). The tag is already loaded.
- Empty Orders stays a permission result, not a count, if the list view uses core `cv_has_access`.
- Registering `FEATURES` only after `seed.py` exists matches `seed.py:18-19`, which imports `{feature.app}.seed`.

**Concerns**
- HIGH: "Shared login/home account help discovers Charlie" cannot be done inside `files_modified`. Credentials are hardcoded, not read from `DEMO_USERS`:
  - `examples/bootstrap5/project/templates/registration/login.html:15`
  - `examples/bootstrap5/project/templates/project/home.html:42-44`
  - `examples/bootstrap5/project/templates/project/base.html:51-52`
  - `examples/bootstrap5/project/management/commands/seed.py:17` (this file is in the plan; the templates are not)
  - German copies of those strings are in `examples/bootstrap5/locale/de/LC_MESSAGES/django.po:1336-1343` and the home msgid near line 1377.
  - `examples/bootstrap5/test_i18n.py:197` requires the last `<code>` to be `developer/developer`. Appending Charlie fails that test. The test is not in this plan's verify, so the failure waits until 06.40-08.
  - The "split a follow-up" sentence does not assign those files to a later plan. 06.40-06 through 06.40-08 do not list them.
- MEDIUM: "Cross-tenant descendant requests fail" can be satisfied by 404 on a broken ancestor chain. D-15 wants denial. A copied Item URL must keep a consistent Tenant → Customer → Order → Item chain and return 403.
- MEDIUM: `{% cv_navbar %}` on a new indented line in `crud_views.html` adds whitespace to every example page. Django does not strip surrounding whitespace. Byte identity requires splicing the tag onto an existing line. This plan's verify does not run the other example HTML tests.
- LOW: `test_every_feature_declares_doc_refs` fails while `docs` is empty (`examples/bootstrap5/test_doc_links.py:105-107`). That is acceptable only because 06.40-06 adds the `DocRef` before the matrix. Do not run the full examples suite as this plan's gate.

**Suggestions**
- Add the three templates, `django.po`/`django.mo`, and `test_i18n.py` to this plan. Put Charlie before the developer sentence, or change the last-code assertion deliberately.
- Pin 403 on a structurally valid cross-tenant URL, and assert denied POSTs leave row counts and field values unchanged.
- Specify the exact `crud_views.html` splice and compare one nonparticipant example response to a pre-change byte fixture.

**Risk Assessment:** HIGH. The scenario is right, but the account-discovery contract is unowned and the existing i18n test will reject a naive edit.

## 06.40-06

Documentation is correctly downstream of measured costs and the example. The reciprocal-link mechanism already exists and the plan uses it.

**Strengths**
- `DocRef.url` builds the Read the Docs path (`examples/bootstrap5/project/features.py:17-26`). `test_docs_page_links_back_to_demo` requires `DEMO_BASE + reverse(feature.url_name)` (`examples/bootstrap5/test_doc_links.py:127-146`). The hardcoded `https://django-crud-views-demo.onrender.com/object-navbar/` matches that if the include is `object-navbar/`.
- `mkdocs.yml` has `nav` commented, so skipping a nav edit is correct.
- Stability policy is an explicit name list (`docs/development/stability.md:7-17`). Inventorying declarations, the tag, three templates, and documented context, and leaving helpers internal, matches D-16.
- Executing documented snippets in `test_navbar_docs.py` is stronger than a prose grep.

**Concerns**
- MEDIUM: Task 01's verify is only `mkdocs build --strict`. That does not check that the live URL equals `reverse("navbar-demo-home")`. A trailing-slash or prefix drift fails later in task 03, which is acceptable if task 03 is mandatory before the plan is done.
- LOW: Quoting `06.40-COST.md` from one Django 5.2 run is fine only with the fixture and cache conditions. The plan already says not to promise zero queries. Keep that sentence next to the table, not only in the task action.
- LOW: A real breaking change is deferred to "treat as a scope finding". That is the right policy; do not let the additive changelog entry be written before the golden and example byte checks in 06.40-03 and 06.40-05 have passed.

**Suggestions**
- Generate the Try-it URL in the docs test with `reverse`, and compare it to the admonition, instead of trusting the hardcoded path.
- If 06.40-02 adds a gettext landmark, this plan should fail unless the German catalog contains it.

**Risk Assessment:** LOW. The doc contract is executable and ordered correctly, assuming 06.40-05 actually lands the route name it cites.

## 06.40-07

The companion target is the external skills repo named by the development docs, not a bundled path. Delivery is local-only, which matches the planning note.

**Strengths**
- `docs/development/index.md:87-91` says the skill lives in `jacob-consulting/skills` and is not bundled. `06.40-COMPANION-GUIDANCE.md` names the four tracked files. The plan refuses installed mirrors and refuses push/publish.
- Verifying remote identity before reuse, and refusing a dirty foreign checkout, is the right guard.
- Comparing the four diffs to the product reference, including literal list keys and access-before-state, is the useful check. A validator pass alone would not catch policy drift.

**Concerns**
- MEDIUM: `<verify>` runs `.venv/bin/python ../skills-navbar-06-40/scripts/validate.py` from the product root. The inspected workflow is `python3 scripts/validate.py` in the companion checkout. If that script uses the process cwd rather than `__file__`, this command fails or validates the wrong tree. The script is not in this repo, so this stays a command-contract risk, not a claim that the script is wrong.
- MEDIUM: The checkout path is relative to the executing worktree. A phase worktree under `/home/alex/projects/workspaces/...` makes `../skills-navbar-06-40` a different directory than from this checkout. The plan allows a worktree fallback, but the verify path is still hardcoded.
- LOW: Task 01's verify runs the validator before task 02's commit. That is fine if the edits are already on disk. A clean validator with no diff must still fail the task, which the `fails_when` text says.

**Suggestions**
- Run the validator with `workdir` set to the recorded companion root, and record that cwd in `06.40-COMPANION-DELIVERY.md`.
- Resolve the checkout path from `git rev-parse --show-toplevel` of the product repo, not from a fixed `../`.

**Risk Assessment:** MEDIUM. Scope and provenance are tight; the gate command may not match the companion workflow.

## 06.40-08

The final gate correctly separates source, installed, declared skips, browser evidence, and companion delivery. A few commands do not measure what they claim.

**Strengths**
- Nox tests clear `PYTHONPATH` and assert the import is from site-packages (`noxfile.py:7-16,30-46`), then rerun with `CV_ACCESS_RECORD_REQUESTS=1` (`noxfile.py:49-57`). Django 4.2 on Python 3.14/3.15 is an explicit skip (`noxfile.py:23-25`). Calling those skips passes would be wrong; the plan forbids that.
- `manage_report_floor` appends posargs after its own list and pins Pydantic 2.2.1 (`noxfile.py:88-107`). The `test` extra includes `django-guardian` (`pyproject.toml:70-80`), so Guardian navbar tests can import there.
- Browser settings that only replace `DATABASES["default"]["NAME"]` avoid the developer database. `DEBUG=True` with empty `ALLOWED_HOSTS` still allows `127.0.0.1` (`examples/bootstrap5/project/settings.py:15-19`). Refusing to treat `deviceScaleFactor` as zoom is correct.
- AC8 staying unmet when the browser cannot launch is the right fail-closed rule.

**Concerns**
- MEDIUM: `.venv/bin/nox -s tests examples crispy_floor -- -n 4 -q` appends `-n 4` after the sessions' own `-n auto` (`noxfile.py:36-45,199`). Last `-n` usually wins, but this is accidental. The examples session has no `-n` of its own (`noxfile.py:212-213`); `-n 4` is valid only because the `test` extra installs xdist.
- MEDIUM: Overall sign-off depends on `06.40-COMPANION-DELIVERY.md` while 06.40-07 runs in parallel and writes that file. A ledger written first can be marked complete before the receipt exists. The plan says not to, but the verify command does not read the receipt.
- LOW: Playwright login must POST the real login form. The login template is a CSRF form (`examples/bootstrap5/project/templates/registration/login.html:13`, `examples/bootstrap5/project/urls.py:13-24`). A cookie-only script will not authenticate.
- LOW: `package` is pinned to Python 3.13 (`noxfile.py:216-217`). If uv cannot provide 3.13, that cell is unavailable, not a pass. The plan already says to record that.

**Suggestions**
- Pass worker count only where the session does not already set `-n`, or document that the later `-n 4` is intentional.
- Make task 02's verify fail if `06.40-COMPANION-DELIVERY.md` has no commit SHA.
- In the browser script, GET `/login/`, submit the form, and then follow navbar `href`s with full document loads.

**Risk Assessment:** MEDIUM. The acceptance ledger is honest; the parallel companion dependency and the combined nox posargs are the weak edges.

## Cross-plan

Wave order matches the data dependencies: declaration and checks, then template contract, then permission tests beside the example slice, then the full scenario, then docs, then companion and matrix. 06.40-03 and 06.40-04 do not share files. 06.40-07 and 06.40-08 do, through the companion receipt.

The plans do achieve the phase goal if executed as written: one opt-in bar, stable owner URLs, access-before-state, application-owned templates, and a Tenant example that does not change context buttons or ancestor policy. They correctly refuse a general URL helper and a forgotten-mixin detector. Empty `requirements` matches the roadmap TBD line and should stay empty.

The review-blocking gap is 06.40-05's Charlie surfaces. Everything else is executable with the fixes above. Path-probe `not_applicable` on the env-prefixed pytest commands is not evidence those interpreters exist.

**Overall risk: MEDIUM**, raised by the unowned login/catalog edit. Fix that file list before execution; the other findings can be tightened in the task actions without reshaping the waves.
