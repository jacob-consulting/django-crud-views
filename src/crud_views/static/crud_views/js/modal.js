/**
 * CrudViews modal: fetch-based modal rendering for views with cv_modal = True.
 *
 * Protocol (see the modals design spec, 2026-07-14, under superpowers/specs):
 *   GET  url  + X-CV-Modal: true  -> 200 modal partial (modal-header + modal-body)
 *   POST form + X-CV-Modal: true  -> 204 + X-CV-Redirect header (success: navigate)
 *                                 -> 422 + re-rendered partial   (validation errors: swap)
 * Anything else falls back to a full-page navigation — never strand the user in a broken modal.
 *
 * Before every content replacement a "cv:modal:unload" CustomEvent is dispatched on #cv-modal
 * while the previous content is still attached (hook for tearing down scripts inside modal
 * content); after every injection a "cv:modal:loaded" CustomEvent follows (hook for
 * re-initializing them).
 *
 * Showing, hiding and sizing the dialog goes through cv.adapters.modal (adapters.js).
 */

const CVModalConst = Object.freeze({
    modal: "cv-modal",
    dialog: "cv-modal-dialog",
    content: "cv-modal-content",
    urlAttr: "data-cv-url",
    loadedEvent: "cv:modal:loaded",
    unloadEvent: "cv:modal:unload",
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

// Each open owns its asynchronous requests, hide subscription and return target.
let cvModalSession = null;
let cvModalGeneration = 0;

function cvModalUsable(el) {
    if (!(el instanceof HTMLElement) || !el.isConnected || !el.getClientRects().length) return false;
    if (el.matches(":disabled, [aria-disabled='true']")) return false;
    for (let node = el; node; node = node.parentElement) {
        if (node.hidden || node.inert || node.getAttribute("aria-hidden") === "true") return false;
        const style = getComputedStyle(node);
        if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse") return false;
    }
    return true;
}

function cvModalFocus(el, temporary = false) {
    if (!cvModalUsable(el)) return false;
    const added = temporary && !el.hasAttribute("tabindex");
    const clean = () => {
        if (added && el.getAttribute("tabindex") === "-1") el.removeAttribute("tabindex");
        el.removeEventListener("blur", clean);
    };
    if (added) el.setAttribute("tabindex", "-1");
    el.focus();
    if (document.activeElement !== el) { clean(); return false; }
    if (added) el.addEventListener("blur", clean, {once: true});
    return true;
}

function cvModalRelease(session) {
    session.shown = false;
    session.unsubscribe?.();
    session.unsubscribe = null;
    session.opener = null;
    if (cvModalSession === session) cvModalSession = null;
}

function cvModalRestore(opener, modal) {
    if (!modal.contains(opener) && cvModalFocus(opener)) return;
    for (const el of document.querySelectorAll("main, [role='main']")) {
        if (!modal.contains(el) && cvModalFocus(el, true)) return;
    }
    for (const el of document.querySelectorAll("a[href], button, input, select, textarea, [tabindex], [contenteditable='true']")) {
        if (!modal.contains(el) && cvModalFocus(el)) return;
    }
    cvModalFocus(document.body, true);
}

function cvModalInject(html, recoverFocus = false) {
    const els = cvModalElements(), session = cvModalSession, active = document.activeElement;
    const lostFocus = recoverFocus && session?.shown && session.modal === els.modal && els.content.contains(active);
    // Listeners tear down old content while attached, then initialize its replacement.
    els.modal.dispatchEvent(new CustomEvent(CVModalConst.unloadEvent, {bubbles: true}));
    els.content.innerHTML = html;
    els.modal.dispatchEvent(new CustomEvent(CVModalConst.loadedEvent, {bubbles: true}));
    if (!lostFocus || cvModalSession !== session || !session.shown || active.isConnected) return;
    if (els.modal.contains(document.activeElement) && cvModalUsable(document.activeElement)) return;
    for (const selector of [":invalid, [aria-invalid='true']", "[" + CVModalConst.dismissAttr + "]"]) {
        for (const el of els.content.querySelectorAll(selector)) if (cvModalFocus(el)) return;
    }
    cvModalFocus(els.modal, true);
}

function cvModalOpen(url, size, opener = document.activeElement) {
    const els = cvModalElements();
    if (cvModalSession) cvModalRelease(cvModalSession);
    const session = {modal: els.modal, opener, shown: false, unsubscribe: null};
    cvModalSession = session;
    cvModalGeneration++;
    fetch(url, {headers: {"X-CV-Modal": "true"}})
        .then(function (response) {
            if (cvModalSession !== session) return null;
            if (!response.ok) {
                cvModalRelease(session);
                globalThis.location.assign(url);
                return null;
            }
            return response.text();
        })
        .then(function (html) {
            if (html === null || cvModalSession !== session) return;
            const adapter = cv.adapters.modal;
            if (typeof adapter.onHidden !== "function") {
                throw new Error("cv.adapters.modal.onHidden(modalEl, callback) is required; update your custom modal adapter.");
            }
            session.unsubscribe = adapter.onHidden(els.modal, function () {
                if (cvModalSession !== session || !session.shown) return;
                const target = session.opener;
                cvModalRelease(session);
                cvModalRestore(target, els.modal);
            });
            if (typeof session.unsubscribe !== "function") {
                throw new Error("cv.adapters.modal.onHidden must return an unsubscribe function.");
            }
            adapter.setSize(els.dialog, size || "");
            els.modal.setAttribute(CVModalConst.urlAttr, url);
            cvModalInject(html);
            if (cvModalSession !== session) return;
            session.shown = true;
            adapter.show(els.modal);
        })
        .catch(function (error) {
            if (cvModalSession !== session) return;
            // A malformed return value is not callable during cleanup.
            if (typeof session.unsubscribe !== "function") session.unsubscribe = null;
            cvModalRelease(session);
            console.error(error);
            globalThis.location.assign(url);
        });
}

function cvModalSubmit(form, submitter) {
    const els = cvModalElements(),
        url = form.getAttribute("action"),
        fallback = els.modal.getAttribute(CVModalConst.urlAttr) || url,
        generation = cvModalGeneration,
        session = cvModalSession?.modal === els.modal ? cvModalSession : null;
    const current = () => els.modal.isConnected && generation === cvModalGeneration &&
        (!session || (cvModalSession === session && session.shown));
    fetch(url, {
        method: "POST",
        // the submitter keeps the clicked button's name/value, as a native submit would
        body: new FormData(form, submitter || undefined),
        headers: {"X-CV-Modal": "true"},
    })
        .then(function (response) {
            if (!current()) return null;
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
            if (html === null || html === undefined || !current()) {
                return;
            }
            cvModalInject(html, true);
        })
        .catch(function () {
            if (current()) globalThis.location.assign(fallback);
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
        cvModalOpen(trigger.getAttribute("href"), trigger.getAttribute(CVModalConst.sizeAttr), trigger);
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
