"""Validate the review packet and recorded consent; never create approval."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PHASE = Path(".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282")
INPUTS = tuple(
    str(PHASE / name) for name in ("06.3-FOCUS-DESIGN.md", "06.3-18-PLAN.md", "06.3-19-PLAN.md", "06.3-20-PLAN.md")
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(text):
    return json.loads(text, object_pairs_hook=unique_object)


def validate(root, command):
    manifest = read_json((root / PHASE / "18-evidence/review-binding.json").read_text())
    require(isinstance(manifest, dict), "Review binding must be an object")
    revision = manifest.get("reviewed_revision")
    require(isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision), "Invalid reviewed revision")
    hashes = manifest.get("artifact_sha256")
    require(isinstance(hashes, dict) and set(hashes) == set(INPUTS), "Expected exactly four reviewed inputs")
    for name in INPUTS:
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        require(hashes[name] == digest, f"Reviewed input changed: {name}")
    if command == "reviewable":
        return "FOCUS_REVIEWABLE"

    approval = (root / PHASE / "06.3-FOCUS-APPROVAL.md").read_text()
    records = re.findall(r"^```json\s*\n(.*?)^```[ \t]*$", approval, re.MULTILINE | re.DOTALL)
    require(len(records) == 1, "Expected exactly one fenced JSON approval record")
    record = read_json(records[0])
    require(isinstance(record, dict), "Approval record must be an object")
    require(record.get("decision") == "approved", "Actual approval is pending or rejected")
    for field in ("actual_response", "reviewer", "timestamp"):
        value = record.get(field)
        require(isinstance(value, str) and value.strip(), f"Missing actual approval field: {field}")
    require(record.get("reviewed_revision") == revision, "Approval revision does not match review packet")
    require(record.get("artifact_sha256") == hashes, "Approval hashes do not match review packet")
    return "FOCUS_APPROVAL_BOUND"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("reviewable", "approval"))
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Repository root (temporary copy for negative controls)",
    )
    args = parser.parse_args()
    try:
        result = validate(args.root, args.command)
    except (OSError, ValueError, TypeError) as error:
        print(f"FOCUS_GATE_FAILED: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
