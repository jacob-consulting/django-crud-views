# Icon Host Placement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Icon libraries with `placement: "host"` put the icon's class on the context / list / card button, the menu
item, the menu toggle and the filter toggle instead of rendering an `<i>` inside them (#258).

**Architecture:** `icons.py` learns two library keys (`placement`, `standalone`) and exposes the bare name class of a
host icon. `button_classes.py` gets four `*:icon-host` slots and one helper that formats a slot with that name class.
`cv_button_data()` puts the result into two new leaf keys; the leaves and the two toggle templates read them (or the
new `{% cv_icon_class %}` tag). `list.filter.js` swaps classes on the button for a host library.

**Tech Stack:** Django templates, Python 3.12+, pytest (+ xdist), vitest (Node 22), MkDocs.

**Spec:** `superpowers/specs/2026-10-23-icon-host-placement-design.md`

## Global Constraints

- Without a host library every template renders byte-for-byte what it renders today; all existing goldens and tests
  stay green unchanged, except hand-built leaf-contract dicts in tests, which gain `"cv_icon_inline": True`.
- Library keys: `placement` = `"element"` (default) | `"host"`; `standalone` default `"{name_class}"`, only read for
  a host library. `host` is valid only with the `font` renderer.
- Class-table slots `context:icon-host`, `list:icon-host`, `card:icon-host`, `menu:icon-host`, default
  `"{name_class}"`; `None` / `""` switches the icon off at that location (no class, no inline icon).
- `label` mode: no host class on an action button (menu items ignore label mode, as today).
- Filter toggle uses host rendering only when both `filter` and `filter-close` are host icons.
- `actions_menu_item_label.html` (legacy) is not touched.
- Not breaking: CHANGELOG `### Added`; `docs/migrating-1.0.md` is still updated (maintainer's request).
- No downstream / client project names in any file. Line length 120, double quotes.
- Branch `feat/icon-host-placement`, in place (no worktree), one commit per task. Run Python tests with
  `pytest tests -n auto`; JS with `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run`.

## Review Focus

1. A `both`-mode button whose action has no icon (`cv_icon` None) with a host library active: no stray class, no
   leading space, label renders as today. → Task 3 test `test_host_both_mode_without_icon`.
2. One page mixing a host icon and a `fas:` / raw-class icon (e.g. a project icon override): each button decides on
   its own. → Task 3 test `test_host_mixed_page_keeps_element_icons_inline`.
3. Disabled host button keeps `disabled`, `data-cv-disabled` and gets the class. → Task 3
   `test_host_disabled_button_keeps_class`.
4. `{% cv_icon value css="me-2" %}` on a host library still appends `css` after the standalone classes. → Task 1
   `test_host_standalone_with_css`.
5. An `*:icon-host` slot set to `None` drops both the class and the inline icon. → Task 3
   `test_host_slot_none_switches_icon_off`.

---

### Task 0: Branch

- [ ] **Step 1:** Commit this plan on `main` (`git add superpowers/plans/2026-10-23-icon-host-placement.md && git
  commit -m "docs(plan): icon host placement (#258)"`), then `git checkout -b feat/icon-host-placement`.

### Task 1: Library keys `placement` / `standalone`

**Files:**
- Modify: `src/crud_views/lib/icons.py` (`font_renderer`, new helper, `_library_check_messages`)
- Test: `tests/test1/test_icons_registry.py`, `tests/test1/test_icons_checks.py`

**Interfaces:**
- Produces: `resolve_icon_name_class(value: str | None) -> str | None` in `crud_views.lib.icons` — the formatted
  `class` of a host icon; `None` for empty values, raw classes, unknown prefixes, non-dict configs, element libraries,
  non-`font` renderers, unusable `class`.

Shared test constant (put in each test module that needs it, or a small helper module `tests/lib/helper/icons.py`):

```python
HOST_LIBRARY = {"ui": {"renderer": "font", "class": "icon-{name}", "placement": "host", "standalone": "icon {name_class}"}}
```

- [ ] **Step 1: Write failing tests** in `test_icons_registry.py` (use `override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY)`):

```python
def test_host_standalone_renders_standalone_classes():
    assert render_icon("ui:check") == '<i class="icon icon-check" aria-hidden="true"></i>'

def test_host_standalone_with_css():
    assert render_icon("ui:check", css="me-2") == '<i class="icon icon-check me-2" aria-hidden="true"></i>'

def test_host_standalone_default_is_name_class():  # library without "standalone"
    ...  # {"ui": {"renderer": "font", "class": "icon-{name}", "placement": "host"}}
    assert render_icon("ui:check") == '<i class="icon-check" aria-hidden="true"></i>'

def test_element_library_ignores_standalone():  # placement absent, standalone set
    assert render_icon("ui:check") == '<i class="icon-check" aria-hidden="true"></i>'

def test_resolve_icon_name_class():
    assert resolve_icon_name_class("ui:check") == "icon-check"
    assert resolve_icon_name_class("fas:check") is None      # element library
    assert resolve_icon_name_class("fa-solid fa-x") is None  # raw class
    assert resolve_icon_name_class("zz:check") is None       # unknown prefix
    assert resolve_icon_name_class(None) is None
    # semantic name via CRUD_VIEWS_ICONS={"detail": "ui:eye"}
    assert resolve_icon_name_class("detail") == "icon-eye"
```

In `test_icons_checks.py` (ids by the existing `ids()` helper):

```python
def test_e355_unknown_placement():           # placement="inline" -> "crud_views.E355"
def test_e355_host_needs_font_renderer():    # renderer=<callable>, placement="host" -> "crud_views.E355"
def test_e354_standalone_not_str():          # standalone=5 -> "crud_views.E354"
def test_e354_standalone_bad_placeholder():  # standalone="icon {name}" -> "crud_views.E354"
def test_host_library_ok():                  # HOST_LIBRARY -> no messages
```

- [ ] **Step 2:** `pytest tests/test1/test_icons_registry.py tests/test1/test_icons_checks.py -n auto` → new tests FAIL.
- [ ] **Step 3: Implement.** In `font_renderer`, when `config.get("placement") == "host"`, format `standalone`
  (default `"{name_class}"`) with `name_class=<formatted class>`; an unusable `standalone` renders `SafeString("")`.
  Add `resolve_icon_name_class` next to `render_icon`, reusing `resolve_icon` and `get_libraries()`. In
  `_library_check_messages`: validate `placement` (E355, also for non-font renderers with `host`), then for `font` +
  `host` validate `standalone` with `.format(name_class="x")` (E354, hint names `{name_class}` as the only
  placeholder).
- [ ] **Step 4:** Same command → PASS; then `pytest tests -n auto` → all green.
- [ ] **Step 5:** Commit `feat(icons): host placement and standalone class for font libraries (#258)`.

### Task 2: `*:icon-host` slots, helper and `{% cv_icon_class %}`

**Files:**
- Modify: `src/crud_views/lib/button_classes.py`, `src/crud_views/templatetags/crud_views.py`
- Test: `tests/test1/test_button_classes.py`, `tests/test1/test_button_classes_checks.py`, `tests/test1/test_icons_tag.py`

**Interfaces:**
- Consumes: `resolve_icon_name_class` (Task 1).
- Produces: `get_icon_host_class(location: str, value: str | None) -> str` in `crud_views.lib.button_classes` — the
  `location:icon-host` slot formatted with the icon's name class; `""` when the icon is not a host icon, the slot is
  `None`/`""`/non-str, or the slot is not a valid format string. Template tag
  `{% cv_icon_class value location %}` (simple_tag, supports `as var`) returning the same string.

- [ ] **Step 1: Failing tests.**

```python
# test_button_classes.py, with HOST_LIBRARY and CRUD_VIEWS_ICONS={"update": "ui:edit"}
def test_icon_host_default_slots():
    for location in ("context", "list", "card", "menu"):
        assert DEFAULT_BUTTON_CLASSES[f"{location}:icon-host"] == "{name_class}"

def test_get_icon_host_class():
    assert get_icon_host_class("context", "update") == "icon-edit"
    assert get_icon_host_class("context", "fas:pen") == ""
    assert get_icon_host_class("context", None) == ""

def test_get_icon_host_class_with_base():  # CRUD_VIEWS_BUTTON_CLASSES={"card:icon-host": "icon {name_class}"}
    assert get_icon_host_class("card", "update") == "icon icon-edit"

def test_get_icon_host_class_slot_none():  # {"menu:icon-host": None}
    assert get_icon_host_class("menu", "update") == ""

# test_button_classes_checks.py
def test_e363_icon_host_bad_placeholder():  # {"list:icon-host": "{name}"} -> "crud_views.E363"
def test_icon_host_none_is_valid():         # {"list:icon-host": None} -> no E363, no W362

# test_icons_tag.py
def test_cv_icon_class_tag():
    # "{% load crud_views %}{% cv_icon_class 'update' 'context' %}" -> "icon-edit"; "detail" (fas) -> ""
```

- [ ] **Step 2:** Run the three files → new tests FAIL.
- [ ] **Step 3: Implement.** Four `"{name_class}"` entries in `DEFAULT_BUTTON_CLASSES` (comment: the class a host
  icon adds to that location's button, #258). `get_icon_host_class` imports `resolve_icon_name_class` from `.icons`
  (icons never imports button_classes). E363 in `button_class_check_messages`: a str `*:icon-host` value whose
  `.format(name_class="x")` raises. Tag `cv_icon_class` beside `cv_icon` in `templatetags/crud_views.py`.
- [ ] **Step 4:** Same tests → PASS; `pytest tests -n auto` green.
- [ ] **Step 5:** Commit `feat(buttons): icon-host class slots and cv_icon_class tag (#258)`.

### Task 3: Leaf contract and the two button leaves

**Files:**
- Modify: `src/crud_views/lib/view/button_data.py`, `src/crud_views/templatetags/crud_views.py` (`cv_button`),
  `src/crud_views/templates/crud_views/tags/button/action.html`, `.../button/menu_item.html`,
  `.../button/menu_item_label.html`
- Test: `tests/test1/test_button_data.py`, `tests/test1/test_button_leaves.py`; add `"cv_icon_inline": True` to the
  hand-built contract dicts (`_context_get` in `test_button_leaves.py`, `_leaf_contract` in
  `test_button_classes_templates.py`, any other — `grep -rn '"cv_flex"' tests`).

**Interfaces:**
- Consumes: `get_icon_host_class` (Task 2).
- Produces: `cv_button_data(ctx: dict, location: str, kind: str = "action") -> dict` with two more keys in the result
  and in `LEAF_KEYS`: `cv_icon_class: str`, `cv_icon_inline: bool`. `kind="menu-item"` uses the `menu` slot and
  ignores label mode; `kind="action"` uses `location` and gives `""` in `label` mode. `cv_icon_inline` is `False`
  whenever the icon is a host icon (even when its slot formats to `""`), else `True`.
  `cv_button` passes its `kind` through.

- [ ] **Step 1: Failing tests** (host library + `CRUD_VIEWS_ICONS={"detail": "ui:eye", "update": "ui:edit"}`):

```python
# test_button_data.py
@pytest.mark.parametrize("location", LOCATIONS)
def test_host_icon_keys(location):
    data = cv_button_data(base(cv_icon_action="detail"), location)
    assert data["cv_icon_class"] == "icon-eye" and data["cv_icon_inline"] is False

def test_element_icon_keys():          # default table: cv_icon_class == "", cv_icon_inline is True
def test_host_label_mode_no_class():   # card, cv_label_mode="label" -> cv_icon_class == ""
def test_menu_item_uses_menu_slot():   # {"menu:icon-host": "m {name_class}"}, kind="menu-item", label mode "label"
    #                                    -> "m icon-eye"
def test_host_slot_none_switches_icon_off():  # {"context:icon-host": None} -> ("", False)
```

```python
# test_button_leaves.py, full render through the views or render_to_string(ACTION_LEAF, cv_button_data(...))
def test_host_icon_mode():   # <a class="... icon-eye" title=...><span class="visually-hidden">Details</span></a>, no <i>
def test_host_both_mode():   # class ends with "icon-eye"; body is exactly "<span>Details</span>"
def test_host_label_mode():  # no icon-eye anywhere, body "<span>Details</span>"
def test_host_both_mode_without_icon():               # cv_icon_action None: class has no trailing space, body as today
def test_host_disabled_button_keeps_class():          # <button disabled data-cv-disabled=... class="... icon-eye">
def test_host_mixed_page_keeps_element_icons_inline() # one "fas:" action -> <i>, one host -> class, same container
def test_host_menu_item():   # class "dropdown-item icon-eye", no <i>, no cv-icon-fw span, label text kept
```

- [ ] **Step 2:** Run both files → FAIL.
- [ ] **Step 3: Implement.** `cv_button_data` computes the two keys (resolve once via `resolve_icon_name_class` to
  know host vs element, then `get_icon_host_class`). Templates:
  - `action.html`: `{% if cv_icon_class %} {{ cv_icon_class }}{% endif %}` at the end of `class="…"`; wrap each
    `{% cv_icon cv_icon %}` (and in `both` the following space) in `{% if cv_icon_inline %}`.
  - `menu_item.html`: same class append; `menu_item_label.html`: icon or `cv-icon-fw` placeholder only when
    `cv_icon_inline`; when not inline, render just the label without a leading space.
- [ ] **Step 4:** Run both files → PASS; `pytest tests -n auto` → all green, goldens untouched (`git status
  tests/test1/golden` clean).
- [ ] **Step 5:** Commit `feat(buttons): host-placed icons in the action and menu-item leaves (#258)`.

### Task 4: Menu toggle and filter toggle

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/actions_menu_toggle.html`,
  `src/crud_views/templates/crud_views/tags/context_action_filter.html`, `src/crud_views/static/crud_views/js/list.filter.js`
  (find the exact path with `find src -name list.filter.js`)
- Test: `tests/test1/test_button_leaves.py` (or the existing filter / action-menu test module), `tests/js/list.filter.test.js`

**Interfaces:**
- Consumes: `{% cv_icon_class %}` (Task 2), the Task 3 rule.
- Produces: `icon_host_keys(icon, location) -> tuple[str, bool]` in `crud_views.lib.view.button_data` (refactor of
  Task 3's computation; `cv_button_data` calls it).
- Produces: filter-toggle attributes `data-cv-filter-icon-open="<class>"` / `data-cv-filter-icon-close="<class>"`
  (both present only in host rendering).

- [ ] **Step 1: Failing tests.**

```python
def test_host_menu_toggle():   # toggle <button> class contains "icon-dots" (CRUD_VIEWS_ICONS["actions-menu"]="ui:dots"),
    #                             no <i>, hidden "More actions" span kept
def test_host_filter_toggle_closed():  # class contains "icon-funnel", data-cv-filter-icon-open="icon-funnel",
    #                                     data-cv-filter-icon-close="icon-x", no [data-cv-filter-icon] spans, hidden label kept
def test_host_filter_toggle_open():    # session filter expanded -> class contains "icon-x", not "icon-funnel"
def test_filter_toggle_mixed_placement_uses_spans():  # only "filter" is host -> both spans, no data-cv-filter-icon-open
```

```js
it("swaps the host icon classes on the button", async () => {
    // fixture variant: <button ... class="btn icon-funnel" data-cv-filter-icon-open="icon-funnel"
    //                   data-cv-filter-icon-close="icon icon-x"> without spans
    f.toggle.click();
    expect(f.toggle.classList.contains("icon-funnel")).toBe(false);
    expect([...f.toggle.classList]).toEqual(expect.arrayContaining(["btn", "icon", "icon-x"]));
    f.toggle.click();
    expect(f.toggle.className).toBe("btn icon-funnel");
});
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: Implement.**
  - `cv_actions_menu` (templatetags) adds `cv_menu_icon_class` and `cv_menu_icon_inline` to its context, computed by
    the same rule as Task 3 (`kind="action"` rule without label mode: host icon → slot class + not inline). Extract
    the rule from `cv_button_data` into a helper in `button_data.py`,
    `icon_host_keys(icon: str | None, location: str) -> tuple[str, bool]`, and use it in both places.
    `actions_menu_toggle.html` appends `cv_menu_icon_class` to `class` and renders `{% cv_icon cv_menu_icon %}` only
    when `cv_menu_icon_inline`.
  - `context_action_filter.html`: `{% cv_icon_class "filter" "context" as open %}{% cv_icon_class "filter-close"
    "context" as close %}`; if both: current state's class appended to `class`, the two data attributes, no spans;
    else today's markup unchanged. Decided edge: with `context:icon-host` set to `None` the tag returns `""`, so the
    filter toggle falls back to the spans (standalone icons); documented in buttons.md next to the slot.
  - `list.filter.js`: if `button.dataset.cvFilterIconOpen !== undefined`, remove the old state's classes and add the
    new state's (split on `/\s+/`, drop empties), else the existing span toggle.
- [ ] **Step 4:** Python + JS tests → PASS; full `pytest tests -n auto` green.
- [ ] **Step 5:** Commit `feat(buttons): host-placed icons on the menu and filter toggles (#258)`.

### Task 5: Docs, migration guide, changelog

**Files:** `docs/reference/icons.md`, `docs/reference/buttons.md`, `docs/reference/theme.md`,
`docs/reference/action_menus.md`, `docs/reference/javascript.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`

- [ ] **Step 1:** Write the sections listed in the spec's "Docs and changelog" (icons "Host placement" section with
  the config, resulting HTML, standalone class, `{% cv_icon_class %}`, filter toggle; the four slots and
  `None` = off in buttons.md's key list; `cv_icon_class` / `cv_icon_inline` in the leaf contract table; theme.md
  paragraph; action_menus.md menu leaves; javascript.md filter class swap; migrating-1.0.md: "Templates to delete",
  both "Hooks instead of copies" bullets, "Contract changes"; CHANGELOG `### Added` with E363 and the new library
  keys).
- [ ] **Step 2:** `mkdocs build --strict` (or `task docs` build equivalent) → no warnings for the touched pages;
  `ruff format --check` / pre-commit pass (CI ruff formats Markdown — keep the venv on the pinned version).
- [ ] **Step 3:** Commit `docs: icon host placement (#258)`.

### Task 6: Acceptance

- [ ] **Step 1:** `pytest tests -n auto`, JS suite, `task check` → all green; record outputs in
  `superpowers/notes/2026-10-23-icon-host-placement-acceptance.md` (Review Focus items each with the test that
  covers it), commit.
- [ ] **Step 2:** Whole-branch review, then bring the issue body in line with what shipped and open the PR (template
  `.github/PULL_REQUEST_TEMPLATE.md`, "Closes #258") — both after the maintainer's go-ahead.
