"""Issue #76: curated public-API surface for the workflow & polymorphic extensions."""


def test_polymorphic_lib_exports_every_name_in_all():
    import crud_views_polymorphic.lib as poly_lib

    for name in poly_lib.__all__:
        assert hasattr(poly_lib, name), f"{name} is in __all__ but not importable from crud_views_polymorphic.lib"


def test_polymorphic_lib_exposes_delete_and_content_type_form():
    from crud_views_polymorphic.lib import (
        PolymorphicContentTypeForm,
        PolymorphicDeleteView,
        PolymorphicDeleteViewPermissionRequired,
    )
    from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm as _form
    from crud_views_polymorphic.lib.delete import (
        PolymorphicDeleteView as _delete,
        PolymorphicDeleteViewPermissionRequired as _delete_perm,
    )

    assert PolymorphicContentTypeForm is _form
    assert PolymorphicDeleteView is _delete
    assert PolymorphicDeleteViewPermissionRequired is _delete_perm
