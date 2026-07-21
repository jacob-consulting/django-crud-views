import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { vi } from "vitest";

// jsdom's URL constructor differs from Node's; wrap in try/catch for compatibility
const JS_DIR = (() => {
    try {
        return fileURLToPath(new URL("../../../src/crud_views/static/crud_views/js/", import.meta.url));
    } catch {
        return fileURLToPath(new URL("../../../src/crud_views/static/crud_views/js/", `file://${process.cwd()}/tests/js/helpers/load.js`));
    }
})();

// jsdom's window.location is unforgeable (cannot be spied on or replaced) and
// its navigation methods are no-ops. The shipped files always navigate via
// `window.location.*`, so loadScript executes them against a Proxy whose
// `location` is this stub; everything else falls through to the real window.
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
    const code = fs.readFileSync(`${JS_DIR}${name}.js`, "utf-8");
    new Function("window", code)(testWindow());
    // jQuery defers $(document).ready() callbacks by a microtask even when the
    // document is already complete; wait for them so wiring is done on return.
    await new Promise((resolve) => window.jQuery(resolve));
}
