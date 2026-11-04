from django.db import models
from django.utils.translation import gettext_lazy as _


class Contact(models.Model):
    name = models.CharField(_("name"), max_length=100, blank=True)
    email = models.EmailField(_("email"))
    last_reminded_dt = models.DateTimeField(_("last reminded"), null=True, blank=True)

    class Meta:
        ordering = ["name", "email"]
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")

    def __str__(self):
        return self.name or self.email
