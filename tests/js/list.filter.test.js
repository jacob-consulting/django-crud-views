import $ from "jquery";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript, nav } from "./helpers/load.js";

function fixture({ expanded = false, queryString = "" } = {}) {
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="${queryString}" data-csrf-token="test-token" hidden></div>
        <button type="button" id="cv-filter-toggle" aria-expanded="${expanded}" aria-controls="filter-collapse">
            <span data-cv-filter-icon="open"${expanded ? " hidden" : ""}><i class="x"></i></span>
            <span data-cv-filter-icon="close"${expanded ? "" : " hidden"}><i class="y"></i></span>
        </button>
        <button type="button" id="filter-button-reset"></button>
        <div id="filter-collapse"></div>`;
    vi.stubGlobal("cvGetConfig", () => ({ request: { path: "/books/", query_string: queryString }, csrfToken: "t" }));
    return {
        open: document.querySelector('[data-cv-filter-icon="open"]'),
        close: document.querySelector('[data-cv-filter-icon="close"]'),
        toggle: document.querySelector("#cv-filter-toggle"),
    };
}

describe("list.filter.js", () => {
    let fetchMock;
    let toggle;

    beforeEach(() => {
        fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
        vi.stubGlobal("fetch", fetchMock);
        toggle = vi.fn();
        window.cv = { ...window.cv, adapters: { collapse: { toggle } } };
        nav.href = "";
    });

    it("flips the hidden attribute on click without touching icon classes", async () => {
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(f.open.hidden).toBe(true);
        expect(f.close.hidden).toBe(false);
        expect(f.open.querySelector("i").className).toBe("x");
        f.toggle.click();
        expect(f.open.hidden).toBe(false);
        expect(f.close.hidden).toBe(true);
    });

    it("flips aria-expanded, posts the new state as JSON and toggles the panel", async () => {
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        expect(toggle).toHaveBeenCalledWith(document.getElementById("filter-collapse"));
        expect(fetchMock).toHaveBeenCalledWith("/books/", {
            method: "POST",
            headers: { "X-CSRFToken": "t", "Content-Type": "application/json; charset=utf-8" },
            body: JSON.stringify({ filter_expanded: true }),
        });
        f.toggle.click();
        expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
        expect(fetchMock.mock.calls[1][1].body).toBe(JSON.stringify({ filter_expanded: false }));
    });

    it.each([
        ["open", "", true, false],
        ["closed", "display: none", false, true],
    ])("derives the state from the panel when the toggle has no aria-expanded (starts %s)", async (_n, style, startsOpen, expected) => {
        const f = fixture();
        f.toggle.removeAttribute("aria-expanded");
        document.getElementById("filter-collapse").setAttribute("style", style);
        await loadScript("list.filter");
        f.toggle.click();
        expect(startsOpen).toBe(!expected);
        expect(fetchMock.mock.calls[0][1].body).toBe(JSON.stringify({ filter_expanded: expected }));
        expect(f.toggle.getAttribute("aria-expanded")).toBe(String(expected));
    });

    it("changes nothing when the collapse adapter throws", async () => {
        vi.spyOn(console, "error").mockImplementation(() => {}); // jsdom reports listener errors here
        const swallow = (event) => event.preventDefault(); // ... and as a window "error" event
        window.addEventListener("error", swallow);
        toggle.mockImplementation(() => {
            throw new Error("no bootstrap");
        });
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        window.removeEventListener("error", swallow);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
        expect(f.open.hidden).toBe(false);
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("changes nothing when the collapse adapter refuses the toggle (panel still animating)", async () => {
        toggle.mockImplementation(() => false);
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(toggle).toHaveBeenCalledTimes(1);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("false");
        expect(f.open.hidden).toBe(false);
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it("still toggles when the state POST fails", async () => {
        fetchMock.mockImplementation(() => Promise.reject(new Error("offline")));
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(toggle).toHaveBeenCalledTimes(1);
        expect(f.toggle.getAttribute("aria-expanded")).toBe("true");
        await new Promise((r) => setTimeout(r, 0)); // the rejection is handled, no unhandled error
    });

    it.each([
        ["sort=name&page=2", "/books/?sort=name&reset_filter=true"],
        ["", "/books/?reset_filter=true"],
        ["order=title&dir=desc&title=x", "/books/?order=title&dir=desc&reset_filter=true"],
        ["sort=a%26b", "/books/?sort=a%26b&reset_filter=true"],
    ])("reset navigates with %j", async (queryString, expected) => {
        fixture({ queryString });
        await loadScript("list.filter");
        document.getElementById("filter-button-reset").click();
        expect(nav.href).toBe(expected);
    });

    it("loads and works without jQuery", async () => {
        vi.stubGlobal("$", undefined);
        vi.stubGlobal("jQuery", undefined);
        try {
            const f = fixture();
            await loadScript("list.filter");
            f.toggle.click();
            expect(toggle).toHaveBeenCalledTimes(1);
        } finally {
            vi.stubGlobal("$", $);
            vi.stubGlobal("jQuery", $);
        }
    });
});
