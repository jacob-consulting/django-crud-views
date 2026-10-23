"""#261: container-list / container-item / container-single keys resolved into a ContainerLayout."""

import pytest
from django.test import override_settings

from crud_views.lib import button_classes as bc
from crud_views.lib.button_classes import (
    DEFAULT_BUTTON_CLASSES,
    ContainerLayout,
    get_container_layout,
    reset_button_classes_cache,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    reset_button_classes_cache()


@pytest.mark.parametrize("loc", ["context", "list", "card"])
def test_defaults(loc):
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-list"] is None
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-item"] == ""
    assert DEFAULT_BUTTON_CLASSES[f"{loc}:container-single"] == "container"
    assert get_container_layout(loc, 1) == ContainerLayout(list_class=None, item_class="", bare=False)


def test_layout_list_and_item():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-list": "x", "list:container-item": "y"}):
        assert get_container_layout("list", 2) == ContainerLayout("x", "y", False)


def test_layout_empty_list_class_is_list():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:container-list": ""}):
        assert get_container_layout("card", 2).list_class == ""


@pytest.mark.parametrize("count, bare", [(1, True), (2, False)])
def test_layout_bare_only_for_one(count, bare):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:container-single": "bare"}):
        assert get_container_layout("context", count).bare is bare


def test_layout_zero_items_never_bare():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:container-single": "bare"}):
        assert get_container_layout("context", 0).bare is False


@pytest.mark.parametrize("value", [None, "", "nonsense", 3])
def test_layout_invalid_single_means_container(value):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-single": value}):
        assert get_container_layout("list", 1).bare is False


def test_layout_non_str_list_is_no_list():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-list": 3}):
        assert get_container_layout("list", 2).list_class is None
