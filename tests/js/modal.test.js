import $ from "jquery";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
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

describe("modal.js", () => {
    let show, hide, setSize;

    beforeAll(async () => {
        await loadScript("modal");
    });

    beforeEach(() => {
        modalSkeleton();
        show = vi.fn();
        hide = vi.fn();
        setSize = vi.fn();
        window.cv = { ...window.cv, adapters: { modal: { show, hide, setSize } } };
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

    // Keep last: re-loading the script registers a second set of document listeners.
    describe("without jQuery", () => {
        it("loads and wires its handlers without jQuery", async () => {
            vi.stubGlobal("$", undefined);
            vi.stubGlobal("jQuery", undefined);
            await expect(loadScript("modal")).resolves.toBeUndefined();
            vi.stubGlobal("$", $);
            vi.stubGlobal("jQuery", $);
        });
    });
});
