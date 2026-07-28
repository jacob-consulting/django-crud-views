def test_public_exports():
    from crud_views.lib.conditional import (  # noqa: F401
        ConditionalFormSet,
        ConditionalGroup,
        ConditionalGroupFormMixin,
        ConditionalGroupModelForm,
        ModelFieldToggle,
        ToggleGroup,
        ToggleSource,
        UIFieldToggle,
    )
    from crud_views.lib.crispy import CrispyModelForm

    assert issubclass(ConditionalGroupModelForm, ConditionalGroupFormMixin)
    assert issubclass(ConditionalGroupModelForm, CrispyModelForm)
