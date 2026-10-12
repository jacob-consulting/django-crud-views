# Hide vs. Disable for Inaccessible Actions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let projects render actions the user may not use as disabled (greyed out) instead of hidden, configurable by setting → ViewSet → target CrudView, across context buttons, list actions and card actions (incl. child card actions).

**Architecture:** The target view's resolved mode travels in the button data built by `CrudView.cv_get_dict()` (`cv_inaccessible_actions`). One pure function `cv_resolve_action(ctx)` in `crud_views/lib/view/visibility.py` decides show / disable / hide at every place an action is rendered or returned. Default templates gain a `{% if cv_disabled %}` branch; the old access condition stays as the second branch, so overridden project templates keep hiding.

**Tech Stack:** Django 4.2–6.0, Pydantic v2, django-tables2, Bootstrap 5 templates, pytest + pytest-django, lxml for HTML assertions.

**Spec:** `superpowers/specs/2026-10-09-inaccessible-actions-hide-disable-design.md`

## Global Constraints

- Setting name `CRUD_VIEWS_INACCESSIBLE_ACTIONS`; values exactly `"hide"` and `"disable"`; default `"hide"`.
- ViewSet field `inaccessible_actions: Literal["hide", "disable"] | None = None`.
- CrudView attribute `cv_inaccessible_actions: str | None = None`; check id `E207` (emitted as `viewset.E207`); settings check id `crud_views.E104`. Do not use E203.
- Resolution order: target `CrudView.cv_inaccessible_actions` → target `cv_viewset.inaccessible_actions` → setting.
- Template variables: `cv_disabled` (bool), `cv_disabled_reason` (`"permission"` | `"state"`), `cv_url` is `None` when disabled. HTML hook: `data-cv-disabled="{{ cv_disabled_reason }}"`.
- Disabled elements never carry `href`, `data-cv-action`, `data-cv-modal`, `data-cv-modal-size`; `<a>` gets `class="… disabled" aria-disabled="true" role="button"`; `<button>` gets the `disabled` attribute.
- `cv_context_url` returns `None` for any unusable action in both modes.
- Unchanged: `FilterContextButton` / `context_action_filter.html`, `cv_context_has_permission`, `LinkChildColumn`, `list_action_form.html`.
- No new translatable strings in the package.
- Line length 120, double quotes, ruff. Changelog entries go under `## Unreleased` at the top of `CHANGELOG.md`.
- Run tests with the repo venv: `.venv/bin/pytest …` from the repo root.

## Review Focus

1. **Overridden tag templates with the old condition** — a project that copied `list_action.html` before this change must keep *hiding* in disable mode, never render a link with `href="None"`. Test: Task 2 `test_old_template_condition_still_hides_disabled_data`.
2. **Re-rendering already-resolved data** — `{% cv_render_context_button ctx %}` over `view.cv_get_context_buttons` resolves twice; a disabled entry must stay disabled, a usable one usable. Tests: Task 2 `test_resolve_is_idempotent`, Task 3 `test_loop_render_disabled_entry`.
3. **Mixed modes in one row** — delete set to `"disable"`, update left at `"hide"`: the row shows a disabled delete and *no* update control. Test: Task 4 `test_list_get_action_disabled` (asserts update absent).
4. **A disabled POST action must never submit** — no hidden `form[id^="cv_form_"]`, no `data-cv-action` on the disabled control, for list and card. Tests: Task 4 `test_list_post_action_disabled_has_no_form`, Task 5 `test_card_post_action_disabled_has_no_form`.
5. **Mis-cased / misspelled mode values** (`"Disable"`, `"grey"`) fail loudly at startup (check or ValidationError), not silently as "hide" at render time. Tests: Task 1 `test_invalid_setting_reported_e104`, `test_viewset_rejects_invalid_value`, `test_e207_invalid_view_value`.

---

### Task 1: Configuration and resolution

**Files:**
- Modify: `src/crud_views/lib/settings.py` (new field + E104 in `check_messages`)
- Modify: `src/crud_views/lib/viewset/__init__.py` (new field `inaccessible_actions`; `Literal` import)
- Modify: `src/crud_views/lib/view/base.py` (attribute `cv_inaccessible_actions`, check E207 in `checks()`, classmethod `cv_get_inaccessible_actions()`, key in `cv_get_dict()`)
- Test: `tests/test1/test_inaccessible_actions_config.py` (create)

**Interfaces:**
- Produces: `crud_views_settings.inaccessible_actions: str`; `CrudViewsSettings.INACCESSIBLE_ACTIONS_VALUES = ("hide", "disable")`; `ViewSet.inaccessible_actions`; `CrudView.cv_inaccessible_actions`; `CrudView.cv_get_inaccessible_actions() -> str` (classmethod); every `cv_get_dict()` result contains `"cv_inaccessible_actions": "hide" | "disable"`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_inaccessible_actions_config.py`:

```python
"""#149: CRUD_VIEWS_INACCESSIBLE_ACTIONS setting, ViewSet.inaccessible_actions, CrudView.cv_inaccessible_actions."""

import pytest
from django.urls import reverse
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from tests.test1.app.views import PublisherDeleteView, cv_publisher


def test_setting_default_is_hide():
    assert CrudViewsSettings().inaccessible_actions == "hide"


@pytest.mark.parametrize("value", ["grey", "Disable", ""])
def test_invalid_setting_reported_e104(value):
    messages = CrudViewsSettings(inaccessible_actions=value).check_messages
    assert [m.id for m in messages] == ["crud_views.E104"]
    assert "CRUD_VIEWS_INACCESSIBLE_ACTIONS" in messages[0].msg


def test_valid_setting_disable_has_no_messages():
    assert CrudViewsSettings(inaccessible_actions="disable").check_messages == []


def test_viewset_rejects_invalid_value():
    from crud_views.lib.viewset import ViewSet
    from tests.test1.app.models import Publisher

    with pytest.raises(ValidationError):
        ViewSet(model=Publisher, name="publisher_bad_mode_149", inaccessible_actions="Disable")


def test_default_resolves_to_hide():
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "hide"


def test_resolution_falls_back_to_setting(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "inaccessible_actions", "disable")
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "disable"


def test_viewset_overrides_setting(monkeypatch):
    monkeypatch.setattr(cv_publisher, "inaccessible_actions", "disable")
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "disable"


def test_view_overrides_viewset(monkeypatch):
    monkeypatch.setattr(cv_publisher, "inaccessible_actions", "disable")
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", "hide")
    assert PublisherDeleteView.cv_get_inaccessible_actions() == "hide"


def _check_ids(view_cls) -> list[str]:
    return [m.id for c in view_cls.checks() for m in c.messages()]


@pytest.mark.parametrize("value", ["grey", "Disable"])
def test_e207_invalid_view_value(monkeypatch, value):
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", value)
    assert "viewset.E207" in _check_ids(PublisherDeleteView)


@pytest.mark.parametrize("value", [None, "hide", "disable"])
def test_e207_valid_view_values(monkeypatch, value):
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", value)
    assert "viewset.E207" not in _check_ids(PublisherDeleteView)


@pytest.mark.django_db
def test_button_data_carries_target_mode(client_user_publisher_view, publisher_penguin, monkeypatch):
    # the TARGET view's mode travels in the data (delete -> PublisherDeleteView), not the rendering view's
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", "disable")
    resp = client_user_publisher_view.get(
        reverse(cv_publisher.get_router_name("detail"), kwargs={"pk": publisher_penguin.pk})
    )
    view, request = resp.context["view"], resp.context["request"]
    delete_ctx = view.cv_get_context(key="delete", obj=publisher_penguin, user=request.user, request=request)
    update_ctx = view.cv_get_context(key="update", obj=publisher_penguin, user=request.user, request=request)
    assert delete_ctx["cv_inaccessible_actions"] == "disable"
    assert update_ctx["cv_inaccessible_actions"] == "hide"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_config.py -v`
Expected: FAIL — `CrudViewsSettings` has no field `inaccessible_actions` (pydantic ignores the unknown kwarg, so `AttributeError`), `cv_get_inaccessible_actions` missing.

- [ ] **Step 3: Implement the setting and E104**

In `src/crud_views/lib/settings.py`, add the ClassVar next to `MANAGE_VIEWS_ENABLED_VALUES`:

```python
    INACCESSIBLE_ACTIONS_VALUES: ClassVar[tuple[str, ...]] = ("hide", "disable")
```

Add the field after the `assets_bundled` field:

```python
    # actions the user may not use: "hide" (default) or "disable" (rendered greyed out); see ViewSet /
    # CrudView overrides (cv_get_inaccessible_actions)
    inaccessible_actions: str = from_settings("CRUD_VIEWS_INACCESSIBLE_ACTIONS", default="hide")
```

In `check_messages`, directly after the `crud_views.E101` block:

```python
        if self.inaccessible_actions not in self.INACCESSIBLE_ACTIONS_VALUES:
            messages.append(
                Error(
                    id="crud_views.E104",
                    msg=(
                        f"setting CRUD_VIEWS_INACCESSIBLE_ACTIONS must be one of "
                        f"{self.INACCESSIBLE_ACTIONS_VALUES}, got {self.inaccessible_actions!r}"
                    ),
                )
            )
```

- [ ] **Step 4: Implement the ViewSet field**

In `src/crud_views/lib/viewset/__init__.py` change `from typing import ClassVar, Self` to `from typing import ClassVar, Literal, Self` and add after the `extends` field:

```python
    inaccessible_actions: Literal["hide", "disable"] | None = None  # None: CRUD_VIEWS_INACCESSIBLE_ACTIONS
```

- [ ] **Step 5: Implement the CrudView attribute, check and resolution**

In `src/crud_views/lib/view/base.py`, next to `cv_extends_template` (line ~74):

```python
    cv_inaccessible_actions: str | None = None  # "hide" | "disable"; None: ViewSet, then setting
```

In `checks()`, directly after the `E253` `CheckExpression`:

```python
        yield CheckExpression(
            context=cls,
            id="E207",
            expression=cls.cv_inaccessible_actions in (None, "hide", "disable"),
            msg=f"cv_inaccessible_actions must be None, 'hide' or 'disable', got {cls.cv_inaccessible_actions!r}",
        )
```

Directly after `cv_get_extends_template()` add:

```python
    @classmethod
    def cv_get_inaccessible_actions(cls) -> str:
        """Hide or disable this action's button for users who may not use it: view, then ViewSet, then setting."""
        if cls.cv_inaccessible_actions:
            return cls.cv_inaccessible_actions
        if cls.cv_viewset is not None and cls.cv_viewset.inaccessible_actions:
            return cls.cv_viewset.inaccessible_actions
        return crud_views_settings.inaccessible_actions
```

In `cv_get_dict()` add to the `data` dict literal, after `"cv_modal_size": cls.cv_modal_size,`:

```python
            "cv_inaccessible_actions": cls.cv_get_inaccessible_actions(),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_config.py -v`
Expected: all PASS.

- [ ] **Step 7: Run the full suite (default behaviour unchanged)**

Run: `.venv/bin/pytest tests -q`
Expected: all PASS (only a new key was added to the data dicts).

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/settings.py src/crud_views/lib/viewset/__init__.py src/crud_views/lib/view/base.py tests/test1/test_inaccessible_actions_config.py
git commit -m "feat: CRUD_VIEWS_INACCESSIBLE_ACTIONS setting with ViewSet/CrudView overrides, E104/E207 (#149)"
```

---

### Task 2: The deciding function `cv_resolve_action`

**Files:**
- Create: `src/crud_views/lib/view/visibility.py`
- Test: `tests/test1/test_inaccessible_actions_resolve.py` (create)

**Interfaces:**
- Consumes: data dicts with keys `cv_access`, `cv_action_enabled`, `cv_inaccessible_actions` (Task 1).
- Produces: `crud_views.lib.view.visibility.cv_resolve_action(ctx: dict | None) -> dict | None` — `None` = hide; otherwise a new dict with `cv_disabled: bool`; when disabled also `cv_url: None` and `cv_disabled_reason: "permission" | "state"`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_inaccessible_actions_resolve.py`:

```python
"""#149: cv_resolve_action decides show / disable / hide from an action's button data."""

import pytest
from django.template import Context, Template

from crud_views.lib.view.visibility import cv_resolve_action


def _ctx(access=True, enabled=True, mode="hide", **extra):
    return {
        "cv_key": "delete",
        "cv_url": "/x/1/delete/",
        "cv_access": access,
        "cv_action_enabled": enabled,
        "cv_inaccessible_actions": mode,
        **extra,
    }


@pytest.mark.parametrize("ctx", [None, {}])
def test_empty_hides(ctx):
    assert cv_resolve_action(ctx) is None


@pytest.mark.parametrize("mode", ["hide", "disable"])
def test_usable_is_shown_unchanged(mode):
    out = cv_resolve_action(_ctx(mode=mode))
    assert out["cv_disabled"] is False
    assert out["cv_url"] == "/x/1/delete/"
    assert "cv_disabled_reason" not in out


@pytest.mark.parametrize("access, enabled", [(False, True), (True, False), (False, False)])
def test_hide_mode_hides_unusable(access, enabled):
    assert cv_resolve_action(_ctx(access=access, enabled=enabled, mode="hide")) is None


@pytest.mark.parametrize(
    "access, enabled, reason",
    [(False, True, "permission"), (True, False, "state"), (False, False, "permission")],
)
def test_disable_mode_flags_unusable(access, enabled, reason):
    out = cv_resolve_action(_ctx(access=access, enabled=enabled, mode="disable"))
    assert out["cv_disabled"] is True
    assert out["cv_url"] is None
    assert out["cv_disabled_reason"] == reason
    assert out["cv_key"] == "delete"


def test_missing_mode_key_hides():
    ctx = _ctx(access=False)
    del ctx["cv_inaccessible_actions"]
    assert cv_resolve_action(ctx) is None


def test_access_must_be_exactly_true():
    # a truthy non-True value is not access (same rule as the old _context_button_visible)
    assert cv_resolve_action(_ctx(access="yes", mode="hide")) is None


def test_input_is_not_mutated():
    ctx = _ctx(access=False, mode="disable")
    before = dict(ctx)
    cv_resolve_action(ctx)
    assert ctx == before


@pytest.mark.parametrize("access, enabled", [(True, True), (False, True), (True, False)])
def test_resolve_is_idempotent(access, enabled):
    once = cv_resolve_action(_ctx(access=access, enabled=enabled, mode="disable"))
    assert cv_resolve_action(once) == once


def test_old_template_condition_still_hides_disabled_data():
    # a project template overridden before #149 keeps today's condition: it must render nothing
    out = cv_resolve_action(_ctx(access=False, mode="disable"))
    tpl = Template('{% if cv_action_enabled is not False and cv_access is True %}<a href="{{ cv_url }}">{% endif %}')
    assert tpl.render(Context(out)) == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_resolve.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crud_views.lib.view.visibility'`.

- [ ] **Step 3: Implement**

Create `src/crud_views/lib/view/visibility.py`:

```python
def cv_resolve_action(ctx: dict | None) -> dict | None:
    """Resolve an action's button data to show / disable / hide (#149).

    An action is usable when the user may access its target (cv_access is True) and the action is
    enabled (cv_action_enabled is not False). An unusable action is hidden unless its target view
    resolved cv_inaccessible_actions to "disable" (see CrudView.cv_get_inaccessible_actions).

    Returns None to hide, a copy flagged cv_disabled=True (cv_url=None, cv_disabled_reason
    "permission" | "state") to render disabled, or a copy flagged cv_disabled=False to render
    normally. Never mutates ctx; resolving resolved data again gives the same result.
    """
    if not ctx:
        return None
    usable = ctx.get("cv_access") is True and ctx.get("cv_action_enabled") is not False
    if usable:
        return {**ctx, "cv_disabled": False}
    if ctx.get("cv_inaccessible_actions") != "disable":
        return None
    reason = "permission" if ctx.get("cv_access") is not True else "state"
    return {**ctx, "cv_disabled": True, "cv_url": None, "cv_disabled_reason": reason}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_resolve.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/visibility.py tests/test1/test_inaccessible_actions_resolve.py
git commit -m "feat: cv_resolve_action decides show/disable/hide for an action (#149)"
```

---

### Task 3: Context buttons — call sites and template

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (`_context_button_visible` removed; `_render_context_button`, `cv_context_action`, `cv_context_url` use `cv_resolve_action`)
- Modify: `src/crud_views/lib/view/base.py` (`cv_get_context_buttons`)
- Modify: `src/crud_views/templates/crud_views/tags/context_action.html`
- Test: `tests/test1/test_inaccessible_actions_context.py` (create)

**Interfaces:**
- Consumes: `cv_resolve_action` (Task 2), `cv_inaccessible_actions` in data (Task 1).
- Produces: disabled context buttons rendered as `<a class="btn btn-outline-primary btn-lg disabled" aria-disabled="true" role="button" data-cv-disabled=… cv-key=…>`; `CrudView.cv_get_context_buttons()` returns resolved dicts (incl. disabled entries).

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_inaccessible_actions_context.py`:

```python
"""#149: context buttons (toolbar, cv_context_button, cv_context_url, cv_get_context_buttons) in disable mode."""

import pytest
from django.template import Context, Template
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import ContextButton
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorDeleteView, AuthorDetailView, AuthorUpdateView


@pytest.fixture
def client_author_view_change(client, cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view_change_149", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    client.force_login(user)
    return client


def _detail(client, cv_author, author):
    resp = client.get(reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk}))
    assert resp.status_code == 200
    return resp


def _render(resp, source):
    return Template("{% load crud_views %}" + source).render(
        Context({"view": resp.context["view"], "request": resp.context["request"]})
    )


@pytest.mark.django_db
def test_toolbar_hide_is_default(client_user_author_view, cv_author, author_douglas_adams):
    doc = lxml_html.fromstring(_detail(client_user_author_view, cv_author, author_douglas_adams).content)
    assert doc.cssselect('[cv-context-container] [cv-key="delete"]') == []


@pytest.mark.django_db
def test_toolbar_disabled_for_permission(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    doc = lxml_html.fromstring(resp.content)
    (btn,) = doc.cssselect('[cv-context-container] [cv-key="delete"]')
    assert btn.tag == "a"
    assert "disabled" in btn.get("class").split()
    assert btn.get("aria-disabled") == "true"
    assert btn.get("role") == "button"
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert btn.get("data-cv-modal") is None
    assert f"/author/{author_douglas_adams.pk}/delete/" not in resp.content.decode()
    # update targets AuthorUpdateView, still "hide": absent
    assert doc.cssselect('[cv-context-container] [cv-key="update"]') == []


@pytest.mark.django_db
def test_toolbar_disabled_for_state(client_author_view_change, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(AuthorUpdateView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    doc = lxml_html.fromstring(_detail(client_author_view_change, cv_author, author_douglas_adams).content)
    (btn,) = doc.cssselect('[cv-context-container] [cv-key="update"]')
    assert btn.get("data-cv-disabled") == "state"
    assert btn.get("href") is None


@pytest.mark.django_db
def test_context_button_tag_and_url(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    out = _render(resp, '{% cv_context_button "delete" %}|{% cv_context_url "delete" as u %}[{{ u }}]')
    button, url = out.split("|")
    assert 'aria-disabled="true"' in button
    assert "href=" not in button
    assert url == "[None]"


@pytest.mark.django_db
def test_context_url_none_in_hide_mode(client_user_author_view, cv_author, author_douglas_adams):
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    assert _render(resp, '{% cv_context_url "delete" as u %}[{{ u }}]') == "[None]"


@pytest.mark.django_db
def test_get_context_buttons_flags_disabled(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    view = _detail(client_user_author_view, cv_author, author_douglas_adams).context["view"]
    by_key = {b["cv_key"]: b for b in view.cv_get_context_buttons()}
    assert by_key["delete"]["cv_disabled"] is True
    assert by_key["delete"]["cv_url"] is None
    assert by_key["detail"]["cv_disabled"] is False
    assert "update" not in by_key


@pytest.mark.django_db
def test_loop_render_disabled_entry(client_user_author_view, cv_author, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    out = _render(resp, "{% for ctx in view.cv_get_context_buttons %}<li>{% cv_render_context_button ctx %}</li>{% endfor %}")
    doc = lxml_html.fromstring(f"<ul>{out}</ul>")
    (btn,) = doc.cssselect('[cv-key="delete"]')
    assert btn.get("aria-disabled") == "true"
    (detail,) = doc.cssselect('[cv-key="detail"]')
    assert detail.get("href")


@pytest.mark.django_db
def test_custom_template_code_receives_disabled_data(
    client_user_author_view, cv_author, author_douglas_adams, monkeypatch
):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(
        AuthorDetailView,
        "cv_context_buttons",
        [
            ContextButton(
                key="del_custom",
                key_target="delete",
                template_code='<i data-d="{{ cv_disabled }}" data-r="{{ cv_disabled_reason }}" data-u="{{ cv_url }}"></i>',
            )
        ],
    )
    resp = _detail(client_user_author_view, cv_author, author_douglas_adams)
    assert _render(resp, '{% cv_context_button "del_custom" %}') == '<i data-d="True" data-r="permission" data-u="None"></i>'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_context.py -v`
Expected: `test_toolbar_hide_is_default` and `test_context_url_none_in_hide_mode` PASS; every disable-mode test FAILS (buttons hidden, `cv_disabled` key missing).

- [ ] **Step 3: Use `cv_resolve_action` in the template tags**

In `src/crud_views/templatetags/crud_views.py`:

Add the import next to `from crud_views.lib.view import CrudView`:

```python
from crud_views.lib.view.visibility import cv_resolve_action
```

Delete the function `_context_button_visible` entirely and replace `_render_context_button` with:

```python
def _render_context_button(view, ctx) -> str:
    ctx = cv_resolve_action(ctx)
    if ctx is None:
        return ""
    if ctx.get("cv_template_code"):
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    template = ctx.get("cv_template") or crud_views_settings.context_button_template
    return view.render_snippet(ctx, template=template)
```

In `cv_context_action` replace

```python
    ctx = cv_get_context(context=context, key=key, obj=obj)
    # gate here, not only in the default template: per-button template / template_code must not show a
    # button the user may not use (#147)
    if not _context_button_visible(ctx):
        return ""
```

with

```python
    # gate here, not only in the default template: per-button template / template_code must not show a
    # button the user may not use (#147); in disable mode they get cv_disabled data instead (#149)
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    if ctx is None:
        return ""
```

In `cv_context_url` replace

```python
    ctx = cv_get_context(context=context, key=key, obj=obj)
    if not _context_button_visible(ctx):
        return None
    return ctx.get("cv_url")
```

with

```python
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    # a bare URL cannot say "disabled": None for every unusable action, in both modes (#149)
    if ctx is None or ctx["cv_disabled"]:
        return None
    return ctx.get("cv_url")
```

Then run `grep -rn "_context_button_visible" src tests` — expected: no output.

- [ ] **Step 4: Use `cv_resolve_action` in `cv_get_context_buttons`**

In `src/crud_views/lib/view/base.py` add `from .visibility import cv_resolve_action` to the module's relative imports, and replace the body loop of `cv_get_context_buttons`:

```python
        result: list[dict] = []
        for key in keys:
            ctx = cv_resolve_action(self.cv_get_context(key=key, obj=obj, user=self.request.user, request=self.request))
            if ctx is not None:
                result.append(ctx)
        return result
```

and change its docstring first line to:

```python
        Resolved context-button data for a custom template loop: hidden buttons are left out, disabled
        ones (cv_inaccessible_actions = "disable") are included with cv_disabled=True.
```

- [ ] **Step 5: Add the disabled branch to `context_action.html`**

Replace `src/crud_views/templates/crud_views/tags/context_action.html` with:

```django
{% if cv_key and cv_disabled %}
    <a class="btn btn-outline-primary btn-lg disabled" aria-disabled="true" role="button"
       data-cv-disabled="{{ cv_disabled_reason }}"
       title="{{ cv_action_label }}"
       cv-key="{{ cv_key }}">
        {% if cv_icon_action %}<i class="{{ cv_icon_action }}" aria-hidden="true"></i>{% endif %}<span class="visually-hidden">{{ cv_action_label }}</span>
    </a>
{% elif cv_key and cv_action_enabled is not False and cv_access is True %}
    <a href="{{ cv_url }}" class="btn btn-outline-primary {% if cv_is_active %}active{% endif %} btn-lg"
       title="{{ cv_action_label }}"
       {% if cv_modal %}data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}"{% endif %}
       cv-key="{{ cv_key }}">
        {% if cv_icon_action %}<i class="{{ cv_icon_action }}" aria-hidden="true"></i>{% endif %}<span class="visually-hidden">{{ cv_action_label }}</span>
    </a>
{% endif %}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_context.py -v`
Expected: all PASS.

- [ ] **Step 7: Run the full suite**

Run: `.venv/bin/pytest tests -q`
Expected: all PASS. If a test imported `_context_button_visible`, change it to call `cv_resolve_action(ctx) is not None` instead.

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py src/crud_views/lib/view/base.py src/crud_views/templates/crud_views/tags/context_action.html tests/test1/test_inaccessible_actions_context.py
git commit -m "feat: context buttons render disabled in disable mode (#149)"
```

---

### Task 4: List actions

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (`cv_list_action`, `cv_list_action_form`)
- Modify: `src/crud_views/templates/crud_views/tags/list_action.html`
- Test: `tests/test1/test_inaccessible_actions_list.py` (create)

**Interfaces:**
- Consumes: `cv_resolve_action` (Task 2).
- Produces: disabled list actions — GET/modal as `<a class="btn btn-outline-primary btn-xs disabled" aria-disabled="true" role="button" data-cv-disabled=… cv-key=…>`, POST as `<button type="button" class="btn btn-outline-primary btn-xs" disabled data-cv-disabled=… cv-key=…>`; no hidden form for disabled POST actions.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_inaccessible_actions_list.py`:

```python
"""#149: list actions (and their hidden POST forms) in disable mode."""

import pytest
from lxml import html as lxml_html

from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.views import (
    AuthorDeleteView,
    AuthorListView,
    AuthorUpView,
    GuardianAuthorDeleteView,
    PublisherDeleteView,
)


def _doc(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.content.decode(), lxml_html.fromstring(resp.content)


@pytest.mark.django_db
def test_list_hide_is_default(client_user_publisher_view, publisher_penguin):
    content, doc = _doc(client_user_publisher_view, "/publisher/")
    assert doc.cssselect('[cv-key="delete"]') == []
    assert f"/publisher/{publisher_penguin.pk}/delete/" not in content


@pytest.mark.django_db
def test_list_get_action_disabled(client_user_publisher_view, publisher_penguin, monkeypatch):
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", "disable")
    content, doc = _doc(client_user_publisher_view, "/publisher/")
    (btn,) = doc.cssselect('a[cv-key="delete"]')
    assert "disabled" in btn.get("class").split()
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert f"/publisher/{publisher_penguin.pk}/delete/" not in content
    # mixed modes: update (PublisherUpdateView) is still "hide"
    assert doc.cssselect('[cv-key="update"]') == []
    # usable action untouched
    (detail,) = doc.cssselect('a[cv-key="detail"]')
    # links may carry ?cv_from=<origin>; compare the path only
    assert detail.get("href", "").startswith(f"/publisher/{publisher_penguin.pk}/detail/")


@pytest.mark.django_db
def test_list_post_action_disabled_has_no_form(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "up"])
    monkeypatch.setattr(AuthorUpView, "cv_inaccessible_actions", "disable")
    content, doc = _doc(client_user_author_view, "/author/")
    (btn,) = doc.cssselect('[cv-key="up"]')
    assert btn.tag == "button"
    assert btn.get("disabled") is not None
    assert btn.get("data-cv-action") is None
    assert btn.get("data-cv-target") is None
    assert doc.cssselect('form[id^="cv_form_"]') == []
    assert f"/author/{author_douglas_adams.pk}/up/" not in content


@pytest.mark.django_db
def test_list_modal_action_disabled(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    _, doc = _doc(client_user_author_view, "/author/")
    (btn,) = doc.cssselect('a[cv-key="delete"]')
    assert btn.get("href") is None
    assert btn.get("data-cv-modal") is None
    assert btn.get("data-cv-modal-size") is None


@pytest.mark.django_db
def test_guardian_object_denial_disabled(client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, monkeypatch):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    monkeypatch.setattr(GuardianAuthorDeleteView, "cv_inaccessible_actions", "disable")
    _, doc = _doc(client_guardian, "/guardian_author/")
    (btn,) = doc.cssselect('a[cv-key="delete"]')
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
```

Before running: confirm `GuardianAuthorDeleteView` is importable from `tests.test1.app.views` (`grep -n "class GuardianAuthorDeleteView" tests/test1/app/views*.py`); if it lives in another module, import it from there.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_list.py -v`
Expected: `test_list_hide_is_default` PASS; all disable-mode tests FAIL (no element for the selector).

- [ ] **Step 3: Use `cv_resolve_action` in the list tags**

In `src/crud_views/templatetags/crud_views.py` replace both tag bodies:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action.html", takes_context=True)
def cv_list_action(context, key, obj=None):
    return cv_resolve_action(cv_get_context(context=context, key=key, obj=obj)) or {}


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/list_action_form.html", takes_context=True)
def cv_list_action_form(context, key, obj=None):
    ctx = cv_resolve_action(cv_get_context(context=context, key=key, obj=obj))
    # a disabled button never submits: no hidden POST form for it (#149)
    if ctx is None or ctx["cv_disabled"]:
        return {}
    return ctx
```

- [ ] **Step 4: Add the disabled branch to `list_action.html`**

Replace `src/crud_views/templates/crud_views/tags/list_action.html` with:

```django
{% if cv_disabled %}
{% if cv_list_action_method == "post" and not cv_modal %}
<button type="button"
    class="btn btn-outline-primary btn-xs"
    disabled
    data-cv-disabled="{{ cv_disabled_reason }}"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    {% if cv_icon_action %}<i class="{{ cv_icon_action }}" aria-hidden="true"></i>{% endif %}<span class="visually-hidden">{{ cv_action_label }}</span>
</button>
{% else %}
<a class="btn btn-outline-primary btn-xs disabled"
    aria-disabled="true"
    role="button"
    data-cv-disabled="{{ cv_disabled_reason }}"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    {% if cv_icon_action %}<i class="{{ cv_icon_action }}" aria-hidden="true"></i>{% endif %}<span class="visually-hidden">{{ cv_action_label }}</span>
</a>
{% endif %}
{% elif cv_action_enabled is not False and cv_access is True %}
{% if cv_list_action_method == "post" and not cv_modal %}
<button type="button"
    data-cv-action="submit-form"
    data-cv-target="cv_form_{{ cv_oid }}"
    class="btn btn-outline-primary btn-xs"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    {% if cv_icon_action %}<i class="{{ cv_icon_action }}" aria-hidden="true"></i>{% endif %}<span class="visually-hidden">{{ cv_action_label }}</span>
</button>
{% else %}
<a {% if cv_modal %}
    href="{{ cv_url }}"
    data-cv-modal="true"
    data-cv-modal-size="{{ cv_modal_size }}"
{% elif cv_list_action_method == "get" %}
    href="{{ cv_url }}"
{% endif %}
    class="btn btn-outline-primary btn-xs"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    {% if cv_icon_action %}<i class="{{ cv_icon_action }}" aria-hidden="true"></i>{% endif %}<span class="visually-hidden">{{ cv_action_label }}</span>
</a>
{% endif %}
{% endif %}
```

(`list_action_form.html` stays unchanged.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_list.py -v`
Expected: all PASS.

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/pytest tests -q`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py src/crud_views/templates/crud_views/tags/list_action.html tests/test1/test_inaccessible_actions_list.py
git commit -m "feat: list actions render disabled in disable mode, no hidden form for them (#149)"
```

---

### Task 5: Card actions, including child card actions (behaviour change)

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (`cv_card_action`)
- Modify: `src/crud_views/templates/crud_views/tags/card_action.html`
- Modify: `tests/test1/test_card.py` (rewrite `test_card_child_action_always_renders`)
- Modify: `docs/reference/card-list-view.md` (the "Child actions always render" paragraph)
- Test: `tests/test1/test_inaccessible_actions_card.py` (create)

**Interfaces:**
- Consumes: `cv_resolve_action` (Task 2), `CrudView.cv_get_inaccessible_actions()` (Task 1).
- Produces: `cv_card_action` returns resolved data or `{}`; child card actions check `child_cls.cv_has_access(user, obj)`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_inaccessible_actions_card.py`:

```python
"""#149: card actions (key and child) in disable mode; child card actions check child permission."""

import pytest
from django.test import Client
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, AuthorUpdateView, AuthorUpView, BookListView


def _card(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    return resp.content.decode(), doc.cssselect(".card.mb-3")[0]


def _by_text(card, text):
    return [a for a in card.cssselect("a.btn") if text in a.text_content()]


@pytest.mark.django_db
def test_card_hide_is_default(client_user_author_view, author_douglas_adams):
    _, card = _card(client_user_author_view, "/author/card/")
    assert _by_text(card, "Edit") == []


@pytest.mark.django_db
def test_card_key_action_disabled(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    content, card = _card(client_user_author_view, "/author/card/")
    (btn,) = _by_text(card, "Edit")
    assert "disabled" in btn.get("class").split()
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert f"/author/{author_douglas_adams.pk}/update/" not in content


@pytest.mark.django_db
def test_card_post_action_disabled_has_no_form(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", label="Details"), CardAction(key="up", label="Up")])
    monkeypatch.setattr(AuthorUpView, "cv_inaccessible_actions", "disable")
    _, card = _card(client_user_author_view, "/author/card/")
    (btn,) = _by_text(card, "Up")
    assert btn.get("href") is None
    assert btn.get("data-cv-action") is None
    assert card.cssselect('form[id^="cv_form_"]') == []


@pytest.fixture
def client_publisher_view_only(cv_publisher):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_pub_no_book_149", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_child_card_action_disabled_without_child_permission(
    client_publisher_view_only, cv_book, publisher_penguin, monkeypatch
):
    monkeypatch.setattr(BookListView, "cv_inaccessible_actions", "disable")
    content, card = _card(client_publisher_view_only, "/publisher/card/")
    (btn,) = _by_text(card, "Books")
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert f"/publisher/{publisher_penguin.pk}/book/" not in content


@pytest.mark.django_db
def test_child_card_action_disabled_for_state(client_user_publisher_card_149, cv_book, publisher_penguin, monkeypatch):
    monkeypatch.setattr(BookListView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(BookListView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    _, card = _card(client_user_publisher_card_149, "/publisher/card/")
    (btn,) = _by_text(card, "Books")
    assert btn.get("data-cv-disabled") == "state"


@pytest.fixture
def client_user_publisher_card_149(cv_publisher, cv_book):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_pub_card_149", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    user_viewset_permission(user, cv_book, "view")
    client = Client()
    client.force_login(user)
    return client
```

In `tests/test1/test_card.py` replace the whole `test_card_child_action_always_renders` function with:

```python
@pytest.mark.django_db
def test_card_child_action_hidden_without_child_permission(cv_publisher, cv_book, publisher_penguin):
    """Child actions check the child view's permission (#149): no book permission -> no Books button."""
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_pub_no_book", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    client = Client()
    client.force_login(user)

    response = client.get("/publisher/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    actions = card.cssselect("a.btn")
    assert len(actions) == 1
    assert "Books" not in card.text_content()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_card.py tests/test1/test_card.py -v`
Expected: `test_card_hide_is_default` PASS; disable-mode tests and `test_card_child_action_hidden_without_child_permission` FAIL.

- [ ] **Step 3: Rewrite `cv_card_action`**

In `src/crud_views/templatetags/crud_views.py` replace the whole `cv_card_action` function with:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/card_action.html", takes_context=True)
def cv_card_action(context, action, obj=None):
    view = cv_get_view(context)
    user = context["request"].user

    if action.child_name:
        url = view.cv_get_child_url(action.child_name, action.child_key, obj)
        child_viewset = view.cv_viewset.get_viewset(action.child_name)
        child_cls = child_viewset.get_view_class(action.child_key)
        # permission is checked on the child view, like ChildContextButton (#149)
        data = {
            "cv_access": child_cls.cv_has_access(user, obj),
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
        return cv_resolve_action(data) or {}

    cls = view.cv_viewset.get_view_class(action.key)
    url = view.cv_get_link_url(cls, action.key, obj)
    view_context = view.cv_get_view_context(object=obj)

    label = action.label or cls.cv_get_action_short_label(context=view_context)

    # always build the full data: disable mode renders label/icon/variant without access (#149)
    data = cls.cv_get_dict(
        context=view_context,
        cv_oid=view.cv_get_oid(action.key, obj=obj),
        cv_url=url,
        cv_access=cls.cv_has_access(user, obj),
        cv_action_enabled=cls.cv_action_enabled(user, obj),
    )
    data.update(
        cv_label=label,
        cv_variant=action.variant,
        cv_flex=action.flex,
        cv_no_label=action.no_label,
    )
    return cv_resolve_action(data) or {}
```

Before replacing, compare with the current function: if it sets any other key in `data.update(...)` than `cv_label`, `cv_variant`, `cv_flex`, `cv_no_label`, keep that key.

- [ ] **Step 4: Add the disabled branch to `card_action.html`**

Replace `src/crud_views/templates/crud_views/tags/card_action.html` with:

```django
{% if cv_disabled %}
<a class="btn btn-{% if cv_variant == 'primary' %}primary{% elif cv_variant == 'tertiary' %}outline-secondary{% else %}secondary{% endif %} btn-sm{% if cv_flex %} flex-grow-1{% endif %} disabled"
   aria-disabled="true"
   role="button"
   data-cv-disabled="{{ cv_disabled_reason }}"
   {% if cv_no_label %}title="{{ cv_label }}"{% endif %}>
   {% if cv_no_label %}{% if cv_icon_action %}<i class="{{ cv_icon_action }}"></i>{% endif %}{% else %}<span>{{ cv_label }}</span>{% endif %}
</a>
{% elif cv_access and cv_action_enabled is not False %}
{% if cv_list_action_method == "post" %}
<form id="cv_form_{{ cv_oid }}" action="{{ cv_url }}" method="post" class="d-none">{% csrf_token %}</form>
{% endif %}
<a {% if cv_modal %}
       href="{{ cv_url }}"
       data-cv-modal="true"
       data-cv-modal-size="{{ cv_modal_size }}"
   {% elif cv_list_action_method == "post" %}
       href="#"
       data-cv-action="submit-form"
       data-cv-target="cv_form_{{ cv_oid }}"
   {% else %}
       href="{{ cv_url }}"
   {% endif %}
   class="btn btn-{% if cv_variant == 'primary' %}primary{% elif cv_variant == 'tertiary' %}outline-secondary{% else %}secondary{% endif %} btn-sm{% if cv_flex %} flex-grow-1{% endif %}"
   {% if cv_no_label %}title="{{ cv_label }}"{% endif %}>
   {% if cv_no_label %}{% if cv_icon_action %}<i class="{{ cv_icon_action }}"></i>{% endif %}{% else %}<span>{{ cv_label }}</span>{% endif %}
</a>
{% endif %}
```

- [ ] **Step 5: Update the card docs paragraph**

In `docs/reference/card-list-view.md` replace the line

```markdown
Child actions always render (no permission check on the card). The target view handles its own permissions. This matches `LinkChildColumn` behavior for tables.
```

with

```markdown
Child actions check the child view's permission (`cv_has_access` and `cv_action_enabled` on the `child_key` view of
the child ViewSet), like `ChildContextButton`. A user who may not open the child view does not see the button, or sees
it disabled when the child view resolves to `"disable"` (see [Hide or disable inaccessible actions](inaccessible_actions.md)).
Before 0.28.0 child actions always rendered and the target view answered with 403. `LinkChildColumn` in tables still
renders without a permission check. With a `GuardianViewSet` child, the child list view's `cv_has_access` is always
`True` (access to the parent is checked per request), so such child card actions keep rendering — the same as
`ChildContextButton`.
```

Note: the link to `inaccessible_actions.md` resolves once Task 7 creates that page; `mkdocs build --strict` is only
run in Task 7.

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test1/test_inaccessible_actions_card.py tests/test1/test_card.py tests/test1/test_card_action_post.py tests/test1/test_guardian_card.py -v`
Expected: all PASS.

- [ ] **Step 7: Run the full suite**

Run: `.venv/bin/pytest tests -q`
Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py src/crud_views/templates/crud_views/tags/card_action.html tests/test1/test_card.py tests/test1/test_inaccessible_actions_card.py docs/reference/card-list-view.md
git commit -m "feat: card actions render disabled; child card actions check child permission (#149)"
```

---

### Task 6: Example app — disabled delete in `context_buttons`

**Files:**
- Modify: `examples/bootstrap5/context_buttons/views.py` (`TicketDeleteView`)
- Modify: `examples/bootstrap5/context_buttons/templates/context_buttons/ticket_detail.html` (comment of section 4 only — no translatable strings)
- Modify: `examples/bootstrap5/context_buttons/tests.py`

**Interfaces:**
- Consumes: `cv_inaccessible_actions` (Task 1), rendering from Tasks 3–4.

- [ ] **Step 1: Write the failing tests**

In `examples/bootstrap5/context_buttons/tests.py`, inside `TicketDetailViewerTest`, replace `test_custom_loop_only_lists_accessible_buttons` with:

```python
    def test_custom_loop_lists_accessible_and_disabled_buttons(self):
        # home + delete (disabled: TicketDeleteView.cv_inaccessible_actions = "disable") + manage;
        # edit_big targets update, which stays hidden
        self.assertEqual(self.rendered(self.detail(self.viewer)).count('class="cv-demo-loop-item"'), 3)

    def test_delete_shown_disabled_in_toolbar(self):
        html = self.rendered(self.detail(self.viewer))
        self.assertIn('data-cv-disabled="permission"', html)
        self.assertIn('aria-disabled="true"', html)
```

and add to `TicketCrudTest`:

```python
    def test_list_shows_disabled_delete_for_viewer(self):
        self.client.force_login(self.viewer)
        resp = self.client.get(reverse("ticket-list"))
        html = resp.content.decode().split('id="snippet-panels"')[0]
        self.assertIn('data-cv-disabled="permission"', html)
        self.assertNotIn(self.delete_url, html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/bootstrap5 && ../../.venv/bin/pytest context_buttons -q; cd ../..`
Expected: the three new/changed tests FAIL; the rest PASS.

- [ ] **Step 3: Implement**

In `examples/bootstrap5/context_buttons/views.py`, in `TicketDeleteView` add after `cv_viewset = cv_ticket`:

```python
    # a viewer (bob) sees the delete button greyed out instead of hidden; edit stays hidden (#149)
    cv_inaccessible_actions = "disable"
```

In `examples/bootstrap5/context_buttons/templates/context_buttons/ticket_detail.html` change the comment line

```django
    {# 4. a loop over the view's cv_context_actions, already filtered to the buttons the user may use #}
```

to

```django
    {# 4. a loop over the view's cv_context_actions: hidden buttons left out, disabled ones (delete for bob) included #}
```

Also update the comment in `TicketDetailView` (`views.py`) from "like every context button it is hidden for a user who may not change the ticket (log in as bob)" to:

```python
    # the header toolbar: edit_big is drawn by its own template_code; it is hidden for a user who may not change
    # the ticket (log in as bob), while delete is shown disabled (TicketDeleteView.cv_inaccessible_actions)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && ../../.venv/bin/pytest -q; cd ../..`
Expected: all PASS (the whole examples suite, incl. `test_docs_sync.py` and `test_i18n.py`).

- [ ] **Step 5: Commit**

```bash
git add examples/bootstrap5/context_buttons
git commit -m "feat(examples): context_buttons demo shows a disabled delete button (#149)"
```

---

### Task 7: Documentation and changelog

**Files:**
- Create: `docs/reference/inaccessible_actions.md`
- Modify: `docs/reference/index.md` (link), `docs/reference/settings.md`, `docs/reference/action_enabled.md`, `docs/reference/context_buttons.md`, `docs/reference/theme.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Create the reference page**

Create `docs/reference/inaccessible_actions.md`:

````markdown
# Hide or disable inaccessible actions

An action is **inaccessible** for a user when they lack the permission for its target view (`cv_has_access`) or
the action is not applicable right now (`cv_action_enabled` returns `False`). By default such actions are
**hidden**. Set the mode to `"disable"` to render them **disabled** (greyed out, not clickable) instead, so users can
see that the action exists.

The mode applies to every place an action is rendered: the context-button toolbar, the manual placement tags
(`cv_context_button`, `cv_get_context_buttons`), list row actions and card actions, including child card actions.

## Configuration

| Where | Attribute | Values |
|---|---|---|
| Django settings | `CRUD_VIEWS_INACCESSIBLE_ACTIONS` | `"hide"` (default), `"disable"` |
| `ViewSet` | `inaccessible_actions` | `None` (use the setting), `"hide"`, `"disable"` |
| `CrudView` | `cv_inaccessible_actions` | `None` (use the ViewSet), `"hide"`, `"disable"` |

The mode is resolved on the **target** view of the action — the view the button links to — not on the page the
button appears on:

```python
class PublisherDeleteView(DeleteViewPermissionRequired):
    cv_viewset = cv_publisher
    cv_inaccessible_actions = "disable"  # delete is greyed out on the list rows, the cards and the detail toolbar
```

Order: `CrudView.cv_inaccessible_actions` → `ViewSet.inaccessible_actions` → `CRUD_VIEWS_INACCESSIBLE_ACTIONS`
(`CrudView.cv_get_inaccessible_actions()` returns the result).

## What "disabled" renders

The default templates render a disabled action without a URL and without the JavaScript hooks
(`data-cv-action`, `data-cv-modal`), so it cannot be activated by mouse or keyboard:

- links: `<a class="btn … disabled" aria-disabled="true" role="button" data-cv-disabled="permission">`
- POST list actions: `<button type="button" class="btn …" disabled data-cv-disabled="permission">`, and no hidden
  POST form

`data-cv-disabled` is `"permission"` when the user lacks the permission and `"state"` when `cv_action_enabled`
returned `False`. Use it to style the two cases differently:

```css
[data-cv-disabled="state"] { opacity: .35; }
```

## Template variables

| Variable | Meaning |
|---|---|
| `cv_disabled` | `True` for a disabled action, `False` for a usable one |
| `cv_disabled_reason` | `"permission"` or `"state"` (only when disabled) |
| `cv_url` | `None` when disabled |

### `cv_context_url` and `cv_get_context_buttons`

- `{% cv_context_url %}` returns `None` for every inaccessible action, in both modes — a bare URL cannot say
  "disabled".
- `view.cv_get_context_buttons()` leaves hidden buttons out and includes disabled ones with `cv_disabled=True` and
  `cv_url=None`. A loop that builds its own `<a href>` must check `cv_disabled`.

### Custom button templates

A `ContextButton(template=...)` or `ContextButton(template_code=...)` receives the disabled data in disable mode and
must render it. Add a `cv_disabled` branch when you switch a target view to `"disable"`:

```django
{% if cv_disabled %}
    <span class="btn btn-primary disabled" aria-disabled="true">{{ cv_action_label }}</span>
{% else %}
    <a href="{{ cv_url }}" class="btn btn-primary">{{ cv_action_label }}</a>
{% endif %}
```

### Overridden tag templates

Templates you copied from `crud_views/tags/` before 0.28.0 (`list_action.html`, `card_action.html`,
`context_action.html`) still check `cv_access is True`. In disable mode `cv_access` stays `False`, so these
templates keep **hiding** the action — never a broken link. Add a `{% if cv_disabled %}` branch (see the shipped
templates) to render disabled buttons.

## System checks

| Id | Meaning |
|---|---|
| `crud_views.E104` | `CRUD_VIEWS_INACCESSIBLE_ACTIONS` is not `"hide"` or `"disable"` |
| `viewset.E207` | `cv_inaccessible_actions` is not `None`, `"hide"` or `"disable"` |

`ViewSet.inaccessible_actions` is validated when the ViewSet is defined (pydantic `ValidationError`).
````

- [ ] **Step 2: Link and cross-reference**

In `docs/reference/index.md`, directly after the line `- [Conditionally disabling an action](action_enabled.md) — …` add:

```markdown
- [Hide or disable inaccessible actions](inaccessible_actions.md) — render actions the user may not use greyed out instead of hidden
```

In `docs/reference/action_enabled.md` replace

```markdown
- The action's button is **hidden entirely** (not greyed out) in list actions, context actions,
  and card actions.
```

with

```markdown
- The action's button is **hidden** in list actions, context actions and card actions — or rendered
  **disabled** when the target view resolves to `"disable"` (see
  [Hide or disable inaccessible actions](inaccessible_actions.md)).
```

In `docs/reference/context_buttons.md` replace the admonition body under `!!! note "`None` means hidden"` with:

```markdown
    Because `cv_context_url` returns `None` for both "no access" and "action disabled" — also when the target view
    renders inaccessible actions disabled — gating your markup with `{% if url %}` makes the link disappear
    entirely. `cv_context_button` and the `{% cv_context_actions %}` container hide inaccessible buttons, or render
    them disabled in disable mode (see [Hide or disable inaccessible actions](inaccessible_actions.md)).
```

and change the sentence under `### `cv_context_button` — render the full button`
"It renders **nothing** when the user lacks access or the action is disabled:" to
"It renders **nothing** when the user lacks access or the action is disabled — or a disabled button when the
target view uses `cv_inaccessible_actions = "disable"`:".

In `docs/reference/settings.md`, add a section after `## List Actions`:

```markdown
## Inaccessible actions

| Setting | Default | Description |
|---|---|---|
| `CRUD_VIEWS_INACCESSIBLE_ACTIONS` | `"hide"` | `"hide"` or `"disable"`: how actions the user may not use are rendered. Overridable per ViewSet (`inaccessible_actions`) and per view (`cv_inaccessible_actions`). See [Hide or disable inaccessible actions](inaccessible_actions.md). Invalid values raise `crud_views.E104`. |
```

Check the table format of the neighbouring sections in `settings.md` first and match it (if they use a different column layout, use theirs).

In `docs/reference/theme.md`, at the end of the file add:

```markdown
## Disabled actions in overridden templates

The shipped `tags/context_action.html`, `tags/list_action.html` and `tags/card_action.html` start with a
`{% if cv_disabled %}` branch. If you override one of them, keep that branch to support
`CRUD_VIEWS_INACCESSIBLE_ACTIONS = "disable"`; without it the action stays hidden. See
[Hide or disable inaccessible actions](inaccessible_actions.md).
```

- [ ] **Step 3: Changelog**

At the top of `CHANGELOG.md`, directly under `# Django CRUD Views - Changelog`, add:

```markdown
## Unreleased

### Added

- Inaccessible actions can be rendered **disabled** instead of hidden: setting `CRUD_VIEWS_INACCESSIBLE_ACTIONS`
  (`"hide"` default, `"disable"`), overridable per ViewSet (`inaccessible_actions`) and per CrudView
  (`cv_inaccessible_actions`, resolved on the action's target view via `cv_get_inaccessible_actions()`). Applies to
  context buttons, list actions and card actions. Templates get `cv_disabled` and `cv_disabled_reason`
  (`"permission"` | `"state"`); disabled buttons carry `aria-disabled` / `disabled` and `data-cv-disabled`. New
  system checks `crud_views.E104` and `viewset.E207` (#149).

### Changed

- Child card actions (`CardAction(child_name=...)`) now check the child view's permission like
  `ChildContextButton`. Users without it no longer see the button (previously it rendered and the target answered
  with 403). Guardian child list views still grant access at render time, so their child card actions keep
  rendering, as with `ChildContextButton` (#149).
- `CrudView.cv_get_context_buttons()` includes disabled entries (`cv_disabled=True`, `cv_url=None`) when the target
  view resolves to `"disable"` (#149).
```

- [ ] **Step 4: Build the docs**

Run: `.venv/bin/mkdocs build --strict -q`
Expected: exits 0, no warnings about broken links to `inaccessible_actions.md`.

- [ ] **Step 5: Lint, format, full test run**

Run: `.venv/bin/ruff format src tests examples && .venv/bin/ruff check --fix src tests examples && .venv/bin/pytest tests -q && (cd examples/bootstrap5 && ../../.venv/bin/pytest -q)`
Expected: ruff reports no remaining errors; both test suites PASS.

- [ ] **Step 6: Commit**

```bash
git add docs CHANGELOG.md
git add -u
git commit -m "docs: hide or disable inaccessible actions, changelog (#149)"
```

---

## After the plan

- Open a PR for `feature/inaccessible-actions-149`, wait for CI incl. codecov/patch (query the check-runs API, `gh pr checks` omits codecov). Do **not** merge unless the user asks.
- Release as 0.28.0 (behaviour change) only when the user asks; then update the `django-crud-views` skill in the skills monorepo.
