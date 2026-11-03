"""Fail closed on incomplete, inconsistent or unexpectedly excluded plan-16 gates."""

import argparse
import ast
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from run import CSP, GOLDEN, HERE, REPAIRS, RETAINED, ROOT, SERIES, recipes, sha, source


def identity(runtime):
    return {key: value for key, value in runtime.items() if key != "imports"}


def load(label, kind, series, expected):
    record = json.loads((HERE / f"{label}.json").read_text())
    assert record["status"] == "complete" and record["exit_code"] == 0, (label, "incomplete/nonzero")
    assert record["finished"] >= record["started"] and record["duration_seconds"] > 0, label
    assert record["source_sha256"] == record["source_after_sha256"] == source()["sha256"], label
    # Preserve the exact checker captured by early sessions, then independently validate with this stricter revision.
    assert record["tools"]["run.py"] == sha(HERE / "run.py"), label
    assert record["tools"]["check.py"] in {sha(HERE / "check.py"), sha(HERE / "capture-check.py")}, label
    for suffix, digest in record["artifacts"].items():
        assert sha(HERE / f"{label}.{suffix}") == digest, (label, suffix)
    assert "log" in record["artifacts"], label
    if not kind:
        assert record["argv"] == expected and record["series"] is None, label
        log = re.sub(r"\x1b\[[0-9;]*m", "", (HERE / f"{label}.log").read_text())
        if label == "javascript":
            assert re.search(r"Tests\s+234 passed", log) and re.search(r"Test Files\s+8 passed", log), label
            assert "06-js-verify: node v24.21.0" in log, label
        elif label == "strict-docs":
            assert "Documentation built in" in log and "WARNING" not in log and "ERROR" not in log, label
        elif label == "ruff-check":
            assert "All checks passed!" in log, label
        else:
            assert re.search(r"\d+ files? already formatted", log), label
        return record, None
    assert record["pytest_argv"] == expected + (
        ["--junitxml=" + str(HERE / f"{label}.xml")] if kind == "test" else []
    ), label
    assert record["series"] == series and record["kind"] == kind, label
    assert record["argv"] == [
        SERIES[series],
        str((HERE / "run.py").relative_to(ROOT)),
        "_pytest",
        str(HERE / f"{label}.nodes.json"),
        *record["pytest_argv"],
    ], label
    assert record["environment"]["PYTHONPATH"] == str(ROOT / "src") + ":" + str(ROOT), label
    assert "nodes.json" in record["artifacts"], label
    nodes = json.loads((HERE / f"{label}.nodes.json").read_text())
    assert nodes["exit_code"] == 0 and nodes["nodes"] and len(set(nodes["nodes"])) == len(nodes["nodes"]), label
    runtime = nodes["runtime"]
    assert runtime["django"].startswith(series + "."), label
    assert Path(runtime["executable"]) == ROOT / SERIES[series], label
    for name, imported in [*runtime["packages"].items(), *runtime["imports"].items()]:
        path = Path(imported["path"])
        assert path.is_relative_to(ROOT / "src") and sha(path) == imported["sha256"], (label, name)
    for required in ("crud_views.lib.deletion", "crud_views.lib.views.delete", "crud_views_guardian.lib.viewset"):
        assert required in runtime["imports"], (label, required)
    expected_deselected = [GOLDEN] if label.endswith("-full") and series in ("4.2", "6.0") else []
    assert nodes["deselected"] == expected_deselected, (label, nodes["deselected"])
    if kind == "collect":
        assert not nodes["outcomes"], label
    else:
        outcomes = nodes["outcomes"]
        assert {row["node"] for row in outcomes} == set(nodes["nodes"]), (label, "missing outcomes")
        assert len(outcomes) == len(nodes["nodes"]), label
        assert all(row["outcome"] in ("passed", "skipped") and row["xfail"] is None for row in outcomes), label
        skips = [row for row in outcomes if row["outcome"] == "skipped"]
        expected_skips = [CSP] if label.endswith("-full") and series in ("4.2", "5.2") else []
        assert [row["node"] for row in skips] == expected_skips, (label, skips)
        assert all("built-in CSP middleware requires Django 6.0" in row["reason"] for row in skips), label
        assert "xml" in record["artifacts"], label
        junit = ET.parse(HERE / f"{label}.xml").getroot()
        cases = junit.findall(".//testcase")
        assert (
            len(cases) == len(nodes["nodes"]) and not junit.findall(".//failure") and not junit.findall(".//error")
        ), label
        assert len(junit.findall(".//skipped")) == len(skips), label
        junit_nodes = {case.attrib["classname"].replace(".", "/") + ".py::" + case.attrib["name"] for case in cases}
        assert junit_nodes == set(nodes["nodes"]), (label, "JUnit node mismatch")
    print(
        json.dumps(
            {
                "label": label,
                "nodes": len(nodes["nodes"]),
                "outcomes": dict(Counter(row["outcome"] for row in nodes["outcomes"])),
                "deselected": nodes["deselected"],
                "seconds": record["duration_seconds"],
            }
        )
    )
    return record, nodes


def check(group):
    assert json.loads((HERE / "source-manifest.json").read_text()) == source(), "source manifest drift"
    required = json.loads((HERE.parent / "09-evidence/expected-nodes.json").read_text())["required_families"]
    required = {key: set(value) for key, value in required.items()}
    for filename in REPAIRS + RETAINED:
        module = "tests/test1/" + filename
        required.setdefault(module, set()).update(
            node.name
            for node in ast.parse((ROOT / module).read_text()).body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        )
    reference = None
    full_reference = None
    for series in SERIES:
        sessions = {}
        for label, argv, kind in recipes("focused", series):
            _, sessions[label.rsplit("-", 1)[1]] = load(label, kind, series, argv)
        collected = set(sessions["collect"]["nodes"])
        assert collected == set(sessions["repairs"]["nodes"]) | set(sessions["retained"]["nodes"]), series
        for module, names in required.items():
            for name in names:
                assert any(
                    node == f"{module}::{name}" or node.startswith(f"{module}::{name}[") for node in collected
                ), (series, module, name)
        assert reference is None or reference == collected, (series, "focused collection differs")
        reference = collected
        identities = [identity(sessions[name]["runtime"]) for name in sessions]
        assert all(identity == identities[0] for identity in identities[1:]), (series, "runtime drift")
        if group == "all":
            for label, argv, kind in recipes("full", series):
                _, full = load(label, kind, series, argv)
                assert identity(full["runtime"]) == identities[0], (series, "full runtime drift")
                assert collected <= set(full["nodes"]), (series, "focused nodes absent from full suite")
                full_nodes = set(full["nodes"]) | set(full["deselected"])
                assert full_reference is None or full_reference == full_nodes, (series, "full collection differs")
                full_reference = full_nodes
    if group == "all":
        for label, argv, kind in recipes("quality", None):
            load(label, kind, None, argv)
    print(
        f"GAP_MATRIX_OK group={group} focused_nodes={len(reference)} "
        f"required_families={sum(map(len, required.values()))} source={source()['sha256']}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("focused", "all"), required=True)
    check(parser.parse_args().group)
