from django.contrib.auth import get_user_model

from crud_views.lib.exceptions import cv_raise

try:
    from django_filters.views import FilterMixin

    _base_metaclass = type(FilterMixin)
except ImportError:
    _base_metaclass = type

User = get_user_model()


class CrudViewMetaClass(_base_metaclass):
    """
    Registers CrudViews at ViewSet
    """

    renamed_attributes = ()

    def __new__(cls, name, bases, attrs, **kwargs):
        obj = super().__new__(cls, name, bases, attrs, **kwargs)
        cv_viewset = attrs.get("cv_viewset")
        if cv_viewset:
            # get key to register view
            key = getattr(obj, "cv_key", None)
            cv_raise(key is not None, f"ViewSet {obj} has no attribute cv_key")

            # register view
            cv_viewset.register_view_class(key, obj)  # noqa

            # auto-set model from viewset if not explicitly provided
            if "model" not in attrs:
                obj.model = cv_viewset.model
        return obj
