"""Published trace contracts checked against actual command, dispatch and manage output."""

import json
import re
from dataclasses import fields
from io import StringIO
from pathlib import Path
from typing import get_args

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from django.utils import translation
from lxml import html

from crud_views.lib.access_trace import AccessStep, AccessTrace, trace_access
from crud_views.lib.access_trace_export import Kind, Outcome, PlanRow, Provider, StepResult, export_schema
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views.management.commands import cv_access
from crud_views_guardian.lib.views import GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1 import test_manage_docs
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_docs import ANCHORS, heading_anchors
from tests.test1.test_manage_requirements import register

ROOT = Path(__file__).resolve().parents[2]
developer = test_manage_docs.developer


def reference(name="manage"):
    return (ROOT / f"docs/reference/{name}.md").read_text()


def section(title):
    return reference().split(f"### {title}\n", 1)[1].split("\n### ", 1)[0]


@pytest.mark.django_db
def test_documented_schema_and_command_codes(cv_author, developer):
    out, err = StringIO(), StringIO()
    path = reverse(cv_author.get_router_name("manage"))
    call_command("cv_access", path, developer.username, as_json=True, no_color=True, stdout=out, stderr=err)
    data = json.loads(out.getvalue())
    assert data == trace_access(path, developer).to_dict()
    assert not err.getvalue() and "\x1b" not in out.getvalue()
    assert data["version"] == 1
    assert set(re.findall(r"^\| `(\w+)` \|", section("Version 1 document"), re.M)) == set(data)
    documented_steps = set(re.findall(r"^\| `(\w+)` \|", section("Step fields"), re.M))
    assert documented_steps == {f.name for f in fields(AccessStep)} == set(data["steps"][0])
    assert set(data) == {f.name for f in fields(AccessTrace)}
    codes = dict(re.findall(r"^\| `(\w+)` \| `(\d)` \|", section("Outcomes and streams"), re.M))
    assert codes == {
        "allowed": "0",
        "denied": "1",
        "not_found": "1",
        "login_redirect": "1",
        "error": "2",
        "no_such_route": "2",
    }
    assert data["outcome"] == "allowed" and codes[data["outcome"]] == "0"
    out = StringIO()
    call_command("cv_access", path, developer.username, no_color=True, stdout=out)
    assert "This user may open the page; handler-phase checks are not evaluated." in out.getvalue()
    assert "This user may open the page; handler-phase checks are not evaluated." in reference()
    for as_json in (False, True):
        out, err = StringIO(), StringIO()
        with pytest.raises(SystemExit) as exited:
            call_command("cv_access", "/missing/", anonymous=True, as_json=as_json, stdout=out, stderr=err)
        assert exited.value.code == 2
        if as_json:
            sample = json.loads(reference().split("```json\n", 1)[1].split("```", 1)[0])
            assert json.loads(out.getvalue()) == sample and not err.getvalue()
        else:
            assert not out.getvalue() and err.getvalue() == "No such CRUD view route: /missing/\n"


@pytest.mark.django_db
@pytest.mark.parametrize("outcome", ["allowed", "denied", "not_found", "login_redirect", "error", "no_such_route"])
def test_every_documented_exit_code_matches_real_dispatch(outcome):
    from tests.test1.test_access_trace_command import invoke
    from tests.test1.test_manage_requirements import grant

    def build(suffix):
        vs = ViewSet(model=Publisher, name="docoutcome" + suffix)
        attrs = {}
        if outcome == "error":

            def broken_gate(self):
                raise ValueError("documented failure")

            attrs["has_permission"] = broken_gate
        register(DetailViewPermissionRequired, vs, **attrs)
        return vs, [vs]

    with isolated_routes(build) as vs:
        obj = Publisher.objects.create(name="never published")
        actor = _user("doc outcomes")
        if outcome in {"allowed", "not_found"}:
            grant(actor, vs, "view")
        path = _url(vs, "tested", pk=99999 if outcome == "not_found" else obj.pk)
        if outcome == "no_such_route":
            path = "/missing/"
        selector = ["--anonymous"] if outcome == "login_redirect" else [actor.username]
        code, stdout, stderr = invoke(path, *selector, "--as-json", "--no-color")
    data = json.loads(stdout)
    assert data["outcome"] == outcome and not stderr
    codes = dict(re.findall(r"^\| `(\w+)` \| `(\d)` \|", section("Outcomes and streams"), re.M))
    assert code == int(codes[outcome])
    step_section = section("Step fields")
    assert all(f"`{step['kind']}`" in step_section and f"`{step['result']}`" in step_section for step in data["steps"])
    if outcome == "error":
        assert data["steps"][data["decided_by"] - 1]["exception"] == {
            "class": "ValueError",
            "message": "documented failure",
        }


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_enabled_help_anchor_and_setting_contract(request, fixture, client, developer, monkeypatch):
    host = request.getfixturevalue(fixture)
    assert CrudViewsSettings.model_fields["manage_access_trace"].default is False
    assert "| CRUD_VIEWS_MANAGE_ACCESS_TRACE |" in reference("settings")
    assert "[Access check](manage.md#access-check)" in reference("settings")
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", True)
    monkeypatch.setattr(host.get_view_class("manage"), "manage_docs_base_url", "https://example.test/manage/")
    client.force_login(developer)
    response = client.get(reverse(host.get_router_name("manage")))
    assert response.status_code == 200
    links = html.fromstring(response.content).cssselect("[data-cv-manage-help]")
    expected = ANCHORS | {"access-check"}
    if fixture == "cv_author":
        expected = expected - {"guardian"}
    assert {link.get("href") for link in links} == {"https://example.test/manage/#" + anchor for anchor in expected}
    assert ANCHORS | {"access-check"} <= heading_anchors()


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
@pytest.mark.parametrize(
    "case,error_field",
    [
        ("initial", None),
        ("valid", None),
        ("mode", None),
        ("unknown_user", "user"),
        ("empty_user", "user"),
        ("empty_path", "path"),
        ("invalid_path", "path"),
    ],
)
def test_documented_access_mapping_distinguishes_optional_web_validation(
    request, fixture, client, developer, monkeypatch, case, error_field
):
    host = request.getfixturevalue(fixture)
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", True)
    client.force_login(developer)
    query = {"cv_access_mode": "path", "cv_access_user": developer.username, "cv_access_path": "/missing/"}
    if case == "initial":
        query = {}
    elif case == "mode":
        query["cv_access_mode"] = "invalid"
    elif case in {"unknown_user", "empty_user"}:
        query["cv_access_user"] = "unknown" if case == "unknown_user" else ""
    elif case in {"empty_path", "invalid_path"}:
        query["cv_access_path"] = "" if case == "empty_path" else "http://["
    response = client.get(reverse(host.get_router_name("manage")), query)
    assert response.status_code == 200
    mapping = response.context["manage_access_trace"]
    documented = reference("theme").split("### Access trace mapping\n", 1)[1].split("\n### ", 1)[0]
    rows = dict(re.findall(r"^\| `(\w+)` \| (.+) \|$", documented, re.M))
    assert "error_field" in rows, "The theme contract must describe field-associated validation"
    assert "optional" in rows["error_field"].lower()
    assert "`user`" in rows["error_field"] and "`path`" in rows["error_field"]
    assert "direct builder" in rows["error_field"] and "absent" in rows["error_field"]
    base_fields = set(rows) - {"error_field"}
    assert set(mapping) == base_fields | ({"error_field"} if error_field else set())
    if error_field:
        assert mapping["error_field"] == error_field
        assert mapping["error"] and mapping["actor"] is None
    builder = host.get_view_class("manage")().get_manage_access_trace(host, developer, mode="path", path="/missing/")
    assert set(builder) == base_fields


@pytest.mark.django_db
@pytest.mark.parametrize("inner_denies", [True, False])
def test_documented_custom_boundary_has_unknown_inner_origin(inner_denies):
    calls = []

    class Inner(DetailViewPermissionRequired):
        def has_permission(self):
            calls.append("inner")
            return not inner_denies

    class Outer(Inner):
        def has_permission(self):
            calls.append("outer")
            result = super().has_permission()
            return result if inner_denies else False

    def build(suffix):
        vs = ViewSet(model=Publisher, name="docboundary" + suffix)
        register(Outer, vs)
        return vs, [vs]

    with isolated_routes(build) as vs:
        trace = trace_access(_url(vs, "tested", pk=1), _user("boundary"))
    decision = trace.steps[trace.decided_by - 1]
    assert trace.outcome == "denied" and calls == ["outer", "inner"]
    assert decision.kind == "custom_gate" and decision.how == "observed_boundary"
    assert decision.source == f"{Outer.__module__}.{Outer.__qualname__}.has_permission"
    assert "inner" in decision.message and "unknown" in decision.message
    text = " ".join(section("Custom method boundaries").split())
    for phrase in (
        "observed_boundary",
        "actual observed bound callable",
        "inner denying implementation is unknown",
        "super()",
        "inherited library method",
    ):
        assert phrase in text


@pytest.mark.django_db
def test_documented_counts_are_before_context_parent_scoping(client, monkeypatch):
    parents = [Publisher.objects.create(name=str(i)) for i in range(2)]
    books = [Book.objects.create(title=str(i), publisher=parents[i % 2]) for i in range(4)]
    user = _user("count docs")

    def build(suffix):
        parent = GuardianViewSet(model=Publisher, name="docparent" + suffix)
        child = GuardianViewSet(
            model=Book, name="docchild" + suffix, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
        register(GuardianListViewPermissionRequired, child, cv_key="list")
        return (parent, child), [parent, child]

    with isolated_routes(build) as (parent, child):
        parent.assign_perm("view", user, parents[0])
        for book in books[:3]:
            child.assign_perm("view", user, book)
        original = GuardianViewSet.get_queryset
        monkeypatch.setattr(
            GuardianViewSet,
            "get_queryset",
            lambda self, view: Book.objects.all() if self is child else original(self, view),
        )
        path = _url(child, "list", **{parent.name + "_pk": parents[0].pk})
        trace = trace_access(path, user)
        assert [s.counts for s in trace.steps if s.kind == "list_filter"] == [{"total": 4, "visible": 3}]
        client.force_login(user)
        response = client.get(path)
        assert response.status_code == 200
        assert {obj.pk for obj in response.context["object_list"]} == {books[0].pk, books[2].pk}
    text = section("List count boundary")
    for phrase in (
        "pre-Guardian queryset",
        "final get_queryset return",
        "_scope_child_queryset",
        "pagination",
        "omitting the parent filter",
        "Default ViewSet querysets",
    ):
        assert phrase in text


def test_operational_boundaries_and_reference_links():
    limits = " ".join(section("Diagnostic limits").split())
    for boundary in (
        "default-database transaction",
        "savepoint",
        "no saved session",
        "no delivered messages",
        "cross-database",
        "external services",
        "process-wide caches",
        "http://localhost",
        "empty query",
        "headers",
        "body",
        "LoginRequiredMiddleware",
        "process_view()",
        "other middleware and URL decorators are not traced",
        "UnsupportedTraceResponse",
        "POST-only",
        "workflow transition",
        "nested-list",
        "delete-preview",
        "form/action/workflow writes",
        "exception class and message",
        "no object title",
    ):
        assert boundary in limits
    for name in ("guardian", "nested", "resources"):
        doc = reference(name)
        links = re.findall(r"\]\(manage.md#([\w-]+)\)", doc)
        assert "cv_access" in links and "diagnostic-limits" in links
        targets = {h.lower().replace(" ", "-") for h in re.findall(r"^#{2,3} ([\w -]+)$", reference(), re.M)}
        assert set(links) <= targets
        if name != "resources":
            assert "custom-method-boundaries" in links and "list-count-boundary" in links
            text = " ".join(doc.split())
            assert "omitting the parent filter" in text
            assert "context-time parent scoping" in text
            assert "nested-list database" in text
    release = (ROOT / "CHANGELOG.md").read_text().split("## Unreleased", 1)[1].split("\n## ", 1)[0]
    added = release.split("### Added", 1)[1].split("\n### ", 1)[0]
    assert "cv_access" in added and "CRUD_VIEWS_MANAGE_ACCESS_TRACE" in added


# Schema access, streams and validation failures (#375), bound to real command behavior.


def cv_access_reference():
    return reference().split("## cv_access\n", 1)[1].split("\n## ", 1)[0]


def invocation_rows():
    """The second Outcomes and streams table: first cell -> (exit, streams)."""
    header = "| Invocation or failure | Exit | Streams |"
    text = section("Outcomes and streams")
    assert header in text, "Outcomes and streams must document non-outcome invocations"
    table = text.split(header, 1)[1].split("\n\n", 1)[0]
    return {
        cell: (int(code), streams)
        for cell, code, streams in re.findall(r"^\| (.+?) \| `(\d)` \| (.+) \|$", table, re.M)
    }


def malformed_trace():
    return AccessTrace(path="/x/", outcome="allowed", steps=[AccessStep(1, "route", result="maybe")])


def test_documented_schema_access_matches_the_command():
    assert "### Schema and compatibility\n" in reference()
    text = " ".join(section("Schema and compatibility").split())
    for phrase in (
        "python manage.py cv_access --schema",
        "exit `2`",
        "`--as-json`",
        "`--force-color`",
        "No static schema file",
        "consumers must tolerate them",
        "version bump or an explicit maintainer decision",
        "generated schema is authoritative",
        "not a public Python API",
        "`to_dict()`",
    ):
        assert phrase in text, phrase
    assert "```json" not in section("Schema and compatibility")
    examples = cv_access_reference().split("```bash\n", 1)[1].split("```", 1)[0]
    assert "python manage.py cv_access --schema" in examples.splitlines()
    for flags in ([], ["--force-color"]):
        out = StringIO()
        call_command("cv_access", "--schema", *flags, stdout=out)
        assert "\x1b" not in out.getvalue()
        assert json.loads(out.getvalue()) == export_schema()


def test_documented_actor_and_color_rules_are_scoped_to_tracing():
    intro = " ".join(cv_access_reference().split("\n### ", 1)[0].split())
    assert "For tracing, supply a user or `--anonymous`, never both; `--schema` takes neither." in intro
    assert "Trace JSON colors keys and result/outcome values." in intro
    assert "`--schema` output is always plain." in intro
    assert "DJANGO_COLORS" in intro


def test_documented_invocation_streams_match_real_exits(monkeypatch):
    from tests.test1.test_access_trace_command import invoke

    rows = invocation_rows()
    assert set(rows) == {"`--schema`", "Output validation failure", "Unknown user or wrong invocation"}
    code, stdout, stderr = invoke("--schema")
    assert (code, rows["`--schema`"][0]) == (0, 0)
    assert json.loads(stdout) == export_schema() and not stderr
    assert "no trace" in rows["`--schema`"][1]
    monkeypatch.setattr(cv_access, "trace_access", lambda path, actor: malformed_trace())
    for mode in ([], ["--as-json"]):
        out, err = StringIO(), StringIO()
        with translation.override("en"), pytest.raises(CommandError) as caught:
            call_command("cv_access", "/x/", "--anonymous", *mode, stdout=out, stderr=err)
        assert caught.value.returncode == rows["Output validation failure"][0] == 2
        assert not out.getvalue() and not err.getvalue()
        assert str(caught.value).startswith("Output validation failed (ValidationError): ")
    assert "`Output validation failed (ValidationError): ...`" in rows["Output validation failure"][1]
    assert "no trace document" in rows["Output validation failure"][1]
    assert rows["Unknown user or wrong invocation"][0] == 2
    # The six outcome rows remain the only backticked word/digit rows.
    codes = dict(re.findall(r"^\| `(\w+)` \| `(\d)` \|", section("Outcomes and streams"), re.M))
    assert set(codes) == {"allowed", "denied", "not_found", "login_redirect", "error", "no_such_route"}


def test_documented_validation_failure_is_not_an_outcome():
    assert "### Schema and compatibility\n" in reference()
    text = " ".join(section("Schema and compatibility").split())
    for phrase in (
        "Output validation failed",
        "not an outcome",
        "no trace document",
        "field locations",
        "never their values",
        "cv_get_requirement()",
        "does not run this validation",
    ):
        assert phrase in text, phrase
    after_tables = section("Outcomes and streams").split("| Invocation or failure | Exit | Streams |", 1)[1]
    paragraph = " ".join(after_tables.split("\n\n", 1)[1].split("```", 1)[0].split())
    assert "validation failure" in paragraph and "no trace document" in paragraph and "`--as-json`" in paragraph


@pytest.mark.django_db
def test_documented_empty_user_before_actor_resolution():
    rows = dict(re.findall(r"^\| `(\w+)` \| (.+) \|$", section("Version 1 document"), re.M))
    assert rows["user"].endswith("or `{}` before actor resolution.")
    assert trace_access("http://[bad/x/", None).to_dict()["user"] == {}


# Closed version-1 vocabularies and the #375 release entry.


def backticked(text):
    return set(re.findall(r"`([^`]+)`", text))


def sentence(text, start):
    """The sentence starting with ``start``, up to its terminating period."""
    return re.search(rf"{start} (.+?)\.(?:\s|$)", text).group(1)


def test_documented_vocabularies_equal_the_model_literals():
    text = section("Step fields")
    provider = re.search(r"^\| `provider` \| (.+) \|$", text, re.M).group(1)
    assert backticked(provider) == set(get_args(Provider))
    prose = " ".join(text.split())
    assert backticked(sentence(prose, "Kinds are")) == set(get_args(Kind))
    assert backticked(sentence(prose, "Step results are")) == set(get_args(StepResult))
    assert "Step results include" not in prose


def test_documented_vocabularies_are_closed_sets():
    prose = " ".join(section("Step fields").split())
    assert "Outcomes, kinds, step results and providers are closed sets in version 1" in prose
    assert "[Schema and compatibility](#schema-and-compatibility)" in prose
    assert "Plan rows use the same kinds and only the `unavailable` result" in prose
    assert PlanRow.model_fields["kind"].annotation == Kind
    assert set(get_args(PlanRow.model_fields["result"].annotation)) == {"unavailable", type(None)}
    assert set(get_args(Outcome)) == set(
        dict(re.findall(r"^\| `(\w+)` \| `(\d)` \|", section("Outcomes and streams"), re.M))
    )


def test_access_trace_contract_release_entry():
    changelog = (ROOT / "CHANGELOG.md").read_text().split("## Unreleased\n", 1)[1].split("\n## ", 1)[0]
    entries = []
    for part in re.split(r"^### ", changelog, flags=re.M)[1:]:
        heading, body = part.split("\n", 1)
        entries += [(heading, entry) for entry in re.split(r"^- ", body, flags=re.M)[1:] if "(#375)" in entry]
    assert len(entries) == 1 and entries[0][0] == "Added"
    entry = " ".join(entries[0][1].split())
    assert entry.startswith("**Access trace contract** (#375):")
    assert "docs/reference/manage.md#schema-and-compatibility" in entry
    targets = {h.lower().replace(" ", "-") for h in re.findall(r"^#{2,3} ([\w -]+)$", reference(), re.M)}
    assert "schema-and-compatibility" in targets
    for phrase in ("cv_access --schema", "exits 2", "not an outcome", "German"):
        assert phrase in entry, phrase
