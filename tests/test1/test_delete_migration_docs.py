"""Execute the published migration fences, including copied templates and real deletion effects."""

import copy
import re
import sys
from dataclasses import replace
from types import ModuleType, SimpleNamespace

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.db.models.signals import post_delete
from django.test import Client, override_settings
from django.test.utils import isolate_apps
from django.urls import clear_url_caches
from lxml import html

from crud_views.lib import check as check_module
from crud_views.lib.deletion import DeletePreviewContribution, inspect_deletion
from crud_views.lib.views import ListViewPermissionRequired
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from tests.test1.test_label_mode_docs import DOCS, FENCE, _section

MIGRATION = DOCS / "migrating-1.0.md"
TEMPLATE_FENCE = re.compile(r"^```django\n(.*?)^```", re.MULTILINE | re.DOTALL)
OVERRIDE = "### Safe deletion preview overrides"
EFFECT = "### Describing custom deletion effects"
TEMPLATES = "### Copied delete templates with incomplete previews"
NOTICE = "This preview is incomplete. Custom deletion behavior may affect additional objects."
GENERIC = "Other objects still reference this one; remove or reassign them before deleting it."


def _recipe(heading, pattern=FENCE, count=1):
    section = _section(MIGRATION.read_text(), heading)  # asserts the exact heading appears once
    fences = pattern.findall(section)
    assert len(fences) == count, f"{heading}: expected {count} complete recipe fences"
    return fences


@pytest.fixture
def recipes(monkeypatch, transactional_db):
    """Dynamic effects, modules, tables, registry, URL caches and signals all belong to this test."""
    registry_before = dict(_REGISTRY)
    vocabulary_before = dict(check_module._VOCAB_CACHE)
    events = []
    with isolate_apps("tests.test1.app"):

        def delete_attachments(collector, field, sub_objs, using):
            events.append(("handler", using))
            collector.collect(sub_objs, source=field.remote_field.model, source_attr=field.name)

        class Document(models.Model):
            title = models.CharField(max_length=80)

            class Meta:
                app_label = "app"

            def delete(self, *, using=None, keep_parents=False):
                events.append(("model", using))
                PreviewNote.objects.using(using).filter(document_key=self.pk).delete()
                return super().delete(using=using, keep_parents=keep_parents)

            def __str__(self):
                return self.title

        class PreviewNote(models.Model):
            document_key = models.IntegerField()
            title = models.CharField(max_length=80)

            class Meta:
                app_label = "app"

            def __str__(self):
                return self.title

        class Attachment(models.Model):
            document = models.ForeignKey(Document, on_delete=delete_attachments)
            title = models.CharField(max_length=80)

            class Meta:
                app_label = "app"

            def __str__(self):
                return self.title

        class Blocker(models.Model):
            document = models.ForeignKey(Document, on_delete=models.PROTECT)
            title = models.CharField(max_length=80)
            is_archived = models.BooleanField(default=False)

            class Meta:
                app_label = "app"

            def __str__(self):
                return self.title

        model_classes = (Document, PreviewNote, Attachment, Blocker)
        with connection.schema_editor() as editor:
            for model in model_classes:
                editor.create_model(model)
        name = "migration_document"
        signal_id = "migration_document_deleted"

        def deleted(sender, using, **kwargs):
            events.append(("signal", using))

        post_delete.connect(deleted, sender=Document, dispatch_uid=signal_id, weak=False)
        try:
            vs = ViewSet(model=Document, name=name)

            class DocumentListView(ListViewPermissionRequired):
                cv_viewset = vs

            package = ModuleType("myapp")
            package.__path__ = []
            model_module = ModuleType("myapp.models")
            for model in model_classes:
                setattr(model_module, model.__name__, model)
            viewsets = ModuleType("myapp.viewsets")
            viewsets.cv_document = vs
            for module in (package, model_module, viewsets):
                monkeypatch.setitem(sys.modules, module.__name__, module)

            def build(heading):
                # The entire published fence executes, including imports and class registration.
                vs._views.pop("delete", None)
                namespace = {"__name__": "myapp.recipe"}
                exec(compile(_recipe(heading)[0], str(MIGRATION), "exec"), namespace)
                return vs.get_view_class("delete")

            content, snippet = _recipe(TEMPLATES, TEMPLATE_FENCE, count=2)
            config = copy.deepcopy(settings.TEMPLATES)
            config[0]["APP_DIRS"] = False
            config[0]["OPTIONS"]["loaders"] = [
                (
                    "django.template.loaders.locmem.Loader",
                    {"myapp/delete.content.html": content, "myapp/delete_related.html": snippet},
                ),
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ]
            urls = ModuleType("myapp.recipe_urls")
            monkeypatch.setitem(sys.modules, urls.__name__, urls)

            def install(view):
                view.cv_content_template = "myapp/delete.content.html"
                urls.urlpatterns = vs.urlpatterns
                clear_url_caches()

            actor = User.objects.create_user(username="recipe_actor")
            ct = ContentType.objects.get_for_model(Document)
            perm, _ = Permission.objects.get_or_create(content_type=ct, codename="delete_document", name="Delete doc")
            actor.user_permissions.add(perm)
            client = Client()
            client.force_login(actor)
            target = Document.objects.create(title="Document")
            note = PreviewNote.objects.create(document_key=target.pk, title="<script>secret note</script>")
            attachment = Attachment.objects.create(document=target, title="Secret attachment")
            with override_settings(ROOT_URLCONF=urls.__name__, TEMPLATES=config):
                clear_url_caches()
                yield SimpleNamespace(
                    build=build,
                    install=install,
                    client=client,
                    target=target,
                    note=note,
                    attachment=attachment,
                    Document=Document,
                    PreviewNote=PreviewNote,
                    Attachment=Attachment,
                    Blocker=Blocker,
                    events=events,
                    actor=actor,
                    url=f"/{name}/{target.pk}/delete/",
                )
        finally:
            post_delete.disconnect(sender=Document, dispatch_uid=signal_id)
            clear_url_caches()
            ContentType.objects.clear_cache()
            with _REGISTRY_LOCK:
                _REGISTRY.clear()
                _REGISTRY.update(registry_before)
            check_module._VOCAB_CACHE.clear()
            check_module._VOCAB_CACHE.update(vocabulary_before)
            with connection.schema_editor() as editor:
                for model in reversed(model_classes):
                    editor.delete_model(model)


@pytest.mark.parametrize("heading,summary", [(OVERRIDE, {"preview note": 1}), (EFFECT, {"attachment": 1})])
@pytest.mark.parametrize("details", [False, True])
def test_published_providers_and_copied_templates_execute(recipes, heading, summary, details):
    r = recipes
    view = r.build(heading)
    view.cv_show_related_objects = details
    r.install(view)
    response = r.client.get(r.url)
    assert response.status_code == 200
    assert response.context["delete_preview_incomplete"] is True  # the other boundary is unresolved
    assert response.context["has_protected_objects"] is False
    assert ("related_summary" in response.context) is details
    markup = response.content.decode()
    assert markup.count(NOTICE) == 1
    assert "secret note" not in markup and "Secret attachment" not in markup
    doc = html.fromstring(markup)
    assert len(doc.cssselect('input[name="confirm"]')) == 1
    assert len(doc.cssselect('button[type="submit"]')) == 1
    if details:
        assert response.context["related_summary"] == summary
        assert "partial counts" in markup
    assert r.events == []
    invalid = r.client.post(r.url, {})
    assert invalid.status_code == 200
    assert invalid.context["form"].errors
    assert r.events == [] and r.Document.objects.filter(pk=r.target.pk).exists()
    success = r.client.post(r.url, {"confirm": "on"})
    assert success.status_code == 302
    assert not r.Document.objects.exists() and not r.PreviewNote.objects.exists() and not r.Attachment.objects.exists()
    assert r.events == [("model", "default"), ("handler", "default"), ("signal", "default")]


@pytest.mark.parametrize("details", [False, True])
@pytest.mark.parametrize("block", ["hidden-native", "archived-native", "provider", "business"])
def test_copied_templates_preserve_independent_notices_and_gates(recipes, details, block):
    r = recipes
    view = r.build(OVERRIDE)
    view.cv_show_related_objects = details
    if block in ("hidden-native", "archived-native"):
        r.Blocker.objects.create(
            document=r.target, title="Never disclose blocker", is_archived=block == "archived-native"
        )
    if block == "archived-native":
        # Authorization permits blocker labels; the published business redaction must still narrow them.
        ct = ContentType.objects.get_for_model(r.Blocker)
        permission = Permission.objects.create(content_type=ct, codename="view_blocker", name="View blocker")
        r.actor.user_permissions.add(permission)
    elif block == "provider":
        original = view.cv_get_delete_preview

        def veto(self, boundaries, *, using):
            return [replace(record, protected=(r.note,)) for record in original(self, boundaries, using=using)]

        view.cv_get_delete_preview = veto
    elif block == "business":
        view.cv_check_delete_protection = lambda self: ["Business veto"]
    r.install(view)
    for response in (r.client.get(r.url), r.client.post(r.url, {"confirm": "on"})):
        assert response.status_code == 200
        markup = response.content.decode()
        assert markup.count(NOTICE) == 1
        assert "Never disclose blocker" not in markup and "secret note" not in markup
        assert not html.fromstring(markup).cssselect("form")
        assert ("Business veto" in markup) is (block == "business")
        assert (GENERIC in markup) is (block != "business")
        assert response.context["has_protected_objects"] is (block != "business")
        if details:
            assert response.context["protected_objects"] == []
    assert r.events == [] and r.Document.objects.filter(pk=r.target.pk).exists()


@pytest.mark.parametrize("invalid", ["duplicate", "stale", "unsaved"])
def test_published_provider_invalid_records_fail_before_write(recipes, invalid):
    r = recipes
    view = r.build(EFFECT)
    original = view.cv_get_delete_preview

    def broken(self, boundaries, *, using):
        records = original(self, boundaries, using=using)
        assert len(records) == 1
        if invalid == "duplicate":
            return records * 2
        if invalid == "stale":
            return [replace(records[0], boundary=replace(records[0].boundary, source_pks=(-1,)))]
        return [replace(records[0], deleted=(r.Attachment(title="unsaved"),))]

    view.cv_get_delete_preview = broken
    r.install(view)
    with pytest.raises(ValueError, match=r"boundary|boundar|saved"):
        r.client.get(r.url)
    assert r.events == [] and r.Document.objects.filter(pk=r.target.pk).exists()


def test_published_provider_boundary_attestation_and_public_imports(recipes):
    from crud_views.lib.deletion import DeleteInspection, DeletePreviewBoundary, RelatedObjects, merge_delete_preview
    from crud_views.lib.views.delete import RelatedObjects as LegacyRelatedObjects

    r = recipes
    assert RelatedObjects is LegacyRelatedObjects
    inspection = inspect_deletion(r.target, using="default")
    assert isinstance(inspection, DeleteInspection)
    assert all(isinstance(boundary, DeletePreviewBoundary) for boundary in inspection.boundaries)
    contributions = []
    for heading in (OVERRIDE, EFFECT):
        view = r.build(heading)()
        view.object = r.target
        contributions.extend(view.cv_get_delete_preview(inspection.boundaries, using="default"))
    assert all(isinstance(record, DeletePreviewContribution) for record in contributions)
    merged = merge_delete_preview(inspection, contributions, using="default")
    assert merged.complete and merged.related.summary == {"preview note": 1, "attachment": 1}
    assert r.events == []


@pytest.mark.parametrize("blocked", [False, True])
def test_copied_templates_render_attested_counts_and_authorized_labels(recipes, blocked):
    r = recipes
    preview = r.build(OVERRIDE)()
    view = r.build(EFFECT)
    effect = view.cv_get_delete_preview

    def combined(self, boundaries, *, using):
        return preview.cv_get_delete_preview(boundaries, using=using) + effect(self, boundaries, using=using)

    view.cv_get_delete_preview = combined
    r.actor.is_superuser = True
    r.actor.save()
    if blocked:
        r.Blocker.objects.create(document=r.target, title="<b>Authorized blocker</b>")
    r.install(view)
    response = r.client.get(r.url)
    assert response.status_code == 200 and response.context["delete_preview_incomplete"] is False
    markup = response.content.decode()
    assert NOTICE not in markup and "partial counts" not in markup
    assert "The following related objects will also be deleted:" in markup
    assert "&lt;script&gt;secret note&lt;/script&gt;" in markup and "<script>secret note" not in markup
    if blocked:
        assert "Deletion is blocked by protected relationships:" in markup
        assert "&lt;b&gt;Authorized blocker&lt;/b&gt;" in markup and GENERIC not in markup
    assert bool(html.fromstring(markup).cssselect("form")) is (not blocked)
    assert r.events == []


@pytest.mark.django_db
def test_real_author_and_car_remain_incomplete_without_attestation():
    from tests.test1.app.models import Author, Car

    author = Author.objects.create(first_name="Ordered", last_name="Control")
    car = Car.objects.create(name="Polymorphic control", doors=4)
    assert not inspect_deletion(author, using="default").complete
    car_inspection = inspect_deletion(car, using="default")
    assert not car_inspection.complete
    assert car_inspection.related.summary == {"vehicle": 1}
