"""Real bilingual Resource pages load shipped catalogs and retain diagnostic facts."""

import json
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group, Permission
from django.test import override_settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import trans_real
from lxml import html

from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_access_trace_command import invoke
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_manage_locales import RESOURCE_MESSAGES

pytestmark = pytest.mark.django_db
LEGEND = next(message for message in RESOURCE_MESSAGES if message.startswith("resource:"))
RESTRICTIONS = next(message for message in RESOURCE_MESSAGES if message.startswith("Developer-group"))


@pytest.fixture
def localized_resource(request, monkeypatch, django_user_model, client):
    """All Resource classes, holders and route registrations are local to this fixture."""
    options = getattr(request, "param", {})
    mapping = options.get("mapping", "mapped")
    declared = options.get("declared", False)
    nested = options.get("nested", False)
    monkeypatch.setattr(trans_real, "_translations", {})
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")
    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    monkeypatch.setattr(crud_views_settings, "manage_access_trace", True)
    state = SimpleNamespace(explicit=False, broken=False, reads=[])

    class LocaleItem(Resource):
        key: str

        class Meta:
            app_label = "locale_storage"
            pk_field = "key"
            verbose_name = "<script>metadata</script>"
            verbose_name_plural = "localized items"
            ordering = "key"

        @classmethod
        def cv_get_items(cls, request, **kwargs):
            assert state.explicit, "An idle manage page must not list Resources"
            state.reads.append(("list", request.user.pk))
            if state.broken:
                raise ValueError("<script>external error & detail</script>")
            return [cls(key="one")]

        @classmethod
        def cv_get_item(cls, request, pk, **kwargs):
            assert state.explicit, "An idle manage page must not fetch a Resource"
            state.reads.append(("item", request.user.pk))
            return super().cv_get_item(request, pk, **kwargs)

    developer = django_user_model.objects.create_user(username="<script>developer</script>")
    developer.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    actor = django_user_model.objects.create_user(username="<script>selected</script>")
    permission = Permission.objects.get(content_type__app_label="app", codename="view_author")
    group = Group.objects.create(name="<script>group</script>")
    group.permissions.add(permission)
    developer.groups.add(group)
    actor.groups.add(group)
    holders = []
    if mapping == "mapped":
        for index in range(21):
            user = django_user_model.objects.create_user(username=f"holder {index:02} <script>name</script>")
            user.user_permissions.add(permission)
            holders.append(user)

    def build(suffix):
        parents, coords = [], {}
        if nested:
            parent = ViewSet(model=Publisher, name="localeparent" + suffix)
            obj = Publisher.objects.create(name="locale parent")
            parents.append(parent)
            coords[parent.name + "_pk"] = obj.pk
            parent_permission = Permission.objects.get(content_type__app_label="app", codename="view_publisher")
            for user in (developer, actor):
                user.user_permissions.add(parent_permission)
        kwargs = {}
        if mapping != "omitted":
            kwargs["resource_permissions"] = {"view": "app.view_author"} if mapping == "mapped" else mapping
        if declared:
            kwargs.update(verbose_name="<script>declared</script>", ordering="")
        vs = ViewSet(
            model=LocaleItem,
            name="localeresource" + suffix,
            parent=ParentViewSet(name=parents[0].name) if parents else None,
            **kwargs,
        )
        if mapping == "mapped":
            for base, key in [(ListViewPermissionRequired, "list"), (DetailViewPermissionRequired, "detail")]:
                type(
                    "Localized" + key.title(),
                    (ResourceViewMixin, base),
                    {"__module__": __name__, "cv_viewset": vs, "cv_key": key, "cv_list_display": ["key"]},
                )
        return SimpleNamespace(vs=vs, parents=parents, coords=coords), [*parents, vs]

    with isolated_routes(build) as env:
        env.path = reverse(env.vs.get_router_name("manage"), kwargs=env.coords)
        env.actor, env.developer, env.state = actor, developer, state
        env.mapping, env.declared, env.holders = mapping, declared, holders
        client.force_login(developer)
        yield env


@pytest.mark.parametrize(
    "localized_resource",
    [
        {"mapping": mapping, "declared": declared, "nested": nested}
        for mapping in ("mapped", None, {}, "omitted")
        for declared, nested in ((False, False), (True, True))
    ],
    indirect=True,
)
@pytest.mark.parametrize("classes", [None, "locale-resource", ""])
def test_resource_manage_localized_render(client, localized_resource, classes):
    env = localized_resource
    badges_by_language = {}
    for language in ("en", "de"):
        labels = RESOURCE_MESSAGES if language == "de" else {key: key for key in RESOURCE_MESSAGES}
        overrides = {} if classes is None else {"manage:badge-resource": classes}
        with translation.override(language), override_settings(CRUD_VIEWS_BUTTON_CLASSES=overrides):
            response = client.get(env.path)
        assert response.status_code == 200 and not env.state.reads
        root = html.fromstring(response.content)
        identity = root.get_element_by_id("cv-manage-viewset")
        assert labels["Resource"] in identity.text_content()
        assert labels["Resource metadata"] in identity.text_content()
        assert "<script>" not in response.content.decode()
        facts = {row["key"]: row for row in response.context["manage_facts"]}
        for key in ("app_label", "pk_field", "pk_type", "verbose_name", "ordering"):
            row = identity.xpath(f".//tr[th='{key}']")[0]
            expected_default = not (env.declared and key in {"verbose_name", "ordering"})
            assert facts[key]["is_default"] is expected_default
            assert facts[key]["source"] == (
                ("gesetzt" if language == "de" else "set") if not expected_default else labels["Resource metadata"]
            )
            assert facts[key]["source"] in row.text_content()
        presentation = root.get_element_by_id("cv-manage-presentation")
        mapping_row = presentation.xpath(".//tr[th='resource_permissions']")[0]
        assert ("data-cv-default-row" in mapping_row.attrib) is (env.mapping == "omitted")
        assert ("Standardwerte anzeigen" if language == "de" else "Show defaults") in root.text_content()
        if env.parents:
            expected_url = reverse(env.parents[0].get_router_name("manage"))
            assert expected_url in root.get_element_by_id("cv-manage-hierarchy").xpath(".//a/@href")
        card = root.get_element_by_id("cv-manage-permissions")
        assert labels[LEGEND] in card.text_content()
        if env.mapping == "mapped":
            matrix = response.context["manage_permissions"]
            assert len(matrix["users"]) == 20 and len(matrix["users_overflow"]) == 1
            class_lists = []
            for site in ("actor", "groups", "users", "users-overflow"):
                badges = card.cssselect(f"[data-manage-{site}] [data-permission=view] span")
                assert badges and all(badge.text == labels["resource"] for badge in badges)
                class_lists.extend(badge.get("class") for badge in badges)
            assert set(class_lists) == {"badge bg-info text-dark" if classes is None else classes}
            badges_by_language[language] = class_lists
            for value in (env.developer.username, "<script>group</script>", env.holders[-1].username):
                assert value in card.text_content()
            assert not card.cssselect("script")
        else:
            assert labels["No Resource permissions declared"] in card.text_content()
            assert labels[RESTRICTIONS] in card.text_content()
            assert not card.cssselect("table, [data-permission]")
    if env.mapping == "mapped":
        assert badges_by_language["en"] == badges_by_language["de"]


def stable(value):
    """Compare the entire schema while excluding only translated human prose."""
    if isinstance(value, dict):
        return {key: None if key in {"message", "untraced"} else stable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


@pytest.mark.parametrize("localized_resource", [{}, {"nested": True}], indirect=True)
@pytest.mark.parametrize("mode", ["path", "viewset"])
@pytest.mark.parametrize("broken", [False, True])
def test_resource_manage_localized_trace_parity(client, localized_resource, mode, broken):
    env = localized_resource
    env.state.explicit = True
    env.state.broken = broken
    documents = {}
    path = reverse(env.vs.get_router_name("list"), kwargs=env.coords)
    for language in ("en", "de"):
        with translation.override(language):
            response = client.get(
                env.path,
                {
                    "cv_access_mode": mode,
                    "cv_access_user": env.actor.username,
                    "cv_access_pk": "one",
                    "cv_access_path": path,
                },
            )
            assert response.status_code == 200
            assert response.wsgi_request.user.pk == env.developer.pk
            data = response.context["manage_access_trace"]
            root = html.fromstring(response.content)
            assert not root.cssselect("script")
            rows = data["rows"] if mode == "viewset" else [{"key": "path", "path": path, "trace": data["trace"]}]
            if mode == "viewset":
                assert [row["key"] for row in rows] == list(env.vs.get_all_views())
            documents[language] = []
            for row in rows:
                trace = row["trace"]
                assert trace is not None
                code, stdout, stderr = invoke(row["path"], env.actor.username, "--as-json", "--no-color")
                assert stderr == "" and json.loads(stdout) == trace
                expected = "denied" if row["key"] == "manage" else "error" if broken else "allowed"
                assert trace["outcome"] == expected
                assert code == {"allowed": 0, "denied": 1, "error": 2}[expected]
                _, text, stderr = invoke(row["path"], env.actor.username, "--no-color")
                assert stderr == ""
                panel = (
                    root.cssselect(f'[data-cv-access-row="{row["key"]}"]')[0]
                    if mode == "viewset"
                    else root.get_element_by_id("cv-manage-access-trace")
                ).text_content()
                for notice in trace["untraced"]:
                    assert notice in panel and notice in text
                for step in trace["steps"]:
                    for field in ("message", "provider", "permission"):
                        if step.get(field):
                            assert step[field] in panel and step[field] in text
                    if step.get("exception"):
                        for value in step["exception"].values():
                            assert value in panel and value in text
                if expected == "error":
                    assert "&lt;script&gt;external error &amp; detail&lt;/script&gt;" in response.content.decode()
                documents[language].append(trace)
            assert all(actor == env.actor.pk for _, actor in env.state.reads)
    assert stable(documents["en"]) == stable(documents["de"])
