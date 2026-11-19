I'll verify R20 against the live check and resolver code, then review each plan against source.
The mutation hazard is in the live `_views` iterator. I'll check Django's resolver cache and every caller of the readiness helper.
R20’s preflight depends on check entry points and existing tests. I’ll trace those next, then spot-check the other plans.
R20 is closed at planning level. R1–R19 stay closed. No new required plan change.

## 06.40-01

The opt-in module, literal destinations, and startup ordering match the live check path. R20 is closed here.

**Strengths**
- `ViewSet.checks` iterates `self._views.values()` live (`src/crud_views/lib/viewset/__init__.py:286-287`), while `checks_all` snapshots only the registry (`:225-232`). Completing URLconf inside `check_viewsets` before that snapshot (`src/crud_views/checks.py:39-47`) stops the import from mutating an active iterator.
- `URLResolver.url_patterns` is a `cached_property` on Django 4.2, 5.2, and 6.0. The cache is written to `__dict__` only after success (`django/utils/functional.py:47` / 4.2 `:57`). A presence check, not truthiness, correctly treats a cached empty list as complete and an uncached include as not ready. `get_resolver()` does not import (`django/urls/resolvers.py:108-116`).
- Default `load=True` keeps `check_ancestor_declarations` (`checks.py:209`) and `cv_manage_view.py:39` unchanged. Navbar checks using only `load=False` cannot retry a failed import during iteration.
- The cold fixture (late views on an existing ViewSet and a new ViewSet, first `check_viewsets` result, then `run_checks`) is the right regression. A no-exception assertion is explicitly insufficient.

**Concerns**
- None newly actionable.

**Suggestions**
- Keep the Task 01 “Details” item an explicit label. The stock short label is `Detail` (`snippets/action_short/detail.html:3`).

**Risk:** LOW. The mutation hazard is ordered out, and the tests lock the cache contract.

## 06.40-02

Lazy shared context, three guarded leaves, and the German landmark are executable and bounded.

**Strengths**
- One view-local `SimpleLazyObject`, modal `X-CV-Modal: true` (`base.py:71-73`), and empty output when no items remain match D-08/D-11.
- `django.po` / `django.mo` exist. The German assertion is a literal `aria-label`, so an English fallback cannot pass.
- Escaping consumes Plan 01’s plain strings once. `render_snippet` already strips and marks safe (`base.py:591-592`); the plan does not decode raw captions.

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk:** LOW.

## 06.40-03

Admission order and cost measurement reuse the existing hooks without rewriting them.

**Strengths**
- Child admission is exactly `_cv_child_link_has_access(user, parent_obj)` (`base.py:528-541`). Guardian create already applies the parent gate and overrides that hook (`guardian/lib/views.py:377-389`), so a second parent call would be wrong.
- `clear_ct_cache` is the cold reset used by `reset_discovery` (`test_guardian_child_link_visibility.py:1052-1057`). Plan 03 names it separately from Django’s content-type cache.
- Real GET 403/200 cases keep visibility distinct from request authority.

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk:** LOW.

## 06.40-04

The Tenant/Customer slice uses existing Guardian and parent-edge APIs.

**Strengths**
- `AncestorPolicy(provider="guardian", accept_global_perms=False)` matches `guardian_demo/views.py:21-27`. `cascade` defaults to the global `True` (`ancestor_policy.py:19-22,57`).
- `ParentViewSet(name=..., attribute=...)` is the real FK seam (`parentviewset.py:13-18,62-66`). Prefixed ViewSet names must not be inferred as field names.
- Example Nox installs dependencies and changes to `examples/bootstrap5` (`noxfile.py:202-213`). The separate `makemigrations --check` cannot be masked by pytest.

**Concerns**
- None newly actionable.

**Suggestions**
- Make the landing path `""` under `object-navbar/` so `reverse("navbar-demo-home")` equals the URL Plan 06 hardcodes. Plan 06’s backlink test will fail otherwise.

**Risk:** LOW.

## 06.40-05

The full hierarchy, grants, and index placement follow existing example contracts.

**Strengths**
- `FeatureGroupsTest.test_grouping_matches_spec` requires an exact `ui` app list ending in `theming` (`project/tests.py:457-474`). Adding `navbar_demo` at the end is the required edit.
- `ThemeIndexView` is the landing analog: `BreadcrumbMixin`, `LoginRequiredMixin`, `TemplateView`, `cv_breadcrumb_get`, `example_about`, `snippet_panels` (`theming/views.py:21-31`, `theming/index.html:1-39`).
- `DEMO_USERS` does not render shared notices (`seeding.py:5-10`). Charlie belongs in the example intro and `seed.py:17`, not in those catalogs.
- Descendant `ParentViewSet(..., attribute="customer"|"order")` is required; `get_attribute()` would otherwise use the ViewSet name (`parentviewset.py:66`).

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk:** LOW.

## 06.40-06

Documentation, stability inventory, and reciprocal links are tied to existing checkers.

**Strengths**
- `test_doc_links.py:139-147` requires `DEMO_BASE + reverse(feature.url_name)` inside the example admonition. The planned `/object-navbar/` URL is testable, not decorative.
- `## Snippet variables` is a level-two heading with an eight-row table (`templates.md:161-181`). A separate navbar heading avoids that schema.
- `#nav:` is commented (`mkdocs.yml:3`). `mkdocs build --strict` is the right gate.

**Concerns**
- None that require a plan change. `docs/reference/.pages:26-32` is an explicit awesome-pages list, so a new file will not appear in the sidebar unless added. `validation.nav.omitted_files` defaults to `info`, so strict build will not fail. `buttons.md` is already index-linked and absent from that sidebar.

**Suggestions**
- Optional: add `navbar.md` under Actions & navigation in `docs/reference/.pages`. Not required for AC9 if the reference index entry lands.

**Risk:** LOW.

## 06.40-07

Companion delivery stays outside this repo and is not treated as publication.

**Strengths**
- Targets match `06.40-COMPANION-GUIDANCE.md`. Acquisition, `git ls-files`, native `scripts/validate.py`, and a separate local commit are explicit.
- A missing checkout remains unmet. Installed mirrors are excluded.

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk:** LOW. Delivery still depends on reaching `jacob-consulting/skills` at execution time.

## 06.40-08

Browser cleanup and the matrix commands match the real Nox sessions.

**Strengths**
- `tests` clears `PYTHONPATH` and asserts installed origin (`noxfile.py:7-16,30-31`). Django 4.2 on Python 3.14/3.15 is an explicit skip (`:23-25`).
- `manage_report_floor` appends posargs after its own tests and asserts Pydantic 2.2.1 (`noxfile.py:88-106`). The command lists all six navbar modules, including `test_navbar_docs.py`.
- `examples` forwards posargs from `examples/bootstrap5` (`:212-213`). Isolated SQLite plus `finally` cleanup is the right browser boundary.
- The prose “six modules plus documentation” disagrees with that command, but the command is the one that runs. No test is omitted.

**Concerns**
- None newly actionable.

**Suggestions**
- Align the Task 02 sentence with the six-file command. No extra module is missing.

**Risk:** LOW. AC8 still needs a real browser at execution; the plan already treats a missing browser as unmet.

## Cross-plan

R20 is closed. The preflight is before both the registry snapshot and the live `_views` iterator. Navbar checks cannot import during that iterator. Cold, failed, empty-cache, and unloaded-include cases are owned by `06.40-01-03` and rerun by the matrix.

R1–R19 remain closed. Owner labels, `pk_name` versus `owner.pk`, Guardian content-type reset, byte parity, parent attributes, feature membership, landing composition, credential copy, snippet heading, German catalog, migration drift, and browser cleanup still have executable owners. No new source evidence reopens them.

No concrete missing obligation. Optional only: sidebar `.pages` entry, empty landing path spelled in Plan 04, and the Plan 08 count sentence.
