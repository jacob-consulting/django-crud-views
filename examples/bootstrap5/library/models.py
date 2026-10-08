import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel


class Author(models.Model):
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(_("first name"), max_length=100)
    last_name = models.CharField(_("last name"), max_length=100)
    pseudonym = models.CharField(_("pseudonym"), max_length=100, blank=True)
    created_dt = models.DateTimeField(_("created"), auto_now_add=True)
    modified_dt = models.DateTimeField(_("modified"), auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = _("author")
        verbose_name_plural = _("authors")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(OrderedModel):
    title = models.CharField(_("title"), max_length=100)
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name=_("author"))

    class Meta(OrderedModel.Meta):
        verbose_name = _("book")
        verbose_name_plural = _("books")

    def __str__(self):
        return self.title
