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
