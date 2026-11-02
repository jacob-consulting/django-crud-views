"""Hermetic companion evidence tests; no production companion or Django imports."""

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


@pytest.fixture(autouse=True)
def no_companion_environment(monkeypatch):
    for key in ("CV_THEME_SOURCE", "CV_PACK_SOURCE", "CV_THEME_CORE_BASE", "CV_THEME_PYTHON", "CV_FOCUS_PYTHON"):
        monkeypatch.delenv(key, raising=False)


def test_missing_sources_fail_closed(tmp_path):
    with pytest.raises(sources.EvidenceError, match="source"):
        sources.inspect_sources(tmp_path / "absent", "abc", "https://example.invalid/theme.git")


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
    }
    for row in report["actions"] + report["cancel_no_url"]:
        row["source_sha256"] = sources.digest(sources.inventory(adopted_files()[1]))
    return report


def test_full_compatibility_records_pass():
    baseline, files, native = adopted_files()
    sources.validate_phase_evidence(phase_report(native), files, baseline)


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


def test_real_archive_capture_and_check_use_pinned_copies(repo, tmp_path, monkeypatch):
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
    core_parent = run_git(core, "rev-parse", "HEAD")
    run_git(core, "add", str(output))
    run_git(core, "commit", "-m", "delivery evidence")
    provisional["core_receipt"] = receipt(core, core_parent)
    sources.atomic_json(output, provisional)
    committed = sources.delivered_probe(root, baseline, replay, output, env=env, runner=runner, require_committed=True)
    assert committed["status"] == "complete" and len(calls) == 6
    assert sources.validate_bundle(committed, binding, committed=True)
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


def test_committed_slot_alone_cannot_mark_bundle_complete(tmp_path):
    output = tmp_path / "bundle.json"
    with pytest.raises(sources.EvidenceError):
        sources.merge_delivery(output, "committed_probe", delivery_record())
    assert not output.exists()
