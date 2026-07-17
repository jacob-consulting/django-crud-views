# Expand Django System Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the five remaining check gaps from issue #28 — a type-validating check class, formset type/mapping checks, a reactivated context-action check, a filter-header template check, and workflow dependency checks.

**Architecture:** Checks are pydantic `Check` subclasses that yield `django.core.checks.Error` messages from a `messages()` method; view/mixin `checks()` classmethods yield instances, collected via `ViewSet.checks_all()`. New check classes go in `crud_views/lib/check.py`; wiring goes in the relevant view/mixin; the workflow app gets its own `checks.py` registered from `apps.py:ready()`. Tests follow the repo idiom: instantiate a check with a dummy `context` object and assert on `list(check.messages())`.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, pydantic, pytest. Test app under `tests/test1/`.

## Global Constraints

- Line length 120, double quotes, `ruff format` clean (pre-commit runs `ruff-format`).
- All `CrudView` class attributes use the `cv_` prefix.
- Check ids resolve through `Check.get_id()` to `viewset.<id>` for core checks; workflow checks use literal `crud_views_workflow.Exxx` ids.
- Run tests from `tests/`: `cd tests && pytest`.
- Test app imports: `from tests.test1.app.models import Book, Publisher`, `from crud_views.lib.formsets import FormSet, FormSets`.
- Do NOT touch gap #4 — `cv_extends_template` (view) and `extends` (viewset) are already validated by E111.

## File Structure

- `src/crud_views/lib/check.py` — add `CheckAttributeType` (E101) and `CheckMapping` (E205); repair `ContextActionCheck` (E203).
- `src/crud_views/lib/view/base.py` — wire `ContextActionCheck` into `CrudView.checks()`.
- `src/crud_views/lib/formsets/mixins.py` — replace colliding E200 declarations with E204/E205/E206.
- `src/crud_views/lib/views/list.py` — add filter-header `CheckTemplateOrCode` to a `ListView.checks()` override.
- `src/crud_views_workflow/checks.py` — NEW: dependency checks (E001/E002).
- `src/crud_views_workflow/apps.py` — register the new checks module in `ready()`.
- `tests/test1/test_expand_checks.py` — NEW: all unit tests for this work.

---

### Task 1: `CheckAttributeType` (E101)

**Files:**
- Modify: `src/crud_views/lib/check.py` (add class after `CheckAttributeReg`)
- Test: `tests/test1/test_expand_checks.py` (new file)

**Interfaces:**
- Consumes: `CheckAttribute` (existing base: fields `context`, `id`, `attribute`, `nullable`; properties `exists`, `value`; `messages()`).
- Produces: `CheckAttributeType(context, id, attribute, expected_type)` — `expected_type: type | tuple[type, ...]`; yields the base existence error(s) plus one `Error` (id `viewset.<id>`) when the attribute exists, is non-None, and `isinstance(value, expected_type)` is False.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_expand_checks.py`:

```python
from crud_views.lib.check import CheckAttributeType


class GoodType:
    attr = "a string"


class BadType:
    attr = 123


class NoneType:
    attr = None


def test_check_attribute_type_correct_emits_no_message():
    check = CheckAttributeType(context=GoodType, id="E101", attribute="attr", expected_type=str)
    assert list(check.messages()) == []


def test_check_attribute_type_wrong_emits_error():
    check = CheckAttributeType(context=BadType, id="E101", attribute="attr", expected_type=str)
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E101"
    assert "is not of type" in messages[0].msg


def test_check_attribute_type_none_defers_to_existence_only():
    # nullable=True so the existence check passes; type check must not fire on None
    check = CheckAttributeType(context=NoneType, id="E101", attribute="attr", expected_type=str, nullable=True)
    assert list(check.messages()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_expand_checks.py -v`
Expected: FAIL with `ImportError: cannot import name 'CheckAttributeType'`

- [ ] **Step 3: Write minimal implementation**

In `src/crud_views/lib/check.py`, add after the `CheckAttributeReg` class (ends line ~98):

```python
class CheckAttributeType(CheckAttribute):
    """
    Check attribute value is an instance of the expected type
    """

    id: str = "E101"
    expected_type: type | tuple[type, ...]
    msg: str = "Attribute »{attribute}» value »{value}» is not of type »{expected_type}» at »{context}»"

    def get_message_context(self) -> dict:
        context = super().get_message_context()
        context.update(expected_type=self.expected_type)
        return context

    def messages(self) -> Iterable[CheckMessage]:
        yield from super().messages()
        if self.exists and self.value is not None and not isinstance(self.value, self.expected_type):
            yield Error(id=self.get_id(), msg=self.get_message())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_expand_checks.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/check.py tests/test1/test_expand_checks.py
git commit -m "feat(checks): add CheckAttributeType (E101) for value-type validation (#28)"
```

---

### Task 2: `CheckMapping` (E205)

**Files:**
- Modify: `src/crud_views/lib/check.py` (add class after `CheckAttributeType`)
- Test: `tests/test1/test_expand_checks.py`

**Interfaces:**
- Consumes: `CheckAttribute` base.
- Produces: `CheckMapping(context, id, attribute, key_type, value_type)` — validates the attribute is a `dict`; every key is a **subclass** of `key_type` (guarded by `isinstance(key, type)` so a non-class key yields an error instead of raising `TypeError`); every value is an **instance** of `value_type`. Yields one `Error` per violation (id `viewset.<id>`).

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_expand_checks.py`:

```python
from crud_views.lib.check import CheckMapping
from django.db.models import Model
from tests.test1.app.models import Book


class NotADict:
    attr = ["not", "a", "dict"]


class NonClassKey:
    attr = {"strkey": "v"}


class NonSubclassKey:
    attr = {int: "v"}


class BadValue:
    attr = {Book: 123}


class ValidMapping:
    attr = {Book: "v"}


def test_check_mapping_not_a_dict_errors():
    check = CheckMapping(context=NotADict, id="E205", attribute="attr", key_type=Model, value_type=str)
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E205"


def test_check_mapping_non_class_key_errors_without_raising():
    check = CheckMapping(context=NonClassKey, id="E205", attribute="attr", key_type=Model, value_type=str)
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E205"


def test_check_mapping_non_subclass_key_errors():
    check = CheckMapping(context=NonSubclassKey, id="E205", attribute="attr", key_type=Model, value_type=str)
    assert len(list(check.messages())) == 1


def test_check_mapping_bad_value_errors():
    check = CheckMapping(context=BadValue, id="E205", attribute="attr", key_type=Model, value_type=str)
    assert len(list(check.messages())) == 1


def test_check_mapping_valid_emits_no_message():
    check = CheckMapping(context=ValidMapping, id="E205", attribute="attr", key_type=Model, value_type=str)
    assert list(check.messages()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_expand_checks.py -k mapping -v`
Expected: FAIL with `ImportError: cannot import name 'CheckMapping'`

- [ ] **Step 3: Write minimal implementation**

In `src/crud_views/lib/check.py`, add after `CheckAttributeType`:

```python
class CheckMapping(CheckAttribute):
    """
    Check attribute is a dict mapping keys (subclasses of key_type) to values (instances of value_type)
    """

    id: str = "E205"
    key_type: type | tuple[type, ...]
    value_type: type | tuple[type, ...]
    msg: str = "Attribute »{attribute}» at »{context}» is not a valid mapping: {detail}"

    def _error(self, detail: str) -> Error:
        kwargs = self.get_message_context()
        return Error(id=self.get_id(), msg=self.msg.format(detail=detail, **kwargs))

    def messages(self) -> Iterable[CheckMessage]:
        yield from super().messages()
        if not self.exists or self.value is None:
            return
        value = self.value
        if not isinstance(value, dict):
            yield self._error(f"expected a dict, got {type(value).__name__}")
            return
        for key, val in value.items():
            if not isinstance(key, type) or not issubclass(key, self.key_type):
                yield self._error(f"key »{key!r}» is not a subclass of {self.key_type}")
            if not isinstance(val, self.value_type):
                yield self._error(f"value for »{key!r}» is not of type {self.value_type}")
```

Note: `get_message_context()` (inherited from `CheckAttribute`) includes a `value` key; `_error` passes `detail` explicitly and spreads the rest — `msg` references only `{attribute}`, `{context}`, `{detail}`, so extra keys are harmless.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_expand_checks.py -k mapping -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/check.py tests/test1/test_expand_checks.py
git commit -m "feat(checks): add CheckMapping (E205) for dict key/value type validation (#28)"
```

---

### Task 3: Formsets checks wiring (E204 / E205 / E206)

**Files:**
- Modify: `src/crud_views/lib/formsets/mixins.py` (three `checks()` methods)
- Test: `tests/test1/test_expand_checks.py`

**Interfaces:**
- Consumes: `CheckAttributeType` (Task 1), `CheckMapping` (Task 2), existing `CheckAttribute`.
- Produces: `FormSetMixinBase.checks()` yields `CheckAttribute(id="E206", attribute="cv_formsets_required")`; `FormSetMixin.checks()` yields `CheckAttributeType(id="E204", attribute="cv_formsets", expected_type=FormSets)`; `PolymorphicFormSetsViewMixin.checks()` yields `CheckMapping(id="E205", attribute="cv_polymorphic_formsets", key_type=Model, value_type=FormSets)`. All ids distinct from `cv_key`'s E200.

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_expand_checks.py`:

```python
from crud_views.lib.check import CheckAttributeType as _CAT, CheckMapping as _CM
from crud_views.lib.formsets.formsets import FormSets
from tests.test1.app.views_formset import PublisherFormSetCreateView


def test_formset_create_view_yields_e204_typed_check():
    checks = list(PublisherFormSetCreateView.checks())
    e204 = [c for c in checks if getattr(c, "id", None) == "E204"]
    assert len(e204) == 1
    assert isinstance(e204[0], _CAT)
    assert e204[0].attribute == "cv_formsets"
    assert e204[0].expected_type is FormSets


def test_formset_checks_do_not_reuse_e200_for_formsets():
    # E200 belongs to cv_key; formsets must not collide with it
    checks = list(PublisherFormSetCreateView.checks())
    e200_attrs = {getattr(c, "attribute", None) for c in checks if getattr(c, "id", None) == "E200"}
    assert "cv_formsets" not in e200_attrs
    assert "cv_formsets_required" not in e200_attrs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_expand_checks.py -k formset -v`
Expected: FAIL — no check with id `E204` (currently `cv_formsets` is declared under `E200`).

- [ ] **Step 3: Write minimal implementation**

In `src/crud_views/lib/formsets/mixins.py`:

Update the import line (currently `from crud_views.lib.check import Check, CheckAttribute`):

```python
from crud_views.lib.check import Check, CheckAttribute, CheckAttributeType, CheckMapping
from crud_views.lib.formsets.formsets import FormSets
from django.db.models import Model
```

(Keep existing imports; add `Model` and `FormSets` if not already imported. `FormSets` is imported lazily elsewhere via `.formsets` — verify no circular import; if one occurs, import `FormSets`/`Model` inside the `checks()` method instead.)

In `FormSetMixinBase.checks()` change:

```python
        yield CheckAttribute(context=cls, id="E200", attribute="cv_formsets_required")
```

to:

```python
        yield CheckAttribute(context=cls, id="E206", attribute="cv_formsets_required")
```

In `FormSetMixin.checks()` change:

```python
        yield CheckAttribute(context=cls, id="E200", attribute="cv_formsets")
```

to:

```python
        yield CheckAttributeType(context=cls, id="E204", attribute="cv_formsets", expected_type=FormSets)
```

In `PolymorphicFormSetsViewMixin.checks()` change:

```python
        yield CheckAttribute(context=cls, id="E200", attribute="cv_polymorphic_formsets")
```

to:

```python
        yield CheckMapping(
            context=cls,
            id="E205",
            attribute="cv_polymorphic_formsets",
            key_type=Model,
            value_type=FormSets,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_expand_checks.py -k formset -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the formsets regression suite**

Run: `cd tests && pytest test1/test_formsets_bugs.py -q`
Expected: PASS (no regressions from the id changes)

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/formsets/mixins.py tests/test1/test_expand_checks.py
git commit -m "feat(checks): type/mapping checks for cv_formsets & cv_polymorphic_formsets, fix E200 collision (#28)"
```

---

### Task 4: ~~Reactivate `ContextActionCheck` (E203)~~ — DROPPED as obsolete

> **Outcome (2026-07-17):** This task was NOT completed as written. During
> implementation it was found that `CrudView.cv_get_context()` (`base.py:409`)
> deliberately treats an unresolvable `cv_context_actions` key as "not a
> misconfiguration" and skips it, and that the framework's default context
> actions (all include `"home"`) plus the common partial-viewset pattern would
> make E203 false-positive on legitimate configs. Per human decision, gap #3 is
> closed as **obsolete**: the dead `ContextActionCheck` class was removed from
> `check.py`, no wiring was added, and the `CampaignDetailView` fixture cleanup
> was retained. See design spec section 3. The steps below are retained for
> historical context only — do not execute them.

**Files:**
- Modify: `src/crud_views/lib/check.py` (repair `ContextActionCheck.messages()`)
- Modify: `src/crud_views/lib/view/base.py` (wire into `CrudView.checks()`)
- Test: `tests/test1/test_expand_checks.py`

**Interfaces:**
- Consumes: `ViewSet.has_view(name) -> bool`; view attributes `cv_viewset`, `cv_context_actions: list[str] | None`.
- Produces: `ContextActionCheck(context=cls, id="E203")` yields one `Error` (id `viewset.E203`) per `cv_context_actions` entry that does not resolve via `cv_viewset.has_view(...)`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_expand_checks.py`:

```python
from crud_views.lib.check import ContextActionCheck


class FakeViewset:
    def __init__(self, keys):
        self._keys = keys

    def has_view(self, name):
        return name in self._keys


class CtxActionsValid:
    cv_viewset = FakeViewset(["update", "delete"])
    cv_context_actions = ["update", "delete"]


class CtxActionsBad:
    cv_viewset = FakeViewset(["update"])
    cv_context_actions = ["update", "does_not_exist"]


class CtxActionsNone:
    cv_viewset = FakeViewset(["update"])
    cv_context_actions = None


def test_context_action_check_valid_emits_no_message():
    check = ContextActionCheck(context=CtxActionsValid, id="E203")
    assert list(check.messages()) == []


def test_context_action_check_missing_view_emits_error():
    check = ContextActionCheck(context=CtxActionsBad, id="E203")
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E203"
    assert "does_not_exist" in messages[0].msg


def test_context_action_check_none_emits_no_message():
    check = ContextActionCheck(context=CtxActionsNone, id="E203")
    assert list(check.messages()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_expand_checks.py -k context_action -v`
Expected: FAIL — `AttributeError: 'FakeViewset' object has no attribute ...` / the current body reads `self.context.cv` which does not exist on these contexts.

- [ ] **Step 3: Repair the check class**

In `src/crud_views/lib/check.py`, replace the `ContextActionCheck` body:

```python
class ContextActionCheck(Check):
    """
    Checks for context action
    """

    id: str = "E203"
    msg: str = "Context action »{action}» does not resolve to a view in the viewset at »{context}»"

    def messages(self) -> Iterable[CheckMessage]:
        viewset = self.context.cv_viewset
        actions = self.context.cv_context_actions or list()
        for action in actions:
            if not viewset.has_view(action):
                yield Error(id=self.get_id(), msg=self.msg.format(action=action, context=self.context))
```

- [ ] **Step 4: Wire it into `CrudView.checks()`**

In `src/crud_views/lib/view/base.py`, in `CrudView.checks()` (after the E111 yield at line ~98), add:

```python
        yield ContextActionCheck(context=cls, id="E203")
```

Add `ContextActionCheck` to the existing import block from `crud_views.lib.check` (lines 13-16).

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_expand_checks.py -k context_action -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Run the full check suite for regressions**

Run: `cd tests && pytest test1/test_check_messages.py test1/test_settings_checks.py -q`
Expected: PASS. Then run `cd tests && pytest -q` to confirm no registered-check failures surface from real test views whose `cv_context_actions` must all resolve.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/check.py src/crud_views/lib/view/base.py tests/test1/test_expand_checks.py
git commit -m "feat(checks): reactivate ContextActionCheck as E203 (#28)"
```

---

### Task 5: Filter header template check (E110)

**Files:**
- Modify: `src/crud_views/lib/views/list.py` (add `ListView.checks()` override)
- Test: `tests/test1/test_expand_checks.py`

**Interfaces:**
- Consumes: `CheckTemplateOrCode(context, attribute)` (existing; validates `<attr>` / `<attr>_code` pair, default id `E110`).
- Produces: `ListView.checks()` yields everything from `super().checks()` plus `CheckTemplateOrCode(context=cls, attribute="cv_filter_header_template")`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_expand_checks.py`:

```python
from crud_views.lib.check import CheckTemplateOrCode


class FilterHeaderMissing:
    cv_filter_header_template = "does-not-exist.html"
    cv_filter_header_template_code = None


class FilterHeaderValid:
    cv_filter_header_template = "crud_views/snippets/header/filter.html"
    cv_filter_header_template_code = None


def test_filter_header_missing_template_errors():
    check = CheckTemplateOrCode(context=FilterHeaderMissing, attribute="cv_filter_header_template")
    messages = list(check.messages())
    assert len(messages) == 1
    assert "does-not-exist.html" in messages[0].msg


def test_filter_header_valid_template_emits_no_message():
    check = CheckTemplateOrCode(context=FilterHeaderValid, attribute="cv_filter_header_template")
    assert list(check.messages()) == []


def test_list_view_checks_include_filter_header():
    from crud_views.lib.views.list import ListView

    checks = list(ListView.checks())
    attrs = {getattr(c, "attribute", None) for c in checks if isinstance(c, CheckTemplateOrCode)}
    assert "cv_filter_header_template" in attrs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_expand_checks.py -k filter_header -v`
Expected: The two `CheckTemplateOrCode`-behavior tests PASS (class already exists); `test_list_view_checks_include_filter_header` FAILS — `cv_filter_header_template` not yet yielded by `ListView.checks()`.

- [ ] **Step 3: Add the `ListView.checks()` override**

In `src/crud_views/lib/views/list.py`, add a `checks()` classmethod to `ListView` (after the `cv_filter_header` property, staying inside the class). First ensure the imports include `Check` and `CheckTemplateOrCode` and `Iterable`:

```python
from typing import Iterable
from crud_views.lib.check import Check, CheckTemplateOrCode
```

Then add:

```python
    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        yield CheckTemplateOrCode(context=cls, attribute="cv_filter_header_template")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_expand_checks.py -k filter_header -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/views/list.py tests/test1/test_expand_checks.py
git commit -m "feat(checks): validate cv_filter_header_template on ListView (E110) (#28)"
```

---

### Task 6: Workflow dependency checks (E001 / E002)

**Files:**
- Create: `src/crud_views_workflow/checks.py`
- Modify: `src/crud_views_workflow/apps.py` (register in `ready()`)
- Test: `tests/test1/test_expand_checks.py`

**Interfaces:**
- Produces: `crud_views_workflow.checks.check_workflow_dependencies(app_configs=None, **kwargs) -> list[Error]` — returns `[]` when the app is not installed; otherwise yields `Error(id="crud_views_workflow.E001")` if `django_fsm` is not importable and `Error(id="crud_views_workflow.E002")` if `fsm_admin` is not importable. Helper `_importable(name: str) -> bool` (monkeypatchable in tests).

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_expand_checks.py`:

```python
def test_workflow_deps_all_present_no_errors():
    from crud_views_workflow import checks as wf_checks

    # dev env installs the [workflow] extra, so both deps import
    assert wf_checks.check_workflow_dependencies() == []


def test_workflow_missing_django_fsm_emits_e001(monkeypatch):
    from crud_views_workflow import checks as wf_checks

    monkeypatch.setattr(wf_checks, "_importable", lambda name: name != "django_fsm")
    errors = wf_checks.check_workflow_dependencies()
    assert any(e.id == "crud_views_workflow.E001" for e in errors)
    assert all(e.id != "crud_views_workflow.E002" for e in errors)


def test_workflow_missing_fsm_admin_emits_e002(monkeypatch):
    from crud_views_workflow import checks as wf_checks

    monkeypatch.setattr(wf_checks, "_importable", lambda name: name != "fsm_admin")
    errors = wf_checks.check_workflow_dependencies()
    assert any(e.id == "crud_views_workflow.E002" for e in errors)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_expand_checks.py -k workflow -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crud_views_workflow.checks'`

- [ ] **Step 3: Create the checks module**

Create `src/crud_views_workflow/checks.py`:

```python
import importlib.util

from django.apps import apps
from django.core.checks import Error, register

TAG = "crud_views_workflow"


def _importable(name: str) -> bool:
    """True if the named top-level module can be imported."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


@register(TAG)
def check_workflow_dependencies(app_configs=None, **kwargs):
    """Error when crud_views_workflow is installed but its runtime deps are missing."""
    errors = []
    if not apps.is_installed("crud_views_workflow"):
        return errors
    if not _importable("django_fsm"):
        errors.append(
            Error(
                "django-fsm-2 is required by crud_views_workflow but is not installed.",
                hint="Install the optional extra: pip install django-crud-views[workflow]",
                id="crud_views_workflow.E001",
            )
        )
    if not _importable("fsm_admin"):
        errors.append(
            Error(
                "django-fsm-2-admin is required by crud_views_workflow but is not installed.",
                hint="Install the optional extra: pip install django-crud-views[workflow]",
                id="crud_views_workflow.E002",
            )
        )
    return errors
```

- [ ] **Step 4: Register the checks module in `ready()`**

In `src/crud_views_workflow/apps.py`, replace the `ready()` body:

```python
    def ready(self):
        import crud_views_workflow.checks  # noqa
```

(Remove the `# import crud_views.checks  # noqa` comment and the `pass`.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_expand_checks.py -k workflow -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add src/crud_views_workflow/checks.py src/crud_views_workflow/apps.py tests/test1/test_expand_checks.py
git commit -m "feat(checks): workflow dependency checks for django-fsm-2 & fsm-admin (E001/E002) (#28)"
```

---

### Task 7: Full-suite verification & lint

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `cd tests && pytest -q`
Expected: All pass (existing baseline was 530 passed, 1 skipped; expect that plus the new `test_expand_checks.py` cases).

- [ ] **Step 2: Run Django's own check command against the test project**

Run: `cd tests && python -m pytest test1/test_expand_checks.py -q` (already covered) and confirm no uncaught exceptions during check collection by running the suite; the registered checks execute when the test app boots.

- [ ] **Step 3: Lint & format**

Run: `ruff format && ruff check --fix`
Expected: clean, no changes needed beyond formatting.

- [ ] **Step 4: Commit any lint fixes (if produced)**

```bash
git add -A
git commit -m "style: ruff format for system-checks expansion (#28)" || echo "nothing to commit"
```

---

## Self-Review

**Spec coverage:**
- Gap #1 (type validation) → Task 1 (`CheckAttributeType`, E101). ✓
- Gap #2 (formsets checks) → Task 2 (`CheckMapping`, E205) + Task 3 (wiring E204/E205/E206). ✓
- Gap #3 (reactivate ContextActionCheck) → Task 4 (E203 repair + wiring). ✓
- Gap #5 (filter header template) → Task 5 (E110 on `ListView`). ✓
- Gap #6 (workflow deps) → Task 6 (E001/E002 + `ready()` registration). ✓
- Gap #4 → intentionally out of scope (already covered by E111). ✓
- ID table from spec fully realized: E101, E203, E204, E205, E206, E110, E001, E002. ✓
- Testing section (TDD per gap, dummy-context idiom, monkeypatch for deps) → each task Step 1. ✓
- Verification (pytest green, ruff clean, manual check) → Task 7. ✓

**Placeholder scan:** No TBD/TODO; every code step shows complete code; every command has expected output. ✓

**Type consistency:** `CheckAttributeType(expected_type=...)`, `CheckMapping(key_type=, value_type=)`, `ContextActionCheck(id="E203")`, `check_workflow_dependencies()` / `_importable()` names are consistent across the tasks that define and consume them. Formsets ids E204/E205/E206 distinct from cv_key's E200. ✓
