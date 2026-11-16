"""Inspect registered configuration through the configured manage builders."""

import json
from typing import ClassVar

from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from crud_views.checks import _url_configuration_loaded
from crud_views.lib.manage_report import CatalogueData, CatalogueEntry, CatalogueResult, ReportError, Selection
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
    return 0 if report.status == "complete" else 2


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
        try:
            if invalid:
                report = CatalogueResult(
                    status="failed",
                    selection=selection,
                    data=None,
                    errors=[
                        ReportError(code="invalid_arguments", message=_("Choose --list, --schema or a ViewSet name."))
                    ],
                )
            else:
                entries = _load_catalogue()
                report = CatalogueResult(
                    status="complete",
                    selection=selection,
                    data=CatalogueData(
                        entries=[
                            CatalogueEntry(**_identity(entry), views=list(entry.get_all_views())) for entry in entries
                        ]
                    ),
                )
        except Exception as exc:
            report = CatalogueResult(
                status="failed",
                selection=selection,
                data=None,
                errors=[ReportError(code="collection_failed", message=str(exc), exception_class=type(exc).__name__)],
            )
        self.stdout.write(_format_json(report) if as_json else _format_text(report), style_func=lambda value: value)
        code = _exit_code(report)
        if code:
            raise SystemExit(code)
