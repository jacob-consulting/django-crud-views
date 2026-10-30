"""Independent database evidence: colliding identities, trusted write routing and Guardian projection."""

from contextlib import contextmanager

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, router, transaction
from django.test import Client

from crud_views.lib.views.delete import DeleteView
from tests.test1.app.models import Book, Contract, Publisher
from tests.test1.app.views import PublisherProtectedDeleteView

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "shard"])
ALIASES = ["default", "shard"]


def _world(using, *, protected=False):
    root = Publisher.objects.using(using).create(pk=41, name=f"{using} publisher")
    Book.objects.using(using).create(pk=71, publisher_id=root.pk, title=f"{using} child")
    if protected:
        Contract.objects.using(using).create(pk=81, publisher_id=root.pk, title=f"{using} secret")
    return root


def _actor(using, **kwargs):
    return User.objects.db_manager(using).create_user(pk=51, username=f"{using} actor", **kwargs)


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("protected", [False, True])
def test_core_alias_request_uses_only_selected_protection(database_routes, using, protected):
    other = next(alias for alias in ALIASES if alias != using)
    target = _world(using, protected=protected)
    untouched = _world(other, protected=not protected)
    with database_routes(using):
        actor = _actor(using, is_superuser=True, is_staff=True)
        client = Client()
        client.force_login(actor)
        response = client.get(f"/publisher_cascade/{target.pk}/delete/")
        assert response.status_code == 200
        assert response.context["has_protected_objects"] is protected
        response = client.post(f"/publisher_cascade/{target.pk}/delete/", {"confirm": "on"})
        assert response.status_code == (200 if protected else 302)
    assert Publisher.objects.using(using).filter(pk=41).exists() is protected
    assert Publisher.objects.using(other).get(pk=untouched.pk).name == f"{other} publisher"
    assert Book.objects.using(other).get(pk=71).title == f"{other} child"


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("atomic", [False, True])
@pytest.mark.parametrize("custom", [False, True])
def test_routing_atomic_and_commit_pin_once(monkeypatch, using, atomic, custom):
    other = next(alias for alias in ALIASES if alias != using)
    target = _world(using)
    _world(other, protected=True)
    observations = []
    original_delete = Publisher.delete
    if custom:

        def delete(self, *, using):
            observations.append(("delete", using, connections[using].in_atomic_block))
            return original_delete(self, using=using)

        monkeypatch.setattr(Publisher, "delete", delete)

    class Routed(PublisherProtectedDeleteView):
        cv_atomic = atomic

        def cv_get_db_alias(self):
            observations.append(("selector", self.object.pk))
            return using

        @contextmanager
        def cv_get_atomic(self):
            assert self.cv_get_delete_db_alias() == using
            with super().cv_get_atomic():
                observations.append(("atomic", connections[using].in_atomic_block))
                yield

        def cv_form_valid_hook(self, context):
            observations.append(("hook", self.object.pk, connections[using].in_atomic_block))

        def cv_on_commit(self, context):
            observations.append(("commit", connections[using].in_atomic_block))

    view = Routed()
    view.object = target
    assert not view._cv_inspect_deletion().related.protected
    # Holding the other connection proves callback registration does not silently default to it.
    with transaction.atomic(using=other):
        view.cv_form_valid_process({})
        assert observations[-1] == ("commit", False)
    assert [event for event in observations if event[0] == "selector"] == [("selector", 41)]
    assert ("hook", None, atomic) in observations
    assert ("atomic", atomic) in observations
    if custom:
        assert ("delete", using, atomic) in observations
    assert not Publisher.objects.using(using).filter(pk=41).exists()
    assert Publisher.objects.using(other).filter(pk=41).exists()


@pytest.mark.parametrize("using", ALIASES)
def test_routing_instance_hint_overrides_read_alias(monkeypatch, using):
    read = next(alias for alias in ALIASES if alias != using)
    loaded = _world(read, protected=True)
    _world(using)
    # These cached read-side relations must never seed the write-side inspection.
    loaded._prefetched_objects_cache = {"contracts": list(loaded.contracts.using(read).all())}
    seen = []

    class WriteRouter:
        def db_for_write(self, model, **hints):
            seen.append((model, hints.get("instance")))
            return using

    monkeypatch.setattr(router, "routers", [WriteRouter()])
    view = DeleteView()
    view.object = loaded
    inspection = view._cv_inspect_deletion()
    assert not inspection.related.protected
    assert all(obj._state.db == using for obj in list(view._walk_nested(inspection.related.tree))[1:])
    view.cv_form_valid_process({})
    assert seen == [(Publisher, loaded)]
    assert Publisher.objects.using(read).filter(pk=41).exists()
    assert not Publisher.objects.using(using).filter(pk=41).exists()


@pytest.mark.parametrize("atomic", [False, True])
def test_alias_direct_process_pins_before_pk_clear(atomic):
    target = _world("shard")
    calls = []

    class Direct(DeleteView):
        cv_atomic = atomic

        def cv_get_db_alias(self):
            calls.append(self.object.pk)
            return "shard"

    view = Direct()
    view.object = target
    view.cv_form_valid_process({})
    assert calls == [41]
    assert target.pk is None
    assert view.cv_get_delete_db_alias() == "shard"


@pytest.mark.parametrize("alias", [None, "", "missing", 3])
def test_alias_invalid_selector_fails_before_mutation(alias):
    target = _world("default")
    view = DeleteView()
    view.object = target
    view.cv_get_db_alias = lambda: alias
    with pytest.raises(ImproperlyConfigured, match="configured database"):
        view.cv_form_valid_process({})
    assert Publisher.objects.filter(pk=41).exists()


def test_alias_unresolved_view_diagnostic():
    for target in [None, Publisher(), Publisher(pk=41)]:
        view = DeleteView()
        view.object = target
        with pytest.raises(ImproperlyConfigured, match="saved self.object"):
            view.cv_form_valid_process({})


def test_alias_incompatible_custom_signature_never_runs(monkeypatch):
    target = _world("default")
    calls = []

    def delete(self):
        calls.append(self.pk)

    monkeypatch.setattr(Publisher, "delete", delete)
    view = DeleteView()
    view.object = target
    with pytest.raises(ImproperlyConfigured, match="using"):
        view.cv_form_valid_process({})
    assert calls == []
    assert Publisher.objects.filter(pk=41).exists()


def _grant(actor, obj, codename):
    from guardian.shortcuts import assign_perm

    assign_perm(codename, actor, obj)


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize("kind", ["object", "group", "global", "group-global", "superuser"])
def test_guardian_real_requests_colocate_actor_grants_and_labels(database_routes, using, kind):
    other = next(alias for alias in ALIASES if alias != using)
    target = _world(using, protected=True)
    _world(other, protected=True)
    with database_routes(using):
        actor = _actor(using, is_superuser=kind == "superuser")
        _grant(actor, target, "delete_publisher")
        blocker = Contract.objects.get(pk=81)
        if kind == "object":
            _grant(actor, blocker, "view_contract")
        elif kind in {"group", "group-global"}:
            group = Group.objects.create(name="preview group")
            actor.groups.add(group)
            if kind == "group":
                _grant(group, blocker, "view_contract")
            else:
                group.permissions.add(Permission.objects.get(codename="view_contract"))
        elif kind == "global":
            actor.user_permissions.add(Permission.objects.get(codename="view_contract"))
        from tests.test1.app.views import GuardianPublisherCascadeDeleteView

        previous = GuardianPublisherCascadeDeleteView.cv_guardian_accept_global_perms
        GuardianPublisherCascadeDeleteView.cv_guardian_accept_global_perms = kind in {"global", "group-global"}
        try:
            client = Client()
            client.force_login(actor)
            response = client.get(f"/guardian_publisher_cascade/{target.pk}/delete/")
        finally:
            GuardianPublisherCascadeDeleteView.cv_guardian_accept_global_perms = previous
        assert response.status_code == 200
        assert response.context["has_protected_objects"] is True
        assert [str(obj) for obj in response.context["protected_objects"]] == [f"{using} secret"]
        assert f"{other} secret" not in response.content.decode()


@pytest.mark.parametrize("using", ALIASES)
def test_guardian_other_alias_grant_never_reveals_colliding_label(database_routes, using):
    other = next(alias for alias in ALIASES if alias != using)
    target = _world(using, protected=True)
    _world(other, protected=True)
    with database_routes(other):
        other_actor = _actor(other)
        _grant(other_actor, Contract.objects.get(pk=81), "view_contract")
    with database_routes(using):
        actor = _actor(using)
        assert actor.pk == other_actor.pk
        _grant(actor, target, "delete_publisher")
        client = Client()
        client.force_login(actor)
        response = client.get(f"/guardian_publisher_cascade/{target.pk}/delete/")
        assert response.status_code == 200
        assert response.context["has_protected_objects"] is True
        assert response.context["protected_objects"] == []
        assert "secret" not in response.content.decode()


@pytest.mark.parametrize("using", ALIASES)
@pytest.mark.parametrize(
    "misroute",
    [
        "actor",
        "contenttype",
        "user-grant",
        "group-grant",
        "user",
        "group",
        "permission",
        "user-groups",
        "user-permissions",
        "group-permissions",
        "hinted-groups",
        "hinted-permissions",
    ],
)
@pytest.mark.parametrize("kind", ["superuser", "global", "object", "through"])
def test_guardian_topology_mismatch_hides_every_fast_path(database_routes, monkeypatch, using, misroute, kind):
    from django.contrib.contenttypes.models import ContentType
    from guardian.models import GroupObjectPermission, UserObjectPermission

    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin
    from tests.test1.app.models import Genre

    other = next(alias for alias in ALIASES if alias != using)
    _world(using, protected=True)
    _world(other, protected=True)
    with database_routes(other):
        _actor(other, is_superuser=True)
    with database_routes(using):
        actor = _actor(using, is_superuser=kind in {"superuser", "through"})
        blocker = Contract.objects.get(pk=81)
        if kind == "object":
            _grant(actor, blocker, "view_contract")
        if kind == "global":
            actor.user_permissions.add(Permission.objects.get(codename="view_contract"))
        if kind == "through":
            genre = Genre.objects.create(name="genre")
            genre.publishers.add(Publisher.objects.get(pk=41))
            blocker = Genre.publishers.through.objects.get()
    routes = {
        "contenttype": ContentType,
        "user-grant": UserObjectPermission,
        "group-grant": GroupObjectPermission,
        "user": User,
        "group": Group,
        "permission": Permission,
        "user-groups": User.groups.through,
        "user-permissions": User.user_permissions.through,
        "group-permissions": Group.permissions.through,
    }
    overrides = {routes[misroute]: other} if misroute in routes else {}
    if misroute == "actor":
        actor = User.objects.using(other).get(pk=51)
    if misroute.startswith("hinted-"):
        base_router = router.routers[0]

        class HintedRouter:
            def db_for_read(self, model, **hints):
                if hints.get("instance") is not None and model is (
                    Group if misroute == "hinted-groups" else Permission
                ):
                    return other
                return base_router.db_for_read(model, **hints)

            def db_for_write(self, model, **hints):
                return base_router.db_for_write(model, **hints)

        monkeypatch.setattr(router, "routers", [HintedRouter()])
    with database_routes(using, overrides):
        mixin = GuardianDeleteRelatedObjectsMixin()
        mixin.cv_guardian_accept_global_perms = True
        related = RelatedObjects(tree=[blocker], summary={"objects": 1}, protected=[blocker])
        result = mixin.cv_filter_related_objects(actor, related)
        assert result.protected == []
        assert result.tree == [None]
        assert result.summary == {"objects": 1}


def test_guardian_signature_requires_candidate_alias():
    from crud_views_guardian.lib.views import _PermittedPks

    actor = _actor("default")
    with pytest.raises(TypeError, match="using"):
        _PermittedPks(actor, False)(Publisher)


def test_guardian_alias_cache_and_interleaved_requests(database_routes):
    from crud_views_guardian.lib.views import _PermittedPks

    clients = {}
    for using in ALIASES:
        target = _world(using, protected=True)
        with database_routes(using):
            actor = _actor(using)
            _grant(actor, target, "delete_publisher")
            if using == "shard":
                _grant(actor, Contract.objects.get(pk=81), "view_contract")
            client = Client()
            client.force_login(actor)
            clients[using] = client
    with database_routes("shard"):
        actor = User.objects.get(pk=51)
        permitted = _PermittedPks(actor, False)
        assert permitted(Contract, using="shard") == {81}
        assert permitted(Contract, using="default") == set()
    for using in ["shard", "default", "shard", "default"]:
        with database_routes(using):
            response = clients[using].get("/guardian_publisher_cascade/41/delete/")
            assert response.status_code == 200
            assert bool(response.context["protected_objects"]) is (using == "shard")


def test_guardian_cross_alias_global_cache_does_not_grant_labels(database_routes):
    from crud_views.lib.views.delete import RelatedObjects
    from crud_views_guardian.lib.views import GuardianDeleteRelatedObjectsMixin

    _world("shard", protected=True)
    with database_routes("shard"):
        actor = _actor("shard")
        actor._perm_cache = actor._user_perm_cache = actor._group_perm_cache = {"app.view_contract"}
        mixin = GuardianDeleteRelatedObjectsMixin()
        mixin.cv_guardian_accept_global_perms = True
        blocker = Contract.objects.get(pk=81)
        result = mixin.cv_filter_related_objects(actor, RelatedObjects([], {}, [blocker]))
        assert result.protected == []
        assert actor._perm_cache == {"app.view_contract"}
