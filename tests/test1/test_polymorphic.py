import pytest
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client

from crud_views.lib.viewset import ViewSet
from tests.lib.helper.boostrap5 import Table
from tests.test1.app.models import Vehicle, Car, Truck


@pytest.mark.django_db
def test_viewset_has_polymorphic_views(cv_vehicle: ViewSet):
    """Polymorphic viewset should have all expected views registered."""
    for view_name in ["list", "detail", "create", "create_select", "update", "delete"]:
        assert cv_vehicle.has_view(view_name), f"ViewSet missing view: {view_name}"


@pytest.mark.django_db
def test_viewset_url_patterns(cv_vehicle: ViewSet):
    """URL patterns should include polymorphic-specific routes."""
    routes = {p.name for p in cv_vehicle.urlpatterns}
    assert "vehicle-create_select" in routes
    assert "vehicle-create" in routes

    # Create URL should contain polymorphic_ctype_id
    create_patterns = [p for p in cv_vehicle.urlpatterns if p.name == "vehicle-create"]
    assert len(create_patterns) == 1
    assert "polymorphic_ctype_id" in create_patterns[0].pattern.regex.pattern


@pytest.mark.django_db
def test_list_shows_all_subtypes(client_user_vehicle_view: Client, cv_vehicle, car_sedan, truck_semi):
    """List view should show all polymorphic subtypes."""
    response = client_user_vehicle_view.get("/vehicle/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 2
    names = {row.columns[1].text for row in table.rows}
    assert "Sedan" in names
    assert "Semi" in names


@pytest.mark.django_db
def test_detail_car(client_user_vehicle_view: Client, cv_vehicle, car_sedan):
    """Detail view should resolve to the correct polymorphic subtype."""
    response = client_user_vehicle_view.get(f"/vehicle/{car_sedan.pk}/detail/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Sedan" in content


@pytest.mark.django_db
def test_detail_truck(client_user_vehicle_view: Client, cv_vehicle, truck_semi):
    response = client_user_vehicle_view.get(f"/vehicle/{truck_semi.pk}/detail/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Semi" in content


@pytest.mark.django_db
def test_create_select_shows_form(client_user_vehicle_add: Client, cv_vehicle):
    """Create-select view should show a form with polymorphic type choices."""
    response = client_user_vehicle_add.get("/vehicle/create/select/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "polymorphic_ctype_id" in content


@pytest.mark.django_db
def test_create_select_redirects_to_create(client_user_vehicle_add: Client, cv_vehicle):
    """Submitting create-select should redirect to the polymorphic create view."""
    car_ct = ContentType.objects.get_for_model(Car)
    response = client_user_vehicle_add.post("/vehicle/create/select/", {"polymorphic_ctype_id": car_ct.id})
    assert response.status_code == 302
    assert f"/vehicle/create//ct/{car_ct.id}/" in response.url


@pytest.mark.django_db
def test_create_car(client_user_vehicle_add: Client, cv_vehicle):
    """Creating a Car through the polymorphic create view."""
    car_ct = ContentType.objects.get_for_model(Car)

    # GET the form
    response = client_user_vehicle_add.get(f"/vehicle/create//ct/{car_ct.id}/")
    assert response.status_code == 200

    # POST the form
    response = client_user_vehicle_add.post(f"/vehicle/create//ct/{car_ct.id}/", {"name": "Coupe", "doors": 2})
    assert response.status_code == 302

    car = Car.objects.get(name="Coupe")
    assert car.doors == 2
    # Should also be queryable as Vehicle
    assert Vehicle.objects.filter(pk=car.pk).exists()


@pytest.mark.django_db
def test_create_truck(client_user_vehicle_add: Client, cv_vehicle):
    """Creating a Truck through the polymorphic create view."""
    truck_ct = ContentType.objects.get_for_model(Truck)

    response = client_user_vehicle_add.post(
        f"/vehicle/create//ct/{truck_ct.id}/", {"name": "Pickup", "payload_tons": 5}
    )
    assert response.status_code == 302

    truck = Truck.objects.get(name="Pickup")
    assert truck.payload_tons == 5


@pytest.mark.django_db
def test_update_car(client_user_vehicle_change: Client, cv_vehicle, car_sedan):
    """Updating a Car through the polymorphic update view."""
    response = client_user_vehicle_change.get(f"/vehicle/{car_sedan.pk}/update/")
    assert response.status_code == 200

    response = client_user_vehicle_change.post(f"/vehicle/{car_sedan.pk}/update/", {"name": "Sports Car", "doors": 2})
    assert response.status_code == 302

    car_sedan.refresh_from_db()
    assert car_sedan.name == "Sports Car"
    assert car_sedan.doors == 2


@pytest.mark.django_db
def test_update_truck(client_user_vehicle_change: Client, cv_vehicle, truck_semi):
    """Updating a Truck through the polymorphic update view."""
    response = client_user_vehicle_change.post(
        f"/vehicle/{truck_semi.pk}/update/", {"name": "Big Rig", "payload_tons": 30}
    )
    assert response.status_code == 302

    truck_semi.refresh_from_db()
    assert truck_semi.name == "Big Rig"
    assert truck_semi.payload_tons == 30


@pytest.mark.django_db
def test_delete_vehicle(client_user_vehicle_delete: Client, cv_vehicle, car_sedan):
    """Deleting a polymorphic vehicle."""
    pk = car_sedan.pk

    response = client_user_vehicle_delete.get(f"/vehicle/{pk}/delete/")
    assert response.status_code == 200

    response = client_user_vehicle_delete.post(f"/vehicle/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302

    assert not Vehicle.objects.filter(pk=pk).exists()
    assert not Car.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_polymorphic_queryset_returns_subtypes(cv_vehicle, car_sedan, truck_semi):
    """Vehicle.objects.all() should return Car and Truck instances."""
    vehicles = list(Vehicle.objects.all())
    types = {type(v) for v in vehicles}
    assert Car in types
    assert Truck in types
