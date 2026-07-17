from django.db import models
from ordered_model.models import OrderedModel


class Questionnaire(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Question(OrderedModel):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=200)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.text


class Choice(OrderedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    label = models.CharField(max_length=100)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.label
