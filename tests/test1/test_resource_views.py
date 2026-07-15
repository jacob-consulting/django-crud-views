import hashlib

import pytest
from django.test.client import Client


def md5(key: str) -> str:
    return hashlib.md5(key.encode()).hexdigest()


@pytest.fixture
def s3_bucket():
    """Snapshot/restore the fake bucket so mutating tests stay isolated."""
    from tests.test1.app import resources

    original = [dict(row) for row in resources.FAKE_BUCKET]
    yield resources.FAKE_BUCKET
    resources.FAKE_BUCKET[:] = original


@pytest.mark.django_db
def test_list_renders_rows(client_user_s3file_view: Client):
    response = client_user_s3file_view.get("/s3file/")
    assert response.status_code == 200
    content = response.content.decode()
    # page 1 of 2 (paginate_by=2); tables2 renders attribute access on Pydantic rows
    assert "reports/2026/q1.pdf" in content
    assert "reports/2026/q2.pdf" in content


@pytest.mark.django_db
def test_list_pagination_page2(client_user_s3file_view: Client):
    response = client_user_s3file_view.get("/s3file/?page=2")
    assert response.status_code == 200
    assert "images/logo.png" in response.content.decode()


@pytest.mark.django_db
def test_list_requires_permission(client: Client, user_a):
    client.force_login(user_a)
    response = client.get("/s3file/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_anonymous_redirects_to_login(client: Client):
    response = client.get("/s3file/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_detail_renders_object(client_user_s3file_view: Client):
    response = client_user_s3file_view.get(f"/s3file/{md5('reports/2026/q1.pdf')}/detail/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "reports/2026/q1.pdf" in content
    assert "111" in content


@pytest.mark.django_db
def test_detail_unknown_pk_404(client_user_s3file_view: Client):
    response = client_user_s3file_view.get(f"/s3file/{'0' * 32}/detail/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_detail_requires_permission(client: Client, user_a):
    client.force_login(user_a)
    response = client.get(f"/s3file/{md5('reports/2026/q1.pdf')}/detail/")
    assert response.status_code == 403


def test_session_data_app_label_shim():
    """SessionData reads view.model._meta.app_label (session.py:49) — the
    Options shim must satisfy it (spec §3 coupling point 5)."""
    from crud_views.lib.session import SessionData
    from tests.test1.app.resources import S3File

    class _StubView:
        model = S3File

    assert SessionData(view=_StubView()).app_label == "app"
