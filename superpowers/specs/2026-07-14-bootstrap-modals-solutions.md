# Modal Views for django-crud-views — Solution Comparison (Bootstrap 5)

**Date:** 2026-07-14
**Status:** Solution comparison — input for the implementation brainstorming session. Not an implementation spec.
**Source prompt:** `superpowers/prompts/2026-07-14-bootstrap-modals.md`

## 1. Goal and Scope

Add opt-in modal rendering to CRUD views: a view class declares `cv_modal = True` and its action buttons
(list-row buttons, context-action buttons) open the view in a Bootstrap 5 modal instead of navigating to a
full page.

Decisions already made in the brainstorming dialogue:

- **Success flow:** after a successful action inside a modal, the browser performs a **full-page redirect**
  to the view's `cv_success_key` target. `get_success_url()` semantics and Django messages stay untouched.
- **Phasing:** phase 1 covers **delete**, **custom form** (`CustomFormView`), and **detail**. The chosen
  architecture must not preclude **create/update** (phase 2), but phase 1 does not implement them.
- **Theme:** Bootstrap 5 only (the `crud_views` core app). `crud_views_plain` ignores `cv_modal`
  gracefully — buttons stay plain links, views render full pages.
- **Solutions compared:** a no-new-dependency vanilla solution and an htmx solution. Both share the same
  server-side foundation (Section 3); they differ in client transport (Sections 4 and 5).

Non-goals for phase 1: stacked/nested modals, in-place list refresh after success, modals for `ActionView`
POST-only actions (up/down already post directly without a confirmation page), polymorphic two-step create
inside a modal.

## 2. Grounding: How the Relevant Machinery Works Today

Everything below is verifiable on `main` (v0.10.2).

### 2.1 Page composition — the content/chrome split already exists

Every view template extends the host project's wrapper (`CRUD_VIEWS_EXTENDS`, e.g.
`examples/bootstrap5/app/templates/app/crud_views.html`) and puts its actual content into a separate
partial:

```django
{# src/crud_views/templates/crud_views/view_delete.html #}
{% extends cv_extends %}
{% block cv_content %}
    {% include "crud_views/view_delete.content.html" %}
{% endblock cv_content %}
```

The wrapper renders the card chrome — `{% cv_header_icon %}`, `{% cv_header %}`,
`{% cv_context_actions object %}`, `{% cv_paragraph %}` — around the `cv_content` block. The
`view_*.content.html` partials (`view_delete.content.html`, `view_custom_form.content.html`,
`view_detail.content.html`) contain exactly what a modal body needs and nothing more. **This split is the
seam both solutions build on.**

The delete content partial already contains the complete confirmation UI (delete-protection alert,
related-objects tree, form):

```django
{# src/crud_views/templates/crud_views/view_delete.content.html (abridged) #}
{% if delete_protection_errors %}
    <div class="alert alert-danger">…</div>
{% else %}
    {% if related_summary or protected_objects %}
        {% include "crud_views/snippets/delete/related_objects.html" %}
    {% endif %}
    <form class="cv-form" method="post" novalidate>
        {% csrf_token %}
        {{ form.non_form_errors }}
        {% cv_render_form %}
    </form>
{% endif %}
```

Note that the `<form>` element lives in the content partial (crispy renders fields and submit button
inside it via `{% cv_render_form %}` → `tags/form.html`), not in the chrome. A modal body therefore
carries its own working form.

### 2.2 Buttons know the target view class

`{% cv_list_action %}` and `{% cv_context_action %}` build their context via
`CrudView.cv_get_context(key, obj, user, request)` (`src/crud_views/lib/view/base.py:346`), which resolves
the **target** view class from the ViewSet registry (`cv_get_cls`, `base.py:236`) and merges in
`cv_get_dict()` class attributes (`base.py:206`: `cv_key`, `cv_list_action_method`, `cv_icon_action`, …).
Adding `cv_modal` / `cv_modal_size` to `cv_get_dict()` makes them available to both button templates with
no new plumbing. The button templates then only need a conditional branch:

```django
{# src/crud_views/templates/crud_views/tags/list_action.html — today #}
<a {% if cv_list_action_method == "get" %} href="{{ cv_url }}"
   {% elif cv_list_action_method == "post" %} href="#" data-cv-action="submit-form"
        data-cv-target="cv_form_{{ cv_oid }}" {% endif %} … >
```

### 2.3 POST lifecycle — one override point for the redirect

`CrudViewProcessFormMixin.post()` (`src/crud_views/lib/views/mixins.py:24`) drives delete and custom-form
POSTs: `cv_form_is_valid` → `cv_form_valid` → `cv_form_valid_hook` (this is where `MessageMixin` queues
the success message, `mixins.py:110`) → `cv_form_valid_redirect` (`mixins.py:81`, returns
`HttpResponseRedirect(self.get_success_url())`). Invalid forms re-render via `cv_form_invalid` →
`render_to_response(context)`. `DeleteView.post()` (`src/crud_views/lib/views/delete.py:162`) follows the
same shape and additionally re-renders with `delete_protection_errors` attached to the form.

**`cv_form_valid_redirect` is the single hook both solutions override** to answer a modal POST with a
"navigate the whole page" instruction instead of a 302 (a 302 is useless to `fetch`/htmx: they follow it
transparently and receive the target page's HTML).

### 2.4 JS and asset infrastructure

- Assets are registered centrally in `CrudViewsSettings.javascript()` / `.css` (`settings.py:117`) and
  loaded by `{% cv_js %}` / `{% cv_css %}`. A new `modal.js` slots into this dict.
- `{% cv_config %}` renders a hidden `#cv-config` element with the CSRF token and request path;
  `viewset.js` reads it via `cvGetConfig()`.
- `viewset.js` binds with **document-level delegation** (`$(document).on("click", "[data-cv-action=…]")`)
  — handlers like the hidden-form submit keep working for DOM injected later (i.e. inside a modal).
- `formset.js` does the opposite: it instantiates `CrudViewsFormset` **once at DOM-ready**
  (`$(function () { if (document.querySelector(".cv-formset-content")) new CrudViewsFormset(); })`) and
  binds directly to the elements present at that moment, selecting globally (`form.cv-form`). Injected
  modal content would not be wired up. This is the central phase-2 risk (Section 7).
- Bootstrap's JS is **host-provided** (`{% bootstrap_javascript %}` in the example `base.html`); the
  package can rely on `window.bootstrap.Modal` being present in the Bootstrap 5 theme, but must fail with
  a clear error if it is not (same pattern as `cvGetConfig()`'s missing-element error).
- jQuery is already a documented requirement of the existing JS.

## 3. Shared Foundation (identical in both solutions)

The server-side design is deliberately the same for both solutions — the real decision is the client
transport. This also means a later migration from Solution A to Solution B (or vice versa) touches almost
no Python.

### 3.1 API surface

```python
class CrudView:
    …
    cv_modal: bool = False        # opt-in: action buttons open this view in a modal
    cv_modal_size: str = ""       # "" | "modal-sm" | "modal-lg" | "modal-xl" (Bootstrap size class)
```

Usage:

```python
class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_modal = True
```

- `cv_get_dict()` (`base.py:206`) additionally returns `cv_modal` and `cv_modal_size`.
- New system checks (in the `checks()` chain, following the existing `CheckExpression` pattern from
  `views/detail.py`): `cv_modal_size` must be one of the allowed values; warning if `cv_modal = True` on a
  view type outside phase-1 support (create/update/list) until phase 2 lands.

### 3.2 Request detection: same URL, content negotiation

A modal request is a normal GET/POST to the **existing** view URL carrying a marker; the view answers with
a partial instead of a full page.

- **Marker:** the request header `X-CV-Modal: true` (Solution A) or `HX-Request` (Solution B). A helper on
  the view normalizes this:

```python
# crud_views/lib/views/modal.py (new)
def cv_is_modal_request(request) -> bool:
    return request.headers.get("X-CV-Modal") == "true"
```

Both solutions send this same header: Solution A sets it explicitly on `fetch`, Solution B declares it
once via `hx-headers` on the buttons/shell (Section 5.1). Detection stays transport-agnostic.

- **Why a header, not `?cv-modal=1`:** a query parameter leaks into pagination/filter links generated from
  the current URL, bookmarks deep-link to a chrome-less fragment, and it survives copy/paste. A header
  never appears in URLs. Cost: responses on the same URL differ by header, so modal-capable views should
  send `Vary: X-CV-Modal` (Django's `patch_vary_headers`) for cache correctness.
- **Fallback for free:** a plain GET without the marker (deep link, JS disabled, `crud_views_plain` theme,
  crawler) renders the unchanged full page. `cv_modal` is progressive enhancement, never a hard switch.

### 3.3 Dual rendering via `get_template_names()`

A new mixin, mixed into `CrudView` itself (so guardian/workflow/polymorphic subclasses inherit it):

```python
class CrudViewModalMixin:
    def get_template_names(self):
        if self.cv_modal and cv_is_modal_request(self.request):
            return ["crud_views/modal/content.html"]
        return super().get_template_names()
```

`crud_views/modal/content.html` is one generic wrapper reusing the existing chrome tags and the view's
content partial:

```django
{# src/crud_views/templates/crud_views/modal/content.html #}
{% load crud_views %}
<div class="modal-header">
    <h5 class="modal-title">{% cv_header_icon %} {% cv_header %}</h5>
    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
</div>
<div class="modal-body">
    {% include view.cv_content_template %}
</div>
{# no modal-footer in phase 1: the submit button is rendered by crispy inside the body form,
   and detail modals only need the header close button #}
```

This requires making the content-partial name a class attribute instead of a string hardcoded in the
full-page template:

```python
class DeleteView(…):
    template_name = "crud_views/view_delete.html"
    cv_content_template = "crud_views/view_delete.content.html"   # new
```

and, as a targeted refactor, the full-page templates change their static include to
`{% include view.cv_content_template %}` so the name lives in exactly one place. (Today
`view_delete.html` hardcodes the include; leaving both would invite drift.)

One more targeted change to the content partials: their `<form>` tags currently have no `action`
attribute (they post back to their own page URL, which works full-page). Inside a modal the DOM
`form.action` property resolves to the *hosting document's* URL — the list page — which is wrong. The
partials therefore gain an explicit `action="{{ request.path }}"`:

```django
<form class="cv-form" method="post" action="{{ request.path }}" novalidate>
```

This is a no-op in full-page mode and gives both transports (Section 4/5) the correct POST target when
the form is injected into a modal on a different URL.

### 3.4 Success protocol (full-page redirect, as decided)

Override in the same mixin:

```python
class CrudViewModalMixin:
    def cv_form_valid_redirect(self, context: dict):
        url = self.get_success_url()
        if cv_is_modal_request(self.request):
            response = HttpResponse(status=204)
            response["X-CV-Redirect"] = url          # Solution A reads this…
            response["HX-Redirect"] = url            # …Solution B reads this (harmless to set both)
            return response
        return HttpResponseRedirect(url)
```

The success message is already queued into the session by `MessageMixin.cv_form_valid_hook`
(`mixins.py:110`) *before* `cv_form_valid_redirect` runs, so it renders normally on the page the browser
navigates to. No change to messages.

**Validation errors / delete protection:** `cv_form_invalid` (and `DeleteView.post`'s protection branch)
already call `render_to_response(context)` — with the `get_template_names()` override in place this
automatically re-renders the *modal partial* with errors. The only open sub-decision is the status code
(200 vs 422); see Section 6.2.

### 3.5 The modal shell

One empty shell per page, rendered once in the host base template next to `{% cv_config %}`:

```django
{# host base.html #}
{% cv_config %} {% cv_css %} {% cv_js %} {% cv_modal_shell %}
```

```django
{# src/crud_views/templates/crud_views/modal/shell.html — rendered by the cv_modal_shell tag #}
<div class="modal fade" id="cv-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog" id="cv-modal-dialog">
        <div class="modal-content" id="cv-modal-content"></div>
    </div>
</div>
```

The client puts the fetched partial into `#cv-modal-content` and applies `cv_modal_size` to the dialog.
If a modal button is clicked and the shell is missing, the JS throws the same style of explicit error as
`cvGetConfig()` does today.

### 3.6 Per-view-type behavior in phase 1

| View | GET in modal | POST in modal |
|---|---|---|
| `DeleteView` | confirmation partial: protection alert, related objects, form | delete → 204 + redirect header; protection/validation errors → re-rendered partial |
| `CustomFormView` (object and no-object variants) | form partial | `CrudViewProcessFormMixin` flow, same as delete |
| `DetailView` | read-only `django-object-detail` groups; header close button only | n/a |

Context actions (`cv_context_actions`) are **not** rendered inside the modal in phase 1 — they navigate to
other pages, which contradicts staying in a modal; the header close button suffices.

## 4. Solution A — Vanilla `fetch` + Bootstrap Modal (no new dependency)

### 4.1 Mechanism

A new `modal.js` (registered in `CrudViewsSettings.javascript()`, loaded by `{% cv_js %}`), written in the
same style as `viewset.js`: document-level delegation, `cvGetConfig()` for the CSRF token, explicit errors.

Button template branch:

```django
{# tags/list_action.html — new first branch #}
<a {% if cv_modal %}
    href="{{ cv_url }}"
    data-cv-modal="true"
    data-cv-modal-size="{{ cv_modal_size }}"
{% elif cv_list_action_method == "get" %}
    href="{{ cv_url }}"
{% elif cv_list_action_method == "post" %} … {% endif %} … >
```

(`href` stays populated: middle-click/ctrl-click and no-JS degrade to the full page.)

`modal.js` sketch (~120 lines, on par with the existing files):

```javascript
$(document).on("click", "[data-cv-modal='true']", function (e) {
    e.preventDefault();
    cvModalOpen($(this).attr("href"), $(this).attr("data-cv-modal-size"));
});

function cvModalOpen(url, size) {
    fetch(url, {headers: {"X-CV-Modal": "true"}})
        .then(r => r.text())
        .then(html => {
            const dialog = document.getElementById("cv-modal-dialog");   // throw if missing, like cvGetConfig
            dialog.className = "modal-dialog" + (size ? " " + size : "");
            document.getElementById("cv-modal-content").innerHTML = html;
            bootstrap.Modal.getOrCreateInstance(document.getElementById("cv-modal")).show();
        });
}

// delegated submit for any form inside the shell
$(document).on("submit", "#cv-modal-content form", function (e) {
    e.preventDefault();
    fetch(this.getAttribute("action"), {   // explicit action="{{ request.path }}", see Section 3.3
        method: "POST",
        body: new FormData(this),                 // carries the {% csrf_token %} field
        headers: {"X-CV-Modal": "true"},
    }).then(r => {
        const redirect = r.headers.get("X-CV-Redirect");
        if (redirect) { window.location.assign(redirect); return; }
        return r.text().then(html => {            // validation errors: swap partial in place
            document.getElementById("cv-modal-content").innerHTML = html;
        });
    });
});
```

### 4.2 Pros

- **Zero new dependencies.** The package already ships its own JS on jQuery; this is one more file in an
  established pattern (`settings.javascript()`, `cv_js`, delegation, `cvGetConfig` error style).
- No requirements pushed onto host projects beyond what exists today (Bootstrap 5 JS, jQuery).
- Full control over the protocol; no version coupling to an external library's release cycle.
- The custom header protocol (`X-CV-Modal` / `X-CV-Redirect`) deliberately mirrors htmx's shape
  (`HX-Request` / `HX-Redirect`), keeping a later htmx migration cheap.

### 4.3 Cons

- The package owns transport code that htmx provides for free: response swapping, error paths, request
  headers, redirect handling — all custom, all to maintain.
- **No JS test infrastructure exists in the repo** (confirmed 2026-06-28); `modal.js` correctness is
  covered only indirectly by Python tests asserting partial/headers, or requires new jsdom infrastructure.
- Every future partial-UI feature (in-place list refresh, filter-as-you-type) grows more bespoke JS
  instead of reusing a general mechanism.

## 5. Solution B — htmx

### 5.1 Mechanism

Same server foundation; htmx replaces `modal.js` as transport. The most contained variant puts
`hx-boost`-style attributes on the *shell*, not on every button/form:

Button branch emits htmx attributes:

```django
{# tags/list_action.html — htmx variant #}
<a {% if cv_modal %}
    href="{{ cv_url }}"
    hx-get="{{ cv_url }}"
    hx-target="#cv-modal-content"
    hx-headers='{"X-CV-Modal": "true"}'
    data-cv-modal-size="{{ cv_modal_size }}"
{% elif … %} … {% endif %} … >
```

Forms inside the fetched partial are intercepted by one attribute on the shell — htmx inherits attributes
from ancestors, so the shell declares the target once:

```django
<div class="modal fade" id="cv-modal" hx-target="#cv-modal-content" hx-headers='{"X-CV-Modal": "true"}'>
    …
</div>
```

with `hx-boost="true"` on the shell converting the partial's inner form to an htmx request automatically
(boosted forms use the form's `action` attribute — set explicitly per Section 3.3, so the POST hits the
modal view's URL, not the hosting page).

A *small* glue script is still required — htmx does not know Bootstrap:

```javascript
document.body.addEventListener("htmx:afterSwap", function (e) {
    if (e.detail.target.id === "cv-modal-content") {
        bootstrap.Modal.getOrCreateInstance(document.getElementById("cv-modal")).show();
    }
});
```

Success redirect is htmx-native: the server's `HX-Redirect` header (already set in Section 3.4) makes htmx
perform a full `window.location` navigation. Validation errors: the re-rendered partial swaps into the
open modal automatically (htmx 2.x swaps 200s by default; a 422 needs `htmx.config.responseHandling` or
the `django-htmx` middleware conventions — see Section 6.2).

Server-side detection can optionally use the `django-htmx` middleware (`request.htmx`), but a plain
`request.headers.get("HX-Request")` check keeps it dependency-free on the Python side.

### 5.2 Dependency delivery — the crux

A reusable package imposing a JS framework on host projects has exactly two options:

1. **Vendor it:** ship `htmx.min.js` (~16 kB gzipped) in `static/crud_views/js/` and add it to
   `settings.javascript()`. Hosts get it automatically via `{% cv_js %}`; the package owns the htmx
   version (and its upgrade path, e.g. the 1.x→2.x breaking changes). Risk: a host that *already* uses
   htmx now has two copies/versions on the page.
2. **Require it:** document "if you set `cv_modal = True`, include htmx yourself" and add a system check
   that can only warn (the server cannot see the client's script tags). Risk: silent breakage class that
   `crud_views` checks otherwise eliminate by design.

### 5.3 Pros

- Battle-tested swap/transport semantics; `HX-Redirect`, history, error events all exist and are
  documented ecosystem-wide.
- Materially less custom JS to own (~10-line Bootstrap glue vs ~120-line protocol implementation).
- Establishes a general partial-update idiom the package can reuse later (list refresh after modal
  success, filter panels, formset row loading — today `formset.js` hand-rolls its AJAX row fetch).
- Large Django community mindshare (django-htmx, countless modal-form tutorials with this exact shape).

### 5.4 Cons

- **A reusable library imposes a runtime framework choice on every host project** — the heaviest con.
  Hosts with CSP policies, vendoring rules, or an existing Alpine/Stimulus/React setup must now also
  accommodate htmx for one feature.
- Two client idioms coexist in the package: jQuery-class-based (`formset.js`, `CrudViewsFormset`) and
  htmx attributes. Until formset.js is migrated, the codebase carries both philosophies.
- htmx attributes baked into `crud_views` (Bootstrap 5) templates widen the divergence from
  `crud_views_plain`, which overrides templates by name and would need to strip them.
- Version coupling: htmx 2.x config differences (e.g. swapping on 4xx responses) become the package's
  compatibility problem.

## 6. Cross-Cutting Sub-Decisions (same for both solutions)

### 6.1 Same-URL content negotiation vs separate modal endpoints

| | Same URL + header (proposed) | Separate `…/delete/modal/` endpoints |
|---|---|---|
| URL patterns | unchanged (`ViewSet.urlpatterns` untouched) | every modal view registers a second route; `cv_get_url`/`get_router_name` need a modal variant |
| Permissions | identical view class ⇒ identical `cv_permission` enforcement | duplicated wiring, second place to get it right |
| Deep-link fallback | automatic (no header ⇒ full page) | `/modal/` URL reachable directly, renders a chrome-less fragment |
| Caching | needs `Vary: X-CV-Modal` | clean separation |
| Testing | one URL, assert on header presence | double the URL surface |

**Recommendation:** same URL. The `Vary` header is a one-line cost; the alternative doubles the routing
and permission surface for no functional gain.

### 6.2 Status code for invalid modal forms

- `200` + re-rendered partial: simplest, htmx-default-compatible; but the client cannot distinguish
  "validation failed" from "confirmation page" without inspecting HTML.
- `422` + re-rendered partial: semantically correct, lets Solution A's JS branch cleanly; Solution B needs
  htmx 2.x response-handling config (or django-htmx idioms) to swap 4xx bodies.

Leaning `422` for Solution A, `200` for Solution B (each transport's native idiom). To be settled in the
implementation session.

### 6.3 Extension packages

The mixin lives in `CrudView` core, so `crud_views_guardian` (permission mixins),
`crud_views_workflow` (`WorkflowView` is a form view — a natural modal candidate later), and
`crud_views_polymorphic` inherit modal capability structurally. Only the polymorphic **create-select →
create** chain is explicitly out of scope: it is a two-step navigation, which inside a modal means
swapping modal content across steps — deferred with phase 2.

### 6.4 `crud_views_plain`

`crud_views_plain` overrides templates by name and ships no JS. Its `tags/list_action.html` /
`tags/context_action.html` simply never emit the modal attributes, so `cv_modal = True` degrades to
today's full-page behavior with zero code. No check needed; document the behavior.

## 7. Phase 2 Outlook: Create and Update in Modals

Nothing in Sections 3–5 blocks create/update — `CreateView`/`UpdateView` use the same
`CrudViewProcessFormMixin` POST flow and have `view_create.content.html` / `view_update.content.html`
partials. The known, concrete obstacles:

1. **`formset.js` initialization.** `CrudViewsFormset` is constructed once at DOM-ready and only if
   `.cv-formset-content` exists at that moment; its selectors are page-global (`form.cv-form`). Injected
   modal content is invisible to it. Required refactor: make `CrudViewsFormset` instantiable per container
   root (constructor takes a root element, all `sel()` calls scope to it) and have the modal client
   re-initialize after injection (Solution A: after `innerHTML` assignment; Solution B: on
   `htmx:afterSwap`). This refactor is independent and could ship before phase 2.
2. **Conditional field groups** (unmerged `feat/conditional-field-groups` branch): validation is
   server-authoritative with cosmetic client JS — the same re-init treatment applies to its toggle
   script once merged.
3. **Layout width.** Crispy `Row`/`ColumnN` grids designed for a full card are cramped in a default
   modal; `cv_modal_size = "modal-lg"`/`"modal-xl"` exists for exactly this.
4. **Third-party widgets** (date pickers, select2-style selects) initialized at DOM-ready share the
   re-init problem; out of the package's control but worth documenting.

Phase 1 should therefore: (a) keep the shell/injection API such that "content was injected" has a single
well-defined moment/event to hook re-initialization onto, and (b) not bake "the modal body has no dynamic
JS" into any assumption.

## 8. Comparison and Recommendation

| Criterion | A: vanilla fetch | B: htmx |
|---|---|---|
| New runtime dependency | none | htmx (vendored or host-provided) |
| Custom JS owned by package | ~120 lines protocol + UI | ~10 lines Bootstrap glue |
| Server-side code | identical | identical |
| Validation re-render | hand-rolled swap | native |
| Success redirect | custom `X-CV-Redirect` | native `HX-Redirect` |
| Fit with existing JS style | seamless (`viewset.js` idiom) | second idiom alongside jQuery classes |
| Plain-theme divergence | attributes only in bootstrap5 button templates | htmx attrs additionally in modal/form templates |
| Future partial-UI features | each one bespoke | general mechanism established |
| Testability today | Python-side only (no JS infra) — custom protocol untested on client | Python-side only — but client transport is externally tested |
| Host-project impact | none | CSP/vendoring/version considerations |

**Recommendation: Solution A for phase 1.** The deciding factors are library ethics and consistency: a
reusable Django package should not impose a frontend framework for one opt-in feature, and the package
already owns comparable hand-rolled JS (`formset.js` is far larger than the proposed `modal.js`). The
server protocol is designed header-compatible with htmx, so if phase 2 (formsets in modals, partial list
refresh) tips the cost balance, migrating the transport to htmx later replaces one JS file and one button
template branch — the Python layer stays.

Counter-argument worth recording: if the maintainers already foresee htmx as the package's long-term
interaction layer (it would also clean up `formset.js`'s hand-rolled AJAX), starting with B avoids
building protocol code that is discarded later. This is a strategic direction call, not a technical one.

## 9. Open Questions for the Implementation Session

1. Transport choice: Solution A (recommended) or B — including, if B, vendored vs host-provided htmx.
2. Invalid-form status code: 422 vs 200 (Section 6.2).
3. `cv_modal_shell` placement: required manual tag in the host base template (like `{% cv_config %}`,
   plus documented error when missing) vs auto-appending the shell from the full-page view templates.
4. Should `cv_modal` also be settable per *link context* (e.g. delete opens as modal from the list but as
   a full page from the detail view), or is per-view-class enough for phase 1?
5. Check IDs and severity for the new system checks (`cv_modal_size` values, phase-1 view-type guard).
6. Test strategy: Python tests asserting partial rendering, `Vary`, 204 + redirect headers are
   straightforward; is jsdom-based JS testing worth introducing now (repo currently has none)?
7. Naming: `X-CV-Modal` / `X-CV-Redirect` header names, `crud_views/modal/` template directory,
   `cv_content_template` attribute.
