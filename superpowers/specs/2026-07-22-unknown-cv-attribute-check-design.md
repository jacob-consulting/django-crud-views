# System check for unknown `cv_*` attributes (W280)

**Issue:** [#86](https://github.com/jacob-consulting/django-crud-views/issues/86) — System checks don't catch dead `cv_*` attributes (unknown names silently ignored). Relates to [#28](https://github.com/jacob-consulting/django-crud-views/issues/28).

**Date:** 2026-07-22

## Problem

CrudView config attributes use the `cv_` prefix and are read by `getattr`. A typo or stale name — `cv_message` instead of `cv_message_template_code`, a `cv_mesage_template` misspelling, or an attribute removed in a rename — is silently ignored: the view runs with the package default and the author gets no feedback. This actually happened at scale: 39 occurrences of a non-existent `cv_message` across 8 example apps went unnoticed for months (fixed on `feature/m4-docs`, commit `575867b`).

Existing system checks validate *known* attributes (`CheckTemplateOrCode` on `cv_message_template`, etc.) but nothing flags an *unknown* `cv_`-prefixed attribute on a CrudView subclass. Precedent exists: W270 (`CheckBreadcrumbKeyObject`) already warns about one specific mistyped attribute value.

## Goals

- Warn (W-level) when a user's CrudView subclass declares a `cv_*` **data attribute** that is not part of the package's known attribute set.
- Suggest the likely intended name (near-match).
- No false positives for attributes legitimately contributed by `crud_views` core or its extension apps (workflow, polymorphic, guardian, object_detail) or `crud_views_widget_*` community extensions.
- Provide a local, explicit escape hatch for a user's own legitimately-custom `cv_*` attribute.

## Non-goals

- Flagging `cv_*` **methods** (overrides or user helpers). Only non-callable data attributes are checked — this targets the reported bug class (dead config values) while avoiding false positives on user helper methods. Typo'd method overrides are out of scope.
- A hand-maintained registry of valid attribute names.

## Approach

A single new `Check` subclass, `CheckUnknownAttributes`, yielded once per view from the base `CrudView.checks()` classmethod. It introspects the view's MRO at check time, builds the known-set, and emits one `Warning` per unknown attribute. This follows the W270 model exactly and plugs into the existing collection path: `ViewSet.checks()` ends with `for view in self._views.values(): yield from view.checks()`, and `ViewSet.checks_all()` drives `crud_views.checks.check_viewsets`.

**Why introspection, not a registry:** every legitimate config attribute is already declared with a default on a package class (e.g. `cv_message_template: str | None = None` and `cv_message_template_code: str | None = None` at `base.py:82-83`). The known-set therefore derives itself from the class hierarchy and stays correct as attributes are added or renamed — no separate list to maintain.

### Known-set / suspect / unknown computation

Walking `context.__mro__`:

- **Known set** — `cv_*` names in the `__dict__` of every class whose `__module__` starts with `"crud_views"`. This single prefix covers `crud_views`, `crud_views_workflow`, `crud_views_polymorphic`, `crud_views_guardian`, and any `crud_views_widget_*` community extension following the naming contract.
- **Suspects** — `cv_*` names in the `__dict__` of every *non-package* class in the MRO (user code — **all** such classes, so typos on a shared user mixin are caught too, not only on the leaf view), restricted to **data attributes**: values that are not functions, `classmethod`, `staticmethod`, or `property`. `cv_message = "x"` is a suspect; `def cv_helper(self): ...` is skipped.
- **Allowlist** — the union of `cv_check_ignore_attributes` across the MRO (see escape hatch).
- **Unknown** — `suspects − known − allowlist`. One warning per remaining name.

### Escape hatch

A new declared attribute on the base CrudView:

```python
cv_check_ignore_attributes: frozenset[str] = frozenset()  # custom cv_* data attrs to exempt from W280
```

Gathered as the **union** across the MRO so a user mixin and the leaf view can each contribute exemptions independently (a plain `getattr` would let the most-derived class shadow the others). Because it is itself a package-declared `cv_*` attribute, it is in the known-set and never trips the check.

`SILENCED_SYSTEM_CHECKS = ["viewset.W280"]` also silences the warning for free (any Django check ID does). Documented as the coarse, global fallback; the per-class allowlist is the recommended, targeted mechanism.

### Message and near-match

Check id: `viewset.W280` (Django `Warning`). One message per unknown attribute:

> `cv_message` on `<AuthorList>` is not a known crud_views attribute — it is silently ignored (dead attribute or typo). Did you mean `cv_message_template_code`?

Near-match resolution: `difflib.get_close_matches(name, known, n=1)`; if difflib's ratio misses because the correct name is much longer (e.g. `cv_message` vs `cv_message_template_code`), fall back to a prefix match — the shortest known name that starts with the unknown name. If neither yields a candidate, omit the "Did you mean" clause. The `hint` points at `cv_check_ignore_attributes` for intentional custom attributes.

## Components

| Unit | Responsibility | Depends on |
| --- | --- | --- |
| `CheckUnknownAttributes(Check)` in `lib/check.py` | Compute known/suspect/unknown from `context.__mro__`; yield one `Warning` per unknown attr with a near-match suggestion. | `difflib`, existing `Check` base. |
| `cv_check_ignore_attributes` on `CrudView` (`lib/view/base.py`) | Declared exemption set; unioned across MRO by the check. | — |
| `CrudView.checks()` wiring (`lib/view/base.py`) | `yield CheckUnknownAttributes(context=cls)`. | Existing `checks()` chain. |

The check is self-contained: given a class it needs only the MRO and `difflib`. It is unit-testable against a hand-built class without the full app registry.

## Testing

New test module under `tests/test1/`:

- A view declaring `cv_message = "x"` produces a `viewset.W280` warning naming `cv_message` and suggesting `cv_message_template_code`.
- A view that overrides a real attribute (`cv_message_template_code = "..."`) produces no warning.
- A view declaring a custom `cv_foo = 1` listed in `cv_check_ignore_attributes` produces no warning; the same attribute without the allowlist does warn.
- An exemption declared on a user mixin applies to a leaf view that adds its own exemption (union, not shadow).
- An extension-contributed attribute (e.g. workflow's `cv_message_template_code`) produces no warning.
- A user-defined `cv_*` **method** produces no warning (data-attribute restriction).

## Docs and changelog

- Add a W280 entry to the system-checks reference documentation, describing the warning and both escape hatches (per-class `cv_check_ignore_attributes`, global `SILENCED_SYSTEM_CHECKS`).
- CHANGELOG entry. PR description notes "Relates to #28".
