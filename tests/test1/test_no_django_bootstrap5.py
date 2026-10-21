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
    # rglob() on a missing path yields nothing without complaining, which would narrow the guard in silence.
    assert root.exists(), f"scan root {root} does not exist; update ROOTS"
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


def test_scan_rejects_a_missing_root(tmp_path):
    """A renamed or absent root must fail loudly: rglob() on a missing path yields nothing, silently."""
    with pytest.raises(AssertionError):
        list(_scan(tmp_path / "does-not-exist"))


# What {% bootstrap_css %} / {% bootstrap_javascript %} used to emit, now written by hand: pin it, or a dropped
# or mistyped tag leaves both suites green and the pages unstyled.
BOOTSTRAP_ASSETS = [
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        "sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz",
    ),
]
BASE_TEMPLATES = [
    REPO / "tests" / "test1" / "app" / "templates" / "app" / "base.html",
    REPO / "examples" / "bootstrap5" / "project" / "templates" / "project" / "base.html",
]


@pytest.mark.parametrize("template", BASE_TEMPLATES, ids=lambda p: str(p.relative_to(REPO)))
@pytest.mark.parametrize("url,integrity", BOOTSTRAP_ASSETS, ids=["css", "js"])
def test_base_template_loads_bootstrap_with_sri(template, url, integrity):
    source = template.read_text(encoding="utf-8")
    assert url in source, f"{template.relative_to(REPO)} does not load {url}"
    assert integrity in source, f"{template.relative_to(REPO)} loads {url} without its SRI hash"


@pytest.mark.parametrize("template", BASE_TEMPLATES, ids=lambda p: str(p.relative_to(REPO)))
def test_base_template_renders_messages_through_crud_views(template):
    assert "{% cv_messages %}" in template.read_text(encoding="utf-8")
