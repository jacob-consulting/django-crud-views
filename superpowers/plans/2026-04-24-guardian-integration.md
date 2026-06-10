# Guardian Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `crud_views_guardian` sub-package that provides per-object permissions via django-guardian, with drop-in `Guardian*ViewPermissionRequired` classes and a `GuardianViewSet`.

**Architecture:** Three mixins hook into `get_object()`, `get_queryset()`, and `dispatch()` respectively. `GuardianObjectPermissionMixin` uses `ObjectPermissionChecker` for strict per-object checks (no model-level fallback by default). `GuardianQuerysetMixin` filters list querysets via `get_objects_for_user`. `GuardianParentPermissionMixin` checks per-object permission on the parent instance before dispatching child views.

**Tech Stack:** django-guardian ≥ 2.4, pytest-django, existing crud_views test infrastructure.

---

## File Map

**Create:**
- `crud_views_guardian/__init__.py` — package marker
- `crud_views_guardian/apps.py` — `CrudViewsGuardianConfig`
- `crud_views_guardian/lib/__init__.py` — package marker
- `crud_views_guardian/lib/mixins.py` — `GuardianObjectPermissionMixin`, `GuardianQuerysetMixin`, `GuardianParentPermissionMixin`
- `crud_views_guardian/lib/views.py` — `Guardian*ViewPermissionRequired` drop-in classes
- `crud_views_guardian/lib/viewset.py` — `GuardianViewSet`
- `tests/lib/helper/guardian.py` — `user_guardian_object_perm` test helper
- `tests/test1/test_guardian.py` — all guardian tests

**Modify:**
- `pyproject.toml` — add `guardian` optional dep; add `guardian` to `test` deps
- `tests/test1/conftest.py` — add guardian to `INSTALLED_APPS`, `AUTHENTICATION_BACKENDS`, `ANONYMOUS_USER_NAME`; add guardian fixtures
- `tests/test1/app/views.py` — add `cv_guardian_author`, `cv_guardian_book` guardian viewsets and views
- `tests/test1/app/urls.py` — register guardian viewset URL patterns
- `examples/bootstrap5/app/views/author.py` — swap to `GuardianViewSet` + `Guardian*` view classes
- `examples/bootstrap5/app/views/book.py` — swap to `GuardianViewSet` + `Guardian*` view classes
- `examples/bootstrap5/app/settings.py` — add guardian to `INSTALLED_APPS`, `AUTHENTICATION_BACKENDS`
- `mkdocs.yml` — add `guardian.md` to navigation
- `README.md` — add guardian to optional integrations section
- `docs/guardian.md` — new documentation page (create)

---

## Task 1: Package Scaffold

**Files:**
- Create: `crud_views_guardian/__init__.py`
- Create: `crud_views_guardian/apps.py`
- Create: `crud_views_guardian/lib/__init__.py`

- [ ] **Step 1: Create `crud_views_guardian/__init__.py`**

```python
# crud_views_guardian/__init__.py
```

- [ ] **Step 2: Create `crud_views_guardian/apps.py`**

```python
from django.apps import AppConfig


class CrudViewsGuardianConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_guardian"
    label = "cvg"

    def ready(self):
        pass
```

- [ ] **Step 3: Create `crud_views_guardian/lib/__init__.py`**

```python
# crud_views_guardian/lib/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add crud_views_guardian/
git commit -m "feat: scaffold crud_views_guardian sub-package"
```

---

## Task 2: `GuardianViewSet`

**Files:**
- Create: `crud_views_guardian/lib/viewset.py`

- [ ] **Step 1: Create `crud_views_guardian/lib/viewset.py`**

```python
from crud_views.lib.viewset import ViewSet


class GuardianViewSet(ViewSet):
    """
    ViewSet subclass with per-object permission support via django-guardian.

    Attributes:
        cv_guardian_parent_permission: permission key checked on parent object
            for child list/detail/update/delete views. None = skip check.
        cv_guardian_parent_create_permission: permission key checked on parent
            object for child create views. None = falls back to
            cv_guardian_parent_permission.
    """

    cv_guardian_parent_permission: str | None = "view"
    cv_guardian_parent_create_permission: str | None = None

    def assign_perm(self, perm: str, user_or_group, obj) -> None:
        """Assign per-object permission using a short key ("view", "change", etc.)."""
        from guardian.shortcuts import assign_perm
        assign_perm(self.permissions[perm], user_or_group, obj)

    def remove_perm(self, perm: str, user_or_group, obj) -> None:
        """Remove per-object permission using a short key."""
        from guardian.shortcuts import remove_perm
        remove_perm(self.permissions[perm], user_or_group, obj)

    def get_objects_for_user(self, user, perm: str, qs=None):
        """Return queryset of objects for which user has the given per-object permission."""
        from guardian.shortcuts import get_objects_for_user
        return get_objects_for_user(
            user,
            self.permissions[perm],
            qs if qs is not None else self.model.objects.all(),
            accept_global_perms=False,
            use_groups=True,
        )
```

- [ ] **Step 2: Commit**

```bash
git add crud_views_guardian/lib/viewset.py
git commit -m "feat: add GuardianViewSet with assign/remove/get helpers"
```

---

## Task 3: Core Mixins

**Files:**
- Create: `crud_views_guardian/lib/mixins.py`

- [ ] **Step 1: Create `crud_views_guardian/lib/mixins.py`**

```python
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


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
    """

    cv_guardian_accept_global_perms: bool = False

    def _check_object_perm(self, user, perm: str, obj) -> bool:
        if self.cv_guardian_accept_global_perms:
            return user.has_perm(perm, obj)
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
                return user.has_perm(perm, obj)
            from guardian.core import ObjectPermissionChecker
            checker = ObjectPermissionChecker(user)
            return checker.has_perm(perm.split(".")[1], obj)
        return False


class GuardianQuerysetMixin:
    """
    For list views.

    Filters get_queryset() to only objects the user has per-object permission on,
    via guardian's get_objects_for_user().

    cv_guardian_accept_global_perms = False (default): strict — only objects
    with an explicit per-object grant are returned.
    Set to True to also include objects accessible via model-level permission.
    """

    cv_guardian_accept_global_perms: bool = False

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


class GuardianParentPermissionMixin:
    """
    For child viewset views (any view type where cv_viewset.parent is set).

    In dispatch(), before any other processing, checks per-object permission
    on the parent instance. Raises 403 if denied. No-op when cv_viewset.parent
    is None.

    Reads cv_guardian_parent_permission / cv_guardian_parent_create_permission
    from the child GuardianViewSet. Respects cv_guardian_accept_global_perms
    from the combined view class.
    """

    def dispatch(self, request, *args, **kwargs):
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

- [ ] **Step 2: Commit**

```bash
git add crud_views_guardian/lib/mixins.py
git commit -m "feat: add GuardianObjectPermissionMixin, GuardianQuerysetMixin, GuardianParentPermissionMixin"
```

---

## Task 4: View Classes

**Files:**
- Create: `crud_views_guardian/lib/views.py`

- [ ] **Step 1: Create `crud_views_guardian/lib/views.py`**

```python
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ActionViewPermissionRequired,
)
from crud_views_guardian.lib.mixins import (
    GuardianObjectPermissionMixin,
    GuardianQuerysetMixin,
    GuardianParentPermissionMixin,
)


class GuardianDetailViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DetailViewPermissionRequired
):
    pass


class GuardianUpdateViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, UpdateViewPermissionRequired
):
    pass


class GuardianDeleteViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DeleteViewPermissionRequired
):
    pass


class GuardianActionViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, ActionViewPermissionRequired
):
    pass


class GuardianListViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianQuerysetMixin, ListViewPermissionRequired
):
    pass


class GuardianCreateViewPermissionRequired(
    GuardianParentPermissionMixin, CreateViewPermissionRequired
):
    """
    For top-level creates: GuardianParentPermissionMixin is a no-op (no parent).
    Django's PermissionRequiredMixin checks model-level add_<model> permission.

    For child creates: GuardianParentPermissionMixin checks per-object permission
    on the parent instance using cv_guardian_parent_create_permission (falls back
    to cv_guardian_parent_permission). No model-level add_<child> check is made.
    """
    pass
```

- [ ] **Step 2: Commit**

```bash
git add crud_views_guardian/lib/views.py
git commit -m "feat: add Guardian*ViewPermissionRequired drop-in view classes"
```

---

## Task 5: `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `guardian` optional dependency and add to `test` deps**

In `pyproject.toml`, in `[project.optional-dependencies]`, add:

```toml
guardian = [
    "django-guardian>=2.4",
]
```

Also add `"django-guardian>=2.4"` to the `test` list so the test suite always has it:

```toml
test = [
    "nox",
    "pytest",
    "pytest-cov",
    "pytest-random-order",
    "pytest-mock",
    "pytest-django",
    "pytest-xdist",
    "lxml",
    "django-guardian>=2.4",
]
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add django-guardian as optional dependency"
```

---

## Task 6: Test Infrastructure

**Files:**
- Modify: `tests/test1/conftest.py`
- Create: `tests/lib/helper/guardian.py`
- Modify: `tests/test1/app/views.py`
- Modify: `tests/test1/app/urls.py`

- [ ] **Step 1: Create `tests/lib/helper/guardian.py`**

```python
def user_guardian_object_perm(user, viewset, perm, obj):
    """Assign a per-object guardian permission to a user."""
    from guardian.shortcuts import assign_perm
    assign_perm(viewset.permissions[perm], user, obj)
```

- [ ] **Step 2: Update `tests/test1/conftest.py` — add guardian to Django settings**

In `pytest_configure()`, add to `INSTALLED_APPS`:

```python
"guardian",
"crud_views_guardian.apps.CrudViewsGuardianConfig",
```

Add new settings:

```python
AUTHENTICATION_BACKENDS=[
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
],
ANONYMOUS_USER_NAME=None,
```

- [ ] **Step 3: Add guardian fixtures to `tests/test1/conftest.py`**

Add at the bottom of `conftest.py`:

```python
@pytest.fixture
def cv_guardian_author():
    from tests.test1.app.views import cv_guardian_author as ret
    return ret


@pytest.fixture
def cv_guardian_book():
    from tests.test1.app.views import cv_guardian_book as ret
    return ret


@pytest.fixture
def author_b():
    from tests.test1.app.models import Author
    return Author.objects.create(first_name="Terry", last_name="Pratchett")


@pytest.fixture
def book_under_author_douglas(author_douglas_adams):
    from tests.test1.app.models import Book
    return Book.objects.create(title="Hitchhiker's Guide", price="9.99", author=author_douglas_adams)


@pytest.fixture
def user_guardian(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(username="user_guardian", password="password")


@pytest.fixture
def client_guardian(client, user_guardian):
    client.force_login(user_guardian)
    return client
```

- [ ] **Step 4: Add guardian viewsets and views to `tests/test1/app/views.py`**

Add imports at top:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
)
```

Add after the existing `cv_author` / `cv_book` section (at the end of the file):

```python
# Guardian viewsets for guardian integration tests

cv_guardian_author = GuardianViewSet(
    model=Author,
    name="guardian_author",
    icon_header="fa-regular fa-user",
)


class GuardianAuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_guardian_author
    cv_list_actions = ["detail", "update", "delete"]


class GuardianAuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_guardian_author


class GuardianAuthorCreateView(CrispyModelViewMixin, GuardianCreateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_guardian_author


class GuardianAuthorUpdateView(CrispyModelViewMixin, GuardianUpdateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_guardian_author


class GuardianAuthorDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_guardian_author


cv_guardian_book = GuardianViewSet(
    model=Book,
    name="guardian_book",
    parent=ParentViewSet(name="guardian_author"),
    icon_header="fa-regular fa-address-book",
    cv_guardian_parent_permission="view",
    cv_guardian_parent_create_permission="change",
)


class GuardianBookListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = BookTable
    cv_viewset = cv_guardian_book
    cv_list_actions = ["detail", "update", "delete"]


class GuardianBookDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_guardian_book


class GuardianBookCreateView(CrispyModelViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_guardian_book


class GuardianBookUpdateView(CrispyModelViewMixin, GuardianUpdateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_guardian_book


class GuardianBookDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_guardian_book
```

- [ ] **Step 5: Register guardian URL patterns in `tests/test1/app/urls.py`**

```python
from tests.test1.app.views import cv_author, cv_publisher, cv_book, cv_vehicle, cv_campaign, cv_guardian_author, cv_guardian_book

urlpatterns = []
urlpatterns += cv_author.urlpatterns
urlpatterns += cv_publisher.urlpatterns
urlpatterns += cv_book.urlpatterns
urlpatterns += cv_vehicle.urlpatterns
urlpatterns += cv_campaign.urlpatterns
urlpatterns += cv_guardian_author.urlpatterns
urlpatterns += cv_guardian_book.urlpatterns
```

- [ ] **Step 6: Run the existing test suite to confirm nothing is broken**

```bash
pytest tests/test1/ -x -q --ignore=tests/test1/test_guardian.py
```

Expected: all existing tests pass.

- [ ] **Step 7: Commit**

```bash
git add tests/ pyproject.toml
git commit -m "test: add guardian test infrastructure and viewsets"
```

---

## Task 7: Tests — Object-Level Enforcement

**Files:**
- Create: `tests/test1/test_guardian.py`

- [ ] **Step 1: Create `tests/test1/test_guardian.py` with object-level enforcement tests**

```python
import pytest
from django.test.client import Client

from tests.lib.helper.guardian import user_guardian_object_perm


# ── Object-level enforcement: detail/update/delete ──────────────────────────

@pytest.mark.django_db
def test_object_perm_granted_detail(client_guardian, user_guardian, cv_guardian_author, author_douglas_adams):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_object_perm_denied_detail(client_guardian, cv_guardian_author, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_object_perm_granted_update(client_guardian, user_guardian, cv_guardian_author, author_douglas_adams):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "change", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/update/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_object_perm_denied_update(client_guardian, cv_guardian_author, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/update/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_object_perm_granted_delete(client_guardian, user_guardian, cv_guardian_author, author_douglas_adams):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "delete", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/delete/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_object_perm_denied_delete(client_guardian, cv_guardian_author, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/delete/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_model_level_perm_only_is_denied_in_strict_mode(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams
):
    """User with model-level view_author but no per-object grant is denied (strict mode)."""
    from tests.lib.helper.user import user_viewset_permission
    user_viewset_permission(user_guardian, cv_guardian_author, "view")
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/detail/")
    assert response.status_code == 403
```

- [ ] **Step 2: Run these tests — expect them to fail (views don't exist yet if Task 6 incomplete, otherwise should pass)**

```bash
pytest tests/test1/test_guardian.py::test_object_perm_granted_detail \
       tests/test1/test_guardian.py::test_object_perm_denied_detail \
       tests/test1/test_guardian.py::test_model_level_perm_only_is_denied_in_strict_mode \
       -v
```

Expected: all 3 pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_guardian.py tests/lib/helper/guardian.py
git commit -m "test: add guardian object-level enforcement tests"
```

---

## Task 8: Tests — List Queryset Filtering

**Files:**
- Modify: `tests/test1/test_guardian.py`

- [ ] **Step 1: Add list filtering tests**

Append to `tests/test1/test_guardian.py`:

```python
# ── List queryset filtering ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_list_shows_only_permitted_objects(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, author_b
):
    """User sees only authors they have per-object view permission on."""
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    response = client_guardian.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" in response.content.decode()
    assert "Terry" not in response.content.decode()


@pytest.mark.django_db
def test_list_empty_when_no_object_perms(client_guardian, cv_guardian_author, author_douglas_adams, author_b):
    """User with no per-object grants sees empty list."""
    response = client_guardian.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" not in response.content.decode()
    assert "Terry" not in response.content.decode()


@pytest.mark.django_db
def test_list_respects_group_permissions(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, author_b
):
    """User in a group with per-object perm sees the object."""
    from django.contrib.auth.models import Group
    from guardian.shortcuts import assign_perm
    group = Group.objects.create(name="editors")
    user_guardian.groups.add(group)
    assign_perm(cv_guardian_author.permissions["view"], group, author_douglas_adams)
    response = client_guardian.get("/guardian_author/")
    assert response.status_code == 200
    assert "Douglas" in response.content.decode()
    assert "Terry" not in response.content.decode()
```

- [ ] **Step 2: Run**

```bash
pytest tests/test1/test_guardian.py -k "list" -v
```

Expected: all 3 pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_guardian.py
git commit -m "test: add guardian list queryset filtering tests"
```

---

## Task 9: Tests — Create Views

**Files:**
- Modify: `tests/test1/test_guardian.py`

- [ ] **Step 1: Add create view tests**

Append to `tests/test1/test_guardian.py`:

```python
# ── Create views ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_top_level_create_requires_model_level_add_perm(
    client_guardian, user_guardian, cv_guardian_author
):
    """Top-level create uses model-level add permission (no object exists yet)."""
    from tests.lib.helper.user import user_viewset_permission
    user_viewset_permission(user_guardian, cv_guardian_author, "add")
    response = client_guardian.get("/guardian_author/create/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_top_level_create_denied_without_model_level_perm(client_guardian):
    """Top-level create is denied when user has no add permission."""
    response = client_guardian.get("/guardian_author/create/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_child_create_requires_parent_change_perm(
    client_guardian, user_guardian, cv_guardian_author, cv_guardian_book, author_douglas_adams
):
    """Child create requires cv_guardian_parent_create_permission ('change') on parent."""
    user_guardian_object_perm(user_guardian, cv_guardian_author, "change", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/guardian_book/create/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_child_create_denied_with_only_view_perm_on_parent(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams
):
    """Child create is denied when user only has 'view' on parent (needs 'change')."""
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/guardian_book/create/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_child_create_denied_without_parent_perm(client_guardian, author_douglas_adams):
    """Child create is denied when user has no permission on parent."""
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/guardian_book/create/")
    assert response.status_code == 403
```

- [ ] **Step 2: Run**

```bash
pytest tests/test1/test_guardian.py -k "create" -v
```

Expected: all 5 pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_guardian.py
git commit -m "test: add guardian create view tests"
```

---

## Task 10: Tests — Parent Permission & `cv_has_access`

**Files:**
- Modify: `tests/test1/test_guardian.py`

- [ ] **Step 1: Add parent permission and cv_has_access tests**

Append to `tests/test1/test_guardian.py`:

```python
# ── Parent permission (child list/detail/update/delete) ──────────────────────

@pytest.mark.django_db
def test_child_list_requires_parent_view_perm(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams
):
    """Child list requires cv_guardian_parent_permission ('view') on parent."""
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/guardian_book/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_child_list_denied_without_parent_perm(client_guardian, author_douglas_adams):
    """Child list is denied when user has no view permission on parent."""
    pk = author_douglas_adams.pk
    response = client_guardian.get(f"/guardian_author/{pk}/guardian_book/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_child_detail_denied_without_parent_view_perm(
    client_guardian, user_guardian, cv_guardian_book, author_douglas_adams, book_under_author_douglas
):
    """Child detail denied even with per-object book perm if parent perm missing."""
    user_guardian_object_perm(user_guardian, cv_guardian_book, "view", book_under_author_douglas)
    author_pk = author_douglas_adams.pk
    book_pk = book_under_author_douglas.pk
    response = client_guardian.get(f"/guardian_author/{author_pk}/guardian_book/{book_pk}/detail/")
    assert response.status_code == 403


# ── cv_has_access ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_cv_has_access_with_grant(user_guardian, cv_guardian_author, author_douglas_adams):
    from tests.test1.app.views import GuardianAuthorDetailView
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    assert GuardianAuthorDetailView.cv_has_access(user_guardian, author_douglas_adams) is True


@pytest.mark.django_db
def test_cv_has_access_without_grant(user_guardian, cv_guardian_author, author_douglas_adams):
    from tests.test1.app.views import GuardianAuthorDetailView
    assert GuardianAuthorDetailView.cv_has_access(user_guardian, author_douglas_adams) is False


@pytest.mark.django_db
def test_cv_has_access_no_object_returns_false(user_guardian, cv_guardian_author):
    from tests.test1.app.views import GuardianAuthorDetailView
    assert GuardianAuthorDetailView.cv_has_access(user_guardian) is False


# ── accept_global_perms = True ───────────────────────────────────────────────

@pytest.mark.django_db
def test_accept_global_perms_allows_model_level_on_detail(
    client, cv_guardian_author, author_douglas_adams
):
    """With accept_global_perms=True, model-level perm grants object access."""
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import GuardianAuthorDetailView

    user = User.objects.create_user(username="global_perm_user", password="password")
    user_viewset_permission(user, cv_guardian_author, "view")

    # Temporarily override on the view class
    original = GuardianAuthorDetailView.cv_guardian_accept_global_perms
    GuardianAuthorDetailView.cv_guardian_accept_global_perms = True
    client.force_login(user)
    try:
        pk = author_douglas_adams.pk
        response = client.get(f"/guardian_author/{pk}/detail/")
        assert response.status_code == 200
    finally:
        GuardianAuthorDetailView.cv_guardian_accept_global_perms = original
```

- [ ] **Step 2: Run**

```bash
pytest tests/test1/test_guardian.py -k "parent or cv_has_access or accept_global" -v
```

Expected: all tests pass.

- [ ] **Step 3: Run full guardian test suite**

```bash
pytest tests/test1/test_guardian.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test1/test_guardian.py
git commit -m "test: add guardian parent permission and cv_has_access tests"
```

---

## Task 11: Bootstrap5 Example

**Files:**
- Modify: `examples/bootstrap5/app/views/author.py`
- Modify: `examples/bootstrap5/app/views/book.py`
- Modify: `examples/bootstrap5/app/settings.py` (or wherever INSTALLED_APPS is defined)

- [ ] **Step 1: Update `examples/bootstrap5/project/settings.py`**

Add to `INSTALLED_APPS`:
```python
"guardian",
"crud_views_guardian.apps.CrudViewsGuardianConfig",
```

Add new settings:
```python
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]
ANONYMOUS_USER_NAME = None
```

- [ ] **Step 2: Run migrations for the example app**

```bash
cd examples/bootstrap5 && python manage.py migrate
```

Expected: guardian tables created (`guardian_userobjectpermission`, `guardian_groupobjectpermission`).

- [ ] **Step 3: Update `examples/bootstrap5/app/views/author.py`**

Change the import block from:
```python
from crud_views.lib.viewset import ViewSet
```
to:
```python
from crud_views.lib.viewset import ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)
```

Change the viewset from:
```python
cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```
to:
```python
cv_author = GuardianViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

Change each view class base to its guardian equivalent:

```python
class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, GuardianListViewPermissionRequired):
    ...

class AuthorCreateView(CrispyModelViewMixin, MessageMixin, GuardianCreateViewPermissionRequired):
    ...

class AuthorUpdateView(CrispyModelViewMixin, MessageMixin, GuardianUpdateViewPermissionRequired):
    ...

class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, GuardianDeleteViewPermissionRequired):
    ...

class AuthorDetailView(GuardianDetailViewPermissionRequired):
    ...
```

Leave `AuthorUpView`, `AuthorDownView`, `RedirectBooksView`, `AuthorContactView` unchanged (they use `change`/`view` model-level perms which are appropriate).

- [ ] **Step 4: Update `examples/bootstrap5/app/views/book.py`**

Change imports similarly and update viewset:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)
```

```python
cv_book = GuardianViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    icon_header="fa-regular fa-address-book",
    cv_guardian_parent_permission="view",
    cv_guardian_parent_create_permission="change",
)
```

Update each book view's base class to the guardian equivalent.

- [ ] **Step 5: Add a management command for demo permissions**

Create `examples/bootstrap5/app/management/commands/setup_guardian_demo.py`:

Also create `examples/bootstrap5/app/management/__init__.py` and `examples/bootstrap5/app/management/commands/__init__.py` (empty files).

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Assign per-object guardian permissions to demo users for the guardian example."

    def handle(self, *args, **options):
        from app.models import Author, Book
        from app.views.author import cv_author
        from app.views.book import cv_book

        User = get_user_model()

        editor, _ = User.objects.get_or_create(username="editor")
        editor.set_password("editor")
        editor.save()

        reader, _ = User.objects.get_or_create(username="reader")
        reader.set_password("reader")
        reader.save()

        # Give editor model-level add_author so top-level create works
        ct = ContentType.objects.get_for_model(Author)
        add_perm = Permission.objects.get(content_type=ct, codename="add_author")
        editor.user_permissions.add(add_perm)

        for author in Author.objects.all():
            cv_author.assign_perm("view", reader, author)
            cv_author.assign_perm("view", editor, author)
            cv_author.assign_perm("change", editor, author)
            cv_author.assign_perm("delete", editor, author)

        for book in Book.objects.all():
            cv_book.assign_perm("view", reader, book)
            cv_book.assign_perm("view", editor, book)
            cv_book.assign_perm("change", editor, book)
            cv_book.assign_perm("delete", editor, book)

        self.stdout.write(self.style.SUCCESS(
            "Done. Users: editor/editor (full access), reader/reader (view only).\n"
            "Run 'python manage.py loaddata authors' first if no authors exist."
        ))
```

- [ ] **Step 6: Commit**

```bash
git add examples/bootstrap5/
git commit -m "feat: update bootstrap5 example to use guardian views"
```

---

## Task 12: Documentation

**Files:**
- Create: `docs/guardian.md`
- Modify: `mkdocs.yml`
- Modify: `README.md`

- [ ] **Step 1: Create `docs/guardian.md`**

```markdown
# Per-Object Permissions (django-guardian)

The `crud_views_guardian` sub-package adds per-object permission support via
[django-guardian](https://django-guardian.readthedocs.io/). Users opt in by
swapping `ViewSet` → `GuardianViewSet` and `*ViewPermissionRequired` →
`Guardian*ViewPermissionRequired`.

## Installation

```bash
pip install django-crud-views[guardian]
```

## Setup

```python
INSTALLED_APPS = [
    ...
    "guardian",
    "crud_views_guardian.apps.CrudViewsGuardianConfig",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

ANONYMOUS_USER_NAME = None
```

Then run migrations:

```bash
python manage.py migrate
```

## Usage

Replace `ViewSet` with `GuardianViewSet` and each `*ViewPermissionRequired` with
its `Guardian*` equivalent:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)

cv_author = GuardianViewSet(model=Author, name="author")

class AuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_author
    ...

class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    ...
```

## Assigning Per-Object Permissions

```python
# Grant user permission to view a specific author
cv_author.assign_perm("view", user, author_instance)

# Grant a group permission
cv_author.assign_perm("change", group, author_instance)

# Revoke permission
cv_author.remove_perm("view", user, author_instance)

# Get all objects a user can view
qs = cv_author.get_objects_for_user(user, "view")
```

## Strict Mode (Default)

By default, `accept_global_perms=False`: users with a model-level `view_author`
Django permission are **not** granted access to individual objects. Only explicit
per-object grants (via `assign_perm`) count.

To allow model-level permissions as a fallback for a specific view:

```python
class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_guardian_accept_global_perms = True
```

## Create Views

`CreateView` cannot check per-object permission on an object that doesn't exist
yet. Two cases:

**Top-level creates** (no parent viewset): Django's standard model-level
`add_<model>` permission is checked. Grant this globally to users who should
be able to create objects.

**Child creates** (with parent viewset): The parent object exists. Guardian
checks per-object permission on the parent using
`cv_guardian_parent_create_permission`. No model-level check is made on the
child model.

## Parent Viewsets

When a child viewset has `parent=ParentViewSet(...)`, guardian checks permission
on the parent instance before dispatching any child view.

Configure what permission is required on the parent:

```python
cv_book = GuardianViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    cv_guardian_parent_permission="view",          # for list/detail/update/delete
    cv_guardian_parent_create_permission="change", # for create (None = use above)
)
```

## Group Permissions

Guardian group permissions are respected by default (`use_groups=True`).
Assign permissions to groups:

```python
from guardian.shortcuts import assign_perm
assign_perm(cv_author.permissions["view"], group, author_instance)
```
```

- [ ] **Step 2: Add `guardian.md` to `mkdocs.yml`**

Find the nav section with `polymorphic` or `workflow` and add `guardian.md` nearby:

```yaml
- guardian.md
```

- [ ] **Step 3: Add guardian to optional integrations in `README.md`**

Find the optional integrations section (around the line mentioning `django-polymorphic`) and add:

```markdown
- [django-guardian](https://django-guardian.readthedocs.io/) — per-object permissions via `crud_views_guardian` (`pip install django-crud-views[guardian]`)
```

- [ ] **Step 4: Commit**

```bash
git add docs/guardian.md mkdocs.yml README.md
git commit -m "docs: add django-guardian integration documentation"
```

---

## Task 13: Final Verification

- [ ] **Step 1: Run the full test suite**

```bash
pytest tests/test1/ -v
```

Expected: all tests pass, including the new guardian tests.

- [ ] **Step 2: Verify guardian URL patterns are correct by listing them**

```bash
python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test1.conftest'
# just check imports are clean
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.mixins import GuardianObjectPermissionMixin, GuardianQuerysetMixin, GuardianParentPermissionMixin
print('All imports OK')
"
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete crud_views_guardian sub-package implementation"
```
