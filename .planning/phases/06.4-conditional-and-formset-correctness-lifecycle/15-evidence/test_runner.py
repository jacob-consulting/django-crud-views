"""Successor evidence regressions; stdlib-only, never runs the full matrix."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_focused_accepts_strengthened_reclean_identity_family(self):
        # Synthetic validator fixture: plan11 strengthens the original family
        # with recleaning; its new exact name must remain a required selection.
        record = json.loads(
            json.dumps(self.historical["gates"]["django6.0-focused"]).replace(
                "test_invalid_existing_ids_never_save", "test_reclean_invalid_existing_ids_never_save"
            )
        )
        runner.validate_python(record)
        with self.assertRaisesRegex(ValueError, "missing test_reclean_invalid_existing_ids_never_save"):
            runner.validate_python(self.historical["gates"]["django6.0-focused"])


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
            "capture_request": {"selections": {"javascript": self.javascript["selection"]}},
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


class CurrentCapture(unittest.TestCase):
    def test_wr02_invalid_python_fails_before_unrelated_command(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.json"
            with (
                patch.dict(runner.os.environ, {"CV_FOCUS_PYTHON": "/missing/selected-review-python"}),
                patch.object(runner, "command_record", side_effect=ValueError("unrelated gate started")) as command,
            ):
                with self.assertRaisesRegex(ValueError, "CV_FOCUS_PYTHON.*selected-review-python"):
                    runner.run(output, only="strict-docs")
                command.assert_not_called()
            self.assertFalse(output.exists())
            self.assertFalse((output.parent / "source-manifest.json").exists())

    def test_wr02_invalid_runtime_subprocess_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.json"
            original = {"source_manifest": runner.source(), "gates": {}}
            runner.write_json(output, original)
            before = output.read_bytes()
            result = subprocess.run(
                [sys.executable, str(HERE / "run.py"), "--run", "--only", "strict-docs", "--output", str(output)],
                env={**runner.os.environ, "CV_FOCUS_PYTHON": "/missing/selected-review-python"},
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("CV_FOCUS_PYTHON", result.stderr)
            self.assertIn("selected-review-python", result.stderr)
            self.assertNotIn("START ", result.stdout)
            self.assertNotIn("REUSE ", result.stdout)
            self.assertEqual(output.read_bytes(), before)
            self.assertFalse((output.parent / "source-manifest.json").exists())

    def test_all_invalid_selections_fail_before_any_process(self):
        variables = (
            "CV_FOCUS_PYTHON",
            "CV_FOCUS_NODE",
            "CV_FOCUS_CHROMIUM",
            "CV_FOCUS_PLAYWRIGHT",
            "CV_FRAGMENT_PYTHON",
            "CV_CONDITIONAL_PORT",
        )
        for variable in variables:
            with (
                self.subTest(variable=variable),
                patch.dict(runner.os.environ, {variable: "/missing/selected-runtime"}),
                patch.object(runner.subprocess, "run") as processes,
            ):
                with self.assertRaisesRegex(ValueError, variable):
                    runner.capture_request()
                processes.assert_not_called()

    def test_effective_selections_affect_only_relevant_gates(self):
        original = runner.capture_request()["selections"]
        with patch.dict(runner.os.environ, {"CV_FOCUS_PYTHON": str(runner.ROOT / runner.SERIES["5.2"])}):
            changed = runner.capture_request()["selections"]
        self.assertNotEqual(original["conditional-browser"], changed["conditional-browser"])
        self.assertNotEqual(original["modal-browser"], changed["modal-browser"])
        self.assertEqual(original["javascript"], changed["javascript"])
        with patch.dict(runner.os.environ, {"CV_FRAGMENT_PYTHON": str(runner.ROOT / runner.SERIES["5.2"])}):
            bridge = runner.capture_request()["selections"]
        self.assertNotEqual(original["javascript-integration"], bridge["javascript-integration"])
        self.assertEqual(original["conditional-browser"], bridge["conditional-browser"])
        with patch.dict(runner.os.environ, {"CV_CONDITIONAL_PORT": "8244"}):
            port = runner.capture_request()["selections"]
        self.assertNotEqual(original["conditional-browser"], port["conditional-browser"])
        self.assertEqual(original["modal-browser"], port["modal-browser"])
        with patch.object(runner, "validate_gate") as validate:
            record = {"selection": original["conditional-browser"]}
            self.assertTrue(runner.can_reuse(record, {}, original["conditional-browser"]))
            self.assertFalse(runner.can_reuse(record, {}, changed["conditional-browser"]))
            validate.assert_called_once()

    def test_matching_selection_reuses_real_docs_and_historical_check_ignores_current_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.json"
            command = [sys.executable, str(HERE / "run.py"), "--output", str(output), "--only", "strict-docs"]
            first = subprocess.run([*command, "--run"], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = json.loads(output.read_text())["gates"]["strict-docs"]
            second = subprocess.run([*command, "--run"], capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("REUSE strict-docs", second.stdout)
            self.assertEqual(json.loads(output.read_text())["gates"]["strict-docs"], before)
            historical = subprocess.run(
                [*command, "--check"],
                env={
                    **runner.os.environ,
                    "CV_FOCUS_NODE": "/missing/historical-node",
                    "CV_FOCUS_PYTHON": "/missing/historical-python",
                    "CV_FRAGMENT_PYTHON": "/missing/historical-bridge",
                },
                capture_output=True,
                text=True,
            )
            self.assertEqual(historical.returncode, 0, historical.stderr)
            packet = json.loads(output.read_text())
            packet["source_manifest"]["sha256"] = "stale"
            runner.write_json(output, packet)
            stale = subprocess.run([*command, "--check"], capture_output=True, text=True)
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("stale", stale.stderr)

    def test_changed_valid_browser_selection_reruns_affected_gate(self):
        # Isolate orchestration from real browser execution; no matrix is launched.
        def browser(label, selection=None):
            return {"id": label, "selection": selection, "duration_seconds": 0}

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(runner, "validate_gate"),
            patch.object(runner, "browser_gate", side_effect=browser) as gate,
        ):
            output = Path(directory) / "capture.json"
            runner.run(output, only="conditional-browser")
            runner.run(output, only="conditional-browser")
            self.assertEqual(gate.call_count, 1)
            with patch.dict(runner.os.environ, {"CV_FOCUS_PYTHON": str(runner.ROOT / runner.SERIES["5.2"])}):
                runner.run(output, only="conditional-browser")
            self.assertEqual(gate.call_count, 2)
            saved = json.loads(output.read_text())
            self.assertEqual(
                saved["gates"]["conditional-browser"]["selection"],
                saved["capture_request"]["selections"]["conditional-browser"],
            )


class CompletePacketFixture:
    """Explicitly synthetic provenance, never saved as acceptance evidence.

    Retain the full historical gate structure, rebinding only source-dependent
    observations needed to exercise the current validators without a product run.
    """

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.manifest = runner.source()
        self.packet = json.loads((HERE.parent / "18-evidence/results.json").read_text())
        self.packet.update(source_manifest=self.manifest, runner_sha256=runner.sha(runner.__file__))
        for gate in self.packet["gates"].values():
            gate.update(
                source_sha256=self.manifest["sha256"],
                source_after_sha256=self.manifest["sha256"],
                runner_sha256=runner.sha(runner.__file__),
            )
            if "inventory" in gate:
                gate["inventory"].update(
                    source_sha256=self.manifest["sha256"], source_after_sha256=self.manifest["sha256"]
                )
        selected = runner.self_test_ids()
        gate = self.packet["gates"]["evidence-self-tests"]
        gate.update(
            selected_tests=selected,
            stdout="",
            stderr="\n".join(f"{identity.rsplit('.', 1)[1]} ({identity}) ... ok" for identity in selected)
            + f"\nRan {len(selected)} tests in 1.0s\n\nOK\n",
        )
        self.output = self.directory / "packet.json"
        self.handoff = json.loads((HERE.parent / "19-evidence/handoff.json").read_text())
        self.handoff.update(source_sha256=self.manifest["sha256"], runner_sha256=runner.sha(runner.__file__))
        # Pending dispositions exercise structural validity without inventing reviews.
        for report in self.handoff["reports"].values():
            report["status"] = "pending"
        findings = {}
        for gap, reviews in runner.GAP_REVIEWS.items():
            for identity in [gap, *reviews]:
                findings[identity] = {
                    "status": "pending",
                    "threats": ["T-06.4-" + n for n in runner.GAP_THREATS[gap]],
                    "evidence": [{"gate": "javascript"}],
                }
            findings[gap]["review_ids"] = reviews
        self.handoff["findings"] = findings
        self.handoff["threats"] = {
            "T-06.4-" + n: {"status": "pending"}
            for n in {n for values in runner.GAP_THREATS.values() for n in values} | {"35", "36"}
        }

    def save(self):
        runner.write_json(self.output, self.packet)
        runner.write_json(self.directory / "source-manifest.json", self.manifest)
        self.handoff["packet"] = {"path": str(self.output.relative_to(runner.ROOT)), "sha256": runner.sha(self.output)}
        runner.write_json(self.directory / "handoff.json", self.handoff)

    def cli(self, handoff=False):
        self.save()
        args = (
            ["--check-handoff", str(self.directory / "handoff.json")]
            if handoff
            else ["--check", "--output", str(self.output)]
        )
        return subprocess.run([sys.executable, str(HERE / "run.py"), *args], capture_output=True, text=True)

    def assert_rejected_everywhere(self, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            runner.validate(self.packet, self.manifest)
        self.save()
        with self.assertRaisesRegex(ValueError, pattern):
            runner.validate_handoff(self.handoff)
        for handoff in (False, True):
            with self.subTest(handoff=handoff):
                result = self.cli(handoff)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("MATRIX_REJECTED", result.stderr)
                self.assertRegex(result.stderr, pattern)
                self.assertNotIn("MATRIX_OK", result.stdout)


class CheckerControlEvidence(CompletePacketFixture, unittest.TestCase):
    def test_complete_packet_cli_and_pending_handoff_positive(self):
        runner.validate(self.packet, self.manifest)
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PHASE64_MATRIX_OK", result.stdout)
        result = self.cli(handoff=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout), {"structurally_valid": True, "ready": False, "disposition": "not-ready"}
        )

    def test_missing_detailed_inventory_rejects_cli_aggregate_and_handoff(self):
        self.packet.pop("checker_control_evidence")
        self.assert_rejected_everywhere("Checker control evidence inventory")

    def test_contradictory_success_outcomes_reject_everywhere(self):
        for outcome in self.packet["checker_control_evidence"].values():
            outcome.update(returncode=0, stdout="PHASE64_MATRIX_OK", stderr="")
        self.assert_rejected_everywhere("Checker control exit")

    def test_malformed_outcomes_are_not_rejections(self):
        original = copy.deepcopy(self.packet)
        cases = [
            ("returncode", True, "exit"),
            ("returncode", -9, "exit"),
            ("returncode", 127, "exit"),
            ("returncode", "1", "exit"),
            ("stdout", "PHASE64_MATRIX_OK", "diagnostic"),
            ("stderr", "", "diagnostic"),
            ("stderr", "MATRIX_REJECTED: Missing/stale source manifest\n", "diagnostic"),
            ("stderr", "Traceback: setup failed\n", "diagnostic"),
        ]
        for key, value, pattern in cases:
            with self.subTest(key=key, value=value):
                self.packet = copy.deepcopy(original)
                self.packet["checker_control_evidence"]["exit-code"][key] = value
                with self.assertRaisesRegex(ValueError, "Checker control " + pattern):
                    runner.validate(self.packet, self.manifest)

    def test_command_identity_normalizes_only_transport_directory(self):
        original = copy.deepcopy(self.packet)
        for index, value in (
            (0, "/bin/true"),
            (1, "/tmp/run.py"),
            (2, "--run"),
            (3, "--only"),
            (4, "/tmp/other.json"),
            (4, "exit-code.json"),
        ):
            with self.subTest(index=index, value=value):
                self.packet = copy.deepcopy(original)
                self.packet["checker_control_evidence"]["exit-code"]["command"][index] = value
                with self.assertRaisesRegex(ValueError, "Checker control command"):
                    runner.validate(self.packet, self.manifest)

    def test_exact_summary_and_detail_inventory(self):
        original = copy.deepcopy(self.packet)
        for key in ("checker_controls", "checker_control_evidence"):
            for extra in (False, True):
                with self.subTest(key=key, extra=extra):
                    self.packet = copy.deepcopy(original)
                    if extra:
                        self.packet[key]["invented"] = copy.deepcopy(self.packet[key]["exit-code"])
                    else:
                        self.packet[key].pop("exit-code")
                    with self.assertRaisesRegex(ValueError, "Checker control.*inventory"):
                        runner.validate(self.packet, self.manifest)

    def test_duplicate_keys_reject_at_both_cli_entry_points(self):
        self.save()
        text = self.output.read_text()
        self.output.write_text(text.replace('"schema": 2', '"schema": 2, "schema": 2', 1))
        self.handoff["packet"]["sha256"] = runner.sha(self.output)
        handoff = self.directory / "handoff.json"
        runner.write_json(handoff, self.handoff)
        for args in (["--check", "--output", str(self.output)], ["--check-handoff", str(handoff)]):
            result = subprocess.run([sys.executable, str(HERE / "run.py"), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("MATRIX_REJECTED: Duplicate JSON key: schema", result.stderr)


class HandoffEvidence(unittest.TestCase):
    def setUp(self):
        # Synthetic unit fixture, never a claimed acceptance packet. Full-matrix
        # validation is a separate tested gate, mocked here to test handoff rules.
        self.temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        directory = Path(self.temporary.name)
        self.manifest = runner.source()
        matrix = {"gates": {"javascript": {"returncode": 0}}}
        packet_path = directory / "packet.json"
        runner.write_json(packet_path, matrix)
        runner.write_json(directory / "source-manifest.json", self.manifest)
        report_path = directory / "report.txt"
        report_path.write_text("Unit fixture: independent review pending; no acceptance claim.\n")
        self.reference = {"path": str(report_path.relative_to(runner.ROOT)), "sha256": runner.sha(report_path)}
        findings = {}
        for gap, reviews in runner.GAP_REVIEWS.items():
            for identity in [gap, *reviews]:
                findings[identity] = {
                    "status": "pending",
                    "threats": ["T-06.4-" + n for n in runner.GAP_THREATS[gap]],
                    "evidence": [{"gate": "javascript"}],
                }
            findings[gap]["review_ids"] = reviews
        required_threats = {"T-06.4-" + n for ns in runner.GAP_THREATS.values() for n in ns} | {
            "T-06.4-35",
            "T-06.4-36",
        }
        self.data = {
            "schema": 1,
            "ready": False,
            "source_sha256": self.manifest["sha256"],
            "runner_sha256": runner.sha(runner.__file__),
            "packet": {"path": str(packet_path.relative_to(runner.ROOT)), "sha256": runner.sha(packet_path)},
            "reports": {
                key: {**self.reference, "status": "pending"} for key in ("code", "security", "ui", "verification")
            },
            "findings": findings,
            "threats": {key: {"status": "pending"} for key in required_threats},
            "decisions": [f"D-{i:02}" for i in range(1, 20)],
            "fallback_edges": [{"id": i, "status": "flagged-unresolved"} for i in range(1, 32)],
            "human_checks": {
                "H1": {"status": "pending"},
                "H2": {
                    "status": "pending",
                    "prohibition": runner.PROHIBITION,
                    "canonical_status": "flagged-unverified",
                },
            },
        }
        validator = patch.object(runner, "validate")
        self.matrix_validator = validator.start()
        self.addCleanup(validator.stop)

    def test_pending_packet_is_structurally_valid_but_not_ready(self):
        result = runner.validate_handoff(self.data)
        self.assertEqual(result, {"structurally_valid": True, "ready": False, "disposition": "not-ready"})
        self.matrix_validator.assert_called_once()

    def test_missing_findings_and_links_reject(self):
        for identity in self.data["findings"]:
            with self.subTest(identity=identity):
                altered = copy.deepcopy(self.data)
                altered["findings"].pop(identity)
                with self.assertRaisesRegex(ValueError, "finding"):
                    runner.validate_handoff(altered)

    def test_missing_case_reference_rejects(self):
        self.data["findings"]["G6"]["evidence"][0]["case"] = "not-a-real-case"
        with self.assertRaisesRegex(ValueError, "case"):
            runner.validate_handoff(self.data)

    def test_stale_report_hash_rejects(self):
        self.data["reports"]["security"]["sha256"] = "stale"
        with self.assertRaisesRegex(ValueError, "hash"):
            runner.validate_handoff(self.data)

    def test_stale_source_provenance_rejects(self):
        self.data["source_sha256"] = "stale"
        with self.assertRaisesRegex(ValueError, "provenance"):
            runner.validate_handoff(self.data)

    def test_false_readiness_rejects(self):
        self.data["ready"] = True
        with self.assertRaisesRegex(ValueError, "readiness"):
            runner.validate_handoff(self.data)

    def test_unattributed_human_approval_rejects(self):
        for identity in ("H1", "H2"):
            with self.subTest(identity=identity):
                altered = copy.deepcopy(self.data)
                altered["human_checks"][identity]["status"] = "accepted"
                with self.assertRaisesRegex(ValueError, "Unattributed"):
                    runner.validate_handoff(altered)

    def test_unreviewed_finding_cannot_close(self):
        self.data["findings"]["WR-01"]["status"] = "closed"
        self.data["findings"]["WR-01"]["review"] = "code"
        with self.assertRaisesRegex(ValueError, "independent passed report"):
            runner.validate_handoff(self.data)

    def test_missing_human_state_or_prohibition_rejects(self):
        self.data["human_checks"].pop("H1")
        with self.assertRaisesRegex(ValueError, "H1/H2"):
            runner.validate_handoff(self.data)

    def test_malformed_packet_subprocess_rejects(self):
        output = Path(self.temporary.name) / "handoff.json"
        runner.write_json(output, {"schema": 1})
        result = subprocess.run(
            [sys.executable, str(HERE / "run.py"), "--check-handoff", str(output)], capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MATRIX_REJECTED", result.stderr)


if __name__ == "__main__":
    unittest.main()
