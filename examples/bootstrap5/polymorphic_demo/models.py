from django.db import models
from polymorphic.models import PolymorphicModel


class Vehicle(PolymorphicModel):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Car(Vehicle):
    doors = models.IntegerField(default=4)


class Truck(Vehicle):
    payload_tons = models.IntegerField(default=1)


class Motorcycle(Vehicle):
    engine_cc = models.IntegerField(default=600)
