# CardView Ordering, Filter, Paging & Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `CardListView` an order-by combo + direction toggle, django-filter filtering, Django pagination, and optional session persistence — without filter and order clobbering each other's query params.

**Architecture:** A reusable `CardOrderMixin` resolves a whitelisted `(field, direction)` from GET params and applies `.order_by()` in `get_queryset()`. `CardListView` inherits it and adds Django-native `paginate_by`. Filtering stays the opt-in `ListViewTableFilterMixin` (already composes correctly: django-filter filters the ordered queryset). A toolbar template (above the grid) and a pagination snippet (below) carry each other's params as hidden inputs / preserved query strings so nothing is lost.

**Tech Stack:** Django 4.2/5.2/6.0, django-filter, django-crispy-forms, django-tables2 (list view only), pytest, lxml for HTML assertions, Bootstrap 5 theme, ruff.

---

## Background / key facts for the implementer

- `CardListView` lives in `src/crud_views/lib/views/card.py` and is currently
  `class CardListView(CrudView, generic.ListView)`. It renders
  `crud_views/view_card.html` → `view_card.content.html` (the card grid).
- `ListViewTableFilterMixin` (django-filter `FilterView`) lives in
  `src/crud_views/lib/views/mixins.py`. Its `get_filterset_kwargs` passes
  `queryset=self.get_queryset()`, so ordering applied in `get_queryset()` flows
  through filtering automatically — **this is why order and filter compose.**
- `ListViewFilterFormHelper` lives in `src/crud_views/lib/views/list.py`. It already
  injects a hidden `sort` field into the filter form so the table sort survives a
  filter submit. We extend it to also inject `order` + `dir`.
- The Bootstrap theme path is `crud_views` (`crud_views_settings.theme_path`).
  Filter snippets live under `crud_views/templates/crud_views/snippets/...`.
- **CSP note:** the project pursues CSP compatibility — do **not** add inline
  `onchange="this.form.submit()"` JS. The direction (↑/↓) buttons are themselves the
  submit/apply action; selecting a field then clicking a direction button applies both.
- GET param names are configurable (`cv_order_param` default `"order"`,
  `cv_order_dir_param` default `"dir"`) because a model may have a field literally
  named `order` (the test app's `Author` is an `OrderedModel`).
- Tests use pytest + Django test client + `lxml.html` (see `tests/test1/test_card.py`).
  Run from the `tests/` directory.

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `src/crud_views/lib/views/mixins.py` | Add `CardOrderMixin` (order resolution, queryset ordering, context); extend `ListViewTableFilterMixin.get()` reset to preserve `order`/`dir` | Modify |
| `src/crud_views/lib/views/card.py` | `CardListView` inherits `CardOrderMixin`; document `paginate_by` | Modify |
| `src/crud_views/lib/views/list.py` | `ListViewFilterFormHelper` injects hidden `order`/`dir` | Modify |
| `src/crud_views/templatetags/crud_views.py` | New `{% cv_pagination %}` inclusion tag | Modify |
| `src/crud_views/templates/crud_views/view_card.content.html` | Render order toolbar (top) + pagination (bottom) | Modify |
| `src/crud_views/templates/crud_views/snippets/card_order.html` | Order combo + direction toggle | Create |
| `src/crud_views/templates/crud_views/snippets/pagination.html` | Bootstrap5 pagination nav | Create |
| `tests/test1/app/views.py` | Dedicated `cv_publisher_order` card viewset for ordering/paging/filter tests | Modify |
| `tests/test1/app/urls.py` | Register `cv_publisher_order.urlpatterns` | Modify |
| `tests/test1/test_card_order.py` | New tests for ordering, direction, paging, coexistence, persistence | Create |
| `examples/bootstrap5/app/views/book.py` | Add `cv_order_fields`, `cv_order_default`, `paginate_by` to `BookCardListView` | Modify |
| `docs/reference/card-list-view.md` | Document ordering, paging, coexistence, persistence | Modify |
| `skills/django-crud-views/SKILL.md` + `references/api-reference.md` | Document new attributes | Modify |

---

## Task 1: `CardOrderMixin` — whitelisted queryset ordering

**Files:**
- Modify: `src/crud_views/lib/views/mixins.py`
- Modify: `src/crud_views/lib/views/card.py`
- Modify: `tests/test1/app/views.py`
- Modify: `tests/test1/app/urls.py`
- Test: `tests/test1/test_card_order.py` (create)

- [ ] **Step 1: Add the test-app demo viewset**

In `tests/test1/app/views.py`, after the `PublisherCardListView` class (around line 274),
add a dedicated viewset so ordering/paging/filter tests don't disturb existing card tests:

```python
# --- Publisher Order Demo (card with ordering, paging, filter) ---

cv_publisher_order = ViewSet(
    model=Publisher,
    name="publisher_order",
)


class PublisherOrderFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Publisher
        fields = ["name"]


class PublisherOrderCardListView(ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_publisher_order
    cv_order_fields = ["name", ("id", "ID")]
    cv_order_default = "name"
    paginate_by = 2
    filterset_class = PublisherOrderFilter
    formhelper_class = PublisherFilterFormHelper
    cv_card_actions = []
```

> `cv_card_actions = []` keeps this a card-only viewset (no detail/update needed).
> `ListViewTableFilterMixin`, `CardListViewPermissionRequired`, `PublisherFilterFormHelper`,
> and `ViewSet` are already imported in this file.

- [ ] **Step 2: Register its URLs**

In `tests/test1/app/urls.py`, add `cv_publisher_order` to the import list and append its
urlpatterns:

```python
from tests.test1.app.views import (
    cv_author,
    cv_author_wide_card,
    cv_author_custom_detail,
    cv_publisher,
    cv_publisher_order,
    cv_book,
    cv_vehicle,
    cv_campaign,
    cv_guardian_author,
    cv_guardian_publisher,
    cv_guardian_book,
    cv_guardian_publisher_cascade,
    cv_publisher_cascade,
    cv_publisher_protected,
    cv_publisher_form_protected,
    cv_publisher_linked,
)
```

and after `urlpatterns += cv_publisher.urlpatterns` add:

```python
urlpatterns += cv_publisher_order.urlpatterns
```

- [ ] **Step 3: Write the failing ordering test**

Create `tests/test1/test_card_order.py`:

```python
import pytest
from django.contrib.auth.models import User
from django.test.client import Client
from lxml import html

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_publisher_order():
    from tests.test1.app.views import cv_publisher_order as ret

    return ret


@pytest.fixture
def client_publisher_order(client, cv_publisher_order) -> Client:
    user = User.objects.create_user(username="user_pub_order", password="password")
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


def _card_titles(response) -> list[str]:
    doc = html.fromstring(response.content)
    return [c.text_content().strip() for c in doc.cssselect(".card.mb-3 .card-title")]


@pytest.mark.django_db
def test_card_order_ascending(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=asc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Alpha", "Bravo"]  # paginate_by=2, asc


@pytest.mark.django_db
def test_card_order_descending(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Charlie", "Bravo"]  # paginate_by=2, desc


@pytest.mark.django_db
def test_card_order_invalid_field_ignored(client_publisher_order, publishers):
    # "name; DROP" is not in cv_order_fields -> falls back to cv_order_default ("name" asc)
    response = client_publisher_order.get("/publisher_order/card/?order=bogus&dir=asc&page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Alpha", "Bravo"]


@pytest.mark.django_db
def test_card_order_default_applied(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?page=1")
    assert response.status_code == 200
    titles = _card_titles(response)
    assert titles == ["Alpha", "Bravo"]  # cv_order_default = "name"
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `cd tests && pytest test1/test_card_order.py -v`
Expected: FAIL — `CardListView` has no `cv_order_fields`/ordering yet, so `AttributeError`
or wrong ordering (and `test_card_order_descending` returns ascending order).

- [ ] **Step 5: Implement `CardOrderMixin`**

In `src/crud_views/lib/views/mixins.py`, add this class (place it just before
`ListViewTableMixin`). The file already imports `SessionData`; add no new imports for this
step:

```python
class CardOrderMixin:
    """
    Adds order-by + direction support to card views.

    The order field is whitelisted against ``cv_order_fields`` so an arbitrary
    GET parameter can never reach ``QuerySet.order_by()`` (no ordering injection).
    Direction is restricted to ``asc`` / ``desc``.
    """

    cv_order_fields: list = []  # list[str | tuple[str, str]]: field name or (name, label)
    cv_order_default: str | None = None  # e.g. "-name"; leading "-" => descending
    cv_order_param: str = "order"
    cv_order_dir_param: str = "dir"

    def cv_get_order_field_names(self) -> list[str]:
        return [f[0] if isinstance(f, (tuple, list)) else f for f in self.cv_order_fields]

    def cv_get_order(self) -> tuple[str | None, str]:
        """Resolve (field_name_or_None, direction) from GET, whitelisted."""
        names = self.cv_get_order_field_names()
        field = self.request.GET.get(self.cv_order_param) or ""
        direction = self.request.GET.get(self.cv_order_dir_param) or "asc"
        if direction not in ("asc", "desc"):
            direction = "asc"
        if field in names:
            return field, direction
        # not selected / not whitelisted -> fall back to default ordering
        if self.cv_order_default:
            default = self.cv_order_default
            if default.startswith("-"):
                return default[1:], "desc"
            return default, "asc"
        return None, direction

    def get_queryset(self):
        qs = super().get_queryset()
        field, direction = self.cv_get_order()
        if field:
            prefix = "-" if direction == "desc" else ""
            qs = qs.order_by(f"{prefix}{field}")
        return qs
```

- [ ] **Step 6: Wire `CardOrderMixin` into `CardListView`**

In `src/crud_views/lib/views/card.py`, update the imports and class declaration:

```python
from django.views import generic

from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.view.card import CardAction
from crud_views.lib.views.mixins import CardOrderMixin
from crud_views.lib.settings import crud_views_settings


class CardListView(CardOrderMixin, CrudView, generic.ListView):
    template_name = "crud_views/view_card.html"

    cv_pk: bool = False
    cv_key = "card"
    cv_path = "card"
    cv_object = False
    cv_card_actions: list[CardAction] = []
    cv_card_container_class: str = "col-md-6"
    cv_card_template: str = "crud_views/tags/card.html"
    cv_context_actions = crud_views_settings.list_context_actions
    paginate_by = None  # set per-view to enable pagination
    # ... (keep the rest of the existing attributes/methods unchanged)
```

> Keep every other existing attribute and the `cv_get_filter_icon` / `cv_filter_header`
> members exactly as they are. Only the base classes, the new import, and the
> `paginate_by = None` line are added.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cd tests && pytest test1/test_card_order.py -v`
Expected: PASS (4 passed).

- [ ] **Step 8: Run the existing card tests to confirm no regression**

Run: `cd tests && pytest test1/test_card.py test1/test_guardian_card.py -q`
Expected: all pass (the new mixin defaults to no ordering / no paging).

- [ ] **Step 9: Commit**

```bash
git add src/crud_views/lib/views/mixins.py src/crud_views/lib/views/card.py \
        tests/test1/app/views.py tests/test1/app/urls.py tests/test1/test_card_order.py
git commit -m "feat(card): add CardOrderMixin with whitelisted queryset ordering"
```

---

## Task 2: Order toolbar context + template

**Files:**
- Modify: `src/crud_views/lib/views/mixins.py` (add `get_context_data` to `CardOrderMixin`)
- Create: `src/crud_views/templates/crud_views/snippets/card_order.html`
- Modify: `src/crud_views/templates/crud_views/view_card.content.html`
- Test: `tests/test1/test_card_order.py`

- [ ] **Step 1: Write the failing toolbar tests**

Append to `tests/test1/test_card_order.py`:

```python
@pytest.mark.django_db
def test_card_order_toolbar_renders(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    form = doc.cssselect("form#cv-card-order-form")
    assert len(form) == 1
    options = doc.cssselect("#cv-card-order-form select[name=order] option")
    values = [o.get("value") for o in options]
    assert values == ["name", "id"]
    labels = [o.text_content().strip() for o in options]
    assert labels == ["Name", "ID"]
    dir_buttons = doc.cssselect("#cv-card-order-form button[name=dir]")
    assert {b.get("value") for b in dir_buttons} == {"asc", "desc"}


@pytest.mark.django_db
def test_card_order_toolbar_marks_active_direction(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc")
    doc = html.fromstring(response.content)
    desc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=desc]")[0]
    asc_btn = doc.cssselect("#cv-card-order-form button[name=dir][value=asc]")[0]
    assert "active" in desc_btn.get("class")
    assert "active" not in asc_btn.get("class")


@pytest.mark.django_db
def test_card_order_toolbar_absent_without_fields(client_user_author_view, cv_author, author_douglas_adams):
    # the plain AuthorCardListView has no cv_order_fields -> no toolbar
    response = client_user_author_view.get("/author/card/")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect("form#cv-card-order-form")) == 0
```

> `client_user_author_view`, `cv_author`, `author_douglas_adams` are existing fixtures
> available from the test app conftest (used in `test_card.py`).

- [ ] **Step 2: Run to verify failure**

Run: `cd tests && pytest test1/test_card_order.py -k toolbar -v`
Expected: FAIL — no `#cv-card-order-form` in the rendered HTML.

- [ ] **Step 3: Add `get_context_data` to `CardOrderMixin`**

In `src/crud_views/lib/views/mixins.py`, add this method to `CardOrderMixin` (after
`get_queryset`):

```python
    def cv_get_order_choices(self) -> list[dict]:
        current, _ = self.cv_get_order()
        choices = []
        for f in self.cv_order_fields:
            if isinstance(f, (tuple, list)):
                name, label = f[0], f[1]
            else:
                name = f
                try:
                    label = str(self.model._meta.get_field(name).verbose_name).capitalize()
                except Exception:  # pragma: no cover - defensive
                    label = name
            choices.append({"name": name, "label": label, "selected": name == current})
        return choices

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current, direction = self.cv_get_order()
        context["cv_order_choices"] = self.cv_get_order_choices()
        context["cv_order_current"] = current or ""
        context["cv_order_dir"] = direction
        context["cv_order_param"] = self.cv_order_param
        context["cv_order_dir_param"] = self.cv_order_dir_param
        # all current GET params except order/dir/page, for the toolbar's hidden inputs
        preserved = []
        skip = {self.cv_order_param, self.cv_order_dir_param, "page"}
        for key in self.request.GET:
            if key in skip:
                continue
            for value in self.request.GET.getlist(key):
                preserved.append({"name": key, "value": value})
        context["cv_order_preserved_params"] = preserved
        return context
```

- [ ] **Step 4: Create the toolbar template**

Create `src/crud_views/templates/crud_views/snippets/card_order.html`:

```html
{% load i18n %}
{% if view.cv_order_fields %}
<form method="get" id="cv-card-order-form" class="d-flex align-items-center gap-2 mb-3">
    <label class="mb-0 me-1" for="cv-order-select">{% translate "Order by" %}</label>
    <select name="{{ cv_order_param }}" id="cv-order-select" class="form-select form-select-sm w-auto">
        {% for choice in cv_order_choices %}
            <option value="{{ choice.name }}"{% if choice.selected %} selected{% endif %}>{{ choice.label }}</option>
        {% endfor %}
    </select>
    <div class="btn-group btn-group-sm" role="group" aria-label="{% translate 'Sort direction' %}">
        <button type="submit" name="{{ cv_order_dir_param }}" value="asc"
                class="btn btn-outline-secondary{% if cv_order_dir == 'asc' %} active{% endif %}"
                title="{% translate 'Ascending' %}">
            <i class="fa-solid fa-arrow-up-short-wide"></i>
        </button>
        <button type="submit" name="{{ cv_order_dir_param }}" value="desc"
                class="btn btn-outline-secondary{% if cv_order_dir == 'desc' %} active{% endif %}"
                title="{% translate 'Descending' %}">
            <i class="fa-solid fa-arrow-down-wide-short"></i>
        </button>
    </div>
    {% for param in cv_order_preserved_params %}
        <input type="hidden" name="{{ param.name }}" value="{{ param.value }}">
    {% endfor %}
</form>
{% endif %}
```

> Direction buttons are the submit action (CSP-safe, no inline JS): pick a field, then
> click ↑/↓ to apply. Preserved hidden inputs carry the active filter so ordering does
> not drop it.

- [ ] **Step 5: Render the toolbar in the card content template**

Edit `src/crud_views/templates/crud_views/view_card.content.html` to include the toolbar
at the top:

```html
{% load crud_views %}

{% include "crud_views/snippets/card_order.html" %}

<div class="row">
    {% for object in object_list %}
        <div class="{{ view.cv_card_container_class }}">
            {% cv_card object %}
        </div>
        {% empty %}
        <div class="col-12">
            <p class="text-muted">No items found.</p>
        </div>
    {% endfor %}
</div>
```

- [ ] **Step 6: Run the toolbar tests**

Run: `cd tests && pytest test1/test_card_order.py -k toolbar -v`
Expected: PASS (3 passed).

- [ ] **Step 7: Run the full card test files**

Run: `cd tests && pytest test1/test_card.py test1/test_card_order.py test1/test_guardian_card.py -q`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/views/mixins.py \
        src/crud_views/templates/crud_views/snippets/card_order.html \
        src/crud_views/templates/crud_views/view_card.content.html \
        tests/test1/test_card_order.py
git commit -m "feat(card): render order-by combo + direction toggle toolbar"
```

---

## Task 3: Pagination snippet + `{% cv_pagination %}` tag

**Files:**
- Create: `src/crud_views/templates/crud_views/snippets/pagination.html`
- Modify: `src/crud_views/templatetags/crud_views.py`
- Modify: `src/crud_views/templates/crud_views/view_card.content.html`
- Test: `tests/test1/test_card_order.py`

- [ ] **Step 1: Write the failing pagination tests**

Append to `tests/test1/test_card_order.py`:

```python
@pytest.mark.django_db
def test_card_pagination_limits_cards(client_publisher_order, publishers):
    # 3 publishers, paginate_by=2 -> page 1 shows 2 cards
    response = client_publisher_order.get("/publisher_order/card/?page=1")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect(".card.mb-3")) == 2
    assert len(doc.cssselect("nav .pagination")) == 1


@pytest.mark.django_db
def test_card_pagination_second_page(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?page=2")
    doc = html.fromstring(response.content)
    assert len(doc.cssselect(".card.mb-3")) == 1  # 3rd item


@pytest.mark.django_db
def test_card_pagination_links_preserve_order_and_filter(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc")
    doc = html.fromstring(response.content)
    hrefs = [a.get("href") for a in doc.cssselect("nav .pagination a.page-link")]
    assert hrefs, "expected page links"
    # every page link keeps order + dir and never duplicates page
    for href in hrefs:
        assert "order=name" in href
        assert "dir=desc" in href
        assert href.count("page=") == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tests && pytest test1/test_card_order.py -k pagination -v`
Expected: FAIL — no `.pagination` nav rendered.

- [ ] **Step 3: Add the `cv_pagination` inclusion tag**

In `src/crud_views/templatetags/crud_views.py`, add this tag (place it near the other
inclusion tags, e.g. after `cv_render_filter`):

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/snippets/pagination.html", takes_context=True)
def cv_pagination(context):
    request = context.get("request")
    params = request.GET.copy() if request is not None else {}
    if hasattr(params, "pop"):
        params.pop("page", None)
    base_qs = params.urlencode() if hasattr(params, "urlencode") else ""
    return {
        "page_obj": context.get("page_obj"),
        "paginator": context.get("paginator"),
        "is_paginated": context.get("is_paginated", False),
        "base_qs": base_qs,
    }
```

- [ ] **Step 4: Create the pagination snippet**

Create `src/crud_views/templates/crud_views/snippets/pagination.html`:

```html
{% if is_paginated %}
<nav aria-label="pagination" class="mt-3">
    <ul class="pagination justify-content-center">
        {% if page_obj.has_previous %}
            <li class="page-item">
                <a class="page-link" href="?{% if base_qs %}{{ base_qs }}&amp;{% endif %}page={{ page_obj.previous_page_number }}">&laquo;</a>
            </li>
        {% else %}
            <li class="page-item disabled"><span class="page-link">&laquo;</span></li>
        {% endif %}
        {% for num in paginator.page_range %}
            {% if num == page_obj.number %}
                <li class="page-item active"><span class="page-link">{{ num }}</span></li>
            {% else %}
                <li class="page-item">
                    <a class="page-link" href="?{% if base_qs %}{{ base_qs }}&amp;{% endif %}page={{ num }}">{{ num }}</a>
                </li>
            {% endif %}
        {% endfor %}
        {% if page_obj.has_next %}
            <li class="page-item">
                <a class="page-link" href="?{% if base_qs %}{{ base_qs }}&amp;{% endif %}page={{ page_obj.next_page_number }}">&raquo;</a>
            </li>
        {% else %}
            <li class="page-item disabled"><span class="page-link">&raquo;</span></li>
        {% endif %}
    </ul>
</nav>
{% endif %}
```

- [ ] **Step 5: Render pagination in the card content template**

Edit `src/crud_views/templates/crud_views/view_card.content.html` to call the tag below
the grid (final version of the file):

```html
{% load crud_views %}

{% include "crud_views/snippets/card_order.html" %}

<div class="row">
    {% for object in object_list %}
        <div class="{{ view.cv_card_container_class }}">
            {% cv_card object %}
        </div>
        {% empty %}
        <div class="col-12">
            <p class="text-muted">No items found.</p>
        </div>
    {% endfor %}
</div>

{% cv_pagination %}
```

- [ ] **Step 6: Run pagination tests**

Run: `cd tests && pytest test1/test_card_order.py -k pagination -v`
Expected: PASS (3 passed).

> Note: `lxml` decodes `&amp;` in `href` back to `&`, so the `in` assertions on
> `order=name` / `dir=desc` hold.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py \
        src/crud_views/templates/crud_views/snippets/pagination.html \
        src/crud_views/templates/crud_views/view_card.content.html \
        tests/test1/test_card_order.py
git commit -m "feat(card): add pagination controls preserving filter + order"
```

---

## Task 4: Filter ⇄ order coexistence + persistence

**Files:**
- Modify: `src/crud_views/lib/views/list.py` (`ListViewFilterFormHelper`)
- Modify: `src/crud_views/lib/views/mixins.py` (`ListViewTableFilterMixin.get` reset branch)
- Test: `tests/test1/test_card_order.py`

- [ ] **Step 1: Write the failing coexistence/persistence tests**

Append to `tests/test1/test_card_order.py`:

```python
@pytest.mark.django_db
def test_filter_form_carries_active_order_as_hidden(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?order=name&dir=desc&name=a")
    doc = html.fromstring(response.content)
    hidden = {i.get("name"): i.get("value") for i in doc.cssselect("form#filter-form input[type=hidden]")}
    assert hidden.get("order") == "name"
    assert hidden.get("dir") == "desc"


@pytest.mark.django_db
def test_order_toolbar_carries_active_filter_as_hidden(client_publisher_order, publishers):
    response = client_publisher_order.get("/publisher_order/card/?name=Alp")
    doc = html.fromstring(response.content)
    hidden = {i.get("name"): i.get("value") for i in doc.cssselect("#cv-card-order-form input[type=hidden]")}
    assert hidden.get("name") == "Alp"


@pytest.mark.django_db
def test_reset_filter_preserves_order(client_publisher_order, publishers):
    response = client_publisher_order.get(
        "/publisher_order/card/?reset_filter=true&order=name&dir=desc", follow=False
    )
    assert response.status_code == 302
    assert "order=name" in response.url
    assert "dir=desc" in response.url
    assert "reset_filter" not in response.url
```

> The filter form has `id="filter-form"` (see `crud_views/tags/list_filter.html`).
> Filter persistence is on by default (`cv_filter_persistence`), so the reset branch runs.

- [ ] **Step 2: Run to verify failure**

Run: `cd tests && pytest test1/test_card_order.py -k "carries or reset" -v`
Expected: FAIL — filter form has no hidden `order`/`dir`; reset URL drops `order`/`dir`.

- [ ] **Step 3: Extend `ListViewFilterFormHelper` to carry order + dir**

In `src/crud_views/lib/views/list.py`, update the `__init__` of `ListViewFilterFormHelper`
(currently it adds a hidden `sort`). Replace the hidden-field block:

```python
    def __init__(self, view, request, form=None):
        super().__init__(form)

        self.view = view
        # add filter control buttons
        self.add_input(
            layout.Submit("submit", _("Apply Filter"), css_id="filter-button"),
        )
        self.add_input(
            layout.Reset(
                "reset",
                _("Reset Filter"),
                css_id="filter-button-reset",
                css_class=crud_views_settings.filter_reset_button_css_class,
            )
        )

        # add hidden fields with control values so a filter submit does not
        # drop the active table sort (ListView) or card order (CardView)
        sort = request.GET.get("sort") or ""
        self.add_input(layout.Hidden("sort", sort))

        order_param = getattr(view, "cv_order_param", "order")
        dir_param = getattr(view, "cv_order_dir_param", "dir")
        order = request.GET.get(order_param) or ""
        direction = request.GET.get(dir_param) or ""
        if order:
            self.add_input(layout.Hidden(order_param, order))
        if direction:
            self.add_input(layout.Hidden(dir_param, direction))
```

- [ ] **Step 4: Extend the reset branch to preserve order + dir**

In `src/crud_views/lib/views/mixins.py`, add `urlencode` to the existing
`from urllib.parse import parse_qs` import:

```python
from urllib.parse import parse_qs, urlencode
```

Then in `ListViewTableFilterMixin.get`, replace the `reset_filter` block (the part that
currently rebuilds `url` preserving only `sort`):

```python
            reset_filter = qs.get("reset_filter", ["false"])[0] == "true"
            if reset_filter:
                try:
                    del sd[self.cv_session_key_querystring]
                except KeyError:
                    pass
                url = self.request.path
                keep = {}
                order_param = getattr(self, "cv_order_param", "order")
                dir_param = getattr(self, "cv_order_dir_param", "dir")
                for key in ("sort", order_param, dir_param):
                    value = qs.get(key, [None])[0]
                    if value:
                        keep[key] = value
                if keep:
                    url += "?" + urlencode(keep)
                return HttpResponseRedirect(url)
```

> Verify the current import line is `from urllib.parse import parse_qs` before editing; if
> it imports differently, add `urlencode` alongside whatever is there.

- [ ] **Step 5: Run coexistence/persistence tests**

Run: `cd tests && pytest test1/test_card_order.py -k "carries or reset" -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Run full card + list suites for regressions**

Run: `cd tests && pytest test1/test_card.py test1/test_card_order.py test1/test_guardian_card.py test1/test_crud.py -q`
Expected: all pass (the `ListView` filter form still works; `sort` still preserved).

- [ ] **Step 7: Commit**

```bash
git add src/crud_views/lib/views/list.py src/crud_views/lib/views/mixins.py \
        tests/test1/test_card_order.py
git commit -m "feat(card): keep filter and order in sync across submits, paging, and reset"
```

---

## Task 5: Update the bootstrap5 example app

**Files:**
- Modify: `examples/bootstrap5/app/views/book.py`

- [ ] **Step 1: Check the example Book model for orderable fields**

Run: `grep -n "class Book\|= models\." examples/bootstrap5/app/models.py`
Expected: confirm `Book` has `title` and `price` fields (the example form already uses both).

- [ ] **Step 2: Add ordering + paging to `BookCardListView`**

In `examples/bootstrap5/app/views/book.py`, update the `BookCardListView` class to add the
new attributes (keep the existing filter and card actions):

```python
class BookCardListView(ListViewTableFilterMixin, GuardianCardListViewPermissionRequired):
    cv_viewset = cv_book
    cv_path = ""
    filterset_class = BookFilter
    formhelper_class = BookFilterFormHelper
    cv_order_fields = ["title", ("price", "Price")]
    cv_order_default = "title"
    paginate_by = 6
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(child_name="book_review", child_key="card", label="Reviews"),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]
```

- [ ] **Step 3: Verify the example app boots and the card view renders**

Run:
```bash
cd examples/bootstrap5 && python manage.py check
```
Expected: `System check identified no issues`.

> If a logged-in manual smoke test is desired, the maintainer can run the dev server and
> visit a book card page; not required for this task.

- [ ] **Step 4: Commit**

```bash
git add examples/bootstrap5/app/views/book.py
git commit -m "docs(example): demonstrate card ordering + paging on BookCardListView"
```

---

## Task 6: Update documentation

**Files:**
- Modify: `docs/reference/card-list-view.md`

- [ ] **Step 1: Add an "Ordering" section**

In `docs/reference/card-list-view.md`, after the existing "Filter Integration" section
(around line 125), add:

````markdown
## Ordering

Declare orderable fields with `cv_order_fields`. The card view then renders an
"Order by" combo plus an ascending/descending toggle above the grid.

```python
from crud_views.lib.views import CardListViewPermissionRequired

class BookCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_book
    cv_order_fields = ["title", ("price", "Price")]  # str or (name, label)
    cv_order_default = "title"                        # leading "-" => descending
    cv_card_actions = [...]
```

| Attribute | Type | Default | Description |
|---|---|---|---|
| `cv_order_fields` | `list[str \| tuple[str, str]]` | `[]` | Orderable fields. A string uses the model field's verbose name as the label; a `(name, label)` tuple sets an explicit label. The combo is hidden when empty. |
| `cv_order_default` | `str \| None` | `None` | Ordering applied when no `order` parameter is present. Leading `-` means descending (e.g. `"-created"`). |
| `cv_order_param` | `str` | `"order"` | GET parameter name for the field. Change it if a model field is literally named `order`. |
| `cv_order_dir_param` | `str` | `"dir"` | GET parameter name for the direction (`asc`/`desc`). |

The selected field is **whitelisted** against `cv_order_fields`, so an arbitrary
`?order=` value can never reach `order_by()`. To apply a sort, pick a field and click
the ↑ or ↓ button.

## Paging

Set Django's `paginate_by` to enable pagination. A Bootstrap pagination control renders
below the grid; its links preserve the active filter and order.

```python
class BookCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_book
    paginate_by = 12
    cv_card_actions = [...]
```

## Filter, Order & Paging Coexistence

Filter, order, and page all live in the URL query string and never clobber each other:

- The order toolbar carries the active filter as hidden inputs.
- The filter form carries the active order/direction as hidden inputs.
- Pagination links carry both the filter and the order.

When `cv_filter_persistence` is enabled (the default), the whole query string — filter
**and** order — is stored in the session and restored on the next visit. Resetting the
filter keeps the active order.
````

- [ ] **Step 2: Verify docs build (optional but recommended)**

Run: `python -m mkdocs build -f mkdocs.yml -q` (or `task docs` and visit the page).
Expected: no build errors.

- [ ] **Step 3: Commit**

```bash
git add docs/reference/card-list-view.md
git commit -m "docs: document card ordering, paging, and coexistence"
```

---

## Task 7: Update the inline skill

**Files:**
- Modify: `skills/django-crud-views/SKILL.md`
- Modify: `skills/django-crud-views/references/api-reference.md`

- [ ] **Step 1: Locate the card-view section in the skill**

Run: `grep -n -i "card" skills/django-crud-views/SKILL.md skills/django-crud-views/references/api-reference.md`
Expected: find the existing CardListView mention(s) to extend.

- [ ] **Step 2: Document the new attributes in the API reference**

In `skills/django-crud-views/references/api-reference.md`, add to the CardListView
documentation (mirror the existing attribute-table style in that file):

```markdown
#### CardListView ordering & paging

- `cv_order_fields: list[str | tuple[str, str]]` — orderable fields; renders an
  "Order by" combo + asc/desc toggle. String = field name (label from verbose_name);
  tuple = `(name, label)`. The chosen field is whitelisted (no `order_by` injection).
- `cv_order_default: str | None` — default ordering when no `order` param; leading `-`
  = descending.
- `cv_order_param` / `cv_order_dir_param` — GET param names (default `"order"` / `"dir"`).
- `paginate_by: int | None` — Django pagination; renders a pagination nav whose links
  preserve the active filter + order.

Filter (`ListViewTableFilterMixin`), order, and page never override each other and are
persisted together via `cv_filter_persistence`.
```

- [ ] **Step 3: Add a one-line pointer in SKILL.md**

In `skills/django-crud-views/SKILL.md`, in the section that lists card-view capabilities,
add a sentence:

```markdown
Card views support ordering (`cv_order_fields` + direction toggle), Django pagination
(`paginate_by`), and django-filter filtering — all coexisting and session-persistable.
See `references/api-reference.md` for attributes.
```

> Match the surrounding heading/bullet style of the actual file; adjust wording to fit.

- [ ] **Step 4: Commit**

```bash
git add skills/django-crud-views/SKILL.md skills/django-crud-views/references/api-reference.md
git commit -m "docs(skill): document card ordering, paging, and filter coexistence"
```

---

## Task 8: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the whole test suite directly**

Run: `cd tests && pytest -q`
Expected: all tests pass (including the new `test_card_order.py`).

- [ ] **Step 2: Lint and format**

Run:
```bash
task check
task format
```
Expected: ruff reports no remaining issues; formatting clean. If `task format` changes
files, review and amend.

- [ ] **Step 3: Run the nox matrix (if environment supports it)**

Run: `task test`
Expected: green across the Python × Django matrix. If the full matrix is unavailable
locally, note it and rely on CI.

- [ ] **Step 4: Final commit (only if formatting changed files)**

```bash
git add -A
git commit -m "chore: ruff format for card ordering feature"
```

---

## Self-Review notes (author)

- **Spec coverage:** order combo (Task 1–2), direction toggle (Task 2), filter analog
  (reused `ListViewTableFilterMixin`, exercised in Tasks 1/4), paging (Task 3),
  filter⇄order non-clobbering (Task 4), optional persistence (Task 4, reuses
  `cv_filter_persistence`), example app (Task 5), docs (Task 6), skill (Task 7),
  tests (Tasks 1–4). All spec sections map to tasks.
- **Naming consistency:** `cv_order_fields`, `cv_order_default`, `cv_order_param`,
  `cv_order_dir_param`, `cv_get_order`, `cv_get_order_choices`, `cv_order_choices`,
  `cv_order_preserved_params`, `cv_pagination`, `#cv-card-order-form` used consistently
  across tasks and templates.
- **Backward compatibility:** `cv_order_fields=[]` and `paginate_by=None` by default;
  `ListViewFilterFormHelper` only adds hidden `order`/`dir` when present, so `ListView`
  is unaffected.
