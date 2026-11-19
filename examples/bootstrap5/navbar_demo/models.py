from django.db import models
from django.utils.translation import gettext_lazy as _


class Tenant(models.Model):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("tenant")
        verbose_name_plural = _("tenants")

    def __str__(self):
        return self.name


class Customer(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="customers", verbose_name=_("tenant"))
    name = models.CharField(_("name"), max_length=100)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("customer")
        verbose_name_plural = _("customers")

    def __str__(self):
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders", verbose_name=_("customer"))
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __str__(self):
        return self.name


class Item(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("order"))
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name


class Address(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses", verbose_name=_("customer")
    )
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("address")
        verbose_name_plural = _("addresses")

    def __str__(self):
        return self.name
