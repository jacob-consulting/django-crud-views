"""#221: django-bootstrap5 is not a dependency of the package or of either host project.

crud_views renders messages with ``{% cv_messages %}`` and the example and test projects load Bootstrap from a
CDN tag, so nothing may reference the app again. ``docs/`` and ``CHANGELOG.md`` are deliberately not scanned:
both name the package in migration prose.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
# The shipped package, the packaging metadata and both host projects that used the tags (#221).
ROOTS = [
    REPO / "src",
    REPO / "pyproject.toml",
    REPO / "tests" / "test1",
    REPO / "examples" / "bootstrap5",
]
# collectstatic output and caches live under examples/bootstrap5 on a developer machine.
SKIP = {"__pycache__", "staticfiles", "node_modules"}


def _scan(root: Path):
    for path in [root] if root.is_file() else root.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".html", ".toml"} or path == SELF:
            continue
        if any(part in SKIP or part.startswith(".") for part in path.relative_to(REPO).parts):
            continue
        yield path


FILES = sorted({path for root in ROOTS for path in _scan(root)})


def test_files_are_discovered():
    assert FILES, "no files found to scan"


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(REPO)))
def test_no_django_bootstrap5_reference(path):
    source = path.read_text(encoding="utf-8")
    for needle in ("django_bootstrap5", "django-bootstrap5"):
        assert needle not in source, (
            f"{path.relative_to(REPO)} references {needle}; crud_views renders messages with "
            "{% cv_messages %} and loads Bootstrap from a CDN tag (#221)"
        )
