# Design: ManageView / GuardianManageView Class Customization

**Date:** 2026-04-28  
**Status:** Approved

## Summary

Allow the base class used for the auto-registered `manage` view to be overridden, both per-viewset (via a `manage_view_class` field) and globally (via Django settings). Applies to both `ViewSet` and `GuardianViewSet`.

## Motivation

Currently `ViewSet.register()` hard-codes `ManageView` as the base for the auto-created manage view, and `GuardianViewSet.register()` hard-codes `GuardianManageView`. Users who want to customize the manage view (e.g. add extra context, restrict access differently, change the template) must bypass the auto-registration mechanism entirely. This feature makes customization a first-class option.

## Data Model Changes

### `CrudViewsSettings` (`crud_views/lib/settings.py`)

Two new optional settings:

```python
manage_view_class: str | None = from_settings("CRUD_VIEWS_MANAGE_VIEW_CLASS", default=None)
guardian_manage_view_class: str | None = from_settings("CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS", default=None)
```

### `ViewSet` (`crud_views/lib/viewset/__init__.py`)

One new Pydantic field:

```python
manage_view_class: str | None = None
```

`GuardianViewSet` inherits this field — no additional field needed.

## Resolution Logic

### `ViewSet.get_manage_view_class()`

Priority: per-viewset field → global setting → `ManageView`

```python
def get_manage_view_class(self) -> Type[CrudView]:
    from django.utils.module_loading import import_string
    dotted = self.manage_view_class or crud_views_settings.manage_view_class
    if dotted:
        return import_string(dotted)
    return ManageView
```

### `GuardianViewSet.get_manage_view_class()`

Priority: per-viewset field → guardian global setting → `GuardianManageView`

```python
def get_manage_view_class(self) -> Type[CrudView]:
    from django.utils.module_loading import import_string
    from crud_views_guardian.lib.views import GuardianManageView
    dotted = self.manage_view_class or crud_views_settings.guardian_manage_view_class
    if dotted:
        return import_string(dotted)
    return GuardianManageView
```

### `register()` changes

Both `ViewSet.register()` and `GuardianViewSet.register()` replace the hard-coded class body with a dynamic `type()` call:

```python
base = self.get_manage_view_class()
AutoManageView = type("AutoManageView", (base,), {"model": self.model, "cv_viewset": self})
```

`GuardianViewSet.register()` still deletes the base manage view added by `super().register()` before creating its own.

## Error Handling

`import_string` raises `ImportError` with a clear message if the dotted path is invalid. No additional wrapping is needed — a misconfigured path fails loudly at server startup during the first viewset registration. No subclass validation is performed; an incorrect base class will produce an obvious traceback.

## Testing

Four new test cases:

1. **`ViewSet` — per-viewset field**: pass a dotted path to a `ManageView` subclass as `manage_view_class`; assert `get_all_views()["manage"]` is a subclass of it.
2. **`ViewSet` — global setting**: patch `crud_views_settings.manage_view_class`; instantiate a fresh viewset; assert the correct class is used.
3. **`ViewSet` — priority**: set both field and global setting; assert the per-viewset field wins.
4. **`GuardianViewSet`** variants: mirror tests 1–3 using `GuardianViewSet` and `crud_views_settings.guardian_manage_view_class`.

## Documentation

A new subsection in the manage view docs and guardian integration docs covering:

- The `manage_view_class` field on `ViewSet` / `GuardianViewSet`
- `CRUD_VIEWS_MANAGE_VIEW_CLASS` and `CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS` settings
- A short example wiring up a custom manage view subclass both ways

## Skill Update

Add a brief entry to the `django-crud-views` skill under the manage view and guardian sections documenting the `manage_view_class` field and the two Django settings.

## Files to Change

| File | Change |
|------|--------|
| `crud_views/lib/settings.py` | Add `manage_view_class` and `guardian_manage_view_class` settings |
| `crud_views/lib/viewset/__init__.py` | Add `manage_view_class` field; add `get_manage_view_class()`; update `register()` |
| `crud_views_guardian/lib/viewset.py` | Override `get_manage_view_class()`; update `register()` |
| `tests/test1/test_manage.py` | Add plain viewset tests |
| `tests/test1/test_guardian.py` | Add guardian tests |
| `docs/` | Add manage view customization subsection |
| `.claude/plugins/*/django-crud-views/skill.md` | Update skill |
