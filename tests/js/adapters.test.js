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

describe("adapters.js", () => {
    beforeEach(() => { document.body.innerHTML = '<div id="m"><div id="d"></div></div><span id="t"></span>'; });
    afterEach(() => { vi.unstubAllGlobals(); delete window.cv; });

    it("defines cv.adapters.modal/tooltip/collapse/alert and cv.bootstrapAdapters", async () => {
        await loadScript("adapters");
        expect(typeof window.cv.bootstrapAdapters).toBe("function");
        for (const name of ["modal", "tooltip", "collapse", "alert"]) expect(window.cv.adapters[name]).toBeDefined();
        expect(typeof window.cv.adapters.alert.close).toBe("function");
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
