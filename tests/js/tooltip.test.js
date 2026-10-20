import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

// Minimal stand-in for bootstrap.Tooltip: one instance per element, like the real
// getOrCreateInstance.
function fakeBootstrap() {
    const instances = new Map();
    const Tooltip = {
        getOrCreateInstance: vi.fn((el) => {
            if (!instances.has(el)) {
                instances.set(el, { el, hide: vi.fn(), dispose: vi.fn() });
            }
            return instances.get(el);
        }),
        getInstance: vi.fn((el) => instances.get(el) ?? null),
    };
    return { bootstrap: { Tooltip }, instances };
}

function fixture() {
    document.body.innerHTML = `
        <button type="button" data-cv-tooltip="context" title="first"><i class="icon"></i></button>
        <button type="button" data-cv-tooltip title="bare"></button>
        <button type="button" data-bs-toggle="tooltip" data-bs-title="app-owned"></button>
        <div id="cv-modal"><div id="cv-modal-content"></div></div>`;
}

function domReady() {
    document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
}

describe("tooltip.js", () => {
    let fake;

    beforeAll(async () => {
        await loadScript("adapters");
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
        expect(fake.bootstrap.Tooltip.getOrCreateInstance).toHaveBeenCalledTimes(2);
    });

    it("is idempotent", () => {
        domReady();
        window.cv.initTooltips(document);
        expect(fake.instances.size).toBe(2);
    });

    it("initializes triggers injected into the modal", () => {
        domReady();
        const content = document.getElementById("cv-modal-content");
        content.innerHTML = '<button type="button" data-cv-tooltip title="in modal"></button>';
        document.getElementById("cv-modal").dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
        expect(fake.instances.has(content.querySelector("[data-cv-tooltip]"))).toBe(true);
    });

    it("initializes triggers in a formset row added via cv:formset:row-added", () => {
        domReady();
        const content = document.getElementById("cv-modal-content");
        content.innerHTML = '<div class="cv-formset-row"><button type="button" data-cv-tooltip title="in row"></button></div>';
        const row = content.querySelector(".cv-formset-row");
        row.dispatchEvent(new CustomEvent("cv:formset:row-added", { bubbles: true }));
        expect(fake.instances.has(row.querySelector("[data-cv-tooltip]"))).toBe(true);
    });

    it("does nothing (and does not throw) without Bootstrap's JavaScript", () => {
        vi.stubGlobal("bootstrap", undefined);
        expect(() => domReady()).not.toThrow();
        expect(() => window.cv.initTooltips(document)).not.toThrow();
    });

    it("initializes through cv.adapters.tooltip with the marker value as location", () => {
        const original = window.cv.adapters.tooltip;
        const init = vi.fn();
        window.cv.adapters.tooltip = { init };
        try {
            domReady();
            const [contextButton, bareButton] = document.querySelectorAll("[data-cv-tooltip]");
            expect(init).toHaveBeenCalledWith(contextButton, { location: "context" });
            expect(init).toHaveBeenCalledWith(bareButton, { location: "" });
            expect(init).toHaveBeenCalledTimes(2);
        } finally {
            window.cv.adapters.tooltip = original;
        }
    });

    it("keeps working with an adapter written for init(el)", () => {
        const original = window.cv.adapters.tooltip;
        const seen = [];
        window.cv.adapters.tooltip = { init(el) { seen.push(el); } };
        try {
            expect(() => domReady()).not.toThrow();
            expect(seen).toEqual([...document.querySelectorAll("[data-cv-tooltip]")]);
        } finally {
            window.cv.adapters.tooltip = original;
        }
    });

    describe("hide on click", () => {
        it("hides the clicked trigger's tooltip, also when the click lands on its icon", () => {
            domReady();
            const button = document.querySelector("[data-cv-tooltip]"), instance = fake.instances.get(button);
            button.querySelector("i").click();
            expect(instance.hide).toHaveBeenCalledTimes(1);
            button.click(); // a keyboard activation synthesises the same click
            expect(instance.hide).toHaveBeenCalledTimes(2);
        });

        it("ignores clicks on unmarked and app-owned elements", () => {
            domReady();
            document.querySelector('[data-bs-toggle="tooltip"]').click();
            document.body.click();
            expect(fake.bootstrap.Tooltip.getInstance).not.toHaveBeenCalled();
        });

        it("does nothing for a trigger without an instance", () => {
            // no domReady(): nothing was initialised
            const button = document.querySelector("[data-cv-tooltip]");
            expect(() => button.click()).not.toThrow();
            expect(fake.instances.size).toBe(0);
        });

        it("does not throw when the click target is not an element", () => {
            domReady();
            expect(() => document.dispatchEvent(new Event("click", { bubbles: true }))).not.toThrow();
        });

        it("binds the click listener once even when the script is loaded twice", async () => {
            await loadScript("tooltip");
            domReady();
            const button = document.querySelector("[data-cv-tooltip]");
            button.click();
            expect(fake.instances.get(button).hide).toHaveBeenCalledTimes(1);
        });

        it("keeps the Bootstrap hide when only init was replaced (the per-location recipe)", () => {
            domReady();
            const originalInit = window.cv.adapters.tooltip.init;
            try {
                window.cv.adapters.tooltip.init = () => {};
                const button = document.querySelector("[data-cv-tooltip]");
                button.click();
                expect(fake.instances.get(button).hide).toHaveBeenCalledTimes(1);
            } finally {
                window.cv.adapters.tooltip.init = originalInit;
            }
        });

        it("calls a custom adapter's hide(el) and tolerates an adapter without hide", () => {
            const original = window.cv.adapters.tooltip, hide = vi.fn();
            try {
                window.cv.adapters.tooltip = { init() {}, hide };
                const button = document.querySelector("[data-cv-tooltip]");
                button.click();
                expect(hide).toHaveBeenCalledWith(button);
                window.cv.adapters.tooltip = { init() {} };
                expect(() => button.click()).not.toThrow();
            } finally {
                window.cv.adapters.tooltip = original;
            }
        });
    });

    describe("dispose on cv:modal:unload", () => {
        function markedModalContent() {
            const content = document.getElementById("cv-modal-content");
            content.innerHTML = '<button type="button" data-cv-tooltip="object-detail" title="a"></button>'
                + '<button type="button" data-cv-tooltip="formset" title="b"></button>'
                + '<button type="button" data-bs-toggle="tooltip" data-bs-title="app"></button>';
            document.getElementById("cv-modal").dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
            return [...content.querySelectorAll("[data-cv-tooltip]")].map((el) => fake.instances.get(el));
        }

        function unload() {
            document.getElementById("cv-modal").dispatchEvent(new CustomEvent("cv:modal:unload", { bubbles: true }));
        }

        it("disposes every marked trigger under the modal once, and nothing outside it", () => {
            domReady();
            const outside = fake.instances.get(document.querySelector("[data-cv-tooltip]"));
            const inside = markedModalContent();
            unload();
            for (const instance of inside) expect(instance.dispose).toHaveBeenCalledTimes(1);
            expect(outside.dispose).not.toHaveBeenCalled();
            expect(fake.bootstrap.Tooltip.getInstance).toHaveBeenCalledTimes(2); // the app-owned button is not touched
        });

        it("does nothing on an empty modal (first open)", () => {
            domReady();
            expect(() => unload()).not.toThrow();
            expect(fake.bootstrap.Tooltip.getInstance).not.toHaveBeenCalled();
        });

        it("calls a custom adapter's dispose(el) and tolerates an adapter without dispose", () => {
            const original = window.cv.adapters.tooltip, dispose = vi.fn();
            try {
                window.cv.adapters.tooltip = { init() {}, dispose };
                const content = document.getElementById("cv-modal-content");
                content.innerHTML = '<button type="button" data-cv-tooltip title="x"></button>';
                unload();
                expect(dispose).toHaveBeenCalledTimes(1);
                expect(dispose).toHaveBeenCalledWith(content.querySelector("[data-cv-tooltip]"));
                window.cv.adapters.tooltip = { init() {} };
                expect(() => unload()).not.toThrow();
            } finally {
                window.cv.adapters.tooltip = original;
            }
        });

        it("does nothing (and does not throw) on click or unload without Bootstrap's JavaScript", () => {
            vi.stubGlobal("bootstrap", undefined);
            domReady();
            markedModalContent();
            expect(() => unload()).not.toThrow();
            expect(() => document.querySelector("[data-cv-tooltip]").click()).not.toThrow();
        });
    });
});
