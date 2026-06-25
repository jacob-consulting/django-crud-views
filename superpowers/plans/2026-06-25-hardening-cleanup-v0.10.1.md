# Hardening & Cleanup v0.10.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a non-breaking v0.10.1 patch that hardens `ViewSet.default_permissions` codename parsing (#33) and records the `CrispyModelViewMixin` deprecation in the CHANGELOG (#34).

**Architecture:** One-line parsing fix (`str.split` → `str.removesuffix`) on `ViewSet.default_permissions`, guarded by a new regression test that constructs a throwaway ViewSet over an existing model carrying a custom permission whose codename embeds the model name. The #34 deprecation is communicated through the CHANGELOG only — no code change. A final release task bumps the version and follows the project's PR → merge → tag flow.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, Pydantic v2 (ViewSet is a `BaseModel`), pytest / pytest-django, ruff, bump-my-version, Taskfile (`task`).

**Spec:** `superpowers/specs/2026-06-25-hardening-cleanup-design.md`

## Global Constraints

- Python floor is **3.12+** — `str.removesuffix` (3.9+) is available; no compatibility shim needed.
- Line length **120**, **double quotes**, ruff-formatted (pre-commit runs `ruff-format`).
- All `CrudView`/ViewSet attributes use the `cv_` prefix; this change touches neither.
- Release flow (per project history): feature branch → PR → wait CI → fix ruff → squash-merge to `main` → wait main CI; version bump (`bump-my-version`) commits **and** tags `v{new_version}`.
- Quick test loop runs from `tests/`: `cd tests && pytest`. Full matrix is `task test` (nox; slow).
- This release is **non-breaking**: no public symbol is removed (the `CrispyModelViewMixin` alias stays).
- CHANGELOG is hand-maintained; the newest section sits at the top, currently `## 0.10.0`.

---

### Task 1: Harden `default_permissions` codename parsing (#33)

**Files:**
- Modify: `src/crud_views/lib/viewset/__init__.py:357-374` (the `default_permissions` cached_property)
- Test: `tests/test1/test_viewset.py` (append a new test; file already holds the permission-mapping tests)

**Interfaces:**
- Consumes: `crud_views.lib.viewset.ViewSet` (Pydantic `BaseModel`; constructor takes `model=<Model>, name=<str>`), the module-level registry `crud_views.lib.viewset._REGISTRY` (an `OrderedDict` keyed by ViewSet `name`), and `tests.test1.app.models.Book` (PK = `BigAutoField`, so `ContentType.objects.get_for_model(Book).model == "book"`).
- Produces: no new public symbol. `ViewSet.default_permissions` keeps its signature `-> OrderedDict[str, str]` (action key → `"<app_label>.<codename>"`); only the action-key derivation changes.

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_viewset.py`:

```python
@pytest.mark.django_db
def test_default_permissions_parses_action_containing_model_name():
    """Custom permission whose codename embeds the model name parses to the full action.

    Regression (#33): default_permissions split the codename on the first "_<model>"
    occurrence, so an action that itself contains the model name (e.g. "rebook_book" for
    model "book") was truncated to "re". It now strips "_<model>" as a suffix -> "rebook".
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from crud_views.lib.viewset import ViewSet, _REGISTRY
    from tests.test1.app.models import Book

    ct = ContentType.objects.get_for_model(Book)  # ct.model == "book"
    Permission.objects.create(content_type=ct, codename="rebook_book", name="Can rebook book")

    name = "book_perm_parsing_probe"
    viewset = ViewSet(model=Book, name=name)
    try:
        permissions = viewset.default_permissions
    finally:
        _REGISTRY.pop(name, None)  # keep the global registry clean for other tests

    assert "rebook" in permissions  # full action, not the truncated "re"
    assert "re" not in permissions
    assert permissions["rebook"] == f"{ct.app_label}.rebook_book"
    for action in ("add", "change", "delete", "view"):
        assert action in permissions  # standard actions still parse
```

Check that `tests/test1/test_viewset.py` already imports `pytest` and `from crud_views.lib.viewset import ViewSet`; the top of the file should read like:

```python
import pytest
from crud_views.lib.viewset import ViewSet
```

If `import pytest` is missing, add it at the top. (`_REGISTRY` is imported locally inside the test, so no top-level import is needed for it.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_viewset.py::test_default_permissions_parses_action_containing_model_name -v`
Expected: FAIL — `assert "rebook" in permissions` fails because the current `split("_book")[0]` yields `"re"` (so `"rebook"` is absent and `"re"` is present).

- [ ] **Step 3: Write the minimal implementation**

In `src/crud_views/lib/viewset/__init__.py`, replace the `default_permissions` property body. Change the docstring to add the cached/DB note, and replace the parsing line.

Find:

```python
    @cached_property
    def default_permissions(self) -> OrderedDict[str, str]:
        """
        Default permissions extracted from model
            - add
            - change
            - delete
            - view
            - ...
            - and custom permissions defined on model
        """
        model = self.model  # noqa
        content_type = ContentType.objects.get_for_model(model)
        permissions = OrderedDict()
        for permission in Permission.objects.filter(content_type=content_type):
            action = permission.codename.split(f"_{permission.content_type.model}")[0]
            permissions[action] = f"{permission.content_type.app_label}.{permission.codename}"
        return permissions
```

Replace with:

```python
    @cached_property
    def default_permissions(self) -> OrderedDict[str, str]:
        """
        Default permissions extracted from model
            - add
            - change
            - delete
            - view
            - ...
            - and custom permissions defined on model

        Note: this is a process-lifetime ``cached_property`` that performs database queries
        (a ``ContentType`` lookup and a ``Permission`` query). It is evaluated once per
        process and is not refreshed if permissions change at runtime.
        """
        model = self.model  # noqa
        content_type = ContentType.objects.get_for_model(model)
        permissions = OrderedDict()
        for permission in Permission.objects.filter(content_type=content_type):
            # Django codenames are "<action>_<model>"; the model name is always the suffix.
            # Strip it as a suffix (not split on the first match) so actions that themselves
            # contain the model name parse correctly, e.g. "rebook_book" -> "rebook".
            action = permission.codename.removesuffix(f"_{permission.content_type.model}")
            permissions[action] = f"{permission.content_type.app_label}.{permission.codename}"
        return permissions
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_viewset.py::test_default_permissions_parses_action_containing_model_name -v`
Expected: PASS.

- [ ] **Step 5: Run the surrounding suite to confirm no regression**

Run: `cd tests && pytest test1/test_viewset.py test1/test_permissions.py test1/test_permissions_full.py -q`
Expected: all pass (these exercise the permission mapping that `default_permissions` feeds).

- [ ] **Step 6: Lint**

Run: `task check && task format`
Expected: no errors; `default_permissions` body within 120-col, double quotes.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/viewset/__init__.py tests/test1/test_viewset.py
git commit -m "fix(viewset): strip model suffix in default_permissions codename parsing (#33)"
```

---

### Task 2: CHANGELOG 0.10.1 section (#33 + #34)

**Files:**
- Modify: `CHANGELOG.md` (insert a new `## 0.10.1` section above `## 0.10.0`)

**Interfaces:**
- Consumes: nothing in code. Documents Task 1's fix and the standing `CrispyModelViewMixin` deprecation.
- Produces: the release notes consumed by the version bump in Task 3.

- [ ] **Step 1: Insert the 0.10.1 section**

In `CHANGELOG.md`, immediately below the top `# Django CRUD Views - Changelog` heading and above `## 0.10.0`, insert:

```markdown
## 0.10.1

### Fixed

- `ViewSet.default_permissions` now derives each action key by stripping the trailing `_<model>` from the permission codename instead of splitting on its first occurrence. A custom permission whose action contains the model name (e.g. `rebook_book` on a `book` model) previously parsed to a truncated action (`re`); it now parses correctly (`rebook`). Standard `add`/`change`/`delete`/`view` permissions are unaffected.

### Deprecated

- `CrispyModelViewMixin` is deprecated in favor of `CrispyViewMixin` and will be removed in a future release. The two are identical; rename imports and base classes to `CrispyViewMixin`. The alias still works in this release.
```

- [ ] **Step 2: Verify the section renders and ordering is correct**

Run: `sed -n '1,20p' CHANGELOG.md`
Expected: `## 0.10.1` appears directly under the title and above `## 0.10.0`, with `### Fixed` then `### Deprecated`.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): add 0.10.1 section (#33 fix, #34 deprecation)"
```

---

### Task 3: Release — bump to 0.10.1 and follow the PR flow

**Files:**
- Modify (by `bump-my-version`): `pyproject.toml`, `src/crud_views/__init__.py`, `src/crud_views_plain/__init__.py`, `docs/index.md`, `README.md` (version string `0.10.0` → `0.10.1`).

**Interfaces:**
- Consumes: the merged Task 1 + Task 2 commits.
- Produces: a `v0.10.1` git tag (created by `bump-my-version`) that triggers the Publish CI on push.

> This task contains human-driven gates (waiting on CI, squash-merge). Do not bump the version until the code/CHANGELOG commits are on `main`, because `bump-my-version` tags the current commit.

- [ ] **Step 1: Confirm you are on a feature branch (not `main`)**

Run: `git branch --show-current`
Expected: a feature branch name (e.g. `fix/default-permissions-parsing`). If it prints `main`, create and switch first:

```bash
git switch -c fix/default-permissions-parsing
```

(If Task 1/2 were committed on `main` by mistake, move them onto a branch before pushing.)

- [ ] **Step 2: Push the branch and open the PR**

```bash
git push -u origin HEAD
gh pr create --base main --fill --title "Hardening & cleanup v0.10.1 (#33, #34)"
```

- [ ] **Step 3: Wait for PR CI and fix ruff if it flags anything**

Run: `gh pr checks --watch`
Expected: all checks green across Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0. If ruff fails, run `task check && task format`, commit, push, re-watch.

- [ ] **Step 4: Squash-merge to `main` and update local `main`**

```bash
gh pr merge --squash --delete-branch
git switch main && git pull
```

- [ ] **Step 5: Wait for main CI to go green**

Run: `gh run list --branch main --limit 1` then `gh run watch <run-id>`
Expected: main CI green before tagging.

- [ ] **Step 6: Bump the version (creates the commit + `v0.10.1` tag)**

Run: `task bump-patch`
Expected: `bump-my-version` rewrites the five version files `0.10.0` → `0.10.1`, creates a `Bump version: 0.10.0 → 0.10.1` commit, and tags `v0.10.1`. Verify:

```bash
git log --oneline -1 && git tag --list 'v0.10.1'
```

Expected: latest commit is the bump; tag `v0.10.1` exists.

- [ ] **Step 7: Push main and the tag to trigger Publish CI**

```bash
git push origin main --follow-tags
```

Expected: the `v0.10.1` tag push starts the Publish workflow.

- [ ] **Step 8: Confirm Publish CI succeeds**

Run: `gh run list --workflow Publish --limit 1` then `gh run watch <run-id>`
Expected: Publish workflow green; v0.10.1 released.

---

## Self-Review

**Spec coverage:**
- #33 parsing fix (`removesuffix`) + placement-stays-on-ViewSet + cached/DB docstring note → Task 1, Step 3. ✓
- #33 regression test (model-name-embedded codename; standard actions still parse) → Task 1, Step 1. ✓
- #34 CHANGELOG-only deprecation, alias kept, no runtime warning → Task 2, Step 1 (`### Deprecated`); no code touched. ✓
- v0.10.1 patch bump + `### Fixed`/`### Deprecated` headings + PR/merge/tag flow → Tasks 2 & 3. ✓
- Out-of-scope (#55, relocating `default_permissions`, alias removal, warning machinery) → none of these appear in any task. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to" placeholders; every code step shows complete code or exact commands. ✓

**Type consistency:** `ViewSet(model=..., name=...)`, `_REGISTRY` (`OrderedDict`, `.pop(name, None)`), and `default_permissions -> OrderedDict[str, str]` are used identically across Task 1's test and implementation. The test asserts the `"<app_label>.<codename>"` value shape that the implementation produces. ✓
