from typing import Type

import django_tables2 as tables

from .attrs import ColAttr
from .columns import ActionColumn


class TableWithViewContext(tables.Table):
    """
    Table with view context
    """
    ca: Type[ColAttr] = ColAttr

    def __init__(self, *args, **kwargs):
        if not "view" in kwargs:
            raise ValueError(f"view not set in {self.__class__}")
        view = kwargs.pop("view")
        super().__init__(*args, **kwargs)
        self.view = view


class Table(TableWithViewContext):
    """
    Table with action column
    """
    actions = ActionColumn()

    def __init__(self, *args, **kwargs):
        if "sequence" not in kwargs:
            # as default make sure actions are at the end
            kwargs["sequence"] = ("...", "actions")
        super().__init__(*args, **kwargs)

    @staticmethod
    def order_actions(queryset, is_descending):
        """
        do not order actions
        """
        return queryset, True
