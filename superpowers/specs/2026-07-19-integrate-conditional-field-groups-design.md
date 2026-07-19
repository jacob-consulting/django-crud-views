# Integrate `feat/conditional-field-groups` into main

**Date:** 2026-07-19
**Status:** Approved design
**Source prompt:** `superpowers/prompts/2027-07-19-integrate-conditional-fields-groups.md`

## Purpose

`feat/conditional-field-groups` carries a complete, well-tested feature — conditional
field-groups and conditional formsets, toggled by a checkbox — that cannot be merged as-is.
It diverged from `main` in late June 2026, before the M3 examples rewrite
(`superpowers/notes/2026-07-16-release-1-milestone.md`) replaced the old
`examples/bootstrap5/app/` monolith with a per-feature-app layout. The branch's example code
targets a directory tree that no longer exists. This spec defines how the feature reaches
`main` without losing anything from the original branch.

## Background: what the branch contains

`git log main..feat/conditional-field-groups` shows ~90 commits (many spec/plan/fix cycles
typical of SDD work). `git diff main...feat/conditional-field-groups --stat` shows the real
diff is much smaller — 39 files, ~3950 insertions. Grouped by area:

- **Core library** (new): `src/crud_views/lib/conditional/{__init__,toggle,group,layout,formset}.py`
  — `ToggleSource`/`ModelFieldToggle`/`UIFieldToggle`, `ConditionalGroup` +
  `ConditionalGroupModelForm`, `ToggleGroup` crispy layout object (plain `<div>` or, with
  `legend=`, a `<fieldset>`), `ConditionalFormSet` (`on_off="skip"|"purge"`).
- **Core library** (touched): `checks.py` (+80 lines: `check_conditional`, IDs `E310`,
  `E311`, `W320`), `formsets/formsets.py` (+26), `formsets/mixins.py` (+3: one call to
  `formsets.apply_conditional(context["form"])`), `formsets/render_tree.py` (+6),
  `static/crud_views/js/{toggle.js (new),formset.js (+22/-)}`,
  `templates/crud_views/conditional/toggle_group.html` (new),
  `templates/crud_views/formsets/formsets.html` (+8/-).
- **Examples** (old layout, unusable as-is): `examples/bootstrap5/app/models/conditional.py`
  (`Registration`, `Event`, `Session`), `app/views/conditional.py` (`cv_registration`,
  `cv_event` ViewSets — the two "kinds" of the feature), `app/urls.py`, `app/templates/app/nav.html`.
- **Docs**: `docs/reference/conditional.md` (new), `docs/faq.md` (+38, FAQ entry — contains a
  known bug, see Quality bar below), `docs/reference/.pages` (+1 nav entry), `CHANGELOG.md` (+5).
- **Skill**: `skills/django-crud-views/SKILL.md` (+51), `skills/django-crud-views/references/api-reference.md` (+62)
  — this path **no longer exists in this repo** (see Skill update below).
- **Tests**: `tests/test1/test_conditional_{checks,exports,formset,group,layout,toggle}.py`
  (new, ~550 lines), `tests/test1/test_formsets.py` (+24), `tests/test1/app/models.py` (+19:
  `Profile`/`ProfileItem` fixtures), `tests/test1/app/views_formset.py` (+8: a `form_tag=False`
  fix needed for formsets to render inside the CRUD form template).
- **Plans/specs** (already in the correct location per project convention): 5 files under
  `superpowers/plans/` and `superpowers/specs/` documenting the original design — carried
  along for history, no changes needed.

## What changed on `main` since the branch diverged

Checked with `git diff $(git merge-base main feat/conditional-field-groups) main` per file:

- `examples/bootstrap5/app/` was deleted entirely and replaced by the M3 layout: a slim
  `project/` package (settings, root urls, home page reading `project/features.py`) plus
  one self-contained app per feature — `library/`, `nested/`, `formsets/`, `workflow/`,
  `polymorphic_demo/`, `guardian_demo/`, `resources/`, `showcase/`, `object_detail/` (added
  after M3, via the object-detail integration). Each app follows the same flat shape:
  `apps.py`, `models.py`, `views.py`, `seed.py`, `tests.py`, `urls.py`.
- `checks.py`'s existing formset checks were renumbered (`E200` → `E204`/`E205`/`E206`) and
  a new `object_detail` app was integrated as `crud_views_object_detail`. Neither touches the
  branch's new `E310`/`E311`/`W320` IDs — verified no collision (`grep` over all
  `id="crud_views.*"` in `src/` shows only `E100`, `E101`, `E300`, `W110`, `W330`, `W331` in
  use besides the M3-era formset IDs).
- `formsets/mixins.py` changed on the same lines as the branch's one-line hook touches a
  *different* line (check-ID edits vs. the `apply_conditional` call) — low conflict surface,
  applies cleanly.
- `docs/faq.md`, `templates/crud_views/formsets/formsets.html`,
  `static/crud_views/js/formset.js`, `lib/formsets/render_tree.py`: **no changes on main**
  since divergence — branch's patches to these apply cleanly.
- `skills/` directory: **deleted from this repo entirely.** The standalone SKILL.md now
  lives in a separate repo, `~/projects/alex/skills`
  (`plugins/django-crud-views/skills/django-crud-views/SKILL.md` +
  `references/api-reference.md`), confirmed unchanged there for the conditional topic (no
  `ConditionalGroup`/`ToggleGroup` mentions currently).
- `tests/test1/app/models.py` and `views_formset.py`: main's own additions
  (`S3FilePermissions`) and the branch's (`Profile`/`ProfileItem`, `form_tag=False`) both
  append at file-end — no conflict.

## Approach

**Fresh branch off current `main`; hand-port, don't merge or rebase the old branch.**

Rejected alternatives:
- *Merge `main` into the feature branch*: conflict resolution concentrates in the deleted/restructured
  `examples/bootstrap5/app/` tree — resolving "ours deleted, theirs modified" across dozens of
  files for a directory that must be rewritten anyway adds work without adding safety.
- *Rebase the feature branch onto `main`*: replays ~90 commits, each a potential conflict
  point against the same restructured tree. Highest fidelity to commit history, but that
  history is mostly superseded SDD spec/plan/fix cycles — not worth preserving commit-by-commit.

Two-tier port:
1. **Core library — port near-verbatim.** The `conditional` package, `checks.py` additions,
   the `formsets/mixins.py` hook, JS/template changes. These touch code paths that haven't
   moved since divergence, so the branch's diffs apply directly (hand-applied, not via
   `git cherry-pick`, since the branch's commit-by-commit history mixes this work with
   example/doc changes — but the resulting file content should match the branch's final state
   for these files).
2. **Everything downstream of the examples restructure — rewrite against current `main`.**
   New example app, doc cross-references, tests for the example.

## New example app: `examples/bootstrap5/conditional/`

One feature app (not two), following the `formsets/`/`showcase/` flat-file pattern:
`apps.py`, `models.py`, `views.py`, `seed.py`, `tests.py`, `urls.py`. Combines both
"kinds" from the branch, since they share the same underlying mechanism and JS wiring — this
mirrors how `showcase/` already bundles multiple related presentation building blocks in one
app rather than one-app-per-widget.

- **Registration** (conditional field-group): `Registration` model
  (`name`, `with_company`, `company_name`, `vat_id`) carried over from the branch as-is — a
  believable "event registration with optional company billing details" scenario, no
  reinvention needed. `RegistrationForm(ConditionalGroupModelForm)` declares
  `cv_conditional_groups = [ConditionalGroup(toggle=ModelFieldToggle("with_company"), fields=["company_name", "vat_id"], required=["company_name"])]`
  and renders `ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id")), legend="Company details")`
  — this is the fieldset/legend rendering mode.
- **Event → Session** (conditional formset): `Event` (`name`, `with_sessions`) and `Session`
  (FK to `Event`, `title`), carried over as-is. `cv_event_formsets` gates the `sessions`
  formset with `ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="purge")`
  — off means the whole formset is hidden, unvalidated, and existing rows are deleted on save.
- Both ViewSets use `ObjectDetailViewPermissionRequired` for detail pages (the convention in
  `library`/`nested`/`formsets`/`workflow`), not the branch's plain `DetailViewPermissionRequired`.
- `seed.py` follows the existing per-app pattern (idempotent, used by `manage.py seed`):
  a couple of `Registration` rows (one with company details, one without) and one `Event`
  with a few `Session` rows.
- New `Feature` entry appended to `project/features.py`'s `FEATURES` list: `app="conditional"`,
  title "Conditional", an `about` paragraph explaining both kinds, `look_at` pointing at
  `RegistrationForm.cv_conditional_groups` / `ToggleGroup` and `cv_event_formsets`'
  `ConditionalFormSet`, icon e.g. `fa-solid fa-toggle-on`, `url_name="registration-list"`.

## Docs

- `docs/reference/conditional.md`: ported from the branch, code references updated to point
  at `examples/bootstrap5/conditional/views.py` instead of the old `app/views/conditional.py`
  path. Added to `docs/reference/.pages` nav (after `formsets`-adjacent entries, exact
  position decided at implementation time).
- `docs/faq.md`: port the branch's FAQ entry, but **fix** a bug the branch itself never
  caught — the branch's own FAQ example still shows the pre-legend `ToggleGroup` call
  (`ToggleGroup("with_company", ...)` with no `legend=`, and fields on a single row) even
  after the legend/fieldset feature was added later in the branch's history. Write the FAQ
  example against the final, legend-aware API from the start.
- `CHANGELOG.md`: append the conditional feature bullet under the existing `## Unreleased` →
  `### Added` section (main's `Unreleased` already has unrelated entries from the
  object-detail integration — this is an addition, not a rewrite of that section).

## Skill update (separate repo, follow-up step)

Per project memory, `skills/django-crud-views/SKILL.md` was deleted from this repo and now
lives at `~/projects/alex/skills`
(`plugins/django-crud-views/skills/django-crud-views/SKILL.md` and its
`references/api-reference.md`), a repo with its own commit-directly-to-main workflow. "Update
skill" (from the integration prompt) means porting the branch's SKILL.md/api-reference.md
additions into *that* repo — a Quick Reference row, a "Conditional Field-Groups and Formsets"
section, and the `ToggleGroup`/`ConditionalGroup`/`ConditionalFormSet` API entries — done as a
follow-up step once this package's own changes are settled, not as part of this repo's PR.

## Tests

- Port unchanged: `tests/test1/test_conditional_{checks,exports,formset,group,layout,toggle}.py`
  and the `test_formsets.py` additions — these exercise the core lib against
  `tests/test1/app/`, independent of the examples tree.
- Port unchanged (append at file-end, no conflicts): `tests/test1/app/models.py`
  (`Profile`/`ProfileItem`), `tests/test1/app/views_formset.py` (`form_tag=False` fix,
  needed wherever a form renders `Formsets()` inside the CRUD form template).
- New: `examples/bootstrap5/conditional/tests.py`, following the `formsets/tests.py`
  pattern — cover both ViewSets' CRUD flows plus the toggle-on/toggle-off behavior for each
  kind. Update `project/tests.py`'s FEATURES-list assertions to include the new app (mirrors
  the existing per-app checks, e.g. the `polymorphic_demo` one).

## Done when

- `feat/integrate-conditional-field-groups` (new branch off `main`) has the core `conditional`
  lib package, checks, JS, and templates in place; full test suite green.
- `examples/bootstrap5/conditional/` exists, matches the M3 app pattern, appears on the home
  page, and is covered by its own `tests.py`.
- `docs/reference/conditional.md` and the `docs/faq.md` entry are present and internally
  consistent (no stale pre-legend `ToggleGroup` signature).
- `CHANGELOG.md` `Unreleased` section has the conditional feature bullet.
- Nothing from the original branch's functionality (both conditional "kinds", skip vs. purge,
  legend/fieldset mode, system checks) is lost.
- Skill update in `~/projects/alex/skills` tracked as an explicit follow-up (not blocking this
  repo's PR merge, but not forgotten either).
