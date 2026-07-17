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


def test_workflow_lib_exports_every_name_in_all():
    import crud_views_workflow.lib as wf_lib

    for name in wf_lib.__all__:
        assert getattr(wf_lib, name) is not None, (
            f"{name} is in __all__ but not resolvable from crud_views_workflow.lib"
        )


def test_workflow_lib_names_resolve_to_the_same_objects_as_deep_paths():
    from crud_views_workflow.lib import (
        BadgeEnum,
        WorkflowComment,
        WorkflowForm,
        WorkflowModelMixin,
        WorkflowView,
        WorkflowViewPermissionRequired,
    )
    from crud_views_workflow.lib.enums import BadgeEnum as _badge
    from crud_views_workflow.lib.enums import WorkflowComment as _comment
    from crud_views_workflow.lib.forms import WorkflowForm as _form
    from crud_views_workflow.lib.mixins import WorkflowModelMixin as _mixin
    from crud_views_workflow.lib.views import WorkflowView as _view
    from crud_views_workflow.lib.views import WorkflowViewPermissionRequired as _view_perm

    assert BadgeEnum is _badge
    assert WorkflowComment is _comment
    assert WorkflowForm is _form
    assert WorkflowModelMixin is _mixin
    assert WorkflowView is _view
    assert WorkflowViewPermissionRequired is _view_perm


def test_workflow_lib_unknown_attribute_raises_attribute_error():
    import pytest

    import crud_views_workflow.lib as wf_lib

    with pytest.raises(AttributeError):
        _ = wf_lib.NoSuchName
