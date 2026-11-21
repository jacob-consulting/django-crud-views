// Selection stays in the current page's native form controls.
(function () {
    if (globalThis.__cvBulkInit) {
        return;
    }
    globalThis.__cvBulkInit = true;
    const initialized = new WeakSet();

    function init(form) {
        if (initialized.has(form)) {
            return;
        }
        const all = form.querySelector("[data-cv-bulk-all]");
        const count = form.querySelector("[data-cv-bulk-count]");
        if (!all || !count) {
            return;
        }
        const actions = [...form.querySelectorAll("[data-cv-bulk-action]")];
        const items = () => [...document.querySelectorAll("input[type=checkbox][data-cv-bulk-item]")]
            .filter(box => box.form === form);
        const refresh = () => {
            const boxes = items();
            const selected = boxes.filter(box => box.checked).length;
            count.textContent = String(selected);
            actions.forEach(button => { button.disabled = selected === 0; });
            all.checked = boxes.length > 0 && selected === boxes.length;
            all.indeterminate = selected > 0 && selected < boxes.length;
            all.disabled = boxes.length === 0;
        };

        // Bind before revealing controls or changing the native button state.
        document.addEventListener("change", event => {
            if (event.target.matches?.("[data-cv-bulk-item]") && event.target.form === form) {
                refresh();
            }
        });
        all.addEventListener("change", () => {
            items().forEach(box => { box.checked = all.checked; });
            refresh();
        });
        globalThis.addEventListener("pageshow", refresh);
        initialized.add(form);
        form.querySelectorAll("[data-cv-bulk-enhanced]").forEach(el => { el.hidden = false; });
        refresh();
    }

    const start = () => document.querySelectorAll("form[data-cv-bulk]").forEach(init);
    document.addEventListener("DOMContentLoaded", start);
    if (document.readyState !== "loading") {
        start();
    }
})();
