import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { loadScript } from "./helpers/load.js";
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

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

function change(checkbox, checked) {
    checkbox.checked = checked;
    checkbox.dispatchEvent(new Event("change", { bubbles: true }));
}

function nestedFixture() {
    document.body.innerHTML = `<form><input type="checkbox" name="outer" checked>
        <div cv-data-toggle-group cv-data-toggle-field="outer">
            <input type="checkbox" name="inner" checked>
            <div cv-data-toggle-group cv-data-toggle-field="inner">
                <input name="value" value="unsaved"><input name="baseline" disabled>
            </div>
        </div></form>`;
    wire();
    return Object.fromEntries(["outer", "inner", "value", "baseline"].map(name => [name, document.getElementsByName(name)[0]]));
}

describe("conditional disabled ownership", () => {
    beforeAll(async () => { await loadScript("toggle"); });

    it.each(["inner-first", "outer-first"])("composes nested owners in %s order and retains baseline", order => {
        const { outer, inner, value, baseline } = nestedFixture();
        const first = order === "inner-first" ? inner : outer;
        const second = first === inner ? outer : inner;
        change(first, false);
        change(second, false);
        change(first, true);
        expect(value.disabled).toBe(true);
        globalThis.cv.initConditional(document);
        change(second, true);
        expect(value.disabled).toBe(false);
        expect(baseline.disabled).toBe(true);
        expect(value.value).toBe("unsaved");
    });

    it("preserves same-value external disabled writes before synchronous resync", () => {
        const { outer, value } = nestedFixture();
        change(outer, false);
        value.disabled = true; // Same property value still expresses an independent owner.
        change(outer, true); // Must drain records before this synchronous transition.
        expect(value.disabled).toBe(true);
        change(outer, false);
        value.disabled = false;
        globalThis.cv.initConditional(document);
        expect(value.disabled).toBe(true);
        change(outer, true);
        expect(value.disabled).toBe(false);
    });

    it("reacts to external attribute changes while active or inactive", async () => {
        const { outer, value } = nestedFixture();
        value.setAttribute("disabled", "");
        await Promise.resolve();
        expect(value.disabled).toBe(true);
        value.removeAttribute("disabled");
        await Promise.resolve();
        expect(value.disabled).toBe(false);
        change(outer, false);
        value.removeAttribute("disabled");
        await Promise.resolve();
        expect(value.disabled).toBe(true);
        change(outer, true);
        expect(value.disabled).toBe(false);
    });

    it("disables custom native actions but preserves values, files, management and native fieldsets", () => {
        const { group, checkbox } = fixture();
        group.insertAdjacentHTML("beforeend", `<input type="file" name="upload">
            <button type="button">Custom Add</button><button type="button">Delete</button>
            <button type="button" disabled>Reorder</button><fieldset disabled><input name="native" value="keep"></fieldset>
            <input type="hidden" name="rows-INITIAL_FORMS" value="1">
            <input type="hidden" name="rows-MIN_NUM_FORMS" value="0">
            <input type="hidden" name="rows-MAX_NUM_FORMS" value="1000" disabled>`);
        const title = group.querySelector("[name=title]");
        title.value = "unsaved text";
        const upload = group.querySelector("[type=file]");
        const files = upload.files;
        wire();
        change(checkbox, false);
        expect([...group.querySelectorAll("button")].every(button => button.disabled)).toBe(true);
        const data = new FormData(checkbox.form);
        expect([...data.keys()]).toEqual(expect.arrayContaining(["book-None-0-TOTAL_FORMS", "rows-INITIAL_FORMS", "rows-MIN_NUM_FORMS"]));
        expect(data.has("rows-MAX_NUM_FORMS")).toBe(false);
        expect(data.has("title")).toBe(false);
        change(checkbox, true);
        expect([...group.querySelectorAll("button")].map(button => button.disabled)).toEqual([false, false, true]);
        expect(title.value).toBe("unsaved text");
        expect(upload.files).toBe(files);
        const activeData = new FormData(checkbox.form);
        expect(activeData.get("title")).toBe("unsaved text");
        expect(activeData.has("native")).toBe(false);
        expect(group.querySelector("fieldset").disabled).toBe(true);
    });

    it("captures new descendants without capturing temporary disabled state", () => {
        const { outer, value } = nestedFixture();
        change(outer, false);
        value.after(document.createElement("textarea"));
        globalThis.cv.initConditional(value.parentElement);
        expect(value.nextElementSibling.disabled).toBe(true);
        change(outer, true);
        expect(value.disabled).toBe(false);
        expect(value.nextElementSibling.disabled).toBe(false);
    });
});

describe("conditional reset and focus lifecycle", () => {
    beforeAll(async () => { await loadScript("toggle"); });
    afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });

    it("resynchronizes native reset only after the task and only in its owning form", async () => {
        vi.useFakeTimers();
        const { group, checkbox } = fixture({ checked: false });
        const form = checkbox.form;
        form.insertAdjacentHTML("beforeend", `<button type="reset">Reset</button>`);
        form.insertAdjacentHTML("afterend", `<form><input type="checkbox" name="active" checked>
            <div cv-data-toggle-group cv-data-toggle-field="active"><input name="other"></div></form>`);
        wire();
        change(checkbox, true);
        group.querySelector("[name=title]").value = "unsaved";
        const other = document.getElementsByName("other")[0];
        document.querySelectorAll("[name=active]")[1].checked = false; // No change event in other form.
        form.querySelector("[type=reset]").click();
        expect(checkbox.checked).toBe(false); // Native reset already ran.
        expect(group.style.display).toBe("");
        await Promise.resolve();
        expect(group.style.display).toBe(""); // A microtask must not synchronize it.
        await vi.runAllTimersAsync();
        expect(group.style.display).toBe("none");
        expect(group.querySelector("[name=title]").disabled).toBe(true);
        expect(group.querySelector("[name=title]").value).toBe("");
        expect(other.disabled).toBe(false);
        expect(group.querySelector("[name$=-TOTAL_FORMS]").value).toBe("2");
    });

    it.each(["form", "document"])("honors later reset cancellation at %s", async where => {
        vi.useFakeTimers();
        const { group, checkbox } = fixture({ checked: false });
        wire();
        change(checkbox, true);
        group.querySelector("[name=title]").value = "unsaved";
        const target = where === "form" ? checkbox.form : document;
        target.addEventListener("reset", event => event.preventDefault(), { once: true });
        checkbox.form.reset();
        await vi.runAllTimersAsync();
        expect(checkbox.checked).toBe(true);
        expect(group.style.display).toBe("");
        expect(group.querySelector("[name=title]").disabled).toBe(false);
        expect(group.querySelector("[name=title]").value).toBe("unsaved");
    });

    it("restores checked defaults without releasing independent disables or duplicating reset handlers", async () => {
        vi.useFakeTimers();
        const { group, checkbox } = fixture();
        const form = checkbox.form;
        const spy = vi.spyOn(form, "addEventListener");
        const title = group.querySelector("[name=title]");
        title.disabled = true;
        wire();
        globalThis.cv.initConditional(form);
        expect(spy.mock.calls.filter(([type]) => type === "reset")).toHaveLength(1);
        change(checkbox, false);
        form.reset();
        expect(checkbox.checked).toBe(true);
        expect(group.style.display).toBe("none");
        await vi.runAllTimersAsync();
        expect(group.style.display).toBe("");
        expect(title.disabled).toBe(true);
        expect(group.querySelector("select").disabled).toBe(false);
    });

    function visibleGeometry() {
        vi.spyOn(HTMLElement.prototype, "getClientRects").mockReturnValue([{}]);
    }

    it("returns stranded focus to the controlling checkbox without stealing outside focus", () => {
        visibleGeometry();
        const { group, checkbox } = fixture();
        wire();
        group.querySelector("input").focus();
        change(checkbox, false);
        expect(document.activeElement).toBe(checkbox);
        change(checkbox, true);
        const outside = document.createElement("button");
        document.body.append(outside);
        outside.focus();
        change(checkbox, false);
        expect(document.activeElement).toBe(outside);
    });

    it("uses the nearest usable ancestor toggle when an inner target is hidden", () => {
        visibleGeometry();
        const { outer, inner, value } = nestedFixture();
        value.focus();
        outer.checked = false;
        change(inner, false);
        expect(document.activeElement).toBe(outer);
    });

    it.each(["hidden", "inert", "aria-hidden", "aria-disabled", "disabled", "failed-focus"])("rejects %s toggle and focuses its visible in-modal form", reason => {
        visibleGeometry();
        const { group, checkbox } = fixture();
        const form = checkbox.form;
        const modal = document.createElement("div");
        modal.id = "cv-modal";
        form.before(modal);
        modal.append(form);
        const wrapper = document.createElement("div");
        checkbox.before(wrapper);
        wrapper.append(checkbox);
        if (reason === "failed-focus") vi.spyOn(checkbox, "focus").mockImplementation(() => {});
        else if (reason === "disabled") checkbox.disabled = true;
        else wrapper.setAttribute(reason, reason.startsWith("aria-") ? "true" : "");
        wire();
        group.querySelector("input").focus();
        change(checkbox, false);
        expect(document.activeElement).toBe(form);
        expect(form.getAttribute("tabindex")).toBe("-1");
        const button = document.createElement("button");
        form.append(button);
        button.focus();
        expect(form.hasAttribute("tabindex")).toBe(false);
    });

    it("does not focus a hidden initial modal shell and preserves existing fallback tabindex", () => {
        visibleGeometry();
        const { group, checkbox } = fixture();
        const form = checkbox.form;
        form.setAttribute("tabindex", "0");
        checkbox.hidden = true;
        const shell = document.createElement("div");
        shell.setAttribute("aria-hidden", "true");
        form.before(shell);
        shell.append(form);
        wire();
        group.querySelector("input").focus();
        const active = document.activeElement;
        change(checkbox, false);
        expect(document.activeElement).toBe(active);
        expect(form.getAttribute("tabindex")).toBe("0");
        shell.removeAttribute("aria-hidden");
        change(checkbox, true);
        group.querySelector("input").focus();
        change(checkbox, false);
        expect(document.activeElement).toBe(form);
        expect(form.getAttribute("tabindex")).toBe("0");
    });

    it("starts immediately when a script loads after DOMContentLoaded", async () => {
        const dom = new JSDOM(`<form><input type="checkbox" name="late">
            <div cv-data-toggle-group cv-data-toggle-field="late"><input name="value"></div></form>`, { runScripts: "outside-only" });
        try {
            await new Promise(resolve => dom.window.addEventListener("load", resolve, { once: true }));
            dom.window.eval(readFileSync("src/crud_views/static/crud_views/js/toggle.js", "utf8"));
            expect(dom.window.document.querySelector("[cv-data-toggle-group]").style.display).toBe("none");
        } finally { dom.window.close(); }
    });

    it("disposes modal observation and handlers on unload, then permits explicit reuse", async () => {
        const { group, checkbox } = fixture({ checked: false });
        const form = checkbox.form;
        const modal = document.createElement("div");
        form.before(modal);
        modal.append(form);
        wire();
        modal.dispatchEvent(new CustomEvent("cv:modal:unload", { bubbles: true }));
        form.remove();
        group.querySelector("input").disabled = false;
        await Promise.resolve();
        expect(group.querySelector("input").disabled).toBe(false);
        change(checkbox, true);
        expect(group.style.display).toBe("none");
        modal.append(form);
        globalThis.cv.initConditional(form);
        expect(group.style.display).toBe("");
        expect(group.querySelector("input").disabled).toBe(false);
    });

    it("recaptures independent changes made while modal content was disposed", () => {
        const { group, checkbox } = fixture({ checked: false });
        wire();
        const form = checkbox.form;
        form.dispatchEvent(new CustomEvent("cv:modal:unload", { bubbles: true }));
        const title = group.querySelector("[name=title]");
        title.disabled = true;
        checkbox.checked = true;
        globalThis.cv.initConditional(form);
        expect(title.disabled).toBe(true);
        expect(group.querySelector("select").disabled).toBe(false);
    });
});

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
