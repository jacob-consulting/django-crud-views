"""Inspect registered configuration through the configured manage builders."""

import json
from typing import ClassVar

from django.core.management import BaseCommand
from django.utils.translation import gettext as _
from pydantic import ValidationError

from crud_views.checks import _url_configuration_loaded
from crud_views.lib.access_trace import resolve_trace_user
from crud_views.lib.manage_report import (
    CatalogueData,
    CatalogueEntry,
    CatalogueResult,
    InspectionData,
    InspectionResult,
    Report,
    ReportError,
    Selection,
    adapt_section,
    report_schema,
)
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK


def _identity(viewset):
    return {
        "name": viewset.name,
        "kind": "resource"
        if viewset.is_resource
        else ("guardian" if viewset._ancestor_provider == "guardian" else "model"),
        "backing_class": f"{viewset.model.__module__}.{viewset.model.__qualname__}",
        "parent": viewset.parent.name if viewset.parent is not None else None,
    }


def _load_catalogue():
    if not _url_configuration_loaded():
        raise ValueError("Configured URLconf discovery did not complete")
    with _REGISTRY_LOCK:
        entries = list(_REGISTRY.values())
    return sorted(entries, key=lambda viewset: viewset.name)


def _text(value):
    return "".join(char if char.isprintable() else json.dumps(char)[1:-1] for char in str(value))


def _format_json(report):
    return json.dumps(report.model_dump(mode="json"), ensure_ascii=True, allow_nan=False, indent=2)


def _format_text(report):
    # An explicit field tree retains every validated fact, including empty/default values.
    lines = []

    def render(value, prefix=""):
        if isinstance(value, dict) and value:
            for key, item in value.items():
                render(item, f"{prefix}.{key}" if prefix else key)
        elif isinstance(value, list) and value:
            for index, item in enumerate(value):
                render(item, f"{prefix}[{index}]")
        else:
            lines.append(f"{_text(prefix)}: {_text(value)}")

    render(report.model_dump(mode="json"))
    return "\n".join(lines)


def _exit_code(report):
    if report.status != "complete":
        return 2
    if (
        report.kind == "inspection"
        and report.data.checks.data is not None
        and any(message.level >= 40 for message in report.data.checks.data.messages)
    ):
        return 1
    return 0


def _error(exc, section=None):
    return ReportError(
        code="output_validation_failed" if isinstance(exc, (ValidationError, KeyError)) else "collection_failed",
        section=section,
        message="; ".join(error["msg"] for error in exc.errors(include_input=False))
        if isinstance(exc, ValidationError)
        else str(exc),
        exception_class=type(exc).__name__,
        location=list(exc.errors(include_input=False)[0]["loc"]) if isinstance(exc, ValidationError) else [],
    )


def _inspect(viewset, selection, actor):
    identity = _identity(viewset)
    manage = viewset.get_all_views()["manage"]()
    sections, errors = {}, []
    # Builders retain all configuration, authorization and database semantics.
    with manage.manage_export():
        for name, method in (
            ("facts", "get_manage_facts"),
            ("presentation", "get_manage_presentation"),
            ("views", "get_manage_views"),
            ("routes", "get_manage_routes"),
            ("hierarchy", "get_manage_hierarchy"),
            ("ancestor_policy", "get_manage_ancestor_policy"),
            ("permissions", "get_manage_permissions"),
            ("checks", "get_manage_checks"),
            ("guardian", "get_manage_guardian"),
        ):
            if name == "guardian" and identity["kind"] != "guardian":
                sections[name] = {"status": "not_applicable", "data": None, "errors": []}
                continue
            try:
                raw = getattr(manage, method)(viewset, actor)
                data = adapt_section(name, raw, kind=identity["kind"], selected_view=selection.view)
                sections[name] = {"status": "ok", "data": data, "errors": []}
            except Exception as exc:
                sections[name] = {"status": "error", "data": None, "errors": [len(errors)]}
                errors.append(_error(exc, name))
    useful = any(section["status"] == "ok" for section in sections.values())
    return InspectionResult(
        status="complete" if not errors else "partial" if useful else "failed",
        selection=selection,
        data=InspectionData(identity=identity, **sections) if useful else None,
        errors=errors,
    )


class Command(BaseCommand):
    requires_system_checks: ClassVar[list] = []

    @property
    def help(self):
        return _("Inspect registered ViewSet configuration and permission diagnostics.")

    def add_arguments(self, parser):
        parser.add_argument("viewset", nargs="?")
        parser.add_argument("view", nargs="?")
        parser.add_argument("--list", action="store_true", dest="list_viewsets")
        parser.add_argument("--user")
        parser.add_argument("--as-json", action="store_true")
        parser.add_argument("--schema", action="store_true")

    def handle(
        self, *args, viewset=None, view=None, user=None, list_viewsets=False, as_json=False, schema=False, **options
    ):
        selection = Selection(viewset=viewset, view=view, user=user)
        invalid = (
            (list_viewsets and schema)
            or ((list_viewsets or schema) and any(item is not None for item in (viewset, view, user)))
            or not (list_viewsets or schema or viewset)
        )
        result_type = CatalogueResult if list_viewsets else InspectionResult

        def failed(code, message):
            return result_type(
                status="failed", selection=selection, data=None, errors=[ReportError(code=code, message=message)]
            )

        try:
            if invalid:
                report = failed("invalid_arguments", _("Choose --list, --schema or a ViewSet name."))
            elif schema:
                self.stdout.write(
                    json.dumps(report_schema(), ensure_ascii=True, allow_nan=False, indent=2),
                    style_func=lambda value: value,
                )
                return
            else:
                entries = _load_catalogue()
                if list_viewsets:
                    report = CatalogueResult(
                        status="complete",
                        selection=selection,
                        data=CatalogueData(
                            entries=[
                                CatalogueEntry(**_identity(entry), views=list(entry.get_all_views()))
                                for entry in entries
                            ]
                        ),
                    )
                else:
                    selected = next((entry for entry in entries if entry.name == viewset), None)
                    if selected is None:
                        report = failed("unknown_viewset", _("Unknown ViewSet: %(name)s") % {"name": viewset})
                    elif view is not None and view not in selected.get_all_views():
                        report = failed("unknown_view", _("Unknown view: %(name)s") % {"name": view})
                    else:
                        actor = resolve_trace_user(user) if user is not None else None
                        report = (
                            failed("unknown_user", _("Unknown user: %(name)s") % {"name": user})
                            if user is not None and actor is None
                            else _inspect(selected, selection, actor)
                        )
            report = Report.validate_python(report)
        except Exception as exc:
            report = result_type(status="failed", selection=selection, data=None, errors=[_error(exc)])
        self.stdout.write(_format_json(report) if as_json else _format_text(report), style_func=lambda value: value)
        code = _exit_code(report)
        if code:
            raise SystemExit(code)
