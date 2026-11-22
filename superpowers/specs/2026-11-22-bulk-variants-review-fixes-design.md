# Bulk variants (#400): review fixes before merge

**Date:** 2026-11-22
**Status:** approved by the maintainer on 2026-11-22
**Scope:** follow-up to phase 06.47 on branch `gsd/phase-06.47` (PR #402, open).

## Intent

An independent review of phase 06.47 found the implementation matches its plans, with a few weak spots. This
change closes the ones worth closing before PR #402 merges, and leaves the rest alone on purpose.

## Goals

1. A bulk destination whose `cv_action_variant` is `None` or `""` renders as `secondary`, like action buttons do.
2. The frozen pre-variant snapshot and its regeneration ritual are gone.
3. Two overlong documentation lines and one clumsy sentence are tidied.
4. The built wheel and sdist are confirmed to ship `crud_views/tags/button/bulk.html`.

## Non-goals

- Stock `bulk:danger` stays `btn btn-primary` (issue #400 D-03, maintainer-approved).
- No check or warning for themes that styled bulk buttons through `form:submit`. The loss of inheritance is
  documented and the feature is unreleased; the CoreUI, Tabler and AdminLTE themes add the four keys themselves.
- The raw dict in `cv_bulk_buttons` keeps passing `cv_key`/`cv_type`/`cv_name`/`cv_value` to the form normalizer.
  Removing that needs a new helper, which costs more than the duplication.

## Anti-goal

No new public name, setting, check ID or template field.

## Changes

### 1. Variant fallback

`BulkSelectionMixin.cv_bulk_buttons` (`src/crud_views/lib/bulk/__init__.py`) sets
`cv_variant = destination.cv_action_variant or "secondary"`. This mirrors the action normalizer
(`src/crud_views/lib/view/button_data.py`, `ctx.get("cv_variant") or "secondary"`).

A value that is a non-empty string but not one of the four variants still resolves to no class, as on every other
location; `viewset.E209` reports it at check time. That is stated in the docs and pinned by a test, so the choice
is visible instead of accidental.

- Test (`tests/test1/test_bulk_variants.py`): on table and card sources, `None` and `""` render the
  `bulk:secondary` class; an unknown string renders an empty class.
- Docs (`docs/reference/buttons.md`, `cv_variant` row of the bulk leaf contract): one sentence on the fallback and
  on E209.

### 2. Remove the frozen snapshot

Delete `tests/test1/fixtures/bulk_toolbar_pre_variant.json`, `test_stock_toolbar_bytes`, the `SNAPSHOT` constant
and the maintenance-policy docstring. Keep `test_stock_toolbar_matches_form_leaf`, which renders the unchanged
form leaf from each real payload and compares it byte for byte with the page and with the bulk leaf, across the
same 24 source/mode/icon cases.

The snapshot did its job: it proved the switch changed no bytes, and that proof stays in git history
(capture `7108fa87`, switch `7b50b6b8`). Kept in the tree it couples 24 cases to signed return tokens, URLs, icons
and labels owned by other features.

### 3. Records

- `.planning/codebase/CONVENTIONS.md`, `TESTING.md`, `STRUCTURE.md`: replace the "immutable fixture" statements
  with the form-leaf comparison.
- Phase 06.47 records (`06.47-VERIFICATION.md`, `06.47-VALIDATION.md`, `06.47-01-SUMMARY.md`): add a short dated
  amendment note beside the snapshot statements, linking this document. The original text stays, in the same way
  phase 06.47 annotated phase 06.41.

### 4. Documentation tidy

Rewrap the two 146-character lines (`docs/development/stability.md`, `docs/reference/buttons.md`) and fix the
"A and B and C" list of override templates in `stability.md`. No wording that a docs test pins is changed.

## Approaches considered for the snapshot

| | Approach | Trade-off |
|---|---|---|
| A | Delete fixture and test now | Removes 366 lines and the ritual; relies on the live form-leaf comparison and gives up the absolute byte pin (see below). **Chosen by the maintainer.** |
| B | Keep, relax the policy to "regenerate once the form-leaf comparison passes" | Keeps the absolute byte pin, at the cost of a fixture that is regenerated whenever an upstream input changes. |
| C | Keep until Phase 7 freezes the surface | Defers the same deletion and keeps the coupling meanwhile. |

What approach A gives up, found by the final review: the comparison is relative to the form leaf. A byte-only
change upstream of both leaves, such as the attribute order in `cv_attrs` or the `cv_id` format, no longer fails
`test_bulk_variants.py`. Semantic changes there are still caught by the parsed-markup assertions in
`test_bulk_source.py`, and absolute form-leaf bytes by `test_form_buttons_golden.py`.

## Verification

- Focused: `test_bulk_variants.py`, `test_bulk_docs.py`, `test_bulk_source.py`, `test_button_classes.py`.
- Full `tests/test1` on multiple workers, `ruff format --check`, `ruff check`, `mkdocs build --strict`.
- Build wheel and sdist into a scratch directory, confirm `bulk.html` is in both, run `scripts/check_dist.py`.

## Left to the builder

Exact test names, the wording of the doc sentence and of the amendment notes.

## Open after this change

The digest in `06.47-VERIFICATION.md` covers files this change edits, so the phase verification record needs a
refresh by the maintainer's usual step. Commits land on `gsd/phase-06.47`; pushing to PR #402 waits for the
maintainer's word.
