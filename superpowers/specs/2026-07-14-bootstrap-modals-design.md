# Modal Views (Bootstrap 5) — Design Spec

**Date:** 2026-07-14
**Status:** Approved design — basis for the implementation plan.
**Predecessor:** `superpowers/specs/2026-07-14-bootstrap-modals-solutions.md` (solution comparison; Solution A chosen).
**Source prompt:** `superpowers/prompts/2026-07-14-bootstrap-modals.md`

## 1. Decisions

All brainstorming decisions, final:

| Topic | Decision |
|---|---|
| Transport | **Solution A**: vanilla `fetch` + Bootstrap 5 modal, new `modal.js`; no new dependencies |
| Modal opt-in | **Per view class only**: `cv_modal = True` on the view; every button linking to it opens the modal |
| Request detection | `X-CV-Modal: true` request header; same URL, content negotiation; `Vary: X-CV-Modal` on responses |
| Success flow | Full-page redirect: `204` + `X-CV-Redirect: <success_url>`; browser navigates; Django messages untouched |
| Invalid form / delete protection | Re-rendered modal partial with status **422** (non-modal flow keeps 200 as today) |
| Modal shell | Rendered by the existing `{% cv_config %}` tag — zero host-template migration |
| Phase 1 view types | `DeleteView`, `DetailView`, `CustomFormView` (object and no-object variants); create/update hard-gated by a system check until phase 2 |
| Theme | Bootstrap 5 (`crud_views` core) only; `crud_views_plain` ignores `cv_modal` (buttons stay plain links, full pages render) |
| Testing | pytest only (HTTP protocol fully covered); `modal.js` verified manually in the bootstrap5 example app; no JS test infra |

Non-goals: stacked modals, in-place list refresh, modals for `ActionView` (up/down), polymorphic
create-select chain in a modal, context actions inside the modal.

## 2. API Surface

```python
class CrudView:
    cv_modal: bool = False        # opt-in: action buttons open this view in a Bootstrap modal
    cv_modal_size: str = ""       # "" | "modal-sm" | "modal-lg" | "modal-xl"
    cv_content_template: str | None = None   # the view's body partial (set by concrete views)
```

Concrete phase-1 views set their existing partials:

| View | `cv_content_template` |
|---|---|
| `DeleteView` | `crud_views/view_delete.content.html` |
| `DetailView` | `crud_views/view_detail.content.html` |
| `CustomFormView` / `CustomFormNoObjectView` | `crud_views/view_custom_form.content.html` |
| `CreateView` | `crud_views/view_create.content.html` (set now; modal use gated to phase 2) |
| `UpdateView` | `crud_views/view_update.content.html` (set now; modal use gated to phase 2) |
| `ListView` (table) / `CardView` | their existing `.content.html` partials (full-page include refactor only) |

Usage:

```python
class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_modal = True
    cv_modal_size = "modal-lg"    # optional
```

## 3. HTTP Protocol

| Request | Condition | Response |
|---|---|---|
| GET, no `X-CV-Modal` | always | full page (unchanged behavior) — deep links, no-JS, plain theme |
| GET, `X-CV-Modal: true` | `cv_modal = True` | 200, modal partial (`crud_views/modal/content.html`) |
| GET, `X-CV-Modal: true` | `cv_modal = False` | full page (header ignored; view not modal-enabled) |
| POST, `X-CV-Modal: true`, valid | | 204, header `X-CV-Redirect: <get_success_url()>`, empty body |
| POST, `X-CV-Modal: true`, invalid form or delete protection | | 422, re-rendered modal partial |
| POST, no `X-CV-Modal` | | unchanged (302 redirect / 200 re-render) |

All responses from modal-capable views (`cv_modal = True`) carry `Vary: X-CV-Modal`
(`django.utils.cache.patch_vary_headers`).

## 4. Server-Side Changes

### 4.1 `crud_views/lib/views/modal.py` (new)

```python
def cv_is_modal_request(request) -> bool:
    return request.headers.get("X-CV-Modal") == "true"
```

### 4.2 `crud_views/lib/view/base.py` (`CrudView`)

- New class attributes (Section 2).
- `get_template_names()`: return `["crud_views/modal/content.html"]` when
  `self.cv_modal and cv_is_modal_request(self.request)`, else `super()`.
- `dispatch()`: call super, then `patch_vary_headers(response, ["X-CV-Modal"])` when `self.cv_modal`.
- `cv_get_dict()` (line ~206): add `cv_modal=cls.cv_modal, cv_modal_size=cls.cv_modal_size` — this is the
  only plumbing needed for both button templates to see the target view's modal flags.

### 4.3 `crud_views/lib/views/mixins.py` (`CrudViewProcessFormMixin`)

- `cv_form_valid_redirect` (line 81): when modal request → `HttpResponse(status=204)` with
  `X-CV-Redirect: self.get_success_url()`. Messages are already queued by `cv_form_valid_hook`
  (runs before, line 110), so they render after the client-side navigation.
- `cv_form_invalid` (line 69): render as today; set `response.status_code = 422` when modal request.

### 4.4 `crud_views/lib/views/delete.py` (`DeleteView`)

- The delete-protection branch in `post()` (line ~174, `return self.render_to_response(context)`) sets
  status 422 when modal request — same treatment as `cv_form_invalid`.

### 4.5 System checks (`crud_views/lib/check.py` / view `checks()` chains)

- `cv_modal_size` must be one of `""`, `"modal-sm"`, `"modal-lg"`, `"modal-xl"` → **Error**.
- `cv_modal = True` on a view class that is not a subclass of `DeleteView`, `DetailView`, or
  `CustomFormView` → **Error** ("modal rendering is not yet supported for this view type") — the phase-2
  gate. Check IDs: next free numbers in the E2xx range (verify against existing E200/E201/E240–E245 at
  implementation time).

## 5. Template Changes

### 5.1 New: `crud_views/templates/crud_views/modal/content.html`

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

No `modal-footer`: crispy renders the submit button inside the body form; detail modals need only the
header close button. CBV `render_to_response` puts `view` in context automatically, so the chrome tags
work unchanged.

### 5.2 `tags/cv_config.html` — shell appended

```django
<div id="cv-config" … hidden></div>
<div class="modal fade" id="cv-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" id="cv-modal-dialog">
        <div class="modal-content" id="cv-modal-content"></div>
    </div>
</div>
```

### 5.3 Full-page templates — single-source content includes

Every `view_*.html` that includes a `.content.html` partial switches the hardcoded name to
`{% include view.cv_content_template %}` (delete, detail, custom_form, create, update, list_table, card;
both in `crud_views` and — attribute is theme-independent — `crud_views_plain`).

### 5.4 Content partials — explicit form action

`view_delete.content.html` and `view_custom_form.content.html` (and create/update partials, for
phase-2 readiness):

```django
<form class="cv-form" method="post" action="{{ request.path }}" novalidate>
```

No-op in full-page mode; ensures a form injected into a modal posts to the modal view's URL, not the
hosting page's.

### 5.5 Button templates — modal branch (bootstrap5 theme only)

`tags/list_action.html`: new first branch when `cv_modal` — keep `href="{{ cv_url }}"` (middle-click /
no-JS fallback), add `data-cv-modal="true"` and `data-cv-modal-size="{{ cv_modal_size }}"`.
`tags/context_action.html`: same attributes added when `cv_modal`.
`crud_views_plain` button templates: untouched (graceful degradation by omission).

Note: a modal-enabled view with `cv_list_action_method == "post"` cannot occur in phase 1 (only
`ActionView` uses POST list actions, and it is outside the phase-1 gate) — the modal branch takes
precedence over the GET branch only.

## 6. Client: `crud_views/static/crud_views/js/modal.js` (new)

Registered in `CrudViewsSettings.javascript()` (`settings.py:117`) as `"modal": self.get_js("modal.js")`
→ loaded by `{% cv_js %}`. Style: jQuery document-level delegation, explicit errors (matching
`viewset.js`).

Behavior:

1. **Open** — delegated click on `[data-cv-modal='true']`: prevent default, `fetch(href, {headers:
   {"X-CV-Modal": "true"}})`; on 200: set `#cv-modal-dialog` class to `modal-dialog` + size, inject body
   into `#cv-modal-content`, dispatch `cv:modal:loaded`, `bootstrap.Modal.getOrCreateInstance(#cv-modal).show()`.
2. **Submit** — delegated submit on `#cv-modal-content form`: prevent default, `fetch(form.getAttribute("action"),
   {method: "POST", body: new FormData(form), headers: {"X-CV-Modal": "true"}})`:
   - response has `X-CV-Redirect` → `window.location.assign(url)` (modal disappears with navigation);
   - status 422 → inject re-rendered partial into `#cv-modal-content`, dispatch `cv:modal:loaded`;
   - anything else → **fallback**: `window.location.assign(<opened GET url>)` — never strand the user in
     a broken modal. The opened URL is remembered on the shell (e.g. `data-cv-url`) at open time.
3. **Open failure** — non-200 GET or network error: fall back to `window.location.assign(href)`.
4. **Guards** — throw explicit errors if `#cv-modal` is missing (shell not rendered — `{% cv_config %}`
   absent) or `window.bootstrap` is undefined (host did not load Bootstrap JS), mirroring the
   `cvGetConfig()` error style.
5. **`cv:modal:loaded`** — CustomEvent dispatched on `#cv-modal` after every injection; the documented
   phase-2 hook for re-initializing formset/toggle/widget JS inside modal content. CSRF needs no special
   handling: the partial's `{% csrf_token %}` field travels in `FormData`.

## 7. Example App, Docs

- `examples/bootstrap5`: set `cv_modal = True` on one delete view (e.g. Author), one detail view, and one
  custom-form view — the manual verification surface for `modal.js`.
- New mkdocs page (`docs/`) documenting: `cv_modal` / `cv_modal_size`, phase-1 view types, full-page
  fallback (deep links / no-JS), plain-theme behavior, the `cv:modal:loaded` event, and the requirement
  that the host loads Bootstrap 5 JS.

## 8. Tests (pytest, `tests/test1/`)

New `test_modal.py` (fixtures follow existing `cv_<model>` / `client_user_<model>_<perm>` conventions):

1. GET without header → full page (contains `cv_extends` chrome), 200.
2. GET with `X-CV-Modal: true` on modal-enabled delete view → 200, modal partial (contains
   `modal-header`, no `<html>`/chrome), `Vary: X-CV-Modal`.
3. GET with header on `cv_modal = False` view → full page (header ignored).
4. POST delete with header, deletable object → 204, `X-CV-Redirect` == list URL, object deleted, success
   message queued.
5. POST delete with header, protected object (delete-protection errors) → 422, partial contains errors,
   object still exists.
6. POST custom form with header, invalid → 422 partial with form errors; valid → 204 + redirect header.
7. Detail view with header → 200 partial rendering `django-object-detail` groups.
8. Non-modal POST flows unchanged (302 on success, 200 re-render on invalid) — regression guard.
9. List page HTML: modal-enabled target → buttons carry `data-cv-modal="true"` (+ size); disabled →
   attributes absent.
10. System checks: invalid `cv_modal_size` → error; `cv_modal = True` on a `CreateView` subclass → error.

## 9. Acceptance Criteria

- Full test suite green across the nox matrix (`task test`); ruff clean (`task check`, `task format`).
- All new/changed behavior covered by the tests in Section 8.
- Bootstrap5 example: delete/detail/custom-form modals open, validate, and redirect correctly by manual
  check; plain example unchanged.
- No behavior change for any view with `cv_modal = False` (the default) — the entire feature is opt-in.
