import $ from "jquery";
import { beforeEach, vi } from "vitest";
import { resetNav } from "./load.js";

// The shipped files resolve `$` / `jQuery` as bare globals; stubGlobal sets
// them on both globalThis and the jsdom window.
vi.stubGlobal("$", $);
vi.stubGlobal("jQuery", $);

// formset.js logs debug chatter via console.log/console.assert.
vi.spyOn(console, "log").mockImplementation(() => {});
vi.spyOn(console, "assert").mockImplementation(() => {});

beforeEach(() => {
    resetNav();
});
