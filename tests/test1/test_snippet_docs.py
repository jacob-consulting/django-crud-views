"""Phase 06.21 (#339): the snippet-variable table in docs/reference/templates.md is the one canonical list."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "docs/reference/templates.md"
MESSAGES = ROOT / "docs/reference/messages.md"
NESTED = ROOT / "docs/reference/nested.md"
BREADCRUMB = ROOT / "docs/reference/breadcrumb.md"
CHANGELOG = ROOT / "CHANGELOG.md"
MIGRATING = ROOT / "docs/migrating-1.0.md"
PARENT_HEADER = 'cv_header_template_code = _("New department for {{ parent_object }}")'
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
    for needle in ("cv_action_label_template", "cv_breadcrumb_label_template"):
        assert needle in section
    assert "except" in section
    assert "parent_object" in section


def test_snippet_variables_section_documents_lazy_404_and_absent_key():
    section = _section(TEMPLATES, SECTION)
    for needle in ("string_if_invalid", "404", "one level", "no `request` or `user` key"):
        assert needle in section


def test_snippet_variables_are_linked_from_messages_nested_and_breadcrumb():
    for path in (MESSAGES, NESTED, BREADCRUMB):
        assert "templates.md#snippet-variables" in path.read_text(), path.name


def test_nested_docs_show_parent_object_header_in_an_unmarked_fence():
    text = NESTED.read_text()
    assert PARENT_HEADER in text
    # the marked fences from the fork point survive; examples/bootstrap5/test_docs_sync.py checks them verbatim
    assert text.count("<!-- cv-sync:") >= 4
    # select the example by content, not position, so surrounding prose cannot redirect the check
    fences = [m for m in re.finditer(r"^```python\n(.*?)^```$", text, re.M | re.S) if PARENT_HEADER in m.group(1)]
    assert len(fences) == 1
    before = text[: fences[0].start()]
    # same whitespace tolerance as SYNC_BLOCK_RE: no marker binds the fence, even across blank lines
    assert re.search(r"<!--\s*cv-sync:\s*\S+\s*-->\s*$", before) is None


def test_changelog_records_339_as_added_not_breaking():
    text = CHANGELOG.read_text()
    added = text.split("\n### Added\n", 1)[1]
    added = re.split(r"\n#{2,3} ", added, maxsplit=1)[0]
    assert "issues/339" in added
    assert "docs/reference/templates.md#snippet-variables" in added
    breaking = text.split("\n### Breaking\n", 1)[1].split("\n### Added\n", 1)[0]
    assert "issues/339" not in breaking
    assert "issues/339" not in MIGRATING.read_text()
