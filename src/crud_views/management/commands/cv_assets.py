import dataclasses
import json

from django.core.management import BaseCommand

from crud_views.lib.pipeline import asset_rows


class Command(BaseCommand):
    help = (
        "List the crud_views asset registry (core + registered bundles) and how each asset is delivered: "
        "tag, tag (CDN), pipeline:<package> or none. Use --external to list the CDN assets to vendor."
    )

    def add_arguments(self, parser):
        parser.add_argument("--external", action="store_true", help="Only external (CDN) entries.")
        parser.add_argument("--kind", choices=("js", "css"), help="Only this asset kind.")
        parser.add_argument(
            "--format", choices=("table", "json"), default="table", dest="output_format", help="Output format."
        )

    def handle(self, *args, external=False, kind=None, output_format="table", **options):
        rows = [row for row in asset_rows() if (not external or row.external) and (kind is None or row.kind == kind)]
        if output_format == "json":
            self.stdout.write(json.dumps([dataclasses.asdict(row) for row in rows], indent=2))
            return
        lines = [("KEY", "KIND", "DELIVERY", "PATH")]
        for row in rows:
            path = f"{row.path}  [{row.integrity}]" if row.integrity else row.path
            lines.append((row.key, row.kind, row.delivery_label, path))
        widths = [max(len(line[i]) for line in lines) for i in range(3)]
        for line in lines:
            self.stdout.write("  ".join(line[i].ljust(widths[i]) for i in range(3)) + "  " + line[3])
