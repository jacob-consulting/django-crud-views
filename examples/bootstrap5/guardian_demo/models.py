from django.conf import settings
from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
