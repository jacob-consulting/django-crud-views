# Transactions Around Write Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every django-crud-views POST write (form, delete, action views) runs its write phase in one database transaction on the model's write database, with a new post-commit hook `cv_on_commit` for side effects. The call chain, the transaction boundary and every hook are documented in a new reference page, with FAQ entries that link to it.

**Architecture:** `CrudView` gets `cv_atomic` (bool attribute) plus `cv_get_db_alias()`, `cv_get_atomic()` and `cv_on_commit()`. Each of the three POST seams calls a new method that owns the transaction: `cv_form_valid_process()` (form and delete views) or `cv_action_process()` (action views). That method runs the write step and the user hook inside `cv_get_atomic()` and registers `cv_on_commit` through `transaction.on_commit`. The existing inner `atomic()` blocks in formsets and workflow stay, now routed to the model's database. Resource views default to `cv_atomic = False`.

**Tech Stack:** Python 3.12+, Django 4.2/5.2/6.0, pytest + pytest-django 4.14 (`django_capture_on_commit_callbacks` fixture), MkDocs 1.6 (readthedocs theme, awesome-pages), ruff.

**Spec:** `superpowers/specs/2026-10-08-transactions-call-chain-design.md`. Read it before starting; it holds the reasoning behind every decision below.

## Global Constraints

- Branch: `feature/transactions-call-chain-31` (it already exists and holds the spec commit). Never commit to `main`.
- All `CrudView` class attributes use the `cv_` prefix. The new public names are exactly `cv_atomic`, `cv_get_db_alias`, `cv_get_atomic`, `cv_on_commit`, `cv_form_valid_process` and `cv_action_process`. Don't rename them.
- Line length 120, double quotes, ruff format. Run `.venv/bin/ruff format` and `.venv/bin/ruff check --fix` before each commit (the pre-commit hook also runs ruff-format).
- Run tests with the project venv from the repo root: `.venv/bin/python -m pytest …`. In a git worktree, see the note at the end of this plan.
- Don't move `cv_form_valid_redirect` / `get_success_url` into the transaction. DeleteView resolves the success URL **after** `delete()` (issue #167); keep that order.
- `action()` returning `False` must **not** roll back automatically.
- `MessageMixin` keeps adding its message in `cv_form_valid_hook`. Don't move it.
- `on_commit` is registered **without** `robust=True`.
- Out of scope: `select_for_update`, transactions across databases, a global `CRUD_VIEWS_ATOMIC` setting, a system check for `cv_atomic`.
- The release version for the docs text is **0.27.0** (next minor after 0.26.0). Don't bump versions or release; that happens only when the maintainer asks.
- Customer project names never appear in code, docs or commits.
- Tests that subclass a registered view must **not** redeclare `cv_viewset` in the subclass body; a redeclaration re-registers the key and raises "already registered". Prefer `monkeypatch.setattr(RegisteredViewClass, "method", fn)`, which restores itself after the test.

## Review Focus

These inputs are implied by the spec but not covered by the main tests. Each has a test added to the task that owns the code:

1. **`ATOMIC_REQUESTS=True` projects.** `cv_on_commit` must run after the view has returned, at request commit, not inside the view. Test: `test_on_commit_deferred_to_request_commit_with_atomic_requests` (Task 2).
2. **Modal submits (204 + `X-CV-Redirect`).** `cv_on_commit` must still run, and the 204 must be unchanged. Test: `test_modal_delete_runs_on_commit_and_keeps_204` (Task 3).
3. **Delete blocked by `cv_check_delete_protection`.** No write and no `cv_on_commit`. Test: `test_delete_protection_skips_write_phase` (Task 3).
4. **`cv_on_commit` itself raising.** The data stays committed and the error surfaces. Test: `test_on_commit_error_keeps_committed_data` (Task 2).
5. **`action()` returning `False` with `cv_atomic = False`.** No error, no `cv_on_commit`, partial writes stay. Test: `test_action_false_without_atomic_keeps_partial_write` (Task 4).

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `src/crud_views/lib/view/base.py` | modify | `cv_atomic`, `cv_get_db_alias`, `cv_get_atomic`, `cv_on_commit` on `CrudView` |
| `src/crud_views/lib/resource.py` | modify | `ResourceViewMixin.cv_atomic = False`, router-free `cv_get_db_alias` |
| `src/crud_views/lib/views/mixins.py` | modify | `CrudViewProcessFormMixin.cv_form_valid_process`, `post()` calls it |
| `src/crud_views/lib/views/delete.py` | modify | `DeleteView.post()` calls `cv_form_valid_process` |
| `src/crud_views/lib/views/action.py` | modify | `ActionView.cv_action_process`, `post()` calls it |
| `src/crud_views_workflow/lib/views.py` | modify | routed inner atomic, `context["workflow_info"]` |
| `src/crud_views/lib/formsets/mixins.py` | modify | routed inner atomic |
| `tests/test1/app/models.py` | modify | test model `Genre` (M2M to `Publisher`) |
| `tests/test1/app/views.py` | modify | `cv_genre` viewset + list/create views (M2M parent) |
| `tests/test1/app/urls.py` | modify | register `cv_genre.urlpatterns` |
| `tests/test1/test_transactions.py` | create | all new transaction tests |
| `tests/test1/test_conditional_formset.py` | modify | stub gets `cv_get_db_alias`; asserts routing |
| `docs/reference/request_lifecycle.md` | create | call chains, hook reference, transactions, recipes, limitations, migration |
| `docs/reference/.pages` | modify | nav entry for the new page |
| `docs/faq.md` | modify | six FAQ entries linking to recipes |
| `docs/reference/{create,update,delete,custom_form,action,workflow}_view.md` | modify | phase column / links / rewritten `on_transition` example |
| `docs/reference/{formsets,conditional}.md` | modify | transaction sentence links to the new page |
| `docs/development/stability.md` | modify | new public names |
| `mkdocs.yml` | modify | `validation: anchors: warn` |
| `CHANGELOG.md` | modify | Unreleased entries |
| `/home/alex/projects/alex/skills/plugins/django-crud-views/skills/django-crud-views/SKILL.md` | modify (separate repo) | hooks/transactions section + Common Mistakes row |

The test app (`tests/test1/app`) has **no migrations**. pytest-django creates its tables with syncdb, so adding a model needs no migration file.

---

### Task 1: Core transaction API on `CrudView` and `ResourceViewMixin`

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (imports at top; attributes block around lines 54–100; methods after `dispatch()` at ~line 166)
- Modify: `src/crud_views/lib/resource.py` (`ResourceViewMixin`, ~line 134)
- Create: `tests/test1/test_transactions.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `CrudView.cv_atomic: bool = True`
  - `CrudView.cv_get_db_alias(self) -> str`: `router.db_for_write(self.cv_viewset.model)`
  - `CrudView.cv_get_atomic(self) -> contextlib.AbstractContextManager`: `transaction.atomic(using=alias)` or `nullcontext()`
  - `CrudView.cv_on_commit(self, context: dict) -> None`: no-op hook
  - `ResourceViewMixin.cv_atomic = False`; `ResourceViewMixin.cv_get_db_alias()` returns `django.db.DEFAULT_DB_ALIAS`

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_transactions.py`:

```python
"""
Transaction boundary around POST write phases (#31).

See docs/reference/request_lifecycle.md. Tests that patch registered view classes use
monkeypatch.setattr on the class (auto-restored); they never subclass with cv_viewset in the
class body, which would re-register the view key.
"""

from contextlib import nullcontext
from unittest import mock

import pytest
from django.db import DEFAULT_DB_ALIAS, router, transaction

from crud_views.lib.check import CheckUnknownAttributes
from crud_views.lib.view.base import CrudView
from tests.test1.app.models import Publisher


class Boom(Exception):
    pass


def _boom(*args, **kwargs):
    raise Boom("hook failed")


def _record_on_commit(monkeypatch, view_class) -> list[dict]:
    """Replace view_class.cv_on_commit with a recorder; returns the list of contexts it saw."""
    calls: list[dict] = []
    monkeypatch.setattr(view_class, "cv_on_commit", lambda self, context: calls.append(context))
    return calls


# --- Task 1: core API --------------------------------------------------------------------------


def test_crud_view_is_atomic_by_default():
    assert CrudView.cv_atomic is True


def test_resource_views_are_not_atomic():
    from tests.test1.app.resources import S3FileTouchView

    assert S3FileTouchView.cv_atomic is False


def test_db_alias_follows_router():
    from tests.test1.app.views import PublisherCreateView

    with mock.patch.object(router, "db_for_write", return_value="other") as db_for_write:
        assert PublisherCreateView().cv_get_db_alias() == "other"
    db_for_write.assert_called_once_with(Publisher)


def test_get_atomic_wraps_in_atomic_on_routed_alias():
    from tests.test1.app.views import PublisherCreateView

    view = PublisherCreateView()
    with mock.patch.object(view, "cv_get_db_alias", return_value=DEFAULT_DB_ALIAS):
        ctx = view.cv_get_atomic()
    assert isinstance(ctx, transaction.Atomic)
    assert ctx.using == DEFAULT_DB_ALIAS


def test_get_atomic_is_noop_when_disabled():
    from tests.test1.app.views import PublisherCreateView

    view = PublisherCreateView()
    view.cv_atomic = False
    assert isinstance(view.cv_get_atomic(), nullcontext)


def test_resource_db_alias_never_consults_router():
    from tests.test1.app.resources import S3FileTouchView

    with mock.patch.object(router, "db_for_write", side_effect=AssertionError("router consulted")):
        assert S3FileTouchView().cv_get_db_alias() == DEFAULT_DB_ALIAS


def test_cv_on_commit_default_is_noop():
    from tests.test1.app.views import PublisherCreateView

    assert PublisherCreateView().cv_on_commit({}) is None


def test_cv_atomic_is_a_known_attribute():
    class NotAtomicView(CrudView):  # bare subclass: not registered (no cv_viewset in body)
        cv_atomic = False

    assert list(CheckUnknownAttributes(context=NotAtomicView).messages()) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py -v`
Expected: FAIL. `AttributeError: type object 'CrudView' has no attribute 'cv_atomic'` (and similar for the other names). `test_cv_atomic_is_a_known_attribute` fails with one `viewset.W280` message.

- [ ] **Step 3: Implement on `CrudView`**

In `src/crud_views/lib/view/base.py`, add imports. Put `from contextlib import nullcontext` with the stdlib imports at the top (after `from collections.abc import Iterable`), and `from django.db import router, transaction` with the Django imports (after `from django.contrib.auth.mixins import PermissionRequiredMixin`, before `from django.db.models import Model`):

```python
from contextlib import nullcontext
```

```python
from django.db import router, transaction
```

Add the attribute right after `cv_cancel_keys` (line ~69):

```python
    cv_atomic: bool = True  # run the POST write phase in transaction.atomic(); see request_lifecycle.md
```

Add the methods directly after `dispatch()`:

```python
    def cv_get_db_alias(self) -> str:
        """Database alias of the POST write phase; follows DATABASE_ROUTERS for the ViewSet's model."""
        return router.db_for_write(self.cv_viewset.model)

    def cv_get_atomic(self):
        """
        Context manager around the POST write phase: transaction.atomic() on cv_get_db_alias(),
        or a no-op when cv_atomic is False. Override for durable=True or a custom boundary.
        """
        if not self.cv_atomic:
            return nullcontext()
        return transaction.atomic(using=self.cv_get_db_alias())

    def cv_on_commit(self, context: dict) -> None:
        """
        Hook: runs after the write phase is committed, never after a rollback.
        Put side effects here: mail, Celery tasks, webhooks, cache invalidation.
        """
        pass
```

- [ ] **Step 4: Implement on `ResourceViewMixin`**

In `src/crud_views/lib/resource.py`, add `from django.db import DEFAULT_DB_ALIAS` to the imports. Then add to `ResourceViewMixin`, above `get_queryset`:

```python
    cv_atomic: bool = False  # a DB transaction cannot roll back S3 / API writes

    def cv_get_db_alias(self) -> str:
        # a Resource is not a Django model: never hand it to DATABASE_ROUTERS
        return DEFAULT_DB_ALIAS
```

Also extend the class docstring with a third bullet:

```
    - cv_atomic / cv_get_db_alias: no database transaction by default and no
      router lookup; set cv_atomic = True when the view also writes ORM rows.
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py tests/test1/test_unknown_attribute_check.py tests/test1/test_resource_views.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check --fix src tests
git add src/crud_views/lib/view/base.py src/crud_views/lib/resource.py tests/test1/test_transactions.py
git commit -m "feat: cv_atomic, cv_get_atomic, cv_get_db_alias, cv_on_commit on CrudView (#31)"
```

---

### Task 2: Transaction seam for form views (`cv_form_valid_process`)

Covers Create, Update, CustomForm, CustomFormNoObject, Polymorphic Create/Update and Workflow, which all go through `CrudViewProcessFormMixin.post`.

**Files:**
- Modify: `src/crud_views/lib/views/mixins.py` (`CrudViewProcessFormMixin`, lines ~21–45)
- Modify: `tests/test1/app/models.py` (add `Genre` after `Book`)
- Modify: `tests/test1/app/views.py` (add `cv_genre` block after the Book views, ~line 440)
- Modify: `tests/test1/app/urls.py` (import + register `cv_genre`)
- Modify: `tests/test1/test_transactions.py` (append)

**Interfaces:**
- Consumes: `cv_get_atomic()`, `cv_get_db_alias()`, `cv_on_commit()` from Task 1.
- Produces: `CrudViewProcessFormMixin.cv_form_valid_process(self, context: dict) -> None`, which Task 3 (DeleteView) calls. Test fixtures `cv_genre`, `GenreCreateView` and `Genre`.

- [ ] **Step 1: Add the M2M test scaffolding (model, viewset, url)**

The test app has no M2M parent today, and `Book.publisher` is a required FK, so the m2m-through branch of `CreateViewParentMixin` can't be tested on Book. Add a dedicated model.

`tests/test1/app/models.py`, after the `Book` class:

```python
class Genre(models.Model):
    """M2M child of Publisher: exercises CreateViewParentMixin's many_to_many_through branch."""

    name = models.CharField(max_length=100)
    publishers = models.ManyToManyField(Publisher, related_name="genres")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
```

`tests/test1/app/views.py`: add `Genre` to the existing `from tests.test1.app.models import …` line. Then, after the `BookDeleteView` class, add:

```python
# --- Genre (INT PK, many-to-many child of Publisher; transaction tests) ---

cv_genre = ViewSet(
    model=Genre,
    name="genre",
    parent=ParentViewSet(name="publisher", attribute="publishers", many_to_many_through_attribute="genres"),
)


class GenreForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Genre
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class GenreListView(ListViewPermissionRequired):
    cv_viewset = cv_genre


class GenreCreateView(CrispyViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    form_class = GenreForm
    cv_viewset = cv_genre
```

(`ViewSet`, `ParentViewSet`, `CrispyModelForm`, `Row`, `Column4`, `ListViewPermissionRequired`, `CrispyViewMixin`, `CreateViewParentMixin` and `CreateViewPermissionRequired` are already imported in that module; check with `grep -n "^from\|^import" tests/test1/app/views.py`.)

`tests/test1/app/urls.py`: add `cv_genre,` to the import list from `tests.test1.app.views` (alphabetical, after `cv_contract`), and add `urlpatterns += cv_genre.urlpatterns` after `urlpatterns += cv_book.urlpatterns`.

Run: `.venv/bin/python -m pytest tests/test1 -q -x`
Expected: PASS (scaffolding only; nothing uses it yet). If a registry/manage test counts viewsets, update its expected count and say so in the commit message.

- [ ] **Step 2: Write the failing tests**

Append to `tests/test1/test_transactions.py`:

```python
# --- Task 2: form views ------------------------------------------------------------------------


@pytest.fixture
def client_user_genre_add(client, db):
    from django.contrib.auth.models import User

    from tests.lib.helper.user import user_viewset_permission
    from tests.test1.app.views import cv_genre

    user = User.objects.create_user(username="user_genre_add", password="password")
    user_viewset_permission(user, cv_genre, "add")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_create_hook_exception_rolls_back_save(client_user_publisher_add, monkeypatch):
    from tests.test1.app.views import PublisherCreateView

    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_add.post("/publisher/create/", {"name": "Rolled Back"})
    assert not Publisher.objects.filter(name="Rolled Back").exists()


@pytest.mark.django_db
def test_create_hook_exception_keeps_row_without_atomic(client_user_publisher_add, monkeypatch):
    """cv_atomic = False restores the pre-0.27 autocommit behaviour (guard: passes before and after)."""
    from tests.test1.app.views import PublisherCreateView

    monkeypatch.setattr(PublisherCreateView, "cv_atomic", False)
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_add.post("/publisher/create/", {"name": "Kept"})
    assert Publisher.objects.filter(name="Kept").exists()


@pytest.mark.django_db
def test_update_hook_exception_rolls_back_save(client_user_publisher_change, monkeypatch):
    from tests.test1.app.views import PublisherUpdateView

    publisher = Publisher.objects.create(name="Old")
    monkeypatch.setattr(PublisherUpdateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_change.post(f"/publisher/{publisher.pk}/update/", {"name": "New"})
    publisher.refresh_from_db()
    assert publisher.name == "Old"


@pytest.mark.django_db
def test_custom_form_view_write_rolls_back(client_user_author_view, monkeypatch):
    from tests.test1.app.models import Author
    from tests.test1.app.views import AuthorContactView

    author = Author.objects.create(first_name="First", last_name="Author")

    def write(self, context):
        self.object.pseudonym = "written"
        self.object.save()

    monkeypatch.setattr(AuthorContactView, "cv_form_valid", write)
    monkeypatch.setattr(AuthorContactView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_author_view.post(f"/author/{author.pk}/contact/", {"subject": "hi", "body": "there"})
    author.refresh_from_db()
    assert author.pseudonym is None


@pytest.mark.django_db
def test_on_commit_runs_once_after_success(
    client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.views import PublisherCreateView

    calls = _record_on_commit(monkeypatch, PublisherCreateView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_publisher_add.post("/publisher/create/", {"name": "Committed"})
    assert response.status_code == 302
    assert len(calls) == 1
    assert calls[0]["object"].name == "Committed"


@pytest.mark.django_db
def test_on_commit_not_called_for_invalid_form(
    client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.views import PublisherCreateView

    calls = _record_on_commit(monkeypatch, PublisherCreateView)
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = client_user_publisher_add.post("/publisher/create/", {"name": ""})
    assert response.status_code == 200
    assert calls == []
    assert callbacks == []


@pytest.mark.django_db
def test_on_commit_not_called_after_rollback(
    client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.views import PublisherCreateView

    calls = _record_on_commit(monkeypatch, PublisherCreateView)
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_hook", _boom)
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(Boom):
            client_user_publisher_add.post("/publisher/create/", {"name": "Rolled Back"})
    assert calls == []


@pytest.mark.django_db
def test_on_commit_error_keeps_committed_data(
    client_user_publisher_add, monkeypatch, django_capture_on_commit_callbacks
):
    """Review focus 4: a failing side effect must not undo the committed write."""
    from tests.test1.app.views import PublisherCreateView

    monkeypatch.setattr(PublisherCreateView, "cv_on_commit", _boom)
    with pytest.raises(Boom):
        with django_capture_on_commit_callbacks(execute=True):
            client_user_publisher_add.post("/publisher/create/", {"name": "Committed"})
    assert Publisher.objects.filter(name="Committed").exists()


@pytest.mark.parametrize("atomic", [True, False])
@pytest.mark.django_db(transaction=True)
def test_on_commit_runs_before_redirect_in_autocommit(client_user_publisher_add, monkeypatch, atomic):
    """Real commits (no test transaction): cv_on_commit runs inside the view, before the redirect."""
    from tests.test1.app.views import PublisherCreateView

    order: list[str] = []
    original_redirect = PublisherCreateView.cv_form_valid_redirect

    def redirect(self, context):
        order.append("redirect")
        return original_redirect(self, context)

    monkeypatch.setattr(PublisherCreateView, "cv_atomic", atomic)
    monkeypatch.setattr(PublisherCreateView, "cv_on_commit", lambda self, context: order.append("commit"))
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_redirect", redirect)
    response = client_user_publisher_add.post("/publisher/create/", {"name": "Autocommit"})
    assert response.status_code == 302
    assert order == ["commit", "redirect"]


@pytest.mark.django_db(transaction=True)
def test_on_commit_deferred_to_request_commit_with_atomic_requests(client_user_publisher_add, monkeypatch):
    """Review focus 1: under ATOMIC_REQUESTS the view's atomic is a savepoint, so cv_on_commit
    waits for the request transaction, i.e. runs after the view returned."""
    from django.db import connection

    from tests.test1.app.views import PublisherCreateView

    order: list[str] = []
    original_redirect = PublisherCreateView.cv_form_valid_redirect

    def redirect(self, context):
        order.append("redirect")
        return original_redirect(self, context)

    monkeypatch.setitem(connection.settings_dict, "ATOMIC_REQUESTS", True)
    monkeypatch.setattr(PublisherCreateView, "cv_on_commit", lambda self, context: order.append("commit"))
    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_redirect", redirect)
    response = client_user_publisher_add.post("/publisher/create/", {"name": "Deferred"})
    assert response.status_code == 302
    assert order == ["redirect", "commit"]


@pytest.mark.django_db
def test_parent_fk_create_rolls_back(client_user_book_add, publisher_penguin, monkeypatch):
    from tests.test1.app.models import Book
    from tests.test1.app.views import BookCreateView

    monkeypatch.setattr(BookCreateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_book_add.post(f"/publisher/{publisher_penguin.pk}/book/create/", {"title": "Orphan"})
    assert not Book.objects.filter(title="Orphan").exists()


@pytest.mark.django_db
def test_m2m_parent_create_links_parent(client_user_genre_add, publisher_penguin):
    from tests.test1.app.models import Genre

    response = client_user_genre_add.post(f"/publisher/{publisher_penguin.pk}/genre/create/", {"name": "Sci-Fi"})
    assert response.status_code == 302
    assert list(publisher_penguin.genres.values_list("name", flat=True)) == ["Sci-Fi"]
    assert Genre.objects.count() == 1


@pytest.mark.django_db
def test_m2m_add_failure_leaves_no_orphan(client_user_genre_add, publisher_penguin, monkeypatch):
    """The object is saved before m2m.add(); a failure in between must roll the save back."""
    from tests.test1.app.models import Genre
    from tests.test1.app.views import GenreCreateView

    monkeypatch.setattr(GenreCreateView, "cv_parent_many_to_many_through_defaults", _boom)
    with pytest.raises(Boom):
        client_user_genre_add.post(f"/publisher/{publisher_penguin.pk}/genre/create/", {"name": "Orphan"})
    assert not Genre.objects.filter(name="Orphan").exists()


@pytest.mark.django_db
def test_polymorphic_create_goes_through_seam(
    client_user_vehicle_add, monkeypatch, django_capture_on_commit_callbacks
):
    from django.contrib.contenttypes.models import ContentType

    from tests.test1.app.models import Car
    from tests.test1.app.views import VehicleCreateView

    calls = _record_on_commit(monkeypatch, VehicleCreateView)
    car_ct = ContentType.objects.get_for_model(Car)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_vehicle_add.post(f"/vehicle/create//ct/{car_ct.id}/", {"name": "Coupe", "doors": 2})
    assert response.status_code == 302
    assert len(calls) == 1
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py -v`
Expected:
- FAIL: `test_create_hook_exception_rolls_back_save`, `test_update_hook_exception_rolls_back_save`, `test_custom_form_view_write_rolls_back`, `test_parent_fk_create_rolls_back`, `test_m2m_add_failure_leaves_no_orphan` (row still exists), and every `cv_on_commit` test (`calls == []` / `order == ["redirect"]`).
- PASS already (guards): `test_create_hook_exception_keeps_row_without_atomic`, `test_on_commit_not_called_for_invalid_form`, `test_on_commit_not_called_after_rollback`, `test_m2m_parent_create_links_parent`.

Check the failure **reasons** yourself; don't trust a summary line. `test_on_commit_error_keeps_committed_data` fails because `Boom` is never raised.

- [ ] **Step 4: Implement `cv_form_valid_process`**

In `src/crud_views/lib/views/mixins.py`, add `from functools import partial` (stdlib block) and `from django.db import transaction` (Django block). In `CrudViewProcessFormMixin.post`, replace

```python
        if self.cv_form_is_valid(context):
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            return self.cv_form_valid_redirect(context)
```

with

```python
        if self.cv_form_is_valid(context):
            self.cv_form_valid_process(context)
            return self.cv_form_valid_redirect(context)
```

and add this method directly after `post()`:

```python
    def cv_form_valid_process(self, context: dict) -> None:
        """
        Write phase of a valid POST: cv_form_valid and cv_form_valid_hook run inside
        cv_get_atomic(); cv_on_commit is scheduled to run after the commit (never after a
        rollback). A subclass overriding post() should call this to keep the transaction.
        """
        with self.cv_get_atomic():
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())
```

Also update the class docstring's first line from `Mixin for create and update views.` to `Mixin for form-processing views (create, update, delete, custom forms, workflow).`

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py -v`
Expected: all PASS.

Run: `.venv/bin/python -m pytest tests/test1 -q`
Expected: all PASS. If `test_conditional_formset.py::test_purge_rolls_back_when_sibling_formset_save_fails` or a workflow test fails here, stop and report; Tasks 5/6 own those files.

- [ ] **Step 6: Commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check --fix src tests
git add src/crud_views/lib/views/mixins.py tests/test1/app/models.py tests/test1/app/views.py tests/test1/app/urls.py tests/test1/test_transactions.py
git commit -m "feat: form views run their write phase in a transaction, add cv_on_commit (#31)"
```

---

### Task 3: DeleteView uses the seam

**Files:**
- Modify: `src/crud_views/lib/views/delete.py` (`DeleteView.post`, ~lines 197–218)
- Modify: `tests/test1/test_transactions.py` (append)

**Interfaces:**
- Consumes: `CrudViewProcessFormMixin.cv_form_valid_process(context)` from Task 2 (DeleteView already inherits it).
- Produces: nothing new.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_transactions.py`:

```python
# --- Task 3: delete views ----------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_hook_exception_keeps_object(client_user_publisher_delete, monkeypatch):
    from tests.test1.app.views import PublisherDeleteView

    publisher = Publisher.objects.create(name="Survivor")
    monkeypatch.setattr(PublisherDeleteView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_delete.post(f"/publisher/{publisher.pk}/delete/", {"confirm": True})
    assert Publisher.objects.filter(pk=publisher.pk).exists()


@pytest.mark.django_db
def test_delete_runs_on_commit(client_user_publisher_delete, monkeypatch, django_capture_on_commit_callbacks):
    from tests.test1.app.views import PublisherDeleteView

    publisher = Publisher.objects.create(name="Gone")
    calls = _record_on_commit(monkeypatch, PublisherDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_publisher_delete.post(f"/publisher/{publisher.pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert len(calls) == 1
    assert not Publisher.objects.filter(pk=publisher.pk).exists()


@pytest.mark.django_db
def test_delete_protection_skips_write_phase(
    client_user_publisher_protected_delete, monkeypatch, django_capture_on_commit_callbacks
):
    """Review focus 3: a protection veto renders the form again; no delete, no cv_on_commit."""
    from tests.test1.app.views import PublisherProtectedDeleteView

    publisher = Publisher.objects.create(name="Protected")
    calls = _record_on_commit(monkeypatch, PublisherProtectedDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_publisher_protected_delete.post(
            f"/publisher_protected/{publisher.pk}/delete/", {"confirm": True}
        )
    assert response.status_code == 200
    assert calls == []
    assert Publisher.objects.filter(pk=publisher.pk).exists()


@pytest.mark.django_db
def test_modal_delete_runs_on_commit_and_keeps_204(
    client_user_author_modal, author_douglas_adams, monkeypatch, django_capture_on_commit_callbacks
):
    """Review focus 2: modal submits answer 204 + X-CV-Redirect and still run cv_on_commit."""
    from tests.test1.app.views import AuthorModalDeleteView

    calls = _record_on_commit(monkeypatch, AuthorModalDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_author_modal.post(
            f"/author_modal/{author_douglas_adams.pk}/delete/", {"confirm": True}, headers={"X-CV-Modal": "true"}
        )
    assert response.status_code == 204
    assert response.headers["X-CV-Redirect"] == "/author_modal/"
    assert len(calls) == 1


@pytest.mark.django_db
def test_guardian_delete_goes_through_seam(
    client_guardian, user_guardian, publisher_a, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.lib.helper.guardian import user_guardian_object_perm
    from tests.test1.app.views import GuardianPublisherCascadeDeleteView, cv_guardian_publisher_cascade

    user_guardian_object_perm(user_guardian, cv_guardian_publisher_cascade, "delete", publisher_a)
    calls = _record_on_commit(monkeypatch, GuardianPublisherCascadeDeleteView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_guardian.post(f"/guardian_publisher_cascade/{publisher_a.pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert len(calls) == 1
```

(The protected-delete URL prefix is the viewset name `publisher_protected`. If the GET in `tests/test1/test_delete.py` uses a different path for `cv_publisher_protected`, copy that path.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py -v -k "delete"`
Expected:
- FAIL: `test_delete_hook_exception_keeps_object` (object deleted), `test_delete_runs_on_commit`, `test_modal_delete_runs_on_commit_and_keeps_204`, `test_guardian_delete_goes_through_seam` (`calls == []`).
- PASS (guard): `test_delete_protection_skips_write_phase`.

- [ ] **Step 3: Implement**

In `src/crud_views/lib/views/delete.py`, `DeleteView.post`, replace

```python
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            return self.cv_form_valid_redirect(context)
```

with

```python
            self.cv_form_valid_process(context)
            return self.cv_form_valid_redirect(context)
```

Leave everything else in `post()` unchanged; the protection branch stays outside the transaction.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py tests/test1/test_delete.py tests/test1/test_modal.py tests/test1/test_guardian_delete.py tests/test1/test_success_origin.py -v`
Expected: all PASS (`test_success_origin.py` pins the #167 success-URL-after-delete order).

- [ ] **Step 5: Commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check --fix src tests
git add src/crud_views/lib/views/delete.py tests/test1/test_transactions.py
git commit -m "feat: DeleteView runs its write phase in a transaction (#31)"
```

---

### Task 4: ActionView seam (`cv_action_process`)

**Files:**
- Modify: `src/crud_views/lib/views/action.py`
- Modify: `tests/test1/test_transactions.py` (append)

**Interfaces:**
- Consumes: `cv_get_atomic()`, `cv_get_db_alias()`, `cv_on_commit()` (Task 1).
- Produces: `ActionView.cv_action_process(self, context: dict) -> bool`, which returns the `action()` result.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_transactions.py`:

```python
# --- Task 4: action views ----------------------------------------------------------------------


@pytest.fixture
def author(db):
    from tests.test1.app.models import Author

    return Author.objects.create(first_name="First", last_name="Author")


def _write_pseudonym(value: str, result: bool, rollback: bool = False):
    def action(self, context):
        self.object.pseudonym = value
        self.object.save()
        if rollback:
            transaction.set_rollback(True)
        return result

    return action


@pytest.mark.django_db
def test_action_success_hook_exception_rolls_back(client_user_author_change, author, monkeypatch):
    from tests.test1.app.views import AuthorHookPingView

    monkeypatch.setattr(AuthorHookPingView, "action", _write_pseudonym("acted", True))
    monkeypatch.setattr(AuthorHookPingView, "cv_action_success_hook", _boom)
    with pytest.raises(Boom):
        client_user_author_change.post(f"/author/{author.pk}/ping-hook/")
    author.refresh_from_db()
    assert author.pseudonym is None


@pytest.mark.django_db
def test_action_false_does_not_roll_back(
    client_user_author_change, author, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.views import AuthorPingView

    calls = _record_on_commit(monkeypatch, AuthorPingView)
    monkeypatch.setattr(AuthorPingView, "action", _write_pseudonym("partial", False))
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_author_change.post(f"/author/{author.pk}/ping/")
    assert response.status_code == 302
    author.refresh_from_db()
    assert author.pseudonym == "partial"
    assert calls == []


@pytest.mark.django_db
def test_action_set_rollback_recipe(client_user_author_change, author, monkeypatch):
    """docs recipe 'Rolling back a failed action': set_rollback(True) undoes the action's writes."""
    from tests.test1.app.views import AuthorPingView

    monkeypatch.setattr(AuthorPingView, "action", _write_pseudonym("undone", False, rollback=True))
    response = client_user_author_change.post(f"/author/{author.pk}/ping/")
    assert response.status_code == 302
    author.refresh_from_db()
    assert author.pseudonym is None


@pytest.mark.django_db
def test_action_false_without_atomic_keeps_partial_write(
    client_user_author_change, author, monkeypatch, django_capture_on_commit_callbacks
):
    """Review focus 5: cv_atomic = False + False result: no error, no cv_on_commit, write stays."""
    from tests.test1.app.views import AuthorPingView

    calls = _record_on_commit(monkeypatch, AuthorPingView)
    monkeypatch.setattr(AuthorPingView, "cv_atomic", False)
    monkeypatch.setattr(AuthorPingView, "action", _write_pseudonym("partial", False))
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_author_change.post(f"/author/{author.pk}/ping/")
    assert response.status_code == 302
    author.refresh_from_db()
    assert author.pseudonym == "partial"
    assert calls == []


@pytest.mark.django_db
def test_action_on_commit_runs_on_success(
    client_user_author_change, author, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.views import AuthorPingView

    calls = _record_on_commit(monkeypatch, AuthorPingView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_author_change.post(f"/author/{author.pk}/ping/")
    assert response.status_code == 302
    assert len(calls) == 1
    assert calls[0]["object"] == author


@pytest.mark.django_db
def test_ordered_up_hook_exception_rolls_back_swap(client_user_author_change, monkeypatch):
    from tests.test1.app.models import Author
    from tests.test1.app.views import AuthorUpView

    first = Author.objects.create(first_name="A", last_name="First")
    second = Author.objects.create(first_name="B", last_name="Second")
    before = {a.pk: a.order for a in Author.objects.all()}
    monkeypatch.setattr(AuthorUpView, "cv_action_success_hook", _boom)
    with pytest.raises(Boom):
        client_user_author_change.post(f"/author/{second.pk}/up/")
    assert {a.pk: a.order for a in Author.objects.all()} == before
    assert len(before) == 2 and first.pk in before  # both rows took part


@pytest.mark.django_db
def test_resource_action_runs_on_commit_without_transaction(
    client_user_s3file_delete, monkeypatch, django_capture_on_commit_callbacks
):
    import hashlib

    from tests.test1.app import resources

    monkeypatch.setattr(resources, "TOUCHED", [])
    calls = _record_on_commit(monkeypatch, resources.S3FileTouchView)
    key = hashlib.md5(b"reports/2026/q1.pdf").hexdigest()
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_s3file_delete.post(f"/s3file/{key}/touch/")
    assert response.status_code == 302
    assert len(calls) == 1
    assert resources.TOUCHED == ["reports/2026/q1.pdf"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py -v -k "action or ordered or resource_action"`
Expected:
- FAIL: `test_action_success_hook_exception_rolls_back` (pseudonym `"acted"`), `test_ordered_up_hook_exception_rolls_back_swap` (order changed), `test_action_on_commit_runs_on_success` and `test_resource_action_runs_on_commit_without_transaction` (`calls == []`), and `test_action_set_rollback_recipe` (fails with `TransactionManagementError` or a non-None pseudonym, because there is no inner atomic yet and the flag hits the test's own transaction).
- PASS (guards): `test_action_false_does_not_roll_back`, `test_action_false_without_atomic_keeps_partial_write`.

- [ ] **Step 3: Implement**

Replace the top of `src/crud_views/lib/views/action.py` (imports + `post`) with:

```python
from functools import partial

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class ActionView(CrudView, SingleObjectMixin, generic.View):
    cv_list_action_method = "post"
    cv_action_messages: bool = True  # set False to suppress success/error messages

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        self.cv_action_process(context)
        url = self.get_success_url()
        return HttpResponseRedirect(url)

    def cv_action_process(self, context: dict) -> bool:
        """
        Write phase of the action: action() and the success/error message + hook run inside
        cv_get_atomic(); on success cv_on_commit is scheduled to run after the commit.
        A falsy result does NOT roll back; call transaction.set_rollback(True) in action() for that.
        """
        with self.cv_get_atomic():
            result = self.action(context)
            if result:
                self.cv_action_success(context)
                transaction.on_commit(partial(self.cv_on_commit, context), using=self.cv_get_db_alias())
            else:
                self.cv_action_error(context)
        return result
```

Keep `action`, `cv_action_success`, `cv_action_error`, the two hooks and `ActionViewPermissionRequired` unchanged below it.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py tests/test1/test_action_messages.py tests/test1/test_action_ordered.py tests/test1/test_resource_views.py tests/test1/test_card_action_post.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check --fix src tests
git add src/crud_views/lib/views/action.py tests/test1/test_transactions.py
git commit -m "feat: ActionView runs action() in a transaction, add cv_action_process (#31)"
```

---

### Task 5: Workflow: routed inner atomic + `workflow_info` in context

**Files:**
- Modify: `src/crud_views_workflow/lib/views.py` (`WorkflowView.cv_form_valid`, ~lines 85–132)
- Modify: `tests/test1/test_transactions.py` (append)

**Interfaces:**
- Consumes: `cv_get_db_alias()` (Task 1), `cv_form_valid_process` (Task 2; `WorkflowView` inherits it via `CustomFormView`).
- Produces: `context["workflow_info"]`, the `WorkflowInfo` instance, set before `on_transition` is called.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_transactions.py`:

```python
# --- Task 5: workflow --------------------------------------------------------------------------


@pytest.mark.django_db
def test_workflow_on_transition_exception_rolls_back_state_and_info(
    client_user_campaign_change, campaign_new, monkeypatch
):
    """Guard: passes before and after (the inner atomic already existed)."""
    from crud_views_workflow.models import WorkflowInfo
    from tests.test1.app.models import CampaignState
    from tests.test1.app.views import CampaignWorkflowView

    monkeypatch.setattr(CampaignWorkflowView, "on_transition", _boom)
    with pytest.raises(Boom):
        client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
        )
    campaign_new.refresh_from_db()
    assert campaign_new.state == CampaignState.NEW
    assert WorkflowInfo.objects.count() == 0


@pytest.mark.django_db
def test_workflow_info_available_in_on_commit(
    client_user_campaign_change, campaign_new, monkeypatch, django_capture_on_commit_callbacks
):
    from tests.test1.app.models import CampaignState
    from tests.test1.app.views import CampaignWorkflowView

    calls = _record_on_commit(monkeypatch, CampaignWorkflowView)
    with django_capture_on_commit_callbacks(execute=True):
        response = client_user_campaign_change.post(
            f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
        )
    assert response.status_code == 302
    assert len(calls) == 1
    info = calls[0]["workflow_info"]
    assert info.transition == "wf_activate"
    assert info.state_new == CampaignState.ACTIVE


@pytest.mark.django_db
def test_workflow_inner_atomic_uses_routed_alias(client_user_campaign_change, campaign_new, monkeypatch):
    """With cv_atomic = False the transition is still atomic, on the routed alias (not a bare atomic())."""
    from tests.test1.app.views import CampaignWorkflowView

    seen: list = []
    real_atomic = transaction.atomic

    def spy(*args, **kwargs):
        seen.append(kwargs.get("using"))
        return real_atomic(*args, **kwargs)

    monkeypatch.setattr(CampaignWorkflowView, "cv_atomic", False)
    monkeypatch.setattr("crud_views_workflow.lib.views.transaction.atomic", spy)
    response = client_user_campaign_change.post(
        f"/campaign/{campaign_new.pk}/workflow/", {"transition": "wf_activate", "comment": ""}
    )
    assert response.status_code == 302
    assert DEFAULT_DB_ALIAS in seen
    assert None not in seen  # every atomic() in the request names its database
```

Note: `monkeypatch.setattr("crud_views_workflow.lib.views.transaction.atomic", spy)` patches the `atomic` attribute of `django.db.transaction`, so it sees every `atomic()` in the request (including Django's own, which always pass `using=`). The assertion only requires that none is called bare.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py -v -k workflow`
Expected:
- FAIL: `test_workflow_info_available_in_on_commit` (`KeyError: 'workflow_info'`) and `test_workflow_inner_atomic_uses_routed_alias` (`None in seen`).
- PASS (guard): `test_workflow_on_transition_exception_rolls_back_state_and_info`.

- [ ] **Step 3: Implement**

In `src/crud_views_workflow/lib/views.py`, `WorkflowView.cv_form_valid`:

1. Change `with transaction.atomic():` to `with transaction.atomic(using=self.cv_get_db_alias()):`.
2. Directly after the `info = WorkflowInfo.objects.create(...)` statement and before `# call hook`, add:

```python
            # expose the transition record to cv_on_commit (side effects after commit)
            context["workflow_info"] = info
```

3. Replace the `on_transition` docstring with:

```python
        """
        Override for database follow-ups of a transition. Runs inside the transaction, so
        writes here roll back together with the transition. Put side effects (mail, Celery,
        webhooks) in cv_on_commit instead; context["workflow_info"] holds the record there.
        """
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test1/test_transactions.py tests/test1/test_workflow.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check --fix src tests
git add src/crud_views_workflow/lib/views.py tests/test1/test_transactions.py
git commit -m "feat: workflow transitions use the routed database, expose workflow_info to cv_on_commit (#31)"
```

---

### Task 6: Formsets: routed inner atomic

**Files:**
- Modify: `src/crud_views/lib/formsets/mixins.py` (`FormSetMixinBase.cv_form_valid`, ~line 98)
- Modify: `tests/test1/test_conditional_formset.py` (`test_purge_rolls_back_when_sibling_formset_save_fails`, the `_Base` stub ~line 167)

**Interfaces:**
- Consumes: `cv_get_db_alias()` (Task 1). Real views get it from `CrudView`; the test stub defines its own.
- Produces: nothing new.

- [ ] **Step 1: Make the existing test assert routing (failing)**

In `tests/test1/test_conditional_formset.py`, `test_purge_rolls_back_when_sibling_formset_save_fails`, replace

```python
    class _Base:
        def cv_form_valid(self, context):
            context["form"].save()
```

with

```python
    aliases: list[str] = []

    class _Base:
        # cv_atomic = False and no cv_get_atomic(): only the formset mixin's own inner
        # atomic() protects the purge here, which must hold regardless of the view setting
        cv_atomic = False

        def cv_get_db_alias(self):
            aliases.append("default")
            return "default"

        def cv_form_valid(self, context):
            context["form"].save()
```

and add at the end of the test, after the existing `assert ProfileItem…` line:

```python
    assert aliases == ["default"]  # the inner atomic() uses the routed database
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test1/test_conditional_formset.py::test_purge_rolls_back_when_sibling_formset_save_fails -v`
Expected: FAIL on `assert aliases == ["default"]` (`[] != ['default']`). The rollback assertion above it still passes.

- [ ] **Step 3: Implement**

In `src/crud_views/lib/formsets/mixins.py`, `FormSetMixinBase.cv_form_valid`, change `with transaction.atomic():` to `with transaction.atomic(using=self.cv_get_db_alias()):` and extend the docstring's last sentence:

```python
        """
        Save form and formsets — atomically: a conditional purge issues a DELETE
        before sibling formsets save, so a failure later in the flow must roll
        the whole write (main form, purge, formsets) back. This inner block holds
        even with cv_atomic = False; with cv_atomic = True it is a savepoint.
        """
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test1/test_conditional_formset.py tests/test1/test_formsets.py tests/test1/test_formsets_save_order.py tests/test1/test_formsets_bugs.py tests/test1/test_formsets_ergonomics.py tests/test1/test_formsets_parent_required.py tests/test1/test_formsets_validation_gate.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check --fix src tests
git add src/crud_views/lib/formsets/mixins.py tests/test1/test_conditional_formset.py
git commit -m "fix: formset save transaction uses the routed database (#31)"
```

---

### Task 7: Reference page `request_lifecycle.md` + nav + anchor validation

**Files:**
- Create: `docs/reference/request_lifecycle.md`
- Modify: `docs/reference/.pages`
- Modify: `mkdocs.yml`

**Interfaces:**
- Consumes: the final API from Tasks 1–6.
- Produces: stable anchors that Task 8 links to:
  - `#call-chains`
  - `#hook-reference`
  - `#transactions`
  - `#side-effects-after-commit`
  - `#rolling-back-a-failed-action`
  - `#catching-integrityerror`
  - `#durable-services`
  - `#resource-views-writing-orm-rows`
  - `#multiple-databases`
  - `#limitations`
  - `#migrating`

  MkDocs derives each anchor from its heading (lowercase, spaces to `-`, punctuation dropped), so the headings below must stay **exactly** as written.

- [ ] **Step 1: Turn on anchor validation**

Append to `mkdocs.yml`:

```yaml

validation:
    anchors: warn
```

Run: `.venv/bin/mkdocs build --strict -d /tmp/cv-site`
Expected: build succeeds (verified on 2026-10-08: the current docs have no broken anchors).

Prove the check bites: temporarily add `[x](faq.md#no-such-anchor)` to `docs/index.md`, rerun, and confirm the build **aborts** with a warning about `no-such-anchor`. Then remove the line again.

- [ ] **Step 2: Write the page**

Create `docs/reference/request_lifecycle.md` with exactly this content:

````markdown
# Request lifecycle, transactions & hooks

Every write in django-crud-views (create, update, delete, custom forms, workflow transitions and
actions) goes through one of three POST handlers. This page shows the order in which your
overrides are called, which of them run inside the database transaction, and where to put side
effects such as e-mails or Celery tasks.

!!! note "Changed in 0.27.0"
    Before 0.27.0 only formsets and workflow transitions ran in a transaction, and there was no
    `cv_on_commit`. See [Migrating](#migrating) if you override `cv_form_valid_hook` or the action
    hooks.

## Overview

GET requests never write. POST requests are handled by one of three methods:

| POST handler | Used by |
|---|---|
| `CrudViewProcessFormMixin.post` | `CreateView`, `UpdateView`, `CustomFormView`, `CustomFormNoObjectView`, `WorkflowView`, polymorphic create/update |
| `DeleteView.post` | `DeleteView`, polymorphic delete |
| `ActionView.post` | `ActionView`, `OrderedUpView`, `OrderedDownView` |

Each handler has three phases:

1. **Outside the transaction:** load the object, build the context, validate.
2. **In the transaction (the write phase):** your write code and its follow-up hook. If anything
   raises, everything written in this phase is rolled back.
3. **After the commit:** `cv_on_commit(context)`, then the redirect.

## Call chains

`[atomic: …]` is the block inside `cv_get_atomic()`. `⇢ cv_on_commit` means "registered here,
runs after the commit".

### Form views

```text
get_object (if cv_object) → get_context_data → cv_post_hook → cv_form_is_valid
  valid:   cv_form_valid_process [atomic: cv_form_valid → cv_form_valid_hook ⇢ cv_on_commit]
           → cv_form_valid_redirect
  invalid: cv_form_invalid_hook → cv_form_invalid
```

### Delete views

```text
get_object → get_context_data (delete protection, related objects) → cv_post_hook → cv_form_is_valid
  valid + protection errors: render the form again (422 in a modal)
  valid:   cv_form_valid_process [atomic: cv_form_valid (delete) → cv_form_valid_hook ⇢ cv_on_commit]
           → cv_form_valid_redirect
  invalid: cv_form_invalid_hook → cv_form_invalid
```

The success URL is resolved after the delete, so it must not point at the deleted object
(system check `viewset.E254`).

### Action views

```text
get_object → get_context_data
  → cv_action_process [atomic: action() → cv_action_success (message + hook) ⇢ cv_on_commit
                                       | cv_action_error (message + hook)]
  → get_success_url → redirect
```

`cv_form_valid_process(context)` and `cv_action_process(context)` own the transaction. If you
override `post()`, call them instead of `cv_form_valid` / `action()` directly to keep it.

## Hook reference

| Hook | Views | Phase | Use it for | DB writes | Side effects | Call `super()`? |
|---|---|---|---|---|---|---|
| `cv_post_hook(context)` | form, delete | outside | preparing the context | not atomic | no | optional (base is empty) |
| `cv_form_is_valid(context) -> bool` | form, delete | outside | extra validation | no | no | yes (formsets extend it) |
| `cv_form_valid(context)` | form, delete | in transaction | the write itself | yes | no, use `cv_on_commit` | yes, unless you replace the save |
| `cv_form_valid_hook(context)` | form, delete | in transaction | follow-up writes, messages (`MessageMixin`) | yes | no, use `cv_on_commit` | yes (`MessageMixin` relies on it) |
| `cv_parent_many_to_many_through_defaults(...)` | create with m2m parent | in transaction | through-model defaults | n/a | no | no |
| `on_transition(info, ...)` | workflow | in transaction | database follow-ups of a transition | yes | no, use `cv_on_commit` | optional (base is empty) |
| `action(context) -> bool` | action | in transaction | the action itself | yes | no, use `cv_on_commit` | n/a |
| `cv_action_success_hook(context)` | action | in transaction | follow-up writes | yes | no, use `cv_on_commit` | optional |
| `cv_action_error_hook(context)` | action | in transaction | failure audit rows | yes | no | optional |
| `cv_on_commit(context)` | form, delete, action | after commit | mail, Celery, webhooks, cache invalidation | not atomic with the write | **yes** | optional (base is empty) |
| `cv_check_delete_protection() -> list[str]` | delete | outside | vetoing a delete | no | no | optional |
| `cv_form_invalid(context)` | form, delete | outside | custom invalid response | no | no | optional |
| `cv_form_invalid_hook(context)` | form, delete | outside | logging invalid submits | no | no | optional |
| `cv_form_valid_redirect(context)` | form, delete | after the write phase | custom success response | no | no | optional |

`cv_on_commit` runs only on success: never for an invalid form, never after a rollback, never when
`action()` returned `False`. `context["object"]` is the saved object where the view has one (for
deletes, the deleted instance with `pk=None`). For workflow views, `context["workflow_info"]` is the `WorkflowInfo` record
of the transition.

## Transactions

| Name | Kind | Default | Meaning |
|---|---|---|---|
| `cv_atomic` | attribute | `True` (`False` on `ResourceViewMixin`) | wrap the write phase in `transaction.atomic()` |
| `cv_get_db_alias()` | method | `router.db_for_write(viewset.model)` | database of the transaction and of `cv_on_commit` |
| `cv_get_atomic()` | method | `atomic(using=cv_get_db_alias())`, or `nullcontext()` when `cv_atomic` is `False` | the context manager around the write phase |

When `cv_on_commit` runs:

| Situation | `cv_on_commit` runs |
|---|---|
| `cv_atomic = True`, autocommit (Django's default) | right after the view's transaction commits, before the redirect |
| `cv_atomic = False`, autocommit | immediately, because there is no transaction to wait for |
| `ATOMIC_REQUESTS = True` | when the request transaction commits, after the view has returned |
| the write phase raised, or `transaction.set_rollback(True)` was called | never |

With `ATOMIC_REQUESTS = True` the view's own `atomic()` becomes a savepoint inside the request
transaction. That costs almost nothing, and an error in the write phase still rolls back only that
phase.

Formsets and workflow transitions have their own inner `atomic()` on the same database. It keeps
"purge + formset saves" and "state change + `WorkflowInfo`" all-or-nothing even with
`cv_atomic = False`.

If `cv_on_commit` raises, the data stays committed and the request ends with a server error.

## Recipes

### Side effects after commit

Never send mail, start Celery tasks or call webhooks from `cv_form_valid_hook`, `action()` or
`on_transition`: they run before the commit. A Celery worker can pick up the task before the row
is visible (`DoesNotExist`), and if the transaction rolls back, the mail is already gone. Use
`cv_on_commit`:

```python
from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.views import CreateViewPermissionRequired, MessageMixin


class OrderCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_order
    form_class = OrderForm

    def cv_on_commit(self, context):
        send_order_confirmation.delay(self.object.pk)
```

Workflow views get the transition record in the context:

```python
from crud_views_workflow.lib import WorkflowViewPermissionRequired


class CampaignWorkflowView(CrispyViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm

    def cv_on_commit(self, context):
        info = context["workflow_info"]
        send_notification(self.object, info.state_new, info.user)
```

In tests, `cv_on_commit` callbacks only run when you capture them, for example with
pytest-django's `django_capture_on_commit_callbacks(execute=True)` fixture or Django's
`TestCase.captureOnCommitCallbacks(execute=True)`.

### Rolling back a failed action

Returning `False` from `action()` shows the error message but does **not** roll back what
`action()` already wrote; a failure audit row written in `cv_action_error_hook` should survive. To
undo the action's writes, mark the transaction for rollback:

```python
from django.db import transaction

from crud_views.lib.views import ActionViewPermissionRequired


class ArchiveView(ActionViewPermissionRequired):
    cv_viewset = cv_document
    cv_key = "archive"
    cv_path = "archive"

    def action(self, context) -> bool:
        self.object.archived = True
        self.object.save()
        if not archive_storage.store(self.object):
            transaction.set_rollback(True)  # undo the save above
            return False
        return True
```

`set_rollback(True)` needs a transaction: with `cv_atomic = False` it raises
`TransactionManagementError`.

### Catching IntegrityError

`cv_form_valid` runs inside a transaction. On PostgreSQL, a caught database error leaves that
transaction unusable, and the next query raises `TransactionManagementError`. Wrap the statement
that may fail in its own `atomic()` so only that savepoint is rolled back:

```python
from django.db import IntegrityError, transaction


class TagCreateView(CrispyViewMixin, CreateViewPermissionRequired):
    cv_viewset = cv_tag
    form_class = TagForm

    def cv_form_valid(self, context):
        try:
            with transaction.atomic(using=self.cv_get_db_alias()):
                super().cv_form_valid(context)
        except IntegrityError:
            # a concurrent request created the same tag: use that one
            self.object = Tag.objects.get(name=context["form"].cleaned_data["name"])
            context["object"] = self.object
```

### Durable services

A service that opens `transaction.atomic(durable=True)` refuses to run inside another transaction
and raises `RuntimeError`. Turn the view's transaction off and let the service own it:

```python
from crud_views.lib.views.form import CustomFormViewPermissionRequired


class ImportView(CustomFormViewPermissionRequired):
    cv_viewset = cv_dataset
    cv_key = "import"
    cv_path = "import"
    form_class = ImportForm
    cv_atomic = False  # run_import() opens atomic(durable=True) itself

    def cv_form_valid(self, context):
        run_import(self.object, context["form"].cleaned_data["file"])
```

For a different boundary (for example `savepoint=False`), override `cv_get_atomic()` and return
your own context manager.

### Resource views writing ORM rows

`ResourceViewMixin` sets `cv_atomic = False`: a database transaction cannot roll back an S3 upload
or an API call. If a Resource view also writes ORM rows that must commit together, turn the
transaction on, name the database, and move the external call to `cv_on_commit` so it only happens
once the rows are committed:

```python
from django.db import router

from crud_views.lib.resource import ResourceViewMixin
from crud_views.lib.views import ActionViewPermissionRequired


class S3FileArchiveView(ResourceViewMixin, ActionViewPermissionRequired):
    cv_viewset = cv_s3file
    cv_key = "archive"
    cv_path = "archive"
    cv_atomic = True

    def cv_get_db_alias(self) -> str:
        return router.db_for_write(ArchiveLog)

    def action(self, context) -> bool:
        ArchiveLog.objects.create(key=self.object.key, user=self.request.user)
        return True

    def cv_on_commit(self, context):
        s3.copy_to_archive(self.object.key)
```

### Multiple databases

`cv_get_db_alias()` asks your `DATABASE_ROUTERS` for the write database of the ViewSet's model;
the transaction and `cv_on_commit` both use it. Override it when the write phase mainly targets
another model. Django has no transactions across databases: writes to a second database inside
`cv_form_valid` are not rolled back with the first.

## Limitations

- **No transactions across databases.** If a router sends `WorkflowInfo` or formset child models
  to a different database than the view's model, those writes are not atomic with the main write.
- **Checks run before the transaction.** Delete protection (`cv_check_delete_protection`) and the
  workflow permission check run outside the transaction and do not lock rows
  (no `select_for_update`). Two concurrent requests can both pass the check.
- **Inner blocks are always atomic.** Formset saves and workflow transitions keep their own
  `atomic()` even with `cv_atomic = False`.

## Migrating

Coming from 0.26 or earlier, four behaviours changed:

**1. `cv_form_valid_hook`, `cv_action_success_hook` and `cv_action_error_hook` run before the
commit.** Move side effects to `cv_on_commit`:

```python
# before
def cv_form_valid_hook(self, context):
    super().cv_form_valid_hook(context)
    notify_team.delay(self.object.pk)

# after
def cv_on_commit(self, context):
    notify_team.delay(self.object.pk)
```

**2. An exception in those hooks rolls back the write.** Before, the object stayed saved and the
request failed. If you relied on "saved even if the follow-up fails", catch the exception in the
hook or move the follow-up to `cv_on_commit`.

**3. `try/except IntegrityError` inside `cv_form_valid` needs a nested `atomic()`** on PostgreSQL.
See [Catching IntegrityError](#catching-integrityerror).

**4. `atomic(durable=True)` called from the write phase raises `RuntimeError`.** Set
`cv_atomic = False` on that view. See [Durable services](#durable-services).

To get the old behaviour for one view, set `cv_atomic = False`. Hooks then run in autocommit mode
as before, and `cv_on_commit` runs immediately after the write phase.
````

- [ ] **Step 3: Add the page to the nav**

In `docs/reference/.pages`, under `- Core views:`, after `- nested.md`, add:

```yaml
        - Request lifecycle & transactions: request_lifecycle.md
```

- [ ] **Step 4: Build**

Run: `.venv/bin/mkdocs build --strict -d /tmp/cv-site`
Expected: success, with no warnings about `request_lifecycle.md`. Open `/tmp/cv-site/reference/request_lifecycle/index.html` and check that each anchor in the Interfaces list exists: `grep -o 'id="[a-z-]*"' /tmp/cv-site/reference/request_lifecycle/index.html`.

- [ ] **Step 5: Commit**

```bash
git add docs/reference/request_lifecycle.md docs/reference/.pages mkdocs.yml
git commit -m "docs: request lifecycle, transactions & hooks reference page (#31)"
```

---

### Task 8: FAQ entries + cross-links in existing pages

**Files:**
- Modify: `docs/faq.md` (append before `## Why is my \`cv_*\` attribute silently ignored? (check W280)`, the last entry)
- Modify: `docs/reference/create_view.md` (~line 135, "Form Processing Hooks")
- Modify: `docs/reference/update_view.md` (~line 158)
- Modify: `docs/reference/delete_view.md` (~line 73)
- Modify: `docs/reference/custom_form_view.md` (~line 84)
- Modify: `docs/reference/action_view.md` (~line 47, "Hooks")
- Modify: `docs/reference/workflow_view.md` (~line 323, "`on_transition` hook")
- Modify: `docs/reference/formsets.md` (line ~114)
- Modify: `docs/reference/conditional.md` (line ~103)
- Modify: `docs/development/stability.md` (~line 58 and ~line 68)

**Interfaces:**
- Consumes: the anchors from Task 7.
- Produces: nothing.

- [ ] **Step 1: FAQ entries**

Insert into `docs/faq.md`, directly before the `## Why is my \`cv_*\` attribute silently ignored? (check W280)` heading:

````markdown
## How do I send an email or start a Celery task after a save?

Override `cv_on_commit(context)`. It runs after the database transaction has committed, and never
after a rollback. Don't use `cv_form_valid_hook`: it runs inside the transaction.

```python
def cv_on_commit(self, context):
    send_welcome_mail.delay(self.object.pk)
```

See [Side effects after commit](reference/request_lifecycle.md#side-effects-after-commit).

## Why does my Celery task sometimes raise `DoesNotExist`?

The task was started inside the transaction (from `cv_form_valid_hook`, `action()` or
`on_transition`), and the worker ran it before the commit made the row visible. Start it from
`cv_on_commit` instead. See [Side effects after commit](reference/request_lifecycle.md#side-effects-after-commit)
and [when `cv_on_commit` runs](reference/request_lifecycle.md#transactions).

## How do I undo an action's changes when `action()` returns `False`?

Returning `False` shows the error message but keeps what `action()` already wrote. Call
`transaction.set_rollback(True)` before returning. See
[Rolling back a failed action](reference/request_lifecycle.md#rolling-back-a-failed-action).

## Why do I get `TransactionManagementError` after catching `IntegrityError`?

`cv_form_valid` runs inside a transaction. On PostgreSQL a caught database error breaks it. Wrap
the statement that may fail in its own `transaction.atomic()`. See
[Catching IntegrityError](reference/request_lifecycle.md#catching-integrityerror).

## How do I turn off the transaction for one view?

Set `cv_atomic = False` on the view. To change the boundary instead (another database,
`durable=True` services), override `cv_get_db_alias()` or `cv_get_atomic()`. See
[Transactions](reference/request_lifecycle.md#transactions) and
[Durable services](reference/request_lifecycle.md#durable-services).

## Where does each hook run, and which one should I override?

The [hook reference](reference/request_lifecycle.md#hook-reference) lists every overridable method
with its phase (outside, in the transaction, after the commit) and what it is meant for.
````

- [ ] **Step 2: Hook tables in create/update views**

In `docs/reference/create_view.md`, replace the "Form Processing Hooks" table (the six rows starting `| Hook | Description |`) with:

```markdown
| Hook | Phase | Description |
|------|-------|-------------|
| `cv_post_hook(context)` | outside | Called at the start of POST processing |
| `cv_form_is_valid(context)` | outside | Override to add custom validation |
| `cv_form_valid(context)` | in transaction | Called when the form is valid (saves the instance) |
| `cv_form_valid_hook(context)` | in transaction | Called after `cv_form_valid` (used by `MessageMixin`) |
| `cv_on_commit(context)` | after commit | Side effects: mail, Celery, webhooks |
| `cv_form_invalid(context)` | outside | Called when the form is invalid |
| `cv_form_invalid_hook(context)` | outside | Called after form invalid handling |

The full call chain, the transaction settings and recipes are in
[Request lifecycle, transactions & hooks](request_lifecycle.md).
```

In `docs/reference/update_view.md`, replace its identical table (under "The same hooks as [CreateView]…") with the same seven-row table and the same closing sentence.

- [ ] **Step 3: Delete, custom form, action pages**

`docs/reference/delete_view.md`: after the paragraph ending `` `DeleteView` also uses `CrudViewProcessFormMixin`. ``, add:

```markdown

`self.object.delete()` and `cv_form_valid_hook` run in one transaction; side effects belong in
`cv_on_commit`. See [Request lifecycle, transactions & hooks](request_lifecycle.md#call-chains).
```

`docs/reference/custom_form_view.md`: replace the two-row hook table with:

```markdown
| Hook | Phase | Description |
|------|-------|-------------|
| `cv_form_valid(context)` | in transaction | Called when the form is valid — implement your action here |
| `cv_form_valid_hook(context)` | in transaction | Called after `cv_form_valid` (used by `MessageMixin`) |
| `cv_on_commit(context)` | after commit | Side effects: mail, Celery, webhooks |
```

and after the paragraph that starts `After \`cv_form_valid_hook\`, the view redirects…`, add:

```markdown

See [Request lifecycle, transactions & hooks](request_lifecycle.md) for the full call chain.
```

`docs/reference/action_view.md`: replace the "Hooks" section body (from `Override these for side effects…` to the end of its two-row table) with:

```markdown
`action()` and these hooks run in one transaction; side effects belong in `cv_on_commit`, which
runs after the commit and only when `action()` returned truthy:

| Hook | When | Phase |
|------|------|-------|
| `cv_action_success_hook(self, context)` | action returned truthy | in transaction |
| `cv_action_error_hook(self, context)` | action returned falsy | in transaction |
| `cv_on_commit(self, context)` | action returned truthy | after commit |

A falsy result does not roll back what `action()` wrote; see
[Rolling back a failed action](request_lifecycle.md#rolling-back-a-failed-action).
```

- [ ] **Step 4: Workflow page**

In `docs/reference/workflow_view.md`, replace the `### \`on_transition\` hook` intro sentence and code block (lines ~325–335) with:

````markdown
Override `on_transition` for **database** follow-ups of a transition. It runs inside the
transaction, so its writes roll back together with the transition:

```python
class CampaignWorkflowView(CrispyViewMixin, MessageMixin, WorkflowView):
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm

    def on_transition(self, info, transition, state_old, state_new, comment, user, data):
        CampaignAudit.objects.create(campaign=self.object, state=state_new, user=user)
```

Send notifications and start async tasks from `cv_on_commit` instead. It runs after the commit,
and `context["workflow_info"]` holds the `WorkflowInfo` record:

```python
    def cv_on_commit(self, context):
        info = context["workflow_info"]
        send_notification(self.object, info.state_new, info.user)
```

See [Side effects after commit](request_lifecycle.md#side-effects-after-commit).
````

Keep the parameter table that follows unchanged.

- [ ] **Step 5: Formsets, conditional, stability**

`docs/reference/formsets.md` line ~114: change `saves them (in the same transaction as the main object) on a` to `saves them (in the same [transaction](request_lifecycle.md#transactions) as the main object) on a`.

`docs/reference/conditional.md` line ~103: change `runs inside a single database transaction, so a failure elsewhere` to `runs inside a single database [transaction](request_lifecycle.md#transactions), so a failure elsewhere`.

`docs/development/stability.md`: replace

```markdown
**Declared attributes and hooks**: the documented `cv_*` class attributes of the classes
above, and the documented overridable hooks — e.g. `cv_form_valid` (framework work step),
`cv_form_valid_hook` (user extension point), `cv_post_hook`, `cv_form_invalid_hook`,
`cv_form_valid_redirect`.
```

with

```markdown
**Declared attributes and hooks**: the documented `cv_*` class attributes of the classes
above, and the documented overridable hooks — e.g. `cv_form_valid` (framework work step),
`cv_form_valid_hook` (user extension point), `cv_post_hook`, `cv_form_invalid_hook`,
`cv_form_valid_redirect`, and the transaction API: `cv_atomic`, `cv_get_atomic`,
`cv_get_db_alias`, `cv_on_commit`, `cv_form_valid_process`, `cv_action_process`
(see [Request lifecycle, transactions & hooks](../reference/request_lifecycle.md)).
```

and change `and the \`on_transition\` hook is the documented overridable method on \`WorkflowView\`.` to `and the \`on_transition\` hook is the documented overridable method on \`WorkflowView\` (it runs inside the transaction; \`context["workflow_info"]\` is available in \`cv_on_commit\`).`

- [ ] **Step 6: Build**

Run: `.venv/bin/mkdocs build --strict -d /tmp/cv-site`
Expected: success. Anchor validation (Task 7) fails the build if any FAQ link target is wrong.

- [ ] **Step 7: Commit**

```bash
git add docs/faq.md docs/reference docs/development/stability.md
git commit -m "docs: FAQ entries and cross-links for transactions and hooks (#31)"
```

---

### Task 9: Changelog

**Files:**
- Modify: `CHANGELOG.md` (the `## Unreleased` section at the top; it already has a `### Removed` block)

The repo convention marks breaking changes with a `**Breaking:**` prefix inside `### Added` / `### Changed` / `### Removed` / `### Fixed`, not a separate `### BREAKING` heading.

- [ ] **Step 1: Add the entries**

Under `## Unreleased`, add these sections **above** the existing `### Removed`:

```markdown
### Added

- Transactions around every write. Form, delete and action views run their write phase
  (`cv_form_valid` + `cv_form_valid_hook`, resp. `action()` + its success/error hook) in
  `transaction.atomic()` on the model's write database. New `CrudView.cv_atomic` (default `True`,
  `False` on `ResourceViewMixin`), `cv_get_atomic()`, `cv_get_db_alias()`, and the seam methods
  `cv_form_valid_process()` / `cv_action_process()` (#31).
- `cv_on_commit(context)` hook: runs after the commit, never after a rollback. The place for mail,
  Celery tasks and webhooks. Workflow views pass the transition record as
  `context["workflow_info"]` (#31).
- Reference page "Request lifecycle, transactions & hooks" with the call chain of every POST view,
  a hook reference, recipes and a migration guide, plus six FAQ entries that link to it. The docs
  build now validates anchors.

### Changed

- **Breaking:** `cv_form_valid_hook`, `cv_action_success_hook` and `cv_action_error_hook` now run
  inside the transaction, before the commit. Move side effects (mail, Celery, webhooks) to
  `cv_on_commit`, or set `cv_atomic = False` to keep the old behaviour (#31).
- **Breaking:** an exception raised in those hooks now rolls back the write; before, the object
  stayed saved (#31).
- **Breaking:** `try/except IntegrityError` inside `cv_form_valid` needs its own nested
  `transaction.atomic()` on PostgreSQL, otherwise the next query raises
  `TransactionManagementError` (#31).
- **Breaking:** code that calls `transaction.atomic(durable=True)` from the write phase now raises
  `RuntimeError`; set `cv_atomic = False` on that view (#31).

### Fixed

- `CreateView` / `UpdateView` saved the instance and its many-to-many data in separate
  transactions; a failure in `save_m2m()` left a half-saved object (#31).
- `CreateViewParentMixin` with `many_to_many_through_attribute` left an object without a parent
  when adding it to the parent's relation failed (#31).
- The formset and workflow transactions used the `default` database instead of the model's
  routed write database (#31).
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: changelog for transactions around writes (#31)"
```

---

### Task 10: Full verification, PR, issue comment

**Files:** none (verification and GitHub only).

- [ ] **Step 1: Lint and full test run**

```bash
.venv/bin/ruff format --check src tests
.venv/bin/ruff check src tests
.venv/bin/python -m pytest tests -q
.venv/bin/python -m pytest tests -q --random-order
.venv/bin/mkdocs build --strict -d /tmp/cv-site
```

Expected: everything green. The second pytest line runs in random order (`pytest-random-order` is installed in the dev venv). The new tests patch classes only through `monkeypatch` (auto-restored), so order must not matter. If a test fails only in random order, pin it with `--random-order-seed=<seed>` and fix the pollution; don't skip it.

If `task test` (nox matrix: Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0) is available locally, run it too. Otherwise CI covers it.

- [ ] **Step 2: Push and open the PR**

```bash
git push -u origin feature/transactions-call-chain-31
gh pr create --title "Transactions around all write operations + request lifecycle docs (#31)" --body "$(cat <<'EOF'
Closes #31.

Widens #31 from workflow-only to every write view (design: `superpowers/specs/2026-10-08-transactions-call-chain-design.md`).

- Form, delete and action views run their write phase in `transaction.atomic()` on the model's routed write database (`cv_atomic`, `cv_get_atomic()`, `cv_get_db_alias()`).
- New post-commit hook `cv_on_commit(context)` for side effects; workflow views get `context["workflow_info"]`.
- Resource views default to `cv_atomic = False`.
- Fixes: non-atomic `save_m2m`, orphaned m2m-parent creates, unrouted formset/workflow transactions.
- New docs page "Request lifecycle, transactions & hooks", six FAQ entries, anchor validation in the docs build.

**Breaking** (pre-1.0, documented in the migration section): hooks now run before the commit, hook exceptions roll back, nested `atomic()` needed around caught `IntegrityError`, `durable=True` needs `cv_atomic = False`.
EOF
)"
```

- [ ] **Step 3: Wait for CI, fix, do NOT merge**

Check runs: `gh pr checks <PR#> --watch`. `gh pr checks` does not show `codecov/patch`, so also run `gh api repos/jacob-consulting/django-crud-views/commits/$(git rev-parse HEAD)/check-runs --jq '.check_runs[] | "\(.name) \(.conclusion)"'`. If the PR shows zero runs after a few minutes, close and reopen it. Fix ruff or test failures with new commits. **Don't merge.** Merging only happens when the maintainer explicitly asks.

- [ ] **Step 4: Comment on issue #31**

```bash
gh issue comment 31 --body "Scope widened: transactions now apply to every write view (form, delete, action), not only workflow transitions, with a configurable boundary (\`cv_atomic\` / \`cv_get_atomic()\`) and a new post-commit hook \`cv_on_commit\`. Design: \`superpowers/specs/2026-10-08-transactions-call-chain-design.md\`. Implemented in #<PR#>."
```

---

### Task 11: Update the django-crud-views skill (separate repo)

**Files:**
- Modify: `/home/alex/projects/alex/skills/plugins/django-crud-views/skills/django-crud-views/SKILL.md`
- Modify: the plugin changelog in the same plugin directory (`ls /home/alex/projects/alex/skills/plugins/django-crud-views/` to find it), under `[Unreleased]`

**Interfaces:** none.

Never edit the read-only mirror under `~/.claude/plugins/cache/`. Run every git command for this repo as `git -C /home/alex/projects/alex/skills …`: the Bash tool resets the working directory, and a plain `cd … && git push` can push the wrong repo.

- [ ] **Step 1: Add the section**

Find where SKILL.md describes form hooks (`grep -n "cv_form_valid_hook\|Common Mistakes" SKILL.md`). Add after the hooks description (or as a new `## Transactions & hooks` section before Common Mistakes):

```markdown
## Transactions & hooks (since 0.27.0)

Form, delete and action views run their write phase in one transaction:
`cv_form_valid` + `cv_form_valid_hook` (resp. `action()` + `cv_action_success_hook` /
`cv_action_error_hook`) are inside `transaction.atomic(using=cv_get_db_alias())`. Side effects go
in `cv_on_commit(context)`, which runs after the commit and never after a rollback. Workflow views
put the transition record in `context["workflow_info"]`.

- `cv_atomic = False`: no transaction (default on `ResourceViewMixin`; needed for
  `atomic(durable=True)` services).
- `cv_get_atomic()` / `cv_get_db_alias()`: override for a custom boundary or another database.
- `action()` returning `False` does not roll back; call `transaction.set_rollback(True)`.
- Overriding `post()`? Call `cv_form_valid_process(context)` / `cv_action_process(context)` to
  keep the transaction.
```

Add a row to the Common Mistakes table (match its column layout):

```markdown
| Sending mail / starting Celery tasks in `cv_form_valid_hook`, `action()` or `on_transition` | They run before the commit (since 0.27.0); use `cv_on_commit(context)` |
```

Add to the plugin changelog under `[Unreleased]`: `- Document transactions around writes and the cv_on_commit hook (package 0.27.0, unreleased).`

- [ ] **Step 2: Drift audit**

Re-create the drift-audit harness (it isn't persisted; method in the maintainer's notes: configure Django against the real package and check that every `from crud_views* import X` in SKILL.md resolves, every `lib.__all__` name appears, and every `CRUD_VIEWS_*` string maps to a settings field). At minimum, check that each new name exists:

```bash
.venv/bin/python - <<'EOF'
from tests.test1 import conftest
conftest.pytest_configure()  # configures Django settings the same way the test suite does
from crud_views.lib.view.base import CrudView
from crud_views.lib.views.action import ActionView
from crud_views.lib.views.mixins import CrudViewProcessFormMixin
for owner, name in [(CrudView, "cv_atomic"), (CrudView, "cv_get_atomic"), (CrudView, "cv_get_db_alias"),
                    (CrudView, "cv_on_commit"), (CrudViewProcessFormMixin, "cv_form_valid_process"),
                    (ActionView, "cv_action_process")]:
    assert hasattr(owner, name), (owner, name)
print("ok")
EOF
```

Expected: `ok`.

- [ ] **Step 3: Commit and push the skills repo**

```bash
git -C /home/alex/projects/alex/skills add plugins/django-crud-views
git -C /home/alex/projects/alex/skills commit -m "django-crud-views: document transactions and cv_on_commit (package 0.27.0, unreleased)"
git -C /home/alex/projects/alex/skills push origin main
git -C /home/alex/projects/alex/skills status -sb   # expect: ## main...origin/main (no ahead/behind)
```

Do **not** cut a plugin release. That happens only after package 0.27.0 is live on PyPI.

---

## Note: running in a git worktree

If you execute this plan in a git worktree, the inherited `VIRTUAL_ENV` points at the main checkout's venv, and `uv` installs go there. Create the worktree's own venv and install with `env -u VIRTUAL_ENV uv sync -p .venv/bin/python` (or `task dev`), then use that worktree's `.venv/bin/python` for every command above.
