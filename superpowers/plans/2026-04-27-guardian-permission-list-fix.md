# Guardian Permission List Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix broken "list" and "parent" context action buttons in guardian-integrated views and revert a regression in `base.py` that breaks non-guardian per-row buttons.

**Architecture:** Two-change fix — revert `CrudViewPermissionRequiredMixin.cv_has_access` in `base.py` to not pass `obj` to `user.has_perms` (Django's ModelBackend returns empty perms for any object-aware call, breaking non-guardian views), then add a `cv_has_access` override to `GuardianQuerysetMixin` that always returns `True` (the list page is always accessible; guardian queryset filtering is the sole gate).

**Tech Stack:** Python, Django, django-guardian, pytest-django

---

## File Structure

| File | Change |
|---|---|
| `crud_views/lib/view/base.py` | Revert `obj=` from `user.has_perms` call (1-line change) |
| `crud_views_guardian/lib/mixins.py` | Add `cv_has_access` classmethod to `GuardianQuerysetMixin` |
| `tests/test1/test_guardian.py` | Add 3 new tests for list cv_has_access behaviour |

---

### Task 1: Revert base.py regression and fix GuardianQuerysetMixin

**Files:**
- Modify: `tests/test1/test_guardian.py`
- Modify: `crud_views/lib/view/base.py`
- Modify: `crud_views_guardian/lib/mixins.py`

#### Background

`CrudViewPermissionRequiredMixin.cv_has_access` in `crud_views/lib/view/base.py` currently reads:

```python
@classmethod
def cv_has_access(cls, user: User, obj: Model | None = None) -> bool:
    perm = cls.cv_viewset.permissions.get(cls.cv_permission)
    perms = (perm,) if perm else tuple()
    has_access = user.has_perms(perms, obj=obj if obj else None)
    return has_access
```

The `obj=obj if obj else None` argument is wrong: Django's `ModelBackend.get_all_permissions` returns an empty set whenever `obj is not None`, so any non-guardian view's `cv_has_access` called with a row object returns `False`. All per-row buttons disappear.

`GuardianQuerysetMixin` in `crud_views_guardian/lib/mixins.py` has no `cv_has_access` override, so the base model-level check runs. Guardian users have no model-level grants → "list" and "parent" buttons disappear.

The fix:
1. Revert `base.py` to `user.has_perms(perms)` (no obj).
2. Add `cv_has_access` to `GuardianQuerysetMixin` that returns `True` always — the list page is always accessible; queryset filtering is the gate.

- [ ] **Step 1: Write three failing tests**

Add these tests to the end of `tests/test1/test_guardian.py`:

```python
# ── cv_has_access for list views ──────────────────────────────────────────────


@pytest.mark.django_db
def test_list_cv_has_access_no_object_returns_true(user_guardian):
    """List cv_has_access returns True when no object — list is always accessible."""
    from tests.test1.app.views import GuardianAuthorListView

    assert GuardianAuthorListView.cv_has_access(user_guardian) is True


@pytest.mark.django_db
def test_list_cv_has_access_with_object_returns_true(user_guardian, author_douglas_adams):
    """List cv_has_access returns True even with an object (e.g. parent-button wrong-type case)."""
    from tests.test1.app.views import GuardianAuthorListView

    assert GuardianAuthorListView.cv_has_access(user_guardian, author_douglas_adams) is True


@pytest.mark.django_db
def test_non_guardian_cv_has_access_with_model_perm(client, cv_guardian_author, author_douglas_adams):
    """Non-guardian cv_has_access returns True when user has model-level perm (base.py revert check)."""
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import AuthorDetailView

    user = User.objects.create_user(username="model_perm_user", password="password")
    user_viewset_permission(user, cv_guardian_author, "view")
    user = User.objects.get(pk=user.pk)

    pk = author_douglas_adams.pk
    assert AuthorDetailView.cv_has_access(user, author_douglas_adams) is True
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test1/test_guardian.py::test_list_cv_has_access_no_object_returns_true tests/test1/test_guardian.py::test_list_cv_has_access_with_object_returns_true tests/test1/test_guardian.py::test_non_guardian_cv_has_access_with_model_perm -v
```

Expected: all 3 FAIL (first two fail because `GuardianQuerysetMixin` has no override yet; third may pass or fail depending on whether base.py is already reverted).

- [ ] **Step 3: Revert the obj-passing in base.py**

In `crud_views/lib/view/base.py`, change the last line of `CrudViewPermissionRequiredMixin.cv_has_access` from:

```python
        has_access = user.has_perms(perms, obj=obj if obj else None)
```

to:

```python
        has_access = user.has_perms(perms)
```

The full method after the change:

```python
@classmethod
def cv_has_access(cls, user: User, obj: Model | None = None) -> bool:
    perm = cls.cv_viewset.permissions.get(cls.cv_permission)
    perms = (perm,) if perm else tuple()
    has_access = user.has_perms(perms)
    return has_access
```

- [ ] **Step 4: Add cv_has_access to GuardianQuerysetMixin**

In `crud_views_guardian/lib/mixins.py`, add the following classmethod to `GuardianQuerysetMixin` immediately after `has_permission`:

```python
    @classmethod
    def cv_has_access(cls, user, obj=None):
        return True
```

The full `GuardianQuerysetMixin` after the change:

```python
class GuardianQuerysetMixin:
    """
    For list views.

    Filters get_queryset() to only objects the user has per-object permission on,
    via guardian's get_objects_for_user().

    cv_guardian_accept_global_perms = False (default): strict — only objects
    with an explicit per-object grant are returned.
    Set to True to also include objects accessible via model-level permission.

    Overrides has_permission() to always return True — queryset filtering is
    the sole access control mechanism for list views.

    Overrides cv_has_access() to always return True — the list page is always
    accessible; queryset filtering is the sole gate. This ensures "list" and
    "parent" context action buttons are always visible regardless of whether
    an object is provided.
    """

    cv_guardian_accept_global_perms: bool = False

    def has_permission(self):
        return True

    @classmethod
    def cv_has_access(cls, user, obj=None):
        return True

    def get_queryset(self):
        from guardian.shortcuts import get_objects_for_user

        qs = super().get_queryset()
        perm = self.cv_viewset.permissions.get(self.cv_permission)
        return get_objects_for_user(
            self.request.user,
            perm,
            qs,
            accept_global_perms=self.cv_guardian_accept_global_perms,
            use_groups=True,
        )
```

- [ ] **Step 5: Run all three new tests to verify they pass**

```bash
pytest tests/test1/test_guardian.py::test_list_cv_has_access_no_object_returns_true tests/test1/test_guardian.py::test_list_cv_has_access_with_object_returns_true tests/test1/test_guardian.py::test_non_guardian_cv_has_access_with_model_perm -v
```

Expected: all 3 PASS.

- [ ] **Step 6: Run the full test suite to check for regressions**

```bash
pytest tests/test1/ -v
```

Expected: 188 passed, 1 skipped (185 existing + 3 new).

- [ ] **Step 7: Commit**

```bash
git add crud_views/lib/view/base.py crud_views_guardian/lib/mixins.py tests/test1/test_guardian.py
git commit -m "fix: restore list button visibility in guardian views"
```
