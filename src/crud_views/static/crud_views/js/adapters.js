// src/crud_views/static/crud_views/js/adapters.js
// cv.adapters: the only place crud_views scripts touch a UI library. Themes replace entries;
// cv.bootstrapAdapters(ns) builds all three for any Bootstrap-compatible namespace.
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
                setSize(dialogEl, size) { dialogEl.className = "modal-dialog" + (SIZE_CLASSES[size] ? " " + SIZE_CLASSES[size] : ""); },
            },
            tooltip: { init(el) { component(ns, "Tooltip")?.getOrCreateInstance(el); } },
            collapse: { toggle(el) { const Collapse = component(ns, "Collapse"); if (!Collapse) throw missing("Collapse"); Collapse.getOrCreateInstance(el).toggle(); } },
        };
    };
    cv.adapters = Object.assign(cv.bootstrapAdapters(() => globalThis.bootstrap), cv.adapters || {});
})(globalThis.cv);
