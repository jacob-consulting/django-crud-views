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
        delete window.cv;
        vi.restoreAllMocks();
        vi.unstubAllGlobals();
    });

    async function loadTabs() {
        await loadScript("adapters"); // Existing core loading remains the default.
        await loadScript("tabs", "crud_views_object_detail");
        expect(window.cv.initObjectDetailTabs).toBeTypeOf("function");
    }

    function observedError(root, name) {
        let error;
        const observe = event => { error = event.error; event.preventDefault(); };
        window.addEventListener("error", observe);
        try { modalEvent(root, name); } finally { window.removeEventListener("error", observe); }
        return error;
    }

    it("dispatches to early and late custom tab adapters without a library lookup", async () => {
        const early = { init: vi.fn(), dispose: vi.fn() };
        window.cv = { adapters: { tab: early } };
        await loadTabs();
        expect(window.cv.adapters.tab).toBe(early);
        window.cv.initObjectDetailTabs();
        expect(early.init).toHaveBeenCalledTimes(2);
        expect(early.init.mock.calls.map(([el]) => el.id)).toEqual(["page-0", "page-1"]);
        const late = { init: vi.fn(), dispose: vi.fn() };
        window.cv.adapters.tab = late;
        window.cv.initObjectDetailTabs();
        modalEvent(document.getElementById("page"), "unload");
        expect(late.init).toHaveBeenCalledTimes(2);
        expect(late.dispose).toHaveBeenCalledTimes(2);
        expect(early.dispose).not.toHaveBeenCalled();
        expect(fake.bootstrap.Tab.getOrCreateInstance).not.toHaveBeenCalled();
    });

    it.each(["cv", "adapters", "tab"])("no-ops with absent %s for init and disposal", async missing => {
        await loadTabs();
        const initialize = window.cv.initObjectDetailTabs;
        if (missing === "cv") delete window.cv;
        else if (missing === "adapters") delete window.cv.adapters;
        else delete window.cv.adapters.tab;
        initialize();
        expect(observedError(document.getElementById("page"), "unload")).toBeUndefined();
        expect(fake.bootstrap.Tab.getOrCreateInstance).not.toHaveBeenCalled();
        expect(fake.bootstrap.Tab.getInstance).not.toHaveBeenCalled();
    });

    it.each([{}, { init() {} }, { dispose() {} }, { init: 1, dispose() {} }])(
        "rejects malformed present adapter %j on init and unload", async adapter => {
            await loadTabs();
            window.cv.adapters.tab = adapter;
            expect(() => window.cv.initObjectDetailTabs()).toThrow(TypeError);
            expect(observedError(document.getElementById("page"), "unload")).toBeInstanceOf(TypeError);
        });

    it.each(["init", "dispose"])("preserves the original custom %s exception", async method => {
        await loadTabs();
        const error = new Error("custom adapter failure");
        window.cv.adapters.tab = { init() {}, dispose() {}, [method]() { throw error; } };
        if (method === "init") {
            expect(() => window.cv.initObjectDetailTabs()).toThrow(error);
            expect(observedError(document.getElementById("page"), "loaded")).toBe(error);
        } else expect(observedError(document.getElementById("page"), "unload")).toBe(error);
    });

    it("never resolves adapters for native or empty roots on either lifecycle", async () => {
        await loadTabs();
        document.body.innerHTML = '<section id="native"></section><div data-cv-od-tabs id="empty"></div>';
        const lookup = vi.fn(() => { throw new Error("lookup"); });
        Object.defineProperty(window.cv, "adapters", { configurable: true, get: lookup });
        window.cv.initObjectDetailTabs();
        for (const root of document.body.children) {
            expect(observedError(root, "loaded")).toBeUndefined();
            expect(observedError(root, "unload")).toBeUndefined();
        }
        expect(lookup).not.toHaveBeenCalled();
    });

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

    function modalEvent(root, name) {
        root.dispatchEvent(new CustomEvent(`cv:modal:${name}`, { bubbles: true }));
    }

    it("initializes injected modal tabs without touching page siblings", async () => {
        document.body.insertAdjacentHTML("beforeend", `<div id="modal">${tabs("injected")}</div>`);
        await loadTabs();
        modalEvent(document.getElementById("modal"), "loaded");
        expect([...fake.instances.keys()].map(el => el.id)).toEqual(["injected-0", "injected-1"]);
    });

    it("disposes only existing modal instances while the content is attached", async () => {
        document.body.insertAdjacentHTML("beforeend", `<div id="modal">${tabs("injected")}</div>`);
        await loadTabs();
        window.cv.initObjectDetailTabs();
        const modal = document.getElementById("modal");
        const old = [...modal.querySelectorAll('[role="tab"]')].map(el => [el, fake.instances.get(el)]);
        old.forEach(([el, instance]) => instance.dispose.mockImplementation(() => {
            expect(el.isConnected).toBe(true);
            fake.instances.delete(el);
        }));
        fake.bootstrap.Tab.getOrCreateInstance.mockClear();
        modalEvent(modal, "unload");
        old.forEach(([, instance]) => expect(instance.dispose).toHaveBeenCalledOnce());
        expect([...fake.instances.keys()].map(el => el.id)).toEqual(["page-0", "page-1"]);
        expect(fake.bootstrap.Tab.getOrCreateInstance).not.toHaveBeenCalled();
        modalEvent(modal, "unload");
        old.forEach(([, instance]) => expect(instance.dispose).toHaveBeenCalledOnce());
    });

    it("ignores nested unrelated tablists during disposal", async () => {
        const root = document.getElementById("page");
        root.insertAdjacentHTML("beforeend", `
            <div role="tablist"><button role="tab" data-bs-toggle="pill" id="foreign"></button></div>
            ${tabs("nested", 1)}`);
        await loadTabs();
        const foreign = document.getElementById("foreign");
        const instance = fake.bootstrap.Tab.getOrCreateInstance(foreign);
        window.cv.initObjectDetailTabs();
        modalEvent(root, "unload");
        expect([...fake.instances.keys()]).toEqual([foreign]);
        expect(instance.dispose).not.toHaveBeenCalled();
        expect(fake.bootstrap.Tab.getInstance.mock.calls.map(([el]) => el.id))
            .toEqual(["page-0", "page-1", "nested-0"]);
    });

    it("handles repeated load, unload, retained reopen and replacement using the root itself", async () => {
        await loadTabs();
        const root = document.getElementById("page");
        modalEvent(root, "loaded");
        const first = [...fake.instances.values()];
        expect(first).toHaveLength(2);
        modalEvent(root, "loaded");
        expect([...fake.instances.values()]).toEqual(first);
        modalEvent(root, "unload");
        expect(fake.instances.size).toBe(0);
        modalEvent(root, "loaded");
        expect(fake.instances.size).toBe(2);
        expect([...fake.instances.values()]).not.toEqual(first);
        modalEvent(root, "unload");
        root.innerHTML = '<button role="tab" data-bs-toggle="pill" id="replacement"></button>';
        modalEvent(root, "loaded");
        expect([...fake.instances.keys()]).toEqual([document.getElementById("replacement")]);
    });

    it("installs lifecycle listeners once across repeated script evaluation", async () => {
        await loadTabs();
        const hooks = ["DOMContentLoaded", "cv:modal:loaded", "cv:modal:unload"];
        const before = listeners.filter(([type]) => hooks.includes(type));
        expect(before.map(([type]) => type).sort()).toEqual([...hooks].sort());
        await loadScript("tabs", "crud_views_object_detail");
        expect(listeners.filter(([type]) => hooks.includes(type))).toEqual(before);
        modalEvent(document.getElementById("page"), "loaded");
        expect(fake.bootstrap.Tab.getOrCreateInstance).toHaveBeenCalledTimes(2);
        modalEvent(document.getElementById("page"), "unload");
        expect(fake.bootstrap.Tab.getInstance).toHaveBeenCalledTimes(2);
    });

    it("preserves second-tab selection and focus on repeated modal loads", async () => {
        document.body.innerHTML = tabs("page", 2, 1);
        const root = document.getElementById("page");
        const second = document.getElementById("page-1");
        second.focus();
        const before = root.innerHTML;
        const focus = vi.spyOn(second, "focus");
        await loadTabs();
        modalEvent(root, "loaded");
        modalEvent(root, "loaded");
        expect(fake.instances.size).toBe(2);
        expect(root.innerHTML).toBe(before);
        expect(document.activeElement).toBe(second);
        expect(focus).not.toHaveBeenCalled();
        fake.instances.forEach(instance => expect(instance.show).not.toHaveBeenCalled());
    });

    it("makes no Bootstrap lookup for native or empty modal content", async () => {
        document.body.innerHTML = '<section id="native">Native</section><div data-cv-od-tabs id="empty"></div>';
        const lookup = vi.spyOn(window, "bootstrap", "get").mockImplementation(() => {
            throw new Error("Native layouts must not access Bootstrap");
        });
        await loadTabs();
        for (const root of document.body.children) {
            modalEvent(root, "loaded");
            modalEvent(root, "unload");
        }
        expect(lookup).not.toHaveBeenCalled();
    });

    it("tolerates missing Bootstrap during loaded and unload lifecycle", async () => {
        vi.stubGlobal("bootstrap", undefined);
        const before = document.body.innerHTML;
        await loadTabs();
        const root = document.getElementById("page");
        modalEvent(root, "loaded");
        modalEvent(root, "unload");
        expect(document.body.innerHTML).toBe(before);
    });
});
