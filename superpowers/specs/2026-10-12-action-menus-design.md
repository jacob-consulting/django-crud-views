# Overflow menu for list, context and card actions — design

- Issue: [#174](https://github.com/jacob-consulting/django-crud-views/issues/174)
- Date: 2026-10-12
- Status: draft (awaiting spec review)

## Goal

Views with many actions render one button per action. In each of the three action locations — list rows, the context
toolbar and cards — a project can name the actions that stay **inline** as buttons; every other action goes into one
Bootstrap dropdown (`⋯`) at the end of the group. With the default (`None`) nothing changes: the containers render the
same HTML as today.

- `None`: feature off, all buttons (default)
- `[]`: every foldable action goes into the menu
- `["detail"]`: `detail` stays a button, the rest go into the menu

Actions added to a view later land in the menu automatically. Inline buttons keep their relative order, menu items keep
theirs.

## Decisions (from brainstorming)

| Question | Decision |
|---|---|
| Scope of the "unknown inline key" warning | **View level only.** `viewset.W290` checks `cv_*_actions_inline` set on the view class. ViewSet and setting values are shared defaults; keys missing on some views are expected there. Type errors are checked on all three levels. |
| Delivery | **One PR** in this repo: package, tests, example app, docs, `de` catalog, CHANGELOG. The skill update (jacob-consulting/skills) and drift audit follow after merge. |
| Architecture | **Python resolver + branch in each container** (approach 1): a pure splitter, one group method per location, and an `{% if group is None %}` branch that keeps today's markup verbatim. |
| Toggle look | **`⋯` icon toggle** in a nested `.btn-group` (no caret, no split button). A split-style toggle only fits exactly one inline button and reads as "variants of the button on the left"; it is shown as a template override in the docs instead. |
| Toggle customization | **No style setting.** `CRUD_VIEWS_ACTIONS_MENU_ICON` swaps the icon; the toggle lives in its own small template (`actions_menu_toggle.html`) so a project overriding it copies ~5 lines and keeps the package's menu/item markup. |
| Disabled menu items | **`<button type="button" class="dropdown-item" disabled>`** for every disabled item, GET included. Deviates from the issue (`<a class="dropdown-item disabled" aria-disabled="true">`): PR #176 replaced exactly that anchor pattern after SonarQube flagged it. |
| Toggle corner rounding | The toggle carries `.dropdown-toggle` (so Bootstrap's button-group radius rules exclude it) plus `.cv-menu-toggle`; one package CSS rule hides the caret. Without `.dropdown-toggle`, the `<ul>` after the button makes it `:not(:last-child)` and Bootstrap squares its right corners (measured in the mockup). |

## Background: current state (verified in code)

- **Containers** (`src/crud_views/templates/crud_views/`):
  - `columns/actions.html` (tables2 `ActionColumn`): loops `view.cv_list_actions` twice — `cv_list_action_form`
    (hidden POST forms) then `cv_list_action` inside `<fieldset class="btn-group btn-group-xs">`.
  - `tags/context_actions.html` (inclusion tag `cv_context_actions`): loops `view.cv_context_actions`, calls
    `cv_context_action` inside `<fieldset class="btn-group btn-group-lg">`.
  - `tags/card.html` (rendered by `cv_card`, template overridable via `CardListView.cv_card_template`): loops
    `view.cv_card_actions`, calls `cv_card_action` inside `<div class="d-flex gap-2">`. `card_action.html` renders its
    own hidden POST form.
- **Per-item tags** each build and resolve one action: `cv_get_context()` → `cv_resolve_action()` (#149) → template.
  `cv_card_action` builds its data itself (key actions via the target's `cv_get_dict`; child actions from the child
  view class).
- **Match keys:** the configured key (entry in `cv_list_actions` / `cv_context_actions`) is not always the resolved
  data's `cv_key` — e.g. the default `ContextButton(key="home", key_target="list")` resolves to `cv_key="list"`. Inline
  matching therefore uses the configured key, not `cv_key`.
- **Custom context-button templates:** every context entry carries `cv_template` — the default
  `crud_views_settings.context_button_template` unless the button sets `template` / `template_code`.
  `FilterContextButton` sets its own template (`context_action_filter.html`).
- **JS hooks are delegated** (`$(document).on("click", "[data-cv-action='submit-form']" …)` in `viewset.js`,
  `[data-cv-modal='true']` in `modal.js`), so they fire from inside an open menu.
- **Bootstrap:** the example loads Bootstrap 5.3.3 `bootstrap.bundle.min.js` (Popper included) via django-bootstrap5,
  and Font Awesome 6.7.2. `btn-xs` / `btn-group-xs` are not Bootstrap classes and have no package CSS.
- **Package CSS:** `static/crud_views/css/table.css` is registered through `cv_css`.
- **Resolution precedent:** `CrudView.cv_get_inaccessible_actions()` (view → ViewSet → setting) tests truthiness; the
  inline getters must test `is not None` because `[]` is meaningful.
- **Check IDs in use:** settings `crud_views.E100–E104`; view `viewset.E200–E207` (E203 retired, do not reuse),
  `E250–E255`, `E260–E262`, `W270`, `W280`.

## Design

### 1. Configuration and resolution

**Settings** (`CrudViewsSettings`, `src/crud_views/lib/settings.py`):

| Field | Django setting | Default |
|---|---|---|
| `list_actions_inline` | `CRUD_VIEWS_LIST_ACTIONS_INLINE` | `None` |
| `context_actions_inline` | `CRUD_VIEWS_CONTEXT_ACTIONS_INLINE` | `None` |
| `card_actions_inline` | `CRUD_VIEWS_CARD_ACTIONS_INLINE` | `None` |
| `actions_menu_icon` | `CRUD_VIEWS_ACTIONS_MENU_ICON` | `"fa-solid fa-ellipsis"` |

The three inline fields are typed `Any` and validated by a new settings check **`crud_views.E105`** (error): each must
be `None` or a list/tuple of strings. This mirrors E104 for `CRUD_VIEWS_INACCESSIBLE_ACTIONS` and gives a check message
instead of a pydantic error at import.

**ViewSet** (`src/crud_views/lib/viewset/__init__.py`): `list_actions_inline`, `context_actions_inline`,
`card_actions_inline: list[str] | None = None`. Pydantic validates them at construction, like `inaccessible_actions`.

**CrudView:**

- `cv_list_actions_inline: list[str] | None = None` and `cv_context_actions_inline: list[str] | None = None` on the
  `CrudView` base, next to `cv_list_actions` / `cv_context_actions`.
- `cv_card_actions_inline: list[str] | None = None` on `CardListView`, next to `cv_card_actions`.
- Classmethods `cv_get_list_actions_inline()`, `cv_get_context_actions_inline()`, `cv_get_card_actions_inline()`:
  first value that **is not None** of view attribute → ViewSet field → setting.

**Where it resolves:** on the view that **renders** the group — the list view for its row actions and toolbar, the card
view for its cards, the detail/update/… view for its own toolbar. #149's hide/disable mode still resolves on each
action's **target** view, through `cv_resolve_action`, before any split.

**Checks:**

| ID | Level | Condition |
|---|---|---|
| `crud_views.E105` | settings, error | an inline setting is not `None` or a list/tuple of strings |
| `viewset.E208` | view, error | a `cv_*_actions_inline` set on the class is not `None` or a list/tuple of strings |
| `viewset.W290` | view, warning | a key in the class's own `cv_*_actions_inline` is not among that location's actions |

W290 compares against `cv_list_actions` (list rows), `cv_context_actions` (toolbar), and `CardAction.key`, or
`child_name` for child actions (cards). It checks only the attribute as set on the class (not the resolved value) and
never ViewSet or setting values. The new attributes are declared on the classes, so W280 (unknown attributes) does not
flag them.

### 2. Splitter, group methods, tags

**Pure splitter** — new module `src/crud_views/lib/view/action_menu.py`:

```python
@dataclass
class ActionGroup:
    inline: list[dict]
    menu: list[dict]

    @property
    def all(self) -> list[dict]:  # inline + menu, for the hidden POST form loop
        return [*self.inline, *self.menu]


def cv_split_actions(
    items: list[tuple[str, dict]],
    inline_keys: Sequence[str] | None,
    foldable: Callable[[dict], bool] | None = None,
) -> ActionGroup | None: ...
```

- `items` are `(match_key, resolved_ctx)` pairs; callers have already run `cv_resolve_action` and dropped hidden
  actions.
- Returns `None` when `inline_keys is None`.
- An item is inline when `match_key in inline_keys` or `foldable` is given and returns `False`; otherwise it goes to
  the menu. Both lists keep input order. Disabled items are split like any other.
- Pure: no request, no view, no mutation of the dicts.

**Foldable rule (context toolbar only):** an entry is not foldable when `cv_template_code` is set or `cv_template`
differs from `crud_views_settings.context_button_template`. This keeps custom buttons and the filter toggle inline
with no special case. List rows and cards always render through their own item templates, so all their items are
foldable.

**Group methods** — each returns `None` immediately when the resolved inline value is `None`, without building any
action data, so the default path costs nothing extra:

- `CrudView.cv_get_list_action_group(obj)` — over `cv_list_actions`: `cv_get_context(key, obj, user, request)` →
  `cv_resolve_action`; skips keys raising `ViewSetKeyFoundError` and empty/hidden results, as the tags do today.
- `CrudView.cv_get_context_action_group(obj=None)` — the same over `cv_context_actions`; `obj` defaults to
  `self.object` like `cv_get_context_buttons()`; passes the foldable rule.
- `CardListView.cv_get_card_action_group(obj)` — over `cv_card_actions`, match key `action.key or action.child_name`.
  The data building moves out of the `cv_card_action` tag into
  `CardListView.cv_get_card_action_data(action, obj, user) -> dict` (unresolved data), which the existing tag also
  calls, so inline and menu items cannot drift apart.

**Template tags** (`src/crud_views/templatetags/crud_views.py`):

| Tag | Kind | Purpose |
|---|---|---|
| `{% cv_list_action_group record as group %}` | simple tag | group for a list row |
| `{% cv_card_action_group object as group %}` | simple tag | group for a card |
| `cv_context_actions` (existing) | inclusion tag | additionally puts `group` into its context |
| `cv_render_list_action ctx` | simple tag | renders resolved data with `list_action.html` |
| `cv_render_list_action_form ctx` | simple tag | renders `list_action_form.html`; nothing for disabled data |
| `cv_render_card_action ctx` | simple tag | renders resolved data with `card_action.html` |
| `cv_render_context_button ctx` (existing) | simple tag | already renders resolved context data |
| `cv_actions_menu group location` | inclusion tag | renders `actions_menu.html` with the menu items |
| `cv_render_menu_item ctx location` | simple tag | renders one resolved item with `actions_menu_item.html` (the dict's keys become the template context, plus `cv_location`) |

In group mode each list-row key is resolved once; today `cv_list_action_form` and `cv_list_action` each resolve it.

### 3. Templates and markup

**Containers** open with the group tag and branch on `{% if group is None %}`; that branch is today's markup unchanged.

- `columns/actions.html` group branch: hidden POST forms for `group.all` (via `cv_render_list_action_form`) before
  the fieldset; inside the fieldset the inline items (`cv_render_list_action`) followed by the menu.
- `tags/context_actions.html` group branch: inline items (`cv_render_context_button`), then the menu. The outer
  `{% if view.cv_context_actions %}` guard stays.
- `tags/card.html` group branch: inline items (`cv_render_card_action`; inline POST cards keep rendering their own
  form, unchanged); hidden forms for POST menu items (`cv_render_list_action_form`) before the dropdown; then the
  menu.

The menu is rendered only when `group.menu` is non-empty. A menu whose items are all disabled is rendered.

**Overridable menu templates:**

- `tags/actions_menu.html` — wrapper + list, includes the toggle template:

  ```html
  {% load crud_views %}
  <div class="{{ cv_menu_wrapper_class }}" {% if cv_location != "card" %}role="group"{% endif %}>
      {% include "crud_views/tags/actions_menu_toggle.html" %}
      <ul class="dropdown-menu dropdown-menu-end">
          {% for item in cv_menu_items %}<li>{% cv_render_menu_item item cv_location %}</li>{% endfor %}
      </ul>
  </div>
  ```

  `cv_menu_wrapper_class` is `btn-group` for list rows and the toolbar (Bootstrap's nested button group, so borders
  join the inline buttons) and `dropdown` for cards (`d-flex gap-2`, not a button group).

- `tags/actions_menu_toggle.html` — the button only:

  ```html
  {% load i18n %}
  <button type="button" class="btn {{ cv_toggle_class }} dropdown-toggle cv-menu-toggle"
          data-bs-toggle="dropdown" aria-expanded="false" aria-label="{% translate 'More actions' %}"
          {% if cv_location == "list" %}data-bs-popper-config='{"strategy":"fixed"}'{% endif %}>
      <i class="{{ cv_menu_icon }}" aria-hidden="true"></i><span class="visually-hidden">{% translate "More actions" %}</span>
  </button>
  ```

  `cv_toggle_class`: `btn-outline-primary btn-xs` (list), `btn-outline-primary btn-lg` (toolbar),
  `btn-secondary btn-sm` (cards) — the classes of the neighbouring buttons. `cv_menu_icon` is the
  `actions_menu_icon` setting. Row menus always use Popper's fixed strategy so they escape `.table-responsive`
  clipping; whether the toolbar or cards need it too is verified in the example.

- `tags/actions_menu_item.html` — one template for all locations:

  | Item | Markup |
  |---|---|
  | disabled (any method) | `<button type="button" class="dropdown-item" disabled data-cv-disabled="{{ cv_disabled_reason }}">` — no URL, no `data-cv-action`, no `data-cv-modal` |
  | POST, not modal (list/card) | `<button type="button" class="dropdown-item" data-cv-action="submit-form" data-cv-target="cv_form_{{ cv_oid }}">` |
  | modal | `<a class="dropdown-item" href="{{ cv_url }}" data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}">` |
  | GET | `<a class="dropdown-item{% if cv_is_active %} active{% endif %}" href="{{ cv_url }}"{% if cv_is_active %} aria-current="page"{% endif %}>` |

  Every item keeps `cv-key="{{ cv_key }}"`. Content: icon `<i class="{{ cv_icon_action }} fa-fw" aria-hidden="true">`,
  or an empty `<span class="fa-fw d-inline-block"></span>` spacer, then a visible label:

  - cards: `cv_label` (`CardAction.label` or the target's short label)
  - list rows and toolbar: `cv_action_short_label`, falling back to `cv_action_label`
  - toolbar items additionally get `title="{{ cv_action_label }}"`

  `CardAction.variant`, `flex` and `no_label` apply to inline card buttons only.

**CSS** — one rule added to `static/crud_views/css/table.css`:

```css
.cv-menu-toggle.dropdown-toggle::after { display: none; }
```

`.dropdown-toggle` is kept on the toggle because Bootstrap's button-group rule
`.btn-group > .btn:not(:last-child):not(.dropdown-toggle)` would otherwise square its right corners (the `<ul>`
follows the button).

**i18n:** "More actions" → `de`: "Weitere Aktionen".

**JS:** no changes. Bootstrap closes the menu on item click; the delegated handlers fire inside it (verified in the
browser, see Testing).

**Bootstrap requirement:** the project's base template must load the Bootstrap JS bundle (Popper included) — already
required by modals and the language selector. Documented, no new dependency.

## Testing

Package tests in `tests/test1/`:

- **Splitter** (`cv_split_actions`): `None` → `None`; `[]` folds all; `["key"]`; unknown keys ignored; order kept on
  both sides; foldable predicate keeps items inline under `[]`; disabled items are split like others; input dicts not
  mutated.
- **Regression (golden):** with all inline values `None`, list rows, context toolbar and cards (including child card
  actions, POST and modal actions, disable mode) render the same HTML as before the change, compared after whitespace
  normalization. Golden files are captured from `main` before the container templates change.
- **Resolution:** view → ViewSet → setting; `[]` on a higher level beats a non-`None` lower level; resolves on the
  rendering view (two views of one ViewSet with different `cv_context_actions_inline`).
- **Hide/disable:** hidden actions never appear; no toggle when the menu would be empty; disabled menu items have no
  `href` / `data-cv-action` / `data-cv-modal` and carry `data-cv-disabled`; toggle rendered when all menu items are
  disabled.
- **Rendering:** POST menu item targets an existing hidden form; no form for disabled items; modal attributes kept;
  active toolbar item has `.active` and `aria-current="page"`, inline active button keeps `.active`; custom-template
  context buttons and the filter toggle stay inline under `[]`; card menu items use `CardAction.label` and ignore
  `variant` / `flex` / `no_label`; child card actions fold by `child_name`.
- **Checks:** `crud_views.E105`, `viewset.E208`, `viewset.W290` (positive and negative, W290 not raised for ViewSet or
  setting values).

Browser verification (Playwright, on the example app):

- POST and modal actions fire from inside an open menu; the menu closes.
- Last-row menus in the responsive table are not clipped.
- Toggle corner rounding correct (computed `border-*-radius`), caret hidden.
- Screenshot of a list row and a context toolbar with the menu open, for the docs.

## Example app

New app `examples/bootstrap5/action_menus/` (bootstrap5), following the other example apps (models, seed, urls, views,
tests, migrations):

- A model with ~8 row actions: detail, update, delete, two `ActionView`s (one POST, one modal), up/down
  (`OrderedUpView` / `OrderedDownView`), a child list.
- List view with `cv_list_actions_inline = ["detail", "up", "down"]`, rendered with a **responsive table**
  (tables2 `bootstrap5-responsive.html` or equivalent), covering the clipping fix.
- Detail view with `cv_context_actions_inline = ["update"]`, so the active state shows inline (on update) and in the
  menu (on detail).
- Card view with `cv_card_actions_inline` keeping a `variant="primary"` card action inline and child card actions in
  the menu.
- One target view with `cv_inaccessible_actions = "disable"` and a seeded demo user without that permission, showing
  disabled menu items.
- Page-marker tests and `de` translations (example catalog).

## Documentation

- New page `docs/reference/action_menus.md`: configuration table and resolution order (rendering view vs. #149's
  target view); what is never folded; interaction with hide/disable; template variables and the overridable templates
  (containers, `actions_menu.html`, `actions_menu_toggle.html`, `actions_menu_item.html`), including a split-style
  toggle override example with the note that it suits exactly one inline button; clipping / popper note; Bootstrap JS
  bundle requirement; "overridden containers" note — projects that override `columns/actions.html`,
  `context_actions.html` or `card.html` won't get the menu until they adopt the group branch.
- Cross-links from `list_view.md`, `context_buttons.md`, `card-list-view.md`, `inaccessible_actions.md`,
  `settings.md`; `mkdocs.yml` nav entry; checks reference lists E105 / E208 / W290.
- Screenshot from the browser verification.

## Changelog and delivery

- One PR from branch `action-menus-174`; CHANGELOG entry under Unreleased (feature, new settings, new checks).
- `.superpowers/` added to `.gitignore` in the same PR (brainstorming mockups).
- After merge: update the `django-crud-views` skill in jacob-consulting/skills (three locations, config levels and
  resolution, never-folded rules, new checks) and re-run the skill drift audit.

## Out of scope

- Manual placement tags `cv_context_button`, `cv_context_url`, `cv_get_context_buttons()` — unchanged; custom loops can
  build their own menu from `cv_get_context_buttons()`.
- Workflow transitions (`crud_views_workflow`) and `ObjectDetailView`.
- A toggle that shows the current action's label; an "auto" fold threshold; a menu style setting.
- `up` / `down` stay foldable; the docs recommend keeping them inline.
