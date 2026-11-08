"""Ancestor authorization across the shipped endpoint families and extensions, on real nested routes.

Every test drives real ``Client`` requests against isolated traced chains (``tests.test1.ancestor_cases``) and
asserts exact statuses plus the named request events: ``<level>_queryset`` / ``<level>_gate`` for each ancestor
ViewSet, ``child`` for the endpoint's own queryset, and ``local_permission``, ``state``, ``form``, ``save`` and
``on_commit`` for endpoint-local work. Ancestors are Publisher (``outer``) and Book (``inner``); the endpoints are
BookNote or test-only nested models (ordered, workflow; polymorphic vehicles below a garage instead of a Book).

Core create/update/delete, nested manage and the order rules themselves are covered by ``test_ancestor_requests``;
this module covers the remaining shipped families, custom endpoints and the built-in redirect.
"""

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms import modelform_factory
from django.test import Client
from django.urls import clear_url_caches, reverse
from django.views import generic

from crud_views.lib.view import CrudView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy
from tests.test1.ancestor_cases import CHECKED, EVENTS, ancestor_scope, book_child_chain, traced_chain
from tests.test1.app.models import (
    AncestorCar,
    AncestorGarage,
    AncestorStep,
    AncestorTask,
    AncestorTaskState,
    AncestorTruck,
    AncestorVehicle,
    Book,
    BookNote,
    Publisher,
)
from tests.test1.test_ancestor_requests import (
    FormTrace,
    LocalTrace,
    client_for,
    define,
    make_user,
)

WRITE = AncestorPermissions(nearest="change", higher="view")
STRICT = AncestorPermissions(nearest="change", higher="change")
ANCESTRY = ["outer_queryset", "outer_gate", "inner_queryset", "inner_gate"]
ANCESTOR_PERMS = ["view_publisher", "change_publisher", "view_book", "change_book"]

# Publisher (outer) → Book (inner) → BookNote (endpoint)
NOTE_TWO = book_child_chain(BookNote, depth=2)


@pytest.fixture(autouse=True)
def events():
    EVENTS.clear()
    CHECKED.clear()
    yield EVENTS
    EVENTS.clear()
    CHECKED.clear()


@pytest.fixture
def scope():
    with ancestor_scope() as scope:
        yield scope


def local_perms(model) -> list[str]:
    name = model._meta.model_name
    return [f"{action}_{name}" for action in ("view", "add", "change", "delete")]


def endpoint_url(viewset, key, parents, obj=None, **extra) -> str:
    """Reverse ``key`` on a nested ``viewset``; ``parents`` are the ancestor instances, outermost first."""
    kwargs = dict(extra)
    parent = viewset.parent
    for ancestor_obj in reversed(parents):
        kwargs[parent.get_pk_name()] = ancestor_obj.pk
        parent = parent.viewset.parent
    if obj is not None:
        kwargs[viewset.pk_name] = obj.pk
    return reverse(viewset.get_router_name(key), kwargs=kwargs)


def ancestry_data():
    publisher = Publisher.objects.create(name="Publisher")
    book = Book.objects.create(title="Book", publisher=publisher)
    return publisher, book


def snapshot():
    """Every row the endpoints could write, with the ordered position and workflow state."""
    return (
        sorted(BookNote.objects.values_list("pk", "note")),
        sorted(AncestorVehicle.objects.values_list("pk", "name")),
        sorted(AncestorStep.objects.values_list("pk", "order")),
        sorted(AncestorTask.objects.values_list("pk", "state")),
    )


# ── shipped families ──────────────────────────────────────────────────────────


POLYMORPHIC_FORMS = {
    AncestorCar: modelform_factory(AncestorCar, fields=["name", "doors"]),
    AncestorTruck: modelform_factory(AncestorTruck, fields=["name", "payload_tons"]),
}


def _family(name):
    """(endpoint model, view bases, view attributes, method, object row, extra URL kwargs, allowed status)."""
    from crud_views.lib.views import (
        CardListView,
        CardListViewPermissionRequired,
        DetailView,
        DetailViewPermissionRequired,
        ListView,
        ListViewPermissionRequired,
    )
    from crud_views.lib.views.action_ordered import (
        OrderedDownView,
        OrderedUpDownPermissionRequired,
        OrderedUpView,
        OrderedUpViewPermissionRequired,
    )
    from crud_views_object_detail.lib.views import ObjectDetailView, ObjectDetailViewPermissionRequired
    from crud_views_polymorphic.lib.create import PolymorphicCreateView, PolymorphicCreateViewPermissionRequired
    from crud_views_polymorphic.lib.create_select import (
        PolymorphicCreateSelectView,
        PolymorphicCreateSelectViewPermissionRequired,
    )
    from crud_views_polymorphic.lib.delete import PolymorphicDeleteView, PolymorphicDeleteViewPermissionRequired
    from crud_views_polymorphic.lib.detail import PolymorphicDetailView, PolymorphicDetailViewPermissionRequired
    from crud_views_polymorphic.lib.update import PolymorphicUpdateView, PolymorphicUpdateViewPermissionRequired

    display = {"cv_property_display": [{"title": "Attributes", "properties": ["note"]}]}
    poly = {"polymorphic_forms": POLYMORPHIC_FORMS}
    # name: (model, plain base, permission variant, attributes, method, object, extra kwargs, allowed status)
    table = {
        "list": (BookNote, ListView, ListViewPermissionRequired, {}, "get", None, {}, 200),
        "card": (BookNote, CardListView, CardListViewPermissionRequired, {}, "get", None, {}, 200),
        "detail": (BookNote, DetailView, DetailViewPermissionRequired, {}, "get", "row", {}, 200),
        "object-detail": (
            BookNote,
            ObjectDetailView,
            ObjectDetailViewPermissionRequired,
            display,
            "get",
            "row",
            {},
            200,
        ),
        "poly-detail": (
            AncestorVehicle,
            PolymorphicDetailView,
            PolymorphicDetailViewPermissionRequired,
            {},
            "get",
            "row",
            {},
            200,
        ),
        "poly-create": (
            AncestorVehicle,
            PolymorphicCreateView,
            PolymorphicCreateViewPermissionRequired,
            poly,
            "get",
            None,
            {"polymorphic_ctype_id": "car"},
            200,
        ),
        "poly-update": (
            AncestorVehicle,
            PolymorphicUpdateView,
            PolymorphicUpdateViewPermissionRequired,
            poly,
            "get",
            "row",
            {},
            200,
        ),
        "poly-delete": (
            AncestorVehicle,
            PolymorphicDeleteView,
            PolymorphicDeleteViewPermissionRequired,
            {},
            "post",
            "row",
            {},
            302,
        ),
        "poly-select-get": (
            AncestorVehicle,
            PolymorphicCreateSelectView,
            PolymorphicCreateSelectViewPermissionRequired,
            {},
            "get",
            None,
            {},
            200,
        ),
        "poly-select-post": (
            AncestorVehicle,
            PolymorphicCreateSelectView,
            PolymorphicCreateSelectViewPermissionRequired,
            {},
            "post",
            None,
            {},
            302,
        ),
        "up": (AncestorStep, OrderedUpView, OrderedUpViewPermissionRequired, {}, "post", "second", {}, 302),
        "down": (AncestorStep, OrderedDownView, OrderedUpDownPermissionRequired, {}, "post", "row", {}, 302),
    }
    return table[name]


FAMILIES = [
    "list",
    "card",
    "detail",
    "object-detail",
    "poly-detail",
    "poly-create",
    "poly-update",
    "poly-delete",
    "poly-select-get",
    "poly-select-post",
    "up",
    "down",
]


def family_chain(model):
    """Publisher (outer) → inner → ``model``: polymorphic vehicles live in a garage, the others in a Book."""
    if model is AncestorVehicle:
        return ((Publisher, None, "outer"), (AncestorGarage, "publisher", "inner"), (model, "garage", "child"))
    return book_child_chain(model, depth=2)


def family_data(model):
    """(publisher, inner object, two endpoint rows) for ``model``."""
    publisher = Publisher.objects.create(name="Publisher")
    if model is AncestorVehicle:
        garage = AncestorGarage.objects.create(publisher=publisher, name="Garage")
        rows = [
            AncestorCar.objects.create(garage=garage, name="Car"),
            AncestorTruck.objects.create(garage=garage, name="Truck"),
        ]
        return publisher, garage, rows
    book = Book.objects.create(title="Book", publisher=publisher)
    if model is BookNote:
        return publisher, book, [BookNote.objects.create(book=book, note=f"Note {i}") for i in (1, 2)]
    return publisher, book, [AncestorStep.objects.create(book=book, name=f"Step {i}") for i in (1, 2)]


@pytest.mark.django_db
@pytest.mark.parametrize("variant", ["plain", "permission"])
@pytest.mark.parametrize("name", FAMILIES)
def test_all_shipped_families_reach_ancestry_before_local_work(scope, events, name, variant):
    """Every shipped family (as a normal subclass and as its permission variant) authorizes the ancestors first: a
    denied ancestor is 403 before any child, local permission, state, form or write; allowed ancestry continues into
    the existing local behavior."""
    from django.contrib.contenttypes.models import ContentType

    from crud_views.lib.views import DetailView, ListView

    model, plain, permission, attrs, method, row, extra, allowed_status = _family(name)
    routes = traced_chain(scope, family_chain(model))
    child = routes.endpoint
    inner = routes.viewsets[1].model._meta.model_name
    bases = (FormTrace, plain) if variant == "plain" else (FormTrace, LocalTrace, permission)
    view = define(scope, child, bases, **attrs)
    # success/cancel targets of the endpoint (plain: no local gate of their own)
    for support in (ListView, DetailView):
        if support.cv_key != view.cv_key:
            define(scope, child, support)
    if name.startswith("poly-select"):
        from crud_views_polymorphic.lib.create import PolymorphicCreateView

        define(scope, child, PolymorphicCreateView, polymorphic_forms=POLYMORPHIC_FORMS)
    scope.mount([child])
    publisher, inner_obj, rows = family_data(model)
    obj = {"row": rows[0], "second": rows[1], None: None}[row]
    if extra.get("polymorphic_ctype_id") == "car":
        extra = {"polymorphic_ctype_id": ContentType.objects.get_for_model(AncestorCar).pk}
    url = endpoint_url(child, view.cv_key, [publisher, inner_obj], obj=obj, **extra)
    payload = {}
    if name == "poly-select-post":
        payload = {"polymorphic_ctype_id": ContentType.objects.get_for_model(AncestorCar).pk}

    def request(user):
        events.clear()
        client = client_for(user)
        return client.post(url, payload) if method == "post" else client.get(url)

    # every local and inner grant, but no Publisher grant: the outer gate denies before any endpoint work
    before = snapshot()
    inner_perms = [f"view_{inner}", f"change_{inner}"]
    denied = make_user("denied", [*inner_perms, *local_perms(model)])
    assert request(denied).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]
    assert snapshot() == before

    allowed = make_user("allowed", ["view_publisher", "change_publisher", *inner_perms, *local_perms(model)])
    response = request(allowed)
    assert response.status_code == allowed_status, response.content[:300]
    assert events[:4] == ANCESTRY
    local = events[4:]
    assert local, "allowed ancestry continues into endpoint-local work"
    if variant == "permission":
        assert local[0] == "local_permission"
    if name in ("up", "down"):
        assert snapshot() != before
        assert sorted(AncestorStep.objects.values_list("name", "order")) == [("Step 1", 1), ("Step 2", 0)]
    if name == "poly-delete":
        assert not AncestorVehicle.objects.filter(pk=obj.pk).exists()


# ── renamed built-ins, exact overrides and Card navigation ────────────────────


def permissions_checked():
    return [permission for _trace, permission in CHECKED]


READ_CHECKED = ["app.view_publisher", "app.view_book"]
WRITE_CHECKED = ["app.view_publisher", "app.change_book"]
STRICT_CHECKED = ["app.change_publisher", "app.change_book"]


@pytest.mark.django_db
def test_renamed_builtin_and_exact_action_override_requests(scope, events):
    from crud_views.lib.views import DetailView, ListView, UpdateView

    # "show" is a renamed DetailView (Read), "edit" a renamed UpdateView (Write); "inspect" is a renamed DetailView
    # whose exact entry replaces the whole Read pair
    routes = traced_chain(scope, NOTE_TWO, policies={2: AncestorPolicy(actions={"inspect": STRICT})})
    child = routes.endpoint
    define(scope, child, ListView)
    define(scope, child, DetailView, key="show")
    define(scope, child, UpdateView, key="edit", fields=["note"])
    define(scope, child, DetailView, key="inspect")
    scope.mount([child])
    publisher, book = ancestry_data()
    note = BookNote.objects.create(book=book, note="Note")
    reader = client_for(make_user("reader", ["view_publisher", "view_book"]))
    writer = client_for(make_user("writer", ["view_publisher", "change_book"]))
    strict = client_for(make_user("strict", ["change_publisher", "change_book"]))

    def get(client, key):
        CHECKED.clear()
        return client.get(endpoint_url(child, key, [publisher, book], obj=note)).status_code

    assert (get(reader, "show"), permissions_checked()) == (200, READ_CHECKED)
    assert (get(reader, "edit"), permissions_checked()) == (403, WRITE_CHECKED)
    assert (get(writer, "edit"), permissions_checked()) == (200, WRITE_CHECKED)
    # the exact entry replaces both components: no family Read requirement is merged in
    assert (get(reader, "inspect"), permissions_checked()) == (403, ["app.change_publisher"])
    assert (get(strict, "inspect"), permissions_checked()) == (200, STRICT_CHECKED)


@pytest.mark.django_db
def test_card_only_navigation_uses_the_card_key_and_later_list_keeps_it(scope, events):
    from crud_views.lib.views import CardListView, ListView

    routes = traced_chain(scope, NOTE_TWO, policies={2: AncestorPolicy(actions={"card": STRICT})})
    child = routes.endpoint
    define(scope, child, CardListView)
    scope.mount([child])
    publisher, book = ancestry_data()
    reader = client_for(make_user("reader", ["view_publisher", "view_book"]))
    strict = client_for(make_user("strict", ["change_publisher", "change_book"]))

    # navigation's list → card fallback reaches the Card endpoint, which applies its own "card" entry
    list_kwargs = {child.parent.get_pk_name(): book.pk, child.parent.viewset.parent.get_pk_name(): publisher.pk}
    navigated = reverse(child.get_router_name("list"), kwargs=list_kwargs)
    assert navigated == endpoint_url(child, "card", [publisher, book])
    assert reader.get(navigated).status_code == 403
    assert permissions_checked() == ["app.change_publisher"]
    CHECKED.clear()
    assert strict.get(navigated).status_code == 200
    assert permissions_checked() == STRICT_CHECKED

    # registering a real List later never retargets the Card entry; the List uses the Read pair
    define(scope, child, ListView)
    child.__dict__.pop("urlpatterns", None)  # drop the cached patterns; the scope's URL module rebuilds them
    clear_url_caches()
    CHECKED.clear()
    assert reader.get(endpoint_url(child, "list", [publisher, book])).status_code == 200
    assert permissions_checked() == READ_CHECKED
    CHECKED.clear()
    assert reader.get(endpoint_url(child, "card", [publisher, book])).status_code == 403
    assert strict.get(endpoint_url(child, "card", [publisher, book])).status_code == 200
    assert permissions_checked() == ["app.change_publisher", *STRICT_CHECKED]


# ── custom endpoints need an exact pair when nested ───────────────────────────

EFFECTS: list[str] = []


class EffectForm(forms.Form):
    pass


def custom_endpoint(scope, viewset, kind):
    """Register one custom endpoint of ``kind`` on ``viewset``; return its key and HTTP method."""
    from crud_views.lib.crispy import CrispyViewMixin
    from crud_views.lib.views import ActionView
    from crud_views.lib.views.form import CustomFormNoObjectView, CustomFormView
    from crud_views_guardian.lib.views import GuardianActionViewPermissionRequired
    from crud_views_workflow.lib.forms import WorkflowForm
    from crud_views_workflow.lib.views import WorkflowView

    class Effect:
        def action(self, context):
            EFFECTS.append(kind)
            return True

        def cv_form_valid(self, context):
            EFFECTS.append(kind)

    if kind == "action":
        define(scope, viewset, (Effect, ActionView), key="approve")
        return "approve", "post"
    if kind == "guardian-action":
        define(scope, viewset, (Effect, GuardianActionViewPermissionRequired), key="approve")
        return "approve", "post"
    if kind == "form":
        define(scope, viewset, (Effect, CustomFormView), key="approve", form_class=EffectForm)
        return "approve", "post"
    if kind == "form-no-object":
        define(scope, viewset, (Effect, CustomFormNoObjectView), key="approve", form_class=EffectForm)
        return "approve", "post"
    if kind == "workflow":
        form = type(
            f"TaskWorkflowForm{scope.sfx}",
            (WorkflowForm,),
            {
                "Meta": type("Meta", (), {"model": AncestorTask, "fields": ["transition", "comment"]}),
                "__module__": __name__,
            },
        )
        define(scope, viewset, (CrispyViewMixin, WorkflowView), form_class=form)
        return "workflow", "post"

    class CustomRedirect(CrudView, generic.RedirectView):
        """An arbitrary custom redirect: no built-in family, even though it only redirects."""

        cv_key = "jump"
        cv_path = "jump"
        cv_object = False

        def get_redirect_url(self, *args, **kwargs):
            EFFECTS.append(kind)
            return "/elsewhere/"

    define(scope, viewset, CustomRedirect)
    return "jump", "get"


CUSTOM_KINDS = ["action", "guardian-action", "form", "form-no-object", "workflow", "redirect"]
CUSTOM_KEYS = {"workflow": "workflow", "redirect": "jump"}  # every other kind registers "approve"
CUSTOM_ANCESTRY = {
    # id: (depth, ancestors' provider, ancestry events of an allowed request)
    "depth-1": (1, None, ["outer_queryset", "outer_gate"]),
    "depth-2": (2, None, ANCESTRY),
    "all-none": (2, "none", ["outer_queryset", "inner_queryset"]),
}


def custom_chain(scope, kind, ancestry, actions=None):
    from crud_views.lib.views import DetailView, ListView
    from tests.test1.test_ancestor_guardian import TracedGuardianViewSet

    depth, provider, _events = CUSTOM_ANCESTRY[ancestry]
    model = AncestorTask if kind == "workflow" else BookNote
    policies = {index: AncestorPolicy(provider=provider) for index in range(depth) if provider is not None}
    if actions is not None:
        policies[depth] = AncestorPolicy(actions=actions)
    classes = {depth: TracedGuardianViewSet} if kind == "guardian-action" else {}
    routes = traced_chain(scope, book_child_chain(model, depth), policies=policies, viewset_classes=classes)
    child = routes.endpoint
    key, method = custom_endpoint(scope, child, kind)
    define(scope, child, ListView)
    define(scope, child, DetailView)
    scope.mount([child])
    return routes, model, key, method


def custom_target(model, book):
    if model is AncestorTask:
        return AncestorTask.objects.create(book=book, name="Task")
    return BookNote.objects.create(book=book, note="Note")


def custom_request(client, routes, key, method, parents, obj, kind):
    no_object = kind in ("form-no-object", "redirect")
    url = endpoint_url(routes.endpoint, key, parents, obj=None if no_object else obj)
    if method == "get":
        return client.get(url)
    payload = {"transition": "wf_done", "comment": ""} if kind == "workflow" else {}
    return client.post(url, payload)


@pytest.mark.django_db
@pytest.mark.parametrize("ancestry", list(CUSTOM_ANCESTRY))
@pytest.mark.parametrize("kind", CUSTOM_KINDS)
def test_nested_custom_endpoint_requires_explicit_pair(scope, events, kind, ancestry):
    """A nested generic action, custom form (object or none), workflow or custom redirect without its exact action
    pair is a configuration error before any actor or object work, in both depths and with all-none ancestry."""
    EFFECTS.clear()
    depth = CUSTOM_ANCESTRY[ancestry][0]
    routes, model, key, method = custom_chain(scope, kind, ancestry)
    publisher, book = ancestry_data()
    parents = [publisher, book][-depth:]
    obj = custom_target(model, book)
    user = make_user("editor", [*ANCESTOR_PERMS, *local_perms(model)])

    for client in (Client(), client_for(user)):
        events.clear()
        with pytest.raises(ImproperlyConfigured, match=rf"actions\[{key!r}\]"):
            custom_request(client, routes, key, method, parents, obj, kind)
        assert events == []
    assert EFFECTS == []


@pytest.mark.django_db
@pytest.mark.parametrize("ancestry", list(CUSTOM_ANCESTRY))
@pytest.mark.parametrize("kind", CUSTOM_KINDS)
def test_nested_custom_endpoint_with_declared_pair_reaches_local_behavior(scope, events, kind, ancestry):
    EFFECTS.clear()
    depth, _provider, ancestry_events = CUSTOM_ANCESTRY[ancestry]
    publisher, book = ancestry_data()
    parents = [publisher, book][-depth:]
    routes, model, key, method = custom_chain(scope, kind, ancestry, actions={CUSTOM_KEYS.get(kind, "approve"): WRITE})
    obj = custom_target(model, book)
    user = make_user("editor", [*ANCESTOR_PERMS, *local_perms(model)])
    if kind == "guardian-action":
        routes.endpoint.assign_perm("change", user, obj)

    # the declared Write pair is enforced: Book view alone (no change) is denied at the nearest gate
    if ancestry != "all-none":
        events.clear()
        viewer = make_user("viewer", ["view_publisher", "view_book", *local_perms(model)])
        assert custom_request(client_for(viewer), routes, key, method, parents, obj, kind).status_code == 403
        assert events == ancestry_events
        assert EFFECTS == []

    events.clear()
    response = custom_request(client_for(user), routes, key, method, parents, obj, kind)
    assert response.status_code == 302, response.content[:300]
    assert events[: len(ancestry_events)] == ancestry_events
    if kind == "workflow":
        obj.refresh_from_db()
        assert obj.state == AncestorTaskState.DONE
    else:
        assert [kind] == EFFECTS


@pytest.mark.django_db
@pytest.mark.parametrize("kind", CUSTOM_KINDS)
def test_top_level_custom_endpoint_needs_no_declaration(scope, events, kind):
    from crud_views.lib.views import DetailView, ListView
    from tests.test1.ancestor_cases import TracedViewSet
    from tests.test1.test_ancestor_guardian import TracedGuardianViewSet

    EFFECTS.clear()
    model = AncestorTask if kind == "workflow" else BookNote
    viewset_class = TracedGuardianViewSet if kind == "guardian-action" else TracedViewSet
    viewset = scope.viewset(viewset_class, model=model, name=scope.name("topcustom"), trace="child")
    key, method = custom_endpoint(scope, viewset, kind)
    define(scope, viewset, ListView)
    define(scope, viewset, DetailView)
    scope.mount([viewset])
    _publisher, book = ancestry_data()
    obj = custom_target(model, book)
    user = make_user("editor", local_perms(model))
    if kind == "guardian-action":
        viewset.assign_perm("change", user, obj)
    no_object = kind in ("form-no-object", "redirect")
    url = reverse(viewset.get_router_name(key), kwargs={} if no_object else {"pk": obj.pk})
    client = client_for(user)
    payload = {"transition": "wf_done", "comment": ""} if kind == "workflow" else {}
    response = client.get(url) if method == "get" else client.post(url, payload)
    assert response.status_code == 302
    assert not [event for event in events if event.endswith("_gate")]
    if kind == "workflow":
        obj.refresh_from_db()
        assert obj.state == AncestorTaskState.DONE
    else:
        assert [kind] == EFFECTS


# ── built-in redirect to a child ──────────────────────────────────────────────


def redirect_routes(scope, book_policy=None):
    """Publisher (outer) → Book (inner, with a RedirectChildView to its notes) → BookNote (child, Read list)."""
    from crud_views.lib.views import DetailView, ListView, RedirectChildView

    policies = {1: book_policy} if book_policy is not None else {}
    routes = traced_chain(scope, NOTE_TWO, policies=policies)
    book_vs, note_vs = routes.viewsets[1], routes.endpoint
    define(scope, book_vs, ListView)
    define(scope, book_vs, DetailView)
    define(scope, book_vs, RedirectChildView, cv_redirect=note_vs.name, cv_redirect_key="list")
    define(scope, note_vs, ListView)
    scope.mount([book_vs, note_vs])
    publisher, book = ancestry_data()
    source = reverse(
        book_vs.get_router_name("redirect_child"),
        kwargs={
            book_vs.parent.get_pk_name(): publisher.pk,
            "pk": book.pk,
            # the path segment only admits [a-z_]; the target is the view's cv_redirect, not this segment
            "redirect": "notes",
            "redirect_key": "list",
        },
    )
    destination = endpoint_url(note_vs, "list", [publisher, book])
    return source, destination


@pytest.mark.django_db
def test_redirect_child_is_read_without_an_action_entry(scope, events):
    source, destination = redirect_routes(scope)

    # built-in Read pair: Publisher view; the object lookup and redirect follow ancestry
    response = client_for(make_user("reader", ["view_publisher"])).get(source)
    assert (response.status_code, response["Location"]) == (302, destination)
    assert events == ["outer_queryset", "outer_gate", "inner_queryset"]
    assert permissions_checked() == ["app.view_publisher"]

    # denied ancestry: no object lookup and no redirect processing
    events.clear()
    assert client_for(make_user("outsider", ["view_book", "view_booknote"])).get(source).status_code == 403
    assert events == ["outer_queryset", "outer_gate"]


@pytest.mark.django_db
def test_redirect_child_explicit_pair_overrides_the_read_pair(scope, events):
    source, destination = redirect_routes(
        scope, AncestorPolicy(actions={"redirect_child": AncestorPermissions(nearest="change", higher="view")})
    )
    assert client_for(make_user("reader", ["view_publisher"])).get(source).status_code == 403
    assert permissions_checked() == ["app.change_publisher"]
    response = client_for(make_user("editor", ["change_publisher"])).get(source)
    assert (response.status_code, response["Location"]) == (302, destination)


@pytest.mark.django_db
def test_redirect_destination_authorizes_independently(scope, events):
    source, destination = redirect_routes(scope)
    client = client_for(make_user("source-only", ["view_publisher"]))

    response = client.get(source, follow=True)

    # the source (Publisher view) redirects; the destination is its own request with its own Read ancestry
    # (Publisher view, Book view) and denies at the Book gate
    assert response.redirect_chain == [(destination, 302)]
    assert response.status_code == 403
    assert events == [
        "outer_queryset",
        "outer_gate",
        "inner_queryset",
        "outer_queryset",
        "outer_gate",
        "inner_queryset",
        "inner_gate",
    ]
