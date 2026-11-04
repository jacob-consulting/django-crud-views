from django.db import models
from django.utils.translation import gettext_lazy as _


class Gadget(models.Model):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("gadget")
        verbose_name_plural = _("gadgets")

    def __str__(self):
        return self.name
