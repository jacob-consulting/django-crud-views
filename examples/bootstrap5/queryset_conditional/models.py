from django.db import models
from django.utils.translation import gettext_lazy as _


class ServiceCategory(models.Model):
    code = models.CharField(_("code"), max_length=40, unique=True)

    class Meta:
        ordering = ["code"]
        verbose_name = _("service category")
        verbose_name_plural = _("service categories")

    def __str__(self):
        return self.code


class Service(models.Model):
    name = models.CharField(_("name"), max_length=100)
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, verbose_name=_("category"))

    class Meta:
        ordering = ["name"]

    def __str__(self):
        # Native option labels use an already-loaded field, never a category query.
        return self.name


class RequestBatch(models.Model):
    title = models.CharField(_("title"), max_length=100)

    class Meta:
        ordering = ["title"]
        verbose_name = _("request batch")
        verbose_name_plural = _("request batches")

    def __str__(self):
        return self.title


class ServiceRequest(models.Model):
    batch = models.ForeignKey(
        RequestBatch, on_delete=models.CASCADE, related_name="requests", blank=True, null=True, verbose_name=_("batch")
    )
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name=_("service"))
    visit_address = models.CharField(_("visit address"), max_length=200, blank=True)
    meeting_url = models.URLField(_("meeting URL"), blank=True)

    class Meta:
        ordering = ["pk"]
        verbose_name = _("service request")
        verbose_name_plural = _("service requests")

    def __str__(self):
        return _("Service request %(pk)s") % {"pk": self.pk}
