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

import pytest


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


def test_workflow_run_transition_import_without_app_registry():
    code = textwrap.dedent(
        """
        from django.conf import settings
        settings.configure()
        from crud_views_workflow.lib import run_transition
        assert callable(run_transition)
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


def test_workflow_lib_package_imports_without_app_registry():
    """The crud_views_workflow.lib package body must be lazy: importing the package before the
    app registry is ready must not drag in .lib.views (WorkflowInfo model + auth mixins)."""
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        import crud_views_workflow.lib

        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_workflow_lib_model_mixin_public_path_imports_without_app_registry():
    """`from crud_views_workflow.lib import WorkflowModelMixin` is the documented public path and is
    used by consumer model modules loaded before the app registry is ready -- it must not raise."""
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowForm, WorkflowModelMixin

        assert WorkflowModelMixin is not None
        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_object_detail_lib_package_imports_without_app_registry():
    """The crud_views_object_detail.lib package body must be lazy: importing the package before
    the app registry is ready must not drag in .lib.views (CrudView + auth mixins)."""
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        import crud_views_object_detail.lib

        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_object_detail_config_helpers_import_without_app_registry():
    """`x()`, `PropertyConfig`, etc. are used inside consumer model/view modules loaded before
    the app registry is ready; the config helpers must resolve without importing `lib.views`."""
    code = textwrap.dedent(
        """
        from django.conf import settings

        settings.configure()  # no django.setup() -- the app registry is not ready

        from crud_views_object_detail.lib import BadgeConfig, LinkConfig, PropertyConfig, PropertyGroupConfig, x

        assert x is not None
        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


FIRST_IMPORTS = [
    "from crud_views.lib.viewset import ViewSet",
    "from crud_views.lib.viewset import ParentViewSet, PrimaryKeys",
    "from crud_views.lib.table import Table, LinkChildColumn",
    "from crud_views.lib.table.columns import NaturalDayColumn",
    "from crud_views.lib.views import ListViewPermissionRequired, RedirectChildView",
    "from crud_views.lib.view import CrudView",
    "from crud_views_polymorphic.lib import PolymorphicCreateViewPermissionRequired",
    "from crud_views_guardian.lib.viewset import GuardianViewSet",
]


def test_object_detail_mapping_without_polymorphic(tmp_path):
    """Exact ordinary base/child/proxy mappings work with both optional packages absent."""
    app = tmp_path / "mappingapp"
    app.mkdir()
    (app / "__init__.py").write_text("")
    (app / "models.py").write_text(
        textwrap.dedent(
            """
            from django.db import models

            class Base(models.Model):
                name = models.CharField(max_length=100)

            class Child(Base):
                code = models.CharField(max_length=100)

            class Proxy(Child):
                class Meta:
                    proxy = True
            """
        )
    )
    code = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(tmp_path)!r})
        blocked = ("polymorphic", "crud_views_polymorphic")
        for name in blocked:
            sys.modules[name] = None

        import django
        from django.conf import settings
        settings.configure(
            SECRET_KEY="mapping-test",
            INSTALLED_APPS=[
                "django.contrib.contenttypes", "django.contrib.auth",
                "crud_views", "crud_views_object_detail", "mappingapp",
            ],
            TEMPLATES=[{{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}}],
        )
        django.setup()

        from django.core.exceptions import ImproperlyConfigured
        from django.template.loader import render_to_string
        from crud_views_object_detail.lib.mixins import ObjectDetailMixin
        from mappingapp.models import Base, Child, Proxy

        class DetailBase:
            @classmethod
            def checks(cls):
                return []

            def get_context_data(self, **kwargs):
                return {{"object": self.object}}

        class OrdinaryDetail(ObjectDetailMixin, DetailBase):
            cv_property_display = {{
                model: [{{"title": model.__name__, "properties": ["name"]}}]
                for model in (Base, Child, Proxy)
            }}

        declaration = OrdinaryDetail.cv_property_display
        assert not [m for check in OrdinaryDetail.checks() for m in check.messages()]
        for model in (Base, Child, Proxy):
            view = OrdinaryDetail()
            view.object = model(name="Ordinary mapped value")
            assert view.get_property_display()[0].title == model.__name__
            assert OrdinaryDetail.cv_property_display is declaration

        html = render_to_string("crud_views_object_detail/view_detail.content.html", view.get_context_data())
        assert "Ordinary mapped value" in html
        assert "Proxy" in html

        for configured, missing in ((Child, (Base, Proxy)), (Base, (Child, Proxy))):
            for actual in missing:
                view = OrdinaryDetail()
                view.cv_property_display = {{configured: declaration[configured]}}
                view.object = actual(name="Unmapped")
                try:
                    view.get_property_display()
                except ImproperlyConfigured as exc:
                    assert actual._meta.label in str(exc)
                    assert "__main__.OrdinaryDetail" in str(exc)
                else:
                    raise AssertionError("Inherited or proxy fallback selected")

        assert not [
            name for name, module in sys.modules.items()
            if module is not None and any(name == root or name.startswith(root + ".") for root in blocked)
        ]
        print("MAPPING-WITHOUT-POLYMORPHIC-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "MAPPING-WITHOUT-POLYMORPHIC-OK" in result.stdout


@pytest.mark.parametrize("statement", FIRST_IMPORTS)
def test_public_module_importable_as_first_crud_views_import(statement):
    """Regression: `from crud_views.lib.viewset import ViewSet` as the first crud_views import in a
    process raised a circular ImportError (viewset -> views.manage -> views -> views.child -> viewset,
    whose PrimaryKeys was not bound yet). Each statement runs first in a fresh interpreter."""
    code = textwrap.dedent(
        f"""
        import django
        from django.conf import settings

        settings.configure(INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
        django.setup()

        {statement}

        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_resource_with_viewset_pk_in_models_module(tmp_path):
    """A Resource defined in a consumer models.py using ViewSet.PK is imported while Django
    populates apps -- before any other crud_views module is loaded -- and must not raise."""
    app = tmp_path / "storageapp"
    app.mkdir()
    (app / "__init__.py").write_text("")
    (app / "models.py").write_text(
        textwrap.dedent(
            """
            from crud_views.lib.resource import Resource
            from crud_views.lib.viewset import ViewSet


            class S3File(Resource):
                key: str

                class Meta:
                    pk_field = "key"
                    pk_type = ViewSet.PK.STR
            """
        )
    )
    code = textwrap.dedent(
        f"""
        import sys

        sys.path.insert(0, {str(tmp_path)!r})

        import django
        from django.conf import settings

        settings.configure(INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "storageapp"])
        django.setup()
        print("IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "IMPORT-OK" in result.stdout


def test_settings_defers_button_data_until_checks():
    """D-07: crud_views.lib.settings imports before django.setup() without loading the view package; the
    E108 check loads button_data (for LOCATIONS) only when it runs, and reads the raw setting then."""
    code = textwrap.dedent(
        """
        import sys

        from django.conf import settings

        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "nope"},
        )

        from crud_views.lib.settings import crud_views_settings

        assert "crud_views.lib.view" not in sys.modules, "view package imported by settings"
        assert "crud_views.lib.view.button_data" not in sys.modules, "button_data imported by settings"

        import django

        django.setup()

        assert "crud_views.lib.view.button_data" not in sys.modules, "button_data imported by django.setup()"

        messages = crud_views_settings.check_messages

        assert "crud_views.lib.view.button_data" in sys.modules, "check did not load button_data"
        ids = [m.id for m in messages]
        assert ids.count("crud_views.E108") == 1, ids
        assert set(ids) <= {"crud_views.E100", "crud_views.E108"}, ids
        (e108,) = [m for m in messages if m.id == "crud_views.E108"]
        assert "key 'card'" in e108.msg and "'nope'" in e108.msg, e108.msg

        print("SETTINGS-DEFERRED-IMPORT-OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "SETTINGS-DEFERRED-IMPORT-OK" in result.stdout
