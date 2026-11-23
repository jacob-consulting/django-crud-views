"""What changed in the three Acme example copies since they were last declared in sync.

    python drift.py report    # read-only: every path under example/ that changed since the baseline
    python drift.py accept    # write the baseline from the three HEAD commits (only at the end of a sync)

The baseline (baseline.json, next to this file) holds the git blob id of every tracked file under example/ in each
repo, as of the last sync. A path whose three blob ids still equal the baseline is in the state that sync accepted,
identical or deliberately different, and is not reported. For every other path the report names the repos where it
changed (the sources of a port) and the repos where it did not (the targets).

Only committed state counts (HEAD). Checkouts are looked up next to the django-crud-views checkout that holds this
file; pass --tabler / --coreui / --adminlte for any other layout. Standard library only.

Exit status of "report": 0 when nothing drifted, 1 when at least one path did. 1 is a finding, not a failure.
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
THEMES = ("tabler", "coreui", "adminlte")
KINDS = (
    ("migrations", lambda p, name: "/migrations/" in p),
    ("tests", lambda p, name: "/tests/" in p or name.startswith("test") or name == "tests.py"),
    ("project config", lambda p, name: p.split("/")[1] in ("config", "manage.py", "pytest.ini")),
    ("project templates/static", lambda p, name: p.split("/")[1] in ("templates", "static")),
    ("app templates", lambda p, name: name.endswith(".html")),
    ("app static", lambda p, name: "/static/" in p),
    ("app python", lambda p, name: True),
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def kind(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return next(label for label, test in KINDS if test(path, name))


def snapshot(repo: Path) -> dict[str, str]:
    """path -> blob id for every file under example/ in the repo's HEAD commit."""
    blobs = {}
    for line in git(repo, "ls-tree", "-r", "HEAD", "--", "example").splitlines():
        meta, path = line.split("\t", 1)
        blobs[path] = meta.split()[2]
    return blobs


def has_object(repo: Path, name: str) -> bool:
    """True if the commit or blob is in this clone (a shallow clone may lack the baseline's)."""
    return subprocess.run(["git", "-C", str(repo), "cat-file", "-e", name], capture_output=True).returncode == 0


def commits_since(repo: Path, base: str) -> None:
    """Print the commits since the baseline that touch example/, and what else each of them touches."""
    if not has_object(repo, f"{base}^{{commit}}"):
        print("      baseline commit is not in this clone (shallow?): no commit list; try git fetch --unshallow")
        return
    for line in git(repo, "log", "--format=%h %ad %s", "--date=short", f"{base}..HEAD", "--", "example").splitlines():
        print(f"      {line}")
        outside = git(repo, "show", "--name-only", "--format=", line.split()[0], "--", ".", ":(exclude)example").split()
        if outside:
            print(f"          also outside example/: {', '.join(outside)}")


def report(repos: dict[str, Path], baseline: dict) -> int:
    now = {theme: snapshot(repo) for theme, repo in repos.items()}
    then = baseline["paths"]
    print(f"Baseline written {baseline['written']}.")
    for theme, repo in repos.items():
        head = git(repo, "rev-parse", "--short", "HEAD").strip()
        dirty = " (uncommitted changes under example/: not counted)" if git(repo, "status", "--porcelain", "--", "example") else ""
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
        print(f"  {theme:9} {repo}  {branch} at {head}, baseline {baseline['commits'][theme][:7]}{dirty}")
        commits_since(repo, baseline["commits"][theme])

    drift, converged = [], []
    for path in sorted(set(then) | set().union(*now.values())):
        old = then.get(path, dict.fromkeys(THEMES))
        new = {theme: now[theme].get(path) for theme in THEMES}
        if new == old:
            continue
        (converged if len(set(new.values())) == 1 else drift).append((path, old, new))

    print(f"\n{len(drift)} path(s) changed since the baseline and differ between the repos; {len(converged)} changed and are now identical in all three.")
    groups: dict[tuple, list] = {}
    for path, old, new in drift:
        sources = tuple(theme for theme in THEMES if new[theme] != old[theme])
        groups.setdefault(sources, []).append((path, old, new))
    for sources, items in groups.items():
        targets = [theme for theme in THEMES if theme not in sources]
        print(f"\n== changed in: {', '.join(sources)}   unchanged in: {', '.join(targets) or 'none'}   ({len(items)} path(s))")
        for path, old, new in items:
            print(f"\n  {path}   [{kind(path)}]")
            for theme in sources:
                repo, before, after = repos[theme], old[theme], new[theme]
                if after is None:
                    print(f"    {theme}: deleted")
                elif before is None:
                    print(f"    {theme}: new file      git -C {repo} show {after}")
                elif has_object(repo, before):
                    print(f"    {theme}: modified      git -C {repo} diff {before} {after}")
                else:
                    print(f"    {theme}: modified; the baseline blob {before[:7]} is not in this clone (git fetch --unshallow)")
                base = baseline["commits"][theme]
                if has_object(repo, f"{base}^{{commit}}"):
                    for line in git(repo, "log", "--format=%h", f"{base}..HEAD", "--", path).splitlines():
                        print(f"        in {line}")
            for theme in targets:
                print(f"    {theme}: {'absent' if new[theme] is None else 'as at the baseline'}")
    if converged:
        print("\n== changed and now identical in all three (nothing to port)")
        for path, _, _ in converged:
            print(f"  {path}")
    return 1 if drift else 0


def accept(repos: dict[str, Path], baseline_file: Path) -> int:
    now = {theme: snapshot(repo) for theme, repo in repos.items()}
    paths = {
        path: {theme: now[theme].get(path) for theme in THEMES} for path in sorted(set().union(*now.values()))
    }
    data = {
        "written": datetime.date.today().isoformat(),
        "commits": {theme: git(repo, "rev-parse", "HEAD").strip() for theme, repo in repos.items()},
        "paths": paths,
    }
    lines = [f"  {json.dumps(path)}: {json.dumps(blobs)}" for path, blobs in paths.items()]
    head = json.dumps({"written": data["written"], "commits": data["commits"]}, indent=1)[:-2]
    baseline_file.write_text(head + ',\n "paths": {\n' + ",\n".join(lines) + "\n }\n}\n")
    same = sum(1 for blobs in paths.values() if len(set(blobs.values())) == 1)
    print(f"Wrote {baseline_file}: {len(paths)} paths, {same} identical in all three, {len(paths) - same} accepted as different.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("command", choices=("report", "accept"))
    for theme in THEMES:
        parser.add_argument(f"--{theme}", type=Path, default=HERE.parents[2].parent / f"django-crud-views-{theme}")
    parser.add_argument("--baseline", type=Path, default=HERE / "baseline.json")
    args = parser.parse_args()
    repos = {theme: getattr(args, theme).resolve() for theme in THEMES}
    for theme, repo in repos.items():
        if not (repo / "example").is_dir():
            sys.exit(f"{theme}: no example/ in {repo}; pass --{theme} PATH")
    if args.command == "accept":
        return accept(repos, args.baseline)
    if not args.baseline.is_file():
        sys.exit(f"no baseline at {args.baseline}; run 'accept' once the three copies are in a state you accept")
    return report(repos, json.loads(args.baseline.read_text()))


if __name__ == "__main__":
    sys.exit(main())
