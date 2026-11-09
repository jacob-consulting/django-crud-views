import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from .attrs import ColAttr
from .columns import ActionColumn


class TableWithViewContext(tables.Table):
    """
    Table with view context
    """

    ca: type[ColAttr] = ColAttr

    def __init__(self, *args, **kwargs):
        if "view" not in kwargs:
            raise ValueError(f"view not set in {self.__class__}")
        view = kwargs.pop("view")
        super().__init__(*args, **kwargs)
        self.view = view


class Table(TableWithViewContext):
    """
    Table with action column
    """

    actions = ActionColumn(verbose_name=_("Actions"))

    @classmethod
    def cv_default_sequence(cls) -> tuple[str, ...]:
        """The ``sequence`` used when the caller passes none: a declared ``Meta.sequence`` with ``actions`` appended
        unless it names it already, else the historical ``("...", "actions")`` (actions last). A declared sequence
        without ``"..."`` gets one inserted before ``actions`` so unlisted columns stay ahead of it."""
        declared = tuple(cls._meta.sequence or ())
        if not declared:
            return ("...", "actions")
        if "actions" in declared:
            return declared
        if "..." not in declared:
            declared = (*declared, "...")  # django-tables2 would otherwise append its own "..." after actions
        return (*declared, "actions")

    @staticmethod
    def cv_exclude_actions(view) -> bool:
        """True when the owning view declares ``cv_list_actions = None`` (no row actions). An empty list keeps the
        column, as does a view without the attribute. Static: the current user's access is not consulted."""
        return hasattr(view, "cv_list_actions") and view.cv_list_actions is None

    def __init__(self, *args, **kwargs):
        if "sequence" not in kwargs:
            kwargs["sequence"] = self.cv_default_sequence()
        if self.cv_exclude_actions(kwargs.get("view")):
            caller = kwargs.get("exclude") or ()  # None (django-tables2's default) or any falsy value adds nothing
            if isinstance(caller, str):
                caller = (caller,)  # a bare column name, never iterated character-wise
            # django-tables2 uses `exclude or Meta.exclude`, so merge both sources instead of replacing them
            merged = (*self._meta.exclude, *caller, "actions")
            kwargs["exclude"] = tuple(dict.fromkeys(merged))
        super().__init__(*args, **kwargs)

    @staticmethod
    def order_actions(queryset, is_descending):
        """
        do not order actions
        """
        return queryset, True
