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
