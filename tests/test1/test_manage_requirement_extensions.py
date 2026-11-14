"""Every shipped inherited extension description is paired with a native request."""

import importlib

import pytest
from django.contrib.contenttypes.models import ContentType
from django.forms import modelform_factory
from django.urls import reverse

from crud_views.lib.ancestors import _operation_family
from crud_views.lib.crispy import CrispyViewMixin
from crud_views.lib.view import CrudView
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_object_detail.lib.views import ObjectDetailView, ObjectDetailViewPermissionRequired
from crud_views_polymorphic import lib as poly
from crud_views_workflow.lib.views import WorkflowView, WorkflowViewPermissionRequired
from tests.test1 import test_manage_requirements as requirements
from tests.test1.app.models import Author, Campaign, Car, Vehicle, WorkflowRequest
from tests.test1.app.views import CampaignWorkflowForm, WorkflowRequestWorkflowForm
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_manage_requirements import grant, register

developer = requirements.developer
simple_templates = requirements.simple_templates

pytestmark = pytest.mark.django_db

EXTENSION_CASES = [
    (ObjectDetailView, None, Author),
    (ObjectDetailViewPermissionRequired, "view", Author),
    (WorkflowView, None, Campaign),
    (WorkflowViewPermissionRequired, "change", Campaign),
    (poly.PolymorphicCreateSelectView, None, Vehicle),
    (poly.PolymorphicCreateSelectViewPermissionRequired, "add", Vehicle),
    (poly.PolymorphicCreateView, None, Vehicle),
    (poly.PolymorphicCreateViewPermissionRequired, "add", Vehicle),
    (poly.PolymorphicDetailView, None, Vehicle),
    (poly.PolymorphicDetailViewPermissionRequired, "view", Vehicle),
    (poly.PolymorphicUpdateView, None, Vehicle),
    (poly.PolymorphicUpdateViewPermissionRequired, "change", Vehicle),
    (poly.PolymorphicDeleteView, None, Vehicle),
    (poly.PolymorphicDeleteViewPermissionRequired, "delete", Vehicle),
]


def test_extension_inventory_has_request_coverage():
    classes = set()
    modules = ["crud_views_object_detail.lib.views", "crud_views_workflow.lib.views"]
    modules.extend(
        "crud_views_polymorphic.lib." + name for name in ("create_select", "create", "detail", "update", "delete")
    )
    for name in modules:
        module = importlib.import_module(name)
        classes.update(
            cls
            for cls in vars(module).values()
            if isinstance(cls, type) and cls.__module__ == module.__name__ and issubclass(cls, CrudView)
        )
    assert classes == {cls for cls, _, _ in EXTENSION_CASES}


@pytest.mark.parametrize("base,key,model", EXTENSION_CASES, ids=[cls.__name__ for cls, _, _ in EXTENSION_CASES])
def test_extension_description_matches_native_request(base, key, model, client, django_user_model, simple_templates):
    def build(sfx):
        vs = ViewSet(model=model, name="reqext" + sfx)
        attrs = {"template_name": "requirement.html", "get_success_url": lambda self: "/"}
        configured = base
        if issubclass(base, WorkflowView):
            configured = type("CrispyWorkflow", (CrispyViewMixin, base), {})
            attrs["form_class"] = CampaignWorkflowForm
        if issubclass(base, (poly.PolymorphicCreateView, poly.PolymorphicUpdateView)):
            attrs["polymorphic_forms"] = {Car: modelform_factory(Car, fields=["name", "doors"])}
        if issubclass(base, poly.PolymorphicCreateSelectView):
            register(
                poly.PolymorphicCreateView,
                vs,
                "create",
                template_name="requirement.html",
                polymorphic_forms={Car: modelform_factory(Car, fields=["name", "doors"])},
            )
        cls = register(configured, vs, **attrs)
        return (vs, cls), [vs]

    with isolated_routes(build) as (vs, cls):
        if model is Author:
            obj = Author.objects.create(first_name="Rich", last_name="Detail")
        elif model is Campaign:
            obj = Campaign.objects.create(name="Workflow")
        else:
            obj = Car.objects.create(name="Polymorphic", doors=4)
        user = django_user_model.objects.create_user(username="extension")
        client.force_login(user)
        assert cls.cv_get_requirement() == {
            "kind": "permission" if key else "none",
            "value": key,
            "ancestor_applies": True,
        }
        kwargs = {vs.pk_name: obj.pk} if cls.cv_object else {}
        if issubclass(base, poly.PolymorphicCreateView):
            kwargs["polymorphic_ctype_id"] = ContentType.objects.get_for_model(Car).pk
        url = reverse(vs.get_router_name("tested"), kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == (403 if key else 200)
        if key:
            grant(user, vs, key)
            response = client.get(url)
            assert response.status_code == 200
        if issubclass(base, poly.PolymorphicCreateSelectView):
            content_type = ContentType.objects.get_for_model(Car).pk
            choices = response.context["form"].fields["polymorphic_ctype_id"].choices
            assert content_type in [value for value, _ in choices]
            selected = client.post(url, {"polymorphic_ctype_id": content_type})
            assert selected.status_code == 302
            assert selected.url == reverse(vs.get_router_name("create"), kwargs={"polymorphic_ctype_id": content_type})
            assert client.get(selected.url).status_code == 200
        elif issubclass(base, WorkflowView):
            invalid = client.post(url, {"transition": "wf_done", "comment": ""})
            assert invalid.status_code == 200
            assert invalid.context["form"].errors["transition"]
            obj.refresh_from_db()
            assert obj.state == "new"
        elif cls.cv_object:
            assert response.context["object"].pk == obj.pk


@pytest.mark.parametrize("base", [WorkflowView, WorkflowViewPermissionRequired])
def test_workflow_model_gate_is_separate_from_transition_permission(base, client, django_user_model, simple_templates):
    def build(sfx):
        vs = ViewSet(model=WorkflowRequest, name="reqworkflow" + sfx)
        configured = type("CrispyRequestWorkflow", (CrispyViewMixin, base), {})
        cls = register(
            configured,
            vs,
            form_class=WorkflowRequestWorkflowForm,
            template_name="requirement.html",
            get_success_url=lambda self: "/",
        )
        return (vs, cls), [vs]

    with isolated_routes(build) as (vs, cls):
        obj = WorkflowRequest.objects.create(name="Transition policy")
        user = django_user_model.objects.create_user(username="workflow")
        grant(user, vs, "change")
        client.force_login(user)
        url = reverse(vs.get_router_name("tested"), kwargs={vs.pk_name: obj.pk})
        description = cls.cv_get_requirement()
        response = client.get(url)
        assert response.status_code == 200
        assert "wf_process" not in [key for key, _ in response.context["form"].fields["transition"].choices]
        assert client.post(url, {"transition": "wf_process", "comment": ""}).status_code == 200
        obj.refresh_from_db()
        assert obj.state == "new"
        grant(user, vs, "process")
        assert cls.cv_get_requirement() == description
        assert client.post(url, {"transition": "wf_process", "comment": ""}).status_code == 302
        obj.refresh_from_db()
        assert obj.state == "processed"


@pytest.mark.parametrize(
    "base,key", [(poly.PolymorphicCreateSelectView, None), (poly.PolymorphicCreateSelectViewPermissionRequired, "add")]
)
def test_polymorphic_selector_keeps_write_ancestor_gate(base, key, client, developer, simple_templates):
    def build(sfx):
        parent = ViewSet(model=Car, name="reqcar" + sfx)
        vs = ViewSet(model=Vehicle, name="reqvehicle" + sfx, parent=ParentViewSet(name=parent.name, attribute="car"))
        cls = register(base, vs, template_name="requirement.html")
        register(
            poly.PolymorphicCreateView,
            vs,
            "create",
            template_name="requirement.html",
            polymorphic_forms={Car: modelform_factory(Car, fields=["name", "doors"])},
        )
        return (parent, vs, cls), [parent, vs]

    with isolated_routes(build) as (parent, vs, cls):
        obj = Car.objects.create(name="Ancestor", doors=2)
        grant(developer, parent, "view")
        if key:
            grant(developer, vs, key)
        client.force_login(developer)
        assert _operation_family(cls) == "write"
        row = next(r for r in ManageView().get_manage_views(vs, developer) if r["key"] == "tested")
        assert row["parent_requirement"] == {"key": "change", "permission": "app.change_car"}
        url = reverse(vs.get_router_name("tested"), kwargs={parent.name + "_pk": obj.pk})
        assert client.get(url).status_code == 403
        grant(developer, parent, "change")
        assert client.get(url).status_code == 200
