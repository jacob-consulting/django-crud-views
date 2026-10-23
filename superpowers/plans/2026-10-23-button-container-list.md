# Button Container List Markup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Class-table keys that make the `context` / `list` / `card` button containers render their items as a
`<ul>`/`<li>` list, and render a lone item bare (no container).

**Architecture:** Nine new keys in `DEFAULT_BUTTON_CLASSES`, one pure resolver `get_container_layout()` in
`crud_views/lib/button_classes.py` plus check E364, one simple tag `cv_container_layout` that counts items, and
`tags/button/container.html` branching on the result. The three call sites are not touched.

**Tech Stack:** Django templates, pytest + pytest-django, lxml for HTML assertions.

**Spec:** `superpowers/specs/2026-10-23-button-container-list-design.md` (issue #261)

## Global Constraints

- Not breaking: with no new keys set, the containers render today's markup; `tests/test1/test_action_menus_golden.py`
  passes with the golden files unchanged (never regenerate them in this work).
- Locations: `context`, `list`, `card` only. `menu`, `formset`, `card-order` untouched.
- A bare lone item carries no `cv-<location>-container` marker.
- Item count = `len(cv_buttons) + (1 if cv_group and cv_group.menu else 0)`; count by data, never by rendered HTML.
- No changes to `context_actions.html`, `columns/actions.html`, `tags/card.html`, button leaves, or `get_button_class()`.
- No `### Breaking` entry; `docs/migrating-1.0.md` not touched.
- Never name downstream / client projects in code, docs, changelog or tests.
- Python 3.12+, Django 4.2/5.2/6.0, line length 120, double quotes, ruff.
- Run tests with `pytest tests -n auto`.

## Review Focus

- `container-list = ""` must still render a `<ul>` (no `class` attr), unlike `None` → Task 1 `test_layout_empty_list_class_is_list`, Task 2 `test_list_empty_class_renders_bare_ul`.
- One inline button **plus** a menu is two items: container stays → Task 2 `test_bare_one_button_plus_menu_keeps_container`.
- A hidden action must not count: two configured, one hidden → bare → Task 2 `test_bare_ignores_hidden_action`.
- No empty `<li>` when the group has no menu → Task 2 `test_list_no_menu_no_empty_li`.
- Zero items with `"bare"` set must not crash or vanish: empty container as today → Task 1 `test_layout_zero_items_never_bare`.

---

### Task 1: Keys, layout resolver and check E364

**Files:**
- Modify: `src/crud_views/lib/button_classes.py`
- Modify: `src/crud_views/checks.py:405-407` (docstring only: add E364)
- Test: `tests/test1/test_button_container_layout.py` (new), `tests/test1/test_button_classes_checks.py`

**Interfaces:**
- Produces:
  - `CONTAINER_SINGLE_MODES: tuple[str, ...] = ("container", "bare")`
  - `@dataclass(frozen=True) class ContainerLayout: list_class: str | None; item_class: str; bare: bool`
  - `get_container_layout(location: str, item_count: int) -> ContainerLayout`

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_button_container_layout.py` (reuse the
  `_isolate_registry` autouse fixture pattern from `test_button_classes_checks.py`):

```python
from crud_views.lib.button_classes import ContainerLayout, DEFAULT_BUTTON_CLASSES, get_container_layout

@pytest.mark.parametrize("loc", ["context", "list", "card"])
def test_defaults(loc):
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-list"] is None
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-item"] == ""
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-single"] == "container"
    assert get_container_layout(loc, 1) == ContainerLayout(list_class=None, item_class="", bare=False)

def test_layout_list_and_item():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-list": "x", "list:container-item": "y"}):
        assert get_container_layout("list", 2) == ContainerLayout("x", "y", False)

def test_layout_empty_list_class_is_list():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:container-list": ""}):
        assert get_container_layout("card", 2).list_class == ""

@pytest.mark.parametrize("count, bare", [(1, True), (2, False)])
def test_layout_bare_only_for_one(count, bare):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:container-single": "bare"}):
        assert get_container_layout("context", count).bare is bare

def test_layout_zero_items_never_bare():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:container-single": "bare"}):
        assert get_container_layout("context", 0).bare is False

@pytest.mark.parametrize("value", [None, "", "nonsense", 3])
def test_layout_invalid_single_means_container(value):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-single": value}):
        assert get_container_layout("list", 1).bare is False

def test_layout_non_str_list_is_no_list():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-list": 3}):
        assert get_container_layout("list", 2).list_class is None
```

  And in `tests/test1/test_button_classes_checks.py`:

```python
def test_e364_container_single_bad_value():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-single": "naked"}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.E364"]
    assert "'list:container-single'" in messages[0].msg
    assert "bare" in messages[0].hint and "container" in messages[0].hint

def test_container_keys_valid_no_messages():
    register_button_classes({"context:container-list": "", "context:container-item": "li",
                             "context:container-single": "bare", "card:container-single": None})
    assert check_button_classes() == []
```

  Also update the module docstring's id list to include E364.

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test1/test_button_container_layout.py tests/test1/test_button_classes_checks.py -v`
Expected: FAIL (ImportError on `ContainerLayout` / `get_container_layout`; E364 test fails).

- [ ] **Step 3: Implement**
  - Widen `DEFAULT_BUTTON_CLASSES` to `dict[str, str | None]`; add the nine keys next to the existing `*:container`
    entries with a one-line `# (#261)` comment.
  - `get_container_layout()`: read raw values from `get_button_classes()` (not `get_button_class()`, which collapses
    None and ""). `list_class` = the value if it is a str, else None. `item_class` = the value if str, else "".
    `bare` = `item_count == 1 and value of container-single == "bare"`.
  - In `button_class_check_messages()`, in the existing per-key loop: a str key ending `:container-single` whose
    value is a str other than "" and not in `CONTAINER_SINGLE_MODES` → `Error(id="crud_views.E364")`, msg names the
    key and value, hint lists both modes. None / "" pass silently (non-str is already E361).

- [ ] **Step 4: Run to verify they pass**

Run: `pytest tests/test1/test_button_container_layout.py tests/test1/test_button_classes_checks.py tests/test1/test_button_classes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/button_classes.py src/crud_views/checks.py tests/test1/test_button_container_layout.py tests/test1/test_button_classes_checks.py
git commit -m "feat(buttons): container-list/-item/-single class keys and E364 (#261)"
```

### Task 2: Container template renders list and bare markup

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (new tag next to `cv_actions_menu`)
- Modify: `src/crud_views/templates/crud_views/tags/button/container.html`
- Test: `tests/test1/test_button_container_list.py` (new)

**Interfaces:**
- Consumes: `get_container_layout(location, item_count) -> ContainerLayout` (Task 1).
- Produces: simple tag `{% cv_container_layout cv_location cv_buttons cv_group as cv_layout %}` →
  `ContainerLayout`; computes the item count per Global Constraints (`cv_buttons` may be empty, `cv_group` may be None).

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_button_container_list.py`. Use HTTP rendering with
  lxml like `test_action_menus_context.py` / `_list.py` / `_card.py` (monkeypatch `cv_context_actions`,
  `cv_context_actions_inline`, `cv_list_actions`, `cv_list_actions_inline`, `cv_card_actions`,
  `cv_card_actions_inline`; `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)`). `LIST = {"<loc>:container-list":
  "btn-list", "<loc>:container-item": "btn-item"}`.

  | Test | Setup | Assert |
  |---|---|---|
  | `test_list_markup[context\|list\|card]` | 2 inline actions, no menu, LIST | container (`fieldset`/`fieldset`/`div`) keeps its class and `cv-<loc>-container="true"`; its only element child is `ul.btn-list`; `ul` has 2 `li.btn-item` children, each with exactly one child carrying `cv-key` |
  | `test_list_menu_gets_own_li` | context, 1 inline + 2 menu items, LIST | 2 `li`; second `li` contains `.cv-menu-toggle` |
  | `test_list_no_menu_no_empty_li` | list, 2 inline, no menu, LIST | every `li` has an element child |
  | `test_list_empty_class_renders_bare_ul` | list, `container-list: ""` | `ul` present, `ul.get("class") is None`; `li.get("class") is None` |
  | `test_bare_single_button[context\|list\|card]` | 1 inline action, `container-single: "bare"` | no `[cv-<loc>-container]` element in the page region; the action element (`[cv-key]`) is present and its parent is the element that held the container before (the `td` for list) |
  | `test_bare_one_button_plus_menu_keeps_container` | context, 1 inline + 1 menu, bare | container present |
  | `test_bare_only_menu` | list, inline keys `[]`, 2 actions → all in menu, bare | no container; `.cv-menu-toggle` present |
  | `test_bare_ignores_hidden_action` | context on detail page, actions `["detail","update"]`, user with view only (`client_user_author_view`), bare | no container; one `[cv-key]` |
  | `test_bare_wins_over_list` | list, 1 inline, LIST + bare | no `ul`, no container |
  | `test_single_container_mode_keeps_container` | list, 1 inline, LIST, single default | container with `ul` + one `li` |
  | `test_standalone_context_button_never_li` | as `test_context_button_tag.py`: render `{% cv_context_button 'update' %}` with `context:container-list` set | output has no `<li` |

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test1/test_button_container_list.py -v`
Expected: FAIL (no `ul` / container still present), except `test_standalone_context_button_never_li` which passes already.

- [ ] **Step 3: Implement**
  - Tag `cv_container_layout(location, buttons, group) -> ContainerLayout` in `templatetags/crud_views.py`, docstring
    citing #261.
  - `container.html`: first line loads the tag into `cv_layout`. If `cv_layout.bare`: render the buttons loop and
    `cv_actions_menu` with nothing around them. Otherwise the outer element exactly as today; inside it, if
    `cv_layout.list_class is None` keep today's two lines unchanged, else
    `<ul{% if cv_layout.list_class %} class="…"{% endif %}>`, one `<li{% if cv_layout.item_class %} class="…"{% endif %}>`
    per button around `cv_render_button`, and `{% if cv_group.menu %}<li …>{% cv_actions_menu … %}</li>{% endif %}`.
    Use the same `cv_render_button` / `cv_actions_menu` calls as today; no other rendering path.

- [ ] **Step 4: Run to verify they pass, and that default markup is unchanged**

Run: `pytest tests/test1/test_button_container_list.py tests/test1/test_action_menus_golden.py -v`
Expected: PASS, golden files unmodified (`git status tests/test1/golden` clean).

Run: `pytest tests -n auto`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py src/crud_views/templates/crud_views/tags/button/container.html tests/test1/test_button_container_list.py
git commit -m "feat(buttons): list markup and bare lone item in button containers (#261)"
```

### Task 3: Docs and changelog

**Files:**
- Modify: `docs/reference/buttons.md` (key table around lines 69-71; container leaf row at line 242)
- Modify: `docs/reference/theme.md`
- Modify: `CHANGELOG.md` (Unreleased → `### Added`; create the heading after `### Breaking` if absent)

- [ ] **Step 1: Write docs**
  - `buttons.md`: add the nine keys with defaults under the `*:container` rows; a short subsection
    "Button row as a list" with the four-key table from the spec, the list markup example (two buttons + menu), the
    bare rule (one *rendered* item, menu counts as one, hidden actions don't count, zero items unchanged, no marker on
    a bare item), and E364. Mention `{% cv_context_button %}` never gets an `<li>`.
  - `theme.md`: a ~10-line recipe calling `register_button_classes({...})` for all three locations.
  - `CHANGELOG.md`: one Added bullet: the three keys per location, default off, `(#261)`.

- [ ] **Step 2: Verify**

Run: `task check && task format && mkdocs build --strict -q`
Expected: no errors (ruff also formats Markdown in CI).

- [ ] **Step 3: Commit**

```bash
git add docs/reference/buttons.md docs/reference/theme.md CHANGELOG.md
git commit -m "docs(buttons): container list keys and lone-item rule (#261)"
```
