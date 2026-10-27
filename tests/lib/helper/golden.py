"""Normalised markup goldens shared by the table and card pagination tests."""

import os
import re
from pathlib import Path

from lxml import html


def check_golden(path: Path, element):
    """Compare ``element``'s whitespace-normalised markup with ``path``; rewrite it when CV_UPDATE_GOLDEN is set."""
    markup = re.sub(r"\s+", " ", re.sub(r">\s+<", "><", html.tostring(element, encoding="unicode"))).strip()
    if os.environ.get("CV_UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markup + "\n", encoding="utf-8")
    assert markup == path.read_text(encoding="utf-8").strip()
