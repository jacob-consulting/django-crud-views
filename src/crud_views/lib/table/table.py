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
        unless it names it already, else the historical ``("...", "actions")`` (actions last)."""
        declared = tuple(cls._meta.sequence or ())
        if not declared:
            return ("...", "actions")
        if "actions" in declared:
            return declared
        return (*declared, "actions")

    def __init__(self, *args, **kwargs):
        if "sequence" not in kwargs:
            kwargs["sequence"] = self.cv_default_sequence()
        super().__init__(*args, **kwargs)

    @staticmethod
    def order_actions(queryset, is_descending):
        """
        do not order actions
        """
        return queryset, True
