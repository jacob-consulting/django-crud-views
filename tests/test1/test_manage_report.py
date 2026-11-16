"""Bounded configuration values and strict nested wire fields."""

import pytest
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy, override, pgettext_lazy
from pydantic import ValidationError

from crud_views.lib.manage_report import ConfigGroup, PermissionCell, SourceRecord, normalize_value


class Hostile:
    def fail(self, *args, **kwargs):
        raise AssertionError("configuration hook executed")

    __repr__ = __str__ = __bool__ = __eq__ = fail


@pytest.mark.parametrize("value", [None, True, False, 0, 12, 1.5, "x" * 600, list(range(300)), {"x": [None, True]}])
def test_native_values_round_trip_without_truncation(value):
    record = normalize_value(value)
    assert record.kind == "native" and record.value == value


@pytest.mark.parametrize("value", [Hostile(), {1, 2}, {1: "a", "1": "b"}, float("nan"), float("inf")])
def test_unsupported_values_do_not_execute_hooks(value):
    record = normalize_value(value)
    assert record.kind == "unsupported" and record.value is None
    assert record.python_type


def test_cycles_are_distinct_from_shared_containers_and_nested_tuple_origins():
    shared = [1, 2]
    assert normalize_value([shared, shared]).value == [[1, 2], [1, 2]]
    cycle = {"a": []}
    cycle["a"].append(cycle)
    assert normalize_value(cycle).kind == "unsupported"
    record = normalize_value({"tuple": ([1], (False,))})
    assert record.value == {"tuple": [[1], [False]]}
    assert [(m.path, m.python_type) for m in record.normalizations] == [
        (["tuple"], "builtins.tuple"),
        (["tuple", 1], "builtins.tuple"),
    ]


def test_translation_proxy_subclasses_and_arbitrary_promises_are_not_evaluated():
    proxy = gettext_lazy("hello")

    class CustomPromise(type(proxy)):
        __str__ = Hostile.fail

    assert normalize_value(CustomPromise(("hello",), {})).kind == "unsupported"
    assert normalize_value(lazy(Hostile.fail, str)()).kind == "unsupported"
    assert normalize_value(gettext_lazy(Hostile())).kind == "unsupported"
    for language in ("en", "de"):
        with override(language):
            assert normalize_value(proxy).value == str(proxy)
            translated = pgettext_lazy("context", "hello")
            assert normalize_value(translated).value == str(translated)


@pytest.mark.parametrize(
    "model,data",
    [
        (PermissionCell, {"key": "view", "model": "false", "object_count": None}),
        (PermissionCell, {"key": "view", "model": False, "object_count": "1"}),
        (ConfigGroup, {"key": "other", "label": "Other", "entries": [], "default_count": "0"}),
        (SourceRecord, {"code": "set", "declaring_class": 12}),
    ],
)
def test_known_nested_fields_reject_coercion(model, data):
    with pytest.raises(ValidationError):
        model.model_validate(data)
