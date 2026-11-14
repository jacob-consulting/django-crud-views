// Authorized diagnostics stay visible until the defaults control is ready.
(function () {
    if (globalThis.__cvManageInit) {
        return;
    }
    globalThis.__cvManageInit = true;
    const initialized = new WeakSet();

    function updateDefaults(root, show) {
        root.querySelectorAll("[data-cv-default-row]").forEach(row => { row.hidden = !show; });
        root.querySelectorAll("[data-cv-section]").forEach(section => {
            const rows = [...section.parentElement.querySelectorAll("[data-cv-config-row]")];
            const count = section.querySelector("[data-cv-default-count]");
            if (count) {
                count.hidden = !rows.length || rows.some(row => !row.hidden);
            }
        });
    }

    function initManageDefaults(root) {
        const pages = [...root.querySelectorAll("[data-cv-manage]")];
        if (root.matches?.("[data-cv-manage]")) {
            pages.unshift(root);
        }
        pages.forEach(page => {
            if (initialized.has(page)) {
                return;
            }
            const control = page.querySelector("[data-cv-show-defaults]");
            const container = control?.closest("[data-cv-defaults-control]");
            if (!container) {
                return;
            }
            // Bind before changing visibility, so a failed setup leaves readable values.
            page.addEventListener("change", event => {
                if (event.target.matches?.("[data-cv-show-defaults]")) {
                    updateDefaults(page, event.target.checked);
                }
            });
            initialized.add(page);
            control.checked = false;
            updateDefaults(page, false);
            container.hidden = false;
        });
    }

    document.addEventListener("DOMContentLoaded", () => initManageDefaults(document));
    if (document.readyState !== "loading") {
        initManageDefaults(document);
    }
    document.addEventListener("cv:modal:loaded", event => initManageDefaults(event.target));
    globalThis.cv = globalThis.cv || {};
    globalThis.cv.initManageDefaults = initManageDefaults;
})();
