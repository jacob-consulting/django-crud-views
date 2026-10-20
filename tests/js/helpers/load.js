import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { vi } from "vitest";

// Resolve via path, not `new URL(relative, base)` — in the jsdom test
// environment the global URL is jsdom's and rejects file-scheme resolution.
const JS_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../src/crud_views/static/crud_views/js");

// jsdom's window.location is unforgeable (cannot be spied on or replaced) and
// its navigation methods are no-ops. The shipped files always navigate via
// `globalThis.location.*`, so loadScript executes them against a Proxy (bound
// as both `window` and `globalThis`) whose `location` is this stub; everything
// else falls through to the real window.
export const nav = {
    assign: vi.fn(),
    href: "",
};

export function resetNav() {
    nav.assign = vi.fn();
    nav.href = "";
}

function testWindow() {
    return new Proxy(window, {
        get: (target, prop) => (prop === "location" ? nav : Reflect.get(target, prop)),
        set: (target, prop, value) => Reflect.set(target, prop, value),
    });
}

export async function loadScript(name) {
    const code = fs.readFileSync(path.join(JS_DIR, `${name}.js`), "utf-8");
    const win = testWindow();
    // Evaluates the package's own static JS inside the test window, as a <script> tag would.
    new Function("window", "globalThis", code)(win, win); // NOSONAR S1523
    // No shipped script queues its start-up on jQuery's ready any more (formset.js starts on
    // DOMContentLoaded / readyState), so wiring is complete when the evaluation returns. The
    // function stays async so callers keep awaiting it.
}
