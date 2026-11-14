"""Static Presentation declarations never execute context buttons or access machinery."""

import pytest
from django.contrib.auth.models import Group
from lxml import html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view.buttons import (
    ChildContextButton,
    ContextButton,
    FilterContextButton,
    ParentContextButton,
    SiblingContextButton,
)
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ParentViewSet
from tests.test1.app.models import Book
from tests.test1.test_manage_facts import make, register, restore_registry  # noqa: F401


def presentation(viewset):
    builder = getattr(ManageView(), "get_manage_presentation", None)
    assert callable(builder), "Presentation needs an explicit static request-free builder"
    return builder(viewset, None)


def entries(data):
    return {row["key"]: row for section in data["sections"] for row in section["entries"]}


def test_presentation_fields_and_counts():
    viewset = make(
        context_buttons=[],
        extends="",
        context_actions_inline=[],
        list_actions_inline=["detail"],
        card_actions_inline=(),
        context_actions_label_mode={},
        list_actions_label_mode={"detail": "label"},
        form_actions_label_mode={"submit": "both"},
        manage_view_class=None,
    )
    data = presentation(viewset)
    rows = entries(data)
    assert [s["key"] for s in data["sections"]] == ["context-buttons", "templates-and-actions", "label-modes", "other"]
    for key, expected in {
        "context_actions_inline": "[]",
        "list_actions_inline": "['detail']",
        "card_actions_inline": "()",
        "context_actions_label_mode": "{}",
        "list_actions_label_mode": "{'detail': 'label'}",
        "form_actions_label_mode": "{'submit': 'both'}",
    }.items():
        assert rows[key]["value"] == expected
        assert rows[key]["is_default"] is False
    assert rows["extends"]["value"] == repr(crud_views_settings.extends)
    assert rows["extends"]["declared_value"] == "''"
    assert rows["extends"]["is_default"] is False
    assert rows["extends"]["source"] == "CRUD_VIEWS_EXTENDS"
    assert rows["manage_view_class"]["value"] == "crud_views.lib.views.manage.ManageView"
    assert rows["manage_view_class"]["is_default"] is False
    all_rows = [r for s in data["sections"] for r in s["entries"]]
    assert data["default_count"] == sum(r["is_default"] for r in all_rows)
    assert data["set_count"] == sum(not r["is_default"] for r in all_rows)
    assert all(s["default_count"] == sum(r["is_default"] for r in s["entries"]) for s in data["sections"])
    assert rows["context_buttons"]["is_default"] is False


@pytest.mark.parametrize(
    "field",
    [
        "extends",
        "inaccessible_actions",
        "context_actions_inline",
        "list_actions_inline",
        "card_actions_inline",
        "context_actions_label_mode",
        "list_actions_label_mode",
        "form_actions_label_mode",
    ],
)
def test_setting_fallback_preserves_constructor_none(field):
    viewset = make(**{field: None})
    row = entries(presentation(viewset))[field]
    assert row["value"] == repr(getattr(crud_views_settings, field))
    assert row["source"] == "CRUD_VIEWS_" + field.upper()
    assert row["is_default"] is False


@pytest.mark.parametrize("core_setting", [None, "crud_views.lib.views.manage.ManageView"])
@pytest.mark.parametrize("guardian_setting", [None, "crud_views_guardian.lib.views.GuardianManageView"])
@pytest.mark.parametrize("explicit", [False, True])
def test_guardian_manage_class_source_uses_guardian_setting(monkeypatch, core_setting, guardian_setting, explicit):
    from crud_views_guardian.lib.views import GuardianManageView
    from crud_views_guardian.lib.viewset import GuardianViewSet
    from tests.test1.test_manage_provenance import make_viewset

    monkeypatch.setattr(crud_views_settings, "manage_view_class", core_setting)
    monkeypatch.setattr(crud_views_settings, "guardian_manage_view_class", guardian_setting)
    vs = make_viewset(
        GuardianViewSet,
        **({"manage_view_class": "crud_views_guardian.lib.views.GuardianManageView"} if explicit else {}),
    )
    row = entries(GuardianManageView().get_manage_presentation(vs, None))["manage_view_class"]
    assert row["source"] == (
        "set" if explicit else "CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS" if guardian_setting else "default"
    )
    assert row["value"] == "crud_views_guardian.lib.views.GuardianManageView"
    assert row["is_default"] is not explicit


def test_all_configuration_builders_ignore_ambient_request(monkeypatch):
    def poison(self):
        raise AssertionError("No ambient request in data builders")

    monkeypatch.setattr(ManageView, "request", property(poison), raising=False)
    viewset = make()
    register(viewset, cv_has_access=classmethod(lambda *args: pytest.fail("No access evaluation")))
    manage = ManageView()
    assert manage.get_manage_facts(viewset, None)
    assert manage.get_manage_hierarchy(viewset, None)["parents"] == []
    assert manage.get_manage_routes(viewset, None)
    assert manage.get_manage_ancestor_policy(viewset, None)["requests"] is None
    assert manage.get_manage_presentation(viewset, None)["sections"]


@pytest.mark.django_db
def test_five_static_target_kinds_and_missing_targets(django_assert_num_queries):
    root = make(prefix="presentation-root")
    register(root)
    child = make(Book, prefix="presentation-child", parent=ParentViewSet(name=root.name, attribute="publisher"))
    register(child)
    sibling = make(Book, prefix="presentation-sibling", parent=ParentViewSet(name=root.name, attribute="publisher"))
    register(sibling)
    root.context_buttons = [
        ContextButton(key="home", key_target="list"),
        ParentContextButton(key="parent", key_target="list"),
        ChildContextButton(key="child", child_name=child.name),
        FilterContextButton(),
        ContextButton(key="missing", key_target="absent"),
        ChildContextButton(key="missing-child", child_name="absent"),
    ]
    child.context_buttons = [
        ParentContextButton(key="parent", key_target="list"),
        SiblingContextButton(key="sibling", sibling_name=sibling.name, sibling_key="list"),
    ]
    with django_assert_num_queries(0):
        rows = entries(presentation(root))
        assert root.get_router_name("list") in rows["home"]["points_to"]
        assert "/presentation-root/" in rows["home"]["points_to"]
        assert rows["parent"]["points_to"] == "top level, never shown"
        assert child.get_router_name("list") in rows["child"]["points_to"]
        assert "toggles the list filter" in rows["filter"]["points_to"]
        assert root.context_buttons[3].template in rows["filter"]["points_to"]
        assert rows["missing"]["points_to"] == "Target unavailable; review this button's configuration."
        assert rows["missing-child"]["points_to"] == rows["missing"]["points_to"]
        rows = entries(presentation(child))
        assert root.get_router_name("list") in rows["parent"]["points_to"]
        assert sibling.get_router_name("list") in rows["sibling"]["points_to"]
        assert all(not row.get("url") for row in rows.values())


@pytest.mark.django_db
def test_custom_and_static_labels_never_render_or_query(django_assert_num_queries):
    class Custom(ContextButton):
        def get_context(self, context):
            raise AssertionError("must never render")

    class Rendering(ContextButton):
        def render_label(self, *args):
            raise AssertionError("must never render labels")

    class Inherited(ContextButton):
        pass

    viewset = make(
        context_buttons=[
            ContextButton(key="template", key_target="list", label_template="project/object.html"),
            ContextButton(
                key="code",
                key_target="list",
                label_template_code="{{ object.secret }} {{ view.request }} <script>" + "x" * 240,
            ),
            Inherited(key="inherited", key_target="list"),
            Custom(key="custom", key_target="list", template="project/custom.html"),
            Rendering(key="rendering", key_target="list"),
        ]
    )
    register(viewset)
    with django_assert_num_queries(0):
        rows = entries(presentation(viewset))
    assert rows["template"]["label"] == "Template: project/object.html"
    assert rows["code"]["label"].startswith("Inline template: ")
    assert "{{ object.secret }}" in rows["code"]["label"]
    assert rows["code"]["label"].endswith("…")
    assert len(rows["code"]["label"].removeprefix("Inline template: ")) == 201
    assert rows["inherited"]["label"] == "Target view label"
    assert "custom button:" in rows["custom"]["points_to"]
    assert "project/custom.html" in rows["custom"]["points_to"]
    assert rows["custom"]["label"] == rows["rendering"]["label"] == "Dynamic/custom label"
    assert "custom button:" in rows["rendering"]["points_to"]


@pytest.mark.django_db
def test_presentation_closed_counts_help_and_escaping(client, cv_author, django_user_model, monkeypatch):
    actor = django_user_model.objects.create_user(username="presentation-dev")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    client.force_login(actor)
    monkeypatch.setattr(
        cv_author,
        "context_buttons",
        [ContextButton(key="unsafe", key_target="list", label_template_code="{{ object.x }} <script>bad</script>")],
    )
    response = client.get("/author/manage/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    card = doc.get_element_by_id("cv-manage-presentation")
    assert card.tag == "details" and "open" not in card.attrib
    summary = card.find("summary")
    assert summary is not None and not summary.xpath(".//a | .//button | .//input")
    assert card.xpath("./a[contains(@href, '#presentation')]")
    assert "applies to all views" in summary.text_content()
    assert not card.cssselect("script")
    assert "<script>bad</script>" in card.text_content()
    data = response.context["manage_presentation"]
    assert len(card.cssselect("[data-cv-default-row]")) == data["default_count"]
    assert len(card.cssselect("[data-cv-config-row]")) == data["default_count"] + data["set_count"]
    assert all("hidden" not in row.attrib for row in card.cssselect("[data-cv-config-row]"))
    assert card.cssselect("a[href$='#templates-and-actions']") and card.cssselect("a[href$='#label-modes']")
    assert doc.get_element_by_id("cv-manage-views").getparent() is card.getparent()


@pytest.mark.django_db
def test_empty_context_buttons_visible_state(client, cv_author, django_user_model, monkeypatch):
    actor = django_user_model.objects.create_user(username="presentation-empty")
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    client.force_login(actor)
    monkeypatch.setattr(cv_author, "context_buttons", [])
    response = client.get("/author/manage/")
    card = html.fromstring(response.content).get_element_by_id("cv-manage-presentation")
    assert "No context buttons configured." in card.text_content()
