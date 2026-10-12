# Hide or disable inaccessible actions

An action is **inaccessible** for a user when they lack the permission for its target view (`cv_has_access`) or
the action is not applicable right now (`cv_action_enabled` returns `False`). By default such actions are
**hidden**. Set the mode to `"disable"` to render them **disabled** (greyed out, not clickable) instead, so users can
see that the action exists.

The mode applies to every place an action is rendered: the context-button toolbar, the manual placement tags
(`cv_context_button`, `cv_get_context_buttons`), list row actions and card actions, including child card actions.

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
templates keep **hiding** the action — never a broken link. Add a `{% if cv_disabled %}` branch (see the shipped
templates) to render disabled buttons.

## System checks

| Id | Meaning |
|---|---|
| `crud_views.E104` | `CRUD_VIEWS_INACCESSIBLE_ACTIONS` is not `"hide"` or `"disable"` |
| `viewset.E207` | `cv_inaccessible_actions` is not `None`, `"hide"` or `"disable"` |

`ViewSet.inaccessible_actions` is validated when the ViewSet is defined (pydantic `ValidationError`).
