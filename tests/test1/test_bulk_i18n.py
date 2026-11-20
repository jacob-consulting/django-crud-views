"""German catalog completeness and rendered bulk selection, review and execution."""

import re
from pathlib import Path

import polib
import pytest
from django.contrib.messages import get_messages
from django.test import override_settings
from django.utils.translation import override

from tests.test1.test_bulk_flow import review_data, soup

CORE = Path(__file__).resolve().parents[2] / "src" / "crud_views"
TEMPLATES = (
    "snippets/bulk_toolbar.html",
    "columns/bulk_select.html",
    "view_card.content.html",
    "view_bulk_form.content.html",
    "snippets/bulk/eligible.html",
    "snippets/bulk/blocked.html",
    "snippets/bulk/blocked_items.html",
    "snippets/paragraph/bulk.html",
    "snippets/message/bulk.html",
)
MODULE_MSGIDS = (
    "Select",
    "Confirm",
    "This item is unavailable for this action.",
    "Excluded from this confirmation; select it again from the list.",
    "The eligible selection changed. Review it and confirm again.",
    "Select at least one record.",
    "Select at most %(max)d records.",
)


def assert_translated(catalog, msgid, plural=None):
    entry = catalog.find(msgid)
    assert entry is not None, msgid
    assert entry.translated() and "fuzzy" not in entry.flags, msgid
    if plural:
        assert entry.msgid_plural == plural
        assert set(entry.msgstr_plural) == {0, 1}
        assert all(entry.msgstr_plural.values())


def test_bulk_template_catalog_completeness():
    catalog = polib.pofile(str(CORE / "locale/de/LC_MESSAGES/django.po"))
    extracted = set()
    for relative in TEMPLATES:
        template = (CORE / "templates/crud_views" / relative).read_text()
        for literal in re.findall(r'{%\s*translate\s+"([^"]+)"[^%]*%}', template):
            extracted.add(literal)
            assert_translated(catalog, literal)
        for body in re.findall(r"{%\s*blocktranslate\b[^%]*%}(.*?){%\s*endblocktranslate\s*%}", template, re.S):
            parts = re.split(r"{%\s*plural\s*%}", body)
            parts = [re.sub(r"{{\s*(\w+)\s*}}", r"%(\1)s", part) for part in parts]
            extracted.add(parts[0])
            assert_translated(catalog, parts[0], parts[1] if len(parts) == 2 else None)
    assert {"Select this page", "Select %(name)s", "%(counter)s record processed."} <= extracted


def test_bulk_module_catalog_completeness():
    catalog = polib.pofile(str(CORE / "locale/de/LC_MESSAGES/django.po"))
    for msgid in MODULE_MSGIDS:
        assert_translated(catalog, msgid)


@pytest.fixture
def german():
    with override_settings(LANGUAGE_CODE="de", LANGUAGES=[("en", "English"), ("de", "German")]), override("de"):
        yield


@pytest.mark.django_db
def test_bulk_source_german(german, client_user_bulk_publisher_change, bulk_publishers):
    page = soup(client_user_bulk_publisher_change.get("/bulk-publisher/"))
    assert "Diese Seite auswählen" in page.text_content()
    assert "ausgewählt" in page.text_content()
    assert page.cssselect("[data-cv-bulk-item]")[0].get("aria-label") == "Alpha auswählen"
    assert any("Auswählen" in heading.text_content() for heading in page.cssselect("th"))


@pytest.mark.django_db
@pytest.mark.parametrize("blocked_count", [0, 1, 2])
def test_bulk_review_german(german, client_user_bulk_publisher_change, bulk_publishers, blocked_count):
    selected = [record.pk for record in bulk_publishers[:2]] + [987650 + index for index in range(blocked_count)]
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": selected}
    )
    assert response.status_code == 200
    page = soup(response)
    assert "Zu verarbeiten: 2" in page.text_content()
    assert "Bestätigen" in page.text_content()
    assert "Die ausgewählten Einträge vor dem Fortfahren prüfen." in page.text_content()
    if blocked_count:
        heading = "1 Eintrag wird übersprungen" if blocked_count == 1 else "2 Einträge werden übersprungen"
        assert heading in page.text_content()
        assert "Dieser Eintrag ist für diese Aktion nicht verfügbar." in page.text_content()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "count, expected", [(0, "Mindestens einen Eintrag auswählen."), (101, "Höchstens 100 Einträge auswählen.")]
)
def test_bulk_selection_warnings_german(german, client_user_bulk_publisher_change, count, expected):
    response = client_user_bulk_publisher_change.post(
        "/bulk-publisher/archive/", {"cv_bulk_stage": "review", "cv_bulk_ids": list(range(1, count + 1))}
    )
    assert response.status_code == 302
    assert [str(message) for message in get_messages(response.wsgi_request)] == [expected]


@pytest.mark.django_db
@pytest.mark.parametrize("count, expected", [(1, "1 Eintrag verarbeitet."), (2, "2 Einträge verarbeitet.")])
def test_bulk_success_german(german, client_user_bulk_publisher_change, bulk_publishers, count, expected):
    client = client_user_bulk_publisher_change
    review = client.post(
        "/bulk-publisher/archive/",
        {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in bulk_publishers[:count]]},
    )
    assert review.status_code == 200
    response = client.post("/bulk-publisher/archive/", review_data(review))
    assert response.status_code == 302
    assert [str(message) for message in get_messages(response.wsgi_request)] == [expected]
