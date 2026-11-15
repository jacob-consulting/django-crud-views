"""The command formats the shared trace; real processes exercise Django's CLI boundary."""

import errno
import json
import os
import pty
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError

from crud_views.lib.access_trace import AccessStep, AccessTrace, trace_access
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_access_trace import explode
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import grant, register


def test_command_is_discoverable():
    assert "cv_access" in get_commands(), "cv_access must be a discoverable Django command"


@pytest.fixture
def command():
    assert "cv_access" in get_commands(), "cv_access must be a discoverable Django command"
    from crud_views.management.commands import cv_access

    return cv_access


def invoke(*args, **kwargs):
    stdout, stderr = StringIO(), StringIO()
    try:
        result = call_command("cv_access", *args, stdout=stdout, stderr=stderr, **kwargs)
    except SystemExit as exc:
        code = exc.code
    else:
        assert result is None, "handle must not return truthy output for BaseCommand to print again"
        code = 0
    return code, stdout.getvalue(), stderr.getvalue()


@pytest.mark.parametrize(
    "outcome,code",
    [("allowed", 0), ("denied", 1), ("not_found", 1), ("login_redirect", 1), ("no_such_route", 2), ("error", 2)],
)
@pytest.mark.parametrize("as_json", [False, True])
def test_output_and_exit_contract(command, monkeypatch, outcome, code, as_json):
    trace = AccessTrace(
        path="/example/",
        route="example",
        view="project.views.Example",
        outcome=outcome,
        user={"pk": "1", "username": "sam", "active": True, "anonymous": False},
        decided_by=2,
        plan=[{"kind": "own_permission", "viewset": "example", "key": "view", "source": "local"}],
        steps=[
            AccessStep(1, "route", result="passed"),
            AccessStep(
                2,
                "own_permission",
                result="denied",
                permission="app.view_publisher",
                source="local",
                message="No grant",
                exception={"class": "ValueError", "message": "gate error"},
            ),
        ],
        untraced=["other middleware and URL decorators are not traced"],
    )
    calls = []

    def run(path, actor):
        calls.append((path, actor))
        return trace

    monkeypatch.setattr(command, "trace_access", run)
    actual_code, stdout, stderr = invoke("/example/", "--anonymous", *(["--as-json"] if as_json else []))
    assert actual_code == code
    assert len(calls) == 1
    if as_json:
        assert json.loads(stdout) == trace.to_dict()
        assert stderr == ""
    elif outcome == "no_such_route":
        assert stdout == ""
        assert len(stderr.splitlines()) == 1
        assert "/example/" in stderr
    else:
        assert stderr == ""
        for expected in [
            "/example/",
            "example",
            "project.views.Example",
            "sam",
            "Plan",
            "Steps",
            "1.",
            "2.",
            "app.view_publisher",
            "local",
            "No grant",
            "ValueError",
            "gate error",
            "step 2",
            trace.untraced[0],
        ]:
            assert expected in stdout
        if outcome == "allowed":
            assert "may open the page" in stdout.splitlines()[-1]


@pytest.mark.parametrize("args", [[], ["/"], ["/", "sam", "--anonymous"], ["/", "--wrong-option"]])
def test_wrong_invocation_produces_no_trace(command, monkeypatch, args):
    monkeypatch.setattr(command, "trace_access", explode)
    with pytest.raises(CommandError):
        invoke(*args)


@pytest.mark.django_db
@pytest.mark.parametrize("as_json", [False, True])
def test_unknown_actor_is_usage_error(command, as_json):
    with pytest.raises(CommandError) as caught:
        invoke("/", "unknown\nactor", *(["--as-json"] if as_json else []))
    assert caught.value.returncode == 2
    assert len(str(caught.value).splitlines()) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("actor_kind", ["username", "pk", "collision", "inactive", "anonymous"])
def test_real_actor_selection_and_full_url(command, actor_kind, settings):
    settings.CRUD_VIEWS_MANAGE_ACCESS_TRACE = False

    def build(sfx):
        vs = ViewSet(model=Publisher, name="command" + sfx)
        register(DetailViewPermissionRequired, vs, get=explode)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="private object content")
        user = _user("command actor")
        grant(user, vs, "view")
        selector = user.username
        if actor_kind == "pk":
            selector = str(user.pk)
        elif actor_kind == "collision":
            other = _user(str(user.pk))
            selector, user = other.username, other
        elif actor_kind == "inactive":
            user.is_active = False
            user.save()
        args = ["--anonymous"] if actor_kind == "anonymous" else [selector]
        path = _url(vs, "tested", pk=obj.pk)
        code, stdout, stderr = invoke("https://remote.invalid" + path + "?ignored=yes#fragment", *args, "--as-json")
        data = json.loads(stdout)
        expected = trace_access(path, None if actor_kind == "anonymous" else user).to_dict()
        assert data == expected
        assert code == (0 if actor_kind in {"username", "pk"} else 1)
        assert stderr == ""
        assert "private object content" not in stdout


@pytest.mark.django_db
def test_route_configuration_error_is_a_trace(command, monkeypatch):
    from django.core.exceptions import ImproperlyConfigured

    from crud_views.lib import access_trace_runner

    def broken_resolver(path):
        raise ImproperlyConfigured("broken route configuration")

    monkeypatch.setattr(access_trace_runner, "resolve", broken_resolver)
    monkeypatch.setattr(command.Command, "check", explode)
    code, stdout, stderr = invoke("/broken/", "--anonymous", "--as-json")
    assert code == 2
    data = json.loads(stdout)
    assert data["outcome"] == "error"
    assert data["steps"][-1]["exception"] == {"class": "ImproperlyConfigured", "message": "broken route configuration"}
    assert stderr == ""


ANSI = re.compile(r"\x1b\[[0-9;]*m")


@pytest.fixture(scope="module")
def process_env():
    with tempfile.TemporaryDirectory(prefix="cv-access-command-") as directory:
        env = {
            **os.environ,
            "CV_TRACE_CLI_DATABASE": str(Path(directory) / "command.sqlite3"),
            "TERM": "xterm",
            "DJANGO_COLORS": "nocolor",
        }
        result = subprocess.run(
            [sys.executable, "-m", "tests.test1.access_trace_cli_fixture", "--prepare"],
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        yield env
    assert not Path(directory).exists()


def run_process(env, *args, tty=False):
    argv = [sys.executable, "-m", "tests.test1.access_trace_cli_fixture", *args]
    if not tty:
        return subprocess.run(argv, env=env, text=True, capture_output=True, timeout=30)
    master, slave = pty.openpty()

    def read_terminal():
        chunks = []
        while True:
            try:
                data = os.read(master, 65536)
            except OSError as exc:
                if exc.errno == errno.EIO:
                    break
                raise
            if not data:
                break
            chunks.append(data)
        return b"".join(chunks).decode().replace("\r\n", "\n")

    try:
        with subprocess.Popen(argv, env=env, stdout=slave, stderr=subprocess.PIPE, text=True) as process:
            os.close(slave)
            slave = None
            with ThreadPoolExecutor(max_workers=1) as pool:
                output = pool.submit(read_terminal)
                try:
                    _, stderr = process.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    raise
                return subprocess.CompletedProcess(argv, process.returncode, output.result(timeout=5), stderr)
    finally:
        os.close(master)
        if slave is not None:
            os.close(slave)


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize(
    "tty,flag,colored",
    [(False, None, False), (False, "--force-color", True), (True, None, True), (True, "--no-color", False)],
)
def test_real_pipe_and_terminal_color_controls(process_env, as_json, tty, flag, colored):
    args = ["/protected/", "sam"] + (["--as-json"] if as_json else []) + ([flag] if flag else [])
    result = run_process(process_env, *args, tty=tty)
    assert result.returncode == 1, result.stderr
    assert result.stderr == ""
    assert bool(ANSI.search(result.stdout)) is colored
    plain = ANSI.sub("", result.stdout)
    baseline = run_process(process_env, *args[:2], *(["--as-json"] if as_json else []))
    assert plain == baseline.stdout
    if as_json:
        assert json.loads(plain)["outcome"] == "denied"
    if colored:
        for code, word in [
            (32, '"passed"' if as_json else "Passed"),
            (31, '"denied"' if as_json else "Denied"),
            (2, '"not_reached"' if as_json else "Not reached"),
        ]:
            assert f"\x1b[{code}m{word}\x1b[0m" in result.stdout
        if as_json:
            assert '\x1b[36m"version"\x1b[0m:' in result.stdout


@pytest.mark.parametrize(
    "path,actor,outcome,code",
    [
        ("/plain/", "sam", "allowed", 0),
        ("/protected/", "sam", "denied", 1),
        ("/missing/", "sam", "not_found", 1),
        ("/protected/", "--anonymous", "login_redirect", 1),
        ("/absent/", "sam", "no_such_route", 2),
        ("/broken/", "sam", "error", 2),
    ],
)
@pytest.mark.parametrize("as_json", [False, True])
def test_real_process_outcomes(process_env, path, actor, outcome, code, as_json):
    result = run_process(process_env, path, actor, *(["--as-json"] if as_json else []))
    assert result.returncode == code, result.stderr
    assert not ANSI.search(result.stdout + result.stderr)
    if as_json:
        assert json.loads(result.stdout)["outcome"] == outcome
        assert result.stderr == ""
    elif outcome == "no_such_route":
        assert result.stdout == ""
        assert len(result.stderr.splitlines()) == 1
    else:
        assert result.stderr == ""
        assert "Steps:" in result.stdout


@pytest.mark.parametrize(
    "args,code",
    [
        ([], 2),
        (["/plain/"], 2),
        (["/plain/", "sam", "--anonymous"], 2),
        (["/plain/", "missing\nactor", "--as-json"], 2),
        (["/plain/", "sam", "--no-color", "--force-color"], 1),
    ],
)
def test_real_process_invocation_errors(process_env, args, code):
    result = run_process(process_env, *args)
    assert result.returncode == code
    assert result.stdout == ""
    assert result.stderr
    assert "Traceback" not in result.stderr
    if "missing\nactor" in args:
        assert len(result.stderr.splitlines()) == 1


def test_real_terminal_json_preserves_escaped_values(process_env):
    result = run_process(process_env, "/broken/", "sam", "--as-json", tty=True)
    assert result.returncode == 2
    assert '\x1b[33m"error"\x1b[0m' in result.stdout
    plain = ANSI.sub("", result.stdout)
    assert plain == run_process(process_env, "/broken/", "sam", "--as-json").stdout
    data = json.loads(plain)
    deciding = next(step for step in data["steps"] if step["n"] == data["decided_by"])
    assert deciding["exception"]["message"] == 'quoted "value" \\ café 雪\nline\t\x1b[31m'


def test_real_full_url_anonymous_and_username_collision(process_env):
    result = run_process(process_env, "https://invalid.example/plain/?ignored=1#fragment", "--anonymous", "--as-json")
    assert result.returncode == 0
    assert json.loads(result.stdout)["path"] == "/plain/"
    assert json.loads(result.stdout)["user"]["anonymous"] is True
    for selector, pk in [("sam", "1"), ("1", "2"), ("3", "3")]:
        result = run_process(process_env, "/plain/", selector, "--as-json")
        assert result.returncode == 0
        assert json.loads(result.stdout)["user"]["pk"] == pk


def test_fixed_styles_only_color_json_keys_and_result_values(command, monkeypatch):
    values = ["passed", "denied", "error", "skipped", "not_reached", "not_evaluated"]
    trace = AccessTrace(
        path="/",
        outcome="allowed",
        steps=[AccessStep(index, "custom_gate", result=value, message=value) for index, value in enumerate(values, 1)],
    )
    monkeypatch.setattr(command, "trace_access", lambda *args: trace)
    code, output, stderr = invoke("/", "--anonymous", "--as-json", "--force-color")
    assert code == 0
    assert stderr == ""
    assert json.loads(ANSI.sub("", output)) == trace.to_dict()
    for value, color in zip(values, [32, 31, 33, 2, 2, 2], strict=True):
        assert f'\x1b[{color}m"{value}"\x1b[0m' in output
        assert f'\x1b[36m"message"\x1b[0m: "{value}"' in output


def test_real_help_is_translatable_plain_text(process_env):
    result = run_process(process_env, "--help")
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "Trace whether a user may open a project URL" in result.stdout
    for option in ["--anonymous", "--as-json", "--no-color", "--force-color"]:
        assert option in result.stdout
