"""Guardian grants are shared by one actor; destination decisions remain independent."""

from unittest.mock import Mock, call

import guardian.core
import pytest
from django.contrib.auth.models import AnonymousUser, Group, User
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from guardian.conf import settings as guardian_settings
from guardian.shortcuts import assign_perm, remove_perm
from guardian.utils import get_anonymous_user

from crud_views.lib.link_access import _LINK_ALLOWED, _LINK_PERMISSION, _LINK_STATE, _link_access
from crud_views_guardian.lib.ancestors import _guardian_ancestor_has_permission
from tests.test1.app.models import Book, Publisher
from tests.test1.app.views import (
    GuardianPublisherDetailView,
    GuardianPublisherUpdateView,
    cv_guardian_book,
    cv_guardian_publisher,
)


@pytest.fixture
def checker_factory(monkeypatch):
    """Observe construction and evaluation without replacing Guardian's grant loading."""
    real_checker = guardian.core.ObjectPermissionChecker

    def build(user):
        checker = real_checker(user)
        checker.has_perm = Mock(wraps=checker.has_perm)
        return checker

    factory = Mock(side_effect=build)
    monkeypatch.setattr(guardian.core, "ObjectPermissionChecker", factory)
    return factory


@pytest.mark.django_db
@pytest.mark.parametrize("grant_source", ["direct", "group"])
def test_checker_reused_across_own_and_ancestor_checks(checker_factory, grant_source):
    actor = User.objects.create_user(username="shared-checker")
    obj = Publisher.objects.create(name="shared grants")
    grantee = actor
    if grant_source == "group":
        grantee = Group.objects.create(name="shared grants")
        actor.groups.add(grantee)
    assign_perm("app.view_publisher", grantee, obj)
    request = RequestFactory().get("/")
    request.user = actor
    view = GuardianPublisherDetailView()
    view.setup(request, pk=obj.pk)

    assert GuardianPublisherDetailView.cv_has_access(actor, obj) is True
    assert view.get_object().pk == obj.pk
    for rendering_view in (None, view):
        assert (
            _guardian_ancestor_has_permission(
                cv_guardian_publisher, actor, "app.view_publisher", obj, view=rendering_view
            )
            is True
        )

    checker_factory.assert_called_once_with(actor)
    checker = actor._cv_guardian_checker
    assert checker.user is actor
    assert checker.has_perm.call_args_list == [
        call("view_publisher", obj),
        call("view_publisher", obj),
        call("app.view_publisher", obj),
        call("app.view_publisher", obj),
    ]
    assert "_cv_guardian_ancestor_checker" not in vars(view)


@pytest.mark.django_db
def test_checker_separates_users_and_objects(checker_factory, django_assert_num_queries):
    actor = User.objects.create_user(username="first-checker")
    other_actor = User.objects.create_user(username="second-checker")
    obj = Publisher.objects.create(name="first row")
    other_obj = Publisher.objects.create(name="second row")
    colliding = Book.objects.create(pk=obj.pk, title="other model", publisher=obj)
    equivalent = Publisher.objects.get(pk=obj.pk)
    assign_perm("app.view_publisher", actor, obj)
    assign_perm("app.view_publisher", other_actor, other_obj)
    assign_perm("app.view_book", other_actor, colliding)

    assert GuardianPublisherDetailView.cv_has_access(actor, obj) is True
    # An equivalent ORM instance reuses loaded grants, without a second database read.
    with django_assert_num_queries(0):
        assert GuardianPublisherDetailView.cv_has_access(actor, equivalent) is True
    assert equivalent is not obj
    assert GuardianPublisherDetailView.cv_has_access(actor, other_obj) is False
    assert _guardian_ancestor_has_permission(cv_guardian_book, actor, "app.view_book", colliding, view=None) is False
    assert GuardianPublisherDetailView.cv_has_access(other_actor, obj) is False
    assert GuardianPublisherDetailView.cv_has_access(other_actor, other_obj) is True
    assert (
        _guardian_ancestor_has_permission(cv_guardian_book, other_actor, "app.view_book", colliding, view=None) is True
    )

    assert checker_factory.call_args_list == [call(actor), call(other_actor)]
    assert actor._cv_guardian_checker is not other_actor._cv_guardian_checker
    assert actor._cv_guardian_checker.has_perm.call_count == 4
    assert other_actor._cv_guardian_checker.has_perm.call_count == 3


@pytest.mark.django_db
def test_targets_keep_distinct_permissions_and_state(monkeypatch, checker_factory, django_assert_num_queries):
    actor = User.objects.create_user(username="distinct-destinations")
    obj = Publisher.objects.create(name="stateful destination")
    obj.action_allowed = True
    assign_perm("app.view_publisher", actor, obj)
    detail, edit = GuardianPublisherDetailView, GuardianPublisherUpdateView
    hooks = Mock()
    for name, target in (("detail", detail), ("edit", edit)):
        permission = Mock(wraps=target.cv_has_access)
        state = Mock(side_effect=lambda user, row: row.action_allowed)
        hooks.attach_mock(permission, f"{name}_permission")
        hooks.attach_mock(state, f"{name}_state")
        monkeypatch.setattr(target, "cv_has_access", permission)
        monkeypatch.setattr(target, "cv_action_enabled", state)

    assert _link_access(detail, actor, obj) == _LINK_ALLOWED
    assert _link_access(edit, actor, obj) == _LINK_PERMISSION
    obj.action_allowed = False
    with django_assert_num_queries(0):
        assert _link_access(detail, actor, obj) == _LINK_STATE
        assert _link_access(edit, actor, obj) == _LINK_PERMISSION
    obj.action_allowed = True
    assert _link_access(detail, actor, obj) == _LINK_ALLOWED

    assert hooks.mock_calls == [
        call.detail_permission(actor, obj),
        call.detail_state(actor, obj),
        call.edit_permission(actor, obj),
        call.detail_permission(actor, obj),
        call.detail_state(actor, obj),
        call.edit_permission(actor, obj),
        call.detail_permission(actor, obj),
        call.detail_state(actor, obj),
    ]
    assert hooks.edit_state.call_count == 0
    checker_factory.assert_called_once_with(actor)
    assert actor._cv_guardian_checker.has_perm.call_count == 5


@pytest.mark.django_db
def test_anonymous_direct_hook_reuses_checker(monkeypatch, checker_factory):
    backing = User.objects.create_user(username="checker-anonymous")
    monkeypatch.setattr(guardian_settings, "ANONYMOUS_USER_NAME", backing.username)
    assert get_anonymous_user().pk == backing.pk
    obj = Publisher.objects.create(name="anonymous-readable")
    assign_perm("app.view_publisher", backing, obj)
    actor = AnonymousUser()

    for _ in range(2):
        assert GuardianPublisherDetailView.cv_has_access(actor, obj) is True
        assert GuardianPublisherUpdateView.cv_has_access(actor, obj) is False

    checker_factory.assert_called_once_with(actor)
    assert actor._cv_guardian_checker.user.pk == backing.pk
    assert actor._cv_guardian_checker.has_perm.call_count == 4
    assert "_cv_guardian_checker" not in vars(backing)


@pytest.mark.django_db
@pytest.mark.parametrize("grant_source", ["direct", "group"])
@pytest.mark.parametrize("initial_grant", [False, True], ids=["added", "revoked"])
def test_loaded_grants_survive_same_user_mutation(grant_source, initial_grant):
    actor = User.objects.create_user(username="retained-grants")
    obj = Publisher.objects.create(name="mutated grants")
    grantee = actor
    if grant_source == "group":
        grantee = Group.objects.create(name="retained grants")
        actor.groups.add(grantee)
    if initial_grant:
        assign_perm("app.view_publisher", grantee, obj)

    assert GuardianPublisherDetailView.cv_has_access(actor, obj) is initial_grant
    checker = actor._cv_guardian_checker
    mutate = remove_perm if initial_grant else assign_perm
    mutate("app.view_publisher", grantee, obj)

    # Keeping the Python user keeps both loaded grants and loaded absences.
    assert GuardianPublisherDetailView.cv_has_access(actor, obj) is initial_grant
    assert actor._cv_guardian_checker is checker
    fresh = User.objects.get(pk=actor.pk)
    assert fresh is not actor
    assert GuardianPublisherDetailView.cv_has_access(fresh, obj) is not initial_grant
    assert fresh._cv_guardian_checker is not checker


@pytest.mark.django_db
@pytest.mark.parametrize("grant_source", ["direct", "group"])
def test_client_requests_get_distinct_users_and_checkers(grant_source):
    actor = User.objects.create_user(username="request-checkers")
    obj = Publisher.objects.create(name="request ownership")
    grantee = actor
    if grant_source == "group":
        grantee = Group.objects.create(name="request grants")
        actor.groups.add(grantee)
    assign_perm("app.view_publisher", grantee, obj)
    client = Client()
    client.force_login(actor)
    url = reverse(cv_guardian_publisher.get_router_name("detail"), kwargs={cv_guardian_publisher.pk_name: obj.pk})

    first_response, second_response = client.get(url), client.get(url)
    assert first_response.status_code == second_response.status_code == 200
    first, second = first_response.wsgi_request.user, second_response.wsgi_request.user
    assert isinstance(first, SimpleLazyObject) and isinstance(second, SimpleLazyObject)
    assert first.pk == second.pk == actor.pk  # Force lazy resolution before identity inspection.
    assert first is not second
    assert first._wrapped is not second._wrapped
    assert first._wrapped is not actor and second._wrapped is not actor
    assert first._cv_guardian_checker is first._wrapped._cv_guardian_checker
    assert second._cv_guardian_checker is second._wrapped._cv_guardian_checker
    assert first._cv_guardian_checker is not second._cv_guardian_checker


@pytest.mark.django_db
@pytest.mark.parametrize("grant_source", ["direct", "group"])
def test_next_request_observes_revocation(grant_source):
    actor = User.objects.create_user(username="next-request-revocation")
    obj = Publisher.objects.create(name="revoked next request")
    grantee = actor
    if grant_source == "group":
        grantee = Group.objects.create(name="revoked grants")
        actor.groups.add(grantee)
    assign_perm("app.view_publisher", grantee, obj)
    client = Client()
    client.force_login(actor)
    url = reverse(cv_guardian_publisher.get_router_name("detail"), kwargs={cv_guardian_publisher.pk_name: obj.pk})

    first = client.get(url)
    assert first.status_code == 200
    remove_perm("app.view_publisher", grantee, obj)
    assert GuardianPublisherDetailView.cv_has_access(first.wsgi_request.user, obj) is True
    second = client.get(url)
    assert second.status_code == 403
    assert first.wsgi_request.user.pk == second.wsgi_request.user.pk == actor.pk
