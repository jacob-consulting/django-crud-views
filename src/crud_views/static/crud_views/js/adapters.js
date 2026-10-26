// src/crud_views/static/crud_views/js/adapters.js
// cv.adapters: the only place crud_views scripts touch a UI library. Themes replace entries;
// cv.bootstrapAdapters(ns) builds all four for any Bootstrap-compatible namespace.
globalThis.cv = globalThis.cv || {};
(function (cv) {
    const SIZE_CLASSES = Object.freeze({sm: "modal-sm", lg: "modal-lg", xl: "modal-xl"});
    function resolve(ns) { return (typeof ns === "function" ? ns() : ns) || null; }
    function component(ns, name) { const n = resolve(ns); return n && n[name] ? n[name] : null; }
    function missing(name) {
        return new Error(`cv.adapters: Bootstrap 5 JavaScript not loaded (no ${name} on the namespace); load Bootstrap's bundle or assign cv.adapters.`);
    }
    cv.bootstrapAdapters = function (ns) {
        return {
            modal: {
                show(modalEl) { const Modal = component(ns, "Modal"); if (!Modal) throw missing("Modal"); Modal.getOrCreateInstance(modalEl).show(); },
                hide(modalEl) { component(ns, "Modal")?.getInstance(modalEl)?.hide(); },
                setSize(dialogEl, size) {
                    // only the size classes change: a shell override may carry modal-dialog-centered etc.
                    dialogEl.classList.remove(...Object.values(SIZE_CLASSES));
                    dialogEl.classList.add("modal-dialog");
                    if (Object.hasOwn(SIZE_CLASSES, size)) dialogEl.classList.add(SIZE_CLASSES[size]);
                },
            },
            tooltip: {
                init(el) { component(ns, "Tooltip")?.getOrCreateInstance(el); },
                // getInstance, not getOrCreateInstance: a trigger that was never initialised gains nothing here.
                hide(el) { component(ns, "Tooltip")?.getInstance(el)?.hide(); },
                dispose(el) { component(ns, "Tooltip")?.getInstance(el)?.dispose(); },
            },
            collapse: {
                toggle(el) {
                    const Collapse = component(ns, "Collapse");
                    if (!Collapse) throw missing("Collapse");
                    // Bootstrap ignores toggle() while the panel is still animating; report that
                    // so the caller does not flip its own state against an unchanged panel.
                    if (el.classList.contains("collapsing")) return false;
                    Collapse.getOrCreateInstance(el).toggle();
                    return true;
                },
            },
            alert: {
                // without an Alert component the default adapter removes the frame itself; a present
                // component (or a theme's own adapter) owns the outcome, including its errors.
                close(el) {
                    const Alert = component(ns, "Alert");
                    if (Alert) Alert.getOrCreateInstance(el).close();
                    else el.remove();
                },
            },
        };
    };
    cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {});
})(globalThis.cv);
