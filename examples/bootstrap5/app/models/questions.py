from django.db import models
from ordered_model.models import OrderedModel

from app.models import validate_questionmark, validate_alpha


class Question(models.Model):
    question = models.CharField(max_length=100, validators=[validate_questionmark])

    def __str__(self):
        return f"{self.question}"


class QuestionTag(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    tag = models.CharField(max_length=100)


class QuestionChoice(OrderedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.CharField(max_length=100, validators=[validate_alpha])
    help_text = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.choice}"


class QuestionChoiceTag(OrderedModel):
    choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE)
    tag = models.CharField(max_length=100)


class QuestionChoiceTagAnnotation(OrderedModel):
    tag = models.ForeignKey(QuestionChoiceTag, on_delete=models.CASCADE)
    annotation = models.CharField(max_length=100)
