"""Resource metadata remains distinct from URL configuration and never reads items."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from django.urls import reverse
from lxml import html

from crud_views.lib.resource import Resource
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, Publisher
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_resource_manage import make_developer


class MetadataItem(Resource):
    storage_key: str

    class Meta:
        app_label = "storage_metadata"
        pk_field = "storage_key"
        pk_type = "[a-z]+"
        verbose_name = "<script>metadata</script>"
        verbose_name_plural = "stored items"
        ordering = "storage_key"

    @classmethod
    def cv_get_items(cls, request, **kwargs):
        raise AssertionError("Metadata inspection must not list Resources")

    @classmethod
    def cv_get_item(cls, request, pk, **kwargs):
        raise AssertionError("Metadata inspection must not load a Resource")


@pytest.mark.django_db
@pytest.mark.parametrize("overrides", [False, True])
@pytest.mark.parametrize("mapping", ["omitted", None, "empty", "mapped"])
def test_resource_manage_metadata(client, django_user_model, overrides, mapping):
    declared = (
        {}
        if mapping == "omitted"
        else {
            "resource_permissions": {"view": "app.view_author"}
            if mapping == "mapped"
            else {}
            if mapping == "empty"
            else None
        }
    )
    if overrides:
        declared.update(
            verbose_name="custom item",
            verbose_name_plural="custom items",
            ordering="",
            pk="[0-9]+",
            pk_name="route_id",
            context_actions_inline=[],
        )

    def build(sfx):
        vs = ViewSet(model=MetadataItem, name="metadata" + sfx, app="url_namespace", **declared)
        return vs, [vs]

    with isolated_routes(build) as vs:
        # App namespaces are deliberately different from the Resource's session-data namespace.
        client.force_login(make_developer(django_user_model, "metadata developer"))
        response = client.get(f"/{vs.prefix}/manage/")
        assert response.status_code == 200
        facts = {row["key"]: row for row in response.context["manage_facts"]}
        assert facts["app"]["value"] == "'url_namespace'"
        assert facts["app"]["source"] == "set"
        for key, value in {"app_label": "storage_metadata", "pk_field": "storage_key", "pk_type": "[a-z]+"}.items():
            assert key in facts, f"Resource metadata must include {key} separately from URL configuration"
            assert facts[key] == {"key": key, "value": repr(value), "source": "Resource metadata", "is_default": True}
        assert facts["pk"]["value"] == repr("[0-9]+" if overrides else "[a-z]+")
        assert facts["pk"]["source"] == ("set" if overrides else "Resource metadata")
        assert facts["pk_name"]["value"] == repr("route_id" if overrides else "pk")
        assert facts["verbose_name"]["value"] == ("custom item" if overrides else MetadataItem._meta.verbose_name)
        assert facts["verbose_name_plural"]["value"] == ("custom items" if overrides else "stored items")
        assert facts["ordering"]["value"] == repr("" if overrides else "storage_key")
        for key in ("verbose_name", "verbose_name_plural", "ordering"):
            assert facts[key]["source"] == ("set" if overrides else "Resource metadata")
            assert facts[key]["is_default"] is (not overrides)
        assert facts["model"]["value"] == f"{MetadataItem.__module__}.{MetadataItem.__qualname__}"
        presentation = response.context["manage_presentation"]
        assert [section["key"] for section in presentation["sections"]] == [
            "context-buttons",
            "templates-and-actions",
            "label-modes",
            "other",
        ]
        entries = {entry["key"]: entry for section in presentation["sections"] for entry in section["entries"]}
        permission = entries["resource_permissions"]
        assert permission["value"] == repr(declared.get("resource_permissions"))
        assert permission["is_default"] is (mapping == "omitted")
        assert permission["source"] == ("default" if mapping == "omitted" else "set")
        assert presentation["sections"][-1]["entries"][-1] == permission
        if overrides:
            assert entries["context_actions_inline"]["value"] == "[]"
            assert entries["context_actions_inline"]["is_default"] is False
        doc = html.fromstring(response.content)
        permission_row = doc.xpath("//*[@id='cv-manage-presentation']//tr[th='resource_permissions']")[0]
        assert ("data-cv-default-row" in permission_row.attrib) is (mapping == "omitted")
        identity = doc.get_element_by_id("cv-manage-viewset")
        assert not identity.cssselect("script")
        assert "Resource" in identity.text_content()
        if not overrides:
            assert "<script>metadata</script>" in identity.text_content()


@pytest.mark.parametrize("cls", [ViewSet, GuardianViewSet])
def test_resource_manage_preserves_model_schema(cls):
    def build(sfx):
        vs = cls(model=Publisher, name="model_shape" + sfx)
        return vs, [vs]

    with isolated_routes(build) as vs:
        manage = ManageView()
        facts = manage.get_manage_facts(vs, AnonymousUser())
        assert [row["key"] for row in facts] == [
            "name",
            "prefix",
            "pk",
            "pk_name",
            "app",
            "model",
            "parent",
            "verbose_name",
            "verbose_name_plural",
            "ordering",
            "icon_header",
        ]
        assert sum(row["is_default"] for row in facts) == 9
        assert next(row for row in facts if row["key"] == "pk")["source"] == "model Meta"
        presentation = manage.get_manage_presentation(vs, AnonymousUser())
        assert [(section["key"], section["default_count"]) for section in presentation["sections"]] == [
            ("context-buttons", 3),
            ("templates-and-actions", 5),
            ("label-modes", 3),
            ("other", 1),
        ]
        assert [entry["key"] for entry in presentation["sections"][-1]["entries"]] == ["manage_view_class"]
        assert (presentation["default_count"], presentation["set_count"]) == (12, 0)


@pytest.mark.django_db
def test_resource_manage_hierarchy(client, django_user_model):
    def build(sfx):
        root = ViewSet(
            model=Publisher, name="metadata_root" + sfx, prefix="meta-root", ancestor_policy={"provider": "none"}
        )
        mid = ViewSet(
            model=Book,
            name="metadata_mid" + sfx,
            prefix="meta-mid",
            parent=ParentViewSet(name=root.name, attribute="publisher", pk_name="owner_pk"),
            ancestor_policy={"provider": "none"},
        )
        leaf = ViewSet(
            model=MetadataItem,
            name="metadata_leaf" + sfx,
            prefix="meta-leaf",
            parent=ParentViewSet(name=mid.name, pk_name="volume_pk"),
        )
        return (root, mid, leaf), [root, mid, leaf]

    with isolated_routes(build) as (_root, mid, leaf):
        publisher = Publisher.objects.create(pk=12, name="Actual parent")
        Book.objects.create(pk=34, title="Actual book", publisher=publisher)
        actor = make_developer(django_user_model, "hierarchy developer")
        client.force_login(actor)
        # No invented parent objects: only the route description appears under children.
        response = client.get(reverse(mid.get_router_name("manage"), kwargs={"owner_pk": 12}))
        assert response.status_code == 200
        child = response.context["manage_hierarchy"]["children"][0]
        assert child["route_name"] == leaf.get_router_name("manage")
        assert child["route"] == "/meta-root/<owner_pk>/meta-mid/<volume_pk>/meta-leaf/manage/"
        assert child["url"] is None and child["route_error"] is None
        node = html.fromstring(response.content).cssselect("[data-manage-child]")[0]
        assert child["route_name"] in node.text_content() and child["route"] in node.text_content()
        assert not node.cssselect("a") and "no manage page" not in node.text_content()
        response = client.get(reverse(leaf.get_router_name("manage"), kwargs={"owner_pk": 12, "volume_pk": 34}))
        assert response.status_code == 200
        assert [row["url"] for row in response.context["manage_hierarchy"]["parents"]] == [
            "/meta-root/12/meta-mid/manage/",
            "/meta-root/manage/",
        ]
        missing = ManageView().get_manage_hierarchy(leaf, actor)
        assert [row["url"] for row in missing["parents"]] == [None, "/meta-root/manage/"]
        with override_settings(ROOT_URLCONF=type("EmptyURLs", (), {"urlpatterns": []})):
            unresolved = ManageView().get_manage_hierarchy(leaf, actor, route_kwargs={"owner_pk": 12})
        assert all(row["url"] is None and row["route_error"] for row in unresolved["parents"])
