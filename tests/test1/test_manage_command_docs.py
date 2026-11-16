"""Execute published command examples and configured-builder recipes."""

import json
import re
import shlex
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest
from django.conf import settings
from django.urls import get_resolver

from crud_views.lib import check
from crud_views.lib.viewset import _REGISTRY, ViewSet
from tests.test1.app.models import Author
from tests.test1.test_manage_command import SECTIONS, invoke, isolated_catalogue

ROOT = Path(__file__).resolve().parents[2]


def reference(name):
    return (ROOT / f"docs/reference/{name}.md").read_text()


@pytest.mark.django_db
def test_published_command_examples(cv_author, django_user_model):
    django_user_model.objects.create_user(username="alice")
    section = reference("manage").split("## cv_manage_view\n", 1)[1].split("### Configuration report scope", 1)[0]
    commands = re.findall(r"^python manage.py cv_manage_view (.+)$", section, re.M)
    assert len(commands) == 6
    for line in commands:
        args = shlex.split(line)
        code, output = invoke(*args)
        # The existing AuthorContact fixture deliberately has unsilenced E110 findings.
        assert code == (0 if "--list" in args or "--schema" in args else 1)
        if "--schema" in args:
            assert "$defs" in json.loads(output)
        elif "--as-json" in args:
            data = json.loads(output)
            assert data["version"] == 1 and data["status"] == "complete"
            if "--list" in args:
                assert "author" in {row["name"] for row in data["data"]["entries"]}
            else:
                assert data["data"]["identity"]["name"] == cv_author.name
                assert set(data["data"]) == {"identity", *SECTIONS}
                if "list" in args:
                    assert [row["key"] for row in data["data"]["views"]["data"]["entries"]] == ["list"]
                if "--user" in args:
                    assert data["data"]["permissions"]["data"]["actor"]["row"]["label"] == "alice"
        else:
            assert "ViewSet configuration" in output and "author" in output


@pytest.mark.parametrize("args", [(), ("--list", "--schema"), ("--list", "author"), ("--schema", "--user", "alice")])
def test_documented_invalid_combinations(args):
    code, output = invoke(*args, "--as-json")
    result = json.loads(output)
    assert code == 2 and result["status"] == "failed"
    assert result["errors"][0]["code"] == "invalid_arguments"


@pytest.mark.django_db
@pytest.mark.parametrize("legacy", [False, True])
def test_documented_configured_recipe_and_teardown(monkeypatch, legacy):
    original_urlconf = settings.ROOT_URLCONF
    original_patterns = get_resolver().url_patterns
    registry, vocabulary = dict(_REGISTRY), dict(check._VOCAB_CACHE)
    module = ModuleType("documented_manage_recipe")
    recipe = (
        reference("theme").split("<!-- cv-manage-export-recipe -->", 1)[1].split("```python\n", 1)[1].split("```", 1)[0]
    )
    with isolated_catalogue(monkeypatch) as (_, patch):
        patch.setitem(sys.modules, module.__name__, module)
        exec(compile(recipe, "docs/reference/theme.md", "exec"), module.__dict__)
        cls = module.ProjectManageView
        if legacy:
            original = cls.get_manage_facts

            def legacy_rows(self, viewset, user):
                return [{k: v for k, v in row.items() if k != "_export"} for row in original(self, viewset, user)]

            patch.setattr(cls, "get_manage_facts", legacy_rows)
        vs = ViewSet(model=Author, name="recipe_author", manage_view_class=f"{module.__name__}.ProjectManageView")
        manage = vs.get_all_views()["manage"]()
        before = deepcopy(manage.get_manage_facts(vs, None))
        code, output = invoke(vs.name, "--as-json")
        data = json.loads(output)
        assert code == (2 if legacy else 0), output
        if legacy:
            assert data["status"] == "partial" and data["data"]["facts"]["status"] == "error"
            assert data["errors"][0]["code"] == "output_validation_failed"
            assert data["data"]["presentation"]["status"] == "ok"
        else:
            row = next(row for row in data["data"]["facts"]["data"]["entries"] if row["key"] == "project_note")
            assert row["value"]["kind"] == "native"
            assert row["value"]["value"] == "Supported by the project team"
            assert row["source"]["code"] == "default"
        with pytest.raises(RuntimeError, match="recipe teardown"), manage.manage_export():
            manage.get_manage_facts(vs, None)
            raise RuntimeError("recipe teardown")
        assert "_manage_export_enabled" not in manage.__dict__
        assert manage.get_manage_facts(vs, None) == before
    assert dict(_REGISTRY) == registry and vocabulary == check._VOCAB_CACHE
    assert original_urlconf == settings.ROOT_URLCONF and get_resolver().url_patterns is original_patterns
    assert module.__name__ not in sys.modules


def test_documented_section_inventory_and_boundaries():
    text = reference("manage")
    scope = text.split("### Configuration report scope\n", 1)[1].split("### Actors", 1)[0]
    assert set(re.findall(r"^\| `(\w+)` \|", scope, re.M)) == set(SECTIONS)
    for boundary in (
        "caller-owned transaction",
        "autocommit",
        "rollback-only",
        "existing built-in checks",
        "non-string",
        "not sandboxed",
        "closed-enum",
        "users=null",
        "UUID",
        "unresolved parent",
    ):
        assert boundary.lower() in text.lower()
    theme = reference("theme")
    assert "delivered `cv_manage_view`" in theme and "(#371)" in theme
    assert "configuration-dump command remains a separate follow-up" not in theme


def test_delivered_release_and_migration_guidance():
    changelog = (ROOT / "CHANGELOG.md").read_text().split("## Unreleased\n", 1)[1].split("\n## ", 1)[0]
    migration = (ROOT / "docs/migrating-1.0.md").read_text()
    # Restrict classification to this issue's entry, preserving unrelated historical breaking entries.
    phase_entries = []
    for section in re.split(r"^### ", changelog, flags=re.M)[1:]:
        heading, body = section.split("\n", 1)
        for entry in re.split(r"^- ", body, flags=re.M)[1:]:
            if "(#371)" in entry:
                phase_entries.append((heading, entry))
                assert "docs/reference/manage.md#cv_manage_view" in entry
                if heading == "Breaking":
                    assert "## ViewSet configuration command" in migration
                    assert "cv_manage_view" in migration.split("## ViewSet configuration command", 1)[1]
    assert len(phase_entries) == 1 and phase_entries[0][0] == "Added"
    for text in (reference("theme"), migration):
        assert "delivered `cv_manage_view` command" in text
        assert "(#371)" in text and "manage.md#cv_manage_view" in text
        assert "configuration-dump command (#371) is not included" not in text
    # The artifact is produced by plan05; only the final delivery check reads its existence.
    assert (ROOT / "docs/reference/cv_manage_view.schema.json").is_file()
    assert "[complete generated JSON Schema](cv_manage_view.schema.json)" in reference("manage")
