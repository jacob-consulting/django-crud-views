# Hardening & Cleanup — v0.10.1

*Date: 2026-06-25 · Scope: single patch release · Baseline: v0.10.0 (main)*
*Roadmap: [2026-06-24-audit-followup-roadmap-design.md](2026-06-24-audit-followup-roadmap-design.md) — the "Hardening & cleanup" batch, trimmed.*

## What this is

A small, **non-breaking** patch release bundling two low-risk items from the audit
follow-up roadmap:

- **#33** — Harden `ViewSet.default_permissions` codename parsing *(the only code change)*
- **#34** — Deprecate the `CrispyModelViewMixin` alias *(CHANGELOG note only)*

The roadmap originally batched a third item, **#55** (formsets `parent_form` cleanup),
into this release. It is **deferred**: formsets are tricky and the `parent_form`
validation hook may turn out to be needed, so #55 stays open for its own dedicated
brainstorm → spec → plan cycle rather than being gutted here.

## #33 — Harden `default_permissions` codename parsing

### Problem

`ViewSet.default_permissions` (`src/crud_views/lib/viewset/__init__.py:357-374`) derives an
action key for each model permission by splitting the codename on the first occurrence of
`_<model>`:

```python
action = permission.codename.split(f"_{permission.content_type.model}")[0]
```

Django's auto-created permissions have the form `{action}_{model}`, where the model name is
the **suffix** (`add_book`, `change_book`, …). Custom permissions (declared via
`Meta.permissions`) carry arbitrary codenames. Splitting on the *first* `_{model}` truncates
the action whenever `_{model}` appears before the end of the codename. Example — model `book`,
custom permission codename `change_book_status`: `"change_book_status".split("_book")[0]` yields
`"change"`, which silently **collides** with the standard `change` permission. (Note: a codename
like `rebook_book` is *not* affected — `_book` occurs only at the end, so split and removesuffix
agree.)

### Change

Replace the split with a suffix strip:

```python
action = permission.codename.removesuffix(f"_{permission.content_type.model}")
```

`removesuffix` removes the model name only when it is the actual suffix, leaving any earlier
occurrence intact. It is available on the project's Python floor (3.12+). When the codename
does not end with `_{model}` (not expected for model permissions, but defensive), `removesuffix`
returns the codename unchanged rather than raising.

### Placement

`default_permissions` stays on `ViewSet`. It is a model-derived registry concern consumed by
ViewSet routing and permission resolution; relocating it to the view was floated in the issue
but is rejected here as scope-creep with real blast radius for no user-facing gain.

The audit's task-3.6 documentation ask is closed by adding a docstring note that the property is
a process-lifetime `cached_property` performing database queries (`ContentType` lookup +
`Permission` query), so it is evaluated once per process and not refreshed if permissions change
at runtime.

### Test

Add a focused test (in the existing `tests/test1/` suite):

- A custom permission whose codename contains `_{model}` **before its end** (e.g. model `book`
  with permission codename `change_book_status`). This is the case where `split` and
  `removesuffix` diverge — the regression test must use such a codename, or it passes on both the
  old and new code and proves nothing.
- Assert the parsed action key is the full action (`change_book_status`), not the truncated form
  (`change`), and that the standard `change` key still maps to `change_book` (i.e. the truncated
  custom action no longer collides with it).
- Assert the standard `add` / `change` / `delete` / `view` actions still parse correctly for the
  same model (no regression on the common case).

The concrete test mechanism belongs in the implementation plan. It constructs a throwaway
`ViewSet` over an existing model with a runtime-created `Permission`, rather than adding a
dedicated model, to avoid a model-less ViewSet polluting the global registry / system checks.

## #34 — Deprecate `CrispyModelViewMixin` alias

### Problem

`CrispyModelViewMixin(CrispyViewMixin)` (`src/crud_views/lib/crispy/form.py:134-136`) is an empty
public alias of `CrispyViewMixin`, exported in `__all__` and used in docs, examples, and
downstream projects. It was marked for eventual removal but is still a public name.

### Decision

Keep the alias in place this release. **No runtime `DeprecationWarning`** and **no code change** —
a runtime warning was considered and rejected as more churn than the maintainer wants for a name
that is not being removed yet. The existing in-code comment already references issue #34 and is
left as-is.

The deprecation is communicated through the CHANGELOG only:

> **Deprecated:** `CrispyModelViewMixin` is deprecated in favor of `CrispyViewMixin` and will be
> removed in a future release. The two are identical; rename imports/base classes to
> `CrispyViewMixin`.

Actual removal is a later (breaking → minor) release, not this one.

## Release mechanics

- Single feature branch off `main`; roughly two commits (the #33 fix + test, and the CHANGELOG
  updates).
- PR → wait for CI → fix any ruff → squash-merge to `main` → wait for main CI.
- CHANGELOG `## 0.10.1` section with:
  - `### Fixed` — #33 codename parsing.
  - `### Deprecated` — #34 alias note.
- Version bump: **patch → v0.10.1** (`task bump-patch`, which syncs `pyproject.toml`,
  `__init__.py`, docs, README).

## Out of scope

- **#55** formsets `parent_form` cleanup — deferred to its own cycle.
- Relocating `default_permissions` off `ViewSet`.
- Removing the `CrispyModelViewMixin` alias (later release).
- Any runtime deprecation-warning machinery for #34.

## Definition of done

- `default_permissions` uses `removesuffix`, carries the cached/DB docstring note, and the new
  parsing test passes alongside the existing suite.
- CHANGELOG has a `## 0.10.1` section with the `### Fixed` and `### Deprecated` entries.
- Version bumped to 0.10.1, PR merged, main CI green.
