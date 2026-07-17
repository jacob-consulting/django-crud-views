from django.db import models


class Recipe(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.EASY)
    servings = models.IntegerField(default=2)
    favorite = models.BooleanField(default=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
