from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CrudViewsObjectDetailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crud_views_object_detail"
    label = "cvod"
    verbose_name = _("Crud Views Object Detail")

    def ready(self):
        from crud_views.lib.assets import Asset, AssetBundle, get_registered, register_assets

        bundle = AssetBundle(
            key="crud_views_object_detail",
            js=(Asset("crud_views_object_detail/js/tabs.js"),),
        )
        # Django can repopulate apps in tests. Only an identical registration is
        # repeat-safe; a conflicting bundle must retain the registry's error.
        if bundle not in get_registered():
            register_assets(bundle.key, js=bundle.js)
