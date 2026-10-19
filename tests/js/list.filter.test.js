import { beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

function fixture({ expanded = false } = {}) {
    document.body.innerHTML = `
        <div id="cv-config" data-request-path="/books/" data-query-string="" data-csrf-token="test-token" hidden></div>
        <button type="button" id="cv-filter-toggle">
            <span data-cv-filter-icon="open" class="${expanded ? "d-none" : ""}"><i class="x"></i></span>
            <span data-cv-filter-icon="close" class="${expanded ? "" : "d-none"}"><i class="y"></i></span>
        </button>
        <div id="filter-collapse"></div>`;
    return {
        open: document.querySelector('[data-cv-filter-icon="open"]'),
        close: document.querySelector('[data-cv-filter-icon="close"]'),
        toggle: document.querySelector("#cv-filter-toggle"),
    };
}

describe("list.filter.js", () => {
    beforeEach(async () => {
        vi.spyOn($, "post").mockImplementation(() => {});
        $.fn.collapse = vi.fn();
        // viewset.js is evaluated in its own function scope by loadScript, so provide the global it would define.
        vi.stubGlobal("cvGetConfig", () => ({ request: { path: "/books/", query_string: "" }, csrfToken: "t" }));
    });

    it("flips icon visibility on click without touching icon classes", async () => {
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect(f.open.classList.contains("d-none")).toBe(true);
        expect(f.close.classList.contains("d-none")).toBe(false);
        expect(f.open.querySelector("i").className).toBe("x");
        f.toggle.click();
        expect(f.open.classList.contains("d-none")).toBe(false);
        expect(f.close.classList.contains("d-none")).toBe(true);
    });

    it("posts state and toggles the collapse", async () => {
        const f = fixture();
        await loadScript("list.filter");
        f.toggle.click();
        expect($.post).toHaveBeenCalledTimes(1);
        expect($.fn.collapse).toHaveBeenCalledWith("toggle");
    });
});
