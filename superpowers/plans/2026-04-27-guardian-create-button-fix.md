# Guardian Create Button Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the disabled "add" context button on child create views in guardian-integrated viewsets by adding a precise `cv_has_access` override to `GuardianCreateViewPermissionRequired`.

**Architecture:** Single method added to `GuardianCreateViewPermissionRequired` in `crud_views_guardian/lib/views.py`. Three cases: top-level creates fall through to model-level add perm; child creates with no object return True (dispatch enforces the real perm); child creates with the parent object available do a guardian per-object check on that parent.

**Tech Stack:** Python, Django, django-guardian, pytest-django

---

## File Structure

| File | Change |
|---|---|
| `crud_views_guardian/lib/views.py` | Add `cv_has_access` classmethod to `GuardianCreateViewPermissionRequired` |
| `tests/test1/test_guardian.py` | Add 7 unit tests covering all three cases |

---

### Task 1: Add cv_has_access to GuardianCreateViewPermissionRequired

**Files:**
- Modify: `crud_views_guardian/lib/views.py`
- Test: `tests/test1/test_guardian.py`

#### Background

`GuardianCreateViewPermissionRequired` is in `crud_views_guardian/lib/views.py` and currently has only a docstring and `pass`. It needs a `cv_has_access` classmethod.

The test app viewsets to use for testing:
- `GuardianAuthorCreateView` — top-level create (no parent), uses `cv_guardian_author`
- `GuardianBookCreateView` — child create (parent=`cv_guardian_publisher`), uses `cv_guardian_book` with `cv_guardian_parent_create_permission="change"`

Available test fixtures: `user_guardian` (a plain user with no permissions), `cv_guardian_author`, `cv_guardian_publisher`, `cv_guardian_book`, `publisher_a` (a Publisher instance), `book_under_publisher_a` (a Book under publisher_a).

Available helpers:
- `user_guardian_object_perm(user, viewset, perm_key, obj)` — from `tests.lib.helper.guardian`
- `user_viewset_permission(user, viewset, perm_key)` — from `tests.lib.helper.user` (model-level)

- [ ] **Step 1: Write 7 failing tests**

Add the following section to the end of `tests/test1/test_guardian.py`:

```python
# ── cv_has_access for create views ────────────────────────────────────────────


@pytest.mark.django_db
def test_create_cv_has_access_top_level_with_add_perm(user_guardian, cv_guardian_author):
    """Top-level create: True when user has model-level add perm."""
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import GuardianAuthorCreateView

    user_viewset_permission(user_guardian, cv_guardian_author, "add")
    user_guardian = User.objects.get(pk=user_guardian.pk)
    assert GuardianAuthorCreateView.cv_has_access(user_guardian) is True


@pytest.mark.django_db
def test_create_cv_has_access_top_level_without_add_perm(user_guardian):
    """Top-level create: False when user has no model-level add perm."""
    from tests.test1.app.views import GuardianAuthorCreateView

    assert GuardianAuthorCreateView.cv_has_access(user_guardian) is False


@pytest.mark.django_db
def test_create_cv_has_access_child_no_object_with_parent_perm(
    user_guardian, cv_guardian_publisher, publisher_a
):
    """Child create, obj=None: True even when user has parent perm (list-page case)."""
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    assert GuardianBookCreateView.cv_has_access(user_guardian, None) is True


@pytest.mark.django_db
def test_create_cv_has_access_child_no_object_without_parent_perm(user_guardian):
    """Child create, obj=None: True even when user has no parent perm (dispatch enforces)."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_has_access(user_guardian, None) is True


@pytest.mark.django_db
def test_create_cv_has_access_child_with_parent_obj_and_perm(
    user_guardian, cv_guardian_publisher, publisher_a
):
    """Child create, obj=parent instance: True when user has change perm on that parent."""
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    assert GuardianBookCreateView.cv_has_access(user_guardian, publisher_a) is True


@pytest.mark.django_db
def test_create_cv_has_access_child_with_parent_obj_without_perm(user_guardian, publisher_a):
    """Child create, obj=parent instance: False when user has no change perm on that parent."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_has_access(user_guardian, publisher_a) is False


@pytest.mark.django_db
def test_create_cv_has_access_child_wrong_type_obj(user_guardian, book_under_publisher_a):
    """Child create, obj=wrong model type: True (fallback — cannot determine access)."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_has_access(user_guardian, book_under_publisher_a) is True
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test1/test_guardian.py::test_create_cv_has_access_top_level_with_add_perm tests/test1/test_guardian.py::test_create_cv_has_access_top_level_without_add_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_no_object_with_parent_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_no_object_without_parent_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_with_parent_obj_and_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_with_parent_obj_without_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_wrong_type_obj -v
```

Expected: most FAIL (the method doesn't exist yet). The two `obj=None` tests may pass by accident since the base class is called — they still need the override to be correct.

- [ ] **Step 3: Implement cv_has_access in GuardianCreateViewPermissionRequired**

Replace the `pass` in `GuardianCreateViewPermissionRequired` in `crud_views_guardian/lib/views.py` with the full method. The complete class after the change:

```python
class GuardianCreateViewPermissionRequired(GuardianParentPermissionMixin, CreateViewPermissionRequired):
    """
    For top-level creates: GuardianParentPermissionMixin is a no-op (no parent).
    Django's PermissionRequiredMixin checks model-level add_<model> permission.

    For child creates: GuardianParentPermissionMixin checks per-object permission
    on the parent instance using cv_guardian_parent_create_permission (falls back
    to cv_guardian_parent_permission). No model-level add_<child> check is made.
    """

    @classmethod
    def cv_has_access(cls, user, obj=None):
        """
        Three-case permission check for create button visibility.

        Case 1 — Top-level create (cv_viewset.parent is None):
            Falls through to the base class, which checks the model-level
            add_<model> permission. Top-level creates intentionally require a
            model-level grant; there is no parent object to check against.

        Case 2 — Child create, no object (obj=None, e.g. book list page):
            Returns True unconditionally. The list page has no single object, so
            we cannot check the parent permission here. The real enforcement
            happens in dispatch() via GuardianParentPermissionMixin, which checks
            the parent object permission and raises 403 if denied. A user without
            the required grant will be stopped on click — the button showing is
            correct UX.

        Case 3 — Child create, parent object available (e.g. author detail page):
            When obj is an instance of the parent model, checks
            cv_guardian_parent_create_permission (falling back to
            cv_guardian_parent_permission) on that specific parent object via
            guardian's ObjectPermissionChecker. This gives precise per-object
            button visibility: "add book" only appears for parent objects the user
            is actually allowed to create children under.

            If obj is provided but is not an instance of the parent model
            (unexpected; wrong type passed by some other render path), falls back
            to True — cannot determine access without the right object type.
        """
        if cls.cv_viewset.parent is None:
            return super().cv_has_access(user, obj)

        if obj is None:
            return True

        parent_vs = cls.cv_viewset.parent.viewset
        if isinstance(obj, parent_vs.model):
            perm_key = (
                getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None)
                or getattr(cls.cv_viewset, "cv_guardian_parent_permission", "view")
            )
            perm = parent_vs.permissions.get(perm_key)
            accept_global = getattr(cls, "cv_guardian_accept_global_perms", False)
            if accept_global and user.has_perm(perm):
                return True
            from guardian.core import ObjectPermissionChecker

            return ObjectPermissionChecker(user).has_perm(perm.split(".")[1], obj)

        return True
```

- [ ] **Step 4: Run the 7 new tests to verify they pass**

```bash
pytest tests/test1/test_guardian.py::test_create_cv_has_access_top_level_with_add_perm tests/test1/test_guardian.py::test_create_cv_has_access_top_level_without_add_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_no_object_with_parent_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_no_object_without_parent_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_with_parent_obj_and_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_with_parent_obj_without_perm tests/test1/test_guardian.py::test_create_cv_has_access_child_wrong_type_obj -v
```

Expected: all 7 PASS.

- [ ] **Step 5: Run the full test suite**

```bash
pytest tests/test1/ -v
```

Expected: 195 passed, 1 skipped (188 existing + 7 new).

- [ ] **Step 6: Commit**

```bash
git add crud_views_guardian/lib/views.py tests/test1/test_guardian.py
git commit -m "fix: add precise cv_has_access to GuardianCreateViewPermissionRequired"
```
