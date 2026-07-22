# Unknown `cv_*` Attribute Check (W280) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Django system check that warns when a CrudView subclass declares a `cv_*` **data attribute** that no `crud_views` class knows about (dead attribute or typo), with a near-match suggestion.

**Architecture:** A single `Check` subclass, `CheckUnknownAttributes`, is yielded once per view from `CrudView.checks()`. At check time it walks the view's MRO to build the set of legitimate `cv_*` names (from `crud_views*`-module classes) and warns about any user-declared `cv_*` data attribute not in that set, minus a per-class `cv_check_ignore_attributes` allowlist. Follows the existing W270 (`CheckBreadcrumbKeyObject`) precedent and the established `checks()` collection path.

**Tech Stack:** Python (stdlib `difflib`, `pydantic` `BaseModel` `Check` base), Django system checks framework, pytest.

**Spec:** `superpowers/specs/2026-07-22-unknown-cv-attribute-check-design.md` — Issue #86, relates to #28.

## Global Constraints

- Python 3.12 / 3.13 / 3.14; Django 4.2 / 5.2 / 6.0 (no version-specific APIs used here).
- No new runtime dependencies — `difflib` is stdlib.
- Line length 120; double quotes; `ruff format` / `ruff check` clean (pre-commit runs `ruff-format`).
- All CrudView config attributes use the `cv_` prefix.
- Check id is `viewset.W280` (the `Check` base's `get_id()` prepends `viewset.` to the `id` field, so `id = "W280"`).
- Run tests from `tests/`: `cd tests && pytest`.

---

### Task 1: `CheckUnknownAttributes` check class + `cv_check_ignore_attributes` declaration

**Files:**
- Modify: `src/crud_views/lib/check.py` (add imports + new class at end of file)
- Modify: `src/crud_views/lib/view/base.py` (declare `cv_check_ignore_attributes` on `CrudView`, near the `cv_icon_*` block around line 89)
- Test: `tests/test1/test_unknown_attribute_check.py` (new)

**Interfaces:**
- Produces: `CheckUnknownAttributes(context=<class>)` — a `Check` subclass. `context` is a CrudView subclass. `.messages()` yields zero or more `django.core.checks.Warning` with `id="viewset.W280"`, one per unknown `cv_*` data attribute.
- Produces: `CrudView.cv_check_ignore_attributes: frozenset[str] = frozenset()` — per-class allowlist; the check unions this attribute's value across the MRO.
- Consumes: existing `Check` base class from `crud_views.lib.check`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_unknown_attribute_check.py`:

```python
from functools import cached_property

from crud_views.lib.check import CheckUnknownAttributes
from crud_views.lib.view.base import CrudView


# Bare CrudView subclasses do NOT register (metaclass registers only when
# cv_viewset is in the class body), so these are safe, unregistered fixtures
# whose MRO still includes the package classes that populate the known-set.


class DeadAttrView(CrudView):
    cv_message = "Created {{ object }}"  # dead: real API is cv_message_template_code


class GoodOverrideView(CrudView):
    cv_message_template_code = "Created {{ object }}"  # legitimate override of a known attr


class MethodView(CrudView):
    def cv_helper(self):  # user cv_* method — not a data attribute, must not warn
        return 1

    @property
    def cv_computed(self):  # descriptor — must not warn
        return 2

    @cached_property
    def cv_cached(self):  # descriptor — must not warn
        return 3


class ExemptView(CrudView):
    cv_check_ignore_attributes = frozenset({"cv_custom"})
    cv_custom = 1  # custom data attr, exempted by the allowlist


class UnexemptView(CrudView):
    cv_custom = 1  # same custom data attr, but NOT exempted -> must warn


class _ExemptMixin(CrudView):
    cv_check_ignore_attributes = frozenset({"cv_from_mixin"})
    cv_from_mixin = 1


class UnionExemptView(_ExemptMixin):
    cv_check_ignore_attributes = frozenset({"cv_from_leaf"})
    cv_from_leaf = 2


def _w280(context):
    return list(CheckUnknownAttributes(context=context).messages())


def test_dead_attribute_warns_and_suggests_near_match():
    messages = _w280(DeadAttrView)
    assert len(messages) == 1
    m = messages[0]
    assert m.id == "viewset.W280"
    assert "cv_message" in m.msg
    # cv_message_template and cv_message_template_code are both valid near-matches;
    # "cv_message_template" is a substring of both, so this tolerates either suggestion.
    assert "cv_message_template" in m.msg


def test_legitimate_override_does_not_warn():
    assert _w280(GoodOverrideView) == []


def test_cv_methods_and_descriptors_do_not_warn():
    assert _w280(MethodView) == []


def test_allowlisted_custom_attribute_does_not_warn():
    assert _w280(ExemptView) == []


def test_unlisted_custom_attribute_warns():
    messages = _w280(UnexemptView)
    assert len(messages) == 1
    assert "cv_custom" in messages[0].msg


def test_allowlist_is_unioned_across_the_mro():
    # If the check used getattr (leaf shadows), cv_from_mixin would leak a warning.
    assert _w280(UnionExemptView) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_unknown_attribute_check.py -v`
Expected: FAIL — `ImportError: cannot import name 'CheckUnknownAttributes'`.

- [ ] **Step 3: Add imports to `check.py`**

At the top of `src/crud_views/lib/check.py`, change the imports to add `difflib` and Django's `Warning`:

```python
import difflib
import re
from typing import Any, Iterable, Type

from django.core.checks import Error, CheckMessage
from django.core.checks import Warning as DjangoWarning
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from pydantic import BaseModel
```

- [ ] **Step 4: Add the `CheckUnknownAttributes` class at the end of `check.py`**

Append to `src/crud_views/lib/check.py`:

```python
_PACKAGE_PREFIX = "crud_views"
_CV_PREFIX = "cv_"
_IGNORE_ATTR = "cv_check_ignore_attributes"


def _is_config_value(value: Any) -> bool:
    """True for a plain data attribute — not a method, property, classmethod, or other descriptor."""
    return not (callable(value) or hasattr(value, "__get__"))


def _own_cv_annotations(klass: type) -> set[str]:
    """cv_*-prefixed names annotated on this class only (own annotations, no inheritance).

    Handles annotation-only declarations like `cv_formsets: FormSets` (no default) that
    never appear in vars(klass). `klass.__annotations__` returns the class's own annotations
    (empty dict if none) on Python 3.10+; wrapped defensively for the PEP 649 lazy path on 3.14.
    """
    try:
        annotations = klass.__annotations__
    except Exception:
        annotations = vars(klass).get("__annotations__", {})
    return {name for name in annotations if name.startswith(_CV_PREFIX)}


def _collect_cv_names(klass: type, all_names: set[str], data_names: set[str]) -> None:
    """Add klass's own cv_* declarations — defaults (vars) and annotation-only — to the sets."""
    for name in _own_cv_annotations(klass):
        all_names.add(name)
        data_names.add(name)  # annotation-only config attrs are data, suggestible
    for name, value in vars(klass).items():
        if name.startswith(_CV_PREFIX):
            all_names.add(name)
            if _is_config_value(value):
                data_names.add(name)


def _registered_view_classes() -> list[type]:
    """All view classes across every registered ViewSet (empty before the app registry loads)."""
    from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK

    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())
    classes: list[type] = []
    for viewset in viewsets:
        classes.extend(viewset.get_all_views().values())
    return classes


_VOCAB_CACHE: dict[int, tuple[frozenset[str], frozenset[str]]] = {}


def _registry_vocabulary() -> tuple[frozenset[str], frozenset[str]]:
    """Package-wide (all cv_* names, data-attribute cv_* names) declared by any crud_views* class
    used by a registered view. Cached per registry size — the ViewSet registry only grows at
    import time and is stable when system checks run, so the count is a safe cache key."""
    classes = _registered_view_classes()
    key = len(classes)
    cached = _VOCAB_CACHE.get(key)
    if cached is not None:
        return cached
    all_names: set[str] = set()
    data_names: set[str] = set()
    seen: set[type] = set()
    for view in classes:
        for klass in view.__mro__:
            if klass in seen or not klass.__module__.startswith(_PACKAGE_PREFIX):
                continue
            seen.add(klass)
            _collect_cv_names(klass, all_names, data_names)
    result = (frozenset(all_names), frozenset(data_names))
    _VOCAB_CACHE[key] = result
    return result


class CheckUnknownAttributes(Check):
    """
    Warn about cv_* data attributes that no crud_views class declares.

    A typo or stale name (cv_message for cv_message_template_code, an attribute
    removed in a rename) is otherwise silently ignored. The known-set is derived
    from the MRO: every legitimate config attribute is declared with a default on
    a crud_views* class, so no hand-maintained registry is needed. Only non-callable,
    non-descriptor data attributes are flagged (user cv_* methods/properties are skipped).
    """

    id: str = "W280"
    msg: str = (
        "{attribute} on {context} is not a known crud_views attribute — it is silently "
        "ignored (dead attribute or typo).{suggestion}"
    )

    def _context_names(self) -> tuple[set[str], set[str]]:
        """(all cv_* names, data-attribute cv_* names) declared by crud_views* classes in this
        view's own MRO. The data subset is the suggestion pool — kept context-local so a
        'did you mean' hint stays relevant to this view type instead of pulling in unrelated
        attributes (e.g. cv_action_messages from ActionView) via the package-wide set."""
        all_names: set[str] = set()
        data_names: set[str] = set()
        for klass in self.context.__mro__:
            if klass.__module__.startswith(_PACKAGE_PREFIX):
                _collect_cv_names(klass, all_names, data_names)
        return all_names, data_names

    def _allowlist(self) -> set[str]:
        # union across the MRO so a mixin and the leaf view can each exempt their own attrs
        allow: set[str] = set()
        for klass in self.context.__mro__:
            value = vars(klass).get(_IGNORE_ATTR)
            if value:
                allow.update(value)
        return allow

    def _suspects(self) -> set[str]:
        suspects: set[str] = set()
        for klass in self.context.__mro__:
            if klass.__module__.startswith(_PACKAGE_PREFIX):
                continue  # package code defines the known-set, never suspect
            for name, value in vars(klass).items():
                if name.startswith(_CV_PREFIX) and _is_config_value(value):
                    suspects.add(name)
        return suspects

    def _suggestion(self, name: str, pool: set[str]) -> str:
        # pool is the data-attribute known-set — suggest real config attributes, never methods
        candidates = sorted(pool)
        matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)
        if not matches:
            # difflib misses when the correct name is much longer; fall back to prefix
            prefixed = sorted((k for k in candidates if k.startswith(name)), key=len)
            matches = prefixed[:1]
        return f" Did you mean {matches[0]}?" if matches else ""

    def messages(self) -> Iterable[CheckMessage]:
        reg_all, _reg_data = _registry_vocabulary()
        ctx_all, ctx_data = self._context_names()
        known_all = reg_all | ctx_all  # package-wide: is this a real crud_views attribute name?
        unknown = self._suspects() - known_all - self._allowlist()
        for name in sorted(unknown):
            # suggest only from THIS view's own data attributes, so the hint stays relevant
            suggestion = self._suggestion(name, ctx_data)
            msg = self.msg.format(attribute=name, context=self.context, suggestion=suggestion)
            yield DjangoWarning(
                msg,
                hint=(
                    f"Remove it, fix the name, or add it to {_IGNORE_ATTR} on the view "
                    f"if it is an intentional custom attribute."
                ),
                id=self.get_id(),
            )
```

- [ ] **Step 5: Declare `cv_check_ignore_attributes` on `CrudView`**

In `src/crud_views/lib/view/base.py`, after the icons block (the two `cv_icon_*` lines around line 89, immediately before the `@classmethod def checks`), add:

```python
    # W280: custom cv_* data attributes to exempt from the unknown-attribute check
    cv_check_ignore_attributes: frozenset[str] = frozenset()
```

(Declaring it on the package base puts it in the known-set, so a view that sets it does not trip the check on the attribute itself.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_unknown_attribute_check.py -v`
Expected: PASS — all 6 tests.

- [ ] **Step 7: Format and lint**

Run: `task format && task check`
Expected: no changes needed / no errors.

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/check.py src/crud_views/lib/view/base.py tests/test1/test_unknown_attribute_check.py
git commit -m "feat(checks): CheckUnknownAttributes (W280) for dead cv_* attributes (#86)"
```

---

### Task 2: Wire the check into `CrudView.checks()` + integration guards

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (`CrudView.checks()`, ends around line 122)
- Test: `tests/test1/test_unknown_attribute_check.py` (append integration tests)

**Interfaces:**
- Consumes: `CheckUnknownAttributes` from Task 1; `ViewSet.checks_all()` from `crud_views.lib.viewset`.
- Produces: `CrudView.checks()` now yields `CheckUnknownAttributes(context=cls)` in addition to its existing checks. This flows into `ViewSet.checks()` (which ends with `for view in self._views.values(): yield from view.checks()`) and `check_viewsets`.

- [ ] **Step 1: Write the failing integration tests**

Append to `tests/test1/test_unknown_attribute_check.py`:

```python
def test_checks_chain_yields_the_unknown_attribute_check():
    ids = [c.id for c in DeadAttrView.checks()]
    assert "W280" in ids


def test_checks_chain_emits_w280_for_dead_attr():
    warnings = [
        m
        for c in DeadAttrView.checks()
        for m in c.messages()
        if getattr(m, "id", None) == "viewset.W280"
    ]
    assert any("cv_message" in w.msg for w in warnings)


def test_registered_views_have_no_unknown_attribute_warnings():
    # Guards against false positives on the real, correctly-configured test-app views.
    from crud_views.lib.viewset import ViewSet

    w280 = [
        m
        for c in ViewSet.checks_all()
        for m in c.messages()
        if getattr(m, "id", None) == "viewset.W280"
    ]
    assert w280 == [], [w.msg for w in w280]


def test_checks_all_releases_registry_lock_before_yielding():
    # Regression: checks_all() must snapshot-then-release _REGISTRY_LOCK. If it holds the lock
    # across yields, calling .messages() on a yielded check (which re-acquires the lock via the
    # package-wide vocabulary) self-deadlocks. A fast, non-hanging probe: the lock must be free
    # while iterating the generator.
    from crud_views.lib.viewset import ViewSet, _REGISTRY_LOCK

    for _check in ViewSet.checks_all():
        acquired = _REGISTRY_LOCK.acquire(blocking=False)
        if acquired:
            _REGISTRY_LOCK.release()
        assert acquired, "checks_all() held _REGISTRY_LOCK across a yield — messages() would deadlock"
        break  # one iteration proves the lock is released during iteration
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_unknown_attribute_check.py -k "chain or registered" -v`
Expected: FAIL — `W280` not in the checks chain (`test_checks_chain_yields_the_unknown_attribute_check` fails; the emit test fails too).

- [ ] **Step 3: Wire the check into `CrudView.checks()`**

In `src/crud_views/lib/view/base.py`, at the end of the `CrudView.checks()` method body (after the `E251` `CheckExpression` yield, around line 122), add:

```python
        yield CheckUnknownAttributes(context=cls)
```

Add `CheckUnknownAttributes` to the existing import from `crud_views.lib.check` at `base.py:11-18`. Replace that exact block:

```python
from crud_views.lib.check import (
    Check,
    CheckAttributeReg,
    CheckAttribute,
    CheckTemplateOrCode,
    CheckTemplate,
    CheckExpression,
)
```

with:

```python
from crud_views.lib.check import (
    Check,
    CheckAttributeReg,
    CheckAttribute,
    CheckTemplateOrCode,
    CheckTemplate,
    CheckExpression,
    CheckUnknownAttributes,
)
```

- [ ] **Step 3b: Make `checks_all()` release the registry lock before yielding**

The package-wide known-set (`_registry_vocabulary`) re-acquires `_REGISTRY_LOCK` from inside `Check.messages()`. But `ViewSet.checks_all()` currently holds that non-reentrant lock across its entire generator (it yields *inside* `with _REGISTRY_LOCK`), and `check_viewsets` calls `.messages()` mid-iteration — so the second acquire self-deadlocks. Fix `checks_all()` to snapshot-then-release, matching the pattern already used at `checks.py:36`, `checks.py:104`, and `viewset/__init__.py:124`.

In `src/crud_views/lib/viewset/__init__.py`, replace:

```python
    @staticmethod
    def checks_all() -> Iterable[Check]:
        """
        Iterator over all checks of all viewsets
        """
        with _REGISTRY_LOCK:
            for cv in _REGISTRY.values():
                yield from cv.checks()
```

with:

```python
    @staticmethod
    def checks_all() -> Iterable[Check]:
        """
        Iterator over all checks of all viewsets
        """
        with _REGISTRY_LOCK:
            viewsets = list(_REGISTRY.values())
        for cv in viewsets:
            yield from cv.checks()
```

- [ ] **Step 3c: Guard `CheckAttributeReg` against a None value**

The integration test iterates every check's `.messages()` on a fixture whose `cv_key` is `None`. `CheckAttributeReg.messages()` then calls `self.reg.match(self.value)` with `self.value is None`, raising `TypeError`. Add the same `self.value is not None` guard the sibling `CheckAttributeType` already uses. In `src/crud_views/lib/check.py`, in `CheckAttributeReg.messages()`, change:

```python
        if self.exists and not self.reg.match(self.value):
```

to:

```python
        if self.exists and self.value is not None and not self.reg.match(self.value):
```

- [ ] **Step 4: Run the new integration tests**

Run: `cd tests && pytest test1/test_unknown_attribute_check.py -v`
Expected: PASS — all tests including the integration and deadlock-regression tests.

- [ ] **Step 5: Run the full test suite to confirm no regressions / no false positives**

Run: `cd tests && pytest -q`
Expected: PASS — the full suite is green (in particular `test_registered_views_have_no_unknown_attribute_warnings` proves no existing test-app view trips W280).

- [ ] **Step 6: Format and lint**

Run: `task format && task check`
Expected: no changes / no errors.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/view/base.py tests/test1/test_unknown_attribute_check.py
git commit -m "feat(checks): yield W280 from CrudView.checks(); integration guards (#86)"
```

---

### Task 3: Documentation + changelog

**Files:**
- Modify: the system-checks reference doc under `docs/` (locate with the grep in Step 1)
- Modify: `CHANGELOG.md` (or the changelog file the repo uses)

**Interfaces:** none (docs only).

- [ ] **Step 1: Locate the checks reference doc and changelog**

Run:
```bash
grep -rln "W270\|system check\|CheckTemplateOrCode\|E110" docs/ | head
ls CHANGELOG* docs/changelog* 2>/dev/null
```
Expected: identifies the page listing check IDs (where W270 is documented) and the changelog file. Read the W270 entry to match the existing format/heading style.

- [ ] **Step 2: Add the W280 documentation entry**

In the checks reference page, following the W270 entry's format, add an entry for `viewset.W280`. Content to include:

- **What it warns:** a `cv_*` data attribute on a view is not declared by any `crud_views` class — it is silently ignored (a typo or a stale name left over from a rename). Example: `cv_message = "..."` when the real API is `cv_message_template_code`.
- **How the known-set is determined:** any `cv_*` attribute declared on `crud_views` core or an extension app (workflow, polymorphic, guardian, object_detail, or a `crud_views_widget_*` community app) is recognized automatically; only `cv_*` **data attributes** are checked (methods/properties are ignored).
- **Silencing a legitimate custom attribute (recommended):** declare it in the per-class allowlist:
  ```python
  class MyView(UpdateView):
      cv_check_ignore_attributes = frozenset({"cv_my_custom_flag"})
      cv_my_custom_flag = True
  ```
  The allowlist is unioned across the class hierarchy, so a mixin and the concrete view can each contribute exemptions.
- **Global silencing (coarse):** `SILENCED_SYSTEM_CHECKS = ["viewset.W280"]` in Django settings suppresses the warning everywhere; prefer the per-class allowlist for targeted exemption.

- [ ] **Step 3: Add the changelog entry**

Add an entry under the unreleased/next section, matching the existing changelog style, e.g.:

```markdown
- Added system check `viewset.W280`: warns when a view declares a `cv_*` data attribute
  that no `crud_views` class recognizes (dead attribute or typo), with a near-match
  suggestion. Exempt intentional custom attributes via `cv_check_ignore_attributes`.
  Relates to #28. (#86)
```

- [ ] **Step 4: Build docs to confirm no syntax errors (if mkdocs is set up)**

Run: `task docs` briefly (or `mkdocs build` if available) to confirm the page renders; stop the server.
Expected: docs build without errors. (Skip if the docs toolchain is unavailable in the environment.)

- [ ] **Step 5: Commit**

```bash
git add docs CHANGELOG.md
git commit -m "docs(checks): document W280 unknown cv_* attribute warning (#86)"
```

---

## Notes for the implementer

- **Do not** re-verify codegraph/grep facts already baked into this plan; the exact line regions were confirmed against the current tree.
- The `Check` base is a `pydantic` `BaseModel`; `context: Type | object` accepts a class. `CheckUnknownAttributes` overrides `messages()` and formats inline, so it does not rely on `get_message()`.
- Bare `CrudView` subclasses used as test fixtures never register with a ViewSet (the metaclass registers only when `cv_viewset` is present in the class body), so they will not pollute `ViewSet.checks_all()` or other tests.
- If `task format`/`task check` are unavailable, use `ruff format src tests && ruff check --fix src tests`.
