import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";

function fixture({ field = "active", checked = true, checkboxName = field } = {}) {
    document.body.innerHTML = `
        <form>
            <input type="checkbox" name="${checkboxName}" ${checked ? "checked" : ""}>
            <div cv-data-toggle-group cv-data-toggle-field="${field}">
                <input type="text" name="title">
                <select name="genre"></select>
                <textarea name="notes"></textarea>
                <input type="hidden" name="book-None-0-TOTAL_FORMS" value="2">
            </div>
        </form>`;
    return {
        group: document.querySelector("[cv-data-toggle-group]"),
        checkbox: document.querySelector("input[type=checkbox]"),
    };
}

function wire() {
    document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
}

describe("toggle.js", () => {
    beforeAll(async () => {
        await loadScript("toggle");
    });

    beforeEach(() => {
        document.body.innerHTML = "";
    });

    it("keeps a group with a checked toggle visible and enabled", () => {
        const { group } = fixture({ checked: true });
        wire();
        expect(group.style.display).toBe("");
        expect(group.querySelector("[name=title]").disabled).toBe(false);
    });

    it("hides and disables a group whose toggle is unchecked", () => {
        const { group } = fixture({ checked: false });
        wire();
        expect(group.style.display).toBe("none");
        expect(group.querySelector("[name=title]").disabled).toBe(true);
        expect(group.querySelector("[name=genre]").disabled).toBe(true);
        expect(group.querySelector("[name=notes]").disabled).toBe(true);
    });

    it("keeps management-form hidden inputs enabled even when the group is off", () => {
        const { group } = fixture({ checked: false });
        wire();
        expect(group.querySelector("[name$=-TOTAL_FORMS]").disabled).toBe(false);
    });

    it("reacts to checkbox change in both directions", () => {
        const { group, checkbox } = fixture({ checked: true });
        wire();
        checkbox.click();
        expect(group.style.display).toBe("none");
        expect(group.querySelector("[name=title]").disabled).toBe(true);
        checkbox.click();
        expect(group.style.display).toBe("");
        expect(group.querySelector("[name=title]").disabled).toBe(false);
    });

    it("finds the checkbox by its exact bound name", () => {
        const { group } = fixture({ field: "book-None-0-active", checked: false });
        wire();
        expect(group.style.display).toBe("none");
    });

    it("scopes the checkbox lookup to the nearest form", () => {
        document.body.innerHTML = `
            <form id="a"><input type="checkbox" name="active" checked></form>
            <form id="b">
                <input type="checkbox" name="active">
                <div cv-data-toggle-group cv-data-toggle-field="active">
                    <input type="text" name="title">
                </div>
            </form>`;
        wire();
        const group = document.querySelector("[cv-data-toggle-group]");
        expect(group.style.display).toBe("none");
        document.querySelector("#a input").click();
        expect(group.style.display).toBe("none");
    });

    it("leaves a group without a matching checkbox untouched", () => {
        document.body.innerHTML = `
            <div cv-data-toggle-group cv-data-toggle-field="nope">
                <input type="text" name="title">
            </div>`;
        expect(() => wire()).not.toThrow();
        const group = document.querySelector("[cv-data-toggle-group]");
        expect(group.style.display).toBe("");
        expect(group.querySelector("[name=title]").disabled).toBe(false);
    });

    it("wires groups injected into the modal via cv:modal:loaded", () => {
        document.body.innerHTML = `<div id="cv-modal-content"></div>`;
        const content = document.getElementById("cv-modal-content");
        content.innerHTML = `
            <form>
                <input type="checkbox" name="active">
                <div cv-data-toggle-group cv-data-toggle-field="active">
                    <input type="text" name="title">
                </div>
            </form>`;
        content.dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
        expect(content.querySelector("[cv-data-toggle-group]").style.display).toBe("none");
    });

    it("wires groups in a formset row added via cv:formset:row-added", () => {
        document.body.innerHTML = `
            <form>
                <input type="checkbox" name="active">
                <div class="cv-formset-row"></div>
            </form>`;
        const row = document.querySelector(".cv-formset-row");
        row.innerHTML = `
            <div cv-data-toggle-group cv-data-toggle-field="active">
                <input type="text" name="title">
            </div>`;
        row.dispatchEvent(new CustomEvent("cv:formset:row-added", { bubbles: true }));
        expect(row.querySelector("[cv-data-toggle-group]").style.display).toBe("none");
    });

    it("does not double-bind an already-wired group", () => {
        const { checkbox } = fixture();
        const spy = vi.spyOn(checkbox, "addEventListener");
        wire();
        wire();
        expect(spy.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
    });

    it("does not bind by suffix or to a checkbox owned by another form", () => {
        document.body.innerHTML = `<form id="other"></form><form>
            <input type="checkbox" name="parent-active">
            <input type="checkbox" name="active" form="other">
            <div cv-data-toggle-group cv-data-toggle-field="active"><input name="title"></div>
        </form>`;
        wire();
        expect(document.querySelector("[cv-data-toggle-group]").style.display).toBe("");
        expect(document.querySelector("[name=title]").disabled).toBe(false);
    });

    it("binds sibling and nested row prefixes independently despite shared suffixes", () => {
        const names = ["rows-0-active", "rows-1-active", "rows-1-children-0-active", "other-active"];
        document.body.innerHTML = `<form>${names.map((name, index) => `
            <input type="checkbox" name="${name}" ${index === 0 ? "checked" : ""}>
            <div cv-data-toggle-group cv-data-toggle-field="${name}"><input name="value-${index}"></div>`).join("")}</form>`;
        wire();
        const groups = [...document.querySelectorAll("[cv-data-toggle-group]")];
        expect(groups.map(group => group.style.display)).toEqual(["", "none", "none", "none"]);
        document.getElementsByName(names[2])[0].click();
        expect(groups.map(group => group.style.display)).toEqual(["", "none", "", "none"]);
    });

    it("keeps duplicate exact bindings local and warns without field values", () => {
        document.body.innerHTML = `<form>
            <input type="checkbox" name="active" value="SECRET">
            <input type="checkbox" name="active" checked>
            <div cv-data-toggle-group cv-data-toggle-field="active" style="display: flex"><input name="keep" disabled></div>
            <input type="checkbox" name="valid">
            <div cv-data-toggle-group cv-data-toggle-field="valid"><input name="hide"></div>
        </form><form><input type="checkbox" name="active">
            <div cv-data-toggle-group cv-data-toggle-field="active"><input name="other"></div></form>`;
        const warning = vi.spyOn(console, "warn").mockImplementation(() => {});
        wire();
        const groups = [...document.querySelectorAll("[cv-data-toggle-group]")];
        expect(groups.map(group => group.style.display)).toEqual(["flex", "none", "none"]);
        expect(document.getElementsByName("keep")[0].disabled).toBe(true);
        expect(warning).toHaveBeenCalledTimes(1);
        expect(warning.mock.calls[0].join(" ")).toContain("active");
        expect(warning.mock.calls[0].join(" ")).not.toContain("SECRET");
        warning.mockRestore();
    });

    it("does not let an unresolved nested group bypass its bound ancestor", () => {
        document.body.innerHTML = `<form><input type="checkbox" name="outer">
            <div cv-data-toggle-group cv-data-toggle-field="outer">
                <input type="checkbox" name="inner"><input type="checkbox" name="inner">
                <div cv-data-toggle-group cv-data-toggle-field="inner"><input name="value"></div>
            </div></form>`;
        const warning = vi.spyOn(console, "warn").mockImplementation(() => {});
        wire();
        expect(document.getElementsByName("value")[0].disabled).toBe(true);
        warning.mockRestore();
    });

    it("includes an Element root and retries late checkboxes without duplicate handlers", () => {
        document.body.innerHTML = `<form><div cv-data-toggle-group cv-data-toggle-field="late"><input name="value"></div></form>`;
        const group = document.querySelector("[cv-data-toggle-group]");
        globalThis.cv.initConditional(group);
        expect(group.style.display).toBe("");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.name = "late";
        group.before(checkbox);
        const spy = vi.spyOn(checkbox, "addEventListener");
        globalThis.cv.initConditional(checkbox);
        expect(group.style.display).toBe("none");
        checkbox.checked = true;
        globalThis.cv.initConditional(group);
        expect(group.style.display).toBe("");
        expect(spy.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
    });

    it("supports DocumentFragments and names containing selector punctuation", () => {
        const fragment = document.createDocumentFragment();
        const form = document.createElement("form");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.name = 'prefix["<&]-active';
        const group = document.createElement("div");
        group.setAttribute("cv-data-toggle-group", "");
        group.setAttribute("cv-data-toggle-field", checkbox.name);
        group.innerHTML = '<input name="value">';
        form.append(checkbox, group);
        fragment.append(form);
        globalThis.cv.initConditional(fragment);
        expect(group.style.display).toBe("none");
    });
});
