"""Execute the published migration fences, including copied templates and real deletion effects."""

import copy
import hashlib
import re
import sys
from collections import OrderedDict
from dataclasses import replace
from textwrap import indent
from types import ModuleType, SimpleNamespace

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.db.models.signals import post_delete
from django.template import Context, engines
from django.test import Client, override_settings
from django.test.utils import isolate_apps
from django.urls import clear_url_caches, resolve
from django.utils.translation import gettext
from django.utils.translation import override as language_override
from lxml import html

from crud_views.lib import check as check_module
from crud_views.lib.deletion import DeletePreviewContribution, RelatedObjects, inspect_deletion
from crud_views.lib.views import DeleteView, DetailViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet
from tests.test1.test_label_mode_docs import DOCS, FENCE, ROOT, _anchors, _section

MIGRATION = DOCS / "migrating-1.0.md"
TEMPLATE_FENCE = re.compile(r"^```django\n(.*?)^```", re.MULTILINE | re.DOTALL)
OVERRIDE = "### Safe deletion preview overrides"
EFFECT = "### Describing custom deletion effects"
TEMPLATES = "### Copied delete templates with incomplete previews"
NOTICE = "This preview is incomplete. Custom deletion behavior may affect additional objects."
SHORTENED = "This preview is shortened. Additional objects are not shown."
GENERIC = "Other objects still reference this one; remove or reassign them before deleting it."


def protected_recipes(source=None, expected_hashes=None):
    """Shared exact UTF-8/LF contract: no trimming, dedenting or newline normalization."""
    if source is None:
        source = MIGRATION.read_bytes().decode("utf-8")
    assert "\r" not in source, "Recipes require LF newlines"
    result = {}
    for name in ("content", "related", "body"):
        marker = f"<!-- protected-delete-recipe: {name} -->"
        assert source.count(marker) == 1, f"Expected exactly one {name} marker"
        matches = re.findall(rf"^{re.escape(marker)}\n```django\n(.*?)^```$", source, re.MULTILINE | re.DOTALL)
        assert len(matches) == 1, f"Expected adjacent django fence for {name}"
        result[name] = matches[0]
    hashes = {name: hashlib.sha256(body.encode("utf-8")).hexdigest() for name, body in result.items()}
    if expected_hashes is not None:
        assert hashes == expected_hashes, "Recipe bytes changed"
    return result, hashes


def test_protected_recipe_marker_contract():
    source = MIGRATION.read_bytes().decode("utf-8")
    bodies, hashes = protected_recipes(source)
    assert len(_recipe(TEMPLATES, TEMPLATE_FENCE, count=3)) == 3
    for name, body in bodies.items():
        assert body.endswith("\n")
        assert hashes[name] != hashlib.sha256(body[:-1].encode("utf-8")).hexdigest()
        marker = f"<!-- protected-delete-recipe: {name} -->"
        for replacement in ("", marker + "\n" + marker, marker + "\n", marker + "\nprose"):
            with pytest.raises(AssertionError):
                protected_recipes(source.replace(marker, replacement))
        with pytest.raises(AssertionError):
            protected_recipes(source.replace(marker + "\n```django", marker + "\n```html"))
        with pytest.raises(AssertionError, match="bytes changed"):
            protected_recipes(source.replace(body, body + "\n", 1), hashes)


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

            blocker_vs = ViewSet(model=Blocker, name="migration_blocker")

            class BlockerDetailView(DetailViewPermissionRequired):
                cv_viewset = blocker_vs
                cv_modal_supported = True

                def get_queryset(self):
                    # Visibility permits the label; this destination denies archived rows.
                    return super().get_queryset().filter(is_archived=False)

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

            bodies, hashes = protected_recipes()
            template_sources = dict(
                zip(
                    ("myapp/delete.content.html", "myapp/delete_related.html", "myapp/delete_protected.html"),
                    (bodies["content"], bodies["related"], bodies["body"]),
                    strict=True,
                )
            )
            stock_config = copy.deepcopy(settings.TEMPLATES)
            config = copy.deepcopy(settings.TEMPLATES)
            config[0]["APP_DIRS"] = False
            config[0]["OPTIONS"]["loaders"] = [
                (
                    "django.template.loaders.locmem.Loader",
                    template_sources,
                ),
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ]
            urls = ModuleType("myapp.recipe_urls")
            monkeypatch.setitem(sys.modules, urls.__name__, urls)

            def install(view, custom=True):
                view.cv_content_template = (
                    "myapp/delete.content.html" if custom else "crud_views/view_delete.content.html"
                )
                urls.urlpatterns = vs.urlpatterns + blocker_vs.urlpatterns
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
                    detail=BlockerDetailView,
                    template_sources=template_sources,
                    hashes=hashes,
                    stock_config=stock_config,
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


def _protected_fixture(r):
    view = r.build(OVERRIDE)
    view.cv_show_related_objects = True
    view.cv_link_related_objects = True
    # The application's visible-label policy deliberately includes a destination-denied row.
    view.cv_filter_related_objects = DeleteView.cv_filter_related_objects
    ct = ContentType.objects.get_for_model(r.Blocker)
    permission, _ = Permission.objects.get_or_create(content_type=ct, codename="view_blocker", name="View blocker")
    r.actor.user_permissions.add(permission)
    linked = r.Blocker.objects.create(document=r.target, title='<b>Visible "link"</b>')
    plain = r.Blocker.objects.create(document=r.target, title="<script>Visible fallback</script>", is_archived=True)
    return view, linked, plain


@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("mode", ["linked", "link-off", "preview-off", "hidden"])
def test_protected_migration_recipe(recipes, modal, mode):
    r = recipes
    view, linked, plain = _protected_fixture(r)
    view.cv_modal = modal
    view.cv_link_related_objects = mode != "link-off"
    view.cv_show_related_objects = mode != "preview-off"
    if mode == "hidden":
        r.actor.user_permissions.clear()
        ct = ContentType.objects.get_for_model(r.Document)
        r.actor.user_permissions.add(Permission.objects.get(content_type=ct, codename="delete_document"))
    r.install(view)
    headers = {"HTTP_X_CV_MODAL": "true"} if modal else {}
    responses = [
        r.client.get(r.url, **headers),
        r.client.get(r.url, **headers),
        r.client.post(r.url, {"confirm": "on"}, **headers),
    ]
    for index, response in enumerate(responses):
        assert response.status_code == (422 if modal and index == 2 else 200)
        markup = response.content.decode()
        doc = html.fromstring(markup)
        assert (doc.tag == "html") is (not modal)
        assert (response.template_name == ["crud_views/modal/content.html"]) is modal
        assert not doc.cssselect("form")
        assert response.context["has_protected_objects"] is True
        assert response.context["delete_preview_incomplete"] is True
        assert markup.count(NOTICE) == 1
        assert ("protected_objects" in response.context) is (mode != "preview-off")
        bodies = doc.cssselect('[data-protected-delete-recipe="body"]')
        if mode in ("hidden", "preview-off"):
            assert not bodies and GENERIC in markup
            assert "Visible" not in markup
        else:
            assert len(bodies) == 1
            body = bodies[0]
            assert body.getparent().get("role") == "alert"
            assert [item.text_content() for item in body.cssselect("li")] == [str(linked), str(plain)]
            assert not body.cssselect("b, script")
            assert not body.cssselect("a")
            assert response.context["protected_objects"] == [{"obj": linked, "url": None}, {"obj": plain, "url": None}]
    assert r.events == [] and r.Document.objects.filter(pk=r.target.pk).exists()
    assert r.Blocker.objects.count() == 2


def test_protected_migration_stock_restoration(recipes):
    r = recipes
    view, linked, _plain = _protected_fixture(r)
    rendered = []
    for custom in (True, False, True):
        r.install(view, custom=custom)
        config = settings.TEMPLATES if custom else r.stock_config
        with override_settings(TEMPLATES=config):
            response = r.client.get(r.url)
            assert response.status_code == 200
            doc = html.fromstring(response.content)
            assert bool(doc.cssselect('[data-protected-delete-recipe="body"]')) is custom
            assert not doc.cssselect("form")
            alert = next(node for node in doc.cssselect('[role="alert"]') if str(linked) in node.text_content())
            rendered.append([(node.text_content(), node.xpath("./a/@href")) for node in alert.cssselect("li")])
            if custom:
                for path, source in r.template_sources.items():
                    assert engines["django"].get_template(path).template.source == source
    assert rendered[0] == rendered[1] == rendered[2]
    assert protected_recipes(expected_hashes=r.hashes)[1] == r.hashes
    assert r.events == [] and r.Blocker.objects.count() == 2


@pytest.mark.parametrize("custom", [False, True])
@pytest.mark.parametrize("language", ["en", "de"])
def test_protected_theme_recipe(recipes, custom, language):
    r = recipes
    bodies, _ = protected_recipes()
    section = _section((DOCS / "reference/theme.md").read_text(), "## Authorized data in overridden templates")
    fences = TEMPLATE_FENCE.findall(section)
    assert len(fences) == 1
    snippet = bodies["related"] if custom else fences[0]
    template = engines["django"].engine.from_string("{% autoescape off %}" + snippet + "{% endautoescape %}")
    obj = '<script>hostile "label"</script>'
    with language_override(language):
        markup = template.render(
            Context(
                {
                    "has_protected_objects": True,
                    "protected_objects": [{"obj": obj, "url": None}, {"obj": "Text fallback", "url": None}],
                    "delete_preview_truncated": True,
                }
            )
        )
        doc = html.fromstring(markup)
        alert = doc.cssselect('[role="alert"]')[0]
        alert = next(node for node in doc.cssselect('[role="alert"]') if obj in node.text_content())
        assert alert.cssselect("li")[0].text_content() == obj
        assert not alert.cssselect("a, script")
        assert markup.count(gettext(SHORTENED)) == 1
        assert alert.cssselect("li")[1].text_content() == "Text fallback"
        assert len(alert.cssselect("ul")) == 1
        heading = alert.cssselect("strong")[0].text_content()
        assert ("Deletion is blocked" in heading) is (language == "en")
        hidden = template.render(Context({"has_protected_objects": True, "protected_objects": []}))
        assert not html.fromstring(hidden).cssselect("ul, a")
        if language == "en":
            assert GENERIC in hidden
    assert r.events == []


@pytest.mark.parametrize("custom", [False, True])
@pytest.mark.parametrize("modal", [False, True])
@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize(
    "scenario,limit,expected_count,truncated,details",
    [
        ("exact", 4, 4, False, True),
        ("overflow", 3, 3, True, True),
        ("blockers-exhaust", 2, 2, True, False),
        ("blocker-only", 2, 2, False, False),
        ("unlimited", None, 4, False, True),
        ("hidden-tail", 4, 4, False, True),
        ("hidden-only", 1, 0, False, False),
        ("redacted-summary", 3, 3, True, True),
        ("solo-root", 1, 1, False, True),
        ("empty-detail", None, 0, False, False),
    ],
)
def test_delete_preview_truncation_recipe(
    recipes, custom, modal, language, scenario, limit, expected_count, truncated, details
):
    r = recipes
    view, first, second = _protected_fixture(r)
    view.cv_modal = modal
    view.cv_delete_preview_limit = limit
    summary = {} if scenario in ("redacted-summary", "solo-root", "hidden-only", "empty-detail") else {"attachment": 7}
    tree = [r.target, [r.attachment]]
    blockers = [first, second]
    if scenario == "hidden-tail":
        tree.append([None, [None]])
    elif scenario == "hidden-only":
        tree, blockers = [None, [None]], []
    elif scenario in ("solo-root", "empty-detail"):
        r.Blocker.objects.all().delete()
        tree, blockers = ([r.target] if scenario == "solo-root" else [None]), []
    elif scenario == "blocker-only":
        tree = [None]
    blocked = scenario not in ("solo-root", "empty-detail")
    view.cv_filter_related_objects = lambda self, user, related: RelatedObjects(tree, summary, blockers)
    # A real registered destination proves selected cascade links retain ordinary navigation.
    view.cv_get_related_object_url = lambda self, obj: f"/migration_blocker/{first.pk}/detail/" if blocked else None
    r.install(view, custom=custom)
    headers = {"HTTP_X_CV_MODAL": "true"} if modal else {}
    with language_override(language):
        for response in (
            r.client.get(r.url, **headers),
            r.client.post(r.url, {"confirm": "on"} if blocked else {}, **headers),
        ):
            assert response.status_code == (422 if modal and response.request["REQUEST_METHOD"] == "POST" else 200)
            context = response.context
            assert context["has_protected_objects"] is blocked
            assert context["delete_preview_incomplete"] is True
            assert context["delete_preview_truncated"] is truncated
            assert context["related_summary"] == summary
            markup = response.content.decode()
            doc = html.fromstring(markup)
            assert bool(doc.cssselect("form")) is (not blocked)
            assert markup.count(gettext(NOTICE)) == 1
            assert markup.count(gettext(SHORTENED)) == int(truncated)
            assert (gettext("Details about the related objects to be deleted:") in markup) is details
            preview = doc.cssselect(".cv-related-objects")
            lists = preview[0].cssselect("ul") if preview else []
            assert sum(len(node.xpath("./li")) for node in lists) == expected_count + len(summary)
            assert all(node.xpath("./li") for node in lists)
            for entry in context["protected_objects"]:
                assert set(entry) == {"obj", "url"} and entry["url"] is None
            links = preview[0].cssselect("li a") if preview else []
            assert len(links) == (max(0, expected_count - len(context["protected_objects"])) if blocked else 0)
            for link in links:
                assert set(link.attrib) == {"href"}
                assert resolve(link.get("href")).func.view_class is r.detail
                destination = r.client.get(link.get("href"))
                assert destination.status_code == 200 and destination.context["object"] == first
            assert not doc.cssselect(".cv-related-objects b, .cv-related-objects script")
    assert r.events == [] and r.Document.objects.filter(pk=r.target.pk).exists()


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


@pytest.mark.parametrize("invalid", ["duplicate", "stale", "unsaved", "ownerless", "wrong-owner"])
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
        if invalid == "ownerless":
            from crud_views.lib.deletion import DeletePreviewBoundary

            boundary = records[0].boundary
            # Old copied five-field constructors default the appended owner to None.
            copied = DeletePreviewBoundary(
                boundary.kind, boundary.model, boundary.field_name, boundary.using, boundary.source_pks
            )
            return [replace(records[0], boundary=copied)]
        if invalid == "wrong-owner":
            return [
                replace(
                    records[0],
                    boundary=replace(records[0].boundary, field_model=r.Document),
                )
            ]
        return [replace(records[0], deleted=(r.Attachment(title="unsaved"),))]

    view.cv_get_delete_preview = broken
    r.install(view)
    with pytest.raises(ValueError, match=r"boundary|boundar|saved"):
        r.client.get(r.url)
    assert r.events == [] and r.Document.objects.filter(pk=r.target.pk).exists()


@pytest.mark.parametrize("details", [False, True])
@pytest.mark.parametrize("blocked", [False, True])
@pytest.mark.parametrize("empty", [False, True])
def test_documented_provider_added_same_name_relation(recipes, details, blocked, empty):
    from crud_views.lib.deletion import merge_delete_preview

    r = recipes
    # Execute both published fences before a new application model is introduced.
    model_provider = r.build(OVERRIDE)()
    view = r.build(EFFECT)
    effect_provider = view.cv_get_delete_preview

    def combined(self, boundaries, *, using):
        return model_provider.cv_get_delete_preview(boundaries, using=using) + effect_provider(
            self, boundaries, using=using
        )

    view.cv_get_delete_preview = combined
    view.cv_show_related_objects = details
    r.install(view)
    initial = r.client.get(r.url)
    assert initial.status_code == 200 and initial.context["delete_preview_incomplete"] is False
    assert NOTICE not in initial.content.decode()

    def added_effect(*args):
        r.events.append(("added-handler", "must never execute during preview"))

    class AdditionalAttachment(models.Model):
        document = models.ForeignKey(r.Document, on_delete=added_effect)

        class Meta:
            app_label = "app"

    with connection.schema_editor() as editor:
        editor.create_model(AdditionalAttachment)
    try:
        if not empty:
            AdditionalAttachment.objects.create(document=r.target)
        if blocked:
            r.Blocker.objects.create(document=r.target, title="Never disclose new-relation blocker")
        inspection = inspect_deletion(r.target, using="default")
        effect = view()
        effect.object = r.target
        records = effect_provider(effect, inspection.boundaries, using="default")
        assert [record.boundary.field_model for record in records] == [r.Attachment], (
            "The actual published fence must attest Attachment.document only, regardless of added same-name fields"
        )
        records = combined(effect, inspection.boundaries, using="default")
        merged = merge_delete_preview(inspection, records, using="default")
        assert not merged.complete
        assert [boundary.field_model for boundary in merged.boundaries] == [AdditionalAttachment]
        assert merged.related.summary == {"preview note": 1, "attachment": 1}
        responses = [r.client.get(r.url), r.client.post(r.url, {})]
        if blocked:
            responses.append(r.client.post(r.url, {"confirm": "on"}))
        for response in responses:
            assert response.status_code == 200
            assert response.context["delete_preview_incomplete"] is True
            assert response.context["has_protected_objects"] is blocked
            markup = response.content.decode()
            assert markup.count(NOTICE) == 1
            assert "Never disclose new-relation blocker" not in markup
            assert "Secret attachment" not in markup and "secret note" not in markup
            assert (GENERIC in markup) is blocked
            assert len(html.fromstring(markup).cssselect('input[name="confirm"]')) == (0 if blocked else 1)
            if details:
                assert response.context["related_summary"] == {"preview note": 1, "attachment": 1}
                assert response.context["protected_objects"] == []
                assert "partial counts" in markup
            else:
                assert "related_summary" not in response.context
        assert r.events == [] and r.Document.objects.filter(pk=r.target.pk).exists()
        assert AdditionalAttachment.objects.count() == (0 if empty else 1)
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(AdditionalAttachment)


def test_published_provider_boundary_attestation_and_public_imports(recipes):
    from crud_views.lib.deletion import DeleteInspection, DeletePreviewBoundary, RelatedObjects, merge_delete_preview
    from crud_views.lib.views.delete import RelatedObjects as LegacyRelatedObjects

    r = recipes
    assert RelatedObjects is LegacyRelatedObjects
    inspection = inspect_deletion(r.target, using="default")
    assert isinstance(inspection, DeleteInspection)
    assert all(isinstance(boundary, DeletePreviewBoundary) for boundary in inspection.boundaries)
    model_boundary = next(boundary for boundary in inspection.boundaries if boundary.kind == "model_delete")
    copied_model_boundary = DeletePreviewBoundary("model_delete", r.Document, None, "default", (r.target.pk,))
    assert copied_model_boundary == model_boundary and copied_model_boundary.field_model is None
    assert merge_delete_preview(
        inspection, [DeletePreviewContribution(copied_model_boundary, complete=True)], using="default"
    ).boundaries == tuple(boundary for boundary in inspection.boundaries if boundary.kind != "model_delete")
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


def test_documented_signature_and_atomic_adapters_execute(recipes):
    from crud_views.lib.deletion import execute_deletion
    from crud_views.lib.views.delete import DeleteView

    r = recipes
    signature, atomic = _recipe("### Delete method signatures and database selection", count=2)
    namespace = {"Document": r.Document, "__name__": "myapp.signature_recipe"}
    source = "class SignatureAdapter(Document):\n" + indent(signature, "    ")
    source += '\n    class Meta:\n        app_label = "app"\n        proxy = True\n'
    exec(compile(source, str(MIGRATION), "exec"), namespace)
    adapter = namespace["SignatureAdapter"].objects.get(pk=r.target.pk)
    count, _ = execute_deletion(adapter, using="default")
    assert count == 2  # Document + Attachment; PreviewNote is deleted inside the custom method
    assert r.events == [("model", "default"), ("handler", "default")]
    assert not r.Document.objects.exists() and not r.PreviewNote.objects.exists()

    # The published atomic override really enters the pinned alias, without re-running selection.
    exec(compile(atomic, str(MIGRATION), "exec"), namespace)
    view = DeleteView()
    view._cv_delete_db_alias = "default"
    view.cv_get_db_alias = lambda: pytest.fail("selector must not be called again")
    assert not connection.in_atomic_block
    with namespace["cv_get_atomic"](view):
        assert connection.in_atomic_block
    assert not connection.in_atomic_block


def test_documented_delete_diagnostics_reject_before_invocation(recipes, monkeypatch):
    from crud_views.lib.deletion import execute_deletion
    from crud_views.lib.views.delete import DeleteView

    r = recipes
    table = _section(MIGRATION.read_text(), "## Step zero: run the checks")

    class Legacy(DeleteView):
        model = r.Document

        def cv_get_related_objects(self):
            pytest.fail("legacy preview must not execute")

    ids = {message.id for check in Legacy.checks() for message in check.messages()}
    assert "viewset.E263" in ids and "`viewset.E263`" in table
    view = Legacy()
    view.object = r.target
    with pytest.raises(ImproperlyConfigured, match=r"cv_get_delete_preview.*cv_filter_related_objects"):
        view._cv_inspect_deletion()

    def incompatible(self):
        pytest.fail("incompatible delete must not execute")

    monkeypatch.setattr(r.Document, "delete", incompatible)
    ids = {message.id for check in Legacy.checks() for message in check.messages()}
    assert "viewset.E264" in ids and "`viewset.E264`" in table
    with pytest.raises(ImproperlyConfigured, match=r"inspectable signature.*using"):
        execute_deletion(r.target, using="default")
    assert r.events == []


def test_documented_guardian_key_recipe_and_exact_diagnostic(recipes, monkeypatch):
    from crud_views_guardian.lib.viewset import STRICT_HELPER_POLICY, GuardianViewSet

    r = recipes
    vs = GuardianViewSet(model=r.Document, name="migration_guardian_keys")
    vs._default_permissions = OrderedDict(
        [("zebra", "app.view_document"), ("réviser", "app.change_document"), ("alpha", "app.delete_document")]
    )
    monkeypatch.setattr(sys.modules["myapp.viewsets"], "cv_document", vs)
    namespace = {"__name__": "myapp.key_recipe"}
    exec(compile(_recipe("### Guardian permission keys")[0], str(MIGRATION), "exec"), namespace)
    r.actor.is_active = False
    r.actor.save()
    message = "Invalid permission key 'view'. Valid keys: 'alpha', 'réviser', 'zebra'."
    assert message in _section(MIGRATION.read_text(), "### Guardian permission keys")
    for key in ("view", "", None, 1, b"alpha", [], {}, "Alpha", "alpha "):
        expected = f"Invalid permission key {key!r}. Valid keys: 'alpha', 'réviser', 'zebra'."
        for call in (
            lambda key=key: namespace["visible_documents"](r.actor, key),
            lambda key=key: vs.assign_perm(key, r.actor, r.target),
            lambda key=key: vs.remove_perm(key, r.actor, r.target),
        ):
            with pytest.raises(ValueError) as error:
                call()
            assert str(error.value) == expected
    assert not namespace["visible_documents"](r.actor, "réviser").exists()
    with pytest.raises(TypeError):
        STRICT_HELPER_POLICY["accept_global_perms"] = True


def test_delete_breaking_entries_have_matching_migration_contracts():
    unreleased = _section((ROOT / "CHANGELOG.md").read_text(), "## Unreleased")
    breaking = _section(unreleased, "### Breaking")
    for heading in ("Protected delete-preview entries", "Delete previews and protected objects"):
        passages = re.findall(rf"^- \*\*{re.escape(heading)}[^\n]*\n(?:[ ]{{2}}[^\n]*\n)*", unreleased, re.MULTILINE)
        assert len(passages) == 1
        passage = passages[0]
        for term in ("`obj`/`url`", "`obj`", "`url`", "`None`", "filtered", "has_protected_objects", "whole-form"):
            assert term in passage
        assert "always" in passage and "eligible detail" not in passage
        assert "now holds only the\n  protected objects" not in passage
    for term in (
        "CRUD_VIEWS_DELETE_PREVIEW_LIMIT",
        "cv_delete_preview_limit",
        "delete_preview_truncated",
        "50",
        "unlimited",
        "crud_views.E109",
        "viewset.E265",
        "solo-root",
        "empty detail",
    ):
        assert term in breaking
    for term in ("protected_objects.html", "generic alert-items", "no legacy", "modals"):
        assert term in breaking
    anchors = _anchors(MIGRATION)
    for anchor, terms in {
        "safe-deletion-preview-overrides": ("cv_get_related_objects", "viewset.E263", "cv_get_delete_preview"),
        "describing-custom-deletion-effects": ("field_model", "Attachment", "ownerless", "source_pks"),
        "delete-method-signatures-and-database-selection": ("viewset.E264", "using", "cv_get_delete_db_alias"),
        "copied-delete-templates-with-incomplete-previews": (
            "delete_preview_incomplete",
            "has_protected_objects",
            "node.obj",
            "node.url",
            "url=None",
            "body_template",
            "delete_preview_truncated",
            "solo root",
            "empty cascade details",
        ),
        "guardian-permission-keys": ("ValueError", "KeyError", "non-string"),
        "guardian-configured-content-type-permissions": ("app.view_vehicle", "MixedContentTypeError", "child_only_car"),
    }.items():
        assert anchor in anchors and f"docs/migrating-1.0.md#{anchor}" in breaking
        heading = (
            "### "
            + {
                "safe-deletion-preview-overrides": "Safe deletion preview overrides",
                "describing-custom-deletion-effects": "Describing custom deletion effects",
                "delete-method-signatures-and-database-selection": "Delete method signatures and database selection",
                "copied-delete-templates-with-incomplete-previews": "Copied delete templates with incomplete previews",
                "guardian-permission-keys": "Guardian permission keys",
                "guardian-configured-content-type-permissions": "Guardian configured content-type permissions",
            }[anchor]
        )
        section = _section(MIGRATION.read_text(), heading)
        for term in terms:
            assert term in section


def test_protected_public_surface_inventory():
    reference = (DOCS / "reference/delete_view.md").read_text()
    surface = _section(reference, "### Protected-preview public surface")
    for term in (
        "protected_objects",
        "has_protected_objects",
        "obj",
        "url",
        "items",
        "cv_show_related_objects=False",
        "crud_views/snippets/delete/protected_objects.html",
        "cv_get_related_object_url(self, obj)",
        "cascade",
        "Full-page",
        "not a new public authorization",
        "always `None`",
        "CRUD_VIEWS_DELETE_PREVIEW_LIMIT",
        "cv_delete_preview_limit",
        "delete_preview_truncated",
        "related_summary_items",
        "Solo root",
    ):
        assert term in surface
    limit = _section(reference, "### Display limit")
    settings_doc = _section((DOCS / "reference/settings.md").read_text(), "## Delete preview")
    migration = _section(MIGRATION.read_text(), "### Delete previews and protected objects")
    for passage in (limit, settings_doc, migration):
        for term in (
            "CRUD_VIEWS_DELETE_PREVIEW_LIMIT",
            "cv_delete_preview_limit",
            "50",
            "None",
            "unlimited",
            "crud_views.E109",
            "viewset.E265",
            "ImproperlyConfigured",
            "booleans",
            "GET/POST",
        ):
            assert term in passage
    linking = _section(reference, "### Linking Related Objects")
    assert "linking-related-objects" in _anchors(DOCS / "reference/delete_view.md")
    exercise = linking.split('!!! example "Try it live"', 1)[1].split("\nOptionally", 1)[0]
    for term in (
        "https://django-crud-views-demo.onrender.com/library/author/",
        "Earthsea publishing contract",
        "plain protected label",
        "Book",
        "full detail page",
        "modal",
    ):
        assert term in exercise
    assert "Follow `Earthsea" not in exercise
    assert "destination eligibility" not in linking and "private adapter" not in linking
    cost = _section(reference, "#### Collection cost and overrides")
    for term in (
        "complete inspection",
        "effective filtering",
        "presentation",
        "selected cascade occurrence",
        "total graph memory",
        "total queries",
        "Python 3.12 / Django 5.2",
    ):
        assert term in cost
    for obsolete in ("Q(N)", "per visible", "adapter query", "actor certification"):
        assert obsolete not in cost
    example = (ROOT / "examples/bootstrap5/library/views.py").read_text()
    author = example.split("class AuthorDeleteView(", 1)[1].split("# ---", 1)[0]
    for term in ("CASCADE", "cv_show_related_objects", "cv_link_related_objects", "plain text", "delete_view.md"):
        assert term in author
