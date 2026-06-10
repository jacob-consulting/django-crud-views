# Guardian Anonymous User Behavior — Design Spec

**Date:** 2026-04-28
**Status:** Approved
**Scope:** Fix crash when anonymous users hit guardian-protected views; make anonymous-user response configurable per view

---

## Problem

All three guardian mixins override `has_permission()` (or `dispatch()`) to return `True`, bypassing Django's authentication redirect. When an anonymous user reaches guardian internals — `get_objects_for_user()`, `ObjectPermissionChecker`, or a parent pk lookup — guardian calls `User.objects.get(pk=None)` which raises `User.DoesNotExist` and produces a 500 error.

---

## Solution

Add `cv_guardian_anonymous_behavior: str = "redirect"` to all three guardian mixins. When an unauthenticated user is detected, each mixin responds according to this attribute before any guardian call is made.

### Attribute

| Value | Behaviour |
|---|---|
| `"redirect"` | Redirect to login (default — standard Django unauthenticated flow) |
| `"404"` | Raise `Http404` |
| `"403"` | Raise `PermissionDenied` |

Declared independently on each mixin with the same default. Overridden on individual view classes as needed:

```python
class MyDetailView(GuardianDetailViewPermissionRequired):
    cv_guardian_anonymous_behavior = "404"
```

### Per-mixin implementation

**`GuardianQuerysetMixin`** — check in `has_permission()`:

```python
cv_guardian_anonymous_behavior: str = "redirect"

def has_permission(self):
    if not self.request.user.is_authenticated:
        if self.cv_guardian_anonymous_behavior == "404":
            raise Http404
        if self.cv_guardian_anonymous_behavior == "403":
            raise PermissionDenied
        return False  # triggers Django's handle_no_permission() → redirect to login
    return True
```

**`GuardianObjectPermissionMixin`** — check in `has_permission()`:

```python
cv_guardian_anonymous_behavior: str = "redirect"

def has_permission(self):
    if not self.request.user.is_authenticated:
        if self.cv_guardian_anonymous_behavior == "404":
            raise Http404
        if self.cv_guardian_anonymous_behavior == "403":
            raise PermissionDenied
        return False
    return True
```

**`GuardianParentPermissionMixin`** — check at the top of `dispatch()`, before any parent pk lookup:

```python
cv_guardian_anonymous_behavior: str = "redirect"

def dispatch(self, request, *args, **kwargs):
    if not request.user.is_authenticated:
        if self.cv_guardian_anonymous_behavior == "404":
            raise Http404
        if self.cv_guardian_anonymous_behavior == "403":
            raise PermissionDenied
        return self.handle_no_permission()  # redirect to login
    # ... existing parent permission logic
```

---

## Files Changed

| File | Change |
|---|---|
| `crud_views_guardian/lib/mixins.py` | Add `cv_guardian_anonymous_behavior` and anonymous check to all three mixins |
| `tests/test1/test_guardian.py` | 4 new tests |

---

## Testing

| Test | Setup | Expected |
|---|---|---|
| `test_guardian_anonymous_list_redirects` | Anonymous client GET list URL | 302 → login |
| `test_guardian_anonymous_detail_redirects` | Anonymous client GET detail URL | 302 → login |
| `test_guardian_anonymous_child_list_redirects` | Anonymous client GET child list URL | 302 → login |
| `test_guardian_anonymous_behavior_404` | View subclass with `cv_guardian_anonymous_behavior = "404"`, anonymous GET | 404 |

The "404" test uses a dynamically-defined view subclass registered to a temporary URL pattern, or monkeypatches the attribute on an existing view within the test scope.
