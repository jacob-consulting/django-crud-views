"""Requirement metadata describes gates without authorizing a request."""

import importlib

import pytest
from django import forms
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse
from lxml import html

from crud_views.lib import views as core
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView
from crud_views.lib.views import DetailView, DetailViewPermissionRequired
from crud_views.lib.views.form import (
    CustomFormNoObjectView,
    CustomFormNoObjectViewPermissionRequired,
    CustomFormView,
    CustomFormViewPermissionRequired,
)
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib import views as guardian_views
from crud_views_guardian.lib.viewset import STRICT_HELPER_POLICY, GuardianViewSet
from tests.test1.app.models import Author, Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import isolated_routes

GUARDIAN_CASES = [
    (guardian_views.GuardianDetailViewPermissionRequired, "view"),
    (guardian_views.GuardianUpdateViewPermissionRequired, "change"),
    (guardian_views.GuardianDeleteViewPermissionRequired, "delete"),
    (guardian_views.GuardianActionViewPermissionRequired, "change"),
    (guardian_views.GuardianListViewPermissionRequired, "view"),
    (guardian_views.GuardianCardListViewPermissionRequired, "view"),
    (guardian_views.GuardianCreateViewPermissionRequired, "add"),
]

CORE_CASES = [
    (core.ListView, None),
    (core.ListViewPermissionRequired, "view"),
    (core.CardListView, None),
    (core.CardListViewPermissionRequired, "view"),
    (core.DetailView, None),
    (core.DetailViewPermissionRequired, "view"),
    (core.CreateView, None),
    (core.CreateViewPermissionRequired, "add"),
    (core.UpdateView, None),
    (core.UpdateViewPermissionRequired, "change"),
    (core.DeleteView, None),
    (core.DeleteViewPermissionRequired, "delete"),
    (core.ActionView, None),
    (core.ActionViewPermissionRequired, "change"),
    (core.OrderedUpView, None),
    (core.OrderedUpViewPermissionRequired, "change"),
    (core.OrderedDownView, None),
    (core.OrderedUpDownPermissionRequired, "change"),
    (CustomFormView, None),
    (CustomFormViewPermissionRequired, "view"),
    (CustomFormNoObjectView, None),
    (CustomFormNoObjectViewPermissionRequired, "view"),
]


class ProjectManageBase(ManageView):
    pass


def register(base, viewset, key="tested", **attrs):
    return type(
        "Requirement" + base.__name__,
        (base,),
        {
            "__module__": __name__,
            "cv_viewset": viewset,
            "cv_key": key,
            "cv_path": key,
            "cv_context_actions": [],
            "cv_list_actions": [],
            "cv_home_key": None,
            "cv_header_template_code": "Requirement",
            "cv_paragraph_template_code": "",
            "cv_action_label_template_code": "Requirement",
            "cv_action_short_label_template_code": "Requirement",
            **attrs,
        },
    )


def grant(user, viewset, key):
    app, codename = viewset.permissions[key].split(".")
    user.user_permissions.add(Permission.objects.get(content_type__app_label=app, codename=codename))


@pytest.fixture
def developer(django_user_model):
    user = django_user_model.objects.create_user(username="requirement developer")
    user.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return user


@pytest.fixture
def simple_templates(settings):
    # Native handlers and form/collection/object work, with a minimal host template only.
    with override_settings(
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": False,
                "OPTIONS": {
                    "loaders": [
                        (
                            "django.template.loaders.locmem.Loader",
                            {
                                "requirement.html": (
                                    "{{ object }}{% for row in object_list %}{{ row }}{% endfor %}{{ form }}"
                                ),
                            },
                        ),
                        "django.template.loaders.app_directories.Loader",
                    ]
                },
            }
        ]
    ):
        yield


def test_requirement_contract_exists_without_viewset():
    describe = getattr(DetailView, "cv_get_requirement", None)
    assert callable(describe), "Views must describe their owning requirement without evaluating access"
    assert describe() == {"kind": "none", "value": None, "ancestor_applies": True}
    assert DetailViewPermissionRequired.cv_get_requirement() == {
        "kind": "permission",
        "value": "view",
        "ancestor_applies": True,
    }


@pytest.mark.django_db
@pytest.mark.parametrize("described", [False, True])
def test_guardian_parent_delegation_describes_intervening_custom_gate(client, django_user_model, described):
    from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin

    class CustomCreate(core.CreateViewPermissionRequired):
        def has_permission(self):
            return False

    if described:
        CustomCreate.cv_get_requirement = classmethod(
            lambda cls: {"kind": "group", "value": "project gate", "ancestor_applies": True}
        )

    def build(sfx):
        vs = GuardianViewSet(model=Author, name="delegated" + sfx)
        wrapped = type("WrappedCustomCreate", (GuardianParentPermissionMixin, CustomCreate), {})
        view = register(wrapped, vs, fields=["first_name", "last_name"])
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, view):
        actor = django_user_model.objects.create_user(username="delegated gate")
        grant(actor, vs, "add")
        client.force_login(actor)
        assert client.get(reverse(vs.get_router_name("tested"))).status_code == 403
        assert view.cv_get_requirement() == {
            "kind": "group" if described else "custom",
            "value": "project gate" if described else None,
            "ancestor_applies": True,
        }


@pytest.mark.django_db
@pytest.mark.parametrize("base,key", CORE_CASES, ids=[cls.__name__ for cls, _ in CORE_CASES])
def test_core_descriptions_match_native_requests(base, key, client, django_user_model, simple_templates):
    def build(sfx):
        vs = ViewSet(model=Author, name="req" + sfx)
        attrs = {"template_name": "requirement.html", "get_success_url": lambda self: "/"}
        if issubclass(base, (core.CreateView, core.UpdateView)):
            attrs["fields"] = ["first_name", "last_name"]
        if issubclass(base, (CustomFormView, CustomFormNoObjectView)):
            attrs["form_class"] = forms.Form
        if base in (core.ActionView, core.ActionViewPermissionRequired):
            attrs.update(action=lambda self, context: True, cv_action_messages=False)
        view = register(base, vs, **attrs)
        return (vs, view), [vs]

    with isolated_routes(build) as (vs, view):
        obj = Author.objects.create(first_name="Native", last_name="Gate")
        actor = django_user_model.objects.create_user(username="native")
        client.force_login(actor)
        requirement = view.cv_get_requirement()
        assert requirement == {"kind": "permission" if key else "none", "value": key, "ancestor_applies": True}
        kwargs = {vs.pk_name: obj.pk} if view.cv_object else {}
        url = reverse(vs.get_router_name("tested"), kwargs=kwargs)
        request = client.post if issubclass(base, core.ActionView) else client.get
        response = request(url)
        assert response.status_code == (403 if key else 302 if issubclass(base, core.ActionView) else 200)
        if key:
            grant(actor, vs, key)
            response = request(url)
            assert response.status_code == (302 if issubclass(base, core.ActionView) else 200)
        if issubclass(base, (core.ListView, core.CardListView)) and response.status_code == 200:
            assert list(response.context["object_list"]) == [obj]


@pytest.mark.django_db
def test_custom_owner_detection_and_explicit_description(monkeypatch, django_assert_num_queries):
    class ProjectGate:
        def has_permission(self):
            raise AssertionError("description must not authorize")

    class Custom(ProjectGate, DetailViewPermissionRequired):
        pass

    class Inherited(Custom):
        pass

    class Harmless(DetailViewPermissionRequired):
        pass

    class Described(Inherited):
        @classmethod
        def cv_get_requirement(cls):
            return {"kind": "group", "value": "Editors", "ancestor_applies": False}

    class OtherOverride(DetailViewPermissionRequired):
        def get_queryset(self):
            raise AssertionError("outside automatic ownership detection")

    with django_assert_num_queries(0):
        for cls in [Custom, Inherited]:
            assert cls.cv_get_requirement() == {"kind": "custom", "value": None, "ancestor_applies": True}
        assert Described.cv_get_requirement()["value"] == "Editors"
        for cls in [Harmless, OtherOverride]:
            assert cls.cv_get_requirement()["kind"] == "permission"
        assert ManageView.cv_get_requirement()["value"] == crud_views_settings.manage_group


@pytest.mark.django_db
def test_stock_summaries_routes_and_no_authorization(client, cv_author, developer, monkeypatch):
    client.force_login(developer)
    response = client.get("/author/manage/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    rows = response.context["manage_views"]
    routes = {r["key"]: r for r in ManageView().get_manage_routes(cv_author, developer)}
    for row in rows:
        node = doc.get_element_by_id("cv-view-" + row["key"])
        assert node.tag == "details" and "open" not in node.attrib
        summary = node.find("summary")
        assert not summary.xpath(".//a|.//button|.//input")
        assert doc.get_element_by_id(summary.get("aria-describedby")).text_content().strip()
        assert row["class_path"] in node.text_content()
        assert row["class_path"] in summary.text_content()
        assert row["route"] in summary.text_content()
        assert "CrudViewMetaClass" not in row["class_path"]
        assert row["parent_requirement"] is None
        assert row["route_name"] == routes[row["key"]]["name"]
        assert row["route"] == routes[row["key"]]["route"]
        assert row["route_error"] == routes[row["key"]]["route_error"]
    assert "AutoManageView" in next(r["class_path"] for r in rows if r["key"] == "manage")

    def forbidden(*args, **kwargs):
        raise AssertionError("descriptions must not authorize or load objects")

    for cls in cv_author.get_all_views().values():
        monkeypatch.setattr(cls, "has_permission", forbidden, raising=False)
        monkeypatch.setattr(cls, "cv_has_access", forbidden)
        monkeypatch.setattr(cls, "get_object", forbidden, raising=False)
        cls.cv_get_requirement()
    ManageView().get_manage_views(cv_author, developer)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "middle_none,all_none,nearest",
    [(False, False, "view"), (True, False, "view"), (True, True, "view"), (False, False, None)],
)
def test_nearest_enforced_ancestor(middle_none, all_none, nearest, developer):
    def build(sfx):
        grand = ViewSet(
            model=Publisher,
            name="reqgrand" + sfx,
            ancestor_policy=AncestorPolicy(provider="none" if all_none else "model"),
        )
        mid = ViewSet(
            model=Book,
            name="reqmid" + sfx,
            parent=ParentViewSet(name=grand.name, attribute="publisher"),
            ancestor_policy=AncestorPolicy(provider="none" if middle_none else "model"),
        )
        leaf = ViewSet(
            model=BookNote,
            name="reqleaf" + sfx,
            parent=ParentViewSet(name=mid.name, attribute="book"),
            ancestor_policy=AncestorPolicy(
                actions={
                    "tested": AncestorPermissions(nearest="view", higher="view").model_copy(update={"nearest": nearest})
                }
            ),
        )
        register(core.ActionViewPermissionRequired, leaf)
        return (grand, mid, leaf), []

    with isolated_routes(build) as (grand, mid, leaf):
        row = next(r for r in ManageView().get_manage_views(leaf, developer) if r["key"] == "tested")
        expected = (
            None
            if all_none or nearest is None
            else {"key": nearest, "permission": (grand if middle_none else mid).permissions[nearest]}
        )
        assert row["parent_requirement"] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("malformed", ["action", "own", "ancestor"])
def test_admitted_diagnostics_preserve_invalid_endpoint_failure(malformed, client, developer):
    def build(sfx):
        parent = ViewSet(model=Publisher, name="reqparent" + sfx)
        policy = AncestorPolicy(
            actions={}
            if malformed == "action"
            else {
                "tested": AncestorPermissions(nearest="missing" if malformed == "ancestor" else "view", higher="view")
            }
        )
        child = ViewSet(
            model=Book,
            name="reqchild" + sfx,
            parent=ParentViewSet(name=parent.name, attribute="publisher"),
            ancestor_policy=policy,
        )
        register(core.ActionViewPermissionRequired, child, cv_permission="missing" if malformed == "own" else "change")
        return (parent, child), [parent, child]

    with isolated_routes(build) as (parent, child):
        pub = Publisher.objects.create(name="Metadata")
        book = Book.objects.create(title="Metadata", publisher=pub)
        grant(developer, parent, "view")
        client.force_login(developer)
        kwargs = {parent.name + "_pk": pub.pk}
        response = client.get(reverse(child.get_router_name("manage"), kwargs=kwargs))
        assert response.status_code == 200
        row = next(r for r in response.context["manage_views"] if r["key"] == "tested")
        if malformed == "action":
            assert row["requirement_metadata_error"] == "Requirement unavailable; review system checks"
            assert row["parent_requirement"] is None and row["requirement"]["value"] == "change"
        elif malformed == "own":
            assert row["requirement_metadata_error"] == "Undeclared permission key: missing"
            assert row["requirement"]["value"] == "missing" and row["permission"] is None
            assert "undeclared: missing" in response.content.decode()
        else:
            assert row["requirement_metadata_error"] == "Undeclared ancestor permission key: missing"
            assert row["parent_requirement"] == {"key": "missing", "permission": None}
            assert "parent: missing (undeclared)" in response.content.decode()
        with pytest.raises((ImproperlyConfigured, AssertionError)):
            client.post(reverse(child.get_router_name("tested"), kwargs={**kwargs, child.pk_name: book.pk}))


@pytest.mark.django_db
def test_route_failures_and_empty_registry(cv_author, developer, monkeypatch):
    def invalid(self):
        raise ImproperlyConfigured("bad route metadata")

    monkeypatch.setattr(ViewSet, "urlpatterns", property(invalid))
    routes = ManageView().get_manage_routes(cv_author, developer)
    summaries = ManageView().get_manage_views(cv_author, developer)
    assert all(r["route"] is None and r["route_error"] == "Route unavailable; review system checks" for r in routes)
    assert [(r["route"], r["route_error"]) for r in routes] == [(r["route"], r["route_error"]) for r in summaries]
    monkeypatch.setattr(ViewSet, "get_all_views", lambda self: {})
    assert ManageView().get_manage_routes(cv_author, developer) == []
    assert ManageView().get_manage_views(cv_author, developer) == []


@pytest.mark.django_db
def test_redirect_child_description_matches_native_redirect(client, developer, simple_templates):
    def build(sfx):
        sfx = sfx.translate(str.maketrans("0123456789", "ghijklmnop"))
        parent = ViewSet(model=Publisher, name="reqredirect" + sfx)
        child = ViewSet(
            model=Book, name="reqbooks" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
        view = register(core.RedirectChildView, parent, cv_redirect=child.name, cv_redirect_key="list")
        register(core.ListView, child, "list", template_name="requirement.html")
        return (parent, child, view), [parent, child]

    with isolated_routes(build) as (parent, child, view):
        obj = Publisher.objects.create(name="Redirect")
        client.force_login(developer)
        assert view.cv_get_requirement() == {"kind": "none", "value": None, "ancestor_applies": True}
        url = reverse(
            parent.get_router_name("tested"),
            kwargs={parent.pk_name: obj.pk, "redirect": child.name, "redirect_key": "list"},
        )
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse(child.get_router_name("list"), kwargs={parent.name + "_pk": obj.pk})


@pytest.mark.django_db
def test_requirement_is_not_an_action_state_verdict(client, django_user_model, simple_templates):
    def build(sfx):
        vs = ViewSet(model=Author, name="reqstate" + sfx)
        cls = register(
            core.ActionViewPermissionRequired, vs, cv_action_enabled=classmethod(lambda cls, user, obj: False)
        )
        return (vs, cls), [vs]

    with isolated_routes(build) as (vs, cls):
        obj = Author.objects.create(first_name="Disabled", last_name="Action")
        user = django_user_model.objects.create_user(username="state")
        grant(user, vs, "change")
        client.force_login(user)
        assert cls.cv_get_requirement()["value"] == "change"
        assert client.post(reverse(vs.get_router_name("tested"), kwargs={vs.pk_name: obj.pk})).status_code == 403


@pytest.mark.django_db
def test_permission_map_and_auth_exceptions_propagate(cv_author, developer, monkeypatch):
    def broken(self):
        raise ImproperlyConfigured("auth map failure")

    monkeypatch.setattr(ViewSet, "permissions", property(broken))
    with pytest.raises(ImproperlyConfigured, match="auth map failure"):
        ManageView().get_manage_views(cv_author, developer)


def test_declared_key_does_not_read_permission_required(monkeypatch):
    def forbidden(self):
        raise AssertionError("cached authorization property was reached")

    monkeypatch.setattr(DetailViewPermissionRequired, "permission_required", property(forbidden))
    assert DetailViewPermissionRequired.cv_get_requirement()["value"] == "view"


def test_core_inventory_has_request_coverage():
    classes = set()
    for name in (
        "list",
        "card",
        "detail",
        "create",
        "update",
        "delete",
        "action",
        "action_ordered",
        "form",
        "child",
        "manage",
    ):
        module = importlib.import_module("crud_views.lib.views." + name)
        classes.update(
            value
            for value in vars(module).values()
            if isinstance(value, type) and value.__module__ == module.__name__ and issubclass(value, CrudView)
        )
    assert classes == {cls for cls, _ in CORE_CASES} | {core.RedirectChildView, ManageView}


@pytest.mark.django_db
def test_exact_custom_action_policy_matches_request(client, developer):
    def build(sfx):
        parent = ViewSet(model=Publisher, name="reqexact" + sfx)
        child = ViewSet(
            model=Book,
            name="reqaction" + sfx,
            parent=ParentViewSet(name=parent.name, attribute="publisher"),
            ancestor_policy=AncestorPolicy(actions={"tested": AncestorPermissions(nearest="change", higher="view")}),
        )
        register(
            core.ActionViewPermissionRequired,
            child,
            action=lambda self, context: True,
            cv_action_messages=False,
            get_success_url=lambda self: "/",
        )
        return (parent, child), [parent, child]

    with isolated_routes(build) as (parent, child):
        pub = Publisher.objects.create(name="Exact action")
        book = Book.objects.create(title="Exact action", publisher=pub)
        grant(developer, parent, "view")
        grant(developer, child, "change")
        client.force_login(developer)
        url = reverse(child.get_router_name("tested"), kwargs={parent.name + "_pk": pub.pk, child.pk_name: book.pk})
        row = next(r for r in ManageView().get_manage_views(child, developer) if r["key"] == "tested")
        assert row["parent_requirement"] == {"key": "change", "permission": "app.change_publisher"}
        assert client.post(url).status_code == 403
        grant(developer, parent, "change")
        assert client.post(url).status_code == 302


@pytest.mark.django_db
def test_configured_manage_base_keeps_actual_wrapper_identity(developer):
    def build(sfx):
        vs = ViewSet(model=Author, name="reqwrapper" + sfx, manage_view_class=__name__ + ".ProjectManageBase")
        return vs, []

    with isolated_routes(build) as vs:
        cls = vs.get_view_class("manage")
        assert cls.__bases__ == (ProjectManageBase,)
        row = ManageView().get_manage_views(vs, developer)[0]
        assert row["class_path"] == f"{cls.__module__}.{cls.__qualname__}"
        assert row["class_path"].endswith(".AutoManageView")
        assert row["requirement"]["kind"] == "group"


@pytest.mark.django_db
def test_inherited_custom_gate_requests_remain_authoritative(client, developer, simple_templates):
    class ProjectGate:
        def has_permission(self):
            return self.request.user.groups.filter(name="Custom readers").exists()

    class ProjectDetail(ProjectGate, core.DetailViewPermissionRequired):
        pass

    def build(sfx):
        vs = ViewSet(model=Author, name="reqcustom" + sfx)
        cls = register(ProjectDetail, vs, template_name="requirement.html")
        return (vs, cls), [vs]

    with isolated_routes(build) as (vs, cls):
        author = Author.objects.create(first_name="Custom", last_name="Gate")
        grant(developer, vs, "view")
        client.force_login(developer)
        url = reverse(vs.get_router_name("tested"), kwargs={vs.pk_name: author.pk})
        assert cls.cv_get_requirement()["kind"] == "custom"
        assert client.get(url).status_code == 403
        developer.groups.add(Group.objects.create(name="Custom readers"))
        assert client.get(url).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("base,key", GUARDIAN_CASES, ids=[cls.__name__ for cls, _ in GUARDIAN_CASES])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("grant_kind", ["direct", "group", "global"])
def test_guardian_descriptions_match_requests(base, key, nested, grant_kind, client, developer, simple_templates):
    from guardian.shortcuts import assign_perm

    def build(sfx):
        parent = GuardianViewSet(model=Publisher, name="reqgp" + sfx)
        vs = GuardianViewSet(
            model=Book,
            name="reqgc" + sfx,
            parent=ParentViewSet(name=parent.name, attribute="publisher") if nested else None,
            ancestor_policy=AncestorPolicy(
                actions={"tested": AncestorPermissions(nearest="change", higher="view")}
                if nested and issubclass(base, core.ActionView)
                else {}
            ),
        )
        attrs = {"template_name": "requirement.html", "get_success_url": lambda self: "/"}
        if issubclass(base, (core.CreateView, core.UpdateView)):
            attrs["fields"] = ["title"]
        if issubclass(base, core.ActionView):
            attrs.update(action=lambda self, context: True, cv_action_messages=False)
        cls = register(base, vs, **attrs)
        return (parent, vs, cls), [parent, vs]

    with isolated_routes(build) as (parent, vs, cls):
        pub = Publisher.objects.create(name="Requirement parent")
        obj = Book.objects.create(title="Requirement object", publisher=pub)
        creating = issubclass(base, core.CreateView)
        listing = issubclass(base, (core.ListView, core.CardListView))
        own = None if nested and creating else key
        assert cls.cv_get_requirement() == {
            "kind": "permission" if own else "none",
            "value": own,
            "ancestor_applies": True,
        }
        manage = guardian_views.GuardianManageView()
        row = next(r for r in manage.get_manage_views(vs, developer) if r["key"] == "tested")
        assert row["requirement"]["value"] == own
        assert row["guardian_policy"]["effective_policy"] == ("not applicable" if creating else "strict")
        if nested:
            parent_key = "view" if key == "view" else "change"
            assert row["parent_requirement"] == {"key": parent_key, "permission": parent.permissions[parent_key]}
        else:
            assert row["parent_requirement"] is None
        kwargs = {parent.name + "_pk": pub.pk} if nested else {}
        if cls.cv_object:
            kwargs[vs.pk_name] = obj.pk
        url = reverse(vs.get_router_name("tested"), kwargs=kwargs)
        request = client.post if issubclass(base, core.ActionView) else client.get
        client.force_login(developer)
        response = request(url)
        assert response.status_code == (200 if listing and not nested else 403)
        if listing and not nested:
            assert list(response.context["object_list"]) == []
        if nested:
            assign_perm(parent.permissions[parent_key], developer, pub)
            response = request(url)
            assert response.status_code == (200 if listing or creating else 403)
            if listing:
                assert list(response.context["object_list"]) == []
        if own:
            if creating or grant_kind == "global":
                grant(developer, vs, key)
            else:
                holder = developer
                if grant_kind == "group":
                    holder = Group.objects.create(name="Requirement object readers")
                    developer.groups.add(holder)
                assign_perm(vs.permissions[key], holder, obj)
        response = request(url)
        allowed = creating or grant_kind != "global"
        assert response.status_code == (
            200 if listing else 302 if allowed and issubclass(base, core.ActionView) else 200 if allowed else 403
        )
        if listing:
            assert list(response.context["object_list"]) == ([obj] if allowed else [])
        if not creating:
            cls.cv_guardian_accept_global_perms = True
            row = next(r for r in manage.get_manage_views(vs, developer) if r["key"] == "tested")
            assert row["guardian_policy"]["effective_policy"] == "global fallback"
            response = request(url)
            assert response.status_code == (302 if issubclass(base, core.ActionView) else 200)
            if listing:
                assert list(response.context["object_list"]) == [obj]
        assert manage.get_manage_guardian(vs, developer) == {"get_objects_for_user": STRICT_HELPER_POLICY}
        developer.is_active = False
        developer.save()
        # Test the actual dispatch with an inactive authenticated actor; Django login middleware otherwise logs out.
        from django.core.exceptions import PermissionDenied
        from django.test import RequestFactory

        req = RequestFactory().get(url)
        req.user = developer
        with pytest.raises(PermissionDenied):
            cls.as_view()(req, **kwargs)


def test_guardian_inventory_has_request_coverage():
    classes = {
        value
        for value in vars(guardian_views).values()
        if isinstance(value, type) and value.__module__ == guardian_views.__name__ and issubclass(value, CrudView)
    }
    # GuardianManageView shares the full request admission matrix in test_manage_group.py.
    assert classes == {cls for cls, _ in GUARDIAN_CASES} | {guardian_views.GuardianManageView}


@pytest.mark.django_db
def test_guardian_none_provider_parent_and_custom_gate(developer):
    def build(sfx):
        parent = GuardianViewSet(
            model=Publisher, name="reqnonep" + sfx, ancestor_policy=AncestorPolicy(provider="none")
        )
        vs = GuardianViewSet(
            model=Book, name="reqnonec" + sfx, parent=ParentViewSet(name=parent.name, attribute="publisher")
        )
        cls = register(guardian_views.GuardianCreateViewPermissionRequired, vs)
        return (vs, cls), []

    with isolated_routes(build) as (vs, cls):
        row = next(
            r for r in guardian_views.GuardianManageView().get_manage_views(vs, developer) if r["key"] == "tested"
        )
        assert row["requirement"]["kind"] == "none"
        assert row["parent_requirement"] is None

        class Custom(cls):
            def has_permission(self):
                return False

        assert Custom.cv_get_requirement()["kind"] == "custom"
