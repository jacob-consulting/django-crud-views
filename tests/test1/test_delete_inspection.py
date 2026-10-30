"""Real request regressions for read-only deletion inspection and confirmed writes."""

import pytest
from django.db import connection, models
from django.db.models.signals import post_delete
from django.test.utils import isolate_apps

from tests.test1.app.models import Book, BookNote, Contract, Publisher
from tests.test1.app.views import PublisherCascadeDeleteView


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("outcome", ["invalid", "native-blocked", "business-blocked", "permitted"])
def test_tracer_real_preview_confirmation_and_commit(
    client_user_publisher_cascade_delete, publisher_penguin, monkeypatch, outcome
):
    events = []
    survivor = Publisher.objects.create(name="Survivor")
    survivor_book = Book.objects.create(title="Retained book", publisher=survivor)
    book = Book.objects.create(title="Cascade book", publisher=publisher_penguin)
    note = BookNote.objects.create(book=book, note="Reassign on confirmed delete")
    target_pk, book_pk = publisher_penguin.pk, book.pk

    def replacement():
        events.append("SET")
        Publisher.objects.create(name="Callback side effect")
        return survivor_book.pk

    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", models.SET(replacement))
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_form_valid_hook", lambda self, context: events.append("hook"))

    def committed(self, context):
        assert not connection.in_atomic_block
        events.append("commit")

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_on_commit", committed)
    monkeypatch.setattr(
        PublisherCascadeDeleteView,
        "cv_check_delete_protection",
        lambda self: ["Business blocker"] if outcome == "business-blocked" else [],
    )
    blocker = Contract.objects.create(publisher=publisher_penguin, title="Hidden blocker")
    url = f"/publisher_cascade/{target_pk}/delete/"
    response = client_user_publisher_cascade_delete.get(url)
    assert events == [], "GET must describe relationships without running deletion callbacks"
    assert response.status_code == 200
    assert response.context["delete_preview_incomplete"] is True
    assert response.context["has_protected_objects"] is True
    assert response.context["related_summary"] == {"book": 1}
    assert response.context["protected_objects"] == []
    assert "Hidden blocker" not in response.content.decode()
    assert "This preview is incomplete." in response.content.decode()
    assert not Publisher.objects.filter(name="Callback side effect").exists()

    if outcome != "native-blocked":
        blocker.delete()

    def deleted(sender, instance, origin, **kwargs):
        assert type(origin) is Publisher
        assert origin.pk == target_pk
        events.append("delete-signal")

    post_delete.connect(deleted, sender=Book, weak=False)
    try:
        response = client_user_publisher_cascade_delete.post(url, {} if outcome == "invalid" else {"confirm": True})
    finally:
        post_delete.disconnect(deleted, sender=Book)
    if outcome == "permitted":
        assert response.status_code == 302
        assert events == ["SET", "delete-signal", "hook", "commit"]
        assert not Publisher.objects.filter(pk=target_pk).exists()
        assert not Book.objects.filter(pk=book_pk).exists()
        note.refresh_from_db()
        assert note.book_id == survivor_book.pk
        assert Publisher.objects.filter(name="Callback side effect").count() == 1
    else:
        assert response.status_code == 200
        assert events == []
        assert Publisher.objects.filter(pk=target_pk).exists()
        assert Book.objects.filter(pk=book_pk).exists()
        assert not Publisher.objects.filter(name="Callback side effect").exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
def test_direct_delete_process_pins_alias_before_write_and_keeps_it_for_hooks(publisher_penguin, monkeypatch, atomic):
    view = PublisherCascadeDeleteView()
    view.object = publisher_penguin
    view.cv_atomic = atomic
    events = []

    def select():
        events.append("select")
        return "default"

    def hook(context):
        assert view.object.pk is None
        assert view.cv_get_delete_db_alias() == "default"
        events.append("hook")

    monkeypatch.setattr(view, "cv_get_db_alias", select)
    monkeypatch.setattr(view, "cv_form_valid_hook", hook)
    monkeypatch.setattr(view, "cv_on_commit", lambda context: events.append("commit"))
    pk = publisher_penguin.pk
    view.cv_form_valid_process({})
    assert events == ["select", "hook", "commit"]
    assert not Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("preview", [False, True])
@pytest.mark.parametrize("effect", ["SET", "SET_DEFAULT", "custom-on-delete", "model-delete", "private"])
def test_real_preview_callback_safety_and_confirmed_positive_control(
    client_user_publisher_cascade_delete, publisher_penguin, monkeypatch, atomic, modal, preview, effect
):
    events = []
    view = PublisherCascadeDeleteView
    monkeypatch.setattr(view, "cv_atomic", atomic)
    monkeypatch.setattr(view, "cv_modal", True)
    monkeypatch.setattr(view, "cv_show_related_objects", preview)
    survivor = Publisher.objects.create(name="Retained publisher")
    retained = Book.objects.create(title="Retained", publisher=survivor)
    book = Book.objects.create(title="Cascade", publisher=publisher_penguin)
    note = BookNote.objects.create(book=book, note="Note")
    pk = publisher_penguin.pk
    field = BookNote._meta.get_field("book")

    def event():
        events.append(effect)
        Publisher.objects.create(name="Persisted deletion effect")
        return retained.pk

    if effect == "SET":
        monkeypatch.setattr(field.remote_field, "on_delete", models.SET(event))
    elif effect == "SET_DEFAULT":
        original = field._get_default
        monkeypatch.setattr(field, "default", event)
        monkeypatch.setattr(field, "_get_default", event)
        monkeypatch.setattr(field.remote_field, "on_delete", models.SET_DEFAULT)
        assert original is not event
    elif effect == "custom-on-delete":

        def handler(collector, field, rows, using):
            assert using == "default"
            collector.add_field_update(field, event(), rows)

        monkeypatch.setattr(field.remote_field, "on_delete", handler)
    elif effect == "model-delete":

        def delete(self, *, using):
            assert using == "default"
            event()
            return models.Model.delete(self, using=using)

        monkeypatch.setattr(Publisher, "delete", delete)
    else:

        def bulk(rows, using):
            assert using == "default"
            event()
            return []

        private = models.Field()
        private.set_attributes_from_name("private_effect")
        private.bulk_related_objects = bulk
        monkeypatch.setattr(Publisher._meta, "private_fields", [*Publisher._meta.private_fields, private])
    monkeypatch.setattr(view, "cv_form_valid_hook", lambda self, context: events.append("hook"))

    def commit(self, context):
        assert not connection.in_atomic_block
        events.append("commit")

    monkeypatch.setattr(view, "cv_on_commit", commit)
    url = f"/publisher_cascade/{pk}/delete/"
    headers = {"X-CV-Modal": "true"} if modal else {}
    blocker = Contract.objects.create(publisher=publisher_penguin, title="Hidden protection")
    response = client_user_publisher_cascade_delete.get(url, headers=headers)
    assert response.status_code == 200
    assert response.context["delete_preview_incomplete"] is True
    assert response.context["has_protected_objects"] is True
    assert ("related_summary" in response.context) is preview
    assert "This preview is incomplete." in response.content.decode()
    assert "Hidden protection" not in response.content.decode()
    assert events == []
    for data in ({}, {"confirm": True}):
        response = client_user_publisher_cascade_delete.post(url, data, headers=headers)
        assert response.status_code == (422 if modal else 200)
        assert response.context["has_protected_objects"] is True
        assert events == []
        assert not Publisher.objects.filter(name="Persisted deletion effect").exists()
    blocker.delete()
    with monkeypatch.context() as business:
        business.setattr(view, "cv_check_delete_protection", lambda self: ["Business protection"])
        response = client_user_publisher_cascade_delete.post(url, {"confirm": True}, headers=headers)
        assert response.status_code == (422 if modal else 200)
        assert "Business protection" in response.content.decode()
        assert "This preview is incomplete." in response.content.decode()
        assert events == []
        assert not Publisher.objects.filter(name="Persisted deletion effect").exists()
        assert Publisher.objects.filter(pk=pk).exists()
    response = client_user_publisher_cascade_delete.post(url, {"confirm": True}, headers=headers)
    assert response.status_code == (204 if modal else 302)
    if modal:
        assert response["X-CV-Redirect"]
    assert events == [effect, "hook", "commit"]
    assert Publisher.objects.filter(name="Persisted deletion effect").count() == 1
    assert not Publisher.objects.filter(pk=pk).exists()
    if effect in ("SET", "SET_DEFAULT", "custom-on-delete"):
        note.refresh_from_db()
        assert note.book_id == retained.pk


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("modal", [False, True])
def test_missing_target_never_inspects_or_writes(client_user_publisher_cascade_delete, monkeypatch, atomic, modal):
    events = []
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_atomic", atomic)
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", True)
    for hook in ("cv_get_delete_preview", "cv_post_hook", "cv_form_valid", "cv_on_commit"):
        monkeypatch.setattr(PublisherCascadeDeleteView, hook, lambda *args, **kwargs: events.append("unexpected"))
    headers = {"X-CV-Modal": "true"} if modal else {}
    before = list(Publisher.objects.values())
    for method in ("get", "post"):
        response = getattr(client_user_publisher_cascade_delete, method)(
            "/publisher_cascade/999999/delete/", {"confirm": True}, headers=headers
        )
        assert response.status_code == 404
    assert events == []
    assert list(Publisher.objects.values()) == before


@pytest.mark.django_db
@pytest.mark.parametrize("unknown", [False, True])
def test_empty_root_and_empty_unknown_relationship_have_distinct_completeness(publisher_penguin, monkeypatch, unknown):
    from crud_views.lib.deletion import inspect_deletion

    events = []
    if unknown:
        monkeypatch.setattr(
            Book._meta.get_field("publisher").remote_field, "on_delete", models.SET(lambda: events.append("SET"))
        )
    inspection = inspect_deletion(publisher_penguin, using="default")
    assert inspection.related.tree == [publisher_penguin]
    assert inspection.related.summary == {}
    assert inspection.related.protected == []
    assert inspection.complete is (not unknown)
    assert events == []


@pytest.mark.django_db
@pytest.mark.parametrize("target", [None, "unsaved", "not-a-model"])
def test_delete_alias_requires_resolved_saved_target(target):
    from django.core.exceptions import ImproperlyConfigured

    view = PublisherCascadeDeleteView()
    if target == "unsaved":
        view.object = Publisher(name="Unsaved")
    elif target == "not-a-model":
        view.object = object()
    with pytest.raises(ImproperlyConfigured, match=r"saved self\.object"):
        view.cv_get_delete_db_alias()


@pytest.mark.django_db(transaction=True)
def test_native_restrict_closure_and_cycles_use_real_rows():
    from crud_views.lib.deletion import execute_deletion, inspect_deletion

    with isolate_apps("tests.test1.app"):

        class Root(models.Model):
            class Meta:
                app_label = "app"

        class Node(models.Model):
            root = models.ForeignKey(Root, on_delete=models.CASCADE)
            peer = models.ForeignKey("self", null=True, on_delete=models.RESTRICT)

            class Meta:
                app_label = "app"

        with connection.schema_editor() as editor:
            editor.create_model(Root)
            editor.create_model(Node)
        try:
            root = Root.objects.create()
            first = Node.objects.create(root=root)
            second = Node.objects.create(root=root, peer=first)
            first.peer = second
            first.save()
            inspection = inspect_deletion(root, using="default")
            assert inspection.complete
            assert inspection.related.protected == []
            assert inspection.related.summary == {"node": 2}
            assert execute_deletion(root, using="default")[0] == 3
            assert not Node.objects.exists()
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(Node)
                editor.delete_model(Root)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("keep_parents", [False, True])
def test_native_multitable_parent_preview_and_write(keep_parents):
    from crud_views.lib.deletion import _DeleteCollector, inspect_deletion

    with isolate_apps("tests.test1.app"):

        class InspectionParent(models.Model):
            name = models.CharField(max_length=20)

            class Meta:
                app_label = "app"

        class InspectionChild(InspectionParent):
            value = models.IntegerField(default=1)

            class Meta:
                app_label = "app"

        class InspectionNote(models.Model):
            child = models.ForeignKey(InspectionChild, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        with connection.schema_editor() as editor:
            editor.create_model(InspectionParent)
            editor.create_model(InspectionChild)
            editor.create_model(InspectionNote)
        try:
            child = InspectionChild.objects.create(name="Child")
            InspectionNote.objects.create(child=child)
            pk = child.pk
            inspection = inspect_deletion(child, using="default")
            assert inspection.complete
            assert inspection.related.summary == {"inspection parent": 1, "inspection note": 1}
            assert inspection.related.tree[0] == child
            assert inspection.related.tree[1][0] == InspectionParent.objects.get(pk=pk)
            collector = _DeleteCollector(using="default", origin=child)
            collector.collect([child], keep_parents=keep_parents)
            count, _ = collector.delete()
            assert count == (2 if keep_parents else 3)
            assert not InspectionChild.objects.exists()
            assert InspectionParent.objects.filter(pk=pk).exists() is keep_parents
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(InspectionNote)
                editor.delete_model(InspectionChild)
                editor.delete_model(InspectionParent)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("family", ["ordered", "polymorphic"])
def test_shipped_model_overrides_are_partial_and_run_once_with_using(request, monkeypatch, family):
    from tests.test1.app.models import Author, Car, Vehicle

    events = []
    if family == "ordered":
        model = Author
        target = Author.objects.create(first_name="First", last_name="Author")
        sibling = Author.objects.create(first_name="Second", last_name="Author")
        before_order = sibling.order
        client = request.getfixturevalue("client_user_author_delete")
        url = f"/author/{target.pk}/delete/"
    else:
        model = Car
        target = Car.objects.create(name="Car")
        client = request.getfixturevalue("client_user_vehicle_delete")
        url = f"/vehicle/{target.pk}/delete/"
    original = model.delete
    pk = target.pk

    def delete(self, *, using):
        events.append(using)
        return original(self, using=using)

    monkeypatch.setattr(model, "delete", delete)
    response = client.get(url)
    assert response.context["delete_preview_incomplete"] is True
    assert "This preview is incomplete." in response.content.decode()
    assert events == []
    assert client.post(url, {}).status_code == 200
    assert events == []
    assert client.post(url, {"confirm": True}).status_code == 302
    assert events == ["default"]
    assert not model.objects.filter(pk=pk).exists()
    if family == "ordered":
        sibling.refresh_from_db()
        assert sibling.order == before_order - 1
    else:
        assert not Vehicle.objects.filter(pk=pk).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("family", ["ordered", "polymorphic"])
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("handler", [models.PROTECT, models.RESTRICT])
def test_shipped_custom_delete_stale_native_protection_propagates(request, monkeypatch, family, atomic, handler):
    from tests.test1.app.models import Author, Car, Vehicle
    from tests.test1.app.views import AuthorDeleteView, VehicleDeleteView

    events, raised = [], []
    if family == "ordered":
        model, view = Author, AuthorDeleteView
        target = Author.objects.create(first_name="Target", last_name="Author")
        sibling = Author.objects.create(first_name="Sibling", last_name="Author")
        previous_order = sibling.order
        client = request.getfixturevalue("client_user_author_delete")
        url = f"/author/{target.pk}/delete/"
    else:
        model, view = Car, VehicleDeleteView
        target = Car.objects.create(name="Target car")
        client = request.getfixturevalue("client_user_vehicle_delete")
        url = f"/vehicle/{target.pk}/delete/"
    pk = target.pk
    original = model.delete

    def delete(self, *, using):
        events.append("custom")
        assert using == "default"
        try:
            return original(self, using=using)
        except (models.ProtectedError, models.RestrictedError) as error:
            raised.append(error)
            raise

    with isolate_apps("tests.test1.app"):

        class DeleteBlocker(models.Model):
            target = models.ForeignKey(model, on_delete=handler)

            class Meta:
                app_label = "app"

        with connection.schema_editor() as editor:
            editor.create_model(DeleteBlocker)
        try:
            with monkeypatch.context() as effects:
                original_fields = model._meta.get_fields

                def fields(*args, **kwargs):
                    return (*original_fields(*args, **kwargs), DeleteBlocker._meta.get_field("target").remote_field)

                # A real field/table in an isolated app: expose its reverse relation only
                # to this root for this request, and restore it before dropping the table.
                effects.setattr(model._meta, "get_fields", fields)
                effects.setattr(model, "delete", delete)
                effects.setattr(view, "cv_atomic", atomic)
                effects.setattr(view, "cv_form_valid_hook", lambda *args: events.append("hook"))
                effects.setattr(view, "cv_on_commit", lambda *args: events.append("commit"))

                def late_blocker(self, context):
                    assert context["has_protected_objects"] is False
                    DeleteBlocker.objects.create(target=self.object)

                effects.setattr(view, "cv_post_hook", late_blocker)
                response = client.get(url)
                assert response.context["delete_preview_incomplete"] is True
                assert response.context["has_protected_objects"] is False
                assert events == []
                error_type = models.ProtectedError if handler is models.PROTECT else models.RestrictedError
                with pytest.raises(error_type) as caught:
                    client.post(url, {"confirm": True})
                assert caught.value is raised[0]
                assert events == ["custom"]
                assert DeleteBlocker.objects.filter(target_id=pk).exists()
                assert model.objects.filter(pk=pk).exists()
                if family == "ordered":
                    sibling.refresh_from_db()
                    assert sibling.order == previous_order - (0 if atomic else 1)
                else:
                    assert Vehicle.objects.filter(pk=pk).exists()
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(DeleteBlocker)
