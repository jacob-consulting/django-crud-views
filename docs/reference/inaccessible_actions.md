# Hide or disable inaccessible actions

An action is **inaccessible** for a user when they lack the permission for its target view (`cv_has_access`) or
the action is not applicable right now (`cv_action_enabled` returns `False`). By default such actions are
**hidden**. Set the mode to `"disable"` to render them **disabled** (greyed out, not clickable) instead, so users can
see that the action exists.

The mode applies to every place an action is rendered: the context-button toolbar, the manual placement tags
(`cv_context_button`, `cv_get_context_buttons`), list row actions and card actions, including child card actions.

!!! example "Try it live"
    The [Disabled Actions example](https://django-crud-views-demo.onrender.com/disabled-actions/lockable_ticket/) in the
    live demo shows a disabled and a hidden action side by side — log in as `alice` / `alice`. See
    [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## Configuration

| Where | Attribute | Values |
|---|---|---|
| Django settings | `CRUD_VIEWS_INACCESSIBLE_ACTIONS` | `"hide"` (default), `"disable"` |
| `ViewSet` | `inaccessible_actions` | `None` (use the setting), `"hide"`, `"disable"` |
| `CrudView` | `cv_inaccessible_actions` | `None` (use the ViewSet), `"hide"`, `"disable"` |

The mode is resolved on the **target** view of the action — the view the button links to — not on the page the
button appears on:

```python
class PublisherDeleteView(DeleteViewPermissionRequired):
    cv_viewset = cv_publisher
    cv_inaccessible_actions = "disable"  # delete is greyed out on the list rows, the cards and the detail toolbar
```

Order: `CrudView.cv_inaccessible_actions` → `ViewSet.inaccessible_actions` → `CRUD_VIEWS_INACCESSIBLE_ACTIONS`
(`CrudView.cv_get_inaccessible_actions()` returns the result).

## What "disabled" renders

The default templates render a disabled action without a URL and without the JavaScript hooks
(`data-cv-action`, `data-cv-modal`), so it cannot be activated by mouse or keyboard:

- every disabled action (context buttons, list and card actions, whether they link or POST):
  `<button type="button" class="btn …" disabled data-cv-disabled="permission">`, and no hidden POST form

`data-cv-disabled` is `"permission"` when the user lacks the permission and `"state"` when `cv_action_enabled`
returned `False`. Use it to style the two cases differently:

```css
[data-cv-disabled="state"] { opacity: .35; }
```

A disabled icon-only button keeps its `title` and `data-cv-tooltip`, but Bootstrap sets `pointer-events: none` on
`.btn:disabled`, so neither the native `title` nor a tooltip shows on hover. A theme that needs a tooltip there wraps
the button in a focusable element in its own leaf override, Bootstrap's documented workaround; the stock leaf does not.

## Missing core permission declarations

For views using the core `CrudViewPermissionRequiredMixin.cv_has_access`, a missing or falsy entry for
`cv_permission` in the ViewSet's permission mapping denies access before checking the user's permissions.
This applies to ordinary users, anonymous users and superusers, including an empty mapping or an unmatched
custom key. The action is hidden or disabled according to its target's mode; disabled output has reason
`"permission"` and no usable URL, even when the independent action-state check also denies.

Opening the target directly still raises the existing missing-permission assertion with its migration/restart
diagnostic. Fix the declaration or run the required migrations; hiding a control does not fix configuration or
replace request authorization. A previously empty default permission lookup retries, so the same ViewSet can
discover permissions created by migrations. Already populated mappings retain their existing cache policy;
this is not general cache invalidation. Resource permission declarations retain the `viewset.E260` check.

Guardian overrides have their own behavior. In particular, a missing parent permission declaration can fail
host-page rendering for the scoped [Guardian collection links](guardian.md#limits-and-configuration-failures);
this core guard does not catch that failure.

## Template variables

| Variable | Meaning |
|---|---|
| `cv_disabled` | `True` for a disabled action, `False` for a usable one |
| `cv_disabled_reason` | `"permission"` or `"state"` (only when disabled) |
| `cv_url` | `None` when disabled |

### `cv_context_url` and `cv_get_context_buttons`

- `{% cv_context_url %}` returns `None` for every inaccessible action, in both modes — a bare URL cannot say
  "disabled".
- `view.cv_get_context_buttons()` leaves hidden buttons out and includes disabled ones with `cv_disabled=True` and
  `cv_url=None`. A loop that builds its own `<a href>` must check `cv_disabled`.

### Custom button templates

A `ContextButton(template=...)` or `ContextButton(template_code=...)` receives the disabled data in disable mode and
must render it. Add a `cv_disabled` branch when you switch a target view to `"disable"`:

```django
{% if cv_disabled %}
    <span class="btn btn-primary disabled" aria-disabled="true">{{ cv_action_label }}</span>
{% else %}
    <a href="{{ cv_url }}" class="btn btn-primary">{{ cv_action_label }}</a>
{% endif %}
```

### Overridden tag templates

Templates you copied from `crud_views/tags/` before 0.28.0 (`list_action.html`, `card_action.html`,
`context_action.html`) still check `cv_access is True`. In disable mode `cv_access` stays `False`, so these
templates keep **hiding** the action — never a broken link. Replace the copy with the shipped one-line logic template
and override the leaf `crud_views/tags/button/action.html` (or `menu_item.html`) instead: it receives `cv_disabled` and
`cv_disabled_reason` and must render them, see [Buttons](buttons.md#logic-templates-and-leaves).

## System checks

| Id | Meaning |
|---|---|
| `crud_views.E104` | `CRUD_VIEWS_INACCESSIBLE_ACTIONS` is not `"hide"` or `"disable"` |
| `viewset.E207` | `cv_inaccessible_actions` is not `None`, `"hide"` or `"disable"` |

`ViewSet.inaccessible_actions` is validated when the ViewSet is defined (pydantic `ValidationError`).

## Inside action menus

Disabled actions inside an [action menu](action_menus.md) render as disabled dropdown items; hidden ones appear
nowhere, and a menu whose actions are all hidden renders no toggle.
