/**
 * CrudViews modal: fetch-based modal rendering for views with cv_modal = True.
 *
 * Protocol (see the modals design spec, 2026-07-14, under superpowers/specs):
 *   GET  url  + X-CV-Modal: true  -> 200 modal partial (modal-header + modal-body)
 *   POST form + X-CV-Modal: true  -> 204 + X-CV-Redirect header (success: navigate)
 *                                 -> 422 + re-rendered partial   (validation errors: swap)
 * Anything else falls back to a full-page navigation — never strand the user in a broken modal.
 *
 * After every injection a "cv:modal:loaded" CustomEvent is dispatched on #cv-modal
 * (hook for re-initializing scripts inside modal content).
 *
 * Showing, hiding and sizing the dialog goes through cv.adapters.modal (adapters.js).
 */

const CVModalConst = Object.freeze({
    modal: "cv-modal",
    dialog: "cv-modal-dialog",
    content: "cv-modal-content",
    urlAttr: "data-cv-url",
    loadedEvent: "cv:modal:loaded",
    dismissAttr: "data-cv-modal-dismiss",
    sizeAttr: "data-cv-modal-size",
    trigger: "[data-cv-modal='true']",
});

function cvModalElements() {
    const modal = document.getElementById(CVModalConst.modal);
    if (!modal) {
        throw new Error("cvModal: #cv-modal not found. Make sure {% cv_config %} is in your base template.");
    }
    return {
        modal: modal,
        dialog: document.getElementById(CVModalConst.dialog),
        content: document.getElementById(CVModalConst.content),
    };
}

function cvModalInject(html) {
    const els = cvModalElements();
    els.content.innerHTML = html;
    els.modal.dispatchEvent(new CustomEvent(CVModalConst.loadedEvent, {bubbles: true}));
}

function cvModalOpen(url, size) {
    const els = cvModalElements();
    fetch(url, {headers: {"X-CV-Modal": "true"}})
        .then(function (response) {
            if (!response.ok) {
                globalThis.location.assign(url);
                return null;
            }
            return response.text();
        })
        .then(function (html) {
            if (html === null) {
                return;
            }
            cv.adapters.modal.setSize(els.dialog, size || "");
            els.modal.setAttribute(CVModalConst.urlAttr, url);
            cvModalInject(html);
            cv.adapters.modal.show(els.modal);
        })
        .catch(function (error) {
            console.error(error);
            globalThis.location.assign(url);
        });
}

function cvModalSubmit(form, submitter) {
    const els = cvModalElements(),
        url = form.getAttribute("action"),
        fallback = els.modal.getAttribute(CVModalConst.urlAttr) || url;
    fetch(url, {
        method: "POST",
        // the submitter keeps the clicked button's name/value, as a native submit would
        body: new FormData(form, submitter || undefined),
        headers: {"X-CV-Modal": "true"},
    })
        .then(function (response) {
            const redirect = response.headers.get("X-CV-Redirect");
            if (redirect) {
                globalThis.location.assign(redirect);
                return null;
            }
            if (response.status === 422) {
                return response.text();
            }
            globalThis.location.assign(fallback);
            return null;
        })
        .then(function (html) {
            if (html === null || html === undefined) {
                return;
            }
            cvModalInject(html);
        })
        .catch(function () {
            globalThis.location.assign(fallback);
        });
}

document.addEventListener("click", function (event) {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
        return;
    }
    if (!(event.target instanceof Element)) {
        return;
    }
    const trigger = event.target.closest(CVModalConst.trigger);
    if (trigger) {
        event.preventDefault();
        cvModalOpen(trigger.getAttribute("href"), trigger.getAttribute(CVModalConst.sizeAttr));
        return;
    }
    const dismiss = event.target.closest("[" + CVModalConst.dismissAttr + "]");
    if (!dismiss) {
        return;
    }
    const modal = document.getElementById(CVModalConst.modal);
    if (modal && modal.contains(dismiss)) {
        event.preventDefault();
        cv.adapters.modal.hide(modal);
    }
});

document.addEventListener("submit", function (event) {
    if (!(event.target instanceof Element) || !event.target.closest("#" + CVModalConst.content)) {
        return;
    }
    event.preventDefault();
    cvModalSubmit(event.target, event.submitter);
});

// Test seam: expose the modal API on a shared namespace. The functions above
// are already implicit window globals in the browser (top-level declarations);
// this only adds `CVModalConst` and namespaced access for the unit tests.
globalThis.cv = globalThis.cv || {};
Object.assign(globalThis.cv, {CVModalConst, cvModalElements, cvModalInject, cvModalOpen, cvModalSubmit});
