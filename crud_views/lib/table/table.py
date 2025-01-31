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
        wID={"td": {"class": "cv-col-id"}},
        w5={"td": {"class": "cv-col-5"}},
        w10={"td": {"class": "cv-col-10"}},
        w15={"td": {"class": "cv-col-15"}},
        w20={"td": {"class": "cv-col-20"}},
        w25={"td": {"class": "cv-col-25"}},
        w30={"td": {"class": "cv-col-30"}},
        w35={"td": {"class": "cv-col-35"}},
        w40={"td": {"class": "cv-col-40"}},
        w45={"td": {"class": "cv-col-45"}},
        w50={"td": {"class": "cv-col-50"}},
        w55={"td": {"class": "cv-col-55"}},
        w60={"td": {"class": "cv-col-60"}},
        w65={"td": {"class": "cv-col-65"}},
        w70={"td": {"class": "cv-col-70"}},
        w75={"td": {"class": "cv-col-75"}},
        w80={"td": {"class": "cv-col-80"}},
        w85={"td": {"class": "cv-col-85"}},
        w90={"td": {"class": "cv-col-90"}},
        w95={"td": {"class": "cv-col-95"}},
        w100={"td": {"class": "cv-col-100"}},
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
