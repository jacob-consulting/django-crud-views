I'll review all eight plans against source and the locked R17–R19 closures, starting with the cited view, routing, and Guardian cache paths.
The phase is in the roadmap. Next I’ll read the label, route, and cache implementations the revised plans depend on.
R17, R18, and R19 are closed. R1–R16 remain sound. No unresolved HIGH findings.

Coverage limitation: a phase-status seam can report `phase_not_in_roadmap`, but the phase is present at `.planning/ROADMAP.md:68` and `.planning/ROADMAP.md:2118`. The wave list there is stale (`TBD`, `0/8`) and is not the execution contract. Intel left Python symbols uncheckable; the citations below are from direct source reads.

## 06.40-01

One opt-in module, real-request routing, and startup checks cover AC1, AC2, and AC6. Owner labels and route kwargs are now specified against the actual APIs.

Strengths: `cv_get_action_short_label` renders `ViewSet.get_meta(context)` (`src/crud_views/lib/view/base.py:638-643`). `get_meta` merges `context.to_dict()` (`src/crud_views/lib/viewset/__init__.py:539`), and that dict is `{"object": self.object}` (`src/crud_views/lib/view/context.py:25`, `src/crud_views/lib/view/context.py:44-45`). Tasks 01–02 bind that object to the resolved navbar owner after access and state, without mutating the rendering view. `ViewSet.pk_name` is route metadata defaulting to `"pk"` (`src/crud_views/lib/viewset/__init__.py:79`); object routes use it with `obj.pk` (`src/crud_views/lib/view/base.py:731-732`). Child parent args come from `ParentViewSet.get_pk_name()` (`src/crud_views/lib/viewset/parentviewset.py:56-60`), which is not `ViewSet.pk_name`. Literal list/card fallback is real (`src/crud_views/lib/viewset/__init__.py:375-388`). `ActionView` defines `post` only (`src/crud_views/lib/views/action.py:12-23`). `_url_configuration_loaded` is the existing no-cache barrier (`src/crud_views/checks.py:172-195`).

Concerns: none.

Suggestions: none required for R17/R18.

Risk: low. Future execution must spy that the short-label `ViewContext.object` is the owner on owner, child, and grandchild requests.

## 06.40-02

Lazy shared context, three override levels, and escaped accessible markup cover AC4 and AC7. German landmark delivery is an owned catalog change.

Strengths: modal detection is exactly `X-CV-Modal == "true"` (`src/crud_views/lib/view/base.py:71-73`). The fixed breadcrumb inclusion tag cannot select `NavBar.template` (`src/crud_views/templatetags/crud_views.py:446-449`); a context-taking tag is the right seam. `polib` is already a test dependency (`pyproject.toml:81`).

Concerns: none.

Suggestions: none.

Risk: low. Narrow unbroken-token wrapping remains a plan 08 measurement, with the scoped-asset fallback already authorized.

## 06.40-03

Admission order, real destination responses, and separated cost accounting cover AC3–AC5. The cold Guardian content-type reset is now explicit.

Strengths: child admission is `_cv_child_link_has_access(user, parent_obj)` (`src/crud_views/lib/view/base.py:528-541`). State is a separate later call (`src/crud_views/lib/view/base.py:564-566`). Guardian create already applies its parent policy inside that hook (`src/crud_views_guardian/lib/views.py:388-390`). `reset_discovery` clears Django content types and Guardian content types independently, then assigns `_default_permissions = None` (`tests/test1/test_guardian_child_link_visibility.py:1052-1059`). Task 02 names `guardian.shortcuts.clear_ct_cache()` and requires that condition in `COST.md`.

Concerns: none.

Suggestions: none required for R19.

Risk: low. Publish measured SQL only after the new cost tests run. Do not treat hook-call counts as query counts.

## 06.40-04

The example starts as its own Tenant/Customer app with strict Guardian entry and a migration drift gate.

Strengths: `ParentViewSet.get_attribute()` falls back to the parent ViewSet name (`src/crud_views/lib/viewset/parentviewset.py:62-66`), so `attribute="tenant"` is required for `navbar_tenant`. Django’s test database creation calls `migrate` with `run_syncdb=True` (Django 5.2.19 `django/db/backends/base/creation.py:78-83`), so the unmigrated Task 01 slice can create tables before `0001_initial`.

Concerns: none.

Suggestions: none.

Risk: low. Task 02 must still record the `makemigrations --check --dry-run` exit separately from pytest.

## 06.40-05

The full Tenant → Customer → (Order → Item, Address) scenario, bounded grants, and index placement are executable without rewriting shared credential notices.

Strengths: `Feature.about` and `look_at` are required (`examples/bootstrap5/project/features.py:50-60`), and `FeatureGroupsTest` pins the `ui` list (`examples/bootstrap5/project/tests.py:457-477`). `ThemeIndexView` is the landing analog (`examples/bootstrap5/theming/views.py:21-31`). Shared notices still name only Alice/Bob/developer (`examples/bootstrap5/project/templates/project/home.html:42-45`); seed output is a separate literal (`examples/bootstrap5/project/management/commands/seed.py:17`). Cascading remains the default (`src/crud_views/lib/ancestor_policy.py:20`).

Concerns: none.

Suggestions: none.

Risk: low. Denied POST assertions must compare row contents, not only status codes.

## 06.40-06

Reference, stability inventory, and reciprocal demo links are tied to the final API and to `COST.md`.

Strengths: `test_snippet_docs.py` isolates `## Snippet variables` and requires exactly eight rows (`tests/test1/test_snippet_docs.py:14-36`). A preceding `## Object navbar context` heading does not enter that slice. Backlinks are `DEMO_BASE + reverse(feature.url_name)` (`examples/bootstrap5/test_doc_links.py:127-146`), so a guessed `/object-navbar/` path cannot pass unless it is the landing reverse.

Concerns: none.

Suggestions: none.

Risk: low. Do not put navbar fields in the snippet-variable table.

## 06.40-07

Companion guidance is an isolated `jacob-consulting/skills` checkout at `../skills-navbar-06-40`, with native validation and a separate local commit. A missing sibling is an unmet delivery gate, not an orchestrator failure.

Strengths: the plan verifies remote, tracked targets, and local instructions before editing, and forbids installed mirrors and publication.

Concerns: none.

Suggestions: none.

Risk: medium until the checkout and validator actually run. That is an execution prerequisite already specified, not a missing plan step.

## 06.40-08

Live viewport/keyboard evidence and the supported matrix are final gates. Browser cleanup and companion receipt are required before overall sign-off.

Strengths: the example session installs the project before pytest (`noxfile.py:209-213`). Django 4.2/Python 3.14+ skips are declared (`noxfile.py:205-207`). Task 01 owns server and temporary-path cleanup on success and failure.

Concerns: none.

Suggestions: none.

Risk: medium as an execution gate. Unavailable browser or matrix cells stay unmet. They are not passes.

## Cross-plan

R17 signed off. The revised plan binds `ViewContext.object` to the resolved owner, which is the value `get_meta` interpolates. Keeping `ViewContext.view` as the rendering view does not change that path.

R18 signed off. Owner links use `owner_viewset.pk_name` plus `owner.pk`. Child links use `child.parent.get_pk_name()` plus the same `owner.pk`.

R19 signed off. Cold vocabulary reset now includes `guardian.shortcuts.clear_ct_cache()` beside Django `ContentType` and ViewSet vocabulary caches.

R1–R16 were not reopened by those edits. Parent `attribute=` mappings, the locmem harness, registry barrier, snippet heading, own-example credentials, German catalog, migration check, and browser `finally` cleanup are still in the current tasks.

Unresolved HIGH: none.

Actionable non-HIGH plan gaps: none.

Future execution checks, not missing obligations: owner-label spy across depths; `COST.md` totals; 320px/200% reflow and possible scoped CSS; companion clone/validator/commit; Pydantic 2.2.1 floor; honest matrix skips.
