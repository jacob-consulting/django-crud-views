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


def test_value_toggle_export():
    import crud_views.lib.conditional as conditional
    from crud_views.lib.conditional.toggle import ValueToggle

    assert getattr(conditional, "ValueToggle", None) is ValueToggle
    assert "ValueToggle" in conditional.__all__
