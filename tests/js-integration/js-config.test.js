import { afterEach, expect, it, vi } from "vitest";
import { spawnSync } from "node:child_process";
import { selectedPython } from "./python.js";
import { loadScript } from "../js/helpers/load.js";

afterEach(() => {
    for (const name of ["cv", "tabler", "coreui", "bootstrap", "__cvTooltipInit"]) delete window[name];
    document.body.innerHTML = "";
});

it("initializes an owned tooltip through real registered Django config", async () => {
    const python = selectedPython();
    const root = process.cwd();
    const result = spawnSync(python, ["-c", `
from tests.test1.conftest import pytest_configure
pytest_configure()
from crud_views.lib import register_data_prefix, register_js_namespace, register_tooltip_placements
from django.template import Context, Template
from django.test import RequestFactory
register_data_prefix("coreui")
register_js_namespace("tabler")
register_tooltip_placements({"context": "bottom"})
print(Template("{% load crud_views %}{% cv_config %}").render(Context({"request": RequestFactory().get("/theme/")})))
`], {
        cwd: root, encoding: "utf8", timeout: 30000,
        env: { ...process.env, PYTHONPATH: `${root}/src:${root}` },
    });
    expect(result.error, `CV_FRAGMENT_PYTHON=${python}`).toBeUndefined();
    expect(result.status, result.stdout + result.stderr).toBe(0);
    expect(result.stdout.trim()).not.toBe("");
    await loadScript("adapters");
    document.body.innerHTML = result.stdout + '<button data-cv-tooltip="context" title="Owned"></button>' +
        '<button data-bs-toggle="tooltip" title="App"></button>';
    expect(document.getElementById("cv-config").dataset.dataPrefix).toBe("coreui");
    for (const name of ["tabler", "coreui", "bootstrap"]) {
        window[name] = { Tooltip: { getOrCreateInstance: vi.fn(() => ({})) } };
    }
    await loadScript("tooltip");
    for (const name of ["tabler", "coreui", "bootstrap"]) window[name].Tooltip.getOrCreateInstance.mockClear();
    window.cv.initTooltips(document);
    expect(window.tabler.Tooltip.getOrCreateInstance.mock.calls).toEqual([
        [document.querySelector("[data-cv-tooltip]"), { placement: "bottom" }],
    ]);
    expect(window.coreui.Tooltip.getOrCreateInstance).not.toHaveBeenCalled();
    expect(window.bootstrap.Tooltip.getOrCreateInstance).not.toHaveBeenCalled();
}, 35000);
