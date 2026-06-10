# manage_view_class Customization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow the base class used for the auto-registered `manage` view to be overridden per-viewset (`manage_view_class` field) and globally (`CRUD_VIEWS_MANAGE_VIEW_CLASS` / `CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS` settings).

**Architecture:** Add `manage_view_class: str | None` to `ViewSet` and `CrudViewsSettings`. Add `get_manage_view_class()` to `ViewSet` (returns `ManageView` by default) and override it in `GuardianViewSet` (returns `GuardianManageView` by default). Update both `register()` methods to call `get_manage_view_class()` instead of hard-coding the base class.

**Tech Stack:** Python, Django, Pydantic v2, `django.utils.module_loading.import_string`, pytest.

---

## File Map

| File | Change |
|------|--------|
| `crud_views/lib/settings.py` | Add `manage_view_class` and `guardian_manage_view_class` settings fields |
| `crud_views/lib/viewset/__init__.py` | Add `manage_view_class` field; add `get_manage_view_class()`; update `register()` |
| `crud_views_guardian/lib/viewset.py` | Override `get_manage_view_class()`; update `register()` |
| `tests/test1/app/views.py` | Add `CustomManageViewForTest` and `CustomGuardianManageViewForTest` helper classes |
| `tests/test1/test_manage.py` | Add tests for ViewSet field, global setting, priority |
| `tests/test1/test_guardian.py` | Add tests for GuardianViewSet field, global setting, priority |
| `docs/reference/settings.md` | Document the two new settings |
| `docs/reference/guardian.md` | Add `manage_view_class` customization subsection |
| `skills/django-crud-views/SKILL.md` | Update GuardianManageView section; add manage view customization note |

---

### Task 1: Add two settings fields and write the failing tests

**Files:**
- Modify: `crud_views/lib/settings.py`
- Test: `tests/test1/test_manage.py`

- [ ] **Step 1: Write the failing tests**

Add to the bottom of `tests/test1/test_manage.py`:

```python
def test_settings_manage_view_class_default():
    """manage_view_class setting should default to None."""
    from crud_views.lib.settings import crud_views_settings
    assert crud_views_settings.manage_view_class is None


def test_settings_guardian_manage_view_class_default():
    """guardian_manage_view_class setting should default to None."""
    from crud_views.lib.settings import crud_views_settings
    assert crud_views_settings.guardian_manage_view_class is None
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test1/test_manage.py::test_settings_manage_view_class_default tests/test1/test_manage.py::test_settings_guardian_manage_view_class_default -v
```

Expected: `FAILED` — `AttributeError: 'CrudViewsSettings' object has no attribute 'manage_view_class'`

- [ ] **Step 3: Add the two settings fields**

In `crud_views/lib/settings.py`, add after the `manage_show_users` line (around line 36):

```python
manage_view_class: str | None = from_settings("CRUD_VIEWS_MANAGE_VIEW_CLASS", default=None)
guardian_manage_view_class: str | None = from_settings("CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS", default=None)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test1/test_manage.py::test_settings_manage_view_class_default tests/test1/test_manage.py::test_settings_guardian_manage_view_class_default -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add crud_views/lib/settings.py tests/test1/test_manage.py
git commit -m "feat: add manage_view_class and guardian_manage_view_class settings"
```

---

### Task 2: Add test helper classes to the test app

**Files:**
- Modify: `tests/test1/app/views.py`

These classes must be at a stable importable dotted path for use with `import_string` in tests.

- [ ] **Step 1: Add helper classes**

Open `tests/test1/app/views.py`. Add near the top (after existing imports):

```python
from crud_views.lib.views.manage import ManageView
```

(Skip if `ManageView` is already imported.)

Then add at the bottom of the file:

```python
# ── Test helpers ──────────────────────────────────────────────────────────────

class CustomManageViewForTest(ManageView):
    """Importable subclass used by test_manage.py to verify manage_view_class."""
    pass
```

- [ ] **Step 2: Add guardian helper**

In `tests/test1/app/views.py`, also add:

```python
class CustomGuardianManageViewForTest(ManageView):
    """Importable subclass used by test_guardian.py to verify manage_view_class on GuardianViewSet."""
    pass
```

- [ ] **Step 3: Verify importability**

```
python -c "from tests.test1.app.views import CustomManageViewForTest, CustomGuardianManageViewForTest; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add tests/test1/app/views.py
git commit -m "test: add CustomManageViewForTest helpers for manage_view_class tests"
```

---

### Task 3: Add `manage_view_class` field and `get_manage_view_class()` to ViewSet, write failing tests first

**Files:**
- Modify: `crud_views/lib/viewset/__init__.py`
- Test: `tests/test1/test_manage.py`

- [ ] **Step 1: Write the failing tests**

Add to the bottom of `tests/test1/test_manage.py`:

```python
def test_get_manage_view_class_default(cv_author):
    """Default: get_manage_view_class() returns ManageView."""
    from crud_views.lib.views.manage import ManageView
    assert cv_author.get_manage_view_class() is ManageView


def test_get_manage_view_class_global_setting(cv_author, monkeypatch):
    """Global setting: get_manage_view_class() returns the class named by the setting."""
    from crud_views.lib.settings import crud_views_settings
    monkeypatch.setattr(crud_views_settings, "manage_view_class", "tests.test1.app.views.CustomManageViewForTest")
    from tests.test1.app.views import CustomManageViewForTest
    assert cv_author.get_manage_view_class() is CustomManageViewForTest


def test_get_manage_view_class_per_viewset_field(cv_author, monkeypatch):
    """Per-viewset field: get_manage_view_class() returns the class named by the field."""
    monkeypatch.setattr(cv_author, "manage_view_class", "tests.test1.app.views.CustomManageViewForTest")
    from tests.test1.app.views import CustomManageViewForTest
    assert cv_author.get_manage_view_class() is CustomManageViewForTest


def test_get_manage_view_class_field_wins_over_setting(cv_author, monkeypatch):
    """Priority: per-viewset field beats global setting."""
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.views.manage import ManageView
    monkeypatch.setattr(crud_views_settings, "manage_view_class", "crud_views.lib.views.manage.ManageView")
    monkeypatch.setattr(cv_author, "manage_view_class", "tests.test1.app.views.CustomManageViewForTest")
    from tests.test1.app.views import CustomManageViewForTest
    result = cv_author.get_manage_view_class()
    assert result is CustomManageViewForTest
    assert result is not ManageView
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test1/test_manage.py::test_get_manage_view_class_default tests/test1/test_manage.py::test_get_manage_view_class_global_setting tests/test1/test_manage.py::test_get_manage_view_class_per_viewset_field tests/test1/test_manage.py::test_get_manage_view_class_field_wins_over_setting -v
```

Expected: `FAILED` — `AttributeError: 'ViewSet' object has no attribute 'get_manage_view_class'`

- [ ] **Step 3: Add the field and method to ViewSet**

In `crud_views/lib/viewset/__init__.py`:

After the `icon_header` field (around line 86), add:

```python
manage_view_class: str | None = None
```

After the `register_view_class` method (around line 236), add:

```python
def get_manage_view_class(self) -> Type[CrudView]:
    from django.utils.module_loading import import_string
    dotted = self.manage_view_class or crud_views_settings.manage_view_class
    if dotted:
        return import_string(dotted)
    return ManageView
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test1/test_manage.py::test_get_manage_view_class_default tests/test1/test_manage.py::test_get_manage_view_class_global_setting tests/test1/test_manage.py::test_get_manage_view_class_per_viewset_field tests/test1/test_manage.py::test_get_manage_view_class_field_wins_over_setting -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add crud_views/lib/viewset/__init__.py tests/test1/test_manage.py
git commit -m "feat: add manage_view_class field and get_manage_view_class() to ViewSet"
```

---

### Task 4: Update `ViewSet.register()` to use `get_manage_view_class()`, write failing test first

**Files:**
- Modify: `crud_views/lib/viewset/__init__.py`
- Test: `tests/test1/test_manage.py`

- [ ] **Step 1: Write the failing test**

Add to the bottom of `tests/test1/test_manage.py`:

```python
def test_register_uses_custom_manage_view_class():
    """ViewSet.register() wires up the class specified by manage_view_class."""
    import uuid
    from crud_views.lib.viewset import ViewSet, _REGISTRY, _REGISTRY_LOCK
    from tests.test1.app.models import Author
    from tests.test1.app.views import CustomManageViewForTest

    name = f"test_custom_{uuid.uuid4().hex[:8]}"
    try:
        vs = ViewSet(
            model=Author,
            name=name,
            manage_view_class="tests.test1.app.views.CustomManageViewForTest",
        )
        manage_class = vs.get_all_views()["manage"]
        assert issubclass(manage_class, CustomManageViewForTest)
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)
```

- [ ] **Step 2: Run the test to verify it fails**

```
pytest tests/test1/test_manage.py::test_register_uses_custom_manage_view_class -v
```

Expected: `FAILED` — registered manage view is a subclass of `ManageView` but not of `CustomManageViewForTest`.

- [ ] **Step 3: Update `ViewSet.register()` to use `get_manage_view_class()`**

In `crud_views/lib/viewset/__init__.py`, in the `register` model validator, replace:

```python
        class AutoManageView(ManageView):
            model = self.model
            cv_viewset = self
```

with:

```python
        base = self.get_manage_view_class()
        AutoManageView = type("AutoManageView", (base,), {"model": self.model, "cv_viewset": self})
```

- [ ] **Step 4: Run the test to verify it passes**

```
pytest tests/test1/test_manage.py::test_register_uses_custom_manage_view_class -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the full manage test suite to check for regressions**

```
pytest tests/test1/test_manage.py -v
```

Expected: all existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add crud_views/lib/viewset/__init__.py tests/test1/test_manage.py
git commit -m "feat: update ViewSet.register() to use get_manage_view_class()"
```

---

### Task 5: Override `get_manage_view_class()` in GuardianViewSet and update its `register()`, tests first

**Files:**
- Modify: `crud_views_guardian/lib/viewset.py`
- Test: `tests/test1/test_guardian.py`

- [ ] **Step 1: Write the failing tests**

Add to the bottom of `tests/test1/test_guardian.py`:

```python
# ── manage_view_class customization ───────────────────────────────────────────


def test_guardian_get_manage_view_class_default(cv_guardian_author):
    """Default: GuardianViewSet.get_manage_view_class() returns GuardianManageView."""
    from crud_views_guardian.lib.views import GuardianManageView
    assert cv_guardian_author.get_manage_view_class() is GuardianManageView


def test_guardian_get_manage_view_class_global_setting(cv_guardian_author, monkeypatch):
    """Global guardian setting: get_manage_view_class() returns the named class."""
    from crud_views.lib.settings import crud_views_settings
    monkeypatch.setattr(crud_views_settings, "guardian_manage_view_class", "tests.test1.app.views.CustomGuardianManageViewForTest")
    from tests.test1.app.views import CustomGuardianManageViewForTest
    assert cv_guardian_author.get_manage_view_class() is CustomGuardianManageViewForTest


def test_guardian_get_manage_view_class_per_viewset_field(cv_guardian_author, monkeypatch):
    """Per-viewset field on GuardianViewSet: get_manage_view_class() returns the named class."""
    monkeypatch.setattr(cv_guardian_author, "manage_view_class", "tests.test1.app.views.CustomGuardianManageViewForTest")
    from tests.test1.app.views import CustomGuardianManageViewForTest
    assert cv_guardian_author.get_manage_view_class() is CustomGuardianManageViewForTest


def test_guardian_get_manage_view_class_field_wins_over_setting(cv_guardian_author, monkeypatch):
    """Priority: per-viewset field beats guardian global setting."""
    from crud_views.lib.settings import crud_views_settings
    from crud_views_guardian.lib.views import GuardianManageView
    monkeypatch.setattr(crud_views_settings, "guardian_manage_view_class", "crud_views_guardian.lib.views.GuardianManageView")
    monkeypatch.setattr(cv_guardian_author, "manage_view_class", "tests.test1.app.views.CustomGuardianManageViewForTest")
    from tests.test1.app.views import CustomGuardianManageViewForTest
    result = cv_guardian_author.get_manage_view_class()
    assert result is CustomGuardianManageViewForTest
    assert result is not GuardianManageView


def test_guardian_register_uses_custom_manage_view_class():
    """GuardianViewSet.register() wires up the class specified by manage_view_class."""
    import uuid
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.app.models import Author
    from tests.test1.app.views import CustomGuardianManageViewForTest

    name = f"test_gv_custom_{uuid.uuid4().hex[:8]}"
    try:
        vs = GuardianViewSet(
            model=Author,
            name=name,
            manage_view_class="tests.test1.app.views.CustomGuardianManageViewForTest",
        )
        manage_class = vs.get_all_views()["manage"]
        assert issubclass(manage_class, CustomGuardianManageViewForTest)
    finally:
        with _REGISTRY_LOCK:
            _REGISTRY.pop(name, None)
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test1/test_guardian.py::test_guardian_get_manage_view_class_default tests/test1/test_guardian.py::test_guardian_get_manage_view_class_global_setting tests/test1/test_guardian.py::test_guardian_get_manage_view_class_per_viewset_field tests/test1/test_guardian.py::test_guardian_get_manage_view_class_field_wins_over_setting tests/test1/test_guardian.py::test_guardian_register_uses_custom_manage_view_class -v
```

Expected: `FAILED` — `AttributeError: 'GuardianViewSet' object has no attribute 'get_manage_view_class'` (the method doesn't exist yet on the guardian viewset).

- [ ] **Step 3: Add `get_manage_view_class()` override to GuardianViewSet**

In `crud_views_guardian/lib/viewset.py`, after the `cv_guardian_accept_global_perms` field and before the `register` validator, add:

```python
    def get_manage_view_class(self):
        from django.utils.module_loading import import_string
        from crud_views_guardian.lib.views import GuardianManageView
        dotted = self.manage_view_class or crud_views_settings.guardian_manage_view_class
        if dotted:
            return import_string(dotted)
        return GuardianManageView
```

Also add this import at the top of `crud_views_guardian/lib/viewset.py`:

```python
from crud_views.lib.settings import crud_views_settings
```

- [ ] **Step 4: Update `GuardianViewSet.register()` to use `get_manage_view_class()`**

In `crud_views_guardian/lib/viewset.py`, in the `register` validator, replace:

```python
        from crud_views_guardian.lib.views import GuardianManageView

        # Remove the base ManageView that super().register() just added so that the metaclass
        # can call register_view_class() without hitting the "already registered" guard.
        del self._views["manage"]

        class AutoManageView(GuardianManageView):
            model = self.model
            cv_viewset = self
```

with:

```python
        # Remove the base ManageView that super().register() just added so that the metaclass
        # can call register_view_class() without hitting the "already registered" guard.
        del self._views["manage"]

        base = self.get_manage_view_class()
        AutoManageView = type("AutoManageView", (base,), {"model": self.model, "cv_viewset": self})
```

- [ ] **Step 5: Run the new guardian tests to verify they pass**

```
pytest tests/test1/test_guardian.py::test_guardian_get_manage_view_class_default tests/test1/test_guardian.py::test_guardian_get_manage_view_class_global_setting tests/test1/test_guardian.py::test_guardian_get_manage_view_class_per_viewset_field tests/test1/test_guardian.py::test_guardian_get_manage_view_class_field_wins_over_setting tests/test1/test_guardian.py::test_guardian_register_uses_custom_manage_view_class -v
```

Expected: `PASSED`

- [ ] **Step 6: Run full guardian test suite to check for regressions**

```
pytest tests/test1/test_guardian.py -v
```

Expected: all existing tests still pass.

- [ ] **Step 7: Commit**

```bash
git add crud_views_guardian/lib/viewset.py tests/test1/test_guardian.py
git commit -m "feat: add get_manage_view_class() to GuardianViewSet and update register()"
```

---

### Task 6: Run full test suite

**Files:** none

- [ ] **Step 1: Run the complete test suite**

```
pytest tests/test1/ -v
```

Expected: all tests pass. If any fail, fix before continuing.

- [ ] **Step 2: Commit if any fixes were required**

```bash
git add -p
git commit -m "fix: resolve test regressions from manage_view_class feature"
```

---

### Task 7: Update documentation

**Files:**
- Modify: `docs/reference/settings.md`
- Modify: `docs/reference/guardian.md`

- [ ] **Step 1: Add the two new settings to `docs/reference/settings.md`**

In the **Basic settings** table, add two new rows after `CRUD_VIEWS_MANAGE_SHOW_USERS`:

```markdown
| CRUD_VIEWS_MANAGE_VIEW_CLASS | Dotted import path to a custom `ManageView` subclass used as the base for auto-registered manage views. When `None`, uses `ManageView`. | `str \| None` | `None` |
| CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS | Dotted import path to a custom `GuardianManageView` subclass used as the base for auto-registered guardian manage views. When `None`, uses `GuardianManageView`. | `str \| None` | `None` |
```

- [ ] **Step 2: Add a customization subsection to `docs/reference/guardian.md`**

In `docs/reference/guardian.md`, after the **GuardianManageView** section, add:

```markdown
### Customizing the Manage View Class

To use a custom manage view class for a specific viewset, set `manage_view_class` to a dotted import path:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet

class MyCustomGuardianManageView(GuardianManageView):
    template_name = "myapp/custom_guardian_manage.html"

cv_author = GuardianViewSet(
    model=Author,
    name="author",
    manage_view_class="myapp.views.MyCustomGuardianManageView",
)
```

To apply a custom class globally to all guardian viewsets, set in `settings.py`:

```python
CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS = "myapp.views.MyCustomGuardianManageView"
```

The per-viewset `manage_view_class` field takes priority over the global setting.

For plain `ViewSet` (non-guardian), the equivalent is:

```python
CRUD_VIEWS_MANAGE_VIEW_CLASS = "myapp.views.MyCustomManageView"
```
```

- [ ] **Step 3: Commit**

```bash
git add docs/reference/settings.md docs/reference/guardian.md
git commit -m "docs: document manage_view_class customization in settings and guardian reference"
```

---

### Task 8: Update the django-crud-views skill

**Files:**
- Modify: `skills/django-crud-views/SKILL.md`

- [ ] **Step 1: Update the GuardianManageView section**

In `skills/django-crud-views/SKILL.md`, find the `### GuardianManageView` section and append:

```markdown
To customise the manage view class for a specific viewset, pass `manage_view_class="dotted.path.MyClass"` to `GuardianViewSet(...)`. Global default: `CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS`. For plain `ViewSet`: `CRUD_VIEWS_MANAGE_VIEW_CLASS`. Per-viewset field takes priority over the global setting.
```

- [ ] **Step 2: Commit**

```bash
git add skills/django-crud-views/SKILL.md
git commit -m "docs: update django-crud-views skill with manage_view_class customization"
```

---

### Task 9: Final verification

- [ ] **Step 1: Run the full test suite one last time**

```
pytest tests/test1/ -v --tb=short
```

Expected: all tests pass, no warnings about unresolved imports.

- [ ] **Step 2: Verify the skill is up to date**

Read `skills/django-crud-views/SKILL.md` and confirm the manage view customization section is present and accurate.
