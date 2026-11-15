"""Request-free identity, routes and upward-only hierarchy diagnostics."""

import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import pytest
from django.contrib.auth.models import AnonymousUser, Group
from django.test import override_settings
from django.urls import clear_url_caches, resolve
from lxml import html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import ListView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ParentViewSet, ViewSet
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_manage_cards import ManageResource


@pytest.fixture(autouse=True)
def restore_registry():
    with _REGISTRY_LOCK:
        original = dict(_REGISTRY)
    yield
    with _REGISTRY_LOCK:
        _REGISTRY.clear()
        _REGISTRY.update(original)
    clear_url_caches()


def make(model=Publisher, **kwargs):
    return ViewSet(model=model, name="facts_" + uuid4().hex, **kwargs)


def register(viewset, **attrs):
    return type("FactList", (ListView,), {"__module__": __name__, "cv_viewset": viewset, **attrs})


def test_identity_builder_effective_values_and_constructor_sources():
    viewset = make(ordering="", icon_header="", verbose_name=None)
    builder = getattr(ManageView(), "get_manage_facts", None)
    assert callable(builder), "Identity must have an explicit request-free facts builder"
    rows = {row["key"]: row for row in builder(viewset, AnonymousUser())}
    assert rows["model"]["value"] == "tests.test1.app.models.Publisher"
    assert rows["verbose_name"]["value"] == str(Publisher._meta.verbose_name)
    assert rows["verbose_name"]["source"] == "model Meta"
    assert rows["verbose_name"]["is_default"] is False
    for name in ("ordering", "icon_header"):
        assert rows[name]["value"] == "''"
        assert rows[name]["is_default"] is False
    assert rows["prefix"]["is_default"] is True
    assert rows["pk"]["is_default"] is True
    assert rows["pk_name"]["value"] == "'pk'"


@pytest.mark.django_db
def test_hierarchy_uses_only_explicit_coordinates_and_never_samples(django_assert_num_queries):
    root = make(prefix="facts-root", pk_name="root_id")
    mid = make(
        Book,
        prefix="facts-mid",
        pk_name="book_id",
        parent=ParentViewSet(name=root.name, attribute="publisher", pk_name="owner_pk"),
    )
    leaf = make(
        BookNote, prefix="facts-leaf", parent=ParentViewSet(name=mid.name, attribute="book", pk_name="volume_pk")
    )
    resource = make(ManageResource, parent=ParentViewSet(name=leaf.name))
    module = ModuleType("facts_urls")
    module.urlpatterns = root.urlpatterns + mid.urlpatterns + leaf.urlpatterns
    builder = getattr(ManageView(), "get_manage_hierarchy", None)
    assert callable(builder), "Hierarchy must accept explicit route kwargs without a request"
    with override_settings(ROOT_URLCONF=module), django_assert_num_queries(0):
        data = builder(leaf, AnonymousUser(), route_kwargs={"owner_pk": 12, "volume_pk": 34, "unused": 99})
        assert [p["name"] for p in data["parents"]] == [mid.name, root.name]
        assert [p["url"] for p in data["parents"]] == ["/facts-root/12/facts-mid/manage/", "/facts-root/manage/"]
        for parent in data["parents"]:
            assert resolve(parent["url"]).url_name == parent["route_name"]
        missing = builder(leaf, AnonymousUser())
        assert missing["parents"][0]["url"] is None
        assert data["children"][0]["name"] == resource.name
        assert data["children"][0]["resource"] is True
        assert data["children"][0]["route_name"] == resource.get_router_name("manage")
        assert data["children"][0]["route"] == (
            f"/facts-root/<owner_pk>/facts-mid/<volume_pk>/facts-leaf/<{leaf.name}_pk>/{resource.prefix}/manage/"
        )
        assert data["children"][0]["route_error"] is None
        assert data["children"][0]["url"] is None
        assert builder(root, AnonymousUser())["parents"] == []
        assert builder(root, AnonymousUser())["children"][0]["route_name"] == mid.get_router_name("manage")


def test_shared_route_projection_contributed_empty_and_malformed():
    viewset = make(prefix="facts-route")
    register(viewset, cv_path="export", cv_path_contribute=classmethod(lambda cls: r"(?P<format>csv|json)/"))
    manage = ManageView()
    route = next(r for r in manage.get_manage_routes(viewset, None) if r["key"] == "list")
    assert route["route"] == "/facts-route/export/<format>/"
    summary = next(r for r in manage.get_manage_views(viewset, None) if r["key"] == "list")
    assert (summary["route"], summary["route_error"]) == (route["route"], route["route_error"])
    empty = make(ManageResource)
    assert [row["key"] for row in manage.get_manage_routes(empty, None)] == ["manage"]
    assert [row["key"] for row in manage.get_manage_views(empty, None)] == ["manage"]
    empty._views.clear()
    assert manage.get_manage_routes(empty, None) == manage.get_manage_views(empty, None) == []
    broken = make(parent=ParentViewSet(name="missing_parent"))
    register(broken)
    routes = manage.get_manage_routes(broken, None)
    assert all(row["route"] is None and row["route_error"] for row in routes)
    views = manage.get_manage_views(broken, None)
    assert all(row["route_error"] and row["requirement_metadata_error"] for row in views)
    assert manage.get_manage_hierarchy(broken, None)["route_error"]


def test_routes_execute_without_admin_or_admindocs_installed():
    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    code = """
from django.conf import settings
settings.configure(
    SECRET_KEY="facts", INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "crud_views"]
)
import django
django.setup()
from django.contrib.auth.models import Group, AnonymousUser
from crud_views.lib.views.manage import ManageView
from crud_views.lib.views import ListView
from crud_views.lib.viewset import ViewSet
vs = ViewSet(model=Group, name="isolated", prefix="isolated")
class Groups(ListView):
    cv_viewset = vs
routes = ManageView().get_manage_routes(vs, AnonymousUser())
assert next(r for r in routes if r["key"] == "list")["route"] == "/isolated/", routes
"""
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/author/manage/", "/guardian_author/manage/"])
def test_identity_cards_replace_properties_and_spacers(client, django_user_model, path):
    actor = django_user_model.objects.create_user(username="facts-dev")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    client.force_login(actor)
    response = client.get(path)
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    cards = doc.cssselect("#cv-manage-viewset")
    assert len(cards) == 1
    keys = {node.text_content().strip() for node in cards[0].cssselect("th[scope=row]")}
    assert {"name", "prefix", "app", "pk", "pk_name", "model", "parent"} <= keys
    assert not doc.xpath("//h3[normalize-space()='Properties'] | //h4[normalize-space()='Properties']")
    assert not doc.xpath("//br[following-sibling::*[1][self::hr] and following-sibling::*[2][self::br]]")
    assert not doc.cssselect("#cv-manage-hierarchy [data-manage-child] a")
    assert "route (relative to where the ViewSet is included)" in doc.cssselect("#cv-manage-urls")[0].text_content()
