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

    function findCheckbox(scope, name) {
        // Match the toggle checkbox within the nearest form/row scope.
        const escaped = globalThis.CSS?.escape ? CSS.escape(name) : name;
        return scope.querySelector(
            'input[type="checkbox"][name="' + escaped + '"], input[type="checkbox"][name$="-' + escaped + '"]'
        );
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

    function wireGroups(root) {
        root.querySelectorAll("[cv-data-toggle-group]").forEach(function (group) {
            if (group.__cvToggleWired) {
                return;
            }
            group.__cvToggleWired = true;
            const name = group.getAttribute("cv-data-toggle-field");
            const scope = group.closest("form") || document;
            const checkbox = findCheckbox(scope, name);
            if (!checkbox) {
                return;
            }
            apply(group, checkbox);
            checkbox.addEventListener("change", function () {
                apply(group, checkbox);
            });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        wireGroups(document);
    });

    // Modal content is injected via innerHTML after DOMContentLoaded; modal.js
    // dispatches this event exactly so scripts can re-initialize inside it.
    document.addEventListener("cv:modal:loaded", function (event) {
        wireGroups(event.target);
    });
})();
