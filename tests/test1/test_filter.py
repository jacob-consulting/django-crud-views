import pytest
from django.test.client import Client

from tests.lib.helper.boostrap5 import Table


@pytest.mark.django_db
def test_filter_no_params_shows_all(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """Without filter params, all publishers are listed."""
    response = client_user_publisher_view.get("/publisher/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 2


@pytest.mark.django_db
def test_filter_by_name_match(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """Filter with matching name returns only the matched publisher."""
    response = client_user_publisher_view.get("/publisher/?name=penguin")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "Penguin" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_filter_by_name_no_match(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """Filter with non-matching name returns empty table."""
    response = client_user_publisher_view.get("/publisher/?name=nonexistent")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 0


@pytest.mark.django_db
def test_filter_is_case_insensitive(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """icontains lookup should be case-insensitive."""
    response = client_user_publisher_view.get("/publisher/?name=PENGUIN")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "Penguin" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_filter_partial_match(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, publisher_harpercollins
):
    """icontains lookup should match partial strings."""
    response = client_user_publisher_view.get("/publisher/?name=harper")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert "HarperCollins" in table.rows[0].columns[1].text


@pytest.mark.django_db
def test_filter_form_rendered(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """The filter form should be present in the response."""
    response = client_user_publisher_view.get("/publisher/")
    content = response.content.decode("utf-8")
    assert 'id="filter-button"' in content
