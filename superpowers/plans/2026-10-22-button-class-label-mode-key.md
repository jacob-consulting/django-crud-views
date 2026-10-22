# Button class table: label-mode key — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `get_button_class()` and the two leaves that resolve `location:variant` learn the button's label mode, so a theme can give `card:tertiary:icon` different classes from `card:tertiary`, with a one-step fallback and a shape-aware `crud_views.W362`.

**Architecture:** One optional `mode` argument threads from the leaf (`cv_label_mode`, already validated by `cv_button_data()`) through the `cv_button_class` tag into `get_button_class()`, which prefers `location:slot:mode` when that key is *present* in the merged dict and otherwise reads `location:slot`. No default, no markup and no golden changes. The check learns the key shape instead of the defaults growing.

**Tech Stack:** Django 4.2 / 5.2 / 6.0 templates and system checks, pytest + lxml, ruff.

**Spec:** `superpowers/specs/2026-10-22-button-class-label-mode-key-design.md` — issue #209, tracker #228, follow-ups #216 and #227.

## Global Constraints

- Line length 120, double quotes, `ruff format` (Markdown included — CI formats `.md`).
- Python 3.12–3.15, Django 4.2 / 5.2 / 6.0.
- `src/crud_views/lib/button_classes.py` imports nothing from `crud_views.lib.view` at module level (it would drag the app registry into the class table). Function-local import inside the check only.
- `DEFAULT_BUTTON_CLASSES` is unchanged: 34 keys, `EXPECTED_KEYS` in `tests/test1/test_button_classes.py` untouched.
- No file under `tests/test1/golden/` changes. Never run `CV_UPDATE_GOLDEN=1`.
- `get_button_class(location, slot)` and `{% cv_button_class location slot %}` keep working unchanged; the new parameter is trailing and optional.
- One commit per task, on branch `feat/button-class-label-mode-key`. Run tests with `pytest tests -n auto`.

## Review Focus

1. Toolbar and list buttons are `icon` today, so `context:*:icon` and `list:*:icon` keys are **live immediately**, not "after #216" — a theme that registers them restyles every toolbar and row button now. Test in Task 3 (`test_list_row_buttons_resolve_icon_mode`).
2. A trailing colon or empty mode segment in config (`card:tertiary:`) must warn, not pass as a valid key. Test in Task 4.
3. A mode key with a non-string value reports `E361` once, not `E361` plus a spurious `W362`. Test in Task 4.
4. A non-string `mode` from a template variable (`True`, an int) falls back to the base rather than raising. Test in Task 1.
5. Settings `None` on a mode key that a theme also defines switches that mode off (`""`) — the settings layer wins per key, then presence decides. Test in Task 1.

---

## Setup (no tests)

- [ ] Commit the spec and this plan on `main`:

```bash
git add superpowers/specs/2026-10-22-button-class-label-mode-key-design.md superpowers/plans/2026-10-22-button-class-label-mode-key.md
git commit -m "docs: spec and plan for the label-mode class key (#209)"
git checkout -b feat/button-class-label-mode-key
```

---

### Task 1: `get_button_class()` learns the mode

**Files:**
- Modify: `src/crud_views/lib/button_classes.py:85-89`
- Test: `tests/test1/test_button_classes.py`

**Interfaces:**
- Produces: `get_button_class(location: str, slot: str, mode: str | None = None) -> str`. Positional-or-keyword; the tag passes it positionally. Resolution: if `mode` is truthy and `f"{location}:{slot}:{mode}"` is a key of `get_button_classes()`, that entry; else `f"{location}:{slot}"`; then the existing value rule (`str` as-is, anything else `""`).

- [ ] **Step 1: Write the failing tests** (append to `tests/test1/test_button_classes.py`; the module's `_isolate_registry` fixture already resets the theme layer and cache)

```python
def test_mode_key_wins_when_present_else_base():
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    assert get_button_class("card", "tertiary", "icon") == "btn btn-sm btn-icon"
    assert get_button_class("card", "tertiary", "both") == "btn btn-outline-secondary btn-sm"
    assert get_button_class("card", "tertiary") == "btn btn-outline-secondary btn-sm"


def test_mode_key_none_switches_off_and_does_not_fall_through():
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": None}):
        assert get_button_class("card", "tertiary", "icon") == ""
        assert get_button_class("card", "tertiary") == "btn btn-outline-secondary btn-sm"


@pytest.mark.parametrize("mode", ["", "iconn", None, True, 3])
def test_unknown_or_empty_mode_falls_back(mode):
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    assert get_button_class("card", "tertiary", mode) == "btn btn-outline-secondary btn-sm"


def test_settings_base_key_does_not_beat_theme_mode_key():
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary": "btn btn-sm btn-success"}):
        assert get_button_class("card", "tertiary", "icon") == "btn btn-sm btn-icon"
        assert get_button_class("card", "tertiary", "both") == "btn btn-sm btn-success"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": "btn x"}):
        assert get_button_class("card", "tertiary", "icon") == "btn x"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_button_classes.py -k "mode" -v`
Expected: FAIL — `TypeError: get_button_class() takes 2 positional arguments but 3 were given`

- [ ] **Step 3: Implement the signature from Interfaces in `src/crud_views/lib/button_classes.py`**

Update the docstring to say "preferring `location:slot:mode` when that key is present" and the module docstring's `location:slot` mention to `location:slot[:mode]`. Presence check is `key in classes`, not `classes.get(key)`.

- [ ] **Step 4: Run the module's tests**

Run: `pytest tests/test1/test_button_classes.py -v`
Expected: all PASS, including the pre-existing `test_default_table_is_complete` (34 keys).

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/button_classes.py tests/test1/test_button_classes.py
git commit -m "feat(buttons): get_button_class() prefers location:slot:mode when the key is present (#209)"
```

---

### Task 2: Both `cv_button_class` tags take the mode

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py:424-427`
- Modify: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:107-110`
- Test: `tests/test1/test_button_classes.py`

**Interfaces:**
- Consumes: `get_button_class(location, slot, mode=None)` from Task 1.
- Produces: `{% cv_button_class location slot [mode] %}` in both libraries, `def cv_button_class(location, slot, mode=None)` delegating to `get_button_class(location, slot, mode)`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test1/test_button_classes.py`)

```python
def test_tag_third_argument_in_both_libraries():
    for lib in ("crud_views", "crud_views_object_detail"):
        tpl = Template("{% load " + lib + ' %}{% cv_button_class "card" "tertiary" "icon" %}')
        assert tpl.render(Context()) == "btn btn-outline-secondary btn-sm"
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": "x-icon"}):
            assert tpl.render(Context()) == "x-icon"


def test_tag_accepts_mode_variable():
    tpl = Template("{% load crud_views %}{% cv_button_class cv_location cv_variant cv_label_mode %}")
    ctx = {"cv_location": "card", "cv_variant": "tertiary", "cv_label_mode": "icon"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": "x-icon"}):
        assert tpl.render(Context(ctx)) == "x-icon"
        assert tpl.render(Context({**ctx, "cv_label_mode": "both"})) == "btn btn-outline-secondary btn-sm"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_button_classes.py -k "tag_third or tag_accepts_mode" -v`
Expected: FAIL — `TemplateSyntaxError: 'cv_button_class' received too many positional arguments`

- [ ] **Step 3: Add `mode=None` to both tag functions**, docstrings `"Resolved CSS classes for ``location:slot``, or ``location:slot:mode`` when that key exists (autoescaped)."` — identical in both files.

- [ ] **Step 4: Run the module's tests**

Run: `pytest tests/test1/test_button_classes.py -v`
Expected: all PASS (`test_tag_in_both_libraries_escapes` still passes with two arguments).

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py src/crud_views_object_detail/templatetags/crud_views_object_detail.py tests/test1/test_button_classes.py
git commit -m "feat(buttons): {% cv_button_class %} takes an optional label mode in both libraries (#209)"
```

---

### Task 3: The two leaves pass the mode; nothing rendered changes by default

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/button/action.html:2`
- Modify: `src/crud_views/templates/crud_views/tags/context_action_filter.html:3`
- Create: `tests/test1/test_button_class_label_mode.py`

**Interfaces:**
- Consumes: the three-argument tag from Task 2.
- Produces: `action.html` resolves `{% cv_button_class cv_location cv_variant cv_label_mode %}`; `context_action_filter.html` resolves `{% cv_button_class "context" cv_variant|default:"secondary" "icon" %}`.

- [ ] **Step 1: Write the failing tests** in the new module. Model the helpers on `tests/test1/test_card_label_mode_render.py` (`_client`, `_card`, `_inline`, `CARD`); keep them local to this module. Fixtures `author_douglas_adams`, `publisher_penguin`, `cv_author`, `cv_publisher` and `tests.lib.helper.user.user_viewset_permission` exist.

```python
@pytest.mark.django_db
def test_card_same_variant_different_modes_get_different_classes(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail", "update"])
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [
            CardAction(key="detail", label="Details", variant="secondary", label_mode="both"),
            CardAction(key="update", label="Edit", variant="secondary", label_mode="icon"),
        ],
    )
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:secondary:icon": "btn btn-sm btn-icon x-icon"}):
        card = _card(
            _client([(cv_author, ("view", "add", "change", "delete"))]), reverse(cv_author.get_router_name("card"))
        )
    assert _inline(card, "detail").get("class") == "btn btn-secondary btn-sm"
    assert _inline(card, "update").get("class") == "btn btn-sm btn-icon x-icon"


@pytest.mark.django_db
def test_filter_toggle_resolves_icon_mode(cv_publisher, publisher_penguin):
    client = _client([(cv_publisher, ("view",))])

    def toggle_class() -> str:
        return lxml_html.fromstring(client.get("/publisher/").content).cssselect("#cv-filter-toggle")[0].get("class")

    assert toggle_class() == "btn btn-outline-primary btn-lg"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:secondary:icon": "x-icon"}):
        assert toggle_class() == "x-icon"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:secondary:both": "x-both"}):
        assert toggle_class() == "btn btn-outline-primary btn-lg"


@pytest.mark.django_db
def test_list_row_buttons_resolve_icon_mode(cv_publisher, publisher_penguin):
    client = _client([(cv_publisher, ("view", "change", "delete"))])
    keys = {f"list:{v}:icon": "x-list-icon" for v in VARIANTS}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=keys):
        doc = lxml_html.fromstring(client.get("/publisher/").content)
    buttons = doc.xpath("//*[@cv-list-container]/*[@cv-key]")
    assert buttons
    assert {b.get("class") for b in buttons} == {"x-list-icon"}
```

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_button_class_label_mode.py -v`
Expected: all three FAIL on the class assertions (the leaves still resolve the base key).

- [ ] **Step 3: Edit the two templates** to the strings in Interfaces. Nothing else in either file changes.

- [ ] **Step 4: Run the new module, the goldens, the leaf tests and the template guard**

Run: `pytest tests/test1/test_button_class_label_mode.py tests/test1/test_action_menus_golden.py tests/test1/test_button_leaves.py tests/test1/test_button_classes_templates.py tests/test1/test_variants.py -v`
Expected: all PASS. Then `git status --short tests/test1/golden/` prints nothing.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templates/crud_views/tags/button/action.html src/crud_views/templates/crud_views/tags/context_action_filter.html tests/test1/test_button_class_label_mode.py
git commit -m "feat(buttons): the action leaf and the filter toggle resolve the label-mode class key (#209)"
```

---

### Task 4: `crud_views.W362` validates the key shape

**Files:**
- Modify: `src/crud_views/lib/button_classes.py` (`button_class_check_messages()`, the W362 loop)
- Test: `tests/test1/test_button_classes_checks.py`, `tests/test1/test_button_classes.py`

**Interfaces:**
- Produces: `_is_action_mode_key(key: str) -> bool` in `button_classes.py`: true iff `key.split(":")` has exactly three parts with `location in LOCATIONS`, `variant in VARIANTS`, `mode in LABEL_MODES`. The three frozensets are imported **inside the function** from `crud_views.lib.view.button_data`, `.variant`, `.label_mode`. W362 fires for a key that is neither in `DEFAULT_BUTTON_CLASSES` nor an action mode key. When the key has three parts and its first two form a key in `DEFAULT_BUTTON_CLASSES`, the message is `Button class {key!r} has an unknown label mode {mode!r}.` with hint `Use one of ['both', 'icon', 'label'].`; otherwise the existing message and hint.

- [ ] **Step 1: Write the failing tests** (append to `tests/test1/test_button_classes_checks.py`)

```python
@pytest.mark.parametrize("key", ["card:tertiary:icon", "context:primary:both", "list:danger:label"])
def test_w362_accepts_action_mode_keys(key):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "btn"}):
        assert check_button_classes() == []
    register_button_classes({key: "btn"})
    assert check_button_classes() == []


@pytest.mark.parametrize(
    "key",
    [
        "card:tertiary:iconn",
        "card:container:icon",
        "menu:item:both",
        "card:tertiary:icon:extra",
        "card:tertiary:",
        "form:submit:icon",
    ],
)
def test_w362_rejects_bad_mode_shape(key):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "btn"}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.W362"]
    assert key in messages[0].msg


def test_w362_names_the_bad_mode():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:iconn": "btn"}):
        (message,) = check_button_classes()
    assert "'iconn'" in message.msg
    assert "both" in message.hint and "icon" in message.hint and "label" in message.hint


def test_mode_key_non_str_is_e361_only():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": 3}):
        assert ids(check_button_classes()) == ["crud_views.E361"]
```

And the import-weight guard, appended to `tests/test1/test_button_classes.py`:

```python
def test_button_classes_module_has_no_module_level_view_import():
    import ast
    from pathlib import Path

    tree = ast.parse(Path(bc.__file__).read_text())
    offenders = [
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("crud_views.lib.view")
    ]
    assert offenders == []
```

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_button_classes_checks.py tests/test1/test_button_classes.py::test_button_classes_module_has_no_module_level_view_import -v`
Expected: `test_w362_accepts_action_mode_keys` FAIL (W362 reported); `test_w362_names_the_bad_mode` FAIL (`'iconn'` not in the message); `test_mode_key_non_str_is_e361_only` FAIL (today the unknown key adds a W362 after the E361); `test_w362_rejects_bad_mode_shape` and the import guard PASS already.

- [ ] **Step 3: Implement `_is_action_mode_key()` and the two-message W362 loop** per Interfaces. The function-local import is the whole point of the import guard — do not hoist it.

- [ ] **Step 4: Run both check and lookup modules**

Run: `pytest tests/test1/test_button_classes_checks.py tests/test1/test_button_classes.py -v`
Expected: all PASS, `test_default_config_has_no_messages` included.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/button_classes.py tests/test1/test_button_classes_checks.py tests/test1/test_button_classes.py
git commit -m "feat(checks): W362 accepts location:variant:mode keys and names a bad mode segment (#209)"
```

---

### Task 5: Docs and CHANGELOG

**Files:**
- Modify: `docs/reference/buttons.md` (sections at lines 46, 77, 88–110, 147–156, 271–300, 316–325)
- Modify: `docs/reference/context_buttons.md:56-62`
- Modify: `docs/reference/theme.md:82-84`
- Modify: `CHANGELOG.md` (`### Added` under `## Unreleased`, line 93)

**Interfaces:**
- Consumes: the key shape, fallback and check semantics from Tasks 1–4; exact strings below are the spec's.

- [ ] **Step 1: `buttons.md`, "The class table"** — after the first paragraph, add the key shape:

> Action buttons take a third segment, the label mode: `location:variant:mode` with `mode` one of `label`, `icon`, `both` (see [Card list view](card-list-view.md) for how a card button gets its mode; toolbar and row buttons are `icon`). The lookup reads `location:variant:mode` when that key is defined and falls back to `location:variant` otherwise — one step, no chaining. No default defines a mode key: the table below is still the full list of shipped keys, and the 34-key count stands. A theme defines only the modes that differ from its base entry.

- [ ] **Step 2: `buttons.md`, "`CRUD_VIEWS_BUTTON_CLASSES`"** — after the `None` paragraph, the two rules a project needs:

> A mode key set to `None` switches that mode off; it does not fall back to the base key.
>
> Layers merge per key before the mode fallback runs, so a more specific key wins over a more specific layer. Given a theme that registers `card:tertiary:icon`, a project setting `"card:tertiary": "btn btn-sm btn-success"` recolours the labelled tertiary card buttons and **not** the icon-only one — override `card:tertiary:icon` as well.

Update the `get_button_class(location, slot)` sentence to `get_button_class(location, slot, mode=None)`.

- [ ] **Step 3: `buttons.md`, "Rendering"** — add the three-argument form to the example: `<a href="{{ url }}" class="{% cv_button_class cv_location cv_variant cv_label_mode %}">...</a>`, and one sentence: the bundled action leaf passes `cv_label_mode`; the filter toggle passes `"icon"`, so `context:<variant>:icon` reaches it like any other icon-only context button.

- [ ] **Step 4: `buttons.md`, "A theme recipe" and "System checks"** — change the recipe's `class="…"` line to pass `cv_label_mode`, and add after the recipe's first paragraph: "Classes that differ by label mode no longer need this override at all — register `context:primary:both` and the like instead." W362 row becomes: `a CRUD_VIEWS_BUTTON_CLASSES or theme key is neither in the default table nor a valid location:variant:mode (typo, or an unknown label mode)`.

- [ ] **Step 5: `context_buttons.md`** — after the `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` paragraph:

> A custom `template` or `template_code` is rendered from the resolved action data, which carries no `cv_label_mode`. One that resolves its classes with `{% cv_button_class "context" cv_variant %}` should pass its own mode as the third argument — `"icon"` for an icon-only button — the way the bundled `crud_views/tags/context_action_filter.html` does, so a theme's per-mode classes reach it. See [Buttons](buttons.md#the-class-table).

- [ ] **Step 6: `theme.md`, "Buttons"** — extend the first sentence: "…registers them from `AppConfig.ready()`, including per-label-mode keys such as `card:tertiary:icon` (see [Buttons](buttons.md#the-class-table)), and overrides a template only where the markup differs."

- [ ] **Step 7: `CHANGELOG.md`, `### Added`** — one bullet:

> - The button class table takes `location:variant:mode` keys (`mode` one of `label`, `icon`, `both`), read by the action leaf and the filter toggle with a one-step fallback to `location:variant`; `get_button_class()` and `{% cv_button_class %}` gain an optional third argument, `crud_views.W362` accepts the shape and names an unknown mode. No default defines a mode key, so nothing renders differently until a theme or project adds one (#209).

- [ ] **Step 8: Verify formatting and the full suite**

Run: `ruff format --check docs/reference/buttons.md docs/reference/context_buttons.md docs/reference/theme.md CHANGELOG.md && ruff check src tests && pytest tests -n auto -q`
Expected: "already formatted", no lint errors, all tests pass, `git status --short tests/test1/golden/` empty.

- [ ] **Step 9: Commit**

```bash
git add docs/reference/buttons.md docs/reference/context_buttons.md docs/reference/theme.md CHANGELOG.md
git commit -m "docs(buttons): the location:variant:mode key, its fallback and the custom-context-template rule (#209)"
```

---

### Task 6: Issue #209 body, acceptance note, PR

**Files:**
- Create: `superpowers/notes/2026-10-22-button-class-label-mode-key-acceptance.md` (match the newest file in `superpowers/notes/` for structure)

- [ ] **Step 1: Rewrite #209's body before the PR exists** — it is what the PR closes. `gh issue edit 209 --body-file <file>` with:

```markdown
## Summary

The button class table is keyed `location:variant`, so one class string had to serve a button whether it
rendered as an icon, a text label, or both. The leaf knows the mode (`cv_label_mode`, three-valued since #213:
`label`, `icon`, `both`) but never passed it to the lookup. A theme therefore could not give an icon-only button
different classes from a labelled one in the same location and variant — Tabler's `btn-icon` is required on the
former and wrong on the latter — and since #213 made the mode a per-action project knob, the theme cannot even
guess.

## Resolution (option A, spec in `superpowers/specs/2026-10-22-button-class-label-mode-key-design.md`)

- Key shape `location:variant:mode`, `mode` one of the `LabelMode` values, valid in all three locations.
- `get_button_class(location, slot, mode=None)` reads `location:slot:mode` when that key is present and falls
  back to `location:slot` — one step. A mode key set to `None` means no classes, not fall-through.
- `tags/button/action.html` passes `cv_label_mode`; `tags/context_action_filter.html` passes `"icon"`.
- `crud_views.W362` validates the key shape instead of the defaults growing. No default defines a mode key; no
  rendered output changes until a theme or project adds one.

Part of #228. The hard-coded `active` / `flex-grow-1` utilities noted below are #227.

## Acceptance criteria

- A theme can give an icon-only and a labelled button in the same location and variant different classes
  without overriding `tags/button/action.html`.
- Tables and `CRUD_VIEWS_BUTTON_CLASSES` written before the change keep working unchanged.
- A system check rejects an unknown mode segment and a mode segment on a non-action key.
- A card with a `both` and an `icon` action in the same variant renders two different class strings; the filter
  toggle resolves `context:<variant>:icon`; no golden changes.
- `docs/reference/buttons.md` documents the key shape, the fallback, the `None` rule and the layer-vs-specificity
  rule; `context_buttons.md` says a custom context template passes its own mode; CHANGELOG entry.
```

- [ ] **Step 2: Write the acceptance note** — per acceptance criterion in #209 (as rewritten), the test or command that proves it, and the `git status` of `tests/test1/golden/` after the full run. Commit it:

```bash
git add superpowers/notes/2026-10-22-button-class-label-mode-key-acceptance.md
git commit -m "docs: acceptance note for the label-mode class key (#209)"
```

- [ ] **Step 3: Final verification on the branch**

Run: `ruff format --check . && ruff check src tests && pytest tests -n auto -q && git status --short tests/test1/golden/`
Expected: formatted, clean, all pass, no golden output.

- [ ] **Step 4: Push and open the PR**

```bash
git push -u origin feat/button-class-label-mode-key
gh pr create --title "feat(buttons): the class table learns the label mode (#209)" --body-file <file>
```

PR body: the spec's "What it lands on" in five bullets, `Closes #209`, `Part of #228`, the sentence "No golden changes: a diff under `tests/test1/golden/` on this branch is a bug", and a pointer to #227 for the leaf utilities.
