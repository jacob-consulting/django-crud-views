from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Document(models.Model):
    title = models.CharField(_("title"), max_length=100)
    body = models.TextField(_("body"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents", verbose_name=_("owner")
    )
    created_dt = models.DateTimeField(_("created"), auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = _("document")
        verbose_name_plural = _("documents")

    def __str__(self):
        return self.title
