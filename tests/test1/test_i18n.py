from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import translation

REPO = Path(__file__).resolve().parents[2]


def _po(pkg: str, loc: str = "de") -> str:
    return (REPO / "src" / pkg / "locale" / loc / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")


def test_guardian_strings_extracted():
    po = _po("crud_views_guardian")
    for msgid in ["Guardian Configuration", "Permission Holders", "No permission holders found."]:
        assert f'msgid "{msgid}"' in po


def test_polymorphic_type_label_extracted():
    assert 'msgid "Type"' in _po("crud_views_polymorphic")


def test_object_detail_verbose_name_extracted():
    assert 'msgid "Crud Views Object Detail"' in _po("crud_views_object_detail")


@pytest.mark.django_db
@override_settings(
    LANGUAGE_CODE="de",
    LANGUAGES=[("en", "English"), ("de", "German")],
)
def test_german_translations_load():
    """Verify German .mo files are compiled and load correctly."""
    translation.activate("de")
    try:
        from django.utils.translation import gettext as _

        assert _("Reset Filter") == "Filter zurücksetzen"
        assert _("Apply Filter") == "Filter anwenden"
        assert _("Save") == "Sichern"  # Django admin's de translation takes precedence
        assert _("Confirm deletion") == "Löschen bestätigen"
    finally:
        translation.deactivate()
