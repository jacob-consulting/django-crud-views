"""Compiled German diagnostics at real trace, command and inherited-page boundaries."""

import json

import pytest
from django.utils import translation
from django.utils.translation import trans_real
from lxml import html

from crud_views.lib.access_trace import trace_access
from tests.test1.test_access_trace_command import invoke
from tests.test1.test_manage_access_trace import developer, enabled, host, submit  # noqa: F401

pytestmark = pytest.mark.django_db

NOTICES = {
    "en": "other middleware and URL decorators are not traced",
    "de": "Andere Middleware und URL-Dekoratoren werden nicht nachverfolgt",
}


@pytest.fixture(autouse=True)
def fresh_catalog(monkeypatch):
    monkeypatch.setattr(trans_real, "_translations", {})


def stable(value):
    """Retain every schema key, machine code and fact; replace only localized prose."""
    if isinstance(value, dict):
        return {key: None if key in {"message", "untraced"} else stable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def test_notices_are_assembled_once_and_reach_every_real_output(client, host, developer, enabled):
    path = "/author/manage/"
    documents = {}
    for language, notice in NOTICES.items():
        with translation.override(language):
            trace = trace_access(path, developer)
            data = trace.to_dict()
            assert notice in data["untraced"]
            code, stdout, stderr = invoke(path, developer.username, "--as-json", "--no-color")
            assert code == 0 and stderr == ""
            parsed = json.loads(stdout)
            assert notice in parsed["untraced"]
            assert parsed == data
            code, stdout, stderr = invoke(path, developer.username, "--no-color")
            assert code == 0 and stderr == "" and notice in stdout
            response = submit(client, host, developer, cv_access_mode="path", cv_access_user=developer.username, cv_access_path=path)
            assert response.status_code == 200
            card = html.fromstring(response.content).cssselect("#cv-manage-access-trace")[0]
            assert notice in card.text_content()
            assert response.context["manage_access_trace"]["trace"] == data
            documents[language] = data
        with translation.override("de" if language == "en" else "en"):
            assert trace.to_dict() == data
    assert stable(documents["en"]) == stable(documents["de"])
