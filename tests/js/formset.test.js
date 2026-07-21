import { beforeAll, describe, expect, it } from "vitest";
import { loadScript } from "./helpers/load.js";
import { formsetFixture } from "./helpers/dom.js";

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
});
