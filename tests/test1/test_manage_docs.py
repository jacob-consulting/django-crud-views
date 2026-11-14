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
