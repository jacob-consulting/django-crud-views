"""Published trace contracts checked against actual command, dispatch and manage output."""

import json
import re
from dataclasses import fields
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.urls import reverse
from lxml import html

from crud_views.lib.access_trace import AccessStep, AccessTrace, trace_access
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
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
