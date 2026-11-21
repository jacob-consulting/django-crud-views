import { describe, expect, it } from "vitest";
import fs from "node:fs";

const sheets = Object.fromEntries(["manage", "formset"].map(name => [
    name, fs.readFileSync(`src/crud_views/static/crud_views/css/${name}.css`, "utf8"),
]));
const documentation = fs.readFileSync("docs/reference/theme.md", "utf8");

function assertTokenContract(stylesheets, docs) {
    // The bounded scanner is implemented after the negative fixtures establish RED.
}

const mutate = (css, name = "manage") => ({ ...sheets, [name]: sheets[name] + css });

describe("CSS token contract", () => {
    it("accepts the shipped stylesheets and canonical table", () => {
        expect(() => assertTokenContract(sheets, documentation)).not.toThrow();
    });

    it.each([
        ["bare Bootstrap read", ".extra { color: var(--bs-body-bg); }", /unapproved variable read/],
        ["overwritten Bootstrap read", ".extra { color: var(--bs-body-bg); color: red; }", /unapproved variable read/],
        ["nested Bootstrap read", "@media (width > 1px) { .extra { color: var(--bs-body-bg); } }", /unapproved variable read/],
        ["wrong fallback pair", ".extra { color: var(--cv-body-bg, var(--bs-border-color, #fff)); }", /unapproved variable read/],
        ["wrong literal", ".extra { color: var(--cv-body-bg, var(--bs-body-bg, red)); }", /unapproved variable read/],
        ["unknown cv read", ".extra { color: var(--cv-unknown); }", /unapproved variable read/],
        ["upstream cv declaration", ":root { --cv-body-bg: white; }", /upstream cv declaration/],
        ["overwritten cv declaration", ":root { --cv-body-bg: white; --cv-body-bg: black; }", /upstream cv declaration/],
        ["extra Bootstrap declaration", ".extra { --bs-gutter-x: 1rem; }", /Bootstrap declaration/],
        ["misplaced help declaration", ".extra { --bs-btn-color: var(--cv-secondary-text-emphasis, var(--bs-secondary-text-emphasis, #495057)); }", /Bootstrap declaration/],
        ["variable outside a value", "[var(--bs-body-bg)] { color: red; }", /variable outside declaration/],
        ["quoted declaration", '.extra { content: "var(--bs-body-bg)"; }', /unsupported quoted declaration/],
        ["escaped identifier", String.raw`.extra { color: var(--bs-\62ody-bg); }`, /unsupported CSS escape/],
        ["import", '@import "other.css";', /unsupported at-rule/],
        ["unbalanced rule", ".extra { color: red;", /unbalanced/],
        ["unbalanced value", ".extra { color: var(red; }", /unbalanced/],
        ["structural value", ".extra { color: fn(red; blue); }", /unsupported structural value/],
    ])("rejects %s", (_name, css, reason) => {
        expect(() => assertTokenContract(mutate(css), documentation)).toThrow(reason);
    });

    it("rejects a missing table row even when its token remains in prose", () => {
        const docs = documentation.replace(/^\| `--cv-body-bg` .*\n/m, "");
        expect(docs).toContain("--cv-body-bg");
        expect(() => assertTokenContract(sheets, docs)).toThrow(/documentation table/);
    });

    it.each([
        ["duplicate row", docs => docs.replace("| `--cv-body-bg`", "| `--cv-body-bg` | `wrong` |\n| `--cv-body-bg`")],
        ["wrong documented chain", docs => docs.replace("#6c757d", "red")],
        ["duplicate heading", docs => docs + "\n## CSS tokens\n"],
    ])("rejects %s in documentation", (_name, change) => {
        expect(() => assertTokenContract(sheets, change(documentation))).toThrow(/documentation table/);
    });

    it("rejects missing required consumers", () => {
        const changed = { ...sheets, manage: sheets.manage.replace("[data-cv-manage] th {", ".other th {") };
        expect(() => assertTokenContract(changed, documentation)).toThrow(/missing consumer/);
    });

    it("rejects empty sheets", () => {
        expect(() => assertTokenContract({ ...sheets, formset: " /* empty */ " }, documentation)).toThrow(/empty stylesheet/);
    });

    it("accepts whitespace and comments in approved chains", () => {
        const changed = Object.fromEntries(Object.entries(sheets).map(([name, css]) => [
            name, css.replaceAll("var(", "var( /* explanation */ ").replaceAll(",", " ,\n "),
        ]));
        expect(() => assertTokenContract(changed, documentation)).not.toThrow();
    });

    it("accepts approved values in nested media rules and grouped selectors", () => {
        const css = "@media (width > 1px) { @media (width < 1000px) { .a, .b { color: var(--cv-body-bg, var(--bs-body-bg, #fff)); } } }";
        expect(() => assertTokenContract(mutate(css), documentation)).not.toThrow();
    });
});
