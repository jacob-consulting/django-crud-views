# Action Overflow Menus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In list rows, the context toolbar and cards, actions not named in an "inline keys" list fold into one
Bootstrap `⋯` dropdown; with the default `None` every container renders exactly today's HTML.

**Architecture:** A pure splitter (`cv_split_actions`) turns already-resolved action data into an `ActionGroup`
(inline + menu). One group method per location builds the resolved items on the **rendering** view. Each container
template branches on `{% if group is None %}` — that branch is today's markup verbatim — and otherwise renders inline
items through the existing item templates followed by new overridable menu templates.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12–3.14, pydantic (settings / ViewSet), django-tables2, Bootstrap 5.3
bundle (Popper), Font Awesome 6, pytest + pytest-django, lxml for HTML assertions.

**Spec:** `superpowers/specs/2026-10-12-action-menus-design.md` — read it before starting any task.

## Global Constraints

- Branch: `action-menus-174` (already checked out; spec commits are on it).
- Default for every inline value is `None`; with `None` the rendered container HTML must equal today's
  (whitespace-normalized) — enforced by the golden test from Task 1, which must stay green after every task.
- Resolution order for inline keys: CrudView attribute → ViewSet field → setting; first value that `is not None`
  wins (`[]` is meaningful — never test truthiness).
- Resolution happens on the **rendering** view; #149's hide/disable keeps resolving on the target view via
  `cv_resolve_action` (`src/crud_views/lib/view/visibility.py`) before any split.
- New names (exact): settings `CRUD_VIEWS_LIST_ACTIONS_INLINE`, `CRUD_VIEWS_CONTEXT_ACTIONS_INLINE`,
  `CRUD_VIEWS_CARD_ACTIONS_INLINE`, `CRUD_VIEWS_ACTIONS_MENU_ICON` (default `"fa-solid fa-ellipsis"`); ViewSet fields
  `list_actions_inline`, `context_actions_inline`, `card_actions_inline`; view attributes `cv_list_actions_inline`,
  `cv_context_actions_inline` (CrudView), `cv_card_actions_inline` (CardListView).
- New check IDs: `crud_views.E105` (settings), `viewset.E208` (view attribute type), `viewset.W290` (unknown key,
  view-level attribute only). Do not reuse `E203` (retired).
- Disabled menu items are `<button type="button" class="dropdown-item" disabled data-cv-disabled="…">` — never
  `<a aria-disabled>` (SonarQube, PR #176).
- Toggle: `class="btn … dropdown-toggle cv-menu-toggle"`; caret hidden by one CSS rule in `table.css`.
- New translatable string: `"More actions"` → de `"Weitere Aktionen"`.
- Line length 120, double quotes, ruff format/check clean (`task format`, `task check`).
- Run package tests from the repo root: `pytest tests` (quick) — the full matrix is `task test`.
- Every commit message ends with ` (#174)`. No attribution lines.
- Every task's commit must leave `pytest tests` green.

## Review Focus

1. **Configured key ≠ resolved `cv_key`** — the default `home` context button resolves to `cv_key="list"`;
   `cv_context_actions_inline=["home"]` must keep it inline (matching uses the configured key). Test: Task 4.
2. **An inline key whose action is hidden for this user** — appears neither inline nor in the menu, and the group
   stays valid (no empty toggle). Test: Task 4.
3. **ViewSet/setting value naming keys a view lacks** (e.g. global `["detail", "up", "down"]`) — silently ignored
   at render time and never a W290. Test: Task 2.
4. **Tuple values** (`("detail",)`) in settings, ViewSet and view attributes — accepted everywhere a list is.
   Tests: Task 2 (checks), Task 3 (splitter).
5. **Several rows on one page** — each row's POST menu item targets its own hidden form (`cv_form_<viewset>_<key>_<pk>`),
   no cross-row collisions. Test: Task 5.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/crud_views/lib/view/action_menu.py` (new) | `ActionGroup`, `cv_split_actions`, `cv_context_button_foldable`, `cv_is_inline_keys`, `cv_inline_checks` |
| `src/crud_views/lib/check.py` | new `CheckWarningExpression` |
| `src/crud_views/lib/settings.py` | 4 new settings fields, `crud_views.E105` |
| `src/crud_views/lib/viewset/__init__.py` | 3 new ViewSet fields |
| `src/crud_views/lib/view/base.py` | 2 attributes, getters, E208/W290 checks, `cv_get_list_action_group`, `cv_get_context_action_group` |
| `src/crud_views/lib/views/card.py` | `cv_card_actions_inline`, getter, checks, `cv_get_card_action_data`, `cv_get_card_action_group` |
| `src/crud_views/templatetags/crud_views.py` | group tags, render tags, `cv_actions_menu`, `cv_render_menu_item`; refactor `cv_card_action`, `cv_context_action` |
| `src/crud_views/templates/crud_views/tags/actions_menu.html` (new) | wrapper + `<ul>` |
| `src/crud_views/templates/crud_views/tags/actions_menu_toggle.html` (new) | toggle button only |
| `src/crud_views/templates/crud_views/tags/actions_menu_item.html` (new) | one menu item |
| `src/crud_views/templates/crud_views/tags/actions_menu_item_label.html` (new) | icon + label of an item |
| `src/crud_views/templates/crud_views/columns/actions.html` | group branch (list rows) |
| `src/crud_views/templates/crud_views/tags/context_actions.html` | group branch (toolbar) |
| `src/crud_views/templates/crud_views/tags/card.html` | group branch (cards) |
| `src/crud_views/static/crud_views/css/table.css` | caret rule |
| `src/crud_views/locale/de/LC_MESSAGES/django.po/.mo` | "More actions" |
| `tests/test1/test_action_menus_*.py`, `tests/test1/golden/action_menus/*.html` | tests |
| `examples/bootstrap5/action_menus/` (new app) + project wiring | example |
| `docs/reference/action_menus.md` (new) + cross-links | docs |

---

### Task 1: Golden regression baseline

Captures today's container HTML **before any template changes**, so later tasks can prove the `None` path is
unchanged.

**Files:**
- Create: `tests/test1/test_action_menus_golden.py`
- Create: `tests/test1/golden/action_menus/*.html` (generated)

**Interfaces:**
- Consumes: nothing new.
- Produces: the golden test; later tasks only run it.

- [ ] **Step 1: Write the golden test**

```python
"""#174: with every inline value None, the action containers render exactly the pre-#174 HTML.

Golden files were captured from main before the container templates changed. Regenerate ONLY when a change to the
default (None) markup is intended: CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py
"""

import os
import re
import uuid
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Author, Publisher
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDeleteView,
    AuthorListView,
    AuthorUpdateView,
    AuthorUpView,
    cv_author,
    cv_book,
    cv_publisher,
)

GOLDEN_DIR = Path(__file__).parent / "golden" / "action_menus"
AUTHOR_PK = uuid.UUID("00000000-0000-4000-8000-000000000174")
PUBLISHER_PK = 174
LIST_ACTIONS = ["detail", "update", "delete", "up", "down", "ping"]


def _norm(markup: str) -> str:
    markup = re.sub(r'name="csrfmiddlewaretoken" value="[^"]*"', 'name="csrfmiddlewaretoken" value="CSRF"', markup)
    markup = re.sub(r">\s+<", "><", markup)
    return re.sub(r"\s+", " ", markup).strip()


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"golden_174_{uuid.uuid4().hex[:8]}", password="pw")
    for viewset, perms in grants:
        for perm in perms:
            user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def _fragments(client, url, xpath) -> str:
    resp = client.get(url)
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    nodes = doc.xpath(xpath)
    assert nodes, f"no node for {xpath} at {url}"
    return "\n".join(_norm(lxml_html.tostring(n, encoding="unicode")) for n in nodes)


def _compare(name: str, actual: str):
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN") == "1":
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(actual + "\n")
    assert actual == path.read_text().strip()


LIST_TD = "//td[.//fieldset[@cv-list-container]]"
TOOLBAR = "//fieldset[@cv-context-container]"
CARD = "//div[contains(@class, 'card') and contains(@class, 'mb-3')]"
FULL = (cv_author, ("view", "add", "change", "delete"))
VIEW_ONLY = (cv_author, ("view",))


@pytest.fixture
def objects(db):
    Author.objects.create(id=AUTHOR_PK, first_name="Douglas", last_name="Adams")
    Publisher.objects.create(id=PUBLISHER_PK, name="Penguin")


@pytest.fixture
def list_actions(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", LIST_ACTIONS)
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)


@pytest.mark.django_db
def test_list_rows_full(objects, list_actions):
    _compare("list_full", _fragments(_client([FULL]), reverse(cv_author.get_router_name("list")), LIST_TD))


@pytest.mark.django_db
def test_list_rows_disabled(objects, list_actions, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(AuthorUpView, "cv_inaccessible_actions", "disable")
    _compare("list_disabled", _fragments(_client([VIEW_ONLY]), reverse(cv_author.get_router_name("list")), LIST_TD))


@pytest.mark.django_db
def test_toolbar_detail_full(objects):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": AUTHOR_PK})
    _compare("toolbar_detail_full", _fragments(_client([FULL]), url, TOOLBAR))


@pytest.mark.django_db
def test_toolbar_detail_disabled(objects, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": AUTHOR_PK})
    _compare("toolbar_detail_disabled", _fragments(_client([VIEW_ONLY]), url, TOOLBAR))


@pytest.mark.django_db
def test_toolbar_list_with_filter(objects):
    url = reverse(cv_publisher.get_router_name("list"))
    _compare("toolbar_publisher_list", _fragments(_client([(cv_publisher, ("view", "add"))]), url, TOOLBAR))


@pytest.mark.django_db
def test_cards_author_full(objects, monkeypatch):
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [*AuthorCardListView.cv_card_actions, CardAction(key="ping", label="Ping")],
    )
    _compare("cards_author_full", _fragments(_client([FULL]), reverse(cv_author.get_router_name("card")), CARD))


@pytest.mark.django_db
def test_cards_author_disabled(objects, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    url = reverse(cv_author.get_router_name("card"))
    _compare("cards_author_disabled", _fragments(_client([VIEW_ONLY]), url, CARD))


@pytest.mark.django_db
def test_cards_publisher_child(objects):
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",))])
    _compare("cards_publisher_child", _fragments(client, reverse(cv_publisher.get_router_name("card")), CARD))
```

- [ ] **Step 2: Capture the golden files from the unchanged code**

Run: `CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py -v`
Expected: 8 passed; `tests/test1/golden/action_menus/` now holds 8 `.html` files.

If a scenario fails (e.g. a router name differs), fix the **test** (URL/xpath/fixture), never a package file.

- [ ] **Step 3: Inspect the captured files**

Run: `head -c 600 tests/test1/golden/action_menus/*.html`
Expected: each file contains real buttons (`cv-key="detail"` etc.); `list_full.html` contains
`data-cv-action="submit-form"` and `data-cv-modal="true"`; `list_disabled.html` contains `data-cv-disabled`;
`cards_publisher_child.html` contains `Books`; `toolbar_publisher_list.html` contains `cv-filter-toggle`. If a file
is empty or lacks these, the scenario does not exercise what it claims — fix the test and recapture.

- [ ] **Step 4: Verify without the env var**

Run: `pytest tests/test1/test_action_menus_golden.py -v` (run twice — the second run proves stability)
Expected: 8 passed both times.

- [ ] **Step 5: Commit**

```bash
git add tests/test1/test_action_menus_golden.py tests/test1/golden/action_menus
git commit -m "test: golden baseline for action containers (#174)"
```

---

### Task 2: Configuration, resolution and checks

**Files:**
- Create: `src/crud_views/lib/view/action_menu.py`
- Modify: `src/crud_views/lib/check.py` (add `CheckWarningExpression` after `CheckExpression`, ~line 260)
- Modify: `src/crud_views/lib/settings.py` (fields after `inaccessible_actions` ~line 47; filter icon block; E105
  after E104 in `check_messages`)
- Modify: `src/crud_views/lib/viewset/__init__.py:77` (fields after `inaccessible_actions`)
- Modify: `src/crud_views/lib/view/base.py` (attributes after `cv_inaccessible_actions` ~line 76; checks after
  E207 ~line 156; getters after `cv_get_inaccessible_actions` ~line 221)
- Modify: `src/crud_views/lib/views/card.py` (attribute, getter, `checks`)
- Test: `tests/test1/test_action_menus_config.py`

**Interfaces:**
- Produces:
  - `crud_views.lib.view.action_menu.cv_is_inline_keys(value) -> bool`
  - `crud_views.lib.view.action_menu.cv_inline_checks(cls, attribute: str, known_keys) -> Iterator[Check]`
  - `CrudView.cv_get_list_actions_inline() -> Sequence[str] | None` (classmethod)
  - `CrudView.cv_get_context_actions_inline() -> Sequence[str] | None` (classmethod)
  - `CardListView.cv_get_card_actions_inline() -> Sequence[str] | None` (classmethod)
  - `crud_views_settings.actions_menu_icon: str`

- [ ] **Step 1: Write the failing tests**

`tests/test1/test_action_menus_config.py`:

```python
"""#174: inline-keys settings, ViewSet fields, view attributes, resolution and checks."""

import pytest
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.view import CardAction
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDetailView,
    AuthorListView,
    cv_author,
)


def test_settings_defaults():
    s = CrudViewsSettings()
    assert s.list_actions_inline is None
    assert s.context_actions_inline is None
    assert s.card_actions_inline is None
    assert s.actions_menu_icon == "fa-solid fa-ellipsis"


@pytest.mark.parametrize("field", ["list_actions_inline", "context_actions_inline", "card_actions_inline"])
@pytest.mark.parametrize("value", ["detail", ["detail", 1], {"detail": True}, 3])
def test_invalid_setting_e105(field, value):
    messages = CrudViewsSettings(**{field: value}).check_messages
    assert [m.id for m in messages] == ["crud_views.E105"]
    assert f"CRUD_VIEWS_{field.upper()}" in messages[0].msg


@pytest.mark.parametrize("value", [None, [], ["detail"], ("detail", "up")])
def test_valid_setting_values(value):
    assert CrudViewsSettings(list_actions_inline=value).check_messages == []


def test_viewset_rejects_invalid_value():
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import Author

    with pytest.raises(ValidationError):
        ViewSet(model=Author, name="author_bad_inline_174", list_actions_inline="detail")


def test_viewset_accepts_tuple():
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import Author

    vs = ViewSet(model=Author, name="author_tuple_inline_174", context_actions_inline=("update",))
    assert list(vs.context_actions_inline) == ["update"]


def test_default_resolves_to_none():
    assert AuthorListView.cv_get_list_actions_inline() is None
    assert AuthorDetailView.cv_get_context_actions_inline() is None
    assert AuthorCardListView.cv_get_card_actions_inline() is None


def test_setting_is_last_fallback(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "list_actions_inline", ["detail"])
    assert AuthorListView.cv_get_list_actions_inline() == ["detail"]


def test_viewset_beats_setting(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_inline", ["detail"])
    monkeypatch.setattr(cv_author, "context_actions_inline", ["update"])
    assert AuthorDetailView.cv_get_context_actions_inline() == ["update"]


def test_view_empty_list_beats_viewset(monkeypatch):
    # [] is meaningful ("fold everything"): it must not fall through like a falsy value
    monkeypatch.setattr(cv_author, "card_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", [])
    assert AuthorCardListView.cv_get_card_actions_inline() == []


def _ids(view_cls) -> list[str]:
    return [m.id for c in view_cls.checks() for m in c.messages()]


@pytest.mark.parametrize(
    ("view_cls", "attr"),
    [
        (AuthorListView, "cv_list_actions_inline"),
        (AuthorDetailView, "cv_context_actions_inline"),
        (AuthorCardListView, "cv_card_actions_inline"),
    ],
)
@pytest.mark.parametrize("value", ["detail", ["detail", None]])
def test_e208_invalid_view_value(monkeypatch, view_cls, attr, value):
    monkeypatch.setattr(view_cls, attr, value)
    assert "viewset.E208" in _ids(view_cls)


def test_no_inline_messages_by_default():
    for view_cls in (AuthorListView, AuthorDetailView, AuthorCardListView):
        ids = _ids(view_cls)
        assert "viewset.E208" not in ids
        assert "viewset.W290" not in ids


def test_w290_unknown_list_key(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail", "detial"])
    messages = [m for c in AuthorListView.checks() for m in c.messages() if m.id == "viewset.W290"]
    assert len(messages) == 1
    assert "detial" in messages[0].msg
    assert messages[0].level == 30  # django.core.checks.WARNING


def test_w290_known_keys_no_warning(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ("detail", "update"))
    assert "viewset.W290" not in _ids(AuthorListView)


def test_w290_context_key(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["home", "upd"])
    assert "viewset.W290" in _ids(AuthorDetailView)


def test_w290_card_matches_key_and_child_name(monkeypatch):
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [CardAction(key="detail"), CardAction(child_name="book", label="Books")],
    )
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail", "book"])
    assert "viewset.W290" not in _ids(AuthorCardListView)
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["books"])
    assert "viewset.W290" in _ids(AuthorCardListView)


def test_w290_never_for_viewset_or_setting(monkeypatch):
    # shared defaults name keys some views lack (Review Focus 3): no warning, and no render-time error
    monkeypatch.setattr(cv_author, "list_actions_inline", ["detail", "up", "down"])
    monkeypatch.setattr(crud_views_settings, "context_actions_inline", ["nonexistent"])
    for view_cls in (AuthorListView, AuthorDetailView):
        assert "viewset.W290" not in _ids(view_cls)
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test1/test_action_menus_config.py -v`
Expected: FAIL — `AttributeError`/`ValidationError` (no `list_actions_inline` field etc.).

- [ ] **Step 3: Add `CheckWarningExpression`** to `src/crud_views/lib/check.py`, directly after `CheckExpression`:

```python
class CheckWarningExpression(CheckExpression):
    """Like CheckExpression, but reports a warning instead of an error."""

    def messages(self) -> Iterable[CheckMessage]:
        if not self.expression:
            yield DjangoWarning(id=f"viewset.{self.id}", msg=f"{self.msg} at {self.context}")
```

- [ ] **Step 4: Create `src/crud_views/lib/view/action_menu.py`** (validation + checks only; the splitter comes in
  Task 3):

```python
"""Overflow menu for list, context and card actions (#174)."""

from collections.abc import Iterable, Iterator
from typing import Any

from crud_views.lib.check import Check, CheckExpression, CheckWarningExpression


def cv_is_inline_keys(value: Any) -> bool:
    """True for a valid inline-keys value: None, or a list/tuple of strings."""
    if value is None:
        return True
    return isinstance(value, (list, tuple)) and all(isinstance(key, str) for key in value)


def cv_inline_checks(cls, attribute: str, known_keys: Iterable[str] | None) -> Iterator[Check]:
    """viewset.E208 / viewset.W290 for a view's own cv_*_actions_inline attribute.

    Only the attribute set on the view class is checked for unknown keys: ViewSet and setting values are shared
    defaults, so keys missing on some views are expected there.
    """
    value = getattr(cls, attribute)
    valid = cv_is_inline_keys(value)
    yield CheckExpression(
        context=cls,
        id="E208",
        expression=valid,
        msg=f"{attribute} must be None or a list of strings, got {value!r}",
    )
    if not valid or value is None:
        return
    known = list(known_keys or [])
    unknown = [key for key in value if key not in known]
    yield CheckWarningExpression(
        context=cls,
        id="W290",
        expression=not unknown,
        msg=f"{attribute} names {unknown!r}, which are not among this view's actions {known!r} (typo?)",
    )
```

- [ ] **Step 5: Settings** — in `src/crud_views/lib/settings.py`, add after the `inaccessible_actions` field:

```python
    # overflow menu (#174): keys that stay inline buttons; None = no menu. Overridable per ViewSet
    # (*_actions_inline) and per view (cv_*_actions_inline), resolved on the rendering view
    list_actions_inline: Any = from_settings("CRUD_VIEWS_LIST_ACTIONS_INLINE", default=None)
    context_actions_inline: Any = from_settings("CRUD_VIEWS_CONTEXT_ACTIONS_INLINE", default=None)
    card_actions_inline: Any = from_settings("CRUD_VIEWS_CARD_ACTIONS_INLINE", default=None)
    actions_menu_icon: str = from_settings("CRUD_VIEWS_ACTIONS_MENU_ICON", default="fa-solid fa-ellipsis")
```

and in `check_messages`, directly after the E104 block:

```python
        # deferred import: settings.py must not import the view package at module level
        from crud_views.lib.view.action_menu import cv_is_inline_keys

        for setting, value in (
            ("CRUD_VIEWS_LIST_ACTIONS_INLINE", self.list_actions_inline),
            ("CRUD_VIEWS_CONTEXT_ACTIONS_INLINE", self.context_actions_inline),
            ("CRUD_VIEWS_CARD_ACTIONS_INLINE", self.card_actions_inline),
        ):
            if not cv_is_inline_keys(value):
                messages.append(
                    Error(
                        id="crud_views.E105",
                        msg=f"setting {setting} must be None or a list of strings, got {value!r}",
                    )
                )
```

(`Any` is already imported from `typing` in settings.py.)

- [ ] **Step 6: ViewSet fields** — `src/crud_views/lib/viewset/__init__.py`, after `inaccessible_actions`:

```python
    # overflow menu (#174): keys that stay inline buttons; None: CRUD_VIEWS_*_ACTIONS_INLINE
    list_actions_inline: list[str] | tuple[str, ...] | None = None
    context_actions_inline: list[str] | tuple[str, ...] | None = None
    card_actions_inline: list[str] | tuple[str, ...] | None = None
```

- [ ] **Step 7: CrudView attributes, getters, checks** — `src/crud_views/lib/view/base.py`.

Import (next to `from .visibility import cv_resolve_action`):

```python
from .action_menu import cv_inline_checks
```

Attributes, after `cv_inaccessible_actions`:

```python
    cv_list_actions_inline: list[str] | None = None  # list row keys kept as buttons; None: ViewSet, then setting
    cv_context_actions_inline: list[str] | None = None  # toolbar keys kept as buttons; None: ViewSet, then setting
```

Checks, in `checks()` directly after the E207 `CheckExpression`:

```python
        yield from cv_inline_checks(cls, "cv_list_actions_inline", cls.cv_list_actions)
        yield from cv_inline_checks(cls, "cv_context_actions_inline", cls.cv_context_actions)
```

Getters, after `cv_get_inaccessible_actions`:

```python
    @classmethod
    def cv_first_inline_keys(cls, view_value, viewset_field: str):
        """First inline-keys value that is not None: view, then ViewSet, then setting (#174)."""
        if view_value is not None:
            return view_value
        if cls.cv_viewset is not None and getattr(cls.cv_viewset, viewset_field) is not None:
            return getattr(cls.cv_viewset, viewset_field)
        return getattr(crud_views_settings, viewset_field)

    @classmethod
    def cv_get_list_actions_inline(cls):
        """List row keys kept as buttons, the rest go into the menu; None: no menu (#174)."""
        return cls.cv_first_inline_keys(cls.cv_list_actions_inline, "list_actions_inline")

    @classmethod
    def cv_get_context_actions_inline(cls):
        """Context toolbar keys kept as buttons, the rest go into the menu; None: no menu (#174)."""
        return cls.cv_first_inline_keys(cls.cv_context_actions_inline, "context_actions_inline")
```

- [ ] **Step 8: CardListView** — `src/crud_views/lib/views/card.py`. Imports:

```python
from collections.abc import Iterable

from crud_views.lib.check import Check
from crud_views.lib.view.action_menu import cv_inline_checks
```

Attribute after `cv_card_actions`:

```python
    cv_card_actions_inline: list[str] | None = None  # card action keys kept as buttons (#174)
```

Methods (place after `cv_get_filter_icon`):

```python
    @classmethod
    def cv_get_card_actions_inline(cls):
        """Card action keys (CardAction.key, or child_name) kept as buttons; None: no menu (#174)."""
        return cls.cv_first_inline_keys(cls.cv_card_actions_inline, "card_actions_inline")

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        keys = [action.key or action.child_name for action in cls.cv_card_actions]
        yield from cv_inline_checks(cls, "cv_card_actions_inline", keys)
```

- [ ] **Step 9: Run tests**

Run: `pytest tests/test1/test_action_menus_config.py tests/test1/test_action_menus_golden.py -v`
Expected: all PASS.

Run: `pytest tests -q -p no:randomly 2>&1 | tail -3` then `pytest tests -q 2>&1 | tail -3`
Expected: all pass (in particular `test_check_messages.py` and the W280 unknown-attribute tests).

- [ ] **Step 10: Lint and commit**

```bash
task format && task check
git add src/crud_views/lib tests/test1/test_action_menus_config.py
git commit -m "feat: inline-keys configuration and checks for action menus (#174)"
```

---

### Task 3: The pure splitter

**Files:**
- Modify: `src/crud_views/lib/view/action_menu.py`
- Test: `tests/test1/test_action_menus_split.py`

**Interfaces:**
- Produces:
  - `ActionGroup` dataclass: `inline: list[dict]`, `menu: list[dict]`, property `all -> list[dict]`
  - `cv_split_actions(items: list[tuple[str, dict]], inline_keys, foldable=None) -> ActionGroup | None`
  - `cv_context_button_foldable(ctx: dict) -> bool`

- [ ] **Step 1: Write the failing tests**

```python
"""#174: cv_split_actions / ActionGroup / cv_context_button_foldable."""

import copy

import pytest

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.action_menu import ActionGroup, cv_context_button_foldable, cv_split_actions


def _items(*keys):
    return [(key, {"cv_key": key}) for key in keys]


def _keys(ctxs):
    return [c["cv_key"] for c in ctxs]


def test_none_means_feature_off():
    assert cv_split_actions(_items("detail", "update"), None) is None


def test_empty_list_folds_everything():
    group = cv_split_actions(_items("detail", "update", "delete"), [])
    assert _keys(group.inline) == []
    assert _keys(group.menu) == ["detail", "update", "delete"]


def test_named_keys_stay_inline_order_kept():
    group = cv_split_actions(_items("detail", "update", "delete", "up", "down"), ["down", "detail"])
    # inline keeps the action order, not the inline-list order
    assert _keys(group.inline) == ["detail", "down"]
    assert _keys(group.menu) == ["update", "delete", "up"]


def test_tuple_inline_keys():
    group = cv_split_actions(_items("detail", "update"), ("detail",))
    assert _keys(group.inline) == ["detail"]


def test_unknown_inline_key_ignored():
    group = cv_split_actions(_items("detail", "update"), ["nope"])
    assert _keys(group.inline) == []
    assert _keys(group.menu) == ["detail", "update"]


def test_matches_configured_key_not_cv_key():
    # ContextButton(key="home", key_target="list") resolves to cv_key="list"
    group = cv_split_actions([("home", {"cv_key": "list"}), ("update", {"cv_key": "update"})], ["home"])
    assert _keys(group.inline) == ["list"]


def test_disabled_items_split_like_others():
    items = [("detail", {"cv_key": "detail"}), ("delete", {"cv_key": "delete", "cv_disabled": True})]
    group = cv_split_actions(items, ["detail"])
    assert group.menu == [{"cv_key": "delete", "cv_disabled": True}]


def test_unfoldable_stays_inline_under_empty_list():
    items = [("filter", {"cv_key": "filter", "pin": True}), ("update", {"cv_key": "update"})]
    group = cv_split_actions(items, [], foldable=lambda ctx: not ctx.get("pin"))
    assert _keys(group.inline) == ["filter"]
    assert _keys(group.menu) == ["update"]


def test_input_not_mutated():
    items = _items("detail", "update")
    before = copy.deepcopy(items)
    cv_split_actions(items, ["detail"])
    assert items == before


def test_all_is_inline_then_menu():
    group = ActionGroup(inline=[{"a": 1}], menu=[{"b": 2}])
    assert group.all == [{"a": 1}, {"b": 2}]


@pytest.mark.parametrize(
    ("ctx", "expected"),
    [
        ({"cv_template": None}, True),
        ({}, True),
        ({"cv_template": "DEFAULT"}, True),
        ({"cv_template": "my/button.html"}, False),
        ({"cv_template": "DEFAULT", "cv_template_code": "<b>x</b>"}, False),
    ],
)
def test_context_button_foldable(ctx, expected):
    ctx = {k: (crud_views_settings.context_button_template if v == "DEFAULT" else v) for k, v in ctx.items()}
    assert cv_context_button_foldable(ctx) is expected


def test_filter_button_template_is_not_foldable():
    ctx = {"cv_template": f"{crud_views_settings.theme_path}/tags/context_action_filter.html"}
    assert cv_context_button_foldable(ctx) is False
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test1/test_action_menus_split.py -v`
Expected: FAIL — `ImportError: cannot import name 'ActionGroup'`.

- [ ] **Step 3: Implement** — add to `src/crud_views/lib/view/action_menu.py` (extend the imports):

```python
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field

from crud_views.lib.settings import crud_views_settings


@dataclass
class ActionGroup:
    """Resolved action data of one container, split into inline buttons and menu items (#174)."""

    inline: list[dict] = field(default_factory=list)
    menu: list[dict] = field(default_factory=list)

    @property
    def all(self) -> list[dict]:
        """Inline items, then menu items (e.g. for the hidden POST form loop)."""
        return [*self.inline, *self.menu]


def cv_split_actions(
    items: Iterable[tuple[str, dict]],
    inline_keys: Sequence[str] | None,
    foldable: Callable[[dict], bool] | None = None,
) -> ActionGroup | None:
    """Split resolved (match_key, data) pairs into inline buttons and menu items.

    None when inline_keys is None (feature off). An item stays inline when its configured key is in inline_keys
    or foldable(data) is False; everything else goes to the menu. Both lists keep the input order. Hidden actions
    must already be dropped (cv_resolve_action). Never mutates the data dicts.
    """
    if inline_keys is None:
        return None
    keep = set(inline_keys)
    group = ActionGroup()
    for key, ctx in items:
        if key in keep or (foldable is not None and not foldable(ctx)):
            group.inline.append(ctx)
        else:
            group.menu.append(ctx)
    return group


def cv_context_button_foldable(ctx: dict) -> bool:
    """A context button can go into the menu unless it renders a whole custom button (template / template_code),
    e.g. the filter toggle."""
    if ctx.get("cv_template_code"):
        return False
    return ctx.get("cv_template") in (None, crud_views_settings.context_button_template)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test1/test_action_menus_split.py tests/test1/test_action_menus_config.py -v`
Expected: PASS. Then `pytest tests -q 2>&1 | tail -3` — all pass (watch for an import cycle: `settings` imports
`action_menu` only inside `check_messages`).

- [ ] **Step 5: Commit**

```bash
task format && task check
git add src/crud_views/lib/view/action_menu.py tests/test1/test_action_menus_split.py
git commit -m "feat: cv_split_actions splits resolved actions into inline and menu (#174)"
```

---

### Task 4: Group methods on the rendering views

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (after `cv_get_context_buttons`, ~line 463)
- Modify: `src/crud_views/lib/views/card.py`
- Modify: `src/crud_views/templatetags/crud_views.py:326-370` (`cv_card_action` delegates to the view)
- Test: `tests/test1/test_action_menus_groups.py`

**Interfaces:**
- Consumes: `cv_split_actions`, `cv_context_button_foldable`, `ActionGroup` (Task 3); getters (Task 2).
- Produces:
  - `CrudView.cv_get_list_action_group(obj) -> ActionGroup | None`
  - `CrudView.cv_get_context_action_group(obj=None) -> ActionGroup | None`
  - `CardListView.cv_get_card_action_data(action: CardAction, obj, user) -> dict` (unresolved data)
  - `CardListView.cv_get_card_action_group(obj) -> ActionGroup | None`

- [ ] **Step 1: Write the failing tests**

```python
"""#174: group methods resolve on the rendering view and split by configured key."""

import pytest
from django.urls import reverse

from crud_views.lib.view import CardAction
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDeleteView,
    AuthorDetailView,
    AuthorListView,
    PublisherCardListView,
    cv_author,
    cv_publisher,
)


def _view(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


def _keys(ctxs):
    return [c["cv_key"] for c in ctxs]


@pytest.fixture
def list_view(client_user_author_view, author_douglas_adams):
    return _view(client_user_author_view, reverse(cv_author.get_router_name("list")))


@pytest.fixture
def detail_view(client_user_author_view, author_douglas_adams):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author_douglas_adams.pk})
    return _view(client_user_author_view, url)


@pytest.mark.django_db
def test_list_group_none_by_default(list_view, author_douglas_adams):
    assert list_view.cv_get_list_action_group(author_douglas_adams) is None


@pytest.mark.django_db
def test_list_group_hidden_actions_absent(list_view, author_douglas_adams, monkeypatch):
    # view-only user: update/delete are hidden (default "hide") -> appear nowhere (Review Focus 2)
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail", "update"])
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.inline) == ["detail"]
    assert group.menu == []


@pytest.mark.django_db
def test_list_group_disabled_go_to_menu(list_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.menu) == ["delete"]
    assert group.menu[0]["cv_disabled"] is True


@pytest.mark.django_db
def test_list_group_unregistered_key_skipped(list_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "not_registered"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", [])
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.menu) == ["detail"]


@pytest.mark.django_db
def test_context_group_home_matches_configured_key(detail_view, author_douglas_adams, monkeypatch):
    # Review Focus 1: "home" resolves to cv_key "list" but is matched by its configured key
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["home"])
    group = detail_view.cv_get_context_action_group(author_douglas_adams)
    assert _keys(group.inline) == ["list"]
    assert _keys(group.menu) == ["detail"]


@pytest.mark.django_db
def test_context_group_resolves_on_rendering_view(detail_view, author_douglas_adams, monkeypatch):
    # an inline value on the TARGET (list) view must not matter for the detail toolbar
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail"])
    monkeypatch.setattr(AuthorListView, "cv_context_actions_inline", [])
    assert detail_view.cv_get_context_action_group(author_douglas_adams) is None


@pytest.mark.django_db
def test_card_group_by_key_and_child_name(client, user_publisher_view, publisher_penguin, monkeypatch, cv_book):
    from tests.lib.helper.user import user_viewset_permission

    # grant the child (book) permission BEFORE the request, so the child card action is accessible
    user_viewset_permission(user_publisher_view, cv_book, "view")
    client.force_login(user_publisher_view)
    view = _view(client, reverse(cv_publisher.get_router_name("card")))
    monkeypatch.setattr(PublisherCardListView, "cv_card_actions_inline", ["detail"])
    group = view.cv_get_card_action_group(publisher_penguin)
    assert [c["cv_label"] for c in group.inline] == ["Details"]
    assert [c["cv_label"] for c in group.menu] == ["Books"]


@pytest.mark.django_db
def test_card_tag_and_group_share_data(client_user_author_view, author_douglas_adams, monkeypatch):
    view = _view(client_user_author_view, reverse(cv_author.get_router_name("card")))
    action = CardAction(key="detail", label="Details", variant="primary", flex=True)
    data = view.cv_get_card_action_data(action, author_douglas_adams, view.request.user)
    assert data["cv_label"] == "Details"
    assert data["cv_variant"] == "primary"
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [action])
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", [])
    group = view.cv_get_card_action_group(author_douglas_adams)
    assert group.menu[0]["cv_url"] == data["cv_url"]
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test1/test_action_menus_groups.py -v`
Expected: FAIL — `AttributeError: … has no attribute 'cv_get_list_action_group'`.

- [ ] **Step 3: Group methods on CrudView** — `src/crud_views/lib/view/base.py`. Extend the import:

```python
from .action_menu import ActionGroup, cv_context_button_foldable, cv_inline_checks, cv_split_actions
```

After `cv_get_context_buttons`:

```python
    def cv_resolved_actions(self, keys: list[str] | None, obj=None) -> list[tuple[str, dict]]:
        """(configured key, resolved data) for each usable or disabled action; hidden and unregistered keys are
        skipped, as the per-key tags do (#174)."""
        items: list[tuple[str, dict]] = []
        for key in keys or []:
            try:
                ctx = self.cv_get_context(key=key, obj=obj, user=self.request.user, request=self.request)
            except ViewSetKeyFoundError:
                continue
            ctx = cv_resolve_action(ctx)
            if ctx is not None:
                items.append((key, ctx))
        return items

    def cv_get_list_action_group(self, obj) -> ActionGroup | None:
        """Row actions split into inline buttons and menu items; None: no menu, render the plain buttons (#174)."""
        inline = self.cv_get_list_actions_inline()
        if inline is None:
            return None
        return cv_split_actions(self.cv_resolved_actions(self.cv_list_actions, obj), inline)

    def cv_get_context_action_group(self, obj=None) -> ActionGroup | None:
        """Context toolbar split into inline buttons and menu items; buttons with their own template stay inline.
        None: no menu (#174)."""
        inline = self.cv_get_context_actions_inline()
        if inline is None:
            return None
        items = self.cv_resolved_actions(self.cv_context_actions, obj)
        return cv_split_actions(items, inline, foldable=cv_context_button_foldable)
```

(`ViewSetKeyFoundError` is already imported in base.py.)

- [ ] **Step 4: Card data + group** — `src/crud_views/lib/views/card.py`. Imports:

```python
from crud_views.lib.view.action_menu import ActionGroup, cv_inline_checks, cv_split_actions
from crud_views.lib.view.visibility import cv_resolve_action
```

Methods on `CardListView` — move the body of the `cv_card_action` tag here **verbatim**, minus the resolve:

```python
    def cv_get_card_action_data(self, action: CardAction, obj, user) -> dict:
        """Unresolved button data for one card action (#149, #174); the cv_card_action tag and the menu share it."""
        if action.child_name:
            url = self.cv_get_child_url(action.child_name, action.child_key, obj)
            child_viewset = self.cv_viewset.get_viewset(action.child_name)
            child_cls = child_viewset.get_view_class(action.child_key)
            # permission is checked on the child view, like ChildContextButton (#149)
            return {
                "cv_access": bool(child_cls.cv_has_access(user, obj)),
                "cv_action_enabled": child_cls.cv_action_enabled(user, obj),
                "cv_inaccessible_actions": child_cls.cv_get_inaccessible_actions(),
                "cv_url": url,
                "cv_label": action.label,
                "cv_icon_action": child_cls.cv_icon_action,
                "cv_variant": action.variant,
                "cv_flex": action.flex,
                "cv_no_label": action.no_label,
                "cv_list_action_method": "get",
            }

        cls = self.cv_viewset.get_view_class(action.key)
        url = self.cv_get_link_url(cls, action.key, obj)
        view_context = self.cv_get_view_context(object=obj)
        label = action.label or cls.cv_get_action_short_label(context=view_context)

        # always build the full data: disable mode renders label/icon/variant without access (#149)
        data = cls.cv_get_dict(
            context=view_context,
            cv_oid=self.cv_get_oid(action.key, obj=obj),
            cv_url=url,
            cv_access=bool(cls.cv_has_access(user, obj)),
            cv_action_enabled=cls.cv_action_enabled(user, obj),
        )
        data.update(cv_label=label, cv_variant=action.variant, cv_flex=action.flex, cv_no_label=action.no_label)
        return data

    def cv_get_card_action_group(self, obj) -> ActionGroup | None:
        """Card actions split into inline buttons and menu items, matched by CardAction.key or child_name.
        None: no menu (#174)."""
        inline = self.cv_get_card_actions_inline()
        if inline is None:
            return None
        items = []
        for action in self.cv_card_actions:
            ctx = cv_resolve_action(self.cv_get_card_action_data(action, obj, self.request.user))
            if ctx is not None:
                items.append((action.key or action.child_name, ctx))
        return cv_split_actions(items, inline)
```

Before moving, diff the moved body against the current tag (`src/crud_views/templatetags/crud_views.py:326-370`)
so nothing is lost; only `view.` → `self.` changes.

- [ ] **Step 5: Tag delegates** — replace the body of `cv_card_action` in `src/crud_views/templatetags/crud_views.py`:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/card_action.html", takes_context=True)
def cv_card_action(context, action, obj=None):
    view = cv_get_view(context)
    return cv_resolve_action(view.cv_get_card_action_data(action, obj, context["request"].user)) or {}
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test1/test_action_menus_groups.py tests/test1/test_action_menus_golden.py tests/test1/test_card.py tests/test1/test_inaccessible_actions_card.py tests/test1/test_guardian_card.py tests/test1/test_card_action_post.py -v`
Expected: PASS. Then `pytest tests -q 2>&1 | tail -3` — all pass.

- [ ] **Step 7: Commit**

```bash
task format && task check
git add src tests/test1/test_action_menus_groups.py
git commit -m "feat: action group methods on list, context and card views (#174)"
```

---

### Task 5: Menu templates, render tags, CSS, i18n — list rows

**Files:**
- Create: `src/crud_views/templates/crud_views/tags/actions_menu.html`
- Create: `src/crud_views/templates/crud_views/tags/actions_menu_toggle.html`
- Create: `src/crud_views/templates/crud_views/tags/actions_menu_item.html`
- Create: `src/crud_views/templates/crud_views/tags/actions_menu_item_label.html`
- Modify: `src/crud_views/templates/crud_views/columns/actions.html`
- Modify: `src/crud_views/templatetags/crud_views.py`
- Modify: `src/crud_views/static/crud_views/css/table.css`
- Modify: `src/crud_views/locale/de/LC_MESSAGES/django.po` (+ compiled `.mo`)
- Test: `tests/test1/test_action_menus_list.py`

**Interfaces:**
- Consumes: `CrudView.cv_get_list_action_group(obj)` (Task 4).
- Produces (template tags, all in `crud_views` library):
  - `{% cv_list_action_group record as group %}` → `ActionGroup | None`
  - `{% cv_render_list_action ctx %}`, `{% cv_render_list_action_form ctx %}` (inclusion tags)
  - `{% cv_actions_menu group "list"|"context"|"card" %}` (inclusion tag, renders nothing for an empty menu)
  - `{% cv_render_menu_item ctx location %}` (inclusion tag)
  - template context of `actions_menu.html`: `cv_menu_items`, `cv_location`, `cv_menu_wrapper_class`,
    `cv_toggle_class`, `cv_menu_icon`

- [ ] **Step 1: Write the failing tests**

```python
"""#174: overflow menu in list rows."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import translation
from lxml import html as lxml_html

from crud_views.lib.settings import crud_views_settings
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorDeleteView, AuthorListView, AuthorUpdateView, cv_author


@pytest.fixture
def client_full(db):
    user = User.objects.create_user(username="menu_full_174", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def menu_list(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update", "delete", "up", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])


def _rows(client):
    resp = client.get(reverse(cv_author.get_router_name("list")))
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    return doc.xpath("//td[.//fieldset[@cv-list-container]]")


@pytest.mark.django_db
def test_inline_and_menu(client_full, author_douglas_adams, menu_list):
    (td,) = _rows(client_full)
    fieldset = td.cssselect("fieldset")[0]
    inline = [el.get("cv-key") for el in fieldset.xpath("./*[@cv-key]")]
    assert inline == ["detail"]
    toggle = fieldset.cssselect("button.cv-menu-toggle")[0]
    assert toggle.get("data-bs-toggle") == "dropdown"
    assert "dropdown-toggle" in toggle.get("class")
    assert toggle.get("aria-expanded") == "false"
    assert toggle.get("aria-label") == "More actions"
    assert toggle.get("data-bs-popper-config") == '{"strategy":"fixed"}'
    assert toggle.cssselect("i")[0].get("class") == crud_views_settings.actions_menu_icon
    items = fieldset.cssselect("ul.dropdown-menu.dropdown-menu-end .dropdown-item")
    assert [i.get("cv-key") for i in items] == ["update", "delete", "up", "ping"]
    # wrapper is a nested button group so borders join the inline buttons
    assert toggle.getparent().get("class") == "btn-group"


@pytest.mark.django_db
def test_menu_items_have_visible_labels_and_fixed_width_icons(client_full, author_douglas_adams, menu_list):
    (td,) = _rows(client_full)
    update = td.cssselect('.dropdown-item[cv-key="update"]')[0]
    assert update.tag == "a"
    assert update.get("href").endswith("/update/")
    assert "fa-fw" in update.cssselect("i")[0].get("class")
    assert update.text_content().strip() != ""


@pytest.mark.django_db
def test_post_item_targets_hidden_form(client_full, author_douglas_adams, menu_list):
    (td,) = _rows(client_full)
    ping = td.cssselect('.dropdown-item[cv-key="ping"]')[0]
    assert ping.tag == "button"
    assert ping.get("data-cv-action") == "submit-form"
    target = ping.get("data-cv-target")
    forms = td.xpath(f'.//form[@id="{target}"]')
    assert len(forms) == 1
    assert forms[0].getparent().tag == "td"  # outside the menu
    assert forms[0].cssselect('input[name="csrfmiddlewaretoken"]')


@pytest.mark.django_db
def test_two_rows_post_targets_distinct(client_full, author_douglas_adams, author_terry_pratchett, menu_list):
    # Review Focus 5
    targets = []
    for td in _rows(client_full):
        target = td.cssselect('.dropdown-item[cv-key="ping"]')[0].get("data-cv-target")
        assert td.xpath(f'.//form[@id="{target}"]')
        targets.append(target)
    assert len(set(targets)) == 2


@pytest.mark.django_db
def test_modal_item(client_full, author_douglas_adams, menu_list, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    (td,) = _rows(client_full)
    delete = td.cssselect('.dropdown-item[cv-key="delete"]')[0]
    assert delete.get("data-cv-modal") == "true"
    assert delete.get("href")


@pytest.mark.django_db
def test_disabled_item(client_user_author_view, author_douglas_adams, menu_list, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    (td,) = _rows(client_user_author_view)
    update = td.cssselect('.dropdown-item[cv-key="update"]')[0]
    assert update.tag == "button"
    assert update.get("disabled") is not None
    assert update.get("data-cv-disabled") == "permission"
    assert update.get("href") is None
    assert update.get("data-cv-action") is None
    assert update.get("data-cv-modal") is None


@pytest.mark.django_db
def test_no_toggle_when_menu_empty(client_user_author_view, author_douglas_adams, menu_list):
    # view-only user, default hide mode: every menu candidate is hidden
    (td,) = _rows(client_user_author_view)
    assert td.cssselect(".cv-menu-toggle") == []
    assert td.cssselect(".dropdown-menu") == []


@pytest.mark.django_db
def test_toggle_shown_when_all_menu_items_disabled(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    (td,) = _rows(client_user_author_view)
    assert td.cssselect(".cv-menu-toggle")
    assert td.cssselect('.dropdown-item[cv-key="update"][disabled]')


@pytest.mark.django_db
def test_custom_menu_icon(client_full, author_douglas_adams, menu_list, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "actions_menu_icon", "fa-solid fa-bars")
    (td,) = _rows(client_full)
    assert td.cssselect(".cv-menu-toggle i")[0].get("class") == "fa-solid fa-bars"


@pytest.mark.django_db
def test_german_label(client_full, author_douglas_adams, menu_list):
    # the test project has no LocaleMiddleware: activate German around the request (as test_i18n.py does)
    with translation.override("de"):
        resp = client_full.get(reverse(cv_author.get_router_name("list")))
    assert 'aria-label="Weitere Aktionen"' in resp.content.decode()


def test_caret_rule_shipped():
    from pathlib import Path

    import crud_views

    css = (Path(crud_views.__file__).parent / "static/crud_views/css/table.css").read_text()
    assert ".cv-menu-toggle.dropdown-toggle::after" in css
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test1/test_action_menus_list.py -v`
Expected: FAIL — no `.cv-menu-toggle` (container has no group branch yet); `test_caret_rule_shipped` fails.

- [ ] **Step 3: Tags** — add to `src/crud_views/templatetags/crud_views.py` (after `cv_list_action_form`):

```python
@register.simple_tag(takes_context=True)
def cv_list_action_group(context, obj):
    """Row actions split into inline buttons and menu items; None: no menu (#174)."""
    return cv_get_view(context).cv_get_list_action_group(obj)


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action.html", takes_context=True)
def cv_render_list_action(context, ctx):
    """Render already-resolved row action data (#174)."""
    return ctx or {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
def cv_render_list_action_form(context, ctx):
    """Hidden POST form for already-resolved action data; nothing for a disabled action (#174)."""
    if not ctx or ctx.get("cv_disabled"):
        return {}
    return ctx


# (wrapper class, toggle button classes) per location: the toggle matches its neighbouring buttons (#174)
_ACTIONS_MENU_STYLE = {
    "list": ("btn-group", "btn-outline-primary btn-xs"),
    "context": ("btn-group", "btn-outline-primary btn-lg"),
    "card": ("dropdown", "btn-secondary btn-sm"),
}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/actions_menu.html", takes_context=True)
def cv_actions_menu(context, group, location):
    """The ⋯ dropdown for a group's menu items; renders nothing when there are none (#174)."""
    if group is None or not group.menu:
        return {}
    wrapper_class, toggle_class = _ACTIONS_MENU_STYLE[location]
    return {
        "cv_menu_items": group.menu,
        "cv_location": location,
        "cv_menu_wrapper_class": wrapper_class,
        "cv_toggle_class": toggle_class,
        "cv_menu_icon": crud_views_settings.actions_menu_icon,
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/actions_menu_item.html")
def cv_render_menu_item(ctx, location):
    """One dropdown item from resolved action data (#174)."""
    return {**ctx, "cv_location": location}
```

- [ ] **Step 4: Menu templates**

`src/crud_views/templates/crud_views/tags/actions_menu.html`:

```django
{% load crud_views %}
{% if cv_menu_items %}
<div class="{{ cv_menu_wrapper_class }}"{% if cv_location != "card" %} role="group"{% endif %}>
    {% include "crud_views/tags/actions_menu_toggle.html" %}
    <ul class="dropdown-menu dropdown-menu-end">
        {% for item in cv_menu_items %}<li>{% cv_render_menu_item item cv_location %}</li>{% endfor %}
    </ul>
</div>
{% endif %}
```

`src/crud_views/templates/crud_views/tags/actions_menu_toggle.html`:

```django
{% load i18n %}
<button type="button" class="btn {{ cv_toggle_class }} dropdown-toggle cv-menu-toggle"
        data-bs-toggle="dropdown" aria-expanded="false" aria-label="{% translate 'More actions' %}"
        {% if cv_location == "list" %}data-bs-popper-config='{"strategy":"fixed"}'{% endif %}>
    <i class="{{ cv_menu_icon }}" aria-hidden="true"></i><span class="visually-hidden">{% translate "More actions" %}</span>
</button>
```

`src/crud_views/templates/crud_views/tags/actions_menu_item.html`:

```django
{% if cv_disabled %}
<button type="button" class="dropdown-item" disabled
    data-cv-disabled="{{ cv_disabled_reason }}"
    {% if cv_location == "context" %}title="{{ cv_action_label }}"{% endif %}
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</button>
{% elif cv_modal %}
<a class="dropdown-item" href="{{ cv_url }}"
    data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}"
    {% if cv_location == "context" %}title="{{ cv_action_label }}"{% endif %}
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</a>
{% elif cv_list_action_method == "post" and cv_location != "context" %}
<button type="button" class="dropdown-item"
    data-cv-action="submit-form" data-cv-target="cv_form_{{ cv_oid }}"
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</button>
{% else %}
<a class="dropdown-item{% if cv_is_active %} active{% endif %}" href="{{ cv_url }}"
    {% if cv_is_active %}aria-current="page"{% endif %}
    {% if cv_location == "context" %}title="{{ cv_action_label }}"{% endif %}
    cv-key="{{ cv_key }}">{% include "crud_views/tags/actions_menu_item_label.html" %}</a>
{% endif %}
```

`src/crud_views/templates/crud_views/tags/actions_menu_item_label.html`:

```django
{% if cv_icon_action %}<i class="{{ cv_icon_action }} fa-fw" aria-hidden="true"></i>{% else %}<span class="fa-fw d-inline-block" aria-hidden="true"></span>{% endif %} {% if cv_location == "card" %}{% firstof cv_label cv_action_short_label cv_action_label %}{% else %}{% firstof cv_action_short_label cv_action_label %}{% endif %}
```

(The context toolbar renders GET links even for POST target views, like `context_action.html` — hence the
`cv_location != "context"` guard on the POST branch.)

- [ ] **Step 5: List container** — replace `src/crud_views/templates/crud_views/columns/actions.html` with
  (the first branch is the old file body, unchanged):

```django
{% load crud_views %}
{% cv_list_action_group record as group %}
{% if group is None %}

{% for key in view.cv_list_actions %}
    {% cv_list_action_form key record %}
{% endfor %}

<fieldset class="btn-group btn-group-xs" aria-label="Actions" cv-list-container="true">
    {% for key in view.cv_list_actions %}
        {% cv_list_action key record %}
    {% endfor %}
</fieldset>
{% else %}

{% for ctx in group.all %}
    {% cv_render_list_action_form ctx %}
{% endfor %}

<fieldset class="btn-group btn-group-xs" aria-label="Actions" cv-list-container="true">
    {% for ctx in group.inline %}
        {% cv_render_list_action ctx %}
    {% endfor %}
    {% cv_actions_menu group "list" %}
</fieldset>
{% endif %}
```

- [ ] **Step 6: CSS** — append to `src/crud_views/static/crud_views/css/table.css`:

```css
/* action overflow menu (#174): .dropdown-toggle keeps Bootstrap's button-group corner rounding; hide its caret */
.cv-menu-toggle.dropdown-toggle::after {
    display: none;
}
```

- [ ] **Step 7: Translation**

Run: `task msg-make` (repo root) — extracts "More actions" into `src/crud_views/locale/de/LC_MESSAGES/django.po`.
Set its `msgstr "Weitere Aktionen"` (remove any `#, fuzzy` flag on that entry). Then `task msg-comp`.
Review `git diff src/crud_views/locale` — only the new entry (and the POT-Creation-Date header) may change; revert
unrelated reordering if makemessages produced any.

- [ ] **Step 8: Run tests**

Run: `pytest tests/test1/test_action_menus_list.py tests/test1/test_action_menus_golden.py -v`
Expected: PASS. Then `pytest tests -q 2>&1 | tail -3` — all pass (the golden list scenarios prove the `None`
branch is unchanged).

- [ ] **Step 9: Commit**

```bash
task format && task check
git add src tests/test1/test_action_menus_list.py
git commit -m "feat: overflow menu for list row actions (#174)"
```

---

### Task 6: Context toolbar

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/context_actions.html`
- Modify: `src/crud_views/templatetags/crud_views.py` (`cv_context_action`, `cv_context_actions`; new
  `cv_render_context_action`)
- Test: `tests/test1/test_action_menus_context.py`

**Interfaces:**
- Consumes: `CrudView.cv_get_context_action_group(obj)` (Task 4); `cv_actions_menu` (Task 5).
- Produces: `{% cv_render_context_action ctx %}`; `cv_context_actions` inclusion context gains `group`.

- [ ] **Step 1: Write the failing tests**

```python
"""#174: overflow menu in the context toolbar."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import (
    AuthorDeleteView,
    AuthorDetailView,
    AuthorUpdateView,
    PublisherListView,
    cv_author,
    cv_publisher,
)


@pytest.fixture
def client_full(db):
    user = User.objects.create_user(username="toolbar_full_174", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


def _toolbar(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content).xpath("//fieldset[@cv-context-container]")[0]


def _detail_url(author):
    return reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})


@pytest.mark.django_db
def test_active_item_in_menu(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["update"])
    toolbar = _toolbar(client_full, _detail_url(author_douglas_adams))
    assert [el.get("cv-key") for el in toolbar.xpath("./*[@cv-key]")] == ["update"]
    toggle = toolbar.cssselect(".cv-menu-toggle")[0]
    assert "btn-lg" in toggle.get("class")
    assert toggle.get("data-bs-popper-config") is None
    detail = toolbar.cssselect('.dropdown-item[cv-key="detail"]')[0]
    assert "active" in detail.get("class").split()
    assert detail.get("aria-current") == "page"
    assert detail.get("title")  # cv_action_label as title
    home = toolbar.cssselect('.dropdown-item[cv-key="list"]')[0]
    assert home.get("aria-current") is None


@pytest.mark.django_db
def test_active_item_inline_keeps_active_class(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_context_actions", ["home", "detail", "update"])
    monkeypatch.setattr(AuthorUpdateView, "cv_context_actions_inline", ["update"])
    url = reverse(cv_author.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})
    toolbar = _toolbar(client_full, url)
    update = toolbar.xpath('./a[@cv-key="update"]')[0]
    assert "active" in update.get("class").split()


@pytest.mark.django_db
def test_disabled_item(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["home"])
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    toolbar = _toolbar(client_user_author_view, _detail_url(author_douglas_adams))
    delete = toolbar.cssselect('.dropdown-item[cv-key="delete"]')[0]
    assert delete.tag == "button"
    assert delete.get("disabled") is not None
    assert delete.get("data-cv-disabled") == "permission"
    assert delete.get("href") is None


@pytest.mark.django_db
def test_filter_toggle_never_folded(client_user_publisher_view, publisher_penguin, monkeypatch):
    monkeypatch.setattr(PublisherListView, "cv_context_actions_inline", [])
    toolbar = _toolbar(client_user_publisher_view, reverse(cv_publisher.get_router_name("list")))
    assert toolbar.xpath('./button[@id="cv-filter-toggle"]')
    assert not toolbar.cssselect('.dropdown-menu [cv-key="filter"]')


@pytest.mark.django_db
def test_custom_template_button_never_folded(client_full, author_douglas_adams, monkeypatch):
    from crud_views.lib.view import ContextButton

    custom = ContextButton(
        key="edit_big",
        key_target="update",
        template_code='<a href="{{ cv_url }}" class="cv-big" cv-key="{{ cv_key }}">Big</a>',
    )
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [custom])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "edit_big"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", [])
    toolbar = _toolbar(client_full, _detail_url(author_douglas_adams))
    assert toolbar.xpath('./a[contains(@class, "cv-big")]')
    assert [i.get("cv-key") for i in toolbar.cssselect(".dropdown-item")] == ["detail"]


@pytest.mark.django_db
def test_modal_item(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    toolbar = _toolbar(client_full, _detail_url(author_douglas_adams))
    delete = toolbar.cssselect('.dropdown-item[cv-key="delete"]')[0]
    assert delete.get("data-cv-modal") == "true"
```

If `AuthorDetailView` already defines `cv_context_buttons` differently, or `ContextButton` is not exported from
`crud_views.lib.view`, check `tests/test1/test_context_button_template.py` for the import path and adjust the test.

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test1/test_action_menus_context.py -v`
Expected: FAIL — no `.cv-menu-toggle` in the toolbar.

- [ ] **Step 3: Tags** — in `src/crud_views/templatetags/crud_views.py`, extract the rendering half of
  `cv_context_action` into a helper and add the new tag:

```python
def _render_context_action(context, ctx) -> str:
    """Render resolved context-button data: its template_code, its template, or the default button template."""
    if ctx.get("cv_template_code"):
        view = cv_get_view(context)
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    template = ctx.get("cv_template") or crud_views_settings.context_button_template
    return render_to_string(template, context=ctx, request=context["request"])


@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_action(context, key, obj=None):
    obj = obj if obj else None  # fix empty string from template
    # gate here, not only in the default template: per-button template / template_code must not show a
    # button the user may not use (#147); in disable mode they get cv_disabled data instead (#149)
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    if ctx is None:
        return ""
    return _render_context_action(context, ctx)


@register.simple_tag(takes_context=True)
def cv_render_context_action(context, ctx) -> str:
    """Render already-resolved context-button data exactly like cv_context_action does (#174)."""
    return _render_context_action(context, ctx)
```

and give the toolbar inclusion tag the group:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/context_actions.html", takes_context=True)
def cv_context_actions(context, obj=None):
    view: CrudView = cv_get_view(context)
    group = view.cv_get_context_action_group(obj if obj else None)
    return {"view": view, "request": context["request"], "object": obj, "group": group}
```

- [ ] **Step 4: Container** — replace `src/crud_views/templates/crud_views/tags/context_actions.html`:

```django
{% load crud_views %}

{% if view.cv_context_actions %}
{% if group is None %}

    <fieldset class="btn-group btn-group-lg" aria-label="Actions" cv-context-container="true">
        {% for key in view.cv_context_actions %}
            {% cv_context_action key object %}
        {% endfor %}
    </fieldset>

{% else %}

    <fieldset class="btn-group btn-group-lg" aria-label="Actions" cv-context-container="true">
        {% for ctx in group.inline %}
            {% cv_render_context_action ctx %}
        {% endfor %}
        {% cv_actions_menu group "context" %}
    </fieldset>

{% endif %}
{% endif %}
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test1/test_action_menus_context.py tests/test1/test_action_menus_golden.py tests/test1/test_context_button_tag.py tests/test1/test_context_button_template.py -v`
Expected: PASS. Then `pytest tests -q 2>&1 | tail -3` — all pass.

- [ ] **Step 6: Commit**

```bash
task format && task check
git add src tests/test1/test_action_menus_context.py
git commit -m "feat: overflow menu for the context toolbar (#174)"
```

---

### Task 7: Cards

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/card.html`
- Modify: `src/crud_views/templatetags/crud_views.py` (new `cv_card_action_group`, `cv_render_card_action`)
- Test: `tests/test1/test_action_menus_card.py`

**Interfaces:**
- Consumes: `CardListView.cv_get_card_action_group(obj)` (Task 4); `cv_actions_menu`,
  `cv_render_list_action_form` (Task 5).
- Produces: `{% cv_card_action_group object as group %}`, `{% cv_render_card_action ctx %}`.

- [ ] **Step 1: Write the failing tests**

```python
"""#174: overflow menu on cards."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, AuthorUpdateView, PublisherCardListView, cv_author, cv_book, cv_publisher

CARD = "//div[contains(@class, 'card') and contains(@class, 'mb-3')]"


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"card_174_{len(grants)}", password="pw")
    for viewset, perms in grants:
        for perm in perms:
            user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def _card(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content).xpath(CARD)[0]


@pytest.fixture
def author_card_actions(monkeypatch):
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [
            CardAction(key="detail", label="Details", variant="primary", flex=True),
            CardAction(key="update", label="Edit", variant="primary", flex=True, no_label=True),
            CardAction(key="ping", label="Ping"),
        ],
    )
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail"])


@pytest.mark.django_db
def test_inline_card_button_unchanged_and_menu(db, author_douglas_adams, author_card_actions):
    card = _card(_client([(cv_author, ("view", "change"))]), reverse(cv_author.get_router_name("card")))
    row = card.cssselect(".d-flex.gap-2")[0]
    detail = row.xpath("./a")[0]
    assert "btn-primary" in detail.get("class") and "flex-grow-1" in detail.get("class")
    wrapper = row.xpath("./div[contains(@class, 'dropdown')]")[0]
    toggle = wrapper.cssselect(".cv-menu-toggle")[0]
    assert "btn-secondary" in toggle.get("class") and "btn-sm" in toggle.get("class")
    items = wrapper.cssselect(".dropdown-item")
    # variant / flex / no_label are ignored in the menu; CardAction.label is the item text
    assert [i.text_content().strip() for i in items] == ["Edit", "Ping"]
    assert all("btn" not in i.get("class") for i in items)


@pytest.mark.django_db
def test_post_card_item_has_form_outside_menu(db, author_douglas_adams, author_card_actions):
    card = _card(_client([(cv_author, ("view", "change"))]), reverse(cv_author.get_router_name("card")))
    ping = [i for i in card.cssselect(".dropdown-item") if i.text_content().strip() == "Ping"][0]
    assert ping.get("data-cv-action") == "submit-form"
    form = card.xpath(f'.//form[@id="{ping.get("data-cv-target")}"]')[0]
    assert not form.xpath("ancestor::ul")
    assert form.cssselect('input[name="csrfmiddlewaretoken"]')


@pytest.mark.django_db
def test_disabled_card_item(db, author_douglas_adams, author_card_actions, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    card = _card(_client([(cv_author, ("view",))]), reverse(cv_author.get_router_name("card")))
    edit = [i for i in card.cssselect(".dropdown-item") if i.text_content().strip() == "Edit"][0]
    assert edit.tag == "button" and edit.get("disabled") is not None
    assert edit.get("data-cv-disabled") == "permission"


@pytest.mark.django_db
def test_child_card_action_folds_by_child_name(db, publisher_penguin, monkeypatch):
    monkeypatch.setattr(PublisherCardListView, "cv_card_actions_inline", ["detail"])
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",))])
    card = _card(client, reverse(cv_publisher.get_router_name("card")))
    items = card.cssselect(".dropdown-item")
    assert [i.text_content().strip() for i in items] == ["Books"]
    assert items[0].get("href")
    monkeypatch.setattr(PublisherCardListView, "cv_card_actions_inline", ["detail", "book"])
    card = _card(client, reverse(cv_publisher.get_router_name("card")))
    assert card.cssselect(".cv-menu-toggle") == []
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test1/test_action_menus_card.py -v`
Expected: FAIL — no `.cv-menu-toggle` on the card.

- [ ] **Step 3: Tags** — add after `cv_card_action`:

```python
@register.simple_tag(takes_context=True)
def cv_card_action_group(context, obj):
    """Card actions split into inline buttons and menu items; None: no menu (#174)."""
    get_group = getattr(cv_get_view(context), "cv_get_card_action_group", None)
    return get_group(obj) if get_group else None


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/card_action.html", takes_context=True)
def cv_render_card_action(context, ctx):
    """Render already-resolved card action data (#174)."""
    return ctx or {}
```

- [ ] **Step 4: Container** — replace `src/crud_views/templates/crud_views/tags/card.html`:

```django
{% load crud_views %}
{% cv_card_action_group object as group %}

<div class="card mb-3">
    <div class="card-body">
        <h5 class="card-title">{{ object }}</h5>
        <div class="d-flex gap-2">
            {% if group is None %}
            {% for action in view.cv_card_actions %}
                {% cv_card_action action object %}
            {% endfor %}
            {% else %}
            {% for ctx in group.inline %}
                {% cv_render_card_action ctx %}
            {% endfor %}
            {% for ctx in group.menu %}
                {% cv_render_list_action_form ctx %}
            {% endfor %}
            {% cv_actions_menu group "card" %}
            {% endif %}
        </div>
    </div>
</div>
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test1/test_action_menus_card.py tests/test1/test_action_menus_golden.py tests/test1/test_card.py tests/test1/test_guardian_card.py -v`
Expected: PASS. Then `pytest tests -q 2>&1 | tail -3` — all pass.

- [ ] **Step 6: Commit**

```bash
task format && task check
git add src tests/test1/test_action_menus_card.py
git commit -m "feat: overflow menu for card actions (#174)"
```

---

### Task 8: Documentation and changelog

Docs come before the example app because the example's `Feature.docs` links are validated by
`examples/bootstrap5/test_doc_links.py`.

**Files:**
- Create: `docs/reference/action_menus.md`
- Modify: `docs/reference/settings.md`, `docs/reference/list_view.md`, `docs/reference/context_buttons.md`,
  `docs/reference/card-list-view.md`, `docs/reference/inaccessible_actions.md`
- Modify: `CHANGELOG.md`, `.gitignore`

(`mkdocs.yml` has no explicit `nav:` — it is commented out — so the new page appears automatically; nothing to add
there.)

- [ ] **Step 1: Write `docs/reference/action_menus.md`**

````markdown
# Action menus

Views with many actions render one button per action. An **action menu** keeps the actions you name as buttons and
folds all others into one dropdown (`⋯`) at the end of the group. It works in three places: list rows, the context
toolbar and cards.

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
(`cv_action_short_label`), or `CardAction.label` on cards. Toolbar items carry the full label as `title`.
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
````

Notes for the implementer: keep this text, but verify each claim against the code you just wrote (attribute names,
template paths, variable names). Fix the docs, not the code, if they disagree only in wording.

- [ ] **Step 2: Cross-links** — add these exact lines:

`docs/reference/settings.md`: a new section after "## Inaccessible actions":

```markdown
## Action menus

| Key | Description | Type | Default |
|-----|-------------|------|---------|
| CRUD_VIEWS_LIST_ACTIONS_INLINE | List row actions kept as buttons; the rest go into a `⋯` menu. `None`: no menu. See [Action menus](action_menus.md). Invalid values raise `crud_views.E105`. | `list[str] \| None` | `None` |
| CRUD_VIEWS_CONTEXT_ACTIONS_INLINE | The same for the context toolbar. | `list[str] \| None` | `None` |
| CRUD_VIEWS_CARD_ACTIONS_INLINE | The same for card actions. | `list[str] \| None` | `None` |
| CRUD_VIEWS_ACTIONS_MENU_ICON | Icon of the menu toggle (bootstrap5 only) | `str` | `fa-solid fa-ellipsis` |
```

`docs/reference/list_view.md`, `docs/reference/context_buttons.md`, `docs/reference/card-list-view.md`: at the end of
the page, append:

```markdown
!!! tip "Many actions?"
    Fold the less common actions into a `⋯` dropdown: see [Action menus](action_menus.md).
```

(If the page does not use `!!!` admonitions anywhere, check `grep -rn '^!!!' docs | head` — the docs use
mkdocs-material admonitions; if they are not enabled in `mkdocs.yml`, use a plain paragraph instead.)

`docs/reference/inaccessible_actions.md`: at the end, append:

```markdown
## Inside action menus

Disabled actions inside an [action menu](action_menus.md) render as disabled dropdown items; hidden ones appear
nowhere, and a menu whose actions are all hidden renders no toggle.
```

- [ ] **Step 3: Changelog** — in `CHANGELOG.md` under `## Unreleased` → `### Added`, append:

```markdown
- Action menus: list rows, the context toolbar and cards can fold actions into one Bootstrap `⋯` dropdown. Inline
  keys per location via settings `CRUD_VIEWS_LIST_ACTIONS_INLINE`, `CRUD_VIEWS_CONTEXT_ACTIONS_INLINE`,
  `CRUD_VIEWS_CARD_ACTIONS_INLINE`, ViewSet fields `*_actions_inline` and view attributes `cv_*_actions_inline`
  (resolved on the rendering view); `None` (default) keeps today's markup. Toggle icon via
  `CRUD_VIEWS_ACTIONS_MENU_ICON`. Overridable templates `actions_menu.html`, `actions_menu_toggle.html`,
  `actions_menu_item.html`. New system checks `crud_views.E105`, `viewset.E208`, `viewset.W290`. Requires the
  Bootstrap JS bundle (#174).
```

and under `### Internal`:

```markdown
- `.superpowers/` (brainstorming mockups) is git-ignored (#174).
```

- [ ] **Step 4: `.gitignore`** — append a line `.superpowers/`.

- [ ] **Step 5: Build the docs**

Run: `uv run mkdocs build --strict 2>&1 | tail -15` (repo root)
Expected: build succeeds with no warnings about `action_menus.md` links. If `--strict` fails on pre-existing
warnings unrelated to these files, run without `--strict` and confirm no warning mentions the changed files.

- [ ] **Step 6: Commit**

```bash
git add docs CHANGELOG.md .gitignore
git commit -m "docs: action menus reference page and cross-links (#174)"
```

---

### Task 9: Example app `action_menus`

**Files (all under `examples/bootstrap5/`):**
- Create: `action_menus/__init__.py`, `apps.py`, `models.py`, `views.py`, `urls.py`, `seed.py`, `tests.py`,
  `migrations/__init__.py`, `migrations/0001_initial.py` (generated),
  `templates/action_menus/table_responsive.html`
- Modify: `project/settings.py` (`INSTALLED_APPS`), `project/urls.py`, `project/features.py`
- Modify: `locale/de/LC_MESSAGES/django.po/.mo`

**Interfaces:**
- Consumes: all package features from Tasks 2–7.
- Produces: URL names `chore-list`, `chore-card`, `chore-detail`, `chore-update`, `step-list` (ViewSets `chore`,
  `step`); demo users alice (all permissions), bob (view only).

- [ ] **Step 1: Check names are free**

Run: `grep -rn 'name="chore"\|name="step"' examples tests src | head`
Expected: no output. If taken, pick other names and use them consistently below.

- [ ] **Step 2: App skeleton** — `action_menus/apps.py`:

```python
from django.apps import AppConfig


class ActionMenusConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "action_menus"
```

`action_menus/models.py`:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel


class Chore(OrderedModel):
    title = models.CharField(_("title"), max_length=100)
    done = models.BooleanField(_("done"), default=False)
    archived = models.BooleanField(_("archived"), default=False)

    class Meta(OrderedModel.Meta):
        verbose_name = _("chore")
        verbose_name_plural = _("chores")

    def __str__(self):
        return self.title


class Step(models.Model):
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, verbose_name=_("chore"))
    text = models.CharField(_("text"), max_length=200)

    class Meta:
        verbose_name = _("step")
        verbose_name_plural = _("steps")

    def __str__(self):
        return self.text
```

`action_menus/urls.py`:

```python
from action_menus.views import cv_chore, cv_step

urlpatterns = cv_chore.urlpatterns + cv_step.urlpatterns
```

`action_menus/templates/action_menus/table_responsive.html` — the package table inside a scroll container, so the
clipping fix is exercised:

```django
{% extends "crud_views/table/bootstrap5.html" %}
{% block table-wrapper %}<div class="table-responsive">{{ block.super }}</div>{% endblock table-wrapper %}
```

- [ ] **Step 3: Views** — `action_menus/views.py`:

```python
import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from action_menus.models import Chore, Step
from crud_views.lib.crispy import Column6, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.view import CardAction, ChildContextButton
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    CardListViewPermissionRequired,
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    OrderedUpDownPermissionRequired,
    OrderedUpViewPermissionRequired,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ParentViewSet, ViewSet, context_buttons_default
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

cv_chore = ViewSet(
    model=Chore,
    name="chore",
    icon_header="fa-solid fa-broom",
    context_buttons=[*context_buttons_default(), ChildContextButton(key="steps", child_name="step")],
)

# every action of a chore; which ones stay buttons is decided per location below
CHORE_ACTIONS = ["detail", "update", "done", "archive", "steps", "up", "down", "delete"]


class ChoreForm(CrispyModelForm):
    class Meta:
        model = Chore
        fields = ["title", "done", "archived"]

    def get_layout_fields(self):
        return Row(Column6("title"), Column6("done"))


class ChoreTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    done = tables.BooleanColumn()

    class Meta:
        template_name = "action_menus/table_responsive.html"  # scroll container: menus must not clip


class ChoreListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_chore
    table_class = ChoreTable
    cv_list_actions = CHORE_ACTIONS
    cv_list_actions_inline = ["detail", "up", "down"]  # the rest folds into the ⋯ menu
    cv_context_actions = ["card", "create"]


class ChoreCardListView(BreadcrumbMixin, CardListViewPermissionRequired):
    cv_viewset = cv_chore
    cv_context_actions = ["home", "create"]
    cv_card_actions = [
        CardAction(key="detail", label=_("Details"), variant="primary", flex=True),
        CardAction(key="update", label=_("Edit")),
        CardAction(key="done", label=_("Done")),
        CardAction(key="archive", label=_("Archive")),
        CardAction(child_name="step", label=_("Steps")),
        CardAction(key="delete", label=_("Delete")),
    ]
    cv_card_actions_inline = ["detail"]


class ChoreDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_chore
    cv_context_actions = ["home", "detail", "update", "done", "archive", "steps", "delete"]
    cv_context_actions_inline = ["update"]  # the active "detail" shows inside the menu
    cv_property_display = [
        {"title": _("Chore"), "icon": "broom", "properties": ["title", "done", "archived"]},
    ]


class ChoreCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_chore
    form_class = ChoreForm
    cv_message_template_code = _("Created chore “{{ object }}”")


class ChoreUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_chore
    form_class = ChoreForm
    cv_context_actions = ["home", "detail", "update", "delete"]
    cv_context_actions_inline = ["update"]  # the active "update" stays an inline button
    cv_message_template_code = _("Updated chore “{{ object }}”")


class ChoreDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_chore
    form_class = CrispyDeleteForm
    cv_modal = True  # opens in a modal, also from inside the menu
    cv_message_template_code = _("Deleted chore “{{ object }}”")


class ChoreDoneView(BreadcrumbMixin, MessageMixin, ActionViewPermissionRequired):
    cv_viewset = cv_chore
    cv_key = "done"
    cv_path = "done"
    cv_permission = "change"
    cv_backend_only = True
    cv_icon_action = "fa-solid fa-check"
    cv_action_label_template_code = _("Toggle done")
    cv_action_short_label_template_code = _("Done")
    cv_message_template_code = _("Toggled done for “{{ object }}”")
    cv_message_template_error_code = _("Could not toggle done for “{{ object }}”")

    def action(self, context) -> bool:
        self.object.done = not self.object.done
        self.object.save()
        return True


class ChoreArchiveView(BreadcrumbMixin, MessageMixin, ActionViewPermissionRequired):
    cv_viewset = cv_chore
    cv_key = "archive"
    cv_path = "archive"
    cv_permission = "change"
    cv_backend_only = True
    cv_inaccessible_actions = "disable"  # bob sees this one greyed out instead of hidden
    cv_icon_action = "fa-solid fa-box-archive"
    cv_action_label_template_code = _("Archive")
    cv_action_short_label_template_code = _("Archive")
    cv_message_template_code = _("Toggled archive for “{{ object }}”")
    cv_message_template_error_code = _("Could not archive “{{ object }}”")

    def action(self, context) -> bool:
        self.object.archived = not self.object.archived
        self.object.save()
        return True


class ChoreUpView(BreadcrumbMixin, MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_chore
    cv_message_template_code = _("Moved chore “{{ object }}” up")


class ChoreDownView(BreadcrumbMixin, MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_chore
    cv_message_template_code = _("Moved chore “{{ object }}” down")


cv_step = ViewSet(model=Step, name="step", icon_header="fa-solid fa-list-check", parent=ParentViewSet(name="chore"))


class StepForm(CrispyModelForm):
    class Meta:
        model = Step
        fields = ["text"]

    def get_layout_fields(self):
        return Row(Column12("text"))


class StepTable(Table):
    text = tables.Column()


class StepListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_step
    table_class = StepTable
    cv_list_actions = ["update", "delete"]


class StepCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_step
    form_class = StepForm
    cv_message_template_code = _("Created step “{{ object }}”")


class StepUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_step
    form_class = StepForm
    cv_message_template_code = _("Updated step “{{ object }}”")


class StepDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_step
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted step “{{ object }}”")
```

Before relying on these imports, confirm each name is exported where it is imported from (compare with
`library/views.py`, `nested/views.py`, `showcase/views.py`, `context_buttons/views.py`); for example
`ChildContextButton` may need `from crud_views.lib.view.buttons import ChildContextButton`. Check the
`CreateViewParentMixin` MRO position against `nested/views.py`.

- [ ] **Step 4: Seed** — `action_menus/seed.py`:

```python
from django.contrib.auth import get_user_model
from project.seeding import grant_model_perms

from action_menus.models import Chore, Step


def seed():
    user_model = get_user_model()
    # alice may do everything; bob may only look: archive shows disabled for him, the rest disappears
    for model in (Chore, Step):
        grant_model_perms(user_model.objects.get(username="alice"), model)
        grant_model_perms(user_model.objects.get(username="bob"), model, actions=("view",))

    for title in ("Take out the trash", "Water the plants", "Clean the windows", "Fix the bike", "Do the laundry"):
        chore, _ = Chore.objects.get_or_create(title=title)
        Step.objects.get_or_create(chore=chore, text=f"Plan: {title}")
```

- [ ] **Step 5: Wiring**

- `project/settings.py`: add `"action_menus",` to `INSTALLED_APPS` after `"context_buttons",`.
- `project/urls.py`: after the context-buttons line add
  `urlpatterns += [path("action-menus/", include("action_menus.urls"))]`.
- `project/features.py`: append to `FEATURES` (after the Context Buttons entry):

```python
    Feature(
        app="action_menus",
        title="Action Menus",
        description="Fold the less common actions of list rows, the toolbar and cards into a ⋯ dropdown.",
        about=(
            "A chore has eight actions — too many buttons for every table row. The list keeps detail, up and "
            "down as buttons and folds the rest into a ⋯ menu; the toolbar and the cards do the same. Delete opens "
            "a modal and done / archive are POST actions, all from inside the menu. Log in as bob (may only view): "
            "archive stays visible but disabled, the other actions disappear."
        ),
        look_at=(
            "cv_list_actions_inline, cv_context_actions_inline and cv_card_actions_inline in views.py, and "
            "ChoreArchiveView.cv_inaccessible_actions."
        ),
        url_name="chore-list",
        icon="fa-solid fa-ellipsis",
        docs=(
            DocRef(page="reference/action_menus.md", label="Action menus — configuration", anchor="configuration"),
            DocRef(page="reference/action_menus.md", label="Action menus — hide and disable", anchor="hide-and-disable"),
        ),
    ),
```

- [ ] **Step 6: Migration and checks**

Run (in `examples/bootstrap5/`): `uv run manage.py makemigrations action_menus && uv run manage.py check`
Expected: `0001_initial.py` created; `System check identified no issues` (no E208/W290/E255).

- [ ] **Step 7: Example tests** — `action_menus/tests.py`:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from lxml import html as lxml_html
from project.seeding import grant_model_perms

from action_menus.models import Chore, Step


class ActionMenusTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user(username="alice-test", password="pw")
        cls.bob = User.objects.create_user(username="bob-test", password="pw")
        for model in (Chore, Step):
            grant_model_perms(cls.alice, model)
            grant_model_perms(cls.bob, model, actions=("view",))
        cls.chore = Chore.objects.create(title="Take out the trash")

    @staticmethod
    def doc(resp):
        """The page without the code panel, which shows these templates' source (and so their class names)."""
        return lxml_html.fromstring(resp.content.decode().split('id="snippet-panels"')[0])

    def get(self, user, url_name, **kwargs):
        self.client.force_login(user)
        resp = self.client.get(reverse(url_name, kwargs=kwargs or None))
        self.assertEqual(resp.status_code, 200)
        return self.doc(resp)


class ChoreListTest(ActionMenusTestCase):
    def test_row_keeps_inline_buttons_and_menu(self):
        doc = self.get(self.alice, "chore-list")
        fieldset = doc.xpath("//fieldset[@cv-list-container]")[0]
        self.assertEqual([el.get("cv-key") for el in fieldset.xpath("./*[@cv-key]")], ["detail", "up", "down"])
        items = [i.get("cv-key") for i in fieldset.cssselect(".dropdown-item")]
        self.assertEqual(items, ["update", "done", "archive", "list", "delete"])

    def test_table_is_responsive(self):
        doc = self.get(self.alice, "chore-list")
        self.assertTrue(doc.xpath("//div[contains(@class, 'table-responsive')]//td//fieldset[@cv-list-container]"))

    def test_bob_sees_archive_disabled(self):
        doc = self.get(self.bob, "chore-list")
        archive = doc.cssselect('.dropdown-item[cv-key="archive"]')[0]
        self.assertIsNotNone(archive.get("disabled"))
        self.assertEqual(archive.get("data-cv-disabled"), "permission")
        self.assertEqual(doc.cssselect('.dropdown-item[cv-key="update"]'), [])

    def test_german_toggle_label(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("chore-list"), HTTP_ACCEPT_LANGUAGE="de")
        self.assertContains(resp, 'aria-label="Weitere Aktionen"')


class ChoreDetailTest(ActionMenusTestCase):
    def test_active_detail_in_menu(self):
        doc = self.get(self.alice, "chore-detail", pk=self.chore.pk)
        toolbar = doc.xpath("//fieldset[@cv-context-container]")[0]
        detail = toolbar.cssselect('.dropdown-item[cv-key="detail"]')[0]
        self.assertEqual(detail.get("aria-current"), "page")

    def test_active_update_inline(self):
        doc = self.get(self.alice, "chore-update", pk=self.chore.pk)
        toolbar = doc.xpath("//fieldset[@cv-context-container]")[0]
        self.assertIn("active", toolbar.xpath('./a[@cv-key="update"]')[0].get("class").split())


class ChoreCardTest(ActionMenusTestCase):
    def test_card_menu_has_child_action(self):
        doc = self.get(self.alice, "chore-card")
        card = doc.xpath("//div[contains(@class, 'card') and contains(@class, 'mb-3')]")[0]
        labels = [i.text_content().strip() for i in card.cssselect(".dropdown-item")]
        self.assertIn("Steps", labels)
        self.assertIn("Delete", labels)
```

The `steps` ChildContextButton resolves to the child list view, so its `cv-key` is `list` (asserted in
`test_row_keeps_inline_buttons_and_menu`); if the resolved key differs, inspect the rendered HTML and fix the
expectation — but verify the item links to `/action-menus/chore/<pk>/step/…`.

Run (in `examples/bootstrap5/`): `uv run pytest action_menus -v`
Expected: PASS (the German test fails until Step 8 — run it again after).

- [ ] **Step 8: Translations**

Run (in `examples/bootstrap5/`): `task msg-make`, then fill every new empty `msgstr` in
`locale/de/LC_MESSAGES/django.po` that comes from `action_menus/` (e.g. "Details" → "Details", "Edit" →
"Bearbeiten", "Done" → "Erledigt", "Archive" → "Archivieren", "Steps" → "Schritte", "Delete" → "Löschen",
"chore" → "Aufgabe", "chores" → "Aufgaben", "step" → "Schritt", "steps" → "Schritte", "title" → "Titel",
"done" → "erledigt", "archived" → "archiviert", "text" → "Text", "Toggle done" → "Erledigt umschalten", and the
message templates). Reuse existing translations where the msgid already exists. Then `task msg-comp`.

Run: `uv run pytest -q 2>&1 | tail -3` (whole example suite, includes `test_i18n.py`, `test_doc_links.py`,
`test_docs_sync.py`)
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
cd /home/alex/projects/alex/django-crud-views && task format && task check
git add examples/bootstrap5/action_menus examples/bootstrap5/project examples/bootstrap5/locale
git commit -m "feat: action_menus example app (#174)"
```

---

### Task 10: Browser verification and docs screenshot (controller task)

Needs a browser (Playwright MCP); run by the controller, not a subagent without browser tools.

**Files:**
- Create: `docs/reference/screenshots/action-menus.png`
- Modify: `docs/reference/action_menus.md` (embed the screenshot)
- Possibly modify: `src/crud_views/templatetags/crud_views.py` (`_ACTIONS_MENU_STYLE` / toggle popper config) if
  verification finds clipping in the toolbar or cards

- [ ] **Step 1: Start the example**

Run (in `examples/bootstrap5/`, background): `uv run manage.py migrate && uv run manage.py seed && uv run manage.py runserver 8174`

- [ ] **Step 2: Verify in the browser as alice** (`/action-menus/chore/` after login):
  1. Open the **last row's** menu: fully visible, not clipped by the table container.
  2. Click "Done" in a row menu: page reloads with the "Toggled done" message (POST form submitted); the menu closed.
  3. Click "Delete" in a row menu: the delete modal opens; the menu is closed.
  4. Toggle corners: run in the page
     `[...document.querySelectorAll('.cv-menu-toggle')].map(b => getComputedStyle(b).borderTopRightRadius)` —
     no `"0px"` for a toggle that is the last button of its group; caret not visible.
  5. Detail page: "Detail" inside the menu has the active style; update page: inline "Edit" is active.
  6. Card page: open a card menu near the bottom of the viewport; the menu flips/stays visible.
- [ ] **Step 3: Verify as bob**: "Archive" is greyed out and not clickable in rows, toolbar and cards.
- [ ] **Step 4: Fix if needed** — if the toolbar or card menus clip, enable the fixed strategy for that location
  (add `"context"` / `"card"` to the condition in `actions_menu_toggle.html`), extend the matching test in Task 5–7's
  test files, rerun `pytest tests -q`.
- [ ] **Step 5: Screenshot** — with a row menu open (as alice), capture the list and toolbar into
  `docs/reference/screenshots/action-menus.png`; embed below the intro diagram of `docs/reference/action_menus.md`:

```markdown
![A list row and the detail toolbar with the action menu open](screenshots/action-menus.png)
```

- [ ] **Step 6: Stop the server, run everything, commit**

Run: `pytest tests -q 2>&1 | tail -3` and (in `examples/bootstrap5/`) `uv run pytest -q 2>&1 | tail -3`
Expected: all pass.

```bash
git add docs src tests
git commit -m "docs: action menus screenshot; browser-verified menus (#174)"
```

---

## After the plan

- Full matrix: `task test` (nox: Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0) before opening the PR.
- PR from `action-menus-174` → `main`, wait for CI (incl. codecov/patch via check-runs API, SonarCloud), fix ruff
  findings. Merge only when the user asks.
- After merge: skill update in jacob-consulting/skills + drift audit (separate repo, separate request).
