from django import forms

from crud_views.lib.conditional.toggle import ModelFieldToggle, UIFieldToggle


class _ToggleForm(forms.Form):
    flag = forms.BooleanField(required=False)


def test_is_on_reads_cleaned_data_true():
    form = _ToggleForm(data={"flag": "on"})
    assert form.is_valid()
    assert ModelFieldToggle("flag").is_on(form) is True


def test_is_on_reads_cleaned_data_false_when_absent():
    form = _ToggleForm(data={})
    assert form.is_valid()
    assert ModelFieldToggle("flag").is_on(form) is False


def test_is_on_falls_back_to_raw_data_before_clean():
    form = _ToggleForm(data={"flag": "on"})  # not yet validated
    assert UIFieldToggle("flag").is_on(form) is True


def test_is_on_raw_data_falsey_strings():
    form = _ToggleForm(data={"flag": "false"})
    assert ModelFieldToggle("flag").is_on(form) is False


def test_ui_field_toggle_is_injectable():
    assert UIFieldToggle("flag").inject is True
    assert ModelFieldToggle("flag").inject is False
