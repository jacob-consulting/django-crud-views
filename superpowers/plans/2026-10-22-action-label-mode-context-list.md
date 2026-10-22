# Context and list buttons learn the label mode — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A project can give a toolbar or row button a visible text label (`"both"` or `"label"`) per action key, set once in settings and overridable per ViewSet and per view, with today's icon-only markup as the untouched default.

**Architecture:** A `dict[action key → LabelMode]` per location resolves view → ViewSet → setting through the existing `cv_first_inline_keys()` resolver. `cv_get_context()` gains a keyword-only `location` and stamps `cv_label_mode` onto the action dict for `"context"` and `"list"`; the five callers that produce a leaf pass their location. `cv_button_data()` stops forcing `"icon"` off cards and reads the stamp, showing the short label in text modes. No template changes: the leaf already branches on all three modes and already passes the mode to the class table (#209).

**Tech Stack:** Django 4.2 / 5.2 / 6.0, Pydantic v2 (settings and ViewSet), pytest + lxml, ruff.

**Spec:** `superpowers/specs/2026-10-22-action-label-mode-context-list-design.md` — issue #216, tracker #228, after #209 (PR #229), before #227.

## Global Constraints

- Line length 120, double quotes, `ruff format` (Markdown included — CI formats `.md`). `cv_` prefix on `CrudView` attributes.
- Python 3.12–3.15, Django 4.2 / 5.2 / 6.0.
- `settings.py` imports nothing from `crud_views.lib.view` at module level; function-local imports inside `check_messages` only (existing pattern at `settings.py:133`).
- `LEAF_KEYS` in `src/crud_views/lib/view/button_data.py` is unchanged. Nothing under `src/crud_views/templates/` changes.
- No file under `tests/test1/golden/` changes. Never run the golden regeneration. A diff there is a bug.
- `cv_get_context(key, obj, user, request)` keeps working for every existing caller: the new parameter is keyword-only with default `None`.
- Both new settings default to `{}`; ViewSet fields and view attributes default to `None`. Layers are never merged: the first non-`None` layer is used whole.
- Three new check ids and no others: `crud_views.E106`, `viewset.E211`, `viewset.W291`.
- One commit per task, on branch `feat/action-label-mode-context-list`. Run tests with `pytest tests -n auto`.

## Review Focus

1. A labelled key the user may not access renders nothing and raises nothing (`cv_resolve_action` returns `None` before the leaf). Test in Task 4 (`test_labelled_key_without_access_is_hidden`).
2. A labelled key rendered disabled (`cv_inaccessible_actions = "disable"`) is a `<button disabled>` with the visible text, no `title`. Test in Task 4 (`test_labelled_key_rendered_disabled`).
3. A POST-only row action (`ping`) in `"both"` mode keeps `data-cv-action="submit-form"` and its hidden form; the label mode changes text, not behaviour. Test in Task 4 (`test_labelled_post_row_action_keeps_submit_target`).
4. A `ContextButton` with its own `template_code` under a labelled key gets `cv_label_mode` in its context and renders without error. Test in Task 4 (`test_custom_template_code_sees_label_mode`).
5. `cv_get_context()` called without `location` (breadcrumbs, origin links, manage view) returns a dict with no `cv_label_mode` key, so nothing outside buttons sees the stamp. Test in Task 4 (`test_cv_get_context_without_location_is_unstamped`).

---

## Setup (no tests)

- [ ] Commit this plan on `main` (the spec is already committed as `7b374a6`) and branch:

```bash
git add superpowers/plans/2026-10-22-action-label-mode-context-list.md
git commit -m "docs(plan): context and list buttons learn the label mode (#216)"
git checkout -b feat/action-label-mode-context-list
```

---

### Task 1: `cv_button_data()` honours a stamped mode off cards

**Files:**
- Modify: `src/crud_views/lib/view/button_data.py:44-60` (label and mode block), `:94` (title rule unchanged)
- Test: `tests/test1/test_button_data.py`

**Interfaces:**
- Produces: `cv_button_data(ctx: dict, location: str) -> dict`, unchanged signature. For every location `label_mode = ctx.get("cv_label_mode") or ("both" if card else "icon")`, validated with `is_label_mode()` (raises `ValueError` naming `cv_label_mode`, as the card branch does today), then `"icon"` when the label is empty. For `"context"` and `"list"` in a mode other than `"icon"`, `cv_label` is the short label (`cv_action_short_label`, else `cv_action_label`); in `"icon"` it stays the full label. `cv_title` is present only in `"icon"` mode (existing rule, untouched). `cv_short_label` is unchanged in every case.

- [ ] **Step 1: Write the failing tests.** Replace `test_label_mode_always_icon_off_cards` (`test_button_data.py:131-135`) with the inverted test, widen `test_unknown_cv_label_mode_on_card_raises` (line 118) to all three locations, and add the icon-mode pin:

```python
@pytest.mark.parametrize("location", ["context", "list"])
@pytest.mark.parametrize("mode", ["both", "label"])
def test_label_mode_stamped_off_cards_shows_short_label(location, mode):
    data = cv_button_data(base(cv_label_mode=mode), location)
    assert data["cv_label_mode"] == mode
    assert data["cv_label"] == "Detail"
    assert data["cv_short_label"] == "Detail"
    assert "cv_title" not in data


@pytest.mark.parametrize("location", ["context", "list"])
def test_label_mode_icon_off_cards_keeps_full_label_and_title(location):
    data = cv_button_data(base(cv_label_mode="icon"), location)
    assert data["cv_label_mode"] == "icon"
    assert data["cv_label"] == "Show"
    assert data["cv_title"] == "Show"


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("value", ["lable", "icons", "Both", 1, ["both"]])  # the card test's list, now everywhere
def test_unknown_cv_label_mode_raises_everywhere(location, value):
    with pytest.raises(ValueError, match="cv_label_mode"):
        cv_button_data(base(cv_label="Details", cv_label_mode=value), location)
```

`test_unknown_cv_label_mode_on_card_raises` becomes this test; an empty string is not in the list because it is falsy and takes the default.

- [ ] **Step 2: Run them to see them fail**

Run: `pytest tests/test1/test_button_data.py -v -k "stamped_off_cards or icon_off_cards or raises_everywhere"`
Expected: the `both`/`label` cases FAIL (`cv_label_mode == "icon"`), the `context`/`list` raise cases FAIL (no exception).

- [ ] **Step 3: Implement.** In `cv_button_data()` replace the `if card: ... else: label_mode = "icon"` block with the location-independent read from the Interfaces block, and after the empty-label rule add the short-label rule for non-card text modes. The `test_get` expectations (`cv_label == "Show"`, `cv_title == "Show"` off cards with no stamp) must keep passing untouched.

- [ ] **Step 4: Run the module**

Run: `pytest tests/test1/test_button_data.py -v`
Expected: PASS, including `test_get`, `test_pure_and_within_leaf_keys` and every card test.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/button_data.py tests/test1/test_button_data.py
git commit -m "feat(buttons): cv_button_data reads cv_label_mode in every location (#216)"
```

---

### Task 2: The settings and the ViewSet fields

**Files:**
- Modify: `src/crud_views/lib/view/label_mode.py` (add `is_label_mode_map`)
- Modify: `src/crud_views/lib/settings.py:49-53` (fields, after the `*_actions_inline` trio) and `:133-147` (check)
- Modify: `src/crud_views/lib/viewset/__init__.py:78-81` (fields, after the `*_actions_inline` trio)
- Create: `tests/test1/test_action_label_mode_config.py`

**Interfaces:**
- Produces: `is_label_mode_map(value: object) -> bool` in `label_mode.py`: `True` for `None`, or a `dict` whose keys are all `str` and whose values all satisfy `is_label_mode()`.
- Produces: `CrudViewsSettings.context_actions_label_mode: Any` from `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`, `CrudViewsSettings.list_actions_label_mode: Any` from `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE`, both `default={}`. `check_messages` appends `Error(id="crud_views.E106", msg=f"setting {name} must be a dict of action key -> one of {sorted(LABEL_MODES)}, got {value!r}")` when a value is not a `dict` or fails `is_label_mode_map` (`None` is an error here: the setting is the floor).
- Produces: `ViewSet.context_actions_label_mode: dict[str, str] | None = None` and `ViewSet.list_actions_label_mode: dict[str, str] | None = None`, with a Pydantic `field_validator` on both that raises `ValueError` when `is_label_mode_map` is false, so construction raises `ValidationError` like a wrong-typed inline field does.

- [ ] **Step 1: Write the failing tests** in the new module (header docstring: `"""#216: label-mode maps — settings, ViewSet fields, view attributes, resolution and checks."""`; imports as in `test_action_menus_config.py`):

```python
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, True),
        ({}, True),
        ({"create": "both"}, True),
        ({"a": "label", "b": "icon"}, True),
        (["create"], False),
        ("both", False),
        ({"create": "text"}, False),
        ({1: "both"}, False),
        ({"create": None}, False),
    ],
)
def test_is_label_mode_map(value, expected):
    assert is_label_mode_map(value) is expected


def test_settings_defaults():
    s = CrudViewsSettings()
    assert s.context_actions_label_mode == {}
    assert s.list_actions_label_mode == {}


@pytest.mark.parametrize("field", ["context_actions_label_mode", "list_actions_label_mode"])
@pytest.mark.parametrize("value", [None, ["create"], "both", {"create": "text"}, {1: "both"}])
def test_invalid_setting_e106(field, value):
    messages = CrudViewsSettings(**{field: value}).check_messages
    assert [m.id for m in messages] == ["crud_views.E106"]
    assert f"CRUD_VIEWS_{field.upper()}" in messages[0].msg


@pytest.mark.parametrize("value", [{}, {"create": "both"}, {"create": "label", "home": "icon"}])
def test_valid_setting_values(value):
    assert CrudViewsSettings(context_actions_label_mode=value).check_messages == []


@pytest.mark.parametrize("field", ["context_actions_label_mode", "list_actions_label_mode"])
@pytest.mark.parametrize("value", [["create"], {"create": "text"}, "both"])
def test_viewset_rejects_bad_value(field, value):
    with pytest.raises(ValidationError):
        ViewSet(model=Author, name=f"author_bad_{field}_216", **{field: value})


def test_viewset_accepts_map_and_defaults_to_none():
    vs = ViewSet(model=Author, name="author_label_mode_216", context_actions_label_mode={"create": "both"})
    assert vs.context_actions_label_mode == {"create": "both"}
    assert vs.list_actions_label_mode is None
```

- [ ] **Step 2: Run them to see them fail**

Run: `pytest tests/test1/test_action_label_mode_config.py -v`
Expected: `ImportError` on `is_label_mode_map`; after a stub, `AttributeError` / `ValidationError` on the unknown fields.

- [ ] **Step 3: Implement** the three pieces from the Interfaces block. The settings fields carry the comment `# label mode of context / list actions (#216): action key -> "label" | "icon" | "both"; keys not named are "icon". Overridable per ViewSet (*_actions_label_mode) and per view (cv_*_actions_label_mode), resolved on the rendering view`. The check lives next to the `E105` loop and imports `is_label_mode_map` and `LABEL_MODES` function-locally.

- [ ] **Step 4: Run the module and the settings and ViewSet tests**

Run: `pytest tests/test1/test_action_label_mode_config.py tests/test1/test_action_menus_config.py tests/test1/test_settings_checks.py -v -n auto`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/label_mode.py src/crud_views/lib/settings.py src/crud_views/lib/viewset/__init__.py tests/test1/test_action_label_mode_config.py
git commit -m "feat(settings): CRUD_VIEWS_*_ACTIONS_LABEL_MODE and the ViewSet label-mode maps (#216)"
```

---

### Task 3: View attributes, resolution and checks

**Files:**
- Modify: `src/crud_views/lib/view/base.py:79-80` (attributes, after the `_inline` pair), `:166-167` (checks), `:234-251` (getters, after `cv_get_context_actions_inline`)
- Modify: `src/crud_views/lib/view/action_menu.py:18-41` (add `cv_label_mode_checks` after `cv_inline_checks`)
- Test: `tests/test1/test_action_label_mode_config.py`

**Interfaces:**
- Consumes: `is_label_mode_map`, `LABEL_MODES` (Task 2); `cv_first_inline_keys(view_value, viewset_field)` (`base.py:235`, kept under its name — its docstring gains "also the label-mode maps (#216)").
- Produces on `CrudView`:
  - `cv_list_actions_label_mode: dict[str, str] | None = None` and `cv_context_actions_label_mode: dict[str, str] | None = None`.
  - `cv_get_list_actions_label_mode() -> dict[str, str]` and `cv_get_context_actions_label_mode() -> dict[str, str]`, classmethods: `cv_first_inline_keys(cls.cv_<loc>_actions_label_mode, "<loc>_actions_label_mode")`.
  - `cv_get_action_label_mode(location: str, key: str) -> str`, classmethod: the mapping for `"context"` or `"list"`, `.get(key, "icon")`; any other location raises `ValueError`.
- Produces in `action_menu.py`: `cv_label_mode_checks(cls, attribute: str, known_keys: Iterable[str] | None) -> Iterator[Check]`: `CheckExpression(id="E211")` when `is_label_mode_map(value)` is false, message `f"{attribute} must be None or a dict of action key -> one of {sorted(LABEL_MODES)}, got {value!r} (cv_card_actions_label_mode is the string-valued default of card views)"`; then, for a valid non-`None` dict, `CheckWarningExpression(id="W291")` naming the keys not in `known_keys`, message shape as `W290`'s. Wired in `cv_checks()` right after the two `cv_inline_checks` lines, with `cls.cv_list_actions` / `cls.cv_context_actions` as known keys.

- [ ] **Step 1: Write the failing tests** (append to the config module; `_ids(view_cls)` as in `test_action_menus_config.py:77`):

```python
def test_default_resolves_to_empty_and_icon():
    assert AuthorListView.cv_get_list_actions_label_mode() == {}
    assert AuthorDetailView.cv_get_context_actions_label_mode() == {}
    assert AuthorDetailView.cv_get_action_label_mode("context", "create") == "icon"


def test_setting_is_last_fallback(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "list_actions_label_mode", {"detail": "both"})
    assert AuthorListView.cv_get_action_label_mode("list", "detail") == "both"
    assert AuthorListView.cv_get_action_label_mode("list", "update") == "icon"


def test_viewset_beats_setting(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"create": "both"})
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"home": "label"})
    assert AuthorDetailView.cv_get_context_actions_label_mode() == {"home": "label"}
    assert AuthorDetailView.cv_get_action_label_mode("context", "create") == "icon"  # no merge across layers


def test_view_empty_map_beats_viewset(monkeypatch):
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"create": "both"})
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {})
    assert AuthorDetailView.cv_get_action_label_mode("context", "create") == "icon"


def test_card_location_raises():
    with pytest.raises(ValueError):
        AuthorDetailView.cv_get_action_label_mode("card", "detail")


@pytest.mark.parametrize(
    ("view_cls", "attr"),
    [(AuthorListView, "cv_list_actions_label_mode"), (AuthorDetailView, "cv_context_actions_label_mode")],
)
@pytest.mark.parametrize("value", ["both", ["create"], {"create": "text"}, {"create": None}])
def test_e211_invalid_view_value(monkeypatch, view_cls, attr, value):
    monkeypatch.setattr(view_cls, attr, value)
    assert "viewset.E211" in _ids(view_cls)


def test_e211_message_names_the_card_attribute(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", "both")
    (message,) = [m for c in AuthorDetailView.checks() for m in c.messages() if m.id == "viewset.E211"]
    assert "cv_card_actions_label_mode" in message.msg


def test_no_label_mode_messages_by_default():
    for view_cls in (AuthorListView, AuthorDetailView):
        ids = _ids(view_cls)
        assert "viewset.E211" not in ids
        assert "viewset.W291" not in ids


def test_w291_unknown_context_key(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"home": "both", "udpate": "both"})
    messages = [m for c in AuthorDetailView.checks() for m in c.messages() if m.id == "viewset.W291"]
    assert len(messages) == 1
    assert "udpate" in messages[0].msg
    assert messages[0].level == 30  # django.core.checks.WARNING


def test_w291_known_list_keys_no_warning(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both", "update": "label"})
    assert "viewset.W291" not in _ids(AuthorListView)


def test_w291_never_for_viewset_or_setting(monkeypatch):
    monkeypatch.setattr(cv_author, "list_actions_label_mode", {"nonexistent": "both"})
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"nonexistent": "both"})
    for view_cls in (AuthorListView, AuthorDetailView):
        assert "viewset.W291" not in _ids(view_cls)
```

- [ ] **Step 2: Run them to see them fail**

Run: `pytest tests/test1/test_action_label_mode_config.py -v`
Expected: `AttributeError` on the getters; the check tests fail on missing ids.

- [ ] **Step 3: Implement** the attributes, getters, `cv_get_action_label_mode` and `cv_label_mode_checks` from the Interfaces block, and wire the two checks into `cv_checks()`.

- [ ] **Step 4: Run the module, then the whole suite** (the suite takes about ten seconds with xdist and is the only place the `W280` unknown-attribute check and every page render are exercised together)

Run: `pytest tests/test1/test_action_label_mode_config.py -v && pytest tests -n auto`
Expected: PASS (the new `cv_*` attributes are declared on the class, so `CheckUnknownAttributes` knows them).

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/base.py src/crud_views/lib/view/action_menu.py tests/test1/test_action_label_mode_config.py
git commit -m "feat(view): cv_*_actions_label_mode with resolution and checks E211 / W291 (#216)"
```

---

### Task 4: The stamp — `cv_get_context(location=...)` and the five callers

**Files:**
- Modify: `src/crud_views/lib/view/base.py:481-500` (`cv_get_context_buttons`, `cv_resolved_actions`), `:502-517` (the two group getters), `:535-585` (`cv_get_context`)
- Modify: `src/crud_views/templatetags/crud_views.py:77-80` (wrapper), `:115-116` (`cv_list_action`), `:211-218` (`cv_context_action`), `:242-248` (`cv_context_button`)
- Modify: `src/crud_views_guardian/lib/mixins.py:111-128` (override signature and `super()` call)
- Create: `tests/test1/test_action_label_mode_render.py`

**Interfaces:**
- Consumes: `cv_get_action_label_mode(location, key)` (Task 3); `cv_button_data()` reading the stamp (Task 1).
- Produces: `CrudView.cv_get_context(self, key=None, obj=None, user=None, request=None, *, location: str | None = None) -> dict`. When `location` is `"context"` or `"list"` and the result is a non-empty dict, it carries `"cv_label_mode": self.cv_get_action_label_mode(location, key)`; `{}` stays `{}`; `location=None` returns exactly today's dict. Both branches (context button and view key) are stamped.
- Produces: `CrudView.cv_resolved_actions(self, keys, obj=None, *, location: str | None = None)` forwarding `location`; `cv_get_list_action_group` passes `"list"`, `cv_get_context_action_group` passes `"context"`, `cv_get_context_buttons` passes `"context"`.
- Produces: templatetag wrapper `cv_get_context(context, key, obj=None, *, location=None)`; `cv_context_action` and `cv_context_button` pass `location="context"`, `cv_list_action` passes `location="list"`. `cv_list_action_form`, `cv_context_action_form` and everything else are untouched.
- Produces: `GuardianMixin.cv_get_context(self, key=None, obj=None, user=None, request=None, *, location=None)` forwarding `location=location` to `super()`.

- [ ] **Step 1: Write the failing tests** in the new module (docstring `"""#216: labelled context and list buttons as rendered by crud_views/tags/button/action.html."""`). Helpers: `_client(grants)` as in `test_button_class_label_mode.py:19`, `_toolbar(client, url)` from `test_action_menus_context.py:31`, `_rows(client)` from `test_action_menus_list.py:28`, `_render(view, request, snippet)` and `_detail_view(...)` from `test_context_button_tag.py:21-30`. `_buttons(container) -> dict[str, bytes]` returns `{el.get("cv-key"): lxml_html.tostring(el)}` for `container.xpath("./*[@cv-key]")`, and `_button(container, key)` the single element. `AUTHOR_FULL = (cv_author, ("view", "add", "change", "delete"))`, `AUTHOR_VIEW = (cv_author, ("view",))`.

```python
@pytest.mark.django_db
def test_toolbar_labelled_create_leaves_the_other_buttons_byte_identical(author_douglas_adams, monkeypatch):
    client = _client([AUTHOR_FULL])
    url = reverse(cv_author.get_router_name("list"))
    before = _buttons(_toolbar(client, url))
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "both"})
    toolbar = _toolbar(client, url)
    after = _buttons(toolbar)
    assert {k: v for k, v in after.items() if k != "create"} == {k: v for k, v in before.items() if k != "create"}
    create = _button(toolbar, "create")
    assert create.get("title") is None
    assert create.get("data-cv-tooltip") is None
    assert create.xpath("./*[@aria-hidden='true']")  # the icon
    (span,) = create.xpath("./span")
    assert span.get("class") is None
    assert span.text == "Create"


@pytest.mark.django_db
def test_toolbar_label_mode_renders_text_without_icon(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "label"})
    create = _button(_toolbar(_client([AUTHOR_FULL]), reverse(cv_author.get_router_name("list"))), "create")
    assert create.xpath("./*[@aria-hidden='true']") == []
    assert create.get("title") is None
    (span,) = create.xpath("./span")
    assert span.text == "Create"


@pytest.mark.django_db
def test_context_button_is_matched_by_its_configured_key(author_douglas_adams, monkeypatch):
    # "home" targets the list view and renders cv-key="list"; the mapping names "home"
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"home": "both"})
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    home = _button(toolbar, "list")
    assert home.get("title") is None
    assert home.xpath("./span[not(@class)]")
    assert _button(toolbar, "detail").get("title")  # still icon-only


@pytest.mark.django_db
def test_row_labelled_detail_next_to_icon_only_update(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both"})
    (td,) = _rows(_client([AUTHOR_FULL]))
    fieldset = td.cssselect("fieldset")[0]
    detail = _button(fieldset, "detail")
    assert detail.get("title") is None
    assert [s.text for s in detail.xpath("./span")] == ["Detail"]
    update = _button(fieldset, "update")
    assert update.get("title")
    assert update.xpath("./span[contains(@class, 'visually-hidden')]")


@pytest.mark.django_db
def test_row_same_variant_different_modes_get_different_classes(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:secondary:both": "btn btn-xs x-both"}):
        (td,) = _rows(_client([AUTHOR_FULL]))
    fieldset = td.cssselect("fieldset")[0]
    assert _button(fieldset, "detail").get("class") == "btn btn-xs x-both"
    assert _button(fieldset, "update").get("class") == "btn btn-outline-primary btn-xs"


@pytest.mark.django_db
def test_labelled_post_row_action_keeps_submit_target(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"ping": "both"})
    (td,) = _rows(_client([AUTHOR_FULL]))
    ping = _button(td.cssselect("fieldset")[0], "ping")
    assert ping.tag == "button"
    assert ping.get("data-cv-action") == "submit-form"
    assert ping.get("data-cv-target", "").startswith("cv_form_")
    assert ping.get("title") is None
    assert ping.xpath("./span[not(@class)]")


@pytest.mark.django_db
def test_folded_labelled_key_has_no_title_and_icon_key_keeps_it(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["update"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"detail": "both"})
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    detail = toolbar.cssselect('.dropdown-item[cv-key="detail"]')[0]
    assert detail.get("title") is None
    assert "Detail" in detail.text_content()
    assert toolbar.cssselect('.dropdown-item[cv-key="delete"]')[0].get("title")


@pytest.mark.django_db
def test_manual_placement_follows_the_view(author_douglas_adams, monkeypatch, client):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    user = User.objects.create_user(username="manual_216", password="pw")
    for perm in ("view", "change"):
        user_viewset_permission(user, cv_author, perm)
    client.force_login(user)
    view, request = _detail_view(client, cv_author, author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'update' %}")
    assert ">Update</span>" in html
    assert "visually-hidden" not in html
    assert "title=" not in html


@pytest.mark.django_db
def test_labelled_key_without_access_is_hidden(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "both"})
    toolbar = _toolbar(_client([AUTHOR_VIEW]), reverse(cv_author.get_router_name("list")))
    assert toolbar.xpath('./*[@cv-key="create"]') == []


@pytest.mark.django_db
def test_labelled_key_rendered_disabled(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCreateView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(AuthorListView, "cv_context_actions_label_mode", {"create": "both"})
    create = _button(_toolbar(_client([AUTHOR_VIEW]), reverse(cv_author.get_router_name("list"))), "create")
    assert create.tag == "button"
    assert create.get("disabled") is not None
    assert create.get("data-cv-disabled") == "permission"
    assert create.get("title") is None
    assert [s.text for s in create.xpath("./span")] == ["Create"]


@pytest.mark.django_db
def test_custom_template_code_sees_label_mode(author_douglas_adams, monkeypatch):
    custom = ContextButton(key="edit_big", key_target="update", template_code='<a cv-key="big">{{ cv_label_mode }}</a>')
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [custom])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "edit_big"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"edit_big": "both"})
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    assert toolbar.xpath('./a[@cv-key="big"]')[0].text == "both"


@pytest.mark.django_db
def test_cv_get_context_without_location_is_unstamped(author_douglas_adams, monkeypatch, client):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    user = User.objects.create_user(username="unstamped_216", password="pw")
    for perm in ("view", "change"):
        user_viewset_permission(user, cv_author, perm)
    client.force_login(user)
    view, request = _detail_view(client, cv_author, author_douglas_adams)
    plain = view.cv_get_context("update", obj=author_douglas_adams, user=request.user, request=request)
    assert "cv_label_mode" not in plain
    stamped = view.cv_get_context(
        "update", obj=author_douglas_adams, user=request.user, request=request, location="context"
    )
    assert stamped["cv_label_mode"] == "both"
    assert (
        view.cv_get_context(
            "no_such_key", obj=author_douglas_adams, user=request.user, request=request, location="context"
        )
        == {}
    )
    (custom_loop,) = view.cv_get_context_buttons(["update"], obj=author_douglas_adams)
    assert custom_loop["cv_label_mode"] == "both"
```

- [ ] **Step 2: Run them to see them fail**

Run: `pytest tests/test1/test_action_label_mode_render.py -v -n auto`
Expected: every labelled assertion FAILS (buttons still icon-only); `test_cv_get_context_without_location_is_unstamped` fails with `TypeError: unexpected keyword argument 'location'`.

- [ ] **Step 3: Implement** the signatures from the Interfaces block in `base.py`, the templatetags and the guardian mixin. In `cv_get_context()`, collect the result of both branches into one local before a single stamping `return`, so the context-button branch is stamped too.

- [ ] **Step 4: Run the new module, the guardian pages, the menus, the goldens and the leaves**

Run: `pytest tests/test1/test_action_label_mode_render.py tests/test1/test_guardian.py tests/test1/test_guardian_card.py tests/test1/test_guardian_delete.py tests/test1/test_action_menus_*.py tests/test1/test_button_leaves.py tests/test1/test_context_button_tag.py tests/test1/test_inaccessible_actions_context.py -v -n auto`
Expected: PASS. Then `git status --short tests/test1/golden/` prints nothing.

- [ ] **Step 5: Run the whole suite**

Run: `pytest tests -n auto`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/view/base.py src/crud_views/templatetags/crud_views.py src/crud_views_guardian/lib/mixins.py tests/test1/test_action_label_mode_render.py
git commit -m "feat(view): stamp cv_label_mode on context and list actions from the view (#216)"
```

---

### Task 5: Docs and CHANGELOG

**Files:**
- Modify: `docs/reference/settings.md:74-76`, `docs/reference/action_menus.md:22-50,79-84,151-159`, `docs/reference/buttons.md:235-238,295-340,342-352`, `docs/reference/card-list-view.md:57-78`, `docs/reference/context_buttons.md:66-69,356-366`, `CHANGELOG.md:93`

**Interfaces:**
- Consumes: the names from Tasks 2–4. Every sentence below is a decision; wording is the writer's.

- [ ] **Step 1: `settings.md`.** Two rows after `CRUD_VIEWS_CARD_ACTIONS_INLINE`: `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` — "Label mode per context toolbar action key (`\"label\"`, `\"icon\"`, `\"both\"`); keys not named are `icon`. See [Action menus](action_menus.md#label-mode). Invalid values raise `crud_views.E106`." type `dict[str, str]`, default `{}`; `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` — "The same for list row actions."

- [ ] **Step 2: `action_menus.md`.** After the inline-keys block in "Configuration" add a `## Label mode` section (anchor `label-mode`): the three-row table (settings / ViewSet / CrudView × context / list) with the names, one example (`cv_context_actions_label_mode = {"create": "both"}` on a list view), the resolution order "`CrudView` → `ViewSet` → setting, first value that is not `None` wins, whole; `{}` means every action icon-only", that any key not named is `icon`, that keys are the configured keys as in the inline lists (`"home"`, not `"list"`), that the getters `cv_get_context_actions_label_mode()` / `cv_get_list_actions_label_mode()` / `cv_get_action_label_mode(location, key)` return the result, and that cards use `CardAction.label_mode` instead. In "Labels, icons and the active action" replace "Toolbar items carry the full label as `title`" with: menu items render icon and short label in every mode; a context menu item carries the full label as `title` only when its action is `icon`, so a labelled action has no tooltip inline or folded. Add `crud_views.E106`, `viewset.E211`, `viewset.W291` rows to the system-check table and extend the W290 sentence to W291.

- [ ] **Step 3: `buttons.md`.** Leaf contract rows: `cv_label` → "the full label; on cards the explicit `label`, else the short label, else the key; on `context` and `list` the full label in `icon` mode and the short label in `label` / `both`"; `cv_label_mode` → drop "Always `icon` for `context` and `list`", say it is the view's resolved [label mode](action_menus.md#label-mode) for the key there. "A theme recipe": delete the parenthetical "(for the toolbar and rows only the `:icon` keys are read until #216)"; replace the `primary` guard (the `<span{% if cv_variant != "primary" %} class="visually-hidden"{% endif %}>` trick and the paragraph explaining it) with the knob: `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"create": "both"}` plus `"context:primary:icon"` / `"context:primary"` entries in the registered table, and a leaf override that only renames `active` to `is-active`. System-check table: add the `E211` and `W291` rows.

- [ ] **Step 4: `card-list-view.md`.** After the "Label mode" section's last paragraph, one sentence: toolbar and row buttons have their own key-based knob, link `action_menus.md#label-mode`.

- [ ] **Step 5: `context_buttons.md`.** Custom-template paragraph (line 66): the resolved data now carries `cv_label_mode` for the button's configured key; the bundled filter toggle stays icon-only and passes the literal. `cv_context_button` section: one sentence that the tag follows the view's label mode for that key, like the toolbar.

- [ ] **Step 6: `CHANGELOG.md`**, Unreleased → Added, first bullet:

> Context toolbar and list row buttons can show a text label: `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` / `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` map an action key to `"label"`, `"icon"` or `"both"`, overridable per ViewSet (`context_actions_label_mode`, `list_actions_label_mode`) and per view (`cv_context_actions_label_mode`, `cv_list_actions_label_mode`). Keys not named stay icon-only, so nothing renders differently until a project names one; a labelled button has no tooltip, inline or folded. `cv_get_context()` takes a keyword-only `location`, which an override must accept and pass on. Checks `crud_views.E106`, `viewset.E211`, `viewset.W291`. See `docs/reference/action_menus.md` (#216).

- [ ] **Step 7: Verify the docs build and the formatter**

Run: `ruff format --check docs CHANGELOG.md && mkdocs build -q`
Expected: no reformat, no build warning about the new anchor.

- [ ] **Step 8: Commit**

```bash
git add docs/reference/settings.md docs/reference/action_menus.md docs/reference/buttons.md docs/reference/card-list-view.md docs/reference/context_buttons.md CHANGELOG.md
git commit -m "docs: label mode for context and list buttons (#216)"
```

---

### Task 6: Acceptance note, issue body, PR

**Files:**
- Create: `superpowers/notes/2026-10-22-action-label-mode-context-list-acceptance.md`

- [ ] **Step 1: Full verification**

Run: `ruff check src tests && ruff format --check src tests docs && pytest tests -n auto && git status --short tests/test1/golden/`
Expected: clean, PASS, empty.

- [ ] **Step 2: Write the acceptance note** in the shape of `superpowers/notes/2026-10-22-button-class-label-mode-key-acceptance.md`: each of #216's six acceptance criteria mapped to the test names from Tasks 1–4 and the docs commit, plus the two builder-check decisions (folded `title`, manual placement) with their tests.

```bash
git add superpowers/notes/2026-10-22-action-label-mode-context-list-acceptance.md
git commit -m "docs(notes): acceptance report for #216"
```

- [ ] **Step 3: Bring #216's body in line with what ships.** Under "Things to settle" record the answers: the knob is a per-location `dict[key → LabelMode]` in settings / ViewSet / view; `list` and `context` share it; a labelled action has no tooltip inline or folded; the visible text is the short label. Keep the acceptance criteria. Use `gh issue edit 216 --body-file` with the edited body; show the maintainer the diff of the body before posting.

- [ ] **Step 4: Push and open the PR** (title `feat(buttons): context and list buttons learn the label mode (#216)`; body: the spec path, the resolution chain in three lines, "no golden moves — a diff there is a bug, not a regeneration", the `cv_get_context(location=)` note for overrides, `Closes #216`). After the squash merge: tick #216 in #228's checklist, then `git fetch && git checkout main && git reset --hard origin/main && git fetch --prune`.
