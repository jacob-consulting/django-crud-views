import re
from pathlib import Path

import pytest

JS_DIR = Path(__file__).resolve().parents[2] / "src" / "crud_views" / "static" / "crud_views" / "js"
FORBIDDEN = re.compile(r"\bbootstrap\b|\bjQuery\b|\$\(|\$\.")


@pytest.mark.parametrize("name", ["viewset.js", "modal.js", "list.filter.js", "toggle.js", "tooltip.js"])
def test_core_script_has_no_jquery_or_bootstrap_token(name):
    source = (JS_DIR / name).read_text()
    assert not FORBIDDEN.search(source), f"{name} still references jQuery or a bootstrap global"
