import pytest
from django.test.client import Client
from lxml import html


@pytest.fixture
def cv_author_custom_detail():
    from tests.test1.app.views import cv_author_custom_detail as ret

    return ret


@pytest.fixture
def user_author_custom_detail_view(cv_author_custom_detail):
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_custom_detail", password="password")
    user_viewset_permission(user, cv_author_custom_detail, "view")
    return user


@pytest.fixture
def client_user_author_custom_detail(client, user_author_custom_detail_view) -> Client:
    client.force_login(user_author_custom_detail_view)
    return client


@pytest.mark.django_db
def test_detail_custom_view_renders(client_user_author_custom_detail: Client, cv_author_custom_detail, author_douglas_adams):
    """DetailCustomView renders the custom template with object context."""
    pk = author_douglas_adams.pk
    response = client_user_author_custom_detail.get(f"/author_custom_detail/{pk}/detail/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    custom_div = doc.cssselect(".author-custom-detail")
    assert len(custom_div) == 1
    assert "Douglas" in custom_div[0].text_content()
    assert "Adams" in custom_div[0].text_content()


@pytest.mark.django_db
def test_detail_custom_view_permission_denied(client_user_a: Client, cv_author_custom_detail, author_douglas_adams):
    """User without view permission gets 403."""
    pk = author_douglas_adams.pk
    response = client_user_a.get(f"/author_custom_detail/{pk}/detail/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_detail_custom_view_has_correct_key(cv_author_custom_detail):
    """DetailCustomView registers with key 'detail'."""
    view_class = cv_author_custom_detail.get_view_class("detail")
    assert view_class.cv_key == "detail"
    assert view_class.cv_path == "detail"


@pytest.mark.django_db
def test_detail_view_still_works(client_user_author_view: Client, cv_author, author_douglas_adams):
    """Existing DetailView (with ObjectDetailMixin) still renders correctly after refactor."""
    pk = author_douglas_adams.pk
    response = client_user_author_view.get(f"/author/{pk}/detail/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Douglas" in content
    assert "Adams" in content
