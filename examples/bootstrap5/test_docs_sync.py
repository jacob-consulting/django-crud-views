"""Docs <-> examples sync check (M4).

A fenced code block in ``docs/`` immediately preceded by a marker comment::

    <!-- cv-sync: library/views.py -->

must appear verbatim (whitespace-normalized, blank lines ignored) as a
contiguous run of lines in the referenced file. Paths are relative to
``examples/bootstrap5/``. Blocks without a marker are exempt -- the tutorial
uses unmarked blocks for progressive intermediate states.
"""

import re
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent
DOCS_DIR = EXAMPLES_DIR.parents[1] / "docs"

SYNC_BLOCK_RE = re.compile(
    r"<!--\s*cv-sync:\s*(?P<target>\S+)\s*-->\s*```[a-z0-9]*\n(?P<code>.*?)^```",
    re.DOTALL | re.MULTILINE,
)


def find_sync_blocks(markdown: str) -> list[tuple[str, str]]:
    """Return (target, code) tuples for all marked fenced blocks."""
    return [(m["target"], m["code"]) for m in SYNC_BLOCK_RE.finditer(markdown)]


def significant_lines(text: str) -> list[str]:
    """Lines with trailing whitespace stripped, blank lines dropped."""
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def contains_contiguous(haystack: list[str], needle: list[str]) -> bool:
    if not needle:
        return False
    return any(haystack[i : i + len(needle)] == needle for i in range(len(haystack) - len(needle) + 1))


MARKDOWN_FIXTURE = """
Intro text.

<!-- cv-sync: library/views.py -->
```python
cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

Unmarked blocks are exempt:

```python
print("scratch")
```
"""


def test_find_sync_blocks_extracts_marked_only():
    blocks = find_sync_blocks(MARKDOWN_FIXTURE)
    assert blocks == [
        ("library/views.py", 'cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")\n')
    ]


def test_significant_lines_drops_blanks_and_trailing_ws():
    assert significant_lines("a  \n\n  b\n") == ["a", "  b"]


def test_contains_contiguous():
    haystack = ["a", "b", "c", "d"]
    assert contains_contiguous(haystack, ["b", "c"])
    assert not contains_contiguous(haystack, ["b", "d"])
    assert not contains_contiguous(haystack, [])


def iter_marked_blocks():
    params = []
    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        for target, code in find_sync_blocks(md_file.read_text(encoding="utf-8")):
            rel = md_file.relative_to(DOCS_DIR)
            params.append(pytest.param(md_file, target, code, id=f"{rel}:{target}"))
    return params


@pytest.mark.parametrize("md_file, target, code", iter_marked_blocks())
def test_marked_block_matches_source(md_file, target, code):
    source = EXAMPLES_DIR / target
    assert source.is_file(), f"{md_file}: cv-sync target {target!r} does not exist under examples/bootstrap5/"
    assert contains_contiguous(significant_lines(source.read_text(encoding="utf-8")), significant_lines(code)), (
        f"{md_file}: marked block not found contiguously in {target} (whitespace-normalized)"
    )
