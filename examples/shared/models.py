import uuid

from django.db import models
from ordered_model.models import OrderedModel
from polymorphic.models import PolymorphicModel

from crud_views.lib.view import cv_property
from crud_views.lib.views.properties import r


class Author(OrderedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100, verbose_name="Vorname")
    last_name = models.CharField(max_length=100)
    pseudonym = models.CharField(max_length=100, blank=True, null=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Autor"
        verbose_name_plural = "Autoren"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def xyz(self):
        return "xyz-prop"

    @cv_property(label="ABC-Boolean", renderer=r.boolean)
    def abc(self):
        return True


class Book(OrderedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.author}"


class Foo(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Bar(models.Model):
    foo = models.ForeignKey(Foo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Baz(models.Model):
    bar = models.ForeignKey(Bar, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Poly(PolymorphicModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shared = models.CharField(max_length=100)


class PolyOne(Poly):
    one = models.CharField(max_length=100)


class PolyTwo(Poly):
    two = models.CharField(max_length=100)


class Detail(OrderedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integer = models.IntegerField(verbose_name="An integer field")
    number = models.FloatField(verbose_name="A float field")
    char = models.CharField(max_length=100, verbose_name="Text field")
    text = models.TextField(verbose_name="Multiline Text")
    boolean = models.BooleanField(null=True, default=None, verbose_name="A boolean value")
    boolean_two = models.BooleanField(null=True, default=None, verbose_name="Another boolean value")
    date = models.DateField(verbose_name="A date field")
    date_time = models.DateTimeField(verbose_name="A date field with time")
    author = models.ForeignKey(Author, verbose_name="A foreign key field", on_delete=models.SET_NULL, blank=True,
                               null=True)
    foo = models.ManyToManyField(Foo, verbose_name="Foo selected")
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"

    @cv_property(label="model decorated property", label_tooltip="with custom tooltip", renderer=r.boolean)
    def model_prop(self):
        return True


#########################

class Person(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=128)
    members = models.ManyToManyField(Person, through="Membership", related_name="group")

    def __str__(self):
        return self.name


class Membership(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date_joined = models.DateField()
    invite_reason = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "group"], name="unique_person_group"
            )
        ]
