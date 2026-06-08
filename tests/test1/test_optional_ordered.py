import sys

import pytest

from crud_views.lib import ordered


def test_get_ordered_model_returns_class_when_installed():
    """When django-ordered-model is installed, the helper returns the class."""
    from ordered_model.models import OrderedModel

    assert ordered.get_ordered_model() is OrderedModel


def test_get_ordered_model_returns_none_when_absent(monkeypatch):
    """When ordered_model cannot be imported, the helper returns None instead of raising."""
    # Hide ordered_model and its submodule from the import system.
    monkeypatch.setitem(sys.modules, "ordered_model", None)
    monkeypatch.setitem(sys.modules, "ordered_model.models", None)

    assert ordered.get_ordered_model() is None


def test_formsets_module_imports_without_ordered_model(monkeypatch):
    """crud_views.lib.formsets.formsets must import cleanly when ordered_model is absent."""
    import importlib

    monkeypatch.setitem(sys.modules, "ordered_model", None)
    monkeypatch.setitem(sys.modules, "ordered_model.models", None)

    import crud_views.lib.formsets.formsets as formsets_mod

    # Reload under the hidden-package condition; must not raise ImportError.
    reloaded = importlib.reload(formsets_mod)
    assert hasattr(reloaded, "FormSet")

    # Restore a clean module state for other tests.
    monkeypatch.undo()
    importlib.reload(reloaded)


from crud_views.lib import ordered as ordered_helper


@pytest.mark.django_db
def test_check_passes_when_ordered_model_installed(cv_author):
    """With the package installed and ordered views registered, the check is silent."""
    from crud_views.checks import check_ordered_model_installed

    errors = check_ordered_model_installed()
    assert errors == []


@pytest.mark.django_db
def test_check_errors_when_ordered_model_absent(monkeypatch, cv_author):
    """When the package is absent but ordered views are registered, the check errors."""
    from crud_views import checks

    # The test app's Author viewset registers up/down ordered views, so the check
    # must flag the missing dependency.
    monkeypatch.setattr(checks.ordered_helper, "get_ordered_model", lambda: None)

    errors = checks.check_ordered_model_installed()
    assert len(errors) == 1
    assert errors[0].id == "crud_views.E300"
    assert "ordered" in errors[0].msg
