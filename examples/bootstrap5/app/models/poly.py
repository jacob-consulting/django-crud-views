import uuid

from django.db import models
from ordered_model.models import OrderedModel
from polymorphic.models import PolymorphicModel


# TODO: from ordered_model.models import OrderedModel

class Parent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    polys = models.ManyToManyField("Poly", through="PolyParent", related_name="parents")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Poly(PolymorphicModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shared = models.CharField(max_length=100, null=True)

    class Meta:
        ordering = ["shared"]


class PolyOne(Poly):
    one = models.CharField(max_length=100)


class PolyTwo(Poly):
    two = models.CharField(max_length=100)


class PolyThree(Poly):
    three = models.CharField(max_length=100)


class PolyTwoChoice(OrderedModel):
    poly = models.ForeignKey(PolyTwo, on_delete=models.CASCADE)
    choice = models.CharField(max_length=100)


class PolyAnswer(PolymorphicModel, models.Model):
    poly = models.ForeignKey(Poly, on_delete=models.CASCADE)


class PolyAnswerText(PolyAnswer):
    answer = models.CharField(max_length=100, null=True)
    text = models.CharField(max_length=100, null=True)


class PolyAnswerNumber(PolyAnswer):
    answer = models.IntegerField(null=True)
    number = models.IntegerField(null=True)


class PolyParent(models.Model):
    poly = models.ForeignKey(Poly, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    date_joined = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["poly", "parent"], name="unique_poly_parent"
            )
        ]
