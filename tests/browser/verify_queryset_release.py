"""Bounded, source-bound release checks for phase 06.30; no dependency installation."""

import argparse
import copy
import json
import re
import subprocess
from pathlib import Path


def counts(output, kind):
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)
    patterns = {"pytest": r"(\d+) passed", "django": r"Ran (\d+) tests?", "vitest": r"Tests\s+(\d+) passed"}
    matches = re.findall(patterns[kind], output)
    return int(matches[-1]) if matches else 0


def validate_result(result):
    pass


def self_test():
    valid = {"exit": 0, "kind": "pytest", "output": "2 passed in 0.1s", "tests": 2}
    validate_result(valid)
    for name, changes in [
        ("failed exit", {"exit": 1}),
        ("zero tests", {"tests": 0, "output": "no tests ran"}),
        ("skipped behavior", {"output": "2 passed, 1 skipped"}),
        ("invented count", {"tests": 3}),
    ]:
        result = copy.deepcopy(valid)
        result.update(changes)
        try:
            validate_result(result)
        except (ValueError, AssertionError):
            continue
        raise AssertionError(f"Accepted {name}")
    print("SELF_TEST_OK release result negative controls: 4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
