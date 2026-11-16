"""Real command translations, compiled coverage and stable policy/source contracts."""

import gettext
import json
import re
from collections import Counter

import polib
import pytest
from django.utils import translation
from django.utils.translation import trans_real

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import ListView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ViewSet
from crud_views_guardian.lib.views import GUARDIAN_MIXINS, GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1 import test_manage_locales as inventory
from tests.test1.app.models import Publisher
from tests.test1.test_manage_command import invoke, isolated_catalogue
from tests.test1.test_resource_manage import ManageItem


def test_command_msgids_and_placeholders_in_compiled_catalog(monkeypatch):
    # Extend only for this test; keep the older inventory's ownership unchanged.
    monkeypatch.setitem(
        inventory.SOURCES,
        "crud_views",
        [*inventory.SOURCES["crud_views"], "management/commands/cv_manage_view.py", "lib/manage_report.py"],
    )
    for package in ("crud_views", "crud_views_guardian"):
        stem = inventory.ROOT / "src" / package / "locale/de/LC_MESSAGES/django"
        po = polib.pofile(str(stem.with_suffix(".po")))
        with stem.with_suffix(".mo").open("rb") as stream:
            compiled = gettext.GNUTranslations(stream)
        for msgid, plural, context in inventory.messages(package):
            # manage_report constructs empty lazy wrappers only to identify their exact types.
            # Empty msgid is gettext's metadata header, not emitted human copy.
            if msgid == "":
                assert plural == "" and context in (None, "")
                continue
            entry = po.find(msgid, msgctxt=context)
            assert entry is not None and entry.translated() and not entry.fuzzy, msgid
            assert entry.msgid_plural == plural
            key = f"{context}\x04{msgid}" if context else msgid
            if not plural:
                assert compiled.gettext(key) == entry.msgstr
                assert Counter(re.findall(r"%\([^)]+\)[sd]", entry.msgstr)) == Counter(
                    re.findall(r"%\([^)]+\)[sd]", msgid)
                )
        inventory.test_manage_compiled_catalog_matches_po_semantics(package)


@pytest.fixture
def localized_command(monkeypatch, django_user_model):
    monkeypatch.setattr(trans_real, "_translations", {})
    with isolated_catalogue(monkeypatch):
        core = ViewSet(model=Publisher, name="locale_core")
        guardian = GuardianViewSet(model=Publisher, name="locale_guardian")
        resource = ViewSet(
            model=ManageItem, name="locale_resource", resource_permissions={"view": "app.view_publisher"}
        )
        for vs, base in ((core, ListView), (guardian, GuardianListViewPermissionRequired), (resource, ListView)):
            type("LocaleList", (base,), {"__module__": __name__, "cv_viewset": vs, "cv_custom_value": object()})
        actor = django_user_model.objects.create_user(username="locale actor", is_active=False)
        yield core, guardian, resource, actor


def machine_fields(value):
    """Collect machine leaves without discarding synthetic policy/value records."""
    fields = {"code", "scope", "status", "kind", "state", "level", "severity_code", "effective_provider", "provider"}
    found = {}

    def walk(node, path=()):
        if isinstance(node, dict):
            for key, item in node.items():
                if key in fields or key in {"source", "guardian_policy"}:
                    found[(*path, key)] = (
                        {k: v for k, v in item.items() if k != "tooltip"} if isinstance(item, dict) else item
                    )
                walk(item, (*path, key))
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, (*path, index))

    walk(value)
    return found


@pytest.mark.django_db
@pytest.mark.parametrize("kind", [0, 1, 2])
@pytest.mark.parametrize("selected", [False, True])
@pytest.mark.parametrize("shown", [False, True])
def test_real_localized_full_selected_actor_hidden_and_policy(localized_command, monkeypatch, kind, selected, shown):
    vs, actor = localized_command[kind], localized_command[3]
    monkeypatch.setattr(crud_views_settings, "manage_show_users", shown)
    if kind == 1 and selected:
        monkeypatch.setattr(vs.get_view_class("list"), "cv_guardian_accept_global_perms", True)
    args = [vs.name, *(["list", "--user", actor.username] if selected else [])]
    documents = {}
    for language in ("en", "de"):
        with translation.override(language):
            code, output = invoke(*args, "--as-json", "--force-color")
            assert code == 0 and "\x1b" not in output
            document = documents[language] = json.loads(output)
            permissions = document["data"]["permissions"]["data"]
            assert permissions["holder_visibility"] == ("shown" if shown else "hidden")
            assert permissions["users"] == ([] if shown else None)
            assert permissions["superusers"]["names"] == ([] if shown else None)
            assert permissions["actor"]["state"] == ("selected" if selected else "not_selected")
            if selected:
                assert permissions["actor"]["row"]["label"] == actor.username
            rows = document["data"]["views"]["data"]["entries"]
            assert any(
                row["key"] == "custom_value" and row["value"]["kind"] == "unsupported"
                for view in rows
                for section in view["sections"]
                for row in section["entries"]
            )
            if kind == 1:
                for view in rows:
                    cls = vs.get_view_class(view["key"])
                    synthetic = {r["key"]: r for s in view["sections"] if s["key"] == "guardian" for r in s["entries"]}
                    expected_policy = (
                        ("global_fallback" if selected else "strict") if view["key"] == "list" else "not_applicable"
                    )
                    assert view["guardian_policy"]["effective_policy"] == expected_policy
                    assert synthetic["effective_policy"]["value"]["value"] == expected_policy
                    assert synthetic["effective_policy"]["source"]["code"] == "effective"
                    assert synthetic["guardian_mixin"]["value"]["value"] == [
                        f"{mixin.__module__}.{mixin.__qualname__}"
                        for mixin, _ in GUARDIAN_MIXINS
                        if issubclass(cls, mixin)
                    ]
            text_code, text = invoke(*args, "--no-color")
            assert text_code == code
            assert ("ViewSet-Konfiguration" if language == "de" else "ViewSet configuration") in text
            assert ("effektive Berechtigungen" if language == "de" else "effective grants") in text
            if selected:
                assert ("ausgewählte Ansicht: list" if language == "de" else "selected view: list") in text
            if not shown:
                assert ("Anzahlen bleiben sichtbar" if language == "de" else "counts remain visible") in text
            if kind == 2:
                assert (
                    "Ressourcen-Berechtigungen gelten global" if language == "de" else "Resource grants are global"
                ) in text
    assert machine_fields(documents["en"]) == machine_fields(documents["de"])
    if kind == 1:

        def synthetic_values(doc):
            return [
                (row["key"], row["value"], row["source"])
                for view in doc["data"]["views"]["data"]["entries"]
                for section in view["sections"]
                for row in section["entries"]
                if row["key"] in {"effective_policy", "guardian_mixin"}
            ]

        assert synthetic_values(documents["en"]) == synthetic_values(documents["de"])


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["partial", "failed", "checks"])
def test_localized_errors_checks_and_exit_precedence(localized_command, monkeypatch, case):
    vs = localized_command[0]
    if case == "partial":

        def broken(*args):
            raise RuntimeError("custom collection failed")

        monkeypatch.setattr(ManageView, "get_manage_facts", broken)
    if case == "checks":
        monkeypatch.setattr(vs.get_view_class("list"), "cv_icon_header", 123)
    results = []
    for language in ("en", "de"):
        with translation.override(language):
            args = ["missing" if case == "failed" else vs.name]
            code, output = invoke(*args, "--as-json", "--force-color")
            assert "\x1b" not in output
            data = json.loads(output)
            assert code == (1 if case == "checks" else 2)
            assert data["status"] == {"checks": "complete", "partial": "partial", "failed": "failed"}[case]
            if case == "failed":
                assert ("Unbekanntes ViewSet" if language == "de" else "Unknown ViewSet") in data["errors"][0][
                    "message"
                ]
            if case == "checks":
                messages = data["data"]["checks"]["data"]["messages"]
                assert any(m["severity_code"] == "error" and m["level"] == 40 for m in messages)
            text_code, text = invoke(*args, "--no-color")
            assert text_code == code
            if case != "failed":
                assert ("Systemprüfungen" if language == "de" else "System checks") in text
            results.append(machine_fields(data))
    assert results[0] == results[1]


@pytest.mark.django_db
def test_localized_catalogue_schema_help_and_input_errors(localized_command):
    for language in ("en", "de"):
        with translation.override(language):
            code, text = invoke("--list", "--no-color")
            assert code == 0 and ("Katalog" if language == "de" else "Catalogue") in text
            for args in (("--list", "--as-json"), ("--schema",)):
                code, output = invoke(*args, "--force-color")
                assert code == 0 and "\x1b" not in output and json.loads(output)
            for args, word in (
                ((), "Wählen Sie"),
                (("locale_core", "missing"), "Unbekannte Ansicht"),
                (("locale_core", "--user", "missing"), "Unbekannter Benutzer"),
            ):
                code, text = invoke(*args, "--no-color")
                assert code == 2
                if language == "de":
                    assert word in text
            from crud_views.management.commands.cv_manage_view import Command

            assert (
                "Konfiguration und Berechtigungsdiagnosen"
                if language == "de"
                else "configuration and permission diagnostics"
            ) in Command().help
