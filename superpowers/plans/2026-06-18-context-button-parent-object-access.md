# Context Button Parent-Object Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a `ParentContextButton` that targets an object-permission-gated parent view (e.g. parent `detail`) reflect the user's access to the **parent object** on object-less child pages, instead of being wrongly hidden.

**Architecture:** Single-method change in `ParentContextButton.get_context()`
(`src/crud_views/lib/view/buttons.py`). The parent PK is already read from the view's
kwargs to build the URL; load the parent **instance** from the same source via the
existing core helper `cv_get_parent_object()` and check `cv_has_access` /
`cv_action_enabled` against it. Purely core `crud_views` — no Guardian-side change.

**Tech Stack:** Python, Django, django-guardian, pytest. Tests run from `tests/`.

## Global Constraints

- Line length: 120 characters (ruff). Quote style: double quotes.
- No change to core `crud_views` access **contract** (`cv_has_access` signature
  unchanged); the only behavior change is *which object* `ParentContextButton` passes.
- `SiblingContextButton` behavior is **unchanged** — collection-only, no governing
  object; passing `None` stays correct. Only its docstring is clarified.
- Approach B (unified `cv_button_has_access` hook) is **not** implemented here.
- Tests live in `tests/test1/`; run with `cd tests && pytest`.
- Spec: `superpowers/specs/2026-06-18-context-button-parent-object-access-design.md`.

---

## File Structure

- `src/crud_views/lib/view/buttons.py` — the fix in `ParentContextButton.get_context()`
  (add `Http404` import; resolve parent object; check access against it) **and** a
  one-line docstring clarification on `SiblingContextButton`.
- `tests/test1/app/views.py` — add a `ParentContextButton(key="publisher_detail",
  key_target="detail")` to the existing child Guardian viewset `cv_guardian_book`.
- `tests/test1/test_guardian.py` — new test section asserting the parent-detail button
  reflects parent-object `view` permission; default `parent`→list button regression;
  unresolvable-parent case. Reuses the existing `_make_book_list_view` helper
  (`test_guardian.py:370`).
- `superpowers/instructions/0004-context-button-access-create-TODO.md` — add a
  correction note: `SiblingContextButton` is not a "resolve the shared parent" case.

One coherent fix with one test cycle → one task (doc edits folded in).

---

### Task 1: Check `ParentContextButton` access against the parent object

**Files:**
- Modify: `src/crud_views/lib/view/buttons.py` (imports; `ParentContextButton.get_context`
  lines 106-113; `SiblingContextButton` docstring lines 161-164)
- Modify: `tests/test1/app/views.py` (import `ParentContextButton`; extend
  `cv_guardian_book.context_buttons`, lines 41 and 595-598)
- Modify: `superpowers/instructions/0004-context-button-access-create-TODO.md` (after line 58)
- Test: `tests/test1/test_guardian.py` (append a new section after line 438)

**Interfaces:**
- Consumes (existing, do not redefine):
  - `context.view.cv_get_parent_object() -> Model` (`base.py:411`) — raises
    `Http404` (bad PK) or `KeyError` (missing kwarg).
  - `cls.cv_has_access(user, obj) -> bool`, `cls.cv_action_enabled(user, obj) -> bool`.
  - `from crud_views.lib.view import ContextButton, ParentContextButton`.
  - `context_buttons_default()` (`crud_views.lib.viewset`).
  - Test helpers: `_make_book_list_view(user_guardian, publisher_a)`
    (`test_guardian.py:370`), `user_guardian_object_perm(user, viewset, perm, obj)`
    (imported at `test_guardian.py:3`).
- Produces: no new public API. Behavior change only — `ParentContextButton`
  `cv_access` / `cv_action_enabled` are now evaluated against the resolved parent
  object instead of `context.object`.

---

- [ ] **Step 1: Add the `Http404` import to `buttons.py`**

In `src/crud_views/lib/view/buttons.py`, the current import block (lines 1-5) is:

```python
from django.urls import reverse
from pydantic import BaseModel, Field

from .context import ViewContext
from ..settings import crud_views_settings
```

Add the `Http404` import:

```python
from django.http import Http404
from django.urls import reverse
from pydantic import BaseModel, Field

from .context import ViewContext
from ..settings import crud_views_settings
```

- [ ] **Step 2: Add the test fixture — a parent-detail button on the child viewset**

In `tests/test1/app/views.py`, extend the button import (line 41):

```python
from crud_views.lib.view import ContextButton, ParentContextButton
```

Then extend `cv_guardian_book.context_buttons` (lines 595-598) to:

```python
    context_buttons=context_buttons_default()
    + [
        ContextButton(key="create_button", key_target="create"),  # key != key_target
        ParentContextButton(key="publisher_detail", key_target="detail"),  # → object-gated parent detail
    ],
```

- [ ] **Step 3: Write the failing tests**

Append to `tests/test1/test_guardian.py` (after line 438):

```python
# ── ParentContextButton targeting an object-gated parent view ─────────────────


@pytest.mark.django_db
def test_parent_detail_button_visible_with_parent_view_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """A ParentContextButton → parent detail is visible when the user can view the parent object."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    view = _make_book_list_view(user_guardian, publisher_a)
    ctx = view.cv_get_context(key="publisher_detail", obj=None, user=user_guardian)
    assert ctx["cv_access"] is True


@pytest.mark.django_db
def test_parent_detail_button_hidden_without_parent_view_perm(user_guardian, publisher_a):
    """A ParentContextButton → parent detail is hidden when the user cannot view the parent object."""
    view = _make_book_list_view(user_guardian, publisher_a)
    ctx = view.cv_get_context(key="publisher_detail", obj=None, user=user_guardian)
    assert ctx["cv_access"] is False


@pytest.mark.django_db
def test_default_parent_button_visible_regardless_of_object_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """Regression: the default parent→list button stays visible with and without parent view perm."""
    view = _make_book_list_view(user_guardian, publisher_a)
    # without perm — parent list access is unconditional
    without = view.cv_get_context(key="parent", obj=None, user=user_guardian)
    assert without["cv_access"] is True
    # with perm — still visible
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "view", publisher_a)
    with_perm = view.cv_get_context(key="parent", obj=None, user=user_guardian)
    assert with_perm["cv_access"] is True


@pytest.mark.django_db
def test_parent_detail_button_unresolvable_parent_hidden(user_guardian, publisher_a):
    """Unresolvable parent PK → parent-detail button hidden, no exception raised."""
    from unittest.mock import MagicMock
    from django.test import RequestFactory
    from tests.test1.app.views import GuardianBookListView, cv_guardian_book

    rf = RequestFactory()
    request = rf.get("/guardian_publisher/999999/guardian_book/")
    request.user = user_guardian
    resolver_match = MagicMock()
    resolver_match.url_name = cv_guardian_book.get_router_name("list")
    request.resolver_match = resolver_match

    view = GuardianBookListView()
    view.request = request
    view.args = []
    view.kwargs = {"guardian_publisher_pk": "999999"}  # no such publisher

    ctx = view.cv_get_context(key="publisher_detail", obj=None, user=user_guardian)
    assert ctx["cv_access"] is False
```

- [ ] **Step 4: Run the new tests and confirm the access tests FAIL**

Run: `cd tests && pytest test1/test_guardian.py -k "parent_detail or default_parent_button" -v`

Expected: `test_parent_detail_button_visible_with_parent_view_perm` FAILS
(`cv_access` is `False` — access is checked against `context.object` = `None`, so the
object-gated parent detail denies). `test_parent_detail_button_hidden_without_parent_view_perm`,
`test_default_parent_button_visible_regardless_of_object_perm`, and
`test_parent_detail_button_unresolvable_parent_hidden` PASS (they already hold pre-fix
— they lock in non-regression).

- [ ] **Step 5: Apply the fix in `ParentContextButton.get_context()`**

In `src/crud_views/lib/view/buttons.py`, replace the access block (lines 106-113):

```python
        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(context.view.request.user, context.object)

        # check permission
        if cls.cv_has_access(context.view.request.user, context.object):
            dict_kwargs.update(
                cv_access=True,
            )
```

with:

```python
        # the button links UP to the parent, so access is governed by the PARENT
        # object — not context.object (the child instance, or None on a list page).
        parent_obj = None
        if hasattr(context.view, "cv_get_parent_object"):
            try:
                parent_obj = context.view.cv_get_parent_object()
            except (Http404, KeyError):
                parent_obj = None

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(context.view.request.user, parent_obj)

        # check permission against the parent object
        if cls.cv_has_access(context.view.request.user, parent_obj):
            dict_kwargs.update(
                cv_access=True,
            )
```

- [ ] **Step 6: Run the new tests and confirm they all PASS**

Run: `cd tests && pytest test1/test_guardian.py -k "parent_detail or default_parent_button" -v`
Expected: all four tests PASS.

- [ ] **Step 7: Clarify the `SiblingContextButton` docstring**

In `src/crud_views/lib/view/buttons.py`, replace the `SiblingContextButton` docstring
(lines 161-164):

```python
    """
    A context button on a child view that links to a sibling collection — another child of
    the same parent — reusing the parent PK already present in the current URL.
    """
```

with:

```python
    """
    A context button on a child view that links to a sibling collection — another child of
    the same parent — reusing the parent PK already present in the current URL.

    Collection-only: a sibling button has no specific sibling object in scope, so object-gated
    sibling views (detail/update/delete) are unsupported — access is checked with obj=None,
    which is correct only for collection targets (list/card, whose access is unconditional).
    """
```

- [ ] **Step 8: Add the correction note to the Approach B TODO**

In `superpowers/instructions/0004-context-button-access-create-TODO.md`, after the
"Parent-resolution helper" bullet (ends at line 58), insert a new bullet under
"## Why this is bigger than it looks (the wrinkles)":

```markdown
- **`SiblingContextButton` is NOT a "resolve the shared parent" case (correction
  2026-06-18).** It navigates to a sibling *collection* and has no specific sibling
  object in scope, so it can only meaningfully target collection views (`list`/`card`),
  whose access is unconditional. The unified `cv_button_has_access` hook must do **no**
  object resolution for sibling buttons — passing `None` is correct. Only create
  (→ parent) and parent-detail (→ parent) need a resolved object.
```

- [ ] **Step 9: Run the full Guardian suite + lint to confirm no regression**

Run: `cd tests && pytest test1/test_guardian.py -q`
Expected: all pass (the pre-existing `cv_get_context` tests included).

Run: `cd tests && pytest -q`
Expected: full suite green (the change touches a core button type rendered across
many tests).

Run: `ruff check src/crud_views/lib/view/buttons.py tests/test1/app/views.py tests/test1/test_guardian.py`
then `ruff format src/crud_views/lib/view/buttons.py tests/test1/app/views.py tests/test1/test_guardian.py`
Expected: checks pass; format leaves the changed files clean.

- [ ] **Step 10: Commit**

```bash
git add src/crud_views/lib/view/buttons.py tests/test1/app/views.py tests/test1/test_guardian.py \
  superpowers/instructions/0004-context-button-access-create-TODO.md
git commit -m "fix(buttons): check ParentContextButton access against the parent object

A ParentContextButton targeting an object-permission-gated parent view
(e.g. parent detail) was hidden on object-less child pages because access
was checked against context.object (the child, or None on a list) instead
of the parent object the button links to. Resolve the parent instance via
cv_get_parent_object() and check against it. SiblingContextButton is
collection-only and unchanged (docstring clarified).

Claude-Session: https://claude.ai/code/session_01XAzMTw15SVe5rfyrRyNC9i"
```

---

## Self-Review

**Spec coverage:**
- "ParentContextButton checks access against the parent object" → Steps 1, 5. ✓
- "with parent view perm → visible; without → hidden" → Step 3 tests 1-2. ✓
- "default parent→list button stays visible in both cases" → Step 3 test 3. ✓
- "unresolvable parent → hidden, no exception" → Step 3 test 4. ✓
- "no Guardian-side change" → only `buttons.py` + tests + docs touched. ✓
- "SiblingContextButton unchanged, docstring clarified" → Step 7. ✓
- "TODO correction note" → Step 8. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases" — every step has concrete code and exact commands. ✓

**Type consistency:** `cv_get_parent_object()` returns a `Model` and raises
`Http404`/`KeyError`; `cv_has_access(user, obj)` / `cv_action_enabled(user, obj)`
signatures unchanged; `ParentContextButton` / `ContextButton` imported from
`crud_views.lib.view`; test helpers `_make_book_list_view`, `user_guardian_object_perm`
match existing signatures in `test_guardian.py`. ✓
