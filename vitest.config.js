import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        environment: "jsdom",
        include: ["tests/js/**/*.test.js"],
        setupFiles: ["tests/js/helpers/setup.js"],
    },
});
