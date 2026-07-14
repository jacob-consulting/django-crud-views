/**
 * CrudViews modal: fetch-based Bootstrap 5 modal rendering for views with cv_modal = True.
 *
 * Protocol (superpowers/specs/2026-07-14-bootstrap-modals-design.md):
 *   GET  url  + X-CV-Modal: true  -> 200 modal partial (modal-header + modal-body)
 *   POST form + X-CV-Modal: true  -> 204 + X-CV-Redirect header (success: navigate)
 *                                 -> 422 + re-rendered partial   (validation errors: swap)
 * Anything else falls back to a full-page navigation — never strand the user in a broken modal.
 *
 * After every injection a "cv:modal:loaded" CustomEvent is dispatched on #cv-modal
 * (hook for re-initializing scripts inside modal content).
 */

const CVModalConst = Object.freeze({
    modal: "cv-modal",
    dialog: "cv-modal-dialog",
    content: "cv-modal-content",
    urlAttr: "data-cv-url",
    loadedEvent: "cv:modal:loaded",
});

function cvModalElements() {
    const modal = document.getElementById(CVModalConst.modal);
    if (!modal) {
        throw new Error("cvModal: #cv-modal not found. Make sure {% cv_config %} is in your base template.");
    }
    if (typeof bootstrap === "undefined" || !bootstrap.Modal) {
        throw new Error("cvModal: Bootstrap 5 JavaScript not loaded.");
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
                window.location.assign(url);
                return null;
            }
            return response.text();
        })
        .then(function (html) {
            if (html === null) {
                return;
            }
            els.dialog.className = "modal-dialog" + (size ? " " + size : "");
            els.modal.setAttribute(CVModalConst.urlAttr, url);
            cvModalInject(html);
            bootstrap.Modal.getOrCreateInstance(els.modal).show();
        })
        .catch(function () {
            window.location.assign(url);
        });
}

function cvModalSubmit(form) {
    const els = cvModalElements(),
        url = form.getAttribute("action"),
        fallback = els.modal.getAttribute(CVModalConst.urlAttr) || url;
    fetch(url, {
        method: "POST",
        body: new FormData(form),
        headers: {"X-CV-Modal": "true"},
    })
        .then(function (response) {
            const redirect = response.headers.get("X-CV-Redirect");
            if (redirect) {
                window.location.assign(redirect);
                return null;
            }
            if (response.status === 422) {
                return response.text();
            }
            window.location.assign(fallback);
            return null;
        })
        .then(function (html) {
            if (html === null || html === undefined) {
                return;
            }
            cvModalInject(html);
        })
        .catch(function () {
            window.location.assign(fallback);
        });
}

$(document).ready(function () {
    $(document).on("click", "[data-cv-modal='true']", function (e) {
        e.preventDefault();
        cvModalOpen($(this).attr("href"), $(this).attr("data-cv-modal-size"));
    });

    $(document).on("submit", "#cv-modal-content form", function (e) {
        e.preventDefault();
        cvModalSubmit(this);
    });
});
