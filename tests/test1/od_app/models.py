from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Info(models.Model):
    text = models.TextField(verbose_name="Info text", help_text="The info body text")
    is_public = models.BooleanField(default=False, verbose_name="Public")
    create_dt = models.DateTimeField(verbose_name="Created at")
    update_dt = models.DateTimeField(verbose_name="Updated at")

    class Meta:
        app_label = "od_app"

    def __str__(self):
        return f"Info({self.pk})"


class Report(models.Model):
    title = models.CharField(max_length=255, verbose_name="Report title")
    access_users = models.ManyToManyField(User, blank=True, related_name="accessible_reports")
    info = models.OneToOneField(Info, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="owned_reports")

    class Meta:
        app_label = "od_app"

    def __str__(self):
        return self.title

    def title_upper(self):
        return self.title.upper()


class ChoiceValue(models.Model):
    """Choice traversal fixtures, independent of the existing report fixtures."""

    process = models.CharField(
        max_length=20,
        choices=[("natural", "Naturally processed"), ("washed", "Gewaschen — 水"), ("", "Blank declared")],
        default="natural",
        null=True,
    )
    rank = models.IntegerField(choices=[(0, "Zero"), (1, "First")], default=0, null=True)
    flag = models.BooleanField(choices=[(False, "Disabled"), (True, "Enabled")], default=False, null=True)
    plain = models.CharField(max_length=20, default="ordinary")
    previous = models.OneToOneField("self", on_delete=models.CASCADE, null=True, related_name="successor")

    class Meta:
        app_label = "od_app"
        ordering = ["pk"]

    def __str__(self):
        return f"ChoiceValue({self.pk})"


class ChoiceContainer(models.Model):
    foreign = models.ForeignKey(
        ChoiceValue, on_delete=models.CASCADE, null=True, related_name="containers", choices=[(1, "Relation label")]
    )
    single = models.OneToOneField(
        ChoiceValue,
        on_delete=models.CASCADE,
        null=True,
        related_name="single_container",
        choices=[(1, "Relation label")],
    )
    values = models.ManyToManyField(ChoiceValue, related_name="collections")

    class Meta:
        app_label = "od_app"
        ordering = ["pk"]
