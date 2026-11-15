"""Resource manage requests retain the existing model ancestor and database boundaries."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Permission
from django.urls import NoReverseMatch, resolve
from lxml import html

from crud_views.lib.resource import Resource, ResourceViewMixin
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import DetailView, ListView, ListViewTableMixin
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Book, Publisher
from tests.test1.app.resources import S3FileTable
from tests.test1.test_ancestor_authorization import _client, _url, isolated_routes
from tests.test1.test_ancestor_manage import _actor, _grant


class NestedItem(Resource):
    key: str
    size: int = 0

    class Meta:
        pk_field = "key"

    @classmethod
    def cv_get_items(cls, request, **kwargs):
        raise AssertionError("Manage must not list Resource items")

    @classmethod
    def cv_get_item(cls, request, pk, **kwargs):
        raise AssertionError("Manage must not load a Resource item")


def _build_chain(sfx, *, kind="core", depth=2, none=False, cascade=True):
    parent_class = GuardianViewSet if kind == "guardian" else ViewSet
    policy = AncestorPolicy(provider="none") if none else AncestorPolicy()
    grand = parent_class(model=Publisher, name=f"rmpub{sfx}", ancestor_policy=policy)
    mid = parent_class(
        model=Book,
        name=f"rmbook{sfx}",
        parent=ParentViewSet(name=grand.name, attribute="publisher"),
        ancestor_policy=policy,
    )
    ancestors = [grand, mid][:depth]
    leaf = ViewSet(
        model=NestedItem,
        name=f"rmitem{sfx}",
        parent=ParentViewSet(name=ancestors[-1].name) if ancestors else None,
        resource_permissions={"view": "app.view_author"},
        ancestor_policy=AncestorPolicy(cascade=cascade if ancestors else None),
    )
    common = {"cv_viewset": leaf, "cv_context_actions": [], "__module__": __name__}
    type(
        "NestedList",
        (ResourceViewMixin, ListViewTableMixin, ListView),
        {**common, "table_class": S3FileTable, "cv_list_actions": []},
    )
    type(
        "NestedDetail",
        (ResourceViewMixin, DetailView),
        {**common, "template_name": "app/s3file_detail.html"},
    )
    return SimpleNamespace(grand=grand, mid=mid, leaf=leaf, ancestors=ancestors), [*ancestors, leaf]


@pytest.fixture
def manage_events(monkeypatch):
    recorded = []
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "yes")
    for owner, name, event in (
        (ViewSet, "get_queryset", "queryset"),
        (ManageView, "has_permission", "local"),
        (ManageView, "get_manage_permissions", "holders"),
        (ManageView, "get_permission_holders", "legacy_holders"),
    ):
        original = getattr(owner, name)

        def spy(self, *args, _original=original, _event=event, **kwargs):
            vs = self if isinstance(self, ViewSet) else self.cv_viewset
            recorded.append((_event, vs.name))
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(owner, name, spy)
    return recorded


AUTH_CASES = [
    (depth, case)
    for depth in (0, 1, 2)
    for case in (
        ["allow", "local-denied"]
        if depth == 0
        else ["allow", "deny-outer", "missing-outer", "local-denied", "none-member", "none-outsider"]
        + (["nearest-only", "deny-nearest", "missing-nearest", "mismatched"] if depth == 2 else [])
    )
]


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["core", "guardian"])
@pytest.mark.parametrize("cascade", [True, False], ids=["full", "nearest"])
@pytest.mark.parametrize("depth,case", AUTH_CASES)
def test_nested_resource_manage_authorization(monkeypatch, manage_events, kind, cascade, depth, case):
    publisher = Publisher.objects.create(name="Allowed parent")
    other = Publisher.objects.create(name="Other parent")
    book = Book.objects.create(title="Owned book", publisher=publisher)
    foreign = Book.objects.create(title="Foreign book", publisher=other)
    none = case.startswith("none-")
    member = case not in {"local-denied", "none-outsider"}
    actor = _actor("nested resource actor", member=member)
    if not member:
        actor.user_permissions.add(Permission.objects.get(content_type__app_label="app", codename="view_author"))
    if not none:
        if depth and case not in {"deny-outer", "nearest-only"}:
            _grant(kind, actor, Publisher, publisher)
        if depth == 2 and case != "deny-nearest":
            _grant(kind, actor, Book, book)

    def build(sfx):
        return _build_chain(sfx, kind=kind, depth=depth, none=none, cascade=cascade)

    with isolated_routes(build) as chain:
        coordinates = {f"{vs.name}_pk": obj.pk for vs, obj in zip(chain.ancestors, [publisher, book], strict=False)}
        if case == "missing-outer":
            coordinates[f"{chain.grand.name}_pk"] = 987654
        if case in {"missing-nearest", "mismatched"}:
            coordinates[f"{chain.mid.name}_pk"] = 987654 if case == "missing-nearest" else foreign.pk
        url = _url(chain.leaf, "manage", **coordinates)
        assert resolve(url).kwargs == {key: str(value) for key, value in coordinates.items()}
        assert "pk" not in resolve(url).kwargs
        if depth:
            with pytest.raises(NoReverseMatch):
                _url(chain.leaf, "manage")
        client = _client(actor)
        manage_events.clear()
        response = client.get(url)
        denied = case == "deny-nearest" or (case in {"deny-outer", "nearest-only"} and (cascade or depth == 1))
        expected = (
            404 if case in {"missing-outer", "missing-nearest", "mismatched"} else 403 if denied or not member else 200
        )
        assert response.status_code == expected
        local = ("local", chain.leaf.name)
        if expected == 404 or denied:
            assert local not in manage_events
        else:
            assert local in manage_events
            if depth:
                assert manage_events.index(("queryset", chain.ancestors[-1].name)) < manage_events.index(local)
        if case == "deny-outer" and cascade and depth == 2:
            assert ("queryset", chain.mid.name) not in manage_events
        if expected != 200:
            assert not [event for event in manage_events if event[0] in {"holders", "legacy_holders"}]
        else:
            assert manage_events.index(local) < manage_events.index(("holders", chain.leaf.name))
            assert response.context["manage_permissions"]["actor"]["cells"][0]["model"] is False

        # A real sibling render owns the current-parent action projection. Loaders are
        # permitted only for these list/detail requests, and receive the same coordinates.
        if expected != 404 and not denied:
            loads = []

            def items(request, **kwargs):
                loads.append(("list", kwargs))
                return [NestedItem(key="sample")]

            def item(request, pk, **kwargs):
                loads.append(("detail", kwargs))
                assert pk == "sample"
                return NestedItem(key=pk)

            monkeypatch.setattr(NestedItem, "cv_get_items", items)
            monkeypatch.setattr(NestedItem, "cv_get_item", item)
            for key in ("list", "detail"):
                page = client.get(_url(chain.leaf, key, **coordinates, **({"pk": "sample"} if key == "detail" else {})))
                assert page.status_code == 200
                links = html.fromstring(page.content).xpath("//a/@href")
                assert (url in links) is member
            assert [key for key, _ in loads] == ["list", "detail"]
            assert all(all(kwargs[name] == str(value) for name, value in coordinates.items()) for _, kwargs in loads)
