from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Employee(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="employees")
    name = models.CharField(max_length=100)
    email = models.EmailField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Office(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="offices")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
