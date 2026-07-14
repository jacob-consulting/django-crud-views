"""Reusable download-and-stamp infrastructure for extension apps that vendor third-party JS/CSS.

Extension apps build a VendorSpec from their settings and get a ~10-line management
command (call vendor()) plus a drift system check (call check_vendored()) for free.
The target directory must be a project directory on STATICFILES_DIRS — never an
installed package's static/ directory.
"""

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List

from django.core.checks import CheckMessage
from django.core.checks import Warning as CheckWarning

STAMP_NAME = ".vendored"


@dataclass(frozen=True)
class VendorSpec:
    key: str  # registry/bundle key, e.g. "datetimepicker"
    version: str  # pinned upstream version
    base_url: str  # URL template containing {version}
    files: tuple  # filenames to download
    target: Path  # destination directory (should embed the version in its path)

    @property
    def resolved_base_url(self) -> str:
        return self.base_url.format(version=self.version)


def vendor(spec: VendorSpec) -> List[Path]:
    """Download spec.files into spec.target and write a version stamp."""
    spec.target.mkdir(parents=True, exist_ok=True)
    written = []
    base = spec.resolved_base_url.rstrip("/")
    for name in spec.files:
        path = spec.target / name
        with urllib.request.urlopen(f"{base}/{name}") as response:  # noqa: S310
            path.write_bytes(response.read())
        written.append(path)
    (spec.target / STAMP_NAME).write_text(json.dumps({"key": spec.key, "version": spec.version}))
    return written


def check_vendored(spec: VendorSpec) -> List[CheckMessage]:
    """System-check helper: warn when configured pin and vendored files drift."""
    stamp = spec.target / STAMP_NAME
    if not stamp.exists():
        return [
            CheckWarning(
                f"crud_views asset bundle {spec.key!r} is configured as vendored, "
                f"but no vendored files were found at {spec.target}.",
                hint=f"Run the vendor management command for {spec.key!r}.",
                id="crud_views.W330",
            )
        ]
    data = json.loads(stamp.read_text())
    if data.get("version") != spec.version:
        return [
            CheckWarning(
                f"crud_views asset bundle {spec.key!r}: vendored version "
                f"{data.get('version')!r} does not match configured version {spec.version!r}.",
                hint=f"Re-run the vendor management command for {spec.key!r}.",
                id="crud_views.W331",
            )
        ]
    return []
