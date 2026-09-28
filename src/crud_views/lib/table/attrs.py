import copy
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
        # deep copy: the result must not share nested dicts with the operands,
        # which are often the class-level ColAttr presets
        return ColumnAttrs(copy.deepcopy(_merge_attrs(dict(self), dict(other))))


def _merge_class(existing: str, value: str) -> str:
    assert isinstance(value, str)
    classes = existing.split()
    if value not in classes:
        classes.append(value)
    return " ".join(classes)


def _merge_attrs(base: dict, extra: dict) -> dict:
    """Merge ``extra`` into a new dict based on ``base``; neither argument is modified."""
    merged = dict(base)
    for key, value in extra.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _merge_attrs(current, value)
        elif key == "class":
            merged[key] = _merge_class(current or "", value)
        else:
            merged[key] = value
    return merged


class ColAttrMeta(type):
    def __getattribute__(cls, name):
        # print(f"accessing {name}")
        return super().__getattribute__(name)


class ColAttr(metaclass=ColAttrMeta):
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
    action: ColumnAttrs = ColumnAttrs.th_class("cv-col-action") | ColumnAttrs.td_class("cv-col-action")
