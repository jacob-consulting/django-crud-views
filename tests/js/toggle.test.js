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

function choiceFixture(widget, tokens = ["consumer", "wholesale", "distributor"]) {
    document.body.innerHTML = '<form id="choice-owner"></form><form id="other-owner"></form>';
    const form = document.getElementById("choice-owner");
    const name = 'rows["<&]-0-kind';
    const controls = widget === "select" ? [document.createElement("select")] : tokens.map(() => document.createElement("input"));
    controls.forEach((control, index) => {
        control.name = name;
        if (widget === "select") tokens.forEach(token => control.add(new Option(token, token)));
        else { control.type = "radio"; control.value = tokens[index]; control.defaultChecked = index === 0; }
        form.append(control);
    });
    const groups = [[tokens[0]], tokens.slice(1)].map((values, index) => {
        const group = document.createElement("fieldset");
        group.setAttribute("cv-data-toggle-group", "");
        group.setAttribute("cv-data-toggle-field", name);
        group.setAttribute("cv-data-toggle-values", JSON.stringify(values));
        group.innerHTML = `<input name="value-${index}" value="initial-${index}"><input name="baseline-${index}" disabled>`;
        form.append(group);
        return group;
    });
    const choose = token => {
        const control = widget === "select" ? controls[0] : controls.find(input => input.value === token);
        if (widget === "select") control.value = token;
        else control.checked = true;
        control.dispatchEvent(new Event("change", { bubbles: true }));
    };
    return { form, controls, groups, choose, name, tokens, value: groups[1].querySelector("input") };
}

describe("choice conditional lifecycle", () => {
    beforeAll(async () => { await loadScript("toggle"); });
    afterEach(() => {
        document.querySelectorAll("form").forEach(form => form.dispatchEvent(new CustomEvent("cv:modal:unload", { bubbles: true })));
        vi.useRealTimers(); vi.restoreAllMocks();
    });

    it.each(["select", "radio"].flatMap(widget => [[widget, ["consumer", "wholesale", "distributor"]], [widget, ["0", "1", "2"]]]))(
        "choice membership retains shared and disjoint data for %s %j", (widget, tokens) => {
            const { form, groups, choose, value } = choiceFixture(widget, tokens);
            wire();
            expect(groups.map(group => group.style.display)).toEqual(["", "none"]);
            expect(new FormData(form).has("value-1")).toBe(false);
            choose(tokens[1]); value.value = "unsaved";
            expect(groups.map(group => group.style.display)).toEqual(["none", ""]);
            choose(tokens[2]);
            expect(value.disabled).toBe(false);
            expect(new FormData(form).get("value-1")).toBe("unsaved");
            choose(tokens[0]);
            expect(value.value).toBe("unsaved");
            expect(new FormData(form).has("value-1")).toBe(false);
            choose(tokens[1]);
            expect(new FormData(form).get("value-1")).toBe("unsaved");
            expect(form.querySelector("[name=baseline-1]").disabled).toBe(true);
        });

    it.each(["select", "radio"])("choice ownership includes external %s controls and excludes foreign peers", widget => {
        const { form, controls, groups, choose, name } = choiceFixture(widget);
        const other = document.getElementById("other-owner");
        controls.forEach(control => { control.setAttribute("form", form.id); document.body.append(control); });
        const foreign = controls[0].cloneNode(true); foreign.removeAttribute("form"); other.append(foreign);
        const reassigned = foreign.cloneNode(true); reassigned.setAttribute("form", other.id); form.append(reassigned);
        const suffix = foreign.cloneNode(true); suffix.name = `other-${name}`; form.append(suffix);
        wire(); choose("wholesale");
        expect(groups[1].style.display).toBe("");
        foreign.value = "consumer"; foreign.dispatchEvent(new Event("change", { bubbles: true }));
        expect(groups[1].style.display).toBe("");
    });

    it("radio ownership treats no checked peer as inactive and malformed multiple checked peers as unresolved", () => {
        const { controls, groups } = choiceFixture("radio");
        controls.forEach(control => { control.checked = false; }); wire();
        expect(groups.map(group => group.style.display)).toEqual(["none", "none"]);
        controls.slice(0, 2).forEach(control => Object.defineProperty(control, "checked", { configurable: true, value: true }));
        globalThis.cv.initConditional(document);
        expect(groups.map(group => group.style.display)).toEqual(["none", "none"]);
    });

    it("radio listener rebind compares all members, normalizes matches and releases all old peers", () => {
        const { form, controls, groups, choose, value } = choiceFixture("radio");
        const added = controls.map(control => vi.spyOn(control, "addEventListener"));
        const removed = controls.map(control => vi.spyOn(control, "removeEventListener"));
        wire(); globalThis.cv.initConditional(form);
        groups[1].setAttribute("cv-data-toggle-values", '[ "distributor", "wholesale" ]');
        globalThis.cv.initConditional(form);
        added.forEach(spy => expect(spy.mock.calls.filter(([type]) => type === "change")).toHaveLength(2));
        const replacement = controls[2].cloneNode(); controls[2].replaceWith(replacement);
        globalThis.cv.initConditional(form);
        removed.forEach(spy => expect(spy.mock.calls.filter(([type]) => type === "change")).toHaveLength(2));
        replacement.checked = true; replacement.dispatchEvent(new Event("change", { bubbles: true }));
        expect(value.disabled).toBe(false);
        choose("consumer");
        replacement.checked = true;
        controls[2].dispatchEvent(new Event("change", { bubbles: true }));
        expect(value.disabled).toBe(true); // Detached peer must not resync live controls.
        form.dispatchEvent(new CustomEvent("cv:modal:unload", { bubbles: true }));
        replacement.dispatchEvent(new Event("change", { bubbles: true }));
        expect(groups[1].style.display).toBe("none");
        expect(value.disabled).toBe(false);
        form.dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
        expect(value.disabled).toBe(false);
        expect(groups[1].style.display).toBe("");
    });

    it.each(["select", "radio"])("choice disabled baseline and inactive ancestors compose for %s", widget => {
        const { form, controls, groups, choose, value } = choiceFixture(widget);
        const ancestor = document.createElement("div");
        ancestor.setAttribute("cv-data-toggle-group", ""); ancestor.setAttribute("cv-data-toggle-field", "outer");
        form.insertAdjacentHTML("afterbegin", '<input type="checkbox" name="outer" checked>');
        const outer = form.querySelector("[name=outer]");
        form.append(ancestor); ancestor.append(...groups);
        wire(); value.disabled = true; choose("wholesale"); expect(value.disabled).toBe(true);
        choose("consumer"); value.disabled = false; globalThis.cv.initConditional(form);
        expect(value.disabled).toBe(true);
        controls.forEach(control => { control.disabled = true; });
        choose("wholesale"); expect(value.disabled).toBe(false); // Disabled is not a different value.
        change(outer, false); expect(value.disabled).toBe(true);
        groups[1].setAttribute("cv-data-toggle-values", "bad json"); globalThis.cv.initConditional(form);
        change(outer, true); expect(value.disabled).toBe(false);
        expect(controls.every(control => control.disabled)).toBe(true);
    });

    it.each(["select", "radio"].flatMap(widget => ["form", "document"].map(where => [widget, where])))(
        "choice native reset and later canceled reset for %s at %s", async (widget, where) => {
            vi.useFakeTimers();
            const { form, choose, groups, value } = choiceFixture(widget);
            const other = document.getElementById("other-owner");
            other.innerHTML = '<input type="checkbox" name="active" checked><div cv-data-toggle-group cv-data-toggle-field="active"><input name="other"></div>';
            wire(); choose("wholesale"); value.value = "unsaved";
            other.querySelector("input").checked = false;
            (where === "form" ? form : document).addEventListener("reset", event => event.preventDefault(), { once: true });
            form.reset(); await vi.runAllTimersAsync();
            expect(value.value).toBe("unsaved"); expect(value.disabled).toBe(false);
            form.reset(); expect(groups[1].style.display).toBe("");
            await vi.runAllTimersAsync();
            expect(value.value).toBe("initial-1"); expect(value.disabled).toBe(true);
            expect(other.querySelector("[name=other]").disabled).toBe(false);
        });

    it.each(["select", "radio"].flatMap(widget => ["[]", "{}", "null", "[0]", '[""]', '["a","a"]', "broken"].map(metadata => [widget, metadata])))(
        "malformed choice metadata %s %s preserves last state", (widget, metadata) => {
            const { form, groups, choose, value } = choiceFixture(widget);
            wire(); expect(value.disabled).toBe(true);
            groups[1].setAttribute("cv-data-toggle-values", metadata); globalThis.cv.initConditional(form);
            choose("wholesale"); expect(value.disabled).toBe(true);
            groups[1].setAttribute("cv-data-toggle-values", '["wholesale"]'); globalThis.cv.initConditional(form);
            expect(value.disabled).toBe(false);
        });

    it.each(["select", "radio"].flatMap(widget => ["select", "text", "multiple"].map(invalid => [widget, invalid])))(
        "rejects mixed or duplicate choice controls %s with %s and recovers", (widget, invalid) => {
            const { form, name, choose, value } = choiceFixture(widget);
            wire();
            const extra = document.createElement(invalid === "text" ? "input" : "select");
            extra.name = name; if (invalid === "multiple") extra.multiple = true;
            form.append(extra); globalThis.cv.initConditional(form); choose("wholesale");
            expect(value.disabled).toBe(true);
            extra.remove(); globalThis.cv.initConditional(form); expect(value.disabled).toBe(false);
        });

    it.each(["checked", "peer", "form"])("choice focus recovery chooses usable %s radio target", target => {
        vi.spyOn(HTMLElement.prototype, "getClientRects").mockReturnValue([{}]);
        const { form, controls, groups, choose, value } = choiceFixture("radio");
        wire(); choose("wholesale");
        // Hide the shared group by changing its matches, leaving a checked non-first radio.
        value.focus(); groups[1].setAttribute("cv-data-toggle-values", '["consumer"]');
        if (target !== "checked") controls[1].disabled = true;
        if (target === "form") controls.forEach(control => { control.disabled = true; });
        globalThis.cv.initConditional(form);
        expect(document.activeElement).toBe(target === "checked" ? controls[1] : target === "peer" ? controls[0] : form);
        const outside = document.createElement("button"); document.body.append(outside); outside.focus();
        choose("consumer"); choose("distributor"); expect(document.activeElement).toBe(outside);
    });
});

describe("conditional disabled ownership", () => {
    beforeAll(async () => { await loadScript("toggle"); });

    it("keeps a formerly bound inactive group safe during ambiguity and uniquely recovers", () => {
        const warning = vi.spyOn(console, "warn").mockImplementation(() => {});
        try {
            const { group, checkbox } = fixture({ checked: false });
            const form = checkbox.form;
            const title = group.querySelector("[name=title]");
            title.required = true;
            form.insertAdjacentHTML("beforeend", `<input type="checkbox" name="independent" checked>
                <div cv-data-toggle-group cv-data-toggle-field="independent"><input name="other"></div>`);
            const independent = form.querySelector("[name=independent]");
            const other = form.querySelector("[name=other]");
            globalThis.cv.initConditional(form);
            expect(group.style.display).toBe("none");
            expect(title.disabled).toBe(true);
            expect(form.checkValidity()).toBe(true);
            expect(new FormData(form).has("title")).toBe(false);

            const duplicate = checkbox.cloneNode();
            duplicate.checked = true;
            checkbox.after(duplicate);
            globalThis.cv.initConditional(group);
            expect(warning).toHaveBeenCalledTimes(1);
            expect(group.style.display).toBe("none");
            expect(title.disabled).toBe(true);
            expect(form.checkValidity()).toBe(true);
            expect(new FormData(form).has("title")).toBe(false);
            change(checkbox, true);
            change(duplicate, false);
            change(independent, false);
            expect(other.disabled).toBe(true);
            expect(title.disabled).toBe(true);
            expect(group.style.display).toBe("none");

            checkbox.remove();
            duplicate.checked = true;
            const listener = vi.spyOn(duplicate, "addEventListener");
            independent.focus();
            globalThis.cv.initConditional(duplicate);
            globalThis.cv.initConditional(group);
            expect(listener.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
            expect(document.activeElement).toBe(independent);
            expect(group.style.display).toBe("");
            expect(title.disabled).toBe(false);
            expect(form.checkValidity()).toBe(false);
            title.value = "retained entry";
            expect(new FormData(form).get("title")).toBe("retained entry");
            change(duplicate, false);
            expect(form.checkValidity()).toBe(true);
            expect(new FormData(form).has("title")).toBe(false);
            change(duplicate, true);
            expect(title.value).toBe("retained entry");
            expect(new FormData(form).get("title")).toBe("retained entry");
        } finally { vi.restoreAllMocks(); }
    });

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

describe("unresolved conditional ownership lifecycle", () => {
    beforeAll(async () => { await loadScript("toggle"); });
    afterEach(() => {
        document.querySelectorAll("form").forEach(form => {
            form.dispatchEvent(new CustomEvent("cv:modal:unload", { bubbles: true }));
        });
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    it.each([true, false])("retains a formerly bound %s state across zero, two and one matches", checked => {
        const warning = vi.spyOn(console, "warn").mockImplementation(() => {});
        const { group, checkbox } = fixture({ checked });
        const form = checkbox.form;
        const title = group.querySelector("[name=title]");
        title.value = "unsaved entry";
        form.insertAdjacentHTML("afterend", `<form><input type="checkbox" name="active" checked>
            <div cv-data-toggle-group cv-data-toggle-field="active"><input name="other"></div></form>`);
        const otherToggle = document.querySelectorAll("[name=active]")[1];
        const other = document.querySelector("[name=other]");
        globalThis.cv.initConditional(document);

        checkbox.remove();
        globalThis.cv.initConditional(group);
        expect(group.style.display).toBe(checked ? "" : "none");
        expect(title.disabled).toBe(!checked);
        expect(new FormData(form).has("title")).toBe(checked);
        change(checkbox, !checked); // Detached obsolete listener must have no effect.
        expect(title.disabled).toBe(!checked);
        expect(warning).not.toHaveBeenCalled();

        const replacement = checkbox.cloneNode();
        replacement.checked = !checked;
        const duplicate = replacement.cloneNode();
        form.prepend(replacement, duplicate);
        globalThis.cv.initConditional(replacement);
        expect(warning).toHaveBeenCalledTimes(1);
        change(replacement, checked);
        change(duplicate, !checked);
        change(otherToggle, false);
        expect(other.disabled).toBe(true);
        expect(title.disabled).toBe(!checked);
        expect(group.style.display).toBe(checked ? "" : "none");

        duplicate.remove();
        replacement.checked = !checked;
        const listener = vi.spyOn(replacement, "addEventListener");
        globalThis.cv.initConditional(group);
        globalThis.cv.initConditional(form);
        expect(listener.mock.calls.filter(([type]) => type === "change")).toHaveLength(1);
        expect(group.style.display).toBe(checked ? "none" : "");
        expect(title.disabled).toBe(checked);
        expect(title.value).toBe("unsaved entry");
        expect(other.disabled).toBe(true);
        change(replacement, true);
        expect(new FormData(form).get("title")).toBe("unsaved entry");
    });

    it.each([
        ["inner", true, "inner-first"], ["inner", false, "inner-first"],
        ["inner", true, "outer-first"], ["inner", false, "outer-first"],
        ["outer", true, "inner-first"], ["outer", false, "inner-first"],
        ["outer", true, "outer-first"], ["outer", false, "outer-first"],
    ])("composes frozen %s=%s ownership in %s initialization order", (name, checked, order) => {
        vi.spyOn(console, "warn").mockImplementation(() => {});
        document.body.innerHTML = `<form><input type="checkbox" name="outer" checked>
            <div cv-data-toggle-group cv-data-toggle-field="outer">
                <input type="checkbox" name="inner" checked>
                <div cv-data-toggle-group cv-data-toggle-field="inner">
                    <input name="value" value="unsaved"><input name="baseline" disabled>
                    <button type="button">Add</button><button type="button" disabled>Reorder</button>
                    <input type="hidden" name="rows-TOTAL_FORMS" value="2">
                    <input type="hidden" name="rows-MAX_NUM_FORMS" value="1000" disabled>
                </div>
            </div></form>`;
        const form = document.querySelector("form");
        const outer = form.querySelector("[name=outer]");
        const inner = form.querySelector("[name=inner]");
        const frozen = name === "inner" ? inner : outer;
        const bound = name === "inner" ? outer : inner;
        const group = form.querySelector(`[cv-data-toggle-field=${name}]`);
        const value = form.querySelector("[name=value]");
        frozen.checked = checked;
        const groups = [...form.querySelectorAll("[cv-data-toggle-group]")];
        if (order === "inner-first") groups.reverse();
        groups.forEach(root => globalThis.cv.initConditional(root));
        const duplicate = frozen.cloneNode();
        frozen.after(duplicate);
        globalThis.cv.initConditional(group);
        change(frozen, !checked);
        change(duplicate, !checked);
        change(bound, false);
        expect(value.disabled).toBe(true);
        change(bound, true);
        expect(value.disabled).toBe(!checked);
        expect(group.style.display).toBe(checked ? "" : "none");
        expect(form.querySelector("[name=baseline]").disabled).toBe(true);
        expect([...form.querySelectorAll("button")].map(button => button.disabled)).toEqual([!checked, true]);
        expect(new FormData(form).get("rows-TOTAL_FORMS")).toBe("2");
        expect(new FormData(form).has("rows-MAX_NUM_FORMS")).toBe(false);

        value.disabled = true; // Same-value writes must remain independent while frozen off.
        globalThis.cv.initConditional(group);
        duplicate.remove();
        frozen.checked = true;
        globalThis.cv.initConditional(group);
        expect(value.disabled).toBe(true);
        // Freeze again, then release only the independent owner.
        frozen.checked = checked;
        globalThis.cv.initConditional(group);
        frozen.after(duplicate);
        globalThis.cv.initConditional(group);
        value.disabled = false;
        globalThis.cv.initConditional(group);
        expect(value.disabled).toBe(!checked);
        duplicate.remove();
        frozen.checked = true;
        globalThis.cv.initConditional(group);
        expect(value.disabled).toBe(false);
        expect(new FormData(form).get("value")).toBe("unsaved");
    });

    it.each(["form", "document"])("retries only its form after reset and honors cancellation at %s", async where => {
        vi.useFakeTimers();
        vi.spyOn(console, "warn").mockImplementation(() => {});
        const { group, checkbox } = fixture({ checked: false });
        const form = checkbox.form;
        const title = group.querySelector("[name=title]");
        form.insertAdjacentHTML("afterend", `<form><input type="checkbox" name="active" checked>
            <div cv-data-toggle-group cv-data-toggle-field="active"><input name="other"></div></form>`);
        globalThis.cv.initConditional(document);
        const otherToggle = document.querySelectorAll("[name=active]")[1];
        const duplicate = checkbox.cloneNode();
        checkbox.after(duplicate);
        globalThis.cv.initConditional(group);
        checkbox.checked = true;
        title.value = "keep on cancellation";
        otherToggle.checked = false; // Owning-form reset must never resync this form.
        const target = where === "form" ? form : document;
        target.addEventListener("reset", event => event.preventDefault(), { once: true });
        form.reset();
        await vi.runAllTimersAsync();
        expect(checkbox.checked).toBe(true);
        expect(title.value).toBe("keep on cancellation");
        expect(group.style.display).toBe("none");
        expect(title.disabled).toBe(true);
        expect(document.querySelector("[name=other]").disabled).toBe(false);

        // With both checkboxes present native defaults reset, but own state stays frozen.
        form.reset();
        expect(checkbox.checked).toBe(false);
        expect(title.value).toBe("");
        await vi.runAllTimersAsync();
        expect(title.disabled).toBe(true);
        duplicate.remove();
        checkbox.defaultChecked = true;
        checkbox.checked = false;
        form.reset();
        expect(group.style.display).toBe("none");
        await Promise.resolve();
        expect(group.style.display).toBe("none");
        await vi.runAllTimersAsync();
        expect(group.style.display).toBe("");
        expect(title.disabled).toBe(false);
        globalThis.cv.initConditional(form);
        form.reset();
        await vi.runAllTimersAsync();
        expect(document.querySelector("[name=other]").disabled).toBe(false);
        expect(new FormData(form).get("book-None-0-TOTAL_FORMS")).toBe("2");
    });

    it.each(["missing", "ambiguous"])("releases frozen ownership during %s modal disposal and reinsert", async mode => {
        vi.useFakeTimers();
        vi.spyOn(console, "warn").mockImplementation(() => {});
        const { group, checkbox } = fixture({ checked: false });
        const form = checkbox.form;
        const title = group.querySelector("[name=title]");
        title.value = "retained content";
        group.insertAdjacentHTML("beforeend", '<input name="independent" disabled>');
        const independent = group.querySelector("[name=independent]");
        const modal = document.createElement("div");
        form.before(modal);
        modal.append(form);
        modal.dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
        const duplicate = checkbox.cloneNode();
        if (mode === "missing") checkbox.remove();
        else checkbox.after(duplicate);
        globalThis.cv.initConditional(group);
        expect(title.disabled).toBe(true);
        form.dispatchEvent(new Event("reset")); // Queue work that must be invalidated by unload.
        modal.dispatchEvent(new CustomEvent("cv:modal:unload", { bubbles: true }));
        expect(title.disabled).toBe(false);
        expect(independent.disabled).toBe(true);
        form.remove();
        change(checkbox, true);
        change(duplicate, true);
        await vi.runAllTimersAsync();
        expect(group.style.display).toBe("none");
        expect(title.disabled).toBe(false);
        title.disabled = true;
        await Promise.resolve();
        title.disabled = false;
        duplicate.remove();
        form.prepend(checkbox);
        checkbox.checked = true;
        modal.append(form);
        modal.dispatchEvent(new CustomEvent("cv:modal:loaded", { bubbles: true }));
        globalThis.cv.initConditional(group);
        expect(group.style.display).toBe("");
        expect(title.disabled).toBe(false);
        expect(independent.disabled).toBe(true);
        change(checkbox, false);
        change(checkbox, true);
        expect(title.disabled).toBe(false);
        expect(new FormData(form).get("title")).toBe("retained content");
    });

    it.each([true, false])("ignores a stale unresolved toggle during focus recovery with usable ancestor=%s", ancestorUsable => {
        vi.spyOn(console, "warn").mockImplementation(() => {});
        vi.spyOn(HTMLElement.prototype, "getClientRects").mockReturnValue([{}]);
        const { outer, inner, value } = nestedFixture();
        const form = outer.form;
        const group = value.parentElement;
        inner.name = "retired";
        globalThis.cv.initConditional(group);
        expect(group.style.display).toBe("");
        // The obsolete checkbox remains usable outside the group. Only the
        // new resolved owner (hidden here), then ancestor/form, may get focus.
        const replacement = inner.cloneNode();
        replacement.name = "inner";
        replacement.checked = false;
        replacement.hidden = true;
        group.before(replacement);
        outer.hidden = !ancestorUsable;
        value.focus();
        globalThis.cv.initConditional(replacement);
        expect(document.activeElement).toBe(ancestorUsable ? outer : form);
        expect(group.style.display).toBe("none");
        change(replacement, true);
        value.focus();
        globalThis.cv.initConditional(form);
        expect(document.activeElement).toBe(value);
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
