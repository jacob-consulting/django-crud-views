"""The command formats the shared trace; real processes exercise Django's CLI boundary."""

import json
from io import StringIO

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
    code, stdout, stderr = invoke("/broken/", "--anonymous", "--as-json", skip_checks=False)
    assert code == 2
    data = json.loads(stdout)
    assert data["outcome"] == "error"
    assert data["steps"][-1]["exception"] == {"class": "ImproperlyConfigured", "message": "broken route configuration"}
    assert stderr == ""
