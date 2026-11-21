import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

export function selectedPython() {
    const selected = process.env.CV_FRAGMENT_PYTHON;
    if (!selected) {
        throw new Error("CV_FRAGMENT_PYTHON is required: select an installed Python interpreter with the Django test dependencies.");
    }
    try {
        // Preserve the virtualenv launcher path rather than resolving its symlink.
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
