"""
Audit task 2.4 (M9): settings validation must produce clear, idempotent
check messages — a missing CRUD_VIEWS_EXTENDS names the setting instead of
crashing on get_template(None), an invalid CRUD_VIEWS_MANAGE_VIEWS_ENABLED
value is reported, and repeated check runs do not accumulate duplicates.
"""

import pytest

from crud_views.lib.settings import CrudViewsSettings


def test_check_messages_are_idempotent():
    settings_obj = CrudViewsSettings(extends="does-not-exist.html")
    first = list(settings_obj.check_messages)
    second = list(settings_obj.check_messages)
    assert len(first) == 1
    assert len(second) == 1


def test_missing_extends_names_the_setting():
    settings_obj = CrudViewsSettings(extends=None)
    messages = settings_obj.check_messages
    assert len(messages) == 1
    assert "CRUD_VIEWS_EXTENDS" in messages[0].msg


def test_nonexistent_extends_template_reported():
    settings_obj = CrudViewsSettings(extends="does-not-exist.html")
    messages = settings_obj.check_messages
    assert len(messages) == 1
    assert "does-not-exist.html" in messages[0].msg


def test_invalid_manage_views_enabled_reported():
    settings_obj = CrudViewsSettings(manage_views_enabled="bogus")
    messages = settings_obj.check_messages
    assert any("CRUD_VIEWS_MANAGE_VIEWS_ENABLED" in m.msg for m in messages)


def test_valid_settings_produce_no_messages():
    # the test project configures a valid CRUD_VIEWS_EXTENDS template
    settings_obj = CrudViewsSettings()
    assert settings_obj.check_messages == []


def test_theme_setting_warns_it_is_ignored():
    # CRUD_VIEWS_THEME is not a supported setting; theming is done via template-override apps
    settings_obj = CrudViewsSettings(theme="bootstrap5")
    messages = settings_obj.check_messages
    assert any("CRUD_VIEWS_THEME" in m.msg for m in messages)


def test_origin_param_default():
    settings_obj = CrudViewsSettings()
    assert settings_obj.origin_param == "cv_from"


def test_origin_param_valid_name_no_message():
    settings_obj = CrudViewsSettings(origin_param="origin_2")
    assert settings_obj.check_messages == []


def test_origin_param_invalid_name_reported():
    for bad in ("bad param", "bad-param", "Bad", "2bad", "", "a/b", "a=b"):
        settings_obj = CrudViewsSettings(origin_param=bad)
        messages = settings_obj.check_messages
        assert len(messages) == 1, bad
        assert messages[0].id == "crud_views.E103"
        assert "CRUD_VIEWS_ORIGIN_PARAM" in messages[0].msg


@pytest.mark.parametrize("value", [None, 1, 3, 5])
def test_header_level_valid(value):
    assert CrudViewsSettings(header_level=value).check_messages == []


@pytest.mark.parametrize("value", [0, 6, "2", True, 2.0])
def test_header_level_invalid(value):
    messages = CrudViewsSettings(header_level=value).check_messages
    assert len(messages) == 1
    assert messages[0].id == "crud_views.E107"
    assert "CRUD_VIEWS_HEADER_LEVEL" in messages[0].msg


@pytest.mark.parametrize("configured", [None, [], {"form": "bad"}, {"typo": "both"}, {"form": None}])
def test_theme_floor_does_not_suppress_e108(configured):
    from django.test import override_settings

    from crud_views.lib.view.label_mode import register_label_mode_defaults

    register_label_mode_defaults({"form": "both"})
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured):
        errors = [m for m in CrudViewsSettings().check_messages if m.id == "crud_views.E108"]
    assert len(errors) == 1
    assert "CRUD_VIEWS_LABEL_MODE_DEFAULTS" in errors[0].msg


def test_theme_and_valid_project_floors_are_quiet():
    from django.test import override_settings

    from crud_views.lib.view.label_mode import register_label_mode_defaults

    register_label_mode_defaults({"form": "both", "card": "icon"})
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "label"}):
        assert CrudViewsSettings().check_messages == []


@pytest.mark.parametrize("value", [None, 1, 50, True, "4", 0, [], {}])
def test_delete_preview_limit_precedence_setting_load(settings, value):
    import runpy
    from pathlib import Path

    import crud_views.lib.settings as settings_module

    settings.CRUD_VIEWS_DELETE_PREVIEW_LIMIT = value
    # Execute an isolated settings model, without replacing the process-wide singleton.
    captured = runpy.run_path(str(Path(settings_module.__file__)))["crud_views_settings"]
    assert captured.delete_preview_limit == value
    assert type(captured.delete_preview_limit) is type(value)
    valid = value is None or (type(value) is int and value > 0)
    assert any(message.id == "crud_views.E109" for message in captured.check_messages) is not valid
