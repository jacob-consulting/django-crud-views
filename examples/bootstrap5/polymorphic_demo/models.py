from django.db import models
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel


class Vehicle(PolymorphicModel):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("vehicle")
        verbose_name_plural = _("vehicles")

    def __str__(self):
        return self.name


class Car(Vehicle):
    doors = models.IntegerField(_("doors"), default=4)

    class Meta:
        verbose_name = _("car")
        verbose_name_plural = _("cars")


class Truck(Vehicle):
    payload_tons = models.IntegerField(_("payload (tons)"), default=1)

    class Meta:
        verbose_name = _("truck")
        verbose_name_plural = _("trucks")


class Motorcycle(Vehicle):
    engine_cc = models.IntegerField(_("engine (cc)"), default=600)

    class Meta:
        verbose_name = _("motorcycle")
        verbose_name_plural = _("motorcycles")
