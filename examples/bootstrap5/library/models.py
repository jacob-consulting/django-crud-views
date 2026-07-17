import uuid

from django.db import models
from ordered_model.models import OrderedModel


class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pseudonym = models.CharField(max_length=100, blank=True, null=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified")

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(OrderedModel):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title
