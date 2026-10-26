import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import $ from "jquery";
import { listenerErrors } from "./helpers/errors.js";
import { loadScript, nav } from "./helpers/load.js";

// The Python-proven render of a stock dismissible alert (tests/test1/test_alerts.py owns its bytes); resolved
// from this file's own directory, as load.js resolves the shipped scripts from its own.
const DISMISSIBLE_ALERT_HTML = fs.readFileSync(
    path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../test1/golden/alerts/dismissible.html"),
    "utf-8",
);

function orderForm({ autoSubmit = true } = {}) {
    document.body.innerHTML = `
        <form method="get" id="cv-card-order-form">
            <select name="order" id="cv-order-select"${autoSubmit ? ' data-cv-action="submit-on-change"' : ""}>
                <option value="-name">Name Z-A</option>
                <option value="name">Name A-Z</option>
            </select>
        </form>`;
    const form = document.getElementById("cv-card-order-form");
    const select = document.getElementById("cv-order-select");
    // jsdom does not implement form navigation; observe the call instead
    const submit = vi.fn();
    form.submit = submit;
    return { form, select, submit };
}

function change(select, value) {
    select.value = value;
    select.dispatchEvent(new Event("change", { bubbles: true }));
}

describe("viewset.js", () => {
    beforeAll(async () => {
        await loadScript("viewset");
    });

    beforeEach(() => {
        document.body.innerHTML = "";
    });

    describe("data-cv-action='submit-on-change'", () => {
        it("submits the enclosing form when the select changes", () => {
            const { select, submit } = orderForm();
            change(select, "name");
            expect(submit).toHaveBeenCalledTimes(1);
        });

        it("does nothing for a select without the action attribute", () => {
            const { select, submit } = orderForm({ autoSubmit: false });
            change(select, "name");
            expect(submit).not.toHaveBeenCalled();
        });
    });

    describe("data-cv-action='submit-form'", () => {
        function actionForm({ target = "cv-form-1" } = {}) {
            document.body.innerHTML = `
                <form id="cv-form-1" method="post"></form>
                <button type="button" data-cv-action="submit-form" data-cv-target="${target}">go</button>`;
            const form = document.getElementById("cv-form-1");
            form.requestSubmit = vi.fn();
            return { form, button: document.querySelector("[data-cv-action='submit-form']") };
        }

        it("requestSubmits the target form and prevents the default", () => {
            const { form, button } = actionForm();
            const event = new MouseEvent("click", { bubbles: true, cancelable: true });
            button.dispatchEvent(event);
            expect(form.requestSubmit).toHaveBeenCalledTimes(1);
            expect(event.defaultPrevented).toBe(true);
        });

        it("does nothing when the target does not exist", () => {
            const { form, button } = actionForm({ target: "missing" });
            expect(() => button.click()).not.toThrow();
            expect(form.requestSubmit).not.toHaveBeenCalled();
        });
    });

    it("ignores events whose target is not an element", () => {
        document.body.innerHTML = "";
        for (const type of ["click", "change"]) {
            expect(() => document.dispatchEvent(new Event(type, { bubbles: true }))).not.toThrow();
        }
    });

    describe("data-cv-cancel-url", () => {
        it("navigates to the cancel url instead of following the href", () => {
            document.body.innerHTML = `<a href="/wrong/" data-cv-cancel-url="/books/">cancel</a>`;
            const event = new MouseEvent("click", { bubbles: true, cancelable: true });
            document.querySelector("a").dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
            expect(nav.href).toBe("/books/");
        });
    });

    describe("rendered alert dismissal tracer", () => {
        const GLOBALS = ["cv", "bootstrap"];

        // Fresh real defaults per case: clear only cv/bootstrap so the adapters' preservation merge cannot keep an
        // earlier case's fake, then restore exactly the original descriptors (setup.js's $/jQuery stay untouched).
        async function withFreshDefaults(bootstrap, fn) {
            const saved = GLOBALS.map((name) => [name, Object.getOwnPropertyDescriptor(window, name)]);
            try {
                for (const name of GLOBALS) delete window[name];
                if (bootstrap !== undefined) window.bootstrap = bootstrap;
                await loadScript("adapters");
                document.body.innerHTML = `${DISMISSIBLE_ALERT_HTML}<p id="sibling">kept</p>`;
                await fn();
            } finally {
                for (const [name, descriptor] of saved) {
                    if (descriptor) Object.defineProperty(window, name, descriptor);
                    else delete window[name];
                }
            }
        }

        function clickClose() {
            const control = document.querySelector("[data-cv-alert-dismiss]");
            expect(control).not.toBeNull();
            const frame = control.closest('[role="alert"]');
            expect(frame).not.toBeNull();
            const event = new MouseEvent("click", { bubbles: true, cancelable: true });
            const errors = listenerErrors(() => control.dispatchEvent(event));
            return { frame, event, errors };
        }

        it("delegates to a present Alert component with the nearest frame", async () => {
            const instance = { close: vi.fn() }; // a no-op close: the component owns the outcome
            const Alert = { getOrCreateInstance: vi.fn(() => instance) };
            await withFreshDefaults({ Alert }, () => {
                const { frame, event, errors } = clickClose();
                expect(errors).toEqual([]);
                expect(event.defaultPrevented).toBe(true);
                expect(Alert.getOrCreateInstance).toHaveBeenCalledTimes(1);
                expect(Alert.getOrCreateInstance.mock.calls[0][0]).toBe(frame);
                expect(instance.close).toHaveBeenCalledTimes(1);
                expect(frame.isConnected).toBe(true);
            });
        });

        it("removes the frame when no Alert component is loaded", async () => {
            await withFreshDefaults(undefined, () => {
                const { frame, event, errors } = clickClose();
                expect(errors).toEqual([]);
                expect(event.defaultPrevented).toBe(true);
                expect(frame.isConnected).toBe(false);
                expect(document.querySelector('[role="alert"]')).toBeNull();
                expect(document.getElementById("sibling").isConnected).toBe(true);
            });
        });
    });

    // reloads the script (adds listeners), so keep it last
    it("loads without jQuery", async () => {
        vi.stubGlobal("$", undefined);
        vi.stubGlobal("jQuery", undefined);
        try {
            await expect(loadScript("viewset")).resolves.toBeUndefined();
        } finally {
            vi.stubGlobal("$", $);
            vi.stubGlobal("jQuery", $);
        }
    });
});
