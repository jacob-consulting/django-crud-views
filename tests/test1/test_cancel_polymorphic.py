"""The type picker forwards cancel state without changing successful save navigation."""

from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core import signing

from crud_views.lib.view.cancel import MAX_TOKEN, SALT
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Car
from tests.test1.app.views import VehicleCreateSelectView, VehicleCreateView
from tests.test1.test_cancel_navigation import emitted_link, rendered_cancel

pytestmark = pytest.mark.django_db


@pytest.fixture
def vehicle_client(client_user_vehicle_add, user_vehicle_add, cv_vehicle):
    user_viewset_permission(user_vehicle_add, cv_vehicle, "view")
    return client_user_vehicle_add


def selector_link(client, query="x=&x=two"):
    page = client.get("/vehicle/?" + query)
    assert page.status_code == 200
    return emitted_link(page, "/vehicle/create/select/")


def select(client, url):
    ct = ContentType.objects.get_for_model(Car)
    response = client.post(url, {"polymorphic_ctype_id": ct.pk})
    assert response.status_code == 302
    assert urlsplit(response.url).path == f"/vehicle/create/ct/{ct.pk}/"
    assert "cv_from" not in parse_qs(urlsplit(response.url).query)
    return response.url


def test_picker_preserves_captured_query(vehicle_client):
    link = selector_link(vehicle_client)
    concrete = select(vehicle_client, link)
    response = vehicle_client.get(concrete)
    assert rendered_cancel(response) == "/vehicle/?x=&x=two&cv_from_restore=1"


@pytest.mark.parametrize("selector_cancel", ["auto", None])
@pytest.mark.parametrize("concrete_cancel", ["auto", None])
@pytest.mark.parametrize("selector_success", [None, ["list"]])
@pytest.mark.parametrize("concrete_success", [None, ["list"]])
def test_independent_cancel_success_configuration(
    vehicle_client, monkeypatch, selector_cancel, concrete_cancel, selector_success, concrete_success
):
    monkeypatch.setattr(VehicleCreateSelectView, "cv_cancel_keys", selector_cancel)
    monkeypatch.setattr(VehicleCreateView, "cv_cancel_keys", concrete_cancel)
    monkeypatch.setattr(VehicleCreateSelectView, "cv_success_keys", selector_success)
    monkeypatch.setattr(VehicleCreateView, "cv_success_keys", concrete_success)
    monkeypatch.setattr(VehicleCreateView, "cv_success_key", "detail")
    link = selector_link(vehicle_client)
    expected_selector = "/vehicle/?x=&x=two&cv_from_restore=1" if selector_cancel else "/vehicle/"
    for _ in range(2):
        response = vehicle_client.post(link, {})
        assert response.status_code == 200
        assert rendered_cancel(response) == expected_selector
    concrete = select(vehicle_client, link)
    token = parse_qs(urlsplit(concrete).query).get("cv_from_cancel")
    if concrete_cancel and (selector_cancel or selector_success):
        payload = signing.Signer(salt=SALT).unsign_object(token[0])
        assert payload["origin"] == "list"
        assert payload["query"] == ("x=&x=two" if selector_cancel else None)
    else:
        assert token is None
    expected = expected_selector if concrete_cancel else "/vehicle/"
    for _ in range(2):
        response = vehicle_client.post(concrete, {})
        assert response.status_code == 200
        assert rendered_cancel(response) == expected
    response = vehicle_client.post(concrete, {"name": "Picked", "doors": 4})
    obj = Car.objects.get(name="Picked")
    assert response.status_code == 302
    assert response["Location"] == f"/vehicle/{obj.pk}/detail/"


@pytest.mark.parametrize("bad", ["tampered", "oversized", "duplicate", "mismatch"])
def test_invalid_capture_cannot_borrow_success_origin(vehicle_client, monkeypatch, bad):
    monkeypatch.setattr(VehicleCreateSelectView, "cv_success_keys", ["list"])
    monkeypatch.setattr(VehicleCreateView, "cv_success_keys", ["list"])
    link = selector_link(vehicle_client)
    query = parse_qs(urlsplit(link).query, keep_blank_values=True)
    if bad == "tampered":
        query["cv_from_cancel"] = [query["cv_from_cancel"][0] + "bad"]
    elif bad == "oversized":
        query["cv_from_cancel"] = ["x" * (MAX_TOKEN + 1)]
    elif bad == "duplicate":
        query["cv_from"] = ["list", "list"]
    else:
        query["cv_from"] = ["detail"]
    link = "/vehicle/create/select/?" + urlencode(query, doseq=True)
    for _ in range(2):
        assert rendered_cancel(vehicle_client.post(link, {})) == "/vehicle/"
    concrete = select(vehicle_client, link)
    assert parse_qs(urlsplit(concrete).query) == {"cv_from_cancel": ["invalid"]}
    for _ in range(2):
        assert rendered_cancel(vehicle_client.post(concrete, {})) == "/vehicle/"


@pytest.mark.parametrize("query", ["", "x=&x=two"])
@pytest.mark.parametrize("allowed", [["list"], ["detail"]])
def test_token_only_handoff_and_explicit_allowlist(vehicle_client, monkeypatch, query, allowed):
    monkeypatch.setattr(VehicleCreateView, "cv_cancel_keys", allowed)
    link = selector_link(vehicle_client, query)
    params = parse_qs(urlsplit(link).query)
    params.pop("cv_from")
    link = "/vehicle/create/select/?" + urlencode(params, doseq=True)
    concrete = select(vehicle_client, link)
    expected = "/vehicle/?" + (query + "&" if query else "") + "cv_from_restore=1"
    assert rendered_cancel(vehicle_client.post(concrete, {})) == (expected if allowed == ["list"] else "/vehicle/")


def test_parallel_selector_forms_keep_original_state(vehicle_client):
    first = selector_link(vehicle_client, "x=first&x=")
    second = selector_link(vehicle_client, "x=second")
    vehicle_client.get("/vehicle/?x=changed")
    for link, query in [(second, "x=second"), (first, "x=first&x=")]:
        one = select(vehicle_client, link)
        two = select(vehicle_client, link)
        assert one == two
        assert rendered_cancel(vehicle_client.post(one, {})) == f"/vehicle/?{query}&cv_from_restore=1"


def test_direct_concrete_success_still_uses_explicit_shared_origin(vehicle_client, monkeypatch):
    monkeypatch.setattr(VehicleCreateView, "cv_success_keys", ["list"])
    monkeypatch.setattr(VehicleCreateView, "cv_success_key", "detail")
    ct = ContentType.objects.get_for_model(Car)
    response = vehicle_client.post(f"/vehicle/create/ct/{ct.pk}/?cv_from=list", {"name": "Direct", "doors": 2})
    assert response.status_code == 302
    assert response["Location"] == "/vehicle/"
