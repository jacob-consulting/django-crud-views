"""The table selection, review and execution contract for bulk actions."""

import pytest
from lxml import html
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages

from tests.test1.app.models import Publisher

pytestmark = pytest.mark.django_db


def soup(response):
    return html.fromstring(response.content)


def test_table_review_execute_flow(client_user_publisher_view, user_publisher_view):
    user_publisher_view.user_permissions.add(Permission.objects.get(codename="change_publisher"))
    records = [Publisher.objects.create(name=name) for name in ("Alpha", "Beta")]
    client = client_user_publisher_view
    response = client.get("/bulk-publisher/")
    assert response.status_code == 200
    page = soup(response)
    toolbar = page.cssselect("form#cv-bulk-selection")[0]
    assert toolbar.get("method") == "post"
    assert toolbar.cssselect('input[name="csrfmiddlewaretoken"]')[0]
    button = toolbar.cssselect('button[data-cv-bulk-action="archive"]')[0]
    assert button.get("type") == "submit"
    assert button.get("name") == "cv_bulk_stage"
    assert button.get("value") == "review"
    assert button.get("formaction").startswith("/bulk-publisher/archive/?")
    from crud_views.lib.button_classes import get_button_class
    from crud_views.lib.view.label_mode import default_label_mode

    assert " ".join(button.get("class")) == get_button_class("form", "submit", default_label_mode("form"))
    checkboxes = page.cssselect('input[name="cv_bulk_ids"]')
    assert [box.get("value") for box in checkboxes] == [str(obj.pk) for obj in records]
    assert all(box.get("form") == "cv-bulk-selection" for box in checkboxes)
    heading = page.cssselect("table thead th")[0]
    assert heading.text_content().strip() == "Select"
    assert not heading.cssselect("input")

    destination = button.get("formaction")
    response = client.post(destination, {"cv_bulk_stage": "review", "cv_bulk_ids": [obj.pk for obj in records]})
    assert response.status_code == 200
    assert not response.context["form"].is_bound
    page = soup(response)
    assert "Archive selected publishers" in page.text_content()
    form = page.cssselect("form.cv-form")[0]
    assert form.get("action") == destination
    assert form.cssselect('input[name="cv_bulk_stage"]')[0].get("value") == "execute"
    assert [field.get("value") for field in form.cssselect('input[name="cv_bulk_ids"]')] == [
        str(obj.pk) for obj in records
    ]
    assert "Confirm" in form.text_content()
    assert "Cancel" in form.text_content()
    for obj in records:
        assert obj.name in form.text_content()
        assert not [link for link in form.cssselect("a") if link.text_content() == obj.name]
    assert list(Publisher.objects.order_by("pk").values_list("name", flat=True)) == ["Alpha", "Beta"]

    response = client.post(destination, {"cv_bulk_stage": "execute", "cv_bulk_ids": [obj.pk for obj in records]})
    assert response.status_code == 302
    assert response.url == "/bulk-publisher/"
    assert list(Publisher.objects.order_by("pk").values_list("name", flat=True)) == [
        "Alpha (archived)",
        "Beta (archived)",
    ]
    assert [str(message) for message in get_messages(response.wsgi_request)] == ["2 records processed."]
