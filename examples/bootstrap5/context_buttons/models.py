from django.db import models
from django.utils.translation import gettext_lazy as _


class Ticket(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        NORMAL = "normal", _("Normal")
        HIGH = "high", _("High")

    title = models.CharField(_("title"), max_length=100)
    description = models.TextField(_("description"), blank=True)
    priority = models.CharField(_("priority"), max_length=10, choices=Priority.choices, default=Priority.NORMAL)

    class Meta:
        ordering = ["title"]
        verbose_name = _("ticket")
        verbose_name_plural = _("tickets")

    def __str__(self):
        return self.title
