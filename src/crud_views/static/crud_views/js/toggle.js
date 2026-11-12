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
    // An unresolved binding releases its listener, not its last owned state.
    // Absence means this group has never resolved and owns no conditional state.
    const ownedStates = new WeakMap();
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

    function findChoiceControls(form, name) {
        const matches = Array.from(form.elements).filter(el => el.form === form && el.name === name);
        if (matches.length === 1 && matches[0].tagName === "SELECT" && !matches[0].multiple) return matches;
        return matches.every(el => el.tagName === "INPUT" && el.type === "radio") &&
            matches.filter(el => el.checked).length <= 1 ? matches : [];
    }

    function bindingIsOn(binding) {
        if (binding.values === null) return binding.controls[0].checked;
        const selected = binding.controls[0].tagName === "SELECT" ? binding.controls : binding.controls.filter(el => el.checked);
        if (selected.length > 1) return null; // Malformed radio state retains the last resolved ownership.
        return selected.length === 1 && binding.values.includes(selected[0].value);
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

    function usable(el) {
        if (!(el instanceof HTMLElement) || !el.isConnected || !el.getClientRects().length) return false;
        for (let node = el; node; node = node.parentElement) {
            if (node.hidden || node.hasAttribute("inert") || node.inert ||
                node.getAttribute("aria-hidden") === "true" || node.getAttribute("aria-disabled") === "true" ||
                node.matches(":disabled")) return false;
            const style = getComputedStyle(node);
            if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse") return false;
        }
        return true;
    }

    function focus(el, temporary = false) {
        if (!usable(el)) return false;
        const added = temporary && !el.hasAttribute("tabindex");
        const clean = function () {
            if (added && el.getAttribute("tabindex") === "-1") el.removeAttribute("tabindex");
            el.removeEventListener("blur", clean);
        };
        if (added) el.setAttribute("tabindex", "-1");
        el.focus();
        if (document.activeElement !== el) { clean(); return false; }
        if (added) el.addEventListener("blur", clean, { once: true });
        return true;
    }

    function recoverFocus(state, hidden) {
        for (const group of hidden) {
            for (let node = group; node && node !== state.form; node = node.parentElement) {
                const binding = bindings.get(node);
                if (binding) {
                    const candidates = binding.controls.filter(control => control.checked)
                        .concat(binding.controls.filter(control => !control.checked));
                    if (candidates.some(control => control.form === state.form && focus(control))) return;
                }
            }
        }
        focus(state.form, true);
    }

    function sync(state) {
        // A same-value external `disabled = true` still creates a record. Drain
        // it before disconnecting, so our temporary writes never become baseline.
        rememberExternal(state.observer.takeRecords());
        state.observer.disconnect();
        const active = document.activeElement;
        const hidden = [];
        try {
            state.groups.forEach(function (group) {
                const binding = bindings.get(group);
                if (binding) {
                    const enabled = bindingIsOn(binding);
                    if (enabled !== null) ownedStates.set(group, enabled);
                }
                if (ownedStates.has(group)) {
                    const enabled = ownedStates.get(group);
                    if (!enabled && group.style.display !== "none" && group.contains(active)) hidden.push(group);
                    group.style.display = enabled ? "" : "none";
                }
                group.querySelectorAll(CONTROLS).forEach(function (el) {
                    if (!baselines.has(el)) baselines.set(el, el.disabled);
                    state.controls.add(el);
                });
            });
            state.controls.forEach(function (el) {
                let inactive = false;
                if (!MGMT_FIELD.test(el.name || "")) {
                    for (let group = el.parentElement; group && group !== state.form; group = group.parentElement) {
                        if (ownedStates.get(group) === false) inactive = true;
                    }
                }
                const disabled = baselines.get(el) || inactive;
                if (el.disabled !== disabled) el.disabled = disabled;
            });
        } finally {
            observe(state);
        }
        if (hidden.length) recoverFocus(state, hidden.reverse());
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
            state.onReset = function (event) {
                // Native defaults run after event dispatch. A task also observes
                // preventDefault() by listeners later in the propagation path.
                setTimeout(function () {
                    if (!event.defaultPrevented && forms.get(form) === state) initForm(form);
                }, 0);
            };
            form.addEventListener("reset", state.onReset);
            observe(state);
        }
        rememberExternal(state.observer.takeRecords());
        // Discover the complete form before writing, so nesting order cannot
        // snapshot another group's temporary disabled property as baseline.
        const groups = new Set(form.querySelectorAll(GROUP));
        state.groups.forEach(function (group) {
            if (!groups.has(group)) {
                const previous = bindings.get(group);
                previous?.controls.forEach(control => control.removeEventListener("change", previous.onChange));
                bindings.delete(group);
                ownedStates.delete(group);
            }
        });
        state.groups = groups;
        groups.forEach(function (group) {
            const name = group.getAttribute("cv-data-toggle-field");
            const metadata = group.getAttribute("cv-data-toggle-values");
            let values = null;
            let valid = true;
            if (metadata !== null) {
                try { values = JSON.parse(metadata); } catch (_) { valid = false; }
                valid = valid && Array.isArray(values) && values.length > 0 &&
                    values.every(value => typeof value === "string" && value !== "") && new Set(values).size === values.length;
            }
            const matches = !valid ? [] : metadata === null ? findCheckboxes(form, name) : findChoiceControls(form, name);
            const normalized = valid && values !== null ? JSON.stringify(values.slice().sort()) : null;
            const previous = bindings.get(group);
            const controls = metadata !== null || matches.length === 1 ? matches : [];
            if (previous && (previous.controls.length !== controls.length ||
                previous.controls.some((control, index) => control !== controls[index]) || previous.metadata !== normalized)) {
                previous.controls.forEach(control => control.removeEventListener("change", previous.onChange));
                bindings.delete(group);
            }
            if (!controls.length) {
                if (matches.length > 1) {
                    console.warn("crud_views: ambiguous conditional toggle", name);
                }
                return;
            }
            if (!bindings.has(group)) {
                const onChange = function () { sync(state); };
                bindings.set(group, { controls, values, metadata: normalized, onChange });
                controls.forEach(control => control.addEventListener("change", onChange));
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

    document.addEventListener("DOMContentLoaded", function () { initConditional(document); });
    if (document.readyState !== "loading") initConditional(document);

    document.addEventListener("cv:modal:unload", function (event) {
        const owners = new Set(event.target.querySelectorAll("form"));
        if (event.target.matches?.("form")) owners.add(event.target);
        owners.forEach(function (form) {
            const state = forms.get(form);
            if (!state) return;
            rememberExternal(state.observer.takeRecords());
            state.observer.disconnect();
            form.removeEventListener("reset", state.onReset);
            // Release only our temporary state before forgetting ownership. A
            // theme may retain and later reinsert this exact detached content.
            state.controls.forEach(function (el) {
                const disabled = baselines.get(el);
                if (el.disabled !== disabled) el.disabled = disabled;
                baselines.delete(el);
            });
            state.groups.forEach(function (group) {
                const binding = bindings.get(group);
                binding?.controls.forEach(control => control.removeEventListener("change", binding.onChange));
                bindings.delete(group);
                ownedStates.delete(group);
            });
            forms.delete(form);
        });
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
