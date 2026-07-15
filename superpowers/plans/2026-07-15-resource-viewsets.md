# Resource ViewSets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a ViewSet render non-ORM, table-shaped data (e.g. S3 bucket contents) through the existing list/detail/custom-form/action views, via a Pydantic `Resource` base class with a model-style data-access protocol.

**Architecture:** A new `Resource` Pydantic base class carries Django-`Options`-compatible meta (`_meta` shim) plus `cv_get_items`/`cv_get_item` classmethods; `ViewSet.model` widens to accept it, with explicit `resource_permissions` replacing ContentType-derived permissions; a single `ResourceViewMixin` overrides `get_queryset`/`get_object` so every existing view class works unchanged. Resources may be children of model ViewSets but never parents ("leaves only").

**Tech Stack:** Django 4.2/5.2/6.0, Pydantic v2, django-tables2, pytest-django. Spec: `superpowers/specs/2026-07-15-resource-viewsets-design.md`.

## Global Constraints

- No behavior change for model-based ViewSets — the entire existing suite must stay green after every task.
- No create/update views for Resources; no django-filter integration; no Resource-as-parent nesting (all spec §10 non-goals).
- Permissions for Resource ViewSets are explicit (`resource_permissions=` dict) or absent — never derived, never silently defaulted. `default_permissions` must never execute for a Resource (it queries ContentType).
- `crud_views/lib/resource.py` must NOT import from `crud_views.lib.viewset/__init__.py` (circular import — `viewset/__init__.py` imports `resource.py`). Only `crud_views.lib.viewset.path_regs` is safe.
- New check IDs: E260, E261, E262 (E252–E259 left free for other work; used IDs today end at E251).
- Line length 120, double quotes (ruff); all `CrudView` class attributes use `cv_` prefix.
- Test commands run from `tests/`: `cd tests && pytest test1/<file> -v`. Format/lint from repo root: `task format` and `task check`.

---

### Task 1: `Resource` base class with `_meta` shim

**Files:**
- Create: `src/crud_views/lib/resource.py`
- Test: `tests/test1/test_resource.py`

**Interfaces:**
- Consumes: `crud_views.lib.viewset.path_regs.PrimaryKeys` (plain string regex constants: `INT`, `HEX`, `UUID`, `KEY`, `STR`).
- Produces (used by Tasks 2–6):
  - `class ResourceMeta` — defaults holder with class attrs `verbose_name: str = "item"`, `verbose_name_plural: str = "items"`, `app_label: str = "resources"`, `pk_field: str = "pk"`, `pk_type: str = PrimaryKeys.STR`, `ordering: str | None = None`.
  - `class ResourceOptions` — `__init__(self, meta: type)`; instance attrs = the six names above, read from `meta` with `ResourceMeta` fallback.
  - `class Resource(pydantic.BaseModel)` — class attr `_meta: ResourceOptions` (set on every subclass and on `Resource` itself); instance attr/property `pk`; classmethods `cv_get_items(cls, request, **url_kwargs) -> list[Self]` (raises `NotImplementedError`) and `cv_get_item(cls, request, pk, **url_kwargs) -> Self` (default linear scan, raises `django.http.Http404`).

**Key subtlety (why `pk` is NOT a property on the base class):** `property` is a data descriptor. If the base class defined `pk` as a property and a subclass declared a real Pydantic field `pk`, the base property would shadow the field's instance value and recurse (`pk` property → `getattr(self, "pk")` → property). Instead, `__pydantic_init_subclass__` attaches a `pk` property **per subclass** only when the subclass has no field named `pk`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_resource.py`:

```python
import pytest
from django.http import Http404
from pydantic import ValidationError

from crud_views.lib.resource import Resource, ResourceMeta, ResourceOptions
from crud_views.lib.viewset.path_regs import PrimaryKeys


class Item(Resource):
    key: str
    size: int = 0

    class Meta:
        verbose_name = "s3 item"
        verbose_name_plural = "s3 items"
        app_label = "storage"
        pk_field = "key"
        pk_type = PrimaryKeys.STR

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return [cls(key="a", size=1), cls(key="b", size=2)]


def test_meta_defaults_merge():
    class Minimal(Resource):
        pk: str

    assert Minimal._meta.verbose_name == "item"
    assert Minimal._meta.verbose_name_plural == "items"
    assert Minimal._meta.app_label == "resources"
    assert Minimal._meta.pk_field == "pk"
    assert Minimal._meta.pk_type == PrimaryKeys.STR
    assert Minimal._meta.ordering is None


def test_meta_shim_exposes_options_attrs():
    assert Item._meta.verbose_name == "s3 item"
    assert Item._meta.verbose_name_plural == "s3 items"
    assert Item._meta.app_label == "storage"
    assert Item._meta.pk_field == "key"
    # instance access works too (SessionData reads view.model._meta via class,
    # templates may reach it via instances)
    assert Item(key="x")._meta.verbose_name == "s3 item"


def test_options_is_plain_object():
    opts = ResourceOptions(ResourceMeta)
    assert opts.verbose_name == "item"
    assert opts.pk_field == "pk"


def test_pk_property_reads_pk_field():
    assert Item(key="x").pk == "x"


def test_pk_field_may_name_a_python_property():
    class Hashed(Resource):
        key: str

        class Meta:
            pk_field = "key_upper"

        @property
        def key_upper(self) -> str:
            return self.key.upper()

    assert Hashed(key="ab").pk == "AB"


def test_field_named_pk_works_directly():
    class Direct(Resource):
        pk: str

    assert Direct(pk="1").pk == "1"


def test_default_pk_field_without_pk_field_raises():
    with pytest.raises(TypeError, match="pk_field"):
        class Broken(Resource):
            key: str  # Meta.pk_field defaults to "pk" but there is no pk attribute


def test_cv_get_items_not_implemented():
    class Bare(Resource):
        pk: str

    with pytest.raises(NotImplementedError):
        Bare.cv_get_items(None)


def test_cv_get_item_default_scan():
    found = Item.cv_get_item(None, "a")
    assert found.key == "a"
    assert found.size == 1


def test_cv_get_item_raises_http404():
    with pytest.raises(Http404):
        Item.cv_get_item(None, "does-not-exist")


def test_pydantic_validation_still_works():
    with pytest.raises(ValidationError):
        Item(key="a", size="not-an-int")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_resource.py -v`
Expected: FAIL at collection with `ModuleNotFoundError: No module named 'crud_views.lib.resource'`

- [ ] **Step 3: Implement `src/crud_views/lib/resource.py`**

```python
from __future__ import annotations

from typing import Any, List

from django.http import Http404
from pydantic import BaseModel
from typing_extensions import Self

from crud_views.lib.viewset.path_regs import PrimaryKeys

# NOTE: this module must not import from crud_views.lib.viewset (the package
# __init__) — viewset/__init__.py imports this module, importing back would be
# circular. path_regs is a leaf module and safe.


class ResourceMeta:
    """
    Defaults for Resource.Meta. Mirrors the Django model Meta idiom; values
    should be lowercase (ViewSet.get_meta() applies .capitalize()).
    """

    verbose_name: str = "item"
    verbose_name_plural: str = "items"
    app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py)
    pk_field: str = "pk"  # name of the attribute (field or property) identifying a row
    pk_type: str = PrimaryKeys.STR  # URL pattern regex, see path_regs.PrimaryKeys
    ordering: str | None = None  # informational; sort in cv_get_items


_META_ATTRS = ("verbose_name", "verbose_name_plural", "app_label", "pk_field", "pk_type", "ordering")


class ResourceOptions:
    """
    Duck-types the subset of Django's ``model._meta`` (Options) API that
    crud_views reads (verbose_name, verbose_name_plural, app_label), plus the
    Resource-specific attributes (pk_field, pk_type, ordering). Add attributes
    only when a coupling point actually reads them.
    """

    def __init__(self, meta: type):
        for name in _META_ATTRS:
            setattr(self, name, getattr(meta, name, getattr(ResourceMeta, name)))


class Resource(BaseModel):
    """
    Base class for non-ORM table-shaped data rendered through a ViewSet.

    Rows are Pydantic instances, so Django templates and django-tables2 use
    plain attribute access and raw input is validated at conversion time.
    Subclasses define fields, an inner ``Meta`` class and ``cv_get_items``.
    """

    class Meta(ResourceMeta):
        pass

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        cls._meta = ResourceOptions(cls.Meta)

        # Expose object.pk like Django models. A property on the base class
        # would be a data descriptor shadowing a real "pk" field, so it is
        # attached per subclass and only when no "pk" field exists.
        if "pk" not in cls.__pydantic_fields__:
            pk_field = cls._meta.pk_field
            if pk_field == "pk" and not hasattr(cls, "pk"):
                raise TypeError(
                    f"{cls.__name__}: Meta.pk_field is 'pk' but no 'pk' field or attribute is defined"
                )
            if pk_field != "pk":
                cls.pk = property(lambda self, _name=pk_field: getattr(self, _name))

    @classmethod
    def cv_get_items(cls, request, **url_kwargs) -> List[Self]:
        """
        Return all rows. Implemented by the developer (read S3, walk a config
        tree, call an API, ...). ``url_kwargs`` are the resolved URL kwargs of
        the requesting view — for nested ViewSets they contain the parent
        pk(s), e.g. ``publisher_pk``. Must return a plain list (Django's
        Paginator needs len() and slicing).
        """
        raise NotImplementedError(f"{cls.__name__}.cv_get_items() is not implemented")

    @classmethod
    def cv_get_item(cls, request, pk, **url_kwargs) -> Self:
        """
        Return a single row by pk. Default: linear scan over cv_get_items()
        comparing str(row.pk) == str(pk); raises Http404 when not found.
        Deliberately simple — fine for read-all-at-once data. Override when a
        direct lookup is cheaper (e.g. head_object on S3).
        """
        for item in cls.cv_get_items(request, **url_kwargs):
            if str(item.pk) == str(pk):
                return item
        raise Http404(f"{cls._meta.verbose_name} with pk={pk!r} not found")


# __pydantic_init_subclass__ only fires for subclasses; the abstract base needs
# its own _meta so generic code can read Resource._meta without special-casing.
Resource._meta = ResourceOptions(Resource.Meta)
```

Note for implementer: `cls.__pydantic_fields__` is the Pydantic v2 field dict; if the installed Pydantic version exposes it only as `cls.model_fields`, use that instead (both are public in v2.x). The `TypeError` for a missing default pk must fire at class-definition time (the test uses a `with pytest.raises` around the class statement).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_resource.py -v`
Expected: all 11 tests PASS

- [ ] **Step 5: Full suite regression, format, lint**

Run: `cd tests && pytest`
Expected: everything green (new module is not imported by existing code yet).
Run from repo root: `task format && task check`
Expected: no diffs beyond formatting of the new files, no lint errors.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/resource.py tests/test1/test_resource.py
git commit -m "feat(resource): Resource base class with Options-compatible _meta shim"
```

---

### Task 2: ViewSet accepts Resources

**Files:**
- Modify: `src/crud_views/lib/viewset/__init__.py` (field at line 73, `register()` validator at lines 94–119, `register_view_class` at ~line 239, `default_permissions`/`permissions` at lines 357–386, `get_queryset` at lines 204–236)
- Test: `tests/test1/test_resource_viewset.py`

**Interfaces:**
- Consumes: `Resource` from Task 1 (`from crud_views.lib.resource import Resource`).
- Produces (used by Tasks 3–6):
  - `ViewSet(model=<Resource subclass>, name=..., resource_permissions={...} | None)` — new optional field `resource_permissions: Dict[str, str] | None = None`.
  - `ViewSet.is_resource: bool` property.
  - For Resource ViewSets: `permissions` returns `OrderedDict(resource_permissions or {})`; pk auto-detection uses `model._meta.pk_type`; no auto ManageView; `"manage"` is not appended to views' `cv_context_actions`; `ViewSet.get_queryset()` raises `ViewSetError` with an actionable message.

**IMPORTANT — global ViewSet registry:** every `ViewSet(...)` instantiation registers under its `name` for the process lifetime; duplicate names raise. All ViewSets created inside tests need unique names (prefix `t2_`, `t5_`, … per task below).

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_resource_viewset.py`:

```python
from collections import OrderedDict

import pytest
from pydantic import ValidationError

from crud_views.lib.exceptions import ViewSetError
from crud_views.lib.resource import Resource
from crud_views.lib.viewset import ViewSet
from crud_views.lib.viewset.path_regs import PrimaryKeys
from tests.test1.app.models import Author


class T2Item(Resource):
    key: str

    class Meta:
        verbose_name = "t2 item"
        verbose_name_plural = "t2 items"
        pk_field = "key"
        pk_type = PrimaryKeys.HEX

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return [cls(key="aa"), cls(key="bb")]


@pytest.fixture(scope="module")
def vs_t2():
    # module-scoped: registry names are process-global, register exactly once
    return ViewSet(
        model=T2Item,
        name="t2_item",
        resource_permissions={"view": "app.view_s3file"},
    )


def test_is_resource(vs_t2, cv_author):
    assert vs_t2.is_resource is True
    assert cv_author.is_resource is False


def test_pk_type_from_resource_meta(vs_t2):
    assert vs_t2.pk == PrimaryKeys.HEX


def test_pk_explicit_override_still_wins():
    vs = ViewSet(
        model=T2Item,
        name="t2_item_custompk",
        pk=r"[a-f]{2}",
        resource_permissions=None,
    )
    assert vs.pk == r"[a-f]{2}"


def test_permissions_returns_explicit_dict(vs_t2):
    assert vs_t2.permissions == OrderedDict({"view": "app.view_s3file"})


def test_permissions_none_means_empty():
    vs = ViewSet(model=T2Item, name="t2_item_noperm", resource_permissions=None)
    assert vs.permissions == OrderedDict()


def test_no_auto_manage_view(vs_t2, cv_author):
    assert vs_t2.has_view("manage") is False
    assert cv_author.has_view("manage") is True


def test_plain_class_rejected():
    class NotAResource:
        pass

    with pytest.raises(ValidationError):
        ViewSet(model=NotAResource, name="t2_plainclass")


def test_resource_permissions_rejected_for_model_viewset():
    with pytest.raises(ValidationError):
        ViewSet(
            model=Author,
            name="t2_model_with_rp",
            resource_permissions={"view": "app.view_author"},
        )


def test_viewset_get_queryset_guard(vs_t2):
    with pytest.raises(ViewSetError, match="ResourceViewMixin"):
        vs_t2.get_queryset(view=None)
```

Note: `cv_author` is an existing conftest fixture. No `@pytest.mark.django_db` — nothing here touches the database (that is part of the point: Resource permissions must not query ContentType).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_resource_viewset.py -v`
Expected: FAIL — `test_is_resource` with `AttributeError: is_resource`, `ViewSet(model=T2Item, ...)` with `ValidationError` (model is not `Type[Model]`), `resource_permissions` rejected as unexpected field.

- [ ] **Step 3: Implement the ViewSet changes**

All edits in `src/crud_views/lib/viewset/__init__.py`.

3a. Add import (with the other `crud_views.lib` imports near the top):

```python
from crud_views.lib.resource import Resource
```

3b. Widen the model field and add the permissions field (currently line 73):

```python
    model: Type[Model] | Type[Resource]
```

and below `extends: str | None = None` add:

```python
    # Resource-based ViewSets only: explicit permission map, e.g.
    # {"view": "storage.view_s3object", "delete": "storage.delete_s3object"}.
    # None means: no permissions declared (only non-PermissionRequired views).
    resource_permissions: Dict[str, str] | None = None
```

3c. Add the `is_resource` property (after `__str__`):

```python
    @property
    def is_resource(self) -> bool:
        return issubclass(self.model, Resource)
```

3d. In the `register()` validator (lines 94–119), replace the pk-detection block and guard the ManageView creation:

```python
    @model_validator(mode="after")
    def register(self) -> Self:
        if not self.is_resource and self.resource_permissions is not None:
            raise ValueError(f"resource_permissions is only allowed for Resource-based ViewSets, got it at {self!r}")

        if self.pk is None:
            if self.is_resource:
                self.pk = self.model._meta.pk_type
            else:
                from django.db import models

                pk_field_map = {
                    models.UUIDField: self.PK.UUID,
                    models.AutoField: self.PK.INT,
                    models.BigAutoField: self.PK.INT,
                    models.SmallAutoField: self.PK.INT,
                    models.CharField: self.PK.STR,
                    models.SlugField: self.PK.STR,
                }
                self.pk = pk_field_map.get(type(self.model._meta.pk), self.PK.INT)

        with _REGISTRY_LOCK:
            cv_raise(
                self.name not in _REGISTRY,
                f"ViewSet name {self.name} is already registered by {_REGISTRY.get(self.name)!r}",
            )
            _REGISTRY[self.name] = self

        # ManageView is model/session tooling — not supported for Resources (spec §5.4)
        if not self.is_resource:
            base = self.get_manage_view_class()
            _AutoManageView = type("AutoManageView", (base,), {"model": self.model, "cv_viewset": self})  # noqa: F841

        return self
```

3e. In `register_view_class` (~line 239), skip the `"manage"` context action for Resources (the manage view does not exist, and although the `cv_context_action` tag swallows unknown keys, not advertising it is cleaner):

```python
        if crud_views_settings.manage_views_enabled != "no" and not self.is_resource:
```

3f. Guard `default_permissions` and branch `permissions` (lines 357–386):

At the top of `default_permissions` add:

```python
        cv_raise(
            not self.is_resource,
            f"default_permissions must not be used for Resource-based ViewSet {self!r}; set resource_permissions",
        )
```

Replace the `permissions` cached_property body:

```python
    @cached_property
    def permissions(self) -> OrderedDict[str, str]:
        if self.is_resource:
            return OrderedDict(self.resource_permissions or {})
        return self.default_permissions
```

3g. Guard `get_queryset` (line 204) — first statement of the method:

```python
        cv_raise(
            not self.is_resource,
            f"ViewSet.get_queryset() called for Resource-based ViewSet {self!r} — "
            f"add ResourceViewMixin as the FIRST base class of the view",
        )
```

`cv_raise` raises `ViewSetError` when the condition is False (verified: `crud_views/lib/exceptions.py:28` — `def cv_raise(expression, msg, exception=ViewSetError)`), matching the test's `pytest.raises(ViewSetError, ...)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_resource_viewset.py test1/test_resource.py -v`
Expected: all PASS

- [ ] **Step 5: Full suite regression, format, lint**

Run: `cd tests && pytest`
Expected: green — model ViewSet behavior unchanged (manage views still auto-created, permissions still DB-derived).
Run from repo root: `task format && task check`

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/viewset/__init__.py tests/test1/test_resource_viewset.py
git commit -m "feat(viewset): accept Resource classes — explicit permissions, pk from Meta, no manage view"
```

---

### Task 3: `ResourceViewMixin` + list/detail wired in the test app

**Files:**
- Modify: `src/crud_views/lib/resource.py` (append `ResourceViewMixin`)
- Modify: `tests/test1/app/models.py` (append `S3FilePermissions`)
- Create: `tests/test1/app/resources.py`
- Create: `tests/test1/app/templates/app/s3file_detail.html`
- Modify: `tests/test1/app/urls.py`
- Modify: `tests/test1/conftest.py` (append fixtures)
- Test: `tests/test1/test_resource_views.py`

**Interfaces:**
- Consumes: `Resource` (Task 1), `ViewSet(model=Resource, resource_permissions=...)` (Task 2), existing `ListViewTableMixin`, `ListViewPermissionRequired`, `DetailCustomViewPermissionRequired`, `Table`, `user_viewset_permission` test helper.
- Produces:
  - `crud_views.lib.resource.ResourceViewMixin` with `get_queryset(self)` and `get_object(self, queryset=None)`.
  - Test app module `tests/test1/app/resources.py` exporting `FAKE_BUCKET: list[dict]`, `S3File(Resource)`, `cv_s3file: ViewSet` (URLs under `/s3file/`), used and extended by Tasks 4–6.
  - Conftest fixtures `cv_s3file`, `user_s3file_view`, `client_user_s3file_view`, `user_s3file_delete`, `client_user_s3file_delete`.

- [ ] **Step 1: Append `ResourceViewMixin` to `src/crud_views/lib/resource.py`**

```python
class ResourceViewMixin:
    """
    Makes any crud_views view class work on a Resource. MUST be the FIRST
    base class so its methods win the MRO:

        class S3FileListView(ResourceViewMixin, ListViewPermissionRequired): ...

    Overrides the two ORM entry points:
    - get_queryset: replaces CrudView.get_queryset (which delegates to
      ViewSet.get_queryset — ORM + parent filtering). Parent scoping is the
      developer's job inside cv_get_items, using the parent pk url_kwargs.
    - get_object: replaces SingleObjectMixin.get_object. Also used by the
      permission machinery (cv_get_action_object), so a bad pk yields 404
      during the permission phase — same contract as model views.
    """

    def get_queryset(self):
        return self.model.cv_get_items(self.request, **self.kwargs)

    def get_object(self, queryset=None):
        pk = self.kwargs[self.cv_viewset.pk_name]
        return self.model.cv_get_item(self.request, pk, **self.kwargs)
```

(No new test yet — this is exercised end-to-end through the views below.)

- [ ] **Step 2: Add the permission-holder model to `tests/test1/app/models.py`** (append at end)

```python
class S3FilePermissions(models.Model):
    """
    Permission holder for the S3File Resource (spec §7): unmanaged, no table,
    no default permissions — exists only so ContentType/Permission rows are
    created for the custom permissions below.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_s3file", "Can view S3 files"),
            ("delete_s3file", "Can delete S3 files"),
        ]
```

- [ ] **Step 3: Create `tests/test1/app/resources.py`**

```python
import hashlib

import django_tables2 as tables

from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    DetailCustomViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
)
from crud_views.lib.viewset import ViewSet
from crud_views.lib.viewset.path_regs import PrimaryKeys

# fake in-memory "bucket": tests mutate and reset this module-level list
FAKE_BUCKET = [
    {"key": "reports/2026/q1.pdf", "size": 111},
    {"key": "reports/2026/q2.pdf", "size": 222},
    {"key": "images/logo.png", "size": 333},
]


class S3File(Resource):
    key: str
    size: int

    class Meta:
        verbose_name = "s3 file"
        verbose_name_plural = "s3 files"
        app_label = "app"
        pk_field = "key_md5"
        pk_type = PrimaryKeys.HEX

    @property
    def key_md5(self) -> str:
        # S3 keys contain "/" which no pk regex admits; hash them (spec §9)
        return hashlib.md5(self.key.encode()).hexdigest()

    def __str__(self) -> str:
        return self.key

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return [cls.model_validate(row) for row in FAKE_BUCKET]


cv_s3file = ViewSet(
    model=S3File,
    name="s3file",
    resource_permissions={
        "view": "app.view_s3file",
        "delete": "app.delete_s3file",
    },
)


class S3FileTable(Table):
    key = tables.Column()
    size = tables.Column()


class S3FileListView(ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_s3file
    table_class = S3FileTable
    paginate_by = 2  # FAKE_BUCKET has 3 rows -> 2 pages, exercises list pagination
    cv_list_actions = ["detail"]


class S3FileDetailView(ResourceViewMixin, DetailCustomViewPermissionRequired):
    cv_viewset = cv_s3file
    template_name = "app/s3file_detail.html"
```

- [ ] **Step 4: Create `tests/test1/app/templates/app/s3file_detail.html`** (mirrors `app/author_detail_custom.html`)

```html
{% extends cv_extends %}

{% block cv_content %}
<div class="s3file-detail">
    <h2>{{ object.key }}</h2>
    <p class="size">{{ object.size }}</p>
</div>
{% endblock cv_content %}
```

- [ ] **Step 5: Wire URLs in `tests/test1/app/urls.py`**

Add to the imports:

```python
from tests.test1.app.resources import cv_s3file
```

Add at the end of the urlpatterns block:

```python
urlpatterns += cv_s3file.urlpatterns
```

- [ ] **Step 6: Append fixtures to `tests/test1/conftest.py`** (same shape as the author fixtures at lines 104–160)

```python
@pytest.fixture
def cv_s3file():
    from tests.test1.app.resources import cv_s3file as ret

    return ret


@pytest.fixture
def user_s3file_view(cv_s3file):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_s3file_view", password="password")

    user_viewset_permission(user, cv_s3file, "view")

    return user


@pytest.fixture
def client_user_s3file_view(client, user_s3file_view) -> Client:
    client.force_login(user_s3file_view)
    return client


@pytest.fixture
def user_s3file_delete(cv_s3file):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_s3file_delete", password="password")

    user_viewset_permission(user, cv_s3file, "delete")

    return user


@pytest.fixture
def client_user_s3file_delete(client, user_s3file_delete) -> Client:
    client.force_login(user_s3file_delete)
    return client
```

- [ ] **Step 7: Write the failing view tests**

Create `tests/test1/test_resource_views.py`:

```python
import hashlib

import pytest
from django.test.client import Client


def md5(key: str) -> str:
    return hashlib.md5(key.encode()).hexdigest()


@pytest.fixture
def s3_bucket():
    """Snapshot/restore the fake bucket so mutating tests stay isolated."""
    from tests.test1.app import resources

    original = [dict(row) for row in resources.FAKE_BUCKET]
    yield resources.FAKE_BUCKET
    resources.FAKE_BUCKET[:] = original


@pytest.mark.django_db
def test_list_renders_rows(client_user_s3file_view: Client):
    response = client_user_s3file_view.get("/s3file/")
    assert response.status_code == 200
    content = response.content.decode()
    # page 1 of 2 (paginate_by=2); tables2 renders attribute access on Pydantic rows
    assert "reports/2026/q1.pdf" in content
    assert "reports/2026/q2.pdf" in content


@pytest.mark.django_db
def test_list_pagination_page2(client_user_s3file_view: Client):
    response = client_user_s3file_view.get("/s3file/?page=2")
    assert response.status_code == 200
    assert "images/logo.png" in response.content.decode()


@pytest.mark.django_db
def test_list_requires_permission(client: Client, user_a):
    client.force_login(user_a)
    response = client.get("/s3file/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_anonymous_redirects_to_login(client: Client):
    response = client.get("/s3file/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_detail_renders_object(client_user_s3file_view: Client):
    response = client_user_s3file_view.get(f"/s3file/{md5('reports/2026/q1.pdf')}/detail/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "reports/2026/q1.pdf" in content
    assert "111" in content


@pytest.mark.django_db
def test_detail_unknown_pk_404(client_user_s3file_view: Client):
    response = client_user_s3file_view.get(f"/s3file/{'0' * 32}/detail/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_detail_requires_permission(client: Client, user_a):
    client.force_login(user_a)
    response = client.get(f"/s3file/{md5('reports/2026/q1.pdf')}/detail/")
    assert response.status_code == 403


def test_session_data_app_label_shim():
    """SessionData reads view.model._meta.app_label (session.py:49) — the
    Options shim must satisfy it (spec §3 coupling point 5)."""
    from crud_views.lib.session import SessionData
    from tests.test1.app.resources import S3File

    class _StubView:
        model = S3File

    assert SessionData(view=_StubView()).app_label == "app"
```

- [ ] **Step 8: Run tests to verify the new ones pass**

Run: `cd tests && pytest test1/test_resource_views.py -v`
Expected: all PASS. If `test_list_renders_rows` fails inside django-tables2, capture the traceback before changing anything — the likely causes are the table `view` kwarg (must flow through `get_table_kwargs`, untouched) or column accessors (Pydantic attribute access — use `tables.Column(accessor="key")` explicitly if plain `tables.Column()` does not resolve).

- [ ] **Step 9: Full suite regression, format, lint**

Run: `cd tests && pytest`
Expected: green — pay attention to `test_import_safety.py`, `test_viewset_registry.py`, `test_check_messages.py` (a new registered ViewSet participates in registry-wide checks; `cv_s3file` must not emit check errors — if `checks_all` complains about missing header/paragraph templates for the list/detail views, the defaults on `ListView`/`DetailCustomView` cover them; a failure here means a wiring mistake, not a check to silence).
Run from repo root: `task format && task check`

- [ ] **Step 10: Commit**

```bash
git add src/crud_views/lib/resource.py tests/test1/app/models.py tests/test1/app/resources.py \
        tests/test1/app/templates/app/s3file_detail.html tests/test1/app/urls.py \
        tests/test1/conftest.py tests/test1/test_resource_views.py
git commit -m "feat(resource): ResourceViewMixin — list and detail views over non-ORM data"
```

---

### Task 4: Delete via CustomFormView + form-less ActionView

**Files:**
- Modify: `tests/test1/app/resources.py`
- Modify: `tests/test1/test_resource_views.py` (append tests)

**Interfaces:**
- Consumes: `ResourceViewMixin`, `cv_s3file`, `FAKE_BUCKET` (Task 3); existing `CustomFormViewPermissionRequired` (`crud_views/lib/views/form.py:37`), `ActionViewPermissionRequired` (`crud_views/lib/views/action.py:50`), `CrispyModelViewMixin`, `MessageMixin`, `CrispyDeleteForm`.
- Produces: URL routes `/s3file/<pk>/delete/` (GET confirm form + POST) and `/s3file/<pk>/touch/` (POST only); module-level `TOUCHED: list[str]` side-effect log for tests.

Flow notes for the implementer (verified against source):
- `CustomFormView` POST path is `CrudViewProcessFormMixin.post` (`mixins.py:24-41`): sets `self.object = self.get_object()` (our mixin), validates the form, calls `cv_form_valid(context)`, redirects to `cv_success_key` (default `"list"`).
- `ActionView.post` (`action.py:13-22`): sets `self.object = self.get_object()`, calls `action(context) -> bool`, emits success/error message (`cv_message_template_code` / `cv_message_template_error_code`), redirects.
- The permission phase (`CrudViewPermissionRequiredMixin.has_permission`, `base.py:526`) calls `cv_get_action_object()` → `get_object()` — the mixin override makes bad pks 404 there, before the view body.

- [ ] **Step 1: Append to `tests/test1/app/resources.py`**

Extend the imports:

```python
from crud_views.lib.crispy import CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.views import ActionViewPermissionRequired, MessageMixin
from crud_views.lib.views.form import CustomFormViewPermissionRequired
```

Append:

```python
TOUCHED: list[str] = []  # side-effect log for the form-less action, reset by tests


class S3FileDeleteView(ResourceViewMixin, CrispyModelViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    """
    Delete-with-confirm as a custom form view (spec decision 3: no DeleteView
    port — CustomFormView + dev hook IS the delete story for Resources).
    """

    cv_key = "delete"
    cv_path = "delete"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    form_class = CrispyDeleteForm
    cv_message_template_code = "Deleted »{{ object }}«"
    cv_header_template_code = "Delete S3 file"
    cv_paragraph_template_code = "Confirm deletion of »{{ object }}«"

    def cv_form_valid(self, context):
        # the dev hook: this is where delete_object(Bucket=..., Key=obj.key) would go
        FAKE_BUCKET[:] = [row for row in FAKE_BUCKET if row["key"] != self.object.key]


class S3FileTouchView(ResourceViewMixin, ActionViewPermissionRequired):
    """Form-less POST action with a dev hook (spec decision 3)."""

    cv_key = "touch"
    cv_path = "touch"
    cv_viewset = cv_s3file
    cv_permission = "delete"
    cv_backend_only = True
    cv_message_template_code = "Touched »{{ object }}«"
    cv_message_template_error_code = "Touch failed for »{{ object }}«"

    def action(self, context) -> bool:
        # result controllable from the request for testing both branches
        if self.request.GET.get("fail") == "1":
            return False
        TOUCHED.append(self.object.key)
        return True
```

And update the list view's actions so the buttons render (in `S3FileListView`):

```python
    cv_list_actions = ["detail", "delete", "touch"]
```

- [ ] **Step 2: Write the failing tests** (append to `tests/test1/test_resource_views.py`)

```python
@pytest.mark.django_db
def test_delete_get_renders_confirm_form(client_user_s3file_delete: Client, s3_bucket):
    response = client_user_s3file_delete.get(f"/s3file/{md5('images/logo.png')}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "images/logo.png" in content
    assert "<form" in content


@pytest.mark.django_db
def test_delete_post_removes_item_and_redirects(client_user_s3file_delete: Client, s3_bucket):
    response = client_user_s3file_delete.post(f"/s3file/{md5('images/logo.png')}/delete/", {})
    assert response.status_code == 302
    assert response.url == "/s3file/"
    assert not any(row["key"] == "images/logo.png" for row in s3_bucket)
    assert len(s3_bucket) == 2


@pytest.mark.django_db
def test_delete_requires_delete_permission(client_user_s3file_view: Client, s3_bucket):
    # view-only user: 403, bucket untouched
    response = client_user_s3file_view.post(f"/s3file/{md5('images/logo.png')}/delete/", {})
    assert response.status_code == 403
    assert len(s3_bucket) == 3


@pytest.mark.django_db
def test_touch_action_success(client_user_s3file_delete: Client, s3_bucket):
    from tests.test1.app import resources

    resources.TOUCHED.clear()
    response = client_user_s3file_delete.post(f"/s3file/{md5('reports/2026/q1.pdf')}/touch/", follow=True)
    assert response.status_code == 200
    assert resources.TOUCHED == ["reports/2026/q1.pdf"]
    assert "Touched" in response.content.decode()


@pytest.mark.django_db
def test_touch_action_error_branch(client_user_s3file_delete: Client, s3_bucket):
    from tests.test1.app import resources

    resources.TOUCHED.clear()
    response = client_user_s3file_delete.post(f"/s3file/{md5('reports/2026/q1.pdf')}/touch/?fail=1", follow=True)
    assert response.status_code == 200
    assert resources.TOUCHED == []
    assert "Touch failed" in response.content.decode()


@pytest.mark.django_db
def test_touch_requires_delete_permission(client_user_s3file_view: Client, s3_bucket):
    response = client_user_s3file_view.post(f"/s3file/{md5('reports/2026/q1.pdf')}/touch/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_touch_unknown_pk_404(client_user_s3file_delete: Client, s3_bucket):
    response = client_user_s3file_delete.post(f"/s3file/{'0' * 32}/touch/")
    assert response.status_code == 404
```

- [ ] **Step 3: Run tests to verify they fail, then pass**

Run before Step 1 is applied they would 404 (routes missing); after applying both steps:
Run: `cd tests && pytest test1/test_resource_views.py -v`
Expected: all PASS (including the Task 3 tests — the widened `cv_list_actions` must not break the list; the list action buttons render URLs via `obj.pk`, covered by the per-subclass `pk` property).

- [ ] **Step 4: Full suite regression, format, lint**

Run: `cd tests && pytest`
Run from repo root: `task format && task check`

- [ ] **Step 5: Commit**

```bash
git add tests/test1/app/resources.py tests/test1/test_resource_views.py
git commit -m "feat(resource): delete-with-confirm (CustomFormView) and form-less action on Resources"
```

---

### Task 5: System checks E260, E261, E262

**Files:**
- Modify: `src/crud_views/lib/viewset/__init__.py` (`checks()` method, lines 142–151; import `CheckExpression`)
- Test: append to `tests/test1/test_resource_viewset.py`

**Interfaces:**
- Consumes: `ViewSet.checks()` (yields `Check` objects whose `.messages()` yield `django.core.checks` messages with ids `viewset.<ID>`), `CheckExpression` (`crud_views/lib/check.py:215` — Error when `expression` is falsy).
- Produces:
  - **E260**: Resource ViewSet has a registered `*PermissionRequired` view whose `cv_permission` key is missing from `permissions` → Error (spec §5.3: never silently unprotected).
  - **E261**: a ViewSet's parent resolves to a Resource ViewSet → Error (spec §8.2: Resources are leaves).
  - **E262**: Resource ViewSet has a registered Create/Update/Delete view → Error (spec §13).

- [ ] **Step 1: Write the failing tests** (append to `tests/test1/test_resource_viewset.py`)

```python
from crud_views.lib.viewset import ParentViewSet


def check_error_ids(vs) -> list[str]:
    return [message.id for c in vs.checks() for message in c.messages()]


class T5Item(Resource):
    key: str

    class Meta:
        pk_field = "key"

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return []


def test_e260_missing_permission_key():
    from crud_views.lib.views import ListViewPermissionRequired

    vs = ViewSet(model=T5Item, name="t5_e260", resource_permissions=None)

    class T5E260ListView(ListViewPermissionRequired):  # noqa
        cv_viewset = vs  # registers at class definition; cv_permission "view" not in {}

    assert "viewset.E260" in check_error_ids(vs)


def test_e260_ok_when_key_present():
    from crud_views.lib.views import ListViewPermissionRequired

    vs = ViewSet(model=T5Item, name="t5_e260_ok", resource_permissions={"view": "app.view_s3file"})

    class T5E260OkListView(ListViewPermissionRequired):  # noqa
        cv_viewset = vs

    assert "viewset.E260" not in check_error_ids(vs)


def test_e261_resource_as_parent_rejected():
    from crud_views.lib.views import ListView
    from tests.test1.app.models import Author

    vs_parent = ViewSet(model=T5Item, name="t5_e261_parent", resource_permissions=None)

    class T5E261ParentListView(ListView):  # noqa — parent needs a registered view
        cv_viewset = vs_parent

    vs_child = ViewSet(model=Author, name="t5_e261_child", parent=ParentViewSet(name="t5_e261_parent"))

    class T5E261ChildListView(ListView):  # noqa
        cv_viewset = vs_child

    assert "viewset.E261" in check_error_ids(vs_child)
    assert "viewset.E261" not in check_error_ids(vs_parent)


def test_e262_write_views_rejected():
    from crud_views.lib.views import UpdateView

    vs = ViewSet(model=T5Item, name="t5_e262", resource_permissions=None)

    class T5E262UpdateView(UpdateView):  # noqa
        cv_viewset = vs

    assert "viewset.E262" in check_error_ids(vs)


def test_no_new_errors_for_plain_resource_viewset(vs_t2):
    # vs_t2 has no registered views with permissions issues and no parent
    ids = check_error_ids(vs_t2)
    assert "viewset.E260" not in ids
    assert "viewset.E261" not in ids
    assert "viewset.E262" not in ids
```

Note: `ListView`/`UpdateView` non-permission variants are exported from `crud_views.lib.views`; each class definition self-registers via the metaclass. All names are unique (`t5_*`) because the registry is process-global.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_resource_viewset.py -v`
Expected: the four new tests FAIL (no `viewset.E260/E261/E262` ids emitted); existing tests still PASS.

- [ ] **Step 3: Implement the checks**

In `src/crud_views/lib/viewset/__init__.py`:

Extend the check import:

```python
from ..check import CheckAttributeReg, Check, CheckExpression, CheckTemplate
```

Extend `checks()` (lines 142–151) — after the existing E002/E003/E111 yields, before the per-view loop:

```python
        if self.is_resource:
            from crud_views.lib.views import CreateView, DeleteView, UpdateView

            for key, view in self._views.items():
                if issubclass(view, CrudViewPermissionRequiredMixin):
                    yield CheckExpression(
                        context=view,
                        id="E260",
                        expression=view.cv_permission in self.permissions,
                        msg=(
                            f"cv_permission {view.cv_permission!r} of view {key!r} is not declared in "
                            f"resource_permissions of {self!r} — add the key or use the "
                            f"non-PermissionRequired view variant"
                        ),
                    )
                yield CheckExpression(
                    context=view,
                    id="E262",
                    expression=not issubclass(view, (CreateView, UpdateView, DeleteView)),
                    msg=(
                        f"view {key!r} is a Create/Update/Delete view — not supported for "
                        f"Resource-based ViewSets (writes need a real model, see docs)"
                    ),
                )

        if self.parent is not None:
            yield CheckExpression(
                context=self,
                id="E261",
                expression=not self.parent.viewset.is_resource,
                msg=(
                    f"parent ViewSet {self.parent.name!r} is Resource-based — Resources can only be "
                    f"leaves in the nesting hierarchy (v1)"
                ),
            )
```

Implementation notes:
- The `CreateView/UpdateView/DeleteView` import stays inside the method (top-level would be a cycle: `views` modules import from `viewset`). Verify all three non-permission base classes are importable from `crud_views.lib.views`; if `DeleteView` is only exported as `DeleteViewPermissionRequired`, import the base from its module (`crud_views.lib.views.delete`).
- `CrudViewPermissionRequiredMixin` is already imported at the top of the module.
- E261 evaluates `self.parent.viewset` — resolves from the registry; at system-check time all ViewSets are registered.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_resource_viewset.py -v`
Expected: all PASS

- [ ] **Step 5: Full suite regression, format, lint**

Run: `cd tests && pytest`
Expected: green — in particular `test_check_messages.py` / `test_settings_checks.py` (registry-wide checks now include the new ViewSets from tests and the app; ordering of yielded checks may matter to those tests only if they assert exact counts — if one does, update its expectation and say so in the commit message).
Run from repo root: `task format && task check`

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/viewset/__init__.py tests/test1/test_resource_viewset.py
git commit -m "feat(checks): E260-E262 — resource permission coverage, leaf-only nesting, no write views"
```

---

### Task 6: Nesting — model parent with Resource child

**Files:**
- Modify: `tests/test1/app/resources.py` (append nested Resource + ViewSet + views)
- Modify: `tests/test1/app/urls.py`
- Test: append to `tests/test1/test_resource_views.py`

**Interfaces:**
- Consumes: `ParentViewSet` (existing), `cv_publisher` (existing model ViewSet, name `"publisher"`, INT pk → URL kwarg `publisher_pk`), `S3FileTable`, `ResourceViewMixin`.
- Produces: routes `/publisher/<publisher_pk>/publisherfile/` (list) and `/publisher/<publisher_pk>/publisherfile/<pk>/detail/`; `NESTED_BUCKET: list[dict]` module-level store scoped by key prefix `publisher-<pk>/`.

- [ ] **Step 1: Append to `tests/test1/app/resources.py`**

Extend imports:

```python
from crud_views.lib.viewset import ParentViewSet
```

Append:

```python
# nested resource: scoped to a Publisher parent via key prefix "publisher-<pk>/"
NESTED_BUCKET: list[dict] = []


class PublisherFile(Resource):
    key: str
    size: int = 0

    class Meta:
        verbose_name = "publisher file"
        verbose_name_plural = "publisher files"
        app_label = "app"
        pk_field = "key_md5"
        pk_type = PrimaryKeys.HEX

    @property
    def key_md5(self) -> str:
        return hashlib.md5(self.key.encode()).hexdigest()

    def __str__(self) -> str:
        return self.key

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        # THE nesting contract (spec §8.1): the parent pk arrives as a URL
        # kwarg; scoping the listing is the developer's responsibility.
        prefix = f"publisher-{url_kwargs['publisher_pk']}/"
        return [cls.model_validate(row) for row in NESTED_BUCKET if row["key"].startswith(prefix)]


cv_publisher_file = ViewSet(
    model=PublisherFile,
    name="publisherfile",
    parent=ParentViewSet(name="publisher"),
    resource_permissions={"view": "app.view_s3file"},
)


class PublisherFileListView(ResourceViewMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_publisher_file
    table_class = S3FileTable
    cv_list_actions = ["detail"]


class PublisherFileDetailView(ResourceViewMixin, DetailCustomViewPermissionRequired):
    cv_viewset = cv_publisher_file
    template_name = "app/s3file_detail.html"
```

- [ ] **Step 2: Wire URLs in `tests/test1/app/urls.py`**

Change the resources import to:

```python
from tests.test1.app.resources import cv_s3file, cv_publisher_file
```

Append:

```python
urlpatterns += cv_publisher_file.urlpatterns
```

- [ ] **Step 3: Write the failing tests** (append to `tests/test1/test_resource_views.py`)

```python
@pytest.fixture
def nested_bucket():
    from tests.test1.app import resources

    original = [dict(row) for row in resources.NESTED_BUCKET]
    yield resources.NESTED_BUCKET
    resources.NESTED_BUCKET[:] = original


@pytest.mark.django_db
def test_nested_list_scoped_to_parent(client_user_s3file_view: Client, nested_bucket):
    from tests.test1.app.models import Publisher

    p1 = Publisher.objects.create(name="Penguin")
    p2 = Publisher.objects.create(name="HarperCollins")
    nested_bucket.extend(
        [
            {"key": f"publisher-{p1.pk}/contract.pdf", "size": 10},
            {"key": f"publisher-{p2.pk}/other.pdf", "size": 20},
        ]
    )

    response = client_user_s3file_view.get(f"/publisher/{p1.pk}/publisherfile/")
    assert response.status_code == 200
    content = response.content.decode()
    # scoped: p1's file is present, p2's is not
    assert f"publisher-{p1.pk}/contract.pdf" in content
    assert f"publisher-{p2.pk}/other.pdf" not in content


@pytest.mark.django_db
def test_nested_detail_url_contains_parent_pk(client_user_s3file_view: Client, nested_bucket):
    from tests.test1.app.models import Publisher

    p1 = Publisher.objects.create(name="Penguin")
    key = f"publisher-{p1.pk}/contract.pdf"
    nested_bucket.append({"key": key, "size": 10})

    response = client_user_s3file_view.get(f"/publisher/{p1.pk}/publisherfile/{md5(key)}/detail/")
    assert response.status_code == 200
    assert key in response.content.decode()


@pytest.mark.django_db
def test_nested_list_empty_for_parent_without_files(client_user_s3file_view: Client, nested_bucket):
    from tests.test1.app.models import Publisher

    p = Publisher.objects.create(name="NoFiles")
    response = client_user_s3file_view.get(f"/publisher/{p.pk}/publisherfile/")
    assert response.status_code == 200
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_resource_views.py -v`
Expected: all PASS. Known risk: context buttons on the nested list (parent/home buttons) resolve URLs through `view.kwargs` — they receive `publisher_pk` from the request; if a button raises `ViewSetKeyFoundError` for an unregistered key it renders empty (tag-level `ignore_exception`), which is acceptable; a hard 500 is not — investigate, don't skip.

- [ ] **Step 5: Full suite regression, format, lint**

Run: `cd tests && pytest`
Run from repo root: `task format && task check`

- [ ] **Step 6: Commit**

```bash
git add tests/test1/app/resources.py tests/test1/app/urls.py tests/test1/test_resource_views.py
git commit -m "feat(resource): nested Resource ViewSet under model parent (leaf-only nesting)"
```

---

### Task 7: Documentation + CHANGELOG

**Files:**
- Create: `docs/reference/resources.md`
- Modify: `README.md` (feature list — one line + link)
- Modify: `CHANGELOG.md` (Unreleased section)

**Interfaces:**
- Consumes: everything shipped in Tasks 1–6; spec `superpowers/specs/2026-07-15-resource-viewsets-design.md` (§7 permission recipe, §9 pk patterns, §10 non-goals) as the content source.
- Produces: user-facing docs; mkdocs uses the awesome-pages plugin, so a new file under `docs/reference/` is picked up without nav changes.

- [ ] **Step 1: Write `docs/reference/resources.md`**

Structure (write real prose + the code below, sourced from the spec — this is the developer-facing story):

1. **What and why** — render non-DB, table-shaped data (S3 listings, config trees, API results) with the same ViewSet chrome; toolbox scope: list, detail, custom-form actions (e.g. delete-with-confirm), form-less actions. Explicitly: **no create/update** — writes mean the data has a home, use a (possibly unmanaged) model.
2. **Defining a Resource** — the `S3Object` example: fields, `Meta` (verbose names, `app_label`, `pk_field`, `pk_type`), `cv_get_items`, default `cv_get_item` behavior and when to override it.
3. **Primary keys for path-like data** — both patterns from spec §9 with full code: base64url (reversible; keeps a direct-lookup `cv_get_item` override possible; strip `=` padding, restore with `s + "=" * (-len(s) % 4)`) and md5 hash (`pk_type = ViewSet.PK.HEX`; zero extra code; one-way, so resolution is always list-and-match).
4. **Permissions** — the unmanaged permission-holder model recipe from spec §7 verbatim (`managed = False`, `default_permissions = ()`, custom `permissions`), `resource_permissions={"view": ..., "delete": ...}`, `resource_permissions=None` meaning login-only responsibility lies with the project, and the E260 startup check.
5. **Views** — `ResourceViewMixin` FIRST in bases; complete examples for list (`ListViewTableMixin` + table), detail (`DetailCustomView` + own template), delete-with-confirm (`CustomFormView` + `CrispyDeleteForm` + `cv_form_valid` hook calling `delete_object`), form-less action (`ActionView.action`).
6. **Nesting** — rule "models can sit anywhere; Resources are leaves"; model→resource child example with `parent=ParentViewSet(...)` and parent-pk scoping inside `cv_get_items`; E261 for the unsupported direction.
7. **Limitations** — the spec §10 non-goals table adapted for users, including: no django-filter (filter inside `cv_get_items`; in-memory filter helper is a possible future addition), pagination is in-memory, guardian/workflow/polymorphic don't apply to Resources, no ManageView.

- [ ] **Step 2: README + CHANGELOG**

README: add one feature bullet where the feature list is, e.g. `- Resources: render non-ORM data (S3 listings, API results) through ViewSets — list, detail and custom actions without a Django model` linking to the docs page.

CHANGELOG (Unreleased / next minor):

```markdown
### Added
- `Resource` + `ResourceViewMixin`: ViewSets over non-ORM data (list, detail, custom-form and
  form-less actions). Explicit `resource_permissions`, leaf-only nesting, system checks E260–E262.
```

- [ ] **Step 3: Verify docs build**

Run: `uv run mkdocs build 2>&1 | tail -5` (or `task docs` briefly and Ctrl-C)
Expected: build succeeds, no broken-link warnings for the new page.

- [ ] **Step 4: Full suite one last time**

Run: `cd tests && pytest`
Expected: green.
Run from repo root: `task format && task check`

- [ ] **Step 5: Commit**

```bash
git add docs/reference/resources.md README.md CHANGELOG.md
git commit -m "docs: Resources — non-ORM data in ViewSets"
```

---

## Out of scope (do not implement, documented as v2 in the spec)

- In-memory `ResourceFilter` (spec §10.1)
- Resource-as-parent nesting (spec §8.2)
- `GuardianViewSet` with Resources (its `register()` deletes the manage view that resource registration never creates — combination is unsupported; docs say so)

## Verification checklist (after all tasks)

- `cd tests && pytest` — full suite green (474+ existing tests + ~35 new)
- `task check` — clean
- `git log --oneline` — 7 feature/docs commits
- Manual spec walk: every row of spec §3's coupling-point table has its strategy implemented (1,2,3 → Task 2; 4,5 → Task 1 shim + Task 3 session test; 6 → Task 3 mixin; 7 → Task 2; 8 → Task 5)
