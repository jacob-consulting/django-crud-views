import gettext as gettext_mod
from pathlib import Path

import pytest
from django.test import Client

LOCALE_DIR = Path(__file__).resolve().parent / "locale"
LOCALES = ["de"]


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


# Demo apps translate everything shown in their UI (models -> table headers, form and filter
# labels; choices; buttons; messages). About/Look-at panels and seed data stay English.
EXAMPLE_APPS = [
    "library",
    "nested",
    "formsets",
    "workflow",
    "polymorphic_demo",
    "guardian_demo",
    "resources",
    "showcase",
    "object_detail",
    "breadcrumbs",
    "conditional",
]


def _example_models():
    from django.apps import apps

    for label in EXAMPLE_APPS:
        yield from apps.get_app_config(label).get_models()


# fields contributed by third-party abstract bases, never rendered by the demos
THIRD_PARTY_FIELDS = {"polymorphic_ctype"}


def test_example_models_mark_names_for_translation():
    from django.utils.functional import Promise

    missing = []
    for model in _example_models():
        opts = model._meta
        for attr in ("verbose_name", "verbose_name_plural"):
            if not isinstance(opts.original_attrs.get(attr), Promise):
                missing.append(f"{opts.label}.Meta.{attr}")
        for field in opts.get_fields(include_parents=False):
            if field.auto_created or not field.concrete or field.name in THIRD_PARTY_FIELDS:
                continue
            if not isinstance(field._verbose_name, Promise):
                missing.append(f"{opts.label}.{field.name}")
    assert not missing, f"not marked with gettext_lazy: {missing}"


def test_example_choices_mark_labels_for_translation():
    from django.utils.functional import Promise

    missing = []
    for model in _example_models():
        for field in model._meta.get_fields(include_parents=False):
            for value, label in getattr(field, "flatchoices", None) or []:
                if not isinstance(label, Promise):
                    missing.append(f"{model._meta.label}.{field.name}={value}")
    assert not missing, f"choice labels not marked with gettext_lazy: {missing}"


@pytest.mark.django_db
def test_demo_pages_render_german(client, django_user_model):
    from library.models import Author

    Author.objects.create(first_name="Ursula", last_name="Le Guin")
    client.force_login(django_user_model.objects.create_superuser("admin-de", password="p"))

    html = client.get("/library/author/", HTTP_ACCEPT_LANGUAGE="de").content.decode()
    assert "Vorname" in html and "Nachname" in html
    assert "First name" not in html

    # the package's lazy "Save" default (no English override in the examples); Django admin's de
    # catalog wins over crud_views' and renders "Sichern"
    html = client.get("/library/author/create/", HTTP_ACCEPT_LANGUAGE="de").content.decode()
    assert 'value="Sichern"' in html
