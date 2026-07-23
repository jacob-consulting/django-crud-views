import gettext as gettext_mod
from pathlib import Path

import pytest
from django.test import Client

LOCALE_DIR = Path(__file__).resolve().parent / "locale"
LOCALES = ["de", "fr", "es", "pt", "it", "zh_Hans"]


@pytest.mark.django_db
def test_browser_language_default_de():
    client = Client()
    resp = client.get("/", HTTP_ACCEPT_LANGUAGE="de")
    assert resp.status_code == 200
    assert '<html lang="de"' in resp.content.decode()


@pytest.mark.django_db
def test_set_language_switches_and_persists():
    client = Client()
    resp = client.post("/i18n/setlang/", {"language": "de", "next": "/"}, follow=True)
    assert resp.status_code == 200
    assert '<html lang="de"' in resp.content.decode()


@pytest.mark.django_db
def test_selector_present_in_nav():
    resp = Client().get("/")
    body = resp.content.decode()
    assert 'name="language"' in body  # selector form field rendered


@pytest.mark.django_db
def test_nav_logout_translated_de(client, django_user_model):
    user = django_user_model.objects.create_user("u", password="p")
    client.force_login(user)
    resp = client.get("/", HTTP_ACCEPT_LANGUAGE="de")
    assert "Abmelden" in resp.content.decode()  # "Log Out" -> German


# NOTE: mirrors tests/test1/test_i18n.py's package-catalog guards, applied to the
# example app's own locale/ catalogs (#88 final review, Task 9).
def test_no_empty_or_fuzzy_msgstr():
    polib = pytest.importorskip("polib")  # pip/uv add polib to the dev deps if missing
    for loc in LOCALES:
        po = polib.pofile(str(LOCALE_DIR / loc / "LC_MESSAGES" / "django.po"))
        # polib .translated() correctly handles plurals (msgstr[0..n]) and multi-line strings:
        untranslated = [e.msgid for e in po if not e.obsolete and not e.translated()]
        assert not untranslated, f"{loc}: untranslated {untranslated}"
        fuzzy = [e.msgid for e in po if "fuzzy" in e.flags]
        assert not fuzzy, f"{loc}: fuzzy entries render as English: {fuzzy}"


def test_mo_files_load():
    for loc in LOCALES:
        mo = LOCALE_DIR / loc / "LC_MESSAGES" / "django.mo"
        assert mo.exists(), f"missing {mo}"
        with mo.open("rb") as fh:
            gettext_mod.GNUTranslations(fh)  # raises if corrupt
