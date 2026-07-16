# M2 — API Stability & Backlog Triage (0.14.0)

**Date:** 2026-07-16
**Status:** Approved design
**Source:** `superpowers/notes/2026-07-16-release-1-milestone.md`, section M2
**Ships as:** 0.14.0 (contains breaking changes; pre-1.0 breaking window is open)

## Goal

Give 1.0.0's semver promise a defined object: a documented public API surface, no lingering
deprecations, and an explicitly triaged backlog. After M2, issue #34 is closed, issues #28
and #31 carry recorded in/out-of-1.0 decisions, and a stability statement is merged.

## Decisions made in this brainstorm

1. **#34: `CrispyViewMixin` is the surviving name.** It is the accurate name (the mixin
   injects `cv_view` for both `CrispyForm` and `CrispyModelForm`, not just model forms).
   The `CrispyModelViewMixin` alias is removed outright — no deprecation shim; the pre-1.0
   breaking window is open and the milestone already fixed this mechanism.
2. **Formsets API is split: usage public, internals private.** The declaration surface users
   type in their views (`FormSetMixin`, `cv_formsets`, the layout/config classes) becomes
   public and semver-covered. The machinery (`render_tree`, `inline_formset` internals)
   stays explicitly internal.
3. **Public-API definition: rule + enumerated list.** A prose rule backed by an enumerated
   list of covered import paths per app. No enforcement machinery (no `__all__` sweep, no
   import-pinning test).
4. **Stability statement lives in `docs/development/stability.md`**, with a one-paragraph
   "API stability" note on `docs/index.md` linking to it.
5. **#28 (system checks) is deferred to 1.x.** Checks are additive dev-time tooling with no
   semver impact. The issue body is edited to drop the now-obsolete `crud_views_plain` item.
6. **#31 is split.** The hook-placement fix (breaking) happens now in M2; the configurable
   transaction behavior (additive) is deferred to 1.x and the issue rescoped accordingly.

## Work items

### 1. Stability statement

New page `docs/development/stability.md` with three parts:

**The rule.** Public API = names shown in the reference documentation, imported from the
enumerated module paths. Everything else — any module not listed, and all `_`-prefixed
names — is internal and may change without notice.

**The enumerated surface**, grouped per app (categories fixed here; the final name-by-name
list is produced during implementation by auditing the reference docs against the code):

- `crud_views` core:
  - ViewSet layer: `ViewSet`, `ParentViewSet`
  - View classes: `CrudView`, the concrete views (`ListView`, `DetailView`, `CreateView`,
    `UpdateView`, `DeleteView`, `ActionView`, `OrderedUpView`/`OrderedDownView`,
    `CustomFormView`, `CustomFormNoObjectView`, manage/card/detail-custom views) and their
    `*PermissionRequired` variants; `CreateViewParentMixin`; table/filter mixins
    (`ListViewTableMixin`, `ListViewTableFilterMixin`)
  - Crispy layer: `CrispyViewMixin`, `CrispyModelForm`, `CrispyForm`, `CrispyDeleteForm`,
    layout helpers (`Column4`, `Column8`, …)
  - Resources: `Resource`, `ResourceViewMixin`
  - Formsets **declaration surface only**: `FormSetMixin`, `cv_formsets`, the layout/config
    classes users reference in view declarations. `render_tree`, `inline_formset` and other
    machinery are explicitly named as private.
  - Settings: all documented `CRUD_VIEWS_*` names
  - Template tags: the documented tags in `crud_views` and `crud_views_formsets` tag libraries
  - Documented `cv_*` class attributes and overridable hooks (`cv_form_valid`,
    `cv_form_valid_hook`, `cv_post_hook`, …) on public view classes
- `crud_views_workflow`: documented classes (`WorkflowView`, `WorkflowViewPermissionRequired`,
  `WorkflowModelMixin`, …) and the `on_transition` hook
- `crud_views_polymorphic`: documented classes (`PolymorphicCreateSelectView`,
  `PolymorphicCreateView`, … and permission variants)
- `crud_views_guardian`: documented classes (`GuardianViewSet`, `Guardian*PermissionRequired`)

**Deprecation policy post-1.0.** Plain semver: public-API breaking changes only in major
releases. Deprecated names emit `DeprecationWarning` and remain functional until the next
major release. Every deprecation is noted in the CHANGELOG.

`docs/index.md` gains a short "API stability" paragraph linking to the page.

### 2. Resolve #34 — remove `CrispyModelViewMixin`

- Delete the empty alias class in `src/crud_views/lib/crispy/form.py` and its export in
  `src/crud_views/lib/crispy/__init__.py`.
- Migrate all internal usage to `CrispyViewMixin`:
  - `tests/test1/app/views.py`, `tests/test1/app/views_formset.py`,
    `tests/test1/test_custom_form_view.py` (comments/docstrings included)
  - docs: ~10 reference pages + `getting_started/tutorial2.md`
  - current examples (`examples/bootstrap5/app/views/…`) — throwaway migration, M3 rewrites
    them anyway
- CHANGELOG: prominent breaking-change entry with a one-line migration hint
  (`CrispyModelViewMixin` → `CrispyViewMixin`).
- Extensions repo: verified 2026-07-16 to have zero crispy imports — no ripple. Re-verify at
  implementation time.
- Close #34 on merge.

### 3. Resolve #31 (breaking half) — workflow hook placement

`CrudViewProcessFormMixin.post` calls `cv_form_valid` (the framework "do the work" step)
then `cv_form_valid_hook` (the user extension point, a no-op `pass` in every core view).
`WorkflowView` inverts this convention: its transition execution lives in
`cv_form_valid_hook`, occupying the user extension point — a subclass overriding the hook
to add behavior silently destroys transition execution.

- Move the transition logic from `WorkflowView.cv_form_valid_hook` to
  `WorkflowView.cv_form_valid` (`src/crud_views_workflow/lib/views.py`). The method body is
  unchanged, including the hard-coded `transaction.atomic()`; only the placement moves.
- `cv_form_valid_hook` reverts to a free user extension point. The existing `on_transition`
  hook is unaffected.
- CHANGELOG: breaking-change entry for subclasses that relied on the inverted placement.
- Rescope issue #31 to the remaining additive half (configurable transaction behavior),
  record the "deferred to 1.x" decision on it; the issue stays open.

### 4. Triage #28 — deferred to 1.x

- Comment the decision ("deferred to 1.x — additive dev-time tooling, no semver impact") on
  the issue.
- Edit the issue body to drop the obsolete item "run checks in crud_views_plain AppConfig"
  (the app was removed in 0.13.0).
- No code changes.

### 5. Wart sweep

One pass over `src/` for remaining TODO-style API warts, unstated deprecations, and
misnamed public-facing symbols while the breaking window is open. The audit's TODO triage
(2026-06-10) already ran, so expect near-zero findings. Anything found gets a decide-or-defer
note — findings do not automatically expand M2 scope.

## Testing

The existing suite (~320 tests) must stay green after the rename and the hook move:

- `tests/test1/test_custom_form_view.py` already covers the mixin's `cv_view` injection —
  it migrates to the surviving name and keeps passing.
- Workflow tests exercise transitions end-to-end and will catch a botched hook move.
- No new test infrastructure.

## Out of scope

- Implementing #28 (system checks) — deferred to 1.x.
- Implementing configurable transaction behavior (#31 additive half) — deferred to 1.x.
- Any `__all__` cleanup or import-pinning enforcement tests.
- Examples restructuring (M3) and docs tutorial work (M4).

## Done when

- `docs/development/stability.md` merged, linked from `docs/index.md`.
- #34 closed; no grep hits for `CrispyModelViewMixin` outside CHANGELOG/history.
- #28 and #31 carry explicit recorded decisions; #31 rescoped.
- Full test suite green; extensions repo installs and passes against 0.14.0.
- 0.14.0 released per the standard release process.
