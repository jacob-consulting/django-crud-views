# Bulk Variants Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the review gaps of phase 06.47 before PR #402 merges: a `secondary` fallback for an unset bulk variant, removal of the frozen toolbar snapshot, and two documentation tidy-ups.

**Architecture:** One expression changes in `BulkSelectionMixin.cv_bulk_buttons`; everything else is tests, docs and planning records. The byte-compatibility guarantee moves fully onto the existing live comparison against the unchanged form leaf.

**Tech Stack:** Django templates, pytest with pytest-xdist, ruff, MkDocs, hatchling/uv.

**Spec:** `superpowers/specs/2026-11-22-bulk-variants-review-fixes-design.md`

## Global Constraints

- No new public name, setting, check ID or template field.
- Stock `bulk:danger` stays `btn btn-primary`.
- `src/crud_views/templates/crud_views/tags/button/bulk.html`, `form.html`, `action.html`, `FORM_LEAF_KEYS` and `tests/test1/test_bulk_source.py` are not edited.
- Commits land on `gsd/phase-06.47`. Do not push.
- Run commands from the repository root. Interpreter:
  `PY=/home/alex/projects/alex/django-crud-views/.nox/tests-3-12-django-6-0/bin/python`, always with
  `PYTHONPATH=src:.`. Docs and lint tools: `/home/alex/projects/alex/django-crud-views/.venv/bin/{mkdocs,ruff}`.
- Line length 120, double quotes. Commit messages end with
  `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`.

## Review Focus

- A destination that sets the enum member (`Variant.DANGER`) instead of the string: expect the `bulk:danger` class. Pinned in Task 1.
- An unset variant together with a mode key (`bulk:secondary:icon` in icon mode): expect the mode key to win, as for a declared `secondary`. Pinned in Task 1.
- An unknown non-empty string (`"bogus"`): expect an empty class, not a silent `secondary`. Pinned in Task 1.

---

### Task 1: Fall back to `secondary` for an unset bulk variant

**Files:**
- Modify: `src/crud_views/lib/bulk/__init__.py:123`
- Modify: `docs/reference/buttons.md:658` (the `cv_variant` row under "Bulk button leaf")
- Test: `tests/test1/test_bulk_variants.py`

- [ ] **Step 1: Write the failing tests** (append to `tests/test1/test_bulk_variants.py`; add `from crud_views.lib.view.variant import Variant` to the imports)

```python
@pytest.mark.parametrize("source", SOURCE_PATHS)
@pytest.mark.parametrize(
    "variant,expected",
    [(None, "theme-secondary"), ("", "theme-secondary"), (Variant.DANGER, "theme-danger"), ("bogus", "")],
)
def test_unset_variant_falls_back_to_secondary(
    client_user_bulk_publisher_view, settings, monkeypatch, source, variant, expected
):
    """None and "" mean secondary, as for action buttons; an unknown string has no class and is reported by E209."""
    monkeypatch.setattr(cv_bulk_publisher.get_view_class("archive"), "cv_action_variant", variant)
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"bulk:secondary": "theme-secondary", "bulk:danger": "theme-danger"}
    _, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]))
    assert button.get("class") == expected


@pytest.mark.parametrize("source", SOURCE_PATHS)
def test_unset_variant_honours_mode_key(client_user_bulk_publisher_view, settings, monkeypatch, source):
    destination = cv_bulk_publisher.get_view_class("archive")
    monkeypatch.setattr(destination, "cv_action_variant", None)
    monkeypatch.setattr(destination, "cv_icon_action", "delete")
    settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"bulk": "icon"}
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"bulk:secondary": "base", "bulk:secondary:icon": "icon-only"}
    _, button = _archive_control(client_user_bulk_publisher_view.get(SOURCE_PATHS[source]))
    assert button.get("class") == "icon-only"
```

- [ ] **Step 2: Run to verify the failures**

Run: `PYTHONPATH=src:. $PY -m pytest tests/test1/test_bulk_variants.py -k "unset_variant" -q -p no:cacheprovider`
Expected: 6 failed (`None` and `""` on both sources, both mode-key cases, each with `'' == ...`), 4 passed (`Variant.DANGER`, `"bogus"`).

- [ ] **Step 3: Implement**

In `cv_bulk_buttons` replace `data["cv_variant"] = destination.cv_action_variant` with
`data["cv_variant"] = destination.cv_action_variant or "secondary"`.

- [ ] **Step 4: Run to verify they pass**

Run: `PYTHONPATH=src:. $PY -m pytest tests/test1/test_bulk_variants.py tests/test1/test_bulk_source.py -n 6 -q -p no:cacheprovider`
Expected: all pass, 0 failed.

- [ ] **Step 5: Document**

Replace the `cv_variant` row at `docs/reference/buttons.md:658` with:

```markdown
| `cv_variant` | Destination semantic variant: primary, secondary, tertiary or danger. An unset variant (`None` or `""`) arrives as secondary; any other value is passed through, resolves to no class and is reported by `viewset.E209`. |
```

Run: `PYTHONPATH=src:. $PY -m pytest tests/test1/test_bulk_docs.py tests/test1/test_theme_adoption_docs.py -n 6 -q -p no:cacheprovider`
Expected: all pass (the nine-field table check reads only the first column).

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/bulk/__init__.py tests/test1/test_bulk_variants.py docs/reference/buttons.md
git commit -m "fix(06.47): fall back to secondary for an unset bulk variant"
```

---

### Task 2: Remove the frozen toolbar snapshot

**Files:**
- Delete: `tests/test1/fixtures/bulk_toolbar_pre_variant.json` (the `fixtures/` directory then disappears from git; nothing else reads it)
- Modify: `tests/test1/test_bulk_variants.py` (remove `test_stock_toolbar_bytes`, `SNAPSHOT`, `import json`, `from pathlib import Path`; module docstring becomes `"""Bulk semantic styling, compared byte for byte with the unchanged form leaf."""`)
- Modify: `.planning/codebase/CONVENTIONS.md:163`, `.planning/codebase/TESTING.md:169`, `.planning/codebase/STRUCTURE.md:244`
- Modify: `.planning/phases/06.47-semantic-variants-for-bulk-toolbar-buttons-400/06.47-VERIFICATION.md`, `06.47-VALIDATION.md`, `06.47-01-SUMMARY.md`

- [ ] **Step 1: Confirm the surviving comparison covers the same matrix**

Run: `PYTHONPATH=src:. $PY -m pytest tests/test1/test_bulk_variants.py -k "matches_form_leaf" -q -p no:cacheprovider`
Expected: 24 passed.

- [ ] **Step 2: Delete the fixture and the snapshot test**

`git rm tests/test1/fixtures/bulk_toolbar_pre_variant.json`, then remove the items listed under Files. Keep
`raw_bulk_controls`, `_stock_response`, `MODES`, `ICON_CASES` and `SOURCE_PATHS`; other tests use them.

- [ ] **Step 3: Verify nothing dangles**

Run: `grep -rn "bulk_toolbar_pre_variant\|test_stock_toolbar_bytes\|SNAPSHOT" src tests docs examples noxfile.py`
Expected: no output.

Run: `PYTHONPATH=src:. $PY -m pytest tests/test1/test_bulk_variants.py tests/test1/test_bulk_docs.py -n 6 -q -p no:cacheprovider`
Expected: all pass. `ruff check tests/test1/test_bulk_variants.py` reports no unused import.

- [ ] **Step 4: Update the codebase maps**

Rewrite the three listed lines so each names `test_stock_toolbar_matches_form_leaf` as the guard: it renders the
unchanged form leaf from each real normalized payload and compares it byte for byte, terminal newline and signed
URL included, with the source page and with the bulk leaf across 24 source/mode/icon cases. Remove every mention
of an immutable fixture and of a capture policy.

- [ ] **Step 5: Annotate the phase 06.47 records**

Add this note, unchanged, directly below the frontmatter of `06.47-VERIFICATION.md`, below the D-01 row's table
in `06.47-VALIDATION.md`, and at the end of `06.47-01-SUMMARY.md`. Do not edit or delete existing text.

```markdown
> **Amendment (2026-11-22):** The frozen capture `tests/test1/fixtures/bulk_toolbar_pre_variant.json` and
> `test_stock_toolbar_bytes` were removed after the phase review, by maintainer decision. They proved the renderer
> switch changed no bytes; that proof remains in git history (capture `7108fa87`, switch `7b50b6b8`).
> `test_stock_toolbar_matches_form_leaf` keeps guarding the same 24 cases against the unchanged form leaf. See
> `superpowers/specs/2026-11-22-bulk-variants-review-fixes-design.md`. Statements about the capture in this
> document are historical.
```

- [ ] **Step 6: Commit**

```bash
git add -A tests/test1 .planning/codebase .planning/phases/06.47-semantic-variants-for-bulk-toolbar-buttons-400
git commit -m "test(06.47): drop frozen toolbar snapshot, keep form-leaf comparison"
```

---

### Task 3: Tidy two documentation passages

**Files:**
- Modify: `docs/development/stability.md:81-85`
- Modify: `docs/reference/buttons.md:198-201`

- [ ] **Step 1: Fix the override list in `stability.md`**

The list of override templates must read "..., `crud_views/snippets/bulk/blocked.html`,
`crud_views/snippets/bulk/eligible.html` and `crud_views/tags/button/bulk.html`." (one "and"), wrapped at 120
characters. Every template path and the sentence "The two review snippets receive `bulk_review` with `objects`
and `blocked`" stay verbatim.

- [ ] **Step 2: Rewrap the key-count paragraph in `buttons.md`**

Rewrap the paragraph containing "bulk selection contributes eleven keys" at 120 characters. Change no word.

- [ ] **Step 3: Verify**

Run: `git diff -U0 docs | grep '^+' | awk 'length($0) > 121 && $0 !~ /^\+\|/ && $0 !~ /cv_button_class/'`
Expected: no output.

Run: `PYTHONPATH=src:. $PY -m pytest tests/test1/test_bulk_docs.py tests/test1/test_theme_adoption_docs.py -n 6 -q -p no:cacheprovider`
Expected: all pass.

Run: `PYTHONPATH=src:. /home/alex/projects/alex/django-crud-views/.venv/bin/python -m mkdocs build --strict -d "$SCRATCH/site"`
Expected: exit 0, no warnings. (`$SCRATCH` is a directory outside the repository.)

- [ ] **Step 4: Commit**

```bash
git add docs/development/stability.md docs/reference/buttons.md
git commit -m "docs(06.47): rewrap bulk inventory passages"
```

---

### Task 4: Final verification

No files change in this task.

- [ ] **Step 1: Full suite**

Run: `PYTHONPATH=src:. $PY -m pytest tests/test1 -n 8 -q -p no:cacheprovider`
Expected: 0 failed. The count is 17,377 minus the 24 removed snapshot cases plus the 10 new cases.

- [ ] **Step 2: Lint**

Run: `ruff format --check . && ruff check .` (ruff from the `.venv` above)
Expected: exit 0.

- [ ] **Step 3: Distribution contents**

Run: `uv build --out-dir "$SCRATCH/dist"` then
`python scripts/check_dist.py "$SCRATCH/dist"`.
Expected: `check_dist.py` exits 0; the wheel lists `crud_views/templates/crud_views/tags/button/bulk.html` and the
sdist lists `src/crud_views/templates/crud_views/tags/button/bulk.html`; neither lists
`bulk_toolbar_pre_variant.json`.

- [ ] **Step 4: Report**

State the three results with their numbers. The digest in `06.47-VERIFICATION.md` is now stale; refreshing the
phase verification and pushing to PR #402 are the maintainer's steps.
