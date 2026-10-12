# Action menus

Views with many actions render one button per action. An **action menu** keeps the actions you name as buttons and
folds all others into one dropdown (`⋯`) at the end of the group. It works in three places: list rows, the context
toolbar and cards.

!!! example "Try it live"
    The [Action Menus example](https://django-crud-views-demo.onrender.com/action-menus/chore/) in the live demo
    folds chore actions into `⋯` menus on the list, the toolbar and the cards — log in as `alice` / `alice` and as
    `bob` / `bob` to compare what each of them sees. See [Live demo](../getting_started/demo.md) for data resets
    and wake-up time.

```
List row:   [👁]  [⋯]                  Context:  [✏](active) [⋯]
                  ├ ✏ Edit
                  ├ 🗑 Delete   (disabled)
                  └ ⧉ Copy
```

## Configuration

Each location has an **inline keys** list:

| Level | List rows | Context toolbar | Cards |
|---|---|---|---|
| Django settings | `CRUD_VIEWS_LIST_ACTIONS_INLINE` | `CRUD_VIEWS_CONTEXT_ACTIONS_INLINE` | `CRUD_VIEWS_CARD_ACTIONS_INLINE` |
| `ViewSet` | `list_actions_inline` | `context_actions_inline` | `card_actions_inline` |
| `CrudView` | `cv_list_actions_inline` | `cv_context_actions_inline` | `cv_card_actions_inline` (card views) |

- `None` (default): no menu, every action is a button — today's markup, unchanged.
- `[]`: every action goes into the menu.
- `["detail"]`: `detail` stays a button, the rest go into the menu.

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down"]
    cv_list_actions_inline = ["detail", "up", "down"]  # update and delete go into the menu
```

Order: `CrudView` → `ViewSet` → setting; the first value that is not `None` wins, so `[]` on a view overrides a list
on its ViewSet. The getters `cv_get_list_actions_inline()`, `cv_get_context_actions_inline()` and
`cv_get_card_actions_inline()` return the result.

Actions added to a view later land in the menu automatically. Inline buttons keep their relative order, menu items
keep theirs. Cards match an inline key against `CardAction.key`, or `child_name` for child card actions. List rows
and the toolbar match the key as written in `cv_list_actions` / `cv_context_actions` (e.g. `"home"`, not its target
`"list"`).

### Resolved on the rendering view

The inline keys belong to the **container**, so they resolve on the view that renders the group: the list view for
its row actions and toolbar, the card view for its cards, the detail/update/… view for its own toolbar. This differs
from [hide or disable](inaccessible_actions.md), which resolves on each action's **target** view.

## What is never folded

- Context buttons with their own `template=` or `template_code=`: they render a whole button, which cannot become a
  dropdown item.
- The filter toggle of filtered list views (it has its own template).

`up` / `down` (ordered views) can be folded but are awkward in a menu — keep them inline.

## Hide and disable

[Inaccessible actions](inaccessible_actions.md) are resolved first, for every action:

- Hidden actions appear nowhere. If every menu action is hidden, no toggle is rendered.
- Disabled actions inside the menu render as `<button type="button" class="dropdown-item" disabled>` with
  `data-cv-disabled="permission|state"` and no URL or JS hooks. If every menu action is disabled, the toggle is still
  rendered — showing them is the point of disable mode.

## Labels, icons and the active action

Menu items show the target view's icon (fixed width, `fa-fw`) and a visible text label — the short action label
(`cv_action_short_label`), or `CardAction.label` on cards. Toolbar items carry the full label as `title`. A context button's own `label_template` / `label_template_code`
is also used as its menu item text.
`CardAction.variant`, `flex` and `no_label` apply to inline card buttons only.

On the context toolbar the current page's action is highlighted: inline with `.active`, inside the menu with
`.active` and `aria-current="page"`.

## Menu icon

`CRUD_VIEWS_ACTIONS_MENU_ICON` sets the toggle icon (default `"fa-solid fa-ellipsis"`).

## Templates

| Template | Renders |
|---|---|
| `crud_views/columns/actions.html` | list row container |
| `crud_views/tags/context_actions.html` | context toolbar container |
| `crud_views/tags/card.html` | card (`CardListView.cv_card_template`) |
| `crud_views/tags/actions_menu.html` | dropdown wrapper and item list |
| `crud_views/tags/actions_menu_toggle.html` | the toggle button only |
| `crud_views/tags/actions_menu_item.html` | one menu item |
| `crud_views/tags/actions_menu_item_label.html` | icon and label of an item |

Template variables of `actions_menu.html` / `actions_menu_toggle.html`: `cv_menu_items`, `cv_location`
(`"list"`, `"context"`, `"card"`), `cv_menu_wrapper_class`, `cv_toggle_class`, `cv_menu_icon`. A menu item gets the
action's resolved data (`cv_url`, `cv_key`, `cv_action_label`, `cv_action_short_label`, `cv_icon_action`,
`cv_disabled`, `cv_disabled_reason`, `cv_modal`, `cv_is_active`, …) plus `cv_location`.

For custom loops, the groups are available on the views: `cv_get_list_action_group(obj)`,
`cv_get_context_action_group(obj)`, `cv_get_card_action_group(obj)` return an `ActionGroup` (`inline`, `menu`,
`all`) or `None` when the menu is off.

### Example: a split-style toggle

Override `crud_views/tags/actions_menu_toggle.html` to show a caret instead of the icon. This suits only groups with
exactly one inline button — the caret reads as "options for the button on the left":

```django
{% load i18n %}
<button type="button" class="btn {{ cv_toggle_class }} dropdown-toggle dropdown-toggle-split"
        data-bs-toggle="dropdown" aria-expanded="false" aria-label="{% translate 'More actions' %}"
        {% if cv_location == "list" %}data-bs-popper-config='{"strategy":"fixed"}'{% endif %}>
    <span class="visually-hidden">{% translate "More actions" %}</span>
</button>
```

### Overridden containers

Projects that override `columns/actions.html`, `context_actions.html` or `card.html` keep their markup and do not get
the menu until they adopt the `{% if group is None %} … {% else %} … {% endif %}` structure of the package
templates.

## Bootstrap JavaScript and clipping

The menu is a Bootstrap 5 dropdown. The base template must load the Bootstrap **bundle** (`bootstrap.bundle.min.js`,
Popper included) — modals and the language selector already need it.

Row menus use Popper's fixed strategy (`data-bs-popper-config='{"strategy":"fixed"}'`), so they are not clipped by
a `.table-responsive` wrapper.

## System checks

| ID | Meaning |
|---|---|
| `crud_views.E105` | a `CRUD_VIEWS_*_ACTIONS_INLINE` setting is not `None` or a list of strings |
| `viewset.E208` | a `cv_*_actions_inline` attribute is not `None` or a list of strings |
| `viewset.W290` | a view's own `cv_*_actions_inline` names a key that is not among that location's actions (typo?) |

W290 checks only values set on the view class. ViewSet and setting values are shared defaults and may name keys some
views lack.
