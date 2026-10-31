import $ from "jquery";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript, nav, resetNav } from "./helpers/load.js";
import { modalSkeleton } from "./helpers/dom.js";

function textResponse(html, { ok = true, status = 200, headers = {} } = {}) {
    return {
        ok,
        status,
        headers: { get: (name) => headers[name] ?? null },
        text: () => Promise.resolve(html),
    };
}

function stubFetch(responseOrError) {
    const impl = responseOrError instanceof Error
        ? () => Promise.reject(responseOrError)
        : () => Promise.resolve(responseOrError);
    const fetchMock = vi.fn(impl);
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
}

beforeAll(async () => { await loadScript("modal"); });

describe("modal.js", () => {
    let show, hide, setSize;

    beforeEach(() => {
        modalSkeleton();
        show = vi.fn();
        hide = vi.fn();
        setSize = vi.fn();
        window.cv = { ...window.cv, adapters: { modal: { show, hide, setSize, onHidden: () => () => {} } } };
    });

    describe("cvModalOpen", () => {
        it("GETs the url with the X-CV-Modal header", async () => {
            const fetchMock = stubFetch(textResponse("<p>hi</p>"));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(fetchMock).toHaveBeenCalledWith("/books/create/", { headers: { "X-CV-Modal": "true" } });
        });

        it("injects the partial, sets url + size and shows the modal on 200", async () => {
            stubFetch(textResponse("<p>partial</p>"));
            const loaded = vi.fn();
            document.getElementById("cv-modal").addEventListener("cv:modal:loaded", loaded);
            window.cv.cvModalOpen("/books/create/", "lg");
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(document.getElementById("cv-modal-content").innerHTML).toBe("<p>partial</p>");
            expect(setSize).toHaveBeenCalledWith(document.getElementById("cv-modal-dialog"), "lg");
            expect(document.getElementById("cv-modal").getAttribute("data-cv-url")).toBe("/books/create/");
            expect(loaded).toHaveBeenCalled();
            expect(nav.assign).not.toHaveBeenCalled();
        });

        it("dispatches cv:modal:unload before the swap, with the old content still attached", async () => {
            stubFetch(textResponse("<p>second</p>"));
            const modal = document.getElementById("cv-modal"), content = document.getElementById("cv-modal-content");
            content.innerHTML = "<p>first</p>";
            const seen = [];
            modal.addEventListener("cv:modal:unload", (event) => seen.push(["unload", event.target.id, content.innerHTML]));
            modal.addEventListener("cv:modal:loaded", () => seen.push(["loaded", content.innerHTML]));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(seen).toEqual([["unload", "cv-modal", "<p>first</p>"], ["loaded", "<p>second</p>"]]);
            expect(window.cv.CVModalConst.unloadEvent).toBe("cv:modal:unload");
        });

        it("dispatches cv:modal:unload also while the modal is still empty", () => {
            const unload = vi.fn();
            document.getElementById("cv-modal").addEventListener("cv:modal:unload", unload);
            window.cv.cvModalInject("<p>x</p>");
            expect(unload).toHaveBeenCalledTimes(1);
        });

        it("passes the empty token when no size is given", async () => {
            stubFetch(textResponse("<p>x</p>"));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(show).toHaveBeenCalled());
            expect(setSize).toHaveBeenCalledWith(document.getElementById("cv-modal-dialog"), "");
        });

        it("falls back to full-page navigation on a non-OK response", async () => {
            stubFetch(textResponse("boom", { ok: false, status: 500 }));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
            expect(show).not.toHaveBeenCalled();
            expect(document.getElementById("cv-modal-content").innerHTML).toBe("");
        });

        it("falls back to full-page navigation on a network error", async () => {
            stubFetch(new Error("offline"));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
        });
    });

    describe("cvModalSubmit", () => {
        function modalForm({ action = "/books/create/", modalUrl = null } = {}) {
            if (modalUrl) {
                document.getElementById("cv-modal").setAttribute("data-cv-url", modalUrl);
            }
            document.getElementById("cv-modal-content").innerHTML =
                `<form action="${action}"><input type="text" name="title" value="t"></form>`;
            return document.querySelector("#cv-modal-content form");
        }

        it("POSTs FormData with the X-CV-Modal header", async () => {
            const fetchMock = stubFetch(textResponse("", { status: 204, headers: { "X-CV-Redirect": "/books/" } }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalled());
            const [url, options] = fetchMock.mock.calls[0];
            expect(url).toBe("/books/create/");
            expect(options.method).toBe("POST");
            expect(options.headers).toEqual({ "X-CV-Modal": "true" });
            expect(options.body).toBeInstanceOf(FormData);
        });

        it("navigates to the X-CV-Redirect target on success", async () => {
            stubFetch(textResponse("", { status: 204, headers: { "X-CV-Redirect": "/books/" } }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/"));
        });

        it("swaps in the re-rendered partial on 422", async () => {
            stubFetch(textResponse("<form>errors</form>", { ok: false, status: 422 }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() =>
                expect(document.getElementById("cv-modal-content").innerHTML).toBe("<form>errors</form>"));
            expect(nav.assign).not.toHaveBeenCalled();
        });

        it("dispatches cv:modal:unload on the 422 re-render too", async () => {
            stubFetch(textResponse("<form>errors</form>", { ok: false, status: 422 }));
            const unload = vi.fn();
            document.addEventListener("cv:modal:unload", unload, { once: true });
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() =>
                expect(document.getElementById("cv-modal-content").innerHTML).toBe("<form>errors</form>"));
            expect(unload).toHaveBeenCalledTimes(1);
        });

        it("navigates to data-cv-url on an unexpected status", async () => {
            stubFetch(textResponse("boom", { ok: false, status: 500 }));
            window.cv.cvModalSubmit(modalForm({ modalUrl: "/books/create/?step=1" }));
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/?step=1"));
        });

        it("navigates to the form action when no data-cv-url is set", async () => {
            stubFetch(textResponse("boom", { ok: false, status: 500 }));
            window.cv.cvModalSubmit(modalForm());
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
        });

        it("navigates to the fallback on a network error", async () => {
            stubFetch(new Error("offline"));
            window.cv.cvModalSubmit(modalForm({ modalUrl: "/books/create/" }));
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
        });
    });

    describe("guards", () => {
        it("throws a descriptive error when #cv-modal is missing", () => {
            document.body.innerHTML = "";
            expect(() => window.cv.cvModalElements()).toThrow(/#cv-modal not found/);
        });

    });

    describe("delegated handlers", () => {
        it("opens the modal from a [data-cv-modal] link click", async () => {
            const fetchMock = stubFetch(textResponse("<p>x</p>"));
            document.body.insertAdjacentHTML("beforeend",
                `<a href="/books/1/delete/" data-cv-modal="true" data-cv-modal-size="xl">del</a>`);
            document.querySelector("a[data-cv-modal]").click();
            await vi.waitFor(() => expect(show).toHaveBeenCalledWith(document.getElementById("cv-modal")));
            expect(fetchMock).toHaveBeenCalledWith("/books/1/delete/", { headers: { "X-CV-Modal": "true" } });
            expect(setSize).toHaveBeenCalledWith(document.getElementById("cv-modal-dialog"), "xl");
        });

        it("intercepts form submits inside the modal content", async () => {
            const fetchMock = stubFetch(textResponse("", { status: 204, headers: { "X-CV-Redirect": "/done/" } }));
            document.getElementById("cv-modal-content").innerHTML = `<form action="/books/create/"></form>`;
            const form = document.querySelector("#cv-modal-content form");
            const event = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/done/"));
            expect(fetchMock.mock.calls[0][1].method).toBe("POST");
        });

        it("keeps the clicked submit button in the posted form data", async () => {
            const fetchMock = stubFetch(new Response(null, { status: 204, headers: { "X-CV-Redirect": "/done/" } }));
            document.getElementById("cv-modal-content").innerHTML =
                '<form action="/books/1/delete/" method="post"><button type="submit" name="confirm" value="yes">ok</button></form>';
            const form = document.querySelector("#cv-modal-content form");
            const button = form.querySelector("button");
            form.dispatchEvent(new SubmitEvent("submit", { bubbles: true, cancelable: true, submitter: button }));
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/done/"));
            expect(fetchMock.mock.calls[0][1].body.get("confirm")).toBe("yes");
        });

        it("dismiss clicks inside the shell call adapter.hide with #cv-modal", () => {
            document.getElementById("cv-modal-content").innerHTML =
                '<button type="button" data-cv-modal-dismiss></button>';
            const button = document.querySelector("[data-cv-modal-dismiss]");
            const event = new MouseEvent("click", { bubbles: true, cancelable: true });
            button.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
            expect(hide).toHaveBeenCalledWith(document.getElementById("cv-modal"));
        });

        it("logs and falls back to navigation when adapter.show throws", async () => {
            const error = vi.spyOn(console, "error").mockImplementation(() => {});
            show.mockImplementation(() => { throw new Error("no adapter"); });
            stubFetch(textResponse("<p>x</p>"));
            window.cv.cvModalOpen("/books/create/", "");
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/books/create/"));
            expect(error).toHaveBeenCalledTimes(1);
            error.mockRestore();
        });

        it("leaves modified clicks to the browser", () => {
            stubFetch(textResponse("<p>x</p>"));
            document.body.insertAdjacentHTML("beforeend",
                `<a href="/books/1/delete/" data-cv-modal="true" data-cv-modal-size="lg">del</a>`);
            const link = document.querySelector("a[data-cv-modal]");
            for (const init of [{ ctrlKey: true }, { metaKey: true }, { shiftKey: true }, { button: 1 }]) {
                const event = new MouseEvent("click", { bubbles: true, cancelable: true, ...init });
                link.dispatchEvent(event);
                expect(event.defaultPrevented).toBe(false);
            }
            expect(fetch).not.toHaveBeenCalled();
        });
    });

    // Phase 06 (D-17): the form-button leaf renders <button> bodies with nested icon / text spans. The browser's
    // own SubmitEvent.submitter and FormData(form, submitter) carry the clicked button; nothing here is mocked
    // except fetch, which is only spied on to read the body it was given.
    describe("native submitters (form-button leaf)", () => {
        // the three server-rendered bodies of a form button (crud_views/tags/button/form.html)
        const ICON = '<i class="fa-regular fa-trash-can" aria-hidden="true"></i>';
        const BODIES = {
            label: (text) => `<span>${text}</span>`,
            icon: (text) => `${ICON}<span class="visually-hidden">${text}</span>`,
            both: (text) => `${ICON} <span>${text}</span>`,
        };
        // a Django-escaped value, as {{ }} renders it, and the literal text a browser must submit for it
        const HOSTILE_HTML = "&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt; &amp; Ünïcødé ✓ 搜索 &#x27;x&#x27;";
        const HOSTILE = `"><script>alert(1)</script> & Ünïcødé ✓ 搜索 'x'`;

        // the delete confirmation shape: hidden CSRF + confirmation, the delete submitter, a sibling submitter and
        // the type="button" cancel control
        function deleteForm(mode = "label", { deleteValue = "Delete", inModal = true } = {}) {
            const html = `
                <form method="post" action="/author/1/delete/">
                    <input type="hidden" name="csrfmiddlewaretoken" value="csrf-tok">
                    <input type="hidden" name="confirm" value="true">
                    <button type="submit" name="delete" value="${deleteValue}" id="submit-id-delete"
                            class="btn btn-danger">${BODIES[mode]("Delete")}</button>
                    <button type="submit" name="submit" value="Create" id="submit-id-submit"
                            class="btn btn-primary">${BODIES[mode]("Create")}</button>
                    <button type="button" name="reset" value="Cancel" id="button-id-reset" class="btn btn-secondary"
                            data-cv-cancel-url="/author/">${BODIES[mode]("Cancel")}</button>
                </form>`;
            if (inModal) {
                document.getElementById("cv-modal-content").innerHTML = html;
            } else {
                document.body.insertAdjacentHTML("beforeend", `<div id="native">${html}</div>`);
            }
            const form = document.querySelector(inModal ? "#cv-modal-content form" : "#native form");
            return {
                form,
                del: form.querySelector('[name="delete"]'),
                other: form.querySelector('[name="submit"]'),
                cancel: form.querySelector('[name="reset"]'),
            };
        }

        function redirectFetch() {
            return stubFetch(new Response(null, { status: 204, headers: { "X-CV-Redirect": "/author/" } }));
        }

        async function postedBody(fetchMock) {
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith("/author/"));
            expect(fetchMock).toHaveBeenCalledTimes(1);
            const [url, options] = fetchMock.mock.calls[0];
            expect(url).toBe("/author/1/delete/");
            expect(options.method).toBe("POST");
            expect(options.headers).toEqual({ "X-CV-Modal": "true" });
            expect(options.body).toBeInstanceOf(FormData);
            return options.body;
        }

        function entries(formData) {
            return [...formData.entries()];
        }

        it("runs on the browser's own SubmitEvent and FormData", () => {
            // no polyfill or stub: the jsdom window's constructors are the globals the script resolves
            expect(globalThis.FormData).toBe(window.FormData);
            expect(globalThis.SubmitEvent).toBe(window.SubmitEvent);
            expect(Object.getOwnPropertyDescriptor(window.SubmitEvent.prototype, "submitter").get).toBeTypeOf("function");
            expect(Object.getOwnPropertyDescriptor(window.HTMLFormElement.prototype, "requestSubmit").value)
                .toBeTypeOf("function");
            const { form, del } = deleteForm();
            expect(new FormData(form, del).get("delete")).toBe("Delete");
            expect(new FormData(form).get("delete")).toBeNull();
        });

        it.each(Object.keys(BODIES))("a %s-body click on the button, icon or text posts only that submitter", async (mode) => {
            for (const pick of [
                (b) => b,
                (b) => b.querySelector("span"),
                (b) => b.querySelector("i") ?? b.querySelector("span"),
            ]) {
                resetNav();
                const fetchMock = redirectFetch();
                const { form, del, other } = deleteForm(mode);
                const seen = [];
                form.addEventListener("submit", (event) => seen.push(event));
                const target = pick(del);
                expect(del.contains(target)).toBe(true);
                target.click();
                expect(seen).toHaveLength(1);
                expect(seen[0]).toBeInstanceOf(window.SubmitEvent);
                expect(seen[0].submitter).toBe(del);
                expect(seen[0].defaultPrevented).toBe(true);
                const body = await postedBody(fetchMock);
                expect(entries(body)).toEqual([
                    ["csrfmiddlewaretoken", "csrf-tok"],
                    ["confirm", "true"],
                    ["delete", "Delete"],
                ]);
                expect(body.has(other.name)).toBe(false);
                expect(body.has("reset")).toBe(false);
            }
        });

        it("posts the sibling submitter instead when that one is clicked", async () => {
            const fetchMock = redirectFetch();
            const { form, other } = deleteForm("both");
            form.requestSubmit(other);
            const body = await postedBody(fetchMock);
            expect(entries(body)).toEqual([
                ["csrfmiddlewaretoken", "csrf-tok"],
                ["confirm", "true"],
                ["submit", "Create"],
            ]);
        });

        it("a type=button cancel click submits nothing", () => {
            const fetchMock = redirectFetch();
            const { form, cancel } = deleteForm("icon");
            const submit = vi.fn();
            form.addEventListener("submit", submit);
            cancel.querySelector("span").click();
            expect(submit).not.toHaveBeenCalled();
            expect(fetchMock).not.toHaveBeenCalled();
        });

        it("keeps the no-button fallback when the form is submitted without a submitter", async () => {
            const fetchMock = redirectFetch();
            const { form } = deleteForm("icon");
            const seen = [];
            form.addEventListener("submit", (event) => seen.push(event.submitter));
            form.requestSubmit();
            expect(seen).toEqual([null]);
            const body = await postedBody(fetchMock);
            expect(entries(body)).toEqual([
                ["csrfmiddlewaretoken", "csrf-tok"],
                ["confirm", "true"],
            ]);
        });

        it("transmits a hostile / Unicode button value as its decoded literal text", async () => {
            const fetchMock = redirectFetch();
            const { form, del } = deleteForm("both", { deleteValue: HOSTILE_HTML });
            expect(del.value).toBe(HOSTILE);
            expect(form.querySelectorAll("script")).toHaveLength(0);
            del.querySelector("i").click();
            const body = await postedBody(fetchMock);
            expect(body.get("delete")).toBe(HOSTILE);
            expect(body.getAll("delete")).toEqual([HOSTILE]);
            expect(body.get("csrfmiddlewaretoken")).toBe("csrf-tok");
        });

        it("leaves a form outside the modal to native submission with the same submitter payload", () => {
            const fetchMock = redirectFetch();
            const { form, del, other } = deleteForm("icon", { inModal: false });
            const seen = [];
            // registered after modal.js's document listener, so it sees the event the browser would act on
            const native = (event) => {
                seen.push([event.defaultPrevented, event.submitter, entries(new FormData(event.target, event.submitter))]);
                event.preventDefault(); // jsdom does not implement the navigation itself
            };
            window.addEventListener("submit", native);
            try {
                del.querySelector("i").click();
                other.querySelector("span").click();
            } finally {
                window.removeEventListener("submit", native);
            }
            expect(seen).toEqual([
                [false, del, [["csrfmiddlewaretoken", "csrf-tok"], ["confirm", "true"], ["delete", "Delete"]]],
                [false, other, [["csrfmiddlewaretoken", "csrf-tok"], ["confirm", "true"], ["submit", "Create"]]],
            ]);
            expect(fetchMock).not.toHaveBeenCalled();
        });
    });

    // Remove the probe load’s handlers and restore the original controller after this test.
    describe("without jQuery", () => {
        it("loads and wires its handlers without jQuery", async () => {
            vi.stubGlobal("$", undefined);
            vi.stubGlobal("jQuery", undefined);
            const previous = {...window.cv};
            const listeners = vi.spyOn(document, "addEventListener");
            try {
                await expect(loadScript("modal")).resolves.toBeUndefined();
            } finally {
                for (const [type, listener, options] of listeners.mock.calls) document.removeEventListener(type, listener, options);
                listeners.mockRestore();
                window.cv = previous;
                vi.stubGlobal("$", $);
                vi.stubGlobal("jQuery", $);
            }
        });
    });
});

describe("modal focus lifecycle", () => {
    let modal, content, opener, callbacks, cleanups, adapter, geometry;
    const formHTML = '<form action="/save" novalidate><input id="field" required><button type="submit">Save</button></form><button id="close" data-cv-modal-dismiss>Close</button>';
    beforeEach(() => {
        modalSkeleton();
        document.body.insertAdjacentHTML('afterbegin', '<main id="main"><button id="opener">Open</button><button id="alternate"><span id="icon">Alt</span></button></main>');
        modal = document.getElementById('cv-modal'); content = document.getElementById('cv-modal-content');
        opener = document.getElementById('opener'); callbacks = []; cleanups = [];
        // jsdom has no layout. Model rendered geometry only; focus and DOM lifecycle are real.
        geometry = vi.spyOn(HTMLElement.prototype, 'getClientRects').mockImplementation(function () {
            return this.hidden || this.style.display === 'none' || this.type === 'hidden' ? [] : [{width: 20, height: 20}];
        });
        adapter = {
            show: vi.fn(() => { modal.removeAttribute('aria-hidden'); modal.focus(); }),
            hide: vi.fn(), setSize: vi.fn(),
            onHidden: vi.fn((_el, callback) => { const cleanup = vi.fn(); callbacks.push(callback); cleanups.push(cleanup); return cleanup; }),
        };
        window.cv.adapters = {modal: adapter};
    });
    afterEach(() => { geometry.mockRestore(); });
    async function open(html = formHTML, trigger = opener) {
        adapter.show.mockClear(); trigger.focus(); stubFetch(textResponse(html)); window.cv.cvModalOpen('/open', '');
        await vi.waitFor(() => expect(adapter.show).toHaveBeenCalled());
    }
    async function replace(html) {
        const loaded = new Promise(resolve => modal.addEventListener("cv:modal:loaded", resolve, {once: true}));
        stubFetch(textResponse(html, {status: 422})); window.cv.cvModalSubmit(content.querySelector("form"));
        await loaded;
    }
    function complete(index = callbacks.length - 1) {
        modal.setAttribute('aria-hidden', 'true'); callbacks[index]();
    }
    it('does not steal focus before initial show or when injecting without a session', async () => {
        opener.focus(); window.cv.cvModalInject(formHTML); expect(document.activeElement).toBe(opener);
        adapter.show.mockImplementation(() => { expect(document.activeElement).toBe(opener); modal.removeAttribute('aria-hidden'); modal.focus(); });
        await open(); expect(document.activeElement).toBe(modal);
    });
    it('keeps usable focus assigned by loaded listeners after 422', async () => {
        await open(); content.querySelector('input').focus();
        modal.addEventListener('cv:modal:loaded', () => content.querySelector('#close').focus(), {once: true});
        await replace(formHTML.replace('id="field"', 'id="replacement"'));
        expect(document.activeElement.id).toBe('close');
    });
    it('ignores hidden, disabled, inert and aria-hidden invalid fields', async () => {
        await open(); content.querySelector('input').focus();
        await replace('<input required hidden><input required disabled><div inert><input required></div><div aria-hidden="true"><input required></div><input required id="valid-target">');
        expect(document.activeElement.id).toBe('valid-target');
    });
    it('tries dismiss then shell when invalid candidates cannot take focus and restores only added tabindex', async () => {
        await open(); content.querySelector('input').focus();
        modal.removeAttribute('tabindex');
        await replace('<div aria-invalid="true">Not focusable</div><button disabled data-cv-modal-dismiss>Unavailable</button>');
        expect(document.activeElement).toBe(modal); expect(modal.getAttribute('tabindex')).toBe('-1');
        complete(); expect(document.activeElement).toBe(opener); expect(modal.hasAttribute('tabindex')).toBe(false);
    });
    it('does not recover if the active element is outside the replaced content', async () => {
        await open(); opener.focus(); await replace('<input required id="replacement">'); expect(document.activeElement).toBe(opener);
    });
    it('waits for async hide completion; a prevented hide does not restore focus', async () => {
        await open(); const close = content.querySelector('#close'); close.focus(); close.click();
        expect(adapter.hide).toHaveBeenCalled(); expect(document.activeElement).toBe(close); expect(cleanups[0]).not.toHaveBeenCalled();
        complete(); expect(document.activeElement).toBe(opener); expect(cleanups[0]).toHaveBeenCalledTimes(1);
        document.getElementById('alternate').focus(); callbacks[0](); expect(document.activeElement.id).toBe('alternate');
    });
    it('supports synchronous completed hide and cleans the subscription', async () => {
        await open(); adapter.hide.mockImplementation(() => complete()); content.querySelector('#close').click();
        expect(document.activeElement).toBe(opener); expect(cleanups[0]).toHaveBeenCalledTimes(1);
    });
    it.each(['removed', 'disabled', 'hidden', 'inert', 'aria-hidden'])('uses main when opener is %s, cleaning temporary tabindex on blur', async (kind) => {
        await open();
        if (kind === 'removed') opener.remove(); else if (kind === 'aria-hidden') opener.setAttribute(kind, 'true'); else opener[kind] = true;
        complete(); const main = document.getElementById('main'); expect(document.activeElement).toBe(main); expect(main.getAttribute('tabindex')).toBe('-1');
        document.getElementById('alternate').focus(); expect(main.hasAttribute('tabindex')).toBe(false);
    });
    it('keeps existing landmark tabindex and uses external control then body as last resorts', async () => {
        await open(); const main = document.getElementById('main'); main.setAttribute('tabindex', '0'); opener.remove(); complete();
        expect(document.activeElement).toBe(main); document.getElementById('alternate').focus(); expect(main.getAttribute('tabindex')).toBe('0');
        await open(formHTML, document.getElementById('alternate')); document.querySelector('main').remove();
        document.body.insertAdjacentHTML('beforeend', '<button id="fallback">Fallback</button>'); complete(); expect(document.activeElement.id).toBe('fallback');
        await open(formHTML, document.getElementById('fallback')); document.getElementById('fallback').remove(); complete();
        expect(document.activeElement).toBe(document.body); expect(document.body.getAttribute('tabindex')).toBe('-1');
        modal.removeAttribute('aria-hidden'); modal.focus(); expect(document.body.hasAttribute('tabindex')).toBe(false);
    });
    it('captures the delegated trigger when a nested icon was clicked', async () => {
        const alternate = document.getElementById('alternate'); alternate.setAttribute('data-cv-modal', 'true'); alternate.setAttribute('href', '/open');
        opener.focus(); stubFetch(textResponse(formHTML)); document.getElementById('icon').click();
        await vi.waitFor(() => expect(adapter.show).toHaveBeenCalled()); complete(); expect(document.activeElement).toBe(alternate);
    });
    it('recovers focus when an already visible modal navigates to replacement content', async () => {
        await open(); content.querySelector('input').focus();
        const loaded = new Promise(resolve => modal.addEventListener('cv:modal:loaded', resolve, {once: true}));
        stubFetch(textResponse('<input required id="next-field">'));
        // A real adapter does not refocus an already shown shell on a second show call.
        adapter.show.mockImplementation(() => {});
        window.cv.cvModalOpen('/next', '', content.querySelector('input'));
        await loaded;
        expect(document.activeElement.id).toBe('next-field');
    });
    it('retains visible-shell focus recovery across an unresolved intermediate open', async () => {
        await open(); content.querySelector('input').focus();
        vi.stubGlobal('fetch', () => new Promise(() => {})); window.cv.cvModalOpen('/pending');
        const loaded = new Promise(resolve => modal.addEventListener('cv:modal:loaded', resolve, {once: true}));
        stubFetch(textResponse('<input required id="latest-field">')); adapter.show.mockImplementation(() => {});
        window.cv.cvModalOpen('/latest'); await loaded;
        expect(document.activeElement.id).toBe('latest-field');
    });
    it('ignores stale hidden callbacks after a new open and releases previous subscriptions', async () => {
        await open(); const old = callbacks[0]; adapter.show.mockClear(); await open(formHTML, document.getElementById('alternate'));
        expect(cleanups[0]).toHaveBeenCalledTimes(1); const active = document.activeElement; old(); expect(document.activeElement).toBe(active);
        complete(); expect(document.activeElement.id).toBe('alternate'); expect(cleanups[1]).toHaveBeenCalledTimes(1);
    });
    it.each(['hidden', 'replaced'])('ignores a late 422 after the session is %s', async kind => {
        await open(); let resolve; vi.stubGlobal('fetch', () => new Promise(r => { resolve = r; }));
        window.cv.cvModalSubmit(content.querySelector('form'));
        if (kind === 'hidden') complete(); else { adapter.show.mockClear(); await open('<p>new session</p>', document.getElementById('alternate')); }
        const previous = content.innerHTML, active = document.activeElement;
        resolve(textResponse('<input required id="stale">', {status: 422})); await new Promise(r => setTimeout(r, 0));
        expect(content.innerHTML).toBe(previous); expect(document.activeElement).toBe(active);
    });
    it('ignores an old open response and old request errors after a newer open', async () => {
        let resolve; vi.stubGlobal('fetch', () => new Promise(r => { resolve = r; })); window.cv.cvModalOpen('/old', '');
        await open('<p>new</p>'); resolve(textResponse('<p>old</p>')); await new Promise(r => setTimeout(r, 0));
        expect(content.innerHTML).toBe('<p>new</p>'); expect(nav.assign).not.toHaveBeenCalled();
    });
    it.each([undefined, () => null])('falls back before injection for missing/malformed lifecycle hooks', async hook => {
        adapter.onHidden = hook; const error = vi.spyOn(console, 'error').mockImplementation(() => {});
        try { stubFetch(textResponse(formHTML)); window.cv.cvModalOpen('/open', '');
            await vi.waitFor(() => expect(nav.assign).toHaveBeenCalledWith('/open'));
            expect(content.innerHTML).toBe(''); expect(adapter.show).not.toHaveBeenCalled(); expect(error).toHaveBeenCalled();
        } finally { error.mockRestore(); }
    });
    it('unsubscribes after a failed show', async () => {
        adapter.show.mockImplementation(() => { throw new Error('failed show'); });
        const error = vi.spyOn(console, 'error').mockImplementation(() => {});
        try { stubFetch(textResponse(formHTML)); window.cv.cvModalOpen('/open'); await vi.waitFor(() => expect(nav.assign).toHaveBeenCalled());
            expect(cleanups[0]).toHaveBeenCalledTimes(1);
        } finally { error.mockRestore(); }
    });
});
