from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    title = models.CharField(_("title"), max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delete_demo_projects", verbose_name=_("owner")
    )
    is_shared = models.BooleanField(_("shared"), default=False)

    class Meta:
        ordering = ["title"]
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return self.title


class Milestone(models.Model):
    """Deleted together with its project (CASCADE): shown in the delete preview."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones", verbose_name=_("project"))
    title = models.CharField(_("title"), max_length=100)

    class Meta:
        ordering = ["title"]
        verbose_name = _("milestone")
        verbose_name_plural = _("milestones")

    def __str__(self):
        return self.title


class Task(models.Model):
    """Blocks deleting its project (PROTECT) while it exists."""

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="tasks", verbose_name=_("project"))
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delete_demo_tasks", verbose_name=_("owner")
    )
    title = models.CharField(_("title"), max_length=100)

    class Meta:
        ordering = ["title"]
        verbose_name = _("task")
        verbose_name_plural = _("tasks")

    def __str__(self):
        return self.title
