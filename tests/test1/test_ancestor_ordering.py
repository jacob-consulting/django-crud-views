"""
Phase 06.18 plan 04 — interleaved ancestor enforcement across every shipped composition.

Every request below goes through a real URL under a two-ancestor chain::

    Publisher (core ViewSet) → Book (core ViewSet, nested) → leaf (the endpoint under test)

``INVENTORY`` names each shipped family/MRO, its operation (Read / Write / an exact custom ``actions`` entry)
and the dispatch method that reaches the shared ancestor guard first (``GUARD_ENTRY``). For every entry the same
four scenarios run (full cascade):

* ``outer-denied``: the actor lacks the Publisher (higher) permission and the Book row does not exist → 403
  after the Publisher gate; the Book ViewSet queryset is never entered and no leaf work happens.
* ``nearest-denied``: the actor holds Publisher view only → 403 at the Book (nearest) gate; no leaf work.
* ``reached-404``: both gates would pass, the Book belongs to another Publisher → 404 at the Book lookup.
* ``local-reached``: both gates pass, the actor holds no leaf permission → the endpoint's own local stage runs
  (permission 403, Guardian object/list gate, plain lookup/render, manage group gate, Resource loader…), always
  after the complete guard sequence.

In the denial scenarios every event outside the expected guard sequence is a *poison*: the spy raises, so a
reached deeper queryset, local permission, child lookup, state hook, form, fragment render, Resource loader,
manage gate or template render fails the request instead of being merely counted.

Leaf models of the polymorphic, workflow and ordered families are isolated test models (``isolate_apps``) with a
hidden FK to Book; their tables are never created. Every scenario run for them stops before leaf data, so a
reached leaf query would itself fail ("no such table"). The editor-fragment entries use the single-ancestor
Publisher → Book editor (Book carries the notes formset); deeper interleaving is engine-generic and proven by
every other entry.

Fixtures build fresh, uniquely named ViewSets behind a temporary ROOT_URLCONF and restore the registry and caches
(``isolated_routes``).
"""

from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, Group, PermissionsMixin
from django.db import models
from django.forms import inlineformset_factory
from django.http import Http404
from django.test.utils import isolate_apps
from django.utils.module_loading import import_string
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin
from guardian.core import ObjectPermissionChecker

from crud_views.lib.crispy import CrispyModelForm
from crud_views.lib.formsets import FormSet, FormSets, InlineFormSet
from crud_views.lib.resource import Resource
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views.lib.viewset.path_regs import PrimaryKeys
from tests.test1.app.models import Book, BookNote, Publisher
from tests.test1.test_ancestor_authorization import _client, _url, _user, isolated_routes

MISSING = 987654

# ── the composition inventory ────────────────────────────────────────────────

V = "crud_views.lib.views."
G = "crud_views_guardian.lib.views."
P = "crud_views_polymorphic.lib."
CUSTOM = AncestorPermissions(nearest="change", higher="view")

GUARD_ENTRY = {
    "plain": "CrudView.dispatch",
    "permission": "CrudViewPermissionRequiredMixin.dispatch",
    "guardian": "GuardianParentPermissionMixin.dispatch",
    "manage": "ManageView.dispatch",
}


@dataclass(frozen=True)
class Entry:
    id: str
    bases: tuple[str, ...]  # dotted base classes of the endpoint view (outermost first)
    guard: str  # GUARD_ENTRY key: the dispatch that reaches the ancestor guard first
    op: str  # "read" | "write" | "custom" (exact actions entry CUSTOM)
    local: int  # status after ancestry success for an actor without any leaf permission (leaf pk missing)
    leaf: str = "note"  # note | poly | flow | ordered | resource | fragment
    method: str = "get"
    obj: bool = True
    guardian: bool = False  # GuardianViewSet leaf
    key: str | None = None  # registered key when the class has none of its own
    attrs: dict = field(default_factory=dict)


NOTE_FORM = {"fields": ["note"]}
CREATE = "crud_views.lib.views.CreateViewParentMixin"

INVENTORY = (
    # plain core families — no endpoint-local permission gate
    Entry("plain-list", (V + "ListView",), "plain", "read", 200, obj=False),
    Entry("plain-detail", (V + "DetailView",), "plain", "read", 404),
    Entry("plain-create", (CREATE, V + "CreateView"), "plain", "write", 200, obj=False, attrs=NOTE_FORM),
    Entry("plain-update", (V + "UpdateView",), "plain", "write", 404, attrs=NOTE_FORM),
    Entry("plain-delete", (V + "DeleteView",), "plain", "write", 404),
    Entry("plain-card", (V + "CardListView",), "plain", "read", 200, obj=False),
    Entry("plain-redirect-child", (V + "RedirectChildView",), "plain", "read", 404),
    Entry("plain-rich-detail", ("crud_views_object_detail.lib.views.ObjectDetailView",), "plain", "read", 404),
    Entry("plain-action", (V + "ActionView",), "plain", "custom", 404, method="post", key="act"),
    Entry("plain-custom-form", ("crud_views.lib.views.form.CustomFormView",), "plain", "custom", 404, key="form"),
    # core permission-required families
    Entry("core-list", (V + "ListViewPermissionRequired",), "permission", "read", 403, obj=False),
    Entry("core-detail", (V + "DetailViewPermissionRequired",), "permission", "read", 403),
    Entry(
        "core-create",
        (CREATE, V + "CreateViewPermissionRequired"),
        "permission",
        "write",
        403,
        obj=False,
        attrs=NOTE_FORM,
    ),
    Entry("core-update", (V + "UpdateViewPermissionRequired",), "permission", "write", 403, attrs=NOTE_FORM),
    Entry("core-delete", (V + "DeleteViewPermissionRequired",), "permission", "write", 403),
    Entry("core-card", (V + "CardListViewPermissionRequired",), "permission", "read", 403, obj=False),
    Entry(
        "core-rich-detail",
        ("crud_views_object_detail.lib.views.ObjectDetailViewPermissionRequired",),
        "permission",
        "read",
        403,
    ),
    Entry("core-action", (V + "ActionViewPermissionRequired",), "permission", "custom", 403, method="post", key="act"),
    Entry(
        "core-custom-form",
        ("crud_views.lib.views.form.CustomFormViewPermissionRequired",),
        "permission",
        "custom",
        403,
        key="form",
    ),
    Entry(
        "core-custom-form-no-object",
        ("crud_views.lib.views.form.CustomFormNoObjectViewPermissionRequired",),
        "permission",
        "custom",
        403,
        obj=False,
        key="form",
    ),
    Entry(
        "core-ordered-up",
        (V + "OrderedUpViewPermissionRequired",),
        "permission",
        "write",
        403,
        leaf="ordered",
        method="post",
    ),
    Entry(
        "core-ordered-down",
        (V + "OrderedUpDownPermissionRequired",),
        "permission",
        "write",
        403,
        leaf="ordered",
        method="post",
    ),
    # manage (auto-created on every model ViewSet; group gate is local)
    Entry("manage", ("crud_views.lib.views.manage.ManageView",), "manage", "read", 403, obj=False),
    Entry("guardian-manage", (G + "GuardianManageView",), "manage", "read", 403, obj=False, guardian=True),
    # Guardian shipped compositions (parent + object/queryset mixins)
    Entry(
        "guardian-list", (G + "GuardianListViewPermissionRequired",), "guardian", "read", 200, obj=False, guardian=True
    ),
    Entry("guardian-detail", (G + "GuardianDetailViewPermissionRequired",), "guardian", "read", 404, guardian=True),
    Entry(
        "guardian-create",
        (CREATE, G + "GuardianCreateViewPermissionRequired"),
        "guardian",
        "write",
        200,
        obj=False,
        guardian=True,
        attrs=NOTE_FORM,
    ),
    Entry(
        "guardian-update",
        (G + "GuardianUpdateViewPermissionRequired",),
        "guardian",
        "write",
        404,
        guardian=True,
        attrs=NOTE_FORM,
    ),
    Entry("guardian-delete", (G + "GuardianDeleteViewPermissionRequired",), "guardian", "write", 404, guardian=True),
    Entry(
        "guardian-card",
        (G + "GuardianCardListViewPermissionRequired",),
        "guardian",
        "read",
        200,
        obj=False,
        guardian=True,
    ),
    Entry(
        "guardian-action",
        (G + "GuardianActionViewPermissionRequired",),
        "guardian",
        "custom",
        404,
        method="post",
        guardian=True,
        key="act",
    ),
    # Resource leaves
    Entry(
        "resource-list",
        ("crud_views.lib.resource.ResourceViewMixin", V + "ListViewPermissionRequired"),
        "permission",
        "read",
        403,
        obj=False,
        leaf="resource",
    ),
    Entry(
        "resource-detail",
        ("crud_views.lib.resource.ResourceViewMixin", V + "DetailViewPermissionRequired"),
        "permission",
        "read",
        403,
        leaf="resource",
    ),
    # polymorphic
    Entry(
        "poly-detail", (P + "detail.PolymorphicDetailViewPermissionRequired",), "permission", "read", 403, leaf="poly"
    ),
    Entry(
        "poly-create-select",
        (P + "create_select.PolymorphicCreateSelectViewPermissionRequired",),
        "permission",
        "write",
        403,
        obj=False,
        leaf="poly",
    ),
    Entry(
        "poly-create",
        (P + "create.PolymorphicCreateViewPermissionRequired",),
        "permission",
        "write",
        403,
        obj=False,
        leaf="poly",
    ),
    Entry(
        "poly-update", (P + "update.PolymorphicUpdateViewPermissionRequired",), "permission", "write", 403, leaf="poly"
    ),
    Entry(
        "poly-delete", (P + "delete.PolymorphicDeleteViewPermissionRequired",), "permission", "write", 403, leaf="poly"
    ),
    # workflow (unclassified: exact custom entry)
    Entry(
        "workflow",
        ("crud_views_workflow.lib.views.WorkflowViewPermissionRequired",),
        "permission",
        "custom",
        403,
        leaf="flow",
    ),
    # owning-editor formset fragments (Write; Book editor under Publisher)
    Entry("fragment-core-update", (V + "UpdateViewPermissionRequired",), "permission", "write", 403, leaf="fragment"),
    Entry(
        "fragment-guardian-update",
        (G + "GuardianUpdateViewPermissionRequired",),
        "guardian",
        "write",
        403,
        leaf="fragment",
        guardian=True,
    ),
    Entry(
        "fragment-guardian-create",
        (CREATE, G + "GuardianCreateViewPermissionRequired"),
        "guardian",
        "write",
        200,
        leaf="fragment",
        guardian=True,
        obj=False,
    ),
)

ENTRY_IDS = [entry.id for entry in INVENTORY]
TWO_ANCESTORS = [entry for entry in INVENTORY if entry.leaf != "fragment"]  # fragments: single-ancestor editor


# ── leaf models and resources ────────────────────────────────────────────────

RESOURCE_EVENTS: list = []


class OrderingNoteFile(Resource):
    """A Resource leaf below Book; its loader records that it ran and finds nothing."""

    key: str

    class Meta:
        verbose_name = "note file"
        verbose_name_plural = "note files"
        app_label = "app"
        pk_field = "key"
        pk_type = PrimaryKeys.STR

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        RESOURCE_EVENTS.append(("resource", "items"))
        return []

    @classmethod
    def cv_get_item(cls, request, pk, **url_kwargs):
        RESOURCE_EVENTS.append(("resource", "item"))
        raise Http404


def _isolated_leaf_models():
    """Polymorphic, workflow and ordered leaf models with a hidden FK to Book (no tables, no reverse accessor)."""
    from ordered_model.models import OrderedModel
    from polymorphic.models import PolymorphicModel

    from crud_views_workflow.lib.mixins import WorkflowModelMixin

    class OrderingPolyNote(PolymorphicModel):
        book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "app"

    class OrderingPolyNoteA(OrderingPolyNote):
        class Meta:
            app_label = "app"

    class OrderingFlowNote(WorkflowModelMixin, models.Model):
        STATE_CHOICES = models.TextChoices("S", "new")
        STATE_BADGES = {}
        book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="+")
        state = models.CharField(max_length=16, default="new")

        class Meta:
            app_label = "app"

    class OrderingOrderedNote(OrderedModel):
        book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="+")

        class Meta(OrderedModel.Meta):
            app_label = "app"

    return {"poly": OrderingPolyNote, "flow": OrderingFlowNote, "ordered": OrderingOrderedNote}


class NoteForm(CrispyModelForm):
    class Meta:
        model = BookNote
        fields = ["note"]


class NoteInlineFormSet(InlineFormSet):
    def get_helper_layout_fields(self):
        return ["note", self.form_control_col4]


NoteFormSet = inlineformset_factory(
    Book, BookNote, formset=NoteInlineFormSet, form=NoteForm, fields=["note"], extra=1, can_delete=True
)


def _note_formsets() -> FormSets:
    return FormSets(formsets=OrderedDict(notes=FormSet(title="Notes", klass=NoteFormSet)))


# ── routes ───────────────────────────────────────────────────────────────────


def _policy(entry: Entry, key: str, cascade: bool | None) -> dict:
    actions = {key: CUSTOM} if entry.op == "custom" else {}
    if not actions and cascade is None:
        return {}
    return {"ancestor_policy": AncestorPolicy(actions=actions, cascade=cascade)}


def _build_chain(sfx: str, *, cascade: bool | None = None, provider: str | None = None):
    from crud_views.lib.crispy import CrispyViewMixin
    from crud_views.lib.formsets import FormSetMixin
    from crud_views_guardian.lib.viewset import GuardianViewSet

    ancestor_policy = {"ancestor_policy": AncestorPolicy(provider=provider)} if provider else {}
    pub = ViewSet(model=Publisher, name=f"aopub{sfx}", **ancestor_policy)
    book = ViewSet(
        model=Book, name=f"aobook{sfx}", parent=ParentViewSet(name=pub.name, attribute="publisher"), **ancestor_policy
    )
    leaf_models = _isolated_leaf_models()
    ns = SimpleNamespace(pub=pub, book=book, leaves={}, views={}, leaf_models=leaf_models)
    for index, entry in enumerate(INVENTORY):
        bases = tuple(import_string(base) for base in entry.bases)
        view_key = entry.key or next(b.cv_key for b in bases if getattr(b, "cv_key", None))
        vs_class = GuardianViewSet if entry.guardian else ViewSet
        if entry.leaf == "fragment":
            model, parent_vs, attribute = Book, pub, "publisher"
        elif entry.leaf == "resource":
            model, parent_vs, attribute = OrderingNoteFile, book, None
        elif entry.leaf == "note":
            model, parent_vs, attribute = BookNote, book, "book"
        else:
            model, parent_vs, attribute = leaf_models[entry.leaf], book, "book"
        options = _policy(entry, view_key, cascade)
        if entry.leaf == "resource":
            options["resource_permissions"] = {"view": "app.view_booknote"}
        leaf = vs_class(
            model=model,
            name=f"ao{index}{sfx}",
            parent=ParentViewSet(name=parent_vs.name, **({"attribute": attribute} if attribute else {})),
            **options,
        )
        attrs = {"cv_viewset": leaf, "cv_context_actions": [], "cv_list_actions": [], **entry.attrs}
        if entry.key:
            attrs.update(cv_key=entry.key, cv_path=entry.key)
        if "RedirectChildView" in entry.bases[-1]:
            attrs.update(cv_redirect="nowhere", cv_redirect_key="list")
        if entry.op == "write" and entry.leaf == "note":
            attrs["get_success_url"] = lambda self: "/done/"  # the leaf ViewSets register no list endpoint
        if entry.leaf == "fragment":
            bases = (CrispyViewMixin, FormSetMixin, *bases)
            attrs.update(fields=["title"], cv_formsets=_note_formsets())
        if entry.guard == "manage":
            view_class = leaf.get_view_class("manage")  # the automatic manage view of this ViewSet
            assert issubclass(view_class, bases[-1])
        else:
            view_class = type(f"Ordering{index}", bases, attrs)
        ns.leaves[entry.id] = leaf
        ns.views[entry.id] = view_class
    routed = [pub, book, *ns.leaves.values()]
    return ns, routed


@pytest.fixture(autouse=True)
def manage_group_gate(monkeypatch):
    """The test project makes manage public; here the local manage gate is the group (debug_only, DEBUG off)."""
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "debug_only")


def _leaf_vocabulary(ns):
    """Permission rows for the isolated leaf models, so their local permission gate is an ordinary 403."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    for model in ns.leaf_models.values():
        content_type = ContentType.objects.get_for_model(model)
        for action in ("add", "change", "delete", "view"):
            Permission.objects.get_or_create(
                content_type=content_type, codename=f"{action}_{model._meta.model_name}", defaults={"name": action}
            )


@contextmanager
def _chain(**options):
    with isolate_apps("tests.test1.app"), isolated_routes(lambda sfx: _build_chain(sfx, **options)) as ns:
        _leaf_vocabulary(ns)
        yield ns


@pytest.fixture
def chain(db):
    with _chain() as ns:
        yield ns


@pytest.fixture
def world(db):
    penguin = Publisher.objects.create(name="Penguin")
    other = Publisher.objects.create(name="Other")
    book = Book.objects.create(title="Hitchhiker", publisher=penguin)
    foreign = Book.objects.create(title="Foreign", publisher=other)
    return SimpleNamespace(penguin=penguin, other=other, book=book, foreign=foreign)


def _entry_url(chain, entry: Entry, publisher_pk, book_pk, leaf_pk=MISSING) -> str:
    leaf = chain.leaves[entry.id]
    kwargs = {f"{chain.pub.name}_pk": publisher_pk}
    if entry.leaf != "fragment":
        kwargs[f"{chain.book.name}_pk"] = book_pk
    elif entry.obj:
        leaf_pk = book_pk
    if entry.obj:
        kwargs["pk"] = leaf_pk if entry.leaf != "resource" else "nothing"
    view = chain.views[entry.id]
    key = next(k for k, v in leaf.get_all_views().items() if v is view)
    if "RedirectChildView" in entry.bases[-1]:
        kwargs.update(redirect="nowhere", redirect_key="list")
    if entry.id == "poly-create":
        kwargs["polymorphic_ctype_id"] = 1
    url = _url(leaf, key, **kwargs)
    if entry.leaf == "fragment":
        url += "?template=notes&pk=None&num=1&formset_parent_prefix_key="
    return url


def _request(client, entry: Entry, url):
    return client.post(url, {}) if entry.method == "post" else client.get(url)


# ── ordered events with poison ───────────────────────────────────────────────


class Poisoned(AssertionError):
    pass


@pytest.fixture
def trace(monkeypatch):
    """Ordered request events. ``trace.allow`` (a set) turns every other event into a raised ``Poisoned``."""
    state = SimpleNamespace(events=[], allow=None)

    def record(event):
        state.events.append(event)
        if state.allow is not None and event not in state.allow:
            raise Poisoned(f"reached {event} after the expected guard sequence {sorted(state.allow)}")

    def wrap(owner, name, label):
        original = getattr(owner, name)

        def spy(self, *args, **kwargs):
            record(label(self, *args, **kwargs) if callable(label) else (label,))
            return original(self, *args, **kwargs)

        monkeypatch.setattr(owner, name, spy)

    wrap(ViewSet, "get_queryset", lambda self, *a, **k: ("queryset", self.name))
    wrap(PermissionsMixin, "has_perm", lambda self, perm, *a, **k: ("model_perm", perm))
    wrap(AnonymousUser, "has_perm", lambda self, perm, *a, **k: ("model_perm", perm))
    wrap(ObjectPermissionChecker, "has_perm", lambda self, perm, *a, **k: ("object_perm", perm))
    wrap(CrudViewPermissionRequiredMixin, "has_permission", "local_permission")
    wrap(ManageView, "has_permission", "manage_gate")
    wrap(SingleObjectMixin, "get_object", "get_object")
    wrap(FormMixin, "get_form", "form")
    wrap(TemplateResponseMixin, "render_to_response", "render")
    wrap(FormSets, "get_template", "fragment_render")
    original_state = CrudView.cv_action_enabled.__func__

    def state_spy(cls, user, obj=None):
        record(("state",))
        return original_state(cls, user, obj)

    monkeypatch.setattr(CrudView, "cv_action_enabled", classmethod(state_spy))
    RESOURCE_EVENTS.clear()
    original_items, original_item = OrderingNoteFile.cv_get_items.__func__, OrderingNoteFile.cv_get_item.__func__

    def items_spy(cls, request, **kwargs):
        record(("resource", "items"))
        return original_items(cls, request, **kwargs)

    def item_spy(cls, request, pk, **kwargs):
        record(("resource", "item"))
        return original_item(cls, request, pk, **kwargs)

    monkeypatch.setattr(OrderingNoteFile, "cv_get_items", classmethod(items_spy))
    monkeypatch.setattr(OrderingNoteFile, "cv_get_item", classmethod(item_spy))
    return state


def _guard(chain, entry: Entry, *, upto: str) -> list[tuple]:
    """The expected guard event sequence for full cascade, up to and including the named stage."""
    nearest = "change" if entry.op in ("write", "custom") else "view"
    if entry.leaf == "fragment":
        steps = [("queryset", chain.pub.name), ("model_perm", f"app.{nearest}_publisher")]
        return steps[: {"outer": 2, "nearest": 2, "lookup": 1}[upto]]
    steps = [
        ("queryset", chain.pub.name),
        ("model_perm", "app.view_publisher"),
        ("queryset", chain.book.name),
        ("model_perm", f"app.{nearest}_book"),
    ]
    return steps[: {"outer": 2, "lookup": 3, "nearest": 4}[upto]]


# ── structural inventory ─────────────────────────────────────────────────────


@pytest.mark.parametrize("entry", INVENTORY, ids=ENTRY_IDS)
def test_inventory_names_the_guard_entry_of_each_mro(chain, entry):
    """The first ``dispatch`` in the endpoint's MRO is the documented bridge into the ancestor guard."""
    view_class = chain.views[entry.id]
    first = next(klass for klass in view_class.__mro__ if "dispatch" in vars(klass))
    assert f"{first.__name__}.dispatch" == GUARD_ENTRY[entry.guard]


# ── interleaved enforcement, full cascade ────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("entry", TWO_ANCESTORS, ids=lambda e: e.id)
def test_outer_denial_never_enters_the_deeper_queryset(chain, world, trace, entry):
    # every grant except the outer (higher) Publisher permission; the Book row does not exist
    user = _user(f"ao_outer_{entry.id}", (Book, "view"), (Book, "change"), (BookNote, "view"), (BookNote, "change"))
    expected = _guard(chain, entry, upto="outer")
    trace.allow = set(expected)
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, MISSING))
    assert response.status_code == 403
    assert trace.events == expected


@pytest.mark.django_db
@pytest.mark.parametrize("entry", INVENTORY, ids=ENTRY_IDS)
def test_nearest_denial_prevents_all_leaf_work(chain, world, trace, entry):
    perms = [(Publisher, "view"), (BookNote, "view"), (BookNote, "change"), (BookNote, "add"), (BookNote, "delete")]
    if entry.leaf == "fragment":
        perms += [(Book, "view")]  # the editor's own model permission; Publisher change is still missing
    user = _user(f"ao_nearest_{entry.id}", *perms)
    expected = _guard(chain, entry, upto="nearest")
    trace.allow = set(expected)
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, world.book.pk))
    assert response.status_code == 403
    assert trace.events == expected


@pytest.mark.django_db
@pytest.mark.parametrize("entry", TWO_ANCESTORS, ids=lambda e: e.id)
def test_mismatched_deeper_ancestor_is_404_before_leaf_work(chain, world, trace, entry):
    user = _user(f"ao_mismatch_{entry.id}", (Publisher, "view"), (Book, "view"), (Book, "change"))
    expected = _guard(chain, entry, upto="lookup")
    trace.allow = set(expected)
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, world.foreign.pk))
    assert response.status_code == 404
    assert trace.events == expected


@pytest.mark.django_db
@pytest.mark.parametrize("entry", INVENTORY, ids=ENTRY_IDS)
def test_successful_ancestry_reaches_the_local_stage(chain, world, trace, entry):
    perms = [(Publisher, "view"), (Publisher, "change"), (Book, "view"), (Book, "change")]
    if entry.leaf == "fragment":
        perms = [(Publisher, "view"), (Publisher, "change")]
    user = _user(f"ao_local_{entry.id}", *perms)
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, world.book.pk))
    assert response.status_code == entry.local
    guard = _guard(chain, entry, upto="nearest")
    assert trace.events[: len(guard)] == guard
    # the endpoint's own local stage ran, and only after the complete guard sequence
    assert trace.events[len(guard) :], "no local stage reached"
    ancestor_querysets = {("queryset", chain.pub.name), ("queryset", chain.book.name)}
    assert not ancestor_querysets & set(trace.events[len(guard) :])


# ── selection variants: nearest-only and all-none ────────────────────────────


@pytest.fixture
def nearest_only_chain(db):
    with _chain(cascade=False) as ns:
        yield ns


@pytest.fixture
def none_chain(db):
    with _chain(provider="none") as ns:
        yield ns


REPRESENTATIVE = [
    e
    for e in INVENTORY
    if e.id
    in {"plain-detail", "core-detail", "guardian-update", "manage", "resource-detail", "workflow", "core-ordered-up"}
]


@pytest.mark.django_db
@pytest.mark.parametrize("entry", REPRESENTATIVE, ids=lambda e: e.id)
def test_nearest_only_resolves_higher_ancestors_without_their_gate(nearest_only_chain, world, trace, entry):
    chain = nearest_only_chain
    user = _user(f"ao_nearest_only_{entry.id}", (Book, "view"), (Book, "change"))
    # deeper row missing: 404 at the Book lookup, the Publisher permission is never evaluated
    trace.allow = {("queryset", chain.pub.name), ("queryset", chain.book.name)}
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, MISSING))
    assert response.status_code == 404
    assert trace.events == [("queryset", chain.pub.name), ("queryset", chain.book.name)]
    # valid chain: the local stage follows the nearest gate only
    trace.allow, trace.events[:] = None, []
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, world.book.pk))
    assert response.status_code == entry.local
    assert ("model_perm", "app.view_publisher") not in trace.events
    nearest = "change" if entry.op in ("write", "custom") else "view"
    assert trace.events[:3] == [
        ("queryset", chain.pub.name),
        ("queryset", chain.book.name),
        ("model_perm", f"app.{nearest}_book"),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("entry", REPRESENTATIVE, ids=lambda e: e.id)
def test_all_none_chain_validates_relationships_then_reaches_local_work(none_chain, world, trace, entry):
    chain = none_chain
    user = _user(f"ao_none_{entry.id}")
    trace.allow = {("queryset", chain.pub.name), ("queryset", chain.book.name)}
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, world.foreign.pk))
    assert response.status_code == 404
    trace.allow, trace.events[:] = None, []
    response = _request(_client(user), entry, _entry_url(chain, entry, world.penguin.pk, world.book.pk))
    assert response.status_code == entry.local
    assert trace.events[:2] == [("queryset", chain.pub.name), ("queryset", chain.book.name)]
    assert len(trace.events) > 2


# ── writes: denial leaves no persisted state, hook or commit callback ────────


WRITES = [e for e in INVENTORY if e.leaf == "note" and e.op == "write"]


@pytest.mark.django_db
@pytest.mark.parametrize("entry", WRITES, ids=lambda e: e.id)
@pytest.mark.parametrize("scenario", ["outer", "nearest"])
def test_denied_writes_persist_nothing(chain, world, trace, entry, scenario, django_capture_on_commit_callbacks):
    note = BookNote.objects.create(book=world.book, note="kept")
    if scenario == "outer":
        user = _user(
            f"ao_wo_{entry.id}", (Book, "change"), (BookNote, "add"), (BookNote, "change"), (BookNote, "delete")
        )
        book_pk = MISSING
    else:
        user = _user(
            f"ao_wn_{entry.id}", (Publisher, "view"), (BookNote, "add"), (BookNote, "change"), (BookNote, "delete")
        )
        book_pk = world.book.pk
    url = _entry_url(chain, entry, world.penguin.pk, book_pk, leaf_pk=note.pk)
    trace.allow = set(_guard(chain, entry, upto=scenario))
    with django_capture_on_commit_callbacks() as callbacks:
        response = _client(user).post(url, {"note": "changed"})
    assert response.status_code == 403
    assert callbacks == []
    assert list(BookNote.objects.values_list("note", flat=True)) == ["kept"]


@pytest.mark.django_db
@pytest.mark.parametrize("entry", WRITES, ids=lambda e: e.id)
def test_authorized_write_reaches_the_local_lifecycle(chain, world, entry):
    """Control: with ancestry and local grants the same POST reaches the form lifecycle and its write."""
    from guardian.shortcuts import assign_perm

    note = BookNote.objects.create(book=world.book, note="kept")
    perms = [(Publisher, "view"), (Book, "change")]
    perms += [(BookNote, action) for action in ("add", "change", "delete", "view")]
    user = _user(f"ao_wok_{entry.id}", *perms)
    if entry.guardian:
        for action in ("change", "delete", "view"):
            assign_perm(chain.leaves[entry.id].permissions[action], user, note)
    url = _entry_url(chain, entry, world.penguin.pk, world.book.pk, leaf_pk=note.pk)
    response = _client(user).post(url, {"note": "changed"})
    assert response.status_code == 302, response.content[:300]
    expected = {"create": ["changed", "kept"], "update": ["changed"], "delete": []}[entry.id.split("-")[-1]]
    assert sorted(BookNote.objects.values_list("note", flat=True)) == expected


# ── Guardian ancestors: object gates interleave the same way ────────────────


@pytest.fixture
def guardian_chain():
    from crud_views.lib.views import CreateViewParentMixin
    from crud_views_guardian.lib.views import (
        GuardianCreateViewPermissionRequired,
        GuardianDetailViewPermissionRequired,
        GuardianListViewPermissionRequired,
    )
    from crud_views_guardian.lib.viewset import GuardianViewSet

    def build(sfx):
        pub = GuardianViewSet(model=Publisher, name=f"aogpub{sfx}")
        book = GuardianViewSet(
            model=Book, name=f"aogbook{sfx}", parent=ParentViewSet(name=pub.name, attribute="publisher")
        )
        leaf = GuardianViewSet(
            model=BookNote, name=f"aognote{sfx}", parent=ParentViewSet(name=book.name, attribute="book")
        )
        common = {"cv_viewset": leaf, "cv_context_actions": [], "cv_list_actions": []}
        type("L", (GuardianListViewPermissionRequired,), dict(common))
        type("D", (GuardianDetailViewPermissionRequired,), dict(common))
        type("C", (CreateViewParentMixin, GuardianCreateViewPermissionRequired), {**common, "fields": ["note"]})
        return SimpleNamespace(pub=pub, book=book, leaf=leaf), [pub, book, leaf]

    with isolated_routes(build) as ns:
        yield ns


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["list", "detail", "create"])
def test_guardian_outer_object_denial_never_enters_the_deeper_queryset(guardian_chain, world, trace, key):
    from guardian.shortcuts import assign_perm

    gc = guardian_chain
    user = _user(f"ao_g_outer_{key}")
    assign_perm(gc.book.permissions["view"], user, world.book)
    assign_perm(gc.book.permissions["change"], user, world.book)
    kwargs = {f"{gc.pub.name}_pk": world.penguin.pk, f"{gc.book.name}_pk": MISSING}
    if key == "detail":
        kwargs["pk"] = MISSING
    expected = [("queryset", gc.pub.name), ("object_perm", "app.view_publisher")]
    trace.allow = set(expected)
    assert _client(user).get(_url(gc.leaf, key, **kwargs)).status_code == 403
    assert trace.events == expected
    # control: with the Publisher object grant the Book lookup is reached (and misses → 404)
    assign_perm(gc.pub.permissions["view"], user, world.penguin)
    trace.allow = {*expected, ("queryset", gc.book.name)}
    trace.events[:] = []
    assert _client(user).get(_url(gc.leaf, key, **kwargs)).status_code == 404
    assert trace.events == [*expected, ("queryset", gc.book.name)]


# ── manage: ancestry plus the unchanged local settings/group gate ───────────


@pytest.mark.django_db
@pytest.mark.parametrize("entry", [e for e in INVENTORY if e.guard == "manage"], ids=lambda e: e.id)
def test_nested_manage_needs_ancestry_and_group(chain, world, trace, entry, settings):
    from crud_views.lib.settings import crud_views_settings

    url = _entry_url(chain, entry, world.penguin.pk, world.book.pk)
    member = _user(f"ao_mg_{entry.id}")
    member.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    # group membership does not bypass the ancestors …
    trace.allow = set(_guard(chain, entry, upto="outer"))
    assert _client(member).get(_entry_url(chain, entry, world.penguin.pk, MISSING)).status_code == 403
    # … and ancestry does not bypass the group gate
    reader = _user(f"ao_mr_{entry.id}", (Publisher, "view"), (Book, "view"))
    trace.allow, trace.events[:] = None, []
    assert _client(reader).get(url).status_code == 403
    assert trace.events.index(("manage_gate",)) > trace.events.index(("model_perm", "app.view_book"))
    # both: the manage page renders
    for model, action in ((Publisher, "view"), (Book, "view")):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(model)
        member.user_permissions.add(Permission.objects.get(content_type=ct, codename=f"{action}_{ct.model}"))
    assert _client(member).get(url).status_code == 200
