import { beforeAll, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";
import { formsetFixture, rowHtml } from "./helpers/dom.js";

function orderValues() {
    return [...document.querySelectorAll("input[name$=-ORDER]")].map((el) => el.value);
}

describe("formset.js", () => {
    beforeAll(async () => {
        await loadScript("formset");
    });

    describe("XFormset", () => {
        it("parses config, pk and index from the fixture", () => {
            formsetFixture();
            const fs = new window.cv.XFormset(null, "book-None-0");
            expect(fs.prefix).toBe("book-None-0");
            expect(fs.pk).toBeNull();
            expect(fs.index).toBe(0);
            expect(fs.can_order).toBe(true);
            expect(fs.can_delete).toBe(true);
            expect(fs.rows).toHaveLength(2);
        });

        it("parses a concrete parent pk", () => {
            formsetFixture({ pk: "7" });
            const fs = new window.cv.XFormset(null, "book-7-0");
            expect(fs.pk).toBe("7");
            expect(fs.index).toBe(0);
        });

        it("reads and writes the management form", () => {
            formsetFixture({ rows: 2 });
            const fs = new window.cv.XFormset(null, "book-None-0");
            expect(fs.get_total_forms()).toBe(2);
            expect(fs.get_initial_forms()).toBe(2);
            expect(fs.get_min_num_forms()).toBe(0);
            expect(fs.get_max_num_forms()).toBe(1000);
            fs.increment_total_forms();
            expect(fs.get_total_forms()).toBe(3);
        });

        it("renumbers ORDER inputs 1..n in DOM order", () => {
            formsetFixture({ rows: 3 });
            document.querySelectorAll("input[name$=-ORDER]").forEach((el) => (el.value = "9"));
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", "2", "3"]);
        });

        it("blanks ORDER for empty rows", () => {
            formsetFixture({ rows: 3, rowValues: ["a", "", "b"] });
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", "", "2"]);
        });

        it("blanks ORDER for delete-marked rows (hidden DELETE input)", () => {
            formsetFixture({ rows: 3, rowDeleted: [1] });
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", "", "2"]);
        });

        it("blanks ORDER for delete-marked rows (checkbox DELETE input)", () => {
            formsetFixture({ rows: 2 });
            const del = document.querySelector('input[name="book-None-0-1-DELETE"]');
            del.type = "checkbox";
            del.checked = true;
            new window.cv.XFormset(null, "book-None-0").reorder();
            expect(orderValues()).toEqual(["1", ""]);
        });

        it("does nothing when the formset is not orderable", () => {
            formsetFixture({ canOrder: false });
            const fs = new window.cv.XFormset(null, "book-None-0");
            expect(() => fs.reorder()).not.toThrow();
            expect(document.querySelectorAll("input[name$=-ORDER]")).toHaveLength(0);
        });
    });

    describe("XForm", () => {
        it("computes row position facts", () => {
            formsetFixture({ rows: 3 });
            const middle = new window.cv.XForm(null, "book-None-0-1");
            expect(middle.rows_total).toBe(3);
            expect(middle.row_index).toBe(1);
            expect(middle.row_is_first).toBe(false);
            expect(middle.row_is_last).toBe(false);
            expect(middle.row_previous.attr("cv-data-formset-form-prefix")).toBe("book-None-0-0");
            expect(middle.row_next.attr("cv-data-formset-form-prefix")).toBe("book-None-0-2");

            const first = new window.cv.XForm(null, "book-None-0-0");
            expect(first.row_is_first).toBe(true);
            expect(first.row_previous).toBeNull();

            const last = new window.cv.XForm(null, "book-None-0-2");
            expect(last.row_is_last).toBe(true);
            expect(last.row_next).toBeNull();
        });

        it("delete() toggles the hidden DELETE input and button styling", () => {
            formsetFixture();
            const del = document.querySelector('input[name="book-None-0-0-DELETE"]');
            const btn = document.querySelector('button.cv-form-ctrl-delete[cv-data-formset-form-prefix="book-None-0-0"]');

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(del.getAttribute("value")).toBe("1");
            expect(btn.classList.contains("btn-danger")).toBe(true);
            expect(btn.classList.contains("btn-light")).toBe(false);

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(del.getAttribute("value")).toBe("0");
            expect(btn.classList.contains("btn-light")).toBe(true);
        });

        function rowOrderInDom() {
            return [...document.querySelectorAll(".cv-formset-row")]
                .map((el) => el.getAttribute("cv-data-formset-form-prefix"));
        }

        it("up() moves the row before its predecessor and renumbers", () => {
            formsetFixture({ rows: 3 });
            new window.cv.XForm(null, "book-None-0-1").up();
            expect(rowOrderInDom()).toEqual(["book-None-0-1", "book-None-0-0", "book-None-0-2"]);
            expect(document.querySelector('input[name="book-None-0-1-ORDER"]').value).toBe("1");
            expect(document.querySelector('input[name="book-None-0-0-ORDER"]').value).toBe("2");
        });

        it("up() on the first row is a no-op", () => {
            formsetFixture({ rows: 2 });
            new window.cv.XForm(null, "book-None-0-0").up();
            expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-1"]);
        });

        it("down() moves the row after its successor and renumbers", () => {
            formsetFixture({ rows: 3 });
            new window.cv.XForm(null, "book-None-0-1").down();
            expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-2", "book-None-0-1"]);
            expect(document.querySelector('input[name="book-None-0-1-ORDER"]').value).toBe("3");
        });

        it("down() on the last row is a no-op", () => {
            formsetFixture({ rows: 2 });
            new window.cv.XForm(null, "book-None-0-1").down();
            expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-1"]);
        });

        describe("add()", () => {
            function stubAjax(newIndex) {
                return vi.spyOn($, "ajax").mockImplementation((options) => {
                    options.success({ html: rowHtml(newIndex), rows: [`book-None-0-${newIndex}`] });
                });
            }

            it("requests a new row with the formset's coordinates", () => {
                formsetFixture({ rows: 2 });
                const ajax = stubAjax(2);
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                new window.cv.XForm(ctl, "book-None-0-1").add();
                const options = ajax.mock.calls[0][0];
                expect(options.url).toBe("/formset-rows/");
                expect(options.type).toBe("get");
                expect(options.data).toEqual({
                    template: "book",
                    pk: "None",
                    num: 2,
                    formset_parent_prefix_key: "",
                });
                ajax.mockRestore();
            });

            it("appends after the last row, bumps TOTAL_FORMS and wires controls", () => {
                formsetFixture({ rows: 2 });
                const ajax = stubAjax(2);
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                new window.cv.XForm(ctl, "book-None-0-1").add();
                expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-1", "book-None-0-2"]);
                expect(document.querySelector('input[name="book-None-0-TOTAL_FORMS"]').getAttribute("value")).toBe("3");
                expect(ctl.add_form_control_for_new_rows).toHaveBeenCalledWith(["book-None-0-2"]);
                ajax.mockRestore();
            });

            it("inserts before the next row when adding from a middle row", () => {
                formsetFixture({ rows: 2 });
                const ajax = stubAjax(2);
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                new window.cv.XForm(ctl, "book-None-0-0").add();
                expect(rowOrderInDom()).toEqual(["book-None-0-0", "book-None-0-2", "book-None-0-1"]);
                ajax.mockRestore();
            });
        });
    });

    describe("CrudViewsFormset", () => {
        it("initializes on a non-orderable formset without aborting (regression)", () => {
            formsetFixture({ canOrder: false });
            expect(() => new window.cv.CrudViewsFormset()).not.toThrow();
            // delete still works, proving handlers were bound despite missing up/down
            document.querySelector("button.cv-form-ctrl-delete").click();
            expect(document.querySelector('input[name="book-None-0-0-DELETE"]').getAttribute("value")).toBe("1");
        });

        it("initializes on an edit-only formset without an add button", () => {
            formsetFixture({ editOnly: true });
            expect(() => new window.cv.CrudViewsFormset()).not.toThrow();
            document.querySelector("button.cv-form-ctrl-delete").click();
            expect(document.querySelector('input[name="book-None-0-0-DELETE"]').getAttribute("value")).toBe("1");
        });

        it("wires the control buttons to row actions", () => {
            formsetFixture({ rows: 2 });
            new window.cv.CrudViewsFormset();
            document.querySelector('button.cv-form-ctrl-down[cv-data-formset-form-prefix="book-None-0-0"]').click();
            const prefixes = [...document.querySelectorAll(".cv-formset-row")]
                .map((el) => el.getAttribute("cv-data-formset-form-prefix"));
            expect(prefixes).toEqual(["book-None-0-1", "book-None-0-0"]);
        });

        it("reorders all formsets on submit and lets the submit proceed", () => {
            formsetFixture({ rows: 2 });
            new window.cv.CrudViewsFormset();
            document.querySelectorAll("input[name$=-ORDER]").forEach((el) => (el.value = "9"));
            const form = document.querySelector("form.cv-form");
            const event = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(false);
            expect([...document.querySelectorAll("input[name$=-ORDER]")].map((el) => el.value)).toEqual(["1", "2"]);
        });

        it("blocks the submit when reordering fails outright", () => {
            formsetFixture({ rows: 2 });
            const controller = new window.cv.CrudViewsFormset();
            const form = document.querySelector("form.cv-form");
            // make reorder_formsets throw: the controller can no longer find form.cv-form
            form.className = "";
            const event = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
        });
    });
});
