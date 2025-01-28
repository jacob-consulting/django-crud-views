from django.contrib.auth import get_user_model

from crud_views.lib.exceptions import vs_raise

User = get_user_model()


class ViewSetViewMetaClass(type):
    """
    Registers ViewSetViews at ViewSet
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        obj = super().__new__(cls, name, bases, attrs, **kwargs)
        vs = attrs.get("vs")
        if vs:
            # get key to register view
            key = getattr(obj, "vs_key", None)
            vs_raise(key is not None, f"ViewSet {obj} has no attribute vs_key")

            # register view
            vs.register_view_class(key, obj)  # noqa
        return obj
