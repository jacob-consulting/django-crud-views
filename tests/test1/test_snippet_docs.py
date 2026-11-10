"""Phase 06.21 (#339): the snippet-variable table in docs/reference/templates.md is the one canonical list."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "docs/reference/templates.md"
SECTION = "## Snippet variables"
VARIABLES = (
    "object",
    "view",
    "parent_object",
    "verbose_name",
    "verbose_name_plural",
    "verbose_name_translate",
    "verbose_name_plural_translate",
    "viewset",
)


def _section(path, heading):
    text = path.read_text()
    assert text.count(heading) == 1, f"Missing or duplicated section: {heading}"
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_snippet_variables_table_lists_exactly_the_eight_names():
    section = _section(TEMPLATES, SECTION)
    rows = re.findall(r"^\| `([a-z_]+)` \| (.*?) \|$", section, re.M)
    assert tuple(name for name, _ in rows) == VARIABLES
    cells = dict(rows)
    assert "cv" in cells["viewset"]
    assert "None" in cells["object"]
    # only parent_object is ever absent; object is always present, None when the view has none
    assert "absent" not in cells["object"]


def test_snippet_variables_section_states_the_class_label_exclusion():
    section = _section(TEMPLATES, SECTION)
    for needle in ("LinkChildColumn", "cv_action_label_template", "cv_breadcrumb_label_template"):
        assert needle in section
    assert "except" in section
    assert "parent_object" in section


def test_snippet_variables_section_documents_lazy_404_and_absent_key():
    section = _section(TEMPLATES, SECTION)
    for needle in ("string_if_invalid", "404", "one level", "no `request` or `user` key"):
        assert needle in section
