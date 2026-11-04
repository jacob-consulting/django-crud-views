from django.db import models
from django.utils.translation import gettext_lazy as _


class Conference(models.Model):
    name = models.CharField(_("name"), max_length=100)
    with_billing = models.BooleanField(_("Invoice a company"), default=False)
    # nullable text fields clear to None when with_billing is off (see docs/reference/conditional.md#clearing-matrix)
    billing_company = models.CharField(_("billing company"), max_length=200, blank=True, null=True)  # NOSONAR S6553
    billing_vat_id = models.CharField(_("billing VAT ID"), max_length=50, blank=True, null=True)  # NOSONAR S6553
    with_sessions = models.BooleanField(_("This conference has sessions"), default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = _("conference")
        verbose_name_plural = _("conferences")

    def __str__(self):
        return self.name


class Session(models.Model):
    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name="sessions", verbose_name=_("conference")
    )
    title = models.CharField(_("title"), max_length=200)

    class Meta:
        ordering = ["title"]
        verbose_name = _("session")
        verbose_name_plural = _("sessions")

    def __str__(self):
        return self.title


class Speaker(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="speakers", verbose_name=_("session"))
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("speaker")
        verbose_name_plural = _("speakers")

    def __str__(self):
        return self.name
