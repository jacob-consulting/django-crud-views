import copy

import pytest

from crud_views.lib.view.button_data import LEAF_KEYS, cv_button_data

LOCATIONS = ["context", "list", "card"]


def base(**kw):
    ctx = {
        "cv_url": "/u/",
        "cv_key": "detail",
        "cv_action_label": "Show",
        "cv_action_short_label": "Detail",
        "cv_list_action_method": "get",
        "cv_disabled": False,
        "cv_oid": "o1",
        "cv_icon_action": "detail",
        "cv_variant": "primary",
    }
    ctx.update(kw)
    return ctx


@pytest.mark.parametrize("location", LOCATIONS)
def test_get(location):
    data = cv_button_data(base(), location)
    assert data["cv_location"] == location
    assert data["cv_tag"] == "a"
    assert data["cv_href"] == "/u/"
    assert "cv_submit_target" not in data
    assert data["cv_modal"] is False
    assert data["cv_modal_size"] == ""
    assert data["cv_variant"] == "primary"
    assert data["cv_icon"] == "detail"
    assert data["cv_key"] == "detail"
    assert data["cv_disabled"] is False
    assert data["cv_disabled_reason"] == ""
    if location == "card":
        assert data["cv_label"] == "Detail"
        assert data["cv_short_label"] == "Detail"
    else:
        assert data["cv_title"] == "Show"
        assert data["cv_label"] == "Show"
        assert data["cv_short_label"] == "Detail"


@pytest.mark.parametrize("location", LOCATIONS)
def test_post_without_modal(location):
    data = cv_button_data(base(cv_list_action_method="post"), location)
    assert data["cv_tag"] == "button"
    assert data["cv_submit_target"] == "cv_form_o1"
    assert "cv_href" not in data


@pytest.mark.parametrize("location", LOCATIONS)
def test_post_with_modal(location):
    data = cv_button_data(base(cv_list_action_method="post", cv_modal=True, cv_modal_size="lg"), location)
    assert data["cv_tag"] == "a"
    assert data["cv_href"] == "/u/"
    assert data["cv_modal"] is True
    assert data["cv_modal_size"] == "lg"
    assert "cv_submit_target" not in data


@pytest.mark.parametrize("location", LOCATIONS)
def test_disabled(location):
    ctx = base(cv_disabled=True, cv_disabled_reason="permission", cv_url=None, cv_modal=True, cv_is_active=True)
    data = cv_button_data(ctx, location)
    assert data["cv_tag"] == "button"
    assert "cv_href" not in data
    assert "cv_submit_target" not in data
    assert data["cv_modal"] is False
    assert data["cv_active"] is False
    assert data["cv_disabled"] is True
    assert data["cv_disabled_reason"] == "permission"


@pytest.mark.parametrize("location", LOCATIONS)
def test_active(location):
    assert cv_button_data(base(cv_is_active=True), location)["cv_active"] is True
    assert cv_button_data(base(), location)["cv_active"] is False


def test_card_label_mode_defaults_to_both():
    data = cv_button_data(base(cv_label="Details"), "card")
    assert data["cv_label"] == "Details"
    assert data["cv_label_mode"] == "both"
    assert "cv_title" not in data


@pytest.mark.parametrize("mode", ["label", "icon", "both"])
def test_card_label_mode_passes_through(mode):
    data = cv_button_data(base(cv_label="Details", cv_label_mode=mode), "card")
    assert data["cv_label_mode"] == mode


def test_card_icon_mode_gets_title():
    data = cv_button_data(base(cv_label="Details", cv_label_mode="icon"), "card")
    assert data["cv_title"] == "Details"


def test_card_empty_label_forces_icon():
    data = cv_button_data({"cv_label": "", "cv_key": "", "cv_url": "/u/", "cv_label_mode": "both"}, "card")
    assert data["cv_label_mode"] == "icon"


@pytest.mark.parametrize("value", [True, False])
def test_cv_no_label_in_ctx_raises(value):
    # presence, not truthiness: cv_no_label=False is the shape the old card-label tests passed
    ctx = base(cv_label="Details", cv_no_label=value)
    with pytest.raises(ValueError, match="cv_no_label"):
        cv_button_data(ctx, "card")


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("value", ["lable", "icons", "Both", 1, ["both"]])
def test_unknown_cv_label_mode_raises_everywhere(location, value):
    ctx = base(cv_label="Details", cv_label_mode=value)
    with pytest.raises(ValueError, match="cv_label_mode"):
        cv_button_data(ctx, location)


def test_card_label_falls_back_to_key():
    data = cv_button_data({"cv_label": None, "cv_key": "book", "cv_url": "/u/"}, "card")
    assert data["cv_label"] == "book"
    assert data["cv_short_label"] == "book"
    assert "None" not in [str(v) for k, v in data.items() if k != "cv_icon"]


@pytest.mark.parametrize("location", ["context", "list"])
@pytest.mark.parametrize("mode", ["both", "label"])
def test_label_mode_stamped_off_cards_shows_short_label(location, mode):
    data = cv_button_data(base(cv_label_mode=mode), location)
    assert data["cv_label_mode"] == mode
    assert data["cv_label"] == "Detail"
    assert data["cv_short_label"] == "Detail"
    assert "cv_title" not in data


@pytest.mark.parametrize("location", ["context", "list"])
def test_label_mode_icon_off_cards_keeps_full_label_and_title(location):
    data = cv_button_data(base(cv_label_mode="icon"), location)
    assert data["cv_label_mode"] == "icon"
    assert data["cv_label"] == "Show"
    assert data["cv_title"] == "Show"


@pytest.mark.parametrize("location,expected", [("card", True), ("context", False), ("list", False)])
def test_flex(location, expected):
    assert cv_button_data(base(cv_flex=True), location)["cv_flex"] is expected


@pytest.mark.parametrize("location", LOCATIONS)
def test_variant_defaults_to_secondary(location):
    ctx = base()
    del ctx["cv_variant"]
    assert cv_button_data(ctx, location)["cv_variant"] == "secondary"


def test_invalid_location():
    with pytest.raises(ValueError):
        cv_button_data(base(), "toolbar")


@pytest.mark.parametrize("location", LOCATIONS)
def test_pure_and_within_leaf_keys(location):
    ctx = base(cv_list_action_method="post", cv_modal=True, cv_is_active=True, cv_flex=True)
    before = copy.deepcopy(ctx)
    data = cv_button_data(ctx, location)
    assert ctx == before
    assert set(data) <= LEAF_KEYS
