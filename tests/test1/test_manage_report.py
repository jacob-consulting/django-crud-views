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


def test_known_translation_wrappers_support_supported_django_versions():
    values = [
        gettext_lazy("hello"),
        gettext_lazy(message="hello"),
        pgettext_lazy("context", "hello"),
        pgettext_lazy(context="context", message="hello"),
    ]
    for language in ("en", "de"):
        with override(language):
            for value in values:
                try:
                    record = normalize_value(value)
                except AttributeError as exc:
                    pytest.fail(f"Known Django translation proxy layout must be supported: {exc}")
                assert record.kind == "native" and record.value == str(value)


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


def identity_only_report():
    from crud_views.lib.manage_report import InspectionData

    sections = [name for name in InspectionData.model_fields if name not in {"identity", "guardian"}]
    return {
        "kind": "inspection",
        "status": "partial",
        "selection": {},
        "data": {
            "identity": {"name": "example", "kind": "model", "backing_class": "app.Model", "parent": None},
            "guardian": {"status": "not_applicable", "data": None, "errors": []},
            **{name: {"status": "error", "data": None, "errors": [index]} for index, name in enumerate(sections)},
        },
        "errors": [{"code": "collection_failed", "section": name, "message": "unavailable"} for name in sections],
    }


def test_valid_identity_is_useful_surviving_data():
    from crud_views.lib.manage_report import Report

    assert Report.validate_python(identity_only_report()).status == "partial"


@pytest.mark.parametrize("mutation", ["negative", "out_of_bounds", "wrong_section", "duplicate", "orphan", "coercion"])
def test_section_error_references_are_exact_and_typed(mutation):
    from crud_views.lib.manage_report import Report

    raw = identity_only_report()
    # A successful empty section is useful, and still validates its error ownership.
    raw["data"]["facts"] = {"status": "ok", "data": {"entries": []}, "errors": []}
    raw["errors"][0]["section"] = None
    if mutation == "orphan":
        raw["errors"][0]["section"] = "facts"
    else:
        raw["data"]["presentation"]["errors"] = {
            "negative": [-1],
            "out_of_bounds": [100],
            "wrong_section": [2],
            "duplicate": [1, 1],
            "coercion": ["1"],
        }[mutation]
    with pytest.raises(ValidationError):
        Report.validate_python(raw)


@pytest.mark.parametrize(
    "status,data,errors",
    [
        ("ok", None, []),
        ("error", None, []),
        ("not_applicable", None, [0]),
        ("error", {"entries": []}, [0]),
        ("ok", {"entries": []}, [0]),
    ],
)
def test_section_status_data_and_errors_must_agree(status, data, errors):
    from crud_views.lib.manage_report import FactsData, Section

    with pytest.raises(ValidationError):
        Section[FactsData](status=status, data=data, errors=errors)


@pytest.mark.parametrize("location", [[True], [1.5], [{}]])
def test_error_locations_are_only_strict_strings_and_integers(location):
    from crud_views.lib.manage_report import ReportError

    with pytest.raises(ValidationError):
        ReportError(code="output_validation_failed", message="invalid", location=location)


@pytest.mark.parametrize("field", ["code", "status", "kind", "version"])
def test_closed_report_vocabularies_reject_new_variants(field):
    from crud_views.lib.manage_report import Report

    raw = {
        "version": 1,
        "kind": "inspection",
        "status": "failed",
        "selection": {},
        "data": None,
        "errors": [{"code": "collection_failed", "message": "unavailable"}],
    }
    if field == "code":
        raw["errors"][0]["code"] = "new_error"
    else:
        raw[field] = 2 if field == "version" else "new_variant"
    with pytest.raises(ValidationError):
        Report.validate_python(raw)


@pytest.mark.parametrize(
    "status,data,errors",
    [
        ("complete", None, []),
        ("complete", {"entries": []}, [{"code": "collection_failed", "message": "error"}]),
        ("failed", {"entries": []}, [{"code": "collection_failed", "message": "error"}]),
        ("failed", None, []),
        ("partial", None, [{"code": "collection_failed", "message": "error"}]),
        ("partial", {"entries": []}, []),
    ],
)
def test_envelope_status_and_surviving_data_must_agree(status, data, errors):
    from crud_views.lib.manage_report import CatalogueResult

    with pytest.raises(ValidationError):
        CatalogueResult(status=status, selection={}, data=data, errors=errors)


@pytest.mark.parametrize(
    "kind,value", [("class_path", None), ("class_path", 5), ("unsupported", "invented"), ("not_declared", False)]
)
def test_value_coherence_is_a_model_invariant(kind, value):
    """Cross-field validators are deliberately separate from schema type/enum checks."""
    from crud_views.lib.manage_report import ValueRecord

    with pytest.raises(ValidationError):
        ValueRecord(kind=kind, value=value)


@pytest.mark.parametrize(
    "state,row", [("selected", None), ("not_selected", {"id": 1, "label": "x", "member_count": None, "cells": []})]
)
def test_actor_coherence_is_a_model_invariant(state, row):
    from crud_views.lib.manage_report import ActorSelection

    with pytest.raises(ValidationError):
        ActorSelection(state=state, row=row)
