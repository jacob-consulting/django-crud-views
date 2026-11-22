import fs from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

function fakeNamespace() {
    const instance = { show: vi.fn(), hide: vi.fn() };
    const tooltip = { hide: vi.fn(), dispose: vi.fn() };
    const collapse = { toggle: vi.fn() };
    const alert = { close: vi.fn() }; // a no-op close: a present component owns the outcome
    return {
        instance, tooltip, collapse, alert,
        Modal: { getOrCreateInstance: vi.fn(() => instance), getInstance: vi.fn(() => instance) },
        Tooltip: { getOrCreateInstance: vi.fn((el) => ({ el })), getInstance: vi.fn(() => tooltip) },
        Collapse: { getOrCreateInstance: vi.fn(() => collapse) },
        Alert: { getOrCreateInstance: vi.fn(() => alert) },
    };
}

// A Bootstrap-compatible build that ships other components but no Alert (a custom bundle, for instance).
function namespaceWithoutAlert() {
    const ns = fakeNamespace();
    delete ns.Alert;
    return ns;
}

// Two attached frames and a sibling: closing one frame must leave the other two exactly where they were.
function alertFixture() {
    document.body.innerHTML = '<div id="a1" role="alert">one</div><div id="a2" role="alert">two</div><p id="s">kept</p>';
    return ["a1", "a2", "s"].map((id) => document.getElementById(id));
}

function thrownBy(fn) {
    try {
        fn();
    } catch (error) {
        return error;
    }
    return undefined;
}

function publishedAdapterRecipe(marker) {
    const docs = fs.readFileSync("docs/reference/javascript.md", "utf8");
    const token = `<!-- ${marker} -->`;
    expect(docs.split(token)).toHaveLength(2);
    const fence = docs.split(token)[1].match(/^\s*```javascript\n([\s\S]*?)```/);
    expect(fence).not.toBeNull();
    return fence[1];
}

function pageConfig({ namespace = "tabler", prefix = "bs", placements = {context: "bottom"} } = {}) {
    const config = document.createElement("div");
    config.id = "cv-config";
    config.setAttribute("data-js-namespace", namespace);
    config.setAttribute("data-data-prefix", prefix);
    config.setAttribute("data-tooltip-placements", JSON.stringify(placements));
    document.getElementById("cv-config")?.remove();
    document.body.append(config);
    return config;
}

describe("adapters.js", () => {
    beforeEach(() => { document.body.innerHTML = '<div id="m"><div id="d"></div></div><span id="t"></span>'; });
    afterEach(() => { vi.unstubAllGlobals(); delete window.cv; });

    describe("registered tooltip placements", () => {
        let instances, created, globals, Tooltip, adapter;

        beforeEach(async () => {
            await loadScript("adapters");
            instances = new Map();
            created = [];
            Tooltip = {
                getOrCreateInstance: vi.fn((el, options) => {
                    if (!instances.has(el)) {
                        const queued = [];
                        const rawQueue = vi.fn((callback, element, animated) => {
                            queued.push({callback, element, animated});
                            return "queued";
                        });
                        const instance = {
                            queued, rawQueue, _queueCallback: rawQueue,
                            placement: options?.placement ?? el.getAttribute("data-bs-placement"),
                            hide: vi.fn(),
                            dispose: vi.fn(() => {
                                if (instances.get(el) === instance) instances.delete(el);
                            }),
                        };
                        instances.set(el, instance);
                        created.push(instance);
                    }
                    return instances.get(el);
                }),
                getInstance: vi.fn(el => instances.get(el)),
            };
            globals = window;
            vi.stubGlobal("tabler", {Tooltip});
            pageConfig();
            adapter = window.cv.adapters.tooltip;
        });

        it("sets context placement before instance creation", () => {
            const el = document.getElementById("t");
            adapter.init(el, {location: "context"});
            expect(instances.get(el).placement).toBe("bottom");
            expect(Tooltip.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el, {placement: "bottom"});
            expect(el.hasAttribute("data-bs-placement")).toBe(false);
        });

        it.each(["right", ""])("preserves explicit placement %j", placement => {
            const el = document.getElementById("t");
            el.setAttribute("data-bs-placement", placement);
            adapter.init(el, {location: "context"});
            expect(el.hasAttribute("data-bs-placement")).toBe(true);
            expect(instances.get(el).placement).toBe(placement);
            expect(Tooltip.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el);
        });

        it.each(["list", "card", "card-order", "formset", "object-detail", "form", "", undefined])(
            "leaves library placement unchanged for location %j", location => {
                const el = document.getElementById("t");
                if (location === undefined) adapter.init(el);
                else adapter.init(el, {location});
                expect(el.hasAttribute("data-bs-placement")).toBe(false);
                expect(instances.get(el).placement).toBeNull();
                expect(Tooltip.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el);
            },
        );

        it("runs a live queued callback", () => {
            const el = document.getElementById("t"), live = vi.fn();
            adapter.init(el, {location: "context"});
            const instance = instances.get(el);
            expect(instance._queueCallback(live, el, true)).toBe("queued");
            expect(instance.queued[0].element).toBe(el);
            expect(instance.queued[0].animated).toBe(true);
            instance.queued[0].callback();
            expect(live).toHaveBeenCalledOnce();
        });

        it("hides and disposes its own instance without creating during cleanup", () => {
            const el = document.getElementById("t");
            adapter.init(el, {location: "context"});
            const instance = instances.get(el);
            adapter.hide(el);
            expect(instance.hide).toHaveBeenCalledOnce();
            expect(instance.hide.mock.contexts[0]).toBe(instance);
            adapter.dispose(el);
            expect(instance.dispose).toHaveBeenCalledOnce();
            expect(instance.dispose.mock.contexts[0]).toBe(instance);
            expect(instances.has(el)).toBe(false);
            adapter.hide(el);
            adapter.dispose(el);
            expect(instance.hide).toHaveBeenCalledOnce();
            expect(instance.dispose).toHaveBeenCalledOnce();
            expect(Tooltip.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el, {placement: "bottom"});
            expect(created).toHaveLength(1);
        });

        it("suppresses queued callbacks after disposal", () => {
            const el = document.getElementById("t"), stale = vi.fn();
            adapter.init(el, {location: "context"});
            const instance = instances.get(el);
            instance._queueCallback(stale, el, true);
            adapter.dispose(el);
            instance.queued[0].callback();
            expect(stale.mock.calls.length).toBe(0);
        });

        it("suppresses old callbacks after direct replacement and runs replacement work", () => {
            const el = document.getElementById("t"), stale = vi.fn(), live = vi.fn();
            adapter.init(el, {location: "context"});
            const first = instances.get(el);
            first._queueCallback(stale, el, true);
            // Replace the registered identity without disposing the old instance.
            instances.delete(el);
            const replacement = Tooltip.getOrCreateInstance(el);
            expect(replacement).not.toBe(first);
            expect(first.dispose).not.toHaveBeenCalled();
            first.queued[0].callback();
            expect(stale).not.toHaveBeenCalled();
            adapter.init(el, {location: "context"});
            expect(replacement._queueCallback(live, el, false)).toBe("queued");
            expect(replacement.queued[0].element).toBe(el);
            expect(replacement.queued[0].animated).toBe(false);
            replacement.queued[0].callback();
            first.queued[0].callback();
            expect(live).toHaveBeenCalledOnce();
            expect(stale).not.toHaveBeenCalled();
        });

        it.each(["namespace", "component"])("tolerates missing %s and resolves late availability", missing => {
            const el = document.getElementById("t");
            if (missing === "namespace") delete globals.tabler;
            else delete globals.tabler.Tooltip;
            expect(() => adapter.init(el, {location: "context"})).not.toThrow();
            expect(el.hasAttribute("data-bs-placement")).toBe(false);
            expect(Tooltip.getOrCreateInstance).not.toHaveBeenCalled();
            expect(instances.size).toBe(0);
            expect(created).toHaveLength(0);
            globals.tabler ??= {};
            globals.tabler.Tooltip = Tooltip;
            adapter.init(el, {location: "context"});
            expect(instances.get(el).placement).toBe("bottom");
            expect(Tooltip.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el, {placement: "bottom"});
            expect(created).toHaveLength(1);
        });

        it("installs the guard once and reuses the instance on repeated initialization", () => {
            const el = document.getElementById("t"), live = vi.fn();
            adapter.init(el, {location: "context"});
            const instance = instances.get(el), guardedQueue = instance._queueCallback;
            expect(guardedQueue).not.toBe(instance.rawQueue);
            adapter.init(el, {location: "context"});
            expect(instances.get(el)).toBe(instance);
            expect(instances.size).toBe(1);
            expect(created).toHaveLength(1);
            expect(Tooltip.getOrCreateInstance).toHaveBeenCalledTimes(2);
            expect(instance._queueCallback).toBe(guardedQueue);
            expect(instance._queueCallback(live, el, true)).toBe("queued");
            expect(instance.rawQueue).toHaveBeenCalledOnce();
            expect(instance.queued).toHaveLength(1);
            instance.queued[0].callback();
            expect(live).toHaveBeenCalledOnce();
        });
    });

    it.each(["cv-tab-adapter-namespace", "cv-tab-adapter-complete-map"])("published %s supports tab lifecycle without bootstrap", async marker => {
        await loadScript("adapters");
        const code = publishedAdapterRecipe(marker);
        const ns = fakeNamespace();
        const tab = { show: vi.fn(), dispose: vi.fn() };
        ns.Tab = { getOrCreateInstance: vi.fn(() => tab), getInstance: vi.fn(() => tab) };
        const globals = {}; // Deliberately no bootstrap; the provider resolves tabler later.
        new Function("cv", "globalThis", "myModalAdapter", "myTooltipAdapter", "myCollapseAdapter", code)(
            window.cv, globals, ns.Modal, ns.Tooltip, ns.Collapse,
        );
        const adapters = window.cv.adapters, el = document.getElementById("t");
        expect(Object.keys(adapters).sort()).toEqual(["alert", "collapse", "modal", "tab", "tooltip"]);
        adapters.tab.init(el); adapters.tab.dispose(el);
        expect(ns.Tab.getOrCreateInstance).not.toHaveBeenCalled();
        globals.tabler = ns;
        adapters.tab.init(el); adapters.tab.dispose(el);
        expect(ns.Tab.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el);
        expect(ns.Tab.getInstance).toHaveBeenCalledExactlyOnceWith(el);
        expect(tab.dispose).toHaveBeenCalledOnce();
        expect(tab.show).not.toHaveBeenCalled();
        expect(globals.bootstrap).toBeUndefined();
        adapters.alert.close(el);
        expect(ns.alert.close).toHaveBeenCalledOnce();
        if (marker === "cv-tab-adapter-complete-map") {
            expect(adapters.modal).toBe(ns.Modal);
            expect(adapters.tooltip).toBe(ns.Tooltip);
            expect(adapters.collapse).toBe(ns.Collapse);
        } else {
            adapters.modal.show(el); adapters.tooltip.init(el); adapters.collapse.toggle(el);
            expect(ns.instance.show).toHaveBeenCalledOnce();
            expect(ns.Tooltip.getOrCreateInstance).toHaveBeenCalledWith(el);
            expect(ns.collapse.toggle).toHaveBeenCalledOnce();
        }
    });

    it.each(["default", "object", "provider"])("%s tab resolves late components for init and get-only disposal", async kind => {
        await loadScript("adapters");
        let current;
        const object = {};
        const adapter = kind === "default" ? window.cv.adapters.tab
            : window.cv.bootstrapAdapters(kind === "object" ? object : () => current).tab;
        expect(adapter).toBeDefined();
        const el = document.getElementById("t");
        const focus = vi.spyOn(el, "focus");
        adapter.init(el);
        adapter.dispose(el);
        for (let index = 0; index < 2; index++) {
            const instance = { show: vi.fn(), dispose: vi.fn() };
            const Tab = { getOrCreateInstance: vi.fn(() => instance), getInstance: vi.fn(() => instance) };
            current = { Tab };
            object.Tab = Tab;
            window.bootstrap = current;
            adapter.init(el);
            adapter.init(el);
            expect(Tab.getOrCreateInstance).toHaveBeenCalledTimes(2);
            expect(Tab.getOrCreateInstance).toHaveBeenCalledWith(el);
            expect(instance.show).not.toHaveBeenCalled();
            adapter.dispose(el);
            expect(Tab.getInstance).toHaveBeenCalledWith(el);
            expect(instance.dispose).toHaveBeenCalledOnce();
            Tab.getInstance.mockReturnValue(null);
            adapter.dispose(el);
            expect(instance.dispose).toHaveBeenCalledOnce();
            expect(Tab.getOrCreateInstance).toHaveBeenCalledTimes(2);
        }
        expect(focus).not.toHaveBeenCalled();
        focus.mockRestore();
    });

    it.each(["init", "dispose"])("tab %s propagates provider and component errors by identity", async method => {
        await loadScript("adapters");
        const error = new Error("tab failure");
        const el = document.getElementById("t");
        const fail = () => { throw error; };
        for (const ns of [fail, { get Tab() { throw error; } },
            { Tab: { getOrCreateInstance: fail, getInstance: fail } }]) {
            const adapter = window.cv.bootstrapAdapters(ns).tab;
            expect(adapter).toBeDefined();
            expect(thrownBy(() => adapter[method](el))).toBe(error);
        }
        const adapter = window.cv.bootstrapAdapters({ Tab: { getInstance: () => ({ dispose: fail }) } }).tab;
        expect(thrownBy(() => adapter.dispose(el))).toBe(error);
    });

    it("defines cv.adapters.modal/tooltip/collapse/alert and cv.bootstrapAdapters", async () => {
        await loadScript("adapters");
        expect(typeof window.cv.bootstrapAdapters).toBe("function");
        for (const name of ["modal", "tooltip", "collapse", "alert"]) expect(window.cv.adapters[name]).toBeDefined();
        expect(typeof window.cv.adapters.alert.close).toBe("function");
    });

    // Event names follow data-data-prefix on #cv-config (#403); an absent element or attribute means bs.
    const MODAL_EVENT_CASES = [
        ["no #cv-config", () => {}, "bs"],
        ["#cv-config without data-data-prefix", () => pageConfig().removeAttribute("data-data-prefix"), "bs"],
        ["prefix bs", () => pageConfig({prefix: "bs"}), "bs"],
        ["prefix coreui", () => pageConfig({prefix: "coreui"}), "coreui"],
        ["hyphenated prefix", () => pageConfig({prefix: "my-lib"}), "my-lib"],
    ];
    describe.each(MODAL_EVENT_CASES)("modal lifecycle events, %s", (_label, configure, key) => {
        const hide = `hide.${key}.modal`, hidden = `hidden.${key}.modal`;

        it.each(["default", "object", "function"])("%s modal lifecycle waits for its own completed hide and unsubscribes idempotently", async kind => {
            await loadScript("adapters"); configure();
            const adapter = kind === "default" ? window.cv.adapters.modal : window.cv.bootstrapAdapters(kind === "object" ? fakeNamespace() : () => fakeNamespace()).modal;
            const modal = document.getElementById("m"), callback = vi.fn();
            const unsubscribe = adapter.onHidden(modal, callback);
            expect(callback).not.toHaveBeenCalled();
            modal.dispatchEvent(new Event(hide));
            document.getElementById("d").dispatchEvent(new Event(hidden, {bubbles: true}));
            expect(callback).not.toHaveBeenCalled();
            modal.dispatchEvent(new Event(hidden)); expect(callback).toHaveBeenCalledTimes(1);
            unsubscribe(); unsubscribe(); modal.dispatchEvent(new Event(hidden)); expect(callback).toHaveBeenCalledTimes(1);
        });

        it("queues a replacement open during hide and does not deliver the old hidden event to it", async () => {
            await loadScript("adapters"); configure(); const ns = fakeNamespace(), adapter = window.cv.bootstrapAdapters(ns).modal;
            const modal = document.getElementById("m"), first = vi.fn(), second = vi.fn();
            const unsubscribe = adapter.onHidden(modal, first); adapter.show(modal); ns.instance.show.mockClear();
            modal.dispatchEvent(new Event(hide, {cancelable: true})); unsubscribe();
            const stopSecond = adapter.onHidden(modal, second); adapter.show(modal);
            expect(ns.instance.show).not.toHaveBeenCalled();
            modal.dispatchEvent(new Event(hidden));
            expect(first).not.toHaveBeenCalled(); expect(second).not.toHaveBeenCalled(); expect(ns.instance.show).toHaveBeenCalledTimes(1);
            modal.dispatchEvent(new Event(hide)); modal.dispatchEvent(new Event(hidden));
            expect(second).toHaveBeenCalledTimes(1); stopSecond();
        });

        it("cancels pending shows on unsubscribe and handles a later listener preventing hide", async () => {
            await loadScript("adapters"); configure(); const ns = fakeNamespace(), adapter = window.cv.bootstrapAdapters(ns).modal;
            const modal = document.getElementById("m"), callback = vi.fn();
            let stop = adapter.onHidden(modal, callback);
            modal.dispatchEvent(new Event(hide)); stop(); stop = adapter.onHidden(modal, callback);
            adapter.show(modal); stop(); modal.dispatchEvent(new Event(hidden)); expect(ns.instance.show).not.toHaveBeenCalled();
            stop = adapter.onHidden(modal, callback);
            modal.addEventListener(hide, event => event.preventDefault(), {once: true});
            modal.dispatchEvent(new Event(hide, {cancelable: true}));
            adapter.show(modal); await Promise.resolve();
            expect(ns.instance.show).toHaveBeenCalledTimes(1); expect(callback).not.toHaveBeenCalled(); stop();
        });
    });

    it("observes only the registered prefix's modal events", async () => {
        await loadScript("adapters"); pageConfig({prefix: "coreui"});
        const ns = fakeNamespace(), adapter = window.cv.bootstrapAdapters(ns).modal;
        const modal = document.getElementById("m"), callback = vi.fn();
        adapter.onHidden(modal, callback);
        modal.dispatchEvent(new Event("hide.bs.modal"));
        adapter.show(modal);
        expect(ns.instance.show).toHaveBeenCalledTimes(1); // not queued behind another library's hide
        modal.dispatchEvent(new Event("hidden.bs.modal"));
        expect(callback).not.toHaveBeenCalled();
        modal.dispatchEvent(new Event("hide.coreui.modal")); modal.dispatchEvent(new Event("hidden.coreui.modal"));
        expect(callback).toHaveBeenCalledTimes(1);
    });

    it("reads the prefix once per modal element", async () => {
        await loadScript("adapters"); const config = pageConfig({prefix: "coreui"});
        const adapter = window.cv.bootstrapAdapters(fakeNamespace()).modal;
        const first = document.getElementById("m"), second = document.getElementById("t");
        const firstCallback = vi.fn(), secondCallback = vi.fn();
        adapter.onHidden(first, firstCallback);
        config.setAttribute("data-data-prefix", "bs");
        adapter.onHidden(second, secondCallback);
        first.dispatchEvent(new Event("hidden.bs.modal")); expect(firstCallback).not.toHaveBeenCalled();
        first.dispatchEvent(new Event("hidden.coreui.modal")); expect(firstCallback).toHaveBeenCalledTimes(1);
        second.dispatchEvent(new Event("hidden.coreui.modal")); expect(secondCallback).not.toHaveBeenCalled();
        second.dispatchEvent(new Event("hidden.bs.modal")); expect(secondCallback).toHaveBeenCalledTimes(1);
    });

    it("tolerates a present but empty prefix without falling back to bs", async () => {
        await loadScript("adapters"); pageConfig({prefix: ""});
        const ns = fakeNamespace(), adapter = window.cv.bootstrapAdapters(ns).modal;
        const modal = document.getElementById("m"), callback = vi.fn();
        expect(() => adapter.onHidden(modal, callback)).not.toThrow();
        adapter.show(modal); expect(ns.instance.show).toHaveBeenCalledTimes(1);
        modal.dispatchEvent(new Event("hidden.bs.modal")); expect(callback).not.toHaveBeenCalled();
    });

    it("published native-dialog adapter reports only its completed close and cleans up", () => {
        const docs = fs.readFileSync("docs/reference/javascript.md", "utf8").split("## A non-Bootstrap modal")[1].split("## A non-Bootstrap tooltip")[0];
        const code = docs.match(/```javascript\n([\s\S]*?)```/)[1];
        const cv = {adapters: {}}; new Function("cv", code)(cv);
        const dialog = document.createElement("dialog"), child = document.createElement("span"); dialog.append(child); document.body.append(dialog);
        const callback = vi.fn(), unsubscribe = cv.adapters.modal.onHidden(dialog, callback);
        expect(callback).not.toHaveBeenCalled();
        dialog.dispatchEvent(new Event("cancel", {cancelable: true})); child.dispatchEvent(new Event("close", {bubbles: true}));
        expect(callback).not.toHaveBeenCalled();
        dialog.open = true; // A queued close from the previous session arrives after reopening.
        dialog.dispatchEvent(new Event("close")); expect(callback).not.toHaveBeenCalled();
        dialog.open = false;
        dialog.dispatchEvent(new Event("close")); expect(callback).toHaveBeenCalledTimes(1);
        unsubscribe(); unsubscribe(); dialog.dispatchEvent(new Event("close")); expect(callback).toHaveBeenCalledTimes(1);
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

    it("tooltip.hide / dispose drive Tooltip.getInstance and never create an instance", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), t = document.getElementById("t");
        const a = window.cv.bootstrapAdapters(ns);
        a.tooltip.hide(t);
        a.tooltip.dispose(t);
        expect(ns.Tooltip.getInstance).toHaveBeenCalledWith(t);
        expect(ns.tooltip.hide).toHaveBeenCalledTimes(1);
        expect(ns.tooltip.dispose).toHaveBeenCalledTimes(1);
        expect(ns.Tooltip.getOrCreateInstance).not.toHaveBeenCalled();
    });

    it.each([false, true])("tooltip transition callbacks stop after disposal or replacement (placement=%s)", async placement => {
        await loadScript("adapters");
        if (placement) pageConfig();
        const trigger = document.getElementById("t"), queued = [], live = vi.fn();
        let current;
        const first = {
            _queueCallback(callback, element, animated) { queued.push({callback, element, animated}); return "queued"; },
            dispose() { current = null; },
        };
        const Tooltip = {getOrCreateInstance: () => current ??= first, getInstance: () => current};
        const adapter = window.cv.bootstrapAdapters({Tooltip}).tooltip;
        adapter.init(trigger, {location: "context"}); adapter.init(trigger, {location: "context"});
        expect(first._queueCallback(live, trigger, true)).toBe("queued");
        queued[0].callback(); expect(live).toHaveBeenCalledTimes(1);
        expect(queued[0].element).toBe(trigger); expect(queued[0].animated).toBe(true);
        first._queueCallback(live, trigger, true);
        adapter.dispose(trigger); queued[1].callback();
        expect(live).toHaveBeenCalledTimes(1);
        current = {}; queued[1].callback();
        expect(live).toHaveBeenCalledTimes(1);
    });

    it.each([false, true])("live tooltip callback context arguments return and errors are preserved (placement=%s)", async placement => {
        await loadScript("adapters");
        if (placement) pageConfig();
        const trigger = document.getElementById("t"), receiver = {}, calls = [];
        const instance = {_queueCallback(callback, ...args) {
            expect(this).toBe(instance); calls.push(args); return callback.call(receiver, "event", 3);
        }};
        const adapter = window.cv.bootstrapAdapters({Tooltip: {
            getOrCreateInstance: () => instance, getInstance: () => instance,
        }}).tooltip;
        adapter.init(trigger, {location: "context"});
        const result = instance._queueCallback(function(...args) {
            expect(this).toBe(receiver); expect(args).toEqual(["event", 3]); return 7;
        }, trigger, false, "extension");
        expect(result).toBe(7); expect(calls).toEqual([[trigger, false, "extension"]]);
        expect(() => instance._queueCallback(() => {throw Error("live error");}, trigger, true)).toThrow("live error");
    });

    it("tooltip.hide / dispose are silent without an instance and without Tooltip", async () => {
        await loadScript("adapters");
        const ns = fakeNamespace(), t = document.getElementById("t");
        ns.Tooltip.getInstance = vi.fn(() => null);
        const a = window.cv.bootstrapAdapters(ns);
        expect(() => { a.tooltip.hide(t); a.tooltip.dispose(t); }).not.toThrow();
        const none = window.cv.bootstrapAdapters({});
        expect(() => { none.tooltip.hide(t); none.tooltip.dispose(t); }).not.toThrow();
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

    describe("call-time configuration", () => {
        it("reads a late config and changing namespace for every component", async () => {
            await loadScript("adapters");
            const bootstrap = fakeNamespace(), tabler = fakeNamespace(), coreui = fakeNamespace();
            for (const [name, ns] of Object.entries({bootstrap, tabler, coreui})) {
                ns.Tab = {getOrCreateInstance: vi.fn()};
                vi.stubGlobal(name, ns);
            }
            const el = document.getElementById("t"), a = window.cv.adapters;
            const config = pageConfig(); // Added after the adapter script.
            for (const [name, ns] of Object.entries({tabler, coreui})) {
                config.setAttribute("data-js-namespace", name);
                a.modal.show(el); a.tooltip.init(el); a.tab.init(el); a.collapse.toggle(el); a.alert.close(el);
                for (const component of ["Modal", "Tooltip", "Tab", "Collapse", "Alert"]) {
                    expect(ns[component].getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el);
                    expect(bootstrap[component].getOrCreateInstance).not.toHaveBeenCalled();
                }
            }
        });

        it.each(["element", "attribute"])("falls back only for a missing config %s", async missing => {
            await loadScript("adapters");
            vi.stubGlobal("bootstrap", fakeNamespace());
            if (missing === "attribute") pageConfig().removeAttribute("data-js-namespace");
            const el = document.getElementById("t");
            window.cv.adapters.tooltip.init(el);
            expect(window.bootstrap.Tooltip.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el);
        });

        it.each(["tabler", ""])("does not substitute bootstrap for absent selected namespace %j", async namespace => {
            await loadScript("adapters");
            vi.stubGlobal("bootstrap", fakeNamespace());
            vi.stubGlobal(namespace, undefined);
            pageConfig({namespace});
            const el = document.getElementById("t");
            window.cv.adapters.tooltip.init(el, {location: "context"});
            expect(window.bootstrap.Tooltip.getOrCreateInstance).not.toHaveBeenCalled();
            vi.stubGlobal(namespace, fakeNamespace());
            window.cv.adapters.tooltip.init(el, {location: "context"});
            expect(window[namespace].Tooltip.getOrCreateInstance).toHaveBeenCalledExactlyOnceWith(el, {placement: "bottom"});
        });

        it.each(["before", "after"])("preserves a custom tooltip adapter assigned %s load", async when => {
            const tooltip = {init: vi.fn()};
            if (when === "before") window.cv = {adapters: {tooltip}};
            await loadScript("adapters");
            if (when === "after") Object.assign(window.cv.adapters, {tooltip});
            pageConfig();
            const el = document.getElementById("t");
            window.cv.adapters.tooltip.init(el, {location: "context"});
            expect(window.cv.adapters.tooltip).toBe(tooltip);
            expect(tooltip.init).toHaveBeenCalledExactlyOnceWith(el, {location: "context"});
        });

        it.each(["object", "resolver", "default"])("%s provider keeps ownership and prefix-specific placement precedence", async kind => {
            await loadScript("adapters");
            const supplied = fakeNamespace(), selected = fakeNamespace();
            vi.stubGlobal("tabler", selected);
            const adapter = kind === "default" ? window.cv.adapters.tooltip
                : window.cv.bootstrapAdapters(kind === "object" ? supplied : () => supplied).tooltip;
            const provider = kind === "default" ? selected : supplied;
            for (const prefix of ["bs", "coreui"]) {
                pageConfig({prefix});
                for (const explicit of [null, "right", ""]) {
                    const el = document.createElement("button");
                    // The competing prefix must never suppress this theme's registered default.
                    el.setAttribute(`data-${prefix === "bs" ? "coreui" : "bs"}-placement`, "left");
                    if (explicit !== null) el.setAttribute(`data-${prefix}-placement`, explicit);
                    const original = el.outerHTML;
                    provider.Tooltip.getOrCreateInstance.mockClear();
                    adapter.init(el, {location: "context"});
                    expect(provider.Tooltip.getOrCreateInstance.mock.calls).toEqual([
                        explicit === null ? [el, {placement: "bottom"}] : [el],
                    ]);
                    expect(el.outerHTML).toBe(original);
                }
            }
            if (kind !== "default") expect(selected.Tooltip.getOrCreateInstance).not.toHaveBeenCalled();
        });

        it.each([null, "{bad", "null", "[]", '"text"', "3", "true"])("uses library defaults for placements JSON %j", async raw => {
            await loadScript("adapters");
            vi.stubGlobal("tabler", fakeNamespace());
            const config = pageConfig();
            if (raw === null) config.removeAttribute("data-tooltip-placements");
            else config.setAttribute("data-tooltip-placements", raw);
            const el = document.getElementById("t");
            window.cv.adapters.tooltip.init(el, {location: "context"});
            expect(window.tabler.Tooltip.getOrCreateInstance.mock.calls).toEqual([[el]]);
        });

        it.each(["toString", "constructor", "__proto__", "unregistered", undefined])("ignores unmatched/inherited location %j", async location => {
            await loadScript("adapters");
            vi.stubGlobal("tabler", fakeNamespace());
            pageConfig();
            const el = document.getElementById("t");
            window.cv.adapters.tooltip.init(el, {location});
            expect(window.tabler.Tooltip.getOrCreateInstance.mock.calls).toEqual([[el]]);
        });

        it("reads changed placements and prefix on subsequent calls, including a bare location", async () => {
            await loadScript("adapters");
            vi.stubGlobal("tabler", fakeNamespace());
            pageConfig({placements: {"": "left"}}).removeAttribute("data-data-prefix");
            const first = document.createElement("button"), second = document.createElement("button");
            first.setAttribute("data-bs-placement", "");
            second.setAttribute("data-bs-placement", "right");
            window.cv.adapters.tooltip.init(first, {location: ""});
            pageConfig({prefix: "coreui", placements: {"": "auto"}});
            window.cv.adapters.tooltip.init(second, {location: ""});
            expect(window.tabler.Tooltip.getOrCreateInstance.mock.calls).toEqual([[first], [second, {placement: "auto"}]]);
        });

        it.each([false, true])("propagates present provider errors (placement=%s)", async matched => {
            await loadScript("adapters");
            const error = new Error("provider failure");
            vi.stubGlobal("tabler", {Tooltip: {getOrCreateInstance() {throw error;}}});
            pageConfig();
            expect(thrownBy(() => window.cv.adapters.tooltip.init(document.getElementById("t"), {
                location: matched ? "context" : "list",
            }))).toBe(error);
        });
    });

    describe("alert adapter ownership", () => {
        const GLOBALS = ["cv", "bootstrap"];

        // Each case owns its cv object (and therefore its adapter map) before anything is loaded or assigned, so
        // a nested-key change can never land on a shared object; restoring a descriptor alone could not undo that.
        // Only cv/bootstrap are snapshot and restored, so setup.js's $/jQuery stubs are left as they are.
        async function withCaseCv({ cv = {}, bootstrap } = {}, fn) {
            const saved = GLOBALS.map((name) => [name, Object.getOwnPropertyDescriptor(window, name)]);
            try {
                for (const name of GLOBALS) delete window[name];
                window.cv = cv;
                if (bootstrap !== undefined) window.bootstrap = bootstrap;
                await loadScript("adapters");
                await fn(window.cv);
            } finally {
                for (const [name, descriptor] of saved) {
                    if (descriptor) Object.defineProperty(window, name, descriptor);
                    else delete window[name];
                }
            }
        }

        it("removes exactly the supplied frame when no bootstrap global exists", async () => {
            await withCaseCv({}, (cv) => {
                const [a1, a2, s] = alertFixture();
                cv.adapters.alert.close(a1);
                expect(a1.isConnected).toBe(false);
                expect(a2.isConnected).toBe(true);
                expect(s.isConnected).toBe(true);
            });
        });

        it.each([
            ["null", null],
            ["undefined", undefined],
            ["an empty object", {}],
            ["a callback returning null", () => null],
            ["a callback returning undefined", () => undefined],
        ])("removes exactly the supplied frame for %s as the namespace", async (_label, ns) => {
            await withCaseCv({}, (cv) => {
                const [a1, a2, s] = alertFixture();
                cv.bootstrapAdapters(ns).alert.close(a2);
                expect(a2.isConnected).toBe(false);
                expect(a1.isConnected).toBe(true);
                expect(s.isConnected).toBe(true);
            });
        });

        it("removes the frame for a build without the alert component and touches no other component", async () => {
            await withCaseCv({}, (cv) => {
                const ns = namespaceWithoutAlert();
                const [a1, a2, s] = alertFixture();
                cv.bootstrapAdapters(ns).alert.close(a1);
                expect(a1.isConnected).toBe(false);
                expect(a2.isConnected).toBe(true);
                expect(s.isConnected).toBe(true);
                for (const name of ["Modal", "Tooltip", "Collapse"]) {
                    expect(ns[name].getOrCreateInstance).not.toHaveBeenCalled();
                }
            });
        });

        it("hands the frame to a present Alert component of an explicit object namespace", async () => {
            await withCaseCv({}, (cv) => {
                const ns = fakeNamespace();
                const [a1, a2, s] = alertFixture();
                cv.bootstrapAdapters(ns).alert.close(a1);
                expect(ns.Alert.getOrCreateInstance).toHaveBeenCalledTimes(1);
                expect(ns.Alert.getOrCreateInstance.mock.calls[0]).toEqual([a1]);
                expect(ns.Alert.getOrCreateInstance.mock.calls[0][0]).toBe(a1);
                expect(ns.alert.close).toHaveBeenCalledTimes(1);
                // the fake's close is a no-op: the component, not the adapter, decides whether the frame goes
                expect(a1.isConnected).toBe(true);
                expect(a2.isConnected).toBe(true);
                expect(s.isConnected).toBe(true);
            });
        });

        it("resolves a changing callback namespace on every call of the same adapter", async () => {
            await withCaseCv({}, (cv) => {
                let current = null;
                const adapter = cv.bootstrapAdapters(() => current).alert;
                const [a1, a2] = alertFixture();

                adapter.close(a1); // nothing resolved yet: fallback
                expect(a1.isConnected).toBe(false);

                const first = fakeNamespace();
                current = first;
                adapter.close(a2);
                expect(first.Alert.getOrCreateInstance).toHaveBeenCalledWith(a2);
                expect(first.alert.close).toHaveBeenCalledTimes(1);
                expect(a2.isConnected).toBe(true);

                const second = fakeNamespace();
                current = second;
                adapter.close(a2);
                expect(second.Alert.getOrCreateInstance).toHaveBeenCalledWith(a2);
                expect(second.alert.close).toHaveBeenCalledTimes(1);
                expect(first.alert.close).toHaveBeenCalledTimes(1);
                expect(a2.isConnected).toBe(true);

                current = namespaceWithoutAlert();
                adapter.close(a2);
                expect(a2.isConnected).toBe(false);
                expect(second.alert.close).toHaveBeenCalledTimes(1);
            });
        });

        it("uses a bootstrap global assigned or replaced after the defaults were built", async () => {
            await withCaseCv({}, (cv) => {
                const adapter = cv.adapters.alert; // built once, before any global exists
                const [a1, a2, s] = alertFixture();

                adapter.close(a1);
                expect(a1.isConnected).toBe(false);

                const late = fakeNamespace();
                window.bootstrap = late;
                adapter.close(a2);
                expect(cv.adapters.alert).toBe(adapter);
                expect(late.Alert.getOrCreateInstance).toHaveBeenCalledTimes(1);
                expect(late.Alert.getOrCreateInstance.mock.calls[0][0]).toBe(a2);
                expect(late.alert.close).toHaveBeenCalledTimes(1);
                expect(a2.isConnected).toBe(true);

                const replacement = fakeNamespace();
                window.bootstrap = replacement;
                adapter.close(a2);
                expect(replacement.alert.close).toHaveBeenCalledTimes(1);
                expect(late.alert.close).toHaveBeenCalledTimes(1);
                expect(a2.isConnected).toBe(true);
                expect(s.isConnected).toBe(true);
            });
        });

        it("keeps a preassigned alert adapter by identity and fills the other defaults", async () => {
            const custom = { close: vi.fn() };
            const preassigned = { adapters: { alert: custom } };
            await withCaseCv({ cv: preassigned, bootstrap: fakeNamespace() }, (cv) => {
                expect(cv).toBe(preassigned);
                expect(cv.adapters.alert).toBe(custom);
                for (const name of ["modal", "tooltip", "collapse"]) expect(cv.adapters[name]).toBeDefined();
                expect(typeof cv.adapters.modal.show).toBe("function");
                const [a1] = alertFixture();
                cv.adapters.alert.close(a1);
                expect(custom.close).toHaveBeenCalledTimes(1);
                expect(custom.close.mock.calls[0][0]).toBe(a1);
                expect(window.bootstrap.Alert.getOrCreateInstance).not.toHaveBeenCalled();
                expect(a1.isConnected).toBe(true);
            });
        });

        it("leaves the frame attached when a present component's close does nothing", async () => {
            const ns = fakeNamespace();
            await withCaseCv({ bootstrap: ns }, (cv) => {
                const [a1, a2, s] = alertFixture();
                expect(() => cv.adapters.alert.close(a1)).not.toThrow();
                expect(ns.Alert.getOrCreateInstance.mock.calls[0][0]).toBe(a1);
                expect(ns.alert.close).toHaveBeenCalledTimes(1);
                expect([a1, a2, s].every((el) => el.isConnected)).toBe(true);
            });
        });

        it.each([
            ["instance lookup", (ns, error) => { ns.Alert.getOrCreateInstance = vi.fn(() => { throw error; }); }],
            ["close", (ns, error) => { ns.alert.close = vi.fn(() => { throw error; }); }],
        ])("surfaces the original error from a present component's %s and keeps the frame", async (_label, arm) => {
            const ns = fakeNamespace();
            const error = new Error("component failure");
            arm(ns, error);
            const consoleError = vi.spyOn(console, "error");
            const consoleWarn = vi.spyOn(console, "warn");
            try {
                await withCaseCv({ bootstrap: ns }, (cv) => {
                    const [a1, a2, s] = alertFixture();
                    expect(thrownBy(() => cv.adapters.alert.close(a1))).toBe(error);
                    expect(ns.Alert.getOrCreateInstance).toHaveBeenCalledWith(a1);
                    // a throwing component is not "absent": no fallback removal follows the error
                    expect([a1, a2, s].every((el) => el.isConnected)).toBe(true);
                    expect(consoleError).not.toHaveBeenCalled();
                    expect(consoleWarn).not.toHaveBeenCalled();
                });
            } finally {
                consoleError.mockRestore();
                consoleWarn.mockRestore();
            }
        });

        it("repeats the missing-component fallback harmlessly on the same detached element", async () => {
            await withCaseCv({}, (cv) => {
                const [a1, a2, s] = alertFixture();
                cv.adapters.alert.close(a1);
                expect(a1.isConnected).toBe(false);
                expect(() => cv.adapters.alert.close(a1)).not.toThrow();
                expect(a1.isConnected).toBe(false);
                expect(a2.isConnected).toBe(true);
                expect(s.isConnected).toBe(true);
                expect(document.body.children).toHaveLength(2);
            });
        });

        it("hands every repeated close of an attached frame to a present no-op component", async () => {
            const ns = fakeNamespace();
            await withCaseCv({ bootstrap: ns }, (cv) => {
                const [a1] = alertFixture();
                cv.adapters.alert.close(a1);
                cv.adapters.alert.close(a1);
                // no core de-duplication or teardown: each call reaches the component with the same frame
                expect(ns.Alert.getOrCreateInstance).toHaveBeenCalledTimes(2);
                expect(ns.Alert.getOrCreateInstance.mock.calls.map(([el]) => el)).toEqual([a1, a1]);
                expect(ns.alert.close).toHaveBeenCalledTimes(2);
                expect(a1.isConnected).toBe(true);
            });
        });
    });
});
