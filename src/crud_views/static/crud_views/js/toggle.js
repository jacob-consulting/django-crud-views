// src/crud_views/static/crud_views/js/toggle.js
(function () {
    if (window.__cvToggleInit) {
        return;
    }
    window.__cvToggleInit = true;

    function findCheckbox(scope, name) {
        // Match the toggle checkbox within the nearest form/row scope.
        return scope.querySelector(
            'input[type="checkbox"][name="' + name + '"], input[type="checkbox"][name$="-' + name + '"]'
        );
    }

    function apply(group, checkbox) {
        var on = checkbox.checked;
        group.style.display = on ? "" : "none";
        group.querySelectorAll("input, select, textarea").forEach(function (el) {
            el.disabled = !on;
        });
    }

    function wireGroups(root) {
        root.querySelectorAll("[cv-data-toggle-group]").forEach(function (group) {
            var name = group.getAttribute("cv-data-toggle-field");
            var scope = group.closest("form") || document;
            var checkbox = findCheckbox(scope, name);
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
})();
