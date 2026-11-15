"""Typed USERNAME_FIELD conversion uses real ORM fields, including front ends."""

import uuid
from io import StringIO

import pytest
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connection, models
from django.test.utils import isolate_apps
from django.urls import reverse

from crud_views.lib.access_trace import resolve_trace_user
from crud_views.lib.settings import crud_views_settings

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(params=["uuid", "integer"])
def typed_actor(request, monkeypatch):
    with isolate_apps():

        class TypedActor(AbstractBaseUser):
            login = models.UUIDField(unique=True) if request.param == "uuid" else models.IntegerField(unique=True)
            USERNAME_FIELD = "login"

            class Meta:
                app_label = "trace_users"

        with connection.schema_editor() as editor:
            editor.create_model(TypedActor)
        try:
            actor = TypedActor.objects.create(login=uuid.uuid4() if request.param == "uuid" else 123)
            monkeypatch.setattr("crud_views.lib.access_trace_runner.get_user_model", lambda: TypedActor)
            yield actor
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(TypedActor)


def test_username_and_pk_lookup_with_real_typed_fields(typed_actor):
    assert resolve_trace_user(str(typed_actor.login)).pk == typed_actor.pk
    assert resolve_trace_user(str(typed_actor.pk)).pk == typed_actor.pk
    assert resolve_trace_user("unknown") is None


def test_valid_username_still_wins_over_pk(typed_actor):
    if not isinstance(typed_actor.login, int):
        return  # UUID username cannot collide with this model's integer PK.
    winner = type(typed_actor).objects.create(login=typed_actor.pk)
    assert resolve_trace_user(str(typed_actor.pk)).pk == winner.pk


def test_database_errors_are_not_unknown_users(typed_actor, monkeypatch):
    def broken(**kwargs):
        raise OperationalError("database unavailable")

    monkeypatch.setattr(type(typed_actor)._default_manager, "get", broken)
    with pytest.raises(OperationalError, match="database unavailable"):
        resolve_trace_user("unknown")


def test_cli_reports_unknown_typed_username(typed_actor):
    with pytest.raises(CommandError, match="Unknown user: unknown") as error:
        call_command("cv_access", "/author/", "unknown", stdout=StringIO(), stderr=StringIO())
    assert error.value.returncode == 2


@pytest.mark.parametrize("mode", ["path", "viewset"])
def test_manage_form_reports_unknown_typed_username(
    typed_actor, client, cv_author, django_user_model, monkeypatch, mode
):
    viewer = django_user_model.objects.create_user(username="typed user diagnostic viewer")
    viewer.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    monkeypatch.setitem(crud_views_settings.__dict__, "manage_access_trace", True)
    client.force_login(viewer)
    response = client.get(
        reverse(cv_author.get_router_name("manage")),
        {
            "cv_access_mode": mode,
            "cv_access_user": "unknown",
            "cv_access_path": "/author/",
        },
    )
    assert response.status_code == 200
    assert response.context["manage_access_trace"]["error"] == "Unknown user: unknown"
    assert response.context["manage_access_trace"]["trace"] is None
