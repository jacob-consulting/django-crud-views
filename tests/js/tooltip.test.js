import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

// Minimal stand-in for bootstrap.Tooltip: one instance per element, like the real
// getOrCreateInstance.
function fakeBootstrap() {
    const instances = new Map();
    const Tooltip = {
        getOrCreateInstance: vi.fn((el) => {
            if (!instances.has(el)) {
                instances.set(el, { el });
            }
            return instances.get(el);
        }),
    };
    return { bootstrap: { Tooltip }, instances };
}

function fixture() {
    document.body.innerHTML = `
        <button type="button" data-cv-tooltip data-bs-title="first" aria-label="first"></button>
        <button type="button" data-bs-toggle="tooltip" data-bs-title="app-owned"></button>
        <div id="cv-modal"><div id="cv-modal-content"></div></div>`;
}

function domReady() {
    document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
}

describe("tooltip.js", () => {
    let fake;

    beforeAll(async () => {
        await loadScript("tooltip");
    });

    beforeEach(() => {
        fake = fakeBootstrap();
        vi.stubGlobal("bootstrap", fake.bootstrap);
        fixture();
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("initializes the package's tooltip triggers on DOMContentLoaded", () => {
        domReady();
        const ours = document.querySelector("[data-cv-tooltip]");
        expect(fake.instances.has(ours)).toBe(true);
    });

    it("leaves app-owned data-bs-toggle tooltips alone", () => {
        domReady();
        const appOwned = document.querySelector('[data-bs-toggle="tooltip"]');
        expect(fake.instances.has(appOwned)).toBe(false);
        expect(fake.bootstrap.Tooltip.getOrCreateInstance).toHaveBeenCalledTimes(1);
    });

    it("is idempotent", () => {
        domReady();
        window.cv.initTooltips(document);
        expect(fake.instances.size).toBe(1);
    });

    it("initializes triggers injected into the modal", () => {
        domReady();
        const content = document.getElementById("cv-modal-content");
        content.innerHTML = '<button type="button" data-cv-tooltip data-bs-title="in modal"></button>';
        document.getElementById("cv-modal").dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
        expect(fake.instances.has(content.querySelector("[data-cv-tooltip]"))).toBe(true);
    });

    it("does nothing (and does not throw) without Bootstrap's JavaScript", () => {
        vi.stubGlobal("bootstrap", undefined);
        expect(() => domReady()).not.toThrow();
        expect(() => window.cv.initTooltips(document)).not.toThrow();
    });
});
