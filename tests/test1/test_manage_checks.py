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
from tests.test1.test_manage_requirements import developer as developer
from tests.test1.test_manage_requirements import grant, register

pytestmark = pytest.mark.django_db


def test_clean_page_counts_check_objects(client, cv_author, developer, monkeypatch):
    # The project's AuthorContactView intentionally lacks action labels; isolate
    # the clean-state assertion from those unrelated fixture diagnostics.
    for view in cv_author.get_all_views().values():
        for attr in ("cv_action_label_template_code", "cv_action_short_label_template_code"):
            if not getattr(view, attr) and not getattr(view, attr.removesuffix("_code")):
                monkeypatch.setattr(view, attr, "Action")
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
            ancestor_policy=AncestorPolicy(
                actions={}
                if malformed == "action"
                else {
                    "tested": AncestorPermissions(
                        nearest="missing" if malformed == "ancestor" else "view", higher="view"
                    )
                }
            ),
        )
        register(
            ActionViewPermissionRequired,
            child,
            cv_permission="missing" if malformed == "own" else "change",
            cv_paragraph_template_code="Paragraph",
        )
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
        expected = {
            "action": "Requirement unavailable; review system checks",
            "own": "undeclared: missing",
            "ancestor": "parent: missing (undeclared)",
        }
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
    def forbidden(*args, **kwargs):
        raise AssertionError("Project-wide checks must never run on a scoped page")

    for name in ("check_viewsets", "check_asset_registry", "check_asset_pipeline", "check_button_classes"):
        monkeypatch.setattr(checks, name, forbidden)

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
        assert checks.check_icons() == checks.icon_check_messages() + checks.collect_viewset_icon_checks(
            list(checks._REGISTRY.values())
        )


@pytest.mark.parametrize("completed", [False, True])
def test_global_ancestor_entry_preserves_completion_barrier(monkeypatch, completed):
    def build(sfx):
        parent = ViewSet(model=Publisher, name="barrierparent" + sfx)
        child = ViewSet(
            model=Book, name="barrierchild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
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


def test_top_level_undeclared_permission_is_only_scoped_failure(client, developer):
    def build(sfx):
        vs = ViewSet(model=Publisher, name="topcheck" + sfx)
        register(ActionViewPermissionRequired, vs, cv_permission="missing", cv_paragraph_template_code="Paragraph")
        return vs, [vs]

    with isolated_routes(build) as vs:
        client.force_login(developer)
        response = client.get(reverse(vs.get_router_name("manage")))
        assert response.status_code == 200
        assert [m["id"] for m in response.context["manage_checks"]["messages"]] == ["viewset.E269"]
        assert "undeclared: missing" in response.content.decode()


@pytest.mark.parametrize("count", [0, 1])
def test_clean_count_is_not_augmented_by_separate_collectors(cv_author, developer, monkeypatch, count):
    monkeypatch.setattr(ViewSet, "checks", lambda self: (SimpleNamespace(messages=lambda: []) for _ in range(count)))
    assert ManageView().get_manage_checks(cv_author, developer) == {"count": count, "messages": []}


def test_guardian_composition_scoped_silencing_and_core_count(developer):
    from crud_views_guardian.lib.views import GuardianManageView
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.test_guardian_composition import UnsafeUpdate

    def build(sfx):
        parent = GuardianViewSet(model=Publisher, name="composeparent" + sfx)
        child = GuardianViewSet(
            model=Book, name="composechild" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
        register(UnsafeUpdate, child, fields=["title"], cv_paragraph_template_code="Paragraph", cv_cancel_key="manage")
        return (parent, child), []

    with isolated_routes(build) as (parent, child):
        manage = GuardianManageView()
        data = manage.get_manage_checks(child, developer)
        ids = [message["id"] for message in data["messages"]]
        assert "crud_views_guardian.E001" in ids, (
            "Guardian diagnostics must include this ViewSet's incomplete composition"
        )
        assert data["count"] == len(list(child.checks()))
        assert manage.get_manage_checks(parent, developer)["messages"] == []
        assert ManageView().get_manage_checks(child, developer)["messages"] == []
        with override_settings(SILENCED_SYSTEM_CHECKS=["crud_views_guardian.E001"]):
            assert manage.get_manage_checks(child, developer) == {"count": data["count"], "messages": []}
        # Diagnostics do not make an invalid composition requestable.
        with pytest.raises(ImproperlyConfigured, match="GuardianObjectPermissionMixin"):
            child.get_view_class("tested")().has_permission()


def test_core_collectors_do_not_import_optional_guardian():
    import subprocess
    import sys
    import textwrap

    code = textwrap.dedent("""
        import importlib.abc
        import sys
        class NoGuardian(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, *args):
                if fullname.split(".")[0] in {"guardian", "crud_views_guardian"}:
                    raise AssertionError("Core imported optional Guardian: " + fullname)
        sys.meta_path.insert(0, NoGuardian())
        from django.conf import settings
        settings.configure(
            SECRET_KEY="isolated-test",
            INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "crud_views"],
            TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}],
        )
        import django
        django.setup()
        from django.contrib.auth.models import User
        from crud_views.lib.viewset import ViewSet
        from crud_views.lib.views.manage import ManageView
        vs = ViewSet(model=User, name="isolated_checks")
        data = ManageView().get_manage_checks(vs, None)
        assert data["count"] > 0
        assert not any(name.split(".")[0] in {"guardian", "crud_views_guardian"} for name in sys.modules)
        print("CORE-CHECKS-OK")
    """)
    result = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "CORE-CHECKS-OK" in result.stdout
