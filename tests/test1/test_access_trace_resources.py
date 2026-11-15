"""External Resource reads use the fresh actor, while handlers remain uncalled."""

import json

import pytest

from crud_views.lib.access_trace import trace_access
from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.views import ActionViewPermissionRequired, DetailViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from tests.test1.app.models import Publisher
from tests.test1.test_access_trace import explode
from tests.test1.test_ancestor_authorization import _url, _user, isolated_routes
from tests.test1.test_manage_requirements import register


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["detail", "missing", "disabled", "list", "action"])
def test_resource_reads_identity_state_and_counts(case):
    reads = []

    class ExternalItem(Resource):
        key: str
        secret: str

        class Meta:
            pk_field = "key"

        @classmethod
        def cv_get_items(cls, request, **kwargs):
            reads.append((request.user, kwargs))
            return [cls(key="one", secret="never serialize this external content")]

        def __str__(self):
            return explode()

        def __repr__(self):
            return explode()

    def build(sfx):
        parent = ViewSet(model=Publisher, name="resourceparent" + sfx)
        register(ListViewPermissionRequired, parent)
        vs = ViewSet(model=ExternalItem, name="external" + sfx,
                     parent=ParentViewSet(name=parent.name),
                     ancestor_policy=AncestorPolicy(actions={"tested": AncestorPermissions(nearest="view", higher="view")}),
                     resource_permissions={"view": "app.view_publisher", "change": "app.change_publisher"})
        base = ListViewPermissionRequired if case == "list" else ActionViewPermissionRequired if case == "action" else DetailViewPermissionRequired
        combined = type("ResourceEndpoint", (ResourceViewMixin, base), {"__module__": __name__})
        register(combined, vs, get=explode, post=explode, cv_action=explode,
                 cv_action_enabled=classmethod(lambda cls, user, obj: case != "disabled"))
        return (parent, vs), [parent, vs]

    user = _user("external actor", superuser=True)
    parent_obj = Publisher.objects.create(name="parent")
    with isolated_routes(build) as (parent, vs):
        kwargs = {parent.name + "_pk": parent_obj.pk}
        if case != "list":
            kwargs["pk"] = "absent" if case == "missing" else "one"
        result = trace_access(_url(vs, "tested", **kwargs), user)
        assert result.outcome == {"missing": "not_found", "disabled": "denied"}.get(case, "allowed")
        assert reads and all(actor.pk == user.pk and actor is not user for actor, _ in reads)
        assert all(args == {parent.name + "_pk": str(parent_obj.pk)} for _, args in reads)
        assert "never serialize this external content" not in json.dumps(result.to_dict())
        counts = [step.counts for step in result.steps if step.kind == "list_filter"]
        assert counts == ([{"visible": 1, "total": None}] if case == "list" else [])
        if case != "list":
            lookups = [step for step in result.steps if step.kind == "object_lookup"]
            assert len(lookups) == 1, "native Resource loader must report exactly once"
            assert lookups[0].result == ("not_found" if case == "missing" else "passed")
            if case == "missing":
                assert result.decided_by == lookups[0].n
            else:
                assert lookups[0].object == {"model": "resources.externalitem", "pk": "one"}
        assert not vs.is_view_registered("manage")
