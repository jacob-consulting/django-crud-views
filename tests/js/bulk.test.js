import { afterEach, describe, expect, it, vi } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const path = "src/crud_views/static/crud_views/js/bulk.js";
const source = existsSync(path) ? readFileSync(path, "utf8") : "";
let dom;

function fixture({ ready = "complete", size = 3, missing = null } = {}) {
    dom = new JSDOM(`<form id="cv-bulk-selection" data-cv-bulk method="post">
        <button type="submit" hidden formmethod="dialog"></button>
        <label data-cv-bulk-enhanced hidden><input type="checkbox" data-cv-bulk-all>Select this page</label>
        <span data-cv-bulk-enhanced hidden><span data-cv-bulk-count>0</span> selected</span>
        <button type="submit" data-cv-bulk-action formaction="/archive/">Archive</button>
        <button type="submit" data-cv-bulk-action formaction="/publish/">Publish</button>
        </form>
        <table><tbody><tr><td><input type="checkbox" data-cv-bulk-item form="other" checked></td></tr></tbody></table>
        <form id="other"></form>
        ${Array.from({ length: size }, (_, index) => `<div class="card">
        <input type="checkbox" name="selected" value="${index}" data-cv-bulk-item form="cv-bulk-selection"></div>`).join("")}`,
    { runScripts: "outside-only", url: "https://example.test" });
    const document = dom.window.document;
    Object.defineProperty(document, "readyState", { configurable: true, value: ready });
    if (missing) document.querySelector(`[data-cv-bulk-${missing}]`).remove();
    const form = document.querySelector("[data-cv-bulk]");
    return {
        document, form,
        all: form.querySelector("[data-cv-bulk-all]"),
        count: form.querySelector("[data-cv-bulk-count]"),
        actions: [...form.querySelectorAll("[data-cv-bulk-action]")],
        enhanced: [...form.querySelectorAll("[data-cv-bulk-enhanced]")],
        items: [...document.querySelectorAll("[data-cv-bulk-item]")].filter(box => box.form === form),
        load: () => dom.window.eval(source),
        change: (input, checked) => {
            input.checked = checked;
            input.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
        },
    };
}

afterEach(() => { dom?.window.close(); vi.restoreAllMocks(); });

describe("bulk selection toolbar", () => {
    it("leaves a page without a bulk form unchanged", () => {
        const { document, form, load } = fixture();
        form.remove();
        const before = document.body.outerHTML;
        expect(load).not.toThrow();
        expect(document.body.outerHTML).toBe(before);
    });

    it("reveals server controls and disables actions with zero selected", () => {
        const { enhanced, count, actions, load } = fixture();
        load();
        expect(enhanced.every(el => !el.hasAttribute("hidden"))).toBe(true);
        expect(count.textContent).toBe("0");
        expect(actions.every(button => button.disabled)).toBe(true);
    });

    it("updates the count, action state and page checkbox for partial and full selection", () => {
        const { all, count, actions, items, load, change } = fixture(); load();
        change(items[0], true);
        expect(count.textContent).toBe("1");
        expect(actions.every(button => !button.disabled)).toBe(true);
        expect(all.checked).toBe(false);
        expect(all.indeterminate).toBe(true);
        items.slice(1).forEach(item => change(item, true));
        expect(count.textContent).toBe("3");
        expect(all.checked).toBe(true);
        expect(all.indeterminate).toBe(false);
    });

    it("selects and deselects all current-page items from the toolbar", () => {
        const { all, count, actions, items, load, change } = fixture(); load();
        change(all, true);
        expect(items.every(box => box.checked)).toBe(true);
        expect(count.textContent).toBe("3");
        change(all, false);
        expect(items.every(box => !box.checked)).toBe(true);
        expect(count.textContent).toBe("0");
        expect(actions.every(button => button.disabled)).toBe(true);
    });

    it("ignores record checkboxes belonging to another form", () => {
        const { document, all, count, load, change } = fixture(); load();
        const other = document.querySelector('[data-cv-bulk-item][form="other"]');
        expect(count.textContent).toBe("0");
        change(all, true);
        change(all, false);
        expect(other.checked).toBe(true);
        change(other, false);
        expect(count.textContent).toBe("0");
    });

    it("disables page selection and actions on an empty page", () => {
        const { all, actions, load } = fixture({ size: 0 }); load();
        expect(all.disabled).toBe(true);
        expect(all.checked).toBe(false);
        expect(all.indeterminate).toBe(false);
        expect(actions.every(button => button.disabled)).toBe(true);
    });

    it("preserves native submission buttons and the hidden no-navigation default", () => {
        const { form, all, actions, load, change } = fixture();
        const buttons = [...form.querySelectorAll("button")];
        const destinations = actions.map(button => button.getAttribute("formaction"));
        load(); change(all, true);
        expect([...form.querySelectorAll("button")]).toEqual(buttons);
        expect(buttons[0].hidden).toBe(true);
        expect(buttons[0].disabled).toBe(false);
        expect(buttons[0].getAttribute("formmethod")).toBe("dialog");
        expect(actions.map(button => button.getAttribute("formaction"))).toEqual(destinations);
    });

    it("recomputes restored checked values on pageshow", () => {
        const { all, count, actions, items, load } = fixture(); load();
        items.forEach(item => { item.checked = true; });
        dom.window.dispatchEvent(new dom.window.Event("pageshow"));
        expect(count.textContent).toBe("3");
        expect(all.checked).toBe(true);
        expect(actions.every(button => !button.disabled)).toBe(true);
    });

    it("binds once across two evaluations and updates once per change", () => {
        const { document, count, items, load, change } = fixture();
        const listen = vi.spyOn(document, "addEventListener"); load(); load();
        const update = vi.spyOn(count, "textContent", "set");
        change(items[0], true);
        expect(listen.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
        expect(update).toHaveBeenCalledTimes(1);
        expect(count.textContent).toBe("1");
    });

    it.each(["loading", "complete"])("starts at the right time when readyState is %s", ready => {
        const { document, enhanced, load } = fixture({ ready }); load();
        expect(enhanced.every(el => el.hidden)).toBe(ready === "loading");
        document.dispatchEvent(new dom.window.Event("DOMContentLoaded"));
        expect(enhanced.every(el => !el.hidden)).toBe(true);
    });

    it("binds once when interactive startup is followed by repeated DOMContentLoaded", () => {
        const { document, count, items, load, change } = fixture({ ready: "interactive" });
        const listen = vi.spyOn(document, "addEventListener"); load();
        document.dispatchEvent(new dom.window.Event("DOMContentLoaded"));
        document.dispatchEvent(new dom.window.Event("DOMContentLoaded"));
        expect(listen.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
        const update = vi.spyOn(count, "textContent", "set");
        change(items[0], true);
        expect(update).toHaveBeenCalledTimes(1);
        expect(count.textContent).toBe("1");
    });

    it.each(["all", "count"])("keeps the plain toolbar when %s is missing", missing => {
        const { enhanced, actions, load } = fixture({ missing });
        expect(load).not.toThrow();
        expect(enhanced.every(el => el.hidden)).toBe(true);
        expect(actions.every(button => !button.disabled)).toBe(true);
    });

    it("keeps the plain toolbar if listener binding fails", () => {
        const { all, enhanced, actions, load } = fixture();
        vi.spyOn(all, "addEventListener").mockImplementation(() => { throw new Error("binding failed"); });
        expect(load).toThrow("binding failed");
        expect(enhanced.every(el => el.hidden)).toBe(true);
        expect(actions.every(button => !button.disabled)).toBe(true);
    });

    it("uses only the six attributes and numeric text without storage, requests or dependencies", () => {
        expect(source).not.toBe("");
        expect(source).not.toMatch(/\bbootstrap\b|\bjQuery\b|\$\(|\$\.|innerHTML|localStorage|sessionStorage|fetch|XMLHttpRequest|createElement/);
        expect([...new Set(source.match(/data-cv-bulk(?:-[a-z]+)?/g))].sort()).toEqual([
            "data-cv-bulk", "data-cv-bulk-action", "data-cv-bulk-all", "data-cv-bulk-count",
            "data-cv-bulk-enhanced", "data-cv-bulk-item",
        ]);
        expect(source.match(/\w+\.textContent\s*=/g)).toEqual(["count.textContent ="]);
    });
});
