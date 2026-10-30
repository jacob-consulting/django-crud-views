"""Selected native rows must not borrow non-PK joins from authorized read objects."""

import sys
from types import ModuleType, SimpleNamespace

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import connections, models, router, transaction
from django.db.models.signals import post_delete, pre_delete
from django.test import Client, override_settings
from django.test.utils import isolate_apps
from django.urls import clear_url_caches

from crud_views.lib import check as check_module
from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.views import DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "shard"])
ALIASES = ("default", "shard")


@pytest.fixture
def selected_graph(monkeypatch):
    registry = dict(_REGISTRY)
    vocabulary = dict(check_module._VOCAB_CACHE)
    events = []
    with isolate_apps("tests.test1.app"):

        class Root(models.Model):
            code = models.CharField(max_length=40, unique=True)

            class Meta:
                app_label = "app"

            def __str__(self):
                return self.code

        class Child(models.Model):
            target = models.ForeignKey(Root, to_field="code", on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        classes = (Root, Child)
        for alias in ALIASES:
            with connections[alias].schema_editor() as editor:
                for model in classes:
                    editor.create_model(model)
            ct = ContentType.objects.db_manager(alias).get_for_model(Root)
            for action in ("view", "delete"):
                Permission.objects.using(alias).create(
                    content_type_id=ct.pk, codename=f"{action}_root", name=f"{action} root"
                )
        urls = ModuleType("selected_join_urls")
        monkeypatch.setitem(sys.modules, urls.__name__, urls)
        vs = ViewSet(model=Root, name="selected_join")

        class RootList(ListViewPermissionRequired):
            cv_viewset = vs

        class RootDelete(CrispyViewMixin, DeleteViewPermissionRequired):
            form_class = CrispyDeleteForm
            cv_viewset = vs
            cv_show_related_objects = True
            cv_modal = True

            def cv_get_db_alias(self):
                events.append(("selector", self.object))
                return super().cv_get_db_alias()

            def cv_form_valid_hook(self, context):
                events.append(
                    ("hook", self.object, self.object.pk, connections[self.cv_get_delete_db_alias()].in_atomic_block)
                )

            def cv_on_commit(self, context):
                events.append(("commit", self.object, connections[self.cv_get_delete_db_alias()].in_atomic_block))

        urls.urlpatterns = vs.urlpatterns

        def before(sender, instance, using, origin, **kwargs):
            events.append(("pre", instance.pk, using, origin))

        def after(sender, instance, using, origin, **kwargs):
            events.append(("post", instance.pk, using, origin))

        pre_delete.connect(before, sender=Root, weak=False)
        post_delete.connect(after, sender=Root, weak=False)
        try:
            with override_settings(ROOT_URLCONF=urls.__name__):
                clear_url_caches()
                yield SimpleNamespace(
                    Root=Root, Child=Child, view=RootDelete, events=events, url="/selected_join/1/delete/"
                )
        finally:
            pre_delete.disconnect(before, sender=Root)
            post_delete.disconnect(after, sender=Root)
            clear_url_caches()
            ContentType.objects.clear_cache()
            with _REGISTRY_LOCK:
                _REGISTRY.clear()
                _REGISTRY.update(registry)
            check_module._VOCAB_CACHE.clear()
            check_module._VOCAB_CACHE.update(vocabulary)
            for alias in ALIASES:
                with connections[alias].schema_editor() as editor:
                    for model in reversed(classes):
                        editor.delete_model(model)


def _join_world(graph, using):
    read = next(alias for alias in ALIASES if alias != using)
    graph.Root.objects.using(read).create(pk=1, code="original")
    graph.Child.objects.using(read).create(pk=11, target_id="original")
    graph.Root.objects.using(using).create(pk=1, code="selected")
    graph.Root.objects.using(using).create(pk=2, code="original")
    graph.Child.objects.using(using).create(pk=22, target_id="original")
    return read


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_native_selected_join_request(selected_graph, database_routes, monkeypatch, using, atomic, modal):
    g = selected_graph
    read = _join_world(g, using)
    monkeypatch.setattr(g.view, "cv_atomic", atomic)
    with database_routes(read):
        actor = User.objects.create_user(username="join_actor", is_superuser=True)
        client = Client()
        client.force_login(actor)
        original_route = router.db_for_write

        def write(model, **hints):
            if model is g.Root:
                g.events.append(("hint", hints.get("instance")))
                return using
            return original_route(model, **hints)

        monkeypatch.setattr(router, "db_for_write", write)
        headers = {"X-CV-Modal": "true"} if modal else {}
        preview = client.get(g.url, headers=headers)
        assert preview.status_code == 200
        assert preview.context["related_summary"] == {}
        assert preview.context["has_protected_objects"] is False
        assert not [event for event in g.events if event[0] in ("pre", "post", "hook", "commit")]
        g.events.clear()
        invalid = client.post(g.url, {}, headers=headers)
        assert invalid.status_code == (422 if modal else 200)
        assert invalid.context["form"].errors
        assert not [event for event in g.events if event[0] in ("pre", "post", "hook", "commit")]
        assert set(g.Root.objects.using(using).values_list("pk", flat=True)) == {1, 2}
        assert set(g.Child.objects.using(using).values_list("pk", flat=True)) == {22}
        g.events.clear()
        # A transaction on the read alias must not defer the selected alias's callback.
        with transaction.atomic(using=read):
            response = client.post(g.url, {"confirm": "on"}, headers=headers)
            assert response.status_code == (204 if modal else 302)
            assert g.events[-1][0] == "commit"
    assert set(g.Root.objects.using(using).values_list("pk", flat=True)) == {2}
    assert set(g.Child.objects.using(using).values_list("pk", flat=True)) == {22}
    assert set(g.Root.objects.using(read).values_list("pk", flat=True)) == {1}
    assert set(g.Child.objects.using(read).values_list("pk", flat=True)) == {11}
    selected = [event for event in g.events if event[0] == "selector"]
    assert len(selected) == 1
    original = selected[0][1]
    assert (original.pk, original.code, original._state.db) == (None, "original", read)
    assert [event for event in g.events if event[0] == "hint"] == [("hint", original)]
    assert [event for event in g.events if event[0] in ("pre", "post")] == [
        ("pre", 1, using, original),
        ("post", 1, using, original),
    ]
    assert all(event[3] is original for event in g.events if event[0] in ("pre", "post"))
    assert g.events[-2:] == [("hook", original, None, atomic), ("commit", original, False)]
