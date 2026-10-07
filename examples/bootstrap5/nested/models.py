from django.db import models
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    name = models.CharField(_("name"), max_length=100)
    city = models.CharField(_("city"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("company")
        verbose_name_plural = _("companies")

    def __str__(self):
        return self.name


class Department(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="departments", verbose_name=_("company")
    )
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("department")
        verbose_name_plural = _("departments")

    def __str__(self):
        return self.name


class Employee(models.Model):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="employees", verbose_name=_("department")
    )
    name = models.CharField(_("name"), max_length=100)
    email = models.EmailField(_("email"))

    class Meta:
        ordering = ["name"]
        verbose_name = _("employee")
        verbose_name_plural = _("employees")

    def __str__(self):
        return self.name


class Office(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="offices", verbose_name=_("company"))
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("office")
        verbose_name_plural = _("offices")

    def __str__(self):
        return self.name
