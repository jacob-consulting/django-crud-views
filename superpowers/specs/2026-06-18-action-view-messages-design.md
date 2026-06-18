# ActionView: evaluate action result and emit messages

- **Date:** 2026-06-18
- **Issue:** [#32](https://github.com/jacob-consulting/django-crud-views/issues/32) — "ActionView: evaluate action result and emit messages"
- **Status:** Approved design

## Problem

`ActionView` (`lib/views/action.py`) is meant to run a side-effecting action on an
object and redirect. The original issue says it "does not evaluate the action result
or emit success/error messages." Investigation shows the picture is more nuanced:

1. **Result evaluation already happens.** `post()` runs `result = self.action(context)`
   and branches: `if result:` → `cv_action_success_hook(context)` else
   `cv_action_error_hook(context)`. So this half of the issue is already done.
2. **No messages are emitted.** Both hooks are empty no-ops, so `ActionView` is silent
   out of the box.
3. **Ordered views configure messages that never fire.** `OrderedUpView` /
   `OrderedDownView` declare `cv_message_template = "crud_views/snippets/message/up.html"`
   (and the `up.html` / `down.html` snippets exist), but they do **not** mix in
   `MessageMixin`, so those "Moved … up/down" messages are dead configuration.
4. **The opt-in error path is broken.** `MessageMixin.cv_get_message(attribute=...)`
   silently ignores its `attribute` argument — it always renders `cv_message_template`.
   Its error branch also guards on `hasattr(self, "cv_error_message")`, an attribute
   that is never defined anywhere. So error messages can never actually appear today.

There are effectively two overlapping, half-wired messaging mechanisms (the empty
`ActionView` hooks and `MessageMixin.action()`), and neither produces an action message
in the shipped library views.

## Goals

- `ActionView` emits a **success** message when the action returns truthy and an
  **error** message when it returns falsy — out of the box, no extra mixin required.
- `OrderedUpView` / `OrderedDownView` "Moved … up/down" messages fire automatically.
- Messaging is **fully disableable** per view.
- Fix the broken success/error message renderer so error messages are actually possible.
- Keep the existing `cv_action_success_hook` / `cv_action_error_hook` extension points
  for non-message side effects.
- Update reference docs and the `skills/django-crud-views` skill.

## Non-goals

- No project-wide settings flag (e.g. `CRUD_VIEWS_ACTION_MESSAGES`). YAGNI; per-view
  control is enough. Can be added later if a real need appears.
- No change to how form views (Create/Update/Delete/Workflow) emit messages, beyond
  pointing them at the corrected shared renderer.

## Design (approach: messaging built into `ActionView`, disableable)

### 1. Base attributes (`lib/view/base.py`)

Today only a success pair exists. Add an error pair alongside it:

```python
# success (exists today)
cv_message_template: str | None = None
cv_message_template_code: str | None = None
# error (new)
cv_message_template_error: str | None = None
cv_message_template_error_code: str | None = None
```

### 2. Safe, success/error-aware message renderer

Replace the broken `cv_get_message` with one that honors success vs. error and returns
`None` (instead of raising via `render_snippet`) when nothing is configured. This is the
template-based opt-out. It lives on base `CrudView` so both `ActionView` and the form
views' `MessageMixin` can use it:

```python
def cv_get_message(self, *, error: bool = False) -> str | None:
    template = self.cv_message_template_error if error else self.cv_message_template
    template_code = self.cv_message_template_error_code if error else self.cv_message_template_code
    if not template and not template_code:
        return None  # nothing configured -> no message
    return self.render_snippet(self.cv_get_meta(), template, template_code)
```

Note: `render_snippet` raises `CrudViewError` when neither template nor code is set, so
the early `return None` guard is required.

### 3. `ActionView` emits directly (`lib/views/action.py`)

```python
class ActionView(CrudView, SingleObjectMixin, generic.View):
    cv_list_action_method = "post"
    cv_action_messages: bool = True  # explicit kill-switch

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        result = self.action(context)
        if result:
            self.cv_action_success(context)
        else:
            self.cv_action_error(context)
        return HttpResponseRedirect(self.get_success_url())

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

    # extension points kept (still no-ops) — for side effects beyond messaging
    def cv_action_success_hook(self, context: dict) -> None: ...
    def cv_action_error_hook(self, context: dict) -> None: ...
```

### 4. Fixed for free

`OrderedUpView` / `OrderedDownView` already set `cv_message_template`, so with emission
in `ActionView` their messages now appear with no extra wiring. They define no error
template, so no error message is emitted (correct — up/down at the boundary is a no-op
that returns `True`).

### 5. `MessageMixin` cleanup (`lib/views/mixins.py`)

- Remove `MessageMixin.action()`. It is now redundant for actions and would
  **double-emit** if anyone wrote `class X(MessageMixin, ActionView)`.
- Keep the form-valid path (`cv_form_valid_hook`) for Create/Update/Delete/Workflow,
  pointing it at the corrected shared `cv_get_message()`.
- The `CheckTemplateOrCode` check currently in `MessageMixin.checks()` stays for form
  views. `ActionView` template fields are optional (silence is valid), so `ActionView`
  does not add a mandatory template check.

### 6. Opt-out, two ways

- Per-view, template-based: leave `cv_message_template` / error template unset → no
  message (existing convention; `cv_get_message` returns `None`).
- Per-view, hard off: `cv_action_messages = False`.

## Backward compatibility

One behavior change: projects using `OrderedUpView` / `OrderedDownView` (or other
`ActionView`s that happened to set `cv_message_template`) will now see success messages
where previously there were none. This is the intended fix. Views with no message
template configured stay silent. A CHANGELOG entry documents the change and the
`cv_action_messages = False` / unset-template opt-outs.

## Documentation changes

- **`docs/reference/ordered_view.md`** — document that up/down now emit messages
  automatically via `cv_message_template`, and how to customize/disable.
- **New `docs/reference/action_view.md`** (registered in `mkdocs.yml` nav alongside the
  other reference pages) — document `ActionView` messaging: success/error templates,
  `cv_message_template_error` / `cv_message_template_error_code`, the
  `cv_action_success_hook` / `cv_action_error_hook` extension points, and
  `cv_action_messages`. (`action_enabled.md` covers a different feature and is left
  alone.)
- **CHANGELOG.md** — entry under the next version.

## `skills/django-crud-views` changes

`skills/django-crud-views/references/api-reference.md` currently documents messaging
incorrectly and must be corrected as part of this work:

- Examples use a non-existent `cv_message = "..."` attribute. Only `cv_message_template`
  and `cv_message_template_code` are read. Replace `cv_message` usages with
  `cv_message_template_code`.
- Template code examples use `{object}` (literal text in Django templates). Correct to
  `{{ object }}` so substitution actually happens.
- The `ActionView` / `OrderedUpView` / `OrderedDownView` examples show
  `MessageMixin` being mixed in for messages. Update them: messages are now built in;
  `MessageMixin` is no longer needed (and no longer wraps `action()`). Show
  `cv_message_template_code` for success and `cv_message_template_error_code` for error,
  plus a note on `cv_action_messages = False` to disable.
- Mention the success/error split and the hooks in `SKILL.md` if it summarizes view
  capabilities.

## Testing (`tests/test1/`)

Add an action view fixture that configures both a success and an error message template
(and one with messaging disabled), then assert via Django's message framework
(`django.contrib.messages.get_messages` / response context):

- Truthy result + success template → one `messages.success` with rendered text.
- Falsy result + error template → one `messages.error` with rendered text.
- No templates configured → no messages (and no `CrudViewError` raised).
- `cv_action_messages = False` → no messages even when templates are set.
- `OrderedUpView` / `OrderedDownView` now produce a success message after up/down
  (extend `tests/test1/test_action_ordered.py`).
- Regression: `cv_action_success_hook` / `cv_action_error_hook` still called on the
  respective branch.

## Files touched

- `src/crud_views/lib/view/base.py` — error template attrs + corrected `cv_get_message`
- `src/crud_views/lib/views/action.py` — emission in `post` via success/error methods
- `src/crud_views/lib/views/mixins.py` — drop `MessageMixin.action()`, reuse shared renderer
- `tests/test1/app/views.py`, `tests/test1/test_action_ordered.py` (and/or a new test
  module) — new fixtures and tests
- `docs/reference/ordered_view.md`, new `docs/reference/action_view.md`, `mkdocs.yml`
  (nav), `CHANGELOG.md`
- `skills/django-crud-views/references/api-reference.md` (and `SKILL.md` if needed)
