"""Import-pure, read-only companion provenance and isolated evidence tooling."""


class EvidenceError(ValueError):
    """A required source or evidence predicate is not established."""


def inspect_sources(root, revision, origin):
    return {"companion_root": str(root)}
