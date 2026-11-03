"""Fail if a built wheel or sdist contains anything outside its allowlist.

Usage: python scripts/check_dist.py dist/

The repository carries planning and tooling folders (.planning/, superpowers/, .codegraph/, .gsd/, ...) that must
never reach PyPI. Rather than list what to keep out, this checks every archive member against what may go in, so a
new folder at the repository root fails the build until someone decides where it belongs.
"""

import sys
import tarfile
import zipfile
from pathlib import Path

# Top-level entries allowed in the sdist, below its "<name>-<version>/" prefix. Keep in sync with
# [tool.hatch.build.targets.sdist] only-include in pyproject.toml; hatchling adds PKG-INFO and .gitignore itself.
SDIST_ALLOWED = {
    "src",
    "tests",
    "docs",
    "examples",
    "noxfile.py",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "pyproject.toml",
    "PKG-INFO",
    ".gitignore",
}

# Top-level entries allowed in the wheel: the five packages plus the .dist-info directory.
WHEEL_PACKAGES = {
    "crud_views",
    "crud_views_workflow",
    "crud_views_polymorphic",
    "crud_views_guardian",
    "crud_views_object_detail",
}


def sdist_violations(path: Path) -> list[str]:
    with tarfile.open(path) as tar:
        names = tar.getnames()
    bad = []
    for name in names:
        parts = name.split("/", 2)
        if len(parts) < 2 or not parts[1]:
            continue  # the "<name>-<version>/" root itself
        if parts[1] not in SDIST_ALLOWED:
            bad.append(name)
    return bad


def wheel_violations(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as whl:
        names = whl.namelist()
    bad = []
    for name in names:
        top = name.split("/", 1)[0]
        if top not in WHEEL_PACKAGES and not top.endswith(".dist-info"):
            bad.append(name)
    return bad


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    dist = Path(argv[1])
    sdists = sorted(dist.glob("*.tar.gz"))
    wheels = sorted(dist.glob("*.whl"))
    if not sdists or not wheels:
        print(f"expected at least one sdist and one wheel in {dist}/", file=sys.stderr)
        return 1

    failed = False
    for path, check in [(p, sdist_violations) for p in sdists] + [(p, wheel_violations) for p in wheels]:
        bad = check(path)
        if bad:
            failed = True
            tops = sorted({"/".join(n.split("/")[: 2 if path.suffix == ".gz" else 1]) for n in bad})
            print(f"FAIL {path.name}: {len(bad)} file(s) outside the allowlist, under: {', '.join(tops)}")
        else:
            print(f"ok   {path.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
