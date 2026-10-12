from django.db import models
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel


class Chore(OrderedModel):
    title = models.CharField(_("title"), max_length=100)
    done = models.BooleanField(_("done"), default=False)
    archived = models.BooleanField(_("archived"), default=False)

    class Meta(OrderedModel.Meta):
        verbose_name = _("chore")
        verbose_name_plural = _("chores")

    def __str__(self):
        return self.title


class Step(models.Model):
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, verbose_name=_("chore"))
    text = models.CharField(_("text"), max_length=200)

    class Meta:
        verbose_name = _("step")
        verbose_name_plural = _("steps")

    def __str__(self):
        return self.text
