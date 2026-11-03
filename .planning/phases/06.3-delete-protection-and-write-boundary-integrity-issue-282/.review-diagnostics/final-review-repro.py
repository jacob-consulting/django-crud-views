"""Focused review probes; all tables live in configured in-memory databases.

Run from the repository root with PYTHONPATH=src:. and a supported interpreter.
Output records observations, not passing acceptance assertions.
"""

import json
from contextlib import contextmanager

from tests.test1.conftest import pytest_configure

pytest_configure()

import django  # noqa: E402
from django.db import connections, models  # noqa: E402
from django.test.utils import isolate_apps  # noqa: E402

from crud_views.lib.deletion import (  # noqa: E402
    DeletePreviewContribution,
    execute_deletion,
    inspect_deletion,
    merge_delete_preview,
)


@contextmanager
def tables(classes, aliases=("default",)):
    for alias in aliases:
        with connections[alias].schema_editor() as editor:
            for model in classes:
                editor.create_model(model)
    try:
        yield
    finally:
        for alias in aliases:
            with connections[alias].schema_editor() as editor:
                for model in reversed(classes):
                    editor.delete_model(model)


def alias_probe():
    with isolate_apps("tests.test1.app"):
        class Root(models.Model):
            code = models.CharField(max_length=10, unique=True)

            class Meta:
                app_label = "app"

        class Child(models.Model):
            target = models.ForeignKey(Root, to_field="code", on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        with tables((Root, Child), ("default", "shard")):
            read = Root.objects.using("default").create(pk=1, code="original")
            Root.objects.using("shard").create(pk=1, code="selected")
            unrelated = Root.objects.using("shard").create(pk=2, code="original")
            child = Child.objects.using("shard").create(target=unrelated)
            preview = inspect_deletion(read, using="shard")
            count, _ = execute_deletion(read, using="shard")
            return {
                "preview_complete": preview.complete,
                "preview_summary": preview.related.summary,
                "deleted_count": count,
                "unrelated_parent_survives": Root.objects.using("shard").filter(pk=2).exists(),
                "unrelated_child_survives": Child.objects.using("shard").filter(pk=child.pk).exists(),
            }


def boundary_probe():
    with isolate_apps("tests.test1.app"):
        class Root(models.Model):
            class Meta:
                app_label = "app"

        class First(models.Model):
            target = models.ForeignKey(Root, on_delete=models.SET_DEFAULT, default=None, null=True)

            class Meta:
                app_label = "app"

        class Second(models.Model):
            target = models.ForeignKey(Root, on_delete=models.SET(lambda: None), null=True)

            class Meta:
                app_label = "app"

        with tables((Root, First, Second)):
            root = Root.objects.create()
            preview = inspect_deletion(root, using="default")
            merged = merge_delete_preview(
                preview, [DeletePreviewContribution(preview.boundaries[0], complete=True)], using="default"
            )
            return {
                "custom_relations": len(Root._meta.related_objects),
                "boundaries": len(preview.boundaries),
                "complete_after_one_attestation": merged.complete,
            }


def null_probe():
    with isolate_apps("tests.test1.app"):
        class Root(models.Model):
            code = models.CharField(max_length=10, unique=True, null=True)

            class Meta:
                app_label = "app"

        class Ref(models.Model):
            target = models.ForeignKey(Root, to_field="code", on_delete=models.PROTECT, null=True)

            class Meta:
                app_label = "app"

        with tables((Root, Ref)):
            root = Root.objects.create(code=None)
            ref = Ref.objects.create(target=None)
            preview = inspect_deletion(root, using="default")
            count, _ = execute_deletion(root, using="default")
            return {
                "preview_protected_count": len(preview.related.protected),
                "actual_deleted_count": count,
                "unlinked_ref_survives": Ref.objects.filter(pk=ref.pk).exists(),
            }


print(json.dumps({"django": django.get_version(), "alias": alias_probe(), "boundary": boundary_probe(), "null": null_probe()}, sort_keys=True))
