from django.db import models
from django.utils.translation import gettext_lazy as _


class Workspace(models.Model):
    name = models.CharField(_("name"), max_length=200)

    class Meta:
        ordering = ["name"]
        verbose_name = _("workspace")
        verbose_name_plural = _("workspaces")

    def __str__(self):
        return self.name


class Board(models.Model):
    title = models.CharField(_("title"), max_length=200)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="boards", verbose_name=_("workspace")
    )

    class Meta:
        ordering = ["title"]
        verbose_name = _("board")
        verbose_name_plural = _("boards")

    def __str__(self):
        return self.title
