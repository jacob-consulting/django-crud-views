"""Keep real manage help links and the published extension contract together."""

import re
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import resolve, reverse
from lxml import html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views.manage import ManageView
from crud_views_guardian.lib.views import GuardianManageView
from tests.test1.test_form_frame import _theme_templates
from tests.test1.test_heading_docs import recipe

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference/manage.md"
ANCHORS = {
    "system-checks",
    "permissions",
    "views",
    "presentation",
    "viewset",
    "hierarchy",
    "url-names",
    "ancestor-policy",
    "guardian",
    "templates-and-actions",
    "label-modes",
}


@pytest.fixture
def developer(django_user_model):
    actor = django_user_model.objects.create_user(username="docs-developer")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return actor


def heading_anchors():
    assert REFERENCE.is_file(), "The manage reference must publish the rendered help targets"
    # These public headings deliberately use only ASCII letters, spaces and hyphens.
    return {heading.lower().replace(" ", "-") for heading in re.findall(r"^## ([\w -]+)$", REFERENCE.read_text(), re.M)}


@pytest.mark.django_db
def test_rendered_manage_help_targets_are_published(client, cv_author, cv_guardian_author, developer):
    client.force_login(developer)
    fragments = set()
    for viewset in (cv_author, cv_guardian_author):
        response = client.get(reverse(viewset.get_router_name("manage")))
        assert response.status_code == 200
        tree = html.fromstring(response.content)
        assert not tree.cssselect("#cv-manage-views summary a")
        for link in tree.cssselect("[data-cv-manage-help]"):
            base, fragment = link.get("href").split("#")
            assert base == viewset.get_view_class("manage").manage_docs_base_url
            assert link.get("target") == "_blank" and link.get("rel") == "noopener"
            fragments.add(fragment)
    assert fragments == ANCHORS
    assert fragments <= heading_anchors()
    assert "(manage.md)" in (ROOT / "docs/reference/index.md").read_text()


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_subclass_docs_base_changes_every_rendered_help_link(request, fixture, developer):
    viewset = request.getfixturevalue(fixture)
    original = viewset.get_view_class("manage")

    class LocalDocs(original):
        # Inheriting an already registered view without redeclaring cv_viewset does not register another route.
        manage_docs_base_url = "https://docs.example.test/team/manage/"

    view = LocalDocs()
    view.request = RequestFactory().get("/manage/")
    view.request.resolver_match = resolve(reverse(viewset.get_router_name("manage")))
    view.request.user = developer
    view.kwargs = {}
    tree = html.fromstring(render_to_string(view.template_name, view.get_context_data(), request=view.request))
    links = tree.cssselect("[data-cv-manage-help]")
    assert links
    assert all(link.get("href").startswith(LocalDocs.manage_docs_base_url + "#") for link in links)
    assert {link.get("href").split("#")[1] for link in links} <= heading_anchors()


@pytest.mark.django_db
def test_manage_public_inventory_matches_rendered_context(client, cv_guardian_author, developer):
    text = (ROOT / "docs/reference/theme.md").read_text().split("## Structured manage contracts\n", 1)[1]
    template = (ROOT / "src/crud_views/templates/crud_views/view_manage.html").read_text()
    blocks = set(re.findall(r"{% block (\w+) %}", template)) - {"cv_content"}
    documented_blocks = set(re.findall(r"^\| `(\w+)` \|", text.split("### Prepared manage context", 1)[0], re.M))
    assert documented_blocks == blocks
    client.force_login(developer)
    response = client.get(reverse(cv_guardian_author.get_router_name("manage")))
    assert response.status_code == 200
    keys = {key for key in response.context_data if key.startswith("manage_")}
    documented = text.split("### Prepared manage context\n", 1)[1].split("### Request-free manage builders", 1)[0]
    assert set(re.findall(r"^\| `(manage_\w+)` \|", documented, re.M)) == keys
    methods = {name for cls in (ManageView, GuardianManageView) for name in vars(cls) if name.startswith("get_manage_")}
    assert set(re.findall(r"^\| `(get_manage_\w+)` \|", text, re.M)) == methods
    assert "`cv_get_requirement()`" in text
    for app in ("crud_views", "crud_views_guardian"):
        catalog = f"src/{app}/locale/de/LC_MESSAGES/django.po"
        assert (ROOT / catalog).is_file()
        assert f"`{catalog}`" in text


def test_manage_script_is_documented_with_its_enhancement_boundary():
    text = (ROOT / "docs/reference/javascript.md").read_text()
    assert "| `manage.js` | nothing | nothing |" in text
    assert "## Manage defaults\n" in text
    section = text.split("## Manage defaults\n", 1)[1].split("\n## ", 1)[0]
    for name in (
        "data-cv-show-defaults",
        "cv.initManageDefaults",
        "DOMContentLoaded",
        "cv:modal:loaded",
        "manage.css",
        "no persistence",
        "without JavaScript",
        "tooltip adapter",
    ):
        assert name.casefold() in section.casefold()
    assert (ROOT / "src/crud_views/static/crud_views/js/manage.js").is_file()


@pytest.mark.django_db
def test_published_legacy_guardian_include_remains_usable(client, cv_guardian_author, developer, monkeypatch):
    path = "manage-docs-legacy.html"
    monkeypatch.setattr(cv_guardian_author.get_view_class("manage"), "template_name", path)
    with _theme_templates({path: recipe(ROOT / "docs/reference/theme.md", "### Legacy manage context and includes")}):
        client.force_login(developer)
        response = client.get(reverse(cv_guardian_author.get_router_name("manage")))
    assert response.status_code == 200
    tree = html.fromstring(response.content)
    assert "GuardianViewSet.get_objects_for_user()" in tree.text_content()
    assert not tree.cssselect("#cv-manage-guardian")
    assert tree.cssselect("#cv-manage-permissions [data-manage-actor]")


def test_manage_breaking_change_has_paired_migration():
    release = (ROOT / "CHANGELOG.md").read_text().split("## Unreleased", 1)[1].split("\n## ", 1)[0]
    breaking = release.split("### Breaking", 1)[1].split("\n### ", 1)[0]
    assert "**Structured manage cards** (#366)" in breaking
    assert "docs/migrating-1.0.md#structured-manage-cards" in breaking
    migration = (ROOT / "docs/migrating-1.0.md").read_text()
    section = migration.split("## Structured manage cards\n", 1)[1].split("\n## ", 1)[0]
    for boundary in ("model_construct", "registered manage", 'manage_views_enabled="no"', "#370", "#371"):
        assert boundary in section
