import pytest
from django.http import Http404
from pydantic import ValidationError

from crud_views.lib.resource import Resource, ResourceMeta, ResourceOptions
from crud_views.lib.viewset.path_regs import PrimaryKeys


class Item(Resource):
    key: str
    size: int = 0

    class Meta:
        verbose_name = "s3 item"
        verbose_name_plural = "s3 items"
        app_label = "storage"
        pk_field = "key"
        pk_type = PrimaryKeys.STR

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        return [cls(key="a", size=1), cls(key="b", size=2)]


def test_meta_defaults_merge():
    class Minimal(Resource):
        pk: str

    assert Minimal._meta.verbose_name == "item"
    assert Minimal._meta.verbose_name_plural == "items"
    assert Minimal._meta.app_label == "resources"
    assert Minimal._meta.pk_field == "pk"
    assert Minimal._meta.pk_type == PrimaryKeys.STR
    assert Minimal._meta.ordering is None


def test_meta_shim_exposes_options_attrs():
    assert Item._meta.verbose_name == "s3 item"
    assert Item._meta.verbose_name_plural == "s3 items"
    assert Item._meta.app_label == "storage"
    assert Item._meta.pk_field == "key"
    # instance access works too (SessionData reads view.model._meta via class,
    # templates may reach it via instances)
    assert Item(key="x")._meta.verbose_name == "s3 item"


def test_options_is_plain_object():
    opts = ResourceOptions(ResourceMeta)
    assert opts.verbose_name == "item"
    assert opts.pk_field == "pk"


def test_pk_property_reads_pk_field():
    assert Item(key="x").pk == "x"


def test_pk_field_may_name_a_python_property():
    class Hashed(Resource):
        key: str

        class Meta:
            pk_field = "key_upper"

        @property
        def key_upper(self) -> str:
            return self.key.upper()

    assert Hashed(key="ab").pk == "AB"


def test_field_named_pk_works_directly():
    class Direct(Resource):
        pk: str

    assert Direct(pk="1").pk == "1"


def test_default_pk_field_without_pk_field_raises():
    with pytest.raises(TypeError, match="pk_field"):

        class Broken(Resource):
            key: str  # Meta.pk_field defaults to "pk" but there is no pk attribute


def test_cv_get_items_not_implemented():
    class Bare(Resource):
        pk: str

    with pytest.raises(NotImplementedError):
        Bare.cv_get_items(None)


def test_cv_get_item_default_scan():
    found = Item.cv_get_item(None, "a")
    assert found.key == "a"
    assert found.size == 1


def test_cv_get_item_raises_http404():
    with pytest.raises(Http404):
        Item.cv_get_item(None, "does-not-exist")


def test_pydantic_validation_still_works():
    with pytest.raises(ValidationError):
        Item(key="a", size="not-an-int")


def test_intermediate_base_pk_shim_does_not_shadow_subclass_pk_field():
    import warnings

    class IntermediateBase(Resource):
        key: str

        class Meta:
            pk_field = "key"

    with warnings.catch_warnings():
        # pydantic warns that field "pk" shadows the inherited property; the
        # neutralizer below is exactly what makes that shadowing safe
        warnings.simplefilter("ignore", UserWarning)

        class Concrete(IntermediateBase):
            pk: str

    obj = Concrete(key="k", pk="real-pk")
    assert obj.pk == "real-pk"


def test_meta_pk_field_pk_with_only_inherited_shim_raises():
    class IntermediateBase2(Resource):
        key: str

        class Meta:
            pk_field = "key"

    with pytest.raises(TypeError, match="pk_field"):

        class Sub(IntermediateBase2):
            class Meta:
                pk_field = "pk"
