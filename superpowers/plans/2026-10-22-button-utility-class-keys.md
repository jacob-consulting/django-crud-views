# The button chain's utility classes move into the class table — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The seven Bootstrap words still hard-coded in the button leaves (`active`, `flex-grow-1`, `visually-hidden`, `d-inline-block`) become class table keys with those words as defaults, or go, so a theme restyles them like every other button class and a rendering guard keeps the chain clean.

**Architecture:** Nine two-segment keys join `DEFAULT_BUTTON_CLASSES` (`<location>:active` ×5, `card:flex`, `<location>:hidden-label` ×3). The leaves replace each literal with `{% cv_button_class %}`; the icon placeholder drops `d-inline-block` because `.cv-icon-fw` already declares the display. A new test installs a sentinel table through `CRUD_VIEWS_BUTTON_CLASSES`, renders the leaves and four pages, and fails on any class token that is neither a sentinel nor `cv-`-prefixed, with two named behaviour exemptions. No Python logic, no CSS, no JS and no golden changes.

**Tech Stack:** Django 4.2 / 5.2 / 6.0 templates, pytest + lxml, ruff.

**Spec:** `superpowers/specs/2026-10-22-button-utility-class-keys-design.md` — issue #227, tracker #228 (last open child), after #216 (PR #230).

## Global Constraints

- Line length 120, double quotes, `ruff format` (Markdown included — CI formats `.md`).
- Exactly nine new keys with these defaults and no others: `context:active`, `list:active`, `card:active`, `menu:active`, `card-order:active` → `active`; `card:flex` → `flex-grow-1`; `context:hidden-label`, `list:hidden-label`, `card:hidden-label` → `visually-hidden`. The table counts 43 keys afterwards.
- No new check ids. `crud_views.W362` keeps reporting `context:active:icon` and `context:flex` as unknown keys.
- `LEAF_KEYS` and `LOCATIONS` in `src/crud_views/lib/view/button_data.py` are unchanged. No file under `src/crud_views/static/` changes. No Python under `src/crud_views/lib/` changes except `button_classes.py`.
- No file under `tests/test1/golden/` changes. Never run the golden regeneration. A diff there is a bug.
- `dropdown-toggle`, `data-bs-toggle`, `data-bs-popper-config`, `dropdown-menu dropdown-menu-end` and `d-none` stay where they are; the first and last are the only guard exemptions.
- One commit per task, on branch `feat/button-utility-class-keys`. Run tests with `pytest tests -n auto`.

## Review Focus

1. `context:active` set to `None`: the active toolbar button renders its base classes only, no `active`, no `None` text, no error. Test in Task 2 (`test_utility_key_set_to_none_renders_no_token`).
2. `card:flex` set to `None`: the same for the stretched card button. Same parametrised test in Task 2.
3. A menu item without an icon renders exactly `<span class="cv-icon-fw" aria-hidden="true">` as its placeholder. Test in Task 3 (`test_menu_item_without_icon_renders_the_fixed_width_placeholder`).
4. A card action in `icon` mode renders its hidden label through `card:hidden-label`, so the key is reachable at every location, not only where the toggles live. Test in Task 3 (`test_card_icon_mode_hidden_label_comes_from_the_table`).
5. The guard still bites after the chain is clean: a literal put back into the leaf fails it with the token named. Mutation step in Task 4.

---

## Setup (no tests)

- [ ] Commit this plan on `main` (the spec is already committed as `a85de42`) and branch:

```bash
git add superpowers/plans/2026-10-22-button-utility-class-keys.md
git commit -m "docs(plan): the button chain's utility classes move into the class table (#227)"
git checkout -b feat/button-utility-class-keys
```

---

### Task 1: The nine keys

**Files:**
- Modify: `src/crud_views/lib/button_classes.py:13-48` (`DEFAULT_BUTTON_CLASSES`)
- Test: `tests/test1/test_button_classes.py:14-57`, `tests/test1/test_button_classes_checks.py:71-80`

**Interfaces:**
- Produces: `get_button_class(location, slot)` resolves the nine keys above to their defaults; the keys are in `DEFAULT_BUTTON_CLASSES`, so `W362` accepts them and `test_every_literal_slot_in_templates_is_a_default_key` accepts literal pairs naming them.

- [ ] **Step 1: Extend the failing tests**

In `tests/test1/test_button_classes.py` add the nine keys to `EXPECTED_KEYS`, change `assert len(EXPECTED_KEYS) == 34` to `== 43`, and add:

```python
@pytest.mark.parametrize(
    ("location", "slot", "default"),
    [
        ("context", "active", "active"),
        ("list", "active", "active"),
        ("card", "active", "active"),
        ("menu", "active", "active"),
        ("card-order", "active", "active"),
        ("card", "flex", "flex-grow-1"),
        ("context", "hidden-label", "visually-hidden"),
        ("list", "hidden-label", "visually-hidden"),
        ("card", "hidden-label", "visually-hidden"),
    ],
)
def test_utility_slots_default_to_the_bootstrap_word(location, slot, default):
    assert get_button_class(location, slot) == default
```

In `tests/test1/test_button_classes_checks.py` append `"context:active:icon"`, `"card:flex:both"`, `"list:hidden-label:icon"` and `"context:flex"` to the key list of the `W362` rejection test that follows `test_w362_accepts_action_mode_keys` (the one parametrised with `"card:tertiary:iconn"`, …).

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -q`
Expected: `test_default_table_is_complete` and the nine `test_utility_slots_default_to_the_bootstrap_word` cases FAIL (`""` instead of the word); the four new `W362` cases PASS already (unknown keys are rejected today).

- [ ] **Step 3: Add the nine rows to `DEFAULT_BUTTON_CLASSES`** after `"card-order:container"`, grouped as in the spec's table, with a one-line comment that these are the utility slots the leaves used to hard-code (#227).

- [ ] **Step 4: Run the tests and the whole suite**

Run: `pytest tests -n auto -q`
Expected: PASS. `git status --short tests/test1/golden/` empty.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/button_classes.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py
git commit -m "feat(buttons): nine utility slots in the class table — active, flex, hidden-label (#227)"
```

---

### Task 2: `active` and `flex` reach the leaves

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/button/action.html:2`
- Modify: `src/crud_views/templates/crud_views/tags/button/menu_item.html:2`
- Modify: `src/crud_views/templates/crud_views/snippets/card_order.html:14,19`
- Test: `tests/test1/test_button_leaves.py`, `tests/test1/test_card_order.py`

**Interfaces:**
- Consumes: the keys from Task 1.
- Produces: the three templates contain no literal `active` or `flex-grow-1`; the class attribute is `<base classes>[ <location:active>][ <card:flex>]`, the space inside each `{% if %}`.

- [ ] **Step 1: Write the failing tests**

In `tests/test1/test_button_leaves.py`, next to `test_action_leaf_renders_from_contract_only` (it uses `_context_get`, `_one`, `render_to_string`, `override_settings`, the `theme_layer` fixture and `register_button_classes`, all already imported):

```python
def test_active_and_flex_come_from_the_table(theme_layer):
    register_button_classes({"context:active": "is-active", "card:active": "is-current", "card:flex": "is-expanded"})
    a = _one(render_to_string(ACTION_LEAF, _context_get()), "a")
    assert a.get("class") == "btn btn-outline-primary btn-lg is-active"
    card = _context_get(cv_location="card", cv_variant="primary", cv_flex=True)
    a = _one(render_to_string(ACTION_LEAF, card), "a")
    assert a.get("class") == "btn btn-primary btn-sm is-current is-expanded"


def test_menu_item_active_comes_from_the_table(theme_layer):
    register_button_classes({"menu:active": "is-active"})
    a = _one(render_to_string(MENU_ITEM_LEAF, _context_get(cv_location="list")), "a")
    assert a.get("class") == "dropdown-item is-active"


@pytest.mark.parametrize(
    ("key", "extra", "base"),
    [
        ("context:active", {}, ["btn", "btn-outline-primary", "btn-lg"]),
        (
            "card:flex",
            {"cv_location": "card", "cv_variant": "primary", "cv_active": False, "cv_flex": True},
            ["btn", "btn-primary", "btn-sm"],
        ),
    ],
)
def test_utility_key_set_to_none_renders_no_token(key, extra, base):
    # Review Focus 1 and 2: the flag is on, the key is None, so only the base classes render (a trailing space is fine)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: None}):
        a = _one(render_to_string(ACTION_LEAF, _context_get(**extra)), "a")
    assert a.get("class").split() == base
```

In `tests/test1/test_card_order.py`, after `test_card_order_toolbar_marks_active_direction` (add `from django.test import override_settings` if the module lacks it):

```python
@pytest.mark.django_db
def test_card_order_toolbar_active_class_comes_from_the_table(client_publisher_order, publishers):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card-order:active": "is-active"}):
        response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc")
    doc = html.fromstring(response.content)
    desc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=desc]")[0]
    asc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=asc]")[0]
    assert desc_btn.get("class") == "btn btn-outline-secondary is-active"
    assert asc_btn.get("class") == "btn btn-outline-secondary"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_button_leaves.py tests/test1/test_card_order.py -q -k "comes_from_the_table or set_to_none"`
Expected: the three `comes_from_the_table` tests FAIL (the literal word renders instead of the registered one); the two `set_to_none` cases FAIL (`active` / `flex-grow-1` still present).

- [ ] **Step 3: Change the three templates** to the exact forms in the spec's "The leaves" section:

- `action.html` line 2: `{% if cv_active %} {% cv_button_class cv_location 'active' %}{% endif %}{% if cv_flex %} {% cv_button_class 'card' 'flex' %}{% endif %}`
- `menu_item.html` line 2: `{% if cv_active %} {% cv_button_class 'menu' 'active' %}{% endif %}`
- `card_order.html` lines 14 and 19: `{% if cv_order_dir == 'asc' %} {% cv_button_class 'card-order' 'active' %}{% endif %}` and the `desc` twin.

- [ ] **Step 4: Run the whole suite**

Run: `pytest tests -n auto -q && git status --short tests/test1/golden/`
Expected: PASS, empty. `test_every_literal_slot_in_templates_is_a_default_key` passes with the new pairs because Task 1 put them in the table.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templates/crud_views/tags/button/action.html src/crud_views/templates/crud_views/tags/button/menu_item.html src/crud_views/templates/crud_views/snippets/card_order.html tests/test1/test_button_leaves.py tests/test1/test_card_order.py
git commit -m "feat(buttons): the leaves take active and flex from the class table (#227)"
```

---

### Task 3: The hidden label and the icon placeholder

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/button/action.html:8` (the `icon` branch)
- Modify: `src/crud_views/templates/crud_views/tags/actions_menu_toggle.html:6`
- Modify: `src/crud_views/templates/crud_views/tags/context_action_filter.html:12`
- Modify: `src/crud_views/templates/crud_views/tags/button/menu_item_label.html:1`
- Modify: `src/crud_views/templates/crud_views/tags/actions_menu_item_label.html:1`
- Test: `tests/test1/test_button_leaves.py`

**Interfaces:**
- Consumes: the `hidden-label` keys from Task 1.
- Produces: every hidden label span in the chain renders `class="{% cv_button_class <location> 'hidden-label' %}"`; the placeholder span renders `class="cv-icon-fw"` only. Default markup is byte-identical.

- [ ] **Step 1: Write the failing tests**

In `tests/test1/test_button_leaves.py` (helpers: `_context_get`, `_one`, `_get`, `client_full`, `theme_layer`; `AuthorListView`, `AuthorCardListView`, `CardAction`, `cv_publisher`, `User`, `Client`, `user_viewset_permission` are imported):

```python
def test_hidden_label_comes_from_the_table(theme_layer):
    register_button_classes({"list:hidden-label": "sr-only"})
    a = _one(render_to_string(ACTION_LEAF, _context_get(cv_location="list", cv_active=False)), "a")
    (hidden,) = a.cssselect("span")
    assert hidden.get("class") == "sr-only"
    assert hidden.text == "Details"


def test_menu_item_without_icon_renders_the_fixed_width_placeholder():
    a = _one(render_to_string(MENU_ITEM_LEAF, _context_get(cv_location="list", cv_active=False, cv_icon=None)), "a")
    (placeholder,) = a.cssselect("span")
    assert placeholder.get("class") == "cv-icon-fw"
    assert placeholder.get("aria-hidden") == "true"


@pytest.mark.django_db
def test_toggles_hidden_label_comes_from_the_table(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update", "delete", "up", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    user = User.objects.create_user(username="leaves_publisher_view", password="pw")
    user_viewset_permission(user, cv_publisher, "view")
    publisher_client = Client()
    publisher_client.force_login(user)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:hidden-label": "sr-only", "context:hidden-label": "sr-label"}):
        _, doc = _get(client_full, "list")
        resp = publisher_client.get(reverse(cv_publisher.get_router_name("list")))
    menu_toggle = doc.cssselect("fieldset[cv-list-container] button.cv-menu-toggle")[0]
    assert menu_toggle.cssselect("span")[0].get("class") == "sr-only"
    assert resp.status_code == 200
    filter_toggle = lxml_html.fromstring(resp.content).cssselect("#cv-filter-toggle")[0]
    assert filter_toggle.cssselect("span")[-1].get("class") == "sr-label"


@pytest.mark.django_db
def test_card_icon_mode_hidden_label_comes_from_the_table(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", label_mode="icon")])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:hidden-label": "sr-only"}):
        _, doc = _get(client_full, "card")
    a = doc.cssselect("div[cv-card-container] a[cv-key=detail]")[0]
    assert a.cssselect("span")[0].get("class") == "sr-only"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `pytest tests/test1/test_button_leaves.py -q -k "hidden_label or placeholder"`
Expected: the three `hidden_label` tests FAIL (`visually-hidden` renders); the placeholder test FAILS (`cv-icon-fw d-inline-block`).

- [ ] **Step 3: Change the five templates**

- `action.html` icon branch: `<span class="{% cv_button_class cv_location 'hidden-label' %}">{{ cv_label }}</span>`
- `actions_menu_toggle.html` line 6: `<span class="{% cv_button_class cv_location 'hidden-label' %}">{% translate "More actions" %}</span>`
- `context_action_filter.html` line 12: `<span class="{% cv_button_class 'context' 'hidden-label' %}">{{ cv_action_label }}</span>`
- `menu_item_label.html` and `actions_menu_item_label.html`: the `{% else %}` span becomes `<span class="cv-icon-fw" aria-hidden="true"></span>`.

- [ ] **Step 4: Run the whole suite**

Run: `pytest tests -n auto -q && git status --short tests/test1/golden/`
Expected: PASS, empty. `test_template_a11y.py` is green unchanged: the default word is still `visually-hidden`.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templates/crud_views/tags tests/test1/test_button_leaves.py
git commit -m "feat(buttons): the hidden label asks the class table; the icon placeholder drops d-inline-block (#227)"
```

---

### Task 4: The rendering guard

**Files:**
- Modify: `tests/test1/test_button_classes_templates.py` (keep the two existing tests; raise the literal-pair bound)

**Interfaces:**
- Consumes: the clean chain from Tasks 2–3; page fixtures in the style of `tests/test1/test_action_menus_golden.py::_client`.
- Produces: `SENTINEL_CLASSES: dict[str, str]`, `BEHAVIOUR_TOKENS: dict[str, str]` (token → reason, the list the follow-up issue empties) and `test_button_chain_renders_only_table_classes`.

- [ ] **Step 1: File the follow-up issue** so its number can go into the exemption reasons. Title: `Bootstrap words that remain in the button chain because they carry behaviour`. Body, from the spec's Issues section: the tokens (`dropdown-toggle`, `data-bs-toggle`, `data-bs-popper-config`, `dropdown-menu dropdown-menu-end`, `d-none` with `list.filter.js`, the language selector's `dropdown-item ... active`), the sentence that the whole-page theme audit (Bulma) is a separate decision deferred on 2026-10-22, and a pointer to `BEHAVIOUR_TOKENS` in `tests/test1/test_button_classes_templates.py` as the list to empty. Label `enhancement`. Note the number for Step 2.

- [ ] **Step 2: Write the guard**

In `tests/test1/test_button_classes_templates.py`:

```python
SENTINEL_CLASSES = {key: "x-" + key.replace(":", "-") for key in DEFAULT_BUTTON_CLASSES}
SENTINELS = set(SENTINEL_CLASSES.values())
BEHAVIOUR_TOKENS = {
    "dropdown-toggle": "Bootstrap's dropdown hook on the menu toggle, kept with data-bs-toggle (#<follow-up>)",
    "d-none": "toggled by list.filter.js on the filter toggle's icon spans (#<follow-up>)",
}


def _offenders(doc) -> list[tuple[str, str]]:
    """(tag, token) for every class token on a sentinel-styled element or one of its span descendants that is
    neither a sentinel, nor cv- prefixed, nor an exempted behaviour token."""


@pytest.mark.django_db
def test_button_chain_renders_only_table_classes(...):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=SENTINEL_CLASSES):
        ...
    assert offenders == []
```

The body of `_offenders` walks `doc.iter()`, picks elements whose class tokens intersect `SENTINELS`, and checks those elements plus `el.iter("span")`, skipping nothing else (icons are `<i>`, so they are never visited). Render, inside the `override_settings` block, and collect offenders from each:

- leaf level, `render_to_string` of `crud_views/tags/button/action.html` for every `location` in `LOCATIONS` × every mode in `LABEL_MODES` with `cv_active=True` and `cv_flex=(location == "card")`, and of `crud_views/tags/button/menu_item.html` with `cv_active=True` (a contract dict with the keys of `_context_get` in `test_button_leaves.py`; copy the dict into this module rather than importing across test modules);
- page level, with clients built like the golden test's `_client`: the publisher list (`cv_publisher`, `view` + `add`: active `list` button, filter toggle, create, rows), the author list with `AuthorListView.cv_list_actions = ["detail", "update", "delete", "up", "ping"]` and `cv_list_actions_inline = ["detail"]` monkeypatched (row menus), the author card page (the `flex=True` detail action), the publisher order card page at `/publisher_order/card/?order=name&dir=asc` and `&dir=desc` (`cv_publisher_order`, `view`), and the author detail page.

Raise the bound in `test_every_literal_slot_in_templates_is_a_default_key` from `>= 15` to `>= 20` (five literal pairs were added in Tasks 2–3).

- [ ] **Step 3: Run it**

Run: `pytest tests/test1/test_button_classes_templates.py -q`
Expected: PASS. If the offender list is not empty, each entry is a real literal in the chain, not a reason to widen `BEHAVIOUR_TOKENS`: fix the template.

- [ ] **Step 4: Mutation check (Review Focus 5)**

Append a literal ` active` inside the `class="…"` of `src/crud_views/templates/crud_views/tags/button/action.html` (after the `{% endif %}` of `cv_flex`), run `pytest tests/test1/test_button_classes_templates.py::test_button_chain_renders_only_table_classes -q`.
Expected: FAIL with `("a", "active")` among the offenders. Then `git checkout -- src/crud_views/templates/crud_views/tags/button/action.html` and run it once more: PASS.

- [ ] **Step 5: Run the whole suite and commit**

Run: `pytest tests -n auto -q && git status --short tests/test1/golden/`
Expected: PASS, empty.

```bash
git add tests/test1/test_button_classes_templates.py
git commit -m "test(buttons): a rendering guard — every class in the button chain comes from the table (#227)"
```

---

### Task 5: Docs and CHANGELOG

**Files:**
- Modify: `docs/reference/buttons.md:60-97` (table, count, the "stays in the templates" paragraph), `:225-241` (leaf contract rows), `:295-347` (the theme recipe)
- Modify: `docs/reference/theme.md:96-101`
- Modify: `docs/reference/action_menus.md:158-166`
- Modify: `docs/reference/card-list-view.md:53`
- Modify: `docs/reference/javascript.md:167`
- Modify: `CHANGELOG.md` (Unreleased)

- [ ] **Step 1: `buttons.md`.** Append five rows to the key table (`context:active` / `list:active` / `card:active` → `active`; `menu:active` → `active`; `card-order:active` → `active`; `card:flex` → `flex-grow-1`; `context:hidden-label` / `list:hidden-label` / `card:hidden-label` → `visually-hidden`). The count sentence becomes "The default table has 43 keys: the rows with four variants stand for four keys each, the rows with three locations for three" and "the count stays 43". Rewrite the paragraph at line 95 so the fixed list is the element, `href`, `type`, `disabled`, `data-cv-*`, `aria-*`, `cv-key`, `dropdown-toggle`, `data-bs-toggle` and the like, followed by: the presentational words the leaves used to hard-code are keys — `<location>:active` for the current page's button, `card:flex` for a stretched card action, `<location>:hidden-label` for the screen-reader text of an icon-only button; a theme on another framework registers its own words there (`is-active`, `is-sr-only`, `sr-only`) and overrides no leaf; `None` on a `hidden-label` key makes the text visible. Leaf contract rows: `cv_active` → "the target is the current view; the leaf adds the `<location>:active` classes; never true for a disabled button"; `cv_flex` → "the leaf adds the `card:flex` classes; true only on cards"; in the `cv_label_mode` row, "icon with a visually hidden label" → "icon with a hidden label (`<location>:hidden-label`)". Theme recipe: the registration block gains `"context:active": "is-active"` and `"context:hidden-label": "is-sr-only"`; delete the `html+django` leaf override and the paragraph "The override changes one word…"; the paragraph "The leaf is shared by…" opens with "When you do override the leaf, for markup that differs, …" and otherwise stays.

- [ ] **Step 2: `theme.md`.** The worked example: register the classes, the `*:active` and `*:hidden-label` keys included when the framework spells those utilities differently, and override nothing for looks; a leaf override is for markup that differs. Keep the logic-templates paragraph.

- [ ] **Step 3: The three one-liners.** `action_menus.md` split-toggle example: `<span class="{% cv_button_class cv_location 'hidden-label' %}">`. `card-list-view.md` `flex` row: "If True, the button gets the `card:flex` classes (`flex-grow-1` by default)". `javascript.md:167`: "A hidden label (`<location>:hidden-label`) or an `aria-label` …".

- [ ] **Step 4: `CHANGELOG.md`.** Under `### Added`: the nine keys and their defaults, one bullet (#227). Under `### Changed`: the leaves `tags/button/action.html`, `tags/button/menu_item.html`, `snippets/card_order.html`, `tags/actions_menu_toggle.html` and `tags/context_action_filter.html` take `active`, `flex-grow-1` and `visually-hidden` from the table (a project override of a leaf keeps rendering whatever it holds); the menu item's icon placeholder drops `d-inline-block`, which `.cv-icon-fw` already provides (#227).

- [ ] **Step 5: Verify and commit**

Run: `ruff format --check docs CHANGELOG.md && grep -c "hidden-label" docs/reference/buttons.md docs/reference/theme.md docs/reference/action_menus.md && grep -n "34 keys\|is-active{% endif %}\|visually-hidden\">" docs/reference/*.md; mkdocs build -q -d /tmp/claude-1000/-home-alex-projects-alex-django-crud-views/5fe5cce4-bf9f-4e23-aaa9-447144261204/scratchpad/site`
Expected: format clean; the three counts are each ≥ 1; the stale-word grep prints nothing (no `34 keys`, no leaf override in the recipe, no literal hidden-label span left in an example); `mkdocs build` (1.6.1 on the venv) prints no warning about a broken anchor.

```bash
git add docs CHANGELOG.md
git commit -m "docs(buttons): the utility slots, the recipe without a leaf override, CHANGELOG (#227)"
```

---

### Task 6: Acceptance note, issue body, PR

**Files:**
- Create: `superpowers/notes/2026-10-22-button-utility-class-keys-acceptance.md`

- [ ] **Step 1: Full verification**

Run: `ruff check src tests && ruff format --check src tests docs && pytest tests -n auto && git status --short tests/test1/golden/ && git diff main --stat -- src/crud_views/static src/crud_views/lib`
Expected: clean, PASS, empty, and the last diff lists `button_classes.py` only.

- [ ] **Step 2: Write the acceptance note** in the shape of `superpowers/notes/2026-10-22-action-label-mode-context-list-acceptance.md`: the spec's five Goals, each mapped to the test names from Tasks 1–4 (the guard, the `comes_from_the_table` tests, the golden test unchanged and green, `test_template_a11y.py` unchanged), the Review Focus items with their tests, and the calls from the spec's last section with where each landed.

```bash
git add superpowers/notes/2026-10-22-button-utility-class-keys-acceptance.md
git commit -m "docs(notes): acceptance report for #227"
```

- [ ] **Step 3: Bring #227's body in line with what ships.** Replace the "Options" section with "Settled (2026-10-22)": option A; scope widened to `visually-hidden` and `d-inline-block`; the nine keys and defaults; the table keys over package CSS (and why); the behaviour tokens exempted and tracked in the follow-up issue from Task 4; the guard. Keep Summary and the "Why the existing guard does not catch it" section. Prepare the body with `gh issue edit 227 --body-file`; show the maintainer the new body before posting.

- [ ] **Step 4: Push and open the PR** following `.github/PULL_REQUEST_TEMPLATE.md`. Title `feat(buttons): the button chain's utility classes move into the class table (#227)`. Summary: the nine keys, the leaves, the guard, "no golden moves — a diff there is a bug", the `d-inline-block` removal. Related issue `Closes #227`. Type: New feature. Checklist ticked after Step 1. After the squash merge GitHub ticks #227 in #228's checklist; then `git fetch && git checkout main && git reset --hard origin/main && git fetch --prune`.
