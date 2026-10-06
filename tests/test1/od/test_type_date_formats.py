"""date/datetime/timestamp property types follow the active locale's DATE_FORMAT / DATETIME_FORMAT."""

import datetime

import pytest
from django.template.loader import render_to_string
from django.utils import translation

TYPES = "crud_views_object_detail/types/default"
DT = datetime.datetime(2026, 10, 6, 9, 19, tzinfo=datetime.UTC)


@pytest.mark.parametrize(
    "lang, expected",
    [("en", "Oct. 6, 2026"), ("de", "6. Oktober 2026")],
)
def test_date_follows_locale(lang, expected):
    with translation.override(lang):
        assert render_to_string(f"{TYPES}/date.html", {"value": DT.date()}).strip() == expected


@pytest.mark.parametrize("template", ["datetime.html", "timestamp.html"])
@pytest.mark.parametrize(
    "lang, expected",
    [("en", "Oct. 6, 2026, 9:19 a.m."), ("de", "6. Oktober 2026 09:19")],
)
def test_datetime_follows_locale(template, lang, expected):
    with translation.override(lang):
        assert expected in render_to_string(f"{TYPES}/{template}", {"value": DT})
