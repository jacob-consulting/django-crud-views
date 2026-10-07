from django.db import models
from django.utils.translation import gettext_lazy as _


class Recipe(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", _("Easy")
        MEDIUM = "medium", _("Medium")
        HARD = "hard", _("Hard")

    title = models.CharField(_("title"), max_length=100)
    description = models.TextField(_("description"), blank=True)
    difficulty = models.CharField(_("difficulty"), max_length=10, choices=Difficulty.choices, default=Difficulty.EASY)
    servings = models.IntegerField(_("servings"), default=2)
    favorite = models.BooleanField(_("favorite"), default=False)
    created_dt = models.DateTimeField(_("created"), auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = _("recipe")
        verbose_name_plural = _("recipes")

    def __str__(self):
        return self.title
