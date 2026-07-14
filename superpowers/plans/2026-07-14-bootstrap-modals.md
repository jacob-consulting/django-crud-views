# Bootstrap 5 Modal Views Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Views with `cv_modal = True` open in a Bootstrap 5 modal (fetched partial, in-modal validation, full-page redirect on success) — opt-in, zero behavior change otherwise.

**Architecture:** Same-URL content negotiation via an `X-CV-Modal: true` request header: the view renders a modal partial (reusing the existing `view_*.content.html` body partials) instead of the full page. POST success answers `204` + `X-CV-Redirect` header (client navigates, Django messages untouched); invalid forms re-render the partial with status `422`. A new `modal.js` (vanilla fetch + jQuery delegation, matching `viewset.js` style) drives one shared modal shell rendered by `{% cv_config %}`. No new dependencies.

**Tech Stack:** Django 4.2–6.0, Python 3.12–3.14, Bootstrap 5 (host-provided JS), jQuery (existing requirement), pytest.

**Authoritative spec:** `superpowers/specs/2026-07-14-bootstrap-modals-design.md` (design), `superpowers/specs/2026-07-14-bootstrap-modals-solutions.md` (rationale). Where this plan and the design spec disagree, the spec wins — flag the discrepancy in your commit message.

## Global Constraints

- Phase-1 view types only: `DeleteView`, `DetailView`, `CustomFormView`, `CustomFormNoObjectView`. Create/update are hard-gated by system check E251.
- Header names exactly: request `X-CV-Modal: true`; response `X-CV-Redirect: <url>`; `Vary: X-CV-Modal` on all responses of modal-enabled views.
- Status codes: 200 modal partial (GET), 204 + `X-CV-Redirect` (POST success), 422 (POST invalid / delete protection). Non-modal requests keep today's codes (302/200).
- `cv_modal_size` allowed values exactly: `""`, `"modal-sm"`, `"modal-lg"`, `"modal-xl"`.
- No new runtime dependencies (Python or JS). No JS test infrastructure.
- `crud_views_plain` theme: no changes to its button templates — `cv_modal` degrades to full pages there.
- Ruff: line length 120, double quotes. All `CrudView` attributes use the `cv_` prefix.
- Everything is opt-in: with `cv_modal = False` (default) the whole test suite must pass unchanged.

---

## Hand-Over: What a Fresh Implementer Needs to Know

### The project

`django-crud-views` groups CRUD class-based views into **ViewSets** (`src/crud_views/lib/viewset/__init__.py`). Each view class registers itself via `cv_viewset = my_viewset`; the ViewSet generates `urlpatterns`. `CrudView` (`src/crud_views/lib/view/base.py`) is the base mixin every concrete view (`src/crud_views/lib/views/*.py`) combines with a Django generic CBV, e.g. `class DeleteView(CrudViewProcessFormMixin, CrudView, generic.DeleteView)`. Because `CrudView` precedes the generic CBV in the MRO, methods defined on `CrudView` (e.g. a new `get_template_names`) override the generic implementations, and `super()` reaches them.

### Rendering model (read this before touching templates)

- Full pages: `crud_views/view_delete.html` extends the **host project's** wrapper template (`cv_extends` context var → `CRUD_VIEWS_EXTENDS` setting) and fills `{% block cv_content %}` with an include of `crud_views/view_delete.content.html`. The wrapper renders the chrome (header, context-action buttons, paragraph).
- Theming = template override by name: `crud_views_plain` ships templates with the *same names* under `src/crud_views_plain/templates/crud_views/`; whichever app comes first in `INSTALLED_APPS` wins. Never branch on a theme setting.
- Action buttons: `{% cv_list_action %}` / `{% cv_context_action %}` template tags (`src/crud_views/templatetags/crud_views.py`) call `CrudView.cv_get_context()` (`base.py:346`), which resolves the **target** view class from the ViewSet and merges class attributes from `cv_get_dict()` (`base.py:206`). Anything added to `cv_get_dict()` is visible in `tags/list_action.html` / `tags/context_action.html`.
- POST lifecycle: `CrudViewProcessFormMixin.post()` (`src/crud_views/lib/views/mixins.py:24`) → `cv_form_is_valid` → `cv_form_valid` → `cv_form_valid_hook` (MessageMixin queues the success message here) → `cv_form_valid_redirect` (line 81). `DeleteView.post()` (`src/crud_views/lib/views/delete.py:162`) mirrors this and re-renders with `delete_protection_errors` when `cv_check_delete_protection()` returns errors.
- JS/CSS assets: registered in `CrudViewsSettings.javascript()` / `.css` (`src/crud_views/lib/settings.py:117`), emitted by `{% cv_js %}` / `{% cv_css %}`. `{% cv_config %}` renders a hidden `#cv-config` div with the CSRF token. `viewset.js` binds with `$(document).on(...)` delegation (works for injected DOM).
- System checks: each view class has a `checks()` classmethod yielding `Check` objects (`src/crud_views/lib/check.py`); `CheckExpression(context=cls, id="E2xx", expression=<bool>, msg="...")` yields `Error(id="viewset.E2xx", ...)` when the expression is false. Used IDs: E002, E003, E111, E200–E202, E220, E230–E235, E240–E245. **E250 and E251 are free — this plan uses them.**

### Commands

```bash
cd tests && pytest                          # full suite, quick (in-memory sqlite, settings via conftest pytest_configure)
cd tests && pytest test1/test_modal.py -v   # just this feature
task check                                  # ruff check --fix
task format                                 # ruff format (also runs as pre-commit hook)
task test                                   # full nox matrix (slow; run once at the end)
```

### Test conventions (`tests/test1/`)

- Test models in `tests/test1/app/models.py`: `Author` (UUID pk), `Publisher` (int pk), `Book` (child of Publisher). Test viewsets in `tests/test1/app/views.py`; variant viewsets for feature testing follow the pattern `cv_publisher_protected` etc. (see `views.py:700-740`) and are wired in `tests/test1/app/urls.py`.
- Fixtures in `tests/test1/conftest.py`: `cv_<name>` (viewset), `user_<name>_<perm>` (user with permission via `user_viewset_permission` helper from `tests.lib.helper.user`), `client_user_<name>_<perm>` (logged-in client). Object fixtures: `author_douglas_adams`, `publisher_penguin`.
- Tests hit URLs directly: `client.get(f"/author/{pk}/delete/")`. Send the modal header with Django ≥4.2's kwarg: `client.get(url, headers={"X-CV-Modal": "true"})`.

### Workflow

1. Create a feature branch off `main`: `git checkout -b feat/bootstrap5-modals`.
2. Commit after every task (steps below include commit commands).
3. When all tasks are done: run `cd tests && pytest`, `task check`, `task format`, then open a PR. Project convention: wait for CI, fix ruff findings if CI flags them, squash-merge to `main`, wait for main CI.

### Known gotchas

- `DetailView` is `class DetailView(ObjectDetailMixin, DetailCustomView)` — `ObjectDetailMixin` comes from the third-party `django_object_detail` package and sits **before** `CrudView` in the MRO. If the detail-modal GET test (Task 1) fails because the full page renders, `ObjectDetailMixin` defines its own `get_template_names`; fix by overriding `get_template_names` on `crud_views`' `DetailView` (same body as the `CrudView` one, calling `super()`).
- Defining a `CrudView` subclass **without** `cv_viewset` (as check tests do) is safe — the metaclass only registers classes that set `cv_viewset`.
- Iterating `SomeView.checks()` yields messages beyond the one under test (template checks etc.) — assert membership of the expected ID, not the full list.
- The plain theme also renders `{% cv_config %}` (it does not override that tag template) — the appended modal shell is an empty, contentless div there: harmless, do not special-case it.
- `MessageMixin` on the test delete view uses the default message snippet — in tests assert *a* success message exists, not its exact text.

---

### Task 1: Server core — `cv_modal` attributes, request detection, modal partial rendering

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (attrs ~line 42-70, `cv_get_dict` ~line 206, new methods near `get_context_data` ~line 99)
- Create: `src/crud_views/templates/crud_views/modal/content.html`
- Modify: `src/crud_views/lib/views/delete.py`, `detail.py`, `form.py`, `create.py`, `update.py`, `list.py`, `card.py`, `mixins.py` (one attribute each)
- Modify: `tests/test1/app/views.py`, `tests/test1/app/urls.py`, `tests/test1/conftest.py`
- Test: `tests/test1/test_modal.py` (new)

**Interfaces:**
- Produces: `CrudView.cv_modal: bool = False`, `cv_modal_size: str = ""`, `cv_modal_supported: bool = False` (class attr, `True` only on phase-1 view types), `cv_content_template: str | None`; module function `cv_is_modal_request(request) -> bool` in `crud_views.lib.view.base`; template `crud_views/modal/content.html`; `cv_get_dict()` additionally returns `cv_modal` and `cv_modal_size`. Test viewsets `cv_author_modal` (list/detail/delete/contact) and `cv_publisher_modal_protected` (list/delete) with conftest fixtures `client_user_author_modal`, `client_user_publisher_modal_protected_delete`.
- Consumes: nothing new.

- [ ] **Step 1: Add test viewsets**

Append to `tests/test1/app/views.py` (imports at the top of the file already cover everything used — verify `CharField`, `Column12`, `CustomFormViewPermissionRequired` are imported; the existing `AuthorContactView` around line 202 uses them):

```python
# --- Author Modal (UUID PK, cv_modal=True on delete/detail/custom form) ---

cv_author_modal = ViewSet(
    model=Author,
    name="author_modal",
)


class AuthorModalListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author_modal


class AuthorModalDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author_modal
    cv_modal = True
    cv_property_display = [
        {"title": "Attributes", "properties": ["first_name", "last_name"]},
    ]


class AuthorModalDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author_modal
    cv_modal = True
    cv_modal_size = "modal-lg"


class AuthorModalContactForm(CrispyModelForm):
    submit_label = "Send"
    subject = CharField(label="Subject", required=True)
    body = CharField(label="Body", required=True)

    class Meta:
        model = Author
        fields = ["subject", "body"]

    def get_layout_fields(self):
        return Column12("subject"), Column12("body")


class AuthorModalContactView(MessageMixin, CrispyModelViewMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"
    cv_path = "contact"
    cv_viewset = cv_author_modal
    cv_modal = True
    form_class = AuthorModalContactForm
    cv_icon_action = "fa-solid fa-envelope"
    cv_message_template_code = "Contacted author"
    cv_header_template_code = "Contact"
    cv_paragraph_template_code = "Contact the author"
    cv_action_label_template_code = "Contact"
    cv_action_short_label_template_code = "Contact"


# --- Publisher Modal Protected (INT PK, cv_modal + delete protection) ---

cv_publisher_modal_protected = ViewSet(
    model=Publisher,
    name="publisher_modal_protected",
)


class PublisherModalProtectedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_modal_protected


class PublisherModalProtectedDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_modal_protected
    cv_modal = True

    def cv_check_delete_protection(self) -> list[str]:
        return ["Cannot delete this publisher."]
```

Mirror the attribute set of the existing `AuthorContactView` (~line 202) if `CustomFormView` checks complain about further missing `cv_*` template attributes.

In `tests/test1/app/urls.py` add both viewsets to the import list and append:

```python
urlpatterns += cv_author_modal.urlpatterns
urlpatterns += cv_publisher_modal_protected.urlpatterns
```

In `tests/test1/conftest.py` add (import of `user_viewset_permission` already exists there; if not, copy the import from `tests/test1/test_delete.py`):

```python
@pytest.fixture
def cv_author_modal():
    from tests.test1.app.views import cv_author_modal as ret

    return ret


@pytest.fixture
def user_author_modal(cv_author_modal):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_modal", password="password")
    user_viewset_permission(user, cv_author_modal, "view")
    user_viewset_permission(user, cv_author_modal, "delete")
    return user


@pytest.fixture
def client_user_author_modal(client, user_author_modal) -> Client:
    client.force_login(user_author_modal)
    return client


@pytest.fixture
def cv_publisher_modal_protected():
    from tests.test1.app.views import cv_publisher_modal_protected as ret

    return ret


@pytest.fixture
def user_publisher_modal_protected_delete(cv_publisher_modal_protected):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_publisher_modal_protected_delete", password="password")
    user_viewset_permission(user, cv_publisher_modal_protected, "delete")
    return user


@pytest.fixture
def client_user_publisher_modal_protected_delete(client, user_publisher_modal_protected_delete) -> Client:
    client.force_login(user_publisher_modal_protected_delete)
    return client
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test1/test_modal.py`:

```python
"""
Tests for cv_modal: Bootstrap 5 modal rendering via X-CV-Modal content negotiation.
Spec: superpowers/specs/2026-07-14-bootstrap-modals-design.md
"""

import pytest
from django.test.client import Client

MODAL_HEADERS = {"X-CV-Modal": "true"}


def template_names(response) -> list:
    return [t.name for t in response.templates if t.name]


# ---------------------------------------------------------------------------
# GET rendering (Task 1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_without_header_renders_full_page(client_user_author_modal: Client, author_douglas_adams):
    """No X-CV-Modal header -> unchanged full page (deep links, no-JS)."""
    response = client_user_author_modal.get(f"/author_modal/{author_douglas_adams.pk}/delete/")
    assert response.status_code == 200
    assert "crud_views/view_delete.html" in template_names(response)
    assert "crud_views/modal/content.html" not in template_names(response)


@pytest.mark.django_db
def test_get_with_header_renders_modal_partial(client_user_author_modal: Client, author_douglas_adams):
    """X-CV-Modal: true on a cv_modal view -> modal partial, no page chrome."""
    response = client_user_author_modal.get(
        f"/author_modal/{author_douglas_adams.pk}/delete/", headers=MODAL_HEADERS
    )
    assert response.status_code == 200
    names = template_names(response)
    assert "crud_views/modal/content.html" in names
    assert "crud_views/view_delete.html" not in names
    content = response.content.decode()
    assert "modal-header" in content
    assert "modal-body" in content
    assert "<html" not in content


@pytest.mark.django_db
def test_get_with_header_on_non_modal_view_renders_full_page(
    client_user_author_delete: Client, cv_author, author_douglas_adams
):
    """Header on a cv_modal=False view is ignored."""
    response = client_user_author_delete.get(f"/author/{author_douglas_adams.pk}/delete/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    assert "crud_views/view_delete.html" in template_names(response)


@pytest.mark.django_db
def test_modal_view_sets_vary_header(client_user_author_modal: Client, author_douglas_adams):
    """Responses of modal-enabled views carry Vary: X-CV-Modal (with and without the header)."""
    url = f"/author_modal/{author_douglas_adams.pk}/delete/"
    for headers in ({}, MODAL_HEADERS):
        response = client_user_author_modal.get(url, headers=headers)
        assert "X-CV-Modal" in response.headers.get("Vary", "")


@pytest.mark.django_db
def test_detail_modal_partial(client_user_author_modal: Client, author_douglas_adams):
    """DetailView renders its object-detail groups inside the modal partial."""
    response = client_user_author_modal.get(f"/author_modal/{author_douglas_adams.pk}/", headers=MODAL_HEADERS)
    assert response.status_code == 200
    assert "crud_views/modal/content.html" in template_names(response)
    assert "Douglas" in response.content.decode()


@pytest.mark.django_db
def test_custom_form_modal_partial(client_user_author_modal: Client, author_douglas_adams):
    """CustomFormView renders its form inside the modal partial."""
    response = client_user_author_modal.get(
        f"/author_modal/{author_douglas_adams.pk}/contact/", headers=MODAL_HEADERS
    )
    assert response.status_code == 200
    assert "crud_views/modal/content.html" in template_names(response)
    assert "<form" in response.content.decode()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_modal.py -v`
Expected: the modal-partial tests FAIL (full page rendered — `crud_views/modal/content.html` not in templates; `Vary` missing). The full-page tests may already pass.

- [ ] **Step 4: Implement**

In `src/crud_views/lib/view/base.py`:

Add import (top of file, with the other django imports):

```python
from django.utils.cache import patch_vary_headers
```

Add module-level function (above the `CrudView` class):

```python
def cv_is_modal_request(request) -> bool:
    """True when the client asked for the modal partial (X-CV-Modal header)."""
    return request.headers.get("X-CV-Modal") == "true"
```

Add class attributes to `CrudView` (next to `cv_extends_template`, ~line 50):

```python
    # modal rendering (Bootstrap 5 theme; see superpowers/specs/2026-07-14-bootstrap-modals-design.md)
    cv_modal: bool = False  # opt-in: action buttons open this view in a modal
    cv_modal_size: str = ""  # "" | "modal-sm" | "modal-lg" | "modal-xl"
    cv_modal_supported: bool = False  # phase gate: which view types may set cv_modal
    cv_content_template: str | None = None  # the view's body partial, shared by full page and modal
```

Add methods to `CrudView` (near `get_context_data`, ~line 99):

```python
    def get_template_names(self):
        if self.cv_modal and cv_is_modal_request(self.request):
            return ["crud_views/modal/content.html"]
        return super().get_template_names()

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.cv_modal:
            patch_vary_headers(response, ["X-CV-Modal"])
        return response
```

In `cv_get_dict()` (~line 211, inside the `data = dict(...)`) add:

```python
            cv_modal=cls.cv_modal,
            cv_modal_size=cls.cv_modal_size,
```

Set `cv_content_template` and (where applicable) `cv_modal_supported` on the concrete views — one line each, next to the existing `template_name`:

| File / class | additions |
|---|---|
| `views/delete.py` `DeleteView` | `cv_content_template = "crud_views/view_delete.content.html"`, `cv_modal_supported = True` |
| `views/detail.py` `DetailView` | `cv_content_template = "crud_views/view_detail.content.html"`, `cv_modal_supported = True` |
| `views/form.py` `CustomFormView` | `cv_content_template = "crud_views/view_custom_form.content.html"`, `cv_modal_supported = True` |
| `views/form.py` `CustomFormNoObjectView` | `cv_content_template = "crud_views/view_custom_form.content.html"`, `cv_modal_supported = True` |
| `views/create.py` `CreateView` | `cv_content_template = "crud_views/view_create.content.html"` |
| `views/update.py` `UpdateView` | `cv_content_template = "crud_views/view_update.content.html"` |
| `views/list.py` `ListView` | `cv_content_template = "crud_views/view_list.content.html"` |
| `views/mixins.py` `ListViewTableMixin` | `cv_content_template = "crud_views/view_list_table.content.html"` |
| `views/card.py` `CardListView` | `cv_content_template = "crud_views/view_card.content.html"` |

Create `src/crud_views/templates/crud_views/modal/content.html`:

```django
{% load crud_views i18n %}
<div class="modal-header">
    <h5 class="modal-title">{% cv_header_icon %} {% cv_header %}</h5>
    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="{% translate 'Close' %}"></button>
</div>
<div class="modal-body">
    {% include view.cv_content_template %}
</div>
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_modal.py -v`
Expected: all PASS. If `test_detail_modal_partial` still renders the full page, see the `ObjectDetailMixin` MRO gotcha in the hand-over section and add the same `get_template_names` override to `crud_views`' `DetailView` directly.

- [ ] **Step 6: Run the full suite (regression)**

Run: `cd tests && pytest`
Expected: all pass (new attributes are inert defaults).

- [ ] **Step 7: Commit**

```bash
git add src/crud_views tests/test1
git commit -m "feat(modal): cv_modal attributes, X-CV-Modal detection, modal partial rendering"
```

---

### Task 2: Single-source content includes in full-page templates

**Files:**
- Modify: `src/crud_views/templates/crud_views/view_delete.html`, `view_detail.html`, `view_custom_form.html`, `view_create.html`, `view_update.html`, `view_list.html`, `view_list_table.html`, `view_card.html`
- Modify: `src/crud_views_plain/templates/crud_views/view_delete.html`, `view_custom_form.html`, `view_create.html`, `view_update.html`, `view_list_table.html`

**Interfaces:**
- Consumes: `view.cv_content_template` (Task 1).
- Produces: nothing new — refactor so the partial name lives only on the view class.

- [ ] **Step 1: Replace the hardcoded includes**

In every listed template, replace the content include, e.g. in `view_delete.html`:

```django
{% include "crud_views/view_delete.content.html" %}
```

becomes

```django
{% include view.cv_content_template %}
```

Only the `*.content.html` include changes — leave other includes (e.g. `view_list_table.filter.html` in the `cv_filter` block) untouched.

- [ ] **Step 2: Run the full suite**

Run: `cd tests && pytest`
Expected: all pass (the attribute values equal the previously hardcoded strings; plain-theme overrides still win by template-name resolution).

- [ ] **Step 3: Commit**

```bash
git add src/crud_views src/crud_views_plain
git commit -m "refactor(templates): single-source content partial names via view.cv_content_template"
```

---

### Task 3: POST protocol — 204 + X-CV-Redirect on success, 422 on invalid/protected

**Files:**
- Modify: `src/crud_views/lib/views/mixins.py` (`cv_form_valid_redirect` line ~81, `cv_form_invalid` line ~69, imports line ~7)
- Modify: `src/crud_views/lib/views/delete.py` (delete-protection branch in `post()`, line ~174)
- Test: `tests/test1/test_modal.py` (append)

**Interfaces:**
- Consumes: `cv_is_modal_request` from `crud_views.lib.view.base` (Task 1).
- Produces: modal POST responses: `HttpResponse(status=204)` with `response["X-CV-Redirect"]`; invalid re-render with `status_code = 422`. Non-modal behavior byte-identical to today.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_modal.py`:

```python
# ---------------------------------------------------------------------------
# POST protocol (Task 3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modal_delete_success_returns_204_with_redirect(client_user_author_modal: Client, author_douglas_adams):
    from django.contrib.messages import get_messages

    from tests.test1.app.models import Author

    pk = author_douglas_adams.pk
    response = client_user_author_modal.post(f"/author_modal/{pk}/delete/", headers=MODAL_HEADERS)
    assert response.status_code == 204
    assert response.headers["X-CV-Redirect"] == "/author_modal/"
    assert not Author.objects.filter(pk=pk).exists()
    assert len(list(get_messages(response.wsgi_request))) == 1  # MessageMixin still queues the message


@pytest.mark.django_db
def test_modal_delete_protection_returns_422_partial(
    client_user_publisher_modal_protected_delete: Client, publisher_penguin
):
    from tests.test1.app.models import Publisher

    pk = publisher_penguin.pk
    response = client_user_publisher_modal_protected_delete.post(
        f"/publisher_modal_protected/{pk}/delete/", headers=MODAL_HEADERS
    )
    assert response.status_code == 422
    assert "crud_views/modal/content.html" in template_names(response)
    assert "Cannot delete this publisher." in response.content.decode()
    assert Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_modal_custom_form_invalid_returns_422(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.post(
        f"/author_modal/{author_douglas_adams.pk}/contact/",
        {"subject": "", "body": ""},
        headers=MODAL_HEADERS,
    )
    assert response.status_code == 422
    assert "crud_views/modal/content.html" in template_names(response)


@pytest.mark.django_db
def test_modal_custom_form_valid_returns_204(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.post(
        f"/author_modal/{author_douglas_adams.pk}/contact/",
        {"subject": "Hello", "body": "Nice to meet you."},
        headers=MODAL_HEADERS,
    )
    assert response.status_code == 204
    assert response.headers["X-CV-Redirect"] == "/author_modal/"


@pytest.mark.django_db
def test_non_modal_post_flows_unchanged(client_user_author_modal: Client, author_douglas_adams):
    """Without the header, a cv_modal view still redirects with 302 (regression guard)."""
    response = client_user_author_modal.post(f"/author_modal/{author_douglas_adams.pk}/delete/")
    assert response.status_code == 302
    assert response.url == "/author_modal/"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_modal.py -v`
Expected: the four new modal-POST tests FAIL (302 instead of 204; 200 instead of 422). `test_non_modal_post_flows_unchanged` passes.

- [ ] **Step 3: Implement**

In `src/crud_views/lib/views/mixins.py`:

Extend imports:

```python
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from crud_views.lib.view.base import cv_is_modal_request
```

(Replace the two existing separate `from django.http import …` lines with one; keep `BadRequest` import as is.)

Replace `cv_form_valid_redirect`:

```python
    def cv_form_valid_redirect(self, context: dict) -> HttpResponse:
        """
        Redirect to the success url.
        Modal requests get 204 + X-CV-Redirect instead of a 302: fetch() follows
        redirects transparently, so the client needs the target as data.
        """
        url = self.get_success_url()
        if self.cv_modal and cv_is_modal_request(self.request):
            response = HttpResponse(status=204)
            response["X-CV-Redirect"] = url
            return response
        return HttpResponseRedirect(url)
```

Replace `cv_form_invalid`:

```python
    def cv_form_invalid(self, context: dict):
        """
        Handle invalid form; modal requests are answered with 422 so the client
        can distinguish the re-rendered partial from a confirmation page.
        """
        response = self.render_to_response(context)
        if self.cv_modal and cv_is_modal_request(self.request):
            response.status_code = 422
        return response
```

In `src/crud_views/lib/views/delete.py`, the protection branch in `post()` (currently `return self.render_to_response(context)` after the `form.add_error` loop, ~line 174):

```python
                response = self.render_to_response(context)
                if self.cv_modal and cv_is_modal_request(self.request):
                    response.status_code = 422
                return response
```

Add the import at the top of `delete.py`:

```python
from crud_views.lib.view.base import cv_is_modal_request
```

(`delete.py` already imports from `crud_views.lib.view`; check for circular-import issues — `crud_views.lib.view.base` must not import from `crud_views.lib.views`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_modal.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full suite and commit**

Run: `cd tests && pytest` — expected all pass.

```bash
git add src/crud_views tests/test1
git commit -m "feat(modal): POST protocol — 204 + X-CV-Redirect on success, 422 on invalid forms"
```

---

### Task 4: System checks E250 (cv_modal_size) and E251 (phase gate)

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (the `checks()` classmethod, ~line 72)
- Test: `tests/test1/test_modal.py` (append)

**Interfaces:**
- Consumes: `cv_modal`, `cv_modal_size`, `cv_modal_supported` (Task 1); `CheckExpression` from `crud_views.lib.check`.
- Produces: system-check errors `viewset.E250`, `viewset.E251`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_modal.py`:

```python
# ---------------------------------------------------------------------------
# System checks (Task 4)
# ---------------------------------------------------------------------------


def check_ids(view_cls) -> list:
    return [m.id for c in view_cls.checks() for m in c.messages()]


def test_check_modal_size_invalid():
    from crud_views.lib.views import DeleteView

    class BadSizeDeleteView(DeleteView):
        cv_modal = True
        cv_modal_size = "modal-huge"

    assert "viewset.E250" in check_ids(BadSizeDeleteView)


def test_check_modal_size_valid_values():
    from crud_views.lib.views import DeleteView

    for size in ("", "modal-sm", "modal-lg", "modal-xl"):

        class GoodSizeDeleteView(DeleteView):
            cv_modal = True
            cv_modal_size = size

        assert "viewset.E250" not in check_ids(GoodSizeDeleteView)


def test_check_modal_not_supported_on_create():
    from crud_views.lib.views import CreateView

    class BadModalCreateView(CreateView):
        cv_modal = True

    assert "viewset.E251" in check_ids(BadModalCreateView)


def test_check_modal_supported_on_delete():
    from crud_views.lib.views import DeleteView

    class GoodModalDeleteView(DeleteView):
        cv_modal = True

    assert "viewset.E251" not in check_ids(GoodModalDeleteView)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_modal.py -v -k check_modal`
Expected: `test_check_modal_size_invalid` and `test_check_modal_not_supported_on_create` FAIL (IDs absent).

- [ ] **Step 3: Implement**

In `src/crud_views/lib/view/base.py`, `CrudView.checks()` (~line 72), after the existing yields add (import `CheckExpression` alongside the other check imports at line 11):

```python
        yield CheckExpression(
            context=cls,
            id="E250",
            expression=cls.cv_modal_size in ("", "modal-sm", "modal-lg", "modal-xl"),
            msg=f"cv_modal_size must be one of '', 'modal-sm', 'modal-lg', 'modal-xl', got {cls.cv_modal_size!r}",
        )
        yield CheckExpression(
            context=cls,
            id="E251",
            expression=not cls.cv_modal or cls.cv_modal_supported,
            msg="cv_modal is not supported for this view type (phase 1: delete, detail and custom form views)",
        )
```

- [ ] **Step 4: Run tests, full suite, commit**

Run: `cd tests && pytest test1/test_modal.py -v` then `cd tests && pytest` — all pass.

```bash
git add src/crud_views tests/test1
git commit -m "feat(modal): system checks E250 (cv_modal_size) and E251 (phase gate)"
```

---

### Task 5: Buttons, form actions, modal shell (bootstrap5 templates)

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/list_action.html`
- Modify: `src/crud_views/templates/crud_views/tags/context_action.html`
- Modify: `src/crud_views/templates/crud_views/tags/cv_config.html`
- Modify: `src/crud_views/templates/crud_views/view_delete.content.html`, `view_custom_form.content.html`, `view_create.content.html`, `view_update.content.html` (form `action` attribute)
- Modify: `tests/test1/app/templates/app/base.html` (only if `{% cv_config %}` is missing)
- Test: `tests/test1/test_modal.py` (append)

**Interfaces:**
- Consumes: `cv_modal` / `cv_modal_size` in button-tag context (Task 1, via `cv_get_dict`).
- Produces: buttons carry `data-cv-modal="true"` + `data-cv-modal-size`; shell markup `#cv-modal` / `#cv-modal-dialog` / `#cv-modal-content` rendered by `{% cv_config %}`; content-partial forms carry `action="{{ request.path }}"` — all of which `modal.js` (Task 6) relies on.

- [ ] **Step 1: Write the failing tests**

First check the test base template: `grep -n "cv_config" tests/test1/app/templates/app/base.html`. If absent, add `{% cv_config %}` (and `{% load crud_views %}` if needed) to its `<head>` — the shell test below depends on it.

Append to `tests/test1/test_modal.py`:

```python
# ---------------------------------------------------------------------------
# Button attributes, form action, shell (Task 5)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_buttons_carry_modal_attributes(client_user_author_modal: Client, author_douglas_adams):
    response = client_user_author_modal.get("/author_modal/")
    content = response.content.decode()
    assert 'data-cv-modal="true"' in content
    assert 'data-cv-modal-size="modal-lg"' in content  # AuthorModalDeleteView


@pytest.mark.django_db
def test_list_buttons_without_modal_have_no_attributes(client_user_author_delete: Client, author_douglas_adams):
    response = client_user_author_delete.get("/author/")
    assert "data-cv-modal" not in response.content.decode()


@pytest.mark.django_db
def test_modal_partial_form_has_explicit_action(client_user_author_modal: Client, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_modal.get(f"/author_modal/{pk}/delete/", headers=MODAL_HEADERS)
    assert f'action="/author_modal/{pk}/delete/"' in response.content.decode()


@pytest.mark.django_db
def test_cv_config_renders_modal_shell(client_user_author_modal: Client):
    response = client_user_author_modal.get("/author_modal/")
    content = response.content.decode()
    assert 'id="cv-modal"' in content
    assert 'id="cv-modal-dialog"' in content
    assert 'id="cv-modal-content"' in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_modal.py -v -k "buttons or shell or explicit_action"`
Expected: all four FAIL except `test_list_buttons_without_modal_have_no_attributes`.

- [ ] **Step 3: Implement**

`tags/list_action.html` — full new content:

```django
{% if cv_action_enabled is not False and cv_access is True %}
<a {% if cv_modal %}
    href="{{ cv_url }}"
    data-cv-modal="true"
    data-cv-modal-size="{{ cv_modal_size }}"
{% elif cv_list_action_method == "get" %}
    href="{{ cv_url }}"
{% elif cv_list_action_method == "post" %}
    href="#"
    data-cv-action="submit-form"
    data-cv-target="cv_form_{{ cv_oid }}"
{% endif %}
    class="btn btn-outline-primary btn-xs"
    role="button"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    <i class="{{ cv_icon_action }}"></i>
</a>
{% endif %}
```

`tags/context_action.html` — full new content (context buttons without `cv_modal` in context render unchanged — missing var is falsy):

```django
{% if cv_key and cv_action_enabled is not False and cv_access is True %}
    <a href="{{ cv_url }}" class="btn btn-outline-primary {% if cv_is_active %}active{% endif %} btn-lg"
       role="button"
       title="{{ cv_action_label }}"
       {% if cv_modal %}data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}"{% endif %}
       cv-key="{{ cv_key }}">
        <i class="{{ cv_icon_action }}"></i>
    </a>
{% endif %}
```

`tags/cv_config.html` — append the shell after the existing config div:

```django
<div id="cv-config"
     data-request-path="{{ request_path }}"
     data-query-string="{{ request_query_string }}"
     data-csrf-token="{{ csrf_token }}"
     hidden></div>
<div class="modal fade" id="cv-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" id="cv-modal-dialog">
        <div class="modal-content" id="cv-modal-content"></div>
    </div>
</div>
```

Form tags in the four content partials (`view_delete.content.html`, `view_custom_form.content.html`, `view_create.content.html`, `view_update.content.html`):

```django
<form class="cv-form" method="post" action="{{ request.path }}" novalidate>
```

(Only the `crud_views` bootstrap5 theme; `crud_views_plain` partials stay untouched.)

- [ ] **Step 4: Run tests, full suite, commit**

Run: `cd tests && pytest test1/test_modal.py -v` then `cd tests && pytest` — all pass (existing tests asserting `<form` still match).

```bash
git add src/crud_views tests/test1
git commit -m "feat(modal): button data attributes, modal shell via cv_config, explicit form actions"
```

---

### Task 6: modal.js

**Files:**
- Create: `src/crud_views/static/crud_views/js/modal.js`
- Modify: `src/crud_views/lib/settings.py` (`javascript()`, line ~117)
- Test: `tests/test1/test_modal.py` (append)

**Interfaces:**
- Consumes: `data-cv-modal` / `data-cv-modal-size` attributes, shell IDs, form `action` attributes (Task 5); `X-CV-Redirect` / 422 protocol (Task 3); host-provided `window.bootstrap` and jQuery.
- Produces: `cv:modal:loaded` CustomEvent on `#cv-modal` after every content injection (documented phase-2 re-init hook).

- [ ] **Step 1: Write the failing test**

Append to `tests/test1/test_modal.py`:

```python
# ---------------------------------------------------------------------------
# modal.js registration (Task 6) — JS behavior itself is verified manually
# in examples/bootstrap5 (see design spec, testing decision)
# ---------------------------------------------------------------------------


def test_modal_js_registered_and_shipped():
    from django.contrib.staticfiles import finders

    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.javascript()["modal"] == "crud_views/js/modal.js"
    assert finders.find("crud_views/js/modal.js")


@pytest.mark.django_db
def test_cv_js_tag_includes_modal_js(client_user_author_modal: Client):
    response = client_user_author_modal.get("/author_modal/")
    assert "crud_views/js/modal.js" in response.content.decode()
```

(If the test base template lacks `{% cv_js %}`, add it next to `{% cv_config %}` from Task 5.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_modal.py -v -k modal_js`
Expected: FAIL (`KeyError: 'modal'`, file not found).

- [ ] **Step 3: Implement**

In `src/crud_views/lib/settings.py`, `javascript()`:

```python
    def javascript(self) -> dict:
        return Box(
            {
                "viewset": self.get_js("viewset.js"),
                "formset": self.get_js("formset.js"),
                "list_filter": self.get_js("list.filter.js"),
                "modal": self.get_js("modal.js"),
            }
        )
```

Create `src/crud_views/static/crud_views/js/modal.js`:

```javascript
/**
 * CrudViews modal: fetch-based Bootstrap 5 modal rendering for views with cv_modal = True.
 *
 * Protocol (superpowers/specs/2026-07-14-bootstrap-modals-design.md):
 *   GET  url  + X-CV-Modal: true  -> 200 modal partial (modal-header + modal-body)
 *   POST form + X-CV-Modal: true  -> 204 + X-CV-Redirect header (success: navigate)
 *                                 -> 422 + re-rendered partial   (validation errors: swap)
 * Anything else falls back to a full-page navigation — never strand the user in a broken modal.
 *
 * After every injection a "cv:modal:loaded" CustomEvent is dispatched on #cv-modal
 * (hook for re-initializing scripts inside modal content).
 */

const CVModalConst = Object.freeze({
    modal: "cv-modal",
    dialog: "cv-modal-dialog",
    content: "cv-modal-content",
    urlAttr: "data-cv-url",
    loadedEvent: "cv:modal:loaded",
});

function cvModalElements() {
    const modal = document.getElementById(CVModalConst.modal);
    if (!modal) {
        throw new Error("cvModal: #cv-modal not found. Make sure {% cv_config %} is in your base template.");
    }
    if (typeof bootstrap === "undefined" || !bootstrap.Modal) {
        throw new Error("cvModal: Bootstrap 5 JavaScript not loaded.");
    }
    return {
        modal: modal,
        dialog: document.getElementById(CVModalConst.dialog),
        content: document.getElementById(CVModalConst.content),
    };
}

function cvModalInject(html) {
    const els = cvModalElements();
    els.content.innerHTML = html;
    els.modal.dispatchEvent(new CustomEvent(CVModalConst.loadedEvent, {bubbles: true}));
}

function cvModalOpen(url, size) {
    const els = cvModalElements();
    fetch(url, {headers: {"X-CV-Modal": "true"}})
        .then(function (response) {
            if (!response.ok) {
                window.location.assign(url);
                return null;
            }
            return response.text();
        })
        .then(function (html) {
            if (html === null) {
                return;
            }
            els.dialog.className = "modal-dialog" + (size ? " " + size : "");
            els.modal.setAttribute(CVModalConst.urlAttr, url);
            cvModalInject(html);
            bootstrap.Modal.getOrCreateInstance(els.modal).show();
        })
        .catch(function () {
            window.location.assign(url);
        });
}

function cvModalSubmit(form) {
    const els = cvModalElements(),
        url = form.getAttribute("action"),
        fallback = els.modal.getAttribute(CVModalConst.urlAttr) || url;
    fetch(url, {
        method: "POST",
        body: new FormData(form),
        headers: {"X-CV-Modal": "true"},
    })
        .then(function (response) {
            const redirect = response.headers.get("X-CV-Redirect");
            if (redirect) {
                window.location.assign(redirect);
                return null;
            }
            if (response.status === 422) {
                return response.text();
            }
            window.location.assign(fallback);
            return null;
        })
        .then(function (html) {
            if (html === null || html === undefined) {
                return;
            }
            cvModalInject(html);
        })
        .catch(function () {
            window.location.assign(fallback);
        });
}

$(document).ready(function () {
    $(document).on("click", "[data-cv-modal='true']", function (e) {
        e.preventDefault();
        cvModalOpen($(this).attr("href"), $(this).attr("data-cv-modal-size"));
    });

    $(document).on("submit", "#cv-modal-content form", function (e) {
        e.preventDefault();
        cvModalSubmit(this);
    });
});
```

- [ ] **Step 4: Run tests, full suite, commit**

Run: `cd tests && pytest test1/test_modal.py -v` then `cd tests && pytest` — all pass.

```bash
git add src/crud_views tests/test1
git commit -m "feat(modal): modal.js — fetch-based Bootstrap modal transport"
```

---

### Task 7: Example app, documentation, final verification

**Files:**
- Modify: `examples/bootstrap5/app/views/author.py` (`AuthorDeleteView` ~line 107, `AuthorDetailView` ~line 115, `AuthorContactView` ~line 183)
- Create: `docs/reference/modals.md`
- Test: manual (bootstrap5 example) + full suite + lint

**Interfaces:**
- Consumes: everything from Tasks 1–6.
- Produces: user-facing docs and a manual verification surface.

- [ ] **Step 1: Enable modals in the bootstrap5 example**

Add to the three view classes in `examples/bootstrap5/app/views/author.py` (they subclass Guardian variants of `DeleteView`/`DetailView`/`CustomFormView`, which are phase-1 types):

```python
class AuthorDeleteView(...):
    ...
    cv_modal = True
    cv_modal_size = "modal-lg"


class AuthorDetailView(...):
    ...
    cv_modal = True


class AuthorContactView(...):
    ...
    cv_modal = True
```

- [ ] **Step 2: Manual verification in the example app**

Start the bootstrap5 example (see `examples/bootstrap5` — standard Django project; `python manage.py runserver` after the `task dev` environment setup) and verify in the browser:

1. Author list → row delete button opens a large modal with the confirmation; **Confirm** → page navigates to the list, success message shows.
2. Delete modal on an author with related objects / protection (if configured) → errors render inside the modal, status 422 in devtools.
3. Row detail button → detail modal with property groups; close button works.
4. Contact context action on the detail page → contact modal; submit empty → errors in modal; submit valid → redirect + message.
5. Middle-click a modal delete button → full confirmation page opens in a new tab (fallback).
6. Devtools network tab: modal GETs carry `X-CV-Modal: true`; responses carry `Vary: X-CV-Modal`.

Record any deviation as a bug before proceeding — do not patch around it in the example.

- [ ] **Step 3: Write the documentation page**

Create `docs/reference/modals.md` (mkdocs uses the awesome-pages plugin — a new file under `docs/reference/` appears in the nav automatically):

````markdown
# Modals

Views can opt in to Bootstrap 5 modal rendering: action buttons then open the view in a modal
dialog instead of navigating to a full page.

```python
class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_modal = True                 # opt in
    cv_modal_size = "modal-lg"      # optional: "", "modal-sm", "modal-lg", "modal-xl"
```

## Supported views

`DeleteView`, `DetailView`, `CustomFormView` and `CustomFormNoObjectView` (and their
permission-required and extension-package variants). Setting `cv_modal = True` on other view
types raises system check error `viewset.E251`. Create/update support is planned.

## Behavior

- Buttons linking to a modal-enabled view fetch the view with the `X-CV-Modal: true` header and
  show the returned partial in a shared modal shell (rendered by `{% cv_config %}` — no template
  changes needed in your project).
- On successful POST the server answers `204` with an `X-CV-Redirect` header and the browser
  navigates to the view's success URL — messages and `cv_success_key` work exactly as without
  modals.
- Validation errors (and delete protection) re-render inside the open modal (status 422).
- Progressive enhancement: direct links, middle-click, disabled JavaScript and non-Bootstrap
  themes (e.g. `crud_views_plain`) all render the normal full page.

## Requirements

Your base template must load Bootstrap 5's JavaScript bundle and jQuery (both are already
required for the Bootstrap 5 theme), plus the standard `{% cv_config %}` / `{% cv_js %}` tags.

## Extending

After every content injection the shell dispatches a `cv:modal:loaded` CustomEvent on
`#cv-modal` — use it to initialize custom scripts inside modal content:

```javascript
document.getElementById("cv-modal").addEventListener("cv:modal:loaded", function () {
    // initialize widgets inside the injected modal content
});
```
````

- [ ] **Step 4: Final verification**

```bash
cd tests && pytest          # full suite
task check                  # ruff check --fix
task format                 # ruff format
task test                   # nox matrix — Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0
```

Expected: all green. Docs render check (optional): `task docs` and open `localhost:8001`.

- [ ] **Step 5: Commit and hand back**

```bash
git add examples/bootstrap5 docs/reference/modals.md
git commit -m "docs(modal): example app usage and reference documentation"
```

Then follow the workflow in the hand-over section: push the branch, open a PR, wait for CI, fix ruff findings if flagged, squash-merge.
