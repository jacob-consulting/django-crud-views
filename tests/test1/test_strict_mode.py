"""
Audit task 2.1: the ignore_exception decorator must honor the
CRUD_VIEWS_STRICT setting (defaulting to DEBUG) instead of a hardcoded
module-level STRICT = False, so misconfigurations fail loudly in development.
"""

import pytest
from django.test import override_settings

from crud_views.lib.exceptions import ignore_exception, is_strict


@ignore_exception(KeyError, default_value="fallback")
def _boom():
    raise KeyError("k")


def test_ignore_exception_raises_in_strict_mode():
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(KeyError):
        _boom()


def test_ignore_exception_swallows_when_not_strict():
    with override_settings(CRUD_VIEWS_STRICT=False):
        assert _boom() == "fallback"


def test_strict_defaults_to_debug_on(settings):
    # without CRUD_VIEWS_STRICT set, strictness follows DEBUG
    # (note: pytest-django forces DEBUG=False during tests, so set it explicitly)
    del settings.CRUD_VIEWS_STRICT
    with override_settings(DEBUG=True), pytest.raises(KeyError):
        _boom()


def test_strict_defaults_to_swallow_when_debug_off(settings):
    del settings.CRUD_VIEWS_STRICT
    with override_settings(DEBUG=False):
        assert _boom() == "fallback"


def test_is_strict_follows_the_setting_before_debug():
    with override_settings(CRUD_VIEWS_STRICT=False, DEBUG=True):
        assert is_strict() is False
    with override_settings(CRUD_VIEWS_STRICT=True, DEBUG=False):
        assert is_strict() is True


def test_suite_runs_strict():
    # #264: pytest-django runs with DEBUG=False, so the test settings turn strict mode on explicitly
    from django.conf import settings

    assert settings.CRUD_VIEWS_STRICT is True
