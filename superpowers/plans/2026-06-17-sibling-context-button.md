# SiblingContextButton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `SiblingContextButton` that, placed on a child view, links to a sibling collection (another child of the same parent), reusing the parent PK from the current URL.

**Architecture:** A new `ContextButton` subclass composing the two existing relationship buttons — it guards on the current view having a parent (like `ParentContextButton`), resolves a named sibling viewset and builds its URL from the current view's kwargs (the sibling shares the same parent chain), and renders/labels/templates exactly like `ChildContextButton`. Plus docs, the inline skill, a bootstrap5 example demo, and tests.

**Tech Stack:** Python, Django, Pydantic (button models), django-tables2 (example list views), pytest.

## Global Constraints

- Line length 120, double quotes, ruff format/check.
- Public button attributes use no `cv_` prefix on the button model itself (matches `ChildContextButton`'s `child_name`/`child_key`); the button's *output* dict keys keep the `cv_` prefix.
- Class name is `SiblingContextButton`; parameters are `sibling_name` (required) and `sibling_key` (default `"list"`).
- Access is checked with `obj=None` (model-level on the sibling view); object-level/Guardian permissions on the parent are not consulted (documented limitation).
- Purely additive — no change to existing buttons, viewsets, or templates.
- Tests live in `tests/test1/`; run from the `tests/` directory.

---

### Task 1: `SiblingContextButton` core class + export

Add the class, export it, and prove it with tests against a second child viewset wired into the test app.

**Files:**
- Modify: `src/crud_views/lib/view/buttons.py` (add `SiblingContextButton` after `ChildContextButton`)
- Modify: `src/crud_views/lib/view/__init__.py` (export)
- Modify: `tests/test1/app/views.py` (register a second child of `cv_publisher`: `cv_contract` + list view — test scaffolding)
- Modify: `tests/test1/app/urls.py` (include `cv_contract.urlpatterns`)
- Test: `tests/test1/test_sibling_context_button.py` (new)

**Interfaces:**
- Consumes: `ContextButton._inject_template`, `ContextButton.render_label`, `_resolve_container_key` (existing); `ViewSet.get_viewset`, `get_view_class`, `get_parent_url_args`, `get_router_name`, `icon_header` (existing).
- Produces: `SiblingContextButton(key=..., sibling_name=..., sibling_key="list")` exported from `crud_views.lib.view`; `get_context(context) -> dict` returning the standard button data dict (`cv_url`, `cv_icon_action`, `cv_access`, `cv_action_enabled`, `cv_template`/`cv_template_code`, optional `cv_action_label`) or `{}` when the current view has no parent.

- [ ] **Step 1: Register the test sibling viewset**

In `tests/test1/app/views.py`, after the `cv_book` block (the `BookDeleteView` class, before `# --- Vehicle (polymorphic) ---`), add a second child of `cv_publisher` over the existing `Contract` model:

```python
# --- Contract (second child of publisher, sibling of book) ---

from tests.test1.app.models import Contract  # noqa: E402

cv_contract = ViewSet(
    model=Contract,
    name="contract",
    parent=ParentViewSet(name="publisher"),
    icon_header="fa-solid fa-file-contract",
)


class ContractTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()


class ContractListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = ContractTable
    cv_viewset = cv_contract
    cv_list_actions = ["detail"]


class ContractDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_contract
    cv_property_display = [
        {
            "title": "Attributes",
            "properties": ["title"],
        },
    ]
```

(`Table`, `LinkDetailColumn`, `tables`, `ListViewTableMixin`, `ListViewPermissionRequired`, `DetailViewPermissionRequired`, `ViewSet`, `ParentViewSet` are already imported in this module — confirm at the top of the file; the `Contract` import is added inline above.)

- [ ] **Step 2: Wire the sibling viewset's URLs**

In `tests/test1/app/urls.py`, add `cv_contract` to the import block and append its urlpatterns:

```python
    cv_book,
    cv_contract,
```

and after `urlpatterns += cv_book.urlpatterns`:

```python
urlpatterns += cv_contract.urlpatterns
```

- [ ] **Step 3: Write the failing test**

Create `tests/test1/test_sibling_context_button.py`:

```python
"""SiblingContextButton: child view -> sibling collection, parent PK from the URL."""

import pytest
from django.urls import reverse

from crud_views.lib.view import SiblingContextButton
from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_contract():
    from tests.test1.app.views import cv_contract as ret

    return ret


@pytest.fixture
def client_book_and_contract_view(client, cv_book, cv_contract):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_book_contract_view", password="password")
    user_viewset_permission(user, cv_book, "view")
    user_viewset_permission(user, cv_contract, "view")
    client.force_login(user)
    return client


def _book_list_view(client, publisher):
    from tests.test1.app.views import cv_book

    url = reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_links_to_sibling_with_parent_pk(client_book_and_contract_view, cv_contract, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_book_and_contract_view, publisher_penguin)
    btn = SiblingContextButton(key="to_contracts", sibling_name="contract")
    ctx = btn.get_context(view.cv_get_view_context())

    expected = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    assert ctx["cv_url"] == expected
    assert ctx["cv_access"] is True


@pytest.mark.django_db
def test_hidden_without_access(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    # user has book view but NOT contract view
    view = _book_list_view(client_user_book_view, publisher_penguin)
    btn = SiblingContextButton(key="to_contracts", sibling_name="contract")
    ctx = btn.get_context(view.cv_get_view_context())
    assert ctx.get("cv_access") is not True


@pytest.mark.django_db
def test_empty_on_parentless_view(client_user_publisher_view, cv_publisher, publisher_penguin):
    url = reverse(cv_publisher.get_router_name("list"))
    resp = client_user_publisher_view.get(url)
    assert resp.status_code == 200
    view = resp.context["view"]
    btn = SiblingContextButton(key="to_contracts", sibling_name="contract")
    assert btn.get_context(view.cv_get_view_context()) == {}


@pytest.mark.django_db
def test_unknown_sibling_raises(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    from crud_views.lib.exceptions import ViewSetNotFoundError

    view = _book_list_view(client_user_book_view, publisher_penguin)
    btn = SiblingContextButton(key="to_nothing", sibling_name="does_not_exist")
    with pytest.raises(ViewSetNotFoundError):
        btn.get_context(view.cv_get_view_context())
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd tests && pytest test1/test_sibling_context_button.py -v`
Expected: FAIL — `ImportError: cannot import name 'SiblingContextButton'`.

- [ ] **Step 5: Implement `SiblingContextButton`**

In `src/crud_views/lib/view/buttons.py`, add after the `ChildContextButton` class (before `FilterContextButton`):

```python
class SiblingContextButton(ContextButton):
    """
    A context button on a child view that links to a sibling collection — another child of
    the same parent — reusing the parent PK already present in the current URL.
    """

    sibling_name: str
    sibling_key: str = "list"

    def get_context(self, context: ViewContext) -> dict:
        # only rendered on child views (those with a parent)
        if not context.view.cv_viewset.parent:
            return dict()

        sibling_vs = context.view.cv_viewset.get_viewset(self.sibling_name)
        sibling_key = self._resolve_container_key(sibling_vs, self.sibling_key)
        cls = sibling_vs.get_view_class(sibling_key)

        # the sibling shares the current view's parent chain, so reuse its URL args
        kwargs = {arg: context.view.kwargs[arg] for arg in sibling_vs.get_parent_url_args()}
        cv_url = reverse(sibling_vs.get_router_name(sibling_key), kwargs=kwargs)

        dict_kwargs = dict(
            cv_access=False,
            cv_url=cv_url,
            cv_icon_action=sibling_vs.icon_header,
        )

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(context.view.request.user, None)

        if cls.cv_has_access(context.view.request.user, None):
            dict_kwargs.update(cv_access=True)

        data = cls.cv_get_dict(context=context, **dict_kwargs)

        cv_action_label = self.render_label(data, context)
        if cv_action_label:
            data["cv_action_label"] = cv_action_label

        self._inject_template(data)

        return data
```

(`reverse` is already imported at the top of `buttons.py`.)

- [ ] **Step 6: Export the class**

In `src/crud_views/lib/view/__init__.py`, extend the import and `__all__`:

```python
from .buttons import ContextButton, ParentContextButton, ChildContextButton, SiblingContextButton
```

and add `"SiblingContextButton",` to the `__all__` list after `"ChildContextButton",`.

- [ ] **Step 7: Run test to verify it passes**

Run: `cd tests && pytest test1/test_sibling_context_button.py -v`
Expected: PASS (4 tests).

- [ ] **Step 8: Format, lint, commit**

```bash
task format && task check
git add src/crud_views/lib/view/buttons.py src/crud_views/lib/view/__init__.py tests/test1/app/views.py tests/test1/app/urls.py tests/test1/test_sibling_context_button.py
git commit -m "feat(buttons): add SiblingContextButton (child -> sibling collection)"
```

---

### Task 2: Documentation

Add the reference section and a FAQ entry.

**Files:**
- Modify: `docs/reference/context_buttons.md` (new `SiblingContextButton` section after `ChildContextButton`)
- Modify: `docs/faq.md` (new FAQ entry)

- [ ] **Step 1: Add the reference section**

In `docs/reference/context_buttons.md`, after the `ChildContextButton` section (before `## Customizing Default Buttons`), insert:

````markdown
## SiblingContextButton

Placed on a **child** view, links sideways to a **sibling** collection — another child of the
same parent — reusing the parent PK from the current URL. It is the composition of
`ParentContextButton` (resolve the parent) and `ChildContextButton` (hop to a named child):
use `ChildContextButton` on the *parent* view and `SiblingContextButton` on its *children*.

```python
from crud_views.lib.view import SiblingContextButton

SiblingContextButton(
    key="articles",                # action key referenced in cv_context_actions
    sibling_name="article",        # registry name of the sibling viewset (same parent)
    sibling_key="list",            # target view key in the sibling viewset (default: "list")
    label_template_code="Articles",
)
```

| Parameter             | Type          | Default  | Description                                       |
|-----------------------|---------------|----------|---------------------------------------------------|
| `key`                 | `str`         | required | Action key referenced in `cv_context_actions`     |
| `sibling_name`        | `str`         | required | Registry name of the sibling viewset (same parent)|
| `sibling_key`         | `str`         | `"list"` | Target view key in the sibling viewset            |
| `label_template`      | `str \| None` | `None`   | Path to a Django template for the button label    |
| `label_template_code` | `str \| None` | `None`   | Inline Django template string for the label       |

Renders nothing when the current view has **no parent**. The URL is built from the current
view's kwargs (the sibling shares the same parent chain), so no current object is required.
Access is checked via the sibling view's `cv_has_access(user, None)` — model-level on the
sibling collection; object-level/Guardian permissions keyed on the parent are not consulted.

### Example

Given `Author` with children `Book` and `Article`:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
from crud_views.lib.view import SiblingContextButton
from crud_views.lib.views import ListViewPermissionRequired

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    context_buttons=context_buttons_default() + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)


class BookListView(ListViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["parent", "create", "articles"]
```

On `/author/<author_pk>/book/`, the `"articles"` button links to `/author/<author_pk>/article/`.
````

- [ ] **Step 2: Add the FAQ entry**

In `docs/faq.md`, append:

````markdown
## How do I link from one child collection to a sibling collection?

When you have a parent with several children (e.g. `Author` → `Book`, `Article`) and want a
button on one child's pages that jumps to a sibling collection under the *same* parent, use
[`SiblingContextButton`](reference/context_buttons.md#siblingcontextbutton). Place it on the
child viewset; it reuses the parent PK from the current URL:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
from crud_views.lib.view import SiblingContextButton

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    context_buttons=context_buttons_default() + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)
```

```python
class BookListView(ListViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["parent", "create", "articles"]
```

Use `ChildContextButton` on the parent view to go *down* to a child, and
`SiblingContextButton` on a child view to go *sideways* to a sibling.
````

- [ ] **Step 3: Build docs to verify no broken references**

Run: `uv run mkdocs build`
Expected: build succeeds, no warnings about the edited pages.

- [ ] **Step 4: Commit**

```bash
git add docs/reference/context_buttons.md docs/faq.md
git commit -m "docs(buttons): document SiblingContextButton (reference + FAQ)"
```

---

### Task 3: Inline skill

Update the bundled skill so the agent guidance covers the new button.

**Files:**
- Modify: `skills/django-crud-views/SKILL.md` (subsection after `ChildContextButton`, ~line 226)
- Modify: `skills/django-crud-views/references/api-reference.md` (catalog entry + import line, ~line 305-330)

- [ ] **Step 1: Add the SKILL.md subsection**

In `skills/django-crud-views/SKILL.md`, after the `ChildContextButton` block (after its parameter bullets, ~line 248-250, before the next section), insert:

````markdown
### SiblingContextButton

Use `SiblingContextButton` on a **child** view to link sideways to a **sibling** collection —
another child of the same parent. It reuses the parent PK from the current URL. Pair it with
`ChildContextButton`: `ChildContextButton` on the parent (go down), `SiblingContextButton` on
the children (go sideways).

```python
from crud_views.lib.view import SiblingContextButton
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    context_buttons=context_buttons_default() + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)

# Then reference the key in cv_context_actions on the child's view:
class BookListView(ListViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["parent", "create", "articles"]
```

`SiblingContextButton` parameters:
- `key` — the action key referenced in `cv_context_actions`
- `sibling_name` — registry name of the sibling viewset (must share the same parent)
- `sibling_key` — target view key in the sibling viewset (default `"list"`)

Renders nothing on a view without a parent. Access is checked model-level on the sibling
view (no parent object is consulted).
````

- [ ] **Step 2: Update the api-reference catalog**

In `skills/django-crud-views/references/api-reference.md`, update the import line (~line 305):

```python
from crud_views.lib.view import ContextButton, ParentContextButton, ChildContextButton, SiblingContextButton
```

and after the `### ChildContextButton` block (before the next `###`), add:

````markdown
### SiblingContextButton

On a child view, links to a sibling collection (another child of the same parent), reusing
the parent PK from the URL.

```python
SiblingContextButton(
    key="articles",                # action key referenced in cv_context_actions
    sibling_name="article",        # registry name of the sibling viewset (same parent)
    sibling_key="list",            # target view key in the sibling viewset (default: "list")
)
```

Renders nothing on a parentless view; access checked model-level on the sibling view.
````

- [ ] **Step 3: Commit**

```bash
git add skills/django-crud-views/SKILL.md skills/django-crud-views/references/api-reference.md
git commit -m "docs(skill): document SiblingContextButton"
```

---

### Task 4: bootstrap5 example demo

Give `Foo` a second child (`Qux`) so two siblings exist, and wire `SiblingContextButton` both ways between `Bar` and `Qux`.

**Files:**
- Modify: `examples/bootstrap5/app/models/__init__.py` (add `Qux` model)
- Create: `examples/bootstrap5/app/migrations/0009_qux.py` (via makemigrations)
- Create: `examples/bootstrap5/app/views/qux.py` (full CRUD + sibling button)
- Modify: `examples/bootstrap5/app/views/bar.py` (add sibling button to `cv_bar` + list context actions)
- Modify: `examples/bootstrap5/app/urls.py` (import + register `cv_qux`)

- [ ] **Step 1: Add the `Qux` model**

In `examples/bootstrap5/app/models/__init__.py`, after the `Baz` class:

```python
class Qux(models.Model):
    foo = models.ForeignKey(Foo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name}"
```

- [ ] **Step 2: Create the migration**

Run: `cd examples/bootstrap5 && python manage.py makemigrations app`
Expected: creates `app/migrations/0009_qux.py` adding the `Qux` model. (If the demo DB is in use: `python manage.py migrate`.)

- [ ] **Step 3: Create the `qux` views with the sibling button**

Create `examples/bootstrap5/app/views/qux.py`:

```python
import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _

from app.models import Qux
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.view import SiblingContextButton
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewTableMixin,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    CreateViewParentMixin,
)
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default

cv_qux = ViewSet(
    model=Qux,
    name="qux",
    parent=ParentViewSet(name="foo"),
    icon_header="fa-solid fa-cat",
    context_buttons=context_buttons_default()
    + [
        SiblingContextButton(key="bars", sibling_name="bar", label_template_code="Bars"),
    ],
)


class QuxForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Qux
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class QuxTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class QuxListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Qux
    table_class = QuxTable
    cv_viewset = cv_qux
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["parent", "filter", "create", "bars"]


class QuxDetailView(DetailViewPermissionRequired):
    model = Qux
    cv_viewset = cv_qux
    cv_property_display = [
        {
            "title": _("Properties"),
            "icon": "cat",
            "description": _("Qux attributes"),
            "properties": ["id", "name"],
        },
    ]


class QuxUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Qux
    form_class = QuxForm
    cv_viewset = cv_qux


class QuxCreateView(CrispyModelViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    model = Qux
    form_class = QuxForm
    cv_viewset = cv_qux


class QuxDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Qux
    form_class = CrispyDeleteForm
    cv_viewset = cv_qux
```

- [ ] **Step 4: Add the reverse sibling button on `Bar`**

In `examples/bootstrap5/app/views/bar.py`, change the imports and the `cv_bar` definition, and add context actions to the list view.

Update the viewset import line:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
```

Add the button import (next to the other `crud_views.lib` imports):

```python
from crud_views.lib.view import SiblingContextButton
```

Replace the `cv_bar` assignment:

```python
cv_bar = ViewSet(
    model=Bar,
    name="bar",
    parent=ParentViewSet(name="foo"),
    icon_header="fa-solid fa-bone",
    context_buttons=context_buttons_default()
    + [
        SiblingContextButton(key="quxes", sibling_name="qux", label_template_code="Quxes"),
    ],
)
```

Add `cv_context_actions` to `BarListView`:

```python
class BarListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Bar
    table_class = BarTable
    cv_viewset = cv_bar
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["parent", "filter", "create", "quxes"]
```

- [ ] **Step 5: Register `cv_qux` URLs**

In `examples/bootstrap5/app/urls.py`, add the import after `from app.views.baz import cv_baz`:

```python
from app.views.qux import cv_qux
```

and add `+ cv_qux.urlpatterns` to the `urlpatterns +=` chain (e.g. right after `cv_baz.urlpatterns`):

```python
    + cv_baz.urlpatterns
    + cv_qux.urlpatterns
```

- [ ] **Step 6: Verify the example app boots**

Run: `cd examples/bootstrap5 && python manage.py check && python manage.py makemigrations --check --dry-run`
Expected: `System check identified no issues`; no pending model changes (migration from Step 2 covers `Qux`).

- [ ] **Step 7: Format, lint, commit**

```bash
cd /home/alex/projects/alex/django-crud-views && task format && task check
git add examples/bootstrap5/app/models/__init__.py examples/bootstrap5/app/migrations/0009_qux.py examples/bootstrap5/app/views/qux.py examples/bootstrap5/app/views/bar.py examples/bootstrap5/app/urls.py
git commit -m "docs(example): demo SiblingContextButton between Bar and Qux under Foo"
```

---

### Task 5: Full verification

- [ ] **Step 1: Run the complete test suite**

Run: `cd tests && pytest -q`
Expected: all pass (existing count + the 4 new sibling tests), no new failures.

- [ ] **Step 2: Lint/format clean**

Run: `task format && task check`
Expected: no changes / no errors.

- [ ] **Step 3: Docs build clean**

Run: `uv run mkdocs build`
Expected: build succeeds, no warnings.

- [ ] **Step 4: Review the branch diff**

Run: `git log --oneline main..HEAD && git diff --stat main..HEAD`
Expected: commits for Tasks 1-4 touching `buttons.py`, `lib/view/__init__.py`, test app + new test, docs, skill, and the bootstrap5 example.
```
