// src/crud_views/static/crud_views/js/toggle.js
(function () {
    if (globalThis.__cvToggleInit) {
        return;
    }
    globalThis.__cvToggleInit = true;

    // Management-form hidden inputs must stay enabled even when the group is
    // hidden: disabling them drops them from the POST, so a bound re-render
    // (main-form error) would come back with 0 rows and a tampered-management
    // error once the user re-enables the toggle. The server ignores an off
    // formset's data anyway.
    const MGMT_FIELD = /-(TOTAL_FORMS|INITIAL_FORMS|MIN_NUM_FORMS|MAX_NUM_FORMS)$/;
    const bindings = new WeakMap();

    function findCheckboxes(form, name) {
        // Form ownership includes controls using form= and excludes controls
        // reassigned to another form. Names are data, never selector syntax.
        return Array.from(form.elements).filter(function (el) {
            return el.tagName === "INPUT" && el.type === "checkbox" && el.form === form && el.name === name;
        });
    }

    function apply(group, checkbox) {
        const on = checkbox.checked;
        group.style.display = on ? "" : "none";
        group.querySelectorAll("input, select, textarea").forEach(function (el) {
            if (MGMT_FIELD.test(el.name || "")) {
                return;
            }
            el.disabled = !on;
        });
    }

    function initConditional(root = document) {
        const selector = "[cv-data-toggle-group]";
        const groups = new Set(root.querySelectorAll(selector));
        if (root.matches?.(selector)) {
            groups.add(root);
        }
        // A theme may supply just a newly inserted checkbox as the root.
        const form = root.closest?.("form") || root.form;
        if (form) {
            form.querySelectorAll(selector).forEach(group => groups.add(group));
        }
        groups.forEach(function (group) {
            const name = group.getAttribute("cv-data-toggle-field");
            const owner = group.closest("form");
            const matches = owner ? findCheckboxes(owner, name) : [];
            const previous = bindings.get(group);
            const checkbox = matches.length === 1 ? matches[0] : null;
            if (previous && previous.checkbox !== checkbox) {
                previous.checkbox.removeEventListener("change", previous.onChange);
                bindings.delete(group);
            }
            if (!checkbox) {
                if (matches.length > 1) {
                    console.warn("crud_views: ambiguous conditional toggle", name);
                }
                return;
            }
            apply(group, checkbox);
            if (!bindings.has(group)) {
                const onChange = function () { apply(group, checkbox); };
                bindings.set(group, { checkbox, onChange });
                checkbox.addEventListener("change", onChange);
            }
        });
    }

    globalThis.cv = globalThis.cv || {};
    globalThis.cv.initConditional = initConditional;

    document.addEventListener("DOMContentLoaded", function () {
        initConditional(document);
    });

    // Modal content is injected via innerHTML after DOMContentLoaded; modal.js
    // dispatches this event exactly so scripts can re-initialize inside it.
    document.addEventListener("cv:modal:loaded", function (event) {
        initConditional(event.target);
    });

    // Same for formset rows added by formset.js after page load.
    document.addEventListener("cv:formset:row-added", function (event) {
        initConditional(event.target);
    });
})();
