# Context Button Create Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a custom `ContextButton` whose `key != key_target` and targets a child viewset's `create` view resolve create-access correctly on Guardian list pages, identical to the built-in `"create"` button.

**Architecture:** Single-method change in `GuardianQuerysetMixin.cv_get_context`
(`src/crud_views_guardian/lib/mixins.py`). Before looking up the target view by
`key`, resolve the registered button's `key_target` and look up by that instead. The
existing `cv_permission == "add"` guard, parent-object resolution, and
`cv_access` / `cv_action_enabled` overwrite are unchanged.

**Tech Stack:** Python, Django, django-guardian, pytest. Tests run from `tests/`.

## Global Constraints

- Line length: 120 characters (ruff).
- Quote style: double quotes.
- `cv_` prefix on all `CrudView` attributes; view keys: `list`/`detail`/`create`/`update`/`delete`.
- Tests live in `tests/test1/`; run with `cd tests && pytest`.
- No change to core `crud_views`; no change to the `cv_has_access` contract.
- Spec: `superpowers/specs/2026-06-18-context-button-create-access-design.md`.
- Deferred Approach B (do NOT implement here): `superpowers/instructions/0004-context-button-access-create-TODO.md`.

---

## File Structure

- `tests/test1/app/views.py` — add a `create_button` `ContextButton` to the existing
  child Guardian viewset `cv_guardian_book` so the new behavior can be exercised.
- `tests/test1/test_guardian.py` — add a new test section asserting `"create_button"`
  and `"create"` produce identical `cv_access` / `cv_action_enabled`, plus
  unresolvable-parent and top-level-unchanged cases. Reuses the existing
  `_make_book_list_view` helper (defined at `test1/test_guardian.py:370`).
- `src/crud_views_guardian/lib/mixins.py` — the one-method fix in
  `GuardianQuerysetMixin.cv_get_context` (lines 132-148).

This is a single, coherent fix with one test cycle → one task.

---

### Task 1: Resolve `key_target` for create-button access in the Guardian list mixin

**Files:**
- Modify: `tests/test1/app/views.py:587-594` (add `context_buttons` to `cv_guardian_book`)
- Modify: `src/crud_views_guardian/lib/mixins.py:132-148`
- Test: `tests/test1/test_guardian.py` (append a new section after line 438)

**Interfaces:**
- Consumes (existing, do not redefine):
  - `self.cv_get_context_button(key) -> ContextButton | None` (`base.py:293`)
  - `ContextButton.key_target: str | None` (`buttons.py:14`)
  - `self.cv_viewset.is_view_registered(key) -> bool`, `self.cv_viewset.get_view_class(key)`
  - `target_cls.cv_create_has_access(user, rendering_view, parent_obj) -> bool` (`views.py:125`)
  - `target_cls.cv_action_enabled(user, obj) -> bool`
  - `self.cv_get_parent_object()` (raises `Http404`/`KeyError` when unresolvable)
  - Test helper `_make_book_list_view(user_guardian, publisher_a)` (`test_guardian.py:370`)
  - Test helper `user_guardian_object_perm(user, viewset, perm, obj)` (imported at `test_guardian.py:3`)
  - Test helper `user_viewset_permission(user, viewset, perm)` (`tests/lib/helper/user.py`)
- Produces: no new public API. Behavior change only: `cv_get_context(key=<button
  whose key_target targets child create>, obj=None)` now returns the same
  `cv_access` / `cv_action_enabled` as `cv_get_context(key="create", obj=None)`.

---

- [ ] **Step 1: Add the `create_button` context button to the child Guardian viewset**

In `tests/test1/app/views.py`, ensure `ContextButton` and `context_buttons_default`
are imported (the file already imports from `crud_views.lib.viewset`; add the button
import). Near the top imports add:

```python
from crud_views.lib.view import ContextButton
from crud_views.lib.viewset import context_buttons_default
```

Then change the `cv_guardian_book` definition (currently `views.py:587-594`) to:

```python
cv_guardian_book = GuardianViewSet(
    model=Book,
    name="guardian_book",
    parent=ParentViewSet(name="guardian_publisher", attribute="publisher"),
    icon_header="fa-regular fa-address-book",
    cv_guardian_parent_permission="view",
    cv_guardian_parent_create_permission="change",
    context_buttons=context_buttons_default() + [
        ContextButton(key="create_button", key_target="create"),  # key != key_target
    ],
)
```

> Note: `ViewSet`/`ParentViewSet` are already imported (`views.py:40`). If
> `context_buttons_default` is already importable via an existing `crud_views.lib.viewset`
> import line, extend that line instead of adding a new one.

- [ ] **Step 2: Write the failing tests**

Append to `tests/test1/test_guardian.py` (after line 438):

```python
# ── ContextButton key != key_target targeting child create ────────────────────


@pytest.mark.django_db
def test_create_button_matches_create_with_parent_perm(user_guardian, cv_guardian_publisher, publisher_a):
    """create_button (key != key_target) matches built-in create when parent perm is granted."""
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "change", publisher_a)
    view = _make_book_list_view(user_guardian, publisher_a)
    create = view.cv_get_context(key="create", obj=None, user=user_guardian)
    button = view.cv_get_context(key="create_button", obj=None, user=user_guardian)
    assert create["cv_access"] is True
    assert button["cv_access"] == create["cv_access"]
    assert button["cv_action_enabled"] == create["cv_action_enabled"]


@pytest.mark.django_db
def test_create_button_matches_create_without_parent_perm(user_guardian, publisher_a):
    """create_button is hidden, exactly like built-in create, without parent perm."""
    view = _make_book_list_view(user_guardian, publisher_a)
    create = view.cv_get_context(key="create", obj=None, user=user_guardian)
    button = view.cv_get_context(key="create_button", obj=None, user=user_guardian)
    assert create["cv_access"] is False
    assert button["cv_access"] == create["cv_access"]
    assert button["cv_action_enabled"] == create["cv_action_enabled"]


@pytest.mark.django_db
def test_create_button_unresolvable_parent_denied(user_guardian):
    """Unresolvable parent → create_button denied, no exception raised."""
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

    ctx = view.cv_get_context(key="create_button", obj=None, user=user_guardian)
    assert ctx["cv_access"] is False


@pytest.mark.django_db
def test_top_level_create_unchanged_by_key_target_fix(user_guardian, cv_guardian_author):
    """Top-level (no-parent) create access is unaffected — the override's has_parent guard skips it."""
    from unittest.mock import MagicMock
    from django.contrib.auth.models import User
    from django.test import RequestFactory
    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import GuardianAuthorListView, cv_guardian_author as author_vs

    rf = RequestFactory()
    request = rf.get("/guardian_author/")
    request.user = user_guardian
    resolver_match = MagicMock()
    resolver_match.url_name = author_vs.get_router_name("list")
    request.resolver_match = resolver_match

    view = GuardianAuthorListView()
    view.request = request
    view.args = []
    view.kwargs = {}

    # without model-level add perm → denied
    denied = view.cv_get_context(key="create", obj=None, user=user_guardian)
    assert denied["cv_access"] is False

    # with model-level add perm → granted (refetch user to bust the perm cache)
    user_viewset_permission(user_guardian, cv_guardian_author, "add")
    granted_user = User.objects.get(pk=user_guardian.pk)
    request.user = granted_user
    granted = view.cv_get_context(key="create", obj=None, user=granted_user)
    assert granted["cv_access"] is True
```

- [ ] **Step 3: Run the new tests and confirm the create-button tests FAIL**

Run: `cd tests && pytest test1/test_guardian.py -k "create_button or top_level_create_unchanged" -v`

Expected: `test_create_button_matches_create_with_parent_perm` FAILS
(`button["cv_access"]` is `False` while `create["cv_access"]` is `True`).
`test_create_button_matches_create_without_parent_perm`,
`test_create_button_unresolvable_parent_denied`, and
`test_top_level_create_unchanged_by_key_target_fix` PASS (they already hold pre-fix —
they lock in non-regression).

- [ ] **Step 4: Apply the fix in the Guardian list mixin**

In `src/crud_views_guardian/lib/mixins.py`, inside `GuardianQuerysetMixin.cv_get_context`,
replace the lookup block (currently lines 132-136):

```python
        if obj is None and key is not None and self.cv_viewset.has_parent:
            if self.cv_viewset.is_view_registered(key):
                target_cls = self.cv_viewset.get_view_class(key)
            else:
                target_cls = None
```

with:

```python
        if obj is None and key is not None and self.cv_viewset.has_parent:
            # A custom ContextButton may target the create view via key_target while
            # using a different key (e.g. a second, differently-styled create button).
            # Resolve key_target so the create-access re-derivation finds the view.
            context_button = self.cv_get_context_button(key)
            target_key = context_button.key_target if context_button and context_button.key_target else key
            if self.cv_viewset.is_view_registered(target_key):
                target_cls = self.cv_viewset.get_view_class(target_key)
            else:
                target_cls = None
```

Leave the rest of the method (the `cv_permission == "add"` guard, parent resolution,
and the `ctx["cv_access"]` / `ctx["cv_action_enabled"]` overwrite) unchanged.

- [ ] **Step 5: Run the new tests and confirm they all PASS**

Run: `cd tests && pytest test1/test_guardian.py -k "create_button or top_level_create_unchanged" -v`

Expected: all four tests PASS.

- [ ] **Step 6: Run the full Guardian suite + lint to confirm no regression**

Run: `cd tests && pytest test1/test_guardian.py -q`
Expected: all pass (the pre-existing `cv_get_context` tests at lines 391-438 included).

Run: `task check && task format` (from repo root)
Expected: ruff check passes; format leaves the changed files clean.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views_guardian/lib/mixins.py tests/test1/app/views.py tests/test1/test_guardian.py
git commit -m "fix(guardian): resolve key_target for context-button create access

A custom ContextButton whose key != key_target and targets a child
viewset's create view was always rendered as no-access on list pages,
because the Guardian list mixin looked the target view up by the literal
key. Resolve the button's key_target before the lookup so create-access
is re-derived for any create button, not just the built-in 'create'.

Claude-Session: https://claude.ai/code/session_01XAzMTw15SVe5rfyrRyNC9i"
```

---

## Self-Review

**Spec coverage:**
- "create_button == create with parent perm (access + action_enabled)" → Step 2 test 1. ✓
- "create_button == create without parent perm" → Step 2 test 2. ✓
- "unresolvable parent → denied, no exception" → Step 2 test 3. ✓
- "top-level create access unchanged" → Step 2 test 4. ✓
- "resolve key_target before lookup" fix → Step 4. ✓
- "no core crud_views change; cv_has_access contract unchanged" → only mixin + tests touched. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases" — every step has concrete code and exact commands. ✓

**Type consistency:** `cv_get_context_button` returns `ContextButton | None`; `key_target` is `str | None`; `is_view_registered`/`get_view_class` keyed on the resolved `target_key`; test helpers `_make_book_list_view`, `user_guardian_object_perm`, `user_viewset_permission` match existing signatures in `test_guardian.py`. ✓
