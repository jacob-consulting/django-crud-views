import pytest
from lxml import html

from tests.lib.helper.guardian import user_guardian_object_perm


@pytest.mark.django_db
def test_guardian_card_list_filters_by_object_perm(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, author_terry_pratchett
):
    """User with per-object view on one author only sees that author's card."""
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    response = client_guardian.get("/guardian_author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    cards = doc.cssselect(".card.mb-3")
    assert len(cards) == 1
    title = cards[0].cssselect(".card-title")[0].text_content().strip()
    assert title == "Douglas Adams"


@pytest.mark.django_db
def test_guardian_card_list_empty_without_object_perm(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams
):
    """User without per-object view permission sees no cards."""
    response = client_guardian.get("/guardian_author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    cards = doc.cssselect(".card.mb-3")
    assert len(cards) == 0


@pytest.mark.django_db
def test_guardian_card_list_all_objects_with_perm(
    client_guardian, user_guardian, cv_guardian_author, author_douglas_adams, author_terry_pratchett
):
    """User with per-object view on both authors sees both cards."""
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_douglas_adams)
    user_guardian_object_perm(user_guardian, cv_guardian_author, "view", author_terry_pratchett)
    response = client_guardian.get("/guardian_author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    cards = doc.cssselect(".card.mb-3")
    assert len(cards) == 2
