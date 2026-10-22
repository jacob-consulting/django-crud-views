"""#251: the card, workflow, object-detail and modal headings follow CRUD_VIEWS_HEADER_LEVEL.

With the setting unset, the heading markup is exactly the pre-#251 HTML. Golden files were captured from main before
the templates changed. Regenerate ONLY when a change to the default markup is intended:
CV_UPDATE_GOLDEN=1 pytest tests/test1/test_heading_level.py
"""

import os
import uuid
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from crud_views_object_detail.lib.resolvers import ResolvedGroup
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Author, Campaign
from tests.test1.app.views import cv_author, cv_author_modal, cv_campaign

GOLDEN_DIR = Path(__file__).parent / "golden" / "heading_level"
# the test project's base template wraps {% cv_header %} in its own headings (h5.d-flex > h3); those are the host's
HEADINGS = " | ".join(f"//h{n}[not(ancestor-or-self::h5[contains(@class, 'd-flex')])]" for n in range(1, 7))
LAYOUTS = ["accordion", "card-rows", "list-group-3col", "split-card", "striped-rows", "table-inline", "tabs-vertical"]


def _headings(markup: str) -> str:
    doc = lxml_html.fromstring(f"<div>{markup}</div>")
    return "\n".join(lxml_html.tostring(h, encoding="unicode").strip() for h in doc.xpath(HEADINGS))


def _compare(name: str, actual: str):
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN") == "1":
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(actual + "\n")
    assert actual == path.read_text().strip()


def _render_group(layout: str) -> str:
    group = ResolvedGroup(title="Test", description="Desc", properties=[], icon=None)
    tpl = Template("{% load crud_views_object_detail %}{% render_group group layout=layout %}")
    return tpl.render(Context({"group": group, "layout": layout}))


def _client(viewset, perms) -> Client:
    user = User.objects.create_user(username=f"heading_251_{uuid.uuid4().hex[:8]}", password="pw")
    for perm in perms:
        user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def _get(client: Client, url: str, **kwargs) -> str:
    resp = client.get(url, **kwargs)
    assert resp.status_code == 200
    return resp.content.decode()


def _card_page() -> str:
    Author.objects.create(first_name="Douglas", last_name="Adams")
    client = _client(cv_author, ("view", "add", "change", "delete"))
    return _get(client, reverse(cv_author.get_router_name("card")))


def _workflow_page() -> str:
    campaign = Campaign.objects.create(name="Test Campaign")
    client = _client(cv_campaign, ("change",))
    # one transition, so the history section renders
    client.post(f"/campaign/{campaign.pk}/workflow/", {"transition": "wf_activate", "comment": ""})
    return _get(client, f"/campaign/{campaign.pk}/workflow/")


def _modal_detail() -> str:
    author = Author.objects.create(first_name="Douglas", last_name="Adams")
    client = _client(cv_author_modal, ("view",))
    return _get(client, f"/author_modal/{author.pk}/detail/", headers={"X-CV-Modal": "true"})


SURFACES = {
    "card": _card_page,
    "workflow": _workflow_page,
    "modal_detail": _modal_detail,
    **{f"od_{layout}": (lambda layout=layout: _render_group(layout)) for layout in LAYOUTS},
}


@pytest.mark.django_db
@pytest.mark.parametrize("name", list(SURFACES))
def test_heading_golden_default(name):
    actual = _headings(SURFACES[name]())
    assert actual
    _compare(name, actual)
