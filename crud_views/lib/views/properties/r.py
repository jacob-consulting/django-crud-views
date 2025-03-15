from typing import Any
from uuid import UUID
import datetime as datetime_module
from django.db.models import fields
from django.template.loader import render_to_string
from django.utils.translation import gettext as _


def default(value: Any) -> Any:
    return render_to_string("crud_views/properties/default.html", {"value": value})


def char(value: str | None) -> str:
    return render_to_string("crud_views/properties/char.html", {"value": value})


def text(value: str | None) -> str:
    return render_to_string("crud_views/properties/char.html", {"value": value})


def boolean(value: bool | None) -> str:
    is_true = value is True
    is_false = value is False
    is_null = value is None
    context = {
        "value": value,
        "is_true": is_true,
        "is_false": is_false,
        "is_null": is_null,
        "is_null_title": _("no value provided")
    }
    return render_to_string("crud_views/properties/boolean.html", context)


def foreign_key(value: Any) -> str:
    return render_to_string("crud_views/properties/foreign_key.html", {"value": value})


def many_to_many(value: Any) -> str:
    return render_to_string("crud_views/properties/many_to_many.html", {"value": value})


def uuid(value: UUID | None) -> str:
    context = {"value": value}
    if value is not None:
        first, *between, last = str(value).split("-")
        context.update({
            "first": first,
            "last": last,
        })
    return render_to_string("crud_views/properties/uuid.html", context)


def date(value: datetime_module.date | None) -> str:
    context = {"value": value}
    return render_to_string("crud_views/properties/date.html", context=context)


def datetime(value: datetime_module.datetime | None) -> str:
    context = {"value": value}
    return render_to_string("crud_views/properties/datetime.html", context=context)


field2renderer = {
    fields.UUIDField: uuid,
    fields.CharField: char,
    fields.TextField: text,
    fields.BooleanField: boolean,
    fields.NullBooleanField: boolean,
    fields.related.ForeignKey: foreign_key,
    fields.related.ManyToManyField: many_to_many,
    fields.DateField: date,
    fields.DateTimeField: datetime,
}
