from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class WorkflowInfo(models.Model):
    transition = models.CharField(max_length=255)
    state_old = models.CharField(max_length=255)
    state_new = models.CharField(max_length=255)
    comment = models.TextField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, blank=True, null=True)
    workflow_object_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    workflow_object_pk = models.CharField(max_length=255)
    workflow_object = GenericForeignKey("workflow_object_content_type", "workflow_object_pk")

    class Meta:
        indexes = [
            # Explicit name matches migration 0002 (AddIndex). Without it, Django auto-generates a
            # hashed name that differs from the shipped migration, causing perpetual RenameIndex drift.
            models.Index(
                fields=["workflow_object_pk", "workflow_object_content_type"],
                name="cvw_workflo_workflo_idx",
            ),
        ]
