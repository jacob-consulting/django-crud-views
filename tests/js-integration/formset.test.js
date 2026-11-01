import { describe, expect, it } from "vitest";
import jquery from "jquery";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { JSDOM } from "jsdom";

// Serialized into a disposable Node driver so Django can POST this actual DOM's FormData
// before its test database/registered routes are torn down. No copied server HTML fixtures.
function insertServerFragments(fixture, JSDOM, jquery, assert, source) {
    const dom = new JSDOM(fixture.page, { url: "http://testserver/", runScripts: "outside-only" });
    const win = dom.window;
    win.$ = win.jQuery = jquery(win);
    win.console.log = () => {};
    win.eval(source);
    win.cv.initFormsets();
    const form = win.document.querySelector("form.cv-form");
    assert.ok(form, "real editor form exists");
    const events = [];
    form.addEventListener("cv:formset:row-added", event => {
        events.push({ prefix: event.detail.prefix, rows: event.detail.rows });
        assert.equal(event.target.getAttribute("cv-data-formset-form-prefix"), event.detail.prefix);
    });
    for (const step of fixture.steps) {
        const content = [...form.querySelectorAll(".cv-formset-content")]
            .find(el => el.getAttribute("cv-data-formset-prefix") === step.prefix);
        assert.ok(content, step.prefix);
        const rows = () => [...content.querySelectorAll(".cv-formset-row")]
            .filter(el => el.getAttribute("cv-data-formset-prefix") === step.prefix);
        const before = rows().length;
        const totals = [...form.elements].filter(el => el.name.endsWith("-TOTAL_FORMS"));
        const otherTotals = totals.filter(el => el.name !== `${step.prefix}-TOTAL_FORMS`)
            .map(el => [el, el.value]);
        const total = totals.find(el => el.name === `${step.prefix}-TOTAL_FORMS`);
        assert.equal(Number(total.value), before);
        const last = rows().at(-1);
        const button = [...last.querySelectorAll("button.cv-form-ctrl-add")]
            .find(el => el.getAttribute("cv-data-formset-form-prefix") === last.getAttribute("cv-data-formset-form-prefix"));
        assert.ok(button, "real Add control exists");
        let calls = 0;
        win.$.ajax = request => {
            calls++;
            assert.deepEqual(Object.keys(request.data).sort(), Object.keys(step.params).sort());
            for (const key of Object.keys(step.params)) assert.equal(String(request.data[key]), step.params[key]);
            request.success(step.fragment);
        };
        const eventCount = events.length;
        button.click();
        assert.equal(calls, 1);
        assert.equal(rows().length, before + 1);
        assert.equal(Number(total.value), before + 1);
        for (const [el, value] of otherTotals) assert.equal(el.value, value);
        assert.equal(events.length, eventCount + 1, "one outer event, including nested insertions");
        assert.deepEqual(events.at(-1), { prefix: step.fragment.rows[0], rows: step.fragment.rows });
        const inserted = rows().find(el => el.getAttribute("cv-data-formset-form-prefix") === step.fragment.rows[0]);
        assert.ok(inserted);
        assert.equal(inserted.parentElement, last.parentElement, "row inserted in the intended content wrapper");
        assert.equal(inserted.closest(".cv-formset-content"), content);
        for (const control of inserted.querySelectorAll(".cv-formset-form input[name]")) {
            const owner = control.closest(".cv-formset-row");
            assert.ok(control.name.startsWith(`${owner.getAttribute("cv-data-formset-form-prefix")}-`));
        }
    }
    for (const [name, value] of Object.entries(fixture.values)) {
        const control = [...form.elements].find(el => el.name === name);
        assert.ok(control, name);
        control.value = value;
    }
    const payload = Object.fromEntries(new win.FormData(form));
    dom.window.close();
    return { payload, events };
}

function selectedPython() {
    const selected = process.env.CV_FRAGMENT_PYTHON;
    if (!selected) {
        throw new Error("CV_FRAGMENT_PYTHON is required: select an installed Python interpreter with the Django test dependencies.");
    }
    try {
        // Preserve the virtualenv launcher path: realpath would select its base Python.
        const executable = path.resolve(selected);
        fs.accessSync(executable, fs.constants.X_OK);
        const probe = spawnSync(executable, ["-c", 'print("CV_FRAGMENT_PYTHON_OK")'], {
            encoding: "utf8", timeout: 5000,
        });
        if (probe.error || probe.status !== 0 || probe.stdout.trim() !== "CV_FRAGMENT_PYTHON_OK") {
            throw new Error(probe.error?.message || probe.stderr || "not a usable Python interpreter");
        }
        return executable;
    } catch (error) {
        throw new Error(`CV_FRAGMENT_PYTHON=${selected} is unusable: ${error.message}. Select an installed Python interpreter with the Django test dependencies.`);
    }
}

describe("real Django fragment insertion", () => {
    it("inserts outer and second-sibling fragments and POSTs their real FormData", () => {
        const python = selectedPython();
        const require = createRequire(import.meta.url);
        const directory = fs.mkdtempSync(path.join(os.tmpdir(), "cv-fragment-"));
        const driver = path.join(directory, "driver.cjs");
        const results = path.join(directory, "results.jsonl");
        const source = fs.readFileSync("src/crud_views/static/crud_views/js/formset.js", "utf8");
        fs.writeFileSync(driver, `
const fs = require("node:fs");
const assert = require("node:assert/strict");
const { JSDOM } = require(${JSON.stringify(require.resolve("jsdom"))});
const jquery = require(${JSON.stringify(require.resolve("jquery"))});
const insert = ${insertServerFragments.toString()};
const fixture = JSON.parse(fs.readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(insert(fixture, JSDOM, jquery, assert, ${JSON.stringify(source)})));
`);
        try {
            const result = spawnSync(python, [
                "-m", "pytest", "tests/test1/test_fragment_authorization.py", "-k", "test_server_fragment_dom_round_trip",
                "-q", "-p", "no:cacheprovider", "--tb=short",
            ], {
                cwd: process.cwd(), encoding: "utf8", timeout: 30000,
                env: { ...process.env, PYTHONPATH: `${process.cwd()}/src:${process.cwd()}`,
                    CV_FRAGMENT_DRIVER: driver, CV_FRAGMENT_NODE: process.execPath, CV_FRAGMENT_RESULTS: results },
            });
            expect(result.error, `CV_FRAGMENT_PYTHON=${python}`).toBeUndefined();
            expect(result.status, `CV_FRAGMENT_PYTHON=${python}\n${result.stdout}\n${result.stderr}`).toBe(0);
            expect(result.stdout).toContain("2 passed");
            const records = fs.readFileSync(results, "utf8").trim().split("\n").map(line => JSON.parse(line));
            expect(records.map(record => record.mode)).toEqual(["outer", "nested"]);
            expect(records.map(record => record.events.length)).toEqual([2, 1]);
        } finally {
            fs.rmSync(directory, { recursive: true, force: true });
        }
    }, 35000);
});

describe("integration runtime selection", () => {
    it("rejects an explicitly invalid interpreter without falling back", () => {
        const selected = path.join(os.tmpdir(), "cv-missing-python-plan12");
        const result = spawnSync(process.execPath, [
            "node_modules/vitest/vitest.mjs", "run", "--config", "vitest.integration.config.js",
            "-t", "inserts outer and second-sibling fragments and POSTs their real FormData",
        ], {
            cwd: process.cwd(), encoding: "utf8", timeout: 45000,
            env: { ...process.env, CV_FRAGMENT_PYTHON: selected, NO_COLOR: "1" },
        });
        expect(result.error).toBeUndefined();
        expect(result.status, result.stdout + result.stderr).not.toBe(0);
        expect(result.stdout + result.stderr).toContain("CV_FRAGMENT_PYTHON");
        expect(result.stdout + result.stderr).toContain(selected);
    }, 50000);
});
