"""Cross-contract release inventory, using admitted responses and real registered views."""

import ast
import inspect
import re
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.template.loader import get_template
from django.template.loader_tags import BlockNode
from django.urls import reverse
from lxml import html

from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views.manage import ManageView
from tests.test1.test_form_frame import _theme_templates
from tests.test1.test_heading_docs import recipe

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def developer(django_user_model):
    actor = django_user_model.objects.create_user(username="release-developer")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return actor


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("mode", ["viewset", "path"])
def test_rendered_public_surface_matches_documentation(request, fixture, client, developer, monkeypatch, enabled, mode):
    viewset = request.getfixturevalue(fixture)
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", enabled)
    client.force_login(developer)
    response = client.get(
        reverse(viewset.get_router_name("manage")),
        {"cv_access_mode": mode, "cv_access_user": developer.username, "cv_access_path": "/missing/"},
    )
    assert response.status_code == 200
    text = (ROOT / "docs/reference/theme.md").read_text().split("## Structured manage contracts\n", 1)[1]
    context_section = text.split("### Prepared manage context\n", 1)[1].split("### Request-free manage builders", 1)[0]
    documented_context = set(re.findall(r"^\| `(manage_\w+)` \|", context_section, re.M))
    if fixture == "cv_author":
        documented_context.remove("manage_guardian")
    assert {key for key in response.context_data if key.startswith("manage_")} == documented_context
    access = response.context_data["manage_access_trace"]
    if not enabled:
        assert access is None
    else:
        access_section = text.split("### Access trace mapping\n", 1)[1].split("### Access trace rows", 1)[0]
        documented_access = set(re.findall(r"^\| `(\w+)` \|", access_section, re.M))
        assert "error_field" in documented_access
        # These are valid selections: only invalid web submissions add the optional field.
        assert set(access) == documented_access - {"error_field"}
        assert set(access["actor"]) == {"pk", "username", "active", "anonymous"}
        assert access["actor"]["pk"] == str(developer.pk)
        if mode == "path":
            assert not access["rows"] and access["trace"]["outcome"] == "no_such_route"
        else:
            row_section = text.split("### Access trace rows\n", 1)[1].split("\n### ", 1)[0]
            documented_rows = set(re.findall(r"^\| `(\w+)` \|", row_section, re.M))
            assert [row["key"] for row in access["rows"]] == list(viewset.get_all_views())
            assert all(set(row) == documented_rows for row in access["rows"])
            assert response.context_data["manage_permissions"]["actor"]["id"] == developer.pk

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
    assert len(documented_classes) == 19


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_access_builder_public_signature_without_request(request, fixture, developer, monkeypatch):
    viewset = request.getfixturevalue(fixture)
    instance = viewset.get_view_class("manage")()
    assert not hasattr(instance, "request")
    signature = inspect.signature(ManageView.get_manage_access_trace)
    assert str(signature) == "(self, viewset, user, *, mode, object_pk=None, path=None, route_kwargs=None)"
    assert str(signature) in (ROOT / "docs/reference/theme.md").read_text()

    def forbidden(self):
        raise AssertionError("The public builder must not read request")

    monkeypatch.setattr(ManageView, "request", property(forbidden), raising=False)
    data = instance.get_manage_access_trace(viewset, developer, mode="path", path="/missing/")
    assert data["trace"]["outcome"] == "no_such_route"
    assert data["trace"]["user"] == data["actor"]
    assert "crud_views.lib.access_trace" in (ROOT / "docs/reference/theme.md").read_text()


@pytest.mark.django_db
def test_guardian_selected_actor_preserves_strict_inherited_contract(
    client, cv_guardian_author, developer, django_user_model, monkeypatch
):
    from guardian.shortcuts import assign_perm

    from tests.test1.test_manage_requirements import grant

    actor = django_user_model.objects.create_user(username="release-selected")
    obj = cv_guardian_author.model.objects.create(first_name="one", last_name="private")
    cv_guardian_author.model.objects.create(first_name="two", last_name="private")
    grant(actor, cv_guardian_author, "view")
    assign_perm(cv_guardian_author.permissions["view"], actor, obj)
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", True)
    client.force_login(developer)
    url = reverse(cv_guardian_author.get_router_name("manage"))
    initial = client.get(url).context_data["manage_permissions"]
    response = client.get(url, {"cv_access_mode": "viewset", "cv_access_user": actor.pk})
    matrix = response.context_data["manage_permissions"]
    assert matrix["actor"]["id"] == actor.pk
    assert {k: v for k, v in matrix.items() if k != "actor"} == {k: v for k, v in initial.items() if k != "actor"}
    cell = next(cell for cell in matrix["actor"]["cells"] if cell["key"] == "view")
    assert cell["model"] is True and cell["object_count"] == 1
    assert response.wsgi_request.user.pk == developer.pk


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_shared_trace_partial_theme_recipe(request, fixture, client, developer, monkeypatch):
    viewset = request.getfixturevalue(fixture)
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", True)
    published = recipe(ROOT / "docs/reference/theme.md", "### Shared access trace partial")
    with _theme_templates({"crud_views/includes/access_trace.html": published}):
        client.force_login(developer)
        response = client.get(
            reverse(viewset.get_router_name("manage")),
            {"cv_access_mode": "path", "cv_access_user": developer.username, "cv_access_path": "/missing/"},
        )
    assert response.status_code == 200
    trace = html.fromstring(response.content).cssselect(".theme-access-trace")
    assert len(trace) == 1
    assert "/missing/" in trace[0].text_content() and "no_such_route" in trace[0].text_content()


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


@pytest.mark.django_db
def test_manage_checks_use_shared_alert_frame(client, cv_author, developer, settings):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"alert:warning": "project-checks-alert"}
    client.force_login(developer)
    response = client.get(reverse(cv_author.get_router_name("manage")))
    assert response.status_code == 200
    # The registered fixture's unlabeled AuthorContactView produces genuine scoped findings.
    assert response.context["manage_checks"]["messages"]
    issues = html.fromstring(response.content).get_element_by_id("cv-manage-checks-issues")
    frames = issues.xpath('.//*[@role="alert"]')
    assert len(frames) == 1
    (frame,) = frames
    assert "project-checks-alert" in frame.get("class").split()
    assert frame.xpath(".//h2")[0].text_content() == "Configuration issues"
    for message in response.context["manage_checks"]["messages"]:
        assert message["id"] in frame.text_content()
