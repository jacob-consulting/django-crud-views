"""Complete Guardian list response costs, with independently asserted row permissions."""

import json
import platform
import re
from collections import Counter
from importlib.metadata import version

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from lxml import html

from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.models import Publisher
from tests.test1.app.views import GuardianPublisherListView
from tests.test1.test_navbar_costs import cache_conditions


def list_sql_category(sql):
    """Attribute the outer SELECT; filtering subqueries are not checker grant loads."""
    sql = sql.lower()
    outer = re.search(r'\bfrom "([^"]+)"', sql)
    table = outer.group(1) if outer else None
    if table == "app_publisher":
        return "list_filter"
    if table == "auth_permission":
        if 'join "guardian_userobjectpermission"' in sql:
            return "checker_user_grants"
        if 'join "guardian_groupobjectpermission"' in sql:
            return "checker_group_grants"
        return "model_or_vocabulary_permissions"
    return {
        "auth_user": "actor",
        "django_session": "session",
        "django_content_type": "content_type",
        "auth_group": "groups",
    }.get(table, "other")


@pytest.mark.django_db
@pytest.mark.parametrize("row_count", [0, 1, 3])
def test_guardian_list_row_action_cost(row_count, cv_guardian_publisher, django_user_model, record_property):
    actor = django_user_model.objects.create_user(username="list-cost")
    setup_actor = django_user_model.objects.create_user(username="list-cost-vocabulary")
    rows = [Publisher.objects.create(name=f"Visible publisher {i}") for i in range(row_count)]
    excluded = Publisher.objects.create(name="Excluded publisher")
    for row in rows:
        user_guardian_object_perm(actor, cv_guardian_publisher, "view", row)
    client = Client()
    client.force_login(actor)
    url = reverse(cv_guardian_publisher.get_router_name("list"))
    assert GuardianPublisherListView.cv_list_actions == ["detail", "update", "delete"]

    # Reset process-global discovery, then warm exactly the same vocabulary in every
    # run. Only the setup actor is touched; Client obtains a fresh request user.
    with cache_conditions([cv_guardian_publisher], setup_actor, vocabulary="warm", actor_cache="cold"):
        with CaptureQueriesContext(connection) as capture:
            response = client.get(url)
        assert response.status_code == 200
        assert response.wsgi_request.user is not actor
        assert {row.pk for row in response.context["object_list"]} == {row.pk for row in rows}
        document = html.fromstring(response.content)
        action_cells = document.xpath(
            '//tbody/tr/td[contains(concat(" ", normalize-space(@class), " "), " cv-col-action ")]'
        )
        assert len(action_cells) == row_count
        allowed_urls, denied_urls = [], []
        for row in rows:
            detail = reverse(cv_guardian_publisher.get_router_name("detail"), kwargs={"pk": row.pk})
            cells = [cell for cell in action_cells if cell.xpath(".//a[@href=$url]", url=detail)]
            assert len(cells) == 1
            assert len(cells[0].xpath(".//a[@href=$url]", url=detail)) == 1
            allowed_urls.append(detail)
            for action in ("update", "delete"):
                denied = reverse(cv_guardian_publisher.get_router_name(action), kwargs={"pk": row.pk})
                assert cells[0].xpath(".//*[@href=$url or @action=$url]", url=denied) == []
                denied_urls.append(denied)
        excluded_url = reverse(cv_guardian_publisher.get_router_name("detail"), kwargs={"pk": excluded.pk})
        assert document.xpath(".//*[@href=$url]", url=excluded_url) == []
        assert excluded.name not in document.text_content()

        sql = [{"category": list_sql_category(query["sql"]), "sql": query["sql"]} for query in capture]
        categories = dict(Counter(query["category"] for query in sql))
        record_property(
            "measurement",
            json.dumps(
                {
                    "rows": row_count,
                    "configured_actions": GuardianPublisherListView.cv_list_actions,
                    "allowed_urls": allowed_urls,
                    "denied_urls": denied_urls,
                    "excluded_url": excluded_url,
                    "queries": len(capture),
                    "categories": categories,
                    "versions": {
                        "python": platform.python_version(),
                        "django": version("Django"),
                        "guardian": version("django-guardian"),
                    },
                    "cache_protocol": (
                        "reset-then-warm-vocabulary/setup-actor; fresh-client-request-user; no grant priming"
                    ),
                    "sql": sql,
                },
                sort_keys=True,
            ),
        )
        # Measured on unchanged production; full SQL and immutable before values
        # live in phase 06.49's COST-BASELINE and its isolated/combined receipts.
        total, grants, filtered = {0: (7, 0, 2), 1: (14, 3, 3), 3: (26, 9, 3)}[row_count]
        assert len(capture) == total, sql
        assert categories.get("checker_user_grants", 0) == grants, sql
        assert categories.get("checker_group_grants", 0) == grants, sql
        assert categories["list_filter"] == filtered, sql
        assert categories.get("content_type", 0) == categories.get("other", 0) == 0, sql
