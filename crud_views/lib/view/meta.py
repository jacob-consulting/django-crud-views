from django.contrib.auth import get_user_model

from crud_views.lib.exceptions import cv_raise

User = get_user_model()


class ViewSetViewMetaClass(type):
    """
    Registers ViewSetViews at ViewSet
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        obj = super().__new__(cls, name, bases, attrs, **kwargs)
        cv = attrs.get("cv")
        if cv:
            # get key to register view
            key = getattr(obj, "cv_key", None)
            cv_raise(key is not None, f"ViewSet {obj} has no attribute cv_key")

            # register view
            cv.register_view_class(key, obj)  # noqa
        return obj
