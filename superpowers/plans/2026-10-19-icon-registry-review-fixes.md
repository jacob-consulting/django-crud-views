# Icon Registry Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the eleven findings of the 2026-10-19 code review of `feature/icon-registry`: bad icon
configuration must be reported by `manage.py check` and must never crash a render.

**Architecture:** All hardening lives in `crud_views/lib/icons.py` (resolution, renderers, `icon_check_messages`)
and the view walk in `crud_views/checks.py`. Render paths fail soft (render nothing); system checks are the loud
side and never raise themselves. Two filter cleanups (one expanded-state property, one icon source for header and
toggle) and one object-detail check round it off.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12+, pytest + pytest-django, lxml, MkDocs.

**Spec:** The review findings (table below), read against `superpowers/specs/2026-10-19-icon-registry-design.md`
and `superpowers/plans/2026-10-19-icon-registry.md`. Each finding was reproduced against the branch before this
plan was written.

| # | Finding (file) | Task |
|---|---|---|
| F1 | `CRUD_VIEWS_ICONS` value `None` passes checks, crashes `resolve_icon` (`icons.py`) | 1, 3 |
| F2 | Non-dict `CRUD_VIEWS_ICON_LIBRARIES` entry crashes the check and every render (`icons.py`) | 2 |
| F3 | W353 skips non-str `cv_icon_*` values that crash `render_icon` (`checks.py`) | 1, 3 |
| F4 | E354 never validates the font `class` format string (`icons.py`) | 2 |
| F5 | Filter toggle ignores `cv_get_filter_icon()`; header and toggle can disagree (`buttons.py`) | 5 |
| F6 | Non-callable `renderer` (e.g. `None`) passes checks, renders empty (`icons.py`) | 2 |
| F7 | Table value `""` emits a stray `<i>` instead of nothing (`icons.py`) | 1 |
| F8 | Object-detail group `icon` has no system check (`crud_views_object_detail/lib/mixins.py`) | 6 |
| F9 | `FilterContextButton` duplicates the expanded-state expression of the mixin (`buttons.py`) | 4 |
| F10 | Hard-coded-class test guard uses bare substrings, scans core JS only (`test_icons_templates.py`) | 7 |
| F11 | `_resolve_renderer` and E351 catch only `ImportError` (`icons.py`) | 2 |

## Decisions

- **`None` / blank table value means "no icon".** `CRUD_VIEWS_ICONS = {"field-marker": None}` (or `""`) switches an
  icon off; no check message. Any other non-str icon value is a bug: it renders nothing and is reported.
- **New check IDs:** `crud_views.E355` invalid library config (not a dict, or `renderer` neither `"font"`, a str nor a
  callable); `crud_views.E356` icon value is not a str (table value or `cv_icon_action` / `cv_icon_header`);
  `viewset.W246` object-detail group icon with an unregistered prefix. `ViewSet.icon_header` is `str | None` and
  validated by pydantic, so it needs no E356.
- **`cv_get_filter_icon()` and `{% cv_filter_icon %}` are removed** (clean break, like the already removed
  `cv_filter_icon_class`). The panel header renders `{% cv_icon "filter" %}`; `CRUD_VIEWS_ICONS["filter"]` is the one
  knob for header and toggle. `FilterContextButton` keeps `cv_icon_action = "filter"` so a custom
  `context_action_filter.html` that follows the changelog advice (`{% cv_icon cv_icon_action %}`) still shows an icon.
- **No heuristic for unmigrated bare group icons** (`icon="truck"`): bare values are raw CSS classes by the documented
  rule and a single-token raw class is legitimate (IcoMoon-style fonts). `viewset.W246` covers `prefix:name` only.
- **Render never raises on bad config; checks never raise.** A font `class` that is not a valid format string is an
  E354 error at check time and left to raise at render time (the check gates it, like a missing template).

## Global Constraints

- Python 3.12+, Django 4.2/5.2/6.0; `pytest tests` must pass; `ruff check` and `ruff format --check` clean (line
  length 120, double quotes).
- Package source under `src/`, Python tests under `tests/test1/`. Commit messages follow `fix(icons): ...`.
- No new settings. New check IDs only as listed in Decisions; document every new ID in
  `docs/reference/icons.md` ("System checks" table) and in the CHANGELOG "Added" bullet that lists the IDs.
- JS tests are untouched by this plan. `npx vitest run` needs Node 22 (CI `js.yml`); on this machine's Node 20.20 it
  fails to start (`webidl.util.markAsUncloneable is not a function` from undici) for every JS file, which is
  unrelated to this branch.

## Review Focus

1. **`"xy:a"` where the `xy` library entry is not a dict** at render time (F2 on the render side): renders nothing,
   no exception. Test in Task 2.
2. **A theme calling `register_icon_library("xy", renderer=None)`**: same validation as settings, E355. Test in
   Task 2.
3. **`{% cv_icon v %}` with a non-str from template context** (an int left in a custom template): renders nothing.
   Test in Task 1.
4. **A pinned filter** (`cv_filter_pinned = True`): `cv_filter_expanded` is True and no toggle button is rendered.
   Test in Task 4.
5. **A whitespace-only table value** (`"  "`): treated like empty, renders nothing. Test in Task 1.

---

### Task 1: Blank and non-str icon values render nothing

**Files:**
- Modify: `src/crud_views/lib/icons.py:161-169` (`resolve_icon`)
- Modify: `docs/reference/icons.md:24`
- Test: `tests/test1/test_icons_registry.py`, `tests/test1/test_icons_tag.py`

**Interfaces:**
- Produces: `resolve_icon(value) -> tuple[str, str] | None` returns `None` when `value`, or the table value it maps
  to, is `None`, not a `str`, or whitespace-only. Everything else unchanged.
- Produces: module-private `_icon_str(value: object) -> str | None`: the stripped-check string or `None`. Used
  again by nothing else; keep it private.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_icons_registry.py` (same `override_settings` style as
  the existing tests there):

```python
@pytest.mark.parametrize("value", [None, "", "  "])
def test_table_value_blank_renders_nothing(value):
    with override_settings(CRUD_VIEWS_ICONS={"field-marker": value}):
        assert render_icon("field-marker", css="cv-icon-fw") == ""


@pytest.mark.parametrize("value", [5, ("xy:eye",), object()])
def test_non_str_value_renders_nothing(value):
    assert render_icon(value) == ""


def test_non_str_table_value_renders_nothing():
    with override_settings(CRUD_VIEWS_ICONS={"detail": 5}):
        assert render_icon("detail") == ""
```

and in `tests/test1/test_icons_tag.py`:

```python
def test_cv_icon_tag_non_str_context_value_renders_nothing():
    html = Template("{% load crud_views %}{% cv_icon v %}").render(Context({"v": 5}))
    assert html == ""
```

- [ ] **Step 2: Run** `pytest tests/test1/test_icons_registry.py tests/test1/test_icons_tag.py -v` — Expected: the new
  tests FAIL with `TypeError` (`argument of type 'int' is not iterable`) or with a stray `<i class=" cv-icon-fw"...>`.

- [ ] **Step 3: Implement** `_icon_str` and apply it in `resolve_icon` to the incoming value and to the table value
  (`get_icons().get(value, value)`), returning `None` for either.

- [ ] **Step 4: Run** the two test files — Expected: PASS. Then `pytest tests/test1/test_icons_registry.py -v` as a
  whole: `test_empty_renders_nothing` and `test_raw_class_fallback` still pass.

- [ ] **Step 5: Docs.** In `docs/reference/icons.md` replace line 24 ("An empty value or `None` renders nothing.")
  with: an empty, whitespace-only or `None` value renders nothing, and the same holds for a table value, so
  `CRUD_VIEWS_ICONS = {"field-marker": None}` switches that icon off.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/icons.py docs/reference/icons.md tests/test1/test_icons_registry.py tests/test1/test_icons_tag.py
git commit -m "fix(icons): blank table values switch an icon off, non-str values render nothing"
```

---

### Task 2: Library config validation (E355, E354 format check, E351 any exception)

**Files:**
- Modify: `src/crud_views/lib/icons.py:135-158` (`_resolve_renderer`, `_get_renderers`), `:182-196` (`render_icon`),
  `:218-248` (`icon_check_messages` library loop)
- Modify: `docs/reference/icons.md:211-221` (System checks table), `CHANGELOG.md:59-63` (Added bullet)
- Test: `tests/test1/test_icons_registry.py`, `tests/test1/test_icons_checks.py`

**Interfaces:**
- Produces: `_resolve_renderer(renderer) -> Callable | None`: `"font"` → `font_renderer`; a `str` → `import_string`,
  any `Exception` → `None`; a callable → itself; anything else → `None`.
- Produces: `_get_renderers()` skips library entries whose config is not a `dict` (no key for that prefix).
- Produces: `render_icon` returns `""` when the library config for the prefix is not a `dict`.
- Produces: `icon_check_messages()` library loop, per prefix, in this order:
  1. config not a `dict` → `Error(id="crud_views.E355")`, message
     `Icon library {prefix!r} config must be a dict, got {type(config).__name__}.`, then `continue`.
  2. `renderer == "font"`: `class` missing or not a `str` → E354 (message as today); else trial
     `template.format(name="x")`, any `Exception` → E354 with message
     `Icon library {prefix!r}: 'class' {template!r} is not a valid format string: {exc}`.
  3. `renderer` is a `str` other than `"font"`: `import_string`, any `Exception as exc` → E351 with message
     `Renderer {renderer!r} of icon library {prefix!r} cannot be imported: {type(exc).__name__}: {exc}`.
  4. `renderer` not callable and none of the above → E355, message
     `Icon library {prefix!r}: renderer must be 'font', a dotted path or a callable, got {renderer!r}.`
  Hints for E355: `Set renderer to 'font', a callable or an importable dotted path.` (reuse the E351 hint).

- [ ] **Step 1: Write the failing render tests** in `tests/test1/test_icons_registry.py`:

```python
def _boom(path):
    raise RuntimeError("boom")


def test_non_dict_library_renders_nothing():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": "font"}):
        assert render_icon("xy:a") == ""


def test_non_callable_renderer_renders_nothing():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": None}}):
        assert render_icon("xy:a") == ""


def test_renderer_import_raising_any_exception_renders_nothing(monkeypatch):
    monkeypatch.setattr(icons_module, "import_string", _boom)
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "some.module.render"}}):
        assert render_icon("xy:a") == ""
```

- [ ] **Step 2: Write the failing check tests** in `tests/test1/test_icons_checks.py`:

```python
def _boom(path):
    raise RuntimeError("boom")


def test_e355_library_config_not_a_dict():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": "font"}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E355"]
    assert "'xy'" in messages[0].msg


def test_e355_renderer_not_callable():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": None}}):
        assert ids(check_icons()) == ["crud_views.E355"]


def test_e355_via_register_icon_library(monkeypatch):
    from crud_views.lib import icons as icons_module

    monkeypatch.setattr(icons_module, "_THEME_LIBRARIES", {})
    icons_module.register_icon_library("xy", renderer=None)
    try:
        assert ids(check_icons()) == ["crud_views.E355"]
    finally:
        icons_module.reset_icon_cache()


@pytest.mark.parametrize("template", ["x-{} {name}", "x-{size} {name}", "x-{"])
def test_e354_class_not_a_format_string(template):
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "font", "class": template}}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E354"]
    assert "format string" in messages[0].msg


def test_e351_renderer_import_raises_other_exception(monkeypatch):
    from crud_views.lib import icons as icons_module

    monkeypatch.setattr(icons_module, "import_string", _boom)
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "some.module.render"}}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E351"]
    assert "RuntimeError: boom" in messages[0].msg
```

- [ ] **Step 3: Run** `pytest tests/test1/test_icons_registry.py tests/test1/test_icons_checks.py -v` — Expected: the
  new tests FAIL (`AttributeError: 'str' object has no attribute 'get'`, `RuntimeError: boom`, empty message lists).

- [ ] **Step 4: Implement** the four Produces items. Keep `test_e351_renderer_not_importable`,
  `test_e354_font_library_without_class` and `test_e354_not_for_custom_renderer_or_with_class` passing unchanged.

- [ ] **Step 5: Run** the two test files — Expected: PASS.

- [ ] **Step 6: Docs and changelog.** `docs/reference/icons.md` System checks table: E354 row becomes "a library with
  the `font` renderer has no `class` entry, or its `class` is not a valid format string"; add row `crud_views.E355`
  "a library config is not a dict, or its `renderer` is neither `font`, a dotted path nor a callable". CHANGELOG
  Added bullet: add `E355` to the list of IDs.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/icons.py docs/reference/icons.md CHANGELOG.md tests/test1/test_icons_registry.py tests/test1/test_icons_checks.py
git commit -m "fix(icons): validate library config (E355), font class format (E354), any renderer import error (E351)"
```

---

### Task 3: Non-str icon values are reported (E356)

**Files:**
- Modify: `src/crud_views/lib/icons.py:250-268` (`icon_check_messages` table loop), new public helper
- Modify: `src/crud_views/checks.py:365-392` (`check_icons`)
- Modify: `docs/reference/icons.md` (System checks table, line 24 paragraph), `CHANGELOG.md:59-63`
- Test: `tests/test1/test_icons_checks.py`

**Interfaces:**
- Produces: `is_icon_value(value: object) -> bool` in `crud_views.lib.icons`: `True` for `None` and `str`, else
  `False`. Public (used by `checks.py`).
- Produces: in `icon_check_messages`, per table entry: `not is_icon_value(value)` → `Error(id="crud_views.E356")`,
  message `Icon {key!r} = {value!r} is not a str.`, hint
  `Use a semantic name, 'prefix:name', a raw CSS class, or None for no icon.`, then `continue` (no W352 for it).
- Produces: in `check_icons`, for each `cv_icon_action` / `cv_icon_header` of each view: `not is_icon_value(value)`
  → E356 with message `{owner}.{attr} = {value!r} is not a str.` (same `owner` text as the W353 `warn` closure, same
  hint), and no W353 for that attribute.

- [ ] **Step 1: Replace `test_w353_skips_non_str_values`** in `tests/test1/test_icons_checks.py` (same probe-view
  pattern, same `finally: _REGISTRY.pop`) and add the table tests:

```python
def test_e356_non_str_view_attributes():
    from crud_views.lib.view import CrudView

    name = "icon_check_probe_nonstr"
    viewset = ViewSet(model=Publisher, name=name)
    try:

        class ProbeView(CrudView):
            cv_viewset = viewset
            cv_key = "probe"
            cv_path = "probe"
            cv_icon_action = 5
            cv_icon_header = ("xy:eye",)

        messages = [m for m in check_icons() if m.id in ("crud_views.E356", "crud_views.W353")]
        assert ids(messages) == ["crud_views.E356", "crud_views.E356"]
        text = " ".join(m.msg for m in messages)
        assert "cv_icon_action" in text and "cv_icon_header" in text
    finally:
        _REGISTRY.pop(name, None)


def test_e356_non_str_table_value():
    with override_settings(CRUD_VIEWS_ICONS={"list": 5}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E356"]
    assert "'list'" in messages[0].msg


def test_table_value_none_is_allowed():
    with override_settings(CRUD_VIEWS_ICONS={"filter-close": None}):
        assert check_icons() == []
```

- [ ] **Step 2: Run** `pytest tests/test1/test_icons_checks.py -v` — Expected: the three tests FAIL (`[]` instead of
  E356; `None` already passes, keep it as a regression guard).

- [ ] **Step 3: Implement** `is_icon_value` and the two check sites. Update the `check_icons` docstring to list E356.

- [ ] **Step 4: Run** `pytest tests/test1/test_icons_checks.py tests/test1/test_icons_registry.py -v` — Expected:
  PASS.

- [ ] **Step 5: Docs and changelog.** `docs/reference/icons.md`: add row `crud_views.E356` "a `CRUD_VIEWS_ICONS`
  value, `cv_icon_action` or `cv_icon_header` is neither a str nor `None`"; extend the line-24 paragraph from Task 1
  with "Any other non-string value renders nothing and is reported by `crud_views.E356`." CHANGELOG Added bullet:
  add `E356`.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/icons.py src/crud_views/checks.py docs/reference/icons.md CHANGELOG.md tests/test1/test_icons_checks.py
git commit -m "fix(icons): report non-str icon values (E356) instead of skipping them"
```

---

### Task 4: One `cv_filter_expanded` property for panel and toggle

**Files:**
- Modify: `src/crud_views/lib/views/mixins.py:299-329` (`ListViewTableFilterMixin`)
- Modify: `src/crud_views/lib/view/buttons.py:9,285-317` (`FilterContextButton.get_context`, `SessionData` import)
- Test: `tests/test1/test_filter.py`

**Interfaces:**
- Produces: `ListViewTableFilterMixin.cv_filter_expanded` (read-only `property`, `-> bool`): `True` when
  `cv_filter_pinned`, else `bool(SessionData.from_view(self).get("filter_expanded", False))`.
- Consumes: `get_context_data` sets `context["cv_filter_expanded"] = self.cv_filter_expanded`;
  `FilterContextButton.get_context` sets `data["cv_filter_expanded"] = context.view.cv_filter_expanded` and
  `buttons.py` no longer imports `SessionData`.

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_filter.py`, next to `_filter_icon_states`:

```python
@pytest.mark.django_db
def test_toggle_and_panel_follow_cv_filter_expanded(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    """Both the toggle icon and the panel state read the one view property, not the session directly."""
    view_cls = cv_publisher.get_all_views()["list"]
    monkeypatch.setattr(view_cls, "cv_filter_expanded", property(lambda self: True))
    response = client_user_publisher_view.get("/publisher/")
    assert response.context["cv_filter_expanded"] is True
    assert _filter_icon_states(response) == {"open": True, "close": False}


@pytest.mark.django_db
def test_pinned_filter_is_expanded_without_toggle(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    from lxml import html

    view_cls = cv_publisher.get_all_views()["list"]
    monkeypatch.setattr(view_cls, "cv_filter_pinned", True)
    response = client_user_publisher_view.get("/publisher/")
    assert response.context["cv_filter_expanded"] is True
    assert html.fromstring(response.content).cssselect("#cv-filter-toggle") == []
```

- [ ] **Step 2: Run** `pytest tests/test1/test_filter.py -v` — Expected: the first test FAILS (toggle still reads the
  session: `{"open": False, "close": True}`); the second passes already and stays as the Review Focus guard.

- [ ] **Step 3: Implement** the property, use it in `get_context_data` and in `FilterContextButton.get_context`, drop
  the unused `SessionData` import from `buttons.py`.

- [ ] **Step 4: Run** `pytest tests/test1/test_filter.py -v && ruff check src/crud_views/lib/view/buttons.py` —
  Expected: PASS, no F401.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/views/mixins.py src/crud_views/lib/view/buttons.py tests/test1/test_filter.py
git commit -m "refactor(filter): cv_filter_expanded property shared by panel context and toggle button"
```

---

### Task 5: `filter` is the one icon source for panel header and toggle

**Files:**
- Modify: `src/crud_views/lib/views/list.py:35-40` (remove `cv_get_filter_icon`), `src/crud_views/lib/views/card.py:91-93`
  (remove `cv_get_filter_icon`)
- Modify: `src/crud_views/templatetags/crud_views.py:289-291` (remove `cv_filter_icon` tag)
- Modify: `src/crud_views/templates/crud_views/tags/list_filter.inner.html:6`
- Modify: `CHANGELOG.md:36-38` (removed tags bullet), `docs/` (grep `cv_get_filter_icon`, `cv_filter_icon`)
- Test: `tests/test1/test_icons_templates.py`

**Interfaces:**
- Produces: `list_filter.inner.html` block `cv_filter_header_icon` renders `{% cv_icon "filter" %}`.
- Produces: `ListView` and `CardView` have no `cv_get_filter_icon`; `{% cv_filter_icon %}` no longer exists.
- Unchanged: `FilterContextButton.get_context` keeps `data["cv_icon_action"] = "filter"` (see Decisions).

- [ ] **Step 1: Write the failing tests** in `tests/test1/test_icons_templates.py` (use the `cv_publisher` list page,
  which has a filter; `client_user_publisher_view` and `publisher_penguin` fixtures from `conftest.py`):

```python
@pytest.mark.django_db
def test_filter_header_and_toggle_share_the_filter_icon(client_user_publisher_view, cv_publisher, publisher_penguin):
    with override_settings(CRUD_VIEWS_ICONS={"filter": "fas:magnifying-glass"}):
        resp = client_user_publisher_view.get("/publisher/")
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    header = doc.cssselect("#filter-collapse .card-header i")
    toggle = doc.cssselect("#cv-filter-toggle [data-cv-filter-icon='open'] i")
    assert [i.get("class") for i in header] == ["fa-solid fa-magnifying-glass"]
    assert [i.get("class") for i in toggle] == ["fa-solid fa-magnifying-glass"]
    assert doc.xpath("//i[@class='fa-solid fa-filter']") == []  # no second source of the open icon


def test_cv_filter_icon_tag_and_hook_removed():
    from django.template import Template, TemplateSyntaxError

    from crud_views.lib.views import CardView, ListView

    assert not hasattr(ListView, "cv_get_filter_icon")
    assert not hasattr(CardView, "cv_get_filter_icon")
    with pytest.raises(TemplateSyntaxError):
        Template("{% load crud_views %}{% cv_filter_icon %}")
```

  (`#filter-collapse` wraps the non-pinned panel, `list_filter.html:7`; its `.card-header` holds the header icon.)

- [ ] **Step 2: Run** `pytest tests/test1/test_icons_templates.py -v` — Expected: the second test FAILS (`hasattr`
  True); the first already passes because the hook returns `"filter"` today, and stays as the regression guard.

- [ ] **Step 3: Implement** the removals and the template change. Then
  `grep -rn "cv_get_filter_icon\|cv_filter_icon" src docs tests` must list only the new test.

- [ ] **Step 4: Run** `pytest tests/test1/test_icons_templates.py tests/test1/test_filter.py tests/test1/test_icons_template_names.py -v`
  — Expected: PASS.

- [ ] **Step 5: Changelog and docs.** CHANGELOG removed-tags bullet (line 36): add `cv_filter_icon` and the
  `cv_get_filter_icon()` hook of `ListView` / `CardView`, with "the filter panel header and the toggle both use the
  `filter` icon; change `CRUD_VIEWS_ICONS["filter"]` to change both". Remove any `docs/` mention found by the grep in
  Step 3.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/views/list.py src/crud_views/lib/views/card.py src/crud_views/templatetags/crud_views.py src/crud_views/templates/crud_views/tags/list_filter.inner.html CHANGELOG.md docs tests/test1/test_icons_templates.py
git commit -m "fix(filter)!: panel header and toggle share the filter icon; drop cv_get_filter_icon and cv_filter_icon"
```

---

### Task 6: Object-detail group icon check (viewset.W246)

**Files:**
- Modify: `src/crud_views_object_detail/lib/mixins.py:68-85` (`_checks_property_group`)
- Modify: `docs/reference/icons.md` (System checks table), `CHANGELOG.md:32-35` and `:59-63`
- Test: `tests/test1/od/test_object_detail_view.py`

**Interfaces:**
- Consumes: `crud_views.lib.icons.unregistered_prefix(value) -> str | None` (new import in `mixins.py`);
  `crud_views.lib.check.CheckWarningExpression(context, id, expression, msg)` (yields `viewset.{id}`; add it to the
  existing `from crud_views.lib.check import Check, CheckAttribute, CheckExpression` line).
- Produces: `_checks_property_group` yields, for a `dict` group and for a `PropertyGroupConfig` alike,
  `CheckWarningExpression(context=cls, id="W246", expression=unregistered_prefix(icon) is None,
  msg=f"cv_property_display[{i}]['icon'] = {icon!r} uses unregistered icon library prefix {prefix!r}")` where
  `icon` is `group.icon` / `group.get("icon")` and `prefix = unregistered_prefix(icon)`. The existing early
  `return` for `PropertyGroupConfig` moves after this yield.

- [ ] **Step 1: Write the failing tests** in `tests/test1/od/test_object_detail_view.py` (`_error_ids` collects
  warnings too):

```python
@pytest.mark.parametrize("icon, flagged", [("xy:truck", True), ("fas:truck", False), ("truck", False), (None, False)])
def test_group_icon_unregistered_prefix_w246(icon, flagged):
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [{"title": "A", "icon": icon, "properties": ["name"]}]

    assert ("viewset.W246" in _error_ids(V)) is flagged


def test_group_icon_w246_for_property_group_config():
    from crud_views_object_detail.lib.config import PropertyGroupConfig
    from crud_views_object_detail.lib.views import ObjectDetailView

    class V(ObjectDetailView):
        cv_key = "detail"
        cv_path = "detail"
        cv_property_display = [PropertyGroupConfig(title="A", icon="xy:truck", properties=["name"])]

    assert "viewset.W246" in _error_ids(V)
```

- [ ] **Step 2: Run** `pytest tests/test1/od/test_object_detail_view.py -v` — Expected: the `xy:truck` cases FAIL.

- [ ] **Step 3: Implement** per Produces.

- [ ] **Step 4: Run** `pytest tests/test1/od -v` — Expected: PASS.

- [ ] **Step 5: Docs and changelog.** `docs/reference/icons.md` System checks table: add row `viewset.W246` "an
  object detail group `icon` uses an unregistered library prefix". CHANGELOG line 33 ("An unmigrated bare name is
  not flagged ..."): append "A `prefix:name` group icon with an unregistered prefix is reported by `viewset.W246`."
  Added bullet: add `viewset.W246`.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views_object_detail/lib/mixins.py docs/reference/icons.md CHANGELOG.md tests/test1/od/test_object_detail_view.py
git commit -m "feat(object-detail): W246 warns on group icons with an unregistered library prefix"
```

---

### Task 7: Word-boundary guard for hard-coded icon classes, all apps' static JS

**Files:**
- Modify: `tests/test1/test_icons_templates.py:61-70`

**Interfaces:**
- Produces: module constant `HARDCODED_ICON_CLASS = re.compile(r"(?<![\w-])(fa|bi)-[a-z]")` and the rewritten
  `test_no_hardcoded_icon_classes_in_templates_and_js` scanning `src/*/templates/**/*.html` and
  `src/*/static/**/*.js` (today only `crud_views/static/crud_views/js` has JS; the wider glob covers the other apps
  as soon as they ship any).

- [ ] **Step 1: Add the regex self-test** above the guard:

```python
@pytest.mark.parametrize(
    "text, hit",
    [
        ('class="fa-solid fa-eye"', True),
        ('class="bi bi-eye"', True),
        ("combi-box", False),
        ("data-fa-x", False),
        ("cv-icon-fw", False),
    ],
)
def test_hardcoded_icon_class_regex(text, hit):
    assert bool(HARDCODED_ICON_CLASS.search(text)) is hit
```

- [ ] **Step 2: Run** `pytest tests/test1/test_icons_templates.py -v -k regex` — Expected: FAIL (`NameError`).

- [ ] **Step 3: Implement** the constant and rewrite the guard: `offenders` are the relative paths whose text matches
  `HARDCODED_ICON_CLASS`; `assert files` keeps guarding an empty glob.

- [ ] **Step 4: Run** `pytest tests/test1/test_icons_templates.py -v` — Expected: PASS with `offenders == []` against
  the current tree.

- [ ] **Step 5: Commit**

```bash
git add tests/test1/test_icons_templates.py
git commit -m "test(icons): word-boundary guard for hard-coded icon classes across all apps"
```

---

### Final verification

- [ ] `pytest tests` — Expected: all pass (1367 passed, 3 skipped on the branch before this plan, plus the new
  tests).
- [ ] `ruff check && ruff format --check` — Expected: clean.
- [ ] `grep -n "E355\|E356\|W246" docs/reference/icons.md CHANGELOG.md` — Expected: each ID appears in both files.
