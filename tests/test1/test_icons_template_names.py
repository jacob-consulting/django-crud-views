import re
from pathlib import Path

import crud_views
from crud_views.lib.icons import DEFAULT_ICONS

SRC = Path(crud_views.__file__).resolve().parent.parent
LITERAL = re.compile(r"""\{%\s*cv_icon\s+(["'])([^"']+)\1""")


def test_every_literal_icon_name_in_templates_is_a_default_icon():
    found = {}
    for path in SRC.glob("*/templates/**/*.html"):
        for match in LITERAL.finditer(path.read_text()):
            found[match.group(2)] = path
    assert found, "no cv_icon literals found; the scan is broken"
    unknown = {name: str(p) for name, p in found.items() if name not in DEFAULT_ICONS}
    assert unknown == {}
