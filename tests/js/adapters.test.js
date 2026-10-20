import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

function fakeNamespace() {
    const instance = { show: vi.fn(), hide: vi.fn() };
    const collapse = { toggle: vi.fn() };
    return {
        instance, collapse,
        Modal: { getOrCreateInstance: vi.fn(() => instance), getInstance: vi.fn(() => instance) },
        Tooltip: { getOrCreateInstance: vi.fn((el) => ({ el })) },
        Collapse: { getOrCreateInstance: vi.fn(() => collapse) },
    };
}

describe("adapters.js", () => {
    beforeEach(() => { document.body.innerHTML = '<div id="m"><div id="d"></div></div><span id="t"></span>'; });
    afterEach(() => { vi.unstubAllGlobals(); delete window.cv; });

    it("defines cv.adapters.modal/tooltip/collapse and cv.bootstrapAdapters", async () => {
        await loadScript("adapters");
        expect(typeof window.cv.bootstrapAdapters).toBe("function");
        for (const name of ["modal", "tooltip", "collapse"]) expect(window.cv.adapters[name]).toBeDefined();
    });

    it("modal.show / hide drive Modal.getOrCreateInstance / getInstance", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), a = window.cv.bootstrapAdapters(ns), m = document.getElementById("m");
        a.modal.show(m);
        expect(ns.Modal.getOrCreateInstance).toHaveBeenCalledWith(m);
        expect(ns.instance.show).toHaveBeenCalledTimes(1);
        a.modal.hide(m);
        expect(ns.instance.hide).toHaveBeenCalledTimes(1);
    });

    it("modal.hide tolerates a missing instance", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(); ns.Modal.getInstance = vi.fn(() => null);
        expect(() => window.cv.bootstrapAdapters(ns).modal.hide(document.getElementById("m"))).not.toThrow();
    });

    it.each([["", "modal-dialog"], ["sm", "modal-dialog modal-sm"], ["lg", "modal-dialog modal-lg"],
             ["xl", "modal-dialog modal-xl"], ["huge", "modal-dialog"]])("setSize(%j) -> %j", async (size, cls) => {
        await loadScript("adapters");
        const d = document.getElementById("d"); d.className = "modal-dialog modal-xl";
        window.cv.bootstrapAdapters(fakeNamespace()).modal.setSize(d, size);
        expect(d.className).toBe(cls);
    });

    it("setSize keeps classes that are not size classes (shell overrides)", async () => {
        await loadScript("adapters");
        const d = document.getElementById("d"); d.className = "modal-dialog modal-dialog-centered modal-sm";
        const a = window.cv.bootstrapAdapters(fakeNamespace());
        a.modal.setSize(d, "lg");
        expect(d.classList.contains("modal-dialog-centered")).toBe(true);
        expect(d.classList.contains("modal-sm")).toBe(false);
        expect(d.classList.contains("modal-lg")).toBe(true);
        a.modal.setSize(d, "");
        expect(d.className).toBe("modal-dialog modal-dialog-centered");
    });

    it("tooltip.init uses Tooltip.getOrCreateInstance and is silent without it", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), t = document.getElementById("t");
        window.cv.bootstrapAdapters(ns).tooltip.init(t);
        expect(ns.Tooltip.getOrCreateInstance).toHaveBeenCalledWith(t);
        expect(() => window.cv.bootstrapAdapters({}).tooltip.init(t)).not.toThrow();
    });

    it("collapse.toggle uses Collapse.getOrCreateInstance(el).toggle() and returns true", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), d = document.getElementById("d");
        expect(window.cv.bootstrapAdapters(ns).collapse.toggle(d)).toBe(true);
        expect(ns.Collapse.getOrCreateInstance).toHaveBeenCalledWith(d);
        expect(ns.collapse.toggle).toHaveBeenCalledTimes(1);
    });

    it("collapse.toggle returns false and does not toggle while the panel is still animating", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), d = document.getElementById("d");
        d.className = "collapsing";
        expect(window.cv.bootstrapAdapters(ns).collapse.toggle(d)).toBe(false);
        expect(ns.collapse.toggle).not.toHaveBeenCalled();
    });

    it("modal.show and collapse.toggle throw a clear error without the namespace", async () => {
        await loadScript("adapters");
        const a = window.cv.bootstrapAdapters(undefined);
        expect(() => a.modal.show(document.getElementById("m"))).toThrow(/Bootstrap 5 JavaScript not loaded/);
        expect(() => a.collapse.toggle(document.getElementById("d"))).toThrow(/Bootstrap 5 JavaScript not loaded/);
    });

    it("resolves a function namespace at call time", async () => {
        await loadScript("adapters");
        let ns = null;
        const a = window.cv.bootstrapAdapters(() => ns), m = document.getElementById("m");
        expect(() => a.modal.show(m)).toThrow();
        ns = fakeNamespace();
        a.modal.show(m);
        expect(ns.instance.show).toHaveBeenCalledTimes(1);
    });

    it("default adapters look up globalThis.bootstrap lazily", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace();
        vi.stubGlobal("bootstrap", ns);
        window.cv.adapters.modal.show(document.getElementById("m"));
        expect(ns.instance.show).toHaveBeenCalledTimes(1);
    });

    it("keeps adapters assigned before the script loaded and fills the rest", async () => {
        const custom = { show: vi.fn(), hide: vi.fn(), setSize: vi.fn() };
        window.cv = { adapters: { modal: custom } };
        await loadScript("adapters");
        expect(window.cv.adapters.modal).toBe(custom);
        expect(window.cv.adapters.tooltip).toBeDefined();
        expect(window.cv.adapters.collapse).toBeDefined();
    });
});
