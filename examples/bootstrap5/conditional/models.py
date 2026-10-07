from django.db import models
from django.utils.translation import gettext_lazy as _


class Registration(models.Model):
    name = models.CharField(_("name"), max_length=100)
    with_company = models.BooleanField(_("I represent a company"), default=False)
    company_name = models.CharField(_("company name"), max_length=200, blank=True, null=True)
    vat_id = models.CharField(_("VAT ID"), max_length=50, blank=True, null=True)
    # governed by a transient UIFieldToggle ("add_note") — the checkbox itself is not stored
    note = models.TextField(_("note"), blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("registration")
        verbose_name_plural = _("registrations")

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(_("name"), max_length=100)
    with_sessions = models.BooleanField(_("This event has sessions"), default=False)
    with_speakers = models.BooleanField(_("Show speaker line-up"), default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = _("event")
        verbose_name_plural = _("events")

    def __str__(self):
        return self.name


class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions", verbose_name=_("event"))
    title = models.CharField(_("title"), max_length=200)

    class Meta:
        ordering = ["title"]
        verbose_name = _("session")
        verbose_name_plural = _("sessions")

    def __str__(self):
        return self.title


class Speaker(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="speakers", verbose_name=_("event"))
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("speaker")
        verbose_name_plural = _("speakers")

    def __str__(self):
        return self.name
