"""Estimate PR changed-line coverage from the source-bound coverage.py JSON.

Uses the actual PR base, zero-context Git diff, and coverage.py executable lines.
This estimate does not replace Codecov's multi-upload remote patch calculation.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    git = "/usr/bin/git"
    base = subprocess.check_output([git, "merge-base", args.base, "HEAD"], text=True).strip()
    diff = subprocess.check_output([git, "diff", "--unified=0", base, "--", "src"], text=True)
    changed = {}
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))? ", line)
            start, count = int(match[1]), int(match[2] or 1)
            changed.setdefault(current, set()).update(range(start, start + count))
    coverage = json.loads(args.coverage.read_text())
    files = {}
    for filename, lines in changed.items():
        if filename not in coverage["files"]:
            continue
        data = coverage["files"][filename]
        excluded = set(data["excluded_lines"])
        covered = (set(data["executed_lines"]) & lines) - excluded
        missing = (set(data["missing_lines"]) & lines) - excluded
        if covered or missing:
            files[filename] = {
                "covered": len(covered),
                "executable": len(covered | missing),
                "missing_lines": sorted(missing),
                "existing_excluded_changed_lines": sorted(excluded & lines),
            }
    hit = sum(data["covered"] for data in files.values())
    total = sum(data["executable"] for data in files.values())
    result = {
        "requested_pr_base": args.base,
        "merge_base": base,
        "head": subprocess.check_output([git, "rev-parse", "HEAD"], text=True).strip(),
        "covered": hit,
        "executable": total,
        "percent": 100 * hit / total,
        "target": 96.92,
        "passes_local_estimate": 100 * hit / total >= 96.92,
        "remote_codecov_status": "pending; local estimate uses one Django 5.2 run",
        "files": files,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "files"}))


if __name__ == "__main__":
    main()
