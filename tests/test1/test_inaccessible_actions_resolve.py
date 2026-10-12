"""#149: cv_resolve_action decides show / disable / hide from an action's button data."""

import pytest
from django.template import Context, Template

from crud_views.lib.view.visibility import cv_resolve_action


def _ctx(access=True, enabled=True, mode="hide", **extra):
    return {
        "cv_key": "delete",
        "cv_url": "/x/1/delete/",
        "cv_access": access,
        "cv_action_enabled": enabled,
        "cv_inaccessible_actions": mode,
        **extra,
    }


@pytest.mark.parametrize("ctx", [None, {}])
def test_empty_hides(ctx):
    assert cv_resolve_action(ctx) is None


@pytest.mark.parametrize("mode", ["hide", "disable"])
def test_usable_is_shown_unchanged(mode):
    out = cv_resolve_action(_ctx(mode=mode))
    assert out["cv_disabled"] is False
    assert out["cv_url"] == "/x/1/delete/"
    assert "cv_disabled_reason" not in out


@pytest.mark.parametrize("access, enabled", [(False, True), (True, False), (False, False)])
def test_hide_mode_hides_unusable(access, enabled):
    assert cv_resolve_action(_ctx(access=access, enabled=enabled, mode="hide")) is None


@pytest.mark.parametrize(
    "access, enabled, reason",
    [(False, True, "permission"), (True, False, "state"), (False, False, "permission")],
)
def test_disable_mode_flags_unusable(access, enabled, reason):
    out = cv_resolve_action(_ctx(access=access, enabled=enabled, mode="disable"))
    assert out["cv_disabled"] is True
    assert out["cv_url"] is None
    assert out["cv_disabled_reason"] == reason
    assert out["cv_key"] == "delete"


def test_missing_mode_key_hides():
    ctx = _ctx(access=False)
    del ctx["cv_inaccessible_actions"]
    assert cv_resolve_action(ctx) is None


def test_access_must_be_exactly_true():
    # a truthy non-True value is not access (same rule as the old _context_button_visible)
    assert cv_resolve_action(_ctx(access="yes", mode="hide")) is None


def test_input_is_not_mutated():
    ctx = _ctx(access=False, mode="disable")
    before = dict(ctx)
    cv_resolve_action(ctx)
    assert ctx == before


@pytest.mark.parametrize("access, enabled", [(True, True), (False, True), (True, False)])
def test_resolve_is_idempotent(access, enabled):
    once = cv_resolve_action(_ctx(access=access, enabled=enabled, mode="disable"))
    assert cv_resolve_action(once) == once


def test_old_template_condition_still_hides_disabled_data():
    # a project template overridden before #149 keeps today's condition: it must render nothing
    out = cv_resolve_action(_ctx(access=False, mode="disable"))
    tpl = Template('{% if cv_action_enabled is not False and cv_access is True %}<a href="{{ cv_url }}">{% endif %}')
    assert tpl.render(Context(out)) == ""
