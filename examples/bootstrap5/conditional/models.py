from django.db import models


class Registration(models.Model):
    name = models.CharField(max_length=100)
    with_company = models.BooleanField(default=False, verbose_name="I represent a company")
    company_name = models.CharField(max_length=200, blank=True, null=True)
    vat_id = models.CharField(max_length=50, blank=True, null=True)
    # governed by a transient UIFieldToggle ("add_note") — the checkbox itself is not stored
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=100)
    with_sessions = models.BooleanField(default=False, verbose_name="This event has sessions")
    with_speakers = models.BooleanField(default=False, verbose_name="Show speaker line-up")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Speaker(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="speakers")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
