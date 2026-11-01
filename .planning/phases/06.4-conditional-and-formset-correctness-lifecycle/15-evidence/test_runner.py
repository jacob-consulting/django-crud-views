"""Successor evidence regressions; stdlib-only, never runs the full matrix."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("phase64_successor", HERE / "run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class HistoricalCounterexamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.historical = json.loads((HERE.parent / "10-evidence/results.json").read_text())

    def current_record(self, label):
        record = copy.deepcopy(self.historical["gates"][label])
        manifest = runner.source()
        record.update(source_sha256=manifest["sha256"], source_after_sha256=manifest["sha256"])
        return record, manifest

    def test_wr01_rejects_filtered_javascript_with_consistent_green_counts(self):
        record, manifest = self.current_record("javascript")
        record["command"] += ["tests/js/toggle.test.js", "-t", "renders"]
        record["counts"] = {"passed": 1, "collected": 1}
        with self.assertRaisesRegex(ValueError, "command"):
            runner.validate_gate(record, manifest)

    def test_wr01_rejects_non_strict_docs(self):
        record, manifest = self.current_record("strict-docs")
        record["command"].remove("--strict")
        with self.assertRaisesRegex(ValueError, "command"):
            runner.validate_gate(record, manifest)


class QualityEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = runner.source()
        cls.javascript = runner.quality_gate("javascript")
        cls.integration = runner.quality_gate("javascript-integration")

    def reject(self, alter, pattern, label="javascript"):
        record = copy.deepcopy(self.integration if label == "javascript-integration" else self.javascript)
        alter(record)
        with self.assertRaisesRegex(ValueError, pattern):
            runner.validate_gate(record, self.manifest)

    def test_real_complete_ordinary_capture(self):
        runner.validate_gate(self.javascript, self.manifest)
        self.assertGreater(self.javascript["counts"]["collected"], 300)

    def test_required_bridge_is_independent(self):
        runner.validate_gate(self.integration, self.manifest)
        self.assertIn("javascript-integration", runner.expected_ids())
        self.assertIn("vitest.integration.config.js", self.integration["command"])
        self.assertTrue(all("/js-integration/" in f["name"] for f in self.integration["vitest"]["testResults"]))

    def test_filtered_command(self):
        self.reject(lambda r: r["command"].insert(3, "tests/js/toggle.test.js"), "command")

    def test_wrong_node_executable(self):
        self.reject(lambda r: r["command"].__setitem__(0, "/bin/true"), "command")

    def test_wrong_vitest_subcommand(self):
        self.reject(lambda r: r["command"].__setitem__(2, "list"), "command")

    def test_missing_file(self):
        self.reject(lambda r: r["vitest"]["testResults"].pop(), "file")

    def test_duplicate_file(self):
        self.reject(lambda r: r["vitest"]["testResults"].append(copy.deepcopy(r["vitest"]["testResults"][0])), "file")

    def test_missing_case(self):
        self.reject(lambda r: r["vitest"]["testResults"][0]["assertionResults"].pop(), "selection")

    def test_duplicate_case(self):
        self.reject(
            lambda r: r["vitest"]["testResults"][0]["assertionResults"].append(
                copy.deepcopy(r["vitest"]["testResults"][0]["assertionResults"][0])
            ),
            "selection",
        )

    def test_failed_case(self):
        self.reject(
            lambda r: r["vitest"]["testResults"][0]["assertionResults"][0].__setitem__("status", "failed"),
            "failed/skipped",
        )

    def test_skipped_case(self):
        self.reject(
            lambda r: r["vitest"]["testResults"][0]["assertionResults"][0].__setitem__("status", "pending"),
            "failed/skipped",
        )

    def test_false_counts(self):
        self.reject(lambda r: r.__setitem__("counts", {"passed": 1, "collected": 1, "files": 1}), "counts")

    def test_false_console(self):
        self.reject(lambda r: r.__setitem__("stdout", "Tests 1 passed (1)"), "console")

    def test_filtered_collection_command(self):
        self.reject(lambda r: r["inventory"]["command"].append("-t=one"), "inventory command")

    def test_stale_collection_source(self):
        self.reject(lambda r: r["inventory"].__setitem__("source_sha256", "stale"), "inventory stale")

    def test_required_integration_case_missing(self):
        self.reject(
            lambda r: r["vitest"]["testResults"][0]["assertionResults"].pop(),
            "selection",
            label="javascript-integration",
        )

    def test_wrong_lint_subcommands_and_flags(self):
        for label, command in (("ruff-check", "format"), ("ruff-format", "check")):
            with self.subTest(label=label):
                record = copy.deepcopy(self.javascript)
                record.update(id=label, command=runner.expected_quality(label))
                runner.validate_gate(record, self.manifest)
                record["command"][1] = command
                with self.assertRaisesRegex(ValueError, "command"):
                    runner.validate_gate(record, self.manifest)

    def test_scoped_copy_checks_but_cannot_claim_complete(self):
        packet = {
            "schema": 2,
            "completed": False,
            "only": "javascript",
            "runner_sha256": runner.sha(runner.__file__),
            "source_manifest": self.manifest,
            "required_gate_ids": runner.expected_ids(),
            "gates": {"javascript": self.javascript},
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.json"
            runner.write_json(output, packet)
            runner.write_json(output.parent / "source-manifest.json", self.manifest)
            command = [sys.executable, str(HERE / "run.py"), "--check", "--output", str(output)]
            scoped = subprocess.run([*command, "--only", "javascript"], text=True, capture_output=True)
            self.assertEqual(scoped.returncode, 0, scoped.stderr)
            unscoped = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(unscoped.returncode, 0)
            self.assertIn("Incomplete matrix", unscoped.stderr)
            packet["gates"]["javascript"] = copy.deepcopy(self.javascript)
            packet["gates"]["javascript"]["command"].insert(3, "-t=one")
            runner.write_json(output, packet)
            corrupted = subprocess.run([*command, "--only", "javascript"], text=True, capture_output=True)
            self.assertNotEqual(corrupted.returncode, 0)
            self.assertIn("command", corrupted.stderr)


if __name__ == "__main__":
    unittest.main()
