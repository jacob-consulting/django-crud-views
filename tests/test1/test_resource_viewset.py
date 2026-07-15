from collections import OrderedDict

import pytest
from pydantic import ValidationError

from crud_views.lib.exceptions import ViewSetError
from crud_views.lib.resource import Resource
from crud_views.lib.viewset import ViewSet, ParentViewSet
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


def check_error_ids(vs) -> list[str]:
    return [message.id for c in vs.checks() for message in c.messages()]


class T5Item(Resource):
    key: str

    class Meta:
        pk_field = "key"

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return []


def test_e260_missing_permission_key():
    from crud_views.lib.views import ListViewPermissionRequired

    vs = ViewSet(model=T5Item, name="t5_e260", resource_permissions=None)

    class T5E260ListView(ListViewPermissionRequired):  # noqa
        cv_viewset = vs  # registers at class definition; cv_permission "view" not in {}

    assert "viewset.E260" in check_error_ids(vs)


def test_e260_ok_when_key_present():
    from crud_views.lib.views import ListViewPermissionRequired

    vs = ViewSet(model=T5Item, name="t5_e260_ok", resource_permissions={"view": "app.view_s3file"})

    class T5E260OkListView(ListViewPermissionRequired):  # noqa
        cv_viewset = vs

    assert "viewset.E260" not in check_error_ids(vs)


def test_e261_resource_as_parent_rejected():
    from crud_views.lib.views import ListView
    from tests.test1.app.models import Author

    vs_parent = ViewSet(model=T5Item, name="t5_e261_parent", resource_permissions=None)

    class T5E261ParentListView(ListView):  # noqa — parent needs a registered view
        cv_viewset = vs_parent

    vs_child = ViewSet(model=Author, name="t5_e261_child", parent=ParentViewSet(name="t5_e261_parent"))

    class T5E261ChildListView(ListView):  # noqa
        cv_viewset = vs_child

    assert "viewset.E261" in check_error_ids(vs_child)
    assert "viewset.E261" not in check_error_ids(vs_parent)


def test_e262_write_views_rejected():
    from crud_views.lib.views import UpdateView

    vs = ViewSet(model=T5Item, name="t5_e262", resource_permissions=None)

    class T5E262UpdateView(UpdateView):  # noqa
        cv_viewset = vs

    assert "viewset.E262" in check_error_ids(vs)


def test_no_new_errors_for_plain_resource_viewset(vs_t2):
    # vs_t2 has no registered views with permissions issues and no parent
    ids = check_error_ids(vs_t2)
    assert "viewset.E260" not in ids
    assert "viewset.E261" not in ids
    assert "viewset.E262" not in ids


def test_e002_name_with_digits_is_valid():
    vs = ViewSet(model=T5Item, name="t8_s3name_ok", resource_permissions=None)
    assert "viewset.E002" not in check_error_ids(vs)


def test_e002_name_starting_with_digit_is_invalid():
    vs = ViewSet(model=T5Item, name="3file", resource_permissions=None)
    assert "viewset.E002" in check_error_ids(vs)
