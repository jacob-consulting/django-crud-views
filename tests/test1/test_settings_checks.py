"""
Audit task 2.4 (M9): settings validation must produce clear, idempotent
check messages — a missing CRUD_VIEWS_EXTENDS names the setting instead of
crashing on get_template(None), an invalid CRUD_VIEWS_MANAGE_VIEWS_ENABLED
value is reported, and repeated check runs do not accumulate duplicates.
"""

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
