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
        # Synthetic record defects supplement the original payload records. Only
        # test_real_staged_controls claims executions for this synthetic packet.
        for kind in runner.CORRUPTIONS:
            if kind in self.packet["checker_control_evidence"]:
                continue
            self.packet["checker_controls"][kind] = "rejected"
            self.packet["checker_control_evidence"][kind] = {
                "command": [sys.executable, str(HERE / "run.py"), "--check", "--output", f"/tmp/synthetic/{kind}.json"],
                "returncode": 1,
                "stdout": "",
                "stderr": f"MATRIX_REJECTED: {runner.CONTROL_DIAGNOSTICS[kind]}\n",
            }
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
            report["sha256"] = runner.sha(runner.ROOT / report["path"])
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
    def test_real_staged_controls_and_final_positive(self):
        self.save()
        runner.generate_controls(self.packet, self.manifest, self.output)
        self.assertEqual(set(self.packet["checker_control_evidence"]), set(runner.CORRUPTIONS))
        for kind, record in self.packet["checker_control_evidence"].items():
            self.assertEqual(record["returncode"], 1, kind)
            self.assertEqual(record["stderr"], f"MATRIX_REJECTED: {runner.CONTROL_DIAGNOSTICS[kind]}\n")
        self.assertEqual(self.packet["checker_positive_control"]["returncode"], 0)
        self.assertIn("PHASE64_MATRIX_OK", self.packet["checker_positive_control"]["stdout"])
        self.assertEqual(self.cli(handoff=True).returncode, 0)

    def test_internal_payload_result_cannot_supply_final_acceptance(self):
        self.packet.pop("checker_control_evidence")
        result = runner.validate(self.packet, self.manifest, require_controls=False)
        self.assertIs(result["complete"], False)
        rejected = self.cli()
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("Checker control evidence inventory", rejected.stderr)

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


class ConditionalCaptureEvidence(CompletePacketFixture, unittest.TestCase):
    def conditional(self):
        return self.packet["gates"]["conditional-browser"]

    def case(self, theme="stock"):
        return next(
            c for c in self.conditional()["browser"]["cases"] if c["id"] == "gap-ambiguity" and c["theme"] == theme
        )

    def assert_oversized_dimension_rejects_everywhere(self, dimension):
        positive = self.cli()
        self.assertEqual(positive.returncode, 0, positive.stderr)
        self.assertIn("PHASE64_MATRIX_OK", positive.stdout)
        self.assertEqual(positive.stderr, "")
        positive = self.cli(handoff=True)
        self.assertEqual(positive.returncode, 0, positive.stderr)
        self.assertEqual(
            json.loads(positive.stdout), {"structurally_valid": True, "ready": False, "disposition": "not-ready"}
        )
        self.assertEqual(positive.stderr, "")

        self.case()["captures"][0]["icons"]["glyphs"][0][dimension] = 10**400
        # Collect both real entry points before assertions or direct validation:
        # an escaping exception must not hide the other CLI's observation.
        observations = [(handoff, self.cli(handoff)) for handoff in (False, True)]
        message = "Conditional capture icon observations invalid: desktop"
        for handoff, result in observations:
            self.assertEqual(
                (result.returncode, result.stdout, result.stderr),
                (1, "", f"MATRIX_REJECTED: {message}\n"),
                f"handoff={handoff}",
            )
        packet = runner.load_json(self.output)
        case = next(
            c
            for c in packet["gates"]["conditional-browser"]["browser"]["cases"]
            if c["id"] == "gap-ambiguity" and c["theme"] == "stock"
        )
        for name, validate in (
            ("capture", lambda: runner.validate_conditional_captures(case)),
            ("aggregate", lambda: runner.validate(packet, self.manifest)),
            ("handoff", lambda: runner.validate_handoff(runner.load_json(self.directory / "handoff.json"))),
        ):
            with self.subTest(validator=name):
                with self.assertRaisesRegex(ValueError, f"^{message}$") as caught:
                    validate()
                self.assertIs(type(caught.exception), ValueError)

    def test_oversized_glyph_width_rejects_cli_and_handoff(self):
        self.assert_oversized_dimension_rejects_everywhere("width")

    def test_oversized_glyph_height_rejects_cli_and_handoff(self):
        self.assert_oversized_dimension_rejects_everywhere("height")

    def test_dimension_numeric_contract(self):
        original = copy.deepcopy(self.case())
        for dimension in ("width", "height"):
            for value in (1, 1.5, 10**300, sys.float_info.max, 5e-324):
                with self.subTest(dimension=dimension, valid=value):
                    case = copy.deepcopy(original)
                    case["captures"][0]["icons"]["glyphs"][0][dimension] = value
                    runner.validate_conditional_captures(case)
            for value in (
                0,
                -1,
                0.0,
                -0.5,
                True,
                False,
                None,
                "1",
                [],
                {},
                (),
                float("nan"),
                float("inf"),
                float("-inf"),
                10**400,
                -(10**400),
            ):
                with self.subTest(dimension=dimension, invalid=value):
                    case = copy.deepcopy(original)
                    case["captures"][0]["icons"]["glyphs"][0][dimension] = value
                    with self.assertRaisesRegex(ValueError, "^Conditional capture icon observations invalid: desktop$"):
                        runner.validate_conditional_captures(case)

    def test_overflow_controls_use_capture_diagnostic(self):
        original_controls = {
            "exit-code",
            "required-case-list",
            "raw-balance-assertion",
            "inline-clear-assertion",
            "source-hash",
            "tracer-absent",
            "tracer-skipped",
            "tracer-failed",
            "tracer-zero-selected",
            "disabled-opt-in",
            "disabled-node-absence",
            "negative-control-setup-error",
            "js-filtered-command",
            "js-wrong-executable",
            "js-missing-file",
            "js-duplicate-file",
            "js-missing-case",
            "js-duplicate-case",
            "js-failed-case",
            "js-skipped-case",
            "js-false-counts",
            "integration-missing",
            "docs-non-strict",
            "ruff-wrong-subcommand",
            "ruff-format-missing-check",
            "capture-missing",
            "capture-digest",
            "capture-observation",
            "control-missing-evidence",
            "control-missing-summary",
            "control-success-outcome",
            "control-wrong-command",
            "control-wrong-diagnostic",
        }
        overflow_controls = {"capture-width-overflow", "capture-height-overflow"}
        self.assertEqual(set(runner.CORRUPTIONS), original_controls | overflow_controls)
        self.assertEqual(len(runner.CORRUPTIONS), 35)
        self.assertEqual(set(runner.CONTROL_DIAGNOSTICS), set(runner.CORRUPTIONS))
        self.assertTrue(overflow_controls <= set(runner.PAYLOAD_CORRUPTIONS))
        original = copy.deepcopy(self.packet)
        paths = [HERE.parent / "18-evidence/results.json"] + [
            runner.ROOT / capture["path"] for capture in self.case()["captures"]
        ]
        digests = {path: runner.sha(path) for path in paths}
        for dimension in ("width", "height"):
            with self.subTest(dimension=dimension):
                kind = f"capture-{dimension}-overflow"
                diagnostic = "Conditional capture icon observations invalid: desktop"
                self.assertEqual(runner.CONTROL_DIAGNOSTICS[kind], diagnostic)
                self.packet = copy.deepcopy(original)
                runner.corrupt(self.packet, kind)
                expected = copy.deepcopy(original)
                case = next(
                    c
                    for c in expected["gates"]["conditional-browser"]["browser"]["cases"]
                    if c["id"] == "gap-ambiguity" and c["theme"] == "stock"
                )
                case["captures"][0]["icons"]["glyphs"][0][dimension] = 10**400
                self.assertEqual(self.packet, expected)
                observations = [(handoff, self.cli(handoff)) for handoff in (False, True)]
                for handoff, result in observations:
                    self.assertEqual(
                        (result.returncode, result.stdout, result.stderr),
                        (1, "", f"MATRIX_REJECTED: {diagnostic}\n"),
                        f"{kind}, handoff={handoff}",
                    )
        self.packet = original
        self.assertEqual({path: runner.sha(path) for path in paths}, digests)

    def test_current_three_stock_and_explicit_empty_native_are_valid(self):
        self.assertEqual([c["device"]["id"] for c in self.case()["captures"]], ["desktop", "mobile", "tablet"])
        self.assertEqual(self.case("native")["captures"], [])
        runner.validate_browser(self.conditional())

    def test_missing_capture_inventory_rejects_aggregate_cli_and_handoff(self):
        self.case()["captures"] = []
        self.assert_rejected_everywhere("Conditional capture inventory")

    def test_exact_stock_and_native_inventories(self):
        original = copy.deepcopy(self.conditional())
        mutations = [
            lambda c: c["captures"].pop(),
            lambda c: c["captures"].append(copy.deepcopy(c["captures"][0])),
            lambda c: c["captures"].__setitem__(1, copy.deepcopy(c["captures"][0])),
            lambda c: c["captures"][0]["device"].__setitem__("id", "other"),
        ]
        for alter in mutations:
            self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
            alter(self.case())
            with self.assertRaisesRegex(ValueError, "Conditional capture inventory"):
                runner.validate_browser(self.conditional())
        for missing in (True, False):
            with self.subTest(native_missing=missing):
                self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
                if missing:
                    self.case("native").pop("captures")
                else:
                    self.case("native")["captures"] = copy.deepcopy(self.case()["captures"])
                with self.assertRaisesRegex(ValueError, "Conditional capture inventory"):
                    runner.validate_browser(self.conditional())
        self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
        self.case()["theme"] = "native"
        with self.assertRaisesRegex(ValueError, "browser case"):
            runner.validate_browser(self.conditional())

    def test_device_viewport_and_containment_observations(self):
        original = copy.deepcopy(self.conditional())
        mutations = [
            (lambda c: c["device"].__setitem__("width", 375), "device"),
            (lambda c: c["device"].__setitem__("height", 812), "device"),
            (lambda c: c["device"].__setitem__("deviceScaleFactor", 2), "device"),
            (lambda c: c["device"].__setitem__("hasTouch", True), "device"),
            (lambda c: c["device"].__setitem__("isMobile", "false"), "device"),
            (lambda c: c.__setitem__("viewport", "width=1440"), "viewport"),
            (lambda c: c["document"].__setitem__("clientWidth", 0), "containment"),
            (lambda c: c["document"].__setitem__("innerWidth", 375), "containment"),
            (lambda c: c["document"].__setitem__("scrollWidth", 1441), "containment"),
        ]
        for alter, pattern in mutations:
            with self.subTest(pattern=pattern):
                self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
                alter(self.case()["captures"][0])
                with self.assertRaisesRegex(ValueError, "Conditional capture " + pattern):
                    runner.validate_browser(self.conditional())
        self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
        assertion = next(a for a in self.case()["assertions"] if a["id"] == "responsive-containment")
        assertion["detail"][0]["innerWidth"] = 375
        with self.assertRaisesRegex(ValueError, "Conditional capture containment"):
            runner.validate_browser(self.conditional())

    def test_missing_or_false_rendered_icon_observations(self):
        original = copy.deepcopy(self.conditional())
        mutations = [
            lambda c: c.pop("icons"),
            lambda c: c["icons"].__setitem__("loaded", False),
            lambda c: c["icons"].__setitem__("glyphs", []),
            lambda c: c["icons"]["glyphs"][0].__setitem__("content", "none"),
            lambda c: c["icons"]["glyphs"][0].__setitem__("family", ""),
            lambda c: c["icons"]["glyphs"][0].__setitem__("width", 0),
            lambda c: c["icons"]["glyphs"][0].__setitem__("height", -1),
            lambda c: c["icons"]["glyphs"][0].__setitem__("width", float("nan")),
        ]
        for alter in mutations:
            self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
            alter(self.case()["captures"][0])
            with self.assertRaisesRegex(ValueError, "Conditional capture icon observations"):
                runner.validate_browser(self.conditional())

    def test_stale_digest_rejects_despite_historical_canonical_success(self):
        self.assertEqual(self.conditional()["canonical_check"]["returncode"], 0)
        self.case()["captures"][0]["sha256"] = "0" * 64
        self.assert_rejected_everywhere("Conditional capture digest")

    def test_paths_are_bounded_and_distinct(self):
        original = copy.deepcopy(self.conditional())
        first = self.case()["captures"][0]
        absolute = str(runner.ROOT / first["path"])
        paths = [absolute, ".planning/ui-reviews/06.4-gap-repair/../06.4-gap-repair/desktop.png", "tests/desktop.png"]
        for path in paths:
            with self.subTest(path=path):
                self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
                self.case()["captures"][0]["path"] = path
                with self.assertRaisesRegex(ValueError, "Conditional capture path"):
                    runner.validate_browser(self.conditional())
        self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
        self.case()["captures"][1]["path"] = self.case()["captures"][0]["path"]
        with self.assertRaisesRegex(ValueError, "Conditional capture path"):
            runner.validate_browser(self.conditional())
        with tempfile.TemporaryDirectory(dir=runner.ROOT / ".planning/ui-reviews/06.4-gap-repair") as directory:
            link = Path(directory) / "escape.png"
            target = self.directory / "outside.png"
            target.write_bytes((runner.ROOT / first["path"]).read_bytes())
            link.symlink_to(target)
            self.packet["gates"]["conditional-browser"] = copy.deepcopy(original)
            self.case()["captures"][0]["path"] = str(link.relative_to(runner.ROOT))
            with self.assertRaisesRegex(ValueError, "Conditional capture path"):
                runner.validate_browser(self.conditional())

    def test_changed_deleted_or_non_png_owned_bytes_reject_without_touching_originals(self):
        capture = self.case()["captures"][0]
        original = runner.ROOT / capture["path"]
        digest = runner.sha(original)
        with tempfile.TemporaryDirectory(dir=runner.ROOT / ".planning/ui-reviews/06.4-gap-repair") as directory:
            owned = Path(directory) / "desktop.png"
            owned.write_bytes(original.read_bytes())
            capture["path"] = str(owned.relative_to(runner.ROOT))
            runner.validate_browser(self.conditional())
            owned.write_bytes(owned.read_bytes() + b"damaged")
            with self.assertRaisesRegex(ValueError, "Conditional capture digest"):
                runner.validate_browser(self.conditional())
            owned.write_bytes(b"not a PNG")
            capture["sha256"] = runner.sha(owned)
            with self.assertRaisesRegex(ValueError, "Conditional capture PNG"):
                runner.validate_browser(self.conditional())
            owned.unlink()
            with self.assertRaisesRegex(ValueError, "Conditional capture bytes"):
                runner.validate_browser(self.conditional())
        self.assertEqual(runner.sha(original), digest)

    def test_historical_human_markers_stay_pending(self):
        for identity in ("H1", "H2"):
            self.case()["humanReview"][identity] = "accepted"
            with self.assertRaisesRegex(ValueError, "Conditional capture human review"):
                runner.validate_browser(self.conditional())
            self.case()["humanReview"][identity] = "pending"


class EvidenceRefresh(CompletePacketFixture, unittest.TestCase):
    """Owned synthetic envelopes exercise real CLI validators, never acceptance."""

    def test_invalid_runtime_preflight_preserves_outputs(self):
        output = self.directory / "new" / "results.json"
        result = subprocess.run(
            [
                sys.executable,
                str(HERE / "run.py"),
                "--refresh-from",
                str(HERE.parent / "18-evidence/results.json"),
                "--output",
                str(output),
            ],
            env={**runner.os.environ, "CV_FOCUS_PYTHON": "/missing/refresh-python"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("CV_FOCUS_PYTHON='/missing/refresh-python'", result.stderr)
        self.assertFalse(output.parent.exists())

    def refreshed_fixture(self):
        origin = HERE.parent / "18-evidence/results.json"
        request = runner.capture_request()
        packet = runner.prepare_refresh(origin, self.manifest, request)
        packet["test_fixture"] = "Synthetic fresh gate observations; never acceptance evidence"
        packet["gates"].update({k: self.packet["gates"][k] for k in runner.FRESH_GATES})
        for label in runner.FRESH_GATES:
            packet["gates"][label].update(started=runner.now(), finished=runner.now())
        packet.update(completed=True, finished=runner.now())
        packet["checker_controls"] = self.packet["checker_controls"]
        packet["checker_control_evidence"] = self.packet["checker_control_evidence"]
        self.packet = packet
        return packet

    def test_original_gate_survives_real_refresh_cli_check_and_handoff(self):
        # Only fresh execution is replaced by explicitly synthetic test records.
        # main(), provenance, complete aggregate, controls and handoff are real.
        fixtures = self.directory / "synthetic-fresh.json"
        runner.write_json(
            fixtures,
            {
                k: dict(self.packet["gates"][k], test_fixture="Synthetic observations; never acceptance evidence")
                for k in ("evidence-self-tests", "ruff-check", "ruff-format")
            },
        )
        script = (
            "import importlib.util,json,sys; "
            "s=importlib.util.spec_from_file_location('refresh_cli',sys.argv[1]); "
            "r=importlib.util.module_from_spec(s); s.loader.exec_module(r); "
            "f=json.load(open(sys.argv[2])); "
            "r.quality_gate=lambda name,selection=None:dict(f[name],started=r.now(),finished=r.now()); "
            "sys.argv=[sys.argv[1],*sys.argv[3:]]; sys.exit(r.main())"
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(HERE / "run.py"),
                str(fixtures),
                "--refresh-from",
                str(HERE.parent / "18-evidence/results.json"),
                "--output",
                str(self.output),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.packet = runner.load_json(self.output)
        original = runner.load_json(HERE.parent / "18-evidence/results.json")
        for name in set(original["gates"]) - set(runner.FRESH_GATES):
            self.assertEqual(self.packet["gates"][name], original["gates"][name], name)
        self.assertEqual(self.cli().returncode, 0)
        result = self.cli(handoff=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["ready"])

    def test_source_continuity_rejects_product_runtime_and_path_set_changes(self):
        original = runner.load_json(HERE.parent / "18-evidence/source-manifest.json")
        for label, mutate in (
            ("product", lambda m: m["files"].__setitem__("README.md", "0" * 64)),
            ("addition", lambda m: m["files"].__setitem__("tests/invented.py", "0" * 64)),
            ("deletion", lambda m: m["files"].pop("README.md")),
        ):
            with self.subTest(label=label):
                changed = copy.deepcopy(self.manifest)
                mutate(changed)
                with self.assertRaisesRegex(ValueError, "Refresh source inputs differ"):
                    runner.validate_continuity(original, changed)
        runner.validate_continuity(original, self.manifest)

    def test_changed_effective_selection_rejects_before_output_writes(self):
        request = runner.capture_request()
        request["selections"]["javascript"] = copy.deepcopy(request["selections"]["javascript"])
        request["selections"]["javascript"]["environment"]["CI"] = "invented"
        with self.assertRaisesRegex(ValueError, "Refresh runtime/command selection changed: javascript"):
            runner.prepare_refresh(HERE.parent / "18-evidence/results.json", self.manifest, request)

    def test_missing_fresh_gates_controls_and_forged_timestamps_reject_everywhere(self):
        packet = copy.deepcopy(self.refreshed_fixture())
        mutations = (
            (lambda p: p["gates"].pop("evidence-self-tests"), "Missing/extra matrix gates"),
            (lambda p: p.pop("checker_control_evidence"), "Checker control evidence inventory"),
            (lambda p: p["gates"]["javascript"].__setitem__("started", runner.now()), "Retained gate changed"),
            (lambda p: p.__setitem__("completed", False), "Incomplete matrix"),
        )
        for mutate, pattern in mutations:
            with self.subTest(pattern=pattern):
                self.packet = copy.deepcopy(packet)
                mutate(self.packet)
                self.assert_rejected_everywhere(pattern)

    def test_changed_product_input_and_command_reject_real_refresh_cli(self):
        original = runner.load_json(HERE.parent / "18-evidence/results.json")
        for kind, pattern in (
            ("product", "Refresh source inputs differ: README.md"),
            ("command", "javascript: wrong quality command"),
        ):
            with self.subTest(kind=kind):
                packet = copy.deepcopy(original)
                if kind == "product":
                    manifest = packet["source_manifest"]
                    manifest["files"]["README.md"] = "0" * 64
                    manifest["sha256"] = runner.hashlib.sha256(
                        json.dumps(manifest["files"], sort_keys=True).encode()
                    ).hexdigest()
                else:
                    packet["gates"]["javascript"]["command"].insert(3, "-t=one")
                origin = self.directory / kind / "results.json"
                output = self.directory / (kind + "-output") / "results.json"
                runner.write_json(origin, packet)
                runner.write_json(origin.parent / "source-manifest.json", packet["source_manifest"])
                result = subprocess.run(
                    [sys.executable, str(HERE / "run.py"), "--refresh-from", str(origin), "--output", str(output)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(pattern, result.stderr)
                self.assertFalse(output.parent.exists())

    def test_mutated_origin_and_missing_manifest_reject_everywhere(self):
        self.refreshed_fixture()
        origin = runner.load_json(HERE.parent / "18-evidence/results.json")
        owned = self.directory / "origin" / "results.json"
        runner.write_json(owned, origin)
        reference = {"path": str(owned.relative_to(runner.ROOT)), "sha256": runner.sha(owned)}
        self.packet["retained_from"]["results"] = reference
        self.assert_rejected_everywhere("Missing.*original.*manifest")
        runner.write_json(owned.parent / "source-manifest.json", origin["source_manifest"])
        self.packet["retained_from"]["source_manifest"] = {
            "path": str((owned.parent / "source-manifest.json").relative_to(runner.ROOT)),
            "sha256": runner.sha(owned.parent / "source-manifest.json"),
        }
        owned.write_text(owned.read_text() + "\n")
        self.assert_rejected_everywhere("Retained origin hash mismatch")


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

    def test_wr05_is_required_for_g6(self):
        self.assertIn("WR-05", self.data["findings"])
        self.assertIn("WR-05", self.data["findings"]["G6"]["review_ids"])
        self.assertIn("T-06.4-41", self.data["findings"]["G6"]["threats"])
        self.assertIn("T-06.4-41", self.data["findings"]["WR-05"]["threats"])
        self.assertIn("T-06.4-41", self.data["threats"])
        result = runner.validate_handoff(self.data)
        self.assertEqual(result, {"structurally_valid": True, "ready": False, "disposition": "not-ready"})
        missing = copy.deepcopy(self.data)
        missing["findings"].pop("WR-05")
        with self.assertRaisesRegex(ValueError, "^Missing/extra G/CR/WR handoff finding$"):
            runner.validate_handoff(missing)
        unlinked = copy.deepcopy(self.data)
        unlinked["findings"]["G6"]["review_ids"].remove("WR-05")
        with self.assertRaisesRegex(ValueError, "^Missing canonical finding links: G6$"):
            runner.validate_handoff(unlinked)

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
