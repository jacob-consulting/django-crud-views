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

