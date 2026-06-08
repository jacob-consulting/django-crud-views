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
