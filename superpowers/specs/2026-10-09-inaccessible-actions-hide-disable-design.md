# Configurable hide vs. disable for inaccessible actions — design

- Issue: [#149](https://github.com/jacob-consulting/django-crud-views/issues/149)
- Date: 2026-10-09
- Status: approved (spec reviewed 2026-10-09)

## Goal

Projects can choose whether an action the user may not use is **hidden** (today's behaviour, stays the default) or
rendered **disabled** (greyed out, not clickable, `aria-disabled`), so users can see that the action exists. The
choice is a setting, overridable per ViewSet and per CrudView, and it applies uniformly to every action-rendering
path: context buttons (toolbar and manual placement), list actions, list action forms, card actions and child card
actions.

## Decisions (from brainstorming)

| Question | Decision |
|---|---|
| Whose override applies? | The **target action's** view: target `CrudView` → target `ViewSet` → setting. `PublisherDeleteView.cv_inaccessible_actions = "disable"` greys out the delete button everywhere it appears. |
| Distinguish "no permission" from "action not enabled"? | **One mode for both.** Templates get `cv_disabled_reason = "permission" \| "state"` so custom templates/CSS can still differ. |
| Tooltip / reason text? | **None.** The button keeps its normal label/title; no new translatable strings. |
| `cv_context_url` in disable mode? | Returns **`None`** in both modes (a bare URL cannot carry a disabled flag). |
| `cv_get_context_buttons()` in disable mode? | Includes the entry, flagged `cv_disabled=True`, `cv_url=None`. |
| Child card actions (`CardAction(child_name=...)`) | **In scope; behaviour change.** They now check `cv_has_access` on the child view (like `ChildContextButton`), so in the default `"hide"` mode a user without child permission no longer sees the button (today: visible, click → 403). |
| `LinkChildColumn` (tables) | **Unchanged** — a data column, not an action. |
| Architecture | **Approach A**: the mode travels in the button data (`cv_get_dict`), and one function decides where the data is used. |

## Background: current state (verified in code)

Every action's data dict is built by the target class's `cv_get_dict()` — via the four `ContextButton.get_context`
subclasses (`crud_views/lib/view/buttons.py`) or the plain-key path in `CrudView.cv_get_context()`
(`crud_views/lib/view/base.py`). Guardian (`crud_views_guardian/lib/mixins.py`) post-processes `cv_access` /
`cv_action_enabled` **after** `cv_get_dict` for parent-object create buttons. `cv_card_action` builds its dicts itself.

The hide decision is currently made in five separate places:

| Path | Where the hide decision lives |
|---|---|
| context button tags | `_context_button_visible()` in `crud_views/templatetags/crud_views.py` |
| `CrudView.cv_get_context_buttons()` | inline copy of the same condition in `crud_views/lib/view/base.py` |
| list action | `tags/list_action.html` line 1 |
| list action form | `tags/list_action_form.html` line 1 |
| card action | `tags/card_action.html` line 1, plus `cv_card_action()` returns early with `{cv_access: False, cv_action_enabled}` (no URL, label, icon) |
| child card action | `cv_card_action()` child branch hard-codes `cv_access: True` (documented in `docs/reference/card-list-view.md`, pinned by `test_card_child_action_always_renders`; target view returns 403) |

## Design

### 1. Configuration and resolution

- **Setting** `CRUD_VIEWS_INACCESSIBLE_ACTIONS` → `CrudViewsSettings.inaccessible_actions: str`, default `"hide"`.
  New system check **`crud_views.E104`** in `CrudViewsSettings.check_messages`: value must be `"hide"` or
  `"disable"` (same pattern as E101).
- **ViewSet** field `inaccessible_actions: Literal["hide", "disable"] | None = None`. Pydantic validates the value at
  ViewSet definition; no system check needed. `GuardianViewSet` inherits it.
- **CrudView** attribute `cv_inaccessible_actions: str | None = None`, validated by a new view check **`E207`**
  (value must be `None`, `"hide"` or `"disable"`), yielded from `CrudView.checks()`. E203 is not reused (it belonged to
  the retired context-action check).
- **Resolution** classmethod `CrudView.cv_get_inaccessible_actions() -> str`:
  `cls.cv_inaccessible_actions` → `cls.cv_viewset.inaccessible_actions` → `crud_views_settings.inaccessible_actions`
  (mirrors `cv_get_extends_template()`).
- **Into the data**: `CrudView.cv_get_dict()` adds `"cv_inaccessible_actions": cls.cv_get_inaccessible_actions()`.
  Because `cv_get_dict` runs on the **target** class, the target decides. Nothing is decided at build time, so
  guardian's later changes to `cv_access` / `cv_action_enabled` are respected without guardian changes.

### 2. The deciding function and its call sites

New module `crud_views/lib/view/visibility.py` (importable from `base.py` and the template tags). It replaces
`_context_button_visible` and the inline copy in `cv_get_context_buttons`.

```python
def cv_resolve_action(ctx: dict | None) -> dict | None:
    """Resolve an action's button data to show / disable / hide.

    Returns None to hide, a copy flagged cv_disabled=True (cv_url=None, cv_disabled_reason) to render
    disabled, or a copy flagged cv_disabled=False to render normally. Never mutates ctx.
    """
    if not ctx:
        return None
    usable = ctx.get("cv_access") is True and ctx.get("cv_action_enabled") is not False
    if usable:
        return {**ctx, "cv_disabled": False}
    if ctx.get("cv_inaccessible_actions") != "disable":
        return None
    reason = "permission" if ctx.get("cv_access") is not True else "state"
    return {**ctx, "cv_disabled": True, "cv_url": None, "cv_disabled_reason": reason}
```

- Permission failure takes precedence over state for the reason (`cv_action_enabled` is only meaningful after access).
- Data without `cv_inaccessible_actions` (hand-built dicts) hides — safe default.
- Idempotent: resolving already-resolved data yields the same result (needed because
  `cv_render_context_button` receives entries from `cv_get_context_buttons`).

Call sites:

| Call site | hide | disable |
|---|---|---|
| `cv_context_action` (used per key by the `{% cv_context_actions %}` toolbar template) and `_render_context_button` (used by `cv_context_button`, `cv_render_context_button`) | `""` | render the button's template / template_code with the disabled data |
| `cv_context_url` | `None` | `None` (returns a URL only when `cv_disabled` is False) |
| `CrudView.cv_get_context_buttons()` | entry skipped | entry included, disabled |
| `cv_list_action` | `{}` | disabled data |
| `cv_list_action_form` | `{}` | `{}` (a disabled button never submits; no hidden form) |
| `cv_card_action`, key branch | `{}` | disabled data — the early `return {"cv_access": False, ...}` is removed so label/icon/variant/flex are always built, then resolved |
| `cv_card_action`, child branch | `{}` | disabled data — `cv_access = child_cls.cv_has_access(user, obj)` (same call as `ChildContextButton`), `cv_inaccessible_actions = child_cls.cv_get_inaccessible_actions()`, then resolved |

Guardian: `child_cls.cv_has_access` resolves to the guardian override where present, same as for
`ChildContextButton`; no guardian code changes.

### 3. Templates, markup, accessibility

Only theme: `crud_views/templates/crud_views/tags/`.

| Template | Disabled rendering |
|---|---|
| `context_action.html` | `<a class="btn btn-outline-primary btn-lg disabled" aria-disabled="true" role="button" data-cv-disabled="{{ cv_disabled_reason }}" cv-key=… title=…>` — icon + visually-hidden label kept |
| `list_action.html` (GET / modal) | `<a class="btn btn-outline-primary btn-xs disabled" aria-disabled="true" role="button" data-cv-disabled=…>` |
| `list_action.html` (POST) | `<button type="button" class="btn btn-outline-primary btn-xs" disabled data-cv-disabled=…>` |
| `list_action_form.html` | nothing (never receives disabled data) |
| `card_action.html` (always `<a>`) | `<a class="btn btn-… btn-sm[ flex-grow-1] disabled" aria-disabled="true" role="button" data-cv-disabled=…>` — label or icon as today |

Rules for every disabled element:

- **No `href`**, no `data-cv-action="submit-form"`, no `data-cv-modal` / `data-cv-modal-size`, so the `viewset.js` /
  `modal.js` delegated click handlers cannot fire. An `<a>` without `href` is not focusable; no `tabindex` needed.
- `title` and the visually-hidden label stay; `aria-disabled` / `disabled` lets screen readers announce the state.
  Bootstrap's `.disabled` sets `pointer-events: none`, so the hover title does not show — accepted.
- `data-cv-disabled="permission|state"` lets projects style the two reasons via CSS.

Template structure: `{% if cv_disabled %}…disabled…{% elif <existing condition> %}…unchanged…{% endif %}` — the
existing condition stays as a second safety check.

**Overridden templates stay safe**: in disable mode `cv_access` / `cv_action_enabled` keep their "unusable" values, so
project templates still carrying the old condition keep **hiding** the action — never a clickable link. Projects opt
in by adding a `cv_disabled` branch (documented).

**Per-button custom templates** (`ContextButton(template=...)` / `template_code=...`): since #147 the gate lives in
Python, so these templates usually have **no** access condition. In disable mode they receive the disabled data
(`cv_disabled=True`, `cv_url=None`) and are responsible for rendering it; a template that ignores `cv_disabled` would
render a link with an empty/`None` URL. This is accepted because disable mode is opt-in per target view / ViewSet /
setting: switching it on is the point where a project reviews its custom button templates. The docs (theme / context
button pages) call this out explicitly, with a snippet.

## Testing

All under `tests/test1/`:

- `cv_resolve_action` table test: usable, hide, disable/permission, disable/state, both failing → `permission`,
  empty/None, missing mode key → hide, no mutation, idempotence.
- Resolution order: view → ViewSet → setting (patch the `crud_views_settings` instance attribute; settings are read at
  import).
- System checks: E104 and E207, positive and negative.
- Rendering in both modes via the test client (user lacking a permission; a view with `cv_action_enabled` → False):
  context toolbar, `cv_context_button`, `cv_context_url` (`None` in both modes), `cv_get_context_buttons` (flagged
  entry in disable), list action GET / POST / modal (no `href`, no `data-cv-*`, `<button disabled>` for POST), no
  `list_action_form` in disable, card action key / POST / child.
- Child card actions: rename and rewrite `test_card_child_action_always_renders` →
  `test_card_child_action_hidden_without_child_permission`; add a disable-mode test.
- Guardian: per-object permission denial renders disabled in disable mode.
- Overridden-template compatibility: a test template with the old condition still hides in disable mode.
- Per-button custom `template_code` receives `cv_disabled` / `cv_disabled_reason` in disable mode.
- Default unchanged: the remaining existing suite passes unmodified.

## Documentation

- Settings reference: `CRUD_VIEWS_INACCESSIBLE_ACTIONS`.
- ViewSet reference: `inaccessible_actions`; CrudView attributes: `cv_inaccessible_actions`, resolution order.
- `docs/reference/card-list-view.md`: replace "Child actions always render …" with the permission-checked behaviour.
- Context buttons / manual placement page: `cv_context_url` vs `cv_get_context_buttons` in disable mode.
- Theme / template override guide: the `cv_disabled` branch, `cv_disabled_reason`, `data-cv-disabled` CSS hook.
- System checks reference: E104, E207.

## Example app

Add a disable-mode variant to the `context_buttons` example (`examples/bootstrap5/context_buttons/`) so a
lower-permission demo user sees greyed-out buttons next to hidden ones. Update the `ticket_detail.html` comment that
says `cv_get_context_buttons` is "already filtered to the buttons the user may use".

## Changelog and release

- `### Added`: `CRUD_VIEWS_INACCESSIBLE_ACTIONS`, `ViewSet.inaccessible_actions`, `CrudView.cv_inaccessible_actions`,
  `cv_disabled` / `cv_disabled_reason` template variables, checks `crud_views.E104` and `E207`.
- `### Changed`: child card actions (`CardAction(child_name=...)`) now check permission on the child view; in the
  default mode users without it no longer see the button (previously visible, click → 403).
- Behaviour change → **minor** release (0.28.0). Afterwards update the `django-crud-views` skill in the skills
  monorepo.

## Out of scope

- `FilterContextButton` / `context_action_filter.html`: its data does not come from `cv_get_dict` (no mode key, so it
  always resolves to hide) and it is only `cv_access=True` when it applies to the current list page — it can never be
  disabled, so its template is unchanged.
- `cv_context_has_permission` filter: a pure permission query for gating surrounding markup, not a renderer; unchanged.

- Tooltip / reason text, separate modes per reason, `LinkChildColumn`, manage views.
