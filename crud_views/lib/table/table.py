import django_tables2 as tables
from box import Box

from .columns import ActionColumn


class Table(tables.Table):
    """
    UI CRUD table with actions column
    """
    actions = ActionColumn()

    # additional_actions = None

    col_attr = Box(dict(
        wID={"td": {"class": "vs-col-id"}},
        w5={"td": {"class": "vs-col-5"}},
        w10={"td": {"class": "vs-col-10"}},
        w15={"td": {"class": "vs-col-15"}},
        w20={"td": {"class": "vs-col-20"}},
        w25={"td": {"class": "vs-col-25"}},
        w30={"td": {"class": "vs-col-30"}},
        w35={"td": {"class": "vs-col-35"}},
        w40={"td": {"class": "vs-col-40"}},
        w45={"td": {"class": "vs-col-45"}},
        w50={"td": {"class": "vs-col-50"}},
        w55={"td": {"class": "vs-col-55"}},
        w60={"td": {"class": "vs-col-60"}},
        w65={"td": {"class": "vs-col-65"}},
        w70={"td": {"class": "vs-col-70"}},
        w75={"td": {"class": "vs-col-75"}},
        w80={"td": {"class": "vs-col-80"}},
        w85={"td": {"class": "vs-col-85"}},
        w90={"td": {"class": "vs-col-90"}},
        w95={"td": {"class": "vs-col-95"}},
        w100={"td": {"class": "vs-col-100"}},
    ))


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
