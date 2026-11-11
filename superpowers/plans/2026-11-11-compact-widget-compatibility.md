# Compact Widget Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let developers explicitly opt custom widget families into compact formsets through a marker mixin.

**Architecture:** Add one empty public mixin and bypass only widget-specific validation for marked instances.
Keep the existing stock path and shared schema validation. Rendering continues through the current crispy helper.

**Tech Stack:** Python, Django forms, django-crispy-forms, crispy-bootstrap5, pytest/pytest-django/xdist.

**Spec:** [Compact widget compatibility](../specs/2026-11-11-compact-widget-compatibility-design.md).

## Global Constraints

**Decision status:** the [GSD handover in the design](../specs/2026-11-11-compact-widget-compatibility-design.md#gsd-handover)
records approved decisions D-01–D-05. O-01 was resolved by explicit maintainer approval on 2026-11-11;
no behavior decisions remain open. This plan is ready as input to GSD planning; implementation has not started.

- No registry, adapter framework, HTML inspection, dependency additions or rendering lifecycle changes.
- Metadata inspection must not render widgets or evaluate choices.
- Classic formsets retain their existing path.
- Built-in CheckboxInput support is a separate issue.
- This is additive; document it under Unreleased without a new Breaking entry.
- Follow the repository's 120-character Python line limit and double quotes; use bounded multicore broad tests.

## Review Focus

- Custom non-Select templates: opt-in must not accidentally retain the Select-only restrictions (task 1).
- Marker inheritance: descendants inherit the promise through ordinary isinstance semantics (task 1).
- Hidden/identity fields and inconsistent rows: marker cannot bypass schema validation (task 1).
- Metadata-only and zero-total forms: admission adds no rendering or choice evaluation (task 1).
- Invalid POST and added/deleted row fragments: option metadata and label/error ownership survive (task 1).

## Task 1: Add the marker and verify its admission boundary

**Files:** Modify `src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/formsets/__init__.py`,
and `tests/test1/test_formsets_compact.py`.

**Interfaces:** Produces public `CompactWidgetCompatible`, an empty mixin with a contract docstring.
Consumes the existing `_compact_schema(form, declaration)` and test `_runtime()` helpers; no signature changes.

- [ ] Extend the existing compact tests with failing cases:
  - Public import resolves to the class in `compact.py`; a descendant of a marked widget is also accepted.
  - Marked Select overriding `create_option()` retains `data-beans="1"` in rendered options. Assert shared
    headings, per-row label association and compact label class, help and owned validation errors.
  - Marked Textarea renders successfully, proving this is not a Select-only extension.
  - A marked TextInput with a locmem custom widget template renders that template and preserves its input ID.
  - Parameterize marked equivalents of the current widget rejection matrix: schema admission permits
    changed templates, input types and selection behavior. This asserts admission, not visual certification.
  - Preserve the complete existing unmarked rejection matrix and exact-stock attribute tests.
  - Marked hidden/identity/control fields, blank labels, missing columns and nonuniform rows still fail
    with the existing formset/field context. Marker inheritance must not relax exact row type consistency.
  - Extend existing no-query/zero-total coverage with a marked widget whose render and choice iteration
    fail if called during metadata projection; headings still succeed without extra metadata queries.
  - Exercise a marked Select in the existing authorized add/delete fragment and invalid POST fixtures;
    verify option attributes, current prefixes, associated labels, owned errors and no duplicate headings.
- [ ] Run the focused file and confirm failures concern the missing API/behavior:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test1/test_formsets_compact.py -n 4 -q`.
- [ ] Define and export the marker. In `_compact_schema`, guard the existing widget-specific validation
  block with `not isinstance(widget, CompactWidgetCompatible)`. Keep shared validation outside that guard;
  retain `_CompactHeading.widget_type` as the actual widget type. Do not add renderer or CSS changes.
- [ ] Re-run the focused file; expect all tests to pass. Review that admission does not imply output validation.
- [ ] Commit only the implementation and tests: `feat: allow explicit compact widget compatibility (#349)`.

## Task 2: Publish the developer contract and validate integration

**Files:** Modify `docs/reference/formsets.md`, `tests/test1/test_formsets_compact_docs.py`, and `CHANGELOG.md`.

**Interfaces:** Consumes public `CompactWidgetCompatible` from task 1. Produces a runnable opt-in recipe and
documentation distinguishing package-supported stock widgets from developer-declared compatibility.

- [ ] Add `test_published_compact_widget_recipe_preserves_option_attributes` using the existing documentation
  extraction pattern. Execute a new dedicated Python fence and render its marked Select through compact
  forms; assert a `data-beans` attribute survives and the public import is used.
- [ ] Run that single test serially (tiny selection); confirm the missing recipe causes failure.
- [ ] Update the supported-widget section with the stock and explicit-opt-in paths. Include a self-contained
  Select example whose `create_option()` calls super and marks a known choice value. Explain that any widget
  family can opt in, custom templates are allowed, descendants inherit the promise, schema checks remain,
  and the marker does not validate or fix HTML/CSS/JavaScript. Document responsive/accessibility/error/fragment
  responsibilities and the checkbox label caveat. Add the marker to the public API inventory.
- [ ] Add an additive Unreleased changelog entry linking #349. Do not change historical phase artifacts.
- [ ] Run focused documentation and compact checks:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test1/test_formsets_compact.py tests/test1/test_formsets_compact_docs.py -n 4 -q`.
- [ ] Run `PYTHONPATH=src .venv/bin/python -m pytest tests -n 4 -q` and ruff check/format-check on the changed
  Python files. Expect passing tests and no new lint/format failures; distinguish any baseline failures.
- [ ] Inspect the rendered marked Select at desktop and mobile widths using the existing browser fixture
  or downstream ProductSelect: heading/label visibility, keyboard focus, field errors and added rows.
  Record actual observations; schema admission alone is not evidence of visual compatibility.
- [ ] Commit docs/tests/changelog: `docs: explain custom compact widget opt-in (#349)`.

## Planning handoff

Only planning and the issue update are authorized in this task. No product implementation or checkbox issue
creation is included. The issue body carries the scope and acceptance criteria so it remains usable without
these local planning files. Execution should use an isolated branch/worktree and the repository's checks.
