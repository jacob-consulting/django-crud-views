from __future__ import annotations

from typing import Any, List

from django.http import Http404
from pydantic import BaseModel
from typing_extensions import Self

from crud_views.lib.viewset.path_regs import PrimaryKeys

# NOTE: this module must not import from crud_views.lib.viewset (the package
# __init__) — viewset/__init__.py imports this module, importing back would be
# circular. path_regs is a leaf module and safe.


class ResourceMeta:
    """
    Defaults for Resource.Meta. Mirrors the Django model Meta idiom; values
    should be lowercase (ViewSet.get_meta() applies .capitalize()).
    """

    verbose_name: str = "item"
    verbose_name_plural: str = "items"
    app_label: str = "resources"  # session-data namespace (crud_views/lib/session.py)
    pk_field: str = "pk"  # name of the attribute (field or property) identifying a row
    pk_type: str = PrimaryKeys.STR  # URL pattern regex, see path_regs.PrimaryKeys
    ordering: str | None = None  # informational; sort in cv_get_items


_META_ATTRS = ("verbose_name", "verbose_name_plural", "app_label", "pk_field", "pk_type", "ordering")


class ResourceOptions:
    """
    Duck-types the subset of Django's ``model._meta`` (Options) API that
    crud_views reads (verbose_name, verbose_name_plural, app_label), plus the
    Resource-specific attributes (pk_field, pk_type, ordering). Add attributes
    only when a coupling point actually reads them.
    """

    def __init__(self, meta: type):
        for name in _META_ATTRS:
            setattr(self, name, getattr(meta, name, getattr(ResourceMeta, name)))


class _PkShim(property):
    """Marker type for the per-subclass pk property, so descendants can detect it."""


class _PkShimNeutralized:
    """
    Non-descriptor placeholder assigned onto a subclass that declares a real
    ``pk`` field while inheriting a _PkShim from an ancestor: because it is
    not a data descriptor, the field value in the instance __dict__ wins again.
    """

    __slots__ = ()


class Resource(BaseModel):
    """
    Base class for non-ORM table-shaped data rendered through a ViewSet.

    Rows are Pydantic instances, so Django templates and django-tables2 use
    plain attribute access and raw input is validated at conversion time.
    Subclasses define fields, an inner ``Meta`` class and ``cv_get_items``.
    """

    class Meta(ResourceMeta):
        pass

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        cls._meta = ResourceOptions(cls.Meta)

        # Expose object.pk like Django models. A property on the base class
        # would be a data descriptor shadowing a real "pk" field, so it is
        # attached per subclass and only when no "pk" field exists.
        if "pk" in cls.__pydantic_fields__:
            # a real pk field: unshadow any inherited per-subclass shim so the
            # field value in the instance __dict__ wins again
            if any(isinstance(base.__dict__.get("pk"), _PkShim) for base in cls.__mro__[1:]):
                cls.pk = _PkShimNeutralized()
        else:
            pk_field = cls._meta.pk_field
            if pk_field != "pk":
                cls.pk = _PkShim(lambda self, _name=pk_field: getattr(self, _name))
            else:
                # pk_field == "pk" needs a genuine pk attribute; an inherited
                # _PkShim reads the ANCESTOR's pk_field and does not count
                has_real_pk_attr = any(
                    "pk" in base.__dict__ and not isinstance(base.__dict__["pk"], _PkShim) for base in cls.__mro__
                )
                if not has_real_pk_attr:
                    raise TypeError(f"{cls.__name__}: Meta.pk_field is 'pk' but no 'pk' field or attribute is defined")

    @classmethod
    def cv_get_items(cls, request, **url_kwargs) -> List[Self]:
        """
        Return all rows. Implemented by the developer (read S3, walk a config
        tree, call an API, ...). ``url_kwargs`` are the resolved URL kwargs of
        the requesting view — for nested ViewSets they contain the parent
        pk(s), e.g. ``publisher_pk``. Must return a plain list (Django's
        Paginator needs len() and slicing).
        """
        raise NotImplementedError(f"{cls.__name__}.cv_get_items() is not implemented")

    @classmethod
    def cv_get_item(cls, request, pk, **url_kwargs) -> Self:
        """
        Return a single row by pk. Default: linear scan over cv_get_items()
        comparing str(row.pk) == str(pk); raises Http404 when not found.
        Deliberately simple — fine for read-all-at-once data. Override when a
        direct lookup is cheaper (e.g. head_object on S3).
        """
        for item in cls.cv_get_items(request, **url_kwargs):
            if str(item.pk) == str(pk):
                return item
        raise Http404(f"{cls._meta.verbose_name} with pk={pk!r} not found")


# __pydantic_init_subclass__ only fires for subclasses; the abstract base needs
# its own _meta so generic code can read Resource._meta without special-casing.
Resource._meta = ResourceOptions(Resource.Meta)
