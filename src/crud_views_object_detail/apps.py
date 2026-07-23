from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CrudViewsObjectDetailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_object_detail"
    label = "cvod"
    verbose_name = _("Crud Views Object Detail")
