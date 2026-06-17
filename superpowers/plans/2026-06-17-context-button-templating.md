# Context Button Templating & Manual Placement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let context buttons carry their own render template and be placed by hand anywhere in a template (by key, in a custom loop, and gated by a permission filter), so the same logical action can render with a different shape per view.

**Architecture:** Add `template` / `template_code` to the base `ContextButton` (inherited by all subclasses), defaulting to a new `crud_views_settings.context_button_template`. Both branches of `CrudView.cv_get_context` inject a template so every rendered action carries one. Add three template-layer entry points — `{% cv_context_button key %}`, `{% cv_render_context_button ctx %}` + `view.cv_get_context_buttons`, and the `view|cv_context_has_permission:"key"` filter — that share a single render helper using the existing `CrudView.render_snippet`. The default `{% cv_context_actions %}` container is left behaviorally unchanged.

**Tech Stack:** Python, Django (4.2/5.2/6.0), Pydantic (settings + button models), pytest. Two themes share templates under the `crud_views/` template namespace (`crud_views_settings.theme_path == "crud_views"`).

## Global Constraints

- Line length 120, double quotes, ruff format/check (per CLAUDE.md).
- All `CrudView`/button additions keep the `cv_` prefix for public attributes and template entry points.
- Backwards compatibility is mandatory: existing viewsets, views, the `{% cv_context_actions %}` container, and `{% cv_context_action %}` rendering must behave identically for existing keys.
- Two render contracts are deliberate: the default container renders no-access buttons as *disabled*; the new manual API (`cv_context_button`, loop, filter) *hides* on no-access. Do not change the container's contract.
- View-level `ContextButton` instances in `cv_context_actions` (issue #27) are explicitly out of scope.
- Tests live in `tests/test1/`; run from the `tests/` directory.

---

### Task 1: `ContextButton` templating foundation

Add the template fields, the settings default, and inject a template in both branches of `cv_get_context` so the existing container keeps working with the default and newly supports `template_code`.

**Files:**
- Modify: `src/crud_views/lib/settings.py` (add `context_button_template` property)
- Modify: `src/crud_views/lib/view/buttons.py` (fields + `_inject_template`, wire into `ContextButton`, `ParentContextButton`, `ChildContextButton`, `FilterContextButton`)
- Modify: `src/crud_views/lib/view/base.py:305-345` (`cv_get_context` view-key branch injects `cv_template`)
- Modify: `src/crud_views/templatetags/crud_views.py:65-71` (`cv_context_action` honors `cv_template_code`, falls back to settings)
- Test: `tests/test1/test_context_button_template.py` (new)

**Interfaces:**
- Produces:
  - `crud_views_settings.context_button_template -> str` (default `"crud_views/tags/context_action.html"`, overridable via `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE`)
  - `ContextButton.template: str | None`, `ContextButton.template_code: str | None`
  - `ContextButton._inject_template(self, data: dict) -> None` — sets `data["cv_template_code"]` if `template_code`, else `data["cv_template"]` from `template` or the settings default
  - Every dict returned by `cv_get_context` for a renderable key now carries `cv_template` or `cv_template_code`

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_context_button_template.py`:

```python
"""ContextButton template / template_code fields and the settings default."""

import pytest

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.buttons import ContextButton, FilterContextButton


def test_settings_default_template():
    assert crud_views_settings.context_button_template == "crud_views/tags/context_action.html"


def test_settings_template_override(monkeypatch):
    from django.conf import settings as dj_settings

    monkeypatch.setattr(dj_settings, "CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE", "x/y.html", raising=False)
    # property reads Django settings live
    assert crud_views_settings.context_button_template == "x/y.html"


def test_inject_template_default():
    data = {}
    ContextButton(key="edit", key_target="update")._inject_template(data)
    assert data == {"cv_template": "crud_views/tags/context_action.html"}


def test_inject_template_file():
    data = {}
    ContextButton(key="edit", key_target="update", template="app/edit.html")._inject_template(data)
    assert data == {"cv_template": "app/edit.html"}


def test_inject_template_code_wins():
    data = {}
    ContextButton(
        key="edit", key_target="update", template="app/edit.html", template_code="<a>{{ cv_url }}</a>"
    )._inject_template(data)
    assert data == {"cv_template_code": "<a>{{ cv_url }}</a>"}


def test_filter_button_default_template():
    assert FilterContextButton().template == "crud_views/tags/context_action_filter.html"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_context_button_template.py -v`
Expected: FAIL — `context_button_template` attribute missing / `ContextButton` has no `template` field.

- [ ] **Step 3: Add the settings property**

In `src/crud_views/lib/settings.py`, next to the existing `theme_path` property (around line 84), add:

```python
    @property
    def context_button_template(self) -> str:
        return from_settings(
            "CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE",
            default=f"{self.theme_path}/tags/context_action.html",
        )
```

- [ ] **Step 4: Add fields + `_inject_template` to `ContextButton`**

In `src/crud_views/lib/view/buttons.py`, add the import at the top:

```python
from pydantic import BaseModel, Field
```

Extend the base `ContextButton` fields (after `label_template_code`):

```python
    template: str | None = None
    template_code: str | None = None
```

Add the helper method to `ContextButton` (after `render_label`):

```python
    def _inject_template(self, data: dict) -> None:
        if self.template_code:
            data["cv_template_code"] = self.template_code
        elif self.template:
            data["cv_template"] = self.template
        else:
            data["cv_template"] = crud_views_settings.context_button_template
```

Call `self._inject_template(data)` at the end of `get_context` in `ContextButton`, `ParentContextButton`, and `ChildContextButton` — immediately before `return data` (for `ContextButton`, after the label block; place it before `return data`).

- [ ] **Step 5: Update `FilterContextButton`**

In `FilterContextButton`, set the field default and drop the hardcoded `cv_template` line. Replace the class body so it reads:

```python
class FilterContextButton(ContextButton):
    """
    A context button that
    """

    key: str = "filter"
    template: str | None = Field(
        default_factory=lambda: f"{crud_views_settings.theme_path}/tags/context_action_filter.html"
    )

    def get_context(self, context: ViewContext) -> dict:
        from ..views import ListViewTableFilterMixin

        dict_kwargs = dict(cv_access=False)

        # if view has no filter, no button is shown
        if not isinstance(context.view, ListViewTableFilterMixin):
            return dict_kwargs

        # pinned filter is always visible -> no toggle button
        if getattr(context.view, "cv_filter_pinned", False):
            return dict_kwargs

        list_url = context.view.cv_get_url(key=context.view.cv_key)

        data = dict()
        data["cv_action_label"] = "Filter"
        data["cv_icon_action"] = crud_views_settings.filter_icon
        data["cv_url"] = list_url
        self._inject_template(data)

        return data
```

- [ ] **Step 6: Inject `cv_template` in the view-key branch of `cv_get_context`**

In `src/crud_views/lib/view/base.py`, in `cv_get_context` view-key branch, add `cv_template` to `dict_kwargs` (the dict around line 321):

```python
        dict_kwargs = dict(
            cv_access=False,
            cv_oid=self.cv_get_oid(key=key, obj=obj),
            cv_url=self.cv_get_url(key=key, obj=obj),
            cv_is_active=self.cv_viewset.get_router_name(key) == context.router_name,
            cv_template=crud_views_settings.context_button_template,
        )
```

Confirm `crud_views_settings` is imported in `base.py`; if not, add `from ..settings import crud_views_settings`.

- [ ] **Step 7: Update `cv_context_action` to honor `template_code` and use the settings fallback**

In `src/crud_views/templatetags/crud_views.py`, replace the body of `cv_context_action` (lines 65-71):

```python
@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_action(context, key, obj=None):
    obj = None if not obj else obj  # fix empty string from template
    ctx = cv_get_context(context=context, key=key, obj=obj)
    if ctx.get("cv_template_code"):
        view = cv_get_view(context)
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    template = ctx.get("cv_template") or crud_views_settings.context_button_template
    return render_to_string(template, context=ctx, request=context["request"])
```

(The file-template path keeps passing `request`, preserving current behavior; the settings fallback covers no-button dicts such as the inactive `FilterContextButton`.)

- [ ] **Step 8: Run the new test + regression suite**

Run: `cd tests && pytest test1/test_context_button_template.py test1/test_filter.py test1/test_filter_pinned.py test1/test_context_actions_isolation.py -v`
Expected: PASS (new file passes; filter/container regressions still green).

- [ ] **Step 9: Format, lint, commit**

```bash
task format && task check
git add src/crud_views/lib/settings.py src/crud_views/lib/view/buttons.py src/crud_views/lib/view/base.py src/crud_views/templatetags/crud_views.py tests/test1/test_context_button_template.py
git commit -m "feat(buttons): ContextButton template/template_code with settings default"
```

---

### Task 2: `cv_context_button` by-key placement tag

A tag that renders one button by key anywhere, hiding it when the user has no access or the action is disabled.

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (add `_render_context_button` helper + `cv_context_button` tag)
- Test: `tests/test1/test_context_button_tag.py` (new)

**Interfaces:**
- Consumes: `cv_get_context` dicts carrying `cv_template`/`cv_template_code`, `cv_access`, `cv_action_enabled` (Task 1); `CrudView.render_snippet` (existing).
- Produces:
  - `_render_context_button(view, ctx) -> str` — returns `""` when `ctx` is falsy / `cv_action_enabled is False` / `cv_access is not True`; else renders `template_code` or `template` (falling back to settings default) via `render_snippet`.
  - Template tag `{% cv_context_button key obj %}`.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_context_button_tag.py`:

```python
"""{% cv_context_button %} renders one button by key, hiding on no-access."""

import pytest
from django.template import Context, Template
from django.urls import reverse


def _render(view, request, snippet):
    tpl = Template("{% load crud_views %}" + snippet)
    return tpl.render(Context({"view": view, "request": request})).strip()


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


@pytest.mark.django_db
def test_button_rendered_when_access(client_user_author_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_change, cv_author, author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'update' %}")
    assert 'cv-key="update"' in html


@pytest.mark.django_db
def test_button_hidden_without_access(client_user_author_view, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'update' %}")
    assert html == ""


@pytest.mark.django_db
def test_unknown_key_is_empty(client_user_author_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_change, cv_author, author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'does_not_exist' %}")
    assert html == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_context_button_tag.py -v`
Expected: FAIL — `'cv_context_button'` is not a registered tag.

- [ ] **Step 3: Add helper + tag**

In `src/crud_views/templatetags/crud_views.py`, add after `cv_get_context` (near line 32) the shared helper:

```python
def _render_context_button(view, ctx) -> str:
    if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
        return ""
    if ctx.get("cv_template_code"):
        return view.render_snippet(ctx, template_code=ctx["cv_template_code"])
    template = ctx.get("cv_template") or crud_views_settings.context_button_template
    return view.render_snippet(ctx, template=template)
```

Add the tag after `cv_context_action`:

```python
@register.simple_tag(takes_context=True)
@ignore_exception(ViewSetKeyFoundError, default_value="")
def cv_context_button(context, key, obj=None):
    obj = None if not obj else obj  # fix empty string from template
    ctx = cv_get_context(context=context, key=key, obj=obj)
    view = cv_get_view(context)
    return _render_context_button(view, ctx)
```

(`render_snippet` already returns a `mark_safe` string, so the tag output is not double-escaped.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_context_button_tag.py -v`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
task format && task check
git add src/crud_views/templatetags/crud_views.py tests/test1/test_context_button_tag.py
git commit -m "feat(buttons): add {% cv_context_button %} manual placement tag"
```

---

### Task 3: Custom-loop API — `cv_get_context_buttons` + `cv_render_context_button`

Expose the resolved, access-filtered button list for custom loops, plus a tag to render a pre-resolved entry without re-resolving.

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (add `cv_get_context_buttons` method, near `cv_get_context_button` ~line 289)
- Modify: `src/crud_views/templatetags/crud_views.py` (add `cv_render_context_button` tag)
- Test: `tests/test1/test_context_button_loop.py` (new)

**Interfaces:**
- Consumes: `_render_context_button` (Task 2); `cv_get_context` (Task 1).
- Produces:
  - `CrudView.cv_get_context_buttons(self, keys: list[str] | None = None, obj=None) -> list[dict]` — resolves each key (default `self.cv_context_actions`, in order; object defaults to `getattr(self, "object", None)`), filters out entries failing the hide contract, returns the resolved dicts.
  - Template tag `{% cv_render_context_button ctx %}`.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_context_button_loop.py`:

```python
"""cv_get_context_buttons (access-filtered list) + {% cv_render_context_button %}."""

import pytest
from django.template import Context, Template
from django.urls import reverse


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


@pytest.mark.django_db
def test_list_filters_inaccessible(client_user_author_view, cv_author, author_douglas_adams):
    # view-only user: 'update'/'delete' must be filtered out of the list
    view, _ = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    keys = [b.get("cv_key") for b in view.cv_get_context_buttons()]
    assert "update" not in keys
    assert "delete" not in keys


@pytest.mark.django_db
def test_explicit_keys_order(client_user_author_change, cv_author, author_douglas_adams):
    view, _ = _detail_view(client_user_author_change, cv_author, author_douglas_adams)
    buttons = view.cv_get_context_buttons(keys=["update", "detail"])
    assert [b.get("cv_key") for b in buttons] == ["update", "detail"]


@pytest.mark.django_db
def test_render_tag_renders_entry(client_user_author_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_change, cv_author, author_douglas_adams)
    tpl = Template(
        "{% load crud_views %}"
        "{% for ctx in view.cv_get_context_buttons %}"
        "<span>{% cv_render_context_button ctx %}</span>{% endfor %}"
    )
    html = tpl.render(Context({"view": view, "request": request}))
    assert 'cv-key="update"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_context_button_loop.py -v`
Expected: FAIL — `CrudView` has no `cv_get_context_buttons` / `cv_render_context_button` not registered.

- [ ] **Step 3: Add the accessor method**

In `src/crud_views/lib/view/base.py`, after `cv_get_context_button` (around line 294), add:

```python
    def cv_get_context_buttons(self, keys: list[str] | None = None, obj=None) -> list[dict]:
        """
        Resolved, access-filtered context-button data for a custom template loop.
        keys defaults to this view's cv_context_actions; obj defaults to the view's object.
        """
        keys = keys if keys is not None else (self.cv_context_actions or [])
        if obj is None:
            obj = getattr(self, "object", None)
        result: list[dict] = []
        for key in keys:
            ctx = self.cv_get_context(key=key, obj=obj, user=self.request.user, request=self.request)
            if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
                continue
            result.append(ctx)
        return result
```

- [ ] **Step 4: Add the render tag**

In `src/crud_views/templatetags/crud_views.py`, after `cv_context_button`:

```python
@register.simple_tag(takes_context=True)
def cv_render_context_button(context, ctx) -> str:
    view = cv_get_view(context)
    return _render_context_button(view, ctx)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd tests && pytest test1/test_context_button_loop.py -v`
Expected: PASS.

- [ ] **Step 6: Format, lint, commit**

```bash
task format && task check
git add src/crud_views/lib/view/base.py src/crud_views/templatetags/crud_views.py tests/test1/test_context_button_loop.py
git commit -m "feat(buttons): cv_get_context_buttons accessor + {% cv_render_context_button %}"
```

---

### Task 4: `cv_context_has_permission` filter

A filter usable directly in `{% if %}` to gate surrounding markup by access to a key.

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (add `cv_context_has_permission` filter)
- Test: `tests/test1/test_context_button_permission_filter.py` (new)

**Interfaces:**
- Consumes: `ViewSet.get_view_class(key)`, `CrudView.cv_has_access(user, obj)` (existing).
- Produces: filter `cv_context_has_permission(view, key) -> bool` — `view.cv_viewset.get_view_class(key).cv_has_access(view.request.user, getattr(view, "object", None))`; returns `False` on unknown key.

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_context_button_permission_filter.py`:

```python
"""view|cv_context_has_permission:'key' for {% if %} gating."""

import pytest
from django.template import Context, Template
from django.urls import reverse


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


def _render(view, request, key):
    tpl = Template(
        "{% load crud_views %}{% if view|cv_context_has_permission:'" + key + "' %}YES{% else %}NO{% endif %}"
    )
    return tpl.render(Context({"view": view, "request": request})).strip()


@pytest.mark.django_db
def test_true_for_permitted(client_user_author_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_change, cv_author, author_douglas_adams)
    assert _render(view, request, "update") == "YES"


@pytest.mark.django_db
def test_false_for_forbidden(client_user_author_view, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    assert _render(view, request, "update") == "NO"


@pytest.mark.django_db
def test_false_for_unknown_key(client_user_author_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_change, cv_author, author_douglas_adams)
    assert _render(view, request, "nope") == "NO"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_context_button_permission_filter.py -v`
Expected: FAIL — `cv_context_has_permission` is not a registered filter.

- [ ] **Step 3: Add the filter**

In `src/crud_views/templatetags/crud_views.py`, next to the other `@register.filter` definitions (around line 180):

```python
@register.filter
def cv_context_has_permission(view, key) -> bool:
    try:
        cls = view.cv_viewset.get_view_class(key)
    except Exception:
        return False
    return bool(cls.cv_has_access(view.request.user, getattr(view, "object", None)))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tests && pytest test1/test_context_button_permission_filter.py -v`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
task format && task check
git add src/crud_views/templatetags/crud_views.py tests/test1/test_context_button_permission_filter.py
git commit -m "feat(buttons): add view|cv_context_has_permission filter"
```

---

### Task 5: Documentation

Document the new fields, tags, filter, and the two render contracts in the reference docs.

**Files:**
- Modify: the context-button / template-tag reference page under `docs/` (locate with the grep in Step 1; likely `docs/reference/` or the context-actions page)

- [ ] **Step 1: Locate the docs page**

Run: `cd /home/alex/projects/alex/django-crud-views && grep -rln "cv_context_action\|context button\|context_buttons" docs/`
Expected: one or more reference pages; pick the context-actions / buttons reference page.

- [ ] **Step 2: Add a "Custom button rendering & placement" section**

Document, with copy-paste examples:
- `ContextButton(template=..., template_code=...)` and the `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` default.
- Defining a variant button in the viewset (e.g. `edit_detail`) and trimming `cv_context_actions`.
- `{% cv_context_button "edit_detail" %}` (hides on no-access).
- The custom loop: `{% for ctx in view.cv_get_context_buttons %}{% cv_render_context_button ctx %}{% endfor %}`.
- `{% if view|cv_context_has_permission:"edit_detail" %}…{% endif %}`.
- The two render contracts table (container = disabled, manual API = hidden).

Example block to include:

```django
{% load crud_views %}
{% if view|cv_context_has_permission:"edit_detail" %}
  <div class="toolbar">
    {% cv_context_button "edit_detail" %}
  </div>
{% endif %}

{% for ctx in view.cv_get_context_buttons %}
  <span class="wrap">{% cv_render_context_button ctx %}</span>
{% endfor %}
```

- [ ] **Step 3: Build docs to verify no broken references**

Run: `task docs` (Ctrl-C after it serves cleanly) or `uv run mkdocs build`
Expected: build succeeds, no warnings about the edited page.

- [ ] **Step 4: Commit**

```bash
git add docs/
git commit -m "docs(buttons): document context button templating and manual placement"
```

---

### Task 6: Full suite + final verification

- [ ] **Step 1: Run the complete test suite**

Run: `cd tests && pytest -q`
Expected: all pass (existing count + the new tests across Tasks 1-4), no new failures.

- [ ] **Step 2: Lint/format clean**

Run: `task format && task check`
Expected: no changes / no errors.

- [ ] **Step 3: Review the branch diff**

Run: `git log --oneline main..HEAD && git diff --stat main..HEAD`
Expected: commits for Tasks 1-5, touching `settings.py`, `buttons.py`, `base.py`, `crud_views.py` (templatetags), four new test files, and docs.
