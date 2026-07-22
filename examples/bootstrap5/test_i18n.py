import pytest
from django.test import Client


@pytest.mark.django_db
def test_browser_language_default_de():
    client = Client()
    resp = client.get("/", HTTP_ACCEPT_LANGUAGE="de")
    assert resp.status_code == 200
    assert '<html lang="de"' in resp.content.decode()


@pytest.mark.django_db
def test_set_language_switches_and_persists():
    client = Client()
    resp = client.post("/i18n/setlang/", {"language": "de", "next": "/"}, follow=True)
    assert resp.status_code == 200
    assert '<html lang="de"' in resp.content.decode()


@pytest.mark.django_db
def test_selector_present_in_nav():
    resp = Client().get("/")
    body = resp.content.decode()
    assert 'name="language"' in body  # selector form field rendered
