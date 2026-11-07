// Stock object-detail tabs opt in through data-cv-od-tabs on their tablist.
// The theme adapter's UI library owns selection and keyboard behavior; initialize before the first
// keypress without calling show() or taking focus from the page/modal.
(function () {
    if (globalThis.__cvObjectDetailTabsInit) {
        return;
    }
    globalThis.__cvObjectDetailTabsInit = true;

    const ownedList = "[data-cv-od-tabs]";
    const tablist = '[data-cv-od-tabs], [role="tablist"], .nav, .list-group';
    const trigger = '[data-bs-toggle="tab"], [data-bs-toggle="pill"], [data-bs-toggle="list"]';

    function ownedTriggers(root) {
        const lists = [...root.querySelectorAll(ownedList)];
        if (root.matches?.(ownedList)) {
            lists.unshift(root);
        }
        return lists.flatMap(list => [...list.querySelectorAll(trigger)]
            .filter(el => el.closest(tablist) === list));
    }

    function tabAdapter() {
        const tab = globalThis.cv?.adapters?.tab;
        if (tab == null) return null;
        if (typeof tab.init !== "function" || typeof tab.dispose !== "function") {
            throw new TypeError("cv.adapters.tab must supply init(element) and dispose(element)");
        }
        return tab;
    }

    function initObjectDetailTabs(root = document) {
        const triggers = ownedTriggers(root);
        // Native/unmarked layouts must not even look up the adapter.
        if (!triggers.length) {
            return;
        }
        const tab = tabAdapter();
        if (!tab) {
            return;
        }
        triggers.forEach(el => tab.init(el));
    }

    function disposeObjectDetailTabs(root) {
        const triggers = ownedTriggers(root);
        if (!triggers.length) {
            return;
        }
        const tab = tabAdapter();
        if (!tab) {
            return;
        }
        // Never construct an instance during cleanup. modal.js dispatches unload
        // before replacing attached content; the adapter releases its own handlers.
        triggers.forEach(el => tab.dispose(el));
    }

    globalThis.cv = globalThis.cv || {};
    globalThis.cv.initObjectDetailTabs = initObjectDetailTabs;
    document.addEventListener("DOMContentLoaded", () => initObjectDetailTabs(document));
    if (document.readyState !== "loading") {
        initObjectDetailTabs(document);
    }
    document.addEventListener("cv:modal:loaded", event => initObjectDetailTabs(event.target));
    document.addEventListener("cv:modal:unload", event => disposeObjectDetailTabs(event.target));
})();
