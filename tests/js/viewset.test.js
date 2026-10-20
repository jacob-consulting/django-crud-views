import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import $ from "jquery";
import { loadScript, nav } from "./helpers/load.js";

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

    describe("data-cv-cancel-url", () => {
        it("navigates to the cancel url instead of following the href", () => {
            document.body.innerHTML = `<a href="/wrong/" data-cv-cancel-url="/books/">cancel</a>`;
            const event = new MouseEvent("click", { bubbles: true, cancelable: true });
            document.querySelector("a").dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
            expect(nav.href).toBe("/books/");
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
