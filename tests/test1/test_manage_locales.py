"""German source and compiled catalogs cover the actual diagnostic message inventory."""

import ast
import gettext
import re
from collections import Counter
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
    "crud_views_guardian": [
        "lib/views.py",
        "lib/mixins.py",
        "lib/ancestors.py",
        "templates/crud_views/view_guardian_manage.html",
    ],
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


@pytest.mark.parametrize(
    "call",
    ["_(message)", "_(f'hello {name}')", "pgettext(context, 'one')", "ngettext('one', plural, n)", "_('hello %s')"],
)
def test_extraction_rejects_dynamic_or_unnamed_messages(tmp_path, monkeypatch, call):
    source = "from django.utils.translation import gettext as _, pgettext, ngettext\n" + call
    with pytest.raises(ValueError):
        extract_fixture(tmp_path, monkeypatch, source)


def test_extraction_escaped_literals(tmp_path, monkeypatch):
    source = r"""from django.utils.translation import gettext as _
_("quoted \"word\"\nnext" " line")
"""
    assert extract_fixture(tmp_path, monkeypatch, source) == [('quoted "word"\nnext line', "", None)]


def test_extraction_multiline_template_context_plural(tmp_path, monkeypatch):
    source = """{% load i18n %}{% translate "Open" context "verb" %}
{% blocktranslate trimmed count count=items|length context "rows" %}
    {{ count }} row
{% plural %}
    {{ count }} rows
{% endblocktranslate %}"""
    assert extract_fixture(tmp_path, monkeypatch, source, "html") == [
        ("%(count)s row", "%(count)s rows", "rows"),
        ("Open", "", "verb"),
    ]


def test_extraction_keyword_literals(tmp_path, monkeypatch):
    source = """from django.utils.translation import npgettext_lazy as tr
tr(context="rows", singular="%(count)s row", plural="%(count)s rows", number="count")"""
    assert extract_fixture(tmp_path, monkeypatch, source) == [("%(count)s row", "%(count)s rows", "rows")]


SIGNATURES = {
    "gettext": ("message",),
    "gettext_lazy": ("message",),
    "gettext_noop": ("message",),
    "ngettext": ("singular", "plural"),
    "ngettext_lazy": ("singular", "plural"),
    "pgettext": ("context", "message"),
    "pgettext_lazy": ("context", "message"),
    "npgettext": ("context", "singular", "plural"),
    "npgettext_lazy": ("context", "singular", "plural"),
}


def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{dotted_name(node.value)}.{node.attr}"
    return ""


def django_imports(tree):
    """Resolve explicit import bindings; unrelated gettext-shaped methods are not emitters."""
    bindings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bindings[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bindings[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return bindings


def messages(package):
    """Extract literal Django gettext signatures, failing visibly on unextractable messages."""
    found = set()
    for relative in SOURCES[package]:
        source = (ROOT / "src" / package / relative).read_text()
        if relative.endswith(".html"):
            source = templatize(source)
            # templatize produces xgettext input, not an executable Python module.
            literal = r"""u?(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
            calls = re.findall(
                rf"\b(?:gettext|ngettext|pgettext|npgettext)\({literal}(?:,\s*{literal})*(?:,\s*count)?\)", source
            )
            nodes = [ast.parse(call).body[0].value for call in calls]
            bindings = {name: f"django.utils.translation.{name}" for name in SIGNATURES}
        else:
            tree = ast.parse(source)
            nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
            bindings = django_imports(tree)
        for node in nodes:
            name = dotted_name(node.func)
            root, _, tail = name.partition(".")
            resolved = bindings.get(root, "") + ("." + tail if tail else "")
            module, _, function = resolved.rpartition(".")
            if module != "django.utils.translation" or function not in SIGNATURES:
                continue
            keywords = {kw.arg: kw.value for kw in node.keywords}
            values = {}
            for index, argument in enumerate(SIGNATURES[function]):
                value = node.args[index] if index < len(node.args) else keywords.get(argument)
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    raise ValueError(f"{relative}:{node.lineno}: {function} requires literal {argument}")
                # Named placeholders make translations reorderable and permit parity checks.
                if re.search(r"%(?!%|\([^)]+\)[sd])", value.value.replace("%%", "")):
                    raise ValueError(f"{relative}:{node.lineno}: use named %(name)s interpolation")
                values[argument] = value.value
            found.add((values.get("message", values.get("singular")), values.get("plural", ""), values.get("context")))
    return sorted(found, key=lambda item: (item[0], item[1], item[2] or ""))


@pytest.mark.parametrize("package", SOURCES)
def test_manage_german_catalog_covers_sources(package):
    catalog = polib.pofile(str(ROOT / "src" / package / "locale/de/LC_MESSAGES/django.po"))
    missing = []
    for msgid, plural, context in messages(package):
        entry = catalog.find(msgid, msgctxt=context)
        if (
            entry is None
            or entry.fuzzy
            or not entry.translated()
            or entry.msgid_plural != plural
            or entry.msgctxt != context
        ):
            missing.append(msgid)
    assert not missing, missing


@pytest.mark.parametrize("package", SOURCES)
def test_manage_compiled_catalog_matches_po_semantics(package):
    stem = ROOT / "src" / package / "locale/de/LC_MESSAGES/django"
    catalog = polib.pofile(str(stem.with_suffix(".po")))
    binary = polib.mofile(str(stem.with_suffix(".mo")))

    def semantic(entry):
        return (
            entry.msgid,
            entry.msgid_plural,
            entry.msgctxt,
            entry.msgstr,
            tuple(sorted(entry.msgstr_plural.items())),
        )

    assert {semantic(entry) for entry in binary} == {semantic(entry) for entry in catalog.translated_entries()}
    assert binary.metadata == catalog.metadata
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
                assert Counter(re.findall(r"%\([^)]+\)[sd]", value)) == Counter(
                    re.findall(r"%\([^)]+\)[sd]", entry.msgid if count == 1 else entry.msgid_plural)
                )
        else:
            assert compiled.gettext(key) == entry.msgstr
            assert Counter(re.findall(r"%\([^)]+\)[sd]", entry.msgstr)) == Counter(
                re.findall(r"%\([^)]+\)[sd]", entry.msgid)
            )


def test_compiled_contextual_plural_validation(tmp_path, monkeypatch):
    import sys

    stem = tmp_path / "src/example/locale/de/LC_MESSAGES/django"
    stem.parent.mkdir(parents=True)
    catalog = polib.POFile()
    catalog.metadata = {
        "Language": "de",
        "Content-Type": "text/plain; charset=UTF-8",
        "Plural-Forms": "nplurals=2; plural=(n != 1);",
    }
    catalog.extend(
        [
            polib.POEntry(msgid="Open", msgctxt="verb", msgstr="Öffnen"),
            polib.POEntry(msgid="Open", msgctxt="state", msgstr="Offen"),
            polib.POEntry(
                msgid="%(count)s row",
                msgid_plural="%(count)s rows",
                msgctxt="rows",
                msgstr_plural={0: "%(count)s Zeile", 1: "%(count)s Zeilen"},
            ),
        ]
    )
    catalog.save(str(stem.with_suffix(".po")))
    catalog.save_as_mofile(str(stem.with_suffix(".mo")))
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    test_manage_compiled_catalog_matches_po_semantics("example")
    # A stale binary must fail even if the changed entry is outside today's emitter list.
    catalog[0].msgstr = "Aufmachen"
    catalog.save(str(stem.with_suffix(".po")))
    with pytest.raises(AssertionError):
        test_manage_compiled_catalog_matches_po_semantics("example")


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
