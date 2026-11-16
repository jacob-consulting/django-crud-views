"""Validate real cv_manage_view exports independently of Django and Pydantic.

Run with the audited system interpreter after exporting into a fresh directory:
    python3 tests/check_manage_schema.py /tmp/cv-0636-schema.XXXXXX
No dependency is installed or replaced by this verification tool.
"""

import argparse
import hashlib
import json
import sys
from importlib.metadata import version
from pathlib import Path

REQUIRED = {
    "schema",
    "catalogue",
    "inspection",
    "inspection-guardian",
    "inspection-resource",
    "inspection-selected",
    "inspection-shown",
    "inspection-additive",
    "partial",
    "failed",
    "failed-catalogue",
    "invalid",
    "invalid-required",
    "invalid-type",
    "invalid-enum",
    "invalid-kind",
    "invalid-section",
    "invalid-source",
    "invalid-value",
    "invalid-visibility",
    "invalid-actor",
    "invalid-policy",
    "invalid-count",
    "invalid-identity",
    "invalid-union",
    "invalid-error",
}


def check(directory):
    try:
        import jsonschema
        from jsonschema.validators import validator_for
    except ImportError as exc:
        raise RuntimeError(
            "Independent verifier requires jsonschema; use the audited system python3 environment"
        ) from exc

    files = {path.stem: path for path in directory.glob("*.json")}
    missing = REQUIRED - files.keys()
    if missing:
        raise RuntimeError("Missing command exports: " + ", ".join(sorted(missing)))
    documents = {name: json.loads(path.read_text()) for name, path in files.items()}
    published = Path(__file__).resolve().parents[1] / "docs/reference/cv_manage_view.schema.json"
    receipt = {
        "python": sys.version,
        "jsonschema_version": version("jsonschema"),
        "jsonschema_module": jsonschema.__file__,
        "fixture_directory": str(directory.resolve()),
        "fixtures": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sorted(files.items())},
        "schemas": {},
    }
    for name, schema_path in (("runtime", files["schema"]), ("published", published)):
        schema = json.loads(schema_path.read_text())
        validator_class = validator_for(schema)
        validator_class.check_schema(schema)
        validator = validator_class(schema)
        accepted = rejected = 0
        for fixture, document in sorted(documents.items()):
            if fixture == "schema":
                continue
            try:
                validator.validate(document)
            except jsonschema.ValidationError as exc:
                if not fixture.startswith("invalid"):
                    raise RuntimeError(f"{name} schema rejected valid export {fixture}: {exc.message}") from exc
                rejected += 1
            else:
                if fixture.startswith("invalid"):
                    raise RuntimeError(f"{name} schema accepted invalid fixture {fixture}")
                accepted += 1
        receipt["schemas"][name] = {
            "path": str(schema_path.resolve()),
            "sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
            "validator": validator_class.__name__,
            "accepted": accepted,
            "rejected": rejected,
        }
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Fresh directory populated by the command export test")
    args = parser.parse_args()
    try:
        receipt = check(args.directory)
    except Exception as exc:
        print(f"Schema verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
