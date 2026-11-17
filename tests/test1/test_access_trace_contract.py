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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser, Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from django.utils import translation
from pydantic import ValidationError

from crud_views.lib.access_trace import AccessStep, AccessTrace, trace_access
from crud_views.lib.access_trace_export import (
    AccessTraceExport,
    Kind,
    Outcome,
    Provider,
    StepResult,
    export_schema,
    validate_export,
)
from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import ActionView, DetailViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views.management.commands import cv_access
from crud_views_guardian.lib.mixins import GuardianQuerysetMixin
from tests.test1 import test_access_trace_command as command_tests
from tests.test1 import test_manage_access_trace as web
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_access_trace import assert_export_contract, explode
from tests.test1.test_access_trace_ancestors import chain, coordinates
from tests.test1.test_access_trace_guardian import local_routes, nested_routes
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import grant, register

invoke = command_tests.invoke
process_env = command_tests.process_env
run_process = command_tests.run_process
ANSI = command_tests.ANSI
developer = web.developer
enabled = web.enabled
host = web.host
submit = web.submit

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
        pytest.param(
            AccessTrace(
                path="/a/",
                outcome="login_redirect",
                user={"pk": None, "username": None, "active": False, "anonymous": True},
            ).to_dict(),
            id="anonymous-user",
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
        pytest.param(_set(("user",), {"pk": "1"}), {("value_error", ("user",))}, id="user-partial"),
        pytest.param(_delete(("user", "username")), {("value_error", ("user",))}, id="user-key-removed"),
        pytest.param(_set(("user", "active"), None), {("value_error", ("user",))}, id="user-active-null"),
        pytest.param(_set(("user", "anonymous"), None), {("value_error", ("user",))}, id="user-anonymous-null"),
        pytest.param(
            _set(("user",), {"pk": "1", "username": "sam", "active": None, "anonymous": None}),
            {("value_error", ("user",))},
            id="user-null-flags",
        ),
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


# The shape corpus: real runner traces validate without drift and equal the cv_access --as-json document.

OUTCOME_CODES = {"allowed": 0, "denied": 1, "not_found": 1, "login_redirect": 1, "no_such_route": 2, "error": 2}


@pytest.mark.django_db
@pytest.mark.parametrize("outcome", list(OUTCOME_CODES))
def test_real_outcome_traces_validate_and_match_the_cli(outcome):
    def build(sfx):
        vs = ViewSet(model=Publisher, name="contractoutcome" + sfx)
        attrs = {}
        if outcome == "error":

            def broken_gate(self):
                raise ValueError("contract failure")

            attrs["has_permission"] = broken_gate
        register(DetailViewPermissionRequired, vs, **attrs)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="never published")
        actor = _user("contract outcomes")
        if outcome in {"allowed", "not_found"}:
            grant(actor, vs, "view")
        path = _url(vs, "tested", pk=99999 if outcome == "not_found" else obj.pk)
        if outcome == "no_such_route":
            path = "/missing/"
        anonymous = outcome == "login_redirect"
        trace = trace_access(path, None if anonymous else actor)
        data = trace.to_dict()
        assert data["outcome"] == outcome
        assert_export_contract(data)
        selector = ["--anonymous"] if anonymous else [actor.username]
        code, stdout, stderr = invoke(path, *selector, "--as-json", "--no-color")
    assert code == OUTCOME_CODES[outcome]
    assert stderr == ""
    assert json.loads(stdout) == data
    if outcome == "allowed":
        assert any(step["kind"] == "own_permission" and step["provider"] == "core" for step in data["steps"])


@pytest.mark.django_db
def test_real_pre_actor_error_trace_has_an_empty_user():
    data = trace_access("http://[bad/x/", None).to_dict()
    assert data["user"] == {}
    assert data["outcome"] == "error"
    assert any(step["exception"] is not None for step in data["steps"])
    assert_export_contract(data)
    code, stdout, stderr = invoke("http://[bad/x/", "--anonymous", "--as-json", "--no-color")
    assert code == 2
    assert stderr == ""
    assert json.loads(stdout)["user"] == {}


@pytest.mark.django_db
def test_real_non_str_requirement_hook_fails_closed():
    # The runner carries a project hook's value through unchanged; the gate rejects it in both modes.
    def requirement(cls):
        return {"kind": "permission", "value": 7, "ancestor_applies": False}

    def build(sfx):
        vs = ViewSet(model=Publisher, name="contracthook" + sfx)
        register(DetailViewPermissionRequired, vs, cv_get_requirement=classmethod(requirement))
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="hooked")
        actor = _user("contract hook")
        path = _url(vs, "tested", pk=obj.pk)
        data = trace_access(path, actor).to_dict()
        with pytest.raises(ValidationError) as caught:
            validate_export(data)
        assert any(
            error["type"] == "string_type" and error["loc"][0] == "plan" and error["loc"][-1] == "key"
            for error in caught.value.errors()
        )
        for mode in ([], ["--as-json"]):
            with translation.override("en"):
                error, stdout, stderr = failure(path, actor.username, *mode)
            assert error.returncode == 2
            assert stdout == "" and stderr == ""
            assert "Output validation failed (ValidationError)" in str(error)


@pytest.mark.django_db
def test_real_nested_model_ancestry_validates():
    with isolated_routes(chain) as (outer, inner, leaf, _view):
        pub = Publisher.objects.create(name="private publisher")
        book = Book.objects.create(title="private book", publisher=pub)
        note = BookNote.objects.create(book=book, note="private note")
        data = trace_access(
            _url(leaf, "tested", **coordinates(outer, inner, pub, book, note)), _user("nested")
        ).to_dict()
    assert_export_contract(data)
    gates = [row for row in data["plan"] if row["kind"] == "ancestor_gate"]
    assert gates and all(row["provider"] == "model" for row in gates)
    assert all(set(row) == {"kind", "viewset", "object", "key", "permission", "provider", "source"} for row in gates)


@pytest.mark.django_db
def test_real_unavailable_plan_metadata_validates():
    base = type("LoginFirstAction", (LoginRequiredMixin, ActionView), {"__module__": __name__})
    with isolated_routes(lambda sfx: chain(sfx, base=base)) as (outer, inner, leaf, _view):
        pub = Publisher.objects.create(name="private publisher")
        book = Book.objects.create(title="private book", publisher=pub)
        note = BookNote.objects.create(book=book, note="private note")
        path = _url(leaf, "tested", **coordinates(outer, inner, pub, book, note))
        data = trace_access(path, AnonymousUser()).to_dict()
    assert data["outcome"] == "login_redirect"
    unavailable = [row for row in data["plan"] if row.get("result") == "unavailable"]
    assert unavailable and all(set(row["exception"]) == {"class", "message"} for row in unavailable)
    assert_export_contract(data)


@pytest.mark.django_db
def test_real_guardian_list_counts_validate():
    base = type("LocalList", (GuardianQuerysetMixin, ListViewPermissionRequired), {})
    Publisher.objects.create(name="visible")
    with isolated_routes(lambda sfx: local_routes(sfx, base=base, get=explode)) as (vs, _view):
        data = trace_access(_url(vs, "tested"), _user("guardian list", superuser=True)).to_dict()
    assert data["outcome"] == "allowed"
    counts = [step["counts"] for step in data["steps"] if step["kind"] == "list_filter"]
    assert counts and all(type(count["total"]) is int for count in counts)
    assert any(step["provider"] == "guardian" for step in data["steps"])
    assert_export_contract(data)


@pytest.mark.django_db
def test_real_guardian_nested_create_object_grants_validate():
    pub = Publisher.objects.create(name="outer")
    book = Book.objects.create(title="inner", publisher=pub)
    user = _user("guardian create", (Publisher, "view"), (Book, "change"))
    with isolated_routes(nested_routes) as (outer, inner, leaf, _view, key):
        outer.assign_perm("view", user, pub)
        inner.assign_perm("change", user, book)
        data = trace_access(
            _url(leaf, key, **{outer.name + "_pk": pub.pk, inner.name + "_pk": book.pk}), user
        ).to_dict()
    gates = [step for step in data["steps"] if step["kind"] == "ancestor_gate"]
    assert gates and all(step["provider"] == "guardian" for step in gates)
    grants = [step for step in data["steps"] if step["kind"] == "object_grant"]
    assert [(step["provider"], step["result"]) for step in grants] == [("guardian", "passed")] * 2
    assert_export_contract(data)


def resource_routes(base, reads):
    """A copy of the test_access_trace_resources builder; only the base class is a parameter here."""

    class ContractItem(Resource):
        key: str
        secret: str

        class Meta:
            pk_field = "key"

        @classmethod
        def cv_get_items(cls, request, **kwargs):
            reads.append((request.user, kwargs))
            return [cls(key="one", secret="never serialize this external content")]

        def __str__(self):
            return explode()

        def __repr__(self):
            return explode()

    def build(sfx):
        parent = ViewSet(model=Publisher, name="contractresourceparent" + sfx)
        register(ListViewPermissionRequired, parent)
        vs = ViewSet(
            model=ContractItem,
            name="contractexternal" + sfx,
            parent=ParentViewSet(name=parent.name),
            ancestor_policy=AncestorPolicy(actions={"tested": AncestorPermissions(nearest="view", higher="view")}),
            resource_permissions={"view": "app.view_publisher", "change": "app.change_publisher"},
        )
        combined = type("ResourceEndpoint", (ResourceViewMixin, base), {"__module__": __name__})
        register(
            combined,
            vs,
            get=explode,
            post=explode,
            cv_action=explode,
            cv_action_enabled=classmethod(lambda cls, user, obj: True),
        )
        return (parent, vs), [parent, vs]

    return build


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["list", "detail"])
def test_real_resource_traces_validate(case):
    reads = []
    base = ListViewPermissionRequired if case == "list" else DetailViewPermissionRequired
    user = _user("resource actor", superuser=True)
    parent_obj = Publisher.objects.create(name="parent")
    with isolated_routes(resource_routes(base, reads)) as (parent, vs):
        kwargs = {parent.name + "_pk": parent_obj.pk}
        if case == "detail":
            kwargs["pk"] = "one"
        data = trace_access(_url(vs, "tested", **kwargs), user).to_dict()
    assert data["outcome"] == "allowed" and reads
    assert "never serialize this external content" not in json.dumps(data)
    if case == "list":
        assert [step["counts"] for step in data["steps"] if step["kind"] == "list_filter"] == [
            {"visible": 1, "total": None}
        ]
    else:
        lookups = [step for step in data["steps"] if step["kind"] == "object_lookup"]
        assert [step["object"] for step in lookups] == [{"model": "resources.contractitem", "pk": "one"}]
    assert_export_contract(data)


@pytest.mark.django_db
def test_real_manage_gate_allows_a_manage_group_member(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")

    def build(sfx):
        vs = ViewSet(model=Publisher, name="contractmanage" + sfx)
        register(ManageView, vs, get=explode)
        return vs, [vs]

    user = _user("contract manager")
    user.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    with isolated_routes(build) as vs:
        data = trace_access(_url(vs, "tested"), user).to_dict()
    assert data["outcome"] == "allowed"
    gates = [step for step in data["steps"] if step["kind"] == "manage_gate" and step["result"] != "not_reached"]
    assert [(step["provider"], step["result"], step["how"]) for step in gates] == [("none", "passed", "group_member")]
    assert_export_contract(data)


# Manage-page parity: the Access check traces for core and Guardian hosts equal the CLI document.


def assert_manage_traces_match_the_cli(response, actor):
    data = response.context["manage_access_trace"]
    rows = data["rows"] if data["mode"] == "viewset" else [{"path": data["path_input"], "trace": data["trace"]}]
    executed = 0
    for row in rows:
        if row["trace"] is None:
            continue
        executed += 1
        assert_export_contract(row["trace"])
        code, stdout, stderr = invoke(row["path"], actor.username, "--as-json", "--no-color")
        assert code == OUTCOME_CODES[row["trace"]["outcome"]]
        assert stderr == ""
        assert json.loads(stdout) == row["trace"]
    assert executed >= 1, "every submit must execute at least one trace"


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["path", "viewset"])
def test_manage_page_traces_validate_and_match_the_cli(client, host, developer, enabled, mode):
    params = {"cv_access_mode": mode, "cv_access_user": developer.username}
    if mode == "path":
        params["cv_access_path"] = reverse(host.get_router_name("manage"))
    response = submit(client, host, developer, **params)
    assert response.status_code == 200
    assert response.context["manage_access_trace"]["error"] is None
    assert_manage_traces_match_the_cli(response, developer)
