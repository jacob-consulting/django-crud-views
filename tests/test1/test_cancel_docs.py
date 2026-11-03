"""Execute the published cancellation recipes against real view instances and responses."""

import ast
import inspect
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from django.template import Context, Template
from lxml import html

from tests.test1.test_cancel_navigation import emitted_link
from tests.test1.test_cancel_rendering import assert_owner, rendered_cancel

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference/update_view.md"


def recipe(name):
    return re.search(rf"<!-- cancel-recipe: {name} -->\n```\w+\n(.*?)\n```", REFERENCE.read_text(), re.S)[1]


def python_recipe(name):
    namespace = {}
    exec(compile(recipe(name), str(REFERENCE), "exec"), namespace)
    return namespace


@pytest.mark.django_db
@pytest.mark.parametrize("outcome", ["origin", "fallback", "omitted"])
@pytest.mark.parametrize("tag", ["button", "a"])
def test_guarded_template_matches_stock(
    client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch, settings, outcome, tag
):
    settings.CRUD_VIEWS_BUTTON_CLASSES = {"form:cancel-tag": tag}
    target = cv_author_origin.get_view_class("update")
    monkeypatch.setattr(target, "cv_cancel_keys", "auto")
    source = client_user_author_origin.get("/author_origin/?x=&x=%3Cscript%3E%26%22%27")
    link = emitted_link(source, f"/author_origin/{author_douglas_adams.pk}/update/")
    if outcome != "origin":
        monkeypatch.setattr(
            cv_author_origin.get_view_class("list"), "cv_has_access", classmethod(lambda cls, user, obj=None: False)
        )
    if outcome == "omitted":
        monkeypatch.setattr(
            cv_author_origin.get_view_class("card"), "cv_has_access", classmethod(lambda cls, user, obj=None: False)
        )
    response = client_user_author_origin.get(link)
    assert response.status_code == 200
    result = Template(recipe("guarded-template")).render(
        Context({"view": response.context["view"], "request": response.wsgi_request})
    )
    nodes = html.fragment_fromstring(result, create_parent=True).xpath(".//a")
    if outcome == "omitted":
        assert not nodes
        assert not html.fromstring(response.content).xpath("//form//*[@id='button-id-reset']")
    else:
        (node,) = nodes
        assert node.get("href") == rendered_cancel(response)
        if outcome == "origin":
            assert parse_qs(urlsplit(node.get("href")).query, keep_blank_values=True)["x"] == ["", "<script>&\"'"]
            assert "&amp;" in result
            assert "<script>" not in result
        else:
            assert node.get("href") == "/author_origin/card/"
    assert_owner(response)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mixin", "expected"),
    [("StaticCancelMixin", "list"), ("CurrentViewCancelMixin", "update"), ("CustomOriginCancelMixin", "contact")],
)
def test_configuration_recipes(client_user_author_origin, author_douglas_adams, mixin, expected):
    response = client_user_author_origin.get(f"/author_origin/{author_douglas_adams.pk}/update/?cv_from=contact")
    view = response.context["view"]
    config = python_recipe("configuration")[mixin]
    view.cv_cancel_key, view.cv_cancel_keys = config.cv_cancel_key, config.cv_cancel_keys
    assert view.cv_get_cancel_url() == view.cv_get_url(expected, view.object)


@pytest.mark.django_db
@pytest.mark.parametrize("allowed", [False, True])
@pytest.mark.parametrize("key", ["create", "delete"])
def test_custom_actions_recipe(
    client_user_author_origin, cv_author_origin, author_douglas_adams, monkeypatch, allowed, key
):
    target = cv_author_origin.get_view_class(key)
    recipe_name, mixin_name = (
        ("actions", "CancelAwareActionsMixin") if key == "create" else ("delete-helper", "CancelAwareDeleteHelperMixin")
    )
    mixin = python_recipe(recipe_name)[mixin_name]
    monkeypatch.setattr(target, "form_class", type("DocumentedForm", (mixin, target.form_class), {}))
    for destination in ("list", "card"):
        monkeypatch.setattr(
            cv_author_origin.get_view_class(destination),
            "cv_has_access",
            classmethod(lambda cls, user, obj=None: allowed),
        )
    path = "/author_origin/create/" if key == "create" else f"/author_origin/{author_douglas_adams.pk}/delete/"
    response = client_user_author_origin.get(path)
    assert response.status_code == 200
    assert type(response.context["view"]) is target
    assert type(response.context["form"]) is target.form_class
    assert_owner(response)
    nodes = html.fromstring(response.content).xpath("//form//*[@id='button-id-reset']")
    assert bool(nodes) is allowed


def test_migration_pair_and_current_recipe():
    migration = (ROOT / "docs/migrating-1.0.md").read_text()
    changelog = (ROOT / "CHANGELOG.md").read_text().split("### Breaking", 1)[1].split("### ", 1)[0]
    assert "docs/migrating-1.0.md#dynamic-cancel-navigation" in changelog
    assert recipe("guarded-template") in migration
    old = "{% cv_context_url view.cv_get_cancel_key as url %}"
    before = migration.split("**Before — unsupported key-only Cancel integration:**", 1)[1].split("**After", 1)[0]
    assert old in before
    for path in (ROOT / "docs").rglob("*.md"):
        if path.name != "migrating-1.0.md":
            assert old not in path.read_text(), path


def test_documented_transport_limits_and_parameters(monkeypatch):
    from crud_views.lib.view import cancel

    settings_doc = (ROOT / "docs/reference/settings.md").read_text()
    for value in (cancel.MAX_TOKEN, cancel.MAX_JSON, cancel.MAX_QUERY, cancel.MAX_PAIRS):
        assert f"{value:,}" in settings_doc
    assert cancel.navigation_params() == ("cv_from", "cv_from_cancel", "cv_from_restore")
    monkeypatch.setattr(cancel.crud_views_settings, "origin_param", "back")
    assert cancel.navigation_params() == ("back", "back_cancel", "back_restore")
    for term in ("query=null", 'query=""', "SECRET_KEY_FALLBACKS", "414/400", "do not encrypt"):
        assert term in settings_doc


def test_public_surface_and_synchronized_example(cv_author, monkeypatch):
    from crud_views.lib.view.base import CrudView
    from crud_views.templatetags import crud_views as tags
    from tests.test1.test_cancel_origin import check_ids

    signature = inspect.signature(CrudView.cv_get_cancel_url)
    assert list(signature.parameters) == ["self", "obj", "user", "request"]
    assert all(signature.parameters[name].default is None for name in ("obj", "user", "request"))
    tag_signature = inspect.signature(tags.cv_cancel_url)
    assert list(tag_signature.parameters) == ["context", "obj"]
    assert tag_signature.parameters["obj"].default is None
    assert "cv_cancel_url" in tags.register.tags
    target = cv_author.get_view_class("update")
    assert target.cv_cancel_keys == "auto"
    monkeypatch.setattr(target, "cv_cancel_key", "missing")
    monkeypatch.setattr(target, "cv_cancel_keys", None)
    ids = check_ids(target)
    assert "viewset.E256" in ids
    assert "viewset.E255" not in ids
    source = (ROOT / "examples/bootstrap5/library/views.py").read_text()
    tree = ast.parse(source)
    (update,) = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AuthorUpdateView"]
    assignments = {
        assignment.targets[0].id: assignment.value for assignment in update.body if isinstance(assignment, ast.Assign)
    }
    assert "cv_cancel_keys" not in assignments
    assert ast.literal_eval(assignments["cv_success_keys"]) == ["list", "detail"]
    for path in (REFERENCE, ROOT / "docs/faq.md"):
        (block,) = re.findall(r"<!-- cv-sync: library/views.py -->\n```python\n(.*?)\n```", path.read_text(), re.S)
        assert block in source
