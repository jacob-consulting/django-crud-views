from collections import UserDict
from typing import Self


class ColumnAttrs(UserDict):
    """
    Column attributes for a django-tables columns.
    ColumnAttrs can be merged with the | operator.
    """

    @classmethod
    def td_class(cls, value: str) -> Self:
        """
        Helper function to generate column attributes for the table
        """
        return cls({"td": {"class": f"{value}"}})

    @classmethod
    def th_class(cls, value: str) -> Self:
        """
        Helper function to generate column attributes for the table
        """
        return cls({"th": {"class": f"{value}"}})

    def __or__(self, other):
        assert isinstance(other, ColumnAttrs)

        def merge(dict1, dict2):
            for key, value in dict2.items():
                if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                    dict1[key] = merge(dict1[key], value)
                else:
                    if key == "class":
                        assert isinstance(value, str)
                        # check if class is already set
                        classes = [c for c in dict1.get(key, "").split(" ") if len(c)]
                        if value not in classes:
                            value = dict1.get(key, "") + " " + value
                            dict1[key] = value
                    else:
                        dict1[key] = value
            return dict1

        merged: dict = merge(dict(self), dict(other))
        return ColumnAttrs(merged)


class ColAttr:
    # td width
    ID: ColumnAttrs = ColumnAttrs.td_class("cv-col-id")
    w5: ColumnAttrs = ColumnAttrs.td_class("cv-col-5")
    w10: ColumnAttrs = ColumnAttrs.td_class("cv-col-10")
    w15: ColumnAttrs = ColumnAttrs.td_class("cv-col-15")
    w20: ColumnAttrs = ColumnAttrs.td_class("cv-col-20")
    w25: ColumnAttrs = ColumnAttrs.td_class("cv-col-25")
    w30: ColumnAttrs = ColumnAttrs.td_class("cv-col-30")
    w35: ColumnAttrs = ColumnAttrs.td_class("cv-col-35")
    w40: ColumnAttrs = ColumnAttrs.td_class("cv-col-40")
    w45: ColumnAttrs = ColumnAttrs.td_class("cv-col-45")
    w50: ColumnAttrs = ColumnAttrs.td_class("cv-col-50")
    w55: ColumnAttrs = ColumnAttrs.td_class("cv-col-55")
    w60: ColumnAttrs = ColumnAttrs.td_class("cv-col-60")
    w65: ColumnAttrs = ColumnAttrs.td_class("cv-col-65")
    w70: ColumnAttrs = ColumnAttrs.td_class("cv-col-70")
    w75: ColumnAttrs = ColumnAttrs.td_class("cv-col-75")
    w80: ColumnAttrs = ColumnAttrs.td_class("cv-col-80")
    w85: ColumnAttrs = ColumnAttrs.td_class("cv-col-85")
    w90: ColumnAttrs = ColumnAttrs.td_class("cv-col-90")
    w95: ColumnAttrs = ColumnAttrs.td_class("cv-col-95")
    w100: ColumnAttrs = ColumnAttrs.td_class("cv-col-100")

    # extra
    action: ColumnAttrs = ColumnAttrs.th_class("d-flex justify-content-end") | ColumnAttrs.td_class("d-flex justify-content-end")
