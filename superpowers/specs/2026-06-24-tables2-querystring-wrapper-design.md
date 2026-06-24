# django-tables2 version-agnostic `cv_querystring` wrapper tag

**Date:** 2026-06-24
**Status:** Approved
**Issue:** Consumer-upgrade Issue 2 (HIGH) — list pages break across django-tables2 versions.

## Problem

django-tables2 3.0.0 (released 2026-04-13) renamed the `{% querystring %}` template tag to
`{% querystring_replace %}` (to avoid shadowing Django 5.1's built-in `querystring` tag). The
crud_views Bootstrap 5 list-table template uses `{% querystring_replace %}`, so it only renders on
django-tables2 ≥ 3.0 — yet `pyproject.toml` declares `django-tables2>=2.5.3`. A consumer whose
resolver picks a 2.x release gets a `TemplateSyntaxError` on every list page.

A rejected interim fix (a dispatcher template that includes a version-specific body) worked but added
runtime indirection — a `table_template` settings property, a `cv_table_template` tag, a dispatcher
template, and two duplicate body templates — and pushed the same split onto any consumer who writes a
custom per-view table template. That indirection is the "code noise" this design removes.

## Goal

One list-table template that renders on django-tables2 2.x **and** 3.x with no runtime indirection,
such that a future per-view-configurable table template stays version-safe simply by using the same
tag — no template pairs, no dispatcher, no version branch in settings.

## Design

### Wrapper tag

The django-tables2 querystring tag is registered with `@register.tag` and its parser does
`bits = token.split_contents(); tag = bits.pop(0)` — it **pops and ignores its own tag name**. Both
`querystring` (2.x) and `querystring_replace` (3.x) share this signature. So crud_views can ship one
tag that delegates to whichever django-tables2 registered, passing the token through unchanged.

In `crud_views/templatetags/crud_views.py`:

```python
from django_tables2.templatetags import django_tables2 as _dt2

_querystring_impl = getattr(_dt2, "querystring_replace", None) or _dt2.querystring


@register.tag(name="cv_querystring")
def cv_querystring(parser, token):
    """Version-agnostic django-tables2 querystring tag.

    Delegates to ``querystring_replace`` (django-tables2 >= 3.0) or ``querystring`` (< 3.0).
    Both pop and ignore the tag name, so the token passes through unchanged.
    """
    return _querystring_impl(parser, token)
```

### Template

`crud_views/templates/crud_views/table/bootstrap5.html` is the single real table template again:
`{% load crud_views %}` (plus `{% load django_tables2 %}` if still required for other tags), and the
four `{% querystring_replace … %}` calls become `{% cv_querystring … %}`.

### Cleanup (revert the dispatcher interim work)

- Delete `bootstrap5_ge3.html` and `bootstrap5_lt3.html`.
- Remove `_tables2_major()` and the `table_template` property from `crud_views/lib/settings.py`.
- Remove the `cv_table_template` tag from the templatetags module.
- Keep the `pyproject.toml` floor at `django-tables2>=2.5.3` — both versions work.

## Error handling

No runtime error handling or system check is added. Both django-tables2 versions resolve to a working
tag, so there is nothing to mismatch. The `getattr(..., "querystring_replace", None) or _dt2.querystring`
fallback is the only branch; if a future django-tables2 renamed the tag again, that surfaces as a loud
`AttributeError` at templatetags load — correct and obvious.

## Testing

- **Unit:** `cv_querystring` resolves to `querystring_replace` on the installed django-tables2 3.x, and
  rendering `{% load crud_views %}{% cv_querystring foo='bar' %}` against a request context produces the
  expected query string (real behavior, no mocks).
- **Integration (keep):** render a list page through `DJANGO_TABLES2_TEMPLATE =
  "crud_views/table/bootstrap5.html"` — the end-to-end guard for template + tag.
- Remove the two `_tables2_major` monkeypatch tests (that code is deleted).

## Docs / changelog

- `docs/reference/settings.md`: the crud_views table template is version-agnostic (django-tables2 2.x
  and 3.x) via the `cv_querystring` wrapper tag; no manual `DJANGO_TABLES2_TEMPLATE` switching.
- `CHANGELOG.md` "Unreleased": rewrite to describe the wrapper-tag approach.

## Future-proofing note

When django-tables2 v3 is mature and 2.x support is dropped: remove the `or _dt2.querystring` fallback
(or the wrapper tag entirely, reverting templates to `{% querystring_replace %}`) and bump the pyproject
floor to `>=3.0.0`.
