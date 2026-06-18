# ViewSet-level `extends` template override — design

**Date:** 2026-06-18
**Status:** Approved (pending spec review)

## Problem

The base template that every CRUD view extends is set globally via the
`CRUD_VIEWS_EXTENDS` setting. A user who needs *all views of one ViewSet* to
extend a different base template has no single place to declare it.

Per-view override already exists (`CrudView.cv_extends_template`), but applying
it to a whole ViewSet means repeating the attribute on every view.

## Current behaviour

- `CrudView.cv_extends_template: str | None = None` (`view/base.py:49`).
- `CrudView.cv_get_extends_template()` (`view/base.py:100`) resolves
  **view → global setting**:

  ```python
  def cv_get_extends_template(self) -> str:
      cv_extends = self.cv_extends_template
      extends = cv_extends if cv_extends else crud_views_settings.extends
      return extends
  ```

- `get_context_data()` injects the result as `cv_extends` into the template
  context (`view/base.py:97`).
- `ViewSet` (`viewset/__init__.py:52`) has **no** template/extends field.
- Settings check `E100` (`settings.py:64`) requires `CRUD_VIEWS_EXTENDS` to be
  set and the template to exist.

## Goals

1. Add a `extends` field to `ViewSet` so one declaration covers all its views.
2. Keep the per-view `cv_extends_template` as the finest-grained override.
3. Keep the global setting as the mandatory final fallback.
4. Validate overridden templates at startup via Django system checks
   (both view-level and viewset-level).
5. Document both the ViewSet field and the shared-base-mixin pattern.
6. Test the full fallback chain.

Non-goals: changing the global setting requirement; per-request dynamic
template selection (already possible by overriding `cv_get_extends_template`).

## Design

### 1. New `ViewSet` field

Add to the `ViewSet` Pydantic model (`viewset/__init__.py:52`):

```python
extends: str | None = None  # base template all views in this viewset extend
```

Plain field name (no `cv_` prefix), consistent with existing ViewSet fields
(`prefix`, `ordering`, `icon_header`, …) and with `settings.extends`.

### 2. Three-level resolution chain

Rewrite `CrudView.cv_get_extends_template()` to fall back
**view → viewset → global**:

```python
def cv_get_extends_template(self) -> str:
    if self.cv_extends_template:
        return self.cv_extends_template
    if self.cv_viewset.extends:
        return self.cv_viewset.extends
    return crud_views_settings.extends
```

`self.cv_viewset` is always set (assigned by the metaclass at registration),
including for the auto-generated manage view. Behaviour is unchanged when
neither override is set; per-view still wins over the viewset.

### 3. System checks

Both overrides are optional, so the check must be a no-op when the attribute is
unset and an error only when set-but-unresolvable. The existing
`CheckTemplateOrCode` errors when *neither* template nor `_code` is set, which is
wrong here (there is no `extends_code`). Add a small check class:

```python
class CheckTemplate(Check):
    """Validate that an optional template attribute, if set, resolves."""
    id: str = "E111"
    attribute: str | None = None
    msg_template_not_found: str = "Template »{template}» not found at »{context}»"

    def messages(self) -> Iterable[CheckMessage]:
        template = getattr(self.context, self.attribute, None)
        if template:
            try:
                get_template(template)
            except TemplateDoesNotExist:
                yield Error(id=self.get_id(),
                            msg=self.msg_template_not_found.format(
                                template=template, context=self.context))
```

- **View-level:** in `CrudView.checks()` (`view/base.py:69`), yield
  `CheckTemplate(context=cls, attribute="cv_extends_template")`.
- **ViewSet-level:** in `ViewSet.checks()` (`viewset/__init__.py:141`), yield
  `CheckTemplate(context=self, attribute="extends")`.

The global `E100` check is left untouched — the setting stays mandatory as the
final fallback.

### 4. Documented mixin pattern (the alternative)

Document the zero-config alternative for sharing across views/viewsets or
varying within a viewset:

```python
class MySpecialBase(CrudView):
    cv_extends_template = "my/base.html"

class FooListView(MySpecialBase, ListView):
    ...
```

Guidance: **ViewSet `extends`** = "all views in this viewset, one line";
**mixin** = "share a base across several viewsets, or vary it within one."

### Critical caveat — the override target MUST be a real base template

The crud_views view templates render `{% extends cv_extends %}`, where
`cv_extends` resolves to the override. Therefore the template named by
`cv_extends_template` (or ViewSet `extends`) is itself the base being extended
and **MUST NOT** contain `{% extends cv_extends %}` (nor otherwise re-extend
`cv_extends`). Doing so makes the template try to extend itself, raising:

```
django.template.exceptions.TemplateDoesNotExist
```

The override must point at a normal base template — one that extends your own
site base (e.g. `{% extends "base.html" %}`) or none at all — not at the
crud_views child template indirection. This warning must appear in both the
reference docs and the inline skill.

## Documentation changes

- `docs/reference/` — document `ViewSet.extends` and the resolution order
  (view → viewset → global) where ViewSet fields / templates are described;
  add the mixin pattern as a short note/FAQ.
- **Include the "Critical caveat" above** as a prominent warning admonition:
  the override template MUST NOT contain `{% extends cv_extends %}`, or
  rendering raises `TemplateDoesNotExist`.
- Cross-link from the existing template/`cv_extends_template` docs.
- `CHANGELOG.md` — Unreleased entry.

## Inline skill update

Update `skills/django-crud-views` (`SKILL.md` and/or `references/`) to mention:
- the `extends` field on `ViewSet`,
- the view → viewset → global resolution order,
- the mixin pattern,
- the critical caveat: the override template MUST NOT contain
  `{% extends cv_extends %}` (would raise `TemplateDoesNotExist`),
so the skill recommends the new field when users ask about per-viewset base
templates.

## Tests (`tests/test1/`)

1. ViewSet `extends` propagates to `cv_extends` in **every** view's context.
2. View-level `cv_extends_template` overrides the viewset's `extends`.
3. ViewSet `extends` overrides the global setting.
4. Nothing set anywhere → falls back to the global setting.
5. System check: a ViewSet `extends` naming a missing template raises `E111`.
6. System check: a view `cv_extends_template` naming a missing template
   raises `E111`.

## Files touched

| File | Change |
|---|---|
| `src/crud_views/lib/viewset/__init__.py` | add `extends` field; yield `CheckTemplate` in `checks()` |
| `src/crud_views/lib/view/base.py` | three-level `cv_get_extends_template()`; yield `CheckTemplate` in `checks()` |
| `src/crud_views/lib/check.py` | add `CheckTemplate` class |
| `tests/test1/` | new tests for chain + checks |
| `docs/reference/…` | document field, resolution order, mixin pattern |
| `CHANGELOG.md` | Unreleased entry |
| `skills/django-crud-views/…` | document the field + patterns |
