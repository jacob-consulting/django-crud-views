I'll verify the revised plans against source and the R1–R16 ledgers, starting with HEAD and the mechanisms those findings depend on.
Reviewed revised plans at `0ed46a40` against this checkout. `django-crud-view-components` is not on this machine; cited mechanisms are in `django-crud-views`. R1–R16 are closed in the task text. No new plan-blocking gap.

## 06.40-01

**Summary.** The opt-in module, literal routes, and startup checks match the existing registry and ancestor machinery. R1, R7–R11, R13, and R14 are specified in tasks 01 and 03, not left as ledger claims.

**Strengths.**
- Literal registration before `get_view_class` / `get_router_name` is required: both rewrite a missing `list` to `card` (`src/crud_views/lib/viewset/__init__.py:375-388`).
- Owner identity can reuse `_resolved_ancestor` without a query (`src/crud_views/lib/ancestors.py:576-585`). The active child is the node that owns the edge whose ancestor is the navbar owner; `_walk_ancestors` yields `(edge, ancestor)` nearest-first (`src/crud_views/lib/ancestors.py:89-121`).
- Short-label defaults are `mark_safe` snippet output (`src/crud_views/lib/view/base.py:578-592,638-643`). One `html.unescape`, then `str.__str__`, then template autoescape is the right split from raw captions.
- Registry-dependent checks can call `_url_configuration_loaded()` (`src/crud_views/checks.py:172-195`); `check_viewsets` itself has no barrier (`src/crud_views/checks.py:38-47`). `ViewSet.checks` already yields `view.checks()` (`src/crud_views/lib/viewset/__init__.py:286-287`).
- `cv_object` defaults true (`src/crud_views/lib/view/base.py:123`) and is false on list, card, and create (`src/crud_views/lib/views/list.py:26`, `card.py:24`, `create.py:17`). A capability check covers custom no-object pages. `ActionView` defines only `post` (`src/crud_views/lib/views/action.py:12-23`).
- `cv_extends_template` is the real placement hook (`src/crud_views/lib/view/base.py:426-431`). The shared test base has no navbar tag (`tests/test1/app/templates/app/crud_views.html:7-11`).

**Concerns.** None that need a plan edit.

**Suggestions.** Assert the stock short label `Detail` (`src/crud_views/templates/crud_views/snippets/action_short/detail.html:3`) or an explicit fixture override. Do not change that snippet to satisfy the word "Details". Reuse task 01's preimport-before-snapshot helper in `test_navbar_checks.py`; `tests/test1/test_ancestor_authorization.py:38` exists because a late URLconf import repopulates the registry.

**Risk Assessment:** LOW.

## 06.40-02

**Summary.** Lazy leaves, override modes, and the German landmark are executable. R1's consumer side and R15 are in task 02.

**Strengths.**
- Breadcrumb context is eager (`src/crud_views/lib/breadcrumb.py:280-283`); manage already uses `SimpleLazyObject`. A context-taking tag is required because `cv_breadcrumb` is a fixed inclusion tag (`src/crud_views/templatetags/crud_views.py:446-449`).
- `render_icon("")` can omit an icon (`src/crud_views/lib/icons.py:203-214`). Host placement is inside `render_icon`, not a `navbar:icon-host` class key (`src/crud_views/lib/icons.py:229-231`).
- `test_no_empty_or_fuzzy_msgstr` only inspects entries already in the `.po` (`tests/test1/test_i18n.py:65-73`). Owning `django.po` / `django.mo` and asserting `Abschnitte für` is the missing gate. `polib` is a test extra (`pyproject.toml:81`).

**Concerns.** None.

**Suggestions.** Build the landmark with `blocktranslate` so `%(object)s` interpolates. `{% translate %}` will not. Use `{% cv_icon %}`, not `{% cv_icon_class "navbar" %}`.

**Risk Assessment:** LOW.

## 06.40-03

**Summary.** Access-before-state and measured preservation match the existing hooks. R7 and R9's cold-cache half are in task 02.

**Strengths.**
- Child admission is one `_cv_child_link_has_access(user, parent_obj)` (`src/crud_views/lib/view/base.py:528-541`). State is a separate adapter (`src/crud_views/lib/view/base.py:564-566`). Context buttons do the opposite order (`src/crud_views/lib/view/buttons.py:237-243`).
- A dispatched request already stores `_cv_ancestor_state` (`src/crud_views/lib/ancestors.py:566`). Create-state only calls `get_object_or_404` when that state is missing (`src/crud_views/lib/views/create.py:52-75`), so cost tests must be real guarded requests.
- `ViewSet._default_permissions` is a separate cache from `_VOCAB_CACHE` (`src/crud_views/lib/viewset/__init__.py:489-490`).

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment:** LOW.

## 06.40-04

**Summary.** The Tenant/Customer slice is registrable and the migration gate is now a failing command. R2 and R16 are closed for this slice.

**Strengths.**
- `ParentViewSet.get_attribute()` defaults to the parent ViewSet name (`src/crud_views/lib/viewset/parentviewset.py:62-66`). `attribute="tenant"` is required for `navbar_tenant`. `conditional` already owns `name="customer"` (`examples/bootstrap5/conditional/views.py:272`).
- Guardian Tenant policy matches `examples/bootstrap5/guardian_demo/views.py:21-28`. Ancestor lookup uses the ViewSet queryset, then the permission gate (`src/crud_views/lib/ancestors.py:440-450,562-563`).
- Example Nox installs the project before pytest (`noxfile.py:209-213`). Task 02's `makemigrations --check --dry-run` is outside pytest.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment:** LOW.

## 06.40-05

**Summary.** The full example, seed, landing, and shared-test ownership close R2–R4 and R6. Shared notices stay unchanged, which matches the approved own-example path.

**Strengths.**
- Order and Address need `attribute="customer"`; Item needs `attribute="order"` (`src/crud_views/lib/viewset/parentviewset.py:62-66`).
- `FeatureGroupsTest.test_grouping_matches_spec` is an exact ordered list (`examples/bootstrap5/project/tests.py:457-477`). Owning that file is required.
- Landing contracts are `example_about`, breadcrumb, and `snippet_panels` (`examples/bootstrap5/project/tests.py:75-81,238-247,278-284,394-403`). `ThemeIndexView` is the standalone pattern (`examples/bootstrap5/theming/views.py:21-34`). `_feature_for` keys off the view module's first package component (`examples/bootstrap5/project/templatetags/example_tags.py:72-77`), so the view must live in `navbar_demo`.
- Account notices are hardcoded and require `developer/developer` last (`examples/bootstrap5/test_i18n.py:185-200`; `examples/bootstrap5/project/templates/registration/login.html` and `project/home.html`). `DEMO_USERS` does not render them (`examples/bootstrap5/project/seeding.py:5-10`). The seed stdout check is membership, not exact text (`examples/bootstrap5/test_i18n.py:213-216`).
- A chain-consistent copied URL resolves the Tenant, then `PermissionDenied` (`src/crud_views/lib/ancestors.py:440-450,562-563`). A mismatched chain can 404. Do not change that lookup.

**Concerns.** None requiring a plan edit. Research already separates those two statuses.

**Suggestions.** Assert 403 for a consistent copied Item/Address URL and unchanged rows after denied POST. Assert 404 only for a broken chain.

**Risk Assessment:** LOW.

## 06.40-06

**Summary.** Docs, stability inventory, and reciprocal links are downstream of the example. R3–R6 and R15 are closed by running the full shared suite and isolating the snippet table.

**Strengths.**
- `test_snippet_docs` takes `## Snippet variables` through the next level-two heading and requires eight names (`tests/test1/test_snippet_docs.py:27-36`). A separate `## Object navbar context` before that heading is the safe edit. The section currently ends the file (`docs/reference/templates.md:161`).
- Backlinks are `DEMO_BASE + reverse(feature.url_name)` inside an example admonition (`examples/bootstrap5/test_doc_links.py:139-146`). `/object-navbar/` matches a `""` landing under that include.
- MkDocs `nav` is commented, so no nav edit is required.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment:** LOW.

## 06.40-07

**Summary.** Companion delivery remains a separate local checkout and commit. The prior sandbox HIGH does not apply here: this runner can read sibling paths, and the plan already treats a failed clone as unmet.

**Strengths.**
- `docs/development/index.md` points at the external skills repository. The four targets are named. No installed mirror is a source.
- The checkout is absent at `../skills-navbar-06-40`, which task 01 treats as an acquisition target, not an existing file.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment:** LOW. Residual risk is remote access at execution time, already an unmet gate.

## 06.40-08

**Summary.** Browser cleanup and the matrix ledger close R12. Installed-package and skip handling match Nox.

**Strengths.**
- Task 01 now owns the server and temporary paths across success, assertion failure, and interruption. A JavaScript `finally` cannot reap that process.
- `tests` clears `PYTHONPATH` and passes posargs after `-n auto` (`noxfile.py:30-45`). Django 4.2 on Python 3.14/3.15 is `session.skip` (`noxfile.py:23-25`). `examples` installs `.[all,test,examples]` before pytest (`noxfile.py:209-213`).
- `scripts/check_dist.py:32-38` allowlists whole packages, so new templates and `.mo` files under `crud_views` need no allowlist edit.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment:** LOW. Browser and interpreter availability stay explicit unmet gates, not passes.

## Cross-plan

Wave order and file ownership hold. Plans 03 and 04 still share no files. Plan 05 edits `project/tests.py` and `features.py` before plan 06 extends `features.py` and runs the unfiltered shared suite. Plans 07 and 08 stay disjoint; overall sign-off still waits for the companion receipt.

R1–R16 do not remain. The revisions name the actual mechanisms: snippet unescape versus raw text, explicit `ParentViewSet.attribute`, shared feature tests, ThemeIndexView composition, a separate snippet heading, own-example credentials, a locmem `cv_extends_template` harness, the URLconf barrier, cache reset, `CheckTemplate` semantics, late-bound strings, `cv_object is False`, German `.po`/`.mo`, migration `--check`, and browser `finally` cleanup. Rejected items in the ledgers (shared-notice rewrite, byte-parity relaxation, companion cwd workaround, stale installed example) still disagree with source and should stay rejected.

No further plan edit is required before execution.
