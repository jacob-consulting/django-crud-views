"""Query measurements of nested requests for the ancestor-authorization performance note.

Each case builds an isolated chain (``tests.test1.ancestor_cases``), grants every permission any mode needs, and
issues one cold request (fresh content-type cache and permission vocabulary) followed by one warm repeat of the
same request. ``MODE`` names the authorization behaviour being measured; ``legacy`` is the behaviour before ancestor
policies existed. Counts are recorded, not asserted: they vary across Django versions and the note explains them.

Set ``CV_ANCESTOR_PERF_REPORT=<path>`` to append one JSON line per measured request for the performance note.
"""

import json
import os
import re
from collections import Counter

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from tests.test1.ancestor_cases import ancestor_routes, chain_objects, grant_all

MODE = "legacy"

_TABLE = re.compile(r'\bFROM\s+"([^"]+)"', re.IGNORECASE)
_WRITE = re.compile(r'^\s*(INSERT INTO|UPDATE|DELETE FROM)\s+"([^"]+)"', re.IGNORECASE)
_GUARDIAN_JOIN = re.compile(r'\bJOIN\s+"(guardian_[^"]+)"', re.IGNORECASE)


def _category(sql: str) -> str:
    """The table a statement reads (or writes); a Guardian grant lookup is named by its grant table."""
    match = _WRITE.match(sql)
    if match:
        return f"{match.group(1).split()[0].lower()} {match.group(2)}"
    match = _GUARDIAN_JOIN.search(sql)
    if match:
        return match.group(1)
    match = _TABLE.search(sql)
    return match.group(1) if match else sql.split()[0].upper()


def _measure(client: Client, url: str) -> tuple[int, int, dict[str, int]]:
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url)
    categories = Counter(_category(query["sql"]) for query in ctx.captured_queries)
    return response.status_code, len(ctx.captured_queries), dict(sorted(categories.items()))


def _report(record: dict) -> None:
    path = os.environ.get("CV_ANCESTOR_PERF_REPORT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


@pytest.mark.django_db
@pytest.mark.parametrize("family", ["core", "guardian"])
@pytest.mark.parametrize("depth", [1, 3])
@pytest.mark.parametrize("key", ["list", "detail", "create"])
def test_nested_request_queries(family, depth, key):
    from django.contrib.auth.models import User

    with ancestor_routes(family, depth) as routes:
        ancestors, rows = chain_objects(depth)
        user = User.objects.create_user(username="ancestor-perf", password="password")
        grant_all(user, routes, ancestors, rows)
        client = Client(raise_request_exception=True)
        client.force_login(user)
        url = routes.url(key, ancestors, obj=rows[0] if key == "detail" else None)

        routes.reset_vocabulary()
        cold = _measure(client, url)
        warm = _measure(client, url)

        for label, (status, total, categories) in (("cold", cold), ("warm", warm)):
            assert status == 200, (label, url, status)
            _report(
                {
                    "mode": MODE,
                    "family": family,
                    "depth": depth,
                    "key": key,
                    "phase": label,
                    "status": status,
                    "queries": total,
                    "categories": categories,
                }
            )
