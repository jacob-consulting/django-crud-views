# Dynamic Cancel Button Target Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The cancel button of create/update/delete/custom-form views returns to the sibling view the user came from (list, card, detail, ...), carried as a validated view key in the link's query string, with full backward compatibility.

**Architecture:** Sibling links built by the package (`cv_get_context`, `ContextButton.get_context`, the `cv_card_action` tag) append `?<param>=<current view key>` only when the target view declares an allow-list `cv_cancel_keys`. The target view resolves the cancel key in `CrudView.cv_get_cancel_key()`, validating the incoming value against the key regex, the allow-list, ViewSet registration, and the object requirement, falling back to the unchanged `cv_cancel_key`. All four content templates post to `request.get_full_path` so the origin survives validation re-renders.

**Tech Stack:** Django 4.2/5.2/6.0, Python 3.12+, pydantic settings model, django-crispy-forms, pytest (`pytest tests` from the repo root, plain `django.test.TestCase` in `examples/bootstrap5`), ruff.

**Spec:** `superpowers/specs/2026-09-08-cancel-button-origin-design.md`

## Global Constraints

- Backward compatible: with `cv_cancel_keys` unset (default `None`) every generated URL and every cancel URL is byte-identical to today. The existing 875 tests must keep passing unchanged (baseline: `875 passed, 1 skipped`).
- Setting name: `CRUD_VIEWS_CANCEL_ORIGIN_PARAM`, default `"cv_from"`, settings field `cancel_origin_param`.
- Validation regex for both the setting name and the incoming value: the existing `REGS["name"]` in `src/crud_views/lib/check.py:14`, `^[a-z][a-z0-9_]*$`.
- Check ids: settings `crud_views.E103`, per-view `viewset.E252`.
- Naming: all view attributes use the `cv_` prefix; line length 120; double quotes; ruff format on commit (pre-commit hook).
- Never name any customer project, app, or theme in code, docs, tests, commits, or the skill.
- Docs live under `docs/` (mkdocs only); specs/plans under `superpowers/`.
- The public skill lives in the sibling repo `/home/alex/projects/alex/skills`; all git operations there use `git -C /home/alex/projects/alex/skills ...` in a single Bash invocation.
- Work on branch `feature/cancel-button-origin` (already exists, contains the spec and prompt).
- Run tests with `.venv/bin/pytest tests -q` from the repo root. Run lint with `.venv/bin/ruff check src tests examples` and `.venv/bin/ruff format src tests examples`.

---

## File map

| File | Responsibility |
|---|---|
| `src/crud_views/lib/settings.py` | `cancel_origin_param` field + E103 check |
| `src/crud_views/lib/view/base.py` | `cv_cancel_keys`, `cv_get_origin_key()`, `cv_get_cancel_key()`, `cv_get_link_url()`, E252, `cv_get_dict` key, `get_cancel_button_context()` |
| `src/crud_views/lib/view/buttons.py` | `ContextButton.get_context()` uses `cv_get_link_url()` |
| `src/crud_views/templatetags/crud_views.py` | `cv_card_action` uses `cv_get_link_url()` |
| `src/crud_views/lib/views/manage.py` | manage view attribute table shows `cv_cancel_keys` |
| `src/crud_views/templates/crud_views/view_{create,update,delete,custom_form}.content.html` | form action `request.get_full_path` |
| `tests/test1/app/views.py`, `urls.py`, `conftest.py` | `author_origin` and `guardian_author_origin` test ViewSets + fixtures |
| `tests/test1/test_cancel_origin.py` | all feature tests |
| `tests/test1/test_settings_checks.py`, `tests/test1/test_modal.py` | E103 tests, modal 422 origin test |
| `examples/bootstrap5/library/{views,tests}.py`, `project/features.py` | example usage + tests |
| `docs/reference/{settings,update_view,create_view,delete_view,custom_form_view,card-list-view}.md`, `CHANGELOG.md` | documentation |
| `../skills/plugins/django-crud-views/...` | public skill |

---

### Task 1: Setting `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` with check E103

**Files:**
- Modify: `src/crud_views/lib/settings.py` (field block near line 32, `check_messages` near line 100)
- Test: `tests/test1/test_settings_checks.py`
- Modify: `docs/reference/settings.md` (after the "Session" table, line 24)

**Interfaces:**
- Produces: `crud_views_settings.cancel_origin_param: str` (default `"cv_from"`), check id `crud_views.E103`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_settings_checks.py`:

```python
def test_cancel_origin_param_default():
    settings_obj = CrudViewsSettings()
    assert settings_obj.cancel_origin_param == "cv_from"


def test_cancel_origin_param_valid_name_no_message():
    settings_obj = CrudViewsSettings(cancel_origin_param="origin_2")
    assert settings_obj.check_messages == []


def test_cancel_origin_param_invalid_name_reported():
    for bad in ("bad param", "bad-param", "Bad", "2bad", "", "a/b", "a=b"):
        settings_obj = CrudViewsSettings(cancel_origin_param=bad)
        messages = settings_obj.check_messages
        assert len(messages) == 1, bad
        assert messages[0].id == "crud_views.E103"
        assert "CRUD_VIEWS_CANCEL_ORIGIN_PARAM" in messages[0].msg
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_settings_checks.py -q`
Expected: 3 failures. The first two fail with `ValidationError`/`AttributeError` because the field does not exist; the third because `check_messages` returns `[]`.

- [ ] **Step 3: Add the field and the check**

In `src/crud_views/lib/settings.py`, after the `# session` block (line 33):

```python
    # cancel button
    cancel_origin_param: str = from_settings("CRUD_VIEWS_CANCEL_ORIGIN_PARAM", default="cv_from")
```

In `check_messages`, directly after the `manage_views_enabled` check (before the deferred breadcrumb import), add:

```python
        # deferred import: settings.py must not import check.py at module level
        from crud_views.lib.check import REGS

        if not REGS["name"]["reg"].match(self.cancel_origin_param):
            messages.append(
                Error(
                    id="crud_views.E103",
                    msg=(
                        f"setting CRUD_VIEWS_CANCEL_ORIGIN_PARAM {REGS['name']['msg']}, "
                        f"got {self.cancel_origin_param!r}"
                    ),
                )
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test1/test_settings_checks.py -q`
Expected: all pass (the pre-existing `test_valid_settings_produce_no_messages` still passes because the default name is valid).

- [ ] **Step 5: Document the setting**

In `docs/reference/settings.md`, insert after the Session table (after line 24, before `## Filter`):

```markdown
## Cancel button

| Key              | Description                                                | Type  | Default   |
|------------------|------------------------------------------------------------|-------|-----------|
| CRUD_VIEWS_CANCEL_ORIGIN_PARAM | Query-string parameter that carries the origin view key for views with `cv_cancel_keys` (see [UpdateView](update_view.md#dynamic-cancel-target)). Must match `^[a-z][a-z0-9_]*$`; otherwise system check `crud_views.E103` fails. | `str` | `cv_from` |

```

- [ ] **Step 6: Commit**

```bash
git add src/crud_views/lib/settings.py tests/test1/test_settings_checks.py docs/reference/settings.md
git commit -m "feat(settings): CRUD_VIEWS_CANCEL_ORIGIN_PARAM with check E103"
```

---

### Task 2: Test ViewSets `author_origin` and `guardian_author_origin`

No production code. This task creates the fixtures every later test uses. It must leave the existing suite green.

**Files:**
- Modify: `src/crud_views/lib/view/base.py:66` (declare the attribute only)
- Modify: `tests/test1/app/views.py` (append at end, line 963)
- Modify: `tests/test1/app/urls.py`
- Modify: `tests/test1/conftest.py` (append at end)

**Interfaces:**
- Produces: `CrudView.cv_cancel_keys: list[str] | None = None` (declared, not yet read by anything).
- Produces: URL prefixes `/author_origin/...` and `/guardian_author_origin/...`; fixtures `cv_author_origin`, `client_user_author_origin` (user with view/add/change/delete on the Author model), `cv_guardian_author_origin`.

- [ ] **Step 0: Declare the attribute**

The test views below set `cv_cancel_keys`. `tests/test1/test_unknown_attribute_check.py::test_registered_views_have_no_unknown_attribute_warnings` asserts that no registered view carries an unknown `cv_*` attribute (W280), so the attribute must be declared before the views exist. In `src/crud_views/lib/view/base.py` replace line 66:

```python
    cv_cancel_key: str | None = "list"  # cancel url, defaults to list
    cv_cancel_keys: list[str] | None = None  # origin keys the cancel button may return to; None = static
```

- [ ] **Step 1: Add the ViewSets and views**

Change the import line in `tests/test1/app/views.py`:

```python
from crud_views.lib.views.form import CustomFormNoObjectViewPermissionRequired, CustomFormViewPermissionRequired
```

Append at the end of `tests/test1/app/views.py`:

```python


# --- Author Origin (dynamic cancel target via cv_cancel_keys) ---
# Every form view uses cv_cancel_key = "card" as the static fallback so tests can tell
# "resolved to list" apart from "fell back to the default".

cv_author_origin = ViewSet(
    model=Author,
    name="author_origin",
    context_buttons=context_buttons_default() + [ContextButton(key="edit", key_target="update")],
)


class AuthorOriginListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author_origin
    cv_list_actions = ["detail", "update", "delete"]


class AuthorOriginCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_author_origin
    cv_card_actions = [
        CardAction(key="detail", label="Details"),
        CardAction(key="update", label="Edit"),
    ]


class AuthorOriginDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_author_origin
    cv_context_actions = ["home", "detail", "update", "delete", "edit", "contact"]
    cv_property_display = [{"title": "Attributes", "properties": ["first_name", "last_name"]}]


class AuthorOriginCreateView(CrispyViewMixin, CreateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_author_origin
    cv_cancel_key = "card"
    cv_cancel_keys = ["list", "detail"]


class AuthorOriginUpdateView(CrispyViewMixin, UpdateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_author_origin
    cv_cancel_key = "card"
    cv_cancel_keys = ["list", "detail"]


class AuthorOriginDeleteView(CrispyViewMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author_origin
    cv_cancel_key = "card"
    cv_cancel_keys = ["list", "detail"]

    def cv_check_delete_protection(self) -> list[str]:
        if self.object.pseudonym == "protected":
            return ["This author is protected."]
        return []


class AuthorOriginContactView(CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"
    cv_path = "contact"
    cv_viewset = cv_author_origin
    form_class = AuthorContactForm
    cv_cancel_key = "card"
    cv_cancel_keys = ["list", "detail"]
    cv_message_template_code = "Contacted author »{{ object }}«"
    cv_header_template_code = "Contact Author"
    cv_paragraph_template_code = "Send a message to the Author"
    cv_action_label_template_code = "Contact"
    cv_action_short_label_template_code = "Contact"


class AuthorOriginBroadcastForm(CrispyForm):
    subject = CharField(label="Subject", required=True)

    def get_layout_fields(self):
        return Column12("subject")


class AuthorOriginBroadcastView(CrispyViewMixin, CustomFormNoObjectViewPermissionRequired):
    cv_key = "broadcast"
    cv_path = "broadcast"
    cv_viewset = cv_author_origin
    form_class = AuthorOriginBroadcastForm
    cv_cancel_key = "card"
    cv_cancel_keys = ["list", "detail"]
    cv_header_template_code = "Broadcast"
    cv_paragraph_template_code = "Message all authors"
    cv_action_label_template_code = "Broadcast"
    cv_action_short_label_template_code = "Broadcast"


# --- Guardian Author Origin (cv_cancel_keys under per-object permissions) ---

cv_guardian_author_origin = GuardianViewSet(model=Author, name="guardian_author_origin")


class GuardianAuthorOriginListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_guardian_author_origin
    cv_list_actions = ["detail", "update"]


class GuardianAuthorOriginDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_guardian_author_origin


class GuardianAuthorOriginUpdateView(CrispyViewMixin, GuardianUpdateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_guardian_author_origin
    cv_cancel_keys = ["detail"]
```

- [ ] **Step 2: Register the URLs**

In `tests/test1/app/urls.py`, add `cv_author_origin,` and `cv_guardian_author_origin,` to the import list (alphabetical position: `cv_author_origin` after `cv_author_modal`; `cv_guardian_author_origin` after `cv_guardian_author`) and append:

```python
urlpatterns += cv_author_origin.urlpatterns
urlpatterns += cv_guardian_author_origin.urlpatterns
```

- [ ] **Step 3: Add fixtures**

Append to `tests/test1/conftest.py`:

```python


@pytest.fixture
def cv_author_origin():
    from tests.test1.app.views import cv_author_origin as ret

    return ret


@pytest.fixture
def user_author_origin(cv_author_origin):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_origin", password="password")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author_origin, perm)
    return user


@pytest.fixture
def client_user_author_origin(client, user_author_origin) -> Client:
    client.force_login(user_author_origin)
    return client


@pytest.fixture
def cv_guardian_author_origin():
    from tests.test1.app.views import cv_guardian_author_origin as ret

    return ret
```

- [ ] **Step 4: Run the full suite to prove nothing regressed**

Run: `.venv/bin/pytest tests -q`
Expected: `875 passed, 1 skipped` (same as baseline; the new views are only registered, never exercised yet).

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/lib/view/base.py tests/test1/app/views.py tests/test1/app/urls.py tests/test1/conftest.py
git commit -m "test: author_origin and guardian_author_origin ViewSets for cancel-origin tests"
```

---

### Task 3: Cancel key resolution in `CrudView`

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (attributes line 64-67, `checks()` line 101-131, `cv_get_dict()` line 259-282, `get_cancel_button_context()` line 448-453)
- Modify: `src/crud_views/lib/views/manage.py:109`
- Create: `tests/test1/test_cancel_origin.py`

**Interfaces:**
- Consumes: `crud_views_settings.cancel_origin_param` (Task 1).
- Consumes: `CrudView.cv_cancel_keys` (declared in Task 2).
- Produces:
  - `CrudView.cv_get_origin_key(self) -> str | None`
  - `CrudView.cv_get_cancel_key(self, obj=None) -> str | None`
  - `CrudView.cv_get_link_url(self, cls, key: str, obj=None) -> str` (defined here, wired into the three emit sites in Task 4)
  - check id `viewset.E252`

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_cancel_origin.py`:

```python
"""
Dynamic cancel button target: the origin view key travels in the link's query string,
the target view resolves it through cv_cancel_keys.
Spec: superpowers/specs/2026-09-08-cancel-button-origin-design.md
"""

import re

import pytest
from django.template import Context, Template
from django.urls import reverse

PARAM = "cv_from"


def url(viewset, key, pk=None) -> str:
    kwargs = {"pk": pk} if pk is not None else {}
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def cancel_url(response) -> str:
    """The URL the crispy cancel button navigates to (data-cv-cancel-url)."""
    match = re.search(r'data-cv-cancel-url="([^"]+)"', response.content.decode())
    assert match, "no cancel button rendered"
    return match.group(1)


def hrefs(response) -> list[str]:
    return re.findall(r'href="([^"]+)"', response.content.decode())


def render_cancel_tag(response) -> str:
    """Render {% cv_cancel_button %} against the response's view; return the href."""
    tpl = Template("{% load crud_views %}{% cv_cancel_button %}")
    html = tpl.render(Context({"view": response.context["view"], "request": response.context["request"]}))
    match = re.search(r'href="([^"]+)"', html)
    assert match, html
    return match.group(1)


# ---------------------------------------------------------------------------
# Resolution (Task 3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_default_without_cancel_keys_is_unchanged(client_user_author_change, cv_author, author_douglas_adams):
    """A view without cv_cancel_keys ignores the parameter entirely."""
    pk = author_douglas_adams.pk
    response = client_user_author_change.get(url(cv_author, "update", pk), {PARAM: "detail"})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_author, "list")
    assert response.context["view"].cv_cancel_keys is None


@pytest.mark.django_db
def test_default_without_cancel_keys_is_unchanged_int_pk(client_user_publisher_change, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_user_publisher_change.get(url(cv_publisher, "update", pk), {PARAM: "detail"})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_publisher, "list")


@pytest.mark.django_db
def test_update_resolves_detail_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)
    assert render_cancel_tag(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_update_resolves_list_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "list"})
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_update_without_origin_falls_back(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk))
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value",
    ["card", "nope", " detail", "de-tail", "Detail", "a/b", "detail%20", "", "2detail"],
    ids=["not-allowed", "unregistered", "space", "dash", "upper", "slash", "encoded", "empty", "digit-first"],
)
def test_invalid_or_disallowed_origin_falls_back(
    client_user_author_origin, cv_author_origin, author_douglas_adams, value
):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: value})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_create_cannot_return_to_object_view(client_user_author_origin, cv_author_origin):
    """detail needs an object; a create view has none -> fallback. list is fine."""
    response = client_user_author_origin.get(url(cv_author_origin, "create"), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "card")
    response = client_user_author_origin.get(url(cv_author_origin, "create"), {PARAM: "list"})
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_no_object_custom_form_cannot_return_to_object_view(client_user_author_origin, cv_author_origin):
    response = client_user_author_origin.get(url(cv_author_origin, "broadcast"), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "card")
    response = client_user_author_origin.get(url(cv_author_origin, "broadcast"), {PARAM: "list"})
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_cv_get_cancel_key_defaults_obj_to_view_object(
    client_user_author_origin, cv_author_origin, author_douglas_adams
):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    view = response.context["view"]
    assert view.cv_get_cancel_key() == "detail"
    assert view.cv_get_cancel_key(obj=None) == "detail"
    assert view.cv_get_origin_key() == "detail"


@pytest.mark.django_db
def test_cv_get_dict_exposes_cancel_keys(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    view = response.context["view"]
    ctx = view.cv_get_context("update", obj=author_douglas_adams, user=view.request.user, request=view.request)
    assert ctx["cv_cancel_keys"] == ["list", "detail"]
    assert ctx["cv_cancel_key"] == "card"


# ---------------------------------------------------------------------------
# System check E252
# ---------------------------------------------------------------------------


def check_ids(view_cls) -> list:
    return [m.id for c in view_cls.checks() for m in c.messages()]


def test_check_e252_without_viewset_is_skipped():
    from crud_views.lib.views import UpdateView

    class Unbound(UpdateView):
        cv_cancel_keys = ["nope"]

    assert "viewset.E252" not in check_ids(Unbound)


@pytest.mark.django_db
def test_check_e252_unregistered_key(cv_author_origin):
    from crud_views.lib.views import ActionView

    class BadCancelKeysView(ActionView):
        cv_viewset = cv_author_origin
        cv_key = "e252_probe"
        cv_path = "e252-probe"
        cv_backend_only = True
        cv_cancel_keys = ["nope"]

        def action(self, context):
            return True

    assert "viewset.E252" in check_ids(BadCancelKeysView)


@pytest.mark.django_db
def test_check_e252_registered_keys_pass(cv_author_origin):
    from tests.test1.app.views import AuthorOriginUpdateView

    assert "viewset.E252" not in check_ids(AuthorOriginUpdateView)


def test_check_e252_list_accepted_on_card_only_viewset():
    from tests.test1.app.views import AuthorWideCardCreateView

    class CardOnlyProbe(AuthorWideCardCreateView):
        cv_cancel_keys = ["list"]

    # author_wide_card registers "card" but no "list" -> the list->card fallback applies
    assert "viewset.E252" not in check_ids(CardOnlyProbe)
```

Note on registration: `CrudViewMetaClass.__new__` (`src/crud_views/lib/view/meta.py`) registers a class only when `cv_viewset` appears in that class's own body. So `BadCancelKeysView` (own `cv_viewset`, unique key `e252_probe`, no URL) is registered once and harmlessly, while `CardOnlyProbe` and `Unbound` inherit `cv_viewset` without re-registering anything.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_cancel_origin.py -q`
Expected: the resolution tests fail with the cancel URL equal to the list/card default instead of the origin; `test_cv_get_cancel_key_defaults_obj_to_view_object` fails with `AttributeError: cv_get_cancel_key`; the E252 tests fail because the id is never emitted.

- [ ] **Step 3: Implement the attribute, the resolver, the link helper, and E252**

In `src/crud_views/lib/view/base.py`:

Add the import at the top (after `from django.urls import reverse`):

```python
from urllib.parse import urlencode
```

In `checks()`, after the E251 `CheckExpression`, add:

```python
        yield CheckExpression(
            context=cls,
            id="E252",
            expression=cls.cv_cancel_keys_registered(),
            msg=f"cv_cancel_keys entries must be registered view keys, got {cls.cv_cancel_keys!r}",
        )
```

Add the classmethod next to `cv_get_url_extra_kwargs` (line 307):

```python
    @classmethod
    def cv_cancel_keys_registered(cls) -> bool:
        """True when every cv_cancel_keys entry is a registered sibling key ("list" may fall back to "card")."""
        if not cls.cv_cancel_keys or cls.cv_viewset is None:
            return True
        viewset = cls.cv_viewset
        return all(
            viewset.is_view_registered(key) or (key == "list" and viewset.is_view_registered("card"))
            for key in cls.cv_cancel_keys
        )
```

In `cv_get_dict()`, after `"cv_cancel_key": cls.cv_cancel_key,` add:

```python
            "cv_cancel_keys": cls.cv_cancel_keys,
```

Replace `get_cancel_button_context()` (line 448-453) and add the three new methods directly before it:

```python
    def cv_get_origin_key(self) -> str | None:
        """The sibling view the user came from, as sent by the origin link; None when absent or invalid."""
        value = self.request.GET.get(crud_views_settings.cancel_origin_param)
        if not value or not check.REGS["name"]["reg"].match(value):
            return None
        return value

    def cv_get_cancel_key(self, obj: Model | None = None) -> str | None:
        """The key the cancel button returns to: a validated origin, else cv_cancel_key.

        obj defaults to the view's own object so templates can call this without arguments
        ({% cv_context_url view.cv_get_cancel_key as url %}).
        """
        if obj is None:
            obj = getattr(self, "object", None)
        if not self.cv_cancel_keys:
            return self.cv_cancel_key
        origin = self.cv_get_origin_key()
        if origin not in self.cv_cancel_keys:
            return self.cv_cancel_key
        try:
            cls = self.cv_viewset.get_view_class(origin)  # keeps the list -> card fallback
        except ViewSetKeyFoundError:
            return self.cv_cancel_key
        if cls.cv_object and obj is None:  # a create view cannot return to "detail"
            return self.cv_cancel_key
        return origin

    def cv_get_link_url(self, cls: type[CrudView], key: str, obj: Model | None = None) -> str:
        """URL of a sibling link; carries this view's key when the target resolves its cancel target dynamically."""
        url = self.cv_get_url(key=key, obj=obj)  # reverse() only, never has a query string
        if cls.cv_cancel_keys and self.cv_key in cls.cv_cancel_keys:
            url += "?" + urlencode({crud_views_settings.cancel_origin_param: self.cv_key})
        return url

    def get_cancel_button_context(self, obj: Model | None = None, user: User | None = None, request=None) -> dict:
        """
        Get the context for the cancel button
        """
        url = self.cv_get_url(key=self.cv_get_cancel_key(obj), obj=obj)
        return {"cv_url": url, "cv_action_label": _("Cancel")}
```

In `src/crud_views/lib/views/manage.py`, after line 109 (`"cv_cancel_key": view.cv_cancel_key,`) add:

```python
                            "cv_cancel_keys": view.cv_cancel_keys,
```

- [ ] **Step 4: Run the new tests, then the full suite**

Run: `.venv/bin/pytest tests/test1/test_cancel_origin.py -q`
Expected: all pass.

Run: `.venv/bin/pytest tests -q`
Expected: everything passes (`875 + new`), no W280 warnings for `cv_cancel_keys` anymore.

- [ ] **Step 5: Lint and commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check src tests
git add src/crud_views/lib/view/base.py src/crud_views/lib/views/manage.py tests/test1/test_cancel_origin.py
git commit -m "feat(view): cv_cancel_keys resolves the cancel target from an origin key (E252)"
```

---

### Task 4: Emit the origin key on sibling links (three sites)

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (`cv_get_context()`, line ~426)
- Modify: `src/crud_views/lib/view/buttons.py` (`ContextButton.get_context()`, lines 51-78)
- Modify: `src/crud_views/templatetags/crud_views.py` (`cv_card_action`, line ~329)
- Test: `tests/test1/test_cancel_origin.py` (append)

**Interfaces:**
- Consumes: `CrudView.cv_get_link_url(cls, key, obj)` from Task 3.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_cancel_origin.py`:

```python
# ---------------------------------------------------------------------------
# Link emission (Task 4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_detail_page_links_carry_detail_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    links = hrefs(response)
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail" in links
    assert f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=detail" in links
    assert f"{url(cv_author_origin, 'contact', pk)}?{PARAM}=detail" in links
    # ViewSet-level ContextButton(key="edit", key_target="update") goes through ContextButton.get_context
    assert links.count(f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail") == 2
    # targets without cv_cancel_keys stay clean
    assert url(cv_author_origin, "detail", pk) in links
    assert url(cv_author_origin, "list") in links
    assert not any(h.startswith(url(cv_author_origin, "detail", pk) + "?") for h in links)


@pytest.mark.django_db
def test_list_page_row_actions_carry_list_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "list"))
    links = hrefs(response)
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=list" in links
    assert f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=list" in links
    assert f"{url(cv_author_origin, 'create')}?{PARAM}=list" in links
    assert url(cv_author_origin, "detail", pk) in links


@pytest.mark.django_db
def test_card_page_actions_carry_card_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    """card is not in cv_cancel_keys of the update view -> the card link stays clean.

    This proves the emitter checks the *target's* allow-list, not just its presence.
    """
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "card"))
    links = hrefs(response)
    assert url(cv_author_origin, "update", pk) in links
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=card" not in links


@pytest.mark.django_db
def test_card_action_carries_origin_when_allowed(client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch):
    from tests.test1.app.views import AuthorOriginUpdateView

    monkeypatch.setattr(AuthorOriginUpdateView, "cv_cancel_keys", ["list", "detail", "card"])
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "card"))
    assert f"{url(cv_author_origin, 'update', pk)}?{PARAM}=card" in hrefs(response)
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "card"})
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_cv_context_url_tag_carries_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    tpl = Template("{% load crud_views %}{% cv_context_url 'update' as u %}{{ u }}")
    out = tpl.render(Context({"view": response.context["view"], "request": response.context["request"]}))
    assert out == f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail"


@pytest.mark.django_db
def test_success_url_stays_clean(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_origin.post(
        f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail",
        {"first_name": "Douglas", "last_name": "Adams", "pseudonym": ""},
    )
    assert response.status_code == 302
    assert response["Location"] == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_existing_viewset_links_unchanged(client_user_author_change, cv_author, author_douglas_adams):
    """No cv_cancel_keys anywhere on cv_author -> no link gains a parameter."""
    pk = author_douglas_adams.pk
    response = client_user_author_change.get(url(cv_author, "detail", pk))
    assert not any(f"{PARAM}=" in h for h in hrefs(response))


# ---------------------------------------------------------------------------
# Custom parameter name and guardian (Task 4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_custom_origin_param_name(client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch):
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "cancel_origin_param", "origin")
    pk = author_douglas_adams.pk
    response = client_user_author_origin.get(url(cv_author_origin, "detail", pk))
    assert f"{url(cv_author_origin, 'update', pk)}?origin=detail" in hrefs(response)
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {"origin": "detail"})
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)
    response = client_user_author_origin.get(url(cv_author_origin, "update", pk), {PARAM: "detail"})
    assert cancel_url(response) == url(cv_author_origin, "card")


@pytest.mark.django_db
def test_guardian_update_resolves_detail_origin(
    client_guardian, user_guardian, cv_guardian_author_origin, author_douglas_adams
):
    from tests.lib.helper.guardian import user_guardian_object_perm

    user_guardian_object_perm(user_guardian, cv_guardian_author_origin, "view", author_douglas_adams)
    user_guardian_object_perm(user_guardian, cv_guardian_author_origin, "change", author_douglas_adams)
    pk = author_douglas_adams.pk
    response = client_guardian.get(url(cv_guardian_author_origin, "detail", pk))
    assert response.status_code == 200
    assert f"{url(cv_guardian_author_origin, 'update', pk)}?{PARAM}=detail" in hrefs(response)
    response = client_guardian.get(url(cv_guardian_author_origin, "update", pk), {PARAM: "detail"})
    assert response.status_code == 200
    assert cancel_url(response) == url(cv_guardian_author_origin, "detail", pk)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_cancel_origin.py -q -k "carry or carries or context_url_tag or custom_origin or guardian"`
Expected: the link-emission assertions fail (no `?cv_from=` in any href). `test_success_url_stays_clean` and `test_existing_viewset_links_unchanged` already pass.

- [ ] **Step 3: Wire the three emit sites**

`src/crud_views/lib/view/base.py`, in `cv_get_context()`, replace

```python
            "cv_url": self.cv_get_url(key=key, obj=obj),
```

with

```python
            "cv_url": self.cv_get_link_url(cls, key, obj),
```

(`cls` is assigned by `cv_get_cls_assert_object` a few lines above.)

`src/crud_views/lib/view/buttons.py`, in `ContextButton.get_context()`, replace the beginning of the method:

```python
    def get_context(self, context: ViewContext) -> dict:
        key_target = self._resolve_container_key(context.view.cv_viewset, self.key_target)

        # get target view class
        cls = context.view.cv_get_cls_assert_object(key_target, context.object)

        dict_kwargs = {
            "cv_access": False,
            "cv_url": context.view.cv_get_link_url(cls, key_target, context.object),
        }

        # button visibility — independent of access/permission
        dict_kwargs["cv_action_enabled"] = cls.cv_action_enabled(context.view.request.user, context.object)
```

and delete the old `cls = context.view.cv_get_cls_assert_object(key_target, context.object)` line that followed `dict_kwargs`. The rest of the method is unchanged.

`src/crud_views/templatetags/crud_views.py`, in `cv_card_action`, replace

```python
    url = view.cv_get_url(action.key, obj=obj)
```

with

```python
    url = view.cv_get_link_url(cls, action.key, obj)
```

(`cls = view.cv_viewset.get_view_class(action.key)` is assigned a few lines above.)

- [ ] **Step 4: Run the new tests, then the full suite**

Run: `.venv/bin/pytest tests/test1/test_cancel_origin.py -q`
Expected: all pass.

Run: `.venv/bin/pytest tests -q`
Expected: all pass. Twenty-three existing files compare update/delete URLs exactly; they must still pass because none of their ViewSets declares `cv_cancel_keys`.

- [ ] **Step 5: Lint and commit**

```bash
.venv/bin/ruff format src tests && .venv/bin/ruff check src tests
git add src/crud_views/lib/view/base.py src/crud_views/lib/view/buttons.py src/crud_views/templatetags/crud_views.py tests/test1/test_cancel_origin.py
git commit -m "feat(links): sibling links carry the origin key for views with cv_cancel_keys"
```

---

### Task 5: Origin survives validation bounces (form action = full path)

**Files:**
- Modify: `src/crud_views/templates/crud_views/view_create.content.html:3`
- Modify: `src/crud_views/templates/crud_views/view_update.content.html:3`
- Modify: `src/crud_views/templates/crud_views/view_delete.content.html:17`
- Modify: `src/crud_views/templates/crud_views/view_custom_form.content.html:3`
- Test: `tests/test1/test_cancel_origin.py` (append), `tests/test1/test_modal.py` (append)

**Interfaces:**
- Consumes: resolution (Task 3) and emission (Task 4).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test1/test_cancel_origin.py`:

```python
# ---------------------------------------------------------------------------
# Validation bounces (Task 5): the origin survives an invalid POST re-render
# ---------------------------------------------------------------------------


def form_action(response) -> str:
    match = re.search(r'<form[^>]*class="cv-form"[^>]*action="([^"]*)"', response.content.decode())
    assert match, "no cv-form found"
    return match.group(1)


@pytest.mark.django_db
def test_update_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    origin_url = f"{url(cv_author_origin, 'update', pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {"first_name": "", "last_name": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_create_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin):
    origin_url = f"{url(cv_author_origin, 'create')}?{PARAM}=list"
    response = client_user_author_origin.post(origin_url, {"first_name": "", "last_name": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "list")


@pytest.mark.django_db
def test_delete_unconfirmed_post_keeps_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    origin_url = f"{url(cv_author_origin, 'delete', pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {})  # confirm missing -> invalid
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_delete_protection_post_keeps_origin(client_user_author_origin, cv_author_origin):
    from tests.test1.app.models import Author

    author = Author.objects.create(first_name="Locked", last_name="Author", pseudonym="protected")
    origin_url = f"{url(cv_author_origin, 'delete', author.pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {"confirm": True})
    assert response.status_code == 200
    assert "This author is protected." in response.content.decode()
    assert Author.objects.filter(pk=author.pk).exists()
    # the protection page hides the form; the GET with origin still resolves for the button context
    response = client_user_author_origin.get(origin_url)
    assert response.context["view"].cv_get_cancel_key() == "detail"


@pytest.mark.django_db
def test_custom_form_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin, author_douglas_adams):
    pk = author_douglas_adams.pk
    origin_url = f"{url(cv_author_origin, 'contact', pk)}?{PARAM}=detail"
    response = client_user_author_origin.post(origin_url, {"subject": "", "body": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "detail", pk)


@pytest.mark.django_db
def test_no_object_custom_form_invalid_post_keeps_origin(client_user_author_origin, cv_author_origin):
    origin_url = f"{url(cv_author_origin, 'broadcast')}?{PARAM}=list"
    response = client_user_author_origin.post(origin_url, {"subject": ""})
    assert response.status_code == 200
    assert form_action(response) == origin_url
    assert cancel_url(response) == url(cv_author_origin, "list")
```

Append to `tests/test1/test_modal.py`:

```python
# ---------------------------------------------------------------------------
# Cancel origin survives the modal 422 re-render
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modal_custom_form_invalid_keeps_cancel_origin(client_user_author_modal: Client, author_douglas_adams, monkeypatch):
    """A modal custom-form re-render (422) keeps the origin-resolved cancel URL."""
    import re

    from tests.test1.app.views import AuthorModalContactView

    monkeypatch.setattr(AuthorModalContactView, "cv_cancel_keys", ["detail"])
    pk = author_douglas_adams.pk
    origin_url = f"/author_modal/{pk}/contact/?cv_from=detail"
    response = client_user_author_modal.post(origin_url, {"subject": "", "body": ""}, headers=MODAL_HEADERS)
    assert response.status_code == 422
    html = response.content.decode()
    assert re.search(r'action="' + re.escape(origin_url) + '"', html)
    assert f'data-cv-cancel-url="/author_modal/{pk}/detail/"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test1/test_cancel_origin.py -q -k "invalid_post or unconfirmed or protection" && .venv/bin/pytest tests/test1/test_modal.py -q -k keeps_cancel_origin`
Expected: each `form_action` assertion fails because the action is the bare path (`request.path`), and the cancel URL falls back to card/list.

- [ ] **Step 3: Change the four form actions**

In each of the four templates replace `action="{{ request.path }}"` with `action="{{ request.get_full_path }}"`:

`src/crud_views/templates/crud_views/view_create.content.html`:
```html
<form class="cv-form" method="post" action="{{ request.get_full_path }}" novalidate>
```

`src/crud_views/templates/crud_views/view_update.content.html`:
```html
<form class="cv-form" method="post" action="{{ request.get_full_path }}" enctype="multipart/form-data" novalidate>
```

`src/crud_views/templates/crud_views/view_delete.content.html` (line 17):
```html
    <form class="cv-form" method="post" action="{{ request.get_full_path }}" novalidate>
```

`src/crud_views/templates/crud_views/view_custom_form.content.html`:
```html
<form class="cv-form" method="post" action="{{ request.get_full_path }}" novalidate>
```

- [ ] **Step 4: Run the new tests, then the full suite**

Run: `.venv/bin/pytest tests/test1/test_cancel_origin.py tests/test1/test_modal.py -q`
Expected: all pass. The pre-existing `test_modal_partial_form_has_explicit_action` keeps passing unchanged: it requests without a query string, and `get_full_path` equals `path` then.

Run: `.venv/bin/pytest tests -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views/templates/crud_views/view_create.content.html src/crud_views/templates/crud_views/view_update.content.html src/crud_views/templates/crud_views/view_delete.content.html src/crud_views/templates/crud_views/view_custom_form.content.html tests/test1/test_cancel_origin.py tests/test1/test_modal.py
git commit -m "fix(templates): form views post to the full path so the cancel origin survives validation errors"
```

---

### Task 6: Examples project uses `cv_cancel_keys`

**Files:**
- Modify: `examples/bootstrap5/library/views.py` (`AuthorUpdateView`, `AuthorDeleteView`, lines 94-104)
- Modify: `examples/bootstrap5/project/features.py` (the `library` entry's `look_at`)
- Modify: `examples/bootstrap5/library/tests.py` (`AuthorCrudTest`)

**Interfaces:**
- Produces: the exact code block the docs sync marker in Task 7 points at (`library/views.py`, contiguous lines).

- [ ] **Step 1: Write the failing tests**

Add to `AuthorCrudTest` in `examples/bootstrap5/library/tests.py`:

```python
    def test_update_cancel_returns_to_detail_origin(self):
        detail_url = reverse("author-detail", kwargs={"pk": self.author.pk})
        update_url = reverse("author-update", kwargs={"pk": self.author.pk})
        resp = self.client.get(detail_url)
        self.assertContains(resp, f'href="{update_url}?cv_from=detail"')
        resp = self.client.get(update_url, {"cv_from": "detail"})
        self.assertContains(resp, f'data-cv-cancel-url="{detail_url}"')

    def test_update_cancel_returns_to_list_origin(self):
        list_url = reverse("author-list")
        update_url = reverse("author-update", kwargs={"pk": self.author.pk})
        resp = self.client.get(list_url)
        self.assertContains(resp, f'href="{update_url}?cv_from=list"')
        resp = self.client.get(update_url, {"cv_from": "list"})
        self.assertContains(resp, f'data-cv-cancel-url="{list_url}"')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/bootstrap5 && ../../.venv/bin/pytest library/tests.py -q -k cancel; cd ../..`
Expected: 2 failures, `?cv_from=` not found in the response.

- [ ] **Step 3: Opt the example views in**

In `examples/bootstrap5/library/views.py` replace the two classes:

```python
class AuthorUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message_template_code = "Updated author »{{ object }}«"
    cv_cancel_keys = ["list", "detail"]  # cancel returns to where the user came from


class AuthorDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_author
    form_class = CrispyDeleteForm
    cv_message_template_code = "Deleted author »{{ object }}«"
    cv_show_related_objects = True
    cv_cancel_keys = ["list", "detail"]
```

In `examples/bootstrap5/project/features.py`, change the `library` entry's `look_at` to:

```python
        look_at=(
            "the cv_author and cv_book ViewSets and their List/Detail/Create/Update/Delete views; AuthorTable "
            "and AuthorFilter for the table and filter; BookUpView / BookDownView for ordering; "
            "cv_cancel_keys on AuthorUpdateView / AuthorDeleteView, which sends Cancel back to the page "
            "you came from (list or detail)."
        ),
```

- [ ] **Step 4: Run the example tests**

Run: `cd examples/bootstrap5 && ../../.venv/bin/pytest -q; cd ../..`
Expected: all pass (including `test_docs_sync.py`, which is unaffected until Task 7 adds a marker).

- [ ] **Step 5: Commit**

```bash
.venv/bin/ruff format examples && .venv/bin/ruff check examples
git add examples/bootstrap5/library/views.py examples/bootstrap5/library/tests.py examples/bootstrap5/project/features.py
git commit -m "docs(examples): library update/delete views use cv_cancel_keys"
```

---

### Task 7: Package docs and changelog

**Files:**
- Modify: `docs/reference/update_view.md` (configuration table line 42-50, new section before `## Reusing the Create Form`)
- Modify: `docs/reference/create_view.md` (table line 50-58)
- Modify: `docs/reference/delete_view.md` (table line 28-38)
- Modify: `docs/reference/custom_form_view.md` (table line 70-80)
- Modify: `docs/reference/card-list-view.md` (line 196-199)
- Modify: `CHANGELOG.md` (`## Unreleased`)

**Interfaces:**
- Consumes: the `AuthorUpdateView` block from Task 6 (docs sync marker must match it verbatim, whitespace-normalized, blank lines ignored).

- [ ] **Step 1: Update `docs/reference/update_view.md`**

Add two rows after the `cv_success_key` row of the configuration table:

```markdown
| `cv_cancel_key` | `str` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `list[str] \| None` | `None` | Origin keys the cancel button may return to dynamically; see [Dynamic cancel target](#dynamic-cancel-target) |
```

Insert before `## Reusing the Create Form`:

````markdown
## Dynamic cancel target

*Available since 0.21.0.*

By default the cancel button always returns to `cv_cancel_key` (`"list"`). With `cv_cancel_keys`
the button returns to the sibling view the user came from instead:

<!-- cv-sync: library/views.py -->
```python
class AuthorUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message_template_code = "Updated author »{{ object }}«"
    cv_cancel_keys = ["list", "detail"]  # cancel returns to where the user came from
```

How it works:

- Links **into** a view with `cv_cancel_keys` carry the current view's key as a query parameter
  when that key is listed: `/author/<pk>/update/?cv_from=detail` from the detail page,
  `?cv_from=list` from the list. Links into views without `cv_cancel_keys` are unchanged.
  The parameter name is `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` (default `cv_from`, see [Settings](settings.md#cancel-button)).
- The view resolves the target with `cv_get_cancel_key()`: the value must match `^[a-z][a-z0-9_]*$`,
  be listed in `cv_cancel_keys`, be registered on the ViewSet, and, for object views such as `detail`,
  the current view must have an object (a create view falls back). Anything else falls back to
  `cv_cancel_key`. The parameter is a **view key**, never a URL, so it cannot redirect elsewhere.
- The origin survives validation errors: the form posts to `request.get_full_path`, so an invalid
  submit re-renders with the same cancel target, in full-page and modal mode.
- System check `viewset.E252` fails at startup when an entry of `cv_cancel_keys` is not a registered
  view key (`"list"` is accepted when only a card view is registered).

Works the same on `CreateView`, `DeleteView`, `CustomFormView` and `CustomFormNoObjectView`.
Custom templates that build a back link from the cancel key should use
`{% cv_context_url view.cv_get_cancel_key as url %}` rather than `view.cv_cancel_key`.

````

- [ ] **Step 2: Update the other reference tables**

`docs/reference/create_view.md`, after the `cv_success_key` row:

```markdown
| `cv_cancel_key` | `str` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `list[str] \| None` | `None` | Origin keys the cancel button may return to dynamically; object views such as `detail` are never used from a create view. See [UpdateView](update_view.md#dynamic-cancel-target) |
```

`docs/reference/delete_view.md`, after the `cv_success_key` row:

```markdown
| `cv_cancel_key` | `str` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `list[str] \| None` | `None` | Origin keys the cancel button may return to dynamically. See [UpdateView](update_view.md#dynamic-cancel-target) |
```

`docs/reference/custom_form_view.md`, after the `cv_success_key` row:

```markdown
| `cv_cancel_key` | `str` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `list[str] \| None` | `None` | Origin keys the cancel button may return to dynamically (no-object views only to non-object keys). See [UpdateView](update_view.md#dynamic-cancel-target) |
```

`docs/reference/card-list-view.md`, replace the "List Key Fallback" paragraph with:

```markdown
When a ViewSet has a `CardListView` but no `ListView`, keys that reference `"list"`
(such as `cv_success_key`, `cv_cancel_key`, `cv_cancel_keys`, and the default "home" context button)
automatically fall back to `"card"`. No manual overrides needed. Card actions carry the
`card` origin key into views that list it in `cv_cancel_keys`
(see [Dynamic cancel target](update_view.md#dynamic-cancel-target)).
```

- [ ] **Step 3: Changelog**

Under `## Unreleased` in `CHANGELOG.md`:

```markdown
### Added

- Dynamic cancel button target. A view that declares `cv_cancel_keys = ["list", "detail"]`
  sends its cancel button back to the sibling view the user came from. Sibling links into such a
  view carry the origin as a validated view key in the query string
  (`?cv_from=detail`, name configurable via `CRUD_VIEWS_CANCEL_ORIGIN_PARAM`). Unknown, disallowed,
  or malformed values fall back to the unchanged `cv_cancel_key`. New system checks
  `crud_views.E103` (invalid parameter name) and `viewset.E252` (unregistered key in
  `cv_cancel_keys`). Views without `cv_cancel_keys` are unaffected.

### Changed

- The create, update, delete and custom-form content templates post to `request.get_full_path`
  instead of `request.path`, so the query string survives a validation re-render. Themes that
  override these templates should do the same to get the dynamic cancel target on re-render.
```

- [ ] **Step 4: Verify docs sync and build**

Run: `cd examples/bootstrap5 && ../../.venv/bin/pytest test_docs_sync.py -q; cd ../..`
Expected: pass (the marked block matches `library/views.py` from Task 6).

Run: `.venv/bin/mkdocs build -q`
Expected: no warnings about broken anchors (`update_view.md#dynamic-cancel-target`, `settings.md#cancel-button`).

- [ ] **Step 5: Commit**

```bash
git add docs/reference/update_view.md docs/reference/create_view.md docs/reference/delete_view.md docs/reference/custom_form_view.md docs/reference/card-list-view.md CHANGELOG.md
git commit -m "docs: dynamic cancel target (cv_cancel_keys, CRUD_VIEWS_CANCEL_ORIGIN_PARAM)"
```

---

### Task 8: Public skill update (sibling repo)

**Files (all under `/home/alex/projects/alex/skills/plugins/django-crud-views/`):**
- Modify: `skills/django-crud-views/SKILL.md` (after "### List Key Fallback", line ~228)
- Modify: `skills/django-crud-views/references/api-reference.md` (UpdateView section line ~167, Settings block line ~727, checks section at end)
- Modify: `CHANGELOG.md` (`## [Unreleased]`)

**Interfaces:**
- Consumes: final names from Tasks 1-3: `cv_cancel_keys`, `cv_get_cancel_key()`, `CRUD_VIEWS_CANCEL_ORIGIN_PARAM`, `crud_views.E103`, `viewset.E252`.

- [ ] **Step 1: Write the drift audit and run it against the current skill (must report the gap)**

Create `/tmp/claude-1000/-home-alex-projects-alex-django-crud-views/b1428503-659d-4192-b431-f70a2e2274e5/scratchpad/skill_audit.sh`:

```bash
#!/usr/bin/env bash
# Skill drift audit: every CRUD_VIEWS_* name in the skill must exist in the package source,
# every `from crud_views... import X` in the skill must resolve, and the new feature must be present.
set -u
PKG=/home/alex/projects/alex/django-crud-views
SKILL=/home/alex/projects/alex/skills/plugins/django-crud-views/skills/django-crud-views
ALLOW='^(CRUD_VIEWS_MANAGE|CRUD_VIEWS_STRICT)$'   # group name / read via getattr, not settings fields
echo "== settings names in skill but not in src =="
comm -23 <(grep -rhoE 'CRUD_VIEWS_[A-Z0-9_]+' "$SKILL" | sort -u) \
         <(grep -rhoE 'CRUD_VIEWS_[A-Z0-9_]+' "$PKG/src" | sort -u) | grep -vE "$ALLOW"
echo "== imports that do not resolve =="
grep -rhoE '^from crud_views[a-z_.]* import [A-Za-z_, ]+' "$SKILL" | sort -u | sed 's/ *#.*//' \
  | "$PKG/.venv/bin/python" -c '
import sys
sys.path.insert(0, "'"$PKG"'")
from tests.test1.conftest import pytest_configure
pytest_configure()
bad = 0
for line in sys.stdin:
    line = line.strip()
    try:
        exec(line, {})
    except Exception as e:
        bad += 1
        print(f"  {line}  ->  {e!r}")
sys.exit(bad)
'
echo "== feature presence =="
for needle in cv_cancel_keys CRUD_VIEWS_CANCEL_ORIGIN_PARAM cv_get_cancel_key E103 E252; do
  n=$(grep -rc "$needle" "$SKILL" | awk -F: '{s+=$2} END {print s}')
  echo "  $needle: $n occurrence(s)"
done
```

Run: `bash /tmp/claude-1000/-home-alex-projects-alex-django-crud-views/b1428503-659d-4192-b431-f70a2e2274e5/scratchpad/skill_audit.sh`
Expected before editing: the settings and import sections print nothing (no drift today); the feature presence section prints `0 occurrence(s)` for every needle. That zero is the RED state this task fixes.

- [ ] **Step 2: Edit `SKILL.md`**

Insert after the "### List Key Fallback" paragraph:

````markdown
### Cancel button target

*Available since 0.21.0.*

The cancel button returns to `cv_cancel_key` (`"list"`). Set `cv_cancel_keys` to let it return
to the sibling view the user came from instead:

```python
class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_cancel_keys = ["list", "detail"]   # dynamic; cv_cancel_key stays the fallback
```

Links into such a view carry the origin as a view key in the query string
(`/author/<pk>/update/?cv_from=detail`); the parameter name is `CRUD_VIEWS_CANCEL_ORIGIN_PARAM`
(default `cv_from`). Values that are malformed, not in `cv_cancel_keys`, unregistered, or that
need an object the view lacks (e.g. `detail` on a create view) fall back to `cv_cancel_key`.
The origin survives validation errors (forms post to `request.get_full_path`) and modal
re-renders. Works on Create/Update/Delete/CustomForm views. In custom templates resolve the
target with `{% cv_context_url view.cv_get_cancel_key as url %}`, not `view.cv_cancel_key`.
Checks: `crud_views.E103` (bad parameter name), `viewset.E252` (unregistered key).

````

- [ ] **Step 3: Edit `references/api-reference.md`**

In the UpdateView code block (line ~167-177) add after `cv_success_key = "list"`:

```python
    cv_cancel_key = "list"               # cancel button target (default: "list")
    cv_cancel_keys = ["list", "detail"]  # optional: return to the origin view instead (since 0.21.0)
```

In the Settings block, after the `# Session` lines:

```python
# Cancel button (since 0.21.0)
CRUD_VIEWS_CANCEL_ORIGIN_PARAM = "cv_from"             # query param carrying the origin view key; must match ^[a-z][a-z0-9_]*$ (crud_views.E103)
```

Append at the end of the file:

```markdown
## Dynamic cancel target (`cv_cancel_keys`)

*Available since 0.21.0.*

| Name | Where | Meaning |
|---|---|---|
| `cv_cancel_key` | view attribute, `str \| None`, default `"list"` | static cancel target |
| `cv_cancel_keys` | view attribute, `list[str] \| None`, default `None` | origin keys the cancel button may return to; enables the feature |
| `cv_get_cancel_key(obj=None)` | view method | resolved key: validated origin or `cv_cancel_key`; `obj` defaults to the view's object |
| `cv_get_origin_key()` | view method | raw origin from the request, `None` if absent or not matching `^[a-z][a-z0-9_]*$` |
| `cv_get_link_url(cls, key, obj=None)` | view method | sibling URL, with `?<param>=<own key>` when `cls.cv_cancel_keys` lists this view's key |
| `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` | setting, default `"cv_from"` | parameter name; `crud_views.E103` when invalid |
| `viewset.E252` | system check | an entry of `cv_cancel_keys` is not a registered view key |
```

- [ ] **Step 4: Edit the skill `CHANGELOG.md`**

Under `## [Unreleased]`:

```markdown
### Added
- **Dynamic cancel target** (package 0.21.0): `cv_cancel_keys`, `cv_get_cancel_key()`,
  `CRUD_VIEWS_CANCEL_ORIGIN_PARAM`, checks `crud_views.E103` / `viewset.E252`; new SKILL.md
  section "Cancel button target" and an api-reference table.
```

- [ ] **Step 5: Re-run the audit, commit and push in one invocation**

Run: `bash /tmp/claude-1000/-home-alex-projects-alex-django-crud-views/b1428503-659d-4192-b431-f70a2e2274e5/scratchpad/skill_audit.sh`
Expected: settings and import sections print nothing; every needle reports at least 1 occurrence.

```bash
git -C /home/alex/projects/alex/skills add plugins/django-crud-views && git -C /home/alex/projects/alex/skills commit -m "docs(django-crud-views): dynamic cancel target (cv_cancel_keys, package 0.21.0)" && git -C /home/alex/projects/alex/skills push origin main && git -C /home/alex/projects/alex/skills status -sb | head -1
```

Expected: the last line shows `## main...origin/main` with no ahead/behind marker.

---

### Task 9: Final verification

**Files:** none new.

- [ ] **Step 1: Full package suite, lint, format**

Run: `.venv/bin/ruff format --check src tests examples && .venv/bin/ruff check src tests examples && .venv/bin/pytest tests -q`
Expected: format clean, no lint findings, all tests pass (baseline 875 + the new ones, 1 skipped).

- [ ] **Step 2: Examples suite and docs build**

Run: `cd examples/bootstrap5 && ../../.venv/bin/pytest -q; cd ../.. && .venv/bin/mkdocs build -q`
Expected: all pass, docs build without warnings.

- [ ] **Step 3: JS tests are unaffected**

Run: `npm test --silent 2>&1 | tail -3`
Expected: all pass (no JS was changed; this proves the template change did not break `modal.js` expectations).

- [ ] **Step 4: Hand off**

Use the `superpowers:finishing-a-development-branch` skill: open a PR from `feature/cancel-button-origin` to `main`, wait for CI (lint, js-tests, tests 3.12/3.13/3.14, codecov/patch via the check-runs API, not `gh pr checks`), squash-merge, then wait for CI on `main`.
