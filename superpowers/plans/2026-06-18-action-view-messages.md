# ActionView Result Evaluation & Messages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `ActionView` emit success/error messages out of the box (disableable), fix the broken message renderer, and make the ordered up/down views' configured messages actually fire.

**Architecture:** Move a corrected, success/error-aware `cv_get_message()` onto base `CrudView`, add an error-template attribute pair, have `ActionView.post()` emit `messages.success`/`messages.error` based on the action result via new `cv_action_success`/`cv_action_error` methods (which still call the existing no-op hooks), and remove the redundant `MessageMixin.action()` wrapper. Form views keep emitting via `MessageMixin.cv_form_valid_hook`.

**Tech Stack:** Python, Django (`django.contrib.messages`), pytest / pytest-django.

## Global Constraints

- Line length: 120 characters; double quotes; format with `ruff format`, lint with `ruff check --fix` (project uses `task format` / `task check`).
- Run tests from the `tests/` directory: `cd tests && pytest`.
- All `CrudView` class attributes use the `cv_` prefix.
- Spec: `superpowers/specs/2026-06-18-action-view-messages-design.md`.
- Commit message footer (every commit):
  `Claude-Session: https://claude.ai/code/session_01KqgEeiK2iZ7nGDw92LvqnF`
- Work happens on branch `feature/action-view-messages` (already created).

## File Structure

- `src/crud_views/lib/view/base.py` — add error-template attrs; add corrected `cv_get_message()`.
- `src/crud_views/lib/views/mixins.py` — remove `MessageMixin.cv_get_message()` and `MessageMixin.action()`; keep `cv_form_valid_hook`.
- `src/crud_views/lib/views/action.py` — emit messages in `post()` via `cv_action_success`/`cv_action_error`; add `cv_action_messages`.
- `tests/test1/app/views.py` — fix `AuthorContactView` message template; add `ActionView` test fixtures.
- `tests/test1/test_action_messages.py` — new test module for ActionView messaging.
- `tests/test1/test_action_ordered.py` — add message assertions for up/down.
- `docs/reference/ordered_view.md`, new `docs/reference/action_view.md`, `docs/reference/.pages`, `docs/reference/index.md`, `CHANGELOG.md` — docs.
- `skills/django-crud-views/references/api-reference.md`, `skills/django-crud-views/SKILL.md` — skill corrections.

---

### Task 1: Corrected `cv_get_message()` on base + error-template attrs + `MessageMixin` cleanup

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (attrs near lines 62-63; new method)
- Modify: `src/crud_views/lib/views/mixins.py` (remove `cv_get_message` + `action` from `MessageMixin`)
- Modify: `tests/test1/app/views.py:157` (`AuthorContactView.cv_message_template_code`)
- Test: `tests/test1/test_action_messages.py` (new)

**Interfaces:**
- Produces: `CrudView.cv_get_message(self, *, error: bool = False) -> str | None` — renders the
  error template pair when `error=True`, else the success pair; returns `None` when the chosen
  template pair is unset (never raises).
- Produces (attrs): `cv_message_template_error: str | None`, `cv_message_template_error_code: str | None`.
- Consumes: existing `self.render_snippet(self.cv_get_meta(), template, template_code)` and the
  existing `cv_message_template` / `cv_message_template_code` attrs.

- [ ] **Step 1: Fix the existing form-message fixture to use Django template syntax**

In `tests/test1/app/views.py`, change `AuthorContactView` (currently line 157):

```python
    cv_message_template_code = "Contacted author »{{ object }}«"
```

(Was `"Contacted author »{object}«"` — `{object}` is literal text in a Django template and never substitutes.)

- [ ] **Step 2: Write the failing regression test for form-view messaging**

Create `tests/test1/test_action_messages.py`:

```python
import pytest
from django.contrib.messages import get_messages
from django.test.client import Client

from tests.test1.app.models import Author


def _messages(response) -> list[str]:
    return [m.message for m in get_messages(response.wsgi_request)]


@pytest.mark.django_db
def test_custom_form_view_emits_rendered_message(client_user_author_change: Client, cv_author):
    """MessageMixin form views still emit a message after the renderer moves to base."""
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_change.post(
        f"/author/{a.pk}/contact/", {"subject": "hi", "body": "there"}
    )
    assert response.status_code == 302
    assert f"Contacted author »{a}«" in _messages(response)
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd tests && pytest test1/test_action_messages.py::test_custom_form_view_emits_rendered_message -v`
Expected: FAIL — message reads `Contacted author »{object}«` (literal) instead of the substituted name, OR an import/render error. (Confirms the test exercises the real path before the refactor.)

- [ ] **Step 4: Add error-template attributes to base `CrudView`**

In `src/crud_views/lib/view/base.py`, replace the two message-template attribute lines (currently 62-63):

```python
    cv_message_template: str | None = None  # success message template snippet
    cv_message_template_code: str | None = None  # success message template code
    cv_message_template_error: str | None = None  # error message template snippet
    cv_message_template_error_code: str | None = None  # error message template code
```

- [ ] **Step 5: Add the corrected `cv_get_message()` to base `CrudView`**

In `src/crud_views/lib/view/base.py`, add this method to the `CrudView` class (place it near
`render_snippet` / the other snippet helpers):

```python
    def cv_get_message(self, *, error: bool = False) -> str | None:
        """
        Render the success (default) or error message snippet.
        Returns None when the relevant template pair is not configured.
        """
        if error:
            template = self.cv_message_template_error
            template_code = self.cv_message_template_error_code
        else:
            template = self.cv_message_template
            template_code = self.cv_message_template_code
        if not template and not template_code:
            return None
        return self.render_snippet(self.cv_get_meta(), template, template_code)
```

- [ ] **Step 6: Remove the broken `cv_get_message` and the `action()` wrapper from `MessageMixin`**

In `src/crud_views/lib/views/mixins.py`, delete the `cv_get_message` method (the one whose
`attribute` argument was ignored) and the entire `action()` method from `MessageMixin`. Keep
`checks()` and `cv_form_valid_hook`. The class should become:

```python
class MessageMixin:
    """
    Add messages for a view.
    Note: the view must configure the message template or code:
            - cv_message_template
            - cv_message_template_code
    """

    @classmethod
    def checks(cls) -> Iterable[Check]:
        """
        Iterator of checks for the view
        """
        yield from super().checks()  # noqa
        yield CheckTemplateOrCode(context=cls, attribute="cv_message_template")

    def cv_form_valid_hook(self, context: dict):
        super().cv_form_valid_hook(context)  # noqa
        message = self.cv_get_message()
        if message:
            messages.success(self.request, message)
```

Leave the `from django.contrib import messages` import in place (still used here).

- [ ] **Step 7: Run the regression test to verify it passes**

Run: `cd tests && pytest test1/test_action_messages.py::test_custom_form_view_emits_rendered_message -v`
Expected: PASS — message is `Contacted author »First Author«`.

- [ ] **Step 8: Run the full suite to confirm no regressions**

Run: `cd tests && pytest -q`
Expected: all pass (no test relied on the removed `MessageMixin.action()`).

- [ ] **Step 9: Format, lint, commit**

```bash
cd /home/alex/projects/alex/django-crud-views
task format && task check
git add src/crud_views/lib/view/base.py src/crud_views/lib/views/mixins.py tests/test1/app/views.py tests/test1/test_action_messages.py
git commit -m "refactor(messages): move success/error-aware cv_get_message to base CrudView

Adds cv_message_template_error/_code, makes cv_get_message return None when
unconfigured (no longer raises), and removes the broken MessageMixin.action()
wrapper and its attribute-ignoring cv_get_message.

Claude-Session: https://claude.ai/code/session_01KqgEeiK2iZ7nGDw92LvqnF"
```

---

### Task 2: `ActionView` emits success/error messages (with hooks + opt-outs)

**Files:**
- Modify: `src/crud_views/lib/views/action.py`
- Modify: `tests/test1/app/views.py` (add fixture action views; extend the `crud_views.lib.views` import)
- Test: `tests/test1/test_action_messages.py` (extend)

**Interfaces:**
- Consumes: `CrudView.cv_get_message(*, error=False)` from Task 1.
- Produces: `ActionView.cv_action_messages: bool = True`; `ActionView.cv_action_success(context)`
  and `ActionView.cv_action_error(context)` which emit a message (when enabled and configured)
  then call `cv_action_success_hook` / `cv_action_error_hook` respectively.

- [ ] **Step 1: Add fixture action views to the test app**

In `tests/test1/app/views.py`, add `ActionViewPermissionRequired` to the existing import from
`crud_views.lib.views` (the block that already imports `OrderedUpViewPermissionRequired`,
`OrderedUpDownPermissionRequired`). Then add these classes after `AuthorDownView` (after line 133):

```python
class AuthorPingView(ActionViewPermissionRequired):
    cv_key = "ping"
    cv_path = "ping"
    cv_viewset = cv_author
    cv_backend_only = True
    cv_message_template_code = "Pinged »{{ object }}«"
    cv_message_template_error_code = "Ping failed for »{{ object }}«"

    def action(self, context):
        # result controllable from the request for testing both branches
        return self.request.GET.get("fail") != "1"


class AuthorSilentPingView(ActionViewPermissionRequired):
    cv_key = "ping_silent"
    cv_path = "ping-silent"
    cv_viewset = cv_author
    cv_backend_only = True

    def action(self, context):
        return True


class AuthorMutedPingView(ActionViewPermissionRequired):
    cv_key = "ping_muted"
    cv_path = "ping-muted"
    cv_viewset = cv_author
    cv_backend_only = True
    cv_action_messages = False
    cv_message_template_code = "Should not appear"

    def action(self, context):
        return True


class AuthorHookPingView(ActionViewPermissionRequired):
    cv_key = "ping_hook"
    cv_path = "ping-hook"
    cv_viewset = cv_author
    cv_backend_only = True

    def action(self, context):
        return True

    def cv_action_success_hook(self, context):
        self.object.pseudonym = "hooked"
        self.object.save()
```

(`cv_backend_only = True` mirrors the ordered views so no per-row button/label config is needed.)

- [ ] **Step 2: Write the failing tests for ActionView messaging**

Append to `tests/test1/test_action_messages.py`:

```python
@pytest.mark.django_db
def test_action_view_emits_success_message(client_user_author_change: Client, cv_author):
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_change.post(f"/author/{a.pk}/ping/")
    assert response.status_code == 302
    assert f"Pinged »{a}«" in _messages(response)


@pytest.mark.django_db
def test_action_view_emits_error_message(client_user_author_change: Client, cv_author):
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_change.post(f"/author/{a.pk}/ping/?fail=1")
    assert response.status_code == 302
    assert f"Ping failed for »{a}«" in _messages(response)


@pytest.mark.django_db
def test_action_view_no_template_emits_nothing(client_user_author_change: Client, cv_author):
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_change.post(f"/author/{a.pk}/ping-silent/")
    assert response.status_code == 302
    assert _messages(response) == []


@pytest.mark.django_db
def test_action_view_messages_disabled(client_user_author_change: Client, cv_author):
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_change.post(f"/author/{a.pk}/ping-muted/")
    assert response.status_code == 302
    assert _messages(response) == []


@pytest.mark.django_db
def test_action_view_success_hook_still_runs(client_user_author_change: Client, cv_author):
    a = Author.objects.create(first_name="First", last_name="Author")
    response = client_user_author_change.post(f"/author/{a.pk}/ping-hook/")
    assert response.status_code == 302
    a.refresh_from_db()
    assert a.pseudonym == "hooked"
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd tests && pytest test1/test_action_messages.py -k "action_view" -v`
Expected: FAIL — success/error message tests fail (no message emitted); hook test currently passes
(hook already called by `post`). At least the success and error tests must FAIL before implementing.

- [ ] **Step 4: Implement emission in `ActionView`**

Replace the body of `src/crud_views/lib/views/action.py` with:

```python
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class ActionView(CrudView, SingleObjectMixin, generic.View):
    cv_list_action_method = "post"
    cv_action_messages: bool = True  # set False to suppress success/error messages

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        result = self.action(context)
        if result:
            self.cv_action_success(context)
        else:
            self.cv_action_error(context)
        url = self.get_success_url()
        return HttpResponseRedirect(url)

    def action(self, context: dict) -> bool:
        raise NotImplementedError("Action not implemented")

    def cv_action_success(self, context: dict) -> None:
        if self.cv_action_messages:
            message = self.cv_get_message()
            if message:
                messages.success(self.request, message)
        self.cv_action_success_hook(context)

    def cv_action_error(self, context: dict) -> None:
        if self.cv_action_messages:
            message = self.cv_get_message(error=True)
            if message:
                messages.error(self.request, message)
        self.cv_action_error_hook(context)

    def cv_action_success_hook(self, context: dict) -> None:
        """Hook for additional side effects after a successful action."""
        pass

    def cv_action_error_hook(self, context: dict) -> None:
        """Hook for additional side effects after a failed action."""
        pass


class ActionViewPermissionRequired(CrudViewPermissionRequiredMixin, ActionView):  # this file
    cv_permission = "change"
```

- [ ] **Step 5: Run the ActionView tests to verify they pass**

Run: `cd tests && pytest test1/test_action_messages.py -k "action_view" -v`
Expected: PASS (all five).

- [ ] **Step 6: Format, lint, commit**

```bash
cd /home/alex/projects/alex/django-crud-views
task format && task check
git add src/crud_views/lib/views/action.py tests/test1/app/views.py tests/test1/test_action_messages.py
git commit -m "feat(action): emit success/error messages from ActionView

ActionView.post now renders cv_message_template (success) / _error (failure)
via cv_action_success/cv_action_error, which still call the existing hooks.
Disable per view with cv_action_messages=False or by leaving templates unset.

Claude-Session: https://claude.ai/code/session_01KqgEeiK2iZ7nGDw92LvqnF"
```

---

### Task 3: Ordered up/down views now emit their configured messages

**Files:**
- Test: `tests/test1/test_action_ordered.py` (extend)

No production code changes — this task verifies the "free" fix from Task 2 (the ordered views
already declare `cv_message_template`).

**Interfaces:**
- Consumes: `ActionView` emission from Task 2; `OrderedUpView`/`OrderedDownView`
  `cv_message_template` = `crud_views/snippets/message/up.html` / `down.html` (both render
  `{{ object }}`).

- [ ] **Step 1: Write the failing tests for ordered-view messages**

Append to `tests/test1/test_action_ordered.py` (the `get_messages` import goes at the top):

```python
from django.contrib.messages import get_messages


@pytest.mark.django_db
def test_move_up_emits_message(client_user_author_change: Client, cv_author):
    a1 = Author.objects.create(first_name="First", last_name="Author")
    a2 = Author.objects.create(first_name="Second", last_name="Author")
    response = client_user_author_change.post(f"/author/{a2.pk}/up/")
    assert response.status_code == 302
    rendered = [m.message for m in get_messages(response.wsgi_request)]
    assert any(str(a2) in m for m in rendered)


@pytest.mark.django_db
def test_move_down_emits_message(client_user_author_change: Client, cv_author):
    a1 = Author.objects.create(first_name="First", last_name="Author")
    Author.objects.create(first_name="Second", last_name="Author")
    response = client_user_author_change.post(f"/author/{a1.pk}/down/")
    assert response.status_code == 302
    rendered = [m.message for m in get_messages(response.wsgi_request)]
    assert any(str(a1) in m for m in rendered)
```

- [ ] **Step 2: Run the tests**

Run: `cd tests && pytest test1/test_action_ordered.py -k "emits_message" -v`
Expected: PASS (Task 2 already makes ordered views emit). If they FAIL, the regression is in
Task 2 — fix there, not here.

- [ ] **Step 3: Run the full suite**

Run: `cd tests && pytest -q`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
cd /home/alex/projects/alex/django-crud-views
git add tests/test1/test_action_ordered.py
git commit -m "test(action): assert ordered up/down views emit move messages

Claude-Session: https://claude.ai/code/session_01KqgEeiK2iZ7nGDw92LvqnF"
```

---

### Task 4: Documentation (reference pages + CHANGELOG)

**Files:**
- Create: `docs/reference/action_view.md`
- Modify: `docs/reference/.pages` (nav order)
- Modify: `docs/reference/index.md` (Views list)
- Modify: `docs/reference/ordered_view.md` (Messages section)
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Create `docs/reference/action_view.md`**

```markdown
# ActionView

`ActionView` runs a side-effecting operation on a single object in response to a `POST`,
then redirects. Subclass it and implement `action(self, context) -> bool`; return a truthy
value on success and a falsy value on failure.

```python
from crud_views.lib.views import ActionViewPermissionRequired


class PublishView(ActionViewPermissionRequired):
    cv_key = "publish"
    cv_path = "publish"
    cv_viewset = cv_book
    cv_message_template_code = "Published »{{ object }}«"
    cv_message_template_error_code = "Could not publish »{{ object }}«"

    def action(self, context):
        obj = context["object"]
        if obj.can_publish:
            obj.publish()
            return True
        return False
```

## Messages

After the action runs, `ActionView` evaluates its result and emits a Django message:

- truthy result → `messages.success` rendered from `cv_message_template` /
  `cv_message_template_code`
- falsy result → `messages.error` rendered from `cv_message_template_error` /
  `cv_message_template_error_code`

A message is only emitted when the relevant template is configured. Templates are rendered
with the view metadata in context, including `{{ object }}`.

### Disabling messages

- Leave the message templates unset → no message for that branch.
- Set `cv_action_messages = False` on the view to suppress all action messages.

## Hooks

Override these for side effects beyond messaging; they run after the (optional) message is
emitted:

| Hook | When |
|------|------|
| `cv_action_success_hook(self, context)` | action returned truthy |
| `cv_action_error_hook(self, context)` | action returned falsy |

## View Classes

| Class | Description |
|-------|-------------|
| `ActionView` | Runs `action()` on POST, emits messages, redirects (no permission check) |
| `ActionViewPermissionRequired` | Same, requires `change` permission |
```

- [ ] **Step 2: Register the new page in `docs/reference/.pages`**

Insert `action_view.md` immediately after `action_enabled.md`:

```yaml
nav:
    - index.md
    - list_view.md
    - detail_view.md
    - create_view.md
    - update_view.md
    - delete_view.md
    - action_enabled.md
    - action_view.md
    - custom_form_view.md
    - workflow_view.md
    - polymorphic_view.md
    - context_buttons.md
    - guardian.md
    - ordered_view.md
    - templates.md
    - settings.md
    - ...
```

- [ ] **Step 3: Add ActionView to the Views list in `docs/reference/index.md`**

Under `## Views`, add after the `DeleteView` line:

```markdown
- [ActionView](action_view.md) — run a side-effecting action on an object with success/error messages
```

- [ ] **Step 4: Add a Messages section to `docs/reference/ordered_view.md`**

Append after the `## View Classes` table:

```markdown
## Messages

The up/down views ship with default move messages (`cv_message_template` →
`crud_views/snippets/message/up.html` / `down.html`) and emit them automatically after a
successful move — no extra mixin required. Override `cv_message_template` /
`cv_message_template_code` to customize, or set `cv_action_messages = False` to disable.
```

- [ ] **Step 5: Update `CHANGELOG.md`**

Under `## Unreleased`, in the existing `### Added` list, append:

```markdown
- `ActionView` now evaluates its action result and emits a Django message: a success message (`cv_message_template`/`cv_message_template_code`) on a truthy result and an error message (new `cv_message_template_error`/`cv_message_template_error_code`) on a falsy result. Emission is built in (no `MessageMixin` needed); disable per view with `cv_action_messages = False` or by leaving the templates unset. As a result, `OrderedUpView`/`OrderedDownView` now show their "Moved … up/down" messages automatically.
```

And under `## Unreleased`, add a `### Fixed` entry (create the subsection if absent):

```markdown
- `MessageMixin`'s error path could never fire (its `cv_get_message` ignored the requested attribute and it guarded on an undefined `cv_error_message`). The success/error message renderer now lives on `CrudView.cv_get_message(*, error=False)`, returns `None` when unconfigured instead of raising, and the dead `MessageMixin.action()` wrapper was removed.
```

- [ ] **Step 6: Build the docs to verify**

Run: `cd /home/alex/projects/alex/django-crud-views && uv run mkdocs build --strict 2>&1 | tail -20`
Expected: `INFO - Documentation built` with no warnings/errors. (If `uv run` is unavailable, use the project's `task docs` target to confirm the site renders; stop it after it serves cleanly.)

- [ ] **Step 7: Commit**

```bash
cd /home/alex/projects/alex/django-crud-views
git add docs/reference/action_view.md docs/reference/.pages docs/reference/index.md docs/reference/ordered_view.md CHANGELOG.md
git commit -m "docs(action): document ActionView messaging and ordered-view messages

Claude-Session: https://claude.ai/code/session_01KqgEeiK2iZ7nGDw92LvqnF"
```

---

### Task 5: Update the `django-crud-views` skill

**Files:**
- Modify: `skills/django-crud-views/references/api-reference.md`
- Modify: `skills/django-crud-views/SKILL.md`

**Context:** The skill currently documents a non-existent `cv_message` attribute and uses
`{object}` (literal in Django templates). Only `cv_message_template` / `cv_message_template_code`
(and now the `_error` pair) are read, and substitution needs `{{ object }}`.

- [ ] **Step 1: Fix the form-view messaging examples in `api-reference.md`**

Replace every `cv_message = "..."` with `cv_message_template_code = "..."` and change any
`{object}` inside message strings to `{{ object }}`. Specifically:

- line ~117: `cv_message = "Created »{object}«"` → `cv_message_template_code = "Created »{{ object }}«"`
- line ~137: `cv_message = "Updated »{object}«"` → `cv_message_template_code = "Updated »{{ object }}«"`
- line ~150: `cv_message = "Deleted »{object}«"` → `cv_message_template_code = "Deleted »{{ object }}«"`
- line ~177: `cv_message_template_code = "Contacted »{object}«"` → `cv_message_template_code = "Contacted »{{ object }}«"`

- [ ] **Step 2: Update the ActionView example in `api-reference.md`**

Replace the `### ActionView / ActionViewPermissionRequired` block (around lines 191-205) with:

```markdown
### ActionView / ActionViewPermissionRequired

```python
from crud_views.lib.views import ActionViewPermissionRequired

class MyActionView(ActionViewPermissionRequired):
    cv_key = "my_action"        # unique key for this view
    cv_path = "my-action"       # URL path segment
    cv_viewset = cv_my
    cv_icon_action = "fa-solid fa-bolt"
    cv_message_template_code = "Did the thing to »{{ object }}«"        # success message
    cv_message_template_error_code = "Could not do the thing to »{{ object }}«"  # error message

    def action(self, context):
        obj = context["object"]
        # perform action on obj; return True on success, False on failure
        return True
```

Messages are built in: a truthy `action()` result emits the success message, a falsy result
emits the error message. Disable with `cv_action_messages = False` or by leaving the templates
unset. `MessageMixin` is **not** needed for `ActionView`.
```

- [ ] **Step 3: Update the Ordered views example in `api-reference.md`**

Replace the `### OrderedUpView / OrderedDownView` block (around lines 208-223) with:

```markdown
### OrderedUpView / OrderedDownView (requires django-ordered-model)

```python
from crud_views.lib.views import OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired

class MyUpView(OrderedUpViewPermissionRequired):
    cv_viewset = cv_my

class MyDownView(OrderedUpDownPermissionRequired):
    cv_viewset = cv_my
```

The up/down views ship with default move messages and emit them automatically — no
`MessageMixin` required. Override `cv_message_template_code` to customize, or set
`cv_action_messages = False` to disable. Add `"up"` and `"down"` to `cv_list_actions` in the
list view. Model must extend `OrderedModel` and `ordered_model` must be in `INSTALLED_APPS`.
```

- [ ] **Step 4: Reflect built-in action messaging in `SKILL.md`**

Open `skills/django-crud-views/SKILL.md`. If it mentions `MessageMixin` as required for action
or ordered views, or describes `ActionView` capabilities, update it to state that `ActionView`
(and the ordered up/down views) emit success/error messages built in via
`cv_message_template[_error][_code]`, disableable with `cv_action_messages = False`. If
`SKILL.md` does not discuss messaging, make no change.

- [ ] **Step 5: Verify no stale messaging syntax remains**

Run:
```bash
cd /home/alex/projects/alex/django-crud-views/skills/django-crud-views
grep -rn "cv_message = \|»{object}«\|{object}" . ; echo "exit: $?"
```
Expected: no matches (grep exit status 1 / "exit: 1"). Any remaining hit is a miss — fix it.

- [ ] **Step 6: Commit**

```bash
cd /home/alex/projects/alex/django-crud-views
git add skills/django-crud-views/references/api-reference.md skills/django-crud-views/SKILL.md
git commit -m "docs(skill): correct messaging API and document built-in ActionView messages

Replaces the non-existent cv_message attribute with cv_message_template_code,
fixes {object} -> {{ object }}, and documents built-in ActionView/ordered
messaging (no MessageMixin needed).

Claude-Session: https://claude.ai/code/session_01KqgEeiK2iZ7nGDw92LvqnF"
```

---

### Task 6: Final verification

- [ ] **Step 1: Full test suite**

Run: `cd tests && pytest -q`
Expected: all pass.

- [ ] **Step 2: Lint/format clean**

Run: `cd /home/alex/projects/alex/django-crud-views && task check && task format`
Expected: no changes needed / no errors.

- [ ] **Step 3: Confirm the issue's two requirements are met**

- ActionView evaluates the action result → `cv_action_success`/`cv_action_error` branch in `post`.
- ActionView emits success/error messages → covered by `test_action_view_emits_success_message`
  / `test_action_view_emits_error_message`.

---

## Self-Review Notes

- **Spec coverage:** error attrs (T1), corrected renderer returning None (T1), ActionView
  built-in emission + `cv_action_messages` (T2), `MessageMixin.action()` removal (T1), ordered
  views fire messages (T3), docs incl. new `action_view.md` + nav + CHANGELOG (T4), skill
  corrections incl. `cv_message`→`cv_message_template_code` and `{object}`→`{{ object }}` (T5),
  tests for success/error/no-template/disabled/hooks (T2) and ordered (T3). No project-wide
  setting (explicit non-goal) — not planned. All spec sections map to a task.
- **Type consistency:** `cv_get_message(*, error=False) -> str | None` used identically in base
  (T1), ActionView (T2), and MessageMixin's `cv_form_valid_hook` (T1). Attribute names
  `cv_message_template_error` / `cv_message_template_error_code` consistent across T1/T2/T4/T5.
