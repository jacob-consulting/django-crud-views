# Form button label mode: label / icon / both for submit, delete, cancel and the filter buttons

Issue: #257.

Date: 2026-10-22

## Intent

Card, context and list actions have a label mode (`label` / `icon` / `both`, `crud_views/lib/view/label_mode.py`).
The form buttons do not. `Submit`, `Button` and `Reset` in `crud_views/lib/crispy/buttons.py` are crispy
`BaseInput`s, rendered as `<input type="submit|button|reset">`, and an `<input>` cannot hold an icon. A downstream
project replaced them with its own `<button>` class only to put icons on save, cancel and delete (a folder icon on
save, an X on cancel, a trash icon on delete forms, an `icon_only` switch that moves the text into `aria-label` and
`title`). The package should give a project that without replacing the buttons.

The maintainer's focus words for this series apply: maintainability, low complexity, easy to theme downstream, and
no more upstream surface than the issue needs.

## Goals

- The form buttons render a real `<button>` element and honour a label mode, with the same markup rules as
  `tags/button/action.html`.
- The mode is configured per button key with the same three layers as the context / list label modes: setting,
  ViewSet, view.
- Icons come from the icon registry, so a theme or project swaps them in one place.
- A project's own crispy layout that builds `Submit` / `Button` / `Reset` directly can give them an icon and a mode
  as constructor arguments, without any view.
- With nothing configured, the buttons look as today: text only, same text, classes, `name`, `value`, `id`.

## Non-goals

- Turning cancel into an `<a href>` link (the downstream project did). Cancel stays
  `<button type="button" data-cv-cancel-url>`; `static/crud_views/js/viewset.js` already uses
  `closest("[data-cv-cancel-url]")`, so a click on the icon inside still navigates.
- Per-form label-mode attributes. The mode is a view concern (setting → ViewSet → view); a form that needs something
  else overrides `get_*_button_kwargs()`.
- Formset controls (`formset:*`), the card-order buttons and the language selector: they are not crispy inputs and
  are out of scope.

## Anti-goals

- Changing the POST data. A view that tests `"delete" in request.POST`, or the modal's
  `new FormData(form, event.submitter)` (`modal.js`), must see exactly what it sees today.
- A second copy of the label-mode markup that can drift from `action.html` in behaviour (icon mode without a hidden
  label, a missing `title`, …).

## Scope: the five button keys

The key is the button's existing class-table slot under `form:`.

| Key | Built in | Element | Icon key |
|---|---|---|---|
| `submit` | `CrispyFormMixin.get_submit_button()` (`lib/crispy/form.py`) | `<button type="submit" name="submit">` | `CrispyFormMixin.submit_icon`, default `"save"` (new) |
| `delete` | `CrispyDeleteForm.get_delete_button()` | `<button type="submit" name="delete">` | `delete` (exists) |
| `cancel` | `CrispyFormMixin.get_cancel_button()` | `<button type="button" name="reset" data-cv-cancel-url>` | `cancel` (new) |
| `filter-submit` | `ListViewFilterFormHelper` (`lib/views/list.py`) | `<button type="submit" name="submit" id="filter-button">` | `filter` (exists) |
| `filter-reset` | `ListViewFilterFormHelper` | `<button type="reset" name="reset" id="filter-button-reset">` | `reset` (new) |

The workflow submit needs no own key: `WorkflowForm` (`crud_views_workflow/lib/forms.py`) is a `CrispyForm` with
`submit_label = "Process Workflow Step"`, so it is the `submit` button. It sets `submit_icon = "workflow"` (existing
key), because a save icon next to "Process Workflow Step" reads wrong.

## Design

### Buttons (`lib/crispy/buttons.py`)

`_TableClassMixin` grows two keyword arguments next to `slot`:

```python
Submit("submit", _("Save"), icon="save", label_mode="both")
```

- `icon`: an icon registry name (or anything `{% cv_icon %}` accepts), default `None`.
- `label_mode`: one of `LABEL_MODES`, default `"label"`. An invalid value raises `ValueError` at construction (a
  runtime argument cannot be seen by a system check; `cv_button_data()` raises the same way).
- `field_classes` comes from `get_button_class(location, slot, label_mode)`, so a mode key like `form:submit:icon`
  is read before `form:submit` (same lookup as `card:tertiary:icon`).
- The three classes render one new template, `crud_views/crispy/button.html` (plain path, no template pack), instead
  of crispy's `baseinput.html`. It keeps every attribute crispy renders today (`type` from `input_type`, `name`,
  `value`, `class`, `id`, `flat_attrs`) and renders the body with the rules of `action.html`:
  - `label`: `<span>{{ label }}</span>`.
  - `both`: icon, space, `<span>{{ label }}</span>`.
  - `icon`: icon plus `<span class="{% cv_button_class 'form' 'hidden-label' %}">{{ label }}</span>`, and
    `title="{{ label }}"` on the button (as `cv_button_data()` sets `cv_title` in icon mode).
  - No icon (`icon` is `None` or resolves to nothing): renders as `label` whatever the mode, so a button never ends up
    blank.
- `value` stays the label, so the submitted `submit=Save` / `delete=Delete` pair is unchanged.

Builder's choice: whether the shared body lives in a small include used by both `action.html` and the new template,
or the new template repeats the three branches. Prefer the include if it does not change `action.html`'s output
(its golden snapshots must stay byte-identical).

### Resolving the mode (view, ViewSet, setting)

Mirrors `cv_list_actions_label_mode` / `cv_context_actions_label_mode` (#216):

- Setting `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` in `CrudViewsSettings`, default `{}`.
- ViewSet field `form_actions_label_mode: dict[str, str] | None = None`, validated by the existing
  `check_label_mode_map` validator.
- View attribute `cv_form_actions_label_mode: dict[str, str] | None = None` on `CrudView`.
- `CrudView.cv_get_form_actions_label_mode()` resolves through `cv_first_inline_keys(..., "form_actions_label_mode")`,
  and `CrudView.cv_get_form_action_label_mode(key)` returns `mapping.get(key, "label")`.

**A key that is not named is `label`**, unlike context / list where it is `icon`. That is the "nothing configured looks
as today" goal.

### Wiring

- `CrispyFormMixin.submit_icon: str | None = "save"`.
- `get_submit_button_kwargs()` adds `icon=self.submit_icon` and
  `label_mode=self.cv_view.cv_get_form_action_label_mode("submit")`.
- `get_cancel_button_kwargs()` adds `icon="cancel"` and the `cancel` mode; `get_delete_button_kwargs()` adds
  `icon="delete"` and the `delete` mode.
- `ListViewFilterFormHelper` passes `icon="filter"` / `icon="reset"` and the `filter-submit` / `filter-reset` modes
  from `self.view`.

A form that overrides `get_submit_button_kwargs()` and returns a fresh dict (the pattern in the docs) drops the icon
and mode and gets a plain label button. That is acceptable and matches how its `name` / `value` override works today.
The docs show `{**super().get_submit_button_kwargs(), ...}` as the way to keep them.

### Icons

New registry keys in `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` (`lib/icons.py`):

| Key | `DEFAULT_ICONS` | `BOOTSTRAP_ICONS` |
|---|---|---|
| `save` | `far:floppy-disk` | `floppy` |
| `cancel` | `fas:xmark` | `x-lg` |
| `reset` | `fas:rotate-left` | `arrow-counterclockwise` |

The icon names are the builder's to adjust if one does not exist in the shipped Font Awesome / Bootstrap Icons
versions.

### Button classes (`lib/button_classes.py`)

- New default key `form:hidden-label` = `visually-hidden`, like `context:hidden-label`.
- The W362 check accepts `form:<slot>:<mode>` for the five form slots and a mode in `LABEL_MODES`. A wrong mode
  (`form:submit:iconn`) gets the "unknown label mode" W362 message; an unknown slot keeps the "not a known key" one.
  Today `_action_key_parts()` only knows the action locations and variants, so this is an extension of that check, not
  of `get_button_class()` (which already prefers a present mode key).

### System checks

- `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` joins the E106 loop in `CrudViewsSettings._action_settings_messages()`.
- `cv_form_actions_label_mode` gets E211 / W291 through `cv_label_mode_checks(cls, "cv_form_actions_label_mode",
  FORM_ACTION_KEYS)`, where `FORM_ACTION_KEYS` is the five keys above. The ViewSet field is covered by the existing
  validator.

## Breaking

`<input>` becomes `<button>` for all five buttons, with the label as element text. CSS, JS or tests that select
`input[type=submit]`, `input[type=button]` or `input[type=reset]`, or read the label from the `value` attribute only,
need updating; a project override of crispy's `baseinput.html` no longer affects these buttons. CHANGELOG
`### Breaking` entry and a section in `docs/migrating-1.0.md` (CLAUDE.md rule until 1.0.0).

## Documentation

- `docs/reference/settings.md`: the new setting row, next to the context / list label-mode rows.
- `docs/reference/buttons.md`: the five form keys and the mode keys, `form:hidden-label`, and the `icon=` /
  `label_mode=` constructor arguments for a project's own layouts.
- `docs/reference/action_menus.md` label-mode table (or wherever the three layers are described): the form row,
  with the different default called out.
- The icon key list wherever the registry keys are documented.
- `docs/migrating-1.0.md` and `CHANGELOG.md`.

## Example project

`examples/bootstrap5` sets `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE = {"submit": "both", "delete": "both", "cancel":
"both"}`, so the demo shows icon + text on form buttons while the filter stays text-only.

## Acceptance criteria

- With nothing configured, all five buttons render as `<button>` with the same text, classes, `name`, `value` and
  `id` as the `<input>` today, and the POST of a create, update, delete and workflow form is unchanged.
- `action.html` output is unchanged (existing goldens).
- In `both` mode each of the five buttons shows its icon and text; in `icon` mode the text is in the hidden-label span
  and in `title`.
- The workflow submit uses the `workflow` icon.
- Setting → ViewSet → view resolution works for each layer; an unnamed key is `label`.
- `form:submit:icon` in `CRUD_VIEWS_BUTTON_CLASSES` is used in icon mode and passes the checks; `form:submit:iconn`
  warns.
- E106, E211 and W291 fire for a bad setting / view attribute; `Submit(..., label_mode="x")` raises `ValueError`.
- A button with a mode but no icon renders as `label`.
- Cancel navigates when the click lands on its icon (vitest for `viewset.js`, if not already covered).
- Example project, docs, CHANGELOG and migration guide updated.

## Calls made in the design conversation

- Maintainer: every form button is in scope, the filter buttons included, with `label` as their mode in the stock
  setup.
- Maintainer: `Submit` / `Button` / `Reset` take `icon=` and `label_mode=` directly, default `label`, for layouts
  without a view.
- Claude's calls (approved with the issue): default `label`; cancel stays a JS button; the ViewSet layer exists for
  consistency; new icon keys `save`, `cancel`, `reset`.
- Claude's calls in this spec: invalid `label_mode` raises `ValueError`; a mode without an icon falls back to
  `label`; icon mode sets `title`; `form:hidden-label` as a new class key; the concrete icon names.
