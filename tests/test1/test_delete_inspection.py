"""Real request regressions for read-only deletion inspection and confirmed writes."""

from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from uuid import uuid4

import pytest
from django.db import connection, models
from django.db.models.signals import post_delete
from django.test.utils import isolate_apps

from tests.test1.app.models import Book, BookNote, Contract, Publisher
from tests.test1.app.views import PublisherCascadeDeleteView


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


@pytest.mark.django_db(transaction=True)
def test_inspection_reverse_fk_to_field():
    from crud_views.lib.deletion import inspect_deletion

    with isolate_apps("tests.test1.app"):

        class Target(models.Model):
            code = models.CharField(max_length=60, unique=True)

            class Meta:
                app_label = "app"

        class Cascade(models.Model):
            target = models.ForeignKey(Target, to_field="code", on_delete=models.CASCADE)
            label = models.CharField(max_length=60)

            class Meta:
                app_label = "app"

        class Protector(models.Model):
            target = models.ForeignKey(Target, to_field="code", on_delete=models.PROTECT)

            class Meta:
                app_label = "app"

        with _tables(Target, Cascade, Protector):
            target = Target.objects.create(pk=71, code="鍵-900719925474099312345")
            other = Target.objects.create(pk=72, code="other")
            child = Cascade.objects.create(target=target, label="Loaded without deferral")
            Cascade.objects.create(target=other, label="Unrelated")
            protector = Protector.objects.create(target=target)
            result = inspect_deletion(target, using="default")
            assert result.complete
            assert result.related.tree == [target, [child]]
            assert result.related.summary == {"cascade": 1}
            assert result.related.protected == [protector]
            assert result.related.tree[1][0].get_deferred_fields() == set()


@pytest.mark.django_db(transaction=True)
def test_inspection_distinct_parent_link_keys():
    from crud_views.lib.deletion import inspect_deletion

    with isolate_apps("tests.test1.app"):

        class Parent(models.Model):
            code = models.CharField(max_length=40, unique=True)

            class Meta:
                app_label = "app"

        class Child(Parent):
            child_id = models.IntegerField(primary_key=True)
            parent_link = models.OneToOneField(Parent, to_field="code", parent_link=True, on_delete=models.CASCADE)
            ordinary_key = models.CharField(max_length=40, unique=True)

            class Meta:
                app_label = "app"

        class Cascade(models.Model):
            parent = models.ForeignKey(Parent, to_field="code", on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        class Protector(models.Model):
            child = models.ForeignKey(Child, to_field="ordinary_key", on_delete=models.PROTECT)

            class Meta:
                app_label = "app"

        with _tables(Parent, Child, Cascade, Protector):
            parent = Parent.objects.create(pk=101, code="parent-link-303")
            child = Child(
                id=parent.pk, code=parent.code, child_id=202, parent_link_id=parent.code, ordinary_key="ordinary-404"
            )
            child.save_base(raw=True, force_insert=True)
            cascade = Cascade.objects.create(parent=parent)
            protector = Protector.objects.create(child=child)
            child = Child.objects.get(pk=202)
            result = inspect_deletion(child, using="default")
            assert result.complete
            assert result.related.tree == [child, [parent, cascade]]
            assert result.related.summary == {"parent": 1, "cascade": 1}
            assert result.related.protected == [protector]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("reverse_order", [False, True])
def test_inspection_diamond_cycle_restrict_and_proxy(reverse_order, monkeypatch):
    from crud_views.lib.deletion import DeletePreviewContribution, inspect_deletion, merge_delete_preview

    events = []

    def custom(*args):
        events.append("unsafe")

    with isolate_apps("tests.test1.app"):

        class Root(models.Model):
            key = models.UUIDField(primary_key=True, default=uuid4)

            class Meta:
                app_label = "app"

        class Node(models.Model):
            root = models.ForeignKey(Root, on_delete=models.CASCADE)
            peer = models.ForeignKey("self", null=True, on_delete=models.CASCADE)
            restricted = models.ForeignKey("self", null=True, on_delete=models.RESTRICT, related_name="restrictors")
            unknown = models.ForeignKey("self", null=True, on_delete=custom, related_name="unknowns")

            class Meta:
                app_label = "app"

        class Proxy(Root):
            class Meta:
                proxy = True
                app_label = "app"

        with _tables(Root, Node):
            root = Root.objects.create()
            other = Root.objects.create()
            a = Node.objects.create(root=root)
            b = Node.objects.create(root=root, peer=a, restricted=a)
            a.peer = b
            a.save()
            outside = Node.objects.create(root=other, restricted=a)
            if reverse_order:
                from crud_views.lib import deletion

                original = deletion.get_candidate_relations_to_delete
                monkeypatch.setattr(
                    deletion, "get_candidate_relations_to_delete", lambda opts: reversed(list(original(opts)))
                )
            result = inspect_deletion(Proxy.objects.get(pk=root.pk), using="default")
            assert not result.complete
            assert result.related.summary == {"node": 2}
            assert result.related.protected == [outside]
            assert len(list(PublisherCascadeDeleteView._walk_nested(result.related.tree))) < 12
            boundary = result.boundaries[0]
            merged = merge_delete_preview(
                result, [DeletePreviewContribution(boundary, deleted=(outside,), complete=True)], using="default"
            )
            assert merged.related.protected == [outside], "Provider claims cannot expand native RESTRICT closure"
            assert events == []
            assert set(boundary.source_pks) == {a.pk, b.pk}


@pytest.mark.django_db
def test_provider_tree_shape_and_counts(publisher_penguin, monkeypatch):
    from crud_views.lib.deletion import (
        DeletePreviewContribution,
        RelatedObjects,
        inspect_deletion,
        merge_delete_preview,
    )
    from crud_views.lib.views.delete import RelatedObjects as LegacyRelatedObjects

    assert LegacyRelatedObjects is RelatedObjects
    root = publisher_penguin
    child = Book.objects.create(publisher=root, title="Child")
    grandchild = BookNote.objects.create(book=child, note="Grandchild")
    sibling = Book.objects.create(publisher=root, title="Sibling")
    provider_child = BookNote.objects.create(book=sibling, note="Provider child")
    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", models.SET(lambda: None))
    native = inspect_deletion(root, using="default")
    assert native.related.tree == [root, [child, sibling]]
    assert native.boundaries[0].source_pks == (child.pk, sibling.pk)
    contribution = DeletePreviewContribution(
        native.boundaries[0], deleted=(grandchild, provider_child, grandchild), complete=True
    )
    with pytest.raises(FrozenInstanceError):
        contribution.complete = False
    merged = merge_delete_preview(native, [contribution], using="default")
    assert merged.complete
    assert merged.related.tree == [root, [child, sibling, grandchild, provider_child]]
    assert merged.related.summary == {"book": 2, "book note": 2}
    assert len(merged.related) == 3
    assert native.related.tree == [root, [child, sibling]], "Merging must not mutate the native result"
    # A native nested branch retains its alternating shape and redaction positions.
    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", models.CASCADE)
    nested = inspect_deletion(root, using="default")
    assert nested.related.tree == [root, [child, [grandchild], sibling, [provider_child]]]

    class Actor:
        def has_perm(self, permission):
            return permission != "app.view_book"

    filtered = PublisherCascadeDeleteView().cv_filter_related_objects(Actor(), nested.related)
    assert filtered.tree == [root, [None, [grandchild], None, [provider_child]]]
    assert filtered.summary == {"book": 2, "book note": 2}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid",
    [
        "record",
        "descriptor",
        "unhashable",
        "source-order",
        "alias",
        "duplicate",
        "unsaved",
        "html",
        "dict",
        "wrong-db",
        "complete",
        "container",
    ],
)
def test_provider_rejects_invalid_records(publisher_penguin, monkeypatch, invalid):
    from crud_views.lib.deletion import DeletePreviewContribution, inspect_deletion, merge_delete_preview

    first = Book.objects.create(publisher=publisher_penguin, title="First")
    Book.objects.create(publisher=publisher_penguin, title="Second")
    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", models.SET(lambda: None))
    result = inspect_deletion(publisher_penguin, using="default")
    boundary = result.boundaries[0]
    contribution = DeletePreviewContribution(boundary, deleted=(first,))
    contributions = [contribution]
    if invalid == "record":
        contributions = ["<script>unsafe</script>"]
    elif invalid == "descriptor":
        contributions = [replace(contribution, boundary="invalid")]
    elif invalid == "unhashable":
        contributions = [replace(contribution, boundary=replace(boundary, source_pks=list(boundary.source_pks)))]
    elif invalid == "complete":
        contributions = [replace(contribution, complete="yes")]
    elif invalid == "container":
        contributions = [replace(contribution, deleted="")]
    elif invalid == "source-order":
        contributions = [
            replace(contribution, boundary=replace(boundary, source_pks=tuple(reversed(boundary.source_pks))))
        ]
    elif invalid == "alias":
        contributions = [replace(contribution, boundary=replace(boundary, using="other"))]
    elif invalid == "duplicate":
        contributions *= 2
    else:
        record = {"unsaved": Book(title="unsaved"), "html": "<b>bad</b>", "dict": {}, "wrong-db": first}[invalid]
        if invalid == "wrong-db":
            record._state.db = "other"
        contributions = [replace(contribution, deleted=(record,))]
    with pytest.raises(ValueError):
        merge_delete_preview(result, contributions, using="default")


@pytest.mark.django_db
def test_provider_scoped_coverage_permission_order_and_exceptions(
    client_user_publisher_cascade_delete, publisher_penguin, monkeypatch
):
    from crud_views.lib.deletion import DeletePreviewContribution

    calls = []
    child = Book.objects.create(publisher=publisher_penguin, title="Child")
    note = BookNote.objects.create(book=child, note="<script>隠れた</script>")
    protected = Contract.objects.create(publisher=publisher_penguin, title="Native hidden")
    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", models.SET(lambda: None))
    monkeypatch.setattr(Publisher, "delete", lambda self, **kwargs: None)

    def provider(self, boundaries, *, using):
        calls.append((boundaries, using))
        assert len(boundaries) == 2
        return [DeletePreviewContribution(boundaries[0], deleted=(note,), protected=(note,), complete=True)]

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_get_delete_preview", provider)
    response = client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")
    assert len(calls) == 1
    assert response.context["delete_preview_incomplete"] is True
    assert response.context["has_protected_objects"] is True
    assert response.context["protected_objects"] == []
    assert "隠れた" not in response.content.decode()
    assert protected.title not in response.content.decode()
    assert response.context["related_summary"] == {"book": 1, "book note": 1}
    assert not any("boundar" in key or key == "using" for context in response.context for key in context.flatten())

    class Actor:
        def has_perm(self, permission):
            return permission == "app.view_booknote"

    from crud_views.lib.deletion import RelatedObjects

    second = BookNote.objects.create(book=child, note="Second")
    rows = RelatedObjects([], {}, [note, protected, second])
    assert PublisherCascadeDeleteView().cv_filter_related_objects(Actor(), rows).protected == [note, second]

    def broken(*args, **kwargs):
        raise RuntimeError("provider failure")

    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_get_delete_preview", broken)
    with pytest.raises(RuntimeError, match="provider failure"):
        client_user_publisher_cascade_delete.get(f"/publisher_cascade/{publisher_penguin.pk}/delete/")


@pytest.mark.django_db(transaction=True)
def test_inspection_native_skips_through_and_custom_metadata(monkeypatch):
    from crud_views.lib.deletion import inspect_deletion

    events = []

    class CustomFK(models.ForeignKey):
        def get_foreign_related_value(self, instance):
            events.append("unsafe-custom-join")
            return super().get_foreign_related_value(instance)

    with isolate_apps("tests.test1.app"):

        class Target(models.Model):
            class Meta:
                app_label = "app"

        class Ref(models.Model):
            skipped = models.ForeignKey(Target, null=True, on_delete=models.SET_NULL, related_name="nullable")
            ignored = models.ForeignKey(Target, on_delete=models.DO_NOTHING, related_name="ignored")
            custom = CustomFK(Target, on_delete=models.CASCADE, related_name="custom")

            class Meta:
                app_label = "app"

        class Group(models.Model):
            targets = models.ManyToManyField(Target)

            class Meta:
                app_label = "app"

        with _tables(Target, Ref, Group):
            target = Target.objects.create()
            Ref.objects.create(skipped=target, ignored=target, custom=target)
            group = Group.objects.create()
            group.targets.add(target)
            events.clear()  # setup legitimately uses the custom join
            result = inspect_deletion(target, using="default")
            assert not result.complete
            assert [(b.kind, b.field_name) for b in result.boundaries] == [("on_delete", "custom")]
            through = Group.targets.through.objects.get(target=target)
            assert result.related.tree == [target, [through]]
            assert result.related.summary == {through._meta.verbose_name: 1}
            assert result.related.protected == []
            assert events == []


@pytest.mark.django_db(transaction=True)
def test_inspection_proxy_self_cycle_has_no_phantom_root_count():
    from crud_views.lib.deletion import inspect_deletion

    with isolate_apps("tests.test1.app"):

        class Node(models.Model):
            peer = models.ForeignKey("self", null=True, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        class Proxy(Node):
            class Meta:
                proxy = True
                app_label = "app"

        with _tables(Node):
            root = Node.objects.create()
            child = Node.objects.create(peer=root)
            root.peer = child
            root.save()
            proxy = Proxy.objects.get(pk=root.pk)
            result = inspect_deletion(proxy, using="default")
            assert result.complete
            assert result.related.summary == {}
            assert result.related.tree == [proxy, [child, [proxy]]]


def _check_ids(view):
    return [message.id for check in view.checks() for message in check.messages()]


@pytest.mark.django_db
def test_legacy_collection_override_startup_and_runtime(publisher_penguin, monkeypatch):
    from django.core.exceptions import ImproperlyConfigured

    from crud_views.lib.views.delete import DeleteView

    events = []

    class Legacy(DeleteView):
        def cv_get_related_objects(self):
            events.append("unsafe")

    assert "viewset.E263" in _check_ids(Legacy)
    view = Legacy()
    view.object = publisher_penguin
    with pytest.raises(ImproperlyConfigured, match=r"cv_get_delete_preview.*cv_filter_related_objects"):
        view._cv_inspect_deletion()
    assert events == []


@pytest.mark.django_db
@pytest.mark.parametrize("signature_kind", ["keyword", "kwargs", "no-using", "positional", "opaque"])
def test_custom_delete_signature_diagnostics(publisher_penguin, monkeypatch, signature_kind):
    from django.core.exceptions import ImproperlyConfigured

    from crud_views.lib.deletion import execute_deletion
    from crud_views.lib.views.delete import DeleteView

    events = []

    def keyword(self, *, using):
        events.append(using)

    def kwargs(self, **kwargs):
        events.append(kwargs["using"])

    def no_using(self):
        events.append("unsafe")

    def positional(self, using, /):
        events.append("unsafe")

    class Opaque:
        __signature__ = "uninspectable"

        def __call__(self, **kwargs):
            events.append("unsafe")

    method = {"keyword": keyword, "kwargs": kwargs, "no-using": no_using, "positional": positional, "opaque": Opaque()}[
        signature_kind
    ]
    monkeypatch.setattr(Publisher, "delete", method)

    class SignatureView(DeleteView):
        model = Publisher

    compatible = signature_kind in ("keyword", "kwargs")
    assert ("viewset.E264" in _check_ids(SignatureView)) is (not compatible and signature_kind != "opaque")
    if compatible:
        execute_deletion(publisher_penguin, using="default")
        assert events == ["default"]
    else:
        with pytest.raises(ImproperlyConfigured, match=r"inspectable signature.*using"):
            execute_deletion(publisher_penguin, using="default")
        assert events == []


def test_signature_checks_skip_bare_and_resource_views(monkeypatch):
    from crud_views.lib.resource import Resource, ResourceViewMixin
    from crud_views.lib.views.delete import DeleteView
    from crud_views.lib.viewset import ViewSet

    class Bare(DeleteView):
        cv_modal_size = "bad"

    assert "viewset.E250" in _check_ids(Bare)
    assert "viewset.E264" not in _check_ids(Bare)
    for value in (None, "not a model", object()):

        class NonModel(DeleteView):
            model = value

        assert "viewset.E264" not in _check_ids(NonModel)

    class Item(Resource):
        key: str

        class Meta:
            pk_field = "key"

    vs = ViewSet(model=Item, name="inspection_resource_signature")

    class ResourceDelete(ResourceViewMixin, DeleteView):
        cv_viewset = vs

    assert "viewset.E264" not in _check_ids(ResourceDelete)
    assert "viewset.E262" in [m.id for c in vs.checks() for m in c.messages()]
    monkeypatch.setattr(Publisher, "delete", lambda self: None)

    class BadModel(DeleteView):
        model = Publisher

    assert "viewset.E264" in _check_ids(BadModel)


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("details", [False, True])
@pytest.mark.parametrize("blocker", ["none", "native", "business"])
@pytest.mark.parametrize("row_count", [0, 1, 2])
def test_partial_notice_modes_and_german(
    client_user_publisher_cascade_delete,
    user_publisher_cascade_delete,
    publisher_penguin,
    monkeypatch,
    language,
    modal,
    details,
    blocker,
    row_count,
):
    from django.contrib.auth.models import Permission
    from django.utils.html import escape
    from django.utils.translation import override
    from lxml import html

    labels = ['<script>alert("雪")</script>', "München — 東京"]
    for label in labels[:row_count]:
        Book.objects.create(publisher=publisher_penguin, title=label)
    # A real unknown boundary even for empty relationships, never a synthetic result.
    monkeypatch.setattr(BookNote._meta.get_field("book").remote_field, "on_delete", models.SET(lambda: None))
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", True)
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_show_related_objects", details)
    # Empty cascades need a root boundary as no Book is visited.
    monkeypatch.setattr(Publisher, "delete", lambda self, **kwargs: None)
    user_publisher_cascade_delete.user_permissions.add(Permission.objects.get(codename="view_book"))
    if blocker == "native":
        Contract.objects.create(publisher=publisher_penguin, title="Do not disclose native label")
    elif blocker == "business":
        monkeypatch.setattr(PublisherCascadeDeleteView, "cv_check_delete_protection", lambda self: ["Business block"])
    headers = {"X-CV-Modal": "true"} if modal else {}
    url = f"/publisher_cascade/{publisher_penguin.pk}/delete/"
    with override(language):
        response = client_user_publisher_cascade_delete.get(url, headers=headers)
        notice = {
            "en": "This preview is incomplete. Custom deletion behavior may affect additional objects.",
            "de": "Diese Vorschau ist unvollständig. Benutzerdefiniertes Löschverhalten kann weitere Objekte betreffen.",
        }[language]
        partial = {
            "en": "Some related objects that will also be deleted (partial counts):",
            "de": "Einige verknüpfte Objekte, die ebenfalls gelöscht werden (Teilanzahlen):",
        }[language]
        markup = response.content.decode()
        document = html.fromstring(markup)
        assert response.status_code == 200
        assert markup.count(notice) == 1
        assert document.xpath('//*[contains(@class, "alert-warning")][@role="alert"]')
        assert response.context["delete_preview_incomplete"] is True
        assert response.context["has_protected_objects"] is (blocker == "native")
        assert ("related_summary" in response.context) is details
        if details:
            expected = {"book": row_count} if row_count else {}
            assert response.context["related_summary"] == expected
            assert all(type(count) is int and count >= 0 for count in expected.values())
        assert (partial in markup) is (details and row_count > 0 and blocker != "business")
        assert "Do not disclose native label" not in markup
        assert '<script>alert("雪")</script>' not in markup
        if details and row_count and blocker != "business":
            assert str(escape(labels[0])) in markup
            if row_count == 2:
                assert labels[1] in markup
        confirms = document.xpath('//input[@name="confirm"]')
        forms = document.xpath('//form[contains(@class, "cv-form")]')
        assert len(confirms) == len(forms) == (1 if blocker == "none" else 0)
        if forms:
            assert not forms[0].xpath('.//*[contains(text(), "' + notice + '")]')
        if blocker != "none":
            blocked = client_user_publisher_cascade_delete.post(url, {"confirm": True}, headers=headers)
            assert blocked.status_code == (422 if modal else 200)
            assert notice in blocked.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
def test_complete_preview_retains_copy_and_one_confirmation(
    client_user_publisher_cascade_delete, publisher_penguin, monkeypatch, modal
):
    from lxml import html

    Book.objects.create(publisher=publisher_penguin, title="Complete preview")
    monkeypatch.setattr(PublisherCascadeDeleteView, "cv_modal", True)
    headers = {"X-CV-Modal": "true"} if modal else {}
    response = client_user_publisher_cascade_delete.get(
        f"/publisher_cascade/{publisher_penguin.pk}/delete/", headers=headers
    )
    markup = response.content.decode()
    assert response.context["delete_preview_incomplete"] is False
    assert "The following related objects will also be deleted:" in markup
    assert "partial counts" not in markup
    assert "This preview is incomplete." not in markup
    assert len(html.fromstring(markup).xpath('//input[@name="confirm"]')) == 1


def test_german_delete_catalog_matches_source(tmp_path):
    from pathlib import Path

    import polib

    directory = Path(__file__).resolve().parents[2] / "src/crud_views/locale/de/LC_MESSAGES"
    source = polib.pofile(str(directory / "django.po"))
    for msgid in (
        "This preview is incomplete. Custom deletion behavior may affect additional objects.",
        "Some related objects that will also be deleted (partial counts):",
    ):
        entry = source.find(msgid)
        assert entry is not None and entry.translated()
    regenerated = tmp_path / "django.mo"
    source.save_as_mofile(str(regenerated))
    assert regenerated.read_bytes() == (directory / "django.mo").read_bytes()


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
