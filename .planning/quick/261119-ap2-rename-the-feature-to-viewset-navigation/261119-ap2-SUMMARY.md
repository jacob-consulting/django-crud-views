---
quick_id: 261119-ap2
status: complete
date: 2026-11-19
commit: 39821bca
---

# ViewSet Navigation naming

Renamed the feature to **ViewSet Navigation** throughout the reference and related documentation,
live-demo guide, changelog, example feature registry, landing heading, breadcrumb and entry buttons.
The reference introduction explains that navigation connects an object's views and child ViewSets.
Updated existing documentation and demo assertions to match.

Public API symbols, templates, module names and the `/object-navbar/` route remain unchanged.
Newly named documentation headings retain explicit historical anchors; internal links use the new anchors.

## Verification

- `.nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_navbar_docs.py -n 4 -q`:
  **8 passed**.
- From `examples/bootstrap5`, `../../.nox/examples-3-12-django-5-2/bin/python -m pytest navbar_demo/tests.py project/tests.py -n 4 -q`:
  **102 passed, 75 subtests passed**. Existing Django URL-scheme deprecation and unordered pagination warnings.
- Strict MkDocs build: passed, output outside the repository under `/tmp`.
- Parsed generated documentation: all three new heading IDs and all three historical anchors exist.
- Scoped Ruff lint and format checks plus `git diff --check`: passed.
- Remaining old feature wording in docs/examples is limited to retained URLs and anchor IDs.

## Workflow

Executed inline using the skill's inline fallback. User explicitly requested staying on the current
`gsd/phase-06.40-object-navbar-opt-in-section-navigation-381` branch for shipment with this phase.
No new branch/worktree or phase transition; ROADMAP.md and unrelated untracked work are untouched.
Product commit: `39821bca`.
