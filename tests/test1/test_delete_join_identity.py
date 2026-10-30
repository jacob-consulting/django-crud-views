"""Selected native rows must not borrow non-PK joins from authorized read objects."""

import sys
from contextlib import nullcontext
from types import ModuleType, SimpleNamespace

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import connections, models, router, transaction
from django.db.models.signals import post_delete, post_init, pre_delete
from django.test import Client, override_settings
from django.test.utils import isolate_apps
from django.urls import clear_url_caches

from crud_views.lib import check as check_module
from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.deletion import _DeleteCollector, execute_deletion, inspect_deletion
from crud_views.lib.views import DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "shard"])
ALIASES = ("default", "shard")


@pytest.fixture
def nullable_graph(request, monkeypatch):
    registry = dict(_REGISTRY)
    vocabulary = dict(check_module._VOCAB_CACHE)
    events = []
    with isolate_apps("tests.test1.app"):

        def custom(collector, field, rows, using):
            events.append(("custom", using))
            collector.collect(rows, source=field.remote_field.model, source_attr=field.name)

        handler = getattr(request, "param", models.PROTECT)
        if handler == "custom":
            handler = custom

        class Root(models.Model):
            code = models.CharField(max_length=40, unique=True, null=True)

            class Meta:
                app_label = "app"

            def __str__(self):
                return f"Root {self.pk}"

        class Ref(models.Model):
            target = models.ForeignKey(Root, to_field="code", null=True, on_delete=handler)

            class Meta:
                app_label = "app"

        classes = (Root, Ref)
        with connections["default"].schema_editor() as editor:
            for model in classes:
                editor.create_model(model)
        ct = ContentType.objects.get_for_model(Root)
        for action in ("view", "delete"):
            Permission.objects.create(content_type=ct, codename=f"{action}_root", name=f"{action} root")
        vs = ViewSet(model=Root, name="nullable_join")

        class RootList(ListViewPermissionRequired):
            cv_viewset = vs

        class RootDelete(CrispyViewMixin, DeleteViewPermissionRequired):
            form_class = CrispyDeleteForm
            cv_viewset = vs
            cv_show_related_objects = True
            cv_modal = True

        urls = ModuleType("nullable_join_urls")
        urls.urlpatterns = vs.urlpatterns
        monkeypatch.setitem(sys.modules, urls.__name__, urls)
        actor = User.objects.create_user(username="nullable_actor", is_superuser=True)
        client = Client()
        client.force_login(actor)
        try:
            with override_settings(ROOT_URLCONF=urls.__name__):
                clear_url_caches()
                yield SimpleNamespace(
                    Root=Root, Ref=Ref, view=RootDelete, client=client, events=events, url="/nullable_join/1/delete/"
                )
        finally:
            clear_url_caches()
            ContentType.objects.clear_cache()
            with _REGISTRY_LOCK:
                _REGISTRY.clear()
                _REGISTRY.update(registry)
            check_module._VOCAB_CACHE.clear()
            check_module._VOCAB_CACHE.update(vocabulary)
            with connections["default"].schema_editor() as editor:
                for model in reversed(classes):
                    editor.delete_model(model)


@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_nullable_join_protect_request(nullable_graph, monkeypatch, atomic, modal):
    """An unlinked nullable FK must not prevent confirmation of a null-key root."""
    g = nullable_graph
    root = g.Root.objects.create(pk=1, code=None)
    g.Root.objects.create(pk=2, code=None)
    g.Ref.objects.create(pk=11, target_id=None)
    monkeypatch.setattr(g.view, "cv_atomic", atomic)
    headers = {"X-CV-Modal": "true"} if modal else {}
    preview = g.client.get(g.url, headers=headers)
    assert preview.status_code == 200
    assert preview.context["has_protected_objects"] is False
    assert preview.context["related_summary"] == {}
    assert "confirm" in preview.context["form"].fields
    inspection = inspect_deletion(root, using="default")
    assert inspection.related.protected == []
    assert inspection.related.summary == {}
    assert inspection.related.tree == [root]
    assert inspection.complete is True
    invalid = g.client.post(g.url, {}, headers=headers)
    assert invalid.status_code == (422 if modal else 200)
    assert invalid.context["form"].errors
    assert set(g.Root.objects.values_list("pk", flat=True)) == {1, 2}
    assert set(g.Ref.objects.values_list("pk", flat=True)) == {11}
    response = g.client.post(g.url, {"confirm": "on"}, headers=headers)
    assert response.status_code == (204 if modal else 302)
    assert set(g.Root.objects.values_list("pk", flat=True)) == {2}
    assert set(g.Ref.objects.values_list("pk", flat=True)) == {11}
    assert g.events == []


@pytest.mark.parametrize("nullable_graph", [models.RESTRICT, models.CASCADE], indirect=True)
@pytest.mark.parametrize("unlinked", [0, 1, 3])
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_nullable_join_restrict_cascade_request(nullable_graph, monkeypatch, unlinked, atomic, modal):
    """Neither null-key roots nor unlinked refs contribute a blocker or cascade."""
    g = nullable_graph
    root = g.Root.objects.create(pk=1, code=None)
    g.Root.objects.create(pk=2, code=None)
    g.Root.objects.create(pk=3, code="other")
    for pk in range(11, 11 + unlinked):
        g.Ref.objects.create(pk=pk, target_id=None)
    g.Ref.objects.create(pk=20, target_id="other")
    survivors = {20} | set(range(11, 11 + unlinked))
    monkeypatch.setattr(g.view, "cv_atomic", atomic)
    headers = {"X-CV-Modal": "true"} if modal else {}
    inspection = inspect_deletion(root, using="default")
    assert inspection.complete is True
    assert inspection.related == ([root], {}, [])
    preview = g.client.get(g.url, headers=headers)
    assert preview.status_code == 200
    assert preview.context["related_summary"] == {}
    assert preview.context["has_protected_objects"] is False
    response = g.client.post(g.url, {"confirm": "on"}, headers=headers)
    assert response.status_code == (204 if modal else 302)
    assert set(g.Root.objects.values_list("pk", flat=True)) == {2, 3}
    assert set(g.Ref.objects.values_list("pk", flat=True)) == survivors
    assert g.events == []


@pytest.mark.parametrize("nullable_graph", [models.PROTECT, models.RESTRICT, models.CASCADE], indirect=True)
@pytest.mark.parametrize("unlinked", [0, 1, 3])
@pytest.mark.parametrize("extra_roots", [False, True])
def test_nullable_join_native_counts(nullable_graph, unlinked, extra_roots):
    g = nullable_graph
    root = g.Root.objects.create(pk=1, code=None)
    if extra_roots:
        g.Root.objects.create(pk=2, code=None)
        g.Root.objects.create(pk=3, code=None)
    for pk in range(11, 11 + unlinked):
        g.Ref.objects.create(pk=pk, target_id=None)
    assert inspect_deletion(root, using="default").related == ([root], {}, [])
    assert execute_deletion(root, using="default") == (1, {"app.Root": 1})
    assert set(g.Root.objects.values_list("pk", flat=True)) == ({2, 3} if extra_roots else set())
    assert set(g.Ref.objects.values_list("pk", flat=True)) == set(range(11, 11 + unlinked))
    assert g.events == []


@pytest.mark.parametrize("nullable_graph", [models.PROTECT, models.RESTRICT, models.CASCADE], indirect=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_nullable_join_nonnull_controls(nullable_graph, monkeypatch, atomic, modal):
    """Filtering absent joins must retain actual native protection and cascades."""
    g = nullable_graph
    root = g.Root.objects.create(pk=1, code="selected")
    g.Root.objects.create(pk=2, code="other")
    g.Ref.objects.create(pk=11, target_id=None)
    linked = g.Ref.objects.create(pk=12, target_id="selected")
    g.Ref.objects.create(pk=13, target_id="other")
    cascade = g.Ref._meta.get_field("target").remote_field.on_delete is models.CASCADE
    monkeypatch.setattr(g.view, "cv_atomic", atomic)
    headers = {"X-CV-Modal": "true"} if modal else {}
    inspection = inspect_deletion(root, using="default")
    assert inspection.complete is True
    assert inspection.related.protected == ([] if cascade else [linked])
    assert inspection.related.summary == ({"ref": 1} if cascade else {})
    preview = g.client.get(g.url, headers=headers)
    assert preview.status_code == 200
    assert preview.context["has_protected_objects"] is (not cascade)
    assert preview.context["related_summary"] == ({"ref": 1} if cascade else {})
    response = g.client.post(g.url, {"confirm": "on"}, headers=headers)
    assert response.status_code == ((204 if modal else 302) if cascade else (422 if modal else 200))
    if not cascade:
        assert response.context["has_protected_objects"] is True
    assert set(g.Root.objects.values_list("pk", flat=True)) == ({2} if cascade else {1, 2})
    assert set(g.Ref.objects.values_list("pk", flat=True)) == ({11, 13} if cascade else {11, 12, 13})
    assert g.events == []


@pytest.mark.parametrize("nullable_graph", [models.CASCADE], indirect=True)
def test_nullable_join_nonnull_native_count(nullable_graph):
    g = nullable_graph
    root = g.Root.objects.create(pk=1, code="selected")
    g.Root.objects.create(pk=2, code="other")
    g.Ref.objects.create(pk=11, target_id=None)
    g.Ref.objects.create(pk=12, target_id="selected")
    g.Ref.objects.create(pk=13, target_id="other")
    assert execute_deletion(root, using="default") == (2, {"app.Root": 1, "app.Ref": 1})
    assert set(g.Root.objects.values_list("pk", flat=True)) == {2}
    assert set(g.Ref.objects.values_list("pk", flat=True)) == {11, 13}


@pytest.mark.parametrize("nullable_graph", ["custom"], indirect=True)
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("atomic", [False, True])
def test_nullable_join_unknown_boundary(nullable_graph, monkeypatch, modal, atomic):
    """A null join cannot attest custom behavior or execute it during inspection."""
    g = nullable_graph
    root = g.Root.objects.create(pk=1, code=None)
    g.Root.objects.create(pk=2, code=None)
    g.Ref.objects.create(pk=11, target_id=None)
    monkeypatch.setattr(g.view, "cv_atomic", atomic)
    headers = {"X-CV-Modal": "true"} if modal else {}
    inspection = inspect_deletion(root, using="default")
    assert inspection.complete is False
    assert len(inspection.boundaries) == 1
    boundary = inspection.boundaries[0]
    assert (boundary.kind, boundary.model, boundary.field_name, boundary.field_model) == (
        "on_delete",
        g.Root,
        "target",
        g.Ref,
    )
    assert boundary.source_pks == (1,)
    assert inspection.related == ([root], {}, [])
    for response in (g.client.get(g.url, headers=headers), g.client.post(g.url, {}, headers=headers)):
        assert response.status_code in (200, 422)
        assert response.context["delete_preview_incomplete"] is True
        assert response.context["has_protected_objects"] is False
        assert response.context["related_summary"] == {}
    assert g.events == []
    assert set(g.Root.objects.values_list("pk", flat=True)) == {1, 2}
    assert set(g.Ref.objects.values_list("pk", flat=True)) == {11}
    with monkeypatch.context() as protected:
        protected.setattr(g.view, "cv_check_delete_protection", lambda self: ["Business protection"])
        response = g.client.post(g.url, {"confirm": "on"}, headers=headers)
        assert response.status_code == (422 if modal else 200)
        assert response.context["delete_preview_incomplete"] is True
        assert "Business protection" in response.content.decode()
    assert g.events == []
    assert set(g.Root.objects.values_list("pk", flat=True)) == {1, 2}
    response = g.client.post(g.url, {"confirm": "on"}, headers=headers)
    assert response.status_code == (204 if modal else 302)
    assert g.events == []
    assert set(g.Root.objects.values_list("pk", flat=True)) == {2}
    assert set(g.Ref.objects.values_list("pk", flat=True)) == {11}
    # A real matching row proves this handler does execute after valid confirmation.
    g.Root.objects.create(pk=1, code="selected")
    g.Ref.objects.create(pk=12, target_id="selected")
    response = g.client.post(g.url, {"confirm": "on"}, headers=headers)
    assert response.status_code == (204 if modal else 302)
    assert g.events == [("custom", "default")]
    assert set(g.Root.objects.values_list("pk", flat=True)) == {2}
    assert set(g.Ref.objects.values_list("pk", flat=True)) == {11}


def test_nullable_join_parent_link():
    """A supported nullable parent link must not collect unrelated null-key parents."""
    with isolate_apps("tests.test1.app"):

        class Parent(models.Model):
            code = models.CharField(max_length=40, unique=True, null=True)

            class Meta:
                app_label = "app"

        class Child(Parent):
            child_id = models.IntegerField(primary_key=True)
            parent_link = models.OneToOneField(
                Parent, to_field="code", parent_link=True, null=True, on_delete=models.CASCADE
            )

            class Meta:
                app_label = "app"

        with connections["default"].schema_editor() as editor:
            editor.create_model(Parent)
            editor.create_model(Child)
        try:
            Parent.objects.create(pk=101, code=None)
            Parent.objects.create(pk=102, code=None)
            child = Child(child_id=202, parent_link_id=None)
            child.save_base(raw=True, force_insert=True, using="default")
            inspection = inspect_deletion(child, using="default")
            assert inspection.complete is True
            assert inspection.related == ([child], {}, [])
            collector = _DeleteCollector(using="default", origin=child)
            collector.collect([child])
            assert collector.delete() == (1, {"app.Child": 1})
            assert set(Parent.objects.values_list("pk", flat=True)) == {101, 102}
            with connections["default"].cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM "app_child"')
                assert cursor.fetchone() == (0,)
        finally:
            with connections["default"].schema_editor() as editor:
                editor.delete_model(Child)
                editor.delete_model(Parent)


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

        class Parent(models.Model):
            code = models.CharField(max_length=40, unique=True)

            class Meta:
                app_label = "app"

        class Descendant(Parent):
            child_id = models.IntegerField(primary_key=True)
            parent_link = models.OneToOneField(Parent, to_field="code", parent_link=True, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        class Blocker(models.Model):
            child = models.ForeignKey(Descendant, on_delete=models.PROTECT)

            class Meta:
                app_label = "app"

        classes = (Root, Child, Parent, Descendant, Blocker)
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
                    Root=Root,
                    Child=Child,
                    Parent=Parent,
                    Descendant=Descendant,
                    Blocker=Blocker,
                    view=RootDelete,
                    events=events,
                    url="/selected_join/1/delete/",
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


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("blocked", [False, True])
def test_native_selected_parent_links(selected_graph, database_routes, monkeypatch, using, atomic, blocked):
    """A selected child must query its parent link even with a poisoned descriptor cache."""
    g = selected_graph
    read = next(alias for alias in ALIASES if alias != using)
    for alias, code in ((read, "read-parent"), (using, "selected-parent")):
        parent = g.Parent.objects.using(alias).create(pk=101, code=code)
        g.Parent.objects.using(alias).create(pk=303, code="unrelated")
        child = g.Descendant(id=101, code=code, child_id=202, parent_link_id=parent.code)
        child.save_base(raw=True, force_insert=True, using=alias)
    foreign_parent = g.Parent.objects.using(read).get(pk=303)
    g.Blocker.objects.using(read).create(pk=401, child_id=202)
    if blocked:
        g.Blocker.objects.using(using).create(pk=402, child_id=202)

    def poison(sender, instance, **kwargs):
        g.Descendant._meta.get_field("parent_link").set_cached_value(instance, foreign_parent)

    post_init.connect(poison, sender=g.Descendant, weak=False)
    monkeypatch.setattr(g.view, "get_queryset", lambda self: g.Descendant.objects.using(read).all())
    monkeypatch.setattr(g.view, "cv_atomic", atomic)
    monkeypatch.setattr(g.view, "cv_get_db_alias", lambda self: using)
    try:
        with database_routes(read):
            actor = User.objects.create_user(username="parent_actor", is_superuser=True)
            client = Client()
            client.force_login(actor)
            with transaction.atomic(using=read):
                response = client.post("/selected_join/202/delete/", {"confirm": "on"})
                assert response.status_code == (200 if blocked else 302)
                if not blocked:
                    assert g.events[-1][0] == "commit"
        assert set(g.Parent.objects.using(using).values_list("pk", flat=True)) == ({101, 303} if blocked else {303})
        assert set(g.Descendant.objects.using(using).values_list("pk", flat=True)) == ({202} if blocked else set())
        assert set(g.Parent.objects.using(read).values_list("pk", flat=True)) == {101, 303}
        assert set(g.Descendant.objects.using(read).values_list("pk", flat=True)) == {202}
        assert set(g.Blocker.objects.using(read).values_list("pk", flat=True)) == {401}
        if blocked:
            assert g.events == []
        else:
            original = g.events[-2][1]
            assert original.pk is None and original._state.db == read
            assert original._state.fields_cache["parent_link"] is foreign_parent
            assert g.events[-2:] == [("hook", original, None, atomic), ("commit", original, False)]
    finally:
        post_init.disconnect(poison, sender=g.Descendant)


@pytest.mark.parametrize("using", ALIASES)
def test_native_selected_parent_links_keep_parents(selected_graph, using):
    g = selected_graph
    parent = g.Parent.objects.using(using).create(pk=101, code="parent")
    child = g.Descendant(id=101, code="parent", child_id=202, parent_link_id="parent")
    child.save_base(raw=True, force_insert=True, using=using)
    collector = _DeleteCollector(using=using, origin=child)
    collector.collect([child], keep_parents=True)
    assert collector.delete()[0] == 1
    assert g.Parent.objects.using(using).filter(pk=parent.pk).exists()
    assert not g.Descendant.objects.using(using).exists()


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("atomic", [False, True])
def test_native_selected_missing_row(selected_graph, monkeypatch, using, atomic):
    g = selected_graph
    read = next(alias for alias in ALIASES if alias != using)
    target = g.Root.objects.using(read).create(pk=1, code="original")
    view = g.view()
    view.object = target
    view.cv_atomic = atomic
    monkeypatch.setattr(view, "cv_get_db_alias", lambda: using)
    with pytest.raises(g.Root.DoesNotExist):
        view.cv_form_valid_process({})
    assert g.events == []
    assert target.pk == 1 and target._state.db == read
    assert g.Root.objects.using(read).filter(pk=1).exists()


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("atomic", [False, True])
def test_native_selected_custom_dispatch(selected_graph, monkeypatch, using, atomic):
    g = selected_graph
    read = next(alias for alias in ALIASES if alias != using)
    target = g.Root.objects.using(read).create(pk=1, code="original")
    # A real custom implementation explicitly re-fetches its chosen write row.
    # Its external event and storage effects must survive adapter dispatch unchanged.
    g.Root.objects.using(using).create(pk=1, code="selected")
    original_delete = g.Root.delete

    def delete(self, *, using):
        g.events.append(("model", self, using))
        selected = type(self)._base_manager.using(using).get(pk=self.pk)
        result = original_delete(selected, using=using)
        self.pk = None
        return result

    monkeypatch.setattr(g.Root, "delete", delete)
    with transaction.atomic(using=using) if atomic else nullcontext():
        result = execute_deletion(target, using=using)
    assert result[0] == 1
    assert [event for event in g.events if event[0] == "model"] == [("model", target, using)]
    assert target.pk is None and target._state.db == read
    assert not g.Root.objects.using(using).exists()
    assert g.Root.objects.using(read).filter(pk=1).exists()


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("atomic", [False, True])
def test_native_selected_success_hook_failure(selected_graph, database_routes, monkeypatch, using, atomic):
    g = selected_graph
    read = _join_world(g, using)
    error = RuntimeError("selected hook failed")

    def hook(self, context):
        g.events.append(("failed-hook", self.object, self.object.pk, connections[using].in_atomic_block))
        g.Root.objects.using(using).create(pk=3, code="hook-effect")
        raise error

    monkeypatch.setattr(g.view, "cv_atomic", atomic)
    monkeypatch.setattr(g.view, "cv_get_db_alias", lambda self: using)
    monkeypatch.setattr(g.view, "cv_form_valid_hook", hook)
    with database_routes(read):
        actor = User.objects.create_user(username="hook_actor", is_superuser=True)
        client = Client()
        client.force_login(actor)
        with pytest.raises(RuntimeError) as caught:
            client.post(g.url, {"confirm": "on"})
    assert caught.value is error
    assert set(g.Root.objects.using(using).values_list("pk", flat=True)) == ({1, 2} if atomic else {2, 3})
    assert set(g.Child.objects.using(using).values_list("pk", flat=True)) == {22}
    assert set(g.Root.objects.using(read).values_list("pk", flat=True)) == {1}
    assert [event[0] for event in g.events] == ["pre", "post", "failed-hook"]
    assert g.events[-1][2:] == (None, atomic)


@pytest.mark.parametrize("using", ALIASES)
def test_native_selected_read_error_propagates(selected_graph, monkeypatch, using):
    g = selected_graph
    read = _join_world(g, using)
    target = g.Root.objects.using(read).get(pk=1)
    error = RuntimeError("selected value converter failed")
    field = g.Root._meta.get_field("code")

    def convert(value, expression, connection):
        assert connection.alias == using
        raise error

    monkeypatch.setattr(field, "from_db_value", convert, raising=False)
    with pytest.raises(RuntimeError) as caught:
        execute_deletion(target, using=using)
    assert caught.value is error
    assert target.pk == 1 and g.events == []
    assert set(g.Root.objects.using(using).values_list("pk", flat=True)) == {1, 2}
    assert set(g.Child.objects.using(using).values_list("pk", flat=True)) == {22}


@pytest.mark.parametrize("using", ALIASES)
def test_native_selected_denied_request(selected_graph, database_routes, using):
    g = selected_graph
    read = _join_world(g, using)
    with database_routes(read):
        actor = User.objects.create_user(username="denied_actor")
        client = Client()
        client.force_login(actor)
        assert client.post(g.url, {"confirm": "on"}).status_code == 403
    assert g.events == []
    assert set(g.Root.objects.using(using).values_list("pk", flat=True)) == {1, 2}
    assert set(g.Child.objects.using(using).values_list("pk", flat=True)) == {22}


@pytest.mark.parametrize("using", ALIASES)
def test_native_selected_join_count(selected_graph, using):
    g = selected_graph
    read = _join_world(g, using)
    original = g.Root.objects.using(read).get(pk=1)
    result = execute_deletion(original, using=using)
    assert result == (1, {"app.Root": 1})
    assert original.pk is None
    assert set(g.Root.objects.using(using).values_list("pk", flat=True)) == {2}
    assert set(g.Child.objects.using(using).values_list("pk", flat=True)) == {22}


@pytest.mark.parametrize("using", ALIASES)
def test_native_selected_same_alias_stale_join(selected_graph, using):
    g = selected_graph
    original = g.Root.objects.using(using).create(pk=1, code="original")
    g.Root.objects.using(using).filter(pk=1).update(code="selected")
    g.Root.objects.using(using).create(pk=2, code="original")
    g.Child.objects.using(using).create(pk=22, target_id="original")
    assert execute_deletion(original, using=using) == (1, {"app.Root": 1})
    assert original.pk is None and original.code == "original"
    assert set(g.Root.objects.using(using).values_list("pk", flat=True)) == {2}
    assert set(g.Child.objects.using(using).values_list("pk", flat=True)) == {22}


@pytest.mark.parametrize("using", ALIASES)
def test_native_selected_parent_converter_error(selected_graph, monkeypatch, using):
    g = selected_graph
    parent = g.Parent.objects.using(using).create(pk=101, code="parent")
    child = g.Descendant(id=101, code="parent", child_id=202, parent_link_id="parent")
    child.save_base(raw=True, force_insert=True, using=using)
    target = g.Descendant.objects.using(using).get(pk=202)
    error = RuntimeError("parent converter failed")
    reads = []

    def convert(value, expression, connection):
        reads.append(connection.alias)
        if len(reads) == 2:
            raise error
        return value

    monkeypatch.setattr(g.Parent._meta.get_field("code"), "from_db_value", convert, raising=False)
    with pytest.raises(RuntimeError) as caught:
        execute_deletion(target, using=using)
    assert caught.value is error
    assert reads == [using, using]
    assert target.pk == 202
    assert g.Parent.objects.using(using).filter(pk=parent.pk).exists()
    assert g.Descendant.objects.using(using).filter(pk=202).exists()
