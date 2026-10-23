# Button Container Empty and Label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The `context` / `list` / `card` button container renders nothing when it has no items (#265), and its
element and `aria-label` come from class-table keys, with the default label translated (#266).

**Architecture:** Six new keys in `DEFAULT_BUTTON_CLASSES`; `ContainerLayout` / `get_container_layout()` in
`src/crud_views/lib/button_classes.py` gain `empty`, `tag` and `label`; `tags/button/container.html` branches on
them and stops reading `cv_container_tag`, which the three logic templates stop passing.

**Tech Stack:** Django templates and i18n, pytest + pytest-django, lxml for HTML assertions.

**Spec:** `superpowers/specs/2026-10-23-button-container-empty-label-design.md` (issues #265, #266)

## Global Constraints

- Branch `feat/button-container-empty-label`, in place (no worktree); one commit per task; one PR closing #265 and #266.
- With at least one item and nothing configured (English locale), markup is byte-for-byte today's:
  `tests/test1/test_action_menus_golden.py` passes with golden files unchanged (never regenerate them).
- Locations `context`, `list`, `card` only. `menu`, `formset`, `card-order` untouched.
- Defaults: `context:container-tag` / `list:container-tag` = `"fieldset"`, `card:container-tag` = `"div"`;
  `context:container-label` / `list:container-label` = `gettext_noop("Actions")`, `card:container-label` = `None`.
- Tag fallback `"div"` for `None`, `""` or non-str. Label `""` for `None`, `""` or non-str, else `gettext(value)`.
- No `gettext_lazy` in the class table; E361 unchanged. No new system check. No `role` attribute. No
  `cv_container_tag` fallback.
- `### Breaking` entries in `CHANGELOG.md` → `docs/migrating-1.0.md` updated too (CLAUDE.md rule).
- Never name downstream / client projects in code, docs, changelog or tests.
- Python 3.12+, Django 4.2/5.2/6.0, line length 120, double quotes, ruff. Run tests with `pytest tests -n auto`.

## Review Focus

- A group whose only item is the menu toggle is not empty → Task 2 `test_menu_only_group_keeps_container`.
- Zero items with #261 keys set (`container-list`, `container-single: "bare"`) render `""`, not a bare `<ul>` →
  Task 2 `test_zero_items_render_nothing_whatever_the_keys`.
- A label with HTML characters is escaped in `aria-label` → Task 2 `test_label_is_escaped`.
- The German label shows up through a real view, not only in the resolver → Task 2 `test_context_label_german`.
- A tag set to `None` must not render `<None>` or `<>` → Task 1 `test_layout_tag_fallback_div` and Task 2
  `test_tag_none_renders_div`.

---

### Task 1: Keys and layout resolver

**Files:**
- Modify: `src/crud_views/lib/button_classes.py` (defaults near the `#261` container keys; `ContainerLayout`;
  `get_container_layout()`)
- Test: `tests/test1/test_button_container_layout.py`

**Interfaces:**
- Produces: `ContainerLayout(list_class: str | None, item_class: str, bare: bool, empty: bool, tag: str, label: str)`
  (frozen dataclass, new fields appended in this order); `get_container_layout(location: str, item_count: int)`
  unchanged signature.

- [ ] **Step 1: Write the failing tests** (module docstring gains `#265/#266: empty, container-tag, container-label`)

```python
@pytest.mark.parametrize("loc, tag, label", [("context", "fieldset", "Actions"), ("list", "fieldset", "Actions"), ("card", "div", None)])
def test_defaults_tag_label(loc, tag, label):
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-tag"] == tag
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-label"] == label
    layout = get_container_layout(loc, 1)
    assert (layout.tag, layout.label) == (tag, label or "")

@pytest.mark.parametrize("count, empty", [(0, True), (1, False), (2, False)])
def test_layout_empty(count, empty):
    assert get_container_layout("list", count).empty is empty

def test_layout_tag_and_label_from_settings():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-tag": "div", "list:container-label": "Row"}):
        layout = get_container_layout("list", 2)
    assert (layout.tag, layout.label) == ("div", "Row")

@pytest.mark.parametrize("value", [None, "", 3])
def test_layout_tag_fallback_div(value):  # override_settings with the value; .tag == "div"

@pytest.mark.parametrize("value", [None, "", 3])
def test_layout_label_none(value):  # override list:container-label; .label == ""

def test_layout_label_translated():
    with translation.override("de"):
        assert get_container_layout("context", 1).label == "Aktionen"
```

Also update the existing `test_defaults`: its `ContainerLayout(list_class=None, item_class="", bare=False)` equality
becomes a check of those three attributes (the dataclass now has six fields), and
`test_layout_list_and_item`'s positional `ContainerLayout("x", "y", False)` likewise.

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test1/test_button_container_layout.py -v`
Expected: FAIL (`KeyError: 'context:container-tag'`, `AttributeError: ... 'empty'`).

- [ ] **Step 3: Implement**

Add the six defaults with a comment `# container element and its aria-label (#266); the label is translated at
render`. `from django.utils.translation import gettext, gettext_noop`. Extend `ContainerLayout` (docstring mentions
#265/#266) and `get_container_layout()`: `empty=item_count == 0`; tag and label per Global Constraints. Extend the
function's docstring by one sentence on the fallbacks.

- [ ] **Step 4: Run to verify they pass**

Run: `pytest tests/test1/test_button_container_layout.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -v`
Expected: PASS (no new E361 / W362 from the new keys).

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/button_classes.py tests/test1/test_button_container_layout.py
git commit -m "feat(buttons): container-tag and container-label keys, empty layout (#265, #266)"
```

### Task 2: Container leaf and logic templates

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/button/container.html`
- Modify: `src/crud_views/templates/crud_views/tags/context_actions.html:9`,
  `src/crud_views/templates/crud_views/columns/actions.html:8`, `src/crud_views/templates/crud_views/tags/card.html:12`
  (drop `cv_container_tag=…` from the include)
- Test: `tests/test1/test_button_container_list.py`, `tests/test1/test_button_leaves.py`

**Interfaces:**
- Consumes: `cv_layout.empty`, `cv_layout.tag`, `cv_layout.label` from Task 1 (via the existing
  `{% cv_container_layout cv_location cv_buttons cv_group as cv_layout %}`).

- [ ] **Step 1: Write the failing tests** (in `test_button_container_list.py`, a new section `# --- #265/#266`)

Leaf tests render `"crud_views/tags/button/container.html"` with `cv_location`, `cv_buttons`, `cv_group` (no
`cv_container_tag`); one inline item can be a minimal button ctx as used elsewhere in that file, or go through the
views helpers.

- `test_zero_items_render_nothing_whatever_the_keys` — replaces `test_zero_items_render_as_today_whatever_the_keys`:
  parametrize `group` in `[None, "empty"]` and `loc` in `["context", "list", "card"]`; with and without
  `{**_list_keys(loc), **_bare(loc)}` the output `.strip() == ""`.
- `test_menu_only_group_keeps_container` — group with only a menu item (default keys): exactly one
  `[cv-<loc>-container]` element.
- `test_list_row_without_actions_has_no_container(client_full, monkeypatch)` — `_list_actions(monkeypatch, [])`; GET
  the author list; the `td.cv-col-action` cells (if the column renders) contain no `[cv-list-container]`, and the page
  has no `[cv-list-container]` at all.
- `test_tag_and_label_from_settings` — `override_settings` `{"list:container-tag": "div", "list:container-label":
  "Row"}`, list row through the view: `div[cv-list-container][aria-label="Row"]`, no `fieldset`.
- `test_tag_none_renders_div` — `{"context:container-tag": None}`: toolbar is `div[cv-context-container]`.
- `test_label_none_renders_no_aria_label` — `{"context:container-label": None}`: `[cv-context-container]` has no
  `aria-label`.
- `test_label_is_escaped` — label `'A "b" <c>'`: parsed `aria-label` equals it, raw HTML contains `&quot;`.
- `test_context_label_german(client_full)` — `translation.override("de")` (or `HTTP_ACCEPT_LANGUAGE="de"` if
  `LocaleMiddleware` is active in the test settings): the detail toolbar has `aria-label="Aktionen"`.

In `test_button_leaves.py`, `test_container_div_has_no_aria_label` renders empty groups with `cv_container_tag`;
rewrite it to drop `cv_container_tag` and give each group one inline button (or a menu), keeping its assertions on
`class`, `cv-*-container`, and `aria-label` (`None` for card, `"Actions"` for list).

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test1/test_button_container_list.py tests/test1/test_button_leaves.py -v`
Expected: FAIL (empty groups still render the element; settings tag/label ignored).

- [ ] **Step 3: Implement**

Container leaf per spec "Container leaf": `{% if cv_layout.empty %}{% elif cv_layout.bare %}` … `{% else %}<{{
cv_layout.tag }} class="…"{% if cv_layout.label %} aria-label="{{ cv_layout.label }}"{% endif %}
cv-{{ cv_location }}-container="true">` … `</{{ cv_layout.tag }}>{% endif %}`. Keep the file's existing whitespace
inside the element exactly, so goldens match. Drop `cv_container_tag=…` from the three includes.

- [ ] **Step 4: Run the full suite**

Run: `pytest tests -n auto`
Expected: PASS, golden files unchanged (`git status tests/test1/golden` clean). Any other test that asserted an empty
container (grep `cv-.*-container` in `tests/`) is updated to the new rule, not the leaf.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templates tests/test1
git commit -m "feat(buttons): empty container renders nothing; tag and label from the class table (#265, #266)"
```

### Task 3: Docs, changelog, migration guide

**Files:**
- Modify: `docs/reference/buttons.md` (class table rows ~69-74; "Button row as a list" ~128-156; leaf table row ~278)
- Modify: `docs/reference/action_menus.md` (~177), `docs/migrating-1.0.md` (~256 plus a new section),
  `docs/reference/theme.md` (~115, only if the example container is a `div`), `CHANGELOG.md` (Unreleased)

- [ ] **Step 1: Write**

- `buttons.md`: rows for `<location>:container-tag` and `<location>:container-label` (defaults from Global
  Constraints); the label is passed through `gettext` at render, so a project's own wording is translated by its
  catalogue; `None` / `""` renders no `aria-label`; a `div` container should set the label to `None` (`aria-label`
  on a plain `div` has no role to name); an empty group renders nothing. The leaf row: receives `cv_buttons`,
  `cv_group`, `cv_location`; tag and label come from `cv_layout`.
- `action_menus.md` and `migrating-1.0.md` table: drop `cv_container_tag`.
- `migrating-1.0.md`: a short section with the three Breaking points of the spec, each with what to do.
- `CHANGELOG.md` Unreleased: `### Breaking` bullets (empty container renders nothing; `cv_container_tag` removed, read
  `cv_layout.tag` / set `<location>:container-tag`; default label translated), `### Added` bullet for the two keys,
  each with `(#265)` / `(#266)`.

- [ ] **Step 2: Verify**

Run: `ruff format --check . && ruff check . && grep -rn "cv_container_tag" src docs` 
Expected: ruff clean; grep finds only the migration-guide / changelog mentions that explain the removal.
If `mkdocs` is available: `mkdocs build --strict` passes.

- [ ] **Step 3: Commit**

```bash
git add docs CHANGELOG.md
git commit -m "docs(buttons): container tag and label keys, empty container (#265, #266)"
```
