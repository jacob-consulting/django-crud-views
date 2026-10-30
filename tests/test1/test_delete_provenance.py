"""Native collection provenance and real request transaction evidence (issue #282)."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.db.models.signals import post_delete, pre_delete
from django.test.utils import isolate_apps

from crud_views.lib.deletion import _DeleteCollector, _NativeDeleteBlocked, execute_deletion, inspect_deletion


@contextmanager
def _tables(*model_classes):
    with connection.schema_editor() as editor:
        for model in model_classes:
            editor.create_model(model)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            for model in reversed(model_classes):
                editor.delete_model(model)


def test_native_pk_validation_precedes_collection():
    """Exercise both installed native contracts without inventing composite support on 4.2."""
    with isolate_apps("tests.test1.app"):
        if hasattr(models, "CompositePrimaryKey"):

            class Root(models.Model):
                first = models.IntegerField()
                second = models.IntegerField()
                pk = models.CompositePrimaryKey("first", "second")

                class Meta:
                    app_label = "app"

            target = Root(first=17)
            assert target.pk == (17, None)
        else:

            class Root(models.Model):
                class Meta:
                    app_label = "app"

            target = Root()
        with pytest.raises(ValueError) as native:
            models.Model.delete(target, using="default")
        with pytest.raises(ValueError) as adapted:
            execute_deletion(target, using="default")
        assert str(adapted.value) == str(native.value)


@pytest.fixture
def graph():
    """All model metadata belongs to this test; no live application relation is mutated."""
    with isolate_apps("tests.test1.app"):

        class Root(models.Model):
            label = models.CharField(max_length=50, default="root")

            class Meta:
                app_label = "app"

        class Branch(models.Model):
            root = models.ForeignKey(Root, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        class Leaf(models.Model):
            branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
            root = models.ForeignKey(Root, on_delete=models.CASCADE)
            restricted = models.ForeignKey(Branch, on_delete=models.RESTRICT, related_name="restrictors")

            class Meta:
                app_label = "app"

        class Blocker(models.Model):
            root = models.ForeignKey(Root, on_delete=models.PROTECT)

            class Meta:
                app_label = "app"

        class Custom(models.Model):
            root = models.ForeignKey(Root, on_delete=models.SET_NULL, null=True)

            class Meta:
                app_label = "app"

        class BranchBlocker(models.Model):
            branch = models.ForeignKey(Branch, on_delete=models.PROTECT)

            class Meta:
                app_label = "app"

        class Ignored(models.Model):
            root = models.ForeignKey(Root, on_delete=models.DO_NOTHING, db_constraint=False)

            class Meta:
                app_label = "app"

        with _tables(Root, Branch, Leaf, Blocker, Custom, BranchBlocker, Ignored):
            yield SimpleNamespace(
                Root=Root,
                Branch=Branch,
                Leaf=Leaf,
                Blocker=Blocker,
                Custom=Custom,
                BranchBlocker=BranchBlocker,
                Ignored=Ignored,
            )


@pytest.mark.django_db(transaction=True)
def test_native_protect_before_custom_stops(graph, monkeypatch):
    root = graph.Root.objects.create()
    blocker = graph.Blocker.objects.create(root=root)
    graph.Custom.objects.create(root=root)
    events = []

    def handler(*args):
        events.append("custom")

    monkeypatch.setattr(graph.Custom._meta.get_field("root").remote_field, "on_delete", handler)
    with pytest.raises(_NativeDeleteBlocked) as caught:
        execute_deletion(root, using="default")
    assert isinstance(caught.value.__cause__, ProtectedError)
    assert set(caught.value.__cause__.protected_objects) == {blocker}
    assert events == []
    assert graph.Root.objects.filter(pk=root.pk).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("recursive", [False, True])
def test_custom_before_native_protect_propagates(graph, monkeypatch, recursive):
    from crud_views.lib import deletion

    root = graph.Root.objects.create()
    blocker = graph.Blocker.objects.create(root=root)
    graph.Custom.objects.create(root=root)
    events = []
    native_relations = deletion.get_candidate_relations_to_delete

    def custom_first(opts):
        relations = list(native_relations(opts))
        return sorted(relations, key=lambda rel: rel.related_model is not graph.Custom)

    def handler(collector, field, objects, using):
        events.append("custom")
        graph.Root.objects.using(using).create(label="side effect")
        if recursive:
            collector.collect(objects, source=graph.Root, fail_on_restricted=False)

    monkeypatch.setattr(deletion, "get_candidate_relations_to_delete", custom_first)
    monkeypatch.setattr(graph.Custom._meta.get_field("root").remote_field, "on_delete", handler)
    with pytest.raises(ProtectedError) as caught:
        execute_deletion(root, using="default")
    assert set(caught.value.protected_objects) == {blocker}
    assert events == ["custom"]
    assert graph.Root.objects.filter(label="side effect").exists()


@pytest.mark.django_db(transaction=True)
def test_native_set_null_and_do_nothing_remain_friendly(graph, monkeypatch):
    from crud_views.lib import deletion

    root = graph.Root.objects.create()
    graph.Custom.objects.create(root=root)
    graph.Ignored.objects.create(root=root)
    graph.Blocker.objects.create(root=root)
    native_relations = deletion.get_candidate_relations_to_delete

    def blocker_last(opts):
        return sorted(native_relations(opts), key=lambda rel: rel.related_model is graph.Blocker)

    monkeypatch.setattr(deletion, "get_candidate_relations_to_delete", blocker_last)
    collector = _DeleteCollector(using="default", origin=root)
    with pytest.raises(_NativeDeleteBlocked):
        collector.collect([root])
    assert collector.custom_callback_entered is False
    assert collector.field_updates


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("external", [False, True])
@pytest.mark.parametrize("custom", [False, True])
def test_native_restrict_outer_closure(graph, monkeypatch, external, custom):
    root = graph.Root.objects.create()
    branch = graph.Branch.objects.create(root=root)
    other = graph.Root.objects.create()
    leaf = graph.Leaf.objects.create(root=other if external else root, branch=branch, restricted=branch)
    if external:
        # Outside the cascade closure through BOTH branches, unlike the diamond control.
        outside_branch = graph.Branch.objects.create(root=other)
        leaf.branch = outside_branch
        leaf.save()
    events = []
    if custom:
        graph.Custom.objects.create(root=root)

        def handler(collector, field, objects, using):
            events.append("custom")
            collector.add_field_update(field, None, objects)

        monkeypatch.setattr(graph.Custom._meta.get_field("root").remote_field, "on_delete", handler)
    inspection = inspect_deletion(root, using="default")
    assert bool(inspection.related.protected) is external
    if external:
        expected = RestrictedError if custom else _NativeDeleteBlocked
        with pytest.raises(expected):
            execute_deletion(root, using="default")
        assert graph.Leaf.objects.filter(pk=leaf.pk).exists()
    else:
        count, counts = execute_deletion(root, using="default")
        assert count == 3
        assert counts == {"app.Leaf": 1, "app.Branch": 1, "app.Root": 1}
        assert root.pk is None
    assert events == (["custom"] if custom else [])


@pytest.mark.django_db(transaction=True)
def test_native_sql_signals_origin_fast_deletes_and_updates(graph):
    assert _DeleteCollector.delete is Collector.delete
    root = graph.Root.objects.create()
    branch = graph.Branch.objects.create(root=root)
    graph.Leaf.objects.create(root=root, branch=branch, restricted=branch)
    retained = graph.Custom.objects.create(root=root)
    ignored = graph.Ignored.objects.create(root=root)
    events = []

    def receiver(sender, instance, origin, using, signal, **kwargs):
        events.append((sender, instance.pk, origin, using, signal))

    for signal in (pre_delete, post_delete):
        signal.connect(receiver, sender=graph.Root, weak=False)
    try:
        collector = _DeleteCollector(using="default", origin=root)
        collector.collect([root])
        assert any(qs.model is graph.Leaf for qs in collector.fast_deletes)
        count, _ = collector.delete()
    finally:
        for signal in (pre_delete, post_delete):
            signal.disconnect(receiver, sender=graph.Root)
    assert count == 3
    assert [entry[-1] for entry in events] == [pre_delete, post_delete]
    assert all(origin is root and using == "default" for _, _, origin, using, _ in events)
    assert root.pk is None
    retained.refresh_from_db()
    assert retained.root_id is None
    assert graph.Ignored.objects.filter(pk=ignored.pk).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("signature_kind", ["keyword", "kwargs", "missing", "positional"])
def test_actual_custom_method_signature_dispatch(graph, monkeypatch, signature_kind):
    root = graph.Root.objects.create()
    events = []

    def keyword(self, *, using):
        events.append(using)
        return models.Model.delete(self, using=using)

    def kwargs(self, **options):
        events.append(options)
        return models.Model.delete(self, **options)

    def missing(self):
        events.append("incorrectly invoked")

    def positional(self, using, /):
        events.append("incorrectly invoked")

    monkeypatch.setattr(
        graph.Root,
        "delete",
        {"keyword": keyword, "kwargs": kwargs, "missing": missing, "positional": positional}[signature_kind],
    )
    if signature_kind in {"missing", "positional"}:
        with pytest.raises(ImproperlyConfigured, match="inspectable signature"):
            execute_deletion(root, using="default")
        assert events == []
        assert graph.Root.objects.filter(pk=root.pk).exists()
    else:
        assert execute_deletion(root, using="default")[0] == 1
        assert events == (["default"] if signature_kind == "keyword" else [{"using": "default"}])
        assert root.pk is None


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("handler", [models.PROTECT, models.RESTRICT], ids=["protect", "restrict"])
def test_native_nested_stale_provider_preview(graph, client_user_publisher_delete, monkeypatch, atomic, modal, handler):
    from tests.test1.app.views import PublisherDeleteView

    root = graph.Root.objects.create()
    branch = graph.Branch.objects.create(root=root)
    leaf = graph.Leaf.objects.create(root=root, branch=branch, restricted=branch)
    events = []

    def preview(self, boundaries, *, using):
        assert using == "default"
        result = inspect_deletion(self.object, using=using)
        assert result.related.protected == []
        assert result.related.summary == {"branch": 1, "leaf": 1}
        assert boundaries == ()
        graph.BranchBlocker.objects.using(using).create(branch=branch)
        events.append("preview")
        return ()

    monkeypatch.setattr(PublisherDeleteView, "get_queryset", lambda self: graph.Root.objects.all())
    monkeypatch.setattr(PublisherDeleteView, "cv_atomic", atomic)
    monkeypatch.setattr(PublisherDeleteView, "cv_modal", True)
    monkeypatch.setattr(PublisherDeleteView, "cv_get_delete_preview", preview)
    monkeypatch.setattr(PublisherDeleteView, "cv_form_valid_hook", lambda self, context: events.append("success"))
    monkeypatch.setattr(PublisherDeleteView, "cv_on_commit", lambda self, context: events.append("commit"))
    monkeypatch.setattr(graph.BranchBlocker._meta.get_field("branch").remote_field, "on_delete", handler)
    response = client_user_publisher_delete.post(
        f"/publisher/{root.pk}/delete/", {"confirm": True}, headers={"X-CV-Modal": "true"} if modal else {}
    )
    assert response.status_code == (422 if modal else 200)
    assert response.context["has_protected_objects"] is True
    assert graph.Root.objects.filter(pk=root.pk).exists()
    assert graph.Branch.objects.filter(pk=branch.pk).exists()
    assert graph.Leaf.objects.filter(pk=leaf.pk).exists()
    assert graph.BranchBlocker.objects.count() == 1
    assert events == ["preview"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("keep_parents", [False, True])
def test_native_parent_order_and_keep_parents(keep_parents):
    with isolate_apps("tests.test1.app"):

        class Parent(models.Model):
            class Meta:
                app_label = "app"

        class Child(Parent):
            class Meta:
                app_label = "app"

        with _tables(Parent, Child):
            child = Child.objects.create()
            pk = child.pk
            events = []

            def receiver(sender, instance, origin, **kwargs):
                assert origin is child
                events.append(sender)

            for model in (Parent, Child):
                post_delete.connect(receiver, sender=model, weak=False)
            try:
                collector = _DeleteCollector(using="default", origin=child)
                collector.collect([child], keep_parents=keep_parents)
                collector.delete()
            finally:
                for model in (Parent, Child):
                    post_delete.disconnect(receiver, sender=model)
            assert events == ([Child] if keep_parents else [Child, Parent])
            assert Parent.objects.filter(pk=pk).exists() is keep_parents
            assert not Child.objects.filter(pk=pk).exists()
            assert child.pk is None


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("lazy", [False, True])
def test_custom_lazy_sub_objs_and_request_local_stickiness(graph, monkeypatch, lazy):
    root = graph.Root.objects.create()
    events = []

    def custom(collector, field, objects, using):
        events.append((objects.count(), using))

    custom.lazy_sub_objs = lazy
    monkeypatch.setattr(graph.Custom._meta.get_field("root").remote_field, "on_delete", custom)
    collector = _DeleteCollector(using="default", origin=root)
    collector.collect([root])
    assert events == ([(0, "default")] if lazy else [])
    assert collector.custom_callback_entered is lazy
    second = _DeleteCollector(using="default", origin=root)
    assert second.custom_callback_entered is False
    assert second.data == {}
    graph.Blocker.objects.create(root=root)
    with pytest.raises(_NativeDeleteBlocked):
        second.collect([root])
