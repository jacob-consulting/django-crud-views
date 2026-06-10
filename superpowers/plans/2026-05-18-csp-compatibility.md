# CSP Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all Content Security Policy impediments from django-crud-views templates and Python code so downstream projects can enforce strict CSP without `unsafe-inline`.

**Architecture:** Replace inline `<script>` blocks with `data-*` attributes and externalized JS. Replace inline event handlers (`onclick`) with event delegation in `viewset.js`. Move inline `<style>` to a static CSS file. Replace inline `style=` attributes with CSS classes.

**Tech Stack:** Django templates, vanilla JS (jQuery already a dependency), crispy-forms layout objects.

**Spec:** `superpowers/specs/2026-05-18-csp-compatibility-design.md`

---

### Task 1: Create feature branch

**Files:** None

- [ ] **Step 1: Create and switch to feature branch**

```bash
git checkout -b feature/csp-compatibility
```

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `feature/csp-compatibility`

---

### Task 2: Replace `const.js.html` inline script with `data-*` config element (A1)

**Files:**
- Create: `crud_views/templates/crud_views/tags/cv_config.html`
- Delete: `crud_views/templates/crud_views/tags/const.js.html`
- Modify: `crud_views/templatetags/crud_views.py:42-48`
- Modify: `crud_views/static/crud_views/js/viewset.js`
- Modify: `crud_views/static/crud_views/js/list.filter.js`
- Modify: `tests/test1/app/templates/app/base.html:30`
- Modify: `examples/bootstrap5/app/templates/app/base.html:30`
- Modify: `examples/plain/app/templates/app/base.html:17`

- [ ] **Step 1: Create the new `cv_config.html` template**

Create `crud_views/templates/crud_views/tags/cv_config.html`:

```html
<div id="cv-config"
     data-request-path="{{ request_path }}"
     data-query-string="{{ request_query_string }}"
     hidden></div>
```

- [ ] **Step 2: Update the template tag in `crud_views.py`**

Replace the `cv_const_js` tag (lines 42-48) to point at the new template and add a `cv_config` alias:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/cv_config.html", takes_context=True)
def cv_const_js(context):
    request = context["request"]
    return {
        "request_path": request.path,
        "request_query_string": request.META.get("QUERY_STRING", ""),
    }


@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/cv_config.html", takes_context=True)
def cv_config(context):
    request = context["request"]
    return {
        "request_path": request.path,
        "request_query_string": request.META.get("QUERY_STRING", ""),
    }
```

- [ ] **Step 3: Add `cvGetConfig()` utility to `viewset.js`**

Replace the entire content of `crud_views/static/crud_views/js/viewset.js` with:

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

function cv_list_action_form_submit(cv_oid) {
    let form_name = 'cv_form_' + cv_oid,
        form = $('#' + form_name);
    form.submit();
    return false;
}
```

- [ ] **Step 4: Update `list.filter.js` to use `cvGetConfig()`**

Replace `crud_views/static/crud_views/js/list.filter.js` — every reference to the `ViewSet` global and `csrftoken` global is replaced:

```javascript
$(document).ready(function () {

    var config = cvGetConfig();

    // add event listener to the filter button
    $('#filter-button').click(function () {
        let expanded = $('#filter-button').attr('aria-expanded');
        $('#filter-form')[0].elements["filter_expanded"].value = expanded;
        setFilterExpanded(expanded);
    });

    // filter reset button: reset filter but keep sort
    $('#filter-button-reset').click(function () {
        let url = config.request.path,
            query_string = config.request.query_string,
            params = new URLSearchParams(query_string),
            reset_param = "reset_filter=true";
        if (params.has("sort")) {
            window.location.href = url + "?sort=" + params.get("sort") + "&" + reset_param;
        } else {
            window.location.href = url + "?" + reset_param;
        }
    });

    $("#cv-filter-toggle").click(function (event) {

        // toggle icon
        $(this).find('i').toggleClass(' fa-filter fa-filter-circle-xmark');

        // get vars
        let collapse = $('#filter-collapse'),
            visible = collapse.is(":visible"),
            form = $('#filter-form'),
            csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value,
            data = {
                filter_expanded: !visible,
            };

        console.log('visible', visible);

        $.post({
                url: config.request.path,
                headers: {"X-CSRFToken": csrftoken},
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify(data),
            },
            function (data, status) {
                console.log("Data: " + data + "\nStatus: " + status);
            }
        );

        // console.log('cv_filter_toggle', isVisible, collapse, form);
        collapse.collapse("toggle");
        event.preventDefault();
    });
});
```

- [ ] **Step 5: Update base templates to use `{% cv_config %}` instead of `{% cv_const_js %}`**

In `tests/test1/app/templates/app/base.html`, change line 30:

```
    {% cv_config %}
```

In `examples/bootstrap5/app/templates/app/base.html`, change line 30:

```
    {% cv_config %}
```

In `examples/plain/app/templates/app/base.html`, change line 17:

```
    {% cv_config %}
```

- [ ] **Step 6: Delete the old template**

```bash
rm crud_views/templates/crud_views/tags/const.js.html
```

- [ ] **Step 7: Run tests**

```bash
cd tests && pytest -x -q
```

Expected: All tests pass.

- [ ] **Step 8: Commit**

```bash
git add crud_views/templates/crud_views/tags/cv_config.html crud_views/templatetags/crud_views.py crud_views/static/crud_views/js/viewset.js crud_views/static/crud_views/js/list.filter.js tests/test1/app/templates/app/base.html examples/bootstrap5/app/templates/app/base.html examples/plain/app/templates/app/base.html
git rm crud_views/templates/crud_views/tags/const.js.html
git commit -m "refactor: replace inline const.js script with data-* config element (CSP A1)"
```

---

### Task 3: Remove `csrftoken.html` inline script (A2)

**Files:**
- Delete: `crud_views/templates/crud_views/shared/csrftoken.html`
- Modify: `crud_views/templatetags/crud_views.py:25-27`
- Modify: `examples/bootstrap5/app/templates/app/crud_views.html:7`

The CSRF token read was moved inline into `list.filter.js` in Task 2. The `cv_csrf_token` template tag and its template can now be removed.

- [ ] **Step 1: Remove the `cv_csrf_token` usage from the bootstrap5 example**

In `examples/bootstrap5/app/templates/app/crud_views.html`, delete line 7 (`{% cv_csrf_token %}`).

- [ ] **Step 2: Remove the template tag registration from `crud_views.py`**

Remove lines 25-27 from `crud_views/templatetags/crud_views.py`:

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/shared/csrftoken.html", takes_context=True)
def cv_csrf_token(context):
    return {}
```

- [ ] **Step 3: Delete the template file**

```bash
rm crud_views/templates/crud_views/shared/csrftoken.html
```

- [ ] **Step 4: Run tests**

```bash
cd tests && pytest -x -q
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git rm crud_views/templates/crud_views/shared/csrftoken.html
git add crud_views/templatetags/crud_views.py examples/bootstrap5/app/templates/app/crud_views.html
git commit -m "refactor: remove inline csrftoken script, read CSRF from DOM at point of use (CSP A2)"
```

---

### Task 4: Externalize formset CSS and init script (A3 + C1)

**Files:**
- Create: `crud_views/static/crud_views/css/formset.css`
- Modify: `crud_views/templates/crud_views/formsets/formsets.html`
- Modify: `crud_views/static/crud_views/js/formset.js`
- Modify: `crud_views/lib/settings.py:104-111`

- [ ] **Step 1: Create `formset.css` with the extracted animations**

Create `crud_views/static/crud_views/css/formset.css`:

```css
@keyframes cv-highlight-delete {
    0% {
        background-color: #e2e0e0;
    }
    50% {
        background-color: #ff6a6a;
    }
    100% {
        background-color: #e2e0e0;
    }
}

@keyframes cv-highlight-order {
    0% {
        background-color: #e2e0e0;
    }
    50% {
        background-color: #8fb7ff;
    }
    100% {
        background-color: #e2e0e0;
    }
}

@keyframes cv-highlight-add {
    0% {
        background-color: #e2e0e0;
    }
    50% {
        background-color: #b3d0b3;
    }
    100% {
        background-color: #e2e0e0;
    }
}

.cv-highlight-delete {
    animation: cv-highlight-delete 0.5s;
}

.cv-highlight-order {
    animation: cv-highlight-order 0.5s;
}

.cv-highlight-add {
    animation: cv-highlight-add 0.5s;
}
```

- [ ] **Step 2: Add self-init to `formset.js`**

Append to the very end of `crud_views/static/crud_views/js/formset.js` (after the closing `}` of `CrudViewsFormset` class, at line 595):

```javascript

$(function () {
    if (document.querySelector(".cv-formset-content")) {
        new CrudViewsFormset();
    }
});
```

- [ ] **Step 3: Replace `formsets.html` — remove inline `<style>` and `<script>` blocks**

Replace the entire content of `crud_views/templates/crud_views/formsets/formsets.html` with:

```html
{% load crud_views_formsets %}
{% load static %}

<link rel="stylesheet" href="{% static 'crud_views/css/formset.css' %}">
{% for x_formset in formsets.x_formsets %}
    {% cv_x_formset x_formset %}
{% endfor %}

{% if formsets.scripts %}
    <script src="{% static "crud_views_fieldsets/js/formset.js" %}"></script>
{% endif %}
```

- [ ] **Step 4: Add `formset.css` to settings CSS dict**

In `crud_views/lib/settings.py`, update the `css` property (lines 104-111) to include the formset CSS:

```python
    @cached_property
    def css(self) -> dict:
        return Box(
            {
                "property": self.get_css("property.css"),
                "table": self.get_css("table.css"),
                "formset": self.get_css("formset.css"),
            }
        )
```

- [ ] **Step 5: Run tests**

```bash
cd tests && pytest -x -q
```

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add crud_views/static/crud_views/css/formset.css crud_views/templates/crud_views/formsets/formsets.html crud_views/static/crud_views/js/formset.js crud_views/lib/settings.py
git commit -m "refactor: externalize formset CSS and init script (CSP A3 + C1)"
```

---

### Task 5: Replace cancel button `onclick` handlers (B1 + B2)

**Files:**
- Modify: `crud_views/templates/crud_views/tags/button_cancel.html`
- Modify: `crud_views_plain/templates/crud_views/tags/button_cancel.html`

- [ ] **Step 1: Replace BS5 cancel button template**

Replace the entire content of `crud_views/templates/crud_views/tags/button_cancel.html` with:

```html
{% load i18n %}

<a href="{{ cv_url }}" class="btn btn-secondary" id="cv-cancel">
    Cancel
</a>
```

- [ ] **Step 2: Replace plain cancel button template**

Replace the entire content of `crud_views_plain/templates/crud_views/tags/button_cancel.html` with:

```html
<a href="{{ cv_url }}">
    {{ cv_action_label }}
</a>
```

- [ ] **Step 3: Run tests**

```bash
cd tests && pytest -x -q
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add crud_views/templates/crud_views/tags/button_cancel.html crud_views_plain/templates/crud_views/tags/button_cancel.html
git commit -m "refactor: replace cancel button onclick with anchor href (CSP B1 + B2)"
```

---

### Task 6: Replace BS5 list action inline handlers (B3 + D1)

**Files:**
- Modify: `crud_views/templates/crud_views/tags/list_action.html`
- Modify: `crud_views/templates/crud_views/tags/list_action_form.html`
- Modify: `crud_views/static/crud_views/js/viewset.js`

- [ ] **Step 1: Update BS5 `list_action.html` — remove `onclick` and `javascript:` href**

Replace the entire content of `crud_views/templates/crud_views/tags/list_action.html` with:

```html
<a {% if cv_list_action_method == "get" %}
    href="{{ cv_url }}"
{% elif cv_list_action_method == "post" %}
    href="#"
    data-cv-action="submit-form"
    data-cv-target="cv_form_{{ cv_oid }}"
{% endif %}
    class="btn btn-outline-{% if cv_access is True %}primary{% else %}secondary{% endif %} btn-xs{% if cv_access is not True %} disabled{% endif %}"
    role="button"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    <i class="{{ cv_icon_action }}"></i>
</a>
```

- [ ] **Step 2: Update BS5 `list_action_form.html` — replace inline `style` with CSS class**

Replace the entire content of `crud_views/templates/crud_views/tags/list_action_form.html` with:

```html
{% if cv_list_action_method == "post" %}
    <form id="cv_form_{{ cv_oid }}" action="{{ cv_url }}" method="post" class="d-none">
        {% csrf_token %}
    </form>
{% endif %}
```

- [ ] **Step 3: Add event delegation to `viewset.js`**

Replace the entire content of `crud_views/static/crud_views/js/viewset.js` with:

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

$(document).ready(function () {
    // list action form submit via data-cv-action="submit-form"
    $(document).on("click", "[data-cv-action='submit-form']", function (e) {
        e.preventDefault();
        var targetId = $(this).attr("data-cv-target");
        $("#" + targetId).submit();
    });

    // cancel button navigation via data-cv-cancel-url
    $(document).on("click", "[data-cv-cancel-url]", function (e) {
        e.preventDefault();
        window.location.href = $(this).attr("data-cv-cancel-url");
    });
});
```

- [ ] **Step 4: Run tests**

```bash
cd tests && pytest -x -q
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add crud_views/templates/crud_views/tags/list_action.html crud_views/templates/crud_views/tags/list_action_form.html crud_views/static/crud_views/js/viewset.js
git commit -m "refactor: replace BS5 list action onclick with event delegation (CSP B3 + D1)"
```

---

### Task 7: Replace plain theme list action inline handlers (B4 + D2)

**Files:**
- Modify: `crud_views_plain/templates/crud_views/tags/list_action.html`

- [ ] **Step 1: Replace plain `list_action.html` — use semantic `<button>` instead of `<a onclick>`**

Replace the entire content of `crud_views_plain/templates/crud_views/tags/list_action.html` with:

```html
{% if cv_url %}
    {% if  cv_list_action_method == "get" %}
        <a href="{{  cv_url }}" title="{{ cv_action_label }}">{{  cv_action_short_label }}</a>
    {% endif %}
    {% if cv_list_action_method == "post" %}
        <form action="{{ cv_url }}" method="post" class="cv-inline">
            {% csrf_token %}
            <button type="submit" title="{{ cv_action_label }}">{{ cv_action_short_label }}</button>
        </form>
    {% endif %}
{% endif %}
```

- [ ] **Step 2: Add `cv-inline` class to plain theme CSS**

Replace the content of `crud_views_plain/static/crud_views/css/foo.css` with:

```css
.cv-inline {
    display: inline;
}
```

- [ ] **Step 3: Rename `foo.css` to `crud_views.css`**

```bash
git mv crud_views_plain/static/crud_views/css/foo.css crud_views_plain/static/crud_views/css/crud_views.css
```

- [ ] **Step 4: Update the plain theme's list_filter template to reference the renamed CSS file**

Check if the plain theme's `list_filter.html` references `foo.css`. It does not — it only references JS. No change needed.

- [ ] **Step 5: Run tests**

```bash
cd tests && pytest -x -q
```

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add crud_views_plain/templates/crud_views/tags/list_action.html crud_views_plain/static/crud_views/css/crud_views.css
git commit -m "refactor: replace plain list action onclick with semantic button (CSP B4 + D2)"
```

---

### Task 8: Replace crispy forms cancel button `onclick` (B5)

**Files:**
- Modify: `crud_views/lib/crispy/form.py:66-78`

- [ ] **Step 1: Update `get_cancel_button_kwargs` to use `data-cv-cancel-url` instead of `onclick`**

In `crud_views/lib/crispy/form.py`, replace the `get_cancel_button_kwargs` method (lines 66-78) with:

```python
    def get_cancel_button_kwargs(self) -> dict:
        request = self.cv_view.request
        # get the object from the form instance or the view context object
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

Note: crispy-forms' `Button` passes `**kwargs` through `flatatt`, so `data_cv_cancel_url` renders as `data-cv-cancel-url="..."` in the HTML. The event delegation handler added to `viewset.js` in Task 6 already handles `[data-cv-cancel-url]` clicks.

- [ ] **Step 2: Run tests**

```bash
cd tests && pytest -x -q
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add crud_views/lib/crispy/form.py
git commit -m "refactor: replace crispy cancel button onclick with data attribute (CSP B5)"
```

---

### Task 9: Final verification

**Files:** None

- [ ] **Step 1: Grep for remaining CSP impediments**

```bash
grep -rn 'onclick\|onchange\|onsubmit\|onload' crud_views/ crud_views_plain/ crud_views_workflow/ crud_views_guardian/ --include="*.html" --include="*.py"
grep -rn 'javascript:' crud_views/ crud_views_plain/ crud_views_workflow/ crud_views_guardian/ --include="*.html"
grep -rn '<script' crud_views/ crud_views_plain/ --include="*.html" | grep -v 'src='
grep -rn '<style' crud_views/ crud_views_plain/ --include="*.html"
grep -rn 'style=' crud_views/ crud_views_plain/ --include="*.html"
```

Expected: No results from any of these commands (all CSP impediments removed).

- [ ] **Step 2: Run full test suite**

```bash
cd tests && pytest -v
```

Expected: All tests pass.

- [ ] **Step 3: Lint check**

```bash
task check
```

Expected: Clean.

- [ ] **Step 4: Format check**

```bash
task format
```

Expected: No changes needed.

- [ ] **Step 5: Commit any formatting fixes if needed**

Only if Step 4 produced changes:

```bash
git add -u
git commit -m "style: format"
```
