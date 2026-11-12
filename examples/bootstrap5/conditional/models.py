from django.db import models
from django.utils.translation import gettext_lazy as _


class Registration(models.Model):
    name = models.CharField(_("name"), max_length=100)
    with_company = models.BooleanField(_("I represent a company"), default=False)
    # These nullable text fields clear to None; other pairs use field-aware defaults or explicit empty_values.
    # Unsupported automatic pairs fail crud_views.E312. See docs/reference/conditional.md#clearing-matrix.
    company_name = models.CharField(_("company name"), max_length=200, blank=True, null=True)  # NOSONAR S6553
    vat_id = models.CharField(_("VAT ID"), max_length=50, blank=True, null=True)  # NOSONAR S6553
    # governed by a transient UIFieldToggle ("add_note") — the checkbox itself is not stored
    note = models.TextField(_("note"), blank=True, null=True)  # NOSONAR S6553

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


class Customer(models.Model):
    name = models.CharField(_("name"), max_length=100)
    kind = models.CharField(
        _("customer kind"),
        max_length=20,
        choices=[("consumer", _("Consumer")), ("wholesale", _("Wholesale")), ("distributor", _("Distributor"))],
        default="consumer",
    )
    consumer_note = models.TextField(_("consumer note"), null=True, blank=True)  # NOSONAR S6553
    company = models.CharField(_("company"), max_length=200, null=True, blank=True)  # NOSONAR S6553
    price_tier = models.CharField(  # NOSONAR S6553 — nullable choices demonstrate automatic None clearing
        _("price tier"), max_length=1, choices=[("A", _("A")), ("B", _("B"))], null=True, blank=True, default="A"
    )
    payment_terms = models.CharField(
        _("payment terms"),
        max_length=10,
        choices=[("unset", _("Unset — no business terms")), ("net30", _("Net 30")), ("net60", _("Net 60"))],
        default="unset",
    )
    wholesale_terms = models.IntegerField(
        _("wholesale terms"),
        choices=[(0, _("Prepaid")), (30, _("30 days")), (60, _("60 days"))],
        null=True,
        blank=True,
        default=30,
    )
    distribution_region = models.CharField(_("distribution region"), max_length=100, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("customer")
        verbose_name_plural = _("customers")

    def __str__(self):
        return self.name
