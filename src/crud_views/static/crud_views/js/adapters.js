// src/crud_views/static/crud_views/js/adapters.js
// cv.adapters: the only place crud_views scripts touch a UI library. Themes replace entries;
// cv.bootstrapAdapters(ns) builds all five for any Bootstrap-compatible namespace.
globalThis.cv = globalThis.cv || {};
(function (cv) {
    const SIZE_CLASSES = Object.freeze({sm: "modal-sm", lg: "modal-lg", xl: "modal-xl"});
    function resolve(ns) { return (typeof ns === "function" ? ns() : ns) || null; }
    function component(ns, name) { const n = resolve(ns); return n && n[name] ? n[name] : null; }
    function missing(name) {
        return new Error(`cv.adapters: Bootstrap 5 JavaScript not loaded (no ${name} on the namespace); load Bootstrap's bundle or assign cv.adapters.`);
    }
    // One lifecycle observer per shell, shared by factory instances. Callback subscriptions
    // are removed per session; the WeakMap and shell-owned listeners do not retain detached shells.
    const modalLifecycles = new WeakMap();
    const guardedTooltips = new WeakSet();
    function guardTooltipTransitions(Tooltip, instance, el) {
        if (!instance || guardedTooltips.has(instance) || typeof instance._queueCallback !== "function" ||
            typeof Tooltip.getInstance !== "function") return;
        // Bootstrap 5.3 queues transition completions that outlive dispose(), which
        // nulls their instance state. Guard this instance's private queue seam only:
        // animations and live callbacks are unchanged, disposal stays synchronous.
        // A replacement instance on the same trigger must not revive the old work.
        const queue = instance._queueCallback;
        instance._queueCallback = function (callback, ...args) {
            return queue.call(this, function (...callbackArgs) {
                if (Tooltip.getInstance(el) === instance) return callback.apply(this, callbackArgs);
            }, ...args);
        };
        guardedTooltips.add(instance);
    }
    function modalLifecycle(modalEl) {
        let state = modalLifecycles.get(modalEl);
        if (state) return state;
        state = {hideEvent: null, pendingShow: null, subscribers: new Set()};
        modalLifecycles.set(modalEl, state);
        function showPending() {
            const pending = state.pendingShow;
            state.pendingShow = null;
            if (pending && [...pending.subscribers].some(entry => state.subscribers.has(entry))) pending.show();
        }
        modalEl.addEventListener("hide.bs.modal", event => {
            if (event.target !== modalEl) return;
            state.hideEvent = event;
            // Later listeners may prevent dismissal. Reconcile only after the full dispatch.
            queueMicrotask(() => {
                if (state.hideEvent === event && event.defaultPrevented) {
                    state.hideEvent = null;
                    for (const entry of state.subscribers) if (entry.skipHide === event) entry.skipHide = null;
                    showPending();
                }
            });
        });
        modalEl.addEventListener("hidden.bs.modal", event => {
            if (event.target !== modalEl) return;
            state.hideEvent = null;
            for (const entry of [...state.subscribers]) {
                if (!state.subscribers.has(entry)) continue;
                if (entry.skipHide) entry.skipHide = null;
                else entry.callback();
            }
            // Bootstrap ignores show() during a hide transition. A replacement session
            // waits for that old transition, without consuming its own hide subscription.
            showPending();
        });
        return state;
    }
    cv.bootstrapAdapters = function (ns) {
        return {
            modal: {
                onHidden(modalEl, callback) {
                    const state = modalLifecycle(modalEl), entry = {callback, skipHide: state.hideEvent};
                    state.subscribers.add(entry);
                    return () => {
                        state.subscribers.delete(entry);
                        if (!state.subscribers.size) state.pendingShow = null;
                    };
                },
                show(modalEl) {
                    const Modal = component(ns, "Modal"); if (!Modal) throw missing("Modal");
                    const state = modalLifecycle(modalEl);
                    const show = () => Modal.getOrCreateInstance(modalEl).show();
                    if (state.hideEvent) state.pendingShow = {show, subscribers: new Set(state.subscribers)};
                    else show();
                },
                hide(modalEl) { component(ns, "Modal")?.getInstance(modalEl)?.hide(); },
                setSize(dialogEl, size) {
                    // only the size classes change: a shell override may carry modal-dialog-centered etc.
                    dialogEl.classList.remove(...Object.values(SIZE_CLASSES));
                    dialogEl.classList.add("modal-dialog");
                    if (Object.hasOwn(SIZE_CLASSES, size)) dialogEl.classList.add(SIZE_CLASSES[size]);
                },
            },
            tooltip: {
                init(el) {
                    const Tooltip = component(ns, "Tooltip");
                    if (Tooltip) guardTooltipTransitions(Tooltip, Tooltip.getOrCreateInstance(el), el);
                },
                // getInstance, not getOrCreateInstance: a trigger that was never initialised gains nothing here.
                hide(el) { component(ns, "Tooltip")?.getInstance(el)?.hide(); },
                dispose(el) { component(ns, "Tooltip")?.getInstance(el)?.dispose(); },
            },
            tab: {
                init(el) { component(ns, "Tab")?.getOrCreateInstance(el); },
                // Cleanup must never create an instance on a previously untouched trigger.
                dispose(el) { component(ns, "Tab")?.getInstance(el)?.dispose(); },
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
