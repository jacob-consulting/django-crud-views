"""#149: list actions (and their hidden POST forms) in disable mode."""

import pytest
from lxml import html as lxml_html

from tests.lib.helper.guardian import user_guardian_object_perm
from tests.test1.app.views import (
    AuthorDeleteView,
    AuthorListView,
    AuthorUpView,
    GuardianAuthorDeleteView,
    PublisherDeleteView,
)


def _doc(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.content.decode(), lxml_html.fromstring(resp.content)


@pytest.mark.django_db
def test_list_hide_is_default(client_user_publisher_view, publisher_penguin):
    content, doc = _doc(client_user_publisher_view, "/publisher/")
    assert doc.cssselect('[cv-key="delete"]') == []
    assert f"/publisher/{publisher_penguin.pk}/delete/" not in content


@pytest.mark.django_db
def test_list_get_action_disabled(client_user_publisher_view, publisher_penguin, monkeypatch):
    monkeypatch.setattr(PublisherDeleteView, "cv_inaccessible_actions", "disable")
    content, doc = _doc(client_user_publisher_view, "/publisher/")
    (btn,) = doc.cssselect('a[cv-key="delete"]')
    assert "disabled" in btn.get("class").split()
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert f"/publisher/{publisher_penguin.pk}/delete/" not in content
    # mixed modes: update (PublisherUpdateView) is still "hide"
    assert doc.cssselect('[cv-key="update"]') == []
    # usable action untouched
    (detail,) = doc.cssselect('a[cv-key="detail"]')
    # links may carry ?cv_from=<origin>; compare the path only
    assert detail.get("href", "").startswith(f"/publisher/{publisher_penguin.pk}/detail/")


@pytest.mark.django_db
def test_list_post_action_disabled_has_no_form(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "up"])
    monkeypatch.setattr(AuthorUpView, "cv_inaccessible_actions", "disable")
    content, doc = _doc(client_user_author_view, "/author/")
    (btn,) = doc.cssselect('[cv-key="up"]')
    assert btn.tag == "button"
    assert btn.get("disabled") is not None
    assert btn.get("data-cv-action") is None
    assert btn.get("data-cv-target") is None
    assert doc.cssselect('form[id^="cv_form_"]') == []
    assert f"/author/{author_douglas_adams.pk}/up/" not in content


@pytest.mark.django_db
def test_list_modal_action_disabled(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    _, doc = _doc(client_user_author_view, "/author/")
    (btn,) = doc.cssselect('a[cv-key="delete"]')
    assert btn.get("href") is None
    assert btn.get("data-cv-modal") is None
    assert btn.get("data-cv-modal-size") is None


@pytest.mark.django_db
def test_guardian_object_denial_disabled(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, monkeypatch
):
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    monkeypatch.setattr(GuardianAuthorDeleteView, "cv_inaccessible_actions", "disable")
    _, doc = _doc(client_guardian, "/guardian_author/")
    (btn,) = doc.cssselect('a[cv-key="delete"]')
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
