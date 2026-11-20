import gettext as gettext_mod
from io import StringIO
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
    "object_detail",
    "breadcrumbs",
    "conditional",
    "formsets_conditional",
    "delete_demo",
    "custom_form",
    "bulk_selection",
    "label_modes",
    "flash_messages",
    "disabled_actions",
    "theming",
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
    assert "Vorname" in html
    assert "Nachname" in html
    assert "First name" not in html

    # the package's lazy "Save" default (no English override in the examples); Django admin's de
    # catalog wins over crud_views' and renders "Sichern"
    html = client.get("/library/author/create/", HTTP_ACCEPT_LANGUAGE="de").content.decode()
    assert 'value="Sichern"' in html


def test_bulk_selection_msgids_are_translated():
    import polib

    msgids = [
        "document",
        "documents",
        "title",
        "status",
        "locked",
        "owner",
        "Owner",
        "Draft",
        "Published",
        "Archived",
        "Delete selected documents",
        "Delete",
        "Archive selected documents",
        "Archive",
        "Assign owner to selected documents",
        "Assign owner",
        "Assign",
        "Locked documents cannot be deleted.",
        "Locked documents cannot be archived.",
        "Only drafts can be archived.",
        "Locked documents cannot be reassigned.",
        "{{ view.cv_bulk_objects|length }} documents deleted.",
        "{{ view.cv_bulk_objects|length }} documents archived.",
        "Owner assigned to {{ view.cv_bulk_objects|length }} documents.",
    ]
    catalog = polib.pofile(str(LOCALE_DIR / "de" / "LC_MESSAGES" / "django.po"))
    for msgid in msgids:
        entry = catalog.find(msgid)
        assert entry is not None, f"missing German entry: {msgid}"
        assert entry.translated() and "fuzzy" not in entry.flags, msgid
        if "{{ view.cv_bulk_objects|length }}" in msgid:
            assert "{{ view.cv_bulk_objects|length }}" in entry.msgstr, msgid


@pytest.mark.django_db
def test_bulk_selection_pages_render_german(client, django_user_model):
    from bulk_selection.models import Document
    from django.urls import reverse
    from lxml import html

    first = Document.objects.create(title="First draft")
    second = Document.objects.create(title="Second draft")
    locked = Document.objects.create(title="Locked draft", is_locked=True)
    client.force_login(django_user_model.objects.create_superuser("bulk-admin-de", password="p"))

    response = client.get(reverse("bulk_document-list"), HTTP_ACCEPT_LANGUAGE="de")
    assert response.status_code == 200
    tree = html.fromstring(response.content)
    destinations = {}
    for key, label in (("bulk_delete", "Löschen"), ("archive", "Archivieren"), ("assign_owner", "Eigentümer zuweisen")):
        button = tree.xpath(f'//*[@data-cv-bulk-action="{key}"]')[0]
        assert button.text_content().strip() == label
        destinations[key] = button.attrib["formaction"]

    response = client.post(
        destinations["archive"],
        {"cv_bulk_stage": "review", "cv_bulk_ids": [first.pk, locked.pk]},
        HTTP_ACCEPT_LANGUAGE="de",
    )
    assert response.status_code == 200
    assert "Gesperrte Dokumente können nicht archiviert werden." in response.content.decode()
    assert Document.objects.filter(status="draft").count() == 3

    response = client.post(
        destinations["archive"],
        {"cv_bulk_stage": "review", "cv_bulk_ids": [first.pk, second.pk]},
        follow=True,
        HTTP_ACCEPT_LANGUAGE="de",
    )
    assert response.status_code == 200
    assert response.redirect_chain
    assert "2 Dokumente archiviert." in response.content.decode()
    assert Document.objects.filter(status="archived").count() == 2


def test_example_table_columns_mark_headers_for_translation():
    # explicit column verbose_names bypass the model's (translated) field names
    import importlib
    import inspect

    import django_tables2 as tables
    from django.utils.functional import Promise

    missing = []
    for label in EXAMPLE_APPS:
        module = importlib.import_module(f"{label}.views")
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if not issubclass(cls, tables.Table) or cls.__module__ != module.__name__:
                continue
            for col_name, column in cls.base_columns.items():
                header = column.verbose_name
                if header is not None and not isinstance(header, Promise):
                    missing.append(f"{label}.{name}.{col_name}={header!r}")
    assert not missing, f"table headers not marked with gettext_lazy: {missing}"


@pytest.mark.django_db
def test_demo_chrome_renders_german(client, settings):
    # demo banner, home-page user hint, footer and the rate-limit page
    from django.template.loader import render_to_string
    from django.test import RequestFactory
    from django.utils import translation

    settings.DEMO_MODE = True
    html = client.get("/", HTTP_ACCEPT_LANGUAGE="de").content.decode()
    assert "Öffentliche Demo" in html
    assert "Demo-Benutzer" in html
    assert "Live-Demo" in html
    assert "Doku" in html

    with translation.override("de"):
        html = render_to_string("project/429.html", request=RequestFactory().get("/"))
    assert "Zu viele Änderungen" in html


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "de"])
@pytest.mark.parametrize("surface", ["login", "home", "banner"])
def test_demo_account_notices_include_developer(client, settings, language, surface):
    from django.urls import reverse
    from lxml import html

    settings.DEMO_MODE = surface == "banner"
    response = client.get(reverse("login" if surface == "login" else "home"), HTTP_ACCEPT_LANGUAGE=language)
    assert response.status_code == 200
    document = html.fromstring(response.content)
    notice = document.cssselect("#demo-banner" if surface == "banner" else ".alert-info")[0]
    assert notice.xpath(".//code/text()")[-1] == "developer/developer"
    for credentials in ("alice/alice", "bob/bob", "developer/developer"):
        assert credentials in notice.xpath(".//code/text()")
    assert "read access and developer diagnostics" in notice.text_content()


@pytest.mark.django_db
def test_published_demo_credentials_match_seed_output(client, django_user_model):
    from django.core.management import call_command
    from django.urls import reverse
    from lxml import html

    output = StringIO()
    call_command("seed", stdout=output)
    document = html.fromstring(client.get(reverse("login")).content)
    credentials = document.cssselect(".alert-info")[0].xpath(".//code/text()")
    for username in ("alice", "bob", "developer"):
        credential = f"{username}/{username}"
        assert credential in output.getvalue()
        assert credential in credentials
        assert django_user_model.objects.get(username=username).check_password(username)
