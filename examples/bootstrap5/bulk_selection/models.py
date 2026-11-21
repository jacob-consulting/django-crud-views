from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        ARCHIVED = "archived", _("Archived")

    title = models.CharField(_("title"), max_length=200)
    status = models.CharField(_("status"), max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_locked = models.BooleanField(_("locked"), default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("owner"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bulk_selection_documents",
    )

    class Meta:
        ordering = ["title"]
        verbose_name = _("document")
        verbose_name_plural = _("documents")

    def __str__(self):
        return self.title
