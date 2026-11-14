"""Cross-contract release inventory, using admitted responses and real registered views."""

import ast
import re
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.template.loader import get_template
from django.template.loader_tags import BlockNode
from django.urls import reverse

from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES
from crud_views.lib.settings import crud_views_settings

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def developer(django_user_model):
    actor = django_user_model.objects.create_user(username="release-developer")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return actor


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_rendered_public_surface_matches_documentation(request, fixture, client, developer):
    viewset = request.getfixturevalue(fixture)
    client.force_login(developer)
    response = client.get(reverse(viewset.get_router_name("manage")))
    assert response.status_code == 200
    text = (ROOT / "docs/reference/theme.md").read_text().split("## Structured manage contracts\n", 1)[1]
    context_section = text.split("### Prepared manage context\n", 1)[1].split("### Request-free manage builders", 1)[0]
    documented_context = set(re.findall(r"^\| `(manage_\w+)` \|", context_section, re.M))
    if fixture == "cv_author":
        documented_context.remove("manage_guardian")
    assert {key for key in response.context_data if key.startswith("manage_")} == documented_context

    template = get_template("crud_views/view_manage.html").template
    blocks = {block.name for block in template.nodelist.get_nodes_by_type(BlockNode)} - {"cv_content"}
    documented_blocks = text.split("### Manage blocks\n", 1)[1].split("### Prepared manage context", 1)[0]
    assert blocks == set(re.findall(r"^\| `(\w+)` \|", documented_blocks, re.M))

    buttons = (ROOT / "docs/reference/buttons.md").read_text()
    documented_classes = dict(re.findall(r"^\| `(manage:[\w-]+)` \| `([^`]+)` \|", buttons, re.M))
    assert {
        key: value for key, value in DEFAULT_BUTTON_CLASSES.items() if key.startswith("manage:")
    } == documented_classes
    registration = text.split("### Manage class registration\n", 1)[1]
    assert set(re.findall(r"`(manage:[\w-]+)`", registration)) == set(documented_classes)


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_requirement_fields_match_documented_contract(request, fixture):
    viewset = request.getfixturevalue(fixture)
    text = (ROOT / "docs/reference/theme.md").read_text().split("### Requirement descriptions\n", 1)[1]
    example = ast.literal_eval(text.split("```python\n", 1)[1].split("```", 1)[0].strip())
    requirements = {key: cls.cv_get_requirement() for key, cls in viewset.get_all_views().items()}
    assert {"list", "detail", "create", "update", "delete", "manage"} <= requirements.keys()
    for requirement in requirements.values():
        assert requirement.keys() == example.keys()
        assert requirement["kind"] in {"permission", "group", "none", "custom"}
        assert isinstance(requirement["ancestor_applies"], bool)
    assert requirements["manage"]["kind"] == "group"
    assert requirements["manage"]["value"] == crud_views_settings.manage_group
    assert requirements["update"]["value"] == "change"
