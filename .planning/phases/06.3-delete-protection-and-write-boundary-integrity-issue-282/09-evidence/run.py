"""Capture one plan-09 command without suppressing its output or exit status."""

import argparse
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/alex/projects/alex/django-crud-views")
HERE = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(["git", *args])


def runtime():
    import django
    import django.db.models.deletion as deletion

    import crud_views

    paths = git("diff", "--name-only", "c65bfd5", "--", "src").decode().splitlines()
    hashes = {}
    for filename in paths:
        relative = Path(filename).relative_to("src")
        spec = importlib.util.find_spec(relative.parts[0])
        installed = Path(spec.origin).parent.joinpath(*relative.parts[1:])
        hashes[filename] = {
            "imported": str(installed),
            "checkout_sha256": hashlib.sha256(Path(filename).read_bytes()).hexdigest(),
            "imported_sha256": hashlib.sha256(installed.read_bytes()).hexdigest(),
        }
    return {
        "executable": sys.executable,
        "python": platform.python_version(),
        "django": django.get_version(),
        "crud_views": crud_views.__file__,
        "versions": {
            name: importlib.metadata.version(name)
            for name in [
                "django",
                "django-guardian",
                "django-polymorphic",
                "django-ordered-model",
                "django-crispy-forms",
                "crispy-bootstrap5",
                "pytest",
                "pytest-django",
                "pydantic",
            ]
        },
        "django_deletion_sha256": hashlib.sha256(Path(deletion.__file__).read_bytes()).hexdigest(),
        "changed_production_hashes": hashes,
        "all_changed_source_matches": all(row["checkout_sha256"] == row["imported_sha256"] for row in hashes.values()),
    }


if __name__ == "__main__":
    assert Path.cwd() == ROOT
    assert git("rev-parse", "--show-toplevel").decode().strip() == str(ROOT)
    if sys.argv[1:] == ["probe"]:
        print(json.dumps(runtime(), indent=2))
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("--python")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[0] == "--" else args.command
    record = {
        "label": args.label,
        "started": datetime.datetime.now(datetime.UTC).isoformat(),
        "head": git("rev-parse", "HEAD").decode().strip(),
        "diff_sha256": hashlib.sha256(git("diff", "HEAD", "--binary")).hexdigest(),
        "source_diff_sha256": hashlib.sha256(git("diff", "HEAD", "--binary", "--", "src", "tests")).hexdigest(),
        "source_tree_sha256": hashlib.sha256(git("ls-tree", "-r", "HEAD", "--", "src", "tests", "docs")).hexdigest(),
        "command": shlex.join(command),
        "environment": {name: os.environ.get(name) for name in ["PYTHONPATH", "PYTEST_XDIST_AUTO_NUM_WORKERS"]},
    }
    if args.python:
        record["runtime"] = json.loads(subprocess.check_output([args.python, __file__, "probe"]))
        assert record["runtime"]["all_changed_source_matches"]
    start = time.monotonic()
    with (HERE / f"{args.label}.log").open("w") as output:
        output.write(json.dumps(record, indent=2) + "\n")
        output.flush()
        print(f"START {args.label}: {record['command']}", flush=True)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            output.write(line)
            output.flush()
            print(line, end="", flush=True)
        record["exit_code"] = process.wait()
        record["duration_seconds"] = round(time.monotonic() - start, 3)
        record["finished"] = datetime.datetime.now(datetime.UTC).isoformat()
        output.write("\nRESULT " + json.dumps(record) + "\n")
    (HERE / f"{args.label}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"END {args.label}: exit={record['exit_code']}; seconds={record['duration_seconds']}", flush=True)
    sys.exit(record["exit_code"])
