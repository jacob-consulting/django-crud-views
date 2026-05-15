# DetailCustomView Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract a base `DetailCustomView` from `DetailView` that provides the "detail" role without `ObjectDetailMixin`, allowing fully custom templates for object display.

**Architecture:** `DetailCustomView` (new base) holds all shared detail attributes (key, path, icons, snippets). `DetailView` inherits from it and adds `ObjectDetailMixin` + `cv_property_display`. Permission-required and Guardian variants follow the same pattern.

**Tech Stack:** Django class-based views, pytest, django-guardian

---

### Task 1: Create `DetailCustomView` and refactor `DetailView`

**Files:**
- Create: `crud_views/lib/views/detail_custom.py`
- Create: `crud_views/templates/crud_views/view_detail_custom.html`
- Modify: `crud_views/lib/views/detail.py`
- Modify: `crud_views/lib/views/__init__.py`

- [ ] **Step 1: Create the `DetailCustomView` module**

Create `crud_views/lib/views/detail_custom.py`:

```python
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class DetailCustomView(CrudView, generic.DetailView):
    template_name = "crud_views/view_detail_custom.html"

    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions = crud_views_settings.detail_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/detail.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/detail.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/detail.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/detail.html"

    # icons
    cv_icon_action = "fa-regular fa-eye"


class DetailCustomViewPermissionRequired(CrudViewPermissionRequiredMixin, DetailCustomView):
    cv_permission = "view"
```

- [ ] **Step 2: Create the template**

Create `crud_views/templates/crud_views/view_detail_custom.html`:

```html
{% extends cv_extends %}

{% block cv_content %}
{% endblock cv_content %}
```

- [ ] **Step 3: Refactor `DetailView` to inherit from `DetailCustomView`**

Replace `crud_views/lib/views/detail.py` with:

```python
from typing import Iterable

from django_object_detail import PropertyConfig
from django_object_detail.config import PropertyGroupConfig
from django_object_detail.views import ObjectDetailMixin

from crud_views.lib.check import Check, CheckAttribute, CheckExpression
from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views.detail_custom import DetailCustomView


class DetailView(ObjectDetailMixin, DetailCustomView):
    template_name = "crud_views/view_detail.html"

    cv_property_display: list | None = None

    @property
    def property_display(self):
        return self.cv_property_display

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        # cv_property_display must be set
        yield CheckAttribute(context=cls, id="E240", attribute="cv_property_display")
        # structural validation
        pd = cls.cv_property_display
        if pd is not None:
            yield CheckExpression(
                context=cls,
                id="E241",
                expression=isinstance(pd, list),
                msg="cv_property_display must be a list",
            )
            if isinstance(pd, list):
                for i, group in enumerate(pd):
                    if isinstance(group, PropertyGroupConfig):
                        continue
                    yield CheckExpression(
                        context=cls,
                        id="E242",
                        expression=isinstance(group, dict) and "title" in group,
                        msg=f"cv_property_display[{i}] must be a dict with a 'title' key",
                    )
                    yield CheckExpression(
                        context=cls,
                        id="E243",
                        expression=isinstance(group, dict) and "properties" in group,
                        msg=f"cv_property_display[{i}] must be a dict with a 'properties' key",
                    )
                    if isinstance(group, dict) and "properties" in group:
                        props = group["properties"]
                        yield CheckExpression(
                            context=cls,
                            id="E244",
                            expression=isinstance(props, list),
                            msg=f"cv_property_display[{i}]['properties'] must be a list",
                        )
                        if isinstance(props, list):
                            for j, prop in enumerate(props):
                                yield CheckExpression(
                                    context=cls,
                                    id="E245",
                                    expression=isinstance(prop, (str, dict, PropertyConfig)),
                                    msg=f"cv_property_display[{i}]['properties'][{j}] must be a str, dict, or PropertyConfig",
                                )


class DetailViewPermissionRequired(CrudViewPermissionRequiredMixin, DetailView):
    cv_permission = "view"
```

- [ ] **Step 4: Update `__init__.py` exports**

In `crud_views/lib/views/__init__.py`, add the imports and exports for the new classes. Add after the `detail` import line:

```python
from .detail_custom import DetailCustomView, DetailCustomViewPermissionRequired
```

And add to `__all__`:

```python
"DetailCustomView",
"DetailCustomViewPermissionRequired",
```

- [ ] **Step 5: Run full test suite to verify no regressions**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest -v`
Expected: All 258 tests pass — the refactored `DetailView` behavior is identical.

- [ ] **Step 6: Commit**

```bash
git add crud_views/lib/views/detail_custom.py crud_views/lib/views/detail.py crud_views/lib/views/__init__.py crud_views/templates/crud_views/view_detail_custom.html
git commit -m "refactor: extract DetailCustomView as base class for DetailView"
```

---

### Task 2: Add Guardian variant

**Files:**
- Modify: `crud_views_guardian/lib/views.py`

- [ ] **Step 1: Add `GuardianDetailCustomViewPermissionRequired`**

In `crud_views_guardian/lib/views.py`, add the import at the top (alongside the existing `DetailViewPermissionRequired` import):

```python
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    DetailCustomViewPermissionRequired,
    ...
)
```

Then add the class after `GuardianDetailViewPermissionRequired`:

```python
class GuardianDetailCustomViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DetailCustomViewPermissionRequired
):
    pass
```

- [ ] **Step 2: Run full test suite**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest -v`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add crud_views_guardian/lib/views.py
git commit -m "feat: add GuardianDetailCustomViewPermissionRequired"
```

---

### Task 3: Add tests for `DetailCustomView`

**Files:**
- Create: `tests/test1/app/templates/app/author_detail_custom.html`
- Modify: `tests/test1/app/views.py` (add a `DetailCustomView` to an existing ViewSet)
- Create: `tests/test1/test_detail_custom.py`

- [ ] **Step 1: Create the custom detail template for tests**

Create `tests/test1/app/templates/app/author_detail_custom.html`:

```html
{% extends cv_extends %}

{% block cv_content %}
<div class="author-custom-detail">
    <h2>{{ object.first_name }} {{ object.last_name }}</h2>
    <p class="pseudonym">{{ object.pseudonym|default:"—" }}</p>
</div>
{% endblock cv_content %}
```

- [ ] **Step 2: Add a ViewSet with `DetailCustomView` to the test app**

In `tests/test1/app/views.py`, add a new ViewSet for testing `DetailCustomView`. Add after the `cv_author_wide_card` section (around line 182):

```python
# --- Author Custom Detail (DetailCustomView without ObjectDetailMixin) ---

cv_author_custom_detail = ViewSet(model=Author, name="author_custom_detail")


class AuthorCustomDetailListView(ListViewPermissionRequired):
    cv_viewset = cv_author_custom_detail


class AuthorCustomDetailView(DetailCustomViewPermissionRequired):
    cv_viewset = cv_author_custom_detail
    template_name = "app/author_detail_custom.html"
```

Add the necessary import at the top of the file:

```python
from crud_views.lib.views import DetailCustomViewPermissionRequired
```

Also register the URL patterns in `tests/test1/app/urls.py`:

```python
from tests.test1.app.views import (
    ...
    cv_author_custom_detail,
)

urlpatterns += cv_author_custom_detail.urlpatterns
```

- [ ] **Step 3: Write tests**

Create `tests/test1/test_detail_custom.py`:

```python
import pytest
from django.test.client import Client
from lxml import html

from crud_views.lib.viewset import ViewSet


@pytest.fixture
def cv_author_custom_detail():
    from tests.test1.app.views import cv_author_custom_detail as ret

    return ret


@pytest.fixture
def user_author_custom_detail_view(cv_author_custom_detail):
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_custom_detail", password="password")
    user_viewset_permission(user, cv_author_custom_detail, "view")
    return user


@pytest.fixture
def client_user_author_custom_detail(client, user_author_custom_detail_view) -> Client:
    client.force_login(user_author_custom_detail_view)
    return client


@pytest.mark.django_db
def test_detail_custom_view_renders(client_user_author_custom_detail: Client, cv_author_custom_detail, author_douglas_adams):
    """DetailCustomView renders the custom template with object context."""
    pk = author_douglas_adams.pk
    response = client_user_author_custom_detail.get(f"/author_custom_detail/{pk}/detail/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    custom_div = doc.cssselect(".author-custom-detail")
    assert len(custom_div) == 1
    assert "Douglas" in custom_div[0].text_content()
    assert "Adams" in custom_div[0].text_content()


@pytest.mark.django_db
def test_detail_custom_view_permission_denied(client_user_a: Client, cv_author_custom_detail, author_douglas_adams):
    """User without view permission gets 403."""
    pk = author_douglas_adams.pk
    response = client_user_a.get(f"/author_custom_detail/{pk}/detail/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_detail_custom_view_has_correct_key(cv_author_custom_detail):
    """DetailCustomView registers with key 'detail'."""
    view_class = cv_author_custom_detail.get_view_class("detail")
    assert view_class.cv_key == "detail"
    assert view_class.cv_path == "detail"


@pytest.mark.django_db
def test_detail_view_still_works(client_user_author_view: Client, cv_author, author_douglas_adams):
    """Existing DetailView (with ObjectDetailMixin) still renders correctly after refactor."""
    pk = author_douglas_adams.pk
    response = client_user_author_view.get(f"/author/{pk}/detail/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Douglas" in content
    assert "Adams" in content
```

- [ ] **Step 4: Run the tests**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest test1/test_detail_custom.py -v`
Expected: All 4 tests pass.

- [ ] **Step 5: Run full test suite**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest -v`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/test1/test_detail_custom.py tests/test1/app/views.py tests/test1/app/urls.py tests/test1/app/templates/app/author_detail_custom.html
git commit -m "test: add tests for DetailCustomView"
```

---

### Task 4: Update bootstrap5 example

**Files:**
- Modify: `examples/bootstrap5/app/views/book.py`
- Create: `examples/bootstrap5/app/templates/app/book_detail.html`

- [ ] **Step 1: Create the custom book detail template**

Create `examples/bootstrap5/app/templates/app/book_detail.html`:

```html
{% extends cv_extends %}

{% load i18n %}

{% block cv_content %}
<div class="row">
    <div class="col-md-8">
        <table class="table">
            <tr>
                <th>{% translate "Title" %}</th>
                <td>{{ object.title }}</td>
            </tr>
            <tr>
                <th>{% translate "Price" %}</th>
                <td>{{ object.price }} €</td>
            </tr>
            <tr>
                <th>{% translate "Author" %}</th>
                <td>{{ object.author }}</td>
            </tr>
            <tr>
                <th>{% translate "Created" %}</th>
                <td>{{ object.created_dt }}</td>
            </tr>
            <tr>
                <th>{% translate "Modified" %}</th>
                <td>{{ object.modified_dt }}</td>
            </tr>
        </table>
    </div>
</div>
{% endblock cv_content %}
```

- [ ] **Step 2: Update `BookDetailView` to use `DetailCustomView`**

In `examples/bootstrap5/app/views/book.py`, change the import: replace `GuardianDetailViewPermissionRequired` with `GuardianDetailCustomViewPermissionRequired`:

```python
from crud_views_guardian.lib.views import (
    GuardianCardListViewPermissionRequired,
    GuardianDetailCustomViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)
```

Replace the `BookDetailView` class:

```python
class BookDetailView(GuardianDetailCustomViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["card", "detail", "update", "delete"]
    cv_cancel_key = "card"
    template_name = "app/book_detail.html"
```

- [ ] **Step 3: Commit**

```bash
git add examples/bootstrap5/app/views/book.py examples/bootstrap5/app/templates/app/book_detail.html
git commit -m "feat: use DetailCustomView for BookDetailView in bootstrap5 example"
```

---

### Task 5: Update documentation and skill reference

**Files:**
- Create: `docs/reference/detail_custom_view.md`
- Modify: `skills/django-crud-views/SKILL.md`

- [ ] **Step 1: Create documentation**

Create `docs/reference/detail_custom_view.md`:

```markdown
# DetailCustomView

A detail view for displaying a single object with a fully custom template. Unlike
[`DetailView`](detail_view.md), it does **not** use `ObjectDetailMixin` or
`cv_property_display` — you provide the entire template yourself.

## Quick Reference

| View class | Use for |
|---|---|
| `DetailCustomView` | Custom detail template (no permission check) |
| `DetailCustomViewPermissionRequired` | Custom detail template with model-level permission check |
| `GuardianDetailCustomViewPermissionRequired` | Custom detail template with per-object permissions (django-guardian) |

## When to Use

- **`DetailView`** — when you want structured property groups rendered automatically
  via django-object-detail. Configure `cv_property_display` and you're done.
- **`DetailCustomView`** — when you need full control over the detail page layout.
  You provide a custom `template_name` with your own HTML.

Both register with `cv_key = "detail"` and `cv_path = "detail"` — they fill the
same role in a ViewSet. Use one or the other, not both.

## Minimal Pattern

```python
from crud_views.lib.views import DetailCustomViewPermissionRequired

class BookDetailView(DetailCustomViewPermissionRequired):
    cv_viewset = cv_book
    template_name = "myapp/book_detail.html"
```

The template receives `object`, `view`, and `cv_extends` in its context:

```html
{% extends cv_extends %}

{% block cv_content %}
<h2>{{ object.title }}</h2>
<p>{{ object.description }}</p>
{% endblock cv_content %}
```

## Guardian (Per-Object Permissions)

```python
from crud_views_guardian.lib.views import GuardianDetailCustomViewPermissionRequired

class BookDetailView(GuardianDetailCustomViewPermissionRequired):
    cv_viewset = cv_book  # must be a GuardianViewSet
    template_name = "myapp/book_detail.html"
```

## Class Hierarchy

`DetailCustomView` is the base class for `DetailView`:

```
DetailCustomView          ← custom template, no ObjectDetailMixin
└── DetailView            ← adds ObjectDetailMixin + cv_property_display
```

Both share the same key, path, icons, and snippet templates.
```

- [ ] **Step 2: Update skill reference**

In `skills/django-crud-views/SKILL.md`, add a new section before the `## CardListView` section:

```markdown
## DetailCustomView

Detail view without `ObjectDetailMixin` — full custom template control. Same `cv_key = "detail"` and
`cv_path = "detail"` as `DetailView`. Use when you need complete layout control instead of structured
`cv_property_display` groups.

```python
from crud_views.lib.views import DetailCustomViewPermissionRequired

class BookDetailView(DetailCustomViewPermissionRequired):
    cv_viewset = cv_book
    template_name = "myapp/book_detail.html"
```

Template receives `object`, `view`, and `cv_extends`. Extend `cv_extends` and fill `{% block cv_content %}`.

Guardian variant: `GuardianDetailCustomViewPermissionRequired`.

`DetailCustomView` is the base class for `DetailView` — both share icons, snippets, and context actions.

---
```

- [ ] **Step 3: Commit**

```bash
git add docs/reference/detail_custom_view.md skills/django-crud-views/SKILL.md
git commit -m "docs: add DetailCustomView documentation and skill reference"
```

---

### Task 6: Final verification

- [ ] **Step 1: Run full test suite**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest -v`
Expected: All tests pass.

- [ ] **Step 2: Run linter**

Run: `task check && task format`
Expected: No issues.
