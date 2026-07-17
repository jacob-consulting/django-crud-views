# Card action POST/modal parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Card list actions (`CardAction`) that target POST-only or modal-enabled views render correctly — a hidden POST form + submit-form trigger, or a modal trigger — instead of a bare GET link that 405s.

**Architecture:** The card action template tag (`cv_card_action`) currently hand-rolls its context dict, bypassing `CrudView.cv_get_dict()` which already emits `cv_list_action_method`, `cv_modal`, `cv_modal_size`. We route the tag through `cv_get_dict()` (as the table path does) and rewrite `card_action.html` to mirror `list_action.html`'s modal/GET/POST branch, emitting an inline hidden form for POST actions. Reuses the existing `submit-form` JS in `viewset.js`. No new `CardAction` field, no new client code.

**Tech Stack:** Django template tags + templates, django-crud-views ViewSet/CrudView, pytest + lxml (`cssselect`) for rendered-markup assertions.

## Global Constraints

- Line length: 120 chars; double quotes; `ruff format` on commit (pre-commit hook).
- All `CrudView` attributes use the `cv_` prefix.
- Bootstrap 5 theme; theme path resolved at module load in `templatetags/crud_views.py`.
- Tests run from `tests/`: `cd tests && pytest`.
- Pure package change, no migration, no public API change. A patch release follows merge (out of scope for this plan).
- The `submit-form` JS already exists and loads on every page via `cv_js` — do **not** add JS.

---

### Task 1: Card action POST + modal parity (tag + template)

Rewrite the card action tag to reuse `cv_get_dict()` and the card action template to branch modal/GET/POST with an inline hidden form. Driven by a POST test and a modal test that both start RED.

**Files:**
- Modify: `src/crud_views/templatetags/crud_views.py` (`cv_card_action`, ~L262–306)
- Modify: `src/crud_views/templates/crud_views/tags/card_action.html` (full rewrite)
- Test: `tests/test1/test_card_action_post.py` (create)

**Interfaces:**
- Consumes (already exist, do not change):
  - `CrudView.cv_get_dict(cls, context, **extra) -> dict` — emits `cv_list_action_method`, `cv_modal`, `cv_modal_size`, `cv_key`, `cv_action_label`, etc.
  - `view.cv_get_oid(key, obj) -> str` — returns `"{viewset_name}_{key}_{pk_no_dashes}"`.
  - `view.cv_get_url(key, obj=obj) -> str`; `view.cv_get_view_context(object=obj) -> ViewContext`.
  - `cls.cv_has_access(user, obj)`, `cls.cv_action_enabled(user, obj)`, `cls.cv_get_action_short_label(context=...)`.
  - Target views on `cv_author`: `AuthorUpView` (`cv_key="up"`, `cv_list_action_method="post"`, `cv_permission="change"`), `AuthorDeleteView` (modal-capable).
- Produces: the `cv_card_action` inclusion-tag context now includes `cv_list_action_method`, `cv_modal`, `cv_modal_size`, `cv_oid` for regular-key actions; `cv_list_action_method="get"` for `child_name` actions. Template contract: POST actions emit `<form id="cv_form_{cv_oid}" ...>` + `<a data-cv-action="submit-form" data-cv-target="cv_form_{cv_oid}">`.

- [ ] **Step 1: Write the failing POST test**

Create `tests/test1/test_card_action_post.py`:

```python
import pytest
from django.test.client import Client
from lxml import html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def user_author_view_change(cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view_change", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    user_viewset_permission(user, cv_author, "delete")
    return user


@pytest.fixture
def client_user_author_view_change(client, user_author_view_change) -> Client:
    client.force_login(user_author_view_change)
    return client


@pytest.mark.django_db
def test_card_post_action_renders_submit_form(
    client_user_author_view_change: Client, cv_author, author_douglas_adams, monkeypatch
):
    """A CardAction targeting a POST-only view renders a submit-form trigger + hidden POST form, not a GET link."""
    from tests.test1.app.views import AuthorCardListView

    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [CardAction(key="detail", label="Details"), CardAction(key="up", label="Up")],
    )

    response = client_user_author_view_change.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    pk = author_douglas_adams.pk

    # POST action -> submit-form trigger anchor (href="#", not the action URL)
    trigger = card.cssselect("a[data-cv-action='submit-form']")
    assert len(trigger) == 1
    target = trigger[0].get("data-cv-target")
    assert target.startswith("cv_form_")
    assert trigger[0].get("href") == "#"

    # POST action -> hidden form present, tied to the trigger by id, with the action URL and a CSRF token
    form = card.cssselect(f"form#{target}")
    assert len(form) == 1
    assert form[0].get("action") == f"/author/{pk}/up/"
    assert form[0].get("method") == "post"
    assert "d-none" in form[0].get("class")
    assert len(form[0].cssselect("input[name='csrfmiddlewaretoken']")) == 1

    # The "Up" button must NOT be a bare GET link to the action URL
    hrefs = [a.get("href") for a in card.cssselect("a.btn")]
    assert f"/author/{pk}/up/" not in hrefs
```

- [ ] **Step 2: Write the failing modal test**

Append to `tests/test1/test_card_action_post.py`:

```python
@pytest.mark.django_db
def test_card_modal_action_renders_modal_trigger(
    client_user_author_view_change: Client, cv_author, author_douglas_adams, monkeypatch
):
    """A CardAction targeting a modal-enabled view renders a modal trigger (data-cv-modal), not a plain link."""
    from tests.test1.app.views import AuthorCardListView, AuthorDeleteView

    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    monkeypatch.setattr(AuthorDeleteView, "cv_modal_size", "lg")
    monkeypatch.setattr(
        AuthorCardListView, "cv_card_actions", [CardAction(key="delete", label="Delete")]
    )

    response = client_user_author_view_change.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    pk = author_douglas_adams.pk

    modal_trigger = card.cssselect("a[data-cv-modal='true']")
    assert len(modal_trigger) == 1
    assert modal_trigger[0].get("data-cv-modal-size") == "lg"
    assert modal_trigger[0].get("href") == f"/author/{pk}/delete/"

    # A modal action is neither a submit-form trigger nor does it emit a hidden form
    assert len(card.cssselect("a[data-cv-action='submit-form']")) == 0
    assert len(card.cssselect("form.d-none")) == 0
```

- [ ] **Step 3: Run both tests to verify they fail**

Run: `cd tests && pytest test1/test_card_action_post.py -v`
Expected: both FAIL — the POST test finds no `a[data-cv-action='submit-form']` (current template renders a bare `<a href>`); the modal test finds no `a[data-cv-modal='true']`.

- [ ] **Step 4: Rewrite `cv_card_action` to reuse `cv_get_dict()`**

Replace the whole `cv_card_action` function body in `src/crud_views/templatetags/crud_views.py` (currently ~L262–306) with:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/card_action.html", takes_context=True)
def cv_card_action(context, action, obj=None):
    view = cv_get_view(context)

    if action.child_name:
        url = view.cv_get_child_url(action.child_name, action.child_key, obj)
        child_viewset = view.cv_viewset.get_viewset(action.child_name)
        child_cls = child_viewset.get_view_class(action.child_key)
        return {
            "cv_access": True,
            "cv_action_enabled": child_cls.cv_action_enabled(context["request"].user, obj),
            "cv_url": url,
            "cv_label": action.label,
            "cv_icon_action": child_cls.cv_icon_action,
            "cv_variant": action.variant,
            "cv_flex": action.flex,
            "cv_no_label": action.no_label,
            "cv_list_action_method": "get",
        }

    user = context["request"].user
    cls = view.cv_viewset.get_view_class(action.key)
    access = cls.cv_has_access(user, obj)
    action_enabled = cls.cv_action_enabled(user, obj)

    if not access:
        return {"cv_access": False, "cv_action_enabled": action_enabled}

    url = view.cv_get_url(action.key, obj=obj)
    view_context = view.cv_get_view_context(object=obj)

    if action.label:
        label = action.label
    else:
        label = cls.cv_get_action_short_label(context=view_context)

    data = cls.cv_get_dict(
        context=view_context,
        cv_oid=view.cv_get_oid(action.key, obj=obj),
        cv_url=url,
        cv_access=True,
        cv_action_enabled=action_enabled,
    )
    data.update(
        cv_label=label,
        cv_variant=action.variant,
        cv_flex=action.flex,
        cv_no_label=action.no_label,
    )
    return data
```

- [ ] **Step 5: Rewrite `card_action.html` to branch modal/GET/POST**

Replace the entire contents of `src/crud_views/templates/crud_views/tags/card_action.html` with:

```html
{% if cv_access and cv_action_enabled is not False %}
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

- [ ] **Step 6: Run the two tests to verify they pass**

Run: `cd tests && pytest test1/test_card_action_post.py -v`
Expected: both PASS.

- [ ] **Step 7: Add a GET-regression test and run it**

Append to `tests/test1/test_card_action_post.py`:

```python
@pytest.mark.django_db
def test_card_get_action_stays_plain_link(
    client_user_author_view_change: Client, cv_author, author_douglas_adams, monkeypatch
):
    """GET card actions still render as plain href links (no submit-form, no form, no modal)."""
    from tests.test1.app.views import AuthorCardListView

    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key="detail", label="Details")])

    response = client_user_author_view_change.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.cssselect(".card.mb-3")[0]
    pk = author_douglas_adams.pk

    detail = card.cssselect("a.btn")[0]
    assert detail.get("href") == f"/author/{pk}/detail/"
    assert detail.get("data-cv-action") is None
    assert detail.get("data-cv-modal") is None
    assert len(card.cssselect("form")) == 0
```

Run: `cd tests && pytest test1/test_card_action_post.py -v`
Expected: all three PASS.

- [ ] **Step 8: Run the full card suite to confirm no regressions**

Run: `cd tests && pytest test1/test_card.py test1/test_card_order.py test1/test_filter_pinned.py test1/test_card_action_post.py -v`
Expected: all PASS (existing `test_card_actions_render` / child-action / no-access tests unchanged — the shared `AuthorCardListView.cv_card_actions` is only monkeypatched inside the new tests).

- [ ] **Step 9: Lint and format**

Run: `ruff format . && ruff check --fix`
Expected: no errors; file reformatted if needed.

- [ ] **Step 10: Commit**

```bash
git add src/crud_views/templatetags/crud_views.py \
        src/crud_views/templates/crud_views/tags/card_action.html \
        tests/test1/test_card_action_post.py
git commit -m "fix: card actions support POST and modal targets (#77)

Route cv_card_action through cv_get_dict() and branch card_action.html
modal/GET/POST like list_action.html, emitting a hidden POST form for
POST-only ActionView targets. Fixes 405 on POST card actions and the
latent modal-on-card gap. Reuses existing submit-form JS."
```

---

### Task 2: Document POST/modal card actions

Add a short note to the card-list reference so a reader (especially one who hit the 405) knows POST-only and modal target views are supported.

**Files:**
- Modify: `docs/reference/card-list-view.md`

**Interfaces:**
- Consumes: nothing (docs only).
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Read the CardAction section to find the insertion point**

Run: `sed -n '15,60p' docs/reference/card-list-view.md`
Expected: shows the intro `CardAction` example block and the `## CardAction Fields` heading — insert the note immediately after the intro example (before `## CardAction Fields`).

- [ ] **Step 2: Add the note**

Insert this paragraph after the introductory `cv_card_actions` example block (immediately before the `## CardAction Fields` heading):

```markdown
Actions are rendered to match their target view automatically, exactly as table-list actions are:

- A `key` pointing at a **GET** view (detail, update) renders a plain link.
- A `key` pointing at a **POST-only** view — ordered up/down or any custom `ActionView` — renders a hidden POST form plus a submit-form trigger button (no bare GET link, so no `405 Method Not Allowed`).
- A `key` pointing at a **modal-enabled** view (`cv_modal = True`) renders a modal trigger.

You do not configure this on `CardAction`; the method and modal behaviour derive from the target view.
```

- [ ] **Step 3: Verify the note renders and reads correctly**

Run: `sed -n '15,45p' docs/reference/card-list-view.md`
Expected: the new paragraph appears between the intro example and `## CardAction Fields`, with the three bullets intact.

- [ ] **Step 4: Commit**

```bash
git add docs/reference/card-list-view.md
git commit -m "docs: note POST/modal support for card actions (#77)"
```

---

## Follow-up (out of scope — separate repo, tracked only)

Per the spec, mirror a one-line note into the standalone `SKILL.md` (skills monorepo; the plugin
cache is a read-only mirror) after this fix merges/releases: "`CardAction` targets that are
POST-only or modal views work automatically." Not a task in this plan — no code/API change makes
the current skill text wrong; it is a preventive doc touch handled separately.

## Self-Review

**Spec coverage:**
- Reuse `cv_get_dict()` in card tag → Task 1, Step 4. ✅
- Full modal/GET/POST branch + inline hidden form → Task 1, Step 5. ✅
- `child_name` stays GET (explicit `cv_list_action_method="get"`) → Task 1, Step 4. ✅
- `CardAction` unchanged (no new field) → not modified anywhere. ✅
- Test: POST + GET + modal rendering → Task 1, Steps 1/2/7. ✅
- Docs note → Task 2. ✅
- Skill note → Follow-up section (tracked, not a task). ✅

**Placeholder scan:** No TBD/TODO; every code and command step shows full content. ✅

**Type/name consistency:** Template contract `cv_form_{cv_oid}` / `data-cv-target` matches between Step 4 (tag emits `cv_oid`), Step 5 (template), and the tests (trigger→form tied by matching `id`). `cv_list_action_method` values (`"get"`/`"post"`) consistent across tag, template, and target views. `AuthorUpView` (`up`, POST) and `AuthorDeleteView` (modal) match the verified codebase. ✅
