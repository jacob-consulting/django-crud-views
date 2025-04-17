from typing import Type

import django_tables2 as tables

from .attrs import ColumnAttrs, ColAttr
from .columns import ActionColumn


class Table(tables.Table):
    """
    UI CRUD table with actions column
    """
    actions = ActionColumn()
    ca: Type[ColAttr] = ColAttr

    def __init__(self, *args, **kwargs):
        # kwargs["template_name"] = "django_tables2/bootstrap5.html"
        if "sequence" not in kwargs:
            kwargs["sequence"] = ("...", "actions")
        if not "view" in kwargs:
            raise ValueError(f"view not set in {self.__class__}")
        view = kwargs.pop("view")
        super().__init__(*args, **kwargs)
        self.view = view

    @staticmethod
    def order_actions(queryset, is_descending):
        """
        do not order actions
        """
        return queryset, True
