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
    if (!(e.target instanceof Element)) return;
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
    if (!(e.target instanceof Element)) return;
    const el = e.target.closest("[data-cv-action='submit-on-change']");
    if (el && el.form) el.form.submit();
});

// cancel button navigation via data-cv-cancel-url
document.addEventListener("click", function (e) {
    if (!(e.target instanceof Element)) return;
    const el = e.target.closest("[data-cv-cancel-url]");
    if (!el) return;
    e.preventDefault();
    globalThis.location.href = el.getAttribute("data-cv-cancel-url");
});

// alert dismissal via data-cv-alert-dismiss: the nearest role="alert" frame goes to the current alert adapter
document.addEventListener("click", function (e) {
    if (!(e.target instanceof Element)) return;
    const control = e.target.closest("[data-cv-alert-dismiss]");
    if (!control) return;
    const frame = control.closest('[role="alert"]');
    if (!frame) return;
    e.preventDefault();
    globalThis.cv.adapters.alert.close(frame);
});
