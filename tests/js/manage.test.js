import { afterEach, describe, expect, it, vi } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const path = "src/crud_views/static/crud_views/js/manage.js";
const source = existsSync(path) ? readFileSync(path, "utf8") : "";
let dom;

function fixture(defaults = 2, { ready = "complete", control = true } = {}) {
    const section = (key, set = false) => `<table><tbody>
        <tr data-cv-section="${key}" data-cv-default-count="${defaults}"><th>
        <span data-cv-default-count hidden>${defaults} defaults hidden</span></th></tr>
        ${Array.from({ length: defaults }, () => '<tr data-cv-config-row data-cv-default-row><td>default</td></tr>').join("")}
        ${set ? '<tr data-cv-config-row><td>set value</td></tr>' : ""}
        </tbody></table>`;
    dom = new JSDOM(`<div data-cv-manage>
        ${control ? '<label hidden data-cv-defaults-control><input type="checkbox" data-cv-show-defaults checked>Show defaults</label>' : ""}
        <section id="cv-manage-views">${section("navigation", true)}${section("other")}</section>
        <details id="cv-manage-presentation"><summary>Presentation</summary>${section("templates")}</details>
        </div>`, { runScripts: "outside-only", url: "https://example.test" });
    Object.defineProperty(dom.window.document, "readyState", { configurable: true, value: ready });
    const root = dom.window.document.querySelector("[data-cv-manage]");
    const input = root.querySelector("input");
    return { root, input, load: () => dom.window.eval(source), change: checked => {
        input.checked = checked;
        input.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
    } };
}

afterEach(() => { dom?.window.close(); vi.restoreAllMocks(); });

describe("manage defaults", () => {
    it("provides the defaults initializer", () => {
        fixture().load();
        expect(typeof dom.window.cv?.initManageDefaults).toBe("function");
    });

    it.each([0, 1, 5])("toggles %i defaults in both cards and preserves set rows and counts", defaults => {
        const { root, input, load, change } = fixture(defaults);
        expect([...root.querySelectorAll("[data-cv-config-row]")].every(row => !row.hidden)).toBe(true);
        load();
        expect(input.checked).toBe(false);
        expect(input.parentElement.hidden).toBe(false);
        expect([...root.querySelectorAll("[data-cv-default-row]")].every(row => row.hidden)).toBe(true);
        expect(root.querySelector("[data-cv-config-row]:not([data-cv-default-row])").hidden).toBe(false);
        const counts = [...root.querySelectorAll("span[data-cv-default-count]")];
        expect(counts.map(el => el.hidden)).toEqual([true, defaults === 0, defaults === 0]);
        expect(counts.map(el => el.textContent)).toEqual(Array(3).fill(`${defaults} defaults hidden`));
        input.focus(); change(true);
        expect(dom.window.document.activeElement).toBe(input);
        expect([...root.querySelectorAll("[data-cv-config-row]")].every(row => !row.hidden)).toBe(true);
        expect(counts.every(el => el.hidden)).toBe(true);
        change(false);
        expect([...root.querySelectorAll("[data-cv-default-row]")].every(row => row.hidden)).toBe(true);
    });

    it("waits for readiness and supports late loading", () => {
        const { root, input, load } = fixture(1, { ready: "loading" }); load();
        expect(input.parentElement.hidden).toBe(true);
        expect(root.querySelector("[data-cv-default-row]").hidden).toBe(false);
        dom.window.document.dispatchEvent(new dom.window.Event("DOMContentLoaded"));
        expect(input.parentElement.hidden).toBe(false);
        expect(root.querySelector("[data-cv-default-row]").hidden).toBe(true);
    });

    it("initializes idempotently without resetting the checked choice or duplicate listeners", () => {
        const { root, input, load, change } = fixture();
        const listen = vi.spyOn(root, "addEventListener"); load(); change(true);
        dom.window.cv?.initManageDefaults(root);
        dom.window.cv?.initManageDefaults(dom.window.document);
        load();
        expect(input.checked).toBe(true);
        expect(listen.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
    });

    it("delegates changes without responding to unrelated controls", () => {
        const { root, input, load } = fixture(); load();
        const replacement = input.cloneNode(true); input.replaceWith(replacement);
        replacement.checked = true;
        replacement.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
        expect(root.querySelector("[data-cv-default-row]").hidden).toBe(false);
        const other = dom.window.document.createElement("input"); root.append(other);
        other.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
        expect(root.querySelector("[data-cv-default-row]").hidden).toBe(false);
    });

    it("leaves all values visible when the control is missing", () => {
        const { root, load } = fixture(1, { control: false }); load();
        expect(root.querySelector("[data-cv-default-row]").hidden).toBe(false);
    });

    it("leaves all values visible and control hidden if binding fails", () => {
        const { root, input, load } = fixture();
        vi.spyOn(root, "addEventListener").mockImplementation(() => { throw new Error("binding failed"); });
        expect(load).toThrow("binding failed");
        expect(input.parentElement.hidden).toBe(true);
        expect(root.querySelector("[data-cv-default-row]").hidden).toBe(false);
    });

    it("uses no storage, generated HTML, or direct third-party globals, including comments", () => {
        expect(source).not.toBe("");
        expect(source).not.toMatch(/\bbootstrap\b|\bjQuery\b|\$\(|\$\./);
        expect(source).not.toMatch(/innerHTML|localStorage|sessionStorage/);
    });
});
