# Improve DeleteView Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cascading deletes display and delete protection hooks to `DeleteView`, with Guardian per-object permission support.

**Architecture:** The `DeleteView` gains two opt-in attributes (`cv_show_related_objects`, `cv_link_related_objects`) and a protection hook (`cv_check_delete_protection`). Related object discovery uses Django's `NestedObjects` collector. A `cv_filter_related_objects` method handles permission-based filtering (model-level by default, per-object in the Guardian variant). Templates use a separate included snippet for the related objects tree.

**Tech Stack:** Django (NestedObjects collector from `django.contrib.admin.utils`), django-guardian (for per-object filtering), django-crispy-forms, pytest

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `crud_views/lib/views/delete.py` | Add `cv_show_related_objects`, `cv_link_related_objects`, `cv_get_related_objects()`, `cv_filter_related_objects()`, `cv_check_delete_protection()`, override `get_context_data()` and `cv_form_valid()` |
| Modify | `crud_views/templates/crud_views/view_delete.content.html` | Conditionally include related objects snippet before the form |
| Create | `crud_views/templates/crud_views/snippets/delete/related_objects.html` | Main included template: summary + tree + protected warnings |
| Create | `crud_views/templates/crud_views/snippets/delete/related_objects_tree.html` | Recursive nested tree rendering |
| Modify | `crud_views_guardian/lib/views.py` | Add `GuardianDeleteRelatedObjectsMixin` with per-object `cv_filter_related_objects()` override |
| Create | `tests/test1/test_delete.py` | Unit tests for cascading deletes, protection, permission filtering |
| Create | `tests/test1/test_guardian_delete.py` | Guardian-specific delete tests |
| Modify | `tests/test1/app/models.py` | Add `Contract` model with `on_delete=PROTECT` to Publisher |
| Modify | `tests/test1/app/views.py` | Add test delete view variants with `cv_show_related_objects=True` |
| Modify | `tests/test1/conftest.py` | Add fixtures for new test views and models |
| Modify | `docs/reference/delete_view.md` | Document cascading deletes, delete protection, template customization |
| Modify | `docs/reference/guardian.md` | Document per-object permission filtering on delete |
| Modify | `skills/django-crud-views/references/api-reference.md` | Update DeleteView section with new attributes |

---

## Task 1: Add `Contract` test model with `on_delete=PROTECT`

**Files:**
- Modify: `tests/test1/app/models.py:38-46`

- [ ] **Step 1: Add the Contract model**

Add after the `Book` class (after line 46):

```python
class Contract(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT, related_name="contracts")
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
```

- [ ] **Step 2: Run migrations and verify**

Run: `cd tests && python -c "import django; import tests.test1.conftest; django.setup(); from django.core.management import call_command; call_command('migrate', '--run-syncdb', verbosity=0); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add tests/test1/app/models.py
git commit -m "test: add Contract model with on_delete=PROTECT for delete tests"
```

---

## Task 2: Core implementation — `cv_get_related_objects` and `cv_filter_related_objects`

**Files:**
- Modify: `crud_views/lib/views/delete.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_delete.py`:

```python
import pytest
from django.test.client import Client

from tests.lib.helper.user import user_viewset_permission


@pytest.mark.django_db
def test_related_objects_not_shown_by_default(client_user_publisher_delete, cv_publisher, publisher_penguin):
    """Default DeleteView does not include related_objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_delete.get(f"/publisher/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" not in response.context


@pytest.mark.django_db
def test_related_objects_shown_when_enabled(client_user_publisher_delete, cv_publisher, publisher_penguin):
    """DeleteView with cv_show_related_objects=True includes related objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Book.objects.create(title="Book B", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" in response.context
    assert "related_summary" in response.context
    summary = response.context["related_summary"]
    assert summary["book"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_delete.py -v`

Expected: FAIL — `publisher_cascade` URL not found and `related_objects` not in context.

- [ ] **Step 3: Add test ViewSet and views for cascade-enabled delete**

Add to `tests/test1/app/views.py` after the `PublisherDeleteView` class (after line 215):

```python
# --- Publisher with cascade delete display (test-only) ---

cv_publisher_cascade = ViewSet(
    model=Publisher,
    name="publisher_cascade",
)


class PublisherCascadeDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_cascade
    cv_show_related_objects = True


class PublisherCascadeListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_cascade
```

Also add `cv_publisher_cascade` to the imports in `tests/test1/project/urls.py`. Check the current urls.py first to match the pattern.

- [ ] **Step 4: Add the URL pattern**

Check the URL config and add the new viewset's urlpatterns. The urls.py includes all ViewSet urlpatterns — add:

```python
from tests.test1.app.views import cv_publisher_cascade

urlpatterns += cv_publisher_cascade.urlpatterns
```

- [ ] **Step 5: Add fixture for `client_user_publisher_delete` reuse**

The `client_user_publisher_delete` fixture grants delete permission on the `cv_publisher` ViewSet. We need a user with delete permission on `cv_publisher_cascade` too. Add to `tests/test1/conftest.py`:

```python
@pytest.fixture
def cv_publisher_cascade():
    from tests.test1.app.views import cv_publisher_cascade as ret

    return ret


@pytest.fixture
def user_publisher_cascade_delete(cv_publisher_cascade):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_publisher_cascade_delete", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")
    return user


@pytest.fixture
def client_user_publisher_cascade_delete(client, user_publisher_cascade_delete) -> Client:
    client.force_login(user_publisher_cascade_delete)
    return client
```

Then update `test_delete.py` to use `client_user_publisher_cascade_delete` instead of `client_user_publisher_delete` for the cascade tests:

```python
@pytest.mark.django_db
def test_related_objects_not_shown_by_default(client_user_publisher_delete, cv_publisher, publisher_penguin):
    """Default DeleteView does not include related_objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_delete.get(f"/publisher/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" not in response.context


@pytest.mark.django_db
def test_related_objects_shown_when_enabled(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """DeleteView with cv_show_related_objects=True includes related objects in context."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Book A", publisher=publisher_penguin)
    Book.objects.create(title="Book B", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    assert "related_objects" in response.context
    assert "related_summary" in response.context
    summary = response.context["related_summary"]
    assert summary["book"] == 2
```

- [ ] **Step 6: Implement the core logic in delete.py**

Replace the entire content of `crud_views/lib/views/delete.py`:

```python
from __future__ import annotations

from typing import NamedTuple

from django.contrib.admin.utils import NestedObjects
from django.db import router
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.views.mixins import CrudViewProcessFormMixin


class RelatedObjects(NamedTuple):
    tree: list
    summary: dict[str, int]
    protected: list


class DeleteView(CrudViewProcessFormMixin, CrudView, generic.DeleteView):
    template_name = "crud_views/view_delete.html"

    cv_key = "delete"
    cv_path = "delete"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.delete_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/delete.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/delete.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/delete.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/delete.html"

    # icons
    cv_icon_action = "fa-regular fa-trash-can"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/delete.html"

    # cascading deletes display
    cv_show_related_objects: bool = False
    cv_link_related_objects: bool = False

    def cv_get_related_objects(self) -> RelatedObjects:
        """Collect all objects that would be cascade-deleted using Django's NestedObjects collector."""
        using = router.db_for_write(self.object._meta.model)
        collector = NestedObjects(using=using)
        collector.collect([self.object])

        # Build summary: {model_verbose_name: count} excluding the object itself
        summary = {}
        for model, instances in collector.data.items():
            if model == type(self.object):
                continue
            name = model._meta.verbose_name
            summary[name] = len(instances)

        # Build nested tree from collector (exclude root object)
        def build_tree(obj):
            children = collector.edges.get(obj, [])
            return [(child, build_tree(child)) for child in children]

        tree = build_tree(self.object)

        return RelatedObjects(
            tree=tree,
            summary=summary,
            protected=list(collector.protected),
        )

    def cv_filter_related_objects(self, user, related: RelatedObjects) -> RelatedObjects:
        """Filter related objects based on user's model-level view permissions.

        Objects the user can view: kept as-is.
        Objects the user cannot view: replaced with None (template shows counts).
        """
        if not related.tree:
            return related

        def has_view_perm(model):
            opts = model._meta
            perm = f"{opts.app_label}.view_{opts.model_name}"
            return user.has_perm(perm)

        perm_cache = {}

        def filter_tree(tree):
            filtered = []
            for obj, children in tree:
                model = type(obj)
                if model not in perm_cache:
                    perm_cache[model] = has_view_perm(model)
                if perm_cache[model]:
                    filtered.append((obj, filter_tree(children)))
                else:
                    filtered.append((None, filter_tree(children)))
            return filtered

        return RelatedObjects(
            tree=filter_tree(related.tree),
            summary=related.summary,
            protected=related.protected,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.cv_show_related_objects:
            related = self.cv_get_related_objects()
            related = self.cv_filter_related_objects(self.request.user, related)
            context["related_objects"] = related.tree
            context["related_summary"] = related.summary
            context["protected_objects"] = related.protected
        return context

    def cv_check_delete_protection(self) -> list[str]:
        """Override to add custom business logic that prevents deletion.

        Return a list of error message strings. Empty list means deletion is allowed.
        """
        return []

    def cv_form_valid(self, context: dict):
        """Handle valid form, check protection, then delete the object."""
        errors = self.cv_check_delete_protection()
        if errors:
            form = context["form"]
            for error in errors:
                form.add_error(None, error)
            return
        self.object.delete()


class DeleteViewPermissionRequired(CrudViewPermissionRequiredMixin, DeleteView):
    cv_permission = "delete"
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_delete.py -v`

Expected: Both tests PASS.

- [ ] **Step 8: Run full test suite to check for regressions**

Run: `cd tests && pytest test1/ -v`

Expected: All existing tests still pass.

- [ ] **Step 9: Commit**

```bash
git add crud_views/lib/views/delete.py tests/test1/test_delete.py tests/test1/app/views.py tests/test1/conftest.py tests/test1/project/urls.py
git commit -m "feat: add cascading deletes display and delete protection to DeleteView"
```

---

## Task 3: Fix `cv_form_valid` to abort the redirect when protection errors occur

The `CrudViewProcessFormMixin.post()` method calls `cv_form_valid()` then unconditionally calls `cv_form_valid_hook()` and `cv_form_valid_redirect()`. When `cv_check_delete_protection()` returns errors, we need to abort and re-render the form instead.

**Files:**
- Modify: `crud_views/lib/views/delete.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_delete_protection_view_hook(client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin):
    """cv_check_delete_protection returning errors prevents deletion."""
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.post(
        f"/publisher_protected/{pk}/delete/", {"confirm": True}
    )
    assert response.status_code == 200  # re-renders form, not 302 redirect
    from tests.test1.app.models import Publisher

    assert Publisher.objects.filter(pk=pk).exists()
    assert "Cannot delete" in response.content.decode()
```

- [ ] **Step 2: Add the protected delete view variant**

Add to `tests/test1/app/views.py`:

```python
cv_publisher_protected = ViewSet(
    model=Publisher,
    name="publisher_protected",
)


class PublisherProtectedDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_protected
    cv_show_related_objects = True

    def cv_check_delete_protection(self) -> list[str]:
        return ["Cannot delete this publisher."]


class PublisherProtectedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_protected
```

Add URL pattern and fixtures (same pattern as Task 2).

- [ ] **Step 3: Override `post()` in DeleteView to handle protection errors**

The issue is that `CrudViewProcessFormMixin.post()` assumes `cv_form_valid()` always succeeds. We need DeleteView to override the flow. Update `DeleteView` in `crud_views/lib/views/delete.py`:

```python
    def post(self, request, *args, **kwargs):
        """Override to handle delete protection errors."""
        try:
            self.object = self.get_object()
        except AttributeError:
            self.object = None

        context = self.get_context_data(**kwargs)
        self.cv_post_hook(context)
        if self.cv_form_is_valid(context):
            protection_errors = self.cv_check_delete_protection()
            if protection_errors:
                form = context["form"]
                for error in protection_errors:
                    form.add_error(None, error)
                return self.render_to_response(context)
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            return self.cv_form_valid_redirect(context)
        else:
            self.cv_form_invalid_hook(context)
            return self.cv_form_invalid(context)

    def cv_form_valid(self, context: dict):
        """Handle valid form, delete the object."""
        self.object.delete()
```

This moves `cv_check_delete_protection()` out of `cv_form_valid()` and into the `post()` override, so we can return a response before the redirect happens.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_delete.py -v`

Expected: All tests PASS including the new protection test.

- [ ] **Step 5: Run full test suite**

Run: `cd tests && pytest test1/ -v`

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add crud_views/lib/views/delete.py tests/test1/test_delete.py tests/test1/app/views.py tests/test1/conftest.py tests/test1/project/urls.py
git commit -m "feat: override post() in DeleteView to properly handle protection errors"
```

---

## Task 4: Templates for related objects display

**Files:**
- Create: `crud_views/templates/crud_views/snippets/delete/related_objects.html`
- Create: `crud_views/templates/crud_views/snippets/delete/related_objects_tree.html`
- Modify: `crud_views/templates/crud_views/view_delete.content.html`

- [ ] **Step 1: Write the failing test**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_related_objects_rendered_in_template(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """Related objects are rendered in the delete page HTML."""
    from tests.test1.app.models import Book

    Book.objects.create(title="Hitchhiker's Guide", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    content = response.content.decode()
    assert "Hitchhiker" in content
    assert "book" in content.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_delete.py::test_related_objects_rendered_in_template -v`

Expected: FAIL — template doesn't render related objects yet.

- [ ] **Step 3: Create the recursive tree template**

Create `crud_views/templates/crud_views/snippets/delete/related_objects_tree.html` (tuple format — Task 9 will refactor to dict format when adding linking):

```html
<ul>
{% for obj, children in tree %}
    <li>
        {% if obj is None %}
            <em>(restricted)</em>
        {% else %}
            {{ obj }}
        {% endif %}
        {% if children %}
            {% include "crud_views/snippets/delete/related_objects_tree.html" with tree=children %}
        {% endif %}
    </li>
{% endfor %}
</ul>
```

- [ ] **Step 4: Create the main related objects template**

Create `crud_views/templates/crud_views/snippets/delete/related_objects.html`:

```html
{% if related_summary %}
<div class="cv-related-objects mb-3">
    <div class="alert alert-warning">
        <strong>The following related objects will also be deleted:</strong>
        <ul class="mb-0">
        {% for name, count in related_summary.items %}
            <li>{{ count }} {{ name }}{{ count|pluralize }}</li>
        {% endfor %}
        </ul>
    </div>

    {% if related_objects %}
        {% include "crud_views/snippets/delete/related_objects_tree.html" with tree=related_objects %}
    {% endif %}

    {% if protected_objects %}
    <div class="alert alert-danger">
        <strong>Deletion is blocked by protected relationships:</strong>
        <ul class="mb-0">
        {% for obj in protected_objects %}
            <li>{{ obj }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
</div>
{% endif %}
```

- [ ] **Step 5: Update the delete content template**

Replace `crud_views/templates/crud_views/view_delete.content.html`:

```html
{% load crud_views %}

{% if related_summary %}
    {% include "crud_views/snippets/delete/related_objects.html" %}
{% endif %}

<form class="cv-form" method="post" novalidate>
    {% csrf_token %}

    {{ form.non_form_errors }}

    {% cv_render_form %}
</form>
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_delete.py -v`

Expected: All tests pass including the template rendering test.

- [ ] **Step 7: Run full test suite**

Run: `cd tests && pytest test1/ -v`

Expected: All tests pass.

- [ ] **Step 8: Commit**

```bash
git add crud_views/templates/crud_views/snippets/delete/related_objects.html crud_views/templates/crud_views/snippets/delete/related_objects_tree.html crud_views/templates/crud_views/view_delete.content.html tests/test1/test_delete.py
git commit -m "feat: add templates for cascading deletes display"
```

---

## Task 5: Permission filtering tests

**Files:**
- Modify: `tests/test1/test_delete.py`

- [ ] **Step 1: Write the permission filtering test**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_permission_filtering_hides_restricted_objects(cv_publisher_cascade, publisher_penguin):
    """User without view permission on Book sees counts, not individual objects."""
    from django.contrib.auth.models import User
    from tests.test1.app.models import Book

    Book.objects.create(title="Secret Book A", publisher=publisher_penguin)
    Book.objects.create(title="Secret Book B", publisher=publisher_penguin)

    # Create user with delete perm on publisher_cascade but NO view perm on Book
    user = User.objects.create_user(username="user_no_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    # Should NOT show individual book titles
    assert "Secret Book A" not in content
    assert "Secret Book B" not in content
    # Should still show the summary count
    assert "2" in content
    assert "book" in content.lower()
```

- [ ] **Step 2: Write the test for user WITH view permission**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_permission_filtering_shows_permitted_objects(cv_publisher_cascade, publisher_penguin):
    """User with view permission on Book sees individual object details."""
    from django.contrib.auth.models import User
    from tests.test1.app.models import Book

    Book.objects.create(title="Visible Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_with_book_view", password="password")
    user_viewset_permission(user, cv_publisher_cascade, "delete")
    # Also grant view permission on Book model
    from django.contrib.auth.models import Permission

    perm = Permission.objects.get(codename="view_book")
    user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Visible Book" in content
```

- [ ] **Step 3: Run tests**

Run: `cd tests && pytest test1/test_delete.py -v`

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test1/test_delete.py
git commit -m "test: add permission filtering tests for cascading deletes"
```

---

## Task 6: Protected objects test

**Files:**
- Modify: `tests/test1/test_delete.py`
- Modify: `tests/test1/conftest.py`

- [ ] **Step 1: Write the protected objects test**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_protected_objects_shown_as_warning(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """Protected objects (on_delete=PROTECT) are shown as a warning."""
    from tests.test1.app.models import Contract

    Contract.objects.create(title="Publishing Contract", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    context = response.context
    assert len(context["protected_objects"]) > 0
    content = response.content.decode()
    assert "protected" in content.lower() or "blocked" in content.lower()
```

- [ ] **Step 2: Run test**

Run: `cd tests && pytest test1/test_delete.py::test_protected_objects_shown_as_warning -v`

Expected: PASS (the collector should already detect PROTECT relations).

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_delete.py
git commit -m "test: add protected objects display test"
```

---

## Task 7: Delete protection — form `clean()` test

**Files:**
- Modify: `tests/test1/test_delete.py`
- Modify: `tests/test1/app/views.py`

- [ ] **Step 1: Write the form clean test**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_delete_protection_form_clean(publisher_penguin):
    """Form clean() raising ValidationError prevents deletion."""
    from django.contrib.auth.models import User
    from tests.test1.app.models import Publisher

    user = User.objects.create_user(username="user_form_clean_test", password="password")
    from tests.test1.app.views import cv_publisher_form_protected

    user_viewset_permission(user, cv_publisher_form_protected, "delete")

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.post(f"/publisher_form_protected/{pk}/delete/", {"confirm": True})
    assert response.status_code == 200  # re-renders, not redirect
    assert Publisher.objects.filter(pk=pk).exists()
    assert "Form-level" in response.content.decode()
```

- [ ] **Step 2: Add the form-protected delete view variant**

Add to `tests/test1/app/views.py`:

```python
from django.core.exceptions import ValidationError


class ProtectedDeleteForm(CrispyDeleteForm):
    def clean(self):
        cleaned_data = super().clean()
        raise ValidationError("Form-level protection: cannot delete.")
        return cleaned_data


cv_publisher_form_protected = ViewSet(
    model=Publisher,
    name="publisher_form_protected",
)


class PublisherFormProtectedDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = ProtectedDeleteForm
    cv_viewset = cv_publisher_form_protected


class PublisherFormProtectedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_form_protected
```

Add URL pattern and fixtures (same pattern as before).

- [ ] **Step 3: Run test**

Run: `cd tests && pytest test1/test_delete.py::test_delete_protection_form_clean -v`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test1/test_delete.py tests/test1/app/views.py tests/test1/conftest.py tests/test1/project/urls.py
git commit -m "test: add form clean() delete protection test"
```

---

## Task 8: Successful cascade delete test

**Files:**
- Modify: `tests/test1/test_delete.py`

- [ ] **Step 1: Write the cascade delete test**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_successful_cascade_delete(
    client_user_publisher_cascade_delete, cv_publisher_cascade, publisher_penguin
):
    """With cv_show_related_objects=True, POST still deletes object and cascaded relations."""
    from tests.test1.app.models import Book, Publisher

    book = Book.objects.create(title="Doomed Book", publisher=publisher_penguin)
    pk = publisher_penguin.pk
    response = client_user_publisher_cascade_delete.post(
        f"/publisher_cascade/{pk}/delete/", {"confirm": True}
    )
    assert response.status_code == 302
    assert not Publisher.objects.filter(pk=pk).exists()
    assert not Book.objects.filter(pk=book.pk).exists()
```

- [ ] **Step 2: Run test**

Run: `cd tests && pytest test1/test_delete.py::test_successful_cascade_delete -v`

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_delete.py
git commit -m "test: add successful cascade delete verification"
```

---

## Task 9: Related objects linking

**Files:**
- Modify: `crud_views/lib/views/delete.py`
- Modify: `crud_views/templates/crud_views/snippets/delete/related_objects_tree.html`
- Modify: `tests/test1/test_delete.py`

- [ ] **Step 1: Write the linking test**

Add to `tests/test1/test_delete.py`:

```python
@pytest.mark.django_db
def test_related_objects_linking(publisher_penguin):
    """With cv_link_related_objects=True, related objects with ViewSets are rendered as links."""
    from django.contrib.auth.models import Permission, User
    from tests.test1.app.models import Book

    book = Book.objects.create(title="Linked Book", publisher=publisher_penguin)

    user = User.objects.create_user(username="user_link_test", password="password")
    from tests.test1.app.views import cv_publisher_linked

    user_viewset_permission(user, cv_publisher_linked, "delete")
    perm = Permission.objects.get(codename="view_book")
    user.user_permissions.add(perm)

    client = Client()
    client.force_login(user)

    pk = publisher_penguin.pk
    response = client.get(f"/publisher_linked/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    # The book should be rendered as a link
    assert "<a " in content
    assert "Linked Book" in content
```

- [ ] **Step 2: Add the linked delete view variant**

Add to `tests/test1/app/views.py`:

```python
cv_publisher_linked = ViewSet(
    model=Publisher,
    name="publisher_linked",
)


class PublisherLinkedDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_linked
    cv_show_related_objects = True
    cv_link_related_objects = True


class PublisherLinkedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_linked
```

Add URL pattern and fixtures.

- [ ] **Step 3: Add new methods to `crud_views/lib/views/delete.py`**

Add the following methods to the `DeleteView` class:

```python
    @staticmethod
    def _walk_tree(tree):
        """Yield all (obj, children) pairs from a nested tree."""
        for obj, children in tree:
            yield obj, children
            yield from DeleteView._walk_tree(children)

    def cv_get_related_object_url(self, obj) -> str | None:
        """Get the detail URL for a related object, if its model has a registered ViewSet with a detail view."""
        from crud_views.lib.viewset import _REGISTRY

        model = type(obj)
        for viewset in _REGISTRY.values():
            if viewset.model == model and viewset.is_view_registered("detail"):
                try:
                    router_name = viewset.get_router_name("detail")
                    kwargs = {viewset.pk_name: obj.pk}
                    if viewset.parent:
                        parent_pk_name = viewset.parent.pk_name
                        parent_attr = viewset.parent.attribute
                        parent_obj = getattr(obj, parent_attr, None)
                        if parent_obj:
                            kwargs[parent_pk_name] = parent_obj.pk
                    from django.urls import reverse

                    return reverse(router_name, kwargs=kwargs)
                except Exception:
                    return None
        return None

    def _build_display_tree(self, tree, urls):
        """Convert tree into template-friendly dict format with URLs resolved."""
        result = []
        for obj, children in tree:
            node = {
                "obj": obj,
                "url": urls.get(id(obj)) if obj is not None else None,
                "children": self._build_display_tree(children, urls),
            }
            result.append(node)
        return result
```

- [ ] **Step 4: Refactor `get_context_data` to use dict-based tree with URLs**

Replace the `get_context_data` method in `DeleteView`:

```python
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.cv_show_related_objects:
            related = self.cv_get_related_objects()
            related = self.cv_filter_related_objects(self.request.user, related)
            context["related_summary"] = related.summary
            context["protected_objects"] = related.protected

            urls = {}
            if self.cv_link_related_objects:
                for obj, children in self._walk_tree(related.tree):
                    if obj is not None:
                        url = self.cv_get_related_object_url(obj)
                        if url:
                            urls[id(obj)] = url

            context["related_objects"] = self._build_display_tree(related.tree, urls)
        return context
```

- [ ] **Step 5: Update both templates to use the dict-based tree format**

Replace `crud_views/templates/crud_views/snippets/delete/related_objects_tree.html`:

```html
<ul>
{% for node in tree %}
    <li>
        {% if node.obj is None %}
            <em>(restricted)</em>
        {% elif node.url %}
            <a href="{{ node.url }}">{{ node.obj }}</a>
        {% else %}
            {{ node.obj }}
        {% endif %}
        {% if node.children %}
            {% include "crud_views/snippets/delete/related_objects_tree.html" with tree=node.children %}
        {% endif %}
    </li>
{% endfor %}
</ul>
```

The main template (`related_objects.html`) does not change — it already passes `related_objects` as `tree`.

- [ ] **Step 6: Update earlier tests to match the dict-based tree format**

Update the context assertions in `test_related_objects_shown_when_enabled` — `related_objects` is now a list of dicts:

```python
    assert "related_objects" in response.context
    related_objects = response.context["related_objects"]
    assert len(related_objects) == 2  # 2 books
    assert related_objects[0]["obj"].title in ("Book A", "Book B")
```

- [ ] **Step 7: Run tests**

Run: `cd tests && pytest test1/test_delete.py -v`

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add crud_views/lib/views/delete.py crud_views/templates/crud_views/snippets/delete/related_objects_tree.html tests/test1/test_delete.py tests/test1/app/views.py tests/test1/conftest.py tests/test1/project/urls.py
git commit -m "feat: add related objects linking support in delete view"
```

---

## Task 10: Guardian per-object permission filtering

**Files:**
- Modify: `crud_views_guardian/lib/views.py`
- Create: `tests/test1/test_guardian_delete.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_guardian_delete.py`:

```python
import pytest
from django.test.client import Client

from tests.lib.helper.guardian import user_guardian_object_perm


@pytest.mark.django_db
def test_guardian_per_object_filtering(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    """Guardian delete view filters related objects by per-object view permission."""
    from tests.test1.app.models import Book

    book_visible = Book.objects.create(title="Visible Book", publisher=publisher_a)
    book_hidden = Book.objects.create(title="Hidden Book", publisher=publisher_a)

    # Grant delete on publisher
    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "delete", publisher_a)
    # Grant view on only one book
    from tests.test1.app.views import cv_guardian_book

    user_guardian_object_perm(user_guardian, cv_guardian_book, "view", book_visible)

    pk = publisher_a.pk
    response = client_guardian.get(f"/guardian_publisher_cascade/{pk}/delete/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Visible Book" in content
    assert "Hidden Book" not in content


@pytest.mark.django_db
def test_guardian_delete_still_works(
    client_guardian, user_guardian, cv_guardian_publisher, publisher_a
):
    """Guardian delete with cv_show_related_objects=True still deletes successfully."""
    from tests.test1.app.models import Publisher

    user_guardian_object_perm(user_guardian, cv_guardian_publisher, "delete", publisher_a)
    pk = publisher_a.pk
    response = client_guardian.post(f"/guardian_publisher_cascade/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert not Publisher.objects.filter(pk=pk).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_guardian_delete.py -v`

Expected: FAIL — `guardian_publisher_cascade` URL not found.

- [ ] **Step 3: Add Guardian cascade delete view variant**

Add to `tests/test1/app/views.py`:

```python
cv_guardian_publisher_cascade = GuardianViewSet(
    model=Publisher,
    name="guardian_publisher_cascade",
    icon_header="fa-regular fa-building",
)


class GuardianPublisherCascadeDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_guardian_publisher_cascade
    cv_show_related_objects = True


class GuardianPublisherCascadeListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_guardian_publisher_cascade
```

Add URL pattern.

- [ ] **Step 4: Implement `GuardianDeleteRelatedObjectsMixin`**

Add to `crud_views_guardian/lib/views.py`:

```python
class GuardianDeleteRelatedObjectsMixin:
    """Override cv_filter_related_objects to use per-object guardian permissions."""

    def cv_filter_related_objects(self, user, related):
        from crud_views.lib.viewset import _REGISTRY
        from guardian.shortcuts import get_objects_for_user

        if not related.tree:
            return related

        # Build a cache of permitted object PKs per model
        permitted_pks = {}

        def get_permitted_pks(model):
            if model not in permitted_pks:
                opts = model._meta
                perm = f"{opts.app_label}.view_{opts.model_name}"
                try:
                    qs = get_objects_for_user(user, perm, klass=model, accept_global_perms=False)
                    permitted_pks[model] = set(qs.values_list("pk", flat=True))
                except Exception:
                    permitted_pks[model] = set()
            return permitted_pks[model]

        def filter_tree(tree):
            filtered = []
            for obj, children in tree:
                model = type(obj)
                pks = get_permitted_pks(model)
                if obj.pk in pks:
                    filtered.append((obj, filter_tree(children)))
                else:
                    filtered.append((None, filter_tree(children)))
            return filtered

        from crud_views.lib.views.delete import RelatedObjects

        return RelatedObjects(
            tree=filter_tree(related.tree),
            summary=related.summary,
            protected=related.protected,
        )
```

Update `GuardianDeleteViewPermissionRequired` to include the mixin:

```python
class GuardianDeleteViewPermissionRequired(
    GuardianDeleteRelatedObjectsMixin,
    GuardianParentPermissionMixin,
    GuardianObjectPermissionMixin,
    DeleteViewPermissionRequired,
):
    pass
```

- [ ] **Step 5: Run tests**

Run: `cd tests && pytest test1/test_guardian_delete.py -v`

Expected: All tests PASS.

- [ ] **Step 6: Run full test suite**

Run: `cd tests && pytest test1/ -v`

Expected: All tests pass — guardian mixin is only active when `cv_show_related_objects=True` (the base `cv_filter_related_objects` is only called from `get_context_data` when that flag is set).

- [ ] **Step 7: Commit**

```bash
git add crud_views_guardian/lib/views.py tests/test1/test_guardian_delete.py tests/test1/app/views.py tests/test1/project/urls.py
git commit -m "feat: add Guardian per-object permission filtering for cascading deletes"
```

---

## Task 11: Documentation updates

**Files:**
- Modify: `docs/reference/delete_view.md`
- Modify: `docs/reference/guardian.md`

- [ ] **Step 1: Update delete_view.md**

Add the following sections after the "Form Processing Hooks" section in `docs/reference/delete_view.md`:

```markdown
## Cascading Deletes Display

Show users what related objects will be deleted when they delete an object (similar to Django Admin).
This feature is opt-in.

```python
class PublisherDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True  # show what will be cascade-deleted
```

When enabled, the delete confirmation page displays:

- A summary of related objects by type and count
- A nested tree of individual related objects
- Warnings for protected relationships (`on_delete=PROTECT`)

### Linking Related Objects

Optionally render related objects as links to their detail views:

```python
class PublisherDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
    cv_link_related_objects = True  # link to detail views when available
```

Links are only rendered for related objects whose model has a registered ViewSet with a `detail` view.

### Permission Filtering

Related objects are filtered based on the current user's permissions:

- Objects the user has `view` permission for: shown with full details
- Objects the user lacks `view` permission for: shown as aggregated counts (e.g., "3 book objects")

This ensures users see the full impact of deletion without leaking details of objects they can't normally access.

### Template Customization

The related objects display uses two overridable templates:

- `crud_views/snippets/delete/related_objects.html` — main container with summary, tree, and warnings
- `crud_views/snippets/delete/related_objects_tree.html` — recursive nested tree of individual objects

Override these in your project's template directory to customize the rendering.

## Delete Protection

Add custom business logic to prevent deletion.

### View Hook

Override `cv_check_delete_protection()` to return error messages:

```python
class PublisherDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher

    def cv_check_delete_protection(self) -> list[str]:
        if self.object.books.filter(is_published=True).exists():
            return ["Cannot delete a publisher with published books."]
        return []
```

When the method returns errors, the form is re-rendered with those errors as non-field errors. The object is not deleted.

### Form Hook

Alternatively, use standard Django form validation:

```python
class ProtectedDeleteForm(CrispyDeleteForm):
    def clean(self):
        cleaned_data = super().clean()
        # custom validation logic
        if some_condition:
            raise ValidationError("Cannot delete.")
        return cleaned_data
```

Both hooks are respected. The execution order is:

1. Form validates (checkbox confirmed, `clean()` passes)
2. View calls `cv_check_delete_protection()`
3. If errors from either, form re-renders with non-field errors
4. If no errors, object is deleted
```

- [ ] **Step 2: Update the Configuration table**

Add to the existing configuration table in `docs/reference/delete_view.md`:

```markdown
| `cv_show_related_objects` | `bool` | `False` | Show cascading deletes display |
| `cv_link_related_objects` | `bool` | `False` | Link related objects to their detail views |
```

- [ ] **Step 3: Update guardian.md**

Add a new section before "Working Example" in `docs/reference/guardian.md`:

```markdown
## Cascading Deletes with Per-Object Permissions

When `cv_show_related_objects = True` on a Guardian delete view, the related objects
list is filtered using per-object `view` permissions instead of model-level permissions:

- Objects the user has per-object `view` permission for: shown with full details
- Objects the user lacks per-object `view` permission for: shown as aggregated counts

```python
class PublisherDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
```

Performance: uses `guardian.shortcuts.get_objects_for_user` for bulk queryset filtering —
one query per related model, not one per object.
```

- [ ] **Step 4: Commit**

```bash
git add docs/reference/delete_view.md docs/reference/guardian.md
git commit -m "docs: document cascading deletes display and delete protection"
```

---

## Task 12: Skill reference update

**Files:**
- Modify: `skills/django-crud-views/references/api-reference.md`

- [ ] **Step 1: Update the DeleteView section**

In `skills/django-crud-views/references/api-reference.md`, replace the DeleteView code block (around line 142-151):

```markdown
### DeleteView / DeleteViewPermissionRequired

```python
from crud_views.lib.views import DeleteViewPermissionRequired
from crud_views.lib.crispy import CrispyDeleteForm

class MyDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_my
    form_class = CrispyDeleteForm
    cv_message = "Deleted »{object}«"
    cv_success_key = "list"
    cv_show_related_objects = True     # opt-in: show cascading deletes
    cv_link_related_objects = False    # opt-in: link to detail views

    def cv_check_delete_protection(self) -> list[str]:
        """Return error messages to prevent deletion. Empty list = allowed."""
        if self.object.has_active_contracts():
            return ["Cannot delete: active contracts exist."]
        return []
```

`CrispyDeleteForm` provides a confirmation checkbox. Set `cv_show_related_objects = True` to display related objects that will be cascade-deleted. Override `cv_check_delete_protection()` for custom business logic.
```

- [ ] **Step 2: Commit**

```bash
git add skills/django-crud-views/references/api-reference.md
git commit -m "docs: update skill API reference with delete view improvements"
```

---

## Task 13: Final integration test and cleanup

**Files:**
- All test files

- [ ] **Step 1: Run the full test suite**

Run: `cd tests && pytest test1/ -v`

Expected: All tests pass.

- [ ] **Step 2: Run linting**

Run: `cd /home/alex/projects/alex/django-crud-views && task check`

Expected: No lint errors.

- [ ] **Step 3: Run formatting**

Run: `cd /home/alex/projects/alex/django-crud-views && task format`

- [ ] **Step 4: Run tests one more time after formatting**

Run: `cd tests && pytest test1/ -v`

Expected: All tests pass.

- [ ] **Step 5: Commit any formatting changes**

```bash
git add -u
git commit -m "style: apply ruff formatting"
```
