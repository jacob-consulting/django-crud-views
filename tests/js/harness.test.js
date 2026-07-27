import { describe, expect, it } from "vitest";
import { loadScript } from "./helpers/load.js";

describe("harness", () => {
    it("executes shipped scripts against the jsdom window", async () => {
        expect(window.__cvToggleInit).toBeUndefined();
        await loadScript("toggle");
        expect(window.__cvToggleInit).toBe(true);
    });

    it("provides real jQuery as a global", () => {
        expect(window.$).toBeDefined();
        expect(window.$.fn.jquery).toMatch(/^3\.7\./);
    });
});
