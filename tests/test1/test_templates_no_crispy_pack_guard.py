import re
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
TEMPLATES = sorted(SRC_DIR.glob("crud_views*/templates/**/*.html"))
# A crispy pack path only; the lookbehind keeps a theme app path such as crud_views_bootstrap5/ out of it.
FORBIDDEN = re.compile(r"(?<![\w-])bootstrap5/")


def test_shipped_templates_are_discovered():
    assert TEMPLATES, f"no shipped templates found below {SRC_DIR}"


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: str(p.relative_to(SRC_DIR)))
def test_template_has_no_crispy_pack_path(path):
    source = path.read_text()
    assert not FORBIDDEN.search(source), (
        f"{path.relative_to(SRC_DIR)} hardcodes a bootstrap5/ template path, "
        "which ignores CRISPY_TEMPLATE_PACK and breaks on a non-Bootstrap pack"
    )
