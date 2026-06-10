"""
Audit M5: registering two ViewSets under the same name must fail loudly
instead of silently overwriting the first registration.
"""

import pytest

from crud_views.lib.exceptions import ViewSetError
from crud_views.lib.viewset import ViewSet, _REGISTRY
from tests.test1.app.models import Publisher


def test_duplicate_viewset_name_raises():
    name = "registry_dup_probe"
    ViewSet(model=Publisher, name=name)
    try:
        with pytest.raises(ViewSetError, match=name):
            ViewSet(model=Publisher, name=name)
    finally:
        _REGISTRY.pop(name, None)
