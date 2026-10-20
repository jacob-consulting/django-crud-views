(function () {
    function onToggle(event) {
        const button = event.currentTarget;
        event.preventDefault();

        // The button owns the state in aria-expanded. Collapse first: if the adapter throws
        // (no collapse implementation available), nothing below runs and nothing changes.
        // A template override without aria-expanded: read the state off the panel instead.
        const panel = document.getElementById("filter-collapse");
        const expanded = button.hasAttribute("aria-expanded")
            ? button.getAttribute("aria-expanded") === "true"
            : panel !== null && !panel.hidden && globalThis.getComputedStyle(panel).display !== "none";
        const next = !expanded;
        globalThis.cv.adapters.collapse.toggle(panel);
        button.setAttribute("aria-expanded", String(next));

        // toggle icon (both variants are rendered server side, one is hidden)
        button.querySelectorAll("[data-cv-filter-icon]").forEach((icon) => icon.classList.toggle("d-none"));

        // persist the state server side; a failed request must not undo the toggle
        const config = cvGetConfig();
        fetch(config.request.path, {
            method: "POST",
            headers: {"X-CSRFToken": config.csrfToken, "Content-Type": "application/json; charset=utf-8"},
            body: JSON.stringify({filter_expanded: next}),
        }).catch(() => {});
    }

    // filter reset button: reset filter but keep sort
    function onReset() {
        const config = cvGetConfig(),
            url = config.request.path,
            params = new URLSearchParams(config.request.query_string),
            reset_param = "reset_filter=true";
        if (params.has("sort")) {
            globalThis.location.href = url + "?sort=" + params.get("sort") + "&" + reset_param;
        } else {
            globalThis.location.href = url + "?" + reset_param;
        }
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
