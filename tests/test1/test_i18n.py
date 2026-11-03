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


# NOTE: covers all five shipped packages (#88 Task 4 + Task 5), each with
# a fully translated de catalog.
SHIPPED = {
    "crud_views_polymorphic": ["de"],
    "crud_views_guardian": ["de"],
    "crud_views_object_detail": ["de"],
    "crud_views": ["de"],
    "crud_views_workflow": ["de"],
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
    for _pkg, _loc, d in _iter_po():
        mo = d / "django.mo"
        assert mo.exists(), f"missing {mo}"
        with mo.open("rb") as fh:
            gettext_mod.GNUTranslations(fh)  # raises if corrupt


def test_guardian_manage_renders_translated():
    from django.template import Context, Template

    tmpl = Template('{% load i18n %}{% translate "Permission Holders" %}')
    with translation.override("de"):
        assert tmpl.render(Context({})) != "Permission Holders"


# the translated default label of the filter toggle (#262, FILT-04). Three separate claims: the PO / MO checks prove
# the shipped entry, the gettext sentinel proves the label is translated at render time, and the German page proves
# active-language integration. German spells it "Filter" too, so no rendered word can tell which merged catalog
# supplied it, and an equality-only assertion would pass through gettext's identical-string fallback.

CORE_DE = REPO / "src" / "crud_views" / "locale" / "de" / "LC_MESSAGES"


def test_filter_catalog_entry():
    polib = pytest.importorskip("polib")
    entry = polib.pofile(str(CORE_DE / "django.po")).find("Filter")
    assert entry is not None, "msgid 'Filter' missing from the core German catalog"
    assert not entry.obsolete
    assert "fuzzy" not in entry.flags
    assert entry.msgstr == "Filter"
    assert any(path == "lib/view/buttons.py" for path, _line in entry.occurrences)
    with (CORE_DE / "django.mo").open("rb") as fh:
        compiled = gettext_mod.GNUTranslations(fh)
    assert "Filter" in compiled._catalog  # the compiled key itself, not the fallback for a missing one
    assert compiled.gettext("Filter") == "Filter"


@pytest.mark.django_db
def test_filter_gettext_at_render_time(client_user_publisher_view, cv_publisher, monkeypatch):
    from django.urls import reverse

    from crud_views.lib.view import buttons
    from crud_views.lib.view.buttons import FilterContextButton

    resp = client_user_publisher_view.get(reverse(cv_publisher.get_router_name("list")))
    context = resp.context["view"].cv_get_view_context()
    calls = []

    def sentinel(result):
        def _(msgid):
            calls.append(msgid)
            return result

        return _

    monkeypatch.setattr(buttons, "_", sentinel("Ƒiltər ✓"))
    assert FilterContextButton().get_context(context)["cv_action_label"] == "Ƒiltər ✓"
    monkeypatch.setattr(buttons, "_", sentinel("Ⓕ 过滤"))
    assert FilterContextButton().get_context(context)["cv_action_label"] == "Ⓕ 过滤"  # on every call, not at import
    assert calls == ["Filter", "Filter"]
    # a custom label still wins over the translated seed; an empty custom result keeps it
    assert FilterContextButton(label_template_code="Suchen").get_context(context)["cv_action_label"] == "Suchen"
    empty = FilterContextButton(label_template_code="{% if False %}x{% endif %}")
    assert empty.get_context(context)["cv_action_label"] == "Ⓕ 过滤"


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="de", LANGUAGES=[("en", "English"), ("de", "German")])
@pytest.mark.parametrize("mode", ["icon", "both", "label"])
def test_filter_german_render(client_user_publisher_view, cv_publisher, monkeypatch, mode):
    from django.urls import reverse
    from lxml import html as lxml_html

    from crud_views.lib.settings import crud_views_settings
    from crud_views.lib.view.buttons import FilterContextButton
    from tests.test1.app.views import PublisherListView

    monkeypatch.setattr(PublisherListView, "cv_context_actions_label_mode", None)
    monkeypatch.setattr(cv_publisher, "context_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"filter": mode})
    url = reverse(cv_publisher.get_router_name("list"))

    def toggle():
        doc = lxml_html.fromstring(client_user_publisher_view.get(url).content)
        # the page really is German: the toolbar's container label comes from the same active language
        assert doc.xpath("//fieldset[@cv-context-container]")[0].get("aria-label") == "Aktionen"
        (button,) = doc.xpath("//button[@id='cv-filter-toggle']")
        return button

    with translation.override("en"):
        with translation.override("de"):
            button = toggle()
            label = button.xpath("./span[not(@data-cv-filter-icon)]")[-1].text
            assert label == "Filter"
            assert button.get("title") == ("Filter" if mode == "icon" else None)
            # custom labels still override the translated default
            monkeypatch.setattr(
                cv_publisher,
                "context_buttons",
                [FilterContextButton(label_template_code="Suchen"), *cv_publisher.context_buttons],
            )
            assert toggle().xpath("./span[not(@data-cv-filter-icon)]")[-1].text == "Suchen"
        assert translation.get_language() == "en"  # the German override is undone
