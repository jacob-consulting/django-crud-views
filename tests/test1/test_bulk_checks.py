"""Bulk configuration diagnostics must use declarations without executing application hooks."""

import pytest
from django import forms
from django.core.checks import ERROR, WARNING
from django.urls import clear_url_caches

import tests.test1.project.urls  # noqa: F401 - register shared views before taking snapshots
from crud_views.checks import check_viewsets
from crud_views.lib import check as check_module
from crud_views.lib import viewset as registry
from crud_views.lib.bulk import BulkFormViewPermissionRequired, BulkSelectionMixin
from crud_views.lib.views import CardListView, ListView
from crud_views.lib.views.form import CustomFormNoObjectView, CustomFormNoObjectViewPermissionRequired
from crud_views.lib.views.mixins import ListViewTableMixin
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Publisher

BULK_IDS = {
    f"viewset.{kind}{number}"
    for number, kind in [
        (271, "E"),
        (272, "E"),
        (273, "E"),
        (274, "W"),
        (275, "W"),
        (276, "E"),
        (277, "E"),
        (278, "E"),
        (279, "E"),
    ]
}


@pytest.fixture
def bulk_registry():
    with registry._REGISTRY_LOCK:
        snapshot = dict(registry._REGISTRY)
    vocabulary = dict(check_module._VOCAB_CACHE)
    try:
        yield
    finally:
        with registry._REGISTRY_LOCK:
            registry._REGISTRY.clear()
            registry._REGISTRY.update(snapshot)
        check_module._VOCAB_CACHE.clear()
        check_module._VOCAB_CACHE.update(vocabulary)
        clear_url_caches()


def configured_views(*, source_base=None, source_key="list", viewset_class=ViewSet, model=Publisher):
    viewset = viewset_class(model=model, name="bulk_check_test")
    bases = (
        (BulkSelectionMixin, ListViewTableMixin, ListView) if source_base is None else (BulkSelectionMixin, source_base)
    )
    source = type(
        "BulkCheckSource",
        bases,
        {"cv_viewset": viewset, "cv_key": source_key, "cv_path": source_key, "cv_bulk_actions": ("bulk",)},
    )
    destination = type(
        "BulkCheckDestination",
        (BulkFormViewPermissionRequired,),
        {
            "cv_viewset": viewset,
            "cv_key": "bulk",
            "cv_path": "bulk",
            "cv_permission": "change",
            "cv_action_label_template_code": "Process records",
            "cv_action_short_label_template_code": "Process",
            "cv_form_valid": lambda self, form: None,
        },
    )
    return viewset, source, destination


def messages(view):
    return [message for check in view.checks() for message in check.messages()]


def ids(view):
    return {message.id for message in messages(view)}


def test_correct_bulk_configuration(bulk_registry):
    _, source, destination = configured_views()
    assert not (ids(source) | ids(destination)) & BULK_IDS
    for viewset in registry._REGISTRY.values():
        for view in viewset.get_all_views().values():
            if issubclass(view, (BulkSelectionMixin, BulkFormViewPermissionRequired)):
                assert not ids(view) & BULK_IDS


@pytest.mark.parametrize("value", [["bulk"], ("",), (123,), ("bulk", "bulk"), ([],)])
def test_source_action_shape(bulk_registry, value):
    _, source, _ = configured_views()
    source.cv_bulk_actions = value
    assert "viewset.E271" in ids(source)


def test_empty_actions_valid(bulk_registry):
    _, source, _ = configured_views()
    source.cv_bulk_actions = ()
    assert "viewset.E271" not in ids(source)


@pytest.mark.parametrize("registered", [False, True])
def test_destination_key_requires_bulk_class(bulk_registry, registered):
    viewset, source, _ = configured_views()
    source.cv_bulk_actions = ("other",)
    if registered:
        type(
            "PlainForm",
            (CustomFormNoObjectViewPermissionRequired,),
            {"cv_viewset": viewset, "cv_key": "other", "cv_path": "other"},
        )
    matches = [message for message in messages(source) if message.id == "viewset.E272"]
    assert len(matches) == 1 and "other" in matches[0].msg


@pytest.mark.parametrize("base, invalid", [(ListView, True), (CardListView, False), (None, False)])
def test_source_type(bulk_registry, base, invalid):
    _, source, _ = configured_views(source_base=base)
    assert ("viewset.E273" in ids(source)) is invalid


@pytest.mark.parametrize(
    "size, pagination, limit, warning",
    [
        (200, None, 100, True),
        (10, {"per_page": 150}, 100, True),
        (200, False, 100, False),
        (None, None, 100, False),
        (200, None, 500, False),
        ("200", None, 100, False),
        (True, None, 100, False),
    ],
)
def test_page_size_warning(bulk_registry, size, pagination, limit, warning):
    _, source, destination = configured_views()
    source.paginate_by = size
    source.table_pagination = pagination
    destination.cv_bulk_max = limit
    matches = [message for message in check_viewsets() if message.id == "viewset.W274" and str(source) in message.msg]
    assert bool(matches) is warning
    if warning:
        assert matches[0].level == WARNING
        assert "bulk" in matches[0].msg and str(limit) in matches[0].msg


@pytest.mark.parametrize(
    "key, cancel, warning", [("custom", "auto", True), ("custom", ["custom"], False), ("card", "auto", False)]
)
def test_cancel_origin_warning(bulk_registry, key, cancel, warning):
    _, source, destination = configured_views(source_base=CardListView, source_key=key)
    destination.cv_cancel_keys = cancel
    matches = [message for message in check_viewsets() if message.id == "viewset.W275" and str(source) in message.msg]
    assert bool(matches) is warning
    if warning:
        assert matches[0].level == WARNING and "cv_cancel_key" in matches[0].msg


def test_resource_and_composite_destinations(bulk_registry, monkeypatch):
    from tests.test1.test_resource_viewset import T2Item

    _, source, destination = configured_views(model=T2Item)
    assert "viewset.E273" in ids(source)
    assert "viewset.E276" in ids(destination)
    destination.cv_viewset.model = Publisher
    monkeypatch.setattr(Publisher._meta, "pk_fields", (Publisher._meta.pk, Publisher._meta.pk), raising=False)
    assert "viewset.E276" in ids(destination)


@pytest.mark.parametrize(
    "limit, invalid", [(0, True), (-1, True), (True, True), ("100", True), (None, True), (1, False), (500, False)]
)
def test_positive_integer_limit(bulk_registry, limit, invalid):
    _, _, destination = configured_views()
    destination.cv_bulk_max = limit
    assert ("viewset.E277" in ids(destination)) is invalid


def test_crispy_form_required(bulk_registry):
    _, _, destination = configured_views()
    destination.form_class = forms.Form
    assert "viewset.E278" in ids(destination)


@pytest.mark.parametrize(
    "attribute, value, error, warning",
    [
        ("cv_bulk_max", None, "E277", "W274"),
        ("cv_bulk_max", "100", "E277", "W274"),
        ("cv_cancel_keys", 123, "E252", "W275"),
        ("cv_cancel_keys", ("list",), "E252", "W275"),
        ("form_class", None, "E278", None),
        ("form_class", "invalid.Form", "E278", None),
    ],
)
def test_malformed_destination_pipeline(bulk_registry, attribute, value, error, warning):
    _, source, destination = configured_views()
    source.paginate_by = 200
    setattr(destination, attribute, value)
    result = check_viewsets()
    assert any(
        message.id == f"viewset.{error}" and str(destination) in message.msg and message.level == ERROR
        for message in result
    )
    if warning:
        assert not any(message.id == f"viewset.{warning}" and str(source) in message.msg for message in result)


@pytest.mark.parametrize("configuration", ["noop", "object", "hook_only"])
def test_explicit_write_required(bulk_registry, configuration):
    _, _, destination = configured_views()
    if configuration == "object":
        destination.cv_object = True
    else:
        destination.cv_form_valid = CustomFormNoObjectView.cv_form_valid
        if configuration == "hook_only":
            destination.cv_form_valid_hook = lambda self, form: None
    matches = [message for message in messages(destination) if message.id == "viewset.E279"]
    assert len(matches) == 1 and "cv_form_valid" in matches[0].msg


@pytest.mark.parametrize(
    "attribute, value, expected",
    [("cv_permission", None, "E202"), ("cv_modal", True, "E251"), ("cv_action_label_template_code", None, "E110")],
)
def test_existing_checks_reused(bulk_registry, attribute, value, expected):
    _, _, destination = configured_views()
    setattr(destination, attribute, value)
    assert f"viewset.{expected}" in ids(destination)


def test_checks_do_not_execute_application_code(bulk_registry, monkeypatch):
    _, source, destination = configured_views()

    def forbidden(*args, **kwargs):
        pytest.fail("System checks executed application code")

    for name in ("get_queryset", "cv_bulk_has_permission", "cv_bulk_check", "cv_has_access"):
        monkeypatch.setattr(destination, name, forbidden)
    monkeypatch.setattr(destination.form_class, "__init__", forbidden)
    assert not (ids(source) | ids(destination)) & BULK_IDS


def test_guardian_default_hook_warning(bulk_registry):
    from django.core.checks import run_checks

    from crud_views_guardian.lib.viewset import GuardianViewSet

    _, _, destination = configured_views(viewset_class=GuardianViewSet)
    matches = [
        message for message in run_checks(tags=["crud_views_guardian"]) if message.id == "crud_views_guardian.W002"
    ]
    assert len(matches) == 1
    assert matches[0].obj is destination and matches[0].level == WARNING


def test_guardian_overridden_hook_and_core_are_silent(bulk_registry):
    from crud_views_guardian.checks import collect_guardian_bulk_checks
    from crud_views_guardian.lib.viewset import GuardianViewSet

    viewset, _, destination = configured_views(viewset_class=GuardianViewSet)

    def forbidden(*args, **kwargs):
        pytest.fail("Collector executed the permission hook")

    destination.cv_bulk_has_permission = forbidden
    assert collect_guardian_bulk_checks([viewset]) == []
    core, _, _ = configured_views()
    assert collect_guardian_bulk_checks([core]) == []


def test_guardian_warning_silenced(bulk_registry):
    from django.test import override_settings

    from crud_views_guardian.checks import collect_guardian_bulk_checks
    from crud_views_guardian.lib.viewset import GuardianViewSet

    viewset, _, _ = configured_views(viewset_class=GuardianViewSet)
    with override_settings(SILENCED_SYSTEM_CHECKS=["crud_views_guardian.W002"]):
        assert collect_guardian_bulk_checks([viewset])[0].is_silenced()


def test_guardian_warning_loads_urlconf_before_registry(bulk_registry, monkeypatch):
    from crud_views_guardian.checks import check_guardian_bulk
    from crud_views_guardian.lib.viewset import GuardianViewSet

    loaded = []

    def load():
        loaded.append(configured_views(viewset_class=GuardianViewSet)[2])

    monkeypatch.setattr("crud_views.checks._url_configuration_loaded", load)
    result = check_guardian_bulk()
    assert len(loaded) == 1
    assert any(message.id == "crud_views_guardian.W002" and message.obj is loaded[0] for message in result)


def test_guardian_warning_in_german(bulk_registry):
    from django.utils.translation import override

    from crud_views_guardian.checks import collect_guardian_bulk_checks
    from crud_views_guardian.lib.viewset import GuardianViewSet

    viewset, _, _ = configured_views(viewset_class=GuardianViewSet)
    with override("de"):
        message = collect_guardian_bulk_checks([viewset])[0]
    assert message.msg == (
        "Sammelaktion in einem GuardianViewSet überschreibt cv_bulk_has_permission nicht: "
        "Jeder Eintrag, den ihr Queryset zeigt, gilt als erlaubt."
    )
    assert message.hint == (
        "cv_bulk_has_permission mit der Objektberechtigungsprüfung implementieren oder get_queryset() "
        "einschränken und crud_views_guardian.W002 stummschalten."
    )


def test_core_bulk_checks_without_guardian():
    from tests.test1.test_ancestor_policy import _fresh_settings

    result = _fresh_settings(
        'TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}],',
        """
        import django
        django.setup()
        from django.contrib.auth.models import Group
        from crud_views.lib.bulk import BulkSelectionMixin, BulkFormViewPermissionRequired
        from crud_views.lib.views import ListView, ListViewTableMixin
        from crud_views.lib.viewset import ViewSet
        viewset = ViewSet(model=Group, name="core_bulk")
        class Source(BulkSelectionMixin, ListViewTableMixin, ListView):
            cv_viewset = viewset
            cv_bulk_actions = ("bulk",)
        class Destination(BulkFormViewPermissionRequired):
            cv_viewset = viewset
            cv_key = "bulk"
            cv_path = "bulk"
            cv_permission = "change"
            cv_action_label_template_code = "Process"
            cv_action_short_label_template_code = "Process"
            def cv_form_valid(self, context):
                pass
        messages = [message for check in viewset.checks() for message in check.messages()]
        assert not any(message.id in {"viewset.E271", "viewset.E272", "viewset.E273", "viewset.E276",
            "viewset.E277", "viewset.E278", "viewset.E279", "viewset.W274", "viewset.W275"} for message in messages)
        assert not any(name.startswith(("guardian", "crud_views_guardian")) and module is not None
            for name, module in sys.modules.items())
        print("CORE-BULK-OK")
        """,
        block_guardian=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "CORE-BULK-OK"
