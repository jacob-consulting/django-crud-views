import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

function fakeBootstrap() {
    const instances = new Map();
    const Tab = {
        getOrCreateInstance: vi.fn(el => {
            if (!instances.has(el)) {
                instances.set(el, {
                    show: vi.fn(),
                    dispose: vi.fn(() => instances.delete(el)),
                });
            }
            return instances.get(el);
        }),
        getInstance: vi.fn(el => instances.get(el) ?? null),
    };
    return { bootstrap: { Tab }, instances };
}

function tabs(id = "page", count = 2, selected = 0) {
    return `<div id="${id}" role="tablist" data-cv-od-tabs>${Array.from({ length: count }, (_, index) => `
        <button id="${id}-${index}" role="tab" type="button" data-bs-toggle="pill"
            class="nav-link${index === selected ? " active" : ""}"
            aria-selected="${index === selected}" tabindex="${index === selected ? 0 : -1}">${index}</button>
    `).join("")}</div>`;
}

describe("object-detail tabs real asset", () => {
    let fake, listeners;

    beforeEach(() => {
        fake = fakeBootstrap();
        vi.stubGlobal("bootstrap", fake.bootstrap);
        document.body.innerHTML = tabs();
        // Track only this script's document hooks so each test exercises fresh loading.
        listeners = [];
        const add = document.addEventListener.bind(document);
        vi.spyOn(document, "addEventListener").mockImplementation((...args) => {
            listeners.push(args);
            add(...args);
        });
        vi.spyOn(document, "readyState", "get").mockReturnValue("loading");
    });

    afterEach(() => {
        listeners.forEach(args => document.removeEventListener(...args));
        delete window.__cvObjectDetailTabsInit;
        delete window.cv?.initObjectDetailTabs;
        vi.restoreAllMocks();
        vi.unstubAllGlobals();
    });

    async function loadTabs() {
        await loadScript("adapters"); // Existing core loading remains the default.
        await loadScript("tabs", "crud_views_object_detail");
        expect(window.cv.initObjectDetailTabs).toBeTypeOf("function");
    }

    it("initializes every owned trigger on DOMContentLoaded", async () => {
        await loadTabs();
        expect(fake.instances.size).toBe(0);
        document.dispatchEvent(new Event("DOMContentLoaded"));
        expect([...fake.instances.keys()]).toEqual([...document.querySelectorAll('[role="tab"]')]);
        expect(fake.bootstrap.Tab.getOrCreateInstance).toHaveBeenCalledTimes(2);
    });

    it("initializes immediately when loaded after DOMContentLoaded", async () => {
        vi.spyOn(document, "readyState", "get").mockReturnValue("complete");
        await loadTabs();
        expect(fake.instances.size).toBe(2);
    });

    it("includes the supplied root itself and supports one tab", async () => {
        document.body.innerHTML = tabs("single", 1) + tabs("sibling");
        await loadTabs();
        window.cv.initObjectDetailTabs(document.getElementById("single"));
        expect([...fake.instances.keys()]).toEqual([document.getElementById("single-0")]);
    });

    it("does not capture nested unmarked tablists or unrelated triggers", async () => {
        document.getElementById("page").insertAdjacentHTML("beforeend", `
            <div role="tablist"><button role="tab" data-bs-toggle="pill" id="foreign"></button></div>
            ${tabs("nested", 1)}
            <button type="button" id="plain">Unrelated</button>`);
        await loadTabs();
        window.cv.initObjectDetailTabs();
        expect([...fake.instances.keys()].map(el => el.id)).toEqual(["page-0", "page-1", "nested-0"]);
        expect(fake.bootstrap.Tab.getOrCreateInstance).toHaveBeenCalledTimes(3);
    });

    it("performs no Bootstrap lookup for unmarked native content", async () => {
        document.body.innerHTML = '<section><button role="tab">Native control</button></section>';
        const lookup = vi.spyOn(window, "bootstrap", "get").mockImplementation(() => {
            throw new Error("Native layouts must not access Bootstrap");
        });
        await loadTabs();
        window.cv.initObjectDetailTabs();
        expect(lookup).not.toHaveBeenCalled();
    });

    it("leaves server selection intact without Bootstrap", async () => {
        vi.stubGlobal("bootstrap", undefined);
        const before = document.body.innerHTML;
        await loadTabs();
        window.cv.initObjectDetailTabs();
        expect(document.body.innerHTML).toBe(before);
    });

    it("does not show or focus a tab or change an already selected second tab", async () => {
        document.body.innerHTML = tabs("page", 2, 1);
        const second = document.getElementById("page-1");
        second.focus();
        const focus = vi.spyOn(second, "focus");
        const before = document.body.innerHTML;
        await loadTabs();
        window.cv.initObjectDetailTabs();
        const instances = [...fake.instances.values()];
        window.cv.initObjectDetailTabs();
        expect([...fake.instances.values()]).toEqual(instances);
        expect(instances).toHaveLength(2);
        instances.forEach(instance => expect(instance.show).not.toHaveBeenCalled());
        expect(focus).not.toHaveBeenCalled();
        expect(document.activeElement).toBe(second);
        expect(document.body.innerHTML).toBe(before);
    });

    it("rejects unknown package keys clearly", async () => {
        await expect(loadScript("tabs", "other")).rejects.toThrow("Unknown static package: other");
        await expect(loadScript("tabs", "toString")).rejects.toThrow("Unknown static package: toString");
    });
});
