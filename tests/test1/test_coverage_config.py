"""Guards against drift between the coverage config and the packages in src/.

`crud_views_guardian` was missing from `[tool.coverage.run].source` for a long time
without anyone noticing, because the whole config was inert — coverage.py never found
it while pytest ran from `tests/`. See issue #103.
"""

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _coverage_config() -> dict:
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["tool"]["coverage"]


def _coverage_run_config() -> dict:
    return _coverage_config()["run"]


def test_coverage_source_lists_every_src_package():
    """Every distributed package must be measured, in sorted order."""
    packages = sorted(p.name for p in (REPO_ROOT / "src").iterdir() if (p / "__init__.py").is_file())
    assert _coverage_run_config()["source"] == packages


def test_coverage_emits_relative_paths():
    """Without this, coverage.xml carries an absolute machine-specific <source> prefix."""
    assert _coverage_run_config()["relative_files"] is True


def test_coverage_remaps_installed_package_paths_to_src():
    """nox installs the package non-editably, so coverage sees it under site-packages.

    Without this remapping the report names files
    `.nox/<session>/lib/python3.X/site-packages/crud_views/apps.py`, which Codecov
    cannot match to anything in the repository — the same failure #103 is about,
    only in a different disguise. Running pytest directly against the editable
    `.venv` does *not* reproduce it, which is why it was nearly missed.
    """
    assert _coverage_config()["paths"]["source"] == ["src/", "*/site-packages/"]
