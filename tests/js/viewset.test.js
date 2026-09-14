import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

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
});
