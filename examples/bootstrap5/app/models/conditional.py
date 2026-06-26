from django.db import models
from django.utils.translation import gettext_lazy as _


class Registration(models.Model):
    """Kind 1: a conditional field-group governed by `with_company`."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    with_company = models.BooleanField(default=False, verbose_name=_("I represent a company"))
    company_name = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Company name"))
    vat_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("VAT ID"))

    class Meta:
        verbose_name = _("Registration")
        verbose_name_plural = _("Registrations")

    def __str__(self):
        return self.name


class Event(models.Model):
    """Kind 2: a parent whose entire `sessions` formset is governed by `with_sessions`."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    with_sessions = models.BooleanField(default=False, verbose_name=_("This event has sessions"))

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def __str__(self):
        return self.name


class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=200, verbose_name=_("Title"))

    class Meta:
        ordering = ["title"]
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")

    def __str__(self):
        return self.title
