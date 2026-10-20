function cvGetConfig() {
    const el = document.getElementById("cv-config");
    if (!el) {
        throw new Error("cvGetConfig: #cv-config element not found. Make sure {% cv_config %} is in your base template.");
    }
    return {
        csrfToken: el.dataset.csrfToken,
        request: {
            path: el.dataset.requestPath,
            query_string: el.dataset.queryString,
        }
    };
}

// list action form submit via data-cv-action="submit-form"
document.addEventListener("click", function (e) {
    const el = e.target.closest("[data-cv-action='submit-form']");
    if (!el) return;
    e.preventDefault();
    const form = document.getElementById(el.getAttribute("data-cv-target"));
    if (!form) return;
    if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
    } else {
        form.submit();
    }
});

// auto-submit a form control (e.g. the card order combo) via data-cv-action="submit-on-change"
document.addEventListener("change", function (e) {
    const el = e.target.closest("[data-cv-action='submit-on-change']");
    if (el && el.form) el.form.submit();
});

// cancel button navigation via data-cv-cancel-url
document.addEventListener("click", function (e) {
    const el = e.target.closest("[data-cv-cancel-url]");
    if (!el) return;
    e.preventDefault();
    globalThis.location.href = el.getAttribute("data-cv-cancel-url");
});
