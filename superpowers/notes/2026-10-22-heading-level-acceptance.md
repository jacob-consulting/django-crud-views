# Acceptance — configurable heading level via `CRUD_VIEWS_HEADER_LEVEL` (#251)

Spec: `superpowers/specs/2026-10-22-heading-level-design.md`. Plan: `superpowers/plans/2026-10-22-heading-level.md`.

## Change

- `CrudViewsSettings.header_level` (`CRUD_VIEWS_HEADER_LEVEL`, default `None`), check `crud_views.E107` for anything
  but `None` or an int 1–5.
- `{% cv_heading ["header"] level=N [class=…] %}…{% endcv_heading %}` in `crud_views/templatetags/crud_views.py`.
- The card, modal, both workflow sections and all seven object-detail group templates use it.
- Example: the view title is `{% cv_heading "header" level=1 class="h3 mb-0" %}`, `CRUD_VIEWS_HEADER_LEVEL = 1`, and
  the stray headings on the home page, the "about" box and the snippet panels fit the outline.

## Acceptance

| Criterion (spec) | Evidence |
| --- | --- |
| Unset: every inventory template renders what it renders today, accordion `h2` included | `tests/test1/golden/heading_level/` captured from the templates on `main` before the change (card, workflow, modal_detail, 7 od layouts); `test_heading_golden_default`. Raw renders of all 10 surfaces diffed against `main`'s templates: identical except per-request CSRF tokens. No existing golden changed |
| Set: inventory headings render at `header_level + 1`, accordion included | `test_card_title_follows_setting`, `test_workflow_sections_follow_setting`, `test_od_group_heading_follows_setting`, `test_od_accordion_header_follows_setting`, each at 1 and 2 |
| The look stays: `h{level}` size class when the level moves | same tests assert the class (`h5 card-title`, `h5`, `h5 <od classes>`, `h2 accordion-header` at 2); `test_heading_markup` |
| Modal title is the header; content one below it | `test_modal_title_is_the_header` (X-CV-Modal detail partial, at 1 and 2) |
| One block tag; header mode for the base template | `tests/test1/test_heading_tag.py`: markup table, escaped `class` variable, caller context, `card_title`-style block override, parse-time errors |
| System check rejects values outside 1–5 | `test_header_level_valid` (None, 1, 3, 5), `test_header_level_invalid` (0, 6, "2", True, 2.0 → E107) |
| Example shows the intended setup | outline checked on `/`, author list, od accordion and split-card, workflow page, recipe card list: `h1` → `h2` (→ `h3` snippet accordion); `examples/bootstrap5`: 301 passed |
| Docs and CHANGELOG | `docs/reference/settings.md` "Headings", `docs/reference/templates.md` "Heading levels", `### Added` bullet under Unreleased; no `### Breaking`, `docs/migrating-1.0.md` unchanged; `mkdocs build --strict` clean |
| Nothing else moves | `pytest tests -n auto`: 2619 passed, 2 skipped; ruff check / format clean; final review: non-literal `level=` now a parse-time error |
