# Guardian Child Create Button Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix guardian child create button visibility so it respects per-object permissions on the parent instead of always showing or always hiding.

**Architecture:** Three coordinated changes: (1) `GuardianCreateViewPermissionRequired.cv_has_access` Case 2 becomes `False`; (2) a new `cv_create_has_access` classmethod on `GuardianCreateViewPermissionRequired` encapsulates the correct guardian perm check and is overrideable per-view; (3) `GuardianQuerysetMixin.cv_get_context` resolves the parent object from URL kwargs and calls `cv_create_has_access`, bridging the gap between the instance-level URL context and the classmethod-level access check.

**Tech Stack:** Python, Django, django-guardian, pytest

---

## File Map

| File | Change |
|---|---|
| `crud_views_guardian/lib/views.py` | Add `cv_create_has_access` classmethod to `GuardianCreateViewPermissionRequired`; change Case 2 of `cv_has_access` from `return True` → `return False` |
| `crud_views_guardian/lib/mixins.py` | Add `cv_get_context` override to `GuardianQuerysetMixin` |
| `tests/test1/test_guardian.py` | Update two existing Case 2 tests; add six new tests |
| `src/meinamm/views/netzwerk_member.py` | `NetzwerkMemberCreateView`: swap `CreateViewPermissionRequired` → `GuardianCreateViewPermissionRequired` |
| `src/meinamm/views/projekt_member.py` | `ProjektMemberCreateView`: same swap |

---

## Task 1: Change cv_has_access Case 2 to False and update existing tests

**Files:**
- Modify: `tests/test1/test_guardian.py`
- Modify: `crud_views_guardian/lib/views.py:64-112`

Both existing tests for Case 2 (`obj=None`, has parent) currently assert `True`. They will fail once we change the implementation. Update them first so the test file expresses the target state, then implement.

- [ ] **Step 1: Update the two existing Case 2 tests to assert False**

In `tests/test1/test_guardian.py`, find and update these two tests:

```python
@pytest.mark.django_db
def test_create_cv_has_access_child_no_object_with_parent_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """Child create, obj=None: False — parent obj is not available so access cannot be confirmed."""
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    assert GuardianBookCreateView.cv_has_access(user_guardian, None) is False


@pytest.mark.django_db
def test_create_cv_has_access_child_no_object_without_parent_perm(user_guardian):
    """Child create, obj=None: False — no parent obj, cannot determine access."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_has_access(user_guardian, None) is False
```

- [ ] **Step 2: Run the updated tests to verify they FAIL (implementation still returns True)**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -k "child_no_object" -v
```

Expected: 2 FAILs — `AssertionError: assert True is False`

- [ ] **Step 3: Change Case 2 in GuardianCreateViewPermissionRequired.cv_has_access**

In `crud_views_guardian/lib/views.py`, change line `return True` in the `if obj is None:` branch:

```python
    @classmethod
    def cv_has_access(cls, user, obj=None):
        """
        Three-case permission check for create button visibility.
        ...
        """
        if cls.cv_viewset.parent is None:
            return super().cv_has_access(user, obj)

        if obj is None:
            return False  # was: return True — GuardianQuerysetMixin.cv_get_context handles the real check

        parent_vs = cls.cv_viewset.parent.viewset
        if isinstance(obj, parent_vs.model):
            perm_key = getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None) or getattr(
                cls.cv_viewset, "cv_guardian_parent_permission", "view"
            )
            perm = parent_vs.permissions.get(perm_key)
            accept_global = getattr(cls, "cv_guardian_accept_global_perms", False)
            if accept_global and user.has_perm(perm):
                return True
            from guardian.core import ObjectPermissionChecker

            return ObjectPermissionChecker(user).has_perm(perm.split(".")[1], obj)

        return True
```

- [ ] **Step 4: Run the full guardian test suite to verify only the two updated tests now pass (no regressions)**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -v
```

Expected: all tests pass including the two Case 2 tests now expecting `False`.

- [ ] **Step 5: Commit**

```bash
git add crud_views_guardian/lib/views.py tests/test1/test_guardian.py
git commit -m "fix: guardian child create cv_has_access Case 2 returns False (safe fallback)"
```

---

## Task 2: Add cv_create_has_access classmethod to GuardianCreateViewPermissionRequired

**Files:**
- Modify: `tests/test1/test_guardian.py`
- Modify: `crud_views_guardian/lib/views.py`

`cv_create_has_access` is the hook that does the actual guardian perm check (or custom logic when overridden). It will be called by `GuardianQuerysetMixin.cv_get_context` in Task 3.

- [ ] **Step 1: Write the three failing tests**

Add to `tests/test1/test_guardian.py` after the `# ── cv_has_access for create views` section:

```python
# ── cv_create_has_access ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cv_create_has_access_returns_false_when_parent_obj_is_none(user_guardian):
    """Default cv_create_has_access returns False when parent_obj is None."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_create_has_access(user_guardian, None, None) is False


@pytest.mark.django_db
def test_cv_create_has_access_returns_true_with_parent_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """Default cv_create_has_access returns True when user has required guardian perm on parent."""
    from tests.test1.app.views import GuardianBookCreateView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    assert GuardianBookCreateView.cv_create_has_access(user_guardian, None, publisher_a) is True


@pytest.mark.django_db
def test_cv_create_has_access_returns_false_without_parent_perm(user_guardian, publisher_a):
    """Default cv_create_has_access returns False when user lacks required guardian perm on parent."""
    from tests.test1.app.views import GuardianBookCreateView

    assert GuardianBookCreateView.cv_create_has_access(user_guardian, None, publisher_a) is False
```

- [ ] **Step 2: Run to verify all three fail**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -k "cv_create_has_access" -v
```

Expected: 3 FAILs — `AttributeError: type object 'GuardianBookCreateView' has no attribute 'cv_create_has_access'`

- [ ] **Step 3: Add cv_create_has_access to GuardianCreateViewPermissionRequired in views.py**

Add the classmethod inside `GuardianCreateViewPermissionRequired`, immediately before the existing `cv_has_access` method. The full updated class body in `crud_views_guardian/lib/views.py` becomes:

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
    def cv_create_has_access(cls, user, rendering_view, parent_obj):
        """
        Determine whether the create button should be visible for this child viewset.

        Called by GuardianQuerysetMixin.cv_get_context() when rendering the create
        context action from a list view where obj=None. The list view resolves the
        parent object from its URL kwargs and passes it here.

        Default implementation checks cv_guardian_parent_create_permission (falling
        back to cv_guardian_parent_permission) on the parent object via guardian's
        ObjectPermissionChecker. Override in subclasses for custom logic.

        Args:
            user: the requesting user
            rendering_view: the view instance that is rendering the button
                (e.g. NetzwerkMemberListView) — provides access to
                rendering_view.request, rendering_view.kwargs, etc.
            parent_obj: the resolved parent model instance, or None if resolution
                failed (returns False in that case)
        """
        if parent_obj is None:
            return False
        perm_key = (
            getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None)
            or getattr(cls.cv_viewset, "cv_guardian_parent_permission", "view")
        )
        perm = cls.cv_viewset.parent.viewset.permissions.get(perm_key)
        from guardian.core import ObjectPermissionChecker

        return ObjectPermissionChecker(user).has_perm(perm.split(".")[1], parent_obj)

    @classmethod
    def cv_has_access(cls, user, obj=None):
        """
        Three-case permission check for create button visibility.

        Case 1 — Top-level create (cv_viewset.parent is None):
            Falls through to the base class, which checks the model-level
            add_<model> permission.

        Case 2 — Child create, no object (obj=None, e.g. book list page):
            Returns False. GuardianQuerysetMixin.cv_get_context() handles the
            real check by resolving the parent from URL kwargs and calling
            cv_create_has_access(). This is a safe fallback for any call path
            that bypasses the list view override.

        Case 3 — Child create, parent object available (e.g. author detail page):
            Checks cv_guardian_parent_create_permission on the parent object.
        """
        if cls.cv_viewset.parent is None:
            return super().cv_has_access(user, obj)

        if obj is None:
            return False  # was: return True — list view override handles the real check

        parent_vs = cls.cv_viewset.parent.viewset
        if isinstance(obj, parent_vs.model):
            perm_key = getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None) or getattr(
                cls.cv_viewset, "cv_guardian_parent_permission", "view"
            )
            perm = parent_vs.permissions.get(perm_key)
            accept_global = getattr(cls, "cv_guardian_accept_global_perms", False)
            if accept_global and user.has_perm(perm):
                return True
            from guardian.core import ObjectPermissionChecker

            return ObjectPermissionChecker(user).has_perm(perm.split(".")[1], obj)

        return True
```

- [ ] **Step 4: Run the three new tests to verify they pass**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -k "cv_create_has_access" -v
```

Expected: 3 PASSes.

- [ ] **Step 5: Run full guardian suite to check for regressions**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add crud_views_guardian/lib/views.py tests/test1/test_guardian.py
git commit -m "feat: add cv_create_has_access classmethod to GuardianCreateViewPermissionRequired"
```

---

## Task 3: Add cv_get_context override to GuardianQuerysetMixin

**Files:**
- Modify: `tests/test1/test_guardian.py`
- Modify: `crud_views_guardian/lib/mixins.py`

This override is the bridge: it runs as an instance method (has access to `self.kwargs`), resolves the parent object, and calls `cv_create_has_access` with it. It also ensures a subclass override of `cv_create_has_access` is respected.

`GuardianBookListView` is the test vehicle — it extends `GuardianListViewPermissionRequired` which includes `GuardianQuerysetMixin`. Its parent is `cv_guardian_publisher`. The parent PK kwarg in the URL is `"guardian_publisher_pk"` (the default: `f"{parent_viewset.name}_pk"`).

- [ ] **Step 1: Write three failing tests**

Add to `tests/test1/test_guardian.py` after the `cv_create_has_access` section:

```python
# ── GuardianQuerysetMixin.cv_get_context create button ────────────────────────


def _make_book_list_view(user_guardian, publisher_a):
    """Instantiate GuardianBookListView with request and URL kwargs for publisher_a."""
    from django.test import RequestFactory
    from tests.test1.app.views import GuardianBookListView

    rf = RequestFactory()
    request = rf.get(f"/guardian_publisher/{publisher_a.pk}/guardian_book/")
    request.user = user_guardian

    view = GuardianBookListView()
    view.request = request
    view.args = []
    view.kwargs = {"guardian_publisher_pk": str(publisher_a.pk)}
    return view


@pytest.mark.django_db
def test_cv_get_context_create_with_parent_perm_shows_button(user_guardian, cv_guardian_publisher, publisher_a):
    """cv_get_context resolves parent and grants access when user has change perm on parent."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    view = _make_book_list_view(user_guardian, publisher_a)
    ctx = view.cv_get_context(key="create", obj=None, user=user_guardian)
    assert ctx["cv_access"] is True


@pytest.mark.django_db
def test_cv_get_context_create_without_parent_perm_hides_button(user_guardian, publisher_a):
    """cv_get_context resolves parent and denies access when user lacks change perm on parent."""
    view = _make_book_list_view(user_guardian, publisher_a)
    ctx = view.cv_get_context(key="create", obj=None, user=user_guardian)
    assert ctx["cv_access"] is False


@pytest.mark.django_db
def test_cv_get_context_non_create_key_not_affected(user_guardian, cv_guardian_publisher, publisher_a,
                                                     book_under_publisher_a):
    """cv_get_context override does not interfere with non-create keys (e.g. detail, update)."""
    from tests.test1.app.views import GuardianBookListView

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)

    view = _make_book_list_view(user_guardian, publisher_a)
    # "detail" is a per-row action (requires obj), not a context action —
    # passing the book as obj so cv_get_cls_assert_object doesn't complain
    # The override must not patch cv_access when key != "create"
    from tests.lib.helper.guardian import user_guardian_object_perm as _perm
    from tests.test1.app.views import cv_guardian_book
    _perm(user_guardian, cv_guardian_book, "view", book_under_publisher_a)
    ctx = view.cv_get_context(key="detail", obj=book_under_publisher_a, user=user_guardian)
    # cv_access for detail is determined by GuardianObjectPermissionMixin.cv_has_access, not our override
    assert ctx["cv_access"] is True


@pytest.mark.django_db
def test_cv_get_context_respects_cv_create_has_access_override(user_guardian, publisher_a):
    """An override of cv_create_has_access on the create view class is called by cv_get_context."""
    from django.test import RequestFactory
    from tests.test1.app.views import GuardianBookListView, GuardianBookCreateView

    # Temporarily override cv_create_has_access to always return True regardless of perms
    original = GuardianBookCreateView.cv_create_has_access

    @classmethod
    def always_true(cls, user, rendering_view, parent_obj):
        return True

    GuardianBookCreateView.cv_create_has_access = always_true
    try:
        view = _make_book_list_view(user_guardian, publisher_a)
        # user has no perm on publisher_a, but override returns True
        ctx = view.cv_get_context(key="create", obj=None, user=user_guardian)
        assert ctx["cv_access"] is True
    finally:
        GuardianBookCreateView.cv_create_has_access = original
```

- [ ] **Step 2: Run to verify all four fail**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -k "cv_get_context" -v
```

Expected: first 2 FAILs (`AssertionError`), third PASS (detail key unaffected by non-existent override), fourth FAIL or error. Note which ones fail — confirms the override isn't there yet.

- [ ] **Step 3: Add cv_get_context override to GuardianQuerysetMixin in mixins.py**

Add the method inside `GuardianQuerysetMixin`, after `cv_has_access`:

```python
    def cv_get_context(self, key=None, obj=None, user=None, request=None):
        """
        Override to fix create button visibility for child viewsets under guardian.

        cv_has_access() is a classmethod with no access to the request or URL
        kwargs. When a create context action is rendered from a list page, obj=None
        and the parent object cannot be determined inside cv_has_access() alone.

        This override detects that situation (obj=None, target is a child create
        view, viewset has a parent), resolves the parent object from self.kwargs
        using the existing cv_get_parent_object() helper, and delegates to
        target_cls.cv_create_has_access() with the resolved parent. The result
        replaces cv_access in the already-built context dict — no other context
        fields are affected.
        """
        ctx = super().cv_get_context(key=key, obj=obj, user=user, request=request)

        if obj is None and key is not None and self.cv_viewset.has_parent:
            if self.cv_viewset.is_view_registered(key):
                target_cls = self.cv_viewset.get_view_class(key)
            else:
                target_cls = None
            if target_cls and getattr(target_cls, "cv_permission", None) == "add":
                if hasattr(target_cls, "cv_create_has_access"):
                    try:
                        parent_obj = self.cv_get_parent_object()
                    except Exception:
                        parent_obj = None
                    ctx["cv_access"] = target_cls.cv_create_has_access(user, self, parent_obj)

        return ctx
```

- [ ] **Step 4: Run the four new tests**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -k "cv_get_context" -v
```

Expected: all 4 pass.

- [ ] **Step 5: Run the full guardian suite**

```bash
uv run --with ".[bootstrap5,polymorphic,workflow,ordered,test]" pytest tests/test1/test_guardian.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add crud_views_guardian/lib/mixins.py tests/test1/test_guardian.py
git commit -m "feat: GuardianQuerysetMixin.cv_get_context resolves parent for child create button"
```

---

## Task 4: Fix application views in meinamm

**Files:**
- Modify: `src/meinamm/views/netzwerk_member.py`
- Modify: `src/meinamm/views/projekt_member.py`

Both create views currently extend `CreateViewPermissionRequired`. They must switch to `GuardianCreateViewPermissionRequired` so that:
- `GuardianParentPermissionMixin.has_permission()` bypasses the model-level perm check when the form page loads
- `cv_has_access` Case 3 fires correctly when the create button appears in a context where `obj` IS the parent instance
- The view picks up the default `cv_create_has_access` implementation (used by `cv_get_context` in Task 3)

Note: these files live in the `dpl-examples` repo, not the submodule. Run git commands from there.

- [ ] **Step 1: Update imports and base class in netzwerk_member.py**

Both files already import from `crud_views_guardian.lib.views` — only add `GuardianCreateViewPermissionRequired` to that existing import and remove `CreateViewPermissionRequired` from the `crud_views.lib.views` import.

In `src/meinamm/views/netzwerk_member.py`:

```python
# change:
from crud_views.lib.views import (
    ListViewTableMixin, CreateViewPermissionRequired, CreateViewParentMixin,
    MessageMixin, )
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired, GuardianUpdateViewPermissionRequired, \
    GuardianDeleteViewPermissionRequired

# to:
from crud_views.lib.views import (
    ListViewTableMixin, CreateViewParentMixin,
    MessageMixin, )
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired, GuardianUpdateViewPermissionRequired, \
    GuardianDeleteViewPermissionRequired, GuardianCreateViewPermissionRequired
```

Then change the view class base:

```python
class NetzwerkMemberCreateView(DplCrudViewMenuMixin, DplViewMixin, MessageMixin, CreateViewParentMixin,
                               GuardianCreateViewPermissionRequired):
    form_class = NetzwerkMemberCreateForm
    cv_viewset = cv_netzwerk_members
    cv_message = "Netzwerkmitglied »{object}« wurde hinzugefügt."
    cv_icon_action = "ba-icon-plus"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        parent_object = self.cv_get_parent_object()
        kwargs["parent_object"] = parent_object
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        return form
```

- [ ] **Step 2: Update imports and base class in projekt_member.py**

In `src/meinamm/views/projekt_member.py`, apply the identical import change:

```python
# change:
from crud_views.lib.views import (
    ListViewTableMixin, CreateViewPermissionRequired, CreateViewParentMixin,
    MessageMixin, )
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired, GuardianUpdateViewPermissionRequired, \
    GuardianDeleteViewPermissionRequired

# to:
from crud_views.lib.views import (
    ListViewTableMixin, CreateViewParentMixin,
    MessageMixin, )
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired, GuardianUpdateViewPermissionRequired, \
    GuardianDeleteViewPermissionRequired, GuardianCreateViewPermissionRequired
```

Then change the view class base:

```python
class ProjektMemberCreateView(DplCrudViewMenuMixin, DplViewMixin, MessageMixin, CreateViewParentMixin,
                              GuardianCreateViewPermissionRequired):
    form_class = ProjektMemberCreateForm
    cv_viewset = cv_projekt_member
    cv_message = "Projektmitglied »{object}« wurde hinzugefügt."
    cv_icon_action = "ba-icon-plus"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        parent_object = self.cv_get_parent_object()
        kwargs["parent_object"] = parent_object
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        return form
```

- [ ] **Step 3: Verify no import errors**

```bash
python -c "from meinamm.views.netzwerk_member import NetzwerkMemberCreateView; print('OK')"
python -c "from meinamm.views.projekt_member import ProjektMemberCreateView; print('OK')"
```

Expected: `OK` for both.

- [ ] **Step 4: Commit (from dpl-examples repo root)**

```bash
git add src/meinamm/views/netzwerk_member.py src/meinamm/views/projekt_member.py
git commit -m "fix: use GuardianCreateViewPermissionRequired in member create views"
```
