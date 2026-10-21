# Card Button Label Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give inline card buttons a three-state label mode — label, icon, or both — selected by the card view and overridable per `CardAction`, with label + icon as the new default.

**Architecture:** One tri-valued vocabulary (`"label"` / `"icon"` / `"both"`) runs the whole depth: a `LabelMode` StrEnum beside the existing `Variant` one, `CardAction.label_mode` and `CardListView.cv_card_action_label_mode` as the author-facing layer, `cv_label_mode` as the single leaf-contract key replacing `cv_label_visible`, and a three-way branch in `tags/button/action.html`. `cv_get_card_action_data()` resolves the author layer into `cv_label_mode`; `cv_button_data()` reads only that key and raises if the removed `cv_no_label` reaches it.

**Tech Stack:** Python 3.12–3.15, Django 4.2 / 5.2 / 6.0, Pydantic v2, pytest + pytest-django, lxml for markup assertions, ruff.

**Spec:** `superpowers/specs/2026-10-21-card-button-label-mode-design.md` (commit `9989bd1`)

**Issue:** #213. Siblings: #209 (class-table key, unblocked by this), #216 (toolbar and row labels, deliberately out of scope).

## Global Constraints

- Line length 120; double quotes; `ruff format` on commit (pre-commit hook).
- All `CrudView` class attributes carry the `cv_` prefix.
- `cv_button_data()` must not mutate `ctx` — its docstring promises this and `tests/test1/test_button_data.py` asserts it with `copy.deepcopy`.
- Every key `cv_button_data()` returns must be in `LEAF_KEYS`; `tests/test1/test_button_data.py:136` asserts `set(data) <= LEAF_KEYS`.
- Non-card locations resolve to `"icon"` unconditionally. This is what keeps #216 out of scope; the five non-card goldens must not move.
- New system check id: `E210` (free; `E209` is `variant_check`, the neighbouring vocabulary check).
- Author-facing names are fixed by the spec: `CardAction.label_mode`, `CardListView.cv_card_action_label_mode`.

## Review Focus

Five things the spec implies that no task's happy path exercises. Each has a test added to the task that owns the code (all in Task 4).

1. **The `child_name` branch of `cv_get_card_action_data()`.** It writes `cv_no_label` at `views/card.py:59` separately from the `action.key` branch at line 77. Updating one and forgetting the other leaves cross-viewset card buttons raising `ValueError` at render time.
2. **A `cv_label_mode` that reaches `cv_button_data()` for a non-card location.** It must be ignored, not honoured, or #216 lands by accident and the toolbar goldens move.
3. **A disabled card action in `"both"` mode.** `cv_tag` becomes `button` and there is no `cv_href`; the label mode is orthogonal and must still apply. `cards_author_disabled.html` is the golden that covers it.
4. **A POST-only card action in `"both"` mode.** The `cv_submit_target` path renders a `button`, and an ordered up/down action is the real case.
5. **A card action folded into the overflow menu.** `menu_item_label.html` renders icon + short label regardless of `label_mode`; nothing here may change that, including for an action declared `label_mode="icon"`.

---

### Task 1: The label mode vocabulary

Mirrors `src/crud_views/lib/view/variant.py` exactly — same shape, same check style.

**Files:**
- Create: `src/crud_views/lib/view/label_mode.py`
- Test: `tests/test1/test_label_mode.py`

**Interfaces:**
- Consumes: `crud_views.lib.check.CheckExpression`
- Produces: `LabelMode` (StrEnum: `LABEL = "label"`, `ICON = "icon"`, `BOTH = "both"`), `LABEL_MODES: frozenset[str]`, `is_label_mode(value: object) -> bool`, `label_mode_check(context, owner: str, value) -> CheckExpression`

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from crud_views.lib.view.label_mode import LABEL_MODES, LabelMode, is_label_mode, label_mode_check

def test_label_modes():
    assert LABEL_MODES == {"label", "icon", "both"}

@pytest.mark.parametrize("value", ["label", "icon", "both"])
def test_is_label_mode_true(value):
    assert is_label_mode(value) is True

@pytest.mark.parametrize("value", ["Both", "", None, True, "no_label"])
def test_is_label_mode_false(value):
    assert is_label_mode(value) is False

def test_label_mode_check_message():
    check = label_mode_check(object(), "card action 'detail'", "nope")
    assert check.expression is False
    assert "card action 'detail'" in check.msg
    assert "'nope'" in check.msg
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test1/test_label_mode.py -v`
Expected: FAIL, `ModuleNotFoundError: crud_views.lib.view.label_mode`

- [ ] **Step 3: Implement `label_mode.py`**

Copy the structure of `variant.py`: `StrEnum`, the `frozenset` comprehension, `is_label_mode()` with the `isinstance(value, str)` guard (so `True` is rejected), and `label_mode_check()` returning `CheckExpression(context=context, id="E210", expression=is_label_mode(value), msg=f"{owner} label_mode must be one of {sorted(LABEL_MODES)}, got {value!r}")`.

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test1/test_label_mode.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/label_mode.py tests/test1/test_label_mode.py
git commit -m "feat(buttons): a label mode vocabulary beside the variant one (#213)"
```

---

### Task 2: `CardAction.label_mode`

The field only; nothing reads it yet, so rendering is unchanged and the tree stays green.

**Files:**
- Modify: `src/crud_views/lib/view/card.py`
- Test: `tests/test1/test_card_action_label_mode_field.py`

**Interfaces:**
- Consumes: Task 1's `is_label_mode`
- Produces: `CardAction.label_mode: str | None = None` — `None` means "inherit the view's `cv_card_action_label_mode`"

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from pydantic import ValidationError
from crud_views.lib.view import CardAction

def test_label_mode_defaults_to_none():
    assert CardAction(key="detail").label_mode is None

@pytest.mark.parametrize("mode", ["label", "icon", "both"])
def test_label_mode_accepted(mode):
    assert CardAction(key="detail", label_mode=mode).label_mode == mode

def test_unknown_label_mode_rejected():
    with pytest.raises(ValidationError, match="label_mode"):
        CardAction(key="detail", label_mode="nope")

def test_no_label_with_explicit_label_mode_rejected():
    with pytest.raises(ValidationError, match="no_label"):
        CardAction(key="detail", no_label=True, label_mode="label")

def test_no_label_alone_still_allowed():
    assert CardAction(key="detail", no_label=True).no_label is True
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test1/test_card_action_label_mode_field.py -v`
Expected: FAIL — `label_mode` is not a field, so pydantic ignores or rejects it depending on config

- [ ] **Step 3: Add the field and extend the validator**

Add `label_mode: str | None = None` with the inherit comment, beside the existing `no_label`. Add a second `@model_validator(mode="after")` (do not fold into `check_key_or_child`, which has its own job): reject an unknown value via `is_label_mode`, and reject `no_label=True` together with a non-`None` `label_mode` — the spec makes that a validation error rather than a precedence rule so a config mistake cannot hide.

The spec leaves `Literal["label", "icon", "both"]` versus a validated `str` to the builder. This plan picks `str | None` validated in the validator, to match the sibling field `variant: str | None` on the same model, which is checked by `variant_check` rather than typed as a `Literal`. Say so in the commit.

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test1/test_card_action_label_mode_field.py tests/test1/test_card.py -v`
Expected: PASS (the second file proves nothing else regressed)

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/card.py tests/test1/test_card_action_label_mode_field.py
git commit -m "feat(cards): CardAction.label_mode, with no_label kept as an alias (#213)"
```

---

### Task 3: `cv_card_action_label_mode` on the card view

The view attribute and its system check. Still unconsumed by rendering, so the tree stays green.

**Files:**
- Modify: `src/crud_views/lib/views/card.py` (class attributes, and `checks()` at lines 99-105)
- Test: `tests/test1/test_card_label_modes.py`

**Interfaces:**
- Consumes: Task 1's `label_mode_check`
- Produces: `CardListView.cv_card_action_label_mode: str = "both"`

- [ ] **Step 1: Write the failing tests**

`tests/test1/test_variants.py` is the exact model — copy its shape: a module constant `E210 = "viewset.E210"`, a helper `def e210(checks) -> list[str]` filtering `m.id == E210` over `c.messages()`, and `CardListView` subclasses declared in the test module. There is no global registry of check ids to extend (`test_check_messages.py` tests the check *classes*, not the id set), so nothing else needs touching. Assert:

```python
def test_default_is_both():
    assert CardListView.cv_card_action_label_mode == "both"

def test_bad_view_label_mode_raises_e210():
    # a CardListView subclass with cv_card_action_label_mode = "nope" yields one E210
def test_bad_action_label_mode_raises_e210():
    # a view whose CardAction carries a label_mode that bypassed the field validator
def test_good_values_yield_no_check():
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test1/test_card_label_modes.py -v`
Expected: FAIL, `AttributeError: cv_card_action_label_mode`

- [ ] **Step 3: Add the attribute and wire the check**

Add `cv_card_action_label_mode: str = "both"` to `CardListView`, next to `cv_card_actions_inline`. In `checks()`, after the existing `variant_check` loop, yield `label_mode_check(cls, "cv_card_action_label_mode", cls.cv_card_action_label_mode)`, and inside the same `for action in cls.cv_card_actions` loop yield one for each action whose `label_mode is not None`, with the owner string in the existing style (`f"card action {action.key or action.child_name!r}"`).

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test1/test_card_label_modes.py tests/test1/test_variants.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/views/card.py tests/test1/test_card_label_modes.py
git commit -m "feat(cards): cv_card_action_label_mode on the card view, checked by E210 (#213)"
```

---

### Task 4: The contract switch

The whole behaviour change, atomic. The system is consistent before and after but not in between: `cv_button_data()` cannot stop producing `cv_label_visible` while `action.html` still reads it, and `cv_get_card_action_data()` cannot keep writing `cv_no_label` once `cv_button_data()` raises on it. So the four files move together.

**Files:**
- Modify: `src/crud_views/lib/view/button_data.py` (`LEAF_KEYS`, and `cv_button_data()` lines 36-75)
- Modify: `src/crud_views/lib/views/card.py` (`cv_get_card_action_data()`, both branches: line 59 and line 77)
- Modify: `src/crud_views/templates/crud_views/tags/button/action.html` (the final line)
- Modify: `tests/test1/test_button_data.py` (lines 86-109)
- Create: `tests/test1/test_card_label_mode.py`
- Modify: `tests/test1/golden/action_menus/cards_author_full.html`, `cards_author_disabled.html`, `cards_publisher_child.html`

**Interfaces:**
- Consumes: Task 2's `CardAction.label_mode`, Task 3's `cv_card_action_label_mode`
- Produces: `cv_label_mode` in `LEAF_KEYS` (one of `"label"` / `"icon"` / `"both"`, always present); `cv_label_visible` is gone from the contract

- [ ] **Step 1: Write the failing unit tests in `tests/test1/test_button_data.py`**

Replace `test_card_label_visible` and `test_card_label_hidden` (lines 86-97) and update `test_label_never_visible` (lines 107-109):

```python
def test_card_label_mode_defaults_to_both():
    data = cv_button_data(base(cv_label="Details"), "card")
    assert data["cv_label_mode"] == "both"
    assert "cv_title" not in data

@pytest.mark.parametrize("mode", ["label", "icon", "both"])
def test_card_label_mode_passes_through(mode):
    data = cv_button_data(base(cv_label="Details", cv_label_mode=mode), "card")
    assert data["cv_label_mode"] == mode

def test_card_icon_mode_gets_title():
    data = cv_button_data(base(cv_label="Details", cv_label_mode="icon"), "card")
    assert data["cv_title"] == "Details"

def test_card_empty_label_forces_icon():
    data = cv_button_data({"cv_label": "", "cv_key": "", "cv_url": "/u/", "cv_label_mode": "both"}, "card")
    assert data["cv_label_mode"] == "icon"

def test_cv_no_label_in_ctx_raises():
    with pytest.raises(ValueError, match="cv_no_label"):
        cv_button_data(base(cv_label="Details", cv_no_label=True), "card")

# Review Focus 2
@pytest.mark.parametrize("location", ["context", "list"])
def test_label_mode_always_icon_off_cards(location):
    data = cv_button_data(base(cv_label_mode="both"), location)
    assert data["cv_label_mode"] == "icon"
    assert data["cv_title"] == "Show"
```

- [ ] **Step 2: Write the failing end-to-end tests in `tests/test1/test_card_label_mode.py`**

Follow `tests/test1/test_action_menus_card.py`: `monkeypatch.setattr` on `AuthorCardListView.cv_card_actions`, a logged-in client with the permissions granted, `lxml_html.fromstring`, and per-`cv-key` assertions counting `.//i` and reading visible text.

```python
# the three states on one card, driven per action
def test_three_states_on_one_card():
    # CardAction(key="detail", label="Details", label_mode="both")  -> 1 icon, text "Details", no visually-hidden, no title
    # CardAction(key="update", label="Edit", label_mode="label")    -> 0 icons, text "Edit", no title
    # CardAction(key="delete", label="Delete", label_mode="icon")   -> 1 icon, visually-hidden "Delete", title="Delete"

def test_no_label_still_means_icon_only():
    # CardAction(key="delete", no_label=True) renders exactly as label_mode="icon"

def test_view_default_applies_and_action_overrides_it():
    # cv_card_action_label_mode = "label" on the view; one action with label_mode="both" wins

def test_both_without_an_icon_renders_label_only():
    # monkeypatch.setattr(AuthorPingView, "cv_icon_action", None) -- every concrete view class in the test
    # app sets cv_icon_action, so the None case has to be arranged rather than found.
    # Expect 0 icons, visible text, and markup identical to label_mode="label"

# Review Focus 1
def test_child_name_card_action_resolves_label_mode():
    # PublisherCardListView with CardAction(child_name="book", label="Books", label_mode="both")

# Review Focus 3
def test_disabled_card_action_in_both_mode():
    # CRUD_VIEWS_INACCESSIBLE_ACTIONS = "disable", no permission: <button disabled>, 1 icon, visible text

# Review Focus 4
def test_post_only_card_action_in_both_mode():
    # an ordered up/down action: <button data-cv-action="submit-form">, 1 icon, visible text

# Review Focus 5
def test_menu_item_ignores_label_mode():
    # label_mode="icon" action folded into the overflow menu via cv_card_actions_inline
    # still renders icon + short label from menu_item_label.html
```

- [ ] **Step 3: Run both to verify they fail**

Run: `pytest tests/test1/test_button_data.py tests/test1/test_card_label_mode.py -v`
Expected: FAIL — `KeyError: 'cv_label_mode'` from the unit tests, and the end-to-end tests finding no icons on labelled buttons

- [ ] **Step 4: Switch the leaf contract in `button_data.py`**

In `LEAF_KEYS`, replace `"cv_label_visible"` with `"cv_label_mode"`. In `cv_button_data()`, replace the `label_visible` computation at line 51 with:

```python
if "cv_no_label" in ctx:
    raise ValueError("cv_no_label is no longer a leaf input; use CardAction.label_mode or cv_label_mode")
if card:
    label_mode = ctx.get("cv_label_mode") or "both"
    if not label:
        label_mode = "icon"
else:
    label_mode = "icon"
```

Emit `"cv_label_mode": label_mode` in `data` where `cv_label_visible` was, and change the trailing guard at line 73 to `if label_mode == "icon":`.

- [ ] **Step 5: Resolve the author layer in `views/card.py`**

In both branches of `cv_get_card_action_data()`, replace `cv_no_label` with `cv_label_mode`, resolved as the spec states: `action.label_mode` if not `None`, else `"icon"` if `action.no_label`, else `self.cv_card_action_label_mode`. Extract it to one local or a small helper so the two branches cannot drift apart again — that drift is Review Focus 1.

- [ ] **Step 6: Switch the leaf template**

`tags/button/action.html`, final line, replacing the `cv_label_visible` branch:

```django
cv-key="{{ cv_key }}">{% if cv_label_mode == "icon" %}{% cv_icon cv_icon %}<span class="visually-hidden">{{ cv_label }}</span>{% elif cv_label_mode == "both" %}{% if cv_icon %}{% cv_icon cv_icon %} {% endif %}<span>{{ cv_label }}</span>{% else %}<span>{{ cv_label }}</span>{% endif %}</{{ cv_tag }}>
```

The `{% if cv_icon %}` guard keeps the separator space out of an iconless `"both"`, so it renders byte-identical to `"label"`.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest tests/test1/test_button_data.py tests/test1/test_card_label_mode.py -v`
Expected: PASS

- [ ] **Step 8: Regenerate the goldens, then prove the diff is confined**

```bash
CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py
git diff --stat tests/test1/golden/action_menus/
```

Expected: exactly three files changed — `cards_author_full.html`, `cards_author_disabled.html`, `cards_publisher_child.html`. `CV_UPDATE_GOLDEN=1` rewrites all eight unconditionally (`test_action_menus_golden.py:77-82`), so a diff in `list_full.html`, `list_disabled.html` or any `toolbar_*.html` is a real non-card regression and must be fixed, not committed. Read the three card diffs and confirm each labelled button gained one `<i>` and kept its text.

- [ ] **Step 9: Run the full suite**

Run: `pytest tests`
Expected: PASS. Expect failures first in `test_action_menus_card.py`, `test_card.py`, `test_inaccessible_actions_card.py`, `test_guardian_card.py` and `test_card_action_post.py` — any that assert on card button markup now see an added icon. Update those assertions; do not weaken them.

- [ ] **Step 10: Commit**

```bash
git add src/crud_views tests/test1
git commit -m "feat(cards)!: label_mode replaces cv_label_visible; labelled card buttons get their icon (#213)"
```

---

### Task 5: Documentation and changelog

**Files:**
- Modify: `docs/reference/buttons.md` (the `LEAF_KEYS` table at lines 213-214; the theme recipe at lines 267-300)
- Modify: `docs/reference/card-list-view.md` (the example at line 30; the `CardAction` field table at line 50; the view attribute section)
- Modify: `docs/reference/action_menus.md:84`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: `buttons.md` — the contract table**

Replace the `cv_label_visible` row with `cv_label_mode` (`"label"`, `"icon"` or `"both"`; always present; `"icon"` for every non-card location). Amend the `cv_title` row: present only when `cv_label_mode` is `"icon"`. State in the leaf listing that a renderer registered through the icon library config must emit `aria-hidden="true"` — `render_icon()` does (`icons.py:203`), and `"both"` relies on it so the visible `<span>` is the only accessible name.

- [ ] **Step 2: `buttons.md` — the theme recipe**

This block is **not** a stale copy of the bundled leaf; it is a deliberate `myapp_theme` override, and its intro at line 269 promises `button is-*` classes *and* the label of `primary` buttons next to the icon, so `is-active` and the `{% if cv_variant != "primary" %}` guard are the example's own customizations. Port it to `cv_label_mode` and keep what it demonstrates — because non-card locations resolve to `"icon"`, the variant guard ports verbatim and still does exactly what the prose says. Add a sentence that the card half of this trick is no longer a reason to override the leaf, and that the toolbar half stops being one when #216 lands. Rewrite the prose at line 299 ("keep the `cv_label_visible` branch") for `cv_label_mode`.

- [ ] **Step 3: `card-list-view.md` and `action_menus.md`**

Replace the `no_label` row (line 50) with `label_mode` (`str | None`, `None`, inherits the view) and keep a `no_label` row marked superseded — equivalent to `label_mode="icon"`, and an error if both are set. Document `cv_card_action_label_mode` (`str`, `"both"`) in the view attribute table, with the base-card-view-class note: a project that wants one policy everywhere subclasses rather than setting it per view. Update the example at line 30 to use `label_mode="icon"` on the delete action. In `action_menus.md:84`, list `label_mode` alongside `variant` and `flex` as inline-card-only.

- [ ] **Step 4: `CHANGELOG.md`**

Under `## Unreleased` → `### Breaking`, matching the existing entries' style:
- Labelled inline card buttons now render their icon as well as their text. `CardListView.cv_card_action_label_mode = "label"` restores the old markup for a view; `CardAction(label_mode="label")` for one button.
- `cv_label_visible` has left the leaf contract; `cv_label_mode` replaces it. A project override of `crud_views/tags/button/action.html` must branch on the new key.
- `cv_no_label` is no longer a `cv_button_data()` input and raises `ValueError` naming the replacement. `CardAction(no_label=True)` is unaffected.
- A new `viewset.E210` rejects an unknown `label_mode` or `cv_card_action_label_mode`.

- [ ] **Step 5: Verify the docs build and the examples still match**

Run: `task docs` (or `mkdocs build --strict`) and `pytest tests`
Expected: no broken links, no failures

- [ ] **Step 6: Commit**

```bash
git add docs CHANGELOG.md
git commit -m "docs: the three card button label modes and the E210 check (#213)"
```

---

### Task 6: Downstream acceptance in `tabler-test` (separate repo, after merge)

Not part of this change — the spec puts it outside scope — but `tabler-test` is the case that motivated the issue, so it is where the result is confirmed rather than assumed. Do this against the merged version, not the branch.

**Files (in `/home/alex/projects/alex/tabler-test`):**
- Modify: `customers/views.py:89-91`
- Modify: `docs/crud_views_tabler.md:90`
- Possibly modify: `crud_views_tabler/buttons.py`

- [ ] **Step 1: Confirm the default does the right thing with no code change**

`CustomerCardListView` declares `CardAction(key="detail", label="Open", ...)` and `CardAction(key="update", label="Edit")`. With the new default both should render icon + text. Load the card list and check.

- [ ] **Step 2: Move `delete` off the superseded alias**

`CardAction(key="delete", no_label=True, variant="tertiary")` → `label_mode="icon"`.

- [ ] **Step 3: Record what changed**

Remove the "Labelled card buttons ("Open", "Edit") | icon plus label | label only" row from the accepted-differences table at `docs/crud_views_tabler.md:90` — the difference is gone. The "Toolbar Create" row above it stays; that one is #216.

- [ ] **Step 4: Check whether `card:tertiary` is still honest**

`buttons.py` carries `# The demo's only tertiary card action is icon-only; btn-icon keeps it square.` That comment is still true after step 2, and the real fix is #209. Leave the entry alone and note in the commit that #209 is what retires the comment.

- [ ] **Step 5: Commit in `tabler-test`**

```bash
git commit -m "Theme: card actions move to label_mode; labelled card buttons get their icons back"
```
