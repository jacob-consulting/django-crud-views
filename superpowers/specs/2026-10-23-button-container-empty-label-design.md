# Button container: nothing when empty, configurable tag and translated label

Issues: #265, #266 (one branch, one PR).

Date: 2026-10-23

## Intent

`tags/button/container.html` renders the button group of the context toolbar, a list row and a card. Two problems
share its first line:

- **#265:** a group with no items still renders its element. A list row whose actions are all hidden for the user
  renders `<fieldset class="btn-group btn-group-xs" aria-label="Actions" cv-list-container="true"></fieldset>`. A
  screen reader announces an empty "Actions, group" on every such row; a theme that gives the container padding or a
  border draws an empty box.
- **#266:** the `aria-label="Actions"` is an English literal (not translated on a German page, although the
  catalogue has `msgid "Actions"`), and the element and its name are fixed by the three logic templates passing
  `cv_container_tag`. A theme can change neither without copying templates.

Both are fixed in the container leaf and in `get_container_layout()`, which #261 introduced for the container's
structure keys. The maintainer's focus words for this series apply: maintainability, low complexity, easy to theme
downstream, and no more upstream surface than the issues need.

## Goals

- A group with no rendered items renders nothing: no element, no `cv-<location>-container` attribute.
- The container's element is a class-table key per location; the label is a class-table key per location, rendered
  translated.
- With nothing configured and at least one item, the markup is byte-for-byte what it is today (English locale).

## Non-goals

- A label naming the row's object ("Actions for Douglas Adams"). It needs the object in the container's context;
  #266 lists it as a later step.
- `role="group"` or any other attribute that makes a label on a `div` meaningful. A theme that switches to `div`
  sets the label to `None` (documented).
- A system check on `container-tag` values (e.g. a valid element name). Possible follow-up, mentioned in the PR.
- The `menu`, `formset` and `card-order` containers.

## Anti-goals

- The same "is it empty?" condition in the three logic templates. It lives once, in the container leaf.
- `gettext_lazy` values in the class table. E361 rejects any non-str value, and loosening it for one key family is
  more surface than needed (see Label).

## Design

### Class table (`src/crud_views/lib/button_classes.py`)

Six new defaults next to the #261 container keys:

| Key | Default |
|---|---|
| `context:container-tag` | `"fieldset"` |
| `list:container-tag` | `"fieldset"` |
| `card:container-tag` | `"div"` |
| `context:container-label` | `gettext_noop("Actions")` (the str `"Actions"`) |
| `list:container-label` | `gettext_noop("Actions")` |
| `card:container-label` | `None` |

`gettext_noop` keeps the value a plain str (E361 stays as is) and keeps `"Actions"` in the catalogue through
`makemessages` independent of `lib/table/table.py`.

### Layout (`get_container_layout()`)

`ContainerLayout` grows three fields:

```python
empty: bool       # item_count == 0
tag: str          # location:container-tag; "div" when None, "" or not a str
label: str        # gettext(location:container-label); "" when None, "" or not a str
```

- **Label translation at render time:** the value is passed through `gettext()` when the layout is built, so the
  default `"Actions"` renders as `"Aktionen"` under `de`, and a project's own label is translated if the project's
  catalogue has it as a msgid. A project that wants a fixed wording just sets the string.
- **Tag fallback `"div"`:** builder's call — a neutral element without implicit semantics; `None` / `""` meaning "no
  element" would collide with `container-single: "bare"`, which already covers that.
- The tag is autoescaped in the template like every other class-table value; no validation beyond that (non-goal).

`{% cv_container_layout %}` already counts the inline buttons plus the menu toggle; `empty` uses that count, so a
group whose only item is the menu is not empty.

### Container leaf (`tags/button/container.html`)

```django
{% cv_container_layout cv_location cv_buttons cv_group as cv_layout %}
{% if cv_layout.empty %}{% elif cv_layout.bare %}…as today…{% else %}<{{ cv_layout.tag }} class="…"{% if cv_layout.label %} aria-label="{{ cv_layout.label }}"{% endif %} cv-{{ cv_location }}-container="true">…</{{ cv_layout.tag }}>{% endif %}
```

The label renders whatever the tag; the old `{% if cv_container_tag == "fieldset" %}` test goes away. The leaf no
longer reads `cv_container_tag`.

### Logic templates

`tags/context_actions.html`, `columns/actions.html` and `tags/card.html` drop `cv_container_tag=…` from their
`{% include %}`. No fallback: a value passed by a project's own logic-template override is ignored.

The hidden action forms (`{% cv_render_list_action_form %}`) these templates render before the container are not
touched; they render for menu/inline items, which an empty group does not have.

### Breaking (CHANGELOG `### Breaking` and `docs/migrating-1.0.md`)

- A group with no items renders nothing. JavaScript or CSS that expects `[cv-list-container]` (or the context / card
  attribute) in every row or toolbar must handle its absence.
- `cv_container_tag` is gone. The element comes from `<location>:container-tag`; a project override of
  `container.html` that reads `cv_container_tag` renders `<>` and must read `cv_layout.tag`. A logic-template override
  that passed another tag sets the key instead.
- The default label is translated: on a non-English page `aria-label` changes (e.g. `"Aktionen"`).

## Tests

- `get_container_layout()` unit tests (`tests/test1/test_button_container_layout.py`): `empty` for 0 / 1 / 2 items;
  tag default per location, from settings, fallback `"div"` for `None` / `""` / non-str; label default per location,
  `""` for `None` / `""` / non-str, `"Aktionen"` under `translation.override("de")`.
- Leaf tests: zero items (with and without an `ActionGroup`, any #261 keys) render `""`; a menu-only group still
  renders its container; tag and label from settings appear on the element; `None` label renders no `aria-label`;
  `div` card has no `aria-label` by default; German label through a view.
- Through the views: a list row whose actions are all hidden for the user has no `[cv-list-container]` in its cell.
- Existing tests that render the leaf with zero items to check the element
  (`test_button_leaves.py::test_container_div_has_no_aria_label`,
  `test_button_container_list.py::test_zero_items_render_as_today_whatever_the_keys`) change to non-empty groups or
  to the new expectation. They pass `cv_container_tag`, which is dropped. Goldens under `tests/test1/golden/` stay
  unchanged.

## Docs

- `docs/reference/buttons.md`: the two keys in the class table and in "Button row as a list"; the container leaf row
  (no `cv_container_tag`; reads tag and label from the layout); the empty rule; "a `div` container sets
  `container-label` to `None`".
- `docs/reference/action_menus.md` (line ~177) and `docs/migrating-1.0.md` (line ~256): drop `cv_container_tag`.
- `docs/reference/theme.md`: the list-theme example may set `container-tag` / `container-label` if it uses `div`.
- `CHANGELOG.md`: Breaking entries above, plus Added for the two keys.

## Left to the builder

- Exact test file placement and names.
- Whether the German `.mo` needs a recompile (the msgid exists; recompile only if `makemessages` changes the `.po`).
