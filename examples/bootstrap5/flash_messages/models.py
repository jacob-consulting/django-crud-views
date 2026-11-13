from django.db import models
from django.utils.translation import gettext_lazy as _


class Notice(models.Model):
    """Never stored: the ViewSet needs a model, and its "add" permission guards the compose page."""

    text = models.CharField(_("text"), max_length=200)

    class Meta:
        verbose_name = _("notice")
        verbose_name_plural = _("notices")

    def __str__(self):
        return self.text
