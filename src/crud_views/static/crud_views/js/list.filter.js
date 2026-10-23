(function () {
    function onToggle(event) {
        const button = event.currentTarget;
        event.preventDefault();

        // The button owns the state in aria-expanded. Collapse first: if the adapter throws
        // (no collapse implementation available) or returns false (the panel is still animating
        // and the toggle was ignored), nothing below runs and nothing changes.
        // A template override without aria-expanded: read the state off the panel instead.
        const panel = document.getElementById("filter-collapse");
        const expanded = button.hasAttribute("aria-expanded")
            ? button.getAttribute("aria-expanded") === "true"
            : panel !== null && !panel.hidden && globalThis.getComputedStyle(panel).display !== "none";
        const next = !expanded;
        if (globalThis.cv.adapters.collapse.toggle(panel) === false) {
            return;
        }
        button.setAttribute("aria-expanded", String(next));

        // toggle icon: a host-placed icon (#258) is a class on the button itself, swap it; otherwise both variants
        // are rendered server side as spans and one is hidden
        if (button.dataset.cvFilterIconOpen !== undefined) {
            const classes = (value) => (value || "").split(/\s+/).filter(Boolean);
            const open = classes(button.dataset.cvFilterIconOpen),
                close = classes(button.dataset.cvFilterIconClose);
            button.classList.remove(...(next ? open : close));
            button.classList.add(...(next ? close : open));
        } else {
            button.querySelectorAll("[data-cv-filter-icon]").forEach((icon) => (icon.hidden = !icon.hidden));
        }

        // persist the state server side; a failed request must not undo the toggle
        const config = cvGetConfig();
        fetch(config.request.path, {
            method: "POST",
            headers: {"X-CSRFToken": config.csrfToken, "Content-Type": "application/json; charset=utf-8"},
            body: JSON.stringify({filter_expanded: next}),
        }).catch(() => {});
    }

    // filter reset button: reset filter but keep the table sort / card order (the server keeps the same keys)
    function onReset() {
        const config = cvGetConfig(),
            params = new URLSearchParams(config.request.query_string),
            keep = new URLSearchParams();
        for (const key of ["sort", "order", "dir"]) {
            if (params.has(key)) {
                keep.set(key, params.get(key));
            }
        }
        keep.set("reset_filter", "true");
        globalThis.location.href = config.request.path + "?" + keep.toString();
    }

    function wire() {
        document.getElementById("cv-filter-toggle")?.addEventListener("click", onToggle);
        document.getElementById("filter-button-reset")?.addEventListener("click", onReset);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", wire);
    } else {
        // loaded after DOMContentLoaded already fired (deferred or injected script)
        wire();
    }
})();
