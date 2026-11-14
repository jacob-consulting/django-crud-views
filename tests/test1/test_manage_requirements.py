"""Requirement metadata describes gates without authorizing a request."""

import pytest

from crud_views.lib.views import DetailView, DetailViewPermissionRequired


def test_requirement_contract_exists_without_viewset():
    describe = getattr(DetailView, "cv_get_requirement", None)
    assert callable(describe), "Views must describe their owning requirement without evaluating access"
    assert describe() == {"kind": "none", "value": None, "ancestor_applies": True}
    assert DetailViewPermissionRequired.cv_get_requirement() == {
        "kind": "permission",
        "value": "view",
        "ancestor_applies": True,
    }
