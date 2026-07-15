from collections import OrderedDict

import pytest
from pydantic import ValidationError

from crud_views.lib.exceptions import ViewSetError
from crud_views.lib.resource import Resource
from crud_views.lib.viewset import ViewSet
from crud_views.lib.viewset.path_regs import PrimaryKeys
from tests.test1.app.models import Author


class T2Item(Resource):
    key: str

    class Meta:
        verbose_name = "t2 item"
        verbose_name_plural = "t2 items"
        pk_field = "key"
        pk_type = PrimaryKeys.HEX

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return [cls(key="aa"), cls(key="bb")]


@pytest.fixture(scope="module")
def vs_t2():
    # module-scoped: registry names are process-global, register exactly once
    return ViewSet(
        model=T2Item,
        name="t2_item",
        resource_permissions={"view": "app.view_s3file"},
    )


def test_is_resource(vs_t2, cv_author):
    assert vs_t2.is_resource is True
    assert cv_author.is_resource is False


def test_pk_type_from_resource_meta(vs_t2):
    assert vs_t2.pk == PrimaryKeys.HEX


def test_pk_explicit_override_still_wins():
    vs = ViewSet(
        model=T2Item,
        name="t2_item_custompk",
        pk=r"[a-f]{2}",
        resource_permissions=None,
    )
    assert vs.pk == r"[a-f]{2}"


def test_permissions_returns_explicit_dict(vs_t2):
    assert vs_t2.permissions == OrderedDict({"view": "app.view_s3file"})


def test_permissions_none_means_empty():
    vs = ViewSet(model=T2Item, name="t2_item_noperm", resource_permissions=None)
    assert vs.permissions == OrderedDict()


def test_no_auto_manage_view(vs_t2, cv_author):
    assert vs_t2.has_view("manage") is False
    assert cv_author.has_view("manage") is True


def test_plain_class_rejected():
    class NotAResource:
        pass

    with pytest.raises(ValidationError):
        ViewSet(model=NotAResource, name="t2_plainclass")


def test_resource_permissions_rejected_for_model_viewset():
    with pytest.raises(ValidationError):
        ViewSet(
            model=Author,
            name="t2_model_with_rp",
            resource_permissions={"view": "app.view_author"},
        )


def test_viewset_get_queryset_guard(vs_t2):
    with pytest.raises(ViewSetError, match="ResourceViewMixin"):
        vs_t2.get_queryset(view=None)


def test_guardian_viewset_rejects_resource():
    from crud_views_guardian.lib.viewset import GuardianViewSet

    with pytest.raises(ValidationError, match="does not support Resource"):
        GuardianViewSet(model=T2Item, name="t2_guardian_resource")
