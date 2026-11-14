"""Scoped diagnostics reuse startup collectors without widening page disclosure."""

from types import SimpleNamespace

import pytest
from django.core.checks import Error, Warning
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.test import override_settings
from django.urls import reverse
from lxml import html

from crud_views import checks
from crud_views.lib.views import ActionViewPermissionRequired
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_manage_requirements import developer, grant, register  # noqa: F401

pytestmark = pytest.mark.django_db


def test_clean_page_counts_check_objects(client, cv_author, developer):
    client.force_login(developer)
    response = client.get("/author/manage/")
    assert response.status_code == 200
    keys = set(response.context_data)
    assert "manage_checks" in keys, "The page must prepare scoped check data"
    data = response.context["manage_checks"]
    assert data == {"count": len(list(cv_author.checks())), "messages": []}
    doc = html.fromstring(response.content)
    clean = doc.get_element_by_id("cv-manage-checks-clean")
    assert "no issues" in clean.text_content()
    assert "col-lg-4" in clean.getparent().getparent().get("class", "")
    assert not doc.xpath('//*[@id="cv-manage-checks-issues"]')
    assert doc.xpath('//a[contains(@href,"#system-checks") and @rel="noopener"]')


def test_check_objects_materialized_once_messages_silenced_and_escaped(client, cv_author, developer, monkeypatch):
    calls = []
    message = "<script>" + "long finding " * 100 + "</script>"

    def local_checks(self):
        calls.append(self.name)
        yield SimpleNamespace(messages=lambda: [Error(message, hint="<hint>", id="local.E001")])
        yield SimpleNamespace(messages=lambda: [Warning("hidden", id="local.W002"), Error("second", id="local.E003")])
        yield SimpleNamespace(messages=lambda: [])

    monkeypatch.setattr(ViewSet, "checks", local_checks)
    client.force_login(developer)
    with override_settings(SILENCED_SYSTEM_CHECKS=["local.W002"]):
        response = client.get("/author/manage/")
    assert calls == [cv_author.name]
    data = response.context["manage_checks"]
    assert data["count"] == 3
    assert data["messages"] == [
        {"id": "local.E001", "severity": "Error", "message": message, "hint": "<hint>"},
        {"id": "local.E003", "severity": "Error", "message": "second", "hint": None},
    ]
    markup = response.content.decode()
    assert "&lt;script&gt;" in markup and "&lt;hint&gt;" in markup
    assert "<script>" not in markup and "local.W002" not in markup
    doc = html.fromstring(markup)
    issues = doc.get_element_by_id("cv-manage-checks-issues")
    assert "col-lg-8" in issues.getparent().getparent().get("class", "")
    assert not issues.xpath('.//a[contains(@href,"#system-checks")]')
    assert not doc.xpath('//*[@id="cv-manage-checks-clean"]')


@pytest.mark.parametrize("malformed", ["action", "own", "ancestor"])
def test_scoped_sibling_failure_keeps_manage_admission_and_endpoint_errors(malformed, client, developer):
    def build(sfx):
        parent = ViewSet(model=Publisher, name="checkparent" + sfx)
        child = ViewSet(
            model=Book,
            name="checkchild" + sfx,
            parent=ParentViewSet(name=parent.name, attribute="publisher"),
            ancestor_policy=AncestorPolicy(actions={} if malformed == "action" else {
                "tested": AncestorPermissions(nearest="missing" if malformed == "ancestor" else "view", higher="view")
            }),
        )
        register(ActionViewPermissionRequired, child, cv_permission="missing" if malformed == "own" else "change")
        return (parent, child), [parent, child]

    with isolated_routes(build) as (parent, child):
        pub = Publisher.objects.create(name="Scoped")
        book = Book.objects.create(title="Scoped", publisher=pub)
        client.force_login(developer)
        kwargs = {parent.name + "_pk": pub.pk}
        url = reverse(child.get_router_name("manage"), kwargs=kwargs)
        assert client.get(url).status_code == 403
        grant(developer, parent, "view")
        response = client.get(url)
        assert response.status_code == 200
        code = "viewset.E268" if malformed == "action" else "viewset.E269"
        assert [m["id"] for m in response.context["manage_checks"]["messages"]] == [code]
        markup = response.content.decode()
        assert code in markup and 'id="cv-manage-checks-issues"' in markup
        expected = {"action": "Requirement unavailable; review system checks", "own": "undeclared: missing", "ancestor": "parent: missing (undeclared)"}
        assert expected[malformed] in markup
        doc = html.fromstring(markup)
        summary = doc.get_element_by_id("cv-view-tested").find("summary")
        hidden = doc.get_element_by_id(summary.get("aria-describedby")).text_content()
        if malformed != "action":
            assert "missing" in hidden and summary.xpath('.//*[@title[contains(.,"missing")]]')
        else:
            assert "app.change_book" in hidden
        with pytest.raises((ImproperlyConfigured, AssertionError)):
            client.post(reverse(child.get_router_name("tested"), kwargs={**kwargs, child.pk_name: book.pk}))
        with override_settings(SILENCED_SYSTEM_CHECKS=[code]):
            silenced = client.get(url)
        assert silenced.context["manage_checks"]["messages"] == []
        assert 'id="cv-manage-checks-clean"' in silenced.content.decode()


def test_icon_findings_without_obj_scope_and_exclude_global_registries(cv_author, developer, monkeypatch):
    def build(sfx):
        other = ViewSet(model=Publisher, name="checkother" + sfx, icon_header="otherprefix:bad")
        return other, []

    with isolated_routes(build) as other:
        monkeypatch.setattr(cv_author, "icon_header", "targetprefix:bad")
        monkeypatch.setattr(checks, "icon_check_messages", lambda: [Error("GLOBAL ICON", id="global.E999")])
        data = ManageView().get_manage_checks(cv_author, developer)
        warnings = [m for m in data["messages"] if m["id"] == "crud_views.W353"]
        assert len(warnings) == 1 and "targetprefix" in warnings[0]["message"]
        assert all("otherprefix" not in m["message"] and "GLOBAL ICON" not in m["message"] for m in data["messages"])
        scoped = checks.collect_viewset_icon_checks([cv_author, other])
        assert all(m.obj is None for m in scoped)
        assert len(scoped) == 2
        assert checks.check_icons() == checks.icon_check_messages() + checks.collect_viewset_icon_checks(list(checks._REGISTRY.values()))


@pytest.mark.parametrize("completed", [False, True])
def test_global_ancestor_entry_preserves_completion_barrier(monkeypatch, completed):
    def build(sfx):
        parent = ViewSet(model=Publisher, name="barrierparent" + sfx)
        child = ViewSet(model=Book, name="barrierchild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher"))
        register(ActionViewPermissionRequired, child)
        return child, []

    with isolated_routes(build) as child:
        monkeypatch.setattr(checks, "_url_configuration_loaded", lambda: completed)
        global_messages = checks.check_ancestor_declarations()
        expected = checks.collect_ancestor_checks(list(checks._REGISTRY.values()), completed=completed)
        assert global_messages == expected
        own = [m for m in global_messages if m.obj is child]
        assert [m.id for m in own] == (["viewset.E268"] if completed else [])


@pytest.mark.parametrize("error", [ImproperlyConfigured("routing"), DatabaseError("database")])
def test_check_builder_does_not_fabricate_clean_state(cv_author, developer, monkeypatch, error):
    def broken(self):
        raise error

    monkeypatch.setattr(ViewSet, "checks", broken)
    with pytest.raises(type(error), match=str(error)):
        ManageView().get_manage_checks(cv_author, developer)
