"""German source and compiled catalogs cover the actual diagnostic message inventory."""

import ast
import gettext
import re
from pathlib import Path

import polib
import pytest
from django.urls import reverse
from django.utils import translation
from django.utils.translation import trans_real
from django.utils.translation.template import templatize

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "crud_views": [
        "lib/views/manage.py",
        "lib/access_trace.py",
        "lib/access_trace_runner.py",
        "management/commands/cv_access.py",
        "templates/crud_views/view_manage.html",
        "templates/crud_views/includes/access_trace.html",
    ],
    "crud_views_guardian": ["lib/views.py", "templates/crud_views/view_guardian_manage.html"],
}


@pytest.mark.parametrize(
    "name,args,expected",
    [
        ("gettext", "'one'", ("one", "", None)),
        ("gettext_lazy", "'one'", ("one", "", None)),
        ("gettext_noop", "'one'", ("one", "", None)),
        ("ngettext", "'one', 'many', count", ("one", "many", None)),
        ("ngettext_lazy", "'one', 'many', count", ("one", "many", None)),
        ("pgettext", "'ctx', 'one'", ("one", "", "ctx")),
        ("pgettext_lazy", "'ctx', 'one'", ("one", "", "ctx")),
        ("npgettext", "'ctx', 'one', 'many', count", ("one", "many", "ctx")),
        ("npgettext_lazy", "'ctx', 'one', 'many', count", ("one", "many", "ctx")),
    ],
)
@pytest.mark.parametrize("style", ["bare", "alias", "module", "from_module", "qualified"])
def test_extraction_gettext_signatures(tmp_path, monkeypatch, name, args, expected, style):
    imports, call = {
        "bare": (f"from django.utils.translation import {name}", name),
        "alias": (f"from django.utils.translation import {name} as _", "_"),
        "module": ("import django.utils.translation as tr", f"tr.{name}"),
        "from_module": ("from django.utils import translation as tr", f"tr.{name}"),
        "qualified": ("import django.utils.translation", f"django.utils.translation.{name}"),
    }[style]
    assert extract_fixture(tmp_path, monkeypatch, f"{imports}\n{call}({args})") == [expected]


def extract_fixture(tmp_path, monkeypatch, source, suffix="py"):
    import sys

    path = tmp_path / "src" / "example"
    path.mkdir(parents=True)
    (path / f"fixture.{suffix}").write_text(source)
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    monkeypatch.setitem(SOURCES, "example", [f"fixture.{suffix}"])
    return messages("example")


def test_extraction_ignores_non_django_calls(tmp_path, monkeypatch):
    source = "from elsewhere import gettext as _\nimport elsewhere as tr\n_('foreign')\ntr.npgettext('c', 'a', 'b', n)"
    assert extract_fixture(tmp_path, monkeypatch, source) == []


@pytest.mark.parametrize("call", ["_(message)", "_(f'hello {name}')", "pgettext(context, 'one')", "ngettext('one', plural, n)", "_('hello %s')"])
def test_extraction_rejects_dynamic_or_unnamed_messages(tmp_path, monkeypatch, call):
    source = "from django.utils.translation import gettext as _, pgettext, ngettext\n" + call
    with pytest.raises(ValueError):
        extract_fixture(tmp_path, monkeypatch, source)


def test_extraction_escaped_literals(tmp_path, monkeypatch):
    source = r'''from django.utils.translation import gettext as _
_("quoted \"word\"\nnext" " line")
'''
    assert extract_fixture(tmp_path, monkeypatch, source) == [('quoted "word"\nnext line', "", None)]


def test_extraction_multiline_template_context_plural(tmp_path, monkeypatch):
    source = '''{% load i18n %}{% translate "Open" context "verb" %}
{% blocktranslate trimmed count count=items|length context "rows" %}
    {{ count }} row
{% plural %}
    {{ count }} rows
{% endblocktranslate %}'''
    assert extract_fixture(tmp_path, monkeypatch, source, "html") == [
        ("%(count)s row", "%(count)s rows", "rows"), ("Open", "", "verb")
    ]


def messages(package):
    """Use Django's template extractor; AST string arguments retain plural/context keys."""
    found = set()
    for relative in SOURCES[package]:
        source = (ROOT / "src" / package / relative).read_text()
        if relative.endswith(".html"):
            source = templatize(source)
            # templatize produces xgettext input, not an executable Python module.
            literal = r"""u?(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
            calls = re.findall(
                rf"\b(?:gettext|ngettext|pgettext|npgettext)\({literal}(?:,\s*{literal})*(?:, count)?\)", source
            )
            nodes = [ast.parse(call).body[0].value for call in calls]
        else:
            nodes = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)]
        for node in nodes:
            if not isinstance(node.func, ast.Name) or node.func.id not in {
                "_",
                "gettext",
                "gettext_lazy",
                "ngettext",
                "pgettext",
                "npgettext",
            }:
                continue
            args = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
            context = args.pop(0) if node.func.id in {"pgettext", "npgettext"} else None
            if args:
                found.add((args[0], args[1] if "ngettext" in node.func.id else "", context))
    return sorted(found, key=lambda item: item[0])


@pytest.mark.parametrize("package", SOURCES)
def test_manage_german_catalog_covers_sources(package):
    catalog = polib.pofile(str(ROOT / "src" / package / "locale/de/LC_MESSAGES/django.po"))
    missing = []
    for msgid, plural, context in messages(package):
        entry = catalog.find(msgid, msgctxt=context)
        if entry is None or entry.fuzzy or not entry.translated() or entry.msgid_plural != plural:
            missing.append(msgid)
    assert not missing, missing


@pytest.mark.parametrize("package", SOURCES)
def test_manage_compiled_catalog_matches_po_semantics(package):
    stem = ROOT / "src" / package / "locale/de/LC_MESSAGES/django"
    catalog = polib.pofile(str(stem.with_suffix(".po")))
    with stem.with_suffix(".mo").open("rb") as stream:
        compiled = gettext.GNUTranslations(stream)
    assert compiled.info()["language"] == "de"
    assert compiled.charset().lower() == "utf-8"
    assert "nplurals=2" in compiled.info()["plural-forms"]
    for entry in catalog.translated_entries():
        key = f"{entry.msgctxt}\x04{entry.msgid}" if entry.msgctxt else entry.msgid
        if entry.msgid_plural:
            for count in (0, 1, 2, 21):
                value = compiled.ngettext(key, entry.msgid_plural, count)
                assert value == entry.msgstr_plural[int(count != 1)]
                assert set(re.findall(r"%\([^)]+\)[sd]", value)) == set(
                    re.findall(r"%\([^)]+\)[sd]", entry.msgid if count == 1 else entry.msgid_plural)
                )
        else:
            assert compiled.gettext(key) == entry.msgstr
            assert set(re.findall(r"%\([^)]+\)[sd]", entry.msgstr)) == set(re.findall(r"%\([^)]+\)[sd]", entry.msgid))


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_manage_german_requests_load_compiled_messages(request, fixture, client, django_user_model, monkeypatch):
    from django.contrib.auth.models import Group

    from crud_views.lib.settings import crud_views_settings

    viewset = request.getfixturevalue(fixture)
    developer = django_user_model.objects.create_user(username="locale-developer")
    developer.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    monkeypatch.setattr(trans_real, "_translations", {})
    client.force_login(developer)
    with translation.override("de"):
        response = client.get(reverse(viewset.get_router_name("manage")))
    assert response.status_code == 200
    html = response.content.decode()
    for label in ("Berechtigungen", "Standardwerte anzeigen", "Darstellung", "Hierarchie", "Dokumentation:"):
        assert label in html
    assert "view_author" in html
    assert "pk_name" in html
    if fixture == "cv_guardian_author":
        assert "Globale Modellberechtigungen werden nicht akzeptiert." in html


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
@pytest.mark.parametrize(
    "language,legend",
    [
        (
            "en",
            "Blue: required permission · Magenta: required group · Green: Guardian policy. Hover a badge for details.",
        ),
        (
            "de",
            "Blau: erforderliche Berechtigung · Magenta: erforderliche Gruppe · Grün: Guardian-Richtlinie. "
            "Details erscheinen beim Überfahren eines Abzeichens.",
        ),
    ],
)
def test_rendered_semantic_legend(request, fixture, language, legend, client, django_user_model, monkeypatch):
    from django.contrib.auth.models import Group
    from lxml import html

    from crud_views.lib.settings import crud_views_settings

    vs = request.getfixturevalue(fixture)
    actor = django_user_model.objects.create_user(username="legend-developer")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    client.force_login(actor)
    monkeypatch.setattr(trans_real, "_translations", {})
    with translation.override(language):
        response = client.get(reverse(vs.get_router_name("manage")))
    assert response.status_code == 200
    text = html.fromstring(response.content).cssselect("[data-manage-badge-key]")[0].text_content()
    assert legend in text
    assert ("ancestor permission" if language == "en" else "Berechtigung des übergeordneten ViewSets") in text


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_empty_manage_vocabulary_retains_translated_actor(request, fixture, client, django_user_model, monkeypatch):
    from django.contrib.auth.models import Group
    from lxml import html as html_parser

    from crud_views.lib.settings import crud_views_settings

    viewset = request.getfixturevalue(fixture)
    actor = django_user_model.objects.create_user(username="empty-vocabulary-developer")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    # Pydantic stores PrivateAttr outside __dict__; restore its actual storage.
    monkeypatch.setitem(viewset.__pydantic_private__, "_default_permissions", {})
    client.force_login(actor)
    with translation.override("de"):
        response = client.get(reverse(viewset.get_router_name("manage")))
    assert response.status_code == 200
    root = html_parser.fromstring(response.content)
    rows = root.cssselect("[data-manage-actor]")
    assert len(rows) == 1
    assert "Zugriff für: empty-vocabulary-developer (Sie)" in rows[0].text_content()
    assert "Keine Berechtigungen konfiguriert." in root.text_content()
