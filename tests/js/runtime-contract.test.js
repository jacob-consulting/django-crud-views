import { afterAll, beforeAll, describe, expect, it } from "vitest";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const harness = "tests/js/runtime-contract.test.js";
const requiredFiles = [
    "adapters", "formset", "harness", "list.filter", "modal", "object-detail-tabs", "toggle", "tooltip", "viewset",
].map(name => `tests/js/${name}.test.js`);

describe("test runtime boundary", () => {
    let directory, environment, expectedFiles;

    beforeAll(() => {
        const root = process.cwd();
        expectedFiles = fs.readdirSync(path.join(root, "tests/js"), { recursive: true })
            .filter(name => name.endsWith(".test.js"))
            .map(name => `tests/js/${name.split(path.sep).join("/")}`)
            .filter(name => name !== harness).sort();
        directory = fs.mkdtempSync(path.join(os.tmpdir(), "cv-node-only-"));
        // Only JS, config, executable documentation and HTML golden data are copied.
        // Installed node_modules is linked; no Python tree, install, or checkout mutation.
        for (const relative of [
            "package.json", "vitest.config.js", "vitest.integration.config.js",
            "tests/js", "tests/js-integration", "tests/test1/golden/alerts",
            "src/crud_views/static/crud_views/js", "docs/reference/javascript.md",
        ]) {
            const destination = path.join(directory, relative);
            fs.mkdirSync(path.dirname(destination), { recursive: true });
            fs.cpSync(path.join(root, relative), destination, { recursive: true });
        }
        fs.symlinkSync(path.join(root, "node_modules"), path.join(directory, "node_modules"), "junction");
        const bin = path.join(directory, "bin");
        fs.mkdirSync(bin);
        fs.symlinkSync(process.execPath, path.join(bin, "node"));
        environment = { ...process.env, PATH: bin, NO_COLOR: "1" };
        for (const name of Object.keys(environment)) {
            if (name.startsWith("CV_FRAGMENT_") || name.startsWith("PYTHON") || name === "VIRTUAL_ENV") {
                delete environment[name];
            }
        }
    });

    afterAll(() => {
        if (directory) fs.rmSync(directory, { recursive: true, force: true });
    });

    function run(config, reportName, extra = [], env = environment) {
        const report = path.join(directory, `${reportName}.json`);
        const result = spawnSync(process.execPath, [
            "node_modules/vitest/vitest.mjs", "run", "--config", config,
            "--reporter=json", "--outputFile", report, ...extra,
        ], {
            cwd: directory, env, encoding: "utf8", timeout: 25000,
        });
        expect(result.error, result.stdout + result.stderr).toBeUndefined();
        expect(result.signal).toBeNull();
        expect(fs.existsSync(report), result.stdout + result.stderr).toBe(true);
        return { result, report: JSON.parse(fs.readFileSync(report, "utf8")) };
    }

    it("runs every other ordinary JS file in a checkout with only Node available", () => {
        expect(fs.existsSync(path.join(directory, ".nox"))).toBe(false);
        expect(fs.existsSync(path.join(directory, ".venv"))).toBe(false);
        expect(fs.readdirSync(environment.PATH)).toEqual(["node"]);
        expect(environment.CV_FRAGMENT_PYTHON).toBeUndefined();
        expect(fs.existsSync(path.join(directory,
            "src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js"))).toBe(true);
        for (const name of requiredFiles) expect(expectedFiles).toContain(name);
        const { result, report } = run("vitest.config.js", "ordinary", ["--exclude", harness]);
        const failures = report.testResults.flatMap(file => file.assertionResults)
            .flatMap(test => test.failureMessages).join("\n");
        expect(result.status, failures).toBe(0);
        const files = report.testResults.map(file => path.relative(directory, file.name).split(path.sep).join("/")).sort();
        expect(files).toEqual(expectedFiles);
        expect(files).not.toContain(harness);
        expect(report.numTotalTests).toBeGreaterThan(0);
        expect(report.numFailedTests).toBe(0);
        expect(report.numPendingTests).toBe(0);
        for (const file of report.testResults) {
            expect(file.status, file.name).toBe("passed");
            expect(file.assertionResults.length, file.name).toBeGreaterThan(0);
            for (const assertion of file.assertionResults) expect(assertion.status).toBe("passed");
        }
    }, 30000);

    it.each(["missing", "invalid"])("fails the required integration lane for a %s selected Python", selection => {
        const env = { ...environment };
        const selected = path.join(directory, "missing-python");
        if (selection === "invalid") env.CV_FRAGMENT_PYTHON = selected;
        const { result, report } = run("vitest.integration.config.js", selection, [], env);
        expect(result.status).not.toBe(0);
        expect(report.numTotalTests).toBeGreaterThan(0);
        expect(report.numFailedTests).toBeGreaterThan(0);
        expect(report.numPendingTests).toBe(0);
        const failures = report.testResults.flatMap(file => file.assertionResults)
            .flatMap(test => test.failureMessages).join("\n");
        expect(failures).toContain("CV_FRAGMENT_PYTHON");
        expect(failures).toContain("installed Python interpreter");
        if (selection === "invalid") expect(failures).toContain(selected);
        expect(report.testResults.map(file => path.relative(directory, file.name)))
            .toEqual(["tests/js-integration/formset.test.js"]);
    }, 30000);
});
