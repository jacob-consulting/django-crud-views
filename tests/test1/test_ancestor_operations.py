"""Exact operation classification of nested endpoints for ancestor authorization.

A finite set of shipped view families is Read or Write; an exact registered action entry replaces the family pair;
every other nested endpoint needs an action entry. Classification follows the class family only: never ``cv_key``,
``cv_permission``, the HTTP method or a method body. Action keys are validated against literal registrations once
the registry is complete (``crud_views.E321``).
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.views import generic

from crud_views.checks import check_ancestry
from crud_views.lib.view import CrudView
from crud_views.lib.views import (
    ActionView,
    ActionViewPermissionRequired,
    CardListView,
    CardListViewPermissionRequired,
    CreateView,
    CreateViewPermissionRequired,
    DeleteView,
    DeleteViewPermissionRequired,
    DetailView,
    DetailViewPermissionRequired,
    ListView,
    ListViewPermissionRequired,
    RedirectChildView,
    UpdateView,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.action_ordered import (
    OrderedDownView,
    OrderedUpDownPermissionRequired,
    OrderedUpView,
    OrderedUpViewPermissionRequired,
)
from crud_views.lib.views.form import (
    CustomFormNoObjectView,
    CustomFormNoObjectViewPermissionRequired,
    CustomFormView,
    CustomFormViewPermissionRequired,
)
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet
from crud_views.lib.viewset.ancestry import operation_permissions, validate_registered_actions
from crud_views_guardian.lib.views import (
    GuardianActionViewPermissionRequired,
    GuardianCardListViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianListViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
)
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_object_detail.lib.views import ObjectDetailView, ObjectDetailViewPermissionRequired
from crud_views_polymorphic.lib.create import PolymorphicCreateView, PolymorphicCreateViewPermissionRequired
from crud_views_polymorphic.lib.create_select import (
    PolymorphicCreateSelectView,
    PolymorphicCreateSelectViewPermissionRequired,
)
from crud_views_polymorphic.lib.delete import PolymorphicDeleteView, PolymorphicDeleteViewPermissionRequired
from crud_views_polymorphic.lib.detail import PolymorphicDetailView, PolymorphicDetailViewPermissionRequired
from crud_views_polymorphic.lib.update import PolymorphicUpdateView, PolymorphicUpdateViewPermissionRequired
from crud_views_workflow.lib.views import WorkflowView, WorkflowViewPermissionRequired
from tests.test1.ancestor_cases import ancestor_scope
from tests.test1.app.models import Book, BookNote, Publisher

READ = AncestorPermissions(nearest="view", higher="view")
WRITE = AncestorPermissions(nearest="change", higher="view")
CUSTOM = AncestorPermissions(nearest="approve", higher="view")
STRICT = AncestorPermissions(nearest="change", higher="change")

READ_FAMILIES = [
    ListView,
    ListViewPermissionRequired,
    CardListView,
    CardListViewPermissionRequired,
    DetailView,
    DetailViewPermissionRequired,
    ObjectDetailView,
    ObjectDetailViewPermissionRequired,
    PolymorphicDetailView,
    PolymorphicDetailViewPermissionRequired,
    RedirectChildView,
]
WRITE_FAMILIES = [
    CreateView,
    CreateViewPermissionRequired,
    UpdateView,
    UpdateViewPermissionRequired,
    DeleteView,
    DeleteViewPermissionRequired,
    PolymorphicCreateView,
    PolymorphicCreateViewPermissionRequired,
    PolymorphicUpdateView,
    PolymorphicUpdateViewPermissionRequired,
    PolymorphicDeleteView,
    PolymorphicDeleteViewPermissionRequired,
    PolymorphicCreateSelectView,
    PolymorphicCreateSelectViewPermissionRequired,
    OrderedUpView,
    OrderedUpViewPermissionRequired,
    OrderedDownView,
    OrderedUpDownPermissionRequired,
]
GUARDIAN_READ_FAMILIES = [
    GuardianListViewPermissionRequired,
    GuardianCardListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
]
GUARDIAN_WRITE_FAMILIES = [
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
]


class _CustomTemplateView(CrudView, generic.TemplateView):
    """An endpoint outside every shipped family."""

    cv_key = "custom"
    cv_path = "custom"


UNCLASSIFIED = [
    CustomFormView,
    CustomFormViewPermissionRequired,
    CustomFormNoObjectView,
    CustomFormNoObjectViewPermissionRequired,
    WorkflowView,
    WorkflowViewPermissionRequired,
    ActionView,
    ActionViewPermissionRequired,
    GuardianActionViewPermissionRequired,
    _CustomTemplateView,
]

# (variant, extra class attributes): a renamed key and a misleading local permission keep the family
VARIANTS = [
    ("as shipped", {}),
    ("renamed key", {"cv_key": "renamed"}),
    ("other permission", {"cv_permission": "delete"}),
    ("read permission", {"cv_permission": "view"}),
]


def nested(scope, viewset_class=None, depth: int = 1, provider=None, **policy):
    """Publisher → Book (depth 1) or Publisher → Book → BookNote (depth 2); return the requested ViewSet.

    ``provider`` applies to every ancestor (``"none"`` builds all-none ancestry); ``policy`` configures the requested
    ViewSet's own ``ancestor_policy``.
    """
    ancestor_policy = AncestorPolicy(provider=provider)
    publisher = scope.viewset(
        viewset_class, model=Publisher, name=scope.name("ancoppub"), ancestor_policy=ancestor_policy
    )
    book_kwargs = {
        "model": Book,
        "name": scope.name("ancopbook"),
        "parent": ParentViewSet(name=publisher.name, attribute="publisher"),
    }
    if depth == 1:
        return scope.viewset(viewset_class, ancestor_policy=AncestorPolicy(**policy), **book_kwargs)
    book = scope.viewset(viewset_class, ancestor_policy=ancestor_policy, **book_kwargs)
    return scope.viewset(
        viewset_class,
        model=BookNote,
        name=scope.name("ancopnote"),
        parent=ParentViewSet(name=book.name, attribute="book"),
        ancestor_policy=AncestorPolicy(**policy),
    )


def e321(viewset) -> list[str]:
    return [m.msg for m in check_ancestry() if m.id == "crud_views.E321" and f"{viewset.name!r}" in m.msg]


@pytest.mark.django_db
@pytest.mark.parametrize(("variant", "attrs"), VARIANTS, ids=[v for v, _ in VARIANTS])
@pytest.mark.parametrize(
    ("family", "expected", "guardian"),
    [(f, READ, False) for f in READ_FAMILIES]
    + [(f, WRITE, False) for f in WRITE_FAMILIES]
    + [(f, READ, True) for f in GUARDIAN_READ_FAMILIES]
    + [(f, WRITE, True) for f in GUARDIAN_WRITE_FAMILIES],
    ids=lambda value: getattr(value, "__name__", None) if isinstance(value, type) else None,
)
def test_family_classification_survives_key_and_permission_changes(
    family, expected, guardian, variant, attrs, django_assert_num_queries
):
    with ancestor_scope() as scope:
        viewset = nested(scope, GuardianViewSet if guardian else None)
        # a project subclass of the shipped class, possibly renamed or with a misleading local permission
        view_class = scope.view(family, viewset, **attrs)
        with django_assert_num_queries(0):
            # the classification has no request input: a form GET and its POST share one pair
            assert operation_permissions(view_class) == expected
            validate_registered_actions(viewset)
        assert e321(viewset) == []


@pytest.mark.django_db
@pytest.mark.parametrize("guardian", [False, True], ids=["core", "guardian"])
def test_manage_endpoints_are_read(guardian):
    with ancestor_scope() as scope:
        viewset = nested(scope, GuardianViewSet if guardian else None)
        manage = viewset.get_all_views()["manage"]
        assert operation_permissions(manage) == READ
        renamed = scope.view(manage.__mro__[1], viewset, cv_key="settings")
        assert operation_permissions(renamed) == READ


@pytest.mark.django_db
def test_top_level_endpoints_have_no_operation_requirement():
    with ancestor_scope() as scope:
        viewset = scope.viewset(model=Publisher, name=scope.name("ancoptop"))
        for family in (ListView, CreateView, ActionView, CustomFormView, _CustomTemplateView):
            assert operation_permissions(scope.view(family, viewset, cv_key=f"{family.__name__.lower()}")) is None
        validate_registered_actions(viewset)
        assert e321(viewset) == []


@pytest.mark.django_db
def test_policy_pairs_and_exact_action_entries():
    with ancestor_scope() as scope:
        viewset = nested(scope, read=STRICT, write=READ, actions={"detail": WRITE, "approve": CUSTOM})
        list_view = scope.view(ListView, viewset)
        detail = scope.view(DetailView, viewset)
        create = scope.view(CreateView, viewset)
        approve = scope.view(ActionView, viewset, cv_key="approve")
        assert operation_permissions(list_view) == STRICT  # the ViewSet's Read pair replaces the global one
        assert operation_permissions(create) == READ  # the ViewSet's Write pair replaces the global one
        assert operation_permissions(detail) == WRITE  # an exact entry wins over the family pair
        assert operation_permissions(approve) == CUSTOM
        validate_registered_actions(viewset)
        assert e321(viewset) == []


@pytest.mark.django_db
@pytest.mark.parametrize("ancestry", ["depth 1", "depth 2", "all none"])
@pytest.mark.parametrize("family", UNCLASSIFIED, ids=lambda family: family.__name__)
def test_custom_forms_workflow_and_misleading_actions_require_entries(family, ancestry, django_assert_num_queries):
    with ancestor_scope() as scope:
        depth = 1 if ancestry == "depth 1" else 2
        provider = "none" if ancestry == "all none" else None
        viewset = nested(scope, depth=depth, provider=provider)
        # the generic action is named like a Read endpoint and asks locally for "view": still unclassified
        view_class = scope.view(family, viewset, cv_key="detail", cv_permission="view")
        with django_assert_num_queries(0):
            with pytest.raises(ImproperlyConfigured, match=r"ancestor_policy.actions\['detail'\]"):
                operation_permissions(view_class)
            with pytest.raises(ImproperlyConfigured, match=viewset.name):
                validate_registered_actions(viewset)
            messages = e321(viewset)
        assert len(messages) == 1
        assert "'detail'" in messages[0]

    with ancestor_scope() as scope:
        viewset = nested(scope, depth=depth, provider=provider, actions={"detail": CUSTOM})
        view_class = scope.view(family, viewset, cv_key="detail", cv_permission="view")
        assert operation_permissions(view_class) == CUSTOM
        validate_registered_actions(viewset)
        assert e321(viewset) == []


@pytest.mark.django_db
def test_card_policy_uses_literal_registration():
    with ancestor_scope() as scope:
        # only "card" registered: its entry is valid and used
        viewset = nested(scope, actions={"card": CUSTOM})
        card = scope.view(CardListView, viewset)
        validate_registered_actions(viewset)
        assert e321(viewset) == []
        assert operation_permissions(card) == CUSTOM
        # navigation keeps its list → card fallback, and the fallback target keeps the Card policy
        assert viewset.get_view_class("list") is card
        assert viewset.get_router_name("list").endswith("-card")
        assert operation_permissions(viewset.get_view_class("list")) == CUSTOM

    with ancestor_scope() as scope:
        # only "card" registered: an entry for the navigation alias "list" is unknown
        viewset = nested(scope, actions={"list": CUSTOM})
        card = scope.view(CardListView, viewset)
        with pytest.raises(ImproperlyConfigured, match=r"'list'"):
            validate_registered_actions(viewset)
        assert len(e321(viewset)) == 1
        assert operation_permissions(card) == READ

    with ancestor_scope() as scope:
        # both registered: each entry affects only its own endpoint
        viewset = nested(scope, actions={"card": CUSTOM, "list": STRICT})
        card = scope.view(CardListView, viewset)
        list_view = scope.view(ListView, viewset)
        validate_registered_actions(viewset)
        assert operation_permissions(card) == CUSTOM
        assert operation_permissions(list_view) == STRICT

    with ancestor_scope() as scope:
        # a Card actually registered as "list": the "list" entry is valid, the family stays Read
        viewset = nested(scope)
        card_as_list = scope.view(CardListView, viewset, cv_key="list")
        assert operation_permissions(card_as_list) == READ
    with ancestor_scope() as scope:
        viewset = nested(scope, actions={"list": CUSTOM})
        card_as_list = scope.view(CardListView, viewset, cv_key="list")
        validate_registered_actions(viewset)
        assert e321(viewset) == []
        assert operation_permissions(card_as_list) == CUSTOM


@pytest.mark.django_db
def test_registration_checks_wait_until_complete():
    with ancestor_scope() as scope:
        # the policy may name an endpoint before its view class is defined
        viewset = nested(scope, actions={"approve": CUSTOM})
        scope.view(ListView, viewset)
        assert "approve" not in viewset.get_all_views()
        approve = scope.view(ActionView, viewset, cv_key="approve")
        validate_registered_actions(viewset)
        assert e321(viewset) == []
        assert operation_permissions(approve) == CUSTOM

    with ancestor_scope() as scope:
        # registration completed without the declared endpoint: reported by the check and the runtime guard
        viewset = nested(scope, actions={"approve": CUSTOM})
        scope.view(ListView, viewset)
        with pytest.raises(ImproperlyConfigured, match=r"'approve'"):
            validate_registered_actions(viewset)
        messages = e321(viewset)
        assert len(messages) == 1
        assert "'approve'" in messages[0]

    with ancestor_scope() as scope:
        # adding a real List later never retargets the Card override
        viewset = nested(scope, actions={"card": CUSTOM})
        card = scope.view(CardListView, viewset)
        assert operation_permissions(viewset.get_view_class("list")) == CUSTOM
        list_view = scope.view(ListView, viewset)
        assert viewset.get_view_class("list") is list_view
        assert operation_permissions(list_view) == READ
        assert operation_permissions(card) == CUSTOM
        validate_registered_actions(viewset)
