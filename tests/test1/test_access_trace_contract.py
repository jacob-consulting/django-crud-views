"""The version-1 cv_access export contract: strict output models, the gate before rendering, and schema mode."""

import ast
import copy
import inspect
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import asdict, fields
from io import StringIO
from typing import get_args

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import translation
from pydantic import ValidationError

from crud_views.lib.access_trace import AccessStep, AccessTrace
from crud_views.lib.access_trace_export import (
    AccessTraceExport,
    Kind,
    Outcome,
    Provider,
    StepResult,
    export_schema,
    validate_export,
)
from crud_views.management.commands import cv_access
from tests.test1 import test_access_trace_command as command_tests
from tests.test1.test_access_trace import explode

invoke = command_tests.invoke
process_env = command_tests.process_env
run_process = command_tests.run_process
ANSI = command_tests.ANSI

ESCAPED_KEY = "bad\x1b[31m\nkey"
EXIT_OUTCOMES = {"allowed", "denied", "not_found", "login_redirect", "no_such_route", "error"}


def full_trace(outcome="denied"):
    """Every user key, an own_permission plan row, and steps carrying object, exception and counts."""
    identity = {"model": "app.publisher", "pk": "7"}
    return AccessTrace(
        path="/example/7/",
        route="example-detail",
        view="project.views.Example",
        user={"pk": "1", "username": "sam", "active": True, "anonymous": False},
        outcome=outcome,
        decided_by=3,
        plan=[
            {
                "kind": "own_permission",
                "viewset": "example",
                "object": identity,
                "key": "view",
                "group": None,
                "permission": None,
                "source": "project.views.Example.cv_get_requirement",
            }
        ],
        steps=[
            AccessStep(1, "route", result="passed"),
            AccessStep(2, "list_filter", viewset="example", result="passed", counts={"visible": 2, "total": 5}),
            AccessStep(
                3,
                "own_permission",
                viewset="example",
                object=identity,
                key="view",
                permission="app.view_publisher",
                provider="core",
                source="project.views.Example.cv_get_requirement",
                result="denied",
                how="model permission",
                message="No grant",
                exception={"class": "ValueError", "message": "gate error"},
            ),
        ],
        untraced=["other middleware and URL decorators are not traced"],
    )


def failure(*args):
    """Run the command in-process and return the CommandError plus both streams."""
    stdout, stderr = StringIO(), StringIO()
    with pytest.raises(CommandError) as caught:
        call_command("cv_access", *args, stdout=stdout, stderr=stderr)
    return caught.value, stdout.getvalue(), stderr.getvalue()


def serve(monkeypatch, trace):
    monkeypatch.setattr(cv_access, "trace_access", lambda path, actor: trace)


def hostile_trace():
    """A step with an ESC/newline extra key and a secret string in an integer field."""
    step = asdict(AccessStep(1, "list_filter", result="passed", counts={"visible": "SECRET-VALUE", "total": None}))
    return AccessTrace(path="/x/", outcome="allowed", steps=[{**step, ESCAPED_KEY: "x"}])


def round_trips(data):
    model = validate_export(data)
    assert isinstance(model, AccessTraceExport)
    assert model.model_dump(mode="json", by_alias=True, exclude_unset=True) == data


# Valid traces keep their exact bytes.


def test_valid_json_output_is_byte_identical(monkeypatch):
    trace = full_trace()
    serve(monkeypatch, trace)
    code, stdout, stderr = invoke("/example/7/", "--anonymous", "--as-json", "--no-color")
    assert code == 1
    assert stderr == ""
    assert stdout == json.dumps(trace.to_dict(), ensure_ascii=True, indent=2) + "\n"


def test_valid_forced_color_json_is_byte_identical(monkeypatch):
    trace = full_trace()
    serve(monkeypatch, trace)
    code, stdout, stderr = invoke("/example/7/", "--anonymous", "--as-json", "--force-color")
    assert code == 1
    assert stderr == ""
    assert stdout == cv_access._color_json(json.dumps(trace.to_dict(), ensure_ascii=True, indent=2)) + "\n"


def test_valid_text_output_is_byte_identical(monkeypatch):
    trace = full_trace("allowed")
    serve(monkeypatch, trace)
    code, stdout, stderr = invoke("/example/7/", "--anonymous", "--no-color")
    assert code == 0
    assert stderr == ""
    assert stdout == cv_access._format_text(trace) + "\n"


# Drift: the models describe exactly what to_dict() emits.


def _plan_trace(*rows):
    return AccessTrace(path="/p/", outcome="allowed", plan=list(rows)).to_dict()


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(full_trace().to_dict(), id="full"),
        pytest.param(
            AccessTrace(
                path="/",
                steps=[
                    AccessStep(
                        1, "custom_gate", result="error", exception={"class": "ValueError", "message": "Invalid IPv6"}
                    )
                ],
                decided_by=1,
            ).to_dict(),
            id="error-empty-user",
        ),
        pytest.param(
            _plan_trace(
                {
                    "kind": "manage_gate",
                    "viewset": "v",
                    "object": None,
                    "key": None,
                    "group": "developers",
                    "permission": None,
                    "source": "s",
                }
            ),
            id="plan-own-permission-keys",
        ),
        pytest.param(
            _plan_trace({"kind": "action_state", "viewset": "v", "object": None, "source": "s"}),
            id="plan-action-state",
        ),
        pytest.param(
            _plan_trace(
                {
                    "kind": "ancestor_gate",
                    "viewset": "parent",
                    "object": {"model": "app.parent", "pk": None},
                    "key": "view",
                    "source": "s",
                    "provider": "model",
                    "permission": None,
                }
            ),
            id="plan-ancestor-gate",
        ),
        pytest.param(
            _plan_trace(
                {
                    "kind": "validation",
                    "viewset": "v",
                    "result": "unavailable",
                    "exception": {"class": "KeyError", "message": "'kind'"},
                }
            ),
            id="plan-unavailable",
        ),
        pytest.param(
            AccessTrace(
                path="/r/",
                outcome="allowed",
                steps=[AccessStep(1, "list_filter", result="passed", counts={"visible": 3, "total": None})],
            ).to_dict(),
            id="counts-total-none",
        ),
        pytest.param(
            AccessTrace(
                path="/o/",
                outcome="not_found",
                steps=[AccessStep(1, "object_lookup", object={"model": "app.thing", "pk": None}, result="not_found")],
            ).to_dict(),
            id="object-pk-none",
        ),
    ],
)
def test_valid_exports_round_trip_without_drift(data):
    round_trips(data)


def _set(path, value):
    def mutate(data):
        *parents, last = path
        node = data
        for part in parents:
            node = node[part]
        node[last] = value

    return mutate


def _delete(path):
    def mutate(data):
        *parents, last = path
        node = data
        for part in parents:
            node = node[part]
        del node[last]

    return mutate


class Text:
    def __str__(self):
        return "/looks/like/a/path/"


COUNTS = ("steps", 0, "counts")
EXCEPTION = ("steps", 0, "exception")


@pytest.mark.parametrize(
    "mutate,expected",
    [
        pytest.param(_set((*COUNTS, "visible"), "3"), {("int_type", (*COUNTS, "visible"))}, id="visible-string"),
        pytest.param(_set((*COUNTS, "visible"), True), {("int_type", (*COUNTS, "visible"))}, id="visible-bool"),
        pytest.param(_set(("steps", 0, "result"), "maybe"), {("literal_error", ("steps", 0, "result"))}, id="result"),
        pytest.param(
            _set(("steps", 0, "provider"), "ldap"), {("literal_error", ("steps", 0, "provider"))}, id="provider"
        ),
        pytest.param(_set(("outcome",), "granted"), {("literal_error", ("outcome",))}, id="outcome"),
        pytest.param(_set(("steps", 0, "extra"), 1), {("extra_forbidden", ("steps", 0, "extra"))}, id="step-extra"),
        pytest.param(_set(("plan", 0, "n"), 1), {("extra_forbidden", ("plan", 0, "n"))}, id="plan-n"),
        pytest.param(
            _set(EXCEPTION, {"class_": "ValueError", "message": "m"}),
            {("missing", (*EXCEPTION, "class")), ("extra_forbidden", (*EXCEPTION, "class_"))},
            id="class-alias-misuse",
        ),
        pytest.param(_delete(("steps", 0, "how")), {("missing", ("steps", 0, "how"))}, id="step-key-removed"),
        pytest.param(_set(("version",), 2), {("literal_error", ("version",))}, id="version-2"),
        pytest.param(_set(("version",), True), {("value_error", ("version",))}, id="version-true"),
        pytest.param(_set(("version",), 1.0), {("value_error", ("version",))}, id="version-float"),
        pytest.param(_set(("path",), Text()), {("string_type", ("path",))}, id="path-object"),
    ],
)
def test_malformed_exports_are_rejected(mutate, expected):
    data = copy.deepcopy(full_trace().to_dict())
    data["steps"][0].update(
        counts={"visible": 1, "total": 1}, exception={"class": "ValueError", "message": "m"}, provider="core"
    )
    round_trips(copy.deepcopy(data))
    mutate(data)
    with pytest.raises(ValidationError) as caught:
        validate_export(data)
    assert {(error["type"], tuple(error["loc"])) for error in caught.value.errors()} == expected


# The gate: malformed facts never reach either formatter.


def _assert_one_line_diagnostic(error, stdout, stderr, location):
    message = str(error)
    assert error.returncode == 2
    assert stdout == "" and stderr == ""
    assert len(message.splitlines()) == 1
    assert "Output validation failed (ValidationError)" in message
    assert location in message


@pytest.mark.parametrize("mode", [[], ["--as-json"]])
def test_malformed_trace_is_a_usage_error_in_both_modes(monkeypatch, mode):
    serve(monkeypatch, AccessTrace(path="/x/", outcome="allowed", steps=[AccessStep(1, "route", result="maybe")]))
    with translation.override("en"):
        error, stdout, stderr = failure("/x/", "--anonymous", *mode)
    _assert_one_line_diagnostic(error, stdout, stderr, "steps.0.result")


def test_malformed_no_such_route_trace_writes_no_route_line(monkeypatch):
    serve(
        monkeypatch,
        AccessTrace(path="/x/", outcome="no_such_route", steps=[AccessStep(1, "route", result="maybe")]),
    )
    with translation.override("en"):
        error, stdout, stderr = failure("/x/", "--anonymous")
    _assert_one_line_diagnostic(error, stdout, stderr, "steps.0.result")


def test_diagnostic_escapes_locations_and_omits_values(monkeypatch):
    serve(monkeypatch, hostile_trace())
    with translation.override("en"):
        error, stdout, stderr = failure("/x/", "--anonymous", "--as-json")
    message = str(error)
    _assert_one_line_diagnostic(error, stdout, stderr, "steps.0.counts.visible")
    assert "\\u001b" in message
    assert "\x1b" not in message
    assert "SECRET-VALUE" not in message


@pytest.mark.parametrize("mode", [[], ["--as-json"]])
def test_real_cli_renders_one_escaped_diagnostic_line(monkeypatch, capsys, mode):
    serve(monkeypatch, hostile_trace())
    command = cv_access.Command()
    with translation.override("en"), pytest.raises(SystemExit) as caught:
        command.run_from_argv(["manage.py", "cv_access", "/x/", "--anonymous", *mode])
    assert caught.value.code == 2
    stdout, stderr = capsys.readouterr()
    assert stdout == ""
    assert stderr.endswith("\n")
    assert len(stderr.splitlines()) == 1
    assert stderr.startswith("CommandError: Output validation failed (ValidationError): ")
    assert "\\u001b" in stderr
    for forbidden in ("\x1b", "Traceback", "SECRET-VALUE"):
        assert forbidden not in stderr


# Closed vocabularies match the command's label maps exactly.


def _dict_keys(function, values=None):
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    found = [
        {key.value for key in node.keys}
        for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
        and all(isinstance(key, ast.Constant) and isinstance(key.value, str) for key in node.keys)
        and (
            values is None
            or all(isinstance(value, ast.Constant) and type(value.value) is values for value in node.values)
        )
    ]
    assert len(found) == 1, found
    return found[0]


def test_every_closed_value_has_a_dedicated_label():
    with translation.override("en"):
        for value in get_args(Kind):
            assert cv_access._kind_label(value) != cv_access._text(value), value
        codes = set(get_args(StepResult)) | set(get_args(Outcome))
        assert len(codes) == 11
        for value in codes:
            assert cv_access._result_label(value) != cv_access._text(value), value
    assert set(get_args(Outcome)) == EXIT_OUTCOMES == _dict_keys(cv_access.Command.handle, values=int)
    assert set(get_args(Provider)) == {"core", "guardian", "model", "none"}


def test_label_maps_have_no_orphan_keys():
    assert _dict_keys(cv_access._kind_label) == set(get_args(Kind))
    assert len(get_args(Kind)) == 14
    assert _dict_keys(cv_access._result_label) == set(get_args(StepResult)) | set(get_args(Outcome))


# A real runner trace passes the gate unchanged.


@pytest.mark.django_db
def test_real_missing_route_trace_validates_without_drift():
    code, stdout, stderr = invoke("/missing/", "--anonymous", "--as-json", "--no-color")
    assert code == 2
    assert stderr == ""
    data = json.loads(stdout)
    assert data["outcome"] == "no_such_route"
    round_trips(data)


# Schema mode: exclusive, plain, and free of tracing, actor lookup or database reads (no django_db mark).


@pytest.fixture
def spies(monkeypatch):
    monkeypatch.setattr(cv_access, "trace_access", explode)
    monkeypatch.setattr(cv_access, "resolve_trace_user", explode)


@pytest.mark.parametrize("flags", [[], ["--as-json"], ["--force-color"], ["--as-json", "--force-color"]])
def test_schema_mode_prints_the_plain_generated_schema(spies, flags):
    code, stdout, stderr = invoke("--schema", *flags)
    assert code == 0
    assert stderr == ""
    assert "\x1b" not in stdout
    assert json.loads(stdout) == export_schema()


@pytest.mark.parametrize("args", [["/x/"], ["/x/", "sam"], ["--anonymous"], ["/x/", "--anonymous", "--as-json"]])
def test_schema_mode_rejects_targets_and_actors(spies, args):
    error, stdout, stderr = failure("--schema", *args)
    assert error.returncode == 2
    assert len(str(error).splitlines()) == 1
    assert stdout == "" and stderr == ""


@pytest.mark.parametrize("args", [[], ["--anonymous"], ["--as-json", "--anonymous"]])
def test_missing_path_is_a_usage_error(spies, args):
    error, stdout, stderr = failure(*args)
    assert error.returncode == 2
    assert len(str(error).splitlines()) == 1
    assert stdout == "" and stderr == ""


def _closed(node):
    """Closed values from enum lists and single-value const, on the node and each anyOf branch."""
    values = set()
    for branch in [node, *node.get("anyOf", [])]:
        values.update(branch.get("enum", []))
        if "const" in branch:
            values.add(branch["const"])
    return values


def test_schema_structure_matches_the_models_and_dataclasses():
    schema = export_schema()
    definitions = schema["$defs"]
    assert set(definitions) == {"Counts", "ObjectIdentity", "PlanRow", "Step", "TraceException", "TraceUser"}
    assert schema["required"] == [field.name for field in fields(AccessTrace)]
    assert definitions["Step"]["required"] == [field.name for field in fields(AccessStep)]
    assert definitions["PlanRow"]["required"] == ["kind", "viewset"]
    assert "required" not in definitions["TraceUser"]
    for node in [schema, *definitions.values()]:
        assert node["additionalProperties"] is False
    assert set(definitions["TraceException"]["properties"]) == {"class", "message"}
    root, step, plan = schema["properties"], definitions["Step"]["properties"], definitions["PlanRow"]["properties"]
    assert _closed(root["version"]) == {1}
    assert _closed(root["outcome"]) == set(get_args(Outcome))
    assert _closed(step["kind"]) == _closed(plan["kind"]) == set(get_args(Kind))
    assert _closed(step["result"]) == set(get_args(StepResult))
    assert _closed(plan["result"]) == {"unavailable"}
    assert _closed(step["provider"]) == _closed(plan["provider"]) == set(get_args(Provider))


def test_export_module_imports_without_django():
    env = {key: value for key, value in os.environ.items() if key != "DJANGO_SETTINGS_MODULE"}
    code = (
        "import sys\n"
        "from crud_views.lib.access_trace_export import export_schema\n"
        "export_schema()\n"
        "loaded = [name for name in sys.modules if name == 'django' or name.startswith('django.')]\n"
        "assert not loaded, loaded\n"
    )
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("args,tty", [(["--schema", "--force-color"], True), (["--schema", "--as-json"], False)])
def test_real_process_schema_is_plain(process_env, args, tty):
    result = run_process(process_env, *args, tty=tty)
    assert result.returncode == 0, result.stderr
    assert not ANSI.search(result.stdout)
    assert result.stderr == ""
    assert json.loads(result.stdout) == export_schema()
