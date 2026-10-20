import $ from "jquery";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript, nav } from "./helpers/load.js";
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
