# Pinned Filter (`cv_filter_pinned`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in `cv_filter_pinned` mode so list/card filters render always-open with the toggle button hidden, defaulting off (current collapsed behavior unchanged).

**Architecture:** A new `CRUD_VIEWS_FILTER_PINNED` setting feeds a `cv_filter_pinned` class attribute on `ListViewTableFilterMixin` (covering both `ListView` and `CardListView`). The mixin exposes the flag + forces the filter expanded in context; `FilterContextButton` reuses its existing no-button path to hide the toggle when pinned; the bootstrap5 `list_filter.html` drops the collapse wrapper when pinned. Plain theme needs no template change (already always-visible).

**Tech Stack:** Python, Django, django-filter, Pydantic settings, django-crispy-forms templates, pytest + pytest-django, lxml (HTML assertions).

**Spec:** `superpowers/specs/2026-06-17-filter-pinned-design.md`

> **Testing note — import-time snapshot:** `cv_filter_pinned = crud_views_settings.filter_pinned` is evaluated at class-definition time (same pattern as `cv_filter_persistence`). Monkeypatching `crud_views_settings.filter_pinned` at runtime does **not** retroactively change already-imported view classes. So behavior tests set the flag with `monkeypatch.setattr(SomeView, "cv_filter_pinned", True)` (this models both the per-view override and a setting-driven default, since both surface as the class attribute). The setting→default *wiring* is verified separately by asserting the mixin's default equals the setting value.

> **Test infrastructure already present:** `tests/test1/app/views.py` has filter-enabled views `PublisherListView` (a `ListView`, URL `/publisher/`) and `PublisherOrderCardListView` (a `CardListView`, URL `/publisher_order/card/`). `tests/test1/test_card_order.py` shows the fixture/HTML-assertion patterns (`client_publisher_order`, `publishers`, `lxml.html` + `cssselect`, `user_viewset_permission`). Run tests from the `tests/` dir: `cd tests && pytest ...`. A pre-commit hook runs `ruff format` + `ruff check`.

---

### Task 1: Setting + mixin flag plumbing

**Files:**
- Modify: `src/crud_views/lib/settings.py` (after the `filter_persistence` line, ~33)
- Modify: `src/crud_views/lib/views/mixins.py` (`ListViewTableFilterMixin`: attribute ~239, `get_context_data` ~248–253)
- Test: `tests/test1/test_filter_pinned.py` (new)

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_filter_pinned.py`:

```python
import pytest
from django.contrib.auth.models import User
from django.test.client import Client

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_publisher_order():
    from tests.test1.app.views import cv_publisher_order as ret

    return ret


@pytest.fixture
def client_publisher_order(client, cv_publisher_order) -> Client:
    user = User.objects.create_user(username="user_pinned_card", password="password")
    user_viewset_permission(user, cv_publisher_order, "view")
    client.force_login(user)
    return client


@pytest.fixture
def publishers(db):
    from tests.test1.app.models import Publisher

    return [
        Publisher.objects.create(name="Charlie"),
        Publisher.objects.create(name="Alpha"),
        Publisher.objects.create(name="Bravo"),
    ]


def test_filter_pinned_default_comes_from_setting():
    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.views import ListViewTableFilterMixin

    # default attribute is sourced from the setting (which defaults False)
    assert ListViewTableFilterMixin.cv_filter_pinned == crud_views_settings.filter_pinned
    assert crud_views_settings.filter_pinned is False


@pytest.mark.django_db
def test_pinned_view_forces_filter_expanded_context(client_publisher_order, publishers, monkeypatch):
    from tests.test1.app.views import PublisherOrderCardListView

    # not pinned: expanded comes from session (default False)
    response = client_publisher_order.get("/publisher_order/card/")
    assert response.status_code == 200
    assert response.context["cv_filter_pinned"] is False
    assert response.context["cv_filter_expanded"] is False

    # pinned: forced expanded
    monkeypatch.setattr(PublisherOrderCardListView, "cv_filter_pinned", True)
    response = client_publisher_order.get("/publisher_order/card/")
    assert response.status_code == 200
    assert response.context["cv_filter_pinned"] is True
    assert response.context["cv_filter_expanded"] is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tests && pytest test1/test_filter_pinned.py -v`
Expected: FAIL — `AttributeError`/`KeyError` on `cv_filter_pinned` (attribute and context key don't exist yet).

- [ ] **Step 3: Add the setting**

In `src/crud_views/lib/settings.py`, immediately after the existing line
`filter_persistence: bool = from_settings("CRUD_VIEWS_FILTER_PERSISTENCE", default=True)`
add:

```python
    filter_pinned: bool = from_settings("CRUD_VIEWS_FILTER_PINNED", default=False)
```

- [ ] **Step 4: Add the mixin attribute and update `get_context_data`**

In `src/crud_views/lib/views/mixins.py`, in `ListViewTableFilterMixin`, after the line
`cv_session_key_querystring: str = "filter_query_string"` add:

```python
    cv_filter_pinned: bool = crud_views_settings.filter_pinned
```

Replace the existing `get_context_data`:

```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filter_expanded = SessionData.from_view(self).get("filter_expanded", False)
        context["cv_filter_expanded"] = filter_expanded
        return context
```

with:

```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.cv_filter_pinned:
            # pinned filter is always shown; the toggle/session-expanded state is moot
            filter_expanded = True
        else:
            filter_expanded = SessionData.from_view(self).get("filter_expanded", False)
        context["cv_filter_pinned"] = self.cv_filter_pinned
        context["cv_filter_expanded"] = filter_expanded
        return context
```

(`crud_views_settings` is already imported at the top of `mixins.py`.)

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd tests && pytest test1/test_filter_pinned.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/settings.py src/crud_views/lib/views/mixins.py tests/test1/test_filter_pinned.py
git commit -m "feat(filter): add cv_filter_pinned flag + CRUD_VIEWS_FILTER_PINNED setting"
```

---

### Task 2: Hide the filter toggle button when pinned

**Files:**
- Modify: `src/crud_views/lib/view/buttons.py` (`FilterContextButton.get_context`, ~152–174)
- Test: `tests/test1/test_filter_pinned.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_filter_pinned.py`:

```python
@pytest.mark.django_db
def test_pinned_hides_filter_toggle_button(client_publisher_order, publishers, monkeypatch):
    from lxml import html

    from tests.test1.app.views import PublisherOrderCardListView

    # not pinned: toggle button present
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert doc.cssselect("#cv-filter-toggle"), "toggle should be present when not pinned"

    # pinned: toggle button hidden
    monkeypatch.setattr(PublisherOrderCardListView, "cv_filter_pinned", True)
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert not doc.cssselect("#cv-filter-toggle"), "toggle should be hidden when pinned"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tests && pytest test1/test_filter_pinned.py::test_pinned_hides_filter_toggle_button -v`
Expected: FAIL — the `#cv-filter-toggle` button still renders when pinned.

- [ ] **Step 3: Hide the button when pinned**

In `src/crud_views/lib/view/buttons.py`, in `FilterContextButton.get_context`, find:

```python
        # if view has no filter, no button is shown
        if not isinstance(context.view, ListViewTableFilterMixin):
            return dict_kwargs
```

and add immediately after it:

```python
        # pinned filter is always visible -> no toggle button
        if getattr(context.view, "cv_filter_pinned", False):
            return dict_kwargs
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_filter_pinned.py::test_pinned_hides_filter_toggle_button -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/buttons.py tests/test1/test_filter_pinned.py
git commit -m "feat(filter): hide the filter toggle button when cv_filter_pinned"
```

---

### Task 3: bootstrap5 template — drop the collapse wrapper when pinned

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/list_filter.html`
- Create: `src/crud_views/templates/crud_views/tags/list_filter.inner.html`
- Test: `tests/test1/test_filter_pinned.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_filter_pinned.py`:

```python
@pytest.mark.django_db
def test_pinned_renders_filter_without_collapse(client_publisher_order, publishers, monkeypatch):
    from lxml import html

    from tests.test1.app.views import PublisherOrderCardListView

    # not pinned: collapse wrapper present, filter form present
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert doc.cssselect("#filter-collapse"), "collapse wrapper expected when not pinned"
    assert doc.cssselect("form#filter-form"), "filter form expected"

    # pinned: no collapse wrapper, but filter form still rendered
    monkeypatch.setattr(PublisherOrderCardListView, "cv_filter_pinned", True)
    response = client_publisher_order.get("/publisher_order/card/")
    doc = html.fromstring(response.content)
    assert not doc.cssselect("#filter-collapse"), "collapse wrapper must be gone when pinned"
    assert doc.cssselect("form#filter-form"), "filter form must still render when pinned"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tests && pytest test1/test_filter_pinned.py::test_pinned_renders_filter_without_collapse -v`
Expected: FAIL — `#filter-collapse` is still present when pinned (template unchanged).

- [ ] **Step 3: Extract the inner filter card to a partial**

Create `src/crud_views/templates/crud_views/tags/list_filter.inner.html` with exactly:

```django
{% load crispy_forms_tags %}
{% load crud_views %}

<div class="card-header">
    {% block cv_filter_header_icon %}
        {% cv_filter_icon %}
    {% endblock cv_filter_header_icon %}
    {% block cv_filter_header %}
        {% cv_filter_header %}
    {% endblock cv_filter_header %}
</div>
<div class="card-body">
    {% block cv_content_filter %}
        <form id="filter-form" method="get">
            {% crispy filter.form filter.form.helper %}
        </form>
    {% endblock cv_content_filter %}
</div>
```

- [ ] **Step 4: Branch the wrapper on `cv_filter_pinned`**

Replace the entire contents of `src/crud_views/templates/crud_views/tags/list_filter.html` with:

```django
{% load crispy_forms_tags %}
{% load static %}
{% load crud_views %}

{% if cv_filter_pinned %}
    <div class="card" id="filter-pinned">
        {% include "crud_views/tags/list_filter.inner.html" %}
    </div>
    <br>
{% else %}
    <div class="collapse{% if cv_filter_expanded %} show{% endif %}" id="filter-collapse">
        <div class="card">
            {% include "crud_views/tags/list_filter.inner.html" %}
        </div>
        <br>
    </div>
{% endif %}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_filter_pinned.py::test_pinned_renders_filter_without_collapse -v`
Expected: PASS.

- [ ] **Step 6: Run the full filter-pinned file + a regression sweep of filter/card tests**

Run: `cd tests && pytest test1/test_filter_pinned.py test1/test_card_order.py test1/test_basic.py -v`
Expected: all PASS (the non-pinned branch reproduces the original markup, so `test_card_order.py`'s `form#filter-form` assertions still hold).

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/templates/crud_views/tags/list_filter.html src/crud_views/templates/crud_views/tags/list_filter.inner.html tests/test1/test_filter_pinned.py
git commit -m "feat(filter): render pinned filter without the collapse wrapper (bootstrap5)"
```

---

### Task 4: ListView parity + session field-value persistence under pinning

**Files:**
- Test: `tests/test1/test_filter_pinned.py` (append)

- [ ] **Step 1: Write the tests**

Append to `tests/test1/test_filter_pinned.py`:

```python
@pytest.fixture
def client_publisher_view(client):
    from tests.test1.app.views import cv_publisher

    user = User.objects.create_user(username="user_pinned_list", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_pinned_listview_parity(client_publisher_view, monkeypatch):
    from lxml import html

    from tests.test1.app.views import PublisherListView

    monkeypatch.setattr(PublisherListView, "cv_filter_pinned", True)
    response = client_publisher_view.get("/publisher/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    assert not doc.cssselect("#cv-filter-toggle"), "toggle hidden for pinned ListView"
    assert not doc.cssselect("#filter-collapse"), "no collapse wrapper for pinned ListView"
    assert doc.cssselect("form#filter-form"), "filter form rendered for pinned ListView"


@pytest.mark.django_db
def test_pinned_still_persists_filter_values_to_session(client_publisher_order, publishers, monkeypatch):
    from tests.test1.app.views import PublisherOrderCardListView

    monkeypatch.setattr(PublisherOrderCardListView, "cv_filter_pinned", True)

    # submit a filter value -> stored in session (cv_filter_persistence defaults True)
    response = client_publisher_order.get("/publisher_order/card/?name=Alp")
    assert response.status_code == 200

    # a bare GET restores the stored query string via redirect
    response = client_publisher_order.get("/publisher_order/card/", follow=False)
    assert response.status_code == 302
    assert "name=Alp" in response.url
```

- [ ] **Step 2: Run the tests**

Run: `cd tests && pytest test1/test_filter_pinned.py -v`
Expected: PASS (all tests in the file). No implementation changes are needed — these assert that Tasks 1–3 already deliver ListView parity (same mixin/button/template) and that pinning does not disturb the field-value session persistence in `ListViewTableFilterMixin.get()`.

  If `test_pinned_listview_parity` fails on the fixture/URL, confirm the `cv_publisher` viewset name and that `PublisherListView` is registered at `/publisher/` (see `tests/test1/app/urls.py` and `tests/test1/app/views.py`); fix the fixture/URL to match, not the source.

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_filter_pinned.py
git commit -m "test(filter): cover pinned ListView parity and session persistence"
```

---

### Task 5: Documentation

**Files:**
- Modify: `docs/reference/list_view.md`
- Modify: `docs/reference/card-list-view.md`
- Modify: `docs/reference/settings.md`

- [ ] **Step 1: Document on the ListView filtering page**

In `docs/reference/list_view.md`, locate the "## Filtering with django-filter" section. After its existing content (the filter example block), add:

```markdown
### Always-visible (pinned) filter

By default the filter is collapsed and opened via the filter toggle button. Set
`cv_filter_pinned = True` on a filtered view to render the filter **always open** and
hide the toggle button entirely:

\`\`\`python
class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    filterset_class = AuthorFilter
    cv_filter_pinned = True
\`\`\`

The default comes from the `CRUD_VIEWS_FILTER_PINNED` setting (default `False`). Filter
field values are still persisted to the session when `cv_filter_persistence` is enabled;
only the (now irrelevant) expanded/collapsed state is dropped. Applies equally to
[CardListView](card-list-view.md).
```

(Replace the `\`\`\`` markers with real triple-backticks when writing the file.)

- [ ] **Step 2: Note it on the CardListView page**

In `docs/reference/card-list-view.md`, add a short subsection near the filtering content (or at the end if there is none):

```markdown
### Pinned filter

`CardListView` shares `ListViewTableFilterMixin` with `ListView`, so `cv_filter_pinned = True`
works the same way: the filter renders always-open and the toggle button is hidden. See
[ListView → Always-visible (pinned) filter](list_view.md).
```

- [ ] **Step 3: Add the setting row**

In `docs/reference/settings.md`, add a row to the main `CRUD_VIEWS_*` settings table (place it next to `CRUD_VIEWS_FILTER_PERSISTENCE` if present, otherwise anywhere in that table). Use the table's existing column order `| Setting | Description | Type | Default |`:

```markdown
| CRUD_VIEWS_FILTER_PINNED | When `True`, list/card filters render always-open and the filter toggle button is hidden. Per-view override via `cv_filter_pinned`. | `bool` | `False` |
```

If the table's column order differs, match the existing order — verify by reading the header row first.

- [ ] **Step 4: Verify the docs build (strict)**

Run: `mkdocs build --strict` (from repo root; this is the same command CI runs in `.github/workflows/docs.yml`).
Expected: builds with no warnings/errors. If `mkdocs` is unavailable locally, instead confirm the three files have no broken relative links by inspection.

- [ ] **Step 5: Commit**

```bash
git add docs/reference/list_view.md docs/reference/card-list-view.md docs/reference/settings.md
git commit -m "docs: document cv_filter_pinned and CRUD_VIEWS_FILTER_PINNED"
```

---

### Task 6: In-project skill

**Files:**
- Modify: `skills/django-crud-views/references/api-reference.md`
- Modify: `skills/django-crud-views/SKILL.md`

- [ ] **Step 1: Update the API reference example**

In `skills/django-crud-views/references/api-reference.md`, find the line (~73):

```python
    cv_filter_persistence = True  # store filter state in session
```

and add directly below it:

```python
    cv_filter_pinned = False  # True = filter always open, toggle button hidden
```

- [ ] **Step 2: Update the filter-button description in the skill reference**

In the same file, find the context-buttons description (~line 300) that reads
`... \`filter\` (toggle filter form).` and append a clause so it reads:
`... \`filter\` (toggle filter form; hidden when \`cv_filter_pinned\` is set).`

- [ ] **Step 3: Mention it in the Filtering section**

In the same file, in the Filtering section (~lines 256–259, near the `cv_filter_persistence` mention), add a sentence:

```markdown
Set `cv_filter_pinned = True` to render the filter always-open and hide the toggle button
(default from the `CRUD_VIEWS_FILTER_PINNED` setting). Field-value persistence is unaffected.
```

- [ ] **Step 4: One-line mention in SKILL.md**

In `skills/django-crud-views/SKILL.md`, find the filter guidance and add a sentence:
"To show a filter always-open with no toggle button, set `cv_filter_pinned = True` (or the `CRUD_VIEWS_FILTER_PINNED` setting)."

- [ ] **Step 5: Verify the edits landed**

Run: `grep -rn "cv_filter_pinned" skills/django-crud-views/`
Expected: matches in both `references/api-reference.md` (3 spots) and `SKILL.md` (1 spot).

- [ ] **Step 6: Commit**

```bash
git add skills/django-crud-views/references/api-reference.md skills/django-crud-views/SKILL.md
git commit -m "docs(skill): document cv_filter_pinned"
```

---

### Task 7: Final full-suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `cd tests && pytest -q`
Expected: all pass (prior baseline: 346 passed, 1 skipped — now +~6 new tests). No regressions in `test_card_order.py` / `test_basic.py` / guardian tests.

- [ ] **Step 2: Confirm default-off behavior is unchanged**

Run: `cd tests && pytest test1/test_card_order.py -q`
Expected: PASS — confirms the non-pinned (default) path still renders the collapse wrapper and `#filter-form` exactly as before.

---

## Self-Review notes

- **Spec coverage:** setting (Task 1 Step 3) ✓; mixin attribute + forced-expand context (Task 1 Step 4) ✓; button hide (Task 2) ✓; bootstrap5 collapse-drop (Task 3) ✓; plain theme unchanged (no task needed — covered by shared button-hide, noted) ✓; session field-value persistence preserved (Task 4 persistence test) ✓; ListView+CardListView parity (Tasks 1–4 use both `PublisherOrderCardListView` and `PublisherListView`) ✓; docs 3 files (Task 5) ✓; skill 2 files (Task 6) ✓; tests (a)–(e) mapped: (a) Task 2/3 card pinned, (b) non-pinned assertions in Tasks 2/3, (c) card pinned throughout, (d) Task 1 setting-default test + monkeypatch-attribute behavior tests, (e) Task 4 persistence test ✓.
- **Placeholder scan:** none — every code/template/test step has full content; doc steps give exact text to insert and a grep/verify.
- **Naming consistency:** `cv_filter_pinned` (attribute), `filter_pinned` (settings field), `CRUD_VIEWS_FILTER_PINNED` (env/setting key), `FilterContextButton`, `list_filter.inner.html` used consistently across tasks.
- **Snapshot trap:** explicitly called out so the implementer tests behavior via `monkeypatch.setattr(View, "cv_filter_pinned", True)` rather than patching the setting at runtime.
