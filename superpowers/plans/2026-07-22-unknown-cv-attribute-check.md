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

    def _known(self) -> set[str]:
        known: set[str] = set()
        for klass in self.context.__mro__:
            if klass.__module__.startswith(_PACKAGE_PREFIX):
                known.update(name for name in vars(klass) if name.startswith(_CV_PREFIX))
        return known

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
                if not name.startswith(_CV_PREFIX):
                    continue
                if callable(value) or hasattr(value, "__get__"):
                    continue  # method / property / descriptor — not a config value
                suspects.add(name)
        return suspects

    def _suggestion(self, name: str, known: set[str]) -> str:
        pool = sorted(known)
        matches = difflib.get_close_matches(name, pool, n=1, cutoff=0.6)
        if not matches:
            # difflib misses when the correct name is much longer; fall back to prefix
            prefixed = sorted((k for k in pool if k.startswith(name)), key=len)
            matches = prefixed[:1]
        return f" Did you mean {matches[0]}?" if matches else ""

    def messages(self) -> Iterable[CheckMessage]:
        known = self._known()
        unknown = self._suspects() - known - self._allowlist()
        for name in sorted(unknown):
            msg = self.msg.format(attribute=name, context=self.context, suggestion=self._suggestion(name, known))
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

- [ ] **Step 4: Run the new integration tests**

Run: `cd tests && pytest test1/test_unknown_attribute_check.py -v`
Expected: PASS — all tests including the three integration tests.

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
