"""Hermetic companion evidence tests; no production companion or Django imports."""

import ast
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "theme_adoption_sources", Path(__file__).with_name("theme_adoption_sources.py")
)
sources = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sources
SPEC.loader.exec_module(sources)


def test_floor_selection_covers_theme_modules():
    tree = ast.parse((Path(__file__).resolve().parents[2] / "noxfile.py").read_text())
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"CRISPY_FLOOR_TESTS", "CRISPY_FLOOR_DESELECT"}
    }
    required = {
        "tests/test1/" + name
        for name in (
            "test_theme_form_ownership.py",
            "test_theme_label_modes.py",
            "test_theme_action_groups.py",
            "test_theme_form_requests.py",
            "test_theme_adoption_docs.py",
            "test_alerts.py",
            "test_button_classes.py",
        )
    }
    assert required <= set(assignments["CRISPY_FLOOR_TESTS"])
    assert assignments["CRISPY_FLOOR_DESELECT"] == [
        "--deselect",
        "tests/test1/test_form_buttons_golden.py::test_filter_form_baseline",
    ]


@pytest.fixture(autouse=True)
def no_companion_environment(monkeypatch):
    for key in ("CV_THEME_SOURCE", "CV_PACK_SOURCE", "CV_THEME_CORE_BASE", "CV_THEME_PYTHON", "CV_FOCUS_PYTHON"):
        monkeypatch.delenv(key, raising=False)


def test_missing_sources_fail_closed(tmp_path):
    with pytest.raises(sources.EvidenceError, match="source"):
        sources.inspect_sources(tmp_path / "absent", "abc", "https://example.invalid/theme.git")


def test_working_inventory_excludes_generated_egg_info_without_deleting_it(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/package.py").write_text("actual source")
    metadata = tmp_path / "src/package.egg-info"
    metadata.mkdir()
    (metadata / "PKG-INFO").write_text("editable runtime metadata")
    assert sources.working_files(tmp_path) == {"src/package.py": b"actual source"}
    assert (metadata / "PKG-INFO").read_text() == "editable runtime metadata"


@pytest.mark.parametrize("target", ["CLAUDE.md", "../private", "/etc/passwd", "absent.md", "AGENTS.md"])
def test_archive_materializes_only_internal_regular_file_links(tmp_path, target):
    root, _ = repository(tmp_path / "linked", {"CLAUDE.md": b"project instructions"})
    (root / "AGENTS.md").symlink_to(target)
    run_git(root, "add", "AGENTS.md")
    run_git(root, "commit", "-m", "link")
    revision = run_git(root, "rev-parse", "HEAD")
    if target == "CLAUDE.md":
        assert sources.archive_files(root, revision)["AGENTS.md"] == b"project instructions"
    else:
        with pytest.raises(sources.EvidenceError, match="symlink"):
            sources.archive_files(root, revision)


ORIGIN = "https://example.invalid/theme.git"
FILES = {
    "src/crud_views_tabler/templates/crud_views/modal/shell.html": b"<div>modal</div>",
    "src/crud_views_tabler/templates/crud_views/tags/alert.html": b"<div>alert</div>",
    "src/crud_views_tabler/checks.py": b"def check_tabler_icons():\n    return []\n",
    "src/crud_views_tabler/icons.py": b'TABLER_ICONS = {"detail": "tabler:eye"}\ndef render():\n    return "svg"\n',
    "src/django_tabler/templates/crispy_tabler/field.html": b"field",
    "src/django_tabler/crispy/layout.py": b"class Group:\n    pass\n",
    "example/config/settings.py": b'SECRET_KEY = "pinned-test-key"\n',
}
CORE_FILES = {
    "src/crud_views/templates/" + p.split("/templates/", 1)[1]: b"core" for p in FILES if "/templates/crud_views/" in p
}


def run_git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


def repository(path, files=None):
    path.mkdir(parents=True)
    run_git(path, "init", "-b", "fixture")
    run_git(path, "config", "user.name", "Evidence Test")
    run_git(path, "config", "user.email", "fixture@example.invalid")
    run_git(path, "remote", "add", "origin", ORIGIN)
    for name, content in (files or FILES).items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    run_git(path, "add", ".")
    run_git(path, "commit", "-m", "fixture baseline")
    return path, run_git(path, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    return repository(tmp_path / "recorded companion with spaces")


def manifest_for(root, revision):
    return {"companion_root": str(root), "revision": revision, "origin": ORIGIN, "components": dict(sources.COMPONENTS)}


def runtime():
    return {
        "python": [3, 14, 7],
        "prefix": "/runtime with spaces/.venv",
        "versions": {
            "Django": "6.1.2",
            "django-crispy-forms": "2.7",
            "crispy-bootstrap5": "2026.9",
            "pytest": "9.0",
            "pytest-django": "4.11",
            "pytest-xdist": "3.8",
        },
        "missing": [],
    }


def test_import_is_pure(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("source access at import time")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "resolve", forbidden)
    spec = importlib.util.spec_from_file_location("pure_theme_sources", sources.__file__)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)


@pytest.mark.parametrize("sibling", ["absent", "unrelated"])
def test_recorded_root_ignores_sibling_checkout(repo, tmp_path, monkeypatch, sibling):
    root, revision = repo
    isolated = tmp_path / "isolation/core"
    script = isolated / "tests/browser/theme_adoption_sources.py"
    script.parent.mkdir(parents=True)
    script.write_text(Path(sources.__file__).read_text())
    target = isolated / sources.PHASE_DIR / sources.BASELINE_NAME
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(manifest_for(root, revision)))
    if sibling == "unrelated":
        repository(isolated.parent / "tabler-test")
    monkeypatch.setattr(sources, "__file__", str(script))
    assert sources.resolve_recorded_source() == root


@pytest.mark.parametrize(
    "case", ["absent", "relative", "unrelated", "theme-conflict", "pack-conflict", "origin", "revision"]
)
def test_source_identity_refuses_conflicts(repo, tmp_path, case):
    root, revision = repo
    manifest = manifest_for(root, revision)
    operand, env = "recorded", {}
    if case == "absent":
        manifest["companion_root"] = str(tmp_path / "absent")
    elif case == "relative":
        operand = "../tabler-test"
    elif case == "unrelated":
        operand = str(tmp_path / "other")
    elif case.endswith("conflict"):
        env["CV_THEME_SOURCE" if case.startswith("theme") else "CV_PACK_SOURCE"] = str(tmp_path / "other")
    elif case == "origin":
        manifest["origin"] = "https://wrong.invalid/source.git"
    else:
        manifest["revision"] = "0" * 40
    with pytest.raises(sources.EvidenceError):
        sources.resolve_recorded_source(operand, manifest=manifest, env=env)


def test_runtime_unset_overrides_preserve_venv_symlink_path():
    manifest = {"companion_python": "/runtime with spaces/.venv/bin/python", "runtime": runtime()}
    seen = []

    def probe(path):
        seen.append(str(path))
        return runtime()

    assert str(sources.resolve_companion_python(manifest, env={}, probe=probe)) == manifest["companion_python"]
    assert seen == [manifest["companion_python"]]


@pytest.mark.parametrize("bad", [None, "", "relative/python"])
def test_missing_or_relative_recorded_runtime_fails(bad):
    with pytest.raises(sources.EvidenceError):
        sources.resolve_companion_python({"companion_python": bad}, env={}, probe=lambda _: runtime())


@pytest.mark.parametrize("name", ["CV_THEME_PYTHON", "CV_FOCUS_PYTHON"])
@pytest.mark.parametrize("value", ["", "relative", "/wrong/.venv/bin/python"])
def test_runtime_override_conflicts_fail(name, value):
    manifest = {"companion_python": "/correct/.venv/bin/python", "runtime": runtime()}
    with pytest.raises(sources.EvidenceError):
        sources.resolve_companion_python(manifest, env={name: value}, probe=lambda _: runtime())


@pytest.mark.parametrize("mutation", ["python", "django", "prefix", "missing", "version"])
def test_changed_runtime_is_not_accepted(mutation):
    observed = runtime()
    if mutation == "python":
        observed["python"] = [3, 12, 3]
    elif mutation == "django":
        observed["versions"]["Django"] = "6.0.9"
    elif mutation == "prefix":
        observed["prefix"] = "/different/.venv"
    elif mutation == "missing":
        observed["missing"] = ["xdist"]
    else:
        observed["versions"]["pytest"] = "9.1"
    with pytest.raises(sources.EvidenceError):
        sources.resolve_companion_python(
            {"companion_python": "/recorded/python", "runtime": runtime()}, env={}, probe=lambda _: observed
        )


def test_missing_runtime_executable_fails(tmp_path):
    with pytest.raises(sources.EvidenceError, match="executable missing"):
        sources.runtime_probe(tmp_path / "missing")


def test_complete_independent_inventory_passes():
    report = sources.classify_tree(FILES, CORE_FILES)
    purposes = sources.validate_classifications(report, FILES, CORE_FILES)
    assert "src/crud_views_tabler/checks.py#check_tabler_icons" in purposes
    assert len(report["shadows"]) == 2
    icon_sections = report["classifications"]["src/crud_views_tabler/icons.py"]["sections"]
    assert {row["kind"] for row in icon_sections} == {"required", "adoption"}


@pytest.mark.parametrize("mutation", ["modal", "checks", "added", "hash", "relabel", "symbol", "shadow"])
def test_inventory_omissions_fail_against_real_tree(mutation):
    files = dict(FILES)
    report = sources.classify_tree(files, CORE_FILES)
    if mutation in {"modal", "checks"}:
        path = "src/crud_views_tabler/" + (
            "templates/crud_views/modal/shell.html" if mutation == "modal" else "checks.py"
        )
        report["tracked_tree"].pop(path)
        report["classifications"].pop(path)
        report["shadows"].pop(path, None)
    elif mutation == "added":
        files["src/crud_views_tabler/new_behavior.py"] = b"def hidden():\n    return True\n"
    elif mutation == "hash":
        files["src/crud_views_tabler/checks.py"] += b"# changed\n"
    elif mutation == "relabel":
        report["classifications"]["src/crud_views_tabler/checks.py"]["sections"][0]["kind"] = "adoption"
    elif mutation == "symbol":
        report["classifications"]["src/crud_views_tabler/icons.py"]["sections"].pop()
    else:
        report["shadows"] = {}
    with pytest.raises(sources.EvidenceError):
        sources.validate_classifications(report, files, CORE_FILES)


def test_new_data_registration_does_not_grow_required_purposes():
    after = {**FILES, "src/crud_views_tabler/buttons.py": b'TABLER_BUTTON_CLASSES = {"alert:close": "close"}\n'}
    result = sources.compare_purposes(
        sources.classify_tree(FILES, CORE_FILES), sources.classify_tree(after, CORE_FILES), FILES, after, CORE_FILES
    )
    assert result["before"] == result["after"]


def test_retired_copy_requires_rendered_public_adoption():
    old_path = "src/crud_views_tabler/templates/crud_views/tags/alert.html"
    after = {p: v for p, v in FILES.items() if p != old_path}
    after["src/crud_views_tabler/buttons.py"] = b'TABLER_BUTTON_CLASSES = {"alert:close": "close"}\n'
    before_report, after_report = sources.classify_tree(FILES, CORE_FILES), sources.classify_tree(after, CORE_FILES)
    retired = {
        old_path + "#file": {
            "passed": True,
            "assertions": [{"passed": True}],
            "adoption_paths": ["src/crud_views_tabler/buttons.py"],
        }
    }
    result = sources.compare_purposes(before_report, after_report, FILES, after, CORE_FILES, retired)
    assert result["after"] == result["before"] - 1
    with pytest.raises(sources.EvidenceError, match="retired"):
        sources.compare_purposes(before_report, after_report, FILES, after, CORE_FILES)


def test_renamed_behavior_retains_purpose_identity():
    old = "src/crud_views_tabler/checks.py"
    new = "src/crud_views_tabler/new_checks.py"
    after = {new if p == old else p: v for p, v in FILES.items()}
    old_report, new_report = sources.classify_tree(FILES, CORE_FILES), sources.classify_tree(after, CORE_FILES)
    with pytest.raises(sources.EvidenceError, match="new required"):
        sources.compare_purposes(old_report, new_report, FILES, after, CORE_FILES)
    new_report["classifications"][new]["sections"][0]["purpose_id"] = old + "#check_tabler_icons"
    assert sources.compare_purposes(old_report, new_report, FILES, after, CORE_FILES)["before"] > 0


def command(stdout="1 passed in 0.1s\n", *, code=0, stderr="", argv=None, cwd="/removed/tmp"):
    record = {
        "argv": argv or ["/test/python", "-m", "pytest", "tests", "-n", "4", "-q"],
        "cwd": str(cwd),
        "exit_code": code,
        "stdout": stdout,
        "stderr": stderr,
    }
    record["log_sha256"] = sources.digest(record)
    return record


@pytest.mark.parametrize("mutation", ["runtime", "selection", "duplicate", "cwd"])
def test_exact_suite_commands_cannot_be_replaced_by_other_passing_logs(mutation):
    report = {
        "isolated_roots": {"companion": "/removed/tmp"},
        "suites": [{"command": command(argv=argv)} for argv in sources.suite_commands("/test/python")],
    }
    sources.validate_suite_commands(report, "/test/python")
    if mutation == "runtime":
        report["suites"][0]["command"]["argv"][0] = "/other/python"
    elif mutation == "selection":
        report["suites"][1]["command"]["argv"][3] = "tests/test_one.py"
    elif mutation == "duplicate":
        report["suites"][0] = report["suites"][1]
    else:
        report["suites"][1]["command"]["cwd"] = "/production/source"
    with pytest.raises(sources.EvidenceError, match="wrong suite"):
        sources.validate_suite_commands(report, "/test/python")


@pytest.mark.parametrize("output", ["", "no tests ran in 0.1s\n", "0 passed in 0.1s\n"])
def test_empty_suite_results_fail(output):
    with pytest.raises(sources.EvidenceError, match="zero collected"):
        sources.suite_result(command(output))


def test_baseline_failure_is_retained_not_promoted():
    record = command("FAILED tests/test_pack.py::test_field - AssertionError\n1 failed, 2 passed in 0.2s\n", code=1)
    assert sources.suite_result(record) == {
        "count": 3,
        "outcome": "failed",
        "failures": ["tests/test_pack.py::test_field"],
    }
    with pytest.raises(sources.EvidenceError, match="required suite failed"):
        sources.suite_result(record, passing=True)


def test_tampered_logs_and_private_values():
    record = command()
    record["stdout"] = "20 passed in 0.1s"
    with pytest.raises(sources.EvidenceError, match="tampered"):
        sources.validate_log(record)
    sanitized = sources.sanitize(
        "SECRET_KEY=private-value test_pack.py::test_field PASSED hidden-value", ["hidden-value"]
    )
    assert "private-value" not in sanitized and "hidden-value" not in sanitized
    assert "test_pack.py::test_field PASSED" in sanitized


def adopted_files():
    files = dict(FILES)
    files["src/crud_views_tabler/buttons.py"] = b'TABLER_BUTTON_CLASSES = {"form:submit": "btn"}\n'
    baseline = dict(files)
    values = {"form:submit": "btn", **sources.ADOPTION_CLASSES}
    files["src/crud_views_tabler/buttons.py"] = f"TABLER_BUTTON_CLASSES = {values!r}\n".encode()
    files["src/crud_views_tabler/icons.py"] = (
        f"TABLER_ICONS = {sources.ADOPTION_ICONS!r}\ndef render():\n    return 'svg'\n"
    ).encode()
    files["src/crud_views_tabler/apps.py"] = b'def ready():\n    register_label_mode_defaults({"form": "both"})\n'
    files["src/crud_views_tabler/tests.py"] = (
        f"class ButtonClassTests:\n    def test_table_values(self):\n        expected = {values!r}\n"
        "        self.assertEqual(TABLER_BUTTON_CLASSES, expected)\nclass ThemeAdoptionTests:\n    pass\n"
    ).encode()
    native = {name: ["native-path-" + name] for name in sources.ACTION_ICONS.values()}
    files["src/django_tabler/icons.py"] = f"ICONS = {native!r}\n".encode()
    baseline["src/django_tabler/icons.py"] = files["src/django_tabler/icons.py"]
    return baseline, files, native


def action_records(native):
    return [
        {
            "kind": kind,
            "mode": mode,
            "passed": True,
            "accessible_name": kind,
            "source_sha256": "fixture-source",
            "svg_paths": [] if mode == "label" else native[icon],
            "visible_text": mode != "icon",
            "hidden_text": mode == "icon",
            "font_awesome": False,
            "type": "reset" if kind == "filter-reset" else "button",
            "value": "Reset",
            "reset_restored": True,
            "submit_events": 0,
        }
        for kind, icon in sources.ACTION_ICONS.items()
        for mode in ("both", "icon", "label")
    ]


def cancel_records(native):
    return [
        {
            "destination": destination,
            "requested_tag": tag,
            "mode": mode,
            "activation": activation,
            "passed": True,
            "tag": "button",
            "type": "button",
            "href": None,
            "accessible_name": "Cancel",
            "svg_paths": [] if mode == "label" else native["arrow-left"],
            "submit_events": 0,
            "reset_events": 0,
            "post_requests": 0,
            "navigation_intercepted": False,
            "attribute_present": destination == "empty",
            "attribute_value": "" if destination == "empty" else None,
            "input_before": "edited",
            "input_after": "initial" if destination == "empty" else "edited",
            "navigation": "same-url-get" if destination == "empty" else "none",
            "document_replaced": destination == "empty",
            "document_method": "GET",
            "document_status": 200,
            "url_before": "http://127.0.0.1/form",
            "url_after": "http://127.0.0.1/form",
        }
        for destination in ("absent", "none", "empty")
        for tag in ("button", "a")
        for mode in ("both", "icon", "label")
        for activation in ("click", "Enter", "Space")
    ]


def phase_report(native):
    report = {
        "cases": [
            {"id": case, "passed": True, "assertions": [{"id": "actual-behavior", "passed": True}]}
            for case in sorted(sources.SCENARIOS)
        ],
        "actions": action_records(native),
        "cancel_no_url": cancel_records(native),
        "adoption": {
            "label_modes": {"form": "both"},
            "icons": sources.ADOPTION_ICONS,
            "classes": sources.ADOPTION_CLASSES,
        },
        "test_nodes": [{"id": name, "outcome": "passed"} for name in sources.FOCUSED_TESTS],
        "workflow_branches": [
            {
                "modal": modal,
                "has_workflow_choices": choices,
                "method": method,
                "passed": True,
                "status": 422 if modal and method == "POST" else 200,
                "forms": [{"attrs": {"class": "cv-form"}, "tokens": 1}] if modal or choices else [],
                "nested": [],
                "templates": [
                    {"name": name, "origin": "/isolated/src/owner/templates/" + name}
                    for name in (
                        ["crud_views/view_custom_form.content.html"]
                        if modal
                        else [
                            "crud_views_workflow/view_workflow.content.html",
                            "crud_views_workflow/view_workflow.action.html",
                        ]
                    )
                ],
            }
            for modal in (False, True)
            for choices in (False, True)
            for method in ("GET", "POST")
        ],
        "alert_branches": [
            {
                "native": native,
                "variant": variant,
                "activation": activation,
                "passed": True,
                "hook": {
                    "name": "Close",
                    "type": "button",
                    "native": "alert" if native else None,
                    "crud": None if native else "",
                },
                "adapter_calls": None if native else 1,
            }
            for native in (False, True)
            for variant in (("default",) if native else ("default", "custom", "empty"))
            for activation in ("click", "Enter", "Space")
        ],
    }
    for row in report["actions"] + report["cancel_no_url"]:
        row["source_sha256"] = sources.digest(sources.inventory(adopted_files()[1]))
    return report


def test_full_compatibility_records_pass():
    baseline, files, native = adopted_files()
    sources.validate_phase_evidence(phase_report(native), files, baseline)


@pytest.mark.parametrize("missing", ["workflow_branches", "alert_branches"])
def test_full_replay_rejects_missing_distinct_render_branches(missing):
    baseline, files, native = adopted_files()
    report = phase_report(native)
    report[missing].pop()
    with pytest.raises(sources.EvidenceError, match="missing distinct"):
        sources.validate_phase_evidence(report, files, baseline)


@pytest.mark.parametrize(
    "mutation",
    [
        "mapping",
        "floor",
        "class",
        "equality",
        "empty-svg",
        "wrong-svg",
        "missing-mode",
        "reset",
        "focused",
        "case",
        "text-floor",
    ],
)
def test_adoption_cannot_be_weakened_by_adjusting_totals(mutation):
    baseline, files, native = adopted_files()
    report = phase_report(native)
    if mutation == "mapping":
        files["src/crud_views_tabler/icons.py"] = b"TABLER_ICONS = {}\n"
    elif mutation == "floor":
        files["src/crud_views_tabler/apps.py"] = b'def ready():\n    register_label_mode_defaults({"form": "label"})\n'
    elif mutation == "class":
        files["src/crud_views_tabler/buttons.py"] = b"TABLER_BUTTON_CLASSES = {}\n"
    elif mutation == "equality":
        files["src/crud_views_tabler/tests.py"] = files["src/crud_views_tabler/tests.py"].replace(
            b"assertEqual", b"assertIn"
        )
    elif mutation in {"empty-svg", "wrong-svg"}:
        report["actions"][0]["svg_paths"] = [] if mutation == "empty-svg" else ["wrong-icon"]
    elif mutation == "missing-mode":
        report["actions"].pop()
    elif mutation == "reset":
        report["actions"][-1]["reset_restored"] = False
    elif mutation == "focused":
        report["test_nodes"].pop()
    elif mutation == "case":
        report["cases"].pop()
    else:
        report["adoption"] = {**report["adoption"], "label_modes": {"form": "label"}}
    report["total"] = len(report["actions"])
    with pytest.raises(sources.EvidenceError):
        sources.validate_phase_evidence(report, files, baseline)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "conflated",
        "anchor",
        "href",
        "submit",
        "reset",
        "wrong-icon",
        "empty-no-navigation",
        "intercepted",
        "empty-no-document",
        "lost-edits",
    ],
)
def test_cancel_no_url_branches_fail_independently(mutation):
    _, _, native = adopted_files()
    rows = cancel_records(native)
    absent, empty = rows[0], next(row for row in rows if row["destination"] == "empty")
    if mutation == "missing":
        rows.pop()
    elif mutation == "conflated":
        empty["destination"] = "none"
    elif mutation == "anchor":
        absent["tag"] = "a"
    elif mutation == "href":
        absent["href"] = ""
    elif mutation == "submit":
        absent["submit_events"] = 1
    elif mutation == "reset":
        absent["reset_events"] = 1
    elif mutation == "wrong-icon":
        absent["svg_paths"] = ["check"]
    elif mutation == "empty-no-navigation":
        empty["navigation"] = "none"
    elif mutation == "intercepted":
        empty["navigation_intercepted"] = True
    elif mutation == "empty-no-document":
        empty["document_replaced"] = False
    else:
        absent["input_after"] = "initial"
    with pytest.raises(sources.EvidenceError):
        sources.validate_cancel_records(rows, native)


def delivery_record(binding=None):
    return {
        "status": "passed",
        "bindings": binding or {"source": "abc", "runtime": "def", "config": "ghi"},
        "assertions": [{"id": "verified", "passed": True}],
        "commands": [command()],
    }


def test_delivery_bundle_progression_retains_logs_without_temporary_files(tmp_path):
    path = tmp_path / "10-companion-delivery.json"
    form = delivery_record()
    sources.merge_delivery(path, "form_probe", form)
    with pytest.raises(sources.EvidenceError):
        sources.validate_bundle(sources.load_json(path), form["bindings"], committed=True)
    sources.merge_delivery(path, "delivered_probe", delivery_record())
    final = sources.merge_delivery(path, "committed_probe", delivery_record())
    assert final["form_probe"] == form
    assert final["delivered_probe"] == delivery_record()
    # cwd is historical provenance; validation never needs that removed path.
    assert sources.validate_bundle(final, form["bindings"], committed=True)
    with pytest.raises(sources.EvidenceError, match="partial"):
        sources.merge_delivery(path, "form_probe", form)


@pytest.mark.parametrize("mutation", ["missing-log", "tampered-log", "stale", "failed", "partial"])
def test_incomplete_delivery_never_certifies_acceptance(tmp_path, mutation):
    path = tmp_path / "bundle.json"
    for slot in ("form_probe", "delivered_probe", "committed_probe"):
        bundle = sources.merge_delivery(path, slot, delivery_record())
    if mutation == "missing-log":
        bundle["committed_probe"]["commands"][0].pop("stdout")
    elif mutation == "tampered-log":
        bundle["delivered_probe"]["commands"][0]["stdout"] = "500 passed"
    elif mutation == "stale":
        bundle["committed_probe"]["bindings"]["source"] = "changed"
    elif mutation == "failed":
        bundle["committed_probe"]["status"] = "failed"
    else:
        bundle.pop("committed_probe")
        bundle["status"] = "provisional"
    with pytest.raises(sources.EvidenceError):
        sources.validate_bundle(bundle, delivery_record()["bindings"], committed=True)


def test_wrong_module_and_template_origins_fail(tmp_path):
    companion, core = tmp_path / "companion", tmp_path / "core"
    origins = {
        "modules": {
            name: str((core if name == "crud_views" else companion) / "src" / name / "__init__.py")
            for name in ("crud_views", "crud_views_tabler", "django_tabler", "django_tabler.crispy")
        },
        "templates": {
            p.split("/templates/", 1)[1]: {"origin": str(companion / p), "sha256": sources.digest(data)}
            for p, data in FILES.items()
            if "/templates/" in p
        },
    }
    sources.validate_origins(origins, companion, core, FILES, CORE_FILES)
    bad = copy.deepcopy(origins)
    bad["modules"]["crud_views"] = "/original/editable/checkout/src/crud_views/__init__.py"
    with pytest.raises(sources.EvidenceError, match="wrong imported"):
        sources.validate_origins(bad, companion, core, FILES, CORE_FILES)
    bad = copy.deepcopy(origins)
    bad["templates"]["crud_views/modal/shell.html"]["sha256"] = "wrong"
    with pytest.raises(sources.EvidenceError, match="wrong template"):
        sources.validate_origins(bad, companion, core, FILES, CORE_FILES)


@pytest.mark.parametrize("committed_settings", [False, True])
def test_real_archive_capture_and_check_use_pinned_copies(repo, tmp_path, monkeypatch, committed_settings):
    root, revision = repo
    core, core_revision = repository(tmp_path / "core", CORE_FILES)
    monkeypatch.setattr(sources, "COMPANION_ROOT", str(root))
    monkeypatch.setattr(sources, "COMPANION_REVISION", revision)
    monkeypatch.setattr(sources, "COMPANION_ORIGIN", ORIGIN)
    monkeypatch.setattr(sources, "CORE_BASE", core_revision)
    monkeypatch.setattr(sources, "core_root", lambda: core)
    # The user's dirty settings never enter the archive used by either suite.
    settings_path = root / "example/config/settings.py"
    settings_path.write_text('SECRET_KEY = "private-user-value"\n')
    if committed_settings:
        run_git(root, "add", "example/config/settings.py")
        run_git(root, "commit", "-m", "user settings change")
    before = sources.preservation(root)
    observed = []

    def runner(argv, cwd, env=None):
        cwd = Path(cwd)
        observed.append((list(map(str, argv)), str(cwd), env))
        assert cwd != root
        assert (cwd / "example/config/settings.py").read_bytes() == FILES["example/config/settings.py"]
        if "-c" in argv:
            names = json.loads(argv[-1])
            origins = {
                "modules": {
                    name: str(
                        (cwd.parent / "django-crud-views" if name == "crud_views" else cwd)
                        / "src"
                        / name
                        / "__init__.py"
                    )
                    for name in ("crud_views", "crud_views_tabler", "django_tabler", "django_tabler.crispy")
                },
                "templates": {
                    name: {
                        "origin": str(cwd / next(p for p in FILES if p.endswith("templates/" + name))),
                        "sha256": sources.digest(
                            next(data for p, data in FILES.items() if p.endswith("templates/" + name))
                        ),
                    }
                    for name in names
                },
            }
            return command(json.dumps(origins), argv=list(map(str, argv)))
        if "pytest" in argv:
            assert "DJANGO_SETTINGS_MODULE" not in env
            return command(
                "FAILED tests/test_old.py::test_known - assertion\n1 failed, 2 passed in 0.1s\n",
                code=1,
                argv=list(map(str, argv)),
                cwd=cwd,
            )
        assert list(argv)[-2:] == ["--parallel", "4"]
        return command("Ran 4 tests in 0.1s\nOK\n", argv=list(map(str, argv)), cwd=cwd)

    output = tmp_path / "baseline.json"
    report = sources.capture_baseline(output, env={}, runner=runner, probe=lambda _: runtime())
    assert report["status"] == "captured" and report["tests_outcome"] == "failed"
    assert "private-user-value" not in output.read_text()
    assert sources.preservation(root) == before
    assert len(observed) == 3
    assert sources.check_baseline(report, env={}, probe=lambda _: runtime())
    run_git(root, "commit", "--allow-empty", "-m", "authorized local identity advance")
    assert sources.check_baseline(report, env={}, probe=lambda _: runtime())
    broken = copy.deepcopy(report)
    broken["tests_outcome"] = "passed"
    with pytest.raises(sources.EvidenceError, match="relabeled"):
        sources.check_baseline(broken, env={}, probe=lambda _: runtime())


@pytest.mark.parametrize("path", ["src/crud_views_tabler/checks.py", "tests/new.py", "pyproject.toml"])
def test_capture_rejects_non_settings_descendant_changes(repo, monkeypatch, path):
    root, revision = repo
    monkeypatch.setattr(sources, "COMPANION_ROOT", str(root))
    monkeypatch.setattr(sources, "COMPANION_REVISION", revision)
    monkeypatch.setattr(sources, "COMPANION_ORIGIN", ORIGIN)
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# unrelated source change\n")
    run_git(root, "add", path)
    run_git(root, "commit", "-m", "changed integration input")
    with pytest.raises(sources.EvidenceError, match="continuity"):
        sources._capture_inputs({}, probe=lambda _: runtime())


def test_capture_rejects_non_descendant_identity(repo, monkeypatch):
    root, revision = repo
    monkeypatch.setattr(sources, "COMPANION_ROOT", str(root))
    monkeypatch.setattr(sources, "COMPANION_REVISION", revision)
    monkeypatch.setattr(sources, "COMPANION_ORIGIN", ORIGIN)
    run_git(root, "checkout", "--orphan", "unrelated")
    run_git(root, "commit", "-m", "same tree without ancestry")
    with pytest.raises(sources.EvidenceError, match=r"ancestor|merge-base"):
        sources._capture_inputs({}, probe=lambda _: runtime())


def test_delivery_preserves_settings_only_commit_outside_replay(repo, tmp_path):
    root, revision = repo
    path = root / "example/config/settings.py"
    path.write_text('SECRET_KEY = "user-committed-value"\n')
    run_git(root, "add", "example/config/settings.py")
    run_git(root, "commit", "-m", "user settings")
    parent = run_git(root, "rev-parse", "HEAD")
    baseline = {
        "preserved": sources.preservation(root),
        "source_continuity": sources.capture_continuity(root, revision),
    }
    snapshot = sources.load_json(sources.private_snapshot(root, tmp_path / "private"))
    candidate = dict(FILES)
    target = "src/crud_views_tabler/templates/crud_views/tags/alert.html"
    candidate[target] = b"<div>adopted alert</div>"
    (root / target).write_bytes(candidate[target])
    assert sources.check_delivery_tree(root, candidate, baseline, snapshot)
    run_git(root, "add", target)
    run_git(root, "commit", "-m", "scoped adoption")
    assert sources.check_delivery_tree(root, candidate, baseline, snapshot, receipt=receipt(root, parent))
    path.write_text('SECRET_KEY = "changed-private-value"\n')
    with pytest.raises(sources.EvidenceError, match="private settings"):
        sources.check_delivery_tree(root, candidate, baseline, snapshot)


def receipt(root, parent):
    head = run_git(root, "rev-parse", "HEAD")
    return {
        "repository_root": str(root),
        "before_head": parent,
        "after_head": head,
        "tree": run_git(root, "rev-parse", "HEAD^{tree}"),
        "delta_sha256": sources.digest(sources.git(root, "diff", "--binary", parent, head)),
    }


def test_delivery_tree_provisional_committed_and_private_settings(repo, tmp_path):
    root, parent = repo
    private = root / "example/config/settings.py"
    private.write_text('SECRET_KEY = "preserve-me"\n')
    baseline = {"preserved": sources.preservation(root)}
    snapshot = sources.load_json(sources.private_snapshot(root, tmp_path / "private"))
    candidate = dict(FILES)
    path = "src/crud_views_tabler/templates/crud_views/tags/alert.html"
    candidate[path] = b"<div>candidate alert</div>"
    (root / path).write_bytes(candidate[path])
    assert sources.check_delivery_tree(root, candidate, baseline, snapshot)["index_preserved"]
    run_git(root, "add", path)
    run_git(root, "commit", "-m", "approved theme delta")
    approved = receipt(root, parent)
    assert sources.check_delivery_tree(root, candidate, baseline, snapshot, receipt=approved)
    private.write_text("changed private settings")
    with pytest.raises(sources.EvidenceError, match="private settings"):
        sources.check_delivery_tree(root, candidate, baseline, snapshot, receipt=approved)


@pytest.mark.parametrize("mutation", ["template", "missing", "new", "wrong-repo", "swept-staged", "post-hook"])
def test_delivery_refuses_unapproved_bytes_and_commits(repo, tmp_path, mutation):
    root, parent = repo
    baseline = {"preserved": sources.preservation(root)}
    snapshot = sources.load_json(sources.private_snapshot(root, tmp_path / "private"))
    candidate = dict(FILES)
    path = "src/crud_views_tabler/templates/crud_views/tags/alert.html"
    candidate[path] = b"approved"
    (root / path).write_bytes(candidate[path])
    run_git(root, "add", path)
    if mutation == "swept-staged":
        (root / "src/crud_views_tabler/checks.py").write_text("unrelated = True\n")
        run_git(root, "add", "src/crud_views_tabler/checks.py")
    run_git(root, "commit", "-m", "delivery")
    approved = receipt(root, parent)
    if mutation in {"template", "post-hook"}:
        (root / path).write_text("unexpected drift")
    elif mutation == "missing":
        (root / path).unlink()
    elif mutation == "new":
        (root / "src/crud_views_tabler/new.py").write_text("def behavior(): pass\n")
    elif mutation == "wrong-repo":
        other, _ = repository(tmp_path / "unrelated")
        approved["repository_root"] = str(other)
    with pytest.raises(sources.EvidenceError):
        sources.check_delivery_tree(root, candidate, baseline, snapshot, receipt=approved)


def test_same_file_unrelated_staged_hunk_is_preserved(repo, tmp_path):
    root, _ = repo
    path = "src/crud_views_tabler/checks.py"
    base = "\n".join(f"v{i} = {i}" for i in range(30)) + "\n"
    (root / path).write_text(base)
    run_git(root, "add", path)
    run_git(root, "commit", "-m", "many independent lines")
    files = sources.archive_files(root, run_git(root, "rev-parse", "HEAD"))
    unrelated = base.replace("v25 = 25", "v25 = 99")
    (root / path).write_text(unrelated)
    run_git(root, "add", path)
    baseline = {"preserved": sources.preservation(root)}
    snapshot = sources.load_json(sources.private_snapshot(root, tmp_path / "private"))
    candidate = {**files, path: base.replace("v1 = 1\n", "v1 = 77\n").encode()}
    (root / path).write_text(unrelated.replace("v1 = 1\n", "v1 = 77\n"))
    assert sources.check_delivery_tree(root, candidate, baseline, snapshot)
    run_git(root, "add", path)
    with pytest.raises(sources.EvidenceError, match="index"):
        sources.check_delivery_tree(root, candidate, baseline, snapshot)


def test_replay_checks_patch_full_tree_and_concrete_evidence(tmp_path, monkeypatch):
    baseline_files, candidate_files, native = adopted_files()
    root, revision = repository(tmp_path / "theme", baseline_files)
    core, core_revision = repository(tmp_path / "core", CORE_FILES)
    monkeypatch.setattr(sources, "core_root", lambda: core)
    # Baseline validation is tested separately with real archives; this test composes the replay predicates.
    monkeypatch.setattr(sources, "check_baseline", lambda *a, **kw: True)
    for path, data in candidate_files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    run_git(root, "add", ".")
    patch = sources.git(root, "diff", "--binary", "HEAD").decode()
    baseline = {
        **manifest_for(root, revision),
        "core_revision": core_revision,
        "runtime": runtime(),
        "inventory": sources.classify_tree(baseline_files, CORE_FILES),
        "companion_python": "/test/python",
    }
    report = {
        **phase_report(native),
        "status": "passed",
        "baseline_sha256": sources.digest(baseline),
        "patch": patch,
        "patch_sha256": sources.digest(patch.encode()),
        "core_inventory": sources.inventory(CORE_FILES),
        "inventory": sources.classify_tree(candidate_files, CORE_FILES),
        "runtime": runtime(),
    }
    isolated_companion, isolated_core = tmp_path / "removed-companion", tmp_path / "removed-core"
    report["suites"] = [
        {"command": command(argv=argv, cwd=isolated_companion)}
        for argv in sources.suite_commands(baseline["companion_python"])
    ]
    origins = {
        "modules": {
            name: str((isolated_core if name == "crud_views" else isolated_companion) / "src" / name / "__init__.py")
            for name in ("crud_views", "crud_views_tabler", "django_tabler", "django_tabler.crispy")
        },
        "templates": {
            path.split("/templates/", 1)[1]: {"origin": str(isolated_companion / path), "sha256": sources.digest(data)}
            for path, data in candidate_files.items()
            if "/templates/" in path
        },
    }
    report.update(
        origins=origins,
        origin_command=command(json.dumps(origins)),
        isolated_roots={"companion": str(isolated_companion), "core": str(isolated_core)},
    )
    for row in report["actions"]:
        row["source_sha256"] = sources.digest(sources.inventory(candidate_files))
    assert sources.verify_replay(report, baseline, env={}) == candidate_files
    # Only the independently tested Git delivery boundary is replaced here; final candidate/replay
    # validation still reconstructs real archives and patches and runs every branch predicate.
    monkeypatch.setattr(sources, "validate_committed_delivery", lambda *a, **kw: {"fixture": "receipt"})
    assert sources.validate_final_sources(baseline, report, report, {}, env={}) == {"fixture": "receipt"}
    for mutation in ("patch", "tree", "core", "scenario", "action-source", "added-file", "borrow-purpose"):
        bad = copy.deepcopy(report)
        if mutation == "patch":
            bad["patch"] += "corrupt"
        elif mutation == "tree":
            path = "src/crud_views_tabler/templates/crud_views/modal/shell.html"
            bad["inventory"]["tracked_tree"].pop(path)
            bad["inventory"]["classifications"].pop(path)
            bad["inventory"]["shadows"].pop(path)
        elif mutation == "core":
            bad["core_inventory"] = {}
        elif mutation == "scenario":
            bad["cancel_no_url"].pop()
        elif mutation == "action-source":
            bad["actions"][0]["source_sha256"] = "other-tested-tree"
        else:
            extra = b"def hidden():\n    return False\n"
            target = root / "src/crud_views_tabler/hidden.py"
            target.write_bytes(extra)
            run_git(root, "add", str(target))
            bad["patch"] = sources.git(root, "diff", "--binary", "HEAD").decode()
            bad["patch_sha256"] = sources.digest(bad["patch"].encode())
            if mutation == "borrow-purpose":
                changed = {**candidate_files, "src/crud_views_tabler/hidden.py": extra}
                bad["inventory"] = sources.classify_tree(changed, CORE_FILES)
                bad["inventory"]["classifications"]["src/crud_views_tabler/hidden.py"]["sections"][0]["purpose_id"] = (
                    "src/crud_views_tabler/checks.py#check_tabler_icons"
                )
        with pytest.raises(sources.EvidenceError):
            sources.verify_replay(bad, baseline, env={})
        with pytest.raises(sources.EvidenceError):
            sources.validate_final_sources(baseline, report, bad, {}, env={})
        if mutation not in {"patch", "added-file"}:  # candidate has no patch field; replay owns the exact patch
            with pytest.raises(sources.EvidenceError):
                sources.validate_final_sources(baseline, bad, report, {}, env={})


def test_baseline_failure_comparison_requires_unchanged_test_class_and_rejects_new_failures():
    before = {"src/theme/tests.py": b"class OldTests:\n    def test_old(self):\n        assert False\n"}
    failure = "test_old (theme.tests.OldTests.test_old)"
    log = command(f"FAIL: {failure}\nRan 2 tests in 0.1s\nFAILED (failures=1)\n", code=1)
    baseline = {"command": log}
    current = {"command": log}
    assert sources.compare_suite_failures(current, baseline, before, before)["retained_failures"] == [failure]
    changed = {"src/theme/tests.py": before["src/theme/tests.py"].replace(b"False", b"True")}
    with pytest.raises(sources.EvidenceError, match="changed baseline test"):
        sources.compare_suite_failures(current, baseline, before, changed)
    new = {
        "command": command(
            "FAIL: test_new (theme.tests.OldTests.test_new)\nRan 2 tests in 0.1s\nFAILED (failures=1)\n", code=1
        )
    }
    with pytest.raises(sources.EvidenceError, match="new companion regression"):
        sources.compare_suite_failures(new, baseline, before, before)
    with pytest.raises(sources.EvidenceError, match="missing baseline"):
        sources.compare_suite_failures(current, None, before, before)


def test_working_tree_allows_only_materialized_internal_documentation_link(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("local instructions")
    (tmp_path / "AGENTS.md").symlink_to("CLAUDE.md")
    assert sources.working_files(tmp_path)["AGENTS.md"] == b"local instructions"
    (tmp_path / "unsafe").symlink_to("/etc/passwd")
    with pytest.raises(sources.EvidenceError, match="unexpected source symlink"):
        sources.working_files(tmp_path)


def test_failed_delivery_retains_prior_slot_and_actual_log(tmp_path, monkeypatch):
    output = tmp_path / "bundle.json"
    form = delivery_record()
    sources.merge_delivery(output, "form_probe", form)

    def attempt(*args, runner, **kwargs):
        runner(["/fixture/python", "-m", "pytest"], "/fixture")
        raise sources.EvidenceError("required suite failed")

    monkeypatch.setattr(sources, "_delivered_probe", attempt)
    with pytest.raises(sources.EvidenceError):
        sources.delivered_probe(
            tmp_path, {}, {}, output, runner=lambda *a, **kw: command("FAILED test::case\n1 failed in 0.1s\n", code=1)
        )
    bundle = sources.load_json(output)
    assert bundle["status"] == "failed"
    assert bundle["form_probe"] == form
    assert bundle["delivered_probe"]["commands"][0]["exit_code"] == 1


def test_local_commit_only_identity_change_keeps_tested_content(repo, tmp_path):
    root, parent = repo
    snapshot = sources.load_json(sources.private_snapshot(root, tmp_path / "private"))
    baseline = {"preserved": snapshot["preserved"]}
    run_git(root, "commit", "--allow-empty", "-m", "identity-only source receipt")
    assert sources.check_delivery_tree(root, FILES, baseline, snapshot, receipt=receipt(root, parent))


def test_wrong_repository_sha_cannot_be_a_source_commit(repo, tmp_path):
    root, parent = repo
    other, _ = repository(tmp_path / "other", {**FILES, "other.txt": b"other repository"})
    run_git(other, "commit", "--allow-empty", "-m", "wrong repository receipt")
    wrong = receipt(other, run_git(other, "rev-parse", "HEAD^"))
    wrong["repository_root"] = str(root)
    wrong["before_head"] = parent
    with pytest.raises(sources.EvidenceError):
        sources.verify_receipt(root, wrong, FILES, parent)


def test_delivery_always_reruns_focused_and_owned_form_with_fresh_label_evidence(tmp_path, monkeypatch):
    baseline_files, candidate, native = adopted_files()
    root, parent = repository(tmp_path / "theme", baseline_files)
    core, _ = repository(tmp_path / "core", CORE_FILES)
    monkeypatch.setattr(sources, "core_root", lambda: core)
    baseline = {
        **manifest_for(root, parent),
        "runtime": runtime(),
        "test_configuration": {"test": "only"},
        "preserved": sources.preservation(root),
    }
    snapshot_path = sources.private_snapshot(root, tmp_path / "private")
    for path, data in candidate.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    replay = {"core_inventory": sources.inventory(CORE_FILES)}
    monkeypatch.setattr(sources, "verify_replay", lambda *a, **kw: candidate)
    monkeypatch.setattr(sources, "resolve_companion_python", lambda *a, **kw: Path("/fixture/python"))
    monkeypatch.setattr(sources, "probe_origins", lambda *a, **kw: ({}, command("origin probe\n")))
    binding = {
        "source_sha256": sources.digest(sources.inventory(candidate)),
        "preserved_dirty_sha256": sources.digest(baseline["preserved"]),
        "index_preserved": True,
        "runtime_sha256": sources.digest(baseline["runtime"]),
        "config_sha256": sources.digest(baseline["test_configuration"]),
        "core_sha256": sources.digest(replay["core_inventory"]),
    }
    output = core / sources.PHASE_DIR / "10-companion-delivery.json"
    sources.atomic_json(output, {"schema": 1})
    calls = []

    def runner(argv, cwd, env=None):
        argv = list(map(str, argv))
        calls.append(argv)
        if argv[0] == "node":
            form = {**delivery_record(binding), **phase_report(native), "run_id": env["CV_THEME_PROBE_RUN_ID"]}
            sources.merge_delivery(output, "form_probe", form)
            return command("browser assertions passed\n", argv=argv)
        assert all(name in argv for name in sources.FOCUSED_TESTS)
        return command("Ran 4 tests in 0.1s\nOK\n", argv=argv)

    env = {"CV_THEME_PRIVATE_SNAPSHOT": str(snapshot_path)}
    provisional = sources.delivered_probe(root, baseline, replay, output, env=env, runner=runner)
    assert provisional["status"] == "provisional"
    assert len(calls) == 3
    assert [a[a.index("--case") + 1] for a in calls if "--case" in a] == ["owned-form", "label-floor"]
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "scoped delivery")
    provisional["companion_receipt"] = receipt(root, parent)
    sources.atomic_json(output, provisional)
    # Companion commit/probes precede the core evidence commit; its parent/path boundary is non-self-referential.
    provisional["core_receipt"] = {
        "repository_root": str(core),
        "before_head": run_git(core, "rev-parse", "HEAD"),
        "evidence_paths": [
            sources.PHASE_DIR + "/10-companion-delivery.json",
            sources.PHASE_DIR + "/07-TABLER-HANDOFF.md",
        ],
    }
    provisional["preservation_snapshot"] = sources.load_json(snapshot_path)
    sources.atomic_json(output, provisional)
    committed = sources.delivered_probe(root, baseline, replay, output, env=env, runner=runner, require_committed=True)
    assert committed["status"] == "complete" and len(calls) == 6
    assert sources.validate_bundle(committed, binding, committed=True)
    # A valid HEAD/worktree alone cannot conceal a reverse-staged task hunk.
    run_git(root, "read-tree", parent)
    with pytest.raises(sources.EvidenceError, match="uncommitted task"):
        sources.check_delivery_tree(
            root, candidate, baseline, sources.load_json(snapshot_path), receipt=provisional["companion_receipt"]
        )
    run_git(root, "read-tree", "HEAD")
    snapshot_path.unlink()
    offline = sources.delivered_probe(root, baseline, replay, output, env={}, runner=runner, require_committed=True)
    assert offline["status"] == "complete"
    env = {}
    # Exit zero without replacing the partial record cannot pass a later verification.
    with pytest.raises(sources.EvidenceError, match="current execution"):
        sources.delivered_probe(
            root,
            baseline,
            replay,
            output,
            env=env,
            require_committed=True,
            runner=lambda *a, **kw: command("Ran 4 tests in 0.1s\nOK\n"),
        )
    failed = sources.load_json(output)
    assert failed["status"] == "failed"
    assert failed["history"][-1]["status"] == "complete"


def test_delivery_cli_accepts_the_planned_combined_flags(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sources, "load_json", lambda _: {})
    monkeypatch.setattr(
        sources, "resolve_recorded_source", lambda operand, **kw: Path("/recorded") if operand == "recorded" else None
    )
    calls = []
    monkeypatch.setattr(sources, "delivered_probe", lambda *a, **kw: calls.append((a, kw)) or {"status": "complete"})
    assert (
        sources.main(
            [
                "--verify-replay",
                "--delivered-source",
                "recorded",
                "--require-committed",
                "--output",
                str(tmp_path / "bundle.json"),
            ]
        )
        == 0
    )
    assert calls[0][0][0] == Path("/recorded")
    assert calls[0][1]["require_committed"] is True
    assert json.loads(capsys.readouterr().out)["status"] == "complete"


def test_core_receipt_binds_pending_evidence_parent_and_both_owned_paths(tmp_path):
    root, parent = repository(tmp_path / "core")
    record = {
        "repository_root": str(root),
        "before_head": parent,
        "evidence_paths": [
            sources.PHASE_DIR + "/10-companion-delivery.json",
            sources.PHASE_DIR + "/07-TABLER-HANDOFF.md",
        ],
    }
    sources.validate_core_receipt(record, root)
    for changed in (
        {**record, "repository_root": "/wrong"},
        {**record, "before_head": "0" * 40},
        {**record, "evidence_paths": record["evidence_paths"] + ["unrelated"]},
    ):
        with pytest.raises(sources.EvidenceError):
            sources.validate_core_receipt(changed, root)


def test_registration_only_tracer_defers_synchronized_tests_but_complete_gates_refuse(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "theme_adoption_server", Path(__file__).with_name("theme_adoption_server.py")
    )
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    original = {"src/crud_views_tabler/tests.py": b"class ButtonClassTests: pass\n"}
    pending = server.focused_selection(original, delivered=True)
    assert pending["tests"] == ["django_tabler.tests.PackageTests"]
    assert pending["pending"] == list(sources.FOCUSED_TESTS[:-1])
    for kwargs in ({"delivered": False}, {"delivered": True, "full": True}):
        with pytest.raises(sources.EvidenceError, match="synchronized"):
            server.focused_selection(original, **kwargs)
    synchronized = {"src/crud_views_tabler/tests.py": b"class ThemeAdoptionTests(TestCase): pass\n"}
    assert server.focused_selection(synchronized, delivered=True) == {
        "tests": list(sources.FOCUSED_TESTS),
        "pending": [],
    }


def test_capture_missing_dependencies_halts_before_copying(repo, tmp_path, monkeypatch):
    root, revision = repo
    monkeypatch.setattr(sources, "COMPANION_ROOT", str(root))
    monkeypatch.setattr(sources, "COMPANION_REVISION", revision)
    monkeypatch.setattr(sources, "COMPANION_ORIGIN", ORIGIN)
    observed = runtime()
    observed["missing"] = ["pytest", "pytest_django", "xdist"]
    output = tmp_path / "baseline.json"
    with pytest.raises(sources.EvidenceError, match="missing companion dependencies"):
        sources.capture_baseline(
            output,
            env={},
            probe=lambda _: observed,
            runner=lambda *a, **kw: pytest.fail("suite cannot run without prerequisites"),
        )
    assert not output.exists()


def test_django_failed_summary_is_not_a_failing_test_identity():
    observed = sources.suite_result(
        command(
            "FAIL: test_example (app.tests.Example.test_example)\nRan 2 tests in 0.1s\nFAILED (failures=1)\n", code=1
        )
    )
    assert observed == {
        "count": 2,
        "outcome": "failed",
        "failures": ["test_example (app.tests.Example.test_example)"],
    }


def test_committed_slot_alone_cannot_mark_bundle_complete(tmp_path):
    output = tmp_path / "bundle.json"
    with pytest.raises(sources.EvidenceError):
        sources.merge_delivery(output, "committed_probe", delivery_record())
    assert not output.exists()


def final_report_fixture():
    source = {"src/package.py": "fingerprint"}
    report = {
        "source_inventory": source,
        "gates": {},
        "coverage_limits": {"django60_current_pack": "untested-no-cached-runtime"},
    }
    for name, argv in sources.final_commands().items():
        record = command("Tests 1 passed\n# pass 1\n# fail 0\n", argv=argv, cwd=sources.core_root())
        record["duration_seconds"] = 0.1
        gate = {"command": record, "status": "passed", "source_sha256": sources.digest(source)}
        if name in sources.FINAL_PYTHONS:
            environment, series, floor = sources.FINAL_PYTHONS[name]
            runtime_record = {
                "executable": str(sources.core_root() / f".nox/{environment}/bin/python"),
                "core_module": str(sources.core_root() / "src/crud_views/__init__.py"),
                "versions": {
                    "Django": series + ".1",
                    "django-crispy-forms": "2.0" if floor else "2.7",
                    "crispy-bootstrap5": "2023.10" if floor else "2026.9",
                },
            }
            modules = (
                [
                    "theme_form_ownership",
                    "theme_label_modes",
                    "theme_action_groups",
                    "theme_form_requests",
                    "theme_adoption_docs",
                    "alerts",
                    "button_classes",
                ]
                if name != "example"
                else ["example"]
            )
            xml = (
                "<testsuites><testsuite>"
                + "".join(f'<testcase classname="tests.test1.test_{m}" name="test_contract"/>' for m in modules)
                + "</testsuite></testsuites>"
            )
            gate.update(
                runtime=runtime_record,
                preflight=command(json.dumps(runtime_record)),
                junit=xml,
                junit_sha256=sources.digest(xml.encode()),
                passed=len(modules),
                skipped=0,
            )
        elif name in {"modal-focus", "conditional-formsets"}:
            gate.update(browser={"passed": True}, browser_sha256=sources.digest({"passed": True}))
        report["gates"][name] = gate
    return report


def test_final_required_gates_complete_positive_fixture():
    report = final_report_fixture()
    assert sources.validate_final_gates(report, report["source_inventory"])


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-floor42",
        "missing-floor60",
        "missing-example",
        "stale-source",
        "stale-gate",
        "failed",
        "zero",
        "skip",
        "missing-module",
        "wrong-import",
        "wrong-python",
        "wrong-floor",
        "tampered-log",
        "tampered-junit",
        "substituted-command",
        "zero-js",
        "failed-browser",
        "missing-limit",
        "wrong-count",
    ],
)
def test_final_rejects_incomplete_or_substituted_gate_results(mutation):
    report = final_report_fixture()
    expected = dict(report["source_inventory"])
    gate = report["gates"]["django42-floor"]
    if mutation.startswith("missing-") and mutation not in {"missing-module", "missing-limit"}:
        report["gates"].pop(
            {"missing-floor42": "django42-floor", "missing-floor60": "django60-floor", "missing-example": "example"}[
                mutation
            ]
        )
    elif mutation == "stale-source":
        report["source_inventory"]["src/package.py"] = "changed"
    elif mutation == "stale-gate":
        gate["source_sha256"] = "old"
    elif mutation == "failed":
        gate["status"] = "failed"
    elif mutation in {"zero", "skip", "missing-module"}:
        gate["junit"] = (
            "<testsuites><testsuite>"
            + (
                ""
                if mutation == "zero"
                else '<testcase classname="tests.test1.test_theme_form_ownership" '
                'name="test_contract">' + ("<skipped/>" if mutation == "skip" else "") + "</testcase>"
            )
            + "</testsuite></testsuites>"
        )
        gate["junit_sha256"] = sources.digest(gate["junit"].encode())
    elif mutation in {"wrong-import", "wrong-python", "wrong-floor"}:
        if mutation == "wrong-import":
            gate["runtime"]["core_module"] = "/installed/wheel/crud_views/__init__.py"
        elif mutation == "wrong-python":
            gate["runtime"]["executable"] = "/other/python"
        else:
            gate["runtime"]["versions"]["django-crispy-forms"] = "2.7"
        gate["preflight"] = command(json.dumps(gate["runtime"]))
    elif mutation == "tampered-log":
        gate["command"]["stdout"] += "changed"
    elif mutation == "tampered-junit":
        gate["junit"] += "changed"
    elif mutation == "substituted-command":
        gate["command"] = command(argv=["true"], cwd=sources.core_root())
    elif mutation == "zero-js":
        report["gates"]["javascript"]["command"] = command(
            "No tests found", argv=sources.final_commands()["javascript"], cwd=sources.core_root()
        )
    elif mutation == "failed-browser":
        report["gates"]["modal-focus"]["browser"]["passed"] = False
    elif mutation == "missing-limit":
        report.pop("coverage_limits")
    else:
        gate["passed"] = 999
    with pytest.raises(sources.EvidenceError):
        sources.validate_final_gates(report, expected)


def test_check_final_requires_gate_validation_before_companion_access(monkeypatch):
    monkeypatch.setattr(sources, "final_inventory", lambda: {})

    def unexpected(*args, **kwargs):
        raise AssertionError("must reject absent gates before source access")

    monkeypatch.setattr(sources, "load_json", unexpected)
    with pytest.raises(sources.EvidenceError):
        sources.check_final({})
