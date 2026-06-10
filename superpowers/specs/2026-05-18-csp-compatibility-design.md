# CSP Compatibility Design

**Date:** 2026-05-18
**Goal:** Remove all Content Security Policy impediments from django-crud-views so downstream projects can enforce strict CSP (`script-src`, `style-src`) without nonces or `unsafe-inline`.

## Context

A strict CSP blocks:
- Inline `<script>` blocks and `javascript:` URIs (`script-src`)
- Inline event handlers like `onclick` (`script-src`)
- Inline `<style>` blocks (`style-src`)
- Inline `style=` attributes (`style-src` when not using `unsafe-inline`)

django-crud-views currently uses all four patterns. This spec covers removing each impediment by externalizing code into static files and using `data-*` attributes for data binding.

## Impediments Inventory

### Category A: Inline `<script>` blocks

| ID | File | Purpose |
|----|------|---------|
| A1 | `crud_views/templates/crud_views/tags/const.js.html` | Injects `ViewSet` global with `request.path` and query string |
| A2 | `crud_views/templates/crud_views/shared/csrftoken.html` | Reads CSRF token into `csrftoken` global |
| A3 | `crud_views/templates/crud_views/formsets/formsets.html` (lines 61-65) | jQuery-ready init: `new CrudViewsFormset()` |

### Category B: Inline event handlers

| ID | File | Handler |
|----|------|---------|
| B1 | `crud_views/templates/crud_views/tags/button_cancel.html` | `onclick="location.href='...';return false;"` |
| B2 | `crud_views_plain/templates/crud_views/tags/button_cancel.html` | Same pattern |
| B3 | `crud_views/templates/crud_views/tags/list_action.html` | `onclick="return cv_list_action_form_submit('...')"` + `href="javascript:{}"` |
| B4 | `crud_views_plain/templates/crud_views/tags/list_action.html` | `onclick="this.closest('form').submit();return false;"` + `href="javascript:{}"` |
| B5 | `crud_views/lib/crispy/form.py` (lines 72-77) | Python-side `onclick` on cancel button via crispy-forms |

### Category C: Inline `<style>` blocks

| ID | File | Purpose |
|----|------|---------|
| C1 | `crud_views/templates/crud_views/formsets/formsets.html` (lines 4-54) | Keyframe animations for formset row highlights |

### Category D: Inline `style=` attributes

| ID | File | Attribute |
|----|------|-----------|
| D1 | `crud_views/templates/crud_views/tags/list_action_form.html` | `style="display:none"` |
| D2 | `crud_views_plain/templates/crud_views/tags/list_action.html` | `style="display:inline"` |

## Design

### A1: Replace `const.js.html` with `data-*` attributes

**Current:** Template tag `{% cv_const_js %}` renders an inline `<script>` that creates a `ViewSet` global object.

**New:** Replace with a hidden DOM element carrying `data-*` attributes:

```html
<!-- new template: tags/cv_config.html -->
<div id="cv-config"
     data-request-path="{{ request_path }}"
     data-query-string="{{ request_query_string }}"
     hidden></div>
```

The template tag `cv_const_js` is renamed to `cv_config` and renders this template instead.

**JS changes:** `list.filter.js` and any code reading `ViewSet.request.path` or `ViewSet.request.query_string` will read from `data-*` attributes:

```javascript
function cvGetConfig() {
    var el = document.getElementById("cv-config");
    return {
        request: {
            path: el.dataset.requestPath,
            query_string: el.dataset.queryString,
        }
    };
}
```

The old `const.js.html` template is deleted. The `cv_const_js` tag remains as a deprecated alias that renders the new `cv_config.html`, or is removed entirely with a migration note in the changelog.

### A2: Remove `csrftoken.html` inline script

**Current:** `{% cv_csrf_token %}` renders an inline script that caches `csrftoken` in a global.

**New:** Remove the template and template tag. `list.filter.js` reads the CSRF token at point of use:

```javascript
document.querySelector("[name=csrfmiddlewaretoken]").value
```

Since the CSRF hidden input is always present in forms where the filter JS operates, this is reliable. The `cv_csrf_token` template tag is deprecated or removed.

### A3: Externalize formset init script

**Current:** `formsets.html` contains an inline `<script>` that runs `new CrudViewsFormset()` on DOM ready.

**New:** Move the init into `formset.js` itself. Add a self-initializing guard at the bottom of `formset.js`:

```javascript
$(function () {
    if (document.querySelector(".cv-formset-content")) {
        new CrudViewsFormset();
    }
});
```

Remove the inline `<script>` block from `formsets.html`, keeping only the external `<script src>` tag.

### B1-B2: Cancel button — remove `onclick`

**Current:** Both BS5 and plain cancel button templates use `onclick="location.href='...';"`.

**New:** Replace with a `data-cv-cancel-url` attribute. The button becomes:

```html
<!-- BS5 -->
<a href="{{ cv_url }}" class="btn btn-secondary" id="cv-submit">Cancel</a>
```

Since the cancel button is just a navigation action, it can simply be an `<a>` tag with an `href` — no JavaScript needed at all. This is the simplest and most semantic solution.

### B3-B4: List action — remove `onclick` and `javascript:` href

**Current (BS5):** Uses `href="javascript:{}"` + `onclick="return cv_list_action_form_submit('{{ cv_oid }}')"` to submit a hidden form.

**Current (plain):** Wraps the link in a `<form>` and uses `onclick="this.closest('form').submit()"`.

**New (BS5):** Replace the `<a>` with a `<button>` inside the hidden form, or use `data-*` attributes:

```html
<!-- BS5 list_action.html -->
<a {% if cv_list_action_method == "get" %}
    href="{{ cv_url }}"
{% elif cv_list_action_method == "post" %}
    href="#"
    data-cv-action="submit-form"
    data-cv-target="cv_form_{{ cv_oid }}"
{% endif %}
    class="btn btn-outline-..."
    role="button"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    <i class="{{ cv_icon_action }}"></i>
</a>
```

**New (plain):**

```html
{% if cv_list_action_method == "post" %}
    <form action="{{ cv_url }}" method="post" class="cv-inline">
        {% csrf_token %}
        <button type="submit" title="{{ cv_action_label }}">{{ cv_action_short_label }}</button>
    </form>
{% endif %}
```

The plain version replaces the `<a onclick="...submit()">` with a proper `<button type="submit">` — no JS needed.

### B5: Crispy forms cancel button — remove Python-side `onclick`

**Current:** `CrispyFormMixin.get_cancel_button_kwargs()` generates an `onclick` string.

**New:** Replace with a regular `<a>` link approach. The cancel button should use crispy-forms' `HTML` layout object to render an anchor tag:

```python
def get_cancel_button_kwargs(self) -> dict:
    request = self.cv_view.request
    obj = getattr(self, "instance", getattr(self.cv_view, "object", None))
    context = self.cv_view.get_cancel_button_context(obj=obj, user=request.user, request=request)
    url = context["cv_url"]
    return {
        "name": "reset",
        "value": context["cv_action_label"],
        "css_class": "btn btn-secondary",
        "data_cv_cancel_url": url,
    }
```

The external `viewset.js` handles `[data-cv-cancel-url]` click events:

```javascript
document.addEventListener("click", function(e) {
    var el = e.target.closest("[data-cv-cancel-url]");
    if (el) {
        e.preventDefault();
        window.location.href = el.dataset.cvCancelUrl;
    }
});
```

### C1: Externalize formset CSS

**Current:** `formsets.html` contains an inline `<style>` block with keyframe animations.

**New:** Move the CSS to a new static file:

```
crud_views/static/crud_views/css/formset.css
```

Include it with a `<link>` tag in `formsets.html`:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'crud_views/css/formset.css' %}">
```

### D1-D2: Replace inline `style=` with CSS classes

**D1 (BS5 `list_action_form.html`):** Replace `style="display:none"` with Bootstrap's `d-none` class:

```html
<form id="cv_form_{{ cv_oid }}" action="{{ cv_url }}" method="post" class="d-none">
```

**D2 (plain `list_action.html`):** Replace `style="display:inline"` with a CSS class `cv-inline` defined in a minimal static CSS file for the plain theme, or use the semantic `<button>` approach from B4 which eliminates the need for inline display styling entirely.

## External JS Architecture

A single external file `viewset.js` handles all delegated event listeners:

1. **Cancel buttons** — `[data-cv-cancel-url]` click handler navigates to URL
2. **List action form submit** — `[data-cv-action="submit-form"]` click handler submits the target form
3. **Config reading** — `cvGetConfig()` utility reads from `#cv-config` data attributes

The existing `cv_list_action_form_submit()` function in `viewset.js` stays but is invoked via event delegation rather than inline `onclick`.

## Migration Notes

- `cv_const_js` template tag: deprecate with a warning pointing to `cv_config`, remove in next major version.
- `cv_csrf_token` template tag: deprecate, remove in next major version.
- Downstream projects using `{% cv_const_js %}` in their base templates need to switch to `{% cv_config %}`.
- Downstream projects relying on the `ViewSet` or `csrftoken` globals in custom JS need to use `cvGetConfig()` or read the CSRF token from the DOM directly.
- The `onclick` kwarg removal from `CrispyFormMixin.get_cancel_button_kwargs()` is a breaking change for anyone overriding that method.

## Testing

- All existing tests must continue to pass (they test server-side behavior, not JS).
- Manual verification in the bootstrap5 and plain examples:
  - Cancel buttons navigate correctly
  - List action POST buttons (delete, workflow transitions) still submit
  - Filter toggle, filter reset work
  - Formset add/delete/reorder work
- CSP verification: add a strict CSP header to the test/example app and confirm no console violations.

## Files Changed

| File | Change |
|------|--------|
| `crud_views/templates/crud_views/tags/const.js.html` | Delete |
| `crud_views/templates/crud_views/tags/cv_config.html` | New — data attributes element |
| `crud_views/templates/crud_views/shared/csrftoken.html` | Delete |
| `crud_views/templates/crud_views/formsets/formsets.html` | Remove inline `<style>` and `<script>` blocks |
| `crud_views/templates/crud_views/tags/button_cancel.html` | Replace button with `<a href>` |
| `crud_views_plain/templates/crud_views/tags/button_cancel.html` | Replace button with `<a href>` |
| `crud_views/templates/crud_views/tags/list_action.html` | Remove `onclick`, add `data-*` attributes |
| `crud_views/templates/crud_views/tags/list_action_form.html` | `style="display:none"` → `class="d-none"` |
| `crud_views_plain/templates/crud_views/tags/list_action.html` | Replace `<a onclick>` with `<button type="submit">` |
| `crud_views/lib/crispy/form.py` | Remove `onclick` from cancel button, add `data-cv-cancel-url` |
| `crud_views/static/crud_views/js/viewset.js` | Add event delegation, `cvGetConfig()`, inline CSRF reading |
| `crud_views/static/crud_views/js/list.filter.js` | Read config from `data-*` attrs instead of `ViewSet` global |
| `crud_views/static/crud_views/js/formset.js` | Add self-init at bottom |
| `crud_views/static/crud_views/css/formset.css` | New — extracted formset animations |
| `crud_views/templatetags/crud_views.py` | Rename/add `cv_config` tag, deprecate `cv_const_js` and `cv_csrf_token` |
