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


def _filter_icon_states(response) -> dict:
    from lxml import html

    doc = html.fromstring(response.content)
    spans = doc.cssselect("#cv-filter-toggle [data-cv-filter-icon]")
    return {s.get("data-cv-filter-icon"): "d-none" in s.get("class", "").split() for s in spans}


@pytest.mark.django_db
def test_filter_toggle_icon_collapsed(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """Collapsed panel: open icon visible, close icon hidden."""
    response = client_user_publisher_view.get("/publisher/")
    assert _filter_icon_states(response) == {"open": False, "close": True}


@pytest.mark.django_db
def test_filter_toggle_icon_expanded(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """Expanded panel (stored in session): close icon visible, open icon hidden."""
    post = client_user_publisher_view.post(
        "/publisher/", data='{"filter_expanded": true}', content_type="application/json"
    )
    assert post.status_code == 200
    response = client_user_publisher_view.get("/publisher/")
    assert _filter_icon_states(response) == {"open": True, "close": False}


@pytest.mark.django_db
def test_toggle_and_panel_follow_cv_filter_expanded(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    """Both the toggle icon and the panel state read the one view property, not the session directly."""
    view_cls = cv_publisher.get_all_views()["list"]
    monkeypatch.setattr(view_cls, "cv_filter_expanded", property(lambda self: True))
    response = client_user_publisher_view.get("/publisher/")
    assert response.context["cv_filter_expanded"] is True
    assert _filter_icon_states(response) == {"open": True, "close": False}


@pytest.mark.django_db
def test_pinned_filter_is_expanded_without_toggle(
    client_user_publisher_view: Client, cv_publisher, publisher_penguin, monkeypatch
):
    from lxml import html

    view_cls = cv_publisher.get_all_views()["list"]
    monkeypatch.setattr(view_cls, "cv_filter_pinned", True)
    response = client_user_publisher_view.get("/publisher/")
    assert response.context["cv_filter_expanded"] is True
    assert html.fromstring(response.content).cssselect("#cv-filter-toggle") == []
