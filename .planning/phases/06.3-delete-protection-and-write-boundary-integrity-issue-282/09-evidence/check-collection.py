"""Check added behavioral test families against each interpreter's actual collection."""

import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
required = json.loads((root / "expected-nodes.json").read_text())["required_families"]
reference = None
for series in ("42", "52", "60"):
    lines = (root / f"django{series}-collect.log").read_text().splitlines()
    nodes = {line for line in lines if line.startswith("tests/test1/") and "::" in line}
    missing = [
        f"{module}::{name}"
        for module, names in required.items()
        for name in names
        if not any(node == f"{module}::{name}" or node.startswith(f"{module}::{name}[") for node in nodes)
    ]
    assert not missing, (series, missing)
    if reference is None:
        reference = nodes
    else:
        assert nodes == reference, (series, sorted(nodes ^ reference))
    print(
        json.dumps(
            {
                "series": series,
                "selected": len(nodes),
                "missing_required": missing,
                "required_families": sum(map(len, required.values())),
                "per_module": dict(sorted(Counter(node.split("::")[0] for node in nodes).items())),
            }
        )
    )
