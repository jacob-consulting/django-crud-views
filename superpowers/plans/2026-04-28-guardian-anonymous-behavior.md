# Guardian Anonymous User Behavior Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 500 crash when anonymous users hit guardian-protected views; make the anonymous-user response configurable per view via `cv_guardian_anonymous_behavior`.

**Architecture:** Add `cv_guardian_anonymous_behavior: str = "redirect"` to all three guardian mixins in `crud_views_guardian/lib/mixins.py`. Each mixin checks `is_authenticated` before any guardian call; the response (redirect/404/403) is controlled by the attribute. Single file change + 4 tests.

**Tech Stack:** Python, Django, django-guardian, pytest-django

---

## File Structure

| File | Change |
|---|---|
| `crud_views_guardian/lib/mixins.py` | Add `cv_guardian_anonymous_behavior` attribute and anonymous check to all three mixins |
| `tests/test1/test_guardian.py` | 4 new tests |

---

### Task 1: Fix guardian mixins + tests (TDD)

**Files:**
- Modify: `crud_views_guardian/lib/mixins.py`
- Test: `tests/test1/test_guardian.py`

#### Background

`crud_views_guardian/lib/mixins.py` has three mixins:

1. **`GuardianQuerysetMixin`** — list views. Overrides `has_permission()` to return `True`. `get_queryset()` calls `get_objects_for_user(self.request.user, ...)` which crashes on `AnonymousUser`.

2. **`GuardianObjectPermissionMixin`** — detail/update/delete views. Overrides `has_permission()` to return `True`. `get_object()` calls `ObjectPermissionChecker(user)` which crashes on `AnonymousUser`.

3. **`GuardianParentPermissionMixin`** — child views. `dispatch()` calls `ObjectPermissionChecker(request.user)` on the parent object, which crashes on `AnonymousUser`.

The fix: add `cv_guardian_anonymous_behavior: str = "redirect"` to each mixin and check `is_authenticated` before any guardian call.

Test URLs available (registered in test URL config):
- `GET /guardian_author/` — list view (`GuardianQuerysetMixin`)
- `GET /guardian_author/<pk>/detail/` — detail view (`GuardianObjectPermissionMixin`)
- `GET /guardian_publisher/<pk>/guardian_book/` — child list view (`GuardianParentPermissionMixin`)

The `client` fixture (no `force_login`) gives an anonymous client. Default Django `LOGIN_URL` is `/accounts/login/`.

---

- [ ] **Step 1: Write 4 failing tests**

Append to `tests/test1/test_guardian.py`:

```python
@pytest.mark.django_db
def test_guardian_anonymous_list_redirects(client, cv_guardian_author):
    """Anonymous user on list view gets redirect to login (not 500)."""
    response = client.get("/guardian_author/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_guardian_anonymous_detail_redirects(client, cv_guardian_author, author_douglas_adams):
    """Anonymous user on detail view gets redirect to login (not 500)."""
    pk = author_douglas_adams.pk
    response = client.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_guardian_anonymous_child_list_redirects(client, cv_guardian_publisher, publisher_a):
    """Anonymous user on child list view gets redirect to login (not 500)."""
    pk = publisher_a.pk
    response = client.get(f"/guardian_publisher/{pk}/guardian_book/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_guardian_anonymous_behavior_404(client, cv_guardian_author, monkeypatch):
    """cv_guardian_anonymous_behavior='404' returns 404 for anonymous users."""
    from crud_views_guardian.lib.mixins import GuardianQuerysetMixin
    monkeypatch.setattr(GuardianQuerysetMixin, "cv_guardian_anonymous_behavior", "404")
    response = client.get("/guardian_author/")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alex/projects/alex/django-crud-views && python -m pytest tests/test1/test_guardian.py -v -k "anonymous" 2>&1 | tail -20
```

Expected: 4 FAILs — either 500 errors or wrong status codes.

- [ ] **Step 3: Add `cv_guardian_anonymous_behavior` and the anonymous check to all three mixins**

Open `crud_views_guardian/lib/mixins.py`. Add `from django.http import Http404` to the imports at the top.

Replace the `GuardianQuerysetMixin` class with:

```python
class GuardianQuerysetMixin:
    """
    For list views.

    Filters get_queryset() to only objects the user has per-object permission on,
    via guardian's get_objects_for_user().

    cv_guardian_accept_global_perms = False (default): strict — only objects
    with an explicit per-object grant are returned.
    Set to True to also include objects accessible via model-level permission.

    Overrides has_permission() to always return True for authenticated users —
    queryset filtering is the sole access control mechanism for list views.

    For anonymous users, behaviour is controlled by cv_guardian_anonymous_behavior:
    "redirect" (default): redirect to login via Django's handle_no_permission().
    "404": raise Http404.
    "403": raise PermissionDenied.

    Overrides cv_has_access() to always return True — the list page is always
    accessible; queryset filtering is the sole gate. This ensures "list" and
    "parent" context action buttons are always visible regardless of whether
    an object is provided.
    """

    cv_guardian_accept_global_perms: bool = False
    cv_guardian_anonymous_behavior: str = "redirect"

    def has_permission(self):
        if not self.request.user.is_authenticated:
            if self.cv_guardian_anonymous_behavior == "404":
                raise Http404
            if self.cv_guardian_anonymous_behavior == "403":
                raise PermissionDenied
            return False  # triggers Django's handle_no_permission() → redirect to login
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

Replace the `GuardianObjectPermissionMixin` class with:

```python
class GuardianObjectPermissionMixin:
    """
    For single-object views (Detail, Update, Delete, Action).

    Hooks into get_object(): after the object is loaded, checks per-object
    permission. Raises 403 on denial.

    cv_guardian_accept_global_perms = False (default): uses ObjectPermissionChecker
    which checks only guardian's object-level tables — no model-level fallback.
    Set to True to use user.has_perm(perm, obj) which includes model-level fallback.

    Also overrides cv_has_access() so per-row action buttons in list views
    reflect per-object access correctly.

    Overrides has_permission() to always return True for authenticated users —
    model-level permission is not required; all access control is delegated to
    get_object().

    For anonymous users, behaviour is controlled by cv_guardian_anonymous_behavior:
    "redirect" (default): redirect to login via Django's handle_no_permission().
    "404": raise Http404.
    "403": raise PermissionDenied.
    """

    cv_guardian_accept_global_perms: bool = False
    cv_guardian_anonymous_behavior: str = "redirect"

    def has_permission(self):
        if not self.request.user.is_authenticated:
            if self.cv_guardian_anonymous_behavior == "404":
                raise Http404
            if self.cv_guardian_anonymous_behavior == "403":
                raise PermissionDenied
            return False  # triggers Django's handle_no_permission() → redirect to login
        return True

    def _check_object_perm(self, user, perm: str, obj) -> bool:
        if self.cv_guardian_accept_global_perms:
            # Check model-level perm first (without obj — ModelBackend returns empty
            # set when obj is passed, so we must call has_perm without obj here).
            if user.has_perm(perm):
                return True
        from guardian.core import ObjectPermissionChecker

        checker = ObjectPermissionChecker(user)
        return checker.has_perm(perm.split(".")[1], obj)

    def get_object(self):
        obj = super().get_object()
        perm = self.cv_viewset.permissions.get(self.cv_permission)
        if not self._check_object_perm(self.request.user, perm, obj):
            raise PermissionDenied
        return obj

    @classmethod
    def cv_has_access(cls, user, obj=None):
        perm = cls.cv_viewset.permissions.get(cls.cv_permission)
        if obj is not None:
            if cls.cv_guardian_accept_global_perms:
                # Model-level perm must be checked without obj (ModelBackend ignores
                # obj and returns empty set when obj is passed).
                if user.has_perm(perm):
                    return True
            from guardian.core import ObjectPermissionChecker

            checker = ObjectPermissionChecker(user)
            return checker.has_perm(perm.split(".")[1], obj)
        return False
```

In `GuardianParentPermissionMixin`, add the attribute and the anonymous check at the top of `dispatch()`:

```python
class GuardianParentPermissionMixin:
    """
    For child viewset views (any view type where cv_viewset.parent is set).

    In dispatch(), before any other processing, checks per-object permission
    on the parent instance. Raises 403 if denied. No-op when cv_viewset.parent
    is None.

    Reads cv_guardian_parent_permission / cv_guardian_parent_create_permission
    from the child GuardianViewSet. Respects cv_guardian_accept_global_perms
    from the combined view class.

    When a parent viewset is present, overrides has_permission() to return True
    so that Django's model-level PermissionRequiredMixin is bypassed; the parent
    object-level check in dispatch() is the sole gatekeeper.

    For anonymous users, behaviour is controlled by cv_guardian_anonymous_behavior:
    "redirect" (default): redirect to login via Django's handle_no_permission().
    "404": raise Http404.
    "403": raise PermissionDenied.
    """

    cv_guardian_anonymous_behavior: str = "redirect"

    def has_permission(self):
        if self.cv_viewset.parent is not None:
            return True
        return super().has_permission()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if self.cv_guardian_anonymous_behavior == "404":
                raise Http404
            if self.cv_guardian_anonymous_behavior == "403":
                raise PermissionDenied
            return self.handle_no_permission()  # redirect to login
        parent_vs = self.cv_viewset.parent
        if parent_vs is not None:
            is_create = getattr(self, "cv_permission", None) == "add"
            perm_key = None
            if is_create:
                perm_key = getattr(self.cv_viewset, "cv_guardian_parent_create_permission", None)
            if perm_key is None:
                perm_key = getattr(self.cv_viewset, "cv_guardian_parent_permission", "view")

            if perm_key is not None:
                parent_pk = kwargs.get(parent_vs.get_pk_name())
                parent_obj = get_object_or_404(parent_vs.viewset.model, pk=parent_pk)
                parent_perm = parent_vs.viewset.permissions.get(perm_key)
                accept_global = getattr(self, "cv_guardian_accept_global_perms", False)
                if accept_global:
                    has_perm = request.user.has_perm(parent_perm, parent_obj)
                else:
                    from guardian.core import ObjectPermissionChecker

                    checker = ObjectPermissionChecker(request.user)
                    has_perm = checker.has_perm(parent_perm.split(".")[1], parent_obj)
                if not has_perm:
                    raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
```

- [ ] **Step 4: Run failing tests to verify they now pass**

```bash
cd /home/alex/projects/alex/django-crud-views && python -m pytest tests/test1/test_guardian.py -v -k "anonymous" 2>&1 | tail -20
```

Expected: 4 PASSes.

- [ ] **Step 5: Run full test suite to verify no regressions**

```bash
cd /home/alex/projects/alex/django-crud-views && python -m pytest tests/test1/ -q 2>&1 | tail -5
```

Expected: 204+ passed, 1 skipped, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add crud_views_guardian/lib/mixins.py tests/test1/test_guardian.py
git commit -m "fix: redirect anonymous users from guardian views, add cv_guardian_anonymous_behavior"
```

---

## Self-Review

**Spec coverage:**
- ✅ `cv_guardian_anonymous_behavior: str = "redirect"` on all three mixins
- ✅ `"redirect"` → `return False` in `has_permission()` (triggers Django login redirect) / `handle_no_permission()` in `dispatch()`
- ✅ `"404"` → `raise Http404`
- ✅ `"403"` → `raise PermissionDenied`
- ✅ Anonymous check fires before any guardian call
- ✅ 4 tests: list redirect, detail redirect, child list redirect, "404" override

**Placeholder scan:** None found.

**Type consistency:** `cv_guardian_anonymous_behavior` declared as `str` consistently across all three mixins.
