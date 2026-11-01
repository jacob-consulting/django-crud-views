"""Successor evidence regressions; stdlib-only, never runs the full matrix."""

import copy
import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
