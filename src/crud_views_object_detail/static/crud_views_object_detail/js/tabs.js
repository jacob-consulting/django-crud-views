// Stock object-detail tabs opt in through data-cv-od-tabs on their tablist.
// Bootstrap owns selection and keyboard behavior; initialize before the first
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

    function initObjectDetailTabs(root = document) {
        const triggers = ownedTriggers(root);
        // Native/unmarked layouts must not even look up the Bootstrap global.
        if (!triggers.length) {
            return;
        }
        const Tab = globalThis.bootstrap?.Tab;
        if (!Tab) {
            return;
        }
        triggers.forEach(el => Tab.getOrCreateInstance(el));
    }

    function disposeObjectDetailTabs(root) {
        const triggers = ownedTriggers(root);
        if (!triggers.length) {
            return;
        }
        const Tab = globalThis.bootstrap?.Tab;
        if (!Tab) {
            return;
        }
        // Never construct an instance during cleanup. modal.js dispatches unload
        // before replacing attached content; Bootstrap releases its own handlers.
        triggers.forEach(el => Tab.getInstance(el)?.dispose());
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
