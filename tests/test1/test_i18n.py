import gettext as gettext_mod
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


# NOTE: scoped to the three small packages completed in this task (#88 Task 4).
# Task 5 extends SHIPPED to add crud_views and crud_views_workflow once their
# new-locale catalogs are authored.
SHIPPED = {
    "crud_views_polymorphic": ["de", "fr", "es", "pt", "it", "zh_Hans"],
    "crud_views_guardian": ["de", "fr", "es", "pt", "it", "zh_Hans"],
    "crud_views_object_detail": ["de", "fr", "es", "pt", "it", "zh_Hans"],
}


def _iter_po():
    for pkg, locs in SHIPPED.items():
        for loc in locs:
            yield pkg, loc, REPO / "src" / pkg / "locale" / loc / "LC_MESSAGES"


def test_no_empty_or_fuzzy_msgstr():
    polib = pytest.importorskip("polib")  # pip/uv add polib to the dev deps if missing
    for pkg, loc, d in _iter_po():
        po = polib.pofile(str(d / "django.po"))
        # polib .translated() correctly handles plurals (msgstr[0..n]) and multi-line strings:
        untranslated = [e.msgid for e in po if not e.obsolete and not e.translated()]
        assert not untranslated, f"{pkg}/{loc}: untranslated {untranslated}"
        fuzzy = [e.msgid for e in po if "fuzzy" in e.flags]
        assert not fuzzy, f"{pkg}/{loc}: fuzzy entries render as English: {fuzzy}"


def test_mo_files_load():
    for pkg, loc, d in _iter_po():
        mo = d / "django.mo"
        assert mo.exists(), f"missing {mo}"
        with mo.open("rb") as fh:
            gettext_mod.GNUTranslations(fh)  # raises if corrupt


def test_guardian_manage_renders_translated():
    from django.template import Context, Template

    tmpl = Template('{% load i18n %}{% translate "Permission Holders" %}')
    with translation.override("de"):
        assert tmpl.render(Context({})) != "Permission Holders"
