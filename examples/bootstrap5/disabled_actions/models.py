from django.db import models
from django.utils.translation import gettext_lazy as _


class Ticket(models.Model):
    title = models.CharField(_("title"), max_length=100)
    locked = models.BooleanField(_("locked"), default=False)

    class Meta:
        ordering = ["title"]
        verbose_name = _("ticket")
        verbose_name_plural = _("tickets")

    def __str__(self):
        return self.title
