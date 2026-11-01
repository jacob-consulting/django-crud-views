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
    const forms = new WeakMap();
    const baselines = new WeakMap();
    const GROUP = "[cv-data-toggle-group]";
    const CONTROLS = "input, select, textarea, button";

    function findCheckboxes(form, name) {
        // Form ownership includes controls using form= and excludes controls
        // reassigned to another form. Names are data, never selector syntax.
        return Array.from(form.elements).filter(function (el) {
            return el.tagName === "INPUT" && el.type === "checkbox" && el.form === form && el.name === name;
        });
    }

    function rememberExternal(records) {
        records.forEach(function ({ target }) {
            if (baselines.has(target)) baselines.set(target, target.hasAttribute("disabled"));
        });
    }

    function observe(state) {
        state.observer.observe(state.form, { subtree: true, attributes: true,
            attributeFilter: ["disabled"], attributeOldValue: true });
    }

    function sync(state) {
        // A same-value external `disabled = true` still creates a record. Drain
        // it before disconnecting, so our temporary writes never become baseline.
        rememberExternal(state.observer.takeRecords());
        state.observer.disconnect();
        try {
            state.groups.forEach(function (group) {
                const binding = bindings.get(group);
                if (binding) group.style.display = binding.checkbox.checked ? "" : "none";
                group.querySelectorAll(CONTROLS).forEach(function (el) {
                    if (!baselines.has(el)) baselines.set(el, el.disabled);
                    state.controls.add(el);
                });
            });
            state.controls.forEach(function (el) {
                let inactive = false;
                if (!MGMT_FIELD.test(el.name || "")) {
                    for (let group = el.parentElement; group && group !== state.form; group = group.parentElement) {
                        const binding = bindings.get(group);
                        if (binding && !binding.checkbox.checked) inactive = true;
                    }
                }
                const disabled = baselines.get(el) || inactive;
                if (el.disabled !== disabled) el.disabled = disabled;
            });
        } finally {
            observe(state);
        }
    }

    function initForm(form) {
        let state = forms.get(form);
        if (!state) {
            state = { form, groups: new Set(), controls: new Set() };
            state.observer = new MutationObserver(function (records) {
                rememberExternal(records);
                sync(state);
            });
            forms.set(form, state);
            observe(state);
        }
        rememberExternal(state.observer.takeRecords());
        // Discover the complete form before writing, so nesting order cannot
        // snapshot another group's temporary disabled property as baseline.
        const groups = new Set(form.querySelectorAll(GROUP));
        state.groups.forEach(function (group) {
            if (!groups.has(group)) {
                const previous = bindings.get(group);
                previous?.checkbox.removeEventListener("change", previous.onChange);
                bindings.delete(group);
            }
        });
        state.groups = groups;
        groups.forEach(function (group) {
            const name = group.getAttribute("cv-data-toggle-field");
            const matches = findCheckboxes(form, name);
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
            if (!bindings.has(group)) {
                const onChange = function () { sync(state); };
                bindings.set(group, { checkbox, onChange });
                checkbox.addEventListener("change", onChange);
            }
        });
        sync(state);
    }

    function initConditional(root = document) {
        const owners = new Set();
        if (root.matches?.("form")) owners.add(root);
        const owner = root.closest?.("form") || root.form;
        if (owner) owners.add(owner);
        root.querySelectorAll("form").forEach(form => owners.add(form));
        root.querySelectorAll(GROUP).forEach(group => {
            const form = group.closest("form");
            if (form) owners.add(form);
        });
        owners.forEach(initForm);
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
