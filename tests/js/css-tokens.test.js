import { describe, expect, it } from "vitest";
import fs from "node:fs";

const sheets = Object.fromEntries(["manage", "formset"].map(name => [
    name, fs.readFileSync(`src/crud_views/static/crud_views/css/${name}.css`, "utf8"),
]));
const documentation = fs.readFileSync("docs/reference/theme.md", "utf8");

function assertTokenContract(stylesheets, docs) {
    const chains = {
        "--cv-secondary-color": "var(--cv-secondary-color,var(--bs-secondary-color,#6c757d))",
        "--cv-secondary-text-emphasis": "var(--cv-secondary-text-emphasis,var(--bs-secondary-text-emphasis,#495057))",
        "--cv-body-bg": "var(--cv-body-bg,var(--bs-body-bg,#fff))",
        "--cv-border-color": "var(--cv-border-color,var(--bs-border-color,#dee2e6))",
        "--cv-border-radius": "var(--cv-border-radius,var(--bs-border-radius,.375rem))",
        "--cv-tertiary-bg": "var(--cv-tertiary-bg,var(--bs-tertiary-bg,#f8f9fa))",
    };
    const help = "[data-cv-manage] [data-cv-manage-help].btn-outline-secondary";
    const consumers = [
        ["manage", "[data-cv-manage] th", "color", "--cv-secondary-text-emphasis"],
        ["manage", help, "--bs-btn-color", "--cv-secondary-text-emphasis"],
        ["manage", "[data-cv-manage] .cv-manage-default td", "color", "--cv-secondary-color"],
        ["formset", ".cv-formset-row-card", "border", "--cv-secondary-color"],
        ["formset", ".cv-formset-row-card", "border-radius", "--cv-border-radius"],
        ["formset", ".cv-formset-row-card", "background-color", "--cv-body-bg"],
        ["formset", ".cv-formset-row-compact", "border-radius", "--cv-border-radius"],
        ["formset", ".cv-formset-row-compact", "background-color", "--cv-body-bg"],
        ["formset", ".cv-formset-row-compact.cv-formset-row-bordered", "border", "--cv-border-color"],
        ["formset", ".cv-formset-compact-child", "background-color", "--cv-tertiary-bg"],
        ["formset", ".cv-formset-compact-child", "border", "--cv-border-color"],
        ["formset", ".cv-formset-compact-child", "border-radius", "--cv-border-radius"],
    ];
    const fail = message => { throw new Error(message); };
    const normalize = text => text.trim().replace(/\s+/g, " ").replace(/\s*([(),])\s*/g, "$1");
    const variable = /--(?:bs|cv)-/i;
    const declarations = [];

    // Test-only syntax boundary: ordinary/grouped selectors (quoted attributes allowed),
    // @media and @keyframes, and simple declarations with balanced parentheses. Preserve
    // every declaration occurrence. Escapes, imports, quoted values, structural values,
    // other at-rules and nested selectors fail closed; extend deliberately if CSS changes.
    for (const [sheet, original] of Object.entries(stylesheets)) {
        const css = original.replace(/\/\*[\s\S]*?\*\//g, " ");
        if (/\/\*|\*\//.test(css)) fail("unbalanced CSS comment");
        if (css.includes("\\")) fail("unsupported CSS escape");
        if (!css.trim()) fail(`empty stylesheet: ${sheet}`);
        let cursor = 0;
        const startCount = declarations.length;
        const whitespace = () => { while (/\s/.test(css[cursor] ?? "") && cursor < css.length) cursor++; };

        function rules(nested = false) {
            while (cursor < css.length) {
                whitespace();
                if (cursor === css.length) break;
                if (css[cursor] === "}") {
                    if (!nested) fail("unbalanced closing brace");
                    cursor++;
                    return;
                }
                const start = cursor;
                let quote = null;
                const brackets = [];
                for (; cursor < css.length; cursor++) {
                    const char = css[cursor];
                    if (quote) { if (char === quote) quote = null; continue; }
                    if (char === '"' || char === "'") { quote = char; continue; }
                    if (char === "[" || char === "(") brackets.push(char);
                    if (char === "]" || char === ")") {
                        if (brackets.pop() !== (char === "]" ? "[" : "(")) fail("unbalanced selector");
                    }
                    if (char === "{" && !brackets.length) break;
                    if (char === ";" || char === "}") fail("unsupported at-rule or malformed selector");
                }
                if (quote || brackets.length || cursor === css.length) fail("unbalanced rule");
                const selector = css.slice(start, cursor++).trim().replace(/\s+/g, " ");
                if (!selector) fail("malformed empty selector");
                if (variable.test(selector)) fail("variable outside declaration value");
                if (selector.startsWith("@")) {
                    if (!/^@(media\s+.+|keyframes\s+[\w-]+)$/.test(selector)) fail("unsupported at-rule");
                    rules(true);
                } else {
                    values(selector);
                }
            }
            if (nested) fail("unbalanced rule");
        }

        function values(selector) {
            while (cursor < css.length) {
                whitespace();
                if (css[cursor] === "}") { cursor++; return; }
                const start = cursor;
                while (cursor < css.length && !/[;:{}]/.test(css[cursor])) cursor++;
                const property = css.slice(start, cursor).trim();
                if (css[cursor] !== ":" || !/^(--)?[a-zA-Z][\w-]*$/.test(property)) fail("malformed declaration");
                const valueStart = ++cursor;
                let depth = 0;
                for (; cursor < css.length; cursor++) {
                    const char = css[cursor];
                    if (char === '"' || char === "'") fail("unsupported quoted declaration value");
                    if (char === "(") depth++;
                    if (char === ")" && --depth < 0) fail("unbalanced value");
                    if (char === "{") fail("unsupported structural value");
                    if (char === ";" || char === "}") {
                        if (depth) fail(char === ";" && css.slice(cursor + 1).split("}")[0].includes(")")
                            ? "unsupported structural value" : "unbalanced value");
                        break;
                    }
                }
                if (depth || cursor === css.length) fail("unbalanced value or rule");
                const value = normalize(css.slice(valueStart, cursor));
                if (!value) fail("malformed empty value");
                declarations.push({ sheet, selector, property, value });
                if (css[cursor] === ";") cursor++;
            }
            fail("unbalanced rule");
        }

        rules();
        if (declarations.length === startCount) fail(`empty stylesheet: ${sheet}`);
    }

    const used = new Set();
    let helpDeclarations = 0;
    for (const declaration of declarations) {
        const { sheet, selector, property, value } = declaration;
        if (/^--cv-/i.test(property)) fail("upstream cv declaration");
        if (/^--bs-/i.test(property)) {
            if (sheet !== "manage" || selector !== help || property !== "--bs-btn-color"
                || value !== chains["--cv-secondary-text-emphasis"] || ++helpDeclarations !== 1) {
                fail("unapproved Bootstrap declaration");
            }
        }
        let residual = value;
        for (const [token, chain] of Object.entries(chains)) {
            const pattern = new RegExp(`(?<![\\w-])${chain.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "g");
            residual = residual.replace(pattern, () => { used.add(token); return ""; });
        }
        if (variable.test(residual)) fail("unapproved variable read");
    }
    for (const [sheet, selector, property, token] of consumers) {
        if (!declarations.some(item => item.sheet === sheet && item.selector === selector
            && item.property === property && item.value.includes(chains[token]))) {
            fail(`missing consumer: ${sheet} ${selector} ${property}`);
        }
    }
    expect([...used].sort(), "approved and used tokens").toEqual(Object.keys(chains).sort());

    const headings = [...docs.matchAll(/^## CSS tokens\s*$/gm)];
    if (headings.length !== 1) fail("documentation table requires unique CSS tokens heading");
    const section = docs.slice(headings[0].index + headings[0][0].length).split(/^## /m)[0];
    const lines = section.split("\n").filter(line => line.startsWith("|"));
    if (lines.length !== 8 || !/^\|\s*Token\s*\|\s*Required fallback chain\s*\|$/.test(lines[0])
        || !/^\|\s*-+\s*\|\s*-+\s*\|$/.test(lines[1])) fail("documentation table shape");
    const documented = new Set();
    for (const line of lines.slice(2)) {
        const row = line.match(/^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|$/);
        if (!row || !Object.hasOwn(chains, row[1]) || documented.has(row[1])
            || normalize(row[2]) !== chains[row[1]]) fail("documentation table token/fallback pair");
        documented.add(row[1]);
    }
    expect([...documented].sort(), "documentation table tokens").toEqual([...used].sort());
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
