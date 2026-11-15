"""Isolated process fixture: only the parent's temporary SQLite file is opened."""

import os
import sys
from pathlib import Path


def main():
    from tests.test1.conftest import pytest_configure

    pytest_configure()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connections
    from django.urls import path

    from crud_views.lib.views import DetailView, DetailViewPermissionRequired, ListView
    from crud_views.lib.viewset import ViewSet
    from crud_views.management.commands.cv_access import Command
    from tests.test1.app.models import Publisher
    from tests.test1.test_access_trace import explode
    from tests.test1.test_manage_requirements import register

    database = Path(os.environ["CV_TRACE_CLI_DATABASE"]).resolve()
    # No project database fallback: preparation needs an absent, parent-owned file.
    preparing = sys.argv[1:] == ["--prepare"]
    assert database.parent.is_dir()
    assert database.exists() != preparing
    connections.close_all()
    settings.DATABASES["default"]["NAME"] = str(database)
    settings.ROOT_URLCONF = __name__
    settings.CRUD_VIEWS_MANAGE_ACCESS_TRACE = False

    vs = ViewSet(model=Publisher, name="trace_cli")
    plain = register(ListView, vs, key="plain", get=explode)
    protected = register(DetailViewPermissionRequired, vs, key="protected", get=explode)
    missing = register(DetailView, vs, key="missing", get=explode)

    def broken_gate(self):
        raise ValueError('quoted "value" \\ café 雪\nline\t\x1b[31m')

    broken = register(DetailViewPermissionRequired, vs, key="broken", has_permission=broken_gate, get=explode)
    globals()["urlpatterns"] = [
        path("plain/", plain.as_view(), name="cli-plain"),
        path("protected/", protected.as_view(), {"pk": 1}, name="cli-protected"),
        path("missing/", missing.as_view(), {"pk": 999}, name="cli-missing"),
        path("broken/", broken.as_view(), {"pk": 1}, name="cli-broken"),
    ]
    if preparing:
        call_command("migrate", run_syncdb=True, verbosity=0)
        get_user_model().objects.create_user(pk=1, username="sam")
        get_user_model().objects.create_user(pk=2, username="1")
        get_user_model().objects.create_user(pk=3, username="inactive", is_active=False)
        Publisher.objects.create(pk=1, name="never exposed")
        connections.close_all()
        return
    Command().run_from_argv([sys.argv[0], "cv_access", *sys.argv[1:]])


if __name__ == "__main__":
    main()
