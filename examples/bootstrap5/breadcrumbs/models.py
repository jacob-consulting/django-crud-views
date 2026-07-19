from django.db import models


class Workspace(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Board(models.Model):
    title = models.CharField(max_length=200)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="boards")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
