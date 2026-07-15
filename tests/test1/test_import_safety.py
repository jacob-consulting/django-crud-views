"""
Audit task 2.3 (M8): crud_views modules must not call get_user_model() at
import time (Django convention: settings.AUTH_USER_MODEL string references
for FKs, get_user_model() at call time elsewhere).

Note: modules importing django.contrib.auth.mixins (e.g. lib.view.base via
the lib.view package __init__) can never be imported before django.setup()
-- Django's own auth.views calls get_user_model() at module level. The
tests below cover the modules whose importability crud_views controls.
"""

import subprocess
import sys
import textwrap
from pathlib import Path


def test_templatetags_import_without_app_registry():
    """Regression: previously failed with AppRegistryNotReady (module-level get_user_model)."""
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        import crud_views.templatetags.crud_views_formsets

        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_workflow_mixins_import_without_app_registry():
    """Regression: WorkflowModelMixin must be importable before the app registry is ready.

    A consumer model module that imports WorkflowModelMixin is loaded while Django is still
    populating apps; importing crud_views_workflow's own models at that point raised
    AppRegistryNotReady.
    """
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        import crud_views_workflow.lib.mixins

        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_resource_module_imports_standalone():
    """crud_views.lib.resource must be importable before any other crud_views module
    (users import Resource from models.py, which loads before AppConfig.ready)."""
    result = subprocess.run(
        [sys.executable, "-c", "import crud_views.lib.resource"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2] / "src"),
    )
    assert result.returncode == 0, result.stderr


def test_workflow_models_load_with_late_custom_user_app(tmp_path):
    """
    Contract: a custom AUTH_USER_MODEL whose app is listed *after*
    crud_views_workflow in INSTALLED_APPS must work. The WorkflowInfo.user
    FK uses the settings.AUTH_USER_MODEL string reference as Django's
    documentation requires for swappable user models.
    """
    usersapp = tmp_path / "usersapp"
    usersapp.mkdir()
    (usersapp / "__init__.py").write_text("")
    (usersapp / "models.py").write_text(
        textwrap.dedent(
            """
            from django.contrib.auth.models import AbstractUser


            class MyUser(AbstractUser):
                pass
            """
        )
    )

    code = textwrap.dedent(
        f"""
        import sys

        sys.path.insert(0, {str(tmp_path)!r})

        import django
        from django.conf import settings

        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "crud_views_workflow",  # loads (and imports models) BEFORE usersapp
                "usersapp",
            ],
            AUTH_USER_MODEL="usersapp.MyUser",
        )
        django.setup()

        from crud_views_workflow.models import WorkflowInfo

        field = WorkflowInfo._meta.get_field("user")
        assert field.remote_field.model is not None
        print("IMPORT-OK")
        """
    )

    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout
