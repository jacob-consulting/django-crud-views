// src/crud_views/static/crud_views/js/tooltip.js
//
// Tooltips are opt-in: data attributes alone do nothing until a tooltip is
// instantiated. This initializes the package's own triggers, marked with
// data-cv-tooltip, through cv.adapters.tooltip (see adapters.js). The marker's
// value names the trigger's location (context, list, card, card-order, formset,
// object-detail; "" for a bare marker) and is passed to the adapter as
// init(el, {location}); the tooltip text lives in the trigger's title attribute.
// App-owned [data-bs-toggle="tooltip"] elements are deliberately left to the host
// application, so neither side double-initializes the other's tooltips.
// Lifecycle, through the adapter's optional hide(el) and dispose(el): a click on a
// trigger hides its tooltip, and markers inside the modal are disposed before the
// modal content is replaced (cv:modal:unload).
(function () {
    if (globalThis.__cvTooltipInit) {
        return;
    }
    globalThis.__cvTooltipInit = true;

    function initTooltips(root) {
        // Without a tooltip implementation (or without adapters.js) nothing happens;
        // the trigger's aria-label still carries the text for assistive technology.
        const tooltip = globalThis.cv?.adapters?.tooltip;
        if (!tooltip) {
            return;
        }
        root.querySelectorAll("[data-cv-tooltip]").forEach((el) => {
            tooltip.init(el, {location: el.getAttribute("data-cv-tooltip") || ""});
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
    // Same for formset rows added by formset.js after page load.
    document.addEventListener("cv:formset:row-added", (event) => initTooltips(event.target));

    function disposeTooltips(root) {
        const tooltip = globalThis.cv?.adapters?.tooltip;
        if (!tooltip?.dispose) {
            return;
        }
        root.querySelectorAll("[data-cv-tooltip]").forEach((el) => tooltip.dispose(el));
    }

    // modal.js dispatches this before it replaces the modal content, while the old
    // content is still attached, so instances on it can be torn down (Bootstrap's
    // Tooltip.dispose() needs the trigger's enclosing .modal to unhook its handler).
    document.addEventListener("cv:modal:unload", (event) => disposeTooltips(event.target));

    // A tooltip shown by the focus trigger would otherwise stay until focus leaves the
    // clicked button; Bootstrap's hide() clears all active triggers, so it stays hidden
    // until the next hover or focus. Keyboard activation synthesises the same click.
    document.addEventListener("click", (event) => {
        if (!(event.target instanceof Element)) {
            return;
        }
        const el = event.target.closest("[data-cv-tooltip]");
        if (el) {
            globalThis.cv?.adapters?.tooltip?.hide?.(el);
        }
    });

    globalThis.cv = globalThis.cv || {};
    globalThis.cv.initTooltips = initTooltips;
})();
