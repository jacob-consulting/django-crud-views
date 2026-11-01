import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import fs from "node:fs";
import { JSDOM } from "jsdom";
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

        it("parses multi-digit and UUID parent pks with the server's pk grammar", () => {
            const { prefix } = formsetFixture({ pk: "12" });
            const content = document.querySelector(".cv-formset-content");
            const data = JSON.parse(content.getAttribute("cv-data-formset"));
            const INT = String.raw`\d+`;
            const UUID = String.raw`[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`;
            const a = "0a1b2c3d-0000-4000-8000-00000000000a";
            const r = "9f8e7d6c-1111-4111-8111-11111111111b";
            const cases = [
                ["12-0", INT, "12", 0],
                ["5-0-0-12-0", INT, "12", 0],
                ["15-0-3-123-1", INT, "123", 1],
                ["None-0-3-None-0", INT, null, 0],
                [`${a}-0`, UUID, a, 0],
                [`${a}-0-1-${r}-0`, UUID, r, 0],
                [`${a}-0-1-None-0`, UUID, null, 0],
            ];
            for (const [prefixKey, grammar, pk, index] of cases) {
                content.setAttribute("cv-data-formset", JSON.stringify({ ...data, prefix_key: prefixKey, pk: grammar }));
                const fs = new window.cv.XFormset(null, prefix);
                expect([prefixKey, fs.pk, fs.index]).toEqual([prefixKey, pk, index]);
            }
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
            expect(btn.classList.contains("x-danger")).toBe(true);
            expect(btn.classList.contains("x-ctrl")).toBe(false);
            expect(btn.classList.contains("cv-form-ctrl-delete")).toBe(true);

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(del.getAttribute("value")).toBe("0");
            expect(btn.classList.contains("x-ctrl")).toBe(true);
            expect(btn.classList.contains("x-danger")).toBe(false);
        });

        it("delete() keeps a token shared by both class strings in both directions", () => {
            formsetFixture({ deleteClass: "x x-ctrl", deleteDangerClass: "x x-danger" });
            const btn = document.querySelector('button.cv-form-ctrl-delete[cv-data-formset-form-prefix="book-None-0-0"]');

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(btn.classList.contains("x")).toBe(true);
            expect(btn.classList.contains("x-danger")).toBe(true);
            expect(btn.classList.contains("x-ctrl")).toBe(false);

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(btn.classList.contains("x")).toBe(true);
            expect(btn.classList.contains("x-ctrl")).toBe(true);
            expect(btn.classList.contains("x-danger")).toBe(false);
        });

        it("delete() still recolours when one class string is empty", () => {
            formsetFixture({ deleteClass: "" });
            const btn = document.querySelector('button.cv-form-ctrl-delete[cv-data-formset-form-prefix="book-None-0-0"]');
            expect(btn.getAttribute("data-cv-class")).toBe("");

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(btn.classList.contains("x-danger")).toBe(true);

            new window.cv.XForm(null, "book-None-0-0").delete();
            expect(btn.classList.contains("x-danger")).toBe(false);
            expect(btn.classList.contains("cv-form-ctrl-delete")).toBe(true);
        });

        it("delete() without data-cv-class attributes only toggles the input", () => {
            formsetFixture();
            const del = document.querySelector('input[name="book-None-0-0-DELETE"]');
            const btn = document.querySelector('button.cv-form-ctrl-delete[cv-data-formset-form-prefix="book-None-0-0"]');
            btn.removeAttribute("data-cv-class");
            btn.removeAttribute("data-cv-class-danger");
            const before = btn.className;

            expect(() => new window.cv.XForm(null, "book-None-0-0").delete()).not.toThrow();
            expect(del.getAttribute("value")).toBe("1");
            expect(btn.className).toBe(before);
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

            it("dispatches a bubbling cv:formset:row-added event on the inserted row", () => {
                formsetFixture({ rows: 2 });
                const ajax = stubAjax(2);
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                const events = [];
                const listener = (e) => events.push(e);
                document.addEventListener("cv:formset:row-added", listener);
                new window.cv.XForm(ctl, "book-None-0-1").add();
                document.removeEventListener("cv:formset:row-added", listener);
                expect(events).toHaveLength(1);
                expect(events[0].target.getAttribute("cv-data-formset-form-prefix")).toBe("book-None-0-2");
                expect(events[0].detail).toEqual({ prefix: "book-None-0-2", rows: ["book-None-0-2"] });
                ajax.mockRestore();
            });

            it("dispatches no separate event for nested rows inside a new parent row", () => {
                formsetFixture({ rows: 2 });
                const ajax = vi.spyOn($, "ajax").mockImplementation((options) => {
                    const html = rowHtml(2).replace(
                        /<\/div>\s*$/,
                        `<div class="cv-formset-row" cv-data-formset-form-prefix="child-0"></div></div>`,
                    );
                    options.success({ html, rows: ["book-None-0-2", "child-0"] });
                });
                const ctl = { add_form_control_for_new_rows: vi.fn() };
                const targets = [];
                const listener = (e) => targets.push(e.target.getAttribute("cv-data-formset-form-prefix"));
                document.addEventListener("cv:formset:row-added", listener);
                new window.cv.XForm(ctl, "book-None-0-1").add();
                document.removeEventListener("cv:formset:row-added", listener);
                expect(document.querySelector('[cv-data-formset-form-prefix="child-0"]')).not.toBeNull();
                expect(targets).toEqual(["book-None-0-2"]);
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
        it("rejects a custom Add on an edit-only formset at activation", () => {
            formsetFixture({ editOnly: true });
            const row = document.querySelector(".cv-formset-row");
            row.insertAdjacentHTML("beforeend", '<button type="button" class="cv-form-ctrl-add" cv-data-formset-form-prefix="book-None-0-0"></button>');
            const ajax = vi.spyOn($, "ajax").mockImplementation(() => {});
            new window.cv.CrudViewsFormset();
            row.querySelector(".cv-form-ctrl-add").dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
            expect(ajax).not.toHaveBeenCalled();
            ajax.mockRestore();
        });

        it("initializes same-prefix forms repeatedly through automatic page and modal events", () => {
            formsetFixture({ rows: 2 });
            const page = document.querySelector("form");
            const modal = document.createElement("div");
            document.body.append(modal);
            document.dispatchEvent(new Event("DOMContentLoaded"));
            const other = page.cloneNode(true);
            modal.append(other);
            modal.dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
            expect(typeof window.cv.initFormsets).toBe("function");
            for (const root of [document, modal, other, other.querySelector(".cv-formset-content"), other.querySelector("button")]) {
                window.cv.initFormsets(root);
            }
            other.querySelector(".cv-form-ctrl-delete").click();
            other.querySelector(".cv-form-ctrl-down").click();
            expect(page.querySelector('input[name="book-None-0-0-DELETE"]').value).toBe("0");
            expect(other.querySelector('input[name="book-None-0-0-DELETE"]').value).toBe("1");
            expect([...other.querySelectorAll(".cv-formset-row")].map(row => row.getAttribute("cv-data-formset-form-prefix")))
                .toEqual(["book-None-0-1", "book-None-0-0"]);
            const ajax = vi.spyOn($, "ajax").mockImplementation(options => options.success({ html: rowHtml(2), rows: ["book-None-0-2"] }));
            other.querySelector(".cv-form-ctrl-add").click();
            expect(ajax).toHaveBeenCalledTimes(1);
            expect(other.querySelector('input[name="book-None-0-TOTAL_FORMS"]').value).toBe("3");
            expect(page.querySelector('input[name="book-None-0-TOTAL_FORMS"]').value).toBe("2");
            ajax.mockRestore();
        });

        it("blocks disabled, inactive and non-button override actions including synthetic clicks", () => {
            formsetFixture();
            document.dispatchEvent(new Event("DOMContentLoaded"));
            const ajax = vi.spyOn($, "ajax").mockImplementation(() => {});
            const add = document.querySelector(".cv-form-ctrl-add");
            add.disabled = true;
            add.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
            add.disabled = false;
            add.closest("fieldset").disabled = true;
            add.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
            add.closest("fieldset").disabled = false;
            add.closest(".cv-formset-row").hidden = true;
            add.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
            add.closest(".cv-formset-row").hidden = false;
            add.insertAdjacentHTML("afterend", '<a class="cv-form-ctrl-add" cv-data-formset-form-prefix="book-None-0-0">Add</a>');
            add.parentElement.querySelector("a").dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
            add.type = "submit";
            add.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
            expect(ajax).not.toHaveBeenCalled();
            ajax.mockRestore();
        });

        it("rechecks Delete and Reorder capabilities on each activation", () => {
            formsetFixture({ rows: 2 });
            document.dispatchEvent(new Event("DOMContentLoaded"));
            const content = document.querySelector(".cv-formset-content");
            const data = JSON.parse(content.getAttribute("cv-data-formset"));
            content.setAttribute("cv-data-formset", JSON.stringify({ ...data, can_delete: false, can_order: false }));
            document.querySelector(".cv-form-ctrl-delete").click();
            document.querySelector(".cv-form-ctrl-down").click();
            expect(document.querySelector('input[name="book-None-0-0-DELETE"]').value).toBe("0");
            expect([...content.querySelectorAll(".cv-formset-row")].map(row => row.getAttribute("cv-data-formset-form-prefix")))
                .toEqual(["book-None-0-0", "book-None-0-1"]);
            content.setAttribute("cv-data-formset", JSON.stringify({ ...data, can_delete_extra: false }));
            document.querySelector('input[name="book-None-0-INITIAL_FORMS"]').value = "1";
            content.querySelectorAll(".cv-form-ctrl-delete")[1].click();
            expect(document.querySelector('input[name="book-None-0-1-DELETE"]').value).toBe("0");
        });

        it.each(["12", "0a1b2c3d-0000-4000-8000-00000000000a"])("uses exact names and prefixes through deep ancestry with pk %s", pk => {
            const key = "line-items-child-notes-grand-items";
            const opts = { key, pk, rows: 2 };
            formsetFixture(opts);
            const oldPrefix = `${key}-${pk}-0`;
            const prefixKey = `${pk}-0-1-${pk}-0-2-${pk}-0`;
            const prefix = `${key}-${prefixKey}`;
            document.body.innerHTML = document.body.innerHTML.replaceAll(oldPrefix, prefix);
            const page = document.querySelector("form");
            const content = page.querySelector(".cv-formset-content");
            const metadata = JSON.parse(content.getAttribute("cv-data-formset"));
            content.setAttribute("cv-data-formset", JSON.stringify({ ...metadata, prefix_key: prefixKey,
                parent_prefix_key: `${pk}-0-1-${pk}-0-2`, hierarchy: ["line-items", "child-notes", "grand-items"],
                pk: pk.length > 5 ? "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" : "\\d+" }));
            // Near-match management names and suffix-only row fields precede
            // real controls, so a startsWith/endsWith lookup selects the decoy.
            content.insertAdjacentHTML("afterbegin", `<input name="${prefix}-TOTAL_FORMS-extra" value="99">`);
            const row = content.querySelector(".cv-formset-row");
            row.insertAdjacentHTML("afterbegin", `<input name="decoy-${prefix}-0-id" value="decoy"><input name="decoy-${prefix}-0-DELETE" value="1"><input name="decoy-${prefix}-0-ORDER" value="77">`);
            const decoy = row.cloneNode(true);
            decoy.setAttribute("cv-data-formset-prefix", `${prefix}-extra`);
            decoy.setAttribute("cv-data-formset-form-prefix", `${prefix}-0-extra`);
            decoy.querySelectorAll("input").forEach(input => { input.name = `near-${input.name}`; });
            content.prepend(decoy);
            const other = page.cloneNode(true);
            document.body.append(other);
            document.dispatchEvent(new Event("DOMContentLoaded"));
            const ctl = { form: other };
            const fs = new window.cv.XFormset(ctl, prefix);
            expect(fs.pk).toBe(pk);
            expect(fs.rows).toHaveLength(2);
            expect(fs.get_total_forms()).toBe(2);
            const exact = (selector, attr, value) => [...other.querySelectorAll(selector)].find(el => el.getAttribute(attr) === value);
            const button = action => exact(`button.cv-form-ctrl-${action}`, "cv-data-formset-form-prefix", `${prefix}-0`);
            button("delete").click();
            expect(exact("input", "name", `${prefix}-0-DELETE`).value).toBe("1");
            expect([...page.querySelectorAll("input")].find(input => input.name === `${prefix}-0-DELETE`).value).toBe("0");
            button("down").click();
            expect(new window.cv.XFormset(ctl, prefix).rows.toArray().map(el => el.getAttribute("cv-data-formset-form-prefix")))
                .toEqual([`${prefix}-1`, `${prefix}-0`]);
            expect(exact("input", "name", `decoy-${prefix}-0-ORDER`).value).toBe("77");
            const events = [];
            const listener = event => events.push(event);
            document.addEventListener("cv:formset:row-added", listener);
            const ajax = vi.spyOn($, "ajax").mockImplementation(options => options.success({
                html: rowHtml(2, opts).replaceAll(oldPrefix, prefix), rows: [`${prefix}-2`],
            }));
            button("add").click();
            document.removeEventListener("cv:formset:row-added", listener);
            expect(ajax).toHaveBeenCalledTimes(1);
            expect(ajax.mock.calls[0][0].data).toMatchObject({ pk, num: 2, template: "line-items|child-notes|grand-items", formset_parent_prefix_key: `${pk}-0-1-${pk}-0-2` });
            expect(fs.get_total_forms()).toBe(3);
            expect(events).toHaveLength(1);
            expect(events[0].target).toBe(exact(".cv-formset-row", "cv-data-formset-form-prefix", `${prefix}-2`));
            expect(events[0].detail).toEqual({ prefix: `${prefix}-2`, rows: [`${prefix}-2`] });
            expect([...page.querySelectorAll("input")].find(input => input.name === `${prefix}-TOTAL_FORMS`).value).toBe("2");
            expect(exact("input", "name", `${prefix}-TOTAL_FORMS-extra`).value).toBe("99");
            ajax.mockRestore();
        });

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

        it("binds each control of a row added after init exactly once", () => {
            formsetFixture({ rows: 1 });
            const controller = new window.cv.CrudViewsFormset();
            document.querySelector(".cv-formset-row").insertAdjacentHTML("afterend", rowHtml(1));
            controller.add_form_control_for_new_rows(["book-None-0-1"]);

            // one click toggles DELETE once (a double binding would toggle it back)
            document.querySelector('button.cv-form-ctrl-delete[cv-data-formset-form-prefix="book-None-0-1"]').click();
            expect(document.querySelector('input[name="book-None-0-1-DELETE"]').getAttribute("value")).toBe("1");

            document.querySelector('button.cv-form-ctrl-up[cv-data-formset-form-prefix="book-None-0-1"]').click();
            const prefixes = [...document.querySelectorAll(".cv-formset-row")]
                .map((el) => el.getAttribute("cv-data-formset-form-prefix"));
            expect(prefixes).toEqual(["book-None-0-1", "book-None-0-0"]);
        });

        it("delegates remaining native actions when an override omits order buttons", () => {
            formsetFixture({ rows: 1 });
            const controller = new window.cv.CrudViewsFormset();
            // a new row lacking its up/down buttons although the formset is orderable
            document.querySelector(".cv-formset-row").insertAdjacentHTML("afterend", rowHtml(1));
            document.querySelectorAll('[cv-data-formset-form-prefix="book-None-0-1"].cv-form-ctrl-up, '
                + '[cv-data-formset-form-prefix="book-None-0-1"].cv-form-ctrl-down').forEach((el) => el.remove());

            expect(() => controller.add_form_control_for_new_rows(["book-None-0-1"])).not.toThrow();
            document.querySelector('button.cv-form-ctrl-delete[cv-data-formset-form-prefix="book-None-0-1"]').click();
            expect(document.querySelector('input[name="book-None-0-1-DELETE"]').getAttribute("value")).toBe("1");
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
            // An actual controller failure cancels native submit.
            vi.spyOn(controller, "reorder_formsets").mockImplementation(() => { throw new Error("broken reorder"); });
            const event = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(event);
            expect(event.defaultPrevented).toBe(true);
        });
    });

    describe("start-up guard", () => {
        let win;
        const formsetSource = fs.readFileSync("src/crud_views/static/crud_views/js/formset.js", "utf8");
        const jquerySource = fs.readFileSync("node_modules/jquery/dist/jquery.js", "utf8");
        function boot({ ready = "complete", jq = true, empty = false } = {}) {
            formsetFixture();
            win = new JSDOM(empty ? "" : document.body.innerHTML, { runScripts: "outside-only", url: "https://example.test/" }).window;
            Object.defineProperty(win.document, "readyState", { value: ready, configurable: true });
            win.console.error = vi.fn();
            win.console.log = vi.fn();
            if (jq) win.eval(jquerySource);
            win.eval(formsetSource);
            return win;
        }
        function assertLive() {
            win.document.querySelector(".cv-form-ctrl-delete").click();
            expect(win.document.querySelector('input[name="book-None-0-0-DELETE"]').value).toBe("1");
        }
        afterEach(() => win?.close());

        it("starts automatically when executed after the page is ready", () => {
            boot();
            assertLive();
        });
        it("stays silent on a page without formsets", () => {
            boot({ jq: false, empty: true });
            expect(win.console.error).not.toHaveBeenCalled();
        });
        it("reports missing jQuery once and supports an explicit late retry", () => {
            boot({ jq: false });
            win.cv.initFormsets();
            expect(win.console.error).toHaveBeenCalledTimes(1);
            expect(win.console.error.mock.calls[0][0]).toMatch(/jQuery/);
            win.eval(jquerySource);
            win.cv.initFormsets();
            assertLive();
        });
        it("waits for DOMContentLoaded so jQuery can load later", () => {
            boot({ ready: "loading", jq: false });
            expect(win.console.error).not.toHaveBeenCalled();
            win.eval(jquerySource);
            win.document.dispatchEvent(new win.Event("DOMContentLoaded"));
            assertLive();
        });
        it("retries on window load for deferred jQuery", () => {
            boot({ ready: "interactive", jq: false });
            expect(win.console.error).not.toHaveBeenCalled();
            win.eval(jquerySource);
            win.dispatchEvent(new win.Event("load"));
            assertLive();
        });
        it("reports missing jQuery once after the load retry", () => {
            boot({ ready: "interactive", jq: false });
            win.dispatchEvent(new win.Event("load"));
            win.cv.initFormsets();
            expect(win.console.error).toHaveBeenCalledTimes(1);
        });
        it("initializes a DocumentFragment and root formset/control elements", () => {
            boot({ empty: true });
            const fragment = win.document.createDocumentFragment();
            const container = win.document.createElement("div");
            container.innerHTML = document.body.innerHTML;
            fragment.append(container);
            win.cv.initFormsets(fragment);
            win.document.body.append(fragment);
            win.cv.initFormsets(container.querySelector(".cv-formset-content"));
            win.cv.initFormsets(container.querySelector("button"));
            assertLive();
        });
    });
});
