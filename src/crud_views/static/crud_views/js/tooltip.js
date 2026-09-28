// src/crud_views/static/crud_views/js/tooltip.js
//
// Bootstrap tooltips are opt-in: data attributes alone do nothing until
// bootstrap.Tooltip is instantiated. This initializes the package's own
// triggers, marked with data-cv-tooltip. App-owned [data-bs-toggle="tooltip"]
// elements are deliberately left to the host application, so neither side
// double-initializes the other's tooltips.
(function () {
    if (globalThis.__cvTooltipInit) {
        return;
    }
    globalThis.__cvTooltipInit = true;

    function initTooltips(root) {
        // Without Bootstrap's JavaScript there is no tooltip; the trigger's
        // aria-label still carries the text for assistive technology.
        const Tooltip = globalThis.bootstrap?.Tooltip;
        if (!Tooltip) {
            return;
        }
        root.querySelectorAll("[data-cv-tooltip]").forEach((el) => {
            Tooltip.getOrCreateInstance(el);
        });
    }

    document.addEventListener("DOMContentLoaded", () => initTooltips(document));
    if (document.readyState !== "loading") {
        // loaded after DOMContentLoaded already fired (deferred or injected script)
        initTooltips(document);
    }

    // Modal content is injected via innerHTML after page load; modal.js
    // dispatches this event exactly so scripts can re-initialize inside it.
    document.addEventListener("cv:modal:loaded", (event) => initTooltips(event.target));

    globalThis.cv = globalThis.cv || {};
    globalThis.cv.initTooltips = initTooltips;
})();
