from django.contrib.auth import get_user_model

from crud_views.lib.exceptions import cv_raise

User = get_user_model()


class CrudViewMetaClass(type):
    """
    Registers CrudViews at ViewSet
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        obj = super().__new__(cls, name, bases, attrs, **kwargs)
        cv_viewset = attrs.get("cv_viewset")
        if cv_viewset:
            # get key to register view
            key = getattr(obj, "cv_key", None)
            cv_raise(key is not None, f"ViewSet {obj} has no attribute cv_key")

            # register view
            cv_viewset.register_view_class(key, obj)  # noqa
        return obj
