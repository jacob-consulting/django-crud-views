from django.db import models
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel


class Questionnaire(models.Model):
    title = models.CharField(_("title"), max_length=100)

    class Meta:
        ordering = ["title"]
        verbose_name = _("questionnaire")
        verbose_name_plural = _("questionnaires")

    def __str__(self):
        return self.title


class Question(OrderedModel):
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name="questions", verbose_name=_("questionnaire")
    )
    text = models.CharField(_("text"), max_length=200)

    class Meta(OrderedModel.Meta):
        verbose_name = _("question")
        verbose_name_plural = _("questions")

    def __str__(self):
        return self.text


class Choice(OrderedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices", verbose_name=_("question"))
    label = models.CharField(_("label"), max_length=100)

    class Meta(OrderedModel.Meta):
        verbose_name = _("choice")
        verbose_name_plural = _("choices")

    def __str__(self):
        return self.label


class Checklist(models.Model):
    title = models.CharField(_("title"), max_length=100)

    class Meta:
        ordering = ["pk"]
        verbose_name = _("checklist")
        verbose_name_plural = _("checklists")

    def __str__(self):
        return self.title


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(
        Checklist, on_delete=models.CASCADE, related_name="items", verbose_name=_("checklist")
    )
    label = models.CharField(_("Item"), max_length=200, help_text=_("Describe the task to complete."))
    done = models.BooleanField(_("Done"), default=False, help_text=_("Tick when this item is complete."))

    class Meta:
        ordering = ["pk"]
        verbose_name = _("checklist item")
        verbose_name_plural = _("checklist items")

    def __str__(self):
        return self.label
