import pytest
from django.test import override_settings
from django.utils import translation


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
